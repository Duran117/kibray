"""Admin dashboard views — main admin dashboard, executive BI, master schedule."""
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

    # Prefetch budget_lines + progress_points to avoid N+1 inside compute_project_ev
    from django.db.models import Prefetch
    from core.models import BudgetLine
    from core.services.earned_value import bulk_compute_actual_costs
    active_projects_qs = (
        Project.objects.filter(end_date__isnull=True)
        .prefetch_related(
            Prefetch(
                "budget_lines",
                queryset=BudgetLine.objects.prefetch_related("progress_points"),
            )
        )
        .order_by("name")
    )
    active_projects_list = list(active_projects_qs)
    # Bulk-compute Actual Costs for all active projects in 3 queries total
    ac_by_project = bulk_compute_actual_costs(
        [p.id for p in active_projects_list], as_of=today
    )
    for project in active_projects_list:
        try:
            metrics = compute_project_ev(
                project, as_of=today, prefetched_ac=ac_by_project.get(project.id)
            )
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




# --- EXECUTIVE BI DASHBOARD (Module 21) ---
@login_required
def executive_bi_dashboard(request):
    """High-level consolidated business intelligence dashboard.

    Uses FinancialAnalyticsService to avoid duplicated financial logic across
    various views and ensures consistency of KPIs.

    Supports cache invalidation via ?refresh query parameter.
    """
    if not (request.user.is_superuser or request.user.is_staff):
        messages.error(request, _("Acceso solo para Admin/Staff."))
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
        messages.error(request, _("Acceso solo para Admin/Staff."))
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
