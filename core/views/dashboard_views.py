"""Dashboard views — admin, client, employee, PM, designer, superintendent."""
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


# --- DASHBOARD ADMIN (COMPLETO) ---
@login_required
def dashboard_admin(request):
    """Dashboard completo para Admin con todas las métricas, alertas y aprobaciones"""
    # SECURITY: Only superusers and users with admin role can access
    profile = getattr(request.user, "profile", None)
    role = getattr(profile, "role", None) if profile else None
    if not (request.user.is_superuser or role == "admin"):
        return HttpResponseForbidden("Forbidden")

    # Respect session language hint for legacy rendering (used by i18n tests)
    session_lang = request.session.get("lang")
    if session_lang:
        translation.activate(session_lang)
        request.LANGUAGE_CODE = session_lang

    today = timezone.localdate()
    now = timezone.localtime()

    # Obtener empleado ligado al usuario (para Admin que también es empleado)
    employee = Employee.objects.filter(user=request.user).first()

    # TimeEntry abierto (si está trabajando) - Solo si hay empleado vinculado
    open_entry = None
    if employee:
        open_entry = (
            TimeEntry.objects.filter(employee=employee, end_time__isnull=True).select_related("project", "change_order")
            .order_by("-date", "-start_time")
            .first()
        )

    # Manejo de Clock In/Out para Admins
    if request.method == "POST" and employee:
        action = request.POST.get("action")

        if action == "clock_in":
            if open_entry:
                messages.warning(request, _("You already have an open entry. Clock out first."))
                return redirect("dashboard_admin")
            form = ClockInForm(request.POST)
            if form.is_valid():
                TimeEntry.objects.create(
                    employee=employee,
                    project=form.cleaned_data["project"],
                    change_order=form.cleaned_data.get("change_order"),
                    budget_line=form.cleaned_data.get("budget_line"),  # Nueva línea
                    date=today,
                    start_time=now.time(),
                    end_time=None,
                    notes=form.cleaned_data.get("notes") or "",
                    cost_code=form.cleaned_data.get("cost_code"),
                )
                messages.success(
                    request,
                    _("✓ Clocked in at %(time)s.") % {"time": now.strftime("%H:%M")},
                )
                return redirect("dashboard_admin")

        elif action == "clock_out":
            if not open_entry:
                messages.warning(request, _("You don't have an open entry."))
                return redirect("dashboard_admin")
            open_entry.end_time = now.time()
            open_entry.save()
            messages.success(
                request,
                _("✓ Clocked out at %(time)s. Hours: %(hours)s") % {"time": now.strftime("%H:%M"), "hours": open_entry.hours_worked},
            )
            return redirect("dashboard_admin")

        elif action == "switch_context" and open_entry:
            # CORRECCIÓN: Cerrar entrada actual y crear nueva para registrar tiempo correctamente
            switch_type = request.POST.get("switch_type")
            current_time = now.time()
            
            # Guardar datos de la entrada actual
            old_project = open_entry.project
            old_co = open_entry.change_order
            
            if switch_type == "base":
                # Cerrar entrada actual y crear nueva sin CO
                open_entry.end_time = current_time
                open_entry.save()
                
                TimeEntry.objects.create(
                    employee=employee,
                    project=old_project,
                    change_order=None,
                    budget_line=open_entry.budget_line,
                    date=today,
                    start_time=current_time,
                    end_time=None,
                    notes=f"Switched from CO: {old_co.title if old_co else 'N/A'}",
                    cost_code=open_entry.cost_code,
                )
                messages.success(
                    request,
                    _("✓ Entry closed (%(hours)s hrs). Now on base work. Previously: %(co)s")
                    % {"hours": open_entry.hours_worked, "co": old_co.title if old_co else "N/A"},
                )
                
            elif switch_type == "co":
                target_id = request.POST.get("target_id") or request.POST.get("co_id")
                if target_id:
                    try:
                        new_co = ChangeOrder.objects.get(
                            id=target_id,
                            project=open_entry.project,
                            status__in=['draft', 'pending', 'approved', 'sent', 'billed']
                        )
                        open_entry.end_time = current_time
                        open_entry.save()
                        
                        TimeEntry.objects.create(
                            employee=employee,
                            project=old_project,
                            change_order=new_co,
                            budget_line=None,
                            date=today,
                            start_time=current_time,
                            end_time=None,
                            notes=f"Switched from: {old_co.title if old_co else 'Base work'}",
                            cost_code=open_entry.cost_code,
                        )
                        messages.success(
                            request,
                            _("✓ Entry closed (%(hours)s hrs). Now on %(co)s (%(type)s)")
                            % {"hours": open_entry.hours_worked, "co": new_co.title, "type": new_co.get_pricing_type_display()},
                        )
                    except ChangeOrder.DoesNotExist:
                        messages.error(request, _("Change Order not found or not available."))
                        
            elif switch_type == "project":
                target_id = request.POST.get("target_id") or request.POST.get("project_id")
                if target_id:
                    try:
                        new_project = Project.objects.get(id=target_id)
                        
                        # Cerrar entrada actual
                        open_entry.end_time = current_time
                        open_entry.save()
                        
                        # Verificar que hours_worked se calculó correctamente
                        if open_entry.hours_worked is None or open_entry.hours_worked == 0:
                            logger.warning(
                                f"[Switch Project] hours_worked=0 for entry {open_entry.id}. "
                                f"start={open_entry.start_time}, end={open_entry.end_time}"
                            )
                            # Recalcular manualmente
                            open_entry.refresh_from_db()
                            if open_entry.hours_worked is None or open_entry.hours_worked == 0:
                                # Forzar recálculo
                                if open_entry.start_time and open_entry.end_time:
                                    s = open_entry.start_time.hour * 60 + open_entry.start_time.minute
                                    e = open_entry.end_time.hour * 60 + open_entry.end_time.minute
                                    if e < s:
                                        e += 24 * 60
                                    minutes = e - s
                                    hours = Decimal(minutes) / Decimal(60)
                                    if hours >= Decimal("5.0"):
                                        lunch_min = 12 * 60 + 30
                                        if s < lunch_min <= e:
                                            hours -= Decimal("0.5")
                                    open_entry.hours_worked = hours.quantize(Decimal("0.01"))
                                    open_entry.save(update_fields=['hours_worked'])
                                    logger.info(f"[Switch Project] Forced recalc: {hours}h")
                        
                        TimeEntry.objects.create(
                            employee=employee,
                            project=new_project,
                            change_order=None,
                            budget_line=None,
                            date=today,
                            start_time=current_time,
                            end_time=None,
                            notes=f"Switched from project: {old_project.name}",
                            cost_code=None,
                        )
                        messages.success(
                            request,
                            _("✓ Entry closed (%(hours)s hrs on %(old)s). Now on %(proj)s")
                            % {"hours": open_entry.hours_worked, "old": old_project.name, "proj": new_project.name},
                        )
                    except Project.DoesNotExist:
                        messages.error(request, _("Project not found."))

            elif switch_type == "project_co":
                # Switch project AND set a specific CO in one step (from wizard)
                target_id = request.POST.get("target_id") or request.POST.get("project_id")
                co_id = request.POST.get("co_id")
                if target_id:
                    try:
                        new_project = Project.objects.get(id=target_id)
                        new_co = None
                        if co_id:
                            new_co = ChangeOrder.objects.get(
                                id=co_id, project=new_project,
                                status__in=['draft', 'pending', 'approved', 'sent', 'billed']
                            )
                        open_entry.end_time = current_time
                        open_entry.save()
                        TimeEntry.objects.create(
                            employee=employee,
                            project=new_project,
                            change_order=new_co,
                            budget_line=None,
                            date=today,
                            start_time=current_time,
                            end_time=None,
                            notes=f"Switched from: {old_project.name}" + (f" to CO: {new_co.title}" if new_co else ""),
                            cost_code=None,
                        )
                        msg = _("✓ Entry closed (%(hours)s hrs). Now on %(proj)s") % {
                            "hours": open_entry.hours_worked, "proj": new_project.name
                        }
                        if new_co:
                            msg += f" — {new_co.title}"
                        messages.success(request, msg)
                    except (Project.DoesNotExist, ChangeOrder.DoesNotExist):
                        messages.error(request, _("Project or Change Order not found."))

            return redirect("dashboard_admin")

    # Form para clock in
    form = ClockInForm() if employee else None

    # === MÉTRICAS FINANCIERAS (refactored to service) ===
    fa = FinancialAnalyticsService()
    kpis = fa.get_company_health_kpis()
    net_profit = Decimal(
        str(kpis.get("net_profit", 0))
    )  # maintain existing variable for template compatibility
    # Provide legacy totals for templates/tests expecting these context keys
    total_income = Project.objects.aggregate(t=Sum("total_income"))["t"] or Decimal("0")
    total_expense = Project.objects.aggregate(t=Sum("total_expenses"))["t"] or Decimal("0")

    # === ALERTAS CRÍTICAS ===
    # 1. TimeEntries sin CO asignar
    unassigned_time_count = TimeEntry.objects.filter(change_order__isnull=True).count()
    unassigned_time_hours = TimeEntry.objects.filter(change_order__isnull=True).aggregate(
        total=Sum("hours_worked")
    )["total"] or Decimal("0")

    # 2. Solicitudes Cliente pendientes
    from core.models import ClientRequest

    pending_client_requests = ClientRequest.objects.filter(status="pending").count()

    # 3. Nómina pendiente (periodos aprobados pero no pagados completamente)
    pending_payroll = (
        PayrollPeriod.objects.filter(status="approved")
        .exclude(records__payments__isnull=False)
        .distinct()
        .count()
    )

    # 4. Facturas pendientes de pago
    pending_invoices = Invoice.objects.filter(
        status__in=["SENT", "VIEWED", "APPROVED", "PARTIAL"]
    ).count()
    pending_invoice_amount = Invoice.objects.filter(
        status__in=["SENT", "VIEWED", "APPROVED", "PARTIAL"]
    ).aggregate(total=Sum("total_amount"))["total"] or Decimal("0")

    # 5. COs pendientes de aprobación
    pending_cos = ChangeOrder.objects.filter(status="pending").count()

    # === PROYECTOS CON ALERTAS EV ===
    today = timezone.localdate()
    projects_with_alerts = []

    for project in Project.objects.filter(end_date__isnull=True).order_by("name"):
        try:
            metrics = compute_project_ev(project, as_of=today)
            alerts = []

            # SPI < 0.9: retraso en cronograma
            if metrics and metrics.get("SPI") and metrics["SPI"] < 0.9:
                alerts.append(("danger", f"Retraso crítico (SPI: {metrics['SPI']})"))
            elif metrics and metrics.get("SPI") and metrics["SPI"] < 1.0:
                alerts.append(("warning", f"Leve retraso (SPI: {metrics['SPI']})"))

            # CPI < 0.9: sobrecosto
            if metrics and metrics.get("CPI") and metrics["CPI"] < 0.9:
                alerts.append(("danger", f"Sobrecosto crítico (CPI: {metrics['CPI']})"))
            elif metrics and metrics.get("CPI") and metrics["CPI"] < 1.0:
                alerts.append(("warning", f"Leve sobrecosto (CPI: {metrics['CPI']})"))

            # Presupuesto casi agotado
            if project.budget_total > 0:
                remaining_pct = (project.budget_remaining / project.budget_total) * 100
                if remaining_pct < 10:
                    alerts.append(
                        ("danger", f"Presupuesto crítico ({remaining_pct:.1f}% restante)")
                    )
                elif remaining_pct < 20:
                    alerts.append(("warning", f"Presupuesto bajo ({remaining_pct:.1f}% restante)"))

            if alerts:
                projects_with_alerts.append(
                    {"project": project, "alerts": alerts, "metrics": metrics}
                )
        except Exception:
            pass

    # === APROBACIONES PENDIENTES ===
    # COs pendientes detallados
    pending_cos_list = ChangeOrder.objects.filter(status="pending").select_related("project")[:10]

    # Solicitudes cliente detalladas
    pending_requests_list = ClientRequest.objects.filter(status="pending").select_related(
        "project", "created_by"
    )[:10]

    # Materiales pendientes orden
    pending_materials = MaterialRequest.objects.filter(status="submitted").count()

    # === NÓMINA ===
    # Último periodo y balance
    latest_payroll_period = PayrollPeriod.objects.order_by("-week_start").first()
    payroll_balance = latest_payroll_period.balance_due() if latest_payroll_period else Decimal("0")

    # === RESUMEN PROYECTOS ===
    active_projects = Project.objects.filter(end_date__isnull=True).count()
    completed_projects = Project.objects.filter(end_date__isnull=False).count()

    # === MÉTRICAS TIEMPO ===
    today_entries = TimeEntry.objects.filter(date=today).select_related("employee")
    today_hours = today_entries.aggregate(total=Sum("hours_worked"))["total"] or Decimal("0")
    today_labor_cost = sum(entry.labor_cost for entry in today_entries)

    week_start = today - timedelta(days=today.weekday())
    week_entries = TimeEntry.objects.filter(date__gte=week_start, date__lte=today)
    week_hours = week_entries.aggregate(total=Sum("hours_worked"))["total"] or Decimal("0")

    # Morning Briefing (executive summary)
    morning_briefing = []
    try:
        if unassigned_time_count > 0:
            morning_briefing.append(
                {
                    "text": _("%d time entries without Change Order require assignment")
                    % unassigned_time_count,
                    "severity": "danger" if unassigned_time_count >= 5 else "warning",
                    "action_url": reverse("unassigned_timeentries"),
                    "action_label": _("Assign"),
                    "category": "problems",
                }
            )
        if pending_client_requests > 0:
            morning_briefing.append(
                {
                    "text": _("%d client requests pending review") % pending_client_requests,
                    "severity": "info" if pending_client_requests < 5 else "warning",
                    "action_url": reverse("client_requests_list_all"),
                    "action_label": _("Review"),
                    "category": "approvals",
                }
            )
        if pending_cos > 0:
            morning_briefing.append(
                {
                    "text": _("%d change orders awaiting approval") % pending_cos,
                    "severity": "warning" if pending_cos < 3 else "danger",
                    "action_url": reverse("changeorder_board"),
                    "action_label": _("Approve"),
                    "category": "approvals",
                }
            )
        if pending_invoices > 0:
            morning_briefing.append(
                {
                    "text": _("%d invoices pending payment/processing") % pending_invoices,
                    "severity": "warning",
                    "action_url": reverse("invoice_payment_dashboard"),
                    "action_label": _("Payments"),
                    "category": "problems",
                }
            )
        # Touch-ups count (fetched later, but we need the count here)
        _touchup_count = Task.objects.filter(
            is_touchup=True, status__in=["Pending", "In Progress"]
        ).count()
        if _touchup_count > 0:
            morning_briefing.append(
                {
                    "text": _("%d touch-ups pending across projects") % _touchup_count,
                    "severity": "warning" if _touchup_count >= 5 else "info",
                    "action_url": reverse("task_command_center"),
                    "action_label": _("Review"),
                    "category": "problems",
                }
            )
    except Exception:
        morning_briefing = []

    # Apply filter to morning briefing
    active_filter = request.GET.get("filter", "all")
    if active_filter == "problems":
        morning_briefing = [item for item in morning_briefing if item.get("category") == "problems"]
    elif active_filter == "approvals":
        morning_briefing = [
            item for item in morning_briefing if item.get("category") == "approvals"
        ]

    active_lang = (
        session_lang or getattr(request, "LANGUAGE_CODE", None) or translation.get_language()
    )
    english_mode = str(active_lang or "").lower().startswith("en")

    # === SWITCH OPTIONS (para cambiar proyecto/CO cuando hay entrada abierta) ===
    switch_options = {"other_projects": [], "available_cos": [], "current_project_cos": [], "can_switch_to_base": False}
    if open_entry:
        # Otros proyectos (Admin puede ver todos, excluir el actual)
        other_projects = Project.objects.filter(is_archived=False).exclude(id=open_entry.project_id)[:10]
        switch_options["other_projects"] = [
            {"id": p.id, "name": p.name}
            for p in other_projects
        ]
        
        # COs del proyecto actual (disponibles para trabajo)
        # Incluir draft, pending, approved, sent, billed (excluir solo 'paid' que ya está cerrado)
        current_project_cos = ChangeOrder.objects.filter(
            project=open_entry.project,
            status__in=['draft', 'pending', 'approved', 'sent', 'billed']
        ).exclude(id=open_entry.change_order_id if open_entry.change_order else None)
        cos_list = [
            {"id": co.id, "title": co.title, "pricing_type": co.pricing_type, "pricing_label": f"${co.amount}" if co.pricing_type == 'fixed' else "T&M"}
            for co in current_project_cos
        ]
        switch_options["current_project_cos"] = cos_list
        switch_options["available_cos"] = cos_list
        
        # Puede volver a base si actualmente está en un CO
        switch_options["can_switch_to_base"] = open_entry.change_order is not None

    # === TOUCH-UPS PENDIENTES (cross-project para Admin) ===
    pending_touchups = (
        Task.objects.filter(
            is_touchup=True, status__in=["Pending", "In Progress"]
        )
        .select_related("project", "assigned_to")
        .order_by("-created_at")[:15]
    )
    pending_touchups_count = Task.objects.filter(
        is_touchup=True, status__in=["Pending", "In Progress"]
    ).count()

    context = {
        # Financiero
        "total_income": total_income,
        "total_expense": total_expense,
        "net_profit": net_profit,
        # Alertas
        "unassigned_time_count": unassigned_time_count,
        "unassigned_time_hours": unassigned_time_hours,
        "pending_client_requests": pending_client_requests,
        "pending_payroll": pending_payroll,
        "pending_invoices": pending_invoices,
        "pending_invoice_amount": pending_invoice_amount,
        "pending_cos": pending_cos,
        "pending_materials": pending_materials,
        # Touch-ups
        "pending_touchups": pending_touchups,
        "pending_touchups_count": pending_touchups_count,
        # Proyectos con alertas
        "projects_with_alerts": projects_with_alerts,
        # Aprobaciones
        "pending_cos_list": pending_cos_list,
        "pending_requests_list": pending_requests_list,
        # Nómina
        "latest_payroll_period": latest_payroll_period,
        "payroll_balance": payroll_balance,
        # Resumen proyectos
        "active_projects": active_projects,
        "completed_projects": completed_projects,
        # Tiempo
        "today_hours": today_hours,
        "today_labor_cost": today_labor_cost,
        "week_hours": week_hours,
        "today": today,
        "now": now,
        # Briefing
        "morning_briefing": morning_briefing,
        "active_filter": active_filter,
        # Clock in/out para Admin
        "employee": employee,
        "open_entry": open_entry,
        "form": form,
        "switch_options": switch_options,
        "active_lang": active_lang,
        "session_lang": session_lang,
        "english_mode": english_mode,
    }

    template = "core/dashboard_admin.html"

    context.setdefault("badges", {"unread_notifications_count": 0})

    return render(request, template, context)



# --- DASHBOARD CLIENTE (VISUAL Y ESTÉTICO) ---
@login_required
def dashboard_client(request):
    """Client visual dashboard with progress, photos, invoices"""
    profile = getattr(request.user, "profile", None)
    if not profile or profile.role != "client":
        messages.error(request, "Access restricted to clients only.")
        return redirect("dashboard")

    # Activate user's preferred language
    from django.utils import translation
    user_language = getattr(profile, 'language', None) or 'en'
    translation.activate(user_language)

    # Import unified schedule service for Gantt data
    from core.services.schedule_unified import get_project_progress

    # Client projects: via direct link (legacy) or granular assignment
    access_projects = Project.objects.filter(client_accesses__user=request.user)
    legacy_projects = Project.objects.filter(client=request.user.username)
    projects = access_projects.union(legacy_projects).order_by("-start_date")

    # For each project, calculate visual metrics
    project_data = []
    for project in projects:
        # Invoices
        invoices = project.invoices.all().order_by("-date_issued")[:5]
        total_invoiced = invoices.aggregate(total=Sum("total_amount"))["total"] or Decimal("0")
        total_paid = invoices.aggregate(paid=Sum("amount_paid"))["paid"] or Decimal("0")

        # Progress - use Gantt V2/V1 system
        gantt_progress = get_project_progress(project)
        progress_pct = gantt_progress.get('progress_percent', 0)
        
        # Fallback if no items in Gantt
        if gantt_progress.get('total_items', 0) == 0:
            try:
                metrics = compute_project_ev(project)
                if metrics and metrics.get("PV") and metrics["PV"] > 0:
                    progress_pct = min(100, (metrics.get("EV", 0) / metrics["PV"]) * 100)
            except Exception:
                # Fallback: date-based progress
                if project.start_date and project.end_date:
                    total_days = (project.end_date - project.start_date).days
                    elapsed_days = (timezone.localdate() - project.start_date).days
                    progress_pct = min(100, (elapsed_days / total_days * 100)) if total_days > 0 else 0

        # Recent photos
        from core.models import SitePhoto

        recent_photos = SitePhoto.objects.filter(project=project).order_by("-created_at")[:6]

        # Next schedule - search in Gantt V2 first, then legacy Schedule
        from core.models import ScheduleItemV2
        
        next_schedule = None
        today = timezone.localdate()
        
        # Search in Gantt V2 items - priority:
        # 1. Next future item not completed
        # 2. Item in progress (any date)
        # 3. Next future item (even if completed)
        # 4. Last completed item (most recent)
        
        # 1. Next future item not completed
        next_gantt_item = ScheduleItemV2.objects.filter(
            project=project,
            start_date__gte=today,
            status__in=['planned', 'in_progress']
        ).order_by('start_date').first()
        
        # 2. Item in progress (any date)
        if not next_gantt_item:
            next_gantt_item = ScheduleItemV2.objects.filter(
                project=project,
                status='in_progress'
            ).order_by('-start_date').first()
        
        # 3. Next future item (even if completed)
        if not next_gantt_item:
            next_gantt_item = ScheduleItemV2.objects.filter(
                project=project,
                start_date__gte=today
            ).order_by('start_date').first()
        
        # 4. Last completed item (most recent) - to show latest achievement
        if not next_gantt_item:
            next_gantt_item = ScheduleItemV2.objects.filter(
                project=project,
                status='done'
            ).order_by('-end_date', '-start_date').first()
        
        if next_gantt_item:
            # Create template-compatible object
            class NextEventProxy:
                def __init__(self, item):
                    self.title = item.name
                    self.description = item.description or f"Status: {item.get_status_display()}"
                    # Convert date to datetime for template
                    self.start_datetime = timezone.make_aware(
                        datetime.combine(item.start_date, datetime.min.time())
                    ) if item.start_date else None
                    self.status = item.status
            next_schedule = NextEventProxy(next_gantt_item)
        else:
            # Fallback to legacy Schedule
            next_schedule = (
                Schedule.objects.filter(project=project, start_datetime__gte=timezone.now())
                .order_by("start_datetime")
                .first()
            )

        # Client requests
        from core.models import ClientRequest

        client_requests = ClientRequest.objects.filter(project=project).order_by("-created_at")[:5]

        # Change Orders pending client signature
        # Only show COs that are approved/sent and waiting for client signature
        from core.models import ChangeOrder
        from core.services.financial_service import ChangeOrderService
        
        pending_change_orders = ChangeOrder.objects.filter(
            project=project,
            status__in=['approved', 'sent'],  # Only approved or sent COs (not pending/draft)
            signed_at__isnull=True,  # Not yet signed
        ).filter(
            Q(signature_image__isnull=True) | Q(signature_image='')
        ).order_by('-date_created')[:10]  # Increased limit to 10
        
        # Calculate T&M totals for each pending CO
        for co in pending_change_orders:
            if co.pricing_type == 'T_AND_M':
                tm_data = ChangeOrderService.get_billable_amount(co)
                co.calculated_total = tm_data.get('grand_total', Decimal("0"))
            else:
                co.calculated_total = co.amount or Decimal("0")
        
        # Recently signed Change Orders
        signed_change_orders = ChangeOrder.objects.filter(
            project=project,
        ).exclude(
            Q(signature_image__isnull=True) | Q(signature_image='')
        ).order_by('-signed_at')[:3]
        
        # Color Samples pending approval
        from core.models import ColorSample
        pending_color_samples = ColorSample.objects.filter(
            project=project,
            status__in=['proposed', 'review']
        ).order_by('-created_at')[:5]
        
        # Recently signed/approved Color Samples
        signed_color_samples = ColorSample.objects.filter(
            project=project,
            status='approved'
        ).exclude(
            client_signature__isnull=True
        ).exclude(
            client_signature=''
        ).order_by('-client_signed_at')[:3]

        # Contracts pending signature
        from core.models import Contract
        pending_contracts = Contract.objects.filter(
            project=project,
            status='pending_signature'
        ).order_by('-created_at')[:5]
        
        # Recently signed contracts
        signed_contracts = Contract.objects.filter(
            project=project,
            status__in=['signed', 'active']
        ).exclude(
            client_signed_at__isnull=True
        ).order_by('-client_signed_at')[:3]

        # Recent Daily Logs (only published ones for clients)
        from core.models import DailyLog
        recent_daily_logs = DailyLog.objects.filter(
            project=project,
            is_published=True
        ).select_related('created_by').order_by('-date')[:3]

        project_data.append(
            {
                "project": project,
                "invoices": invoices,
                "total_invoiced": total_invoiced,
                "total_paid": total_paid,
                "balance": total_invoiced - total_paid,
                "progress_pct": int(progress_pct),
                "gantt_progress": gantt_progress,  # Full progress data from Gantt
                "recent_photos": recent_photos,
                "next_schedule": next_schedule,
                "client_requests": client_requests,
                "pending_change_orders": pending_change_orders,
                "signed_change_orders": signed_change_orders,
                "pending_color_samples": pending_color_samples,
                "signed_color_samples": signed_color_samples,
                "pending_contracts": pending_contracts,
                "signed_contracts": signed_contracts,
                "recent_daily_logs": recent_daily_logs,
            }
        )

    # === MORNING BRIEFING (Categorized alerts for client) ===
    morning_briefing = []

    # Category: Updates (new photos, comments)
    latest_photos = []
    for proj_data in project_data:
        latest_photos.extend(proj_data["recent_photos"][:2])

    if latest_photos:
        morning_briefing.append(
            {
                "text": _("There are %(count)s new photos from your project") % {"count": len(latest_photos)},
                "severity": "info",
                "action_url": "#",
                "action_label": _("View photos"),
                "category": "updates",
            }
        )

    # Category: Payments (pending invoices)
    overdue_invoices = []
    for proj_data in project_data:
        for inv in proj_data["invoices"]:
            if proj_data["balance"] > 0:
                overdue_invoices.append(inv)

    if overdue_invoices:
        total_due = sum(inv.total_amount - inv.amount_paid for inv in overdue_invoices)
        invoices_url = reverse("dashboard_client")
        morning_briefing.append(
            {
                "text": _("You have %(amount)s in pending invoices") % {"amount": f"${total_due:,.2f}"},
                "severity": "warning",
                "action_url": invoices_url,
                "action_label": _("View Invoices"),
                "category": "payments",
            }
        )

    # Category: Schedule (upcoming activities)
    upcoming_schedules = []
    for proj_data in project_data:
        if proj_data["next_schedule"]:
            upcoming_schedules.append(proj_data["next_schedule"])

    if upcoming_schedules:
        next_date = upcoming_schedules[0].start_datetime
        morning_briefing.append(
            {
                "text": _("Next activity scheduled for %(date)s") % {"date": next_date.strftime('%m/%d/%Y')},
                "severity": "info",
                "action_url": "#",
                "action_label": _("View schedule"),
                "category": "schedule",
            }
        )

    # Apply filter if requested
    active_filter = request.GET.get("filter", "all")
    if active_filter != "all":
        morning_briefing = [
            item for item in morning_briefing if item.get("category") == active_filter
        ]

    # Get display name (prefer profile display_name, then full name, then username)
    display_name = None
    try:
        prof = getattr(request.user, "profile", None)
        candidate = None
        if prof is not None:
            candidate = getattr(prof, "display_name", None) or getattr(prof, "full_name", None)
        display_name = (candidate or request.user.get_full_name() or request.user.username).strip()
    except Exception:
        display_name = request.user.username

    # Determine active project index from GET param or default to first
    active_project_index = 0
    active_project_id = request.GET.get("project_id")
    if active_project_id:
        for idx, data in enumerate(project_data):
            if str(data["project"].id) == active_project_id:
                active_project_index = idx
                break

    context = {
        "project_data": project_data,
        "today": timezone.localdate(),
        "display_name": display_name,
        "morning_briefing": morning_briefing,
        "active_filter": active_filter,
        "active_project_index": active_project_index,
    }

    # Use premium template (unified design)
    return render(request, "core/dashboard_client_premium.html", context)



# --- EXECUTIVE BI DASHBOARD (Module 21) ---
@login_required
def executive_bi_dashboard(request):
    """High-level consolidated business intelligence dashboard.

    Uses FinancialAnalyticsService to avoid duplicated financial logic across
    various views and ensures consistency of KPIs.

    Supports cache invalidation via ?refresh query parameter.
    """
    if not (request.user.is_superuser or request.user.is_staff):
        messages.error(request, "Acceso solo para Admin/Staff.")
        return redirect("dashboard")

    # Check if refresh is requested
    if request.GET.get("refresh"):
        from django.core.cache import cache

        # Clear all BI-related caches
        today = timezone.localdate()
        cache_keys = [
            f"fa:cashflow:{today.isoformat()}:30",
            "fa:project_margins",
            f"fa:kpis:{today.isoformat()}",
            "fa:inventory_risk",
        ]
        for key in cache_keys:
            cache.delete(key)

    service = FinancialAnalyticsService()
    cash_flow = service.get_cash_flow_projection(days=30)
    margins = service.get_project_margins()
    kpis = service.get_company_health_kpis()
    top_employees = service.get_top_performing_employees(limit=8)
    inventory_risk = service.get_inventory_risk_items()

    from django.conf import settings

    low_margin_threshold = getattr(settings, "BI_LOW_MARGIN_THRESHOLD", 15.0)

    low_margin_projects = [m for m in margins if m["margin_pct"] < low_margin_threshold]
    high_margin_projects = sorted(margins, key=lambda m: m["margin_pct"], reverse=True)[:5]

    context = {
        "today": timezone.localdate(),
        "kpis": kpis,
        "cash_flow_chart_data": cash_flow["chart"],
        "low_margin_projects": low_margin_projects,
        "high_margin_projects": high_margin_projects,
        "top_performing_employees": top_employees,
        "inventory_risk_items": inventory_risk,
    }
    return render(request, "core/dashboard_bi.html", context)



@login_required
def master_schedule_center(request):
    """Master Schedule — React Gantt (all projects as categories).

    Requires admin/staff access. Data loaded via /api/v1/gantt/v2/master/.
    """
    if not (request.user.is_superuser or request.user.is_staff):
        messages.error(request, "Acceso solo para Admin/Staff.")
        return redirect("dashboard")

    from django.contrib.auth import get_user_model
    from django.urls import reverse

    User = get_user_model()
    team_members = (
        User.objects.filter(is_active=True, is_staff=True)
        .order_by("first_name", "last_name")
        .values("id", "first_name", "last_name")
    )

    # iCal feed URL for iPhone / Google Calendar sync
    ical_path = reverse("master-calendar-feed", args=[request.user.pk])
    ical_feed_url = request.build_absolute_uri(ical_path)
    # Extract host and path for webcal:// links
    from urllib.parse import urlparse
    parsed = urlparse(ical_feed_url)
    ical_feed_host = parsed.netloc
    ical_feed_path = parsed.path

    context = {
        "title": "Master Schedule",
        "team_members": list(team_members),
        "ical_feed_url": ical_feed_url,
        "ical_feed_host": ical_feed_host,
        "ical_feed_path": ical_feed_path,
    }
    return render(request, "core/master_schedule_gantt.html", context)



@login_required
def focus_wizard(request):
    """Executive Focus Wizard: 4-Step Daily Planning (Pareto + Eat That Frog).

    Step 1: Brain Dump (capture all tasks)
    Step 2: 80/20 Filter (identify high impact tasks)
    Step 3: The Frog (select #1 most important task)
    Step 4: Battle Plan (break down frog + time blocking)
    """
    context = {
        "title": "Executive Focus Wizard",
        "today": timezone.localdate(),
        "user_token": request.user.id,  # For calendar feed URL
    }
    return render(request, "core/focus_wizard.html", context)



# --- DASHBOARD (Redirect to role-based dashboards) ---
@login_required
def dashboard_view(request):
    """
    Smart redirect to appropriate dashboard based on user role.
    This replaces the old generic dashboard.
    """
    user = request.user

    # Apply preferred language from profile if available
    try:
        prof = getattr(user, "profile", None)
        preferred = getattr(prof, "language", None)
        if preferred and request.session.get("lang") != preferred:
            request.session["lang"] = preferred
            translation.activate(preferred)
    except Exception:
        pass

    # Get user profile to determine role
    profile = getattr(user, "profile", None)
    role = getattr(profile, "role", None)

    # Check if user has an Employee record (priority for employee redirect)
    from core.models import Employee

    has_employee = Employee.objects.filter(user=user).exists()

    # Redirect based on role
    if user.is_superuser or (profile and role == "admin"):
        return redirect("dashboard_admin")
    elif profile and role in ["client", "superintendent"]:
        # Unificación: superintendente utiliza vista cliente/builder
        return redirect("dashboard_client")
    elif profile and role == "project_manager":
        return redirect("dashboard_pm")
    elif profile and role == "employee":
        return redirect("dashboard_employee")
    elif profile and role == "designer":
        return redirect("dashboard_designer")
    # Rol superintendente ya cubierto arriba por cliente/builder unificado
    # PRIORITY FIX: If user has Employee record, always go to employee dashboard
    elif has_employee:
        return redirect("dashboard_employee")
    else:
        # Default: check if user is staff -> PM dashboard, otherwise employee
        if user.is_staff:
            return redirect("dashboard_pm")
        else:
            return redirect("dashboard_employee")



@login_required
def dashboard_employee(request):
    """Dashboard simple para empleados: qué hacer hoy, clock in/out, materiales"""
    # legacy flag kept for compatibility; value is handled by router/templates
    _is_legacy = request.GET.get("legacy", "false").lower() == "true"
    # Obtener empleado ligado al usuario
    employee = Employee.objects.filter(user=request.user).first()
    if not employee:
        messages.error(request, "Tu usuario no está vinculado a un empleado.")
        # NOTE: keep legacy template only (clean template was removed)
        return render(
            request,
            "core/dashboard_employee.html",
            {"employee": None, "badges": {"unread_notifications_count": 0}},
        )

    today = timezone.localdate()
    now = timezone.localtime()

    # TimeEntry abierto (si está trabajando)
    open_entry = (
        TimeEntry.objects.filter(employee=employee, end_time__isnull=True).select_related("project", "change_order")
        .order_by("-date", "-start_time")
        .first()
    )

    # Touch-ups asignados (legacy Task model)
    my_touchups = (
        Task.objects.filter(
            assigned_to=employee, is_touchup=True, status__in=["Pending", "In Progress"]
        )
        .select_related("project")
        .order_by("-created_at")[:10]
    )

    # Touch-ups V2 asignados (nuevo modelo dedicado)
    my_touchups_v2 = (
        TouchUp.objects.filter(
            assigned_to=employee, status__in=["open", "in_progress", "review"]
        )
        .select_related("project")
        .prefetch_related("photos")
        .order_by("-created_at")[:10]
    )

    # === QUÉ HACER HOY (Daily Plan Activities) ===
    from core.models import DailyPlan

    today_plans = (
        DailyPlan.objects.filter(
            plan_date=today,
            project__in=employee.projects.all() if hasattr(employee, "projects") else [],
        )
        .select_related("project")
        .prefetch_related("activities__assigned_employees")
    )

    my_activities = []
    for plan in today_plans:
        for activity in plan.activities.filter(assigned_employees=employee, is_completed=False):
            my_activities.append(
                {
                    "activity": activity,
                    "project": plan.project,
                }
            )

    # === SCHEDULE ASIGNADO HOY ===
    my_schedule = (
        Schedule.objects.filter(assigned_to=request.user, start_datetime__date=today)
        .select_related("project")
        .order_by("start_datetime")
    )

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "clock_in":
            if open_entry:
                messages.warning(request, _("You already have an open entry. Clock out first."))
                return redirect("dashboard_employee")
            form = ClockInForm(request.POST)
            if form.is_valid():
                project = form.cleaned_data["project"]

                # ✅ VALIDACIÓN (Regla A): solo si está asignado HOY.
                # SOURCE OF TRUTH: ResourceAssignment.
                is_assigned_today = ResourceAssignment.objects.filter(
                    employee=employee,
                    project=project,
                    date=today,
                ).exists()

                if not is_assigned_today:
                    messages.error(
                        request,
                        _("❌ You are not assigned to '%(project)s' today. Contact your PM if this is an error.") % {"project": project.name},
                    )
                    return redirect("dashboard_employee")

                TimeEntry.objects.create(
                    employee=employee,
                    project=project,
                    change_order=form.cleaned_data.get("change_order"),
                    budget_line=form.cleaned_data.get("budget_line"),
                    date=today,
                    start_time=now.time(),
                    end_time=None,
                    notes=form.cleaned_data.get("notes") or "",
                    cost_code=form.cleaned_data.get("cost_code"),
                )
                messages.success(
                    request,
                    _("✓ Clocked in at %(time)s.") % {"time": now.strftime("%H:%M")},
                )
                return redirect("dashboard_employee")

        elif action == "clock_out":
            if not open_entry:
                messages.warning(request, _("You don't have an open entry."))
                return redirect("dashboard_employee")
            open_entry.end_time = now.time()
            open_entry.save()  # recalcula hours_worked con tu lógica (almuerzo 12:30)
            messages.success(
                request,
                _("✓ Clocked out at %(time)s. Hours: %(hours)s") % {"time": now.strftime("%H:%M"), "hours": open_entry.hours_worked},
            )
            return redirect("dashboard_employee")

        elif action == "switch_context" and open_entry:
            # CORRECCIÓN: Cerrar entrada actual y crear nueva para registrar tiempo correctamente
            switch_type = request.POST.get("switch_type")
            current_time = now.time()
            
            # Guardar datos de la entrada actual antes de cerrarla
            old_project = open_entry.project
            old_co = open_entry.change_order
            
            # Helper: calcular segundos entre dos tiempos (para detectar clicks accidentales)
            def seconds_between(start, end):
                if not start or not end:
                    return 0
                s = start.hour * 3600 + start.minute * 60 + getattr(start, 'second', 0)
                e = end.hour * 3600 + end.minute * 60 + getattr(end, 'second', 0)
                if e < s:
                    e += 24 * 3600
                return e - s
            
            # Helper: verificar si es un switch instantáneo (< 30 segundos)
            # Solo para clicks accidentales/errores, NO para trabajo real
            def is_instant_switch():
                return seconds_between(open_entry.start_time, current_time) < 30
            
            # Helper function para recalcular hours_worked si es necesario
            def ensure_hours_calculated(entry, context_name):
                if entry.hours_worked is None or entry.hours_worked == 0:
                    logger.warning(
                        f"[{context_name}] hours_worked=0 for entry {entry.id}. "
                        f"start={entry.start_time}, end={entry.end_time}"
                    )
                    if entry.start_time and entry.end_time:
                        s = entry.start_time.hour * 60 + entry.start_time.minute
                        e = entry.end_time.hour * 60 + entry.end_time.minute
                        if e < s:
                            e += 24 * 60
                        minutes = e - s
                        hours = Decimal(minutes) / Decimal(60)
                        if hours >= Decimal("5.0"):
                            lunch_min = 12 * 60 + 30
                            if s < lunch_min <= e:
                                hours -= Decimal("0.5")
                        entry.hours_worked = hours.quantize(Decimal("0.01"))
                        entry.save(update_fields=['hours_worked'])
                        logger.info(f"[{context_name}] Forced recalc: {hours}h")
            
            if switch_type == "base":
                # Si es switch instantáneo (< 1 min), solo actualizar la entrada actual
                if is_instant_switch():
                    logger.info(f"[Emp Switch Base] Instant switch - updating current entry {open_entry.id}")
                    open_entry.change_order = None
                    open_entry.notes = f"Quick switch to base work (was: {old_co.title if old_co else 'N/A'})"
                    open_entry.save()
                    messages.success(
                        request,
                        _("✓ Switched to base work (instant). Previously: %(co)s")
                        % {"co": old_co.title if old_co else "N/A"},
                    )
                else:
                    # Cerrar entrada actual y crear nueva sin CO
                    open_entry.end_time = current_time
                    open_entry.save()
                    ensure_hours_calculated(open_entry, "Emp Switch Base")
                    
                    # Crear nueva entrada sin CO
                    TimeEntry.objects.create(
                        employee=employee,
                        project=old_project,
                        change_order=None,
                        budget_line=open_entry.budget_line,
                        date=today,
                        start_time=current_time,
                        end_time=None,
                        notes=f"Switched from CO: {old_co.title if old_co else 'N/A'}",
                        cost_code=open_entry.cost_code,
                    )
                    messages.success(
                        request,
                        _("✓ Entry closed (%(hours)s hrs). Now on base work (no Change Order). Previously: %(co)s")
                        % {"hours": open_entry.hours_worked, "co": old_co.title if old_co else "N/A"},
                    )
                
            elif switch_type == "co":
                # Cerrar entrada actual y crear nueva con diferente CO
                target_id = request.POST.get("target_id") or request.POST.get("co_id")
                if target_id:
                    try:
                        new_co = ChangeOrder.objects.get(
                            id=target_id,
                            project=open_entry.project,
                            status__in=['draft', 'pending', 'approved', 'sent', 'billed']
                        )
                        
                        # Si es switch instantáneo (< 1 min), solo actualizar la entrada actual
                        if is_instant_switch():
                            logger.info(f"[Emp Switch CO] Instant switch - updating current entry {open_entry.id}")
                            open_entry.change_order = new_co
                            open_entry.budget_line = None  # CO work doesn't use budget lines
                            open_entry.notes = f"Quick switch to CO: {new_co.title} (was: {old_co.title if old_co else 'Base'})"
                            open_entry.save()
                            messages.success(
                                request,
                                _("✓ Switched to %(co)s (instant). Previously: %(old)s")
                                % {"co": new_co.title, "old": old_co.title if old_co else "Base work"},
                            )
                        else:
                            # Cerrar entrada actual
                            open_entry.end_time = current_time
                            open_entry.save()
                            ensure_hours_calculated(open_entry, "Emp Switch CO")
                            
                            # Crear nueva entrada con el nuevo CO
                            TimeEntry.objects.create(
                                employee=employee,
                                project=old_project,
                                change_order=new_co,
                                budget_line=None,  # CO work doesn't use budget lines
                                date=today,
                                start_time=current_time,
                                end_time=None,
                                notes=f"Switched from: {old_co.title if old_co else 'Base work'}",
                                cost_code=open_entry.cost_code,
                            )
                            messages.success(
                                request,
                                _("✓ Entry closed (%(hours)s hrs). Now on %(co)s (%(type)s)")
                                % {"hours": open_entry.hours_worked, "co": new_co.title, "type": new_co.get_pricing_type_display()},
                            )
                    except ChangeOrder.DoesNotExist:
                        messages.error(request, _("Change Order not found or not available."))
                        
            elif switch_type == "project":
                # Cerrar entrada actual y crear nueva en otro proyecto
                target_id = request.POST.get("target_id") or request.POST.get("project_id")
                if target_id:
                    try:
                        # Verificar que el empleado esté asignado a este proyecto hoy
                        is_assigned = ResourceAssignment.objects.filter(
                            employee=employee,
                            project_id=target_id,
                            date=today,
                        ).exists()
                        if not is_assigned:
                            messages.error(request, _("You're not assigned to that project today."))
                        else:
                            new_project = Project.objects.get(id=target_id)
                            
                            # Si es switch instantáneo (< 1 min), solo actualizar la entrada actual
                            if is_instant_switch():
                                logger.info(f"[Emp Switch Project] Instant switch - updating current entry {open_entry.id}")
                                open_entry.project = new_project
                                open_entry.change_order = None
                                open_entry.budget_line = None
                                open_entry.notes = f"Quick switch to project: {new_project.name} (was: {old_project.name})"
                                open_entry.save()
                                messages.success(
                                    request,
                                    _("✓ Switched to %(proj)s (instant). Previously: %(old)s")
                                    % {"proj": new_project.name, "old": old_project.name},
                                )
                            else:
                                # Cerrar entrada actual
                                open_entry.end_time = current_time
                                open_entry.save()
                                ensure_hours_calculated(open_entry, "Emp Switch Project")
                                
                                # Crear nueva entrada en el nuevo proyecto
                                TimeEntry.objects.create(
                                    employee=employee,
                                    project=new_project,
                                    change_order=None,
                                    budget_line=None,
                                    date=today,
                                    start_time=current_time,
                                    end_time=None,
                                    notes=f"Switched from project: {old_project.name}",
                                    cost_code=None,
                                )
                                messages.success(
                                    request,
                                    _("✓ Entry closed (%(hours)s hrs on %(old)s). Now on %(proj)s")
                                    % {"hours": open_entry.hours_worked, "old": old_project.name, "proj": new_project.name},
                                )
                    except Project.DoesNotExist:
                        messages.error(request, _("Project not found."))

            elif switch_type == "project_co":
                # Switch project AND set a specific CO in one step (from wizard)
                target_id = request.POST.get("target_id") or request.POST.get("project_id")
                co_id = request.POST.get("co_id")
                if target_id:
                    try:
                        is_assigned = ResourceAssignment.objects.filter(
                            employee=employee, project_id=target_id, date=today,
                        ).exists()
                        if not is_assigned:
                            messages.error(request, _("You're not assigned to that project today."))
                        else:
                            new_project = Project.objects.get(id=target_id)
                            new_co = None
                            if co_id:
                                new_co = ChangeOrder.objects.get(
                                    id=co_id, project=new_project,
                                    status__in=['draft', 'pending', 'approved', 'sent', 'billed']
                                )
                            open_entry.end_time = current_time
                            open_entry.save()
                            ensure_hours_calculated(open_entry, "Emp Switch ProjectCO")
                            TimeEntry.objects.create(
                                employee=employee,
                                project=new_project,
                                change_order=new_co,
                                budget_line=None,
                                date=today,
                                start_time=current_time,
                                end_time=None,
                                notes=f"Switched from: {old_project.name}" + (f" to CO: {new_co.title}" if new_co else ""),
                                cost_code=None,
                            )
                            msg = _("✓ Entry closed (%(hours)s hrs). Now on %(proj)s") % {
                                "hours": open_entry.hours_worked, "proj": new_project.name
                            }
                            if new_co:
                                msg += f" — {new_co.title}"
                            messages.success(request, msg)
                    except (Project.DoesNotExist, ChangeOrder.DoesNotExist):
                        messages.error(request, _("Project or Change Order not found."))

            return redirect("dashboard_employee")

    # ✅ Obtener proyectos donde está asignado HOY (SOURCE OF TRUTH: ResourceAssignment)
    # Nota: DailyPlan NO define asignación de proyectos; solo planificación.
    my_projects_today = Project.objects.filter(
        resource_assignments__employee=employee,
        resource_assignments__date=today,
    ).distinct()

    # GET o POST inválido - crear form con proyectos filtrados
    form = ClockInForm(available_projects=my_projects_today)

    # === MORNING BRIEFING (Employee Daily Tasks) ===
    morning_briefing = []

    # Category: tasks (Touch-ups pendientes)
    if my_touchups:
        count = len(my_touchups)
        morning_briefing.append(
            {
                "text": f"Tienes {count} {'reparación' if count == 1 else 'reparaciones'} pendiente{'s' if count > 1 else ''}",
                "severity": "warning" if count > 2 else "info",
                "action_url": "#",
                "action_label": "Ver reparaciones",
                "category": "tasks",
            }
        )

    # Category: schedule (Actividades de hoy)
    if my_activities:
        count = len(my_activities)
        morning_briefing.append(
            {
                "text": f"Tienes {count} actividad{'es' if count > 1 else ''} programada{'s' if count > 1 else ''} para hoy",
                "severity": "info",
                "action_url": "#",
                "action_label": "Ver plan",
                "category": "schedule",
            }
        )

    # Horas de la semana (calcular ANTES de usarse)
    week_start = today - timedelta(days=today.weekday())
    week_entries = TimeEntry.objects.filter(
        employee=employee, date__gte=week_start, date__lte=today
    )
    week_hours = sum(entry.hours_worked or 0 for entry in week_entries)

    # Category: clock (Work hours)
    if not open_entry:
        morning_briefing.append(
            {
                "text": "Marca tu entrada para registrar horas de trabajo",
                "severity": "info",
                "action_url": "#",
                "action_label": "Marcar entrada",
                "category": "clock",
            }
        )
    else:
        morning_briefing.append(
            {
                "text": f"Ya marcaste entrada. Tiempo registrado hoy: {week_hours} horas",
                "severity": "success",
                "action_url": "#",
                "action_label": "Marcar salida",
                "category": "clock",
            }
        )

    # Apply filter if requested
    active_filter = request.GET.get("filter", "all")
    if active_filter != "all":
        morning_briefing = [
            item for item in morning_briefing if item.get("category") == active_filter
        ]

    # Historial reciente (últimas 5 entradas)
    recent = TimeEntry.objects.filter(employee=employee).select_related("project", "change_order").order_by("-date", "-start_time")[:5]

    # Mensaje si no tiene asignaciones hoy
    has_assignments_today = my_projects_today.exists()

    # Variables para el template legacy
    assignments_today = ResourceAssignment.objects.filter(
        employee=employee, date=today
    ).select_related("project")

    available_projects_count = my_projects_today.count()
    available_projects_preview = list(my_projects_today[:5])

    # === SWITCH OPTIONS (para cambiar proyecto/CO cuando hay entrada abierta) ===
    switch_options = None
    if open_entry:
        # Otros proyectos (Employee solo ve los asignados hoy, excluir el actual)
        other_projects = list(my_projects_today.exclude(id=open_entry.project_id))
        
        # COs del proyecto actual (disponibles para trabajo)
        # Incluir draft, pending, approved, sent, billed (excluir solo 'paid' que ya está cerrado)
        current_project_cos = ChangeOrder.objects.filter(
            project=open_entry.project,
            status__in=['draft', 'pending', 'approved', 'sent', 'billed']
        ).exclude(id=open_entry.change_order_id if open_entry.change_order else None)
        
        available_cos = [
            {
                "id": co.id, 
                "title": co.title, 
                "pricing_type": co.pricing_type,
                "pricing_label": f"${co.amount}" if co.pricing_type == 'fixed' else "T&M"
            }
            for co in current_project_cos
        ]
        
        switch_options = {
            "other_projects": [{"id": p.id, "name": p.name} for p in other_projects],
            "other_projects_count": len(other_projects),
            "available_cos": available_cos,
            "current_project": {"id": open_entry.project.id, "name": open_entry.project.name},
            "can_switch_to_base": open_entry.change_order is not None,
        }

    context = {
        "employee": employee,
        "open_entry": open_entry,
        "form": form,
        "today": today,
        "now": now,
        "recent": recent,
        "week_hours": week_hours,
        "my_activities": my_activities,
        "my_schedule": my_schedule,
        "my_touchups": my_touchups,
        "my_touchups_v2": my_touchups_v2,
        "morning_briefing": morning_briefing,
        "active_filter": active_filter,
        "badges": {"unread_notifications_count": 0},
        "my_projects_today": my_projects_today,
        "has_assignments_today": has_assignments_today,
        "assignments_today": assignments_today,
        "available_projects_count": available_projects_count,
        "available_projects_preview": available_projects_preview,
        "switch_options": switch_options,
    }

    # Use legacy template (stable version)
    template_name = "core/dashboard_employee.html"
    return render(request, template_name, context)



# --- DASHBOARD PM ---
@login_required
def dashboard_pm(request):
    """Dashboard operacional para PM: materiales, planning, issues, tiempo sin CO"""
    # SECURITY: Only PMs, admins, and superusers can access
    profile = getattr(request.user, "profile", None)
    role = getattr(profile, "role", None) if profile else None
    if not (request.user.is_superuser or role in ("admin", "project_manager") or request.user.is_staff):
        messages.error(request, "Acceso solo para PM/Staff.")
        return redirect("dashboard_employee")

    # Language prompt if user has no preference yet
    show_language_prompt = False
    prof = getattr(request.user, "profile", None)
    if prof:
        if getattr(prof, "language", None):
            if request.session.get("lang") != prof.language:
                request.session["lang"] = prof.language
                translation.activate(prof.language)
        else:
            show_language_prompt = True

    today = timezone.localdate()
    now = timezone.localtime()

    # Obtener empleado ligado al usuario (para PM que también son empleados)
    employee = Employee.objects.filter(user=request.user).first()

    # TimeEntry abierto (si está trabajando) - Solo si hay empleado vinculado
    open_entry = None
    if employee:
        open_entry = (
            TimeEntry.objects.filter(employee=employee, end_time__isnull=True).select_related("project", "change_order")
            .order_by("-date", "-start_time")
            .first()
        )

    # Manejo de Clock In/Out para PMs
    if request.method == "POST" and employee:
        action = request.POST.get("action")

        if action == "clock_in":
            if open_entry:
                messages.warning(request, _("You already have an open entry. Clock out first."))
                return redirect("dashboard_pm")
            form = ClockInForm(request.POST)
            if form.is_valid():
                TimeEntry.objects.create(
                    employee=employee,
                    project=form.cleaned_data["project"],
                    change_order=form.cleaned_data.get("change_order"),
                    budget_line=form.cleaned_data.get("budget_line"),
                    date=today,
                    start_time=now.time(),
                    end_time=None,
                    notes=form.cleaned_data.get("notes") or "",
                    cost_code=form.cleaned_data.get("cost_code"),
                )
                messages.success(
                    request,
                    _("✓ Clocked in at %(time)s.") % {"time": now.strftime("%H:%M")},
                )
                return redirect("dashboard_pm")

        elif action == "clock_out":
            if not open_entry:
                messages.warning(request, _("You don't have an open entry."))
                return redirect("dashboard_pm")
            open_entry.end_time = now.time()
            open_entry.save()
            messages.success(
                request,
                _("✓ Clocked out at %(time)s. Hours: %(hours)s") % {"time": now.strftime("%H:%M"), "hours": open_entry.hours_worked},
            )
            return redirect("dashboard_pm")

        elif action == "switch_context" and open_entry:
            # CORRECCIÓN: Cerrar entrada actual y crear nueva para registrar tiempo correctamente
            switch_type = request.POST.get("switch_type")
            current_time = now.time()
            
            old_project = open_entry.project
            old_co = open_entry.change_order
            
            # Helper: calcular segundos entre dos tiempos (para detectar clicks accidentales)
            def seconds_between(start, end):
                if not start or not end:
                    return 0
                s = start.hour * 3600 + start.minute * 60 + getattr(start, 'second', 0)
                e = end.hour * 3600 + end.minute * 60 + getattr(end, 'second', 0)
                if e < s:
                    e += 24 * 3600
                return e - s
            
            # Helper: verificar si es un switch instantáneo (< 30 segundos)
            # Solo para clicks accidentales/errores, NO para trabajo real
            def is_instant_switch():
                return seconds_between(open_entry.start_time, current_time) < 30
            
            # Helper function para recalcular hours_worked si es necesario
            def ensure_hours_calculated(entry, context_name):
                if entry.hours_worked is None or entry.hours_worked == 0:
                    logger.warning(
                        f"[{context_name}] hours_worked=0 for entry {entry.id}. "
                        f"start={entry.start_time}, end={entry.end_time}"
                    )
                    if entry.start_time and entry.end_time:
                        s = entry.start_time.hour * 60 + entry.start_time.minute
                        e = entry.end_time.hour * 60 + entry.end_time.minute
                        if e < s:
                            e += 24 * 60
                        minutes = e - s
                        hours = Decimal(minutes) / Decimal(60)
                        if hours >= Decimal("5.0"):
                            lunch_min = 12 * 60 + 30
                            if s < lunch_min <= e:
                                hours -= Decimal("0.5")
                        entry.hours_worked = hours.quantize(Decimal("0.01"))
                        entry.save(update_fields=['hours_worked'])
                        logger.info(f"[{context_name}] Forced recalc: {hours}h")
            
            if switch_type == "base":
                # Si es switch instantáneo (< 1 min), solo actualizar la entrada actual
                if is_instant_switch():
                    logger.info(f"[PM Switch Base] Instant switch - updating current entry {open_entry.id}")
                    open_entry.change_order = None
                    open_entry.notes = f"Quick switch to base work (was: {old_co.title if old_co else 'N/A'})"
                    open_entry.save()
                    messages.success(
                        request,
                        _("✓ Switched to base work (instant). Previously: %(co)s")
                        % {"co": old_co.title if old_co else "N/A"},
                    )
                else:
                    open_entry.end_time = current_time
                    open_entry.save()
                    ensure_hours_calculated(open_entry, "PM Switch Base")
                    
                    TimeEntry.objects.create(
                        employee=employee,
                        project=old_project,
                        change_order=None,
                        budget_line=open_entry.budget_line,
                        date=today,
                        start_time=current_time,
                        end_time=None,
                        notes=f"Switched from CO: {old_co.title if old_co else 'N/A'}",
                        cost_code=open_entry.cost_code,
                    )
                    messages.success(
                        request,
                        _("✓ Entry closed (%(hours)s hrs). Now on base work. Previously: %(co)s")
                        % {"hours": open_entry.hours_worked, "co": old_co.title if old_co else "N/A"},
                    )
                
            elif switch_type == "co":
                target_id = request.POST.get("target_id") or request.POST.get("co_id")
                if target_id:
                    try:
                        new_co = ChangeOrder.objects.get(
                            id=target_id,
                            project=open_entry.project,
                            status__in=['draft', 'pending', 'approved', 'sent', 'billed']
                        )
                        
                        # Si es switch instantáneo (< 1 min), solo actualizar la entrada actual
                        if is_instant_switch():
                            logger.info(f"[PM Switch CO] Instant switch - updating current entry {open_entry.id}")
                            open_entry.change_order = new_co
                            open_entry.budget_line = None
                            open_entry.notes = f"Quick switch to CO: {new_co.title} (was: {old_co.title if old_co else 'Base'})"
                            open_entry.save()
                            messages.success(
                                request,
                                _("✓ Switched to %(co)s (instant). Previously: %(old)s")
                                % {"co": new_co.title, "old": old_co.title if old_co else "Base work"},
                            )
                        else:
                            open_entry.end_time = current_time
                            open_entry.save()
                            ensure_hours_calculated(open_entry, "PM Switch CO")
                            
                            TimeEntry.objects.create(
                                employee=employee,
                                project=old_project,
                                change_order=new_co,
                                budget_line=None,
                                date=today,
                                start_time=current_time,
                                end_time=None,
                                notes=f"Switched from: {old_co.title if old_co else 'Base work'}",
                                cost_code=open_entry.cost_code,
                            )
                            messages.success(
                                request,
                                _("✓ Entry closed (%(hours)s hrs). Now on %(co)s (%(type)s)")
                                % {"hours": open_entry.hours_worked, "co": new_co.title, "type": new_co.get_pricing_type_display()},
                            )
                    except ChangeOrder.DoesNotExist:
                        messages.error(request, _("Change Order not found or not available."))
                        
            elif switch_type == "project":
                target_id = request.POST.get("target_id") or request.POST.get("project_id")
                if target_id:
                    try:
                        new_project = Project.objects.get(id=target_id)
                        
                        # Si es switch instantáneo (< 1 min), solo actualizar la entrada actual
                        if is_instant_switch():
                            logger.info(f"[PM Switch Project] Instant switch - updating current entry {open_entry.id}")
                            open_entry.project = new_project
                            open_entry.change_order = None
                            open_entry.budget_line = None
                            open_entry.notes = f"Quick switch to project: {new_project.name} (was: {old_project.name})"
                            open_entry.save()
                            messages.success(
                                request,
                                _("✓ Switched to %(proj)s (instant). Previously: %(old)s")
                                % {"proj": new_project.name, "old": old_project.name},
                            )
                        else:
                            # Cerrar entrada actual
                            open_entry.end_time = current_time
                            open_entry.save()
                            ensure_hours_calculated(open_entry, "PM Switch Project")
                            
                            TimeEntry.objects.create(
                                employee=employee,
                                project=new_project,
                                change_order=None,
                                budget_line=None,
                                date=today,
                                start_time=current_time,
                                end_time=None,
                                notes=f"Switched from project: {old_project.name}",
                                cost_code=None,
                            )
                            messages.success(
                                request,
                                _("✓ Entry closed (%(hours)s hrs on %(old)s). Now on %(proj)s")
                                % {"hours": open_entry.hours_worked, "old": old_project.name, "proj": new_project.name},
                            )
                    except Project.DoesNotExist:
                        messages.error(request, _("Project not found."))

            elif switch_type == "project_co":
                # Switch project AND set a specific CO in one step (from wizard)
                target_id = request.POST.get("target_id") or request.POST.get("project_id")
                co_id = request.POST.get("co_id")
                if target_id:
                    try:
                        new_project = Project.objects.get(id=target_id)
                        new_co = None
                        if co_id:
                            new_co = ChangeOrder.objects.get(
                                id=co_id, project=new_project,
                                status__in=['draft', 'pending', 'approved', 'sent', 'billed']
                            )
                        open_entry.end_time = current_time
                        open_entry.save()
                        ensure_hours_calculated(open_entry, "PM Switch ProjectCO")
                        TimeEntry.objects.create(
                            employee=employee,
                            project=new_project,
                            change_order=new_co,
                            budget_line=None,
                            date=today,
                            start_time=current_time,
                            end_time=None,
                            notes=f"Switched from: {old_project.name}" + (f" to CO: {new_co.title}" if new_co else ""),
                            cost_code=None,
                        )
                        msg = _("✓ Entry closed (%(hours)s hrs). Now on %(proj)s") % {
                            "hours": open_entry.hours_worked, "proj": new_project.name
                        }
                        if new_co:
                            msg += f" — {new_co.title}"
                        messages.success(request, msg)
                    except (Project.DoesNotExist, ChangeOrder.DoesNotExist):
                        messages.error(request, _("Project or Change Order not found."))

            return redirect("dashboard_pm")

    # Form para clock in
    form = ClockInForm() if employee else None

    # === ALERTAS OPERACIONALES ===
    # 1. Tiempo sin CO
    unassigned_time_count = TimeEntry.objects.filter(change_order__isnull=True).count()

    # 2. Materiales pendientes
    pending_materials = MaterialRequest.objects.filter(status__in=["pending", "submitted"]).count()

    # 3. Issues abiertos
    open_issues = Issue.objects.filter(status__in=["open", "in_progress"]).count()

    # 4. RFIs sin respuesta
    open_rfis = RFI.objects.filter(status="open").count()

    # 5. Daily Plans de hoy
    from core.models import DailyPlan

    today_plans = DailyPlan.objects.filter(plan_date=today).count()

    # === MATERIALES PENDIENTES (top 10) ===
    pending_materials_list = (
        MaterialRequest.objects.filter(status__in=["pending", "submitted"])
        .select_related("project", "requested_by")
        .order_by("-created_at")[:10]
    )

    # === ISSUES ACTIVOS (top 10) ===
    active_issues = (
        Issue.objects.filter(status__in=["open", "in_progress"])
        .select_related("project")
        .order_by("-created_at")[:10]
    )

    # === RFIs ABIERTOS ===
    active_rfis = (
        RFI.objects.filter(status="open").select_related("project").order_by("-created_at")[:10]
    )

    # === TIEMPO HOY POR PROYECTO ===
    entries_today = TimeEntry.objects.filter(date=today).select_related("employee", "project")
    hours_by_project = {}
    for entry in entries_today:
        if entry.project:
            proj_name = entry.project.name
            if proj_name not in hours_by_project:
                hours_by_project[proj_name] = Decimal("0")
            hours_by_project[proj_name] += Decimal(entry.hours_worked or 0)

    # === PROYECTOS CON PROGRESO (usando Gantt V2/V1) ===
    from core.services.schedule_unified import get_project_progress
    
    active_projects = Project.objects.filter(end_date__isnull=True).order_by("name")
    project_summary = []
    for project in active_projects:
        # Calcular progreso usando Gantt V2/V1
        gantt_progress = get_project_progress(project)
        progress_pct = gantt_progress.get('progress_percent', 0)
        
        # Fallback si no hay Gantt data
        if gantt_progress.get('total_items', 0) == 0:
            try:
                metrics = compute_project_ev(project, as_of=today)
                if metrics and metrics.get("PV") and metrics["PV"] > 0:
                    progress_pct = min(100, (metrics.get("EV", 0) / metrics["PV"]) * 100)
            except Exception:
                pass

        project_summary.append(
            {
                "project": project,
                "progress_pct": int(progress_pct),
                "gantt_progress": gantt_progress,
                "hours_today": hours_by_project.get(project.name, 0),
            }
        )

    # Morning Briefing (operational summary for PM)
    morning_briefing = []

    # === TOUCH-UPS PENDIENTES (cross-project) ===
    pending_touchups = (
        Task.objects.filter(
            is_touchup=True, status__in=["Pending", "In Progress"]
        )
        .select_related("project", "assigned_to")
        .order_by("-created_at")[:15]
    )
    pending_touchups_count = Task.objects.filter(
        is_touchup=True, status__in=["Pending", "In Progress"]
    ).count()

    # TouchUps V2 pendientes (nuevo modelo dedicado)
    pending_touchups_v2 = (
        TouchUp.objects.filter(status__in=["open", "in_progress", "review"])
        .select_related("project", "assigned_to", "created_by")
        .prefetch_related("photos")
        .order_by("-created_at")[:20]
    )
    pending_touchups_v2_count = TouchUp.objects.filter(
        status__in=["open", "in_progress", "review"]
    ).count()
    unassigned_touchups_v2_count = TouchUp.objects.filter(
        status__in=["open", "in_progress"], assigned_to__isnull=True
    ).count()

    try:
        if unassigned_time_count > 0:
            morning_briefing.append(
                {
                    "text": _("%d unassigned time entries need review") % unassigned_time_count,
                    "severity": "danger" if unassigned_time_count >= 5 else "warning",
                    "action_url": reverse("unassigned_timeentries"),
                    "action_label": _("Assign"),
                    "category": "problems",
                }
            )
        if pending_materials > 0:
            morning_briefing.append(
                {
                    "text": _("%d material requests pending") % pending_materials,
                    "severity": "warning" if pending_materials >= 3 else "info",
                    "action_url": reverse("materials_requests_list_all"),
                    "action_label": _("Review"),
                    "category": "approvals",
                }
            )
        if open_issues > 0:
            morning_briefing.append(
                {
                    "text": _("%d active issues across projects") % open_issues,
                    "severity": "warning" if open_issues < 5 else "danger",
                    "action_url": reverse("pm_select_project", args=["overview"]),
                    "action_label": _("View"),
                    "category": "problems",
                }
            )
        if open_rfis > 0:
            morning_briefing.append(
                {
                    "text": _("%d open RFIs require responses") % open_rfis,
                    "severity": "info",
                    "action_url": reverse("changeorder_board"),
                    "action_label": _("RFIs"),
                    "category": "approvals",
                }
            )
        if pending_touchups_count > 0:
            morning_briefing.append(
                {
                    "text": _("%d touch-ups pending across projects") % pending_touchups_count,
                    "severity": "warning" if pending_touchups_count >= 5 else "info",
                    "action_url": reverse("pm_select_project", args=["touchups"]),
                    "action_label": _("Review"),
                    "category": "problems",
                }
            )
    except Exception:
        morning_briefing = []

    # Filter handling
    active_filter = request.GET.get("filter", "all")
    if active_filter == "problems":
        morning_briefing = [item for item in morning_briefing if item.get("category") == "problems"]
    elif active_filter == "approvals":
        morning_briefing = [
            item for item in morning_briefing if item.get("category") == "approvals"
        ]

    # === SWITCH OPTIONS (para cambiar proyecto/CO cuando hay entrada abierta) ===
    switch_options = {"other_projects": [], "available_cos": [], "current_project_cos": [], "can_switch_to_base": False}
    if open_entry:
        # Otros proyectos (PM puede ver todos, excluir el actual)
        other_projects = Project.objects.filter(is_archived=False).exclude(id=open_entry.project_id)[:10]
        switch_options["other_projects"] = [
            {"id": p.id, "name": p.name}
            for p in other_projects
        ]
        
        # COs del proyecto actual (disponibles para trabajo)
        # Incluir draft, pending, approved, sent, billed (excluir solo 'paid' que ya está cerrado)
        current_project_cos = ChangeOrder.objects.filter(
            project=open_entry.project,
            status__in=['draft', 'pending', 'approved', 'sent', 'billed']
        ).exclude(id=open_entry.change_order_id if open_entry.change_order else None)
        cos_list = [
            {"id": co.id, "title": co.title, "pricing_type": co.pricing_type, "pricing_label": f"${co.amount}" if co.pricing_type == 'fixed' else "T&M"}
            for co in current_project_cos
        ]
        switch_options["current_project_cos"] = cos_list
        switch_options["available_cos"] = cos_list
        
        # Puede volver a base si actualmente está en un CO
        switch_options["can_switch_to_base"] = open_entry.change_order is not None

    context = {
        # Alertas
        "unassigned_time_count": unassigned_time_count,
        "pending_materials": pending_materials,
        "open_issues": open_issues,
        "open_rfis": open_rfis,
        "today_plans": today_plans,
        # Listas
        "pending_materials_list": pending_materials_list,
        "active_issues": active_issues,
        "active_rfis": active_rfis,
        "project_summary": project_summary,
        # Touch-ups
        "pending_touchups": pending_touchups,
        "pending_touchups_count": pending_touchups_count,
        "pending_touchups_v2": pending_touchups_v2,
        "pending_touchups_v2_count": pending_touchups_v2_count,
        "unassigned_touchups_v2_count": unassigned_touchups_v2_count,
        # Context
        "today": today,
        "now": now,
        "show_language_prompt": show_language_prompt,
        # Briefing
        "morning_briefing": morning_briefing,
        "active_filter": active_filter,
        # Clock in/out para PM
        "employee": employee,
        "open_entry": open_entry,
        "form": form,
        "switch_options": switch_options,
        # Badges for notifications
        "badges": {"unread_notifications_count": 0},  # Placeholder
    }

    return render(request, "core/dashboard_pm.html", context)



# --- PM: seleccionar proyecto por acción ---
@login_required
def pm_select_project(request, action: str):
    if not request.user.is_staff:
        messages.error(request, _("Access restricted to PM/Staff only."))
        return redirect("dashboard_employee")

    projects = Project.objects.all().order_by("name")

    if request.method == "POST":
        project_id = request.POST.get("project")
        try:
            pid = int(project_id)
        except (TypeError, ValueError):
            pid = None
        if not pid:
            messages.error(request, _("Please select a project."))
            return render(
                request, "core/pm_select_project.html", {"action": action, "projects": projects}
            )

        target = {
            "materials": "materials_request",
            "tasks": "task_list",
            "pickup": "pickup_view",
            "schedule": "project_schedule",
            "damages": "damage_report_list",
            "inventory": "inventory_view",
            "ev": "project_ev",
            "overview": "project_overview",
            "direct_purchase": "materials_direct_purchase",
            "touchups": "touchup_board",
            "chat": "project_chat_premium",
            "plans": "floor_plan_list",
            "colors": "color_sample_list",
            "dailylogs": "daily_log",
        }.get(action)

        if not target:
            messages.error(request, _("Unsupported action: %(action)s") % {"action": action})
            return render(
                request, "core/pm_select_project.html", {"action": action, "projects": projects}
            )

        return redirect(reverse(target, args=[pid]))

    return render(request, "core/pm_select_project.html", {"action": action, "projects": projects})



# --- DESIGNER & SUPERINTENDENT DASHBOARDS ---
@login_required
def dashboard_designer(request):
    """Dashboard for designers - read-only access to projects, plans, color samples, chat."""
    from django.db import models as db_models

    profile = getattr(request.user, "profile", None)
    is_designer = profile and profile.role == "designer"
    if not is_designer and not request.user.is_superuser:
        return HttpResponseForbidden("Acceso restringido a diseñadores")

    # Projects the designer is involved with (via ColorSample, FloorPlan, or chat)
    projects = (
        Project.objects.filter(
            db_models.Q(color_samples__isnull=False)
            | db_models.Q(floor_plans__isnull=False)
            | db_models.Q(chat_channels__participants=request.user)
        )
        .distinct()
        .order_by("-created_at")[:10]
    )

    # Recent color samples
    color_samples = (
        ColorSample.objects.filter(project__in=projects)
        .select_related("project")
        .order_by("-created_at")[:15]
    )

    # Floor plans
    plans = (
        FloorPlan.objects.filter(project__in=projects)
        .select_related("project")
        .order_by("-created_at")[:10]
    )

    # Recent schedules
    schedules = (
        Schedule.objects.filter(project__in=projects)
        .select_related("project")
        .order_by("-start_datetime")[:10]
    )

    # === MORNING BRIEFING (Design Tasks) ===
    morning_briefing = []

    # Category: designs (New color samples)
    if color_samples:
        count = len(color_samples)
        morning_briefing.append(
            {
                "text": f"Hay {count} nueva{'s' if count > 1 else ''} muestra{'s' if count > 1 else ''} de color",
                "severity": "info",
                "action_url": "#",
                "action_label": "Ver muestras",
                "category": "designs",
            }
        )

    # Category: documents (Plans uploaded)
    if plans:
        count = len(plans)
        morning_briefing.append(
            {
                "text": f"{count} plano{'s' if count > 1 else ''} disponible{'s' if count > 1 else ''} para revisar",
                "severity": "info",
                "action_url": "#",
                "action_label": "Ver planos",
                "category": "documents",
            }
        )

    # Category: schedule (Upcoming meetings)
    if schedules:
        morning_briefing.append(
            {
                "text": f"Tienes {len(schedules)} reunión{'es' if len(schedules) > 1 else ''} programada{'s' if len(schedules) > 1 else ''}",
                "severity": "info",
                "action_url": "#",
                "action_label": "Ver calendario",
                "category": "schedule",
            }
        )

    # Apply filter if requested
    active_filter = request.GET.get("filter", "all")
    if active_filter != "all":
        morning_briefing = [
            item for item in morning_briefing if item.get("category") == active_filter
        ]

    context = {
        "projects": projects,
        "color_samples": color_samples,
        "plans": plans,
        "schedules": schedules,
        "morning_briefing": morning_briefing,
        "active_filter": active_filter,
    }

    return render(request, "core/dashboard_designer.html", context)



@login_required
def dashboard_superintendent(request):
    """Dashboard for superintendents - manage damage reports, touch-ups, task assignments."""
    profile = getattr(request.user, "profile", None)
    if not profile or profile.role != "superintendent":
        return HttpResponseForbidden("Acceso restringido a superintendentes")

    employee = Employee.objects.filter(user=request.user).first()

    # Projects assigned to this superintendent (via damage reports or tasks)
    project_ids = set()

    # Via damage reports
    damage_projects = DamageReport.objects.values_list("project_id", flat=True).distinct()
    project_ids.update(damage_projects)

    # Via assigned touch-ups
    if employee:
        touchup_projects = (
            Task.objects.filter(assigned_to=employee, is_touchup=True)
            .values_list("project_id", flat=True)
            .distinct()
        )
        project_ids.update(touchup_projects)

    projects = Project.objects.filter(id__in=project_ids).order_by("-created_at")[:10]

    # Open damage reports
    damages = (
        DamageReport.objects.filter(project__in=projects, status__in=["reported", "in_repair"])
        .select_related("project", "reported_by")
        .order_by("-created_at")[:15]
    )

    # Assigned touch-ups
    touchups = (
        (
            Task.objects.filter(
                assigned_to=employee, is_touchup=True, status__in=["Pending", "In Progress"]
            )
            .select_related("project")
            .order_by("-created_at")[:15]
        )
        if employee
        else Task.objects.none()
    )

    # Unassigned touch-ups (for assignment)
    unassigned_touchups = (
        Task.objects.filter(
            project__in=projects, is_touchup=True, assigned_to__isnull=True, status="Pending"
        )
        .select_related("project")
        .order_by("-created_at")[:10]
    )

    # === MORNING BRIEFING (On-site Management) ===
    morning_briefing = []

    # Category: issues (Damage reports)
    if damages:
        count = len(damages)
        morning_briefing.append(
            {
                "text": f"Hay {count} {'reporte de daño' if count == 1 else 'reportes de daño'} en progreso",
                "severity": "danger" if count > 3 else "warning",
                "action_url": "#",
                "action_label": "Ver reportes",
                "category": "issues",
            }
        )

    # Category: tasks (Touch-ups to assign)
    if unassigned_touchups:
        count = len(unassigned_touchups)
        morning_briefing.append(
            {
                "text": f"Hay {count} {'reparación' if count == 1 else 'reparaciones'} sin asignar",
                "severity": "warning",
                "action_url": "#",
                "action_label": "Asignar",
                "category": "tasks",
            }
        )

    # Category: progress (My touch-ups)
    if touchups:
        count = len(touchups)
        morning_briefing.append(
            {
                "text": f"Tú tienes {count} {'reparación' if count == 1 else 'reparaciones'} asignada{'s' if count > 1 else ''}",
                "severity": "info",
                "action_url": "#",
                "action_label": "Ver mis reparaciones",
                "category": "progress",
            }
        )

    # Apply filter if requested
    active_filter = request.GET.get("filter", "all")
    if active_filter != "all":
        morning_briefing = [
            item for item in morning_briefing if item.get("category") == active_filter
        ]

    return render(
        request,
        "core/dashboard_superintendent.html",
        {
            "projects": projects,
            "damages": damages,
            "touchups": touchups,
            "unassigned_touchups": unassigned_touchups,
            "morning_briefing": morning_briefing,
            "active_filter": active_filter,
        },
    )


