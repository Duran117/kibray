"""Payroll views — extracted from legacy_views.py in Phase 8."""
from core.views._helpers import *  # noqa: F401, F403
from core.views._helpers import (
    _is_admin_user,
    _is_staffish,
    _require_admin_or_redirect,
    logger,
)
from django.utils.translation import gettext_lazy as _  # noqa: F811


@login_required
def payroll_weekly_review(request):
    """
    Vista para revisar y aprobar la nómina semanal.
    Muestra todos los empleados con sus horas trabajadas en la semana,
    permite editar horas de entrada/salida por día, y registrar pagos.
    
    SOLO ACCESIBLE POR ADMIN/SUPERUSER
    """
    guard = _require_admin_or_redirect(request)
    if guard:
        return guard

    from datetime import datetime, timedelta
    from decimal import Decimal, InvalidOperation
    from core.models import EmployeeSavings

    # Obtener parámetros de fecha (por defecto: semana actual)
    week_start_str = request.GET.get("week_start")
    if week_start_str:
        try:
            week_start = datetime.strptime(week_start_str, "%Y-%m-%d").date()
        except ValueError:
            week_start = datetime.now().date() - timedelta(days=datetime.now().date().weekday())
    else:
        today = datetime.now().date()
        week_start = today - timedelta(days=today.weekday())  # Lunes de esta semana

    week_end = week_start + timedelta(days=6)  # Domingo
    prev_week = week_start - timedelta(days=7)
    next_week = week_start + timedelta(days=7)

    # Crear lista de días de la semana
    day_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    days = []
    for i in range(7):
        day_date = week_start + timedelta(days=i)
        days.append({
            'name': day_names[i],
            'date': day_date,
            'index': i
        })

    # Buscar o crear PayrollPeriod
    period, created = PayrollPeriod.objects.get_or_create(
        week_start=week_start, week_end=week_end, defaults={"created_by": request.user}
    )

    # Obtener todos los empleados activos
    employees = Employee.objects.filter(is_active=True).order_by("last_name", "first_name")

    # POST: Actualizar registros
    if request.method == "POST":
        action = request.POST.get("action")

        if action == "update_records":
            time_format = "%H:%M"
            
            for emp in employees:
                emp_id = str(emp.id)
                
                # Procesar horas de entrada/salida por cada día
                for i in range(7):
                    day = week_start + timedelta(days=i)
                    start_val = request.POST.get(f"start_{emp_id}_{i}")
                    end_val = request.POST.get(f"end_{emp_id}_{i}")
                    
                    # Contar TODAS las entradas del día (incluyendo CO)
                    all_entries_count = TimeEntry.objects.filter(
                        employee=emp, date=day
                    ).count()
                    
                    # Si hay múltiples entradas, NO modificar (inputs están disabled)
                    if all_entries_count > 1:
                        continue
                    
                    # Buscar entrada existente BASE para este día (solo si hay 0 o 1 entrada)
                    existing_entry = TimeEntry.objects.filter(
                        employee=emp, date=day, change_order__isnull=True
                    ).first()
                    
                    if start_val and end_val:
                        try:
                            start_time = datetime.strptime(start_val, time_format).time()
                            end_time = datetime.strptime(end_val, time_format).time()
                        except ValueError:
                            continue
                        
                        if existing_entry:
                            existing_entry.start_time = start_time
                            existing_entry.end_time = end_time
                            existing_entry.save()
                        else:
                            TimeEntry.objects.create(
                                employee=emp,
                                date=day,
                                start_time=start_time,
                                end_time=end_time,
                            )
                    elif existing_entry and not start_val and not end_val:
                        # Si se borraron ambos campos, eliminar la entrada
                        # SOLO si hay exactamente 1 entrada (la base)
                        existing_entry.delete()
                
                # Actualizar PayrollRecord
                record, __ = PayrollRecord.objects.get_or_create(
                    period=period,
                    employee=emp,
                    week_start=week_start,
                    week_end=week_end,
                    defaults={
                        "hourly_rate": emp.hourly_rate,
                        "total_hours": Decimal("0.00"),
                        "total_pay": Decimal("0.00"),
                    },
                )
                
                # IMPORTANTE: Guardar total_pay ANTES de recalcular (para pagos)
                original_total_pay = record.total_pay
                
                # Recalcular horas totales
                time_entries = TimeEntry.objects.filter(
                    employee=emp, date__range=(week_start, week_end)
                )
                total_hours = sum(
                    Decimal(str(entry.hours_worked)) if entry.hours_worked else Decimal("0.00")
                    for entry in time_entries
                )
                
                # Actualizar rate si cambió
                rate = request.POST.get(f"rate_{emp_id}")
                if rate:
                    try:
                        record.adjusted_rate = Decimal(rate)
                    except (ValueError, InvalidOperation, ArithmeticError):
                        pass
                
                record.total_hours = total_hours
                record.split_hours_regular_overtime()
                record.calculate_total_pay()
                record.reviewed = True
                record.save()
                
                # Procesar pago si se proporcionó cantidad pagada y fecha
                paid_amount_str = request.POST.get(f"paid_{emp_id}")
                check_number = request.POST.get(f"check_{emp_id}", "").strip()
                pay_date = request.POST.get(f"pay_date_{emp_id}")
                
                # IMPORTANTE: Solo procesar si hay AMBOS: monto Y fecha
                # Si el campo está vacío, no procesar - el usuario no quiere pagar a este empleado ahora
                if not paid_amount_str or not paid_amount_str.strip():
                    continue  # No payment info entered for this employee
                    
                if not pay_date or not pay_date.strip():
                    continue  # No date entered, skip this employee
                
                try:
                    paid_amount = Decimal(paid_amount_str.strip())
                    
                    # Solo procesar si el monto es > 0
                    if paid_amount <= 0:
                        continue
                    
                    # Verificar si el empleado ya está completamente pagado
                    current_balance = record.balance_due()
                    if current_balance <= 0:
                        # Ya está pagado completamente, no crear más pagos
                        continue
                    
                    # Usar el total_pay ACTUAL del record para calcular savings
                    total_to_pay = record.total_pay if record.total_pay > 0 else paid_amount
                    already_paid = record.amount_paid()
                    remaining = total_to_pay - already_paid
                    
                    # Si paga menos de lo restante, la diferencia es savings
                    if paid_amount < remaining:
                        savings_amount = remaining - paid_amount
                    else:
                        savings_amount = Decimal("0")
                        # Cap payment at remaining balance
                        paid_amount = min(paid_amount, remaining)
                    
                    # Verificar si ya existe un pago para EXACTAMENTE esta fecha y check
                    existing_payment = None
                    if check_number:
                        existing_payment = PayrollPayment.objects.filter(
                            payroll_record=record,
                            check_number=check_number
                        ).first()
                    
                    if not existing_payment:
                        existing_payment = PayrollPayment.objects.filter(
                            payroll_record=record,
                            payment_date=pay_date,
                        ).first()
                    
                    if existing_payment:
                        # Ya existe un pago para esta fecha/check - NO actualizar automáticamente
                        # Esto previene duplicados y modificaciones accidentales
                        messages.warning(
                            request,
                            f"{emp.first_name} {emp.last_name}: Ya existe un pago para esta fecha/cheque. Edita el pago existente si necesitas modificarlo."
                        )
                        continue
                    else:
                        # Crear nuevo pago
                        PayrollPayment.objects.create(
                            payroll_record=record,
                            amount=paid_amount + savings_amount,  # Total amount (paid + saved)
                            amount_taken=paid_amount,  # What employee takes
                            amount_saved=savings_amount,  # What goes to savings
                            payment_date=pay_date,
                            payment_method="check" if check_number else "cash",
                            check_number=check_number,
                            notes=f"Savings: ${savings_amount}" if savings_amount > 0 else "",
                            recorded_by=request.user,
                        )
                        
                        if savings_amount > 0:
                            messages.info(
                                request,
                                f"{emp.first_name} {emp.last_name}: Pagado ${paid_amount}, Ahorro ${savings_amount}"
                            )
                        else:
                            messages.success(
                                request,
                                f"{emp.first_name} {emp.last_name}: Pagado ${paid_amount}"
                            )
                except (ValueError, InvalidOperation) as e:
                    messages.warning(request, f"Error procesando pago para {emp.first_name}: {str(e)}")

            messages.success(request, _("Nómina actualizada correctamente."))
            return redirect(f"{request.path}?week_start={week_start.isoformat()}")

    # Preparar datos de cada empleado
    employee_data = []
    for emp in employees:
        # Buscar o crear PayrollRecord
        record, rec_created = PayrollRecord.objects.get_or_create(
            period=period,
            employee=emp,
            week_start=week_start,
            week_end=week_end,
            defaults={
                "hourly_rate": emp.hourly_rate,
                "total_hours": Decimal("0.00"),
                "total_pay": Decimal("0.00"),
            },
        )

        # Obtener TODAS las entradas de tiempo para cada día (incluyendo CO)
        day_entries = []
        calculated_hours = Decimal("0.00")
        base_hours = Decimal("0.00")
        co_hours = Decimal("0.00")
        
        for i in range(7):
            day = week_start + timedelta(days=i)
            # Obtener TODAS las entradas del día (base + CO)
            entries = TimeEntry.objects.filter(
                employee=emp, date=day
            ).select_related('change_order', 'project').order_by('start_time')
            
            day_total_hours = Decimal("0.00")
            day_base_hours = Decimal("0.00")
            day_co_hours = Decimal("0.00")
            first_start = None
            last_end = None
            entry_details = []
            
            for entry in entries:
                hours = Decimal(str(entry.hours_worked)) if entry.hours_worked else Decimal("0")
                day_total_hours += hours
                
                if entry.change_order:
                    day_co_hours += hours
                    entry_details.append({
                        'type': 'CO',
                        'co_id': entry.change_order.id,
                        'co_title': entry.change_order.title,
                        'hours': float(hours),
                    })
                else:
                    day_base_hours += hours
                    entry_details.append({
                        'type': 'BASE',
                        'project': entry.project.name if entry.project else '',
                        'hours': float(hours),
                    })
                
                # Track first start and last end for display
                if entry.start_time:
                    if first_start is None or entry.start_time < first_start:
                        first_start = entry.start_time
                if entry.end_time:
                    if last_end is None or entry.end_time > last_end:
                        last_end = entry.end_time
            
            calculated_hours += day_total_hours
            base_hours += day_base_hours
            co_hours += day_co_hours
            
            day_entries.append({
                'date': day,  # Add date for modal functionality
                'start': first_start.strftime("%H:%M") if first_start else "",
                'end': last_end.strftime("%H:%M") if last_end else "",
                'hours': day_total_hours if day_total_hours > 0 else None,
                'base_hours': day_base_hours,
                'co_hours': day_co_hours,
                'details': entry_details,
                'entry_count': len(entries),
            })
        
        # Actualizar record con horas calculadas si es diferente
        if record.total_hours != calculated_hours:
            record.total_hours = calculated_hours
            record.split_hours_regular_overtime()
            record.calculate_total_pay()
            record.save()
        
        # Obtener último pago
        last_payment = record.payments.order_by('-payment_date').first()
        
        # Obtener balance de ahorros del empleado
        savings_balance = EmployeeSavings.get_employee_balance(emp)

        employee_data.append({
            "employee": emp,
            "record": record,
            "calculated_hours": calculated_hours,
            "base_hours": base_hours,
            "co_hours": co_hours,
            "day_entries": day_entries,
            "last_payment": last_payment,
            "savings_balance": savings_balance,
        })

    # Calcular totales
    total_hours = sum(data["calculated_hours"] for data in employee_data)
    total_payroll = sum(data["record"].total_pay or Decimal("0") for data in employee_data)
    total_paid = sum(data["record"].amount_paid() for data in employee_data)
    balance_due = total_payroll - total_paid

    context = {
        "period": period,
        "week_start": week_start,
        "week_end": week_end,
        "prev_week": prev_week,
        "next_week": next_week,
        "days": days,
        "employee_data": employee_data,
        "total_hours": total_hours,
        "total_payroll": total_payroll,
        "total_paid": total_paid,
        "balance_due": balance_due,
    }

    return render(request, "core/payroll_weekly_review.html", context)


@login_required
def payroll_record_payment(request, record_id):
    """
    Registrar un pago (parcial o completo) para un PayrollRecord.
    Soporta pagos con ahorro - el empleado puede llevarse menos y dejar el resto.
    SOLO ACCESIBLE POR ADMIN/SUPERUSER
    """
    guard = _require_admin_or_redirect(request)
    if guard:
        return guard

    record = get_object_or_404(PayrollRecord, id=record_id)

    if request.method == "POST":
        amount = request.POST.get("amount")
        amount_taken = request.POST.get("amount_taken")
        amount_saved = request.POST.get("amount_saved", "0")
        payment_date = request.POST.get("payment_date")
        payment_method = request.POST.get("payment_method", "check")
        check_number = request.POST.get("check_number", "")
        reference = request.POST.get("reference", "")
        notes = request.POST.get("notes", "")

        if amount and payment_date:
            try:
                total_amount = Decimal(amount)
                taken = Decimal(amount_taken) if amount_taken else total_amount
                saved = Decimal(amount_saved) if amount_saved else Decimal("0")
                
                # Validate: amount_taken + amount_saved should equal total amount
                if taken + saved != total_amount:
                    messages.error(
                        request,
                        _("Amount taken ($%(taken)s) + Amount saved ($%(saved)s) must equal Total ($%(total)s)")
                        % {"taken": taken, "saved": saved, "total": total_amount}
                    )
                    return redirect(request.path)
                
                PayrollPayment.objects.create(
                    payroll_record=record,
                    amount=total_amount,
                    amount_taken=taken,
                    amount_saved=saved,
                    payment_date=payment_date,
                    payment_method=payment_method,
                    check_number=check_number,
                    reference=reference,
                    notes=notes,
                    recorded_by=request.user,
                )

                if saved > 0:
                    messages.success(
                        request,
                        _("Payment recorded: $%(taken)s paid to %(employee)s, $%(saved)s saved.")
                        % {"taken": taken, "employee": record.employee, "saved": saved},
                    )
                else:
                    messages.success(
                        request,
                        _("Payment of $%(amount)s recorded for %(employee)s.")
                        % {"amount": total_amount, "employee": record.employee},
                    )
            except Exception as e:
                messages.error(request, f"Error processing payment: {str(e)}")
                return redirect(request.path)

            # Redirigir de vuelta a la revisión semanal
            return redirect("payroll_weekly_review")
        else:
            messages.error(request, _("Monto y fecha de pago son requeridos."))

    return render(
        request,
        "core/payroll_payment_form.html",
        {
            "record": record,
        },
    )


@login_required
def payroll_payment_history(request, employee_id=None):
    """
    Historial de pagos de nómina. Si se especifica employee_id, muestra solo ese empleado.
    SOLO ACCESIBLE POR ADMIN/SUPERUSER
    """
    guard = _require_admin_or_redirect(request)
    if guard:
        return guard

    if employee_id:
        employee = get_object_or_404(Employee, id=employee_id)
        records = PayrollRecord.objects.filter(employee=employee).order_by("-week_start")
    else:
        employee = None
        records = PayrollRecord.objects.select_related("employee").all().order_by("-week_start", "employee__last_name")

    # Agregar datos de pagos a cada registro
    records_data = []
    for record in records:
        payments = record.payments.all()
        records_data.append(
            {
                "record": record,
                "payments": payments,
                "amount_paid": record.amount_paid(),
                "balance_due": record.balance_due(),
            }
        )

    context = {
        "employee": employee,
        "records_data": records_data,
    }

    return render(request, "core/payroll_payment_history.html", context)


@login_required
def employee_savings_ledger(request, employee_id=None):
    """
    Vista del ledger de ahorros de empleados.
    Muestra el balance actual y historial de transacciones para cada empleado.
    Permite registrar retiros.
    SOLO ACCESIBLE POR ADMIN/SUPERUSER
    """
    from core.models import EmployeeSavings
    from decimal import Decimal
    
    guard = _require_admin_or_redirect(request)
    if guard:
        return guard
    
    # Si se especifica employee_id, mostrar solo ese empleado
    if employee_id:
        employee = get_object_or_404(Employee, id=employee_id)
        bal = EmployeeSavings.get_employee_balance(employee)
        employees_data = [{
            'employee': employee,
            'balance': bal,
            'abs_balance': abs(bal),
            'ledger': EmployeeSavings.get_employee_ledger(employee),
        }]
    else:
        # Mostrar todos los empleados activos con ahorros
        employees = Employee.objects.filter(is_active=True).order_by('last_name', 'first_name')
        employees_data = []
        
        for emp in employees:
            balance = EmployeeSavings.get_employee_balance(emp)
            # Solo mostrar empleados con historial de ahorros
            has_savings = EmployeeSavings.objects.filter(employee=emp).exists()
            if has_savings or balance > 0:
                employees_data.append({
                    'employee': emp,
                    'balance': balance,
                    'abs_balance': abs(balance),
                    'ledger': EmployeeSavings.get_employee_ledger(emp),
                })
    
    # Calcular totales
    total_balance = sum(data['balance'] for data in employees_data)
    total_employees_with_savings = len([d for d in employees_data if d['balance'] > 0])
    
    # Handle POST: registrar retiro
    if request.method == "POST":
        action = request.POST.get("action")
        
        if action == "withdrawal":
            emp_id = request.POST.get("employee_id")
            amount = request.POST.get("amount")
            notes = request.POST.get("notes", "")
            withdrawal_date = request.POST.get("date")
            
            if emp_id and amount and withdrawal_date:
                try:
                    emp = Employee.objects.get(id=emp_id)
                    withdrawal_amount = Decimal(amount)
                    current_balance = EmployeeSavings.get_employee_balance(emp)
                    
                    # Allow overdraft — balance can go negative
                    # Only block if user didn't confirm the overdraft
                    if withdrawal_amount > current_balance and request.POST.get("confirm_overdraft") != "yes":
                        messages.warning(
                            request,
                            _("%(employee)s only has $%(balance)s saved. "
                              "Use the confirmation checkbox to allow a withdrawal of $%(amount)s (balance will be -$%(deficit)s).")
                            % {
                                "employee": f"{emp.first_name} {emp.last_name}",
                                "balance": current_balance,
                                "amount": withdrawal_amount,
                                "deficit": withdrawal_amount - current_balance,
                            }
                        )
                    else:
                        is_overdraft = withdrawal_amount > current_balance
                        note_prefix = "[OVERDRAFT] " if is_overdraft else ""
                        EmployeeSavings.objects.create(
                            employee=emp,
                            amount=withdrawal_amount,
                            transaction_type='withdrawal',
                            date=withdrawal_date,
                            notes=note_prefix + (notes or "Cash withdrawal"),
                            recorded_by=request.user,
                        )
                        new_balance = current_balance - withdrawal_amount
                        if is_overdraft:
                            messages.warning(
                                request,
                                _("Withdrawal of $%(amount)s recorded for %(employee)s. "
                                  "⚠️ Balance is now -$%(deficit)s (employee owes money).")
                                % {
                                    "amount": withdrawal_amount,
                                    "employee": f"{emp.first_name} {emp.last_name}",
                                    "deficit": abs(new_balance),
                                }
                            )
                        else:
                            messages.success(
                                request,
                                _("Withdrawal of $%(amount)s recorded for %(employee)s. Balance: $%(balance)s")
                                % {
                                    "amount": withdrawal_amount,
                                    "employee": f"{emp.first_name} {emp.last_name}",
                                    "balance": new_balance,
                                }
                            )
                except Employee.DoesNotExist:
                    messages.error(request, _("Employee not found."))
                except Exception as e:
                    messages.error(request, f"Error: {str(e)}")
                
                return redirect("employee_savings_ledger")
        
        elif action == "adjustment":
            emp_id = request.POST.get("employee_id")
            amount = request.POST.get("amount")
            notes = request.POST.get("notes", "")
            adjustment_date = request.POST.get("date")
            
            if emp_id and amount and adjustment_date:
                try:
                    emp = Employee.objects.get(id=emp_id)
                    EmployeeSavings.objects.create(
                        employee=emp,
                        amount=Decimal(amount),  # Can be positive or negative
                        transaction_type='adjustment',
                        date=adjustment_date,
                        notes=notes or "Manual adjustment",
                        recorded_by=request.user,
                    )
                    messages.success(
                        request,
                        _("Adjustment recorded for %(employee)s.")
                        % {"employee": f"{emp.first_name} {emp.last_name}"}
                    )
                except Exception as e:
                    messages.error(request, f"Error: {str(e)}")
                
                return redirect("employee_savings_ledger")

        elif action == "delete_record":
            record_id = request.POST.get("record_id")
            if record_id:
                try:
                    record = EmployeeSavings.objects.get(id=record_id)
                    emp_name = f"{record.employee.first_name} {record.employee.last_name}"
                    txn_type = record.get_transaction_type_display()
                    amount = record.amount
                    record.delete()
                    messages.success(
                        request,
                        _("Deleted %(type)s of $%(amount)s for %(employee)s.")
                        % {"type": txn_type, "amount": amount, "employee": emp_name}
                    )
                except EmployeeSavings.DoesNotExist:
                    messages.error(request, _("Record not found."))
                except Exception as e:
                    messages.error(request, f"Error: {str(e)}")

                return redirect("employee_savings_ledger")
    
    # Get all active employees for dropdown (with balances for withdrawal modal)
    all_employees = Employee.objects.filter(is_active=True).order_by('last_name', 'first_name')
    employee_balances = {}
    for emp in all_employees:
        employee_balances[emp.id] = float(EmployeeSavings.get_employee_balance(emp))

    # Count negative balances
    negative_balance_count = len([d for d in employees_data if d['balance'] < 0])
    total_negative = abs(sum(d['balance'] for d in employees_data if d['balance'] < 0))
    
    # Determine selected employee for context
    selected_employee = None
    if employee_id:
        selected_employee = get_object_or_404(Employee, id=employee_id)
    
    context = {
        "employees_data": employees_data,
        "total_balance": total_balance,
        "total_employees_with_savings": total_employees_with_savings,
        "negative_balance_count": negative_balance_count,
        "total_negative": total_negative,
        "all_employees": all_employees,
        "employee_balances": employee_balances,
        "selected_employee": selected_employee,
    }
    
    return render(request, "core/employee_savings_ledger.html", context)


