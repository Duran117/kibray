"""Expense, income, and time entry views — CRUD."""
from core.views._helpers import *  # noqa: F401, F403
from core.views._helpers import (
    _generate_basic_pdf_from_html,
    _check_user_project_access,
    _is_admin_user,
    _is_pm_or_admin,
    _is_staffish,
    _require_admin_or_redirect,
    _require_roles,
    _parse_date,
    _ensure_inventory_item,
    staff_required,
    logger,
    pisa,
    ROLES_ADMIN,
    ROLES_PM,
    ROLES_STAFF,
    ROLES_FIELD,
    ROLES_ALL_INTERNAL,
    ROLES_CLIENT_SIDE,
    ROLES_PROJECT_ACCESS,
)
from django.utils.translation import gettext_lazy as _  # noqa: F811


# --- CRUD SCHEDULE, EXPENSE, INCOME, TIMEENTRY ---
@login_required
def expense_create_view(request):
    profile = getattr(request.user, "profile", None)
    role = getattr(profile, "role", "employee")
    # Allow Django superusers and staff automatically
    if not (
        request.user.is_superuser
        or request.user.is_staff
        or role in ROLES_STAFF
    ):
        return redirect("dashboard")

    if request.method == "POST":
        form = ExpenseForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect("dashboard")
    else:
        form = ExpenseForm()
    
    # Pass projects and change_orders for dynamic filtering
    projects = Project.objects.all().order_by('name')
    change_orders = ChangeOrder.objects.select_related('project').all().order_by('project__name', 'id')
    cost_codes = CostCode.objects.filter(active=True).order_by('code')
    
    return render(request, "core/expense_form.html", {
        "form": form,
        "projects": projects,
        "change_orders": change_orders,
        "cost_codes": cost_codes,
    })



@login_required
def income_create_view(request):
    profile = getattr(request.user, "profile", None)
    role = getattr(profile, "role", "employee")
    # Allow Django superusers and staff automatically
    if not (
        request.user.is_superuser
        or request.user.is_staff
        or role in ROLES_STAFF
    ):
        return redirect("dashboard")

    if request.method == "POST":
        form = IncomeForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect("dashboard")
    else:
        form = IncomeForm()
    return render(request, "core/income_form.html", {"form": form})



@login_required
def income_list(request):
    from core.models import Income

    profile = getattr(request.user, "profile", None)
    role = getattr(profile, "role", "employee")
    if role not in ["admin", "superuser", "project_manager"] and not request.user.is_staff:
        return redirect("dashboard")
    qs = Income.objects.select_related("project").all().order_by("-date")
    project_id = request.GET.get("project")
    if project_id:
        qs = qs.filter(project_id=project_id)
    return render(request, "core/income_list.html", {"incomes": qs})



@login_required
def income_edit_view(request, income_id):
    from core.models import Income

    income = get_object_or_404(Income, id=income_id)
    profile = getattr(request.user, "profile", None)
    role = getattr(profile, "role", "employee")
    if role not in ["admin", "superuser", "project_manager"] and not request.user.is_staff:
        messages.error(request, _("Acceso denegado."))
        return redirect("income_list")
    if request.method == "POST":
        form = IncomeForm(request.POST, request.FILES, instance=income)
        if form.is_valid():
            form.save()
            messages.success(request, _("Ingreso actualizado."))
            return redirect("income_list")
    else:
        form = IncomeForm(instance=income)
    return render(request, "core/income_form.html", {"form": form, "income": income})



@login_required
def income_delete_view(request, income_id):
    from core.models import Income

    income = get_object_or_404(Income, id=income_id)
    profile = getattr(request.user, "profile", None)
    role = getattr(profile, "role", "employee")
    if role not in ["admin", "superuser", "project_manager"] and not request.user.is_staff:
        messages.error(request, _("Acceso denegado."))
        return redirect("income_list")
    if request.method == "POST":
        income.delete()
        messages.success(request, _("Ingreso eliminado."))
        return redirect("income_list")
    return render(request, "core/income_confirm_delete.html", {"income": income})



@login_required
def expense_list(request):
    from core.models import Expense

    profile = getattr(request.user, "profile", None)
    role = getattr(profile, "role", "employee")
    if role not in ["admin", "superuser", "project_manager"] and not request.user.is_staff:
        return redirect("dashboard")
    qs = Expense.objects.select_related("project").all().order_by("-date")
    project_id = request.GET.get("project")
    if project_id:
        qs = qs.filter(project_id=project_id)
    return render(request, "core/expense_list.html", {"expenses": qs})



@login_required
def expense_edit_view(request, expense_id):
    from core.models import Expense

    expense = get_object_or_404(Expense, id=expense_id)
    profile = getattr(request.user, "profile", None)
    role = getattr(profile, "role", "employee")
    if role not in ["admin", "superuser", "project_manager"] and not request.user.is_staff:
        messages.error(request, _("Acceso denegado."))
        return redirect("expense_list")
    if request.method == "POST":
        form = ExpenseForm(request.POST, request.FILES, instance=expense)
        if form.is_valid():
            form.save()
            messages.success(request, _("Gasto actualizado."))
            return redirect("expense_list")
    else:
        form = ExpenseForm(instance=expense)
    
    # Pass projects and change_orders for dynamic filtering (same as create view)
    projects = Project.objects.all().order_by('name')
    change_orders = ChangeOrder.objects.select_related('project').all().order_by('project__name', 'id')
    cost_codes = CostCode.objects.filter(active=True).order_by('code')
    
    return render(request, "core/expense_form.html", {
        "form": form,
        "expense": expense,
        "projects": projects,
        "change_orders": change_orders,
        "cost_codes": cost_codes,
    })



@login_required
def expense_delete_view(request, expense_id):
    from core.models import Expense

    expense = get_object_or_404(Expense, id=expense_id)
    profile = getattr(request.user, "profile", None)
    role = getattr(profile, "role", "employee")
    if role not in ["admin", "superuser", "project_manager"] and not request.user.is_staff:
        messages.error(request, _("Acceso denegado."))
        return redirect("expense_list")
    if request.method == "POST":
        expense.delete()
        messages.success(request, _("Gasto eliminado."))
        return redirect("expense_list")
    return render(request, "core/expense_confirm_delete.html", {"expense": expense})



@login_required
def timeentry_create_view(request):
    if request.method == "POST":
        form = TimeEntryForm(request.POST)
        if form.is_valid():
            entry = form.save(commit=False)
            # Support both legacy related name 'employee' and current 'employee_profile'
            from core.models import Employee

            emp = getattr(request.user, "employee_profile", None) or getattr(
                request.user, "employee", None
            )
            if emp is None:
                emp = Employee.objects.filter(user=request.user).first()
            entry.employee = emp
            entry.save()
            messages.success(request, _("Horas registradas."))
            return redirect("dashboard")
    else:
        form = TimeEntryForm()
    return render(request, "core/timeentry_form.html", {"form": form})



@login_required
def timeentry_edit_view(request, entry_id: int):
    """Edit an existing TimeEntry. Allowed for staff/PM or the owning employee's user."""
    from core.models import TimeEntry

    entry = get_object_or_404(TimeEntry, id=entry_id)

    # Permissions: staff/pm or owner
    profile = getattr(request.user, "profile", None)
    role = getattr(profile, "role", "employee")
    is_staff_pm = role in ROLES_STAFF or request.user.is_staff
    is_owner = bool(getattr(entry.employee, "user_id", None) == request.user.id)
    if not (is_staff_pm or is_owner):
        messages.error(request, _("Acceso denegado."))
        return redirect("dashboard")

    if request.method == "POST":
        form = TimeEntryForm(request.POST, instance=entry)
        if form.is_valid():
            form.save()
            messages.success(request, _("Registro de horas actualizado."))
            return redirect("dashboard")
    else:
        form = TimeEntryForm(instance=entry)
    return render(request, "core/timeentry_form.html", {"form": form, "timeentry": entry})



@login_required
def timeentry_delete_view(request, entry_id: int):
    """Delete a TimeEntry with confirmation. Same permissions as edit."""
    from core.models import TimeEntry

    entry = get_object_or_404(TimeEntry, id=entry_id)

    profile = getattr(request.user, "profile", None)
    role = getattr(profile, "role", "employee")
    is_staff_pm = role in ROLES_STAFF or request.user.is_staff
    is_owner = bool(getattr(entry.employee, "user_id", None) == request.user.id)
    if not (is_staff_pm or is_owner):
        messages.error(request, _("Acceso denegado."))
        return redirect("dashboard")

    if request.method == "POST":
        entry.delete()
        messages.success(request, _("Registro de horas eliminado."))
        return redirect("dashboard")
    return render(request, "core/timeentry_confirm_delete.html", {"timeentry": entry})



@login_required
def manual_timeentry_create(request):
    """
    Admin view to manually create TimeEntry for any employee.
    Used when employee forgot to check in/out.
    SOLO ACCESIBLE POR ADMIN/SUPERUSER
    """
    from core.models import Employee, Project, ChangeOrder, TimeEntry
    from decimal import Decimal
    from datetime import datetime
    
    guard = _require_admin_or_redirect(request)
    if guard:
        return guard
    
    employees = Employee.objects.filter(is_active=True).order_by('last_name', 'first_name')
    projects = Project.objects.filter(is_archived=False).order_by('name')
    change_orders = ChangeOrder.objects.filter(status='approved').select_related("project").order_by('-date_created')[:100]
    
    if request.method == "POST":
        employee_id = request.POST.get("employee_id")
        project_id = request.POST.get("project_id")
        change_order_id = request.POST.get("change_order_id")
        entry_date = request.POST.get("date")
        start_time = request.POST.get("start_time")
        end_time = request.POST.get("end_time")
        notes = request.POST.get("notes", "")
        
        if employee_id and entry_date and start_time and end_time:
            try:
                emp = Employee.objects.get(id=employee_id)
                
                # Parse times
                start_t = datetime.strptime(start_time, "%H:%M").time()
                end_t = datetime.strptime(end_time, "%H:%M").time()
                
                # Calculate hours
                start_mins = start_t.hour * 60 + start_t.minute
                end_mins = end_t.hour * 60 + end_t.minute
                if end_mins < start_mins:  # Overnight shift
                    end_mins += 24 * 60
                hours_worked = Decimal(str((end_mins - start_mins) / 60.0))
                
                # Create entry
                entry = TimeEntry(
                    employee=emp,
                    date=entry_date,
                    start_time=start_t,
                    end_time=end_t,
                    hours_worked=hours_worked,
                    notes=f"[Manual entry by {request.user.username}] {notes}".strip(),
                )
                
                # Assign project if provided
                if project_id:
                    entry.project = Project.objects.get(id=project_id)
                
                # Assign CO if provided
                if change_order_id:
                    entry.change_order = ChangeOrder.objects.get(id=change_order_id)
                
                entry.save()
                
                messages.success(
                    request,
                    _("Time entry created: %(employee)s - %(hours)s hours on %(date)s")
                    % {
                        "employee": f"{emp.first_name} {emp.last_name}",
                        "hours": hours_worked,
                        "date": entry_date,
                    }
                )
                
                # Redirect back with week_start to stay on same week
                # Calculate week start from entry date
                from datetime import timedelta
                entry_date_obj = datetime.strptime(entry_date, "%Y-%m-%d").date()
                week_start = entry_date_obj - timedelta(days=entry_date_obj.weekday())
                
                return redirect(f"/payroll/week/?week_start={week_start.isoformat()}")
                
            except Employee.DoesNotExist:
                messages.error(request, _("Employee not found."))
            except Project.DoesNotExist:
                messages.error(request, _("Project not found."))
            except ChangeOrder.DoesNotExist:
                messages.error(request, _("Change Order not found."))
            except Exception as e:
                messages.error(request, f"Error creating time entry: {str(e)}")
        else:
            messages.error(request, _("Employee, date, start time, and end time are required."))
    
    # Get default date from query param or today
    default_date = request.GET.get("date", datetime.now().strftime("%Y-%m-%d"))
    default_employee = request.GET.get("employee_id", "")
    
    context = {
        "employees": employees,
        "projects": projects,
        "change_orders": change_orders,
        "default_date": default_date,
        "default_employee": default_employee,
    }
    
    return render(request, "core/manual_timeentry_form.html", context)



@login_required
def unassigned_timeentries_view(request):
    """Lista de TimeEntries sin change_order para asignación masiva por PM/admin."""
    profile = getattr(request.user, "profile", None)
    role = getattr(profile, "role", "employee")
    if role not in ["admin", "superuser", "project_manager"]:
        return redirect("dashboard")

    # Filtros
    project_id = request.GET.get("project")
    employee_id = request.GET.get("employee")
    date_from = request.GET.get("from")
    date_to = request.GET.get("to")

    qs = (
        TimeEntry.objects.filter(change_order__isnull=True)
        .select_related("employee", "project")
        .order_by("-date")
    )
    if project_id:
        qs = qs.filter(project_id=project_id)
    if employee_id:
        qs = qs.filter(employee_id=employee_id)
    if date_from:
        qs = qs.filter(date__gte=date_from)
    if date_to:
        qs = qs.filter(date__lte=date_to)

    # Bulk assign
    if request.method == "POST":
        action = request.POST.get("action")
        selected_ids = request.POST.getlist("selected")
        co_id = request.POST.get("change_order_id")
        if action == "assign" and selected_ids and co_id:
            co = get_object_or_404(ChangeOrder, id=co_id)
            # Validar que todas las filas seleccionadas pertenezcan al proyecto del CO
            diff = (
                TimeEntry.objects.filter(id__in=selected_ids).exclude(project=co.project).exists()
            )
            if diff:
                messages.error(
                    request, _("Selecciona registros del mismo proyecto que el CO elegido.")
                )
                return redirect(request.get_full_path())
            updated = TimeEntry.objects.filter(
                id__in=selected_ids, change_order__isnull=True
            ).update(change_order=co)
            messages.success(
                request,
                _("%(count)s registros asignados al CO #%(co_id)s.")
                % {"count": updated, "co_id": co.id},
            )
            return redirect(request.get_full_path())
        elif action == "create_and_assign" and selected_ids:
            # Crear un nuevo CO rápido
            project_for_new = None
            # Intentar tomar el proyecto de la primera time entry válida
            first_te = (
                TimeEntry.objects.filter(id__in=selected_ids).select_related("project").first()
            )
            if first_te and first_te.project:
                project_for_new = first_te.project
            if not project_for_new:
                messages.error(
                    request,
                    _("No se puede crear CO sin proyecto asociado en los registros seleccionados."),
                )
            else:
                # validar que todos pertenecen al mismo proyecto
                mixed = (
                    TimeEntry.objects.filter(id__in=selected_ids)
                    .exclude(project=project_for_new)
                    .exists()
                )
                if mixed:
                    messages.error(request, _("Para crear CO, selecciona filas de un solo proyecto."))
                    return redirect(request.get_full_path())
                description = request.POST.get("new_co_description", "Trabajo adicional")
                amount = request.POST.get("new_co_amount") or "0"
                try:
                    amt = Decimal(amount)
                except Exception:
                    amt = Decimal("0")
                co = ChangeOrder.objects.create(
                    project=project_for_new, description=description, amount=amt, status="pending"
                )
                updated = TimeEntry.objects.filter(
                    id__in=selected_ids, change_order__isnull=True
                ).update(change_order=co)
                messages.success(
                    request,
                    _("CO #%(co_id)s creado y %(count)s registros asignados.")
                    % {"co_id": co.id, "count": updated},
                )
            return redirect(request.get_full_path())

    # Paginación ligera (tolerante a valores inválidos)
    try:
        page_size = int(request.GET.get("ps", 50))
    except (TypeError, ValueError):
        page_size = 50
    if page_size <= 0:
        page_size = 50
    if page_size > 500:
        page_size = 500
    paginator = Paginator(qs, page_size)
    page_obj = paginator.get_page(request.GET.get("page"))

    projects = Project.objects.all().order_by("name")
    employees = Employee.objects.filter(is_active=True).order_by("last_name")
    change_orders = ChangeOrder.objects.filter(status__in=["pending", "approved", "sent"]).select_related("project").order_by(
        "-date_created"
    )
    if project_id:
        change_orders = change_orders.filter(project_id=project_id)
    change_orders = change_orders[:200]

    return render(
        request,
        "core/unassigned_timeentries.html",
        {
            "page_obj": page_obj,
            "projects": projects,
            "employees": employees,
            "change_orders": change_orders,
            "filters": {
                "project_id": project_id,
                "employee_id": employee_id,
                "date_from": date_from,
                "date_to": date_to,
                "page_size": page_size,
            },
            "page_sizes": [25, 50, 100],
        },
    )

