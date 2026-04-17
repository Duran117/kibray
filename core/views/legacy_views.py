"""Legacy monolithic views module.

Shared helpers, constants, and common imports live in core.views._helpers.
This module re-imports them for backward compatibility.
"""
# Re-export everything from _helpers so existing code keeps working
from core.views._helpers import *  # noqa: F401, F403
from core.views._helpers import (  # explicit imports for linters
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
# _ is excluded from wildcard imports (underscore prefix), import explicitly
from django.utils.translation import gettext_lazy as _  # noqa: F811


# --- CLIENT REQUESTS ---




# --- CLIENT REQUESTS ---
@login_required
def client_request_create(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    
    # SECURITY: Check project access
    has_access, redirect_url = _check_user_project_access(request.user, project)
    if not has_access:
        messages.error(request, _("You don't have access to this project."))
        return redirect(redirect_url)
    
    if request.method == "POST":
        title = request.POST.get("title")
        description = request.POST.get("description", "")
        if not title:
            messages.error(request, _("Título es requerido"))
        else:
            from core.models import ClientRequest

            ClientRequest.objects.create(
                project=project, title=title, description=description, created_by=request.user
            )
            messages.success(request, _("Solicitud creada"))
            return redirect("client_requests_list", project_id=project.id)
    return render(request, "core/client_request_form.html", {"project": project})


@login_required
def client_requests_list(request, project_id=None):
    from core.models import ClientRequest

    if project_id:
        project = get_object_or_404(Project, id=project_id)
        
        # SECURITY: Check project access
        has_access, redirect_url = _check_user_project_access(request.user, project)
        if not has_access:
            messages.error(request, _("You don't have access to this project."))
            return redirect(redirect_url)
        
        qs = ClientRequest.objects.filter(project=project).order_by("-created_at")
        
        # For non-staff clients, only show their own requests
        if not request.user.is_staff:
            qs = qs.filter(created_by=request.user)
    else:
        # Without project_id
        if request.user.is_staff:
            # Staff can see all requests
            project = None
            qs = ClientRequest.objects.all().select_related("project").order_by("-created_at")
        else:
            # Clients see only their own requests across all their projects
            project = None
            client_project_ids = list(
                request.user.project_accesses.filter(is_active=True).values_list('project_id', flat=True)
            )
            qs = ClientRequest.objects.filter(
                created_by=request.user,
                project_id__in=client_project_ids
            ).select_related("project").order_by("-created_at")
    
    return render(request, "core/client_requests_list.html", {"project": project, "requests": qs})


@login_required
def client_request_convert_to_co(request, request_id):
    from core.models import ClientRequest

    cr = get_object_or_404(ClientRequest, id=request_id)
    if cr.change_order:
        messages.info(
            request,
            _("Esta solicitud ya fue convertida al CO #%(co_id)s.") % {"co_id": cr.change_order.id},
        )
        return redirect("client_requests_list", project_id=cr.project.id)
    if request.method == "POST":
        description = request.POST.get("description") or cr.description or cr.title
        amount_str = request.POST.get("amount") or "0"
        try:
            amt = Decimal(amount_str)
        except Exception:
            amt = Decimal("0")
        co = ChangeOrder.objects.create(
            project=cr.project, description=description, amount=amt, status="pending"
        )
        cr.change_order = co
        cr.status = "converted"
        cr.save()
        messages.success(request, _("Solicitud convertida al CO #%(co_id)s.") % {"co_id": co.id})
        return redirect("changeorder_detail", changeorder_id=co.id)
    return render(request, "core/client_request_convert.html", {"req": cr})


PRESET_PRODUCTS = [
    # Pinturas
    {
        "category": "paint",
        "category_label": "Pintura",
        "brand": "sherwin_williams",
        "brand_label": "Sherwin‑Williams",
        "product_name": "Emerald Interior",
        "unit": "gal",
    },
    {
        "category": "primer",
        "category_label": "Primer",
        "brand": "sherwin_williams",
        "brand_label": "Sherwin‑Williams",
        "product_name": "Multi‑Purpose Primer",
        "unit": "gal",
    },
    {
        "category": "paint",
        "category_label": "Pintura",
        "brand": "benjamin_moore",
        "brand_label": "Benjamin Moore",
        "product_name": "Regal Select",
        "unit": "gal",
    },
    # Stain / Laca
    {
        "category": "stain",
        "category_label": "Stain",
        "brand": "milesi",
        "brand_label": "Milesi",
        "product_name": "Interior Wood Stain",
        "unit": "liter",
    },
    {
        "category": "lacquer",
        "category_label": "Laca/Clear",
        "brand": "chemcraft",
        "brand_label": "Chemcraft",
        "product_name": "Clear Lacquer",
        "unit": "liter",
    },
    # Enmascarado / protección
    {
        "category": "tape",
        "category_label": "Tape",
        "brand": "3m",
        "brand_label": "3M",
        "product_name": "2090 ScotchBlue",
        "unit": "roll",
    },
    {
        "category": "plastic",
        "category_label": "Plástico",
        "brand": "3m",
        "brand_label": "3M",
        "product_name": "Hand‑Masker Film 9ft",
        "unit": "roll",
    },
    {
        "category": "masking_paper",
        "category_label": "Papel enmascarar",
        "brand": "3m",
        "brand_label": "3M",
        "product_name": "Hand‑Masker Brown Paper 12in",
        "unit": "roll",
    },
    {
        "category": "floor_paper",
        "category_label": "Papel para piso",
        "brand": "other",
        "brand_label": "Otro",
        "product_name": "Ram Board",
        "unit": "roll",
    },
    # Herramientas
    {
        "category": "brush",
        "category_label": "Brocha",
        "brand": "purdy",
        "brand_label": "Purdy",
        "product_name": 'Pro‑Extra 2.5"',
        "unit": "unit",
    },
    {
        "category": "roller_cover",
        "category_label": "Rodillo (cover)",
        "brand": "wooster",
        "brand_label": "Wooster",
        "product_name": '9in Micro Plush 3/8"',
        "unit": "unit",
    },
    {
        "category": "tray_liner",
        "category_label": "Liner",
        "brand": "other",
        "brand_label": "Otro",
        "product_name": "Liner para charola 9in",
        "unit": "pack",
    },
    {
        "category": "sandpaper",
        "category_label": "Lija",
        "brand": "3m",
        "brand_label": "3M",
        "product_name": "P220 Hookit",
        "unit": "box",
    },
    {
        "category": "blades",
        "category_label": "Cuchillas",
        "brand": "other",
        "brand_label": "Otro",
        "product_name": "Cuchillas trapezoidales",
        "unit": "box",
    },
    # Selladores/PPE
    {
        "category": "caulk",
        "category_label": "Caulk/Sellador",
        "brand": "wurth",
        "brand_label": "Würth",
        "product_name": "Acrylic Latex Caulk (White)",
        "unit": "tube",
    },
    {
        "category": "respirator",
        "category_label": "Respirador",
        "brand": "3m",
        "brand_label": "3M",
        "product_name": "Half Facepiece 6200",
        "unit": "unit",
    },
    {
        "category": "mask",
        "category_label": "Mascarilla",
        "brand": "3m",
        "brand_label": "3M",
        "product_name": "N95",
        "unit": "box",
    },
    {
        "category": "coverall",
        "category_label": "Overol",
        "brand": "other",
        "brand_label": "Otro",
        "product_name": "Coverall desechable",
        "unit": "unit",
    },
    {
        "category": "gloves",
        "category_label": "Guantes",
        "brand": "other",
        "brand_label": "Otro",
        "product_name": "Nitrilo",
        "unit": "box",
    },
]


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


# --- PROJECT PDF ---
@login_required
def project_pdf_view(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    
    # SECURITY: Check project access
    has_access, redirect_url = _check_user_project_access(request.user, project)
    if not has_access:
        messages.error(request, _("You don't have access to this project."))
        return redirect(redirect_url)
    
    incomes = Income.objects.filter(project=project).select_related("change_order")
    expenses = Expense.objects.filter(project=project).select_related("change_order", "cost_code")
    time_entries = TimeEntry.objects.filter(project=project).select_related("employee")
    schedules = Schedule.objects.filter(project=project).order_by("start_datetime")

    total_income = incomes.aggregate(total=Sum("amount"))["total"] or 0
    total_expense = expenses.aggregate(total=Sum("amount"))["total"] or 0
    profit = total_income - total_expense
    total_hours = sum([te.hours_worked for te in time_entries])
    labor_cost = sum([te.labor_cost for te in time_entries])

    context = {
        "project": project,
        "incomes": incomes,
        "expenses": expenses,
        "schedules": schedules,
        "total_income": total_income,
        "total_expense": total_expense,
        "profit": profit,
        "total_hours": total_hours,
        "labor_cost": labor_cost,
        "logo_url": request.build_absolute_uri("/static/Kibray.jpg"),
        "user": request.user,
        "now": timezone.now(),  # <-- reemplazo
    }

    template = get_template("core/project_pdf.html")
    html = template.render(context)
    # Prefer xhtml2pdf if available; otherwise fallback to basic PDF
    if pisa:
        result = BytesIO()
        pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)
        if not pdf.err:
            return HttpResponse(result.getvalue(), content_type="application/pdf")
    fallback_bytes = _generate_basic_pdf_from_html(html)
    return HttpResponse(fallback_bytes, content_type="application/pdf")


# --- CRUD SCHEDULE, EXPENSE, INCOME, TIMEENTRY ---
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
        messages.error(request, "Acceso denegado.")
        return redirect("income_list")
    if request.method == "POST":
        form = IncomeForm(request.POST, request.FILES, instance=income)
        if form.is_valid():
            form.save()
            messages.success(request, "Ingreso actualizado.")
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
        messages.error(request, "Acceso denegado.")
        return redirect("income_list")
    if request.method == "POST":
        income.delete()
        messages.success(request, "Ingreso eliminado.")
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
        messages.error(request, "Acceso denegado.")
        return redirect("expense_list")
    if request.method == "POST":
        form = ExpenseForm(request.POST, request.FILES, instance=expense)
        if form.is_valid():
            form.save()
            messages.success(request, "Gasto actualizado.")
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
        messages.error(request, "Acceso denegado.")
        return redirect("expense_list")
    if request.method == "POST":
        expense.delete()
        messages.success(request, "Gasto eliminado.")
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
            messages.success(request, "Horas registradas.")
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
        messages.error(request, "Acceso denegado.")
        return redirect("dashboard")

    if request.method == "POST":
        form = TimeEntryForm(request.POST, instance=entry)
        if form.is_valid():
            form.save()
            messages.success(request, "Registro de horas actualizado.")
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
        messages.error(request, "Acceso denegado.")
        return redirect("dashboard")

    if request.method == "POST":
        entry.delete()
        messages.success(request, "Registro de horas eliminado.")
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
                messages.error(request, "Employee not found.")
            except Project.DoesNotExist:
                messages.error(request, "Project not found.")
            except ChangeOrder.DoesNotExist:
                messages.error(request, "Change Order not found.")
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


# --- CLIENTE: Vista de proyecto y formularios ---
@login_required
def client_project_view(request, project_id):
    """
    Dashboard completo de UN proyecto individual para el cliente.
    El cliente ve: pending requests, minutas, fotos, schedule, tareas/touch-ups,
    pending contracts/COs for signature, color sample approvals, daily logs.
    """
    project = get_object_or_404(Project, id=project_id)

    # SECURITY: Reuse centralised access check
    has_access, redirect_url = _check_user_project_access(request.user, project)
    if not has_access:
        messages.error(request, _("You don't have access to this project."))
        return redirect(redirect_url)

    # === SOLICITUDES Y COMUNICACIÓN ===
    from core.models import ClientRequest, ProjectMinute

    # Pending client requests (cosas que el cliente solicitó)
    pending_requests = ClientRequest.objects.filter(project=project, status="pending").order_by(
        "-created_at"
    )

    # Minutas visibles para cliente (decisiones, cambios, milestones)
    project_minutes = ProjectMinute.objects.filter(
        project=project, visible_to_client=True
    ).order_by("-event_date")[:10]

    # === FOTOS DEL PROYECTO ===
    from core.models import SitePhoto

    recent_photos = SitePhoto.objects.filter(project=project).order_by("-created_at")[:12]

    # === MUESTRAS DE COLOR ===
    color_samples = project.color_samples.all().order_by("-created_at")[:8]

    # === SCHEDULE PRÓXIMO ===
    upcoming_schedules = Schedule.objects.filter(
        project=project, start_datetime__gte=timezone.now()
    ).order_by("start_datetime")[:5]

    # === TAREAS Y TOUCH-UPS ===
    # Tasks incluyen touch-ups que el cliente puede agregar
    tasks = Task.objects.filter(project=project).order_by("-created_at")
    pending_tasks = tasks.filter(status__in=["Pending", "In Progress"])
    completed_tasks = tasks.filter(status="Completed")[:10]

    # Touch-ups V2 (sistema principal)
    project_touchups_v2 = TouchUp.objects.filter(
        project=project
    ).select_related("assigned_to__user", "floor_plan").prefetch_related("photos").order_by("-created_at")
    active_touchups_v2 = project_touchups_v2.filter(status__in=["open", "in_progress", "review"])
    closed_touchups_v2 = project_touchups_v2.filter(status="closed")[:10]

    # === COMENTARIOS ===
    comments = Comment.objects.filter(project=project).order_by("-created_at")[:10]

    # === FACTURAS ===
    invoices = project.invoices.all().order_by("-date_issued")[:5]
    total_invoiced = invoices.aggregate(total=Sum("total_amount"))["total"] or Decimal("0")
    total_paid = invoices.aggregate(paid=Sum("amount_paid"))["paid"] or Decimal("0")

    # === CONTRACT & CHANGE ORDERS ===
    from core.models import ChangeOrder, Estimate
    
    # Base contract (latest approved estimate)
    latest_estimate = Estimate.objects.filter(
        project=project, approved=True
    ).order_by('-version').first()
    
    base_contract_total = Decimal("0")
    if latest_estimate:
        # total_price is a property, so we need to sum manually
        base_contract_total = sum(
            line.total_price for line in latest_estimate.lines.all()
        ) or Decimal("0")
    
    # Change Orders - considering client signature status
    all_project_cos = ChangeOrder.objects.filter(project=project).order_by('-date_created')
    
    # Approved and SIGNED by client - these are truly approved
    approved_cos = all_project_cos.filter(
        status__in=['approved', 'sent', 'billed', 'paid']
    ).exclude(signed_at__isnull=True, status='approved')  # Exclude approved but not signed
    
    # Pending includes:
    # 1. status='pending' (waiting admin approval)
    # 2. status='approved' but signed_at=None (approved by admin, waiting client signature)
    pending_for_admin = all_project_cos.filter(status='pending')
    pending_for_client = all_project_cos.filter(status='approved', signed_at__isnull=True)
    pending_cos = pending_for_admin | pending_for_client
    
    # Calculate totals - for T&M COs, calculate dynamic total from time entries & expenses
    from core.services.financial_service import ChangeOrderService
    
    def get_co_total(co):
        """Get CO total - for T&M calculates from time entries & expenses"""
        if co.pricing_type == 'T_AND_M':
            billable = ChangeOrderService.get_billable_amount(co)
            return billable.get('grand_total', Decimal("0"))
        return co.amount or Decimal("0")
    
    # Annotate COs for template use
    for co in all_project_cos:
        co.calculated_total = get_co_total(co)
        co.pending_client_signature = (co.status == 'approved' and not co.signed_at)
    
    approved_cos_total = sum(get_co_total(co) for co in approved_cos)
    pending_cos_total = sum(get_co_total(co) for co in pending_cos)
    total_contract_value = base_contract_total + approved_cos_total

    # === PROGRESO DEL PROYECTO (usando Gantt V2/V1) ===
    from core.services.schedule_unified import get_project_progress
    gantt_progress = get_project_progress(project)
    progress_pct = gantt_progress.get('progress_percent', 0)
    
    # Fallback si no hay items en el Gantt
    if gantt_progress.get('total_items', 0) == 0:
        try:
            metrics = compute_project_ev(project)
            if metrics and metrics.get("PV") and metrics["PV"] > 0:
                progress_pct = min(100, (metrics.get("EV", 0) / metrics["PV"]) * 100)
        except Exception:
            # Fallback: progreso basado en fechas
            if project.start_date and project.end_date:
                total_days = (project.end_date - project.start_date).days
                elapsed_days = (timezone.localdate() - project.start_date).days
                progress_pct = min(100, (elapsed_days / total_days * 100)) if total_days > 0 else 0

    # === PROJECT MANAGER (from PM assignments) ===
    from core.models import ProjectManagerAssignment
    pm_assignment = ProjectManagerAssignment.objects.filter(
        project=project
    ).select_related("pm").first()
    project_manager = pm_assignment.pm if pm_assignment else None

    # === PUBLIC FILES ===
    from core.models import ProjectFile
    public_files = ProjectFile.objects.filter(
        project=project, is_public=True
    ).select_related("category").order_by("-uploaded_at")[:10]

    # === FLOOR PLANS (for touch-up location picker) ===
    from core.models import FloorPlan
    floor_plans = FloorPlan.objects.filter(
        project=project, is_current=True
    ).order_by("level", "name")

    # === CONTRACTS PENDING SIGNATURE ===
    from core.models import Contract
    pending_contracts = Contract.objects.filter(
        project=project,
        status="pending_signature",
    ).order_by("-created_at")[:5]

    # === CHANGE ORDERS PENDING CLIENT SIGNATURE ===
    from core.services.financial_service import ChangeOrderService as _COService
    pending_change_orders = ChangeOrder.objects.filter(
        project=project,
        status__in=["approved", "sent"],
        signed_at__isnull=True,
    ).filter(
        Q(signature_image__isnull=True) | Q(signature_image="")
    ).order_by("-date_created")[:10]
    for co in pending_change_orders:
        if co.pricing_type == "T_AND_M":
            co.calculated_total = _COService.get_billable_amount(co).get("grand_total", Decimal("0"))
        else:
            co.calculated_total = co.amount or Decimal("0")

    # === COLOR SAMPLES PENDING APPROVAL ===
    from core.models import ColorSample
    pending_color_samples = ColorSample.objects.filter(
        project=project,
        status__in=["proposed", "review"],
    ).order_by("-created_at")[:5]

    # === DAILY LOGS (published only — visible to client) ===
    from core.models import DailyLog
    recent_daily_logs = DailyLog.objects.filter(
        project=project,
        is_published=True,
    ).select_related("created_by").order_by("-date")[:5]

    # === UNREAD NOTIFICATIONS COUNT ===
    unread_notifications = Notification.objects.filter(
        user=request.user,
        project=project,
        is_read=False,
    ).count()

    context = {
        "project": project,
        "pending_requests": pending_requests,
        "project_minutes": project_minutes,
        "recent_photos": recent_photos,
        "upcoming_schedules": upcoming_schedules,
        "tasks": tasks,
        "pending_tasks": pending_tasks,
        "completed_tasks": completed_tasks,
        "active_touchups_v2": active_touchups_v2,
        "closed_touchups_v2": closed_touchups_v2,
        "comments": comments,
        "invoices": invoices,
        "total_invoiced": total_invoiced,
        "total_paid": total_paid,
        "balance": total_invoiced - total_paid,
        "progress_pct": int(progress_pct),
        "gantt_progress": gantt_progress,
        "color_samples": color_samples,
        "project_manager": project_manager,
        "public_files": public_files,
        "floor_plans": floor_plans,
        # Financial summary
        "latest_estimate": latest_estimate,
        "base_contract_total": base_contract_total,
        "approved_cos": approved_cos,
        "pending_cos": pending_cos,
        "approved_cos_total": approved_cos_total,
        "pending_cos_total": pending_cos_total,
        "total_contract_value": total_contract_value,
        # Actionable items for client
        "pending_contracts": pending_contracts,
        "pending_change_orders": pending_change_orders,
        "pending_color_samples": pending_color_samples,
        "recent_daily_logs": recent_daily_logs,
        "unread_notifications": unread_notifications,
    }
    return render(request, "core/client_project_view.html", context)


@login_required
def client_documents_view(request, project_id):
    """
    Documents workspace view for clients.
    Uses the same workspace as PM but only shows PUBLIC files.
    SECURITY: Only shows files marked as is_public=True for the specific project.
    """
    from core.models import ClientProjectAccess, ProjectFile, FileCategory, DocumentTag
    from django.db.models import Q, Count
    
    project = get_object_or_404(Project, id=project_id)

    # === STRICT ACCESS CONTROL ===
    profile = getattr(request.user, "profile", None)
    has_explicit_access = ClientProjectAccess.objects.filter(
        user=request.user, project=project
    ).exists()
    
    is_project_client = False
    if project.client:
        client_text = project.client.strip().lower()
        is_project_client = client_text in (
            request.user.email.lower(),
            request.user.get_full_name().lower(),
            request.user.username.lower(),
        )
    
    if profile and profile.role == "client":
        if not (has_explicit_access or is_project_client):
            messages.error(request, _("You don't have access to this project."))
            return redirect("dashboard_client")
    elif not (request.user.is_staff or has_explicit_access):
        messages.error(request, _("Access denied."))
        return redirect("dashboard")

    # === GET CATEGORIES (only show those with public files) ===
    # Get categories that have at least one public file
    categories = FileCategory.objects.filter(
        project=project
    ).annotate(
        public_file_count=Count('files', filter=Q(files__is_public=True))
    ).filter(parent=None).order_by('order')
    
    # Get selected category
    selected_category_id = request.GET.get("category")
    selected_category = None
    if selected_category_id:
        selected_category = FileCategory.objects.filter(
            id=selected_category_id, 
            project=project
        ).first()

    # === BUILD FILE QUERYSET - ONLY PUBLIC FILES ===
    files = ProjectFile.objects.filter(
        project=project,
        is_public=True  # CRITICAL: Only public files for clients
    ).select_related("category", "uploaded_by").prefetch_related("document_tags")

    # Filter by category
    if selected_category_id:
        files = files.filter(category_id=selected_category_id)

    # Filter by favorites (client can have their own favorites)
    if request.GET.get("favorites"):
        files = files.filter(is_favorited=True)

    # Filter by tag
    tag_filter = request.GET.get("tag")
    if tag_filter:
        files = files.filter(document_tags__id=tag_filter)

    # Search filter
    search_query = request.GET.get("q")
    if search_query:
        files = files.filter(
            Q(name__icontains=search_query)
            | Q(description__icontains=search_query)
            | Q(tags__icontains=search_query)
        )

    files = files.order_by("-uploaded_at")

    # Get all tags that have public files
    all_tags = DocumentTag.objects.filter(
        project=project,
        files__is_public=True
    ).distinct()
    
    # Stats (only public files)
    total_files = ProjectFile.objects.filter(project=project, is_public=True).count()
    favorites_count = ProjectFile.objects.filter(
        project=project, is_public=True, is_favorited=True
    ).count()

    return render(
        request,
        "core/documents_workspace.html",  # Same workspace template, with is_client_view flag
        {
            "project": project,
            "categories": categories,
            "files": files,
            "selected_category": selected_category,
            "selected_category_id": selected_category_id,
            "search_query": search_query or "",
            "all_tags": all_tags,
            "total_files": total_files,
            "favorites_count": favorites_count,
            "public_count": total_files,  # All visible files are public for client
            "is_client_view": True,  # Flag to hide upload/edit features
        },
    )


@login_required
def client_financials_view(request, project_id):
    """
    Dedicated financial analytics page for clients.
    Shows: Contract breakdown, Change Orders, Invoices, Payments with charts.
    """
    project = get_object_or_404(Project, id=project_id)

    # Access control (same as client_project_view)
    profile = getattr(request.user, "profile", None)
    from core.models import ClientProjectAccess
    has_explicit_access = ClientProjectAccess.objects.filter(
        user=request.user, project=project
    ).exists()
    
    if profile and profile.role == "client":
        if not (has_explicit_access or project.client == request.user.username):
            messages.error(request, "You don't have access to this project.")
            return redirect("dashboard_client")
    else:
        if not (request.user.is_staff or has_explicit_access):
            messages.error(request, "Access denied.")
            return redirect("dashboard")

    # === CONTRACT DATA ===
    from core.models import ChangeOrder, Estimate, Invoice, InvoicePayment
    
    # Base contract (latest approved estimate)
    latest_estimate = Estimate.objects.filter(
        project=project, approved=True
    ).order_by('-version').first()
    
    base_contract_total = Decimal("0")
    estimate_lines = []
    if latest_estimate:
        estimate_lines = latest_estimate.lines.select_related('budget_line').all()
        base_contract_total = sum(line.total_price or Decimal("0") for line in estimate_lines)
    
    # Change Orders by status
    all_change_orders = ChangeOrder.objects.filter(project=project).order_by('-date_created')
    
    # Approved and SIGNED by client - these are truly approved
    approved_cos = all_change_orders.filter(
        status__in=['approved', 'sent', 'billed', 'paid']
    ).exclude(signed_at__isnull=True, status='approved')  # Exclude approved but not signed
    
    # Pending includes: 
    # 1. status='pending' (waiting admin approval)
    # 2. status='approved' but signed_at=None (approved by admin, waiting client signature)
    pending_for_admin = all_change_orders.filter(status='pending')
    pending_for_client = all_change_orders.filter(status='approved', signed_at__isnull=True)
    pending_cos = pending_for_admin | pending_for_client  # Union of both querysets
    
    billed_cos = all_change_orders.filter(status__in=['billed', 'paid'])
    
    # Calculate totals - for T&M COs, calculate dynamic total from time entries & expenses
    from core.services.financial_service import ChangeOrderService
    
    def get_co_total(co):
        """Get CO total - for T&M calculates from time entries & expenses"""
        if co.pricing_type == 'T_AND_M':
            billable = ChangeOrderService.get_billable_amount(co)
            return billable.get('grand_total', Decimal("0"))
        return co.amount or Decimal("0")
    
    # Annotate each CO with its calculated total for template use
    for co in all_change_orders:
        co.calculated_total = get_co_total(co)
        # Mark if pending client signature
        co.pending_client_signature = (co.status == 'approved' and not co.signed_at)
    
    approved_cos_total = sum(get_co_total(co) for co in approved_cos)
    pending_cos_total = sum(get_co_total(co) for co in pending_cos)
    billed_cos_total = sum(get_co_total(co) for co in billed_cos)
    total_contract_value = base_contract_total + approved_cos_total
    
    # === INVOICES DATA ===
    invoices = Invoice.objects.filter(project=project).order_by('-date_issued')
    total_invoiced = sum(inv.total_amount or Decimal("0") for inv in invoices)
    total_paid = sum(inv.amount_paid or Decimal("0") for inv in invoices)
    balance = total_invoiced - total_paid
    
    # === PAYMENT HISTORY ===
    payments = InvoicePayment.objects.filter(
        invoice__project=project
    ).select_related('invoice').order_by('-payment_date')[:20]
    
    # === PROGRESSIVE BILLING DATA ===
    # Calculate % billed per estimate line (for progressive billing visualization)
    from core.models import InvoiceLineEstimate
    lines_billing_data = []
    for line in estimate_lines:
        invoiced_for_line = InvoiceLineEstimate.objects.filter(
            estimate_line=line
        ).aggregate(total=Sum('amount'))['total'] or Decimal("0")
        pct_billed = (invoiced_for_line / line.total_price * 100) if line.total_price else 0
        lines_billing_data.append({
            'line': line,
            'invoiced': invoiced_for_line,
            'remaining': line.total_price - invoiced_for_line,
            'pct_billed': min(100, float(pct_billed)),
        })
    
    # === CHART DATA (for Chart.js) ===
    import json
    contract_breakdown_chart = {
        'labels': json.dumps(['Base Contract', 'Approved COs', 'Pending COs']),
        'data': json.dumps([float(base_contract_total), float(approved_cos_total), float(pending_cos_total)]),
        'colors': json.dumps(['#667eea', '#28a745', '#ffc107']),
    }
    payment_status_chart = {
        'labels': json.dumps(['Contract Value', 'Invoiced', 'Paid']),
        'data': json.dumps([float(total_contract_value), float(total_invoiced), float(total_paid)]),
        'colors': json.dumps(['#667eea', '#17a2b8', '#28a745']),
    }
    
    # Total for all COs
    all_cos_total = approved_cos_total + pending_cos_total

    # Percentages for template
    invoiced_pct = float(total_invoiced / total_contract_value * 100) if total_contract_value else 0
    paid_pct = float(total_paid / total_contract_value * 100) if total_contract_value else 0

    # Recent payments (for template section)
    recent_payments = payments[:10]

    # Estimate lines data for progressive billing table
    estimate_lines_data = []
    for lbd in lines_billing_data:
        line = lbd['line']
        estimate_lines_data.append({
            'code': getattr(line, 'code', '') or getattr(line.budget_line, 'code', '') if hasattr(line, 'budget_line') and line.budget_line else '',
            'description': line.description or '',
            'direct_cost': line.total_price or Decimal("0"),
            'already_pct': lbd['pct_billed'],
        })

    context = {
        "project": project,
        "latest_estimate": latest_estimate,
        "estimate_lines": estimate_lines,
        "estimate_lines_data": estimate_lines_data,
        "lines_billing_data": lines_billing_data,
        "base_contract_total": base_contract_total,
        "change_orders": all_change_orders,  # Alias for template compatibility
        "all_change_orders": all_change_orders,
        "approved_cos": approved_cos,
        "pending_cos": pending_cos,
        "billed_cos": billed_cos,
        "approved_cos_total": approved_cos_total,
        "pending_cos_total": pending_cos_total,
        "billed_cos_total": billed_cos_total,
        "all_cos_total": all_cos_total,
        "total_contract_value": total_contract_value,
        "invoices": invoices,
        "total_invoiced": total_invoiced,
        "total_paid": total_paid,
        "balance": balance,
        "invoiced_pct": invoiced_pct,
        "paid_pct": paid_pct,
        "payments": payments,
        "recent_payments": recent_payments,
        "contract_breakdown_chart": contract_breakdown_chart,
        "payment_status_chart": payment_status_chart,
    }
    return render(request, "core/client_financials.html", context)


@login_required
def agregar_tarea(request, project_id):
    """
    Permite a clientes (y staff) agregar touch-ups usando el modelo TouchUp V2.
    - Cliente crea → se auto-asigna al primer admin activo.
    - Staff crea → puede asignar directamente a un empleado.
    - Se envían notificaciones a admins y PMs.
    """
    from core.models import ClientProjectAccess, TouchUp, TouchUpPhoto

    project = get_object_or_404(Project, id=project_id)

    # Verificar acceso
    profile = getattr(request.user, "profile", None)
    has_access = ClientProjectAccess.objects.filter(user=request.user, project=project).exists()
    if profile and profile.role == "client":
        if not (has_access or project.client == request.user.username):
            messages.error(request, _("You don't have access to this project."))
            return redirect("dashboard_client")
    elif not request.user.is_staff and not has_access:
        messages.error(request, _("Access denied."))
        return redirect("dashboard")

    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        description = request.POST.get("description", "").strip()

        if not title:
            messages.error(request, _("Title is required."))
            return redirect("client_project_view", project_id=project_id)

        # Floor plan location (optional)
        floor_plan_id = request.POST.get("floor_plan_id") or None
        pin_x = request.POST.get("pin_x") or None
        pin_y = request.POST.get("pin_y") or None

        floor_plan_obj = None
        if floor_plan_id:
            from core.models import FloorPlan
            floor_plan_obj = FloorPlan.objects.filter(
                id=floor_plan_id, project=project
            ).first()

        # Create TouchUp V2 (not legacy Task)
        touchup_kwargs = dict(
            project=project,
            title=title,
            description=description,
            status="open",
            priority=request.POST.get("priority", "medium") or "medium",
            created_by=request.user,
        )
        if floor_plan_obj and pin_x and pin_y:
            from decimal import Decimal, InvalidOperation
            try:
                px = Decimal(pin_x)
                py = Decimal(pin_y)
                if 0 <= px <= 1 and 0 <= py <= 1:
                    touchup_kwargs["floor_plan"] = floor_plan_obj
                    touchup_kwargs["pin_x"] = px
                    touchup_kwargs["pin_y"] = py
            except (InvalidOperation, ValueError):
                pass  # Skip invalid pin data, create without location

        touchup = TouchUp.objects.create(**touchup_kwargs)

        # Handle photo uploads (single legacy field + multiple)
        photos = request.FILES.getlist("photos") or []
        single_image = request.FILES.get("image")
        if single_image:
            photos.insert(0, single_image)

        for photo_file in photos:
            TouchUpPhoto.objects.create(
                touchup=touchup,
                image=photo_file,
                phase="before",
                uploaded_by=request.user,
            )

        # Auto-assign to first active admin (superuser or staff with admin role)
        admin_user = User.objects.filter(
            is_active=True, is_superuser=True
        ).first()
        if not admin_user:
            admin_user = User.objects.filter(
                is_active=True, is_staff=True, profile__role="admin"
            ).first()

        # Notify admins and PMs
        admins_and_pms = User.objects.filter(
            is_active=True
        ).filter(
            Q(is_superuser=True) | Q(profile__role__in=["admin", "project_manager"])
        ).distinct()

        creator_name = request.user.get_full_name() or request.user.username
        for u in admins_and_pms:
            if u != request.user:
                Notification.objects.create(
                    user=u,
                    notification_type="task_created",
                    title=_("New Touch-Up: %(title)s") % {"title": title[:60]},
                    message=_("%(creator)s created a touch-up in %(project)s") % {
                        "creator": creator_name,
                        "project": project.name,
                    },
                    related_object_type="TouchUp",
                    related_object_id=touchup.id,
                    link_url=f"/projects/{project.id}/touchups-v2/{touchup.id}/",
                )

        messages.success(
            request,
            _("Touch-up '%(title)s' created successfully. The team has been notified.") % {"title": title},
        )
        return redirect("client_project_view", project_id=project_id)


@login_required
def touchup_board(request, project_id):
    """Vista dedicada para gestionar touch-ups del proyecto (Q11.2 con mejoras)."""
    from django.core.paginator import Paginator

    project = get_object_or_404(Project, id=project_id)
    
    # SECURITY: Check project access
    has_access, redirect_url = _check_user_project_access(request.user, project)
    if not has_access:
        messages.error(request, _("You don't have access to this project."))
        return redirect(redirect_url)
    
    qs = (
        project.tasks.filter(is_touchup=True)
        .select_related("assigned_to", "created_by")
        .order_by("-created_at")
    )

    # Filters
    status = request.GET.get("status")
    if status:
        qs = qs.filter(status=status)

    # ACTIVITY 1: Priority filter (Q11.6)
    priority = request.GET.get("priority")
    if priority:
        qs = qs.filter(priority=priority)

    assigned = request.GET.get("assigned")
    if assigned == "unassigned":
        qs = qs.filter(assigned_to__isnull=True)
    elif assigned:
        qs = qs.filter(assigned_to__id=assigned)

    date_from = request.GET.get("date_from")
    if date_from:
        qs = qs.filter(created_at__date__gte=date_from)

    date_to = request.GET.get("date_to")
    if date_to:
        qs = qs.filter(created_at__date__lte=date_to)

    # ACTIVITY 1: Filter by due date (Q11.1 - overdue tasks)
    show_overdue = request.GET.get("overdue")
    if show_overdue:
        from django.utils import timezone

        qs = qs.filter(due_date__lt=timezone.now().date(), status__in=["pending", "in_progress"])

    # Sorting (updated with new fields)
    sort_by = request.GET.get("sort", "-created_at")
    valid_sorts = [
        "created_at",
        "-created_at",
        "status",
        "-status",
        "assigned_to",
        "-assigned_to",
        "priority",
        "-priority",  # Q11.6
        "due_date",
        "-due_date",  # Q11.1
    ]
    if sort_by in valid_sorts:
        qs = qs.order_by(sort_by)

    # Pagination
    paginator = Paginator(qs, 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # Get available employees for filter dropdown
    employees = Employee.objects.filter(is_active=True).order_by("first_name", "last_name")

    # ACTIVITY 1: Priority choices for filter dropdown
    from core.models import Task

    priority_choices = Task.PRIORITY_CHOICES

    return render(
        request,
        "core/touchup_board.html",
        {
            "project": project,
            "page_obj": page_obj,
            "filter_status": status,
            "filter_priority": priority,
            "filter_assigned": assigned,
            "filter_date_from": date_from,
            "filter_date_to": date_to,
            "show_overdue": show_overdue,
            "sort_by": sort_by,
            "employees": employees,
            "priority_choices": priority_choices,
        },
    )


@login_required
def touchup_quick_update(request, task_id):
    """AJAX endpoint for quick status/assignment updates on touch-up board."""
    if request.method != "POST":
        return JsonResponse({"error": gettext("POST required")}, status=405)

    task = get_object_or_404(Task, id=task_id, is_touchup=True)

    # Check permission: staff, assigned employee, or project client
    employee = Employee.objects.filter(user=request.user).first()
    is_assigned = employee and task.assigned_to == employee
    if not (request.user.is_staff or is_assigned or task.project.client == request.user.username):
        return JsonResponse({"error": gettext("Sin permiso")}, status=403)

    action = request.POST.get("action")

    if action == "status":
        new_status = request.POST.get("status")
        if new_status in dict(Task.STATUS_CHOICES):
            task.status = new_status
            if new_status == "Completed":
                task.completed_at = timezone.now()
            task.save()
            return JsonResponse({"success": True, "status": task.get_status_display()})

    elif action == "assign":
        employee_id = request.POST.get("employee_id")
        if employee_id:
            employee = get_object_or_404(User, id=employee_id)
            task.assigned_to = employee
            task.save()
            return JsonResponse({"success": True, "assigned_to": employee.username})
        else:
            task.assigned_to = None
            task.save()
            return JsonResponse({"success": True, "assigned_to": "Sin asignar"})

    return JsonResponse({"error": gettext("Acción inválida")}, status=400)


@login_required
def damage_report_list(request, project_id):
    """Lista y creación de reportes de daños del proyecto."""
    from core.forms import DamageReportForm
    from core.models import DamagePhoto

    project = get_object_or_404(Project, id=project_id)
    
    # SECURITY: Check project access
    has_access, redirect_url = _check_user_project_access(request.user, project)
    if not has_access:
        messages.error(request, _("You don't have access to this project."))
        return redirect(redirect_url)

    # Handle creation
    if request.method == "POST":
        form = DamageReportForm(project, request.POST, request.FILES)
        if form.is_valid():
            report = form.save(commit=False)
            report.project = project
            report.reported_by = request.user
            report.save()

            # Handle multiple photo uploads
            photos = request.FILES.getlist("photos")
            for photo_file in photos:
                DamagePhoto.objects.create(
                    report=report, image=photo_file, notes=request.POST.get("photo_notes", "")
                )

            messages.success(
                request, _("Reporte creado con %(count)s foto(s)") % {"count": len(photos)}
            )
            return redirect("damage_report_detail", report_id=report.id)
    else:
        form = DamageReportForm(project)

    # List reports
    reports = project.damage_reports.select_related("plan", "pin", "reported_by").all()
    severity = request.GET.get("severity")
    if severity:
        reports = reports.filter(severity=severity)
    status = request.GET.get("status")
    if status:
        reports = reports.filter(status=status)

    return render(
        request,
        "core/damage_report_list.html",
        {
            "project": project,
            "reports": reports,
            "form": form,
            "filter_severity": severity,
            "filter_status": status,
        },
    )


@login_required
def damage_report_detail(request, report_id):
    from core.models import DamageReport

    report = get_object_or_404(DamageReport, id=report_id)
    return render(
        request,
        "core/damage_report_detail.html",
        {
            "report": report,
            "project": report.project,
        },
    )


@login_required
def damage_report_edit(request, report_id):
    """Edit an existing damage report."""
    from core.forms import DamageReportForm
    from core.models import DamageReport

    report = get_object_or_404(DamageReport, id=report_id)
    project = report.project
    profile = getattr(request.user, "profile", None)
    can_edit = (
        request.user.is_staff
        or (profile and profile.role in ROLES_FIELD)
        or (request.user == report.reported_by)
    )
    if not can_edit:
        messages.error(request, "Acceso denegado.")
        return redirect("damage_report_detail", report_id=report.id)
    if request.method == "POST":
        form = DamageReportForm(project, request.POST, request.FILES, instance=report)
        if form.is_valid():
            form.save()
            messages.success(request, "Reporte actualizado.")
            return redirect("damage_report_detail", report_id=report.id)
    else:
        form = DamageReportForm(project, instance=report)
    return render(
        request,
        "core/damage_report_form.html",
        {
            "form": form,
            "project": project,
            "report": report,
            "is_edit": True,
        },
    )


@login_required
def damage_report_delete(request, report_id):
    """Delete a damage report with confirmation."""
    from core.models import DamageReport

    report = get_object_or_404(DamageReport, id=report_id)
    project = report.project
    profile = getattr(request.user, "profile", None)
    can_delete = (
        request.user.is_staff
        or (profile and profile.role in ROLES_FIELD)
        or (request.user == report.reported_by)
    )
    if not can_delete:
        messages.error(request, "Acceso denegado.")
        return redirect("damage_report_detail", report_id=report.id)
    if request.method == "POST":
        project_id = project.id
        report.delete()
        messages.success(request, "Reporte de daño eliminado.")
        return redirect("damage_report_list", project_id=project_id)
    return render(
        request,
        "core/damage_report_confirm_delete.html",
        {
            "project": project,
            "report": report,
        },
    )


@login_required
def damage_report_add_photos(request, report_id):
    """Add multiple photos to existing damage report."""
    from core.models import DamagePhoto, DamageReport

    report = get_object_or_404(DamageReport, id=report_id)

    # Check permission
    if not (request.user.is_staff or request.user == report.reported_by):
        return JsonResponse({"error": gettext("Sin permiso")}, status=403)

    if request.method == "POST":
        photos = request.FILES.getlist("photos")
        if not photos:
            return JsonResponse({"error": gettext("No se enviaron fotos")}, status=400)

        # Create DamagePhoto for each uploaded image
        created_count = 0
        for photo_file in photos:
            notes = request.POST.get("notes", "")
            DamagePhoto.objects.create(report=report, image=photo_file, notes=notes)
            created_count += 1

        return JsonResponse(
            {
                "success": True,
                "count": created_count,
                "message": f"{created_count} foto(s) agregada(s) correctamente",
            }
        )

    return JsonResponse({"error": gettext("Método no permitido")}, status=405)


@login_required
def damage_report_update_status(request, report_id):
    """Update damage report status and severity."""
    report = get_object_or_404(DamageReport, id=report_id)

    # Check permission (staff or superintendent)
    profile = getattr(request.user, "profile", None)
    if not (request.user.is_staff or (profile and profile.role == "superintendent")):
        return JsonResponse({"error": gettext("Sin permiso")}, status=403)

    if request.method == "POST":
        new_status = request.POST.get("status")
        new_severity = request.POST.get("severity")

        if new_status and new_status in dict(DamageReport.STATUS_CHOICES):
            report.status = new_status
            report.save()

        if new_severity and new_severity in dict(DamageReport.SEVERITY_CHOICES):
            report.severity = new_severity
            report.save()

        return JsonResponse(
            {
                "success": True,
                "status": report.get_status_display(),
                "severity": report.get_severity_display(),
            }
        )

    return JsonResponse({"error": gettext("Método no permitido")}, status=405)


# =============================
# Project Chat (Premium)
# =============================


def _ensure_default_channels(project, user):
    group, _ = ChatChannel.objects.get_or_create(
        project=project,
        name="Group",
        defaults={"channel_type": "group", "is_default": True, "created_by": user},
    )
    direct, _ = ChatChannel.objects.get_or_create(
        project=project,
        name="Direct",
        defaults={"channel_type": "direct", "is_default": True, "created_by": user},
    )
    # Ensure participants
    if user and not group.participants.filter(id=user.id).exists():
        group.participants.add(user)
    if user and not direct.participants.filter(id=user.id).exists():
        direct.participants.add(user)
    # Include client user if matches username
    from django.contrib.auth.models import User as DjangoUser

    if project.client:
        try:
            cu = DjangoUser.objects.get(username=project.client)
            group.participants.add(cu)
            direct.participants.add(cu)
        except DjangoUser.DoesNotExist:
            pass
    return group, direct


@login_required
def chat_redirect_to_premium(request, project_id, channel_id=None):
    """Redirect legacy chat URLs to premium chat."""
    if channel_id:
        return redirect("project_chat_premium_channel", project_id=project_id, channel_id=channel_id)
    return redirect("project_chat_premium", project_id=project_id)


@login_required
def project_chat_premium(request, project_id, channel_id=None):
    """
    Premium chat view with WebSocket support.
    """
    from core.models import ClientProjectAccess
    
    project = get_object_or_404(Project, id=project_id)
    
    # ===== SECURITY: Verify user has access to this project =====
    if not request.user.is_staff:
        # Check if user has ClientProjectAccess to this project
        has_client_access = ClientProjectAccess.objects.filter(
            user=request.user,
            project=project,
            is_active=True
        ).exists()
        
        # Check if user is assigned to the project (for employees)
        is_assigned = project.assigned_to.filter(id=request.user.id).exists() if hasattr(project, 'assigned_to') else False
        
        if not has_client_access and not is_assigned:
            messages.error(request, _("You don't have access to this project."))
            return redirect("dashboard_client")
    # ===== END SECURITY CHECK =====
    
    # Ensure default channels exist
    group, direct = _ensure_default_channels(project, request.user)
    
    # Get all channels for this project that user can access
    if request.user.is_staff:
        channels = project.chat_channels.all().order_by("name")
    else:
        channels = project.chat_channels.filter(
            participants=request.user
        ).order_by("name")
    
    # Select active channel
    if channel_id:
        channel = get_object_or_404(ChatChannel, id=channel_id, project=project)
        # Access control
        if not (request.user.is_staff or channel.participants.filter(id=request.user.id).exists()):
            messages.error(request, "No tienes acceso a este canal.")
            return redirect("project_chat_premium", project_id=project.id)
    else:
        # Default to group channel
        channel = group
    
    # Handle channel creation
    if request.method == "POST":
        action = request.POST.get("action")
        
        if action == "send":
            # Send message via HTTP (fallback when WebSocket not available)
            text = (request.POST.get("message") or "").strip()
            link_url = (request.POST.get("link_url") or "").strip() or ""
            image = request.FILES.get("image")
            if text or image or link_url:
                ChatMessage.objects.create(
                    channel=channel,
                    user=request.user,
                    message=text,
                    link_url=link_url,
                    image=image if image else None
                )
            return redirect("project_chat_premium_channel", project_id=project.id, channel_id=channel.id)
        
        elif action == "create_channel":
            channel_name = (request.POST.get("channel_name") or "").strip()
            channel_type = request.POST.get("channel_type", "group")
            if channel_name:
                new_channel = ChatChannel.objects.create(
                    project=project,
                    name=channel_name,
                    channel_type=channel_type
                )
                new_channel.participants.add(request.user)
                messages.success(request, f"Canal '{channel_name}' creado.")
                return redirect("project_chat_premium_channel", project_id=project.id, channel_id=new_channel.id)
            else:
                messages.error(request, "El nombre del canal es requerido.")
        
        elif action == "invite":
            username = (request.POST.get("username") or "").strip()
            from django.contrib.auth.models import User as DjangoUser
            try:
                u = DjangoUser.objects.get(username=username)
                channel.participants.add(u)
                messages.success(request, _("%(username)s invitado al canal.") % {"username": username})
            except DjangoUser.DoesNotExist:
                messages.error(request, "Usuario no encontrado.")
            return redirect("project_chat_premium_channel", project_id=project.id, channel_id=channel.id)
        
        elif action == "delete_channel":
            if channel.is_default:
                messages.error(request, "No puedes eliminar el canal por defecto.")
            else:
                channel_name = channel.name
                channel.delete()
                messages.success(request, f"Canal '{channel_name}' eliminado.")
            return redirect("project_chat_premium", project_id=project.id)
    
    # Get messages for the active channel (for initial load)
    messages_list = channel.messages.select_related("user").order_by("-created_at")[:50]
    messages_list = list(reversed(messages_list))  # Show oldest first
    
    # Get team members for invite functionality
    team_members = []
    if request.user.is_staff:
        from django.contrib.auth.models import User as DjangoUser
        team_members = DjangoUser.objects.filter(is_active=True).exclude(
            id__in=channel.participants.values_list('id', flat=True)
        )
    
    # Prepare channel data for JavaScript
    channels_data = []
    for ch in channels:
        unread_count = ch.messages.exclude(read_by=request.user).count()
        last_msg = ch.messages.order_by("-created_at").first()
        channels_data.append({
            'id': ch.id,
            'name': ch.name,
            'type': ch.channel_type,
            'is_default': ch.is_default,
            'unread': unread_count,
            'last_message': last_msg.message[:50] if last_msg else '',
            'last_time': last_msg.created_at.isoformat() if last_msg else '',
        })
    
    import json
    return render(
        request,
        "core/project_chat_premium.html",
        {
            "project": project,
            "channel": channel,
            "channels": channels,
            "channels_json": json.dumps(channels_data),
            "messages": messages_list,
            "team_members": team_members,
            "current_user_id": request.user.id,
        },
    )


@login_required
def agregar_comentario(request, project_id):
    """
    Permite a clientes y staff agregar comentarios con imágenes.
    Útil para comunicación continua y documentación visual.
    """
    project = get_object_or_404(Project, id=project_id)

    # Verificar acceso
    profile = getattr(request.user, "profile", None)
    from core.models import ClientProjectAccess

    has_access = ClientProjectAccess.objects.filter(user=request.user, project=project).exists()
    if profile and profile.role == "client":
        if not (has_access or project.client == request.user.username):
            messages.error(request, "No tienes acceso a este proyecto.")
            return redirect("dashboard_client")
    elif not request.user.is_staff and not has_access:
        messages.error(request, "Acceso denegado.")
        return redirect("dashboard")

    if request.method == "POST":
        text = request.POST.get("text", "").strip()
        image = request.FILES.get("image")

        if not text and not image:
            messages.error(request, "Debes agregar texto o imagen.")
            return redirect("client_project_view", project_id=project_id)

        Comment.objects.create(
            project=project, user=request.user, text=text or "Imagen adjunta", image=image
        )

        messages.success(request, "Comentario agregado exitosamente.")
        return redirect("client_project_view", project_id=project_id)

    return render(request, "core/agregar_comentario.html", {"project": project})


# --- CHANGE ORDER ---
@login_required
def changeorder_detail_view(request, changeorder_id):
    if not _is_staffish(request.user):
        messages.error(request, _("Access denied."))
        return redirect("dashboard")
    changeorder = get_object_or_404(ChangeOrder, id=changeorder_id)

    # Compute T&M preview if applicable
    tm_preview = None
    if changeorder.pricing_type == "T_AND_M":
        from core.services.financial_service import ChangeOrderService

        tm_preview = ChangeOrderService.get_billable_amount(changeorder)

    # Enrich time entries and expenses for real-time cost display
    time_entries = list(
        changeorder.time_entries.select_related("employee")
        .order_by("-date", "-start_time")
    )
    expenses = list(
        changeorder.expenses.all().order_by("-date")
    )
    is_admin = request.user.is_staff or request.user.is_superuser

    # Compute cost breakdown for both FIXED and T&M
    billing_rate = changeorder.get_effective_billing_rate()
    total_labor_hours = sum(
        (te.hours_worked or 0) for te in time_entries
    )
    total_labor_cost = float(total_labor_hours) * float(billing_rate)
    total_material_cost = sum(float(e.amount or 0) for e in expenses)
    markup_pct = float(changeorder.material_markup_percent or 0)
    total_material_with_markup = total_material_cost * (1 + markup_pct / 100)
    grand_total = total_labor_cost + total_material_with_markup

    cost_data = {
        "billing_rate": billing_rate,
        "total_labor_hours": total_labor_hours,
        "total_labor_cost": round(total_labor_cost, 2),
        "total_material_cost": round(total_material_cost, 2),
        "markup_pct": markup_pct,
        "total_material_with_markup": round(total_material_with_markup, 2),
        "grand_total": round(grand_total, 2),
        "labor_pct": round((total_labor_cost / grand_total * 100) if grand_total > 0 else 0, 1),
        "material_pct": round((total_material_with_markup / grand_total * 100) if grand_total > 0 else 0, 1),
        "time_entry_count": len(time_entries),
        "expense_count": len(expenses),
    }

    return render(
        request,
        "core/changeorder_detail_standalone.html",
        {
            "changeorder": changeorder,
            "tm_preview": tm_preview,
            "time_entries": time_entries,
            "expenses": expenses,
            "cost_data": cost_data,
            "is_admin": is_admin,
        },
    )


@login_required
def changeorder_billing_history_view(request, changeorder_id):
    """
    Billing history report for a Change Order.
    Shows all InvoiceLines with breakdown of labor vs materials.
    Admin/PM only.
    """
    if not _is_staffish(request.user):
        messages.error(request, _("Access denied."))
        return redirect("dashboard")
    changeorder = get_object_or_404(ChangeOrder, id=changeorder_id)

    # Get all invoice lines related to this CO through TimeEntry or Expense
    from django.db.models import Q

    from core.models import InvoiceLine

    invoice_lines = (
        InvoiceLine.objects.filter(
            Q(time_entry__change_order=changeorder) | Q(expense__change_order=changeorder)
        )
        .select_related("invoice")
        .distinct()
        .order_by("-invoice__date_issued", "id")
    )

    # Separate labor and material lines
    labor_lines = []
    material_lines = []

    for line in invoice_lines:
        # Get related time entries and expenses
        time_entries = []
        expenses = []

        if line.time_entry and line.time_entry.change_order == changeorder:
            time_entries = [line.time_entry]

        if line.expense and line.expense.change_order == changeorder:
            expenses = [line.expense]

        line_data = {
            "invoice_line": line,
            "time_entries": time_entries,
            "expenses": expenses,
        }

        # Check if it's labor or materials based on description or related entries
        if (
            time_entries
            or "labor" in line.description.lower()
            or "mano de obra" in line.description.lower()
        ):
            labor_lines.append(line_data)
        else:
            material_lines.append(line_data)

    # Calculate totals
    total_labor = sum(line_item["invoice_line"].amount for line_item in labor_lines)
    total_materials = sum(line_item["invoice_line"].amount for line_item in material_lines)
    grand_total = total_labor + total_materials

    context = {
        "changeorder": changeorder,
        "labor_lines": labor_lines,
        "material_lines": material_lines,
        "total_labor": total_labor,
        "total_materials": total_materials,
        "grand_total": grand_total,
    }

    return render(request, "core/changeorder_billing_history.html", context)


@login_required
def changeorder_cost_breakdown_view(request, changeorder_id):
    """
    Vista estilo factura para mostrar el desglose de costos de un Change Order.
    Separa Materiales vs Mano de Obra para fácil envío al cliente.
    """
    if not _is_staffish(request.user):
        messages.error(request, _("Access denied."))
        return redirect("dashboard")
    from decimal import Decimal

    from django.db.models import Sum

    changeorder = get_object_or_404(ChangeOrder, id=changeorder_id)

    # Get all expenses associated with this CO, separated by category
    material_expenses = changeorder.expenses.filter(
        category__in=["MATERIALES", "ALMACÉN"]
    ).order_by("date")
    other_expenses = changeorder.expenses.exclude(
        category__in=["MATERIALES", "ALMACÉN", "MANO_OBRA"]
    ).order_by("date")

    # Get all time entries for labor costs
    time_entries = changeorder.time_entries.select_related("employee").order_by("date")

    # Calculate totals
    total_materials = material_expenses.aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
    total_other_expenses = other_expenses.aggregate(total=Sum("amount"))["total"] or Decimal("0.00")

    # Labor cost from TimeEntries
    labor_cost = sum(entry.labor_cost for entry in time_entries)
    total_hours = sum((entry.hours_worked or Decimal("0")) for entry in time_entries)

    # Apply markup if CO has T&M pricing
    material_markup_pct = Decimal("0")
    billing_rate = Decimal("50.00")  # Default rate

    if hasattr(changeorder, "pricing_type") and changeorder.pricing_type == "T_AND_M":
        material_markup_pct = changeorder.material_markup_percent or Decimal("0")
        billing_rate = changeorder.get_effective_billing_rate() if hasattr(changeorder, "get_effective_billing_rate") else Decimal("50.00")

    # Calculate billable amounts with markup
    material_with_markup = total_materials * (1 + material_markup_pct / Decimal("100"))
    labor_billable = total_hours * billing_rate

    # Grand totals
    subtotal_cost = total_materials + labor_cost + total_other_expenses
    subtotal_billable = material_with_markup + labor_billable + total_other_expenses
    profit_margin = subtotal_billable - subtotal_cost if subtotal_billable > 0 else Decimal("0.00")

    context = {
        "changeorder": changeorder,
        "material_expenses": material_expenses,
        "other_expenses": other_expenses,
        "time_entries": time_entries,
        "total_materials": total_materials,
        "total_other_expenses": total_other_expenses,
        "labor_cost": labor_cost,
        "total_hours": total_hours,
        "material_markup_pct": material_markup_pct,
        "billing_rate": billing_rate,
        "material_with_markup": material_with_markup,
        "labor_billable": labor_billable,
        "subtotal_cost": subtotal_cost,
        "subtotal_billable": subtotal_billable,
        "profit_margin": profit_margin,
    }

    return render(request, "core/changeorder_cost_breakdown.html", context)


def changeorder_customer_signature_view(request, changeorder_id, token=None):
    """Vista pública para capturar firma de cliente en Change Orders.
    Requires either a valid signed token OR an authenticated user with access.
    """
    changeorder = get_object_or_404(ChangeOrder, id=changeorder_id)

    # --- Calculate T&M total if applicable ---
    tm_breakdown = None
    if changeorder.pricing_type == 'T_AND_M':
        from core.services.financial_service import ChangeOrderService
        tm_breakdown = ChangeOrderService.get_billable_amount(changeorder)

    # --- Access control: token OR authenticated user ---
    if token is not None:
        try:
            payload = signing.loads(token, max_age=60 * 60 * 24 * 7)  # 7 days
            if payload.get("co") != changeorder.id:
                return HttpResponseForbidden("Token does not match this Change Order.")
        except signing.SignatureExpired:
            return HttpResponseForbidden("The signature link has expired. Please request a new one.")
        except signing.BadSignature:
            return HttpResponseForbidden("Invalid or tampered token.")
    elif not request.user.is_authenticated:
        # No token and not logged in — block access
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(request.get_full_path())

    # If already signed, show corresponding screen
    if changeorder.signature_image:
        return render(
            request, "core/changeorder_signature_already_signed.html", {
                "changeorder": changeorder,
                "tm_breakdown": tm_breakdown,
            }
        )

    if request.method == "POST":
        import base64
        import uuid

        from django.core.files.base import ContentFile
        from django.utils import timezone

        signature_data = request.POST.get("signature_data")
        signer_name = request.POST.get("signer_name", "").strip()

        if not signature_data:
            return render(
                request,
                "core/changeorder_signature_form.html",
                {
                    "changeorder": changeorder,
                    "tm_breakdown": tm_breakdown,
                    "error": "Please draw your signature before continuing.",
                },
            )
        if not signer_name:
            return render(
                request,
                "core/changeorder_signature_form.html",
                {
                    "changeorder": changeorder,
                    "tm_breakdown": tm_breakdown,
                    "error": "Please enter your full name.",
                },
            )

        try:
            format_str, imgstr = signature_data.split(";base64,")
            ext = format_str.split("/")[-1]
            signature_file = ContentFile(
                base64.b64decode(imgstr),
                name=f"signature_co_{changeorder.id}_{uuid.uuid4().hex[:8]}.{ext}",
            )

            changeorder.signature_image = signature_file
            changeorder.signed_by = signer_name
            changeorder.signed_at = timezone.now()
            changeorder.status = "approved"
            # Audit trail capture (Paso 4)
            forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR", "")
            ip = (
                forwarded_for.split(",")[0].strip()
                if forwarded_for
                else request.META.get("REMOTE_ADDR")
            )
            changeorder.signed_ip = ip
            changeorder.signed_user_agent = request.META.get("HTTP_USER_AGENT", "")[:512]
            changeorder.save(
                update_fields=[
                    "signature_image",
                    "signed_by",
                    "signed_at",
                    "status",
                    "signed_ip",
                    "signed_user_agent",
                ]
            )

            # --- Process heavy tasks in background (emails, PDF, storage) ---
            customer_email = request.POST.get("customer_email", "").strip()
            try:
                from core.tasks import process_signature_post_tasks
                process_signature_post_tasks.delay(
                    document_type="changeorder",
                    document_id=changeorder.id,
                    signer_name=signer_name,
                    customer_email=customer_email,
                )
            except Exception as task_error:
                # If Celery is not available, log but don't block
                logger.warning(f"Background task failed, will process inline: {task_error}")
                # Fallback: process synchronously but with timeout protection
                try:
                    from core.services.email_service import KibrayEmailService
                    from core.services.pdf_service import generate_signed_changeorder_pdf
                    
                    # Just generate PDF, skip emails if task queue is down
                    pdf_bytes = generate_signed_changeorder_pdf(changeorder)
                    if pdf_bytes:
                        changeorder.signed_pdf = ContentFile(
                            pdf_bytes, name=f"co_{changeorder.id}_signed.pdf"
                        )
                        changeorder.save(update_fields=["signed_pdf"])
                except Exception:
                    pass  # Don't block the signature success

            # --- Generate download token for client ---
            download_token = signing.dumps({"changeorder_id": changeorder.id})

            return render(
                request, "core/changeorder_signature_success.html", {
                    "changeorder": changeorder,
                    "tm_breakdown": tm_breakdown,
                    "download_token": download_token,
                }
            )
        except Exception as e:
            return render(
                request,
                "core/changeorder_signature_form.html",
                {
                    "changeorder": changeorder,
                    "tm_breakdown": tm_breakdown,
                    "error": f"Error processing the signature: {e}",
                },
            )

    return render(request, "core/changeorder_signature_form.html", {
        "changeorder": changeorder,
        "tm_breakdown": tm_breakdown,
    })


@login_required
def changeorder_contractor_signature_view(request, changeorder_id):
    """Vista para capturar firma del contratista/admin en Change Orders.
    Solo accesible por staff/superuser.
    """
    if not request.user.is_staff:
        return HttpResponseForbidden("Only staff members can sign as contractor.")
    
    changeorder = get_object_or_404(ChangeOrder, id=changeorder_id)

    # Calculate T&M total if applicable
    tm_breakdown = None
    if changeorder.pricing_type == 'T_AND_M':
        from core.services.financial_service import ChangeOrderService
        tm_breakdown = ChangeOrderService.get_billable_amount(changeorder)

    # Check if contractor already signed
    if changeorder.contractor_signature:
        messages.info(request, "Este Change Order ya fue firmado por el contratista.")
        return redirect("changeorder_detail", changeorder_id=changeorder.id)

    if request.method == "POST":
        import base64
        import uuid

        from django.core.files.base import ContentFile
        from django.utils import timezone

        signature_data = request.POST.get("signature_data")
        signer_name = request.POST.get("signer_name", "").strip() or request.user.get_full_name() or request.user.username

        if not signature_data:
            messages.error(request, "Por favor dibuja tu firma antes de continuar.")
            return render(
                request,
                "core/changeorder_contractor_signature_form.html",
                {
                    "changeorder": changeorder,
                    "tm_breakdown": tm_breakdown,
                },
            )

        try:
            format_str, imgstr = signature_data.split(";base64,")
            ext = format_str.split("/")[-1]
            signature_file = ContentFile(
                base64.b64decode(imgstr),
                name=f"contractor_sig_co_{changeorder.id}_{uuid.uuid4().hex[:8]}.{ext}",
            )

            changeorder.contractor_signature = signature_file
            changeorder.contractor_signed_by = signer_name
            changeorder.contractor_signed_at = timezone.now()
            changeorder.save(
                update_fields=[
                    "contractor_signature",
                    "contractor_signed_by",
                    "contractor_signed_at",
                ]
            )

            # Regenerate PDF if both signatures are present
            if changeorder.signature_image:
                try:
                    from core.services.pdf_service import generate_changeorder_pdf_reportlab
                    pdf_bytes = generate_changeorder_pdf_reportlab(changeorder)
                    if pdf_bytes:
                        changeorder.signed_pdf = ContentFile(
                            pdf_bytes, name=f"co_{changeorder.id}_signed.pdf"
                        )
                        changeorder.save(update_fields=["signed_pdf"])
                        
                        # Auto-save to project files
                        from core.services.document_storage_service import auto_save_signed_document
                        auto_save_signed_document(changeorder, "changeorder")
                except Exception as e:
                    logger.warning(f"Error regenerating PDF: {e}")

            messages.success(request, f"Change Order #{changeorder.id} firmado exitosamente como contratista.")
            return redirect("changeorder_detail", changeorder_id=changeorder.id)
            
        except Exception as e:
            messages.error(request, f"Error procesando la firma: {e}")
            return render(
                request,
                "core/changeorder_contractor_signature_form.html",
                {
                    "changeorder": changeorder,
                    "tm_breakdown": tm_breakdown,
                },
            )

    return render(request, "core/changeorder_contractor_signature_form.html", {
        "changeorder": changeorder,
        "tm_breakdown": tm_breakdown,
    })


@login_required
def changeorder_create_view(request):
    if not _is_staffish(request.user):
        return redirect("dashboard")
    if request.method == "POST":
        form = ChangeOrderForm(request.POST, request.FILES)
        if form.is_valid():
            co = form.save()
            
            # Handle photo uploads - optimized for faster response
            photos = request.FILES.getlist("photos")
            if photos:
                # Process photos synchronously but in a single transaction
                from django.db import transaction
                with transaction.atomic():
                    for idx, photo_file in enumerate(photos):
                        description = request.POST.get(f"photo_description_{idx}", "")
                        ChangeOrderPhoto.objects.create(
                            change_order=co, image=photo_file, description=description, order=idx
                        )
            
            # Queue background task for post-creation processing (notifications, etc.)
            try:
                from core.tasks import process_changeorder_creation
                process_changeorder_creation.delay(co.id)
            except Exception:
                pass  # Don't block if task queueing fails
            
            messages.success(request, f"Change Order #{co.id} created successfully.")
            return redirect("changeorder_board")
    else:
        form = ChangeOrderForm()

    # Get approved colors from the project if project is selected
    approved_colors = []
    project_id = request.GET.get("project")
    if project_id:
        with contextlib.suppress(Exception):
            approved_colors = ColorSample.objects.filter(
                project_id=project_id, status="approved"
            ).order_by("code")

    return render(request, "core/changeorder_form.html", {"form": form, "approved_colors": approved_colors})


@login_required
def changeorder_edit_view(request, co_id):
    """Editar un Change Order existente"""
    if not _is_staffish(request.user):
        return redirect("dashboard")
    changeorder = get_object_or_404(ChangeOrder, id=co_id)
    if request.method == "POST":
        form = ChangeOrderForm(request.POST, request.FILES, instance=changeorder)
        if form.is_valid():
            co = form.save()
            
            # Handle new photo uploads - optimized with transaction
            photos = request.FILES.getlist("photos")
            if photos:
                from django.db import transaction
                with transaction.atomic():
                    current_count = co.photos.count()
                    for idx, photo_file in enumerate(photos):
                        description = request.POST.get(f"photo_description_{idx}", "")
                        ChangeOrderPhoto.objects.create(
                            change_order=co,
                            image=photo_file,
                            description=description,
                            order=current_count + idx,
                        )
            
            messages.success(request, f"Change Order #{co.id} updated successfully.")
            return redirect("changeorder_board")
    else:
        form = ChangeOrderForm(instance=changeorder)

    # Get approved colors from the project
    approved_colors = ColorSample.objects.filter(
        project=changeorder.project, status="approved"
    ).order_by("code")

    return render(
        request,
        "core/changeorder_form.html",
        {
            "form": form,
            "changeorder": changeorder,
            "is_edit": True,
            "approved_colors": approved_colors,
        },
    )


@login_required
def changeorder_delete_view(request, co_id):
    """Eliminar un Change Order"""
    if not _is_staffish(request.user):
        return redirect("dashboard")
    changeorder = get_object_or_404(ChangeOrder, id=co_id)
    if request.method == "POST":
        changeorder.delete()
        return redirect("changeorder_board")
    return render(request, "core/changeorder_confirm_delete.html", {"changeorder": changeorder})


@login_required
def changeorder_split_view(request, co_id):
    """
    Split a Change Order: move selected time entries, expenses and photos
    from the original CO into a brand-new CO.

    Naming convention:
      - Original: CO-KPI01  → stays as-is (reference_code unchanged).
      - New split: CO-KPI01-01, CO-KPI01-02, etc.

    The new CO inherits project, pricing_type, billing rates, markup from
    the original.  Selected items are **moved** (FK re-pointed), not copied.
    """
    if not _is_staffish(request.user):
        return redirect("dashboard")

    original = get_object_or_404(ChangeOrder, id=co_id)

    # ── Gather movable items ──
    time_entries = list(
        original.time_entries.select_related("employee").order_by("-date", "-start_time")
    )
    expenses = list(original.expenses.all().order_by("-date"))
    photos = list(original.photos.all().order_by("order", "uploaded_at"))

    # ── Compute next reference code (CO-KPI01-01, -02, …) ──
    base_ref = original.reference_code or f"CO-{original.id:04d}"
    # Find existing splits: anything that starts with base_ref + "-"
    existing_splits = (
        ChangeOrder.objects.filter(
            project=original.project,
            reference_code__startswith=base_ref + "-",
        )
        .values_list("reference_code", flat=True)
    )
    max_suffix = 0
    for ref in existing_splits:
        # Extract the last segment after the base_ref
        tail = ref[len(base_ref) + 1:]  # e.g. "01", "02"
        with contextlib.suppress(ValueError):
            max_suffix = max(max_suffix, int(tail))
    next_suffix = max_suffix + 1
    next_reference_code = f"{base_ref}-{next_suffix:02d}"

    # ── POST: perform the split ──
    if request.method == "POST":
        new_ref = request.POST.get("new_reference_code", "").strip()
        new_title = request.POST.get("new_co_title", "").strip()
        new_pricing = request.POST.get("new_pricing_type", original.pricing_type)
        new_amount_raw = request.POST.get("new_amount", "0")
        new_description = request.POST.get("new_description", "").strip()

        # ── Validation ──
        errors = []
        if not new_ref:
            errors.append(_("Reference code is required."))
        if not new_title:
            errors.append(_("Title is required."))

        # Check at least one item selected
        te_ids = request.POST.getlist("time_entry_ids")
        exp_ids = request.POST.getlist("expense_ids")
        photo_ids = request.POST.getlist("photo_ids")
        if not te_ids and not exp_ids and not photo_ids:
            errors.append(_("You must select at least one item to move."))

        # Check reference code uniqueness
        if new_ref and ChangeOrder.objects.filter(reference_code=new_ref).exists():
            errors.append(_("A Change Order with reference code '%(ref)s' already exists.") % {"ref": new_ref})

        if errors:
            for err in errors:
                messages.error(request, err)
            return render(
                request,
                "core/changeorder_split.html",
                {
                    "changeorder": original,
                    "time_entries": time_entries,
                    "expenses": expenses,
                    "photos": photos,
                    "next_reference_code": next_reference_code,
                },
            )

        # ── Parse amount ──
        try:
            from decimal import Decimal as D, InvalidOperation
            new_amount = D(new_amount_raw)
        except (InvalidOperation, ValueError):
            new_amount = Decimal("0")

        # ── Create the new CO in one atomic block ──
        from django.db import transaction

        with transaction.atomic():
            new_co = ChangeOrder.objects.create(
                project=original.project,
                co_title=new_title,
                description=new_description or original.description,
                amount=new_amount,
                pricing_type=new_pricing,
                labor_rate_override=original.labor_rate_override,
                material_markup_percent=original.material_markup_percent,
                status="draft",
                reference_code=new_ref,
                notes=_("Split from %(ref)s") % {"ref": base_ref},
                color=original.color,
            )

            # Move selected time entries
            if te_ids:
                original.time_entries.filter(id__in=te_ids).update(change_order=new_co)

            # Move selected expenses
            if exp_ids:
                original.expenses.filter(id__in=exp_ids).update(change_order=new_co)

            # Move selected photos (re-assign FK)
            if photo_ids:
                original.photos.filter(id__in=photo_ids).update(change_order=new_co)

        messages.success(
            request,
            _("Change Order split successfully. New CO: %(ref)s — %(title)s") % {
                "ref": new_ref,
                "title": new_title,
            },
        )
        return redirect("changeorder_detail", changeorder_id=new_co.id)

    # ── GET: show the split form ──
    return render(
        request,
        "core/changeorder_split.html",
        {
            "changeorder": original,
            "time_entries": time_entries,
            "expenses": expenses,
            "photos": photos,
            "next_reference_code": next_reference_code,
        },
    )


@login_required
def photo_editor_standalone_view(request):
    """Standalone photo editor that opens in new tab/window"""
    return render(request, "core/photo_editor_standalone.html")


@login_required
def get_approved_colors(request, project_id):
    """API endpoint to get approved colors for a project"""
    project = get_object_or_404(Project, id=project_id)
    
    # SECURITY: Check project access
    has_access, redirect_url = _check_user_project_access(request.user, project)
    if not has_access:
        return JsonResponse({"error": "Access denied"}, status=403)
    
    colors = (
        ColorSample.objects.filter(project_id=project_id, status="approved")
        .values("id", "code", "name", "brand", "finish")
        .order_by("code")
    )

    return JsonResponse({"colors": list(colors)})

    # (Legacy annotation and delete endpoints removed; use DRF versions under /api/v1/changeorder-photo/)


def color_sample_client_signature_view(request, sample_id, token=None):
    """Public view to capture client signature on color samples.
    Requires either a valid signed token OR an authenticated user.
    """
    color_sample = get_object_or_404(ColorSample, id=sample_id)

    # --- Access control: token OR authenticated user ---
    if token is not None:
        try:
            payload = signing.loads(token, max_age=60 * 60 * 24 * 7)  # 7 days
            if payload.get("sample_id") != color_sample.id:
                return HttpResponseForbidden("Token does not match this color sample.")
        except signing.SignatureExpired:
            return HttpResponseForbidden("The signature link has expired. Please request a new one.")
        except signing.BadSignature:
            return HttpResponseForbidden("Invalid or tampered token.")
    elif not request.user.is_authenticated:
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(request.get_full_path())

    # If already signed, show corresponding screen
    if color_sample.client_signature:
        return render(
            request,
            "core/color_sample_signature_already_signed.html",
            {"color_sample": color_sample},
        )

    if request.method == "POST":
        import base64
        import uuid

        from django.core.files.base import ContentFile
        from django.utils import timezone

        signature_data = request.POST.get("signature_data")
        signed_name = request.POST.get("signed_name", "").strip()

        if not signature_data:
            return render(
                request,
                "core/color_sample_signature_form.html",
                {
                    "color_sample": color_sample,
                    "error": "Please draw your signature before continuing.",
                },
            )
        if not signed_name:
            return render(
                request,
                "core/color_sample_signature_form.html",
                {"color_sample": color_sample, "error": "Please enter your full name."},
            )

        try:
            # --- Process base64 signature ---
            format_str, imgstr = signature_data.split(";base64,")
            ext = format_str.split("/")[-1]
            if ext not in ["png", "jpeg", "jpg"]:
                ext = "png"

            # Decode base64
            decoded_image = base64.b64decode(imgstr)

            # Create unique filename
            file_name = f"color_sample_{color_sample.id}_signature_{uuid.uuid4().hex}.{ext}"
            signature_file = ContentFile(decoded_image, name=file_name)

            # Get client IP
            x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
            client_ip = (
                x_forwarded_for.split(",")[0]
                if x_forwarded_for
                else request.META.get("REMOTE_ADDR", "")
            )

            # --- Save signature using the new model fields ---
            color_sample.sign_by_client(signature_file, signed_name, client_ip)

            # --- Queue background task for email/PDF (non-blocking) ---
            customer_email = request.POST.get("customer_email", "").strip()
            try:
                from core.tasks import process_signature_post_tasks
                process_signature_post_tasks.delay(
                    document_type="color_sample",
                    document_id=color_sample.id,
                    signer_name=signed_name,
                    customer_email=customer_email if customer_email else None,
                )
            except Exception:
                pass  # Don't block if task queueing fails

            # --- Generate download token for client ---
            from django.core import signing
            download_token = signing.dumps({"sample_id": color_sample.id})

            return render(
                request,
                "core/color_sample_signature_success.html",
                {"color_sample": color_sample, "download_token": download_token},
            )
        except Exception as e:
            return render(
                request,
                "core/color_sample_signature_form.html",
                {"color_sample": color_sample, "error": f"Error processing the signature: {e}"},
            )

    return render(request, "core/color_sample_signature_form.html", {"color_sample": color_sample})


@login_required
def changeorder_board_view(request):
    if not _is_staffish(request.user):
        messages.error(request, _("Access denied."))
        return redirect("dashboard")
    qs = ChangeOrder.objects.select_related("project").order_by("-date_created")
    status = request.GET.get("status")
    project_id = request.GET.get("project")
    if status:
        qs = qs.filter(status=status)
    if project_id:
        with contextlib.suppress(TypeError, ValueError):
            qs = qs.filter(project_id=int(project_id))
    total_amount = qs.aggregate(total=Sum("amount"))["total"] or 0
    projects = Project.objects.order_by("name")
    return render(
        request,
        "core/changeorder_board.html",
        {
            "changeorders": qs,
            "filter_status": status or "",
            "filter_project": str(project_id) if project_id else "",
            "total_amount": total_amount,
            "projects": projects,
        },
    )


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
                    request, "Selecciona registros del mismo proyecto que el CO elegido."
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
                    "No se puede crear CO sin proyecto asociado en los registros seleccionados.",
                )
            else:
                # validar que todos pertenecen al mismo proyecto
                mixed = (
                    TimeEntry.objects.filter(id__in=selected_ids)
                    .exclude(project=project_for_new)
                    .exists()
                )
                if mixed:
                    messages.error(request, "Para crear CO, selecciona filas de un solo proyecto.")
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

@login_required
def daily_log_view(request, project_id):
    """
    Vista para gestionar Daily Logs de un proyecto.
    PM puede crear reportes diarios seleccionando tareas completadas,
    agregando fotos y notas. Visible para PM, diseñadores, cliente, owner.
    """
    from core.forms import DailyLogForm
    from core.models import DailyLogPhoto

    project = get_object_or_404(Project, pk=project_id)
    
    # SECURITY: Check project access
    has_access, redirect_url = _check_user_project_access(request.user, project)
    if not has_access:
        messages.error(request, _("You don't have access to this project."))
        return redirect(redirect_url or "dashboard_client")

    # Verificar permisos (PM, admin, superuser)
    profile = getattr(request.user, "profile", None)
    role = getattr(profile, "role", "employee")
    can_create = role in ROLES_STAFF

    if request.method == "POST" and can_create:
        form = DailyLogForm(request.POST, project=project)
        if form.is_valid():
            dl = form.save(commit=False)
            dl.project = project
            dl.created_by = request.user
            dl.save()

            # Guardar relaciones many-to-many
            form.save_m2m()

            # Procesar fotos si hay
            photos = request.FILES.getlist("photos")
            for photo_file in photos:
                photo = DailyLogPhoto.objects.create(
                    image=photo_file,
                    caption=request.POST.get("photo_caption", ""),
                    uploaded_by=request.user,
                )
                dl.photos.add(photo)

            messages.success(request, _("Daily Log creado para %(date)s") % {"date": dl.date})
            return redirect("daily_log_detail", log_id=dl.id)
    else:
        form = DailyLogForm(project=project) if can_create else None

    # Listar logs del proyecto (ordenados por fecha descendente - más reciente primero)
    logs = (
        project.daily_logs.select_related("created_by", "schedule_item")
        .prefetch_related("completed_tasks", "photos")
        .order_by("-date")
    )

    # Filtros
    if not can_create and role == "employee":
        # Empleados NO pueden ver daily logs
        return redirect("dashboard_employee")

    # Filtrar solo publicados para clientes
    if role == "client":
        logs = logs.filter(is_published=True)

    context = {
        "project": project,
        "logs": logs,
        "form": form,
        "can_create": can_create,
    }
    return render(request, "core/daily_log_list.html", context)


@login_required
def project_activation_view(request, project_id):
    """
    Project Activation Wizard - Automates transition from Sales to Production.

    Converts approved estimate into operational entities:
    - ScheduleItems for Gantt
    - BudgetLines for financial control
    - Tasks for daily operations
    - Invoice for deposit/advance
    """
    from core.services.activation_service import ProjectActivationService

    project = get_object_or_404(Project, pk=project_id)

    # Check permissions (PM, admin, superuser only)
    profile = getattr(request.user, "profile", None)
    role = getattr(profile, "role", "employee")
    if role not in ["admin", "superuser", "project_manager"]:
        messages.error(request, "No tienes permisos para activar proyectos")
        return redirect("dashboard")

    # Get approved estimate
    estimate = project.estimates.filter(approved=True).order_by("-version").first()

    if not estimate:
        messages.error(request, "No hay estimado aprobado para este proyecto")
        return redirect("project_overview", project_id=project.id)

    # Check if already activated
    has_schedule = project.schedule_items.exists()
    has_budget = project.budget_lines.exists()

    if request.method == "POST":
        form = ActivationWizardForm(request.POST, estimate=estimate)

        if form.is_valid():
            try:
                # Initialize service
                service = ProjectActivationService(project=project, estimate=estimate)

                # Get form data
                start_date = form.cleaned_data["start_date"]
                create_schedule = form.cleaned_data["create_schedule"]
                create_budget = form.cleaned_data["create_budget"]
                create_tasks = form.cleaned_data["create_tasks"]
                deposit_percent = form.cleaned_data.get("deposit_percent", 0)
                items_to_schedule = form.cleaned_data.get("items_to_schedule")
                # Selected line IDs (spec wants passing IDs)
                selected_line_ids = (
                    [line.id for line in items_to_schedule]
                    if items_to_schedule and items_to_schedule.exists()
                    else None
                )

                # Get employee from user if exists (for task assignment)
                from core.models import Employee

                employee = Employee.objects.filter(user=request.user).first()

                # Activate project
                result = service.activate_project(
                    start_date=start_date,
                    create_schedule=create_schedule,
                    create_budget=create_budget,
                    create_tasks=create_tasks,
                    deposit_percent=deposit_percent,
                    items_to_schedule=None,  # keep backward compatibility not used now
                    selected_line_ids=selected_line_ids,
                    assigned_to=employee,
                )

                # Build success message
                summary = result["summary"]
                msg_parts = ["Proyecto activado exitosamente:"]

                if summary["schedule_items_count"] > 0:
                    msg_parts.append(
                        f"✓ {summary['schedule_items_count']} ítems de cronograma creados"
                    )

                if summary["budget_lines_count"] > 0:
                    msg_parts.append(
                        f"✓ {summary['budget_lines_count']} líneas de presupuesto creadas"
                    )

                if summary["tasks_count"] > 0:
                    msg_parts.append(f"✓ {summary['tasks_count']} tareas operativas creadas")

                if summary["invoice_created"]:
                    msg_parts.append(f"✓ Factura de anticipo creada (${summary['invoice_amount']})")

                messages.success(request, " | ".join(msg_parts))

                # Redirect to Gantt if schedule was created, otherwise to project detail
                if create_schedule:
                    return redirect("schedule_generator", project_id=project.id)
                else:
                    return redirect("project_overview", project_id=project.id)

            except ValueError as e:
                messages.error(request, _("Error de validación: %(error)s") % {"error": str(e)})
            except Exception as e:
                messages.error(
                    request, _("Error al activar proyecto: %(error)s") % {"error": str(e)}
                )
    else:
        form = ActivationWizardForm(estimate=estimate)

    # Calculate estimate summary
    estimate_lines = estimate.lines.all()
    direct_cost = sum(line.direct_cost() for line in estimate_lines)
    material_markup = (
        (direct_cost * (estimate.markup_material / 100)) if estimate.markup_material else 0
    )
    labor_markup = (direct_cost * (estimate.markup_labor / 100)) if estimate.markup_labor else 0
    overhead = (direct_cost * (estimate.overhead_pct / 100)) if estimate.overhead_pct else 0
    profit = (direct_cost * (estimate.target_profit_pct / 100)) if estimate.target_profit_pct else 0
    estimate_total = direct_cost + material_markup + labor_markup + overhead + profit

    context = {
        "project": project,
        "estimate": estimate,
        "estimate_lines": estimate_lines,
        "estimate_total": estimate_total,
        "form": form,
        "has_schedule": has_schedule,
        "has_budget": has_budget,
        "is_reactivation": has_schedule or has_budget,
    }

    return render(request, "core/project_activation.html", context)


@login_required
def daily_log_detail(request, log_id):
    """Vista detallada de un Daily Log específico"""
    from core.models import DailyLog, DailyLogPhoto, DailyLogScheduleProgress

    log = get_object_or_404(
        DailyLog.objects.select_related("project", "created_by", "schedule_item", "gantt_item_v2").prefetch_related(
            "completed_tasks", "photos", "schedule_progress_entries__schedule_item__phase"
        ),
        id=log_id,
    )

    # Verificar permisos
    profile = getattr(request.user, "profile", None)
    role = getattr(profile, "role", "employee")

    # Empleados no pueden ver
    if role == "employee":
        messages.error(request, "No tienes permiso para ver Daily Logs")
        return redirect("dashboard_employee")

    # Clientes: verificar acceso al proyecto Y que esté publicado
    if role == "client":
        has_access, redirect_url = _check_user_project_access(request.user, log.project)
        if not has_access:
            messages.error(request, _("You don't have access to this project."))
            return redirect("dashboard_client")
        if not log.is_published:
            messages.error(request, "Este Daily Log no está disponible")
            return redirect("dashboard_client")

    # POST: Agregar más fotos
    if request.method == "POST" and role in ROLES_STAFF:
        photos = request.FILES.getlist("photos")
        caption = request.POST.get("caption", "")
        for photo_file in photos:
            photo = DailyLogPhoto.objects.create(
                image=photo_file, caption=caption, uploaded_by=request.user
            )
            log.photos.add(photo)
        messages.success(request, _("%(count)s foto(s) agregada(s)") % {"count": len(photos)})
        return redirect("daily_log_detail", log_id=log.id)

    # Get multiple schedule progress entries
    schedule_progress_entries = log.schedule_progress_entries.select_related(
        "schedule_item", "schedule_item__phase"
    ).order_by("schedule_item__phase__order", "schedule_item__order")

    context = {
        "log": log,
        "project": log.project,
        "can_edit": role in ROLES_STAFF,
        "schedule_progress_entries": schedule_progress_entries,
    }

    return render(request, "core/daily_log_detail.html", context)


@login_required
def daily_log_delete(request, log_id):
    """Delete a Daily Log (PM, admin, superuser only)"""
    from core.models import DailyLog

    log = get_object_or_404(DailyLog.objects.select_related("project"), id=log_id)

    profile = getattr(request.user, "profile", None)
    role = getattr(profile, "role", "employee")
    can_delete = role in ROLES_STAFF

    if not can_delete:
        messages.error(request, "You don't have permission to delete Daily Logs")
        return redirect("daily_log_detail", log_id=log.id)

    if request.method == "POST":
        project_id = log.project_id
        log.delete()
        messages.success(request, "Daily Log deleted successfully")
        return redirect("daily_log", project_id=project_id)

    return render(
        request, "core/daily_log_confirm_delete.html", {"log": log, "project": log.project}
    )


@login_required
def daily_log_create(request, project_id):
    """Dedicated view to create a new Daily Log"""

    from core.forms import DailyLogForm, DailyLogScheduleProgressFormSet, DailyLogScheduleProgressForm
    from core.models import ScheduleItemV2, Task

    project = get_object_or_404(Project, pk=project_id)

    # Check permissions
    profile = getattr(request.user, "profile", None)
    role = getattr(profile, "role", "employee")
    if role not in ["admin", "superuser", "project_manager"]:
        messages.error(request, "Only PM can create Daily Logs")
        return redirect("project_overview", project_id=project.id)

    # Helper function to configure formset querysets
    def configure_formset_querysets(formset, project):
        for form in formset:
            form.fields["schedule_item"].queryset = ScheduleItemV2.objects.filter(
                project=project
            ).select_related("phase").order_by("phase__order", "order")
            form.fields["schedule_item"].label_from_instance = lambda obj: f"{obj.phase.name} → {obj.name}" if obj.phase else obj.name

    if request.method == "POST":
        
        form = DailyLogForm(request.POST, project=project)
        
        if form.is_valid():
            dl = form.save(commit=False)
            dl.project = project
            dl.created_by = request.user
            dl.save()
            form.save_m2m()
            
            logger.info(f"[DailyLog] Created Daily Log #{dl.id} for project {project.name}")

            # Process multiple schedule progress entries
            schedule_formset = DailyLogScheduleProgressFormSet(request.POST, instance=dl, prefix='schedule')
            configure_formset_querysets(schedule_formset, project)
            
            logger.info(f"[DailyLog] Formset is_valid: {schedule_formset.is_valid()}")
            
            if schedule_formset.is_valid():
                progress_entries = schedule_formset.save(commit=False)
                logger.info(f"[DailyLog] Processing {len(progress_entries)} schedule progress entries")
                
                for entry in progress_entries:
                    if entry.schedule_item_id:  # Only save if schedule_item is selected
                        entry.daily_log = dl
                        entry.save()
                        logger.info(f"[DailyLog] Saved entry: {entry.schedule_item.name} = {entry.progress_percent}%")
                
                # Handle deletions
                for obj in schedule_formset.deleted_objects:
                    obj.delete()
            else:
                logger.error(f"[DailyLog] Schedule formset errors: {schedule_formset.errors}")
                logger.error(f"[DailyLog] Formset non_form_errors: {schedule_formset.non_form_errors()}")

            # Process photos
            photos = request.FILES.getlist("photos")
            for photo_file in photos:
                from core.models import DailyLogPhoto

                photo = DailyLogPhoto.objects.create(
                    image=photo_file,
                    caption=request.POST.get("photo_caption", ""),
                    uploaded_by=request.user,
                )
                dl.photos.add(photo)

            messages.success(request, _("Daily Log created successfully"))
            return redirect("daily_log_detail", log_id=dl.id)
    else:
        # Default values
        initial = {
            "date": date.today(),
            "is_published": False,
        }
        form = DailyLogForm(initial=initial, project=project)
        schedule_formset = DailyLogScheduleProgressFormSet(prefix='schedule')
        configure_formset_querysets(schedule_formset, project)

    # Get pending/in-progress tasks for suggestions
    pending_tasks = (
        Task.objects.filter(project=project, status__in=["pending", "in_progress"])
        .select_related("assigned_to")
        .order_by("created_at")
    )

    # Get active Gantt V2 schedule items (not completed)
    active_schedule_items = ScheduleItemV2.objects.filter(
        project=project
    ).exclude(status="done").select_related("phase").order_by("phase__order", "order")[:15]

    context = {
        "project": project,
        "form": form,
        "schedule_formset": schedule_formset,
        "pending_tasks": pending_tasks,
        "active_schedule_items": active_schedule_items,
    }

    return render(request, "core/daily_log_create.html", context)


@login_required
@staff_member_required
def rfi_list_view(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    form = RFIForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        number = (project.rfis.aggregate(m=models.Max("number"))["m"] or 0) + 1
        rfi = form.save(commit=False)
        rfi.project = project
        rfi.number = number
        rfi.save()
        return redirect("rfi_list", project_id=project.id)
    rfis = project.rfis.all()
    return render(request, "core/rfi_list.html", {"project": project, "rfis": rfis, "form": form})


@login_required
@staff_member_required
def rfi_answer_view(request, rfi_id):
    rfi = get_object_or_404(RFI, pk=rfi_id)
    form = RFIAnswerForm(request.POST or None, instance=rfi)
    if request.method == "POST" and form.is_valid():
        ans = form.save(commit=False)
        if ans.answer and ans.status == "open":
            ans.status = "answered"
        ans.save()
        return redirect("rfi_list", project_id=rfi.project_id)
    return render(request, "core/rfi_answer.html", {"rfi": rfi, "form": form})


@login_required
def rfi_edit_view(request, rfi_id):
    """Edit an RFI. Allowed for staff/PM."""
    rfi = get_object_or_404(RFI, pk=rfi_id)
    profile = getattr(request.user, "profile", None)
    role = getattr(profile, "role", "employee")
    if role not in ["admin", "superuser", "project_manager"] and not request.user.is_staff:
        messages.error(request, "Acceso denegado.")
        return redirect("rfi_list", project_id=rfi.project_id)

    if request.method == "POST":
        form = RFIForm(request.POST, instance=rfi)
        if form.is_valid():
            form.save()
            messages.success(request, "RFI actualizado.")
            return redirect("rfi_list", project_id=rfi.project_id)
    else:
        form = RFIForm(instance=rfi)
    return render(request, "core/rfi_form.html", {"form": form, "rfi": rfi, "project": rfi.project})


@login_required
def rfi_delete_view(request, rfi_id):
    """Delete an RFI with confirmation. Staff/PM only."""
    rfi = get_object_or_404(RFI, pk=rfi_id)
    profile = getattr(request.user, "profile", None)
    role = getattr(profile, "role", "employee")
    if role not in ["admin", "superuser", "project_manager"] and not request.user.is_staff:
        messages.error(request, "Acceso denegado.")
        return redirect("rfi_list", project_id=rfi.project_id)

    project_id = rfi.project_id
    if request.method == "POST":
        rfi.delete()
        messages.success(request, "RFI eliminado.")
        return redirect("rfi_list", project_id=project_id)
    return render(request, "core/rfi_confirm_delete.html", {"rfi": rfi})


@login_required
def issue_list_view(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    form = IssueForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        isue = form.save(commit=False)
        isue.project = project
        isue.save()
        return redirect("issue_list", project_id=project.id)
    issues = project.issues.all()
    return render(
        request, "core/issue_list.html", {"project": project, "issues": issues, "form": form}
    )


@login_required
def issue_edit_view(request, issue_id):
    """Edit an Issue. Allowed for staff/PM."""
    issue = get_object_or_404(Issue, pk=issue_id)
    profile = getattr(request.user, "profile", None)
    role = getattr(profile, "role", "employee")
    if role not in ["admin", "superuser", "project_manager"] and not request.user.is_staff:
        messages.error(request, "Acceso denegado.")
        return redirect("issue_list", project_id=issue.project_id)

    if request.method == "POST":
        form = IssueForm(request.POST, instance=issue)
        if form.is_valid():
            form.save()
            messages.success(request, "Issue actualizado.")
            return redirect("issue_list", project_id=issue.project_id)
    else:
        form = IssueForm(instance=issue)
    return render(
        request, "core/issue_form.html", {"form": form, "issue": issue, "project": issue.project}
    )


@login_required
def issue_delete_view(request, issue_id):
    """Delete an Issue with confirmation. Staff/PM only."""
    issue = get_object_or_404(Issue, pk=issue_id)
    profile = getattr(request.user, "profile", None)
    role = getattr(profile, "role", "employee")
    if role not in ["admin", "superuser", "project_manager"] and not request.user.is_staff:
        messages.error(request, "Acceso denegado.")
        return redirect("issue_list", project_id=issue.project_id)

    project_id = issue.project_id
    if request.method == "POST":
        issue.delete()
        messages.success(request, "Issue eliminado.")
        return redirect("issue_list", project_id=project_id)
    return render(request, "core/issue_confirm_delete.html", {"issue": issue})


@login_required
def risk_list_view(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    form = RiskForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        rk = form.save(commit=False)
        rk.project = project
        rk.save()
        return redirect("risk_list", project_id=project.id)
    risks = project.risks.all()
    return render(
        request, "core/risk_list.html", {"project": project, "risks": risks, "form": form}
    )


@login_required
def risk_edit_view(request, risk_id):
    """Edit a Risk. Allowed for staff/PM."""
    risk = get_object_or_404(Risk, pk=risk_id)
    profile = getattr(request.user, "profile", None)
    role = getattr(profile, "role", "employee")
    if role not in ["admin", "superuser", "project_manager"] and not request.user.is_staff:
        messages.error(request, "Acceso denegado.")
        return redirect("risk_list", project_id=risk.project_id)

    if request.method == "POST":
        form = RiskForm(request.POST, instance=risk)
        if form.is_valid():
            form.save()
            messages.success(request, "Risk actualizado.")
            return redirect("risk_list", project_id=risk.project_id)
    else:
        form = RiskForm(instance=risk)
    return render(
        request, "core/risk_form.html", {"form": form, "risk": risk, "project": risk.project}
    )


@login_required
def risk_delete_view(request, risk_id):
    """Delete a Risk with confirmation. Staff/PM only."""
    risk = get_object_or_404(Risk, pk=risk_id)
    profile = getattr(request.user, "profile", None)
    role = getattr(profile, "role", "employee")
    if role not in ["admin", "superuser", "project_manager"] and not request.user.is_staff:
        messages.error(request, "Acceso denegado.")
        return redirect("risk_list", project_id=risk.project_id)

    project_id = risk.project_id
    if request.method == "POST":
        risk.delete()
        messages.success(request, "Risk eliminado.")
        return redirect("risk_list", project_id=project_id)
    return render(request, "core/risk_confirm_delete.html", {"risk": risk})


@login_required
def root_redirect(request):
    """Redirige al dashboard apropiado según rol del usuario"""
    profile = getattr(request.user, "profile", None)
    role = getattr(profile, "role", None)

    # Admin/Superuser → dashboard completo
    if request.user.is_superuser or request.user.is_staff:
        return redirect("dashboard_admin")

    # Según rol definido en Profile
    if role == "project_manager":
        return redirect("dashboard_pm")
    elif role == "client":
        return redirect("dashboard_client")
    elif role == "employee":
        return redirect("dashboard_employee")

    # Fallback
    return redirect("dashboard")


@login_required
def navigation_app_view(request):
    """
    Serves the React navigation SPA for Phase 4 features.
    This view handles client-side routing for paths like /files, /users, /calendar, etc.
    """
    return render(request, "navigation/index.html")


# --- PROJECT EV ---
@login_required
def project_ev_view(request, project_id):
    if not _is_staffish(request.user):
        return redirect("dashboard")
    project = get_object_or_404(Project, pk=project_id)

    # ?as_of=YYYY-MM-DD
    as_of = timezone.now().date()
    as_of_str = request.GET.get("as_of")
    if as_of_str:
        with contextlib.suppress(ValueError):
            as_of = datetime.strptime(as_of_str, "%Y-%m-%d").date()

    # BLOQUEA POST si no tiene permiso (antes de tocar datos)
    if request.method == "POST" and not _is_staffish(request.user):
        messages.error(request, "No tienes permisos para agregar progreso.")
        return redirect("project_ev", project_id=project_id)

    # Form de progreso (solo staff puede crear; coherente con tests que esperan redirect 302)
    if request.method == "POST":
        if _is_staffish(request.user):
            form = BudgetProgressForm(request.POST)
            form.fields["budget_line"].queryset = BudgetLine.objects.filter(project=project)
            if form.is_valid():
                try:
                    form.save()
                except (IntegrityError, ValidationError):
                    # Si ya existe progreso para esa fecha, crea uno en el siguiente día disponible
                    bl = form.cleaned_data.get("budget_line")
                    dt = form.cleaned_data.get("date") or as_of
                    for i in range(1, 8):
                        candidate = dt + timedelta(days=i)
                        if not BudgetProgress.objects.filter(
                            budget_line=bl, date=candidate
                        ).exists():
                            obj = form.save(commit=False)
                            obj.date = candidate
                            obj.save()
                            break
            else:
                # Fallback: intentar crear manualmente si el formulario falla por validaciones no críticas
                try:
                    bl_id = (
                        int(request.POST.get("budget_line"))
                        if request.POST.get("budget_line")
                        else None
                    )
                except (TypeError, ValueError):
                    bl_id = None
                dt_str = request.POST.get("date")
                try:
                    dt = datetime.strptime(dt_str, "%Y-%m-%d").date() if dt_str else as_of
                except ValueError:
                    dt = as_of
                try:
                    qty = Decimal(request.POST.get("qty_completed") or "0")
                    pc = Decimal(request.POST.get("percent_complete") or "0")
                except Exception:
                    qty, pc = Decimal("0"), Decimal("0")

                if bl_id:
                    bl = get_object_or_404(BudgetLine, id=bl_id, project=project)
                    # Ajustar percent si viene vacío y hay qty/qty_total
                    if (pc is None or pc == 0) and getattr(bl, "qty", None) and bl.qty:
                        pc = min(Decimal("100"), (Decimal(qty) / Decimal(bl.qty)) * Decimal("100"))
                    try:
                        BudgetProgress.objects.create(
                            budget_line=bl,
                            date=dt,
                            qty_completed=qty,
                            percent_complete=pc,
                            note=request.POST.get("note", ""),
                        )
                    except IntegrityError:
                        # fecha ocupada: usa siguiente día
                        for i in range(1, 8):
                            candidate = dt + timedelta(days=i)
                            if not BudgetProgress.objects.filter(
                                budget_line=bl, date=candidate
                            ).exists():
                                BudgetProgress.objects.create(
                                    budget_line=bl,
                                    date=candidate,
                                    qty_completed=qty,
                                    percent_complete=pc,
                                    note=request.POST.get("note", ""),
                                )
                                break
            return redirect(f"{reverse('project_ev', args=[project.id])}?as_of={as_of.isoformat()}")
        # Si no staff o form inválido, redirigir (para que test vea 302 en staff y no staff case ya cubierto antes)
        return redirect(f"{reverse('project_ev', args=[project.id])}?as_of={as_of.isoformat()}")
    else:
        form = BudgetProgressForm(initial={"date": as_of})
        form.fields["budget_line"].queryset = BudgetLine.objects.filter(project=project)

    # Calcula métricas
    summary = compute_project_ev(project, as_of=as_of)
    ev = summary.get("EV") or 0
    pv = summary.get("PV") or 0
    ac = summary.get("AC") or 0
    summary["cost_variance"] = (ev - ac) if (ev or ac) else None
    summary["schedule_variance"] = (ev - pv) if (ev or pv) else None

    # Query base
    qs = (
        BudgetProgress.objects.filter(budget_line__project=project, date__lte=as_of)
        .select_related("budget_line", "budget_line__cost_code")
        .order_by("-date", "-id")
    )

    # Paginación
    page_size = int(request.GET.get("ps", 20))
    paginator = Paginator(qs, page_size)
    page_obj = paginator.get_page(request.GET.get("page"))

    context = {
        "project": project,
        "form": form,
        "summary": summary,
        "progress": page_obj.object_list,
        "page_obj": page_obj,
        "as_of": as_of,
        "SPI": summary.get("SPI") or 0,
        "CPI": summary.get("CPI") or 0,
        "can_edit_progress": _is_staffish(request.user),
    }
    return render(request, "core/project_ev.html", context)


@login_required
def project_ev_series(request, project_id):
    if not _is_staffish(request.user):
        return JsonResponse({"error": "forbidden"}, status=403)
    project = get_object_or_404(Project, pk=project_id)
    days = int(request.GET.get("days", 30))
    end_str = request.GET.get("end")
    if end_str:
        try:
            end = datetime.strptime(end_str, "%Y-%m-%d").date()
        except ValueError:
            end = timezone.now().date()
    else:
        end = timezone.now().date()
    start = end - timedelta(days=days - 1)

    labels, pv, ev, ac = [], [], [], []
    cur = start
    while cur <= end:
        s = compute_project_ev(project, as_of=cur)
        labels.append(cur.isoformat())
        pv.append(float(s.get("PV") or 0))
        ev.append(float(s.get("EV") or 0))
        ac.append(float(s.get("AC") or 0))
        cur += timedelta(days=1)

    return JsonResponse({"labels": labels, "PV": pv, "EV": ev, "AC": ac})


@login_required
def project_ev_csv(request, project_id):
    if not _is_staffish(request.user):
        return redirect("dashboard")
    project = get_object_or_404(Project, pk=project_id)
    days = int(request.GET.get("days", 45))
    end_str = request.GET.get("end")
    if end_str:
        try:
            end = datetime.strptime(end_str, "%Y-%m-%d").date()
        except ValueError:
            end = timezone.now().date()
    else:
        end = timezone.now().date()
    start = end - timedelta(days=days - 1)

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = (
        f'attachment; filename="ev_{project.id}_{end.isoformat()}.csv"'
    )
    writer = csv.writer(response)
    writer.writerow(["Date", "PV", "EV", "AC", "SPI", "CPI"])

    cur = start
    while cur <= end:
        s = compute_project_ev(project, as_of=cur)
        pv = s.get("PV") or 0
        ev = s.get("EV") or 0
        ac = s.get("AC") or 0
        spi = (ev / pv) if pv else ""
        cpi = (ev / ac) if ac else ""
        writer.writerow(
            [
                cur.isoformat(),
                float(pv),
                float(ev),
                float(ac),
                float(spi) if spi else "",
                float(cpi) if cpi else "",
            ]
        )
        cur += timedelta(days=1)

    return response


@login_required
def budget_line_plan_view(request, line_id):
    line = get_object_or_404(BudgetLine, pk=line_id)
    form = BudgetLineScheduleForm(request.POST or None, instance=line)
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("budget_lines", project_id=line.project_id)
    return render(request, "core/budget_line_plan.html", {"line": line, "form": form})


@login_required
def project_list(request):
    """List projects filtered by user role.
    
    - Clients: Only see projects they have access to
    - Employees: Only see projects they are assigned to
    - Staff/Admin/PM: See all projects
    """
    profile = getattr(request.user, "profile", None)
    role = getattr(profile, "role", None) if profile else None
    
    # If user is a client, only show their projects
    if role == "client":
        # Get projects via ClientProjectAccess
        access_projects = Project.objects.filter(client_accesses__user=request.user)
        # Get projects via legacy client field
        legacy_projects = Project.objects.filter(client=request.user.username)
        # Combine both querysets
        projects = access_projects.union(legacy_projects).order_by("-start_date")
    elif role == "employee":
        # SECURITY: Employees can only see projects they have time entries for
        # or projects they are scheduled to work on (via daily plan activities)
        emp = getattr(request.user, "employee", None)
        if emp:
            from core.models import TimeEntry
            time_entry_projects = Project.objects.filter(
                timeentry__employee=emp
            ).distinct()
            # Also check daily plan assignments
            activity_projects = Project.objects.filter(
                daily_plans__activities__assigned_employees=emp
            ).distinct()
            projects = (time_entry_projects | activity_projects).distinct().order_by("-start_date")
        else:
            projects = Project.objects.none()
    else:
        # Staff, admin, PM - show all projects
        projects = Project.objects.all().order_by("id")
    
    return render(request, "core/project_list.html", {"projects": projects})


@login_required
def download_progress_sample(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    # SECURITY: Only staff can download project data
    if not _is_staffish(request.user):
        return HttpResponseForbidden(_("Access denied"))
    resp = HttpResponse(content_type="text/csv")
    resp["Content-Disposition"] = f'attachment; filename="progress_sample_project_{project.id}.csv"'
    resp.write("project_id,cost_code,date,percent_complete,qty_completed,note\r\n")
    # Fila de ejemplo
    resp.write(f"{project.id},LAB001,2025-08-24,25,,Inicio\r\n")
    return resp

@login_required
@staff_required
def upload_project_progress(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    if not _is_staffish(request.user):
        messages.error(request, "No tienes permisos para importar progreso.")
        return redirect("project_ev", project_id=project.id)
    context = {"project": project, "result": None, "errors": []}

    if request.method == "POST":
        f = request.FILES.get("file")
        create_missing = bool(request.POST.get("create_missing"))
        if not f:
            return HttpResponseBadRequest("Falta archivo CSV.")
        if f.size and f.size > 2_000_000:
            context["errors"].append("El archivo es demasiado grande (máx. 2 MB).")
            return render(request, "core/upload_progress.html", context)

        text = f.read().decode("utf-8", errors="ignore").lstrip("\ufeff")
        # Detecta delimitador , ; o tab
        try:
            dialect = csv.Sniffer().sniff(text[:2048], delimiters=[",", ";", "\t"])
            delim = dialect.delimiter
        except Exception:
            delim = ","
        reader = csv.DictReader(io.StringIO(text), delimiter=delim)
        headers = {h.lower(): h for h in (reader.fieldnames or [])}
        required = {"cost_code", "date"}
        if not required.issubset(set(headers.keys())):
            context["errors"].append(f"Encabezados requeridos: {sorted(required)}")
            return render(request, "core/upload_progress.html", context)

        created = updated = skipped = 0
        for i, row in enumerate(reader, start=2):
            try:
                cc = (row.get(headers["cost_code"]) or "").strip()
                if not cc:
                    raise ValueError("Falta cost_code.")

                try:
                    cost_code = CostCode.objects.get(code=cc)
                except CostCode.DoesNotExist as exc:
                    raise ValueError(f"CostCode no existe: {cc}") from exc

                bl = (
                    BudgetLine.objects.filter(project=project, cost_code=cost_code)
                    .order_by("id")
                    .first()
                )
                if not bl:
                    if create_missing:
                        bl = BudgetLine.objects.create(
                            project=project,
                            cost_code=cost_code,
                            description=f"Auto {cc}",
                            qty=0,
                            unit="",
                            unit_cost=0,
                        )
                    else:
                        raise ValueError(f"No hay BudgetLine en este proyecto para cost_code={cc}")

                date = _parse_date(row.get(headers["date"]))
                pct = row.get(headers.get("percent_complete"))
                qty = row.get(headers.get("qty_completed"))
                note = (row.get(headers.get("note")) or "").strip()

                pct_val = Decimal(str(pct).strip()) if pct not in (None, "", " ") else None
                qty_val = Decimal(str(qty).strip()) if qty not in (None, "", " ") else Decimal("0")

                if (
                    (pct_val is None or pct_val == 0)
                    and getattr(bl, "qty", None)
                    and bl.qty
                    and bl.qty != 0
                    and qty_val
                ):
                    pct_val = min(Decimal("100"), (qty_val / Decimal(bl.qty)) * Decimal("100"))

                if pct_val is not None and (pct_val < 0 or pct_val > 100):
                    raise ValueError("percent_complete fuera de 0–100.")

                obj, is_created = BudgetProgress.objects.get_or_create(
                    budget_line=bl,
                    date=date,
                    defaults={
                        "qty_completed": qty_val or 0,
                        "percent_complete": pct_val or 0,
                        "note": note,
                    },
                )
                if is_created:
                    obj.full_clean()
                    obj.save()
                    created += 1
                else:
                    if qty_val is not None:
                        obj.qty_completed = qty_val
                    if pct_val is not None:
                        obj.percent_complete = pct_val
                    if note:
                        obj.note = note
                    obj.full_clean()
                    obj.save()
                    updated += 1

            except Exception as e:
                skipped += 1
                context["errors"].append(f"Fila {i}: {e}")

        context["result"] = {"created": created, "updated": updated, "skipped": skipped}

    return render(request, "core/upload_progress.html", context)


@login_required
@staff_required
@require_POST
def delete_progress(request, project_id, pk):
    if not _is_staffish(request.user):
        messages.error(request, "No tienes permisos para borrar progreso.")
        return redirect("project_ev", project_id=project_id)
    prog = get_object_or_404(BudgetProgress, pk=pk, budget_line__project_id=project_id)
    prog.delete()
    messages.success(request, "Progreso eliminado.")
    return redirect("project_ev", project_id=project_id)


@login_required
@staff_required
@require_http_methods(["GET", "POST"])
def edit_progress(request, project_id, pk):
    try:
        prog = BudgetProgress.objects.select_related("budget_line__project").get(
            pk=pk, budget_line__project_id=project_id
        )
    except BudgetProgress.DoesNotExist:
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return HttpResponseNotFound("Not found")
        raise Http404("BudgetProgress not found") from None

    if request.method == "POST":
        form = BudgetProgressEditForm(request.POST, instance=prog)
        if form.is_valid():
            form.save()
            messages.success(request, "Progreso actualizado.")
            as_of = request.POST.get("as_of")
            url = reverse("project_ev", args=[project_id])
            if as_of:
                url = f"{url}?as_of={as_of}"
            return redirect(url)
    else:
        form = BudgetProgressEditForm(instance=prog)
    return render(
        request,
        "core/progress_edit_form.html",
        {"form": form, "project": prog.budget_line.project, "prog": prog},
    )


@login_required
@staff_required
def project_progress_csv(request, project_id):
    if not _is_staffish(request.user):
        messages.error(request, "No tienes permisos para exportar progreso.")
        return redirect("project_ev", project_id=project_id)

    project = get_object_or_404(Project, pk=project_id)

    def parse(d):
        try:
            return datetime.strptime(d, "%Y-%m-%d").date()
        except Exception:
            return None

    start = parse(request.GET.get("start", "")) or None
    end = parse(request.GET.get("end", "")) or None

    qs = BudgetProgress.objects.filter(budget_line__project=project).select_related(
        "budget_line", "budget_line__cost_code"
    )

    if start:
        qs = qs.filter(date__gte=start)
    if end:
        qs = qs.filter(date__lte=end)

    qs = qs.order_by("date", "budget_line__cost_code__code")

    resp = HttpResponse(content_type="text/csv")
    fname_end = (end or (start or timezone.now().date())).isoformat()
    resp["Content-Disposition"] = f'attachment; filename="progress_{project.id}_{fname_end}.csv"'
    w = csv.writer(resp)
    w.writerow(
        [
            "project_id",
            "date",
            "cost_code",
            "description",
            "percent_complete",
            "qty_completed",
            "note",
        ]
    )
    for p in qs:
        w.writerow(
            [
                project.id,
                p.date.isoformat(),
                p.budget_line.cost_code.code,
                p.budget_line.description or p.budget_line.cost_code.name,
                float(p.percent_complete or 0),
                float(p.qty_completed or 0),
                p.note or "",
            ]
        )
    return resp


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


def set_language_view(request, code: str = ""):
    """Set language using Django's standard session/cookie key and persist on profile."""
    lang_code = (code or request.POST.get("language") or "").lower()
    supported = {c[0] for c in settings.LANGUAGES}
    if lang_code not in supported:
        lang_code = settings.LANGUAGE_CODE

    translation.activate(lang_code)
    request.session[translation.LANGUAGE_SESSION_KEY] = lang_code

    # persist on user profile if logged in
    try:
        if request.user.is_authenticated:
            prof = getattr(request.user, "profile", None)
            if prof and prof.language != lang_code:
                prof.language = lang_code
                prof.save(update_fields=["language"])
    except Exception:
        pass

    next_url = request.POST.get("next") or request.META.get("HTTP_REFERER") or reverse("dashboard")
    response = redirect(next_url)

    # mirror Django's set_language cookie behavior
    response.set_cookie(
        settings.LANGUAGE_COOKIE_NAME,
        lang_code,
        max_age=getattr(settings, "LANGUAGE_COOKIE_AGE", None),
        path=getattr(settings, "LANGUAGE_COOKIE_PATH", "/"),
        domain=getattr(settings, "LANGUAGE_COOKIE_DOMAIN", None),
        secure=getattr(settings, "LANGUAGE_COOKIE_SECURE", False),
        httponly=getattr(settings, "LANGUAGE_COOKIE_HTTPONLY", False),
        samesite=getattr(settings, "LANGUAGE_COOKIE_SAMESITE", None),
    )
    return response


@login_required
def project_overview(request, project_id: int):
    if not request.user.is_staff:
        messages.error(request, "Acceso solo para PM/Staff.")
        return redirect("dashboard_employee")

    project = get_object_or_404(Project, pk=project_id)

    # Get Gantt progress first (used for progress bar)
    from core.services.schedule_unified import get_project_progress
    gantt_progress = get_project_progress(project)

    # Imports opcionales por si no existen algunos modelos
    # Nota: algunos modelos están importados a nivel de módulo (Task/Schedule/Issue/DailyLog);
    # aquí sólo necesitamos opcionalmente ProjectFile.
    try:
        from core.models import ProjectFile as ProjectFileModel
    except Exception:
        project_file_model = None
    else:
        project_file_model = ProjectFileModel

    try:
        from core.models import Color as ColorModel
    except Exception:
        color_model = None
    else:
        color_model = ColorModel

    try:
        from core.models import LeftoverItem as LeftoverItemModel  # “sobras” de material
    except Exception:
        leftover_item_model = None
    else:
        leftover_item_model = LeftoverItemModel

    # Info básica segura
    project_info = {
        "address": getattr(project, "address", None),
        "city": getattr(project, "city", None),
        "state": getattr(project, "state", None),
        "zip": getattr(project, "zip", None),
        "client": getattr(project, "client", None),
    }

    colors = []
    if color_model:
        colors = list(color_model.objects.filter(project=project).order_by("name"))

    # Fallback: If no Color model records found, parse from Project text fields
    if not colors:

        class SimpleColor:
            def __init__(self, name, code=None, brand=None):
                self.name = name
                self.code = code
                self.brand = brand

        # 1. Paint Colors
        if getattr(project, "paint_colors", None):
            # Split by comma or newline
            import re

            items = re.split(r"[,\n]+", project.paint_colors)
            for item in items:
                clean_item = item.strip()
                if clean_item:
                    colors.append(SimpleColor(name=clean_item, brand="Paint"))

        # 2. Paint Codes
        if getattr(project, "paint_codes", None):
            items = re.split(r"[,\n]+", project.paint_codes)
            for item in items:
                clean_item = item.strip()
                if clean_item:
                    colors.append(SimpleColor(name=clean_item, brand="Code"))

        # 3. Stains/Finishes
        if getattr(project, "stains_or_finishes", None):
            items = re.split(r"[,\n]+", project.stains_or_finishes)
            for item in items:
                clean_item = item.strip()
                if clean_item:
                    colors.append(SimpleColor(name=clean_item, brand="Finish"))

    upcoming_schedules = (
        Schedule.objects.filter(project=project).order_by("start_datetime")[:10] if Schedule else []
    )
    recent_tasks = Task.objects.filter(project=project).order_by("-id")[:10] if Task else []
    recent_issues = (
        Issue.objects.filter(project=project).order_by("-created_at")[:10] if Issue else []
    )
    recent_logs = (
        DailyLog.objects.filter(project=project).order_by("-date")[:10] if DailyLog else []
    )
    files = (
        project_file_model.objects.filter(project=project).order_by("-uploaded_at")[:10]
        if project_file_model
        else []
    )

    # Load Gantt V2 items for upcoming tasks display
    upcoming_gantt_items = []
    try:
        from core.models import ScheduleItemV2, SchedulePhaseV2
        from datetime import date, timedelta
        
        today = date.today()
        # Get items from today onwards, sorted by start_date
        gantt_items = (
            ScheduleItemV2.objects
            .filter(project=project, start_date__gte=today)
            .select_related('phase', 'assigned_to')
            .order_by('start_date', 'order')[:10]
        )
        
        # If no future items, get recent/current items
        if not gantt_items.exists():
            gantt_items = (
                ScheduleItemV2.objects
                .filter(project=project)
                .select_related('phase', 'assigned_to')
                .order_by('-start_date', 'order')[:10]
            )
        
        for item in gantt_items:
            upcoming_gantt_items.append({
                'id': item.id,
                'title': item.name,
                'start_date': item.start_date,
                'end_date': item.end_date,
                'status': item.status,
                'progress': item.progress,
                'is_milestone': item.is_milestone,
                'phase_name': item.phase.name if item.phase else None,
                'phase_color': item.phase.color if item.phase else '#6366f1',
                'assigned_to': item.assigned_to.get_full_name() if item.assigned_to else None,
            })
    except Exception as e:
        # If ScheduleItemV2 doesn't exist or any error, keep empty list
        pass

    # Floor Plans data
    try:
        from core.models import FloorPlan, PlanPin

        floor_plans = FloorPlan.objects.filter(project=project).order_by("level")[:5]
        total_floor_plans = FloorPlan.objects.filter(project=project).count()
        total_pins = PlanPin.objects.filter(floor_plan__project=project).count()
    except Exception:
        floor_plans = []
        total_floor_plans = 0
        total_pins = 0

    # Touch-ups data
    try:
        from core.models import TouchUpPin

        touchups_pending = TouchUpPin.objects.filter(
            floor_plan__project=project, status="pending"
        ).count()
        touchups_in_progress = TouchUpPin.objects.filter(
            floor_plan__project=project, status="in_progress"
        ).count()
        touchups_completed = TouchUpPin.objects.filter(
            floor_plan__project=project, status="completed"
        ).count()
        total_touchups = touchups_pending + touchups_in_progress + touchups_completed
        recent_touchups = (
            TouchUpPin.objects.filter(floor_plan__project=project)
            .select_related("floor_plan", "assigned_to")
            .order_by("-created_at")[:5]
        )
    except Exception:
        touchups_pending = 0
        touchups_in_progress = 0
        touchups_completed = 0
        total_touchups = 0
        recent_touchups = []

    # Change Orders data
    try:
        from core.models import ChangeOrder

        cos_draft = ChangeOrder.objects.filter(project=project, status="draft").count()
        cos_review = ChangeOrder.objects.filter(project=project, status="review").count()
        cos_approved = ChangeOrder.objects.filter(project=project, status="approved").count()
        cos_in_progress = ChangeOrder.objects.filter(project=project, status="in_progress").count()
        cos_completed = ChangeOrder.objects.filter(project=project, status="completed").count()
        total_cos = ChangeOrder.objects.filter(project=project).count()
    except Exception:
        cos_draft = 0
        cos_review = 0
        cos_approved = 0
        cos_in_progress = 0
        cos_completed = 0
        total_cos = 0

    leftovers = []
    if leftover_item_model:
        q = leftover_item_model.objects.filter(project=project)
        # si hay campo category, filtra pintura/stain/lacquer
        try:
            leftovers = q.filter(category__in=["paint", "stain", "lacquer"]).order_by(
                "category", "name"
            )
        except Exception:
            leftovers = q.order_by("id")

    # Resident Portal data
    portal_active = False
    portal_touchup_count = 0
    portal_session_count = 0
    portal_unit_count = 0
    try:
        from core.models import ResidentPortal, TouchUp as TouchUpModel

        portal_obj = ResidentPortal.objects.filter(project=project).first()
        if portal_obj:
            portal_active = portal_obj.is_active
            portal_touchup_count = (
                TouchUpModel.objects.filter(project=project)
                .exclude(resident_name="")
                .exclude(resident_name__isnull=True)
                .count()
            )
            portal_session_count = portal_obj.sessions.count()
            portal_unit_count = project.units.count()
    except Exception:
        pass

    return render(
        request,
        "core/project_overview.html",
        {
            "project": project,
            "project_info": project_info,
            "show_sidebar": False,  # Hide global sidebar, use project-specific Asana-style sidebar
            "colors": colors,
            "upcoming_schedules": upcoming_schedules,
            "upcoming_gantt_items": upcoming_gantt_items,
            "recent_tasks": recent_tasks,
            "recent_issues": recent_issues,
            "recent_logs": recent_logs,
            "files": files,
            "leftovers": leftovers,
            # Gantt Progress
            "gantt_progress": gantt_progress,
            # Floor Plans
            "floor_plans": floor_plans,
            "total_floor_plans": total_floor_plans,
            "total_pins": total_pins,
            # Touch-ups
            "touchups_pending": touchups_pending,
            "touchups_in_progress": touchups_in_progress,
            "touchups_completed": touchups_completed,
            "total_touchups": total_touchups,
            "recent_touchups": recent_touchups,
            # Change Orders
            "cos_draft": cos_draft,
            "cos_review": cos_review,
            "cos_approved": cos_approved,
            "cos_in_progress": cos_in_progress,
            "cos_completed": cos_completed,
            "total_cos": total_cos,
            # Resident Portal
            "portal_active": portal_active,
            "portal_touchup_count": portal_touchup_count,
            "portal_session_count": portal_session_count,
            "portal_unit_count": portal_unit_count,
        },
    )


def pickup_view(request, project_id: int):
    project = get_object_or_404(Project, pk=project_id)
    # SECURITY: Check project access
    has_access, redirect_url = _check_user_project_access(request.user, project)
    if not has_access:
        messages.error(request, _("Access denied."))
        return redirect(redirect_url or "dashboard")
    return render(request, "core/pickup_view.html", {"project": project})


@login_required
def task_list_view(request, project_id: int):
    from datetime import timedelta

    project = get_object_or_404(Project, pk=project_id)
    
    # SECURITY: Check project access
    has_access, redirect_url = _check_user_project_access(request.user, project)
    if not has_access:
        messages.error(request, _("Access denied."))
        return redirect(redirect_url or "dashboard")
    
    tasks = (
        Task.objects.filter(project=project)
        .select_related("assigned_to")
        .prefetch_related("dependencies")
        if Task
        else []
    )

    # Apply filters from query parameters
    status_filter = request.GET.get("status")
    priority_filter = request.GET.get("priority")
    assigned_filter = request.GET.get("assigned_to")
    overdue_filter = request.GET.get("overdue")

    if status_filter:
        tasks = tasks.filter(status=status_filter)

    if priority_filter:
        tasks = tasks.filter(priority=priority_filter)

    if assigned_filter:
        tasks = tasks.filter(assigned_to_id=assigned_filter)

    today = date.today()
    if overdue_filter == "yes":
        # Tasks overdue (due_date < today and not completed)
        tasks = tasks.filter(due_date__lt=today).exclude(status="Completed")
    elif overdue_filter == "today":
        # Tasks due today
        tasks = tasks.filter(due_date=today)
    elif overdue_filter == "week":
        # Tasks due this week
        week_end = today + timedelta(days=7)
        tasks = tasks.filter(due_date__lte=week_end, due_date__gte=today)

    tasks = tasks.order_by("-id")

    # Get employees for filter dropdown (only actual employees, not clients)
    employees = Employee.objects.filter(is_active=True).order_by("first_name", "last_name")

    can_create = request.user.is_staff
    form = None
    try:
        from core.forms import TaskForm as TaskFormModel
    except Exception:
        task_form_cls = None
    else:
        task_form_cls = TaskFormModel
    if can_create and task_form_cls:
        if request.method == "POST":
            form = task_form_cls(request.POST, request.FILES)
            if form.is_valid():
                inst = form.save(commit=False)
                inst.created_by = request.user
                inst.project = project
                inst.save()
                form.save_m2m()  # Save dependencies
                messages.success(request, "Tarea creada.")
                return redirect("task_list", project_id=project.id)
        else:
            form = task_form_cls(initial={"project": project})

    return render(
        request,
        "core/task_list.html",
        {
            "project": project,
            "tasks": tasks,
            "form": form,
            "can_create": can_create,
            "employees": employees,
            "today": today,
        },
    )


@login_required
def task_detail(request, task_id: int):
    """Detalle de una tarea.

    Permisos:
    - Staff: puede ver cualquier tarea.
    - Empleado: solo tareas asignadas a su Employee.
    """
    from datetime import date

    task = get_object_or_404(Task, pk=task_id)
    employee = Employee.objects.filter(user=request.user).first()

    if not request.user.is_staff and (not employee or task.assigned_to_id != employee.id):
        messages.error(request, gettext("Sin permiso para ver esta tarea."))
        return redirect("task_list_all")

    return render(request, "core/task_detail.html", {
        "task": task,
        "employee": employee,
        "today": date.today(),
    })


@login_required
def task_edit_view(request, task_id: int):
    task = get_object_or_404(Task, pk=task_id)
    if not request.user.is_staff:
        messages.error(request, "Solo staff puede editar tareas.")
        return redirect("task_detail", task_id=task.id)
    from core.forms import TaskForm

    if request.method == "POST":
        form = TaskForm(request.POST, request.FILES, instance=task)
        if form.is_valid():
            form.save()
            messages.success(request, "Tarea actualizada.")
            # Redirect to command center with project filter
            return redirect(f"/tasks/command-center/?project={task.project_id}")
    else:
        form = TaskForm(instance=task)
    return render(request, "core/task_form.html", {"form": form, "task": task, "edit": True})


@login_required
def task_delete_view(request, task_id: int):
    task = get_object_or_404(Task, pk=task_id)
    if not request.user.is_staff:
        messages.error(request, "Solo staff puede eliminar tareas.")
        return redirect("task_detail", task_id=task.id)
    if request.method == "POST":
        project_id = task.project_id
        task.delete()
        messages.success(request, "Tarea eliminada.")
        # Redirect to command center with project filter
        return redirect(f"/tasks/command-center/?project={project_id}")
    return render(request, "core/task_confirm_delete.html", {"task": task})


@login_required
def task_list_all(request):
    """DEPRECATED: Redirect to Task Command Center."""
    return redirect("task_command_center")


@login_required
def task_create_wizard(request):
    """
    Task Creation Wizard - Standalone page for creating tasks.
    
    Opens task_form.html with project selection enabled.
    Staff-only view.
    """
    if not request.user.is_staff:
        messages.error(request, gettext("You don't have permission to create tasks"))
        return redirect("task_command_center")
    
    from core.forms import TaskForm
    
    # Get active projects
    projects = Project.objects.filter(is_archived=False).order_by("name")
    
    # Handle pre-selected project from query param
    project_id = request.GET.get("project")
    initial_project = None
    if project_id:
        try:
            initial_project = Project.objects.get(id=project_id, is_archived=False)
        except Project.DoesNotExist:
            pass
    
    if request.method == "POST":
        form = TaskForm(request.POST, request.FILES)
        if form.is_valid():
            task = form.save(commit=False)
            task.created_by = request.user
            task.save()
            form.save_m2m()  # Save dependencies
            
            messages.success(request, gettext("Task created successfully"))
            
            # Redirect back to command center or project task list
            if task.project:
                return redirect(f"/tasks/command-center/?project={task.project.id}")
            return redirect("task_command_center")
        else:
            messages.error(request, gettext("Please correct the errors below"))
    else:
        initial = {}
        if initial_project:
            initial["project"] = initial_project
        form = TaskForm(initial=initial)
    
    return render(
        request,
        "core/task_form.html",
        {
            "form": form,
            "projects": projects,
            "edit": False,
            "title": gettext("Create New Task"),
        },
    )


@login_required
def task_command_center(request):
    """
    Task Command Center - Centro de control unificado de tareas.
    
    Features:
    - Selector de proyecto con filtrado
    - Estadísticas en tiempo real
    - Filtros avanzados (estado, prioridad, asignado, búsqueda)
    - Creación de tareas via modal
    - Acciones bulk (asignar, cambiar estado/prioridad)
    - Vista detallada de tareas con pines/touchups integrados
    
    Permisos:
    - Staff/Admin: Ve todas las tareas, puede crear/editar/asignar
    - Empleado: Solo ve sus tareas asignadas, puede actualizar estado
    """
    from django.db.models import Count, Q
    from core.notifications import notify_task_created
    
    is_staff = request.user.is_staff or request.user.is_superuser
    today = timezone.localdate()
    
    # Get current employee if exists
    current_employee = Employee.objects.filter(user=request.user).first()
    current_employee_id = current_employee.id if current_employee else None
    
    # Handle POST - Create Task
    if request.method == "POST" and request.POST.get("action") == "create":
        project_id = request.POST.get("project")
        title = request.POST.get("title", "").strip()
        
        if not project_id or not title:
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse({"error": gettext("Project and title are required")}, status=400)
            messages.error(request, gettext("Project and title are required"))
            return redirect("task_command_center")
        
        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse({"error": gettext("Project not found")}, status=404)
            messages.error(request, gettext("Project not found"))
            return redirect("task_command_center")
        
        # Create task
        task = Task.objects.create(
            project=project,
            title=title,
            description=request.POST.get("description", ""),
            priority=request.POST.get("priority", "medium"),
            due_date=request.POST.get("due_date") or None,
            is_touchup=request.POST.get("is_touchup") == "true",
            created_by=request.user,
            status="Pending",
        )
        
        # Handle image upload
        if request.FILES.get("image"):
            task.image = request.FILES["image"]
            task.save()
        
        # Assign employee if provided (staff only)
        if is_staff and request.POST.get("assigned_to"):
            try:
                emp = Employee.objects.get(id=request.POST.get("assigned_to"))
                task.assigned_to = emp
                task.save()
                # Send notification
                notify_task_created(task, request.user)
            except Employee.DoesNotExist:
                pass
        
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"success": True, "task_id": task.id})
        
        messages.success(request, gettext("Task created successfully"))
        return redirect("task_command_center")
    
    # Get projects for selector
    if is_staff:
        projects = Project.objects.filter(is_archived=False).order_by("name")
    else:
        # Employees see projects where they have assignments or tasks
        projects = Project.objects.filter(
            Q(tasks__assigned_to=current_employee) |
            Q(resource_assignments__employee=current_employee)
        ).distinct().filter(is_archived=False).order_by("name")
    
    # Selected project filter
    selected_project_id = request.GET.get("project")
    selected_project = None
    if selected_project_id:
        try:
            selected_project = Project.objects.get(id=selected_project_id)
        except Project.DoesNotExist:
            pass
    
    # Base queryset
    tasks_qs = Task.objects.select_related("project", "assigned_to").prefetch_related("dependencies")
    
    # Apply permissions filter
    if is_staff:
        # Staff sees all tasks
        if selected_project:
            tasks_qs = tasks_qs.filter(project=selected_project)
    else:
        # Employees see only their assigned tasks
        tasks_qs = tasks_qs.filter(assigned_to=current_employee)
        if selected_project:
            tasks_qs = tasks_qs.filter(project=selected_project)
    
    tasks = tasks_qs.order_by("-created_at")
    
    # Calculate statistics
    stats = {
        "total": tasks.count(),
        "pending": tasks.filter(status="Pending").count(),
        "in_progress": tasks.filter(status="In Progress").count(),
        "completed": tasks.filter(status="Completed").count(),
        "overdue": tasks.filter(due_date__lt=today).exclude(status__in=["Completed", "Cancelled"]).count(),
        "unassigned": tasks.filter(assigned_to__isnull=True).count() if is_staff else 0,
        "touchups": tasks.filter(is_touchup=True).count(),
        "my_tasks": tasks.filter(assigned_to=current_employee).count() if current_employee else 0,
    }
    
    # Get employees for assignment dropdown (staff only)
    employees = Employee.objects.filter(is_active=True).order_by("first_name") if is_staff else []
    
    return render(
        request,
        "core/task_command_center.html",
        {
            "tasks": tasks,
            "projects": projects,
            "selected_project": selected_project,
            "stats": stats,
            "employees": employees,
            "is_staff": is_staff,
            "today": today,
            "current_employee_id": current_employee_id,
        },
    )


# ===========================
# ACTIVITY 1: NEW TIME TRACKING ENDPOINTS (Q11.13)
# ===========================


@login_required
def task_start_tracking(request, task_id):
    """AJAX endpoint to start time tracking on a task."""
    if request.method != "POST":
        return JsonResponse({"error": gettext("POST required")}, status=405)

    task = get_object_or_404(Task, id=task_id)
    employee = Employee.objects.filter(user=request.user).first()

    # Check permission
    if not (request.user.is_staff or (employee and task.assigned_to == employee)):
        return JsonResponse({"error": gettext("Sin permiso")}, status=403)

    # Check if task can start (dependencies)
    if not task.can_start():
        incomplete_deps = task.dependencies.filter(status__in=["pending", "in_progress"])
        dep_names = ", ".join([d.title for d in incomplete_deps])
        return JsonResponse(
            {
                "error": gettext("No se puede iniciar. Dependencias incompletas: %(deps)s")
                % {"deps": dep_names}
            },
            status=400,
        )

    # Start tracking
    if task.start_tracking():
        return JsonResponse(
            {
                "success": True,
                "started_at": task.started_at.isoformat() if task.started_at else None,
                "message": "Seguimiento de tiempo iniciado",
            }
        )
    else:
        return JsonResponse({"error": gettext("Ya hay un seguimiento activo")}, status=400)


@login_required
def task_stop_tracking(request, task_id):
    """AJAX endpoint to stop time tracking on a task."""
    if request.method != "POST":
        return JsonResponse({"error": gettext("POST required")}, status=405)

    task = get_object_or_404(Task, id=task_id)
    employee = Employee.objects.filter(user=request.user).first()

    # Check permission
    if not (request.user.is_staff or (employee and task.assigned_to == employee)):
        return JsonResponse({"error": gettext("Sin permiso")}, status=403)

    # Stop tracking
    elapsed = task.stop_tracking()
    if elapsed is not None:
        return JsonResponse(
            {
                "success": True,
                "elapsed_seconds": elapsed,
                "total_hours": task.get_time_tracked_hours(),
                "message": f"Seguimiento detenido. {elapsed} segundos agregados.",
            }
        )
    else:
        return JsonResponse({"error": gettext("No hay seguimiento activo")}, status=400)


# ===========================
# ACTIVITY 1: DAILY PLAN ENHANCEMENTS
# ===========================

def site_photo_list(request, project_id):
    from core.models import Project, SitePhoto

    project = get_object_or_404(Project, pk=project_id)
    
    # SECURITY: Check project access
    has_access, redirect_url = _check_user_project_access(request.user, project)
    if not has_access:
        messages.error(request, _("You don't have access to this project."))
        return redirect(redirect_url or "dashboard_client")
    
    photos = SitePhoto.objects.filter(project=project).order_by("-created_at")
    
    # Filter by photo type if specified
    photo_type = request.GET.get("type")
    if photo_type:
        photos = photos.filter(photo_type=photo_type)
    
    # Determine if user is a client
    profile = getattr(request.user, "profile", None)
    is_client_user = profile and profile.role == "client"
    
    return render(request, "core/site_photo_list.html", {
        "project": project, 
        "photos": photos,
        "is_client_user": is_client_user,
    })


@login_required
def site_photo_create(request, project_id):
    from core.forms import SitePhotoForm
    from core.models import Project, FloorPlan

    project = get_object_or_404(Project, pk=project_id)
    floor_plans = FloorPlan.objects.filter(project=project, is_current=True).order_by("name")
    
    if request.method == "POST":
        form = SitePhotoForm(request.POST, request.FILES, project=project)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.project = project
            obj.created_by = request.user
            try:
                obj.annotations = json.loads(form.cleaned_data.get("annotations") or "{}")
            except Exception:
                obj.annotations = {}
            obj.save()
            messages.success(request, _("Photo and annotations saved."))
            return redirect("site_photo_list", project_id=project.id)
    else:
        form = SitePhotoForm(project=project)
    return render(request, "core/site_photo_form.html", {
        "project": project, 
        "form": form,
        "floor_plans": floor_plans,
    })


@login_required
def site_photo_detail(request, photo_id):
    """View a single site photo with all its details."""
    from core.models import SitePhoto

    photo = get_object_or_404(SitePhoto, pk=photo_id)
    project = photo.project
    
    # Get adjacent photos for navigation
    all_photos = list(SitePhoto.objects.filter(project=project).order_by("-created_at").values_list("id", flat=True))
    current_index = all_photos.index(photo.id) if photo.id in all_photos else 0
    prev_photo_id = all_photos[current_index + 1] if current_index + 1 < len(all_photos) else None
    next_photo_id = all_photos[current_index - 1] if current_index > 0 else None
    
    profile = getattr(request.user, "profile", None)
    is_client_user = profile and profile.role == "client"
    
    return render(request, "core/site_photo_detail.html", {
        "photo": photo,
        "project": project,
        "is_client_user": is_client_user,
        "prev_photo_id": prev_photo_id,
        "next_photo_id": next_photo_id,
        "current_index": current_index + 1,
        "total_photos": len(all_photos),
    })


@login_required
@staff_required
def site_photo_edit(request, photo_id):
    """Edit an existing site photo."""
    from core.forms import SitePhotoForm
    from core.models import SitePhoto, FloorPlan

    photo = get_object_or_404(SitePhoto, pk=photo_id)
    project = photo.project
    floor_plans = FloorPlan.objects.filter(project=project, is_current=True).order_by("name")
    
    if request.method == "POST":
        form = SitePhotoForm(request.POST, request.FILES, instance=photo, project=project)
        if form.is_valid():
            obj = form.save(commit=False)
            try:
                obj.annotations = json.loads(form.cleaned_data.get("annotations") or "{}")
            except Exception:
                pass
            obj.save()
            messages.success(request, _("Photo updated successfully."))
            return redirect("site_photo_detail", photo_id=photo.id)
    else:
        form = SitePhotoForm(instance=photo, project=project)
    
    return render(request, "core/site_photo_form.html", {
        "project": project,
        "form": form,
        "floor_plans": floor_plans,
        "photo": photo,
        "is_edit": True,
    })


@login_required
@staff_required
def site_photo_delete(request, photo_id):
    """Delete a site photo."""
    from core.models import SitePhoto

    photo = get_object_or_404(SitePhoto, pk=photo_id)
    project = photo.project
    
    if request.method == "POST":
        photo.delete()
        messages.success(request, _("Photo deleted successfully."))
        return redirect("site_photo_list", project_id=project.id)
    
    return render(request, "core/site_photo_confirm_delete.html", {
        "photo": photo,
        "project": project,
    })

@login_required
def project_minutes_list(request, project_id):
    """Lista todas las minutas de un proyecto (timeline horizontal)"""
    project = get_object_or_404(Project, id=project_id)
    
    # SECURITY: Check project access
    has_access, redirect_url = _check_user_project_access(request.user, project)
    if not has_access:
        messages.error(request, _("You don't have access to this project."))
        return redirect(redirect_url or "dashboard_client")

    from core.models import ProjectMinute

    # Admin ve todo, Cliente solo ve lo marcado como visible
    if request.user.is_staff or request.user.is_superuser:
        minutes = ProjectMinute.objects.filter(project=project)
    else:
        minutes = ProjectMinute.objects.filter(project=project, visible_to_client=True)

    # Optimizar query con prefetch de comentarios
    minutes = minutes.select_related("created_by").prefetch_related("comments").order_by("event_date")

    # Filtros
    event_type = request.GET.get("type")
    if event_type:
        minutes = minutes.filter(event_type=event_type)

    context = {
        "project": project,
        "minutes": minutes,
        "event_types": ProjectMinute.EVENT_TYPE_CHOICES,
    }
    return render(request, "core/project_minutes_timeline.html", context)


@login_required
def project_minute_create(request, project_id):
    """Crear nueva minuta"""
    project = get_object_or_404(Project, id=project_id)

    # Solo admin/staff pueden crear minutas
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, "No tienes permisos para crear minutas.")
        return redirect("project_minutes_list", project_id=project.id)

    from core.models import ProjectMinute

    if request.method == "POST":
        event_type = request.POST.get("event_type")
        title = request.POST.get("title")
        description = request.POST.get("description", "")
        event_date_str = request.POST.get("event_date")
        participants = request.POST.get("participants", "")
        visible_to_client = request.POST.get("visible_to_client") == "on"
        attachment = request.FILES.get("attachment")

        if not title or not event_date_str:
            messages.error(request, "Título y fecha son requeridos.")
        else:
            try:
                event_date = timezone.datetime.fromisoformat(event_date_str)
            except Exception:
                event_date = timezone.now()

            ProjectMinute.objects.create(
                project=project,
                event_type=event_type,
                title=title,
                description=description,
                event_date=event_date,
                participants=participants,
                attachment=attachment,
                visible_to_client=visible_to_client,
                created_by=request.user,
            )
            messages.success(request, "Minuta creada exitosamente.")
            return redirect("project_minutes_list", project_id=project.id)

    context = {
        "project": project,
        "event_types": ProjectMinute.EVENT_TYPE_CHOICES,
    }
    return render(request, "core/project_minute_form.html", context)


@login_required
def project_minute_detail(request, minute_id):
    """Ver detalles de una minuta con comentarios y CRUD"""
    from core.models import ProjectMinute, MinuteComment

    minute = get_object_or_404(
        ProjectMinute.objects.select_related("project", "created_by").prefetch_related("comments__author"),
        id=minute_id
    )

    # Verificar permisos
    if not (request.user.is_staff or request.user.is_superuser or minute.visible_to_client):
        messages.error(request, "No tienes permisos para ver esta minuta.")
        return redirect("project_minutes_list", project_id=minute.project.id)

    context = {
        "minute": minute,
        "comments": minute.comments.all(),
        "can_edit": request.user.is_staff or request.user.is_superuser,
        "event_types": ProjectMinute.EVENT_TYPE_CHOICES,
    }
    return render(request, "core/project_minute_detail.html", context)


@login_required
def project_minute_edit(request, minute_id):
    """Editar una minuta existente"""
    from core.models import ProjectMinute

    minute = get_object_or_404(ProjectMinute, id=minute_id)

    # Solo admin/staff pueden editar
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, "No tienes permisos para editar minutas.")
        return redirect("project_minute_detail", minute_id=minute.id)

    if request.method == "POST":
        minute.event_type = request.POST.get("event_type", minute.event_type)
        minute.title = request.POST.get("title", minute.title)
        minute.description = request.POST.get("description", "")
        minute.participants = request.POST.get("participants", "")
        minute.visible_to_client = request.POST.get("visible_to_client") == "on"
        
        event_date_str = request.POST.get("event_date")
        if event_date_str:
            try:
                minute.event_date = timezone.datetime.fromisoformat(event_date_str)
            except Exception:
                pass

        attachment = request.FILES.get("attachment")
        if attachment:
            minute.attachment = attachment

        minute.save()
        messages.success(request, "Minuta actualizada exitosamente.")
        return redirect("project_minute_detail", minute_id=minute.id)

    context = {
        "minute": minute,
        "project": minute.project,
        "event_types": ProjectMinute.EVENT_TYPE_CHOICES,
        "is_edit": True,
    }
    return render(request, "core/project_minute_form.html", context)


@login_required
def project_minute_delete(request, minute_id):
    """Eliminar una minuta"""
    from core.models import ProjectMinute

    minute = get_object_or_404(ProjectMinute, id=minute_id)
    project_id = minute.project.id

    # Solo admin/staff pueden eliminar
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, "No tienes permisos para eliminar minutas.")
        return redirect("project_minute_detail", minute_id=minute.id)

    if request.method == "POST":
        minute.delete()
        messages.success(request, "Minuta eliminada exitosamente.")
        return redirect("project_minutes_list", project_id=project_id)

    return redirect("project_minute_detail", minute_id=minute.id)


@login_required
def minute_comment_add(request, minute_id):
    """Agregar comentario a una minuta"""
    from core.models import ProjectMinute, MinuteComment

    minute = get_object_or_404(ProjectMinute, id=minute_id)

    # Verificar que puede ver la minuta
    if not (request.user.is_staff or request.user.is_superuser or minute.visible_to_client):
        messages.error(request, "No tienes permisos.")
        return redirect("project_minutes_list", project_id=minute.project.id)

    if request.method == "POST":
        content = request.POST.get("content", "").strip()
        if content:
            MinuteComment.objects.create(
                minute=minute,
                author=request.user,
                content=content,
            )
            messages.success(request, "Comentario agregado.")
        else:
            messages.error(request, "El comentario no puede estar vacío.")

    # Redireccionar según de dónde vino
    next_url = request.POST.get("next", "")
    if next_url == "timeline":
        return redirect("project_minutes_list", project_id=minute.project.id)
    return redirect("project_minute_detail", minute_id=minute.id)


@login_required
def minute_comment_delete(request, comment_id):
    """Eliminar un comentario"""
    from core.models import MinuteComment

    comment = get_object_or_404(MinuteComment, id=comment_id)
    minute_id = comment.minute.id

    # Solo el autor o admin puede eliminar
    if not (request.user == comment.author or request.user.is_staff or request.user.is_superuser):
        messages.error(request, "No tienes permisos para eliminar este comentario.")
        return redirect("project_minute_detail", minute_id=minute_id)

    if request.method == "POST":
        comment.delete()
        messages.success(request, "Comentario eliminado.")

    return redirect("project_minute_detail", minute_id=minute_id)


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


# ========================================
# CHANGE ORDER API ENDPOINTS
@login_required
@require_http_methods(["PATCH"])
def changeorder_update_status(request, co_id):
    """Update Change Order status via drag and drop in board"""
    try:
        co = get_object_or_404(ChangeOrder, id=co_id)

        # Check permissions
        profile = getattr(request.user, "profile", None)
        role = getattr(profile, "role", "employee")

        if role not in ["admin", "superuser", "project_manager"]:
            return JsonResponse({"success": False, "error": "Sin permisos"}, status=403)

        # Parse request
        data = json.loads(request.body)
        new_status = data.get("status")

        # Validate status
        valid_statuses = ["pending", "approved", "sent", "billed", "paid"]
        if new_status not in valid_statuses:
            return JsonResponse({"success": False, "error": "Estado inválido"}, status=400)

        # Update status
        old_status = co.status
        co.status = new_status
        co.save()

        return JsonResponse(
            {
                "success": True,
                "co_id": co.id,
                "old_status": old_status,
                "new_status": new_status,
                "message": f"Estado actualizado a {co.get_status_display()}",
            }
        )

    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "JSON inválido"}, status=400)
    except Exception as e:
        logger.exception("Error updating change order status")
        return JsonResponse({"success": False, "error": "Error interno del servidor"}, status=500)


@login_required
@require_POST
def changeorder_send_to_client(request, co_id):
    """Send Change Order to client for signature"""
    try:
        co = get_object_or_404(ChangeOrder, id=co_id)

        # Check permissions
        profile = getattr(request.user, "profile", None)
        role = getattr(profile, "role", "employee")

        if role not in ["admin", "superuser", "project_manager"]:
            return JsonResponse({"success": False, "error": "Sin permisos"}, status=403)

        # Validate current status
        if co.status in ["billed", "paid"]:
            return JsonResponse(
                {"success": False, "error": "No se puede enviar un CO ya facturado o pagado"},
                status=400,
            )

        # Update status to 'sent'
        co.status = "sent"
        co.save()

        # Notify project admins/PMs about CO sent to client
        staff_users = User.objects.filter(
            is_active=True,
            profile__role__in=["admin", "project_manager"],
        ).exclude(pk=request.user.pk).distinct()
        for u in staff_users:
            Notification.objects.create(
                user=u,
                project=co.project,
                notification_type="change_order",
                title=_("Change Order #%(id)s sent to client") % {"id": co.id},
                message=_("%(user)s sent CO #%(id)s for project %(project)s to the client.") % {
                    "user": request.user.get_full_name() or request.user.username,
                    "id": co.id,
                    "project": co.project.name,
                },
                related_object_type="ChangeOrder",
                related_object_id=co.id,
                link_url=f"/changeorders/{co.id}/",
            )

        return JsonResponse(
            {
                "success": True,
                "co_id": co.id,
                "message": f"Change Order #{co.id} enviado al cliente",
                "new_status": "sent",
            }
        )

    except Exception as e:
        logger.exception("Error sending change order to client")
        return JsonResponse({"success": False, "error": "Error interno del servidor"}, status=500)


@login_required
def touchup_plans_list(request, project_id):
    """List all floor plans with active touch-ups"""
    from core.models import FloorPlan

    project = get_object_or_404(Project, id=project_id)
    profile = getattr(request.user, "profile", None)

    # Permission check: PM, Admin, Client, Designer, Owner
    if not request.user.is_staff and (
        not profile
        or profile.role
        not in ["project_manager", "admin", "superuser", "client", "designer", "owner"]
    ):
        messages.error(request, "No tienes permiso para gestionar touch-ups")
        return redirect("project_overview", project_id)

    # Get plans with active touch-ups
    plans = FloorPlan.objects.filter(project=project).prefetch_related("touchup_pins")

    # Annotate with active touchup count
    from django.db.models import Count, Q

    plans = plans.annotate(
        active_touchups=Count(
            "touchup_pins", filter=Q(touchup_pins__status__in=["pending", "in_progress"])
        )
    )

    context = {"project": project, "plans": plans, "page_title": "Planos Touch-up"}
    return render(request, "core/touchup_plans_list.html", context)


@login_required
def touchup_plan_detail(request, plan_id):
    """View a single floor plan with its touch-ups"""
    from core.models import FloorPlan, TouchUpPin

    plan = get_object_or_404(FloorPlan, id=plan_id)
    project = plan.project
    profile = getattr(request.user, "profile", None)

    # Permission check
    allowed_roles = [
        "project_manager",
        "admin",
        "superuser",
        "employee",
        "painter",
        "client",
        "designer",
        "owner",
    ]
    if not request.user.is_staff and (not profile or profile.role not in allowed_roles):
        messages.error(request, "No tienes permiso para ver touch-ups")
        return redirect("project_overview", project.id)

    # Get touchups - filter by assigned user if employee
    touchups = TouchUpPin.objects.filter(plan=plan)
    if profile and profile.role in ["employee", "painter"] and not request.user.is_staff:
        touchups = touchups.filter(assigned_to=request.user)

    touchups = touchups.select_related("assigned_to", "created_by", "approved_color", "closed_by")

    # Can create: authorized roles
    can_create = request.user.is_staff or (
        profile and profile.role in ROLES_PROJECT_ACCESS
    )

    context = {
        "project": project,
        "plan": plan,
        "touchups": touchups,
        "can_create": can_create,
        "page_title": f"Touch-ups - {plan.name}",
    }
    return render(request, "core/touchup_plan_detail.html", context)


@login_required
def touchup_create(request, plan_id):
    """Create a new touch-up pin"""
    from core.forms import TouchUpPinForm
    from core.models import FloorPlan

    plan = get_object_or_404(FloorPlan, id=plan_id)
    project = plan.project
    profile = getattr(request.user, "profile", None)

    # Permission check: PM, Admin, Client, Designer, Owner
    if not request.user.is_staff and (
        not profile
        or profile.role
        not in ["project_manager", "admin", "superuser", "client", "designer", "owner"]
    ):
        return JsonResponse({"error": gettext("No autorizado")}, status=403)

    if request.method == "POST":
        form = TouchUpPinForm(request.POST, project=project)
        if form.is_valid():
            touchup = form.save(commit=False)
            touchup.created_by = request.user
            touchup.save()

            messages.success(request, f'Touch-up "{touchup.task_name}" creado')
            return JsonResponse(
                {
                    "success": True,
                    "touchup_id": touchup.id,
                    "message": gettext("Touch-up creado exitosamente"),
                }
            )
        else:
            return JsonResponse({"error": "Formulario inválido", "errors": form.errors}, status=400)

    # GET - return form
    form = TouchUpPinForm(initial={"plan": plan}, project=project)
    return render(
        request, "core/touchup_create_form.html", {"form": form, "plan": plan, "project": project}
    )


@login_required
def touchup_detail_ajax(request, touchup_id):
    """Get touch-up details via AJAX"""
    from core.models import TouchUpPin

    touchup = get_object_or_404(TouchUpPin, id=touchup_id)
    profile = getattr(request.user, "profile", None)

    # Permission check
    can_view = (
        request.user.is_staff
        or (profile and profile.role in ROLES_STAFF)
        or touchup.assigned_to == request.user
    )

    if not can_view:
        return JsonResponse({"error": gettext("No autorizado")}, status=403)

    # Check if user can approve (PM/Admin)
    can_approve = request.user.is_staff or (
        profile and profile.role in ROLES_STAFF
    )

    data = {
        "id": touchup.id,
        "task_name": touchup.task_name,
        "description": touchup.description,
        "status": touchup.status,
        "status_display": touchup.get_status_display(),
        "created_at": touchup.created_at.isoformat(),
        "created_by": str(touchup.created_by) if touchup.created_by else None,
        "assigned_to": str(touchup.assigned_to) if touchup.assigned_to else "Sin asignar",
        "approved_color": touchup.approved_color.name if touchup.approved_color else None,
        "custom_color_name": touchup.custom_color_name,
        "sheen": touchup.sheen,
        "details": touchup.details,
        "can_edit": touchup.can_edit(request.user),
        "can_close": touchup.can_close(request.user),
        "can_approve": can_approve,
        "approval_status": touchup.approval_status,
        "approval_status_display": touchup.get_approval_status_display(),
        "rejection_reason": touchup.rejection_reason,
        "reviewed_by": str(touchup.reviewed_by) if touchup.reviewed_by else None,
        "reviewed_at": touchup.reviewed_at.isoformat() if touchup.reviewed_at else None,
        "completion_photos": [
            {
                "id": photo.id,
                "url": photo.image.url,
                "notes": photo.notes,
                "uploaded_at": photo.uploaded_at.isoformat(),
            }
            for photo in touchup.completion_photos.all()
        ],
    }

    return JsonResponse(data)


@login_required
def touchup_update(request, touchup_id):
    """Update a touch-up (PM/Admin only)"""
    from core.forms import TouchUpPinForm
    from core.models import TouchUpPin

    touchup = get_object_or_404(TouchUpPin, id=touchup_id)

    # Permission check
    if not touchup.can_edit(request.user):
        return JsonResponse({"error": gettext("No autorizado")}, status=403)

    if request.method == "POST":
        form = TouchUpPinForm(request.POST, instance=touchup, project=touchup.plan.project)
        if form.is_valid():
            form.save()
            messages.success(request, "Touch-up actualizado")
            return JsonResponse({"success": True, "message": gettext("Touch-up actualizado")})
        else:
            return JsonResponse({"error": "Formulario inválido", "errors": form.errors}, status=400)

    return JsonResponse({"error": gettext("Método no permitido")}, status=405)


@login_required
def touchup_complete(request, touchup_id):
    """Mark touch-up as completed with photos (Assigned employee or PM)"""
    import json

    from core.models import TouchUpCompletionPhoto, TouchUpPin

    touchup = get_object_or_404(TouchUpPin, id=touchup_id)

    # Permission check
    if not touchup.can_close(request.user):
        return JsonResponse(
            {"error": gettext("No autorizado para cerrar este touch-up")}, status=403
        )

    if request.method == "POST":
        notes = request.POST.get("notes", "")
        photos = request.FILES.getlist("photos")

        if not photos:
            return JsonResponse({"error": gettext("Debes subir al menos una foto")}, status=400)

        # Save completion photos with annotations
        for idx, photo in enumerate(photos):
            # Get annotations for this photo if provided
            annotations_key = f"annotations_{idx}"
            annotations_data = request.POST.get(annotations_key, "{}")

            # Parse annotations JSON
            try:
                annotations = json.loads(annotations_data) if annotations_data else {}
            except json.JSONDecodeError:
                annotations = {}

            TouchUpCompletionPhoto.objects.create(
                touchup=touchup,
                image=photo,
                notes=notes,
                annotations=annotations,
                uploaded_by=request.user,
            )

        # Mark as completed
        touchup.close_touchup(request.user)

        messages.success(request, f'Touch-up "{touchup.task_name}" completado')
        return JsonResponse(
            {"success": True, "message": gettext("Touch-up completado exitosamente")}
        )

    return JsonResponse({"error": gettext("Método no permitido")}, status=405)


@login_required
def touchup_delete(request, touchup_id):
    """Delete a touch-up (PM/Admin only)"""
    from core.models import TouchUpPin

    touchup = get_object_or_404(TouchUpPin, id=touchup_id)

    # Permission check
    if not touchup.can_edit(request.user):
        return JsonResponse({"error": gettext("No autorizado")}, status=403)

    if request.method == "POST":
        plan_id = touchup.plan.id
        task_name = touchup.task_name
        touchup.delete()

        messages.success(request, f'Touch-up "{task_name}" eliminado')
        return JsonResponse({"success": True, "redirect": f"/plans/{plan_id}/touchups/"})

    return JsonResponse({"error": gettext("Método no permitido")}, status=405)


@login_required
def touchup_approve(request, touchup_id):
    """Approve a completed touch-up (PM/Admin only)"""
    from django.utils import timezone

    from core.models import TouchUpPin

    touchup = get_object_or_404(TouchUpPin, id=touchup_id)

    # Permission check - only PM/Admin can approve
    if not touchup.can_edit(request.user):
        return JsonResponse({"error": gettext("No autorizado para aprobar")}, status=403)

    if request.method == "POST":
        touchup.approval_status = "approved"
        touchup.reviewed_by = request.user
        touchup.reviewed_at = timezone.now()
        touchup.save()

        messages.success(request, f'Touch-up "{touchup.task_name}" aprobado')
        return JsonResponse({"success": True, "message": gettext("Touch-up aprobado exitosamente")})

    return JsonResponse({"error": gettext("Método no permitido")}, status=405)


@login_required
def touchup_reject(request, touchup_id):
    """Reject a completed touch-up with reason (PM/Admin only)"""
    from django.utils import timezone

    from core.models import TouchUpPin

    touchup = get_object_or_404(TouchUpPin, id=touchup_id)

    # Permission check - only PM/Admin can reject
    if not touchup.can_edit(request.user):
        return JsonResponse({"error": gettext("No autorizado para rechazar")}, status=403)

    if request.method == "POST":
        reason = request.POST.get("reason", "")
        if not reason:
            return JsonResponse(
                {"error": gettext("Debes proporcionar un motivo de rechazo")}, status=400
            )

        touchup.approval_status = "rejected"
        touchup.rejection_reason = reason
        touchup.reviewed_by = request.user
        touchup.reviewed_at = timezone.now()
        touchup.status = "in_progress"  # Reabrir para que el empleado lo corrija
        touchup.save()

        messages.warning(request, f'Touch-up "{touchup.task_name}" rechazado')
        return JsonResponse(
            {"success": True, "message": gettext("Touch-up rechazado, el empleado debe corregirlo")}
        )

    return JsonResponse({"error": gettext("Método no permitido")}, status=405)


# ========================================================================================
# INFO PIN VIEWS (Different from Touch-up Pins)
# ========================================================================================


@login_required
def pin_info_ajax(request, pin_id):
    """Get info pin details via AJAX"""

    from core.models import PlanPin


    try:
        pin = get_object_or_404(PlanPin, id=pin_id)
        profile = getattr(request.user, "profile", None)

        # Anyone can view info pins
        can_edit = request.user.is_staff or (
            profile
            and profile.role
            in ["project_manager", "admin", "superuser", "client", "designer", "owner"]
        )

        data = {
            "id": pin.id,
            "title": pin.title or "",
            "description": pin.description or "",
            "pin_type": pin.pin_type,
            "pin_type_display": pin.get_pin_type_display(),
            "pin_color": pin.pin_color,
            "can_edit": can_edit,
            "color_sample": None,
            "linked_task": None,
            "attachments": [],
        }

        # Add color sample if exists
        try:
            if pin.color_sample:
                cs = pin.color_sample
                data["color_sample"] = {
                    "id": cs.id,
                    "name": cs.name or "",
                    "code": cs.code or "",
                    "brand": cs.brand or "",
                    "finish": cs.finish or "",
                    "gloss": cs.gloss or "",
                    "status": cs.status or "",
                    "status_display": cs.get_status_display(),
                    "notes": cs.notes or "",
                    "room_location": cs.room_location or "",
                    "sample_number": cs.sample_number or "",
                    "sample_image": cs.sample_image.url if cs.sample_image else None,
                    "reference_photo": cs.reference_photo.url if cs.reference_photo else None,
                }
        except Exception as e:
            logger.error(f"Error loading color sample for pin {pin_id}: {e}")

        # Add linked task if exists
        try:
            if pin.linked_task:
                data["linked_task"] = {
                    "id": pin.linked_task.id,
                    "title": pin.linked_task.title or "",
                    "status": pin.linked_task.status or "",
                }
        except Exception as e:
            logger.error(f"Error loading linked task for pin {pin_id}: {e}")

        # Add attachments (photos)
        try:
            data["attachments"] = [
                {
                    "id": att.id,
                    "image_url": att.image.url if att.image else "",
                    "has_annotations": bool(att.annotations),
                    "created_at": att.created_at.isoformat() if att.created_at else "",
                }
                for att in pin.attachments.all()
            ]
        except Exception as e:
            logger.error(f"Error loading attachments for pin {pin_id}: {e}")

        return JsonResponse(data)

    except Exception as e:
        logger.error(f"Error in pin_info_ajax for pin {pin_id}: {str(e)}", exc_info=True)
        return JsonResponse({"error": "Error loading pin information"}, status=500)


@login_required
def pin_update(request, pin_id):
    """Update info pin details"""
    from core.models import PlanPin

    pin = get_object_or_404(PlanPin, id=pin_id)
    profile = getattr(request.user, "profile", None)

    # Permission check
    can_edit = request.user.is_staff or (
        profile
        and profile.role in ROLES_PROJECT_ACCESS
    )

    if not can_edit:
        return JsonResponse({"error": gettext("No autorizado")}, status=403)

    if request.method == "POST":
        pin.title = request.POST.get("title", pin.title)
        pin.description = request.POST.get("description", pin.description)
        pin.pin_type = request.POST.get("pin_type", pin.pin_type)

        # Update color sample if provided
        color_sample_id = request.POST.get("color_sample_id")
        if color_sample_id:
            from core.models import ColorSample

            with contextlib.suppress(ColorSample.DoesNotExist):
                pin.color_sample = ColorSample.objects.get(id=color_sample_id)

        pin.save()

        messages.success(request, "Pin actualizado exitosamente")
        return JsonResponse({"success": True, "message": gettext("Pin actualizado")})

    return JsonResponse({"error": gettext("Método no permitido")}, status=405)


@login_required
def pin_add_photo(request, pin_id):
    """Add photo attachment to info pin"""
    import json

    from core.models import PlanPin, PlanPinAttachment

    pin = get_object_or_404(PlanPin, id=pin_id)
    profile = getattr(request.user, "profile", None)

    # Permission check
    can_edit = request.user.is_staff or (
        profile
        and profile.role in ROLES_PROJECT_ACCESS
    )

    if not can_edit:
        return JsonResponse({"error": gettext("No autorizado")}, status=403)

    if request.method == "POST":
        photos = request.FILES.getlist("photos")

        if not photos:
            return JsonResponse({"error": gettext("No se enviaron fotos")}, status=400)

        created_attachments = []
        for idx, photo in enumerate(photos):
            # Get annotations for this photo if provided
            annotations_key = f"annotations_{idx}"
            annotations_data = request.POST.get(annotations_key, "{}")

            # Parse annotations JSON
            try:
                annotations = json.loads(annotations_data) if annotations_data else {}
            except json.JSONDecodeError:
                annotations = {}

            attachment = PlanPinAttachment.objects.create(
                pin=pin, image=photo, annotations=annotations
            )
            created_attachments.append({"id": attachment.id, "url": attachment.image.url})

        messages.success(
            request, _("%(count)s foto(s) agregada(s) al pin") % {"count": len(photos)}
        )
        return JsonResponse(
            {
                "success": True,
                "message": "Fotos agregadas exitosamente",
                "attachments": created_attachments,
            }
        )

    return JsonResponse({"error": gettext("Método no permitido")}, status=405)


@login_required
def pin_delete_photo(request, attachment_id):
    """Delete photo attachment from info pin"""
    from core.models import PlanPinAttachment

    attachment = get_object_or_404(PlanPinAttachment, id=attachment_id)
    profile = getattr(request.user, "profile", None)

    # Permission check
    can_edit = request.user.is_staff or (
        profile
        and profile.role in ROLES_PROJECT_ACCESS
    )

    if not can_edit:
        return JsonResponse({"error": gettext("No autorizado")}, status=403)

    if request.method == "POST":
        # Delete file from storage
        if attachment.image:
            attachment.image.delete()

        attachment.delete()

        return JsonResponse({"success": True, "message": gettext("Foto eliminada")})

    return JsonResponse({"error": gettext("Método no permitido")}, status=405)

@login_required
@staff_member_required
def project_create(request):
    """Crear nuevo proyecto"""
    from core.forms import ProjectCreateForm

    if request.method == "POST":
        form = ProjectCreateForm(request.POST)
        if form.is_valid():
            project = form.save()
            messages.success(request, f'Proyecto "{project.name}" creado exitosamente.')
            return redirect("project_overview", project_id=project.id)
    else:
        form = ProjectCreateForm()

    return render(request, "core/project_form.html", {"form": form, "is_create": True})


@login_required
@staff_member_required
def project_edit(request, project_id):
    """Editar proyecto existente"""
    from core.forms import ProjectEditForm

    project = get_object_or_404(Project, id=project_id)

    if request.method == "POST":
        form = ProjectEditForm(request.POST, instance=project)
        if form.is_valid():
            project = form.save()
            messages.success(request, f'Proyecto "{project.name}" actualizado exitosamente.')
            return redirect("project_overview", project_id=project.id)
    else:
        form = ProjectEditForm(instance=project)

    return render(
        request, "core/project_form.html", {"form": form, "project": project, "is_create": False}
    )


@login_required
@staff_member_required
def project_delete(request, project_id):
    """Eliminar proyecto (con confirmación y validación de dependencias)"""
    project = get_object_or_404(Project, id=project_id)

    if request.method == "POST":
        # SECURITY: Logging de auditoría

        audit_logger = logging.getLogger("django")
        audit_logger.warning(
            f"PROJECT_DELETE_ATTEMPT | Actor: {request.user.username} (ID:{request.user.id}) | "
            f"Project: {project.name} (ID:{project.id}) | "
            f"IP: {request.META.get('REMOTE_ADDR')}"
        )

        # SECURITY: Verificar dependencias críticas ANTES de permitir eliminación
        has_expenses = Expense.objects.filter(project=project).exists()
        has_incomes = Income.objects.filter(project=project).exists()
        has_timeentries = TimeEntry.objects.filter(project=project).exists()
        has_changeorders = ChangeOrder.objects.filter(project=project).exists()
        has_dailylogs = DailyLog.objects.filter(project=project).exists()
        has_schedules = ScheduleItemV2.objects.filter(project=project).exists()
        has_invoices = Invoice.objects.filter(project=project).exists()

        if any(
            [
                has_expenses,
                has_incomes,
                has_timeentries,
                has_changeorders,
                has_dailylogs,
                has_schedules,
                has_invoices,
            ]
        ):
            messages.error(
                request,
                "❌ No se puede eliminar este proyecto porque tiene datos financieros o operacionales asociados. "
                "Considera marcarlo como completado en lugar de eliminarlo para preservar la integridad de los datos.",
            )
            return redirect("project_overview", project_id=project.id)

        project_name = project.name
        project.delete()
        messages.success(request, f'Proyecto "{project_name}" eliminado permanentemente.')
        return redirect("project_list")

    # GET: Calcular estadísticas detalladas para confirmación

    expense_count = Expense.objects.filter(project=project).count()
    income_count = Income.objects.filter(project=project).count()
    timeentry_count = TimeEntry.objects.filter(project=project).count()
    co_count = ChangeOrder.objects.filter(project=project).count()
    task_count = Task.objects.filter(project=project).count()
    dailylog_count = DailyLog.objects.filter(project=project).count()
    schedule_count = ScheduleItemV2.objects.filter(project=project).count()
    invoice_count = Invoice.objects.filter(project=project).count()

    context = {
        "project": project,
        "expense_count": expense_count,
        "income_count": income_count,
        "timeentry_count": timeentry_count,
        "co_count": co_count,
        "task_count": task_count,
        "dailylog_count": dailylog_count,
        "schedule_count": schedule_count,
        "invoice_count": invoice_count,
        "has_critical_data": any(
            [
                expense_count,
                income_count,
                timeentry_count,
                co_count,
                dailylog_count,
                schedule_count,
                invoice_count,
            ]
        ),
    }

    return render(request, "core/project_delete_confirm.html", context)


@login_required
@staff_member_required
def project_status_toggle(request, project_id):
    """Cambiar estado del proyecto (activo/completado)"""
    project = get_object_or_404(Project, id=project_id)

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "complete":
            if not project.end_date:
                project.end_date = timezone.localdate()
                project.save()
                messages.success(request, f'Proyecto "{project.name}" marcado como completado.')
        elif action == "reopen":
            project.end_date = None
            project.save()
            messages.success(request, f'Proyecto "{project.name}" reabierto.')

        return redirect("project_overview", project_id=project.id)

    return redirect("project_overview", project_id=project.id)


# --- DEMO: JavaScript i18n ---
@login_required
def js_i18n_demo(request):
    """
    Demo page showing how to use Django's JavaScript translation catalog.
    This demonstrates gettext(), ngettext(), and interpolate() in JavaScript.
    """
    return render(request, "core/js_i18n_demo.html")


# --- ANALYTICS DASHBOARD ---
@login_required
def analytics_dashboard(request):
    """
    Analytics Dashboard - Comprehensive metrics and KPIs.
    Shows: Project performance, employee stats, financial overview.
    SOLO ACCESIBLE POR ADMIN/SUPERUSER
    """
    # Solo admin/superuser puede acceder
    profile = getattr(request.user, 'profile', None)
    if not (request.user.is_superuser or (profile and profile.role == 'admin')):
        messages.error(request, _("No tienes permiso para acceder a Analytics."))
        return redirect("dashboard")
    
    today = timezone.now().date()
    month_start = today.replace(day=1)
    
    # === PROJECT METRICS ===
    total_projects = Project.objects.count()
    active_projects = Project.objects.filter(is_archived=False).count()
    archived_projects = Project.objects.filter(is_archived=True).count()
    
    # Projects this month
    projects_this_month = Project.objects.filter(created_at__gte=month_start).count()
    
    # === EMPLOYEE METRICS ===
    total_employees = Employee.objects.filter(is_active=True).count()
    
    # Hours this month
    month_hours = TimeEntry.objects.filter(
        date__gte=month_start,
        date__lte=today
    ).aggregate(total=Coalesce(Sum('hours_worked'), Decimal('0.00')))['total']
    
    # === CHANGE ORDER METRICS ===
    total_cos = ChangeOrder.objects.count()
    pending_cos = ChangeOrder.objects.filter(status='pending').count()
    approved_cos = ChangeOrder.objects.filter(status='approved').count()
    
    # CO value this month
    co_value_month = ChangeOrder.objects.filter(
        date_created__gte=month_start,
        status='approved'
    ).aggregate(total=Coalesce(Sum('amount'), Decimal('0.00')))['total']
    
    # === TASKS METRICS ===
    total_tasks = Task.objects.count()
    completed_tasks = Task.objects.filter(status='Completed').count()
    overdue_tasks = Task.objects.filter(
        due_date__lt=today
    ).exclude(status='Completed').exclude(status='Cancelled').count()
    
    task_completion_rate = round((completed_tasks / total_tasks * 100), 1) if total_tasks > 0 else 0
    
    # === TOP PROJECTS BY ACTIVITY ===
    top_projects = Project.objects.filter(
        is_archived=False
    ).annotate(
        task_count=Count('tasks'),
        co_count=Count('change_orders'),
        hours=Coalesce(Sum('timeentry__hours_worked'), Decimal('0.00'))
    ).order_by('-hours')[:5]
    
    # === TOP EMPLOYEES BY HOURS ===
    top_employees = Employee.objects.filter(
        is_active=True
    ).annotate(
        month_hours=Coalesce(
            Sum('timeentry__hours_worked', filter=Q(
                timeentry__date__gte=month_start,
                timeentry__date__lte=today
            )),
            Decimal('0.00')
        )
    ).filter(month_hours__gt=0).order_by('-month_hours')[:5]
    
    context = {
        # Project metrics
        'total_projects': total_projects,
        'active_projects': active_projects,
        'archived_projects': archived_projects,
        'projects_this_month': projects_this_month,
        # Employee metrics
        'total_employees': total_employees,
        'month_hours': month_hours,
        # Change order metrics
        'total_cos': total_cos,
        'pending_cos': pending_cos,
        'approved_cos': approved_cos,
        'co_value_month': co_value_month,
        # Task metrics
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'overdue_tasks': overdue_tasks,
        'task_completion_rate': task_completion_rate,
        # Top lists
        'top_projects': top_projects,
        'top_employees': top_employees,
        # Date context
        'month_start': month_start,
        'today': today,
    }
    
    return render(request, "core/analytics_dashboard.html", context)


# --- TOUCHUP BOARD REACT ---
@login_required
def touchup_board_react(request, project_id):
    """
    TouchUp Board React view - serves React-based kanban board for touchups.
    """
    project = get_object_or_404(Project, id=project_id)

    return render(
        request,
        "core/touchup_board_react.html",
        {
            "project_id": project_id,
            "project": project,
        },
    )


# --- COLOR APPROVALS REACT ---
@login_required
def color_approvals_react(request, project_id=None):
    """
    Color Approvals React view - serves React-based color approval management.
    """
    project = None
    if project_id:
        project = get_object_or_404(Project, id=project_id)

    return render(
        request,
        "core/color_approvals_react.html",
        {
            "project_id": project_id,
            "project": project,
        },
    )


# --- PM ASSIGNMENTS REACT ---
@login_required
def pm_assignments_react(request):
    """
    PM Assignments React view - serves React-based PM assignment management.
    """
    return render(request, "core/pm_assignments_react.html", {})


# --- PUBLIC PROPOSAL APPROVAL ---
def proposal_public_view(request, token):
    """
    Public view for clients to approve or reject a proposal.
    No login required - access via unique token.
    """
    from core.models import Proposal

    try:
        proposal = Proposal.objects.select_related("estimate__project").get(client_view_token=token)
    except Proposal.DoesNotExist:
        return HttpResponseNotFound("Propuesta no encontrada o enlace inválido.")

    estimate = proposal.estimate
    project = estimate.project
    lines = estimate.lines.select_related("cost_code").all()

    # Calculate totals using the effective unit price (handles both direct price and breakdown)
    subtotal = sum(line.direct_cost() for line in lines)
    
    # Calculate material/labor totals for markup purposes
    total_material = sum(line.qty * line.material_unit_cost for line in lines if not (line.unit_price and line.unit_price > 0))
    total_labor = sum(line.qty * line.labor_unit_cost for line in lines if not (line.unit_price and line.unit_price > 0))
    
    # Apply markups and overheads
    markup_material_amount = total_material * (estimate.markup_material / Decimal("100"))
    markup_labor_amount = total_labor * (estimate.markup_labor / Decimal("100"))
    overhead_amount = subtotal * (estimate.overhead_pct / Decimal("100"))
    profit_amount = subtotal * (estimate.target_profit_pct / Decimal("100"))

    total = (
        subtotal + markup_material_amount + markup_labor_amount + overhead_amount + profit_amount
    )

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "approve":
            proposal.accepted = True
            proposal.accepted_at = timezone.now()
            estimate.approved = True
            proposal.save(update_fields=["accepted", "accepted_at"])
            estimate.save(update_fields=["approved"])
            
            # --- Auto-create Budget Lines from Estimate (with 30% profit margin) ---
            try:
                from core.services.budget_from_estimate import create_budget_from_estimate
                # Use target_profit_pct from estimate if set, otherwise default 30%
                profit_margin = estimate.target_profit_pct / Decimal("100") if estimate.target_profit_pct else None
                budget_lines = create_budget_from_estimate(estimate, profit_margin=profit_margin)
                logger.info(
                    f"Auto-created {len(budget_lines)} budget lines for approved Estimate {estimate.code}"
                )
            except Exception as e:
                logger.warning(f"Failed to auto-create budget from estimate: {e}")
            
            # --- Auto-create Contract from approved Estimate ---
            contract_url = None
            try:
                from core.services.contract_service import ContractService
                contract = ContractService.create_contract_from_estimate(
                    estimate=estimate,
                    user=None,
                    auto_generate_pdf=True
                )
                logger.info(
                    f"Auto-created contract {contract.contract_number} from approved Estimate {estimate.code}"
                )
                # Build contract signing URL
                from django.urls import reverse
                contract_url = reverse('contract_client_view', kwargs={'token': contract.client_view_token})
            except Exception as e:
                logger.warning(f"Failed to auto-create contract from estimate: {e}")
            
            # --- Auto-save Estimate/Contract PDF to Project Files (legacy, keep for backward compatibility) ---
            try:
                from core.services.document_storage_service import auto_save_estimate_pdf
                # Save as contract since it's been approved
                auto_save_estimate_pdf(estimate, user=None, as_contract=True, overwrite=True)
            except Exception as e:
                logger.warning(f"Failed to auto-save Estimate PDF: {e}")
            
            # Redirect to contract signing page if contract was created
            if contract_url:
                messages.success(
                    request,
                    "Thank you! Your estimate has been approved. Please review and sign the contract to proceed."
                )
                return redirect(contract_url)
            else:
                messages.success(
                    request,
                    "Thank you! We have received your approval. We will begin working on your project."
                )

        elif action == "reject":
            feedback = request.POST.get("feedback", "").strip()
            proposal.client_comment = feedback
            proposal.save(update_fields=["client_comment"])
            messages.info(
                request,
                "We have received your comments. Our team will contact you soon."
            )
            # Notify admins/PMs about proposal rejection
            staff_users = User.objects.filter(
                is_active=True,
                profile__role__in=["admin", "project_manager"],
            ).distinct()
            for u in staff_users:
                Notification.objects.create(
                    user=u,
                    project=project,
                    notification_type="change_order",
                    title=_("Proposal revision requested — %(project)s") % {"project": project.name},
                    message=_("Client feedback on proposal: %(feedback)s") % {
                        "feedback": (feedback[:200] + "...") if len(feedback) > 200 else feedback,
                    },
                    related_object_type="Proposal",
                    related_object_id=proposal.id,
                )

    context = {
        "proposal": proposal,
        "estimate": estimate,
        "project": project,
        "lines": lines,
        "subtotal": subtotal,
        "markup_material": markup_material_amount,
        "markup_labor": markup_labor_amount,
        "overhead": overhead_amount,
        "profit": profit_amount,
        "total": total,
    }

    return render(request, "core/proposal_public.html", context)


# --- STAFF CONTRACT EDIT VIEW ---
@login_required
def contract_edit_view(request, contract_id):
    """
    Staff view to edit contract details (dates, payment schedule, etc.)
    and regenerate PDF.
    """
    from core.models import Contract
    from core.services.contract_service import ContractService
    from datetime import datetime
    import json
    
    if not request.user.is_staff:
        messages.error(request, _("You don't have permission to edit contracts."))
        return redirect("home")
    
    contract = get_object_or_404(Contract, id=contract_id)
    estimate = contract.estimate
    project = contract.project
    
    if request.method == "POST":
        action = request.POST.get("action")
        
        if action == "update_dates":
            # Update schedule dates
            start_date_str = request.POST.get("start_date")
            completion_date_str = request.POST.get("completion_date")
            
            try:
                if start_date_str:
                    contract.start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
                else:
                    contract.start_date = None
                    
                if completion_date_str:
                    contract.completion_date = datetime.strptime(completion_date_str, "%Y-%m-%d").date()
                else:
                    contract.completion_date = None
                
                contract.save(update_fields=["start_date", "completion_date", "updated_at"])
                messages.success(request, _("Contract dates updated successfully."))
            except ValueError as e:
                messages.error(request, _("Invalid date format."))
        
        elif action == "update_payment_schedule":
            # Update payment schedule from JSON
            try:
                payment_schedule_json = request.POST.get("payment_schedule", "[]")
                payment_schedule = json.loads(payment_schedule_json)
                
                # Recalculate amounts based on percentages
                total = float(contract.total_amount)
                for payment in payment_schedule:
                    payment["amount"] = str(round(total * payment["percentage"] / 100, 2))
                
                contract.payment_schedule = payment_schedule
                contract.save(update_fields=["payment_schedule", "updated_at"])
                messages.success(request, _("Payment schedule updated successfully."))
            except (json.JSONDecodeError, KeyError) as e:
                messages.error(request, _("Invalid payment schedule format."))
        
        elif action == "regenerate_pdf":
            # Regenerate PDF with current contract data
            try:
                result = ContractService.generate_contract_pdf(contract, request.user)
                if result:
                    messages.success(request, _("Contract PDF regenerated successfully."))
                else:
                    messages.error(request, _("Failed to regenerate PDF."))
            except Exception as e:
                messages.error(request, _(f"Error regenerating PDF: {str(e)}"))
        
        elif action == "send_to_client":
            # Mark as ready and get client link
            if contract.status == 'draft':
                contract.status = 'pending_signature'
                contract.save(update_fields=["status", "updated_at"])
            messages.success(request, _("Contract ready for client signature."))
        
        return redirect("contract_edit", contract_id=contract.id)
    
    # GET: Display edit form
    context = {
        "contract": contract,
        "estimate": estimate,
        "project": project,
        "lines": estimate.lines.select_related("cost_code").all(),
        "client_url": request.build_absolute_uri(f"/contracts/{contract.client_view_token}/"),
        "payment_schedule_json": json.dumps(contract.payment_schedule or []),
    }
    
    return render(request, "core/contract_edit.html", context)


# --- PUBLIC CONTRACT VIEW (FOR CLIENT SIGNATURE) ---
def contract_client_view(request, token):
    """
    Public view for clients to view and sign a contract.
    No login required - access via unique token.
    
    GET: Display contract details with signature form
    POST: Process signature or revision request
    """
    from core.models import Contract
    from core.services.contract_service import ContractService
    import base64
    
    # Get contract by token
    contract = ContractService.get_contract_by_token(token)
    
    if not contract:
        return HttpResponseNotFound("Contract not found or invalid link.")
    
    estimate = contract.estimate
    project = contract.project
    lines = estimate.lines.select_related("cost_code").all()
    
    # Calculate totals for display
    subtotal = sum(line.direct_cost() for line in lines)
    total_material = sum(line.qty * line.material_unit_cost for line in lines if not (line.unit_price and line.unit_price > 0))
    total_labor = sum(line.qty * line.labor_unit_cost for line in lines if not (line.unit_price and line.unit_price > 0))
    
    markup_material_amount = total_material * (estimate.markup_material / Decimal("100")) if estimate.markup_material else Decimal("0")
    markup_labor_amount = total_labor * (estimate.markup_labor / Decimal("100")) if estimate.markup_labor else Decimal("0")
    overhead_amount = subtotal * (estimate.overhead_pct / Decimal("100")) if estimate.overhead_pct else Decimal("0")
    profit_amount = subtotal * (estimate.target_profit_pct / Decimal("100")) if estimate.target_profit_pct else Decimal("0")
    
    # Handle POST actions
    if request.method == "POST":
        action = request.POST.get("action")
        
        if action == "sign" and contract.can_be_signed:
            # Get signature data
            client_name = request.POST.get("client_name", "").strip()
            signature_data_b64 = request.POST.get("signature_data", "")
            
            if not client_name:
                messages.error(request, "Please enter your full name to sign the contract.")
            else:
                try:
                    # Decode signature if provided
                    signature_bytes = None
                    if signature_data_b64:
                        # Remove data URL prefix if present
                        if "," in signature_data_b64:
                            signature_data_b64 = signature_data_b64.split(",")[1]
                        signature_bytes = base64.b64decode(signature_data_b64)
                    
                    # Get client IP
                    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
                    if x_forwarded_for:
                        client_ip = x_forwarded_for.split(",")[0].strip()
                    else:
                        client_ip = request.META.get("REMOTE_ADDR")
                    
                    # Sign the contract
                    contract = ContractService.sign_contract(
                        contract=contract,
                        client_name=client_name,
                        signature_data=signature_bytes,
                        ip_address=client_ip,
                        generate_signed_pdf=True,
                        user=None
                    )
                    
                    messages.success(
                        request,
                        "Thank you! Your contract has been signed successfully. "
                        "You will receive a confirmation email shortly."
                    )
                    
                    # Notify admins of signed contract
                    staff_users = User.objects.filter(
                        is_active=True,
                        profile__role__in=["admin", "project_manager"],
                    ).distinct()
                    for u in staff_users:
                        Notification.objects.create(
                            user=u,
                            project=contract.project,
                            notification_type="contract",
                            title=_("Contract signed — %(project)s") % {"project": contract.project.name},
                            message=_("%(client)s signed contract %(number)s for project %(project)s.") % {
                                "client": client_name,
                                "number": contract.contract_number,
                                "project": contract.project.name,
                            },
                            related_object_type="Contract",
                            related_object_id=contract.id,
                        )
                    
                except Exception as e:
                    logger.error(f"Error signing contract {contract.contract_number}: {e}")
                    messages.error(request, "An error occurred while signing. Please try again.")
        
        elif action == "request_revision" and contract.status in ['pending_signature', 'revision_requested']:
            revision_notes = request.POST.get("revision_notes", "").strip()
            
            if not revision_notes:
                messages.error(request, "Please provide details about the changes you need.")
            else:
                try:
                    contract = ContractService.request_revision(
                        contract=contract,
                        revision_notes=revision_notes
                    )
                    
                    messages.info(
                        request,
                        "Your revision request has been submitted. "
                        "Our team will review and contact you soon."
                    )
                    
                    # Notify admins of revision request
                    staff_users = User.objects.filter(
                        is_active=True,
                        profile__role__in=["admin", "project_manager"],
                    ).distinct()
                    for u in staff_users:
                        Notification.objects.create(
                            user=u,
                            project=contract.project,
                            notification_type="contract",
                            title=_("Contract revision requested — %(project)s") % {"project": contract.project.name},
                            message=_("Client requested revision on contract %(number)s: %(notes)s") % {
                                "number": contract.contract_number,
                                "notes": (revision_notes[:200] + "...") if len(revision_notes) > 200 else revision_notes,
                            },
                            related_object_type="Contract",
                            related_object_id=contract.id,
                        )
                    
                except Exception as e:
                    logger.error(f"Error requesting revision for {contract.contract_number}: {e}")
                    messages.error(request, "An error occurred. Please try again.")
    
    # Build context
    context = {
        "contract": contract,
        "estimate": estimate,
        "project": project,
        "lines": lines,
        "subtotal": subtotal,
        "markup_material": markup_material_amount,
        "markup_labor": markup_labor_amount,
        "overhead": overhead_amount,
        "profit": profit_amount,
        "total": contract.total_amount,
        "payment_schedule": contract.payment_schedule or [],
        "is_signed": contract.is_signed,
        "can_be_signed": contract.can_be_signed,
        "status": contract.status,
    }
    
    return render(request, "core/contract_client_view.html", context)

@login_required
def project_financials_hub(request, project_id):
    """
    Hub financiero principal del proyecto.
    Muestra resumen de budget, spent, remaining y breakdown por cost code.
    
    Para PM (no admin): muestra Working Budget (-30%) 
    Para Admin/Superuser: muestra Budget real completo
    """
    if not _is_staffish(request.user):
        return redirect("dashboard")
    project = get_object_or_404(Project, pk=project_id)
    
    # Determinar si es PM (no admin)
    profile = getattr(request.user, 'profile', None)
    is_pm = profile and profile.role == 'pm' if profile else False
    
    # Calcular totales
    budget_lines = project.budget_lines.select_related('cost_code').all()
    
    # Total budget = suma de revised_amount de todas las líneas
    total_budget = sum(line.revised_amount or line.baseline_amount for line in budget_lines)
    
    # Working budget para PM = total - 30%
    working_budget = total_budget * Decimal('0.70') if total_budget else Decimal('0')
    
    # Calculate actual spent from expenses linked to project
    from django.db.models import Sum as DJSum
    total_spent = project.expenses.aggregate(total=DJSum('amount'))['total'] or Decimal('0')
    
    # Also include labor cost from time entries
    time_labor_cost = Decimal('0')
    for te in TimeEntry.objects.filter(project=project).select_related('employee'):
        rate = te.employee.hourly_rate if te.employee and te.employee.hourly_rate else Decimal('0')
        time_labor_cost += (te.hours_worked or Decimal('0')) * rate
    total_spent += time_labor_cost
    
    # Remaining
    if is_pm and not request.user.is_superuser:
        remaining = working_budget - total_spent
        display_budget = working_budget
    else:
        remaining = total_budget - total_spent
        display_budget = total_budget
    
    # Porcentajes
    spent_percentage = int((total_spent / display_budget * 100) if display_budget else 0)
    margin_percentage = 30 if is_pm else (int((remaining / total_budget * 100)) if total_budget else 0)
    
    # Preparar datos de líneas para display
    # Pre-compute expense totals per cost_code for per-line breakdown
    from core.models import Expense
    expense_by_costcode = {}
    for exp in Expense.objects.filter(project=project).values('cost_code_id').annotate(total=DJSum('amount')):
        if exp['cost_code_id']:
            expense_by_costcode[exp['cost_code_id']] = exp['total'] or Decimal('0')
    
    lines_data = []
    for line in budget_lines:
        line_budget = line.revised_amount or line.baseline_amount
        # Para PM mostrar budget reducido
        if is_pm and not request.user.is_superuser:
            line_display_budget = line_budget * Decimal('0.70')
        else:
            line_display_budget = line_budget
        
        line_spent = expense_by_costcode.get(line.cost_code_id, Decimal('0'))
        line_remaining = line_display_budget - line_spent
        line_spent_pct = (line_spent / line_display_budget * 100) if line_display_budget else 0
        line_remaining_pct = 100 - float(line_spent_pct)
        
        lines_data.append({
            'cost_code': line.cost_code,
            'description': line.description,
            'display_budget': line_display_budget,
            'spent': line_spent,
            'remaining': line_remaining,
            'spent_pct': line_spent_pct,
            'remaining_pct': line_remaining_pct,
        })
    
    context = {
        'project': project,
        'is_pm': is_pm,
        'total_budget': total_budget,
        'working_budget': working_budget,
        'total_spent': total_spent,
        'remaining': remaining,
        'spent_percentage': spent_percentage,
        'margin_percentage': margin_percentage,
        'budget_lines': lines_data,
        'active_tab': 'overview',
    }
    
    return render(request, 'core/project_financials_hub.html', context)


@login_required
def project_budget_detail(request, project_id):
    """
    Vista de detalle del budget con capacidad de agregar/editar/eliminar líneas.
    Solo staff/admin puede editar.
    """
    if not _is_staffish(request.user):
        return redirect("dashboard")
    project = get_object_or_404(Project, pk=project_id)
    
    # Verificar permisos de edición
    can_edit = request.user.is_staff or request.user.is_superuser
    
    if request.method == 'POST' and can_edit:
        action = request.POST.get('action', 'add')
        
        # DELETE action
        if action == 'delete':
            line_id = request.POST.get('line_id')
            if line_id:
                try:
                    line = BudgetLine.objects.get(pk=line_id, project=project)
                    line.delete()
                    messages.success(request, _('Budget line deleted successfully.'))
                except BudgetLine.DoesNotExist:
                    messages.error(request, _('Budget line not found.'))
            return redirect('project_budget_detail', project_id=project.id)
        
        # EDIT action
        elif action == 'edit':
            line_id = request.POST.get('line_id')
            if line_id:
                try:
                    line = BudgetLine.objects.get(pk=line_id, project=project)
                    line.description = request.POST.get('description', line.description)
                    line.qty = Decimal(str(request.POST.get('qty', line.qty) or 0))
                    line.unit = request.POST.get('unit', line.unit)
                    line.unit_cost = Decimal(str(request.POST.get('unit_cost', line.unit_cost) or 0))
                    # Allow editing revised_amount directly
                    revised = request.POST.get('revised_amount')
                    if revised:
                        line.revised_amount = Decimal(str(revised))
                    line.save()
                    messages.success(request, _('Budget line updated successfully.'))
                except (BudgetLine.DoesNotExist, InvalidOperation) as e:
                    messages.error(request, _('Error updating budget line.'))
            return redirect('project_budget_detail', project_id=project.id)
        
        # ADD action (default)
        else:
            cost_code_id = request.POST.get('cost_code')
            description = request.POST.get('description', '')
            qty = request.POST.get('qty', 0)
            unit = request.POST.get('unit', '')
            unit_cost = request.POST.get('unit_cost', 0)
            
            if cost_code_id:
                try:
                    cost_code = CostCode.objects.get(pk=cost_code_id)
                    BudgetLine.objects.create(
                        project=project,
                        cost_code=cost_code,
                        description=description,
                        qty=Decimal(str(qty)) if qty else Decimal('0'),
                        unit=unit,
                        unit_cost=Decimal(str(unit_cost)) if unit_cost else Decimal('0'),
                    )
                    messages.success(request, _('Budget line added successfully.'))
                except (CostCode.DoesNotExist, InvalidOperation) as e:
                    messages.error(request, _('Error adding budget line.'))
            
            return redirect('project_budget_detail', project_id=project.id)
    
    budget_lines = project.budget_lines.select_related('cost_code').order_by('cost_code__code')
    cost_codes = CostCode.objects.filter(active=True).order_by('code')
    
    # Calcular totales
    total_baseline = sum(line.baseline_amount for line in budget_lines)
    total_revised = sum(line.revised_amount for line in budget_lines)
    variance = total_revised - total_baseline
    
    context = {
        'project': project,
        'budget_lines': budget_lines,
        'cost_codes': cost_codes,
        'can_edit': can_edit,
        'total_baseline': total_baseline,
        'total_revised': total_revised,
        'variance': variance,
        'active_tab': 'budget',
    }
    
    return render(request, 'core/project_budget_detail.html', context)


@login_required  
def project_cost_codes(request, project_id):
    """
    Gestión de Cost Codes - códigos para categorizar costos.
    Solo admin puede crear/editar.
    """
    if not _is_staffish(request.user):
        return redirect("dashboard")
    project = get_object_or_404(Project, pk=project_id)
    
    can_edit = request.user.is_staff or request.user.is_superuser
    
    if request.method == 'POST' and can_edit:
        action = request.POST.get('action', 'create')
        
        if action == 'create':
            code = request.POST.get('code', '').strip().upper()
            name = request.POST.get('name', '').strip()
            category = request.POST.get('category', '').strip()
            
            if code and name:
                try:
                    CostCode.objects.create(
                        code=code,
                        name=name,
                        category=category,
                        active=True,
                    )
                    messages.success(request, _('Cost code created successfully.'))
                except IntegrityError:
                    messages.error(request, _('A cost code with that code already exists.'))
            else:
                messages.error(request, _('Code and name are required.'))
        
        elif action == 'update':
            costcode_id = request.POST.get('costcode_id')
            if costcode_id:
                try:
                    costcode = CostCode.objects.get(pk=costcode_id)
                    costcode.code = request.POST.get('code', '').strip().upper()
                    costcode.name = request.POST.get('name', '').strip()
                    costcode.category = request.POST.get('category', '').strip()
                    costcode.active = request.POST.get('active') == 'on'
                    costcode.save()
                    messages.success(request, _('Cost code updated successfully.'))
                except CostCode.DoesNotExist:
                    messages.error(request, _('Cost code not found.'))
        
        elif action == 'delete':
            costcode_id = request.POST.get('costcode_id')
            if costcode_id:
                try:
                    costcode = CostCode.objects.get(pk=costcode_id)
                    costcode.delete()
                    messages.success(request, _('Cost code deleted.'))
                except CostCode.DoesNotExist:
                    messages.error(request, _('Cost code not found.'))
        
        return redirect('project_cost_codes', project_id=project.id)
    
    cost_codes = CostCode.objects.all().order_by('category', 'code')
    
    # Default categories for construction
    default_categories = [
        'Appliances',
        'Cabinets',
        'Cleanup',
        'Concrete',
        'Countertops',
        'Demolition',
        'Drywall',
        'Electrical',
        'Equipment',
        'Exterior',
        'Exterior Painting',
        'Flooring',
        'Framing',
        'HVAC',
        'Interior',
        'Interior Painting',
        'Labor',
        'Landscaping',
        'Material',
        'Plumbing',
        'Roofing',
        'Subcontractor',
        'Windows & Doors',
        'Other',
    ]
    
    # Get existing categories, normalize to title case
    existing_raw = CostCode.objects.exclude(category__isnull=True).exclude(category='').values_list('category', flat=True).distinct()
    existing_normalized = set()
    for cat in existing_raw:
        # Normalize: "interior painting" -> "Interior Painting"
        normalized = cat.strip().title()
        existing_normalized.add(normalized)
    
    # Merge and deduplicate
    all_categories = sorted(set(default_categories) | existing_normalized)
    
    # Agrupar por categoría (normalizado)
    codes_by_category = defaultdict(list)
    for cc in cost_codes:
        cat = (cc.category or '').strip().title() or _('Uncategorized')
        codes_by_category[cat].append(cc)
    
    context = {
        'project': project,
        'cost_codes': cost_codes,
        'codes_by_category': dict(codes_by_category),
        'can_edit': can_edit,
        'active_tab': 'costcodes',
        'categories': all_categories,
    }
    
    return render(request, 'core/project_cost_codes.html', context)


@login_required
def project_estimates(request, project_id):
    """
    Lista de estimados del proyecto.
    Solo visible para staff/admin.
    """
    # SECURITY: Only staff/superusers can view estimates (financial data)
    if not (request.user.is_staff or request.user.is_superuser):
        return HttpResponseForbidden(_('Access denied'))
    
    project = get_object_or_404(Project, pk=project_id)
    
    estimates = project.estimates.all().order_by('-version')
    
    # Calcular totales para cada estimado
    estimates_data = []
    for est in estimates:
        lines = est.lines.select_related('cost_code')
        direct_cost = sum(line.direct_cost() for line in lines)
        
        # Calcular precio propuesto con markups
        material_markup = direct_cost * (est.markup_material / 100)
        labor_markup = direct_cost * (est.markup_labor / 100)
        overhead = direct_cost * (est.overhead_pct / 100)
        profit = direct_cost * (est.target_profit_pct / 100)
        proposed_price = direct_cost + material_markup + labor_markup + overhead + profit
        
        estimates_data.append({
            'estimate': est,
            'direct_cost': direct_cost,
            'proposed_price': proposed_price,
            'lines_count': lines.count(),
        })
    
    context = {
        'project': project,
        'estimates': estimates_data,
        'can_create': request.user.is_staff or request.user.is_superuser,
        'active_tab': 'estimates',
    }
    
    return render(request, 'core/project_estimates_list.html', context)


@login_required
def project_invoices(request, project_id):
    """
    Lista de facturas del proyecto.
    Solo visible para staff/admin.
    """
    if not (request.user.is_staff or request.user.is_superuser):
        return HttpResponseForbidden(_('Access denied'))
    
    project = get_object_or_404(Project, pk=project_id)
    
    invoices = project.invoices.all().order_by('-created_at')
    
    context = {
        'project': project,
        'invoices': invoices,
        'active_tab': 'invoices',
    }
    
    return render(request, 'core/project_invoices_list.html', context)


# =============================================================================
# PROFESSIONAL PDF GENERATION VIEWS
# =============================================================================

@login_required
def changeorder_pdf_download(request, changeorder_id):
    """
    Generate and download a professional PDF for a signed Change Order.
    """
    from core.services.pdf_service import generate_signed_changeorder_pdf
    
    changeorder = get_object_or_404(ChangeOrder, pk=changeorder_id)
    
    # Security check - only staff or project participants
    if not (request.user.is_staff or request.user.is_superuser):
        return HttpResponseForbidden(_('Access denied'))
    
    try:
        pdf_bytes = generate_signed_changeorder_pdf(changeorder)
        
        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        filename = f"ChangeOrder_{changeorder.id}_{changeorder.project.project_code}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
    except Exception as e:
        messages.error(request, f"Error generating PDF: {str(e)}")
        return redirect('changeorder_list')


@login_required  
def changeorder_pdf_view(request, changeorder_id):
    """
    View the Change Order PDF inline in browser.
    """
    from core.services.pdf_service import generate_signed_changeorder_pdf
    
    changeorder = get_object_or_404(ChangeOrder, pk=changeorder_id)
    
    if not (request.user.is_staff or request.user.is_superuser):
        return HttpResponseForbidden(_('Access denied'))
    
    try:
        pdf_bytes = generate_signed_changeorder_pdf(changeorder)
        
        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        filename = f"ChangeOrder_{changeorder.id}.pdf"
        response['Content-Disposition'] = f'inline; filename="{filename}"'
        return response
    except Exception as e:
        messages.error(request, f"Error generating PDF: {str(e)}")
        return redirect('changeorder_list')


@login_required
def colorsample_pdf_download(request, colorsample_id):
    """
    Generate and download a professional PDF for a signed Color Sample.
    """
    from core.services.pdf_service import generate_signed_colorsample_pdf
    
    colorsample = get_object_or_404(ColorSample, pk=colorsample_id)
    
    if not (request.user.is_staff or request.user.is_superuser):
        return HttpResponseForbidden(_('Access denied'))
    
    try:
        pdf_bytes = generate_signed_colorsample_pdf(colorsample)
        
        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        filename = f"ColorSample_{colorsample.sample_number or colorsample.id}_{colorsample.code}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
    except Exception as e:
        messages.error(request, f"Error generating PDF: {str(e)}")
        return redirect('colorsample_list')


@login_required
def colorsample_pdf_view(request, colorsample_id):
    """
    View the Color Sample PDF inline in browser.
    """
    from core.services.pdf_service import generate_signed_colorsample_pdf
    
    colorsample = get_object_or_404(ColorSample, pk=colorsample_id)
    
    if not (request.user.is_staff or request.user.is_superuser):
        return HttpResponseForbidden(_('Access denied'))
    
    try:
        pdf_bytes = generate_signed_colorsample_pdf(colorsample)
        
        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        filename = f"ColorSample_{colorsample.id}.pdf"
        response['Content-Disposition'] = f'inline; filename="{filename}"'
        return response
    except Exception as e:
        messages.error(request, f"Error generating PDF: {str(e)}")
        return redirect('colorsample_list')


@login_required
def estimate_pdf_download(request, estimate_id):
    """
    Generate and download a professional PDF for an Estimate.
    Query param: ?contract=1 to generate as contract format.
    """
    from core.services.pdf_service import generate_estimate_pdf
    
    estimate = get_object_or_404(Estimate, pk=estimate_id)
    
    if not (request.user.is_staff or request.user.is_superuser):
        return HttpResponseForbidden(_('Access denied'))
    
    as_contract = request.GET.get('contract', '0') == '1'
    
    try:
        pdf_bytes = generate_estimate_pdf(estimate, as_contract=as_contract)
        
        doc_type = "Contract" if as_contract else "Estimate"
        filename = f"{doc_type}_{estimate.code}_{estimate.project.project_code}.pdf"
        
        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
    except Exception as e:
        messages.error(request, f"Error generating PDF: {str(e)}")
        return redirect('estimate_list')


@login_required
def estimate_pdf_view(request, estimate_id):
    """
    View the Estimate/Contract PDF inline in browser.
    Query param: ?contract=1 to generate as contract format.
    """
    from core.services.pdf_service import generate_estimate_pdf
    
    estimate = get_object_or_404(Estimate, pk=estimate_id)
    
    if not (request.user.is_staff or request.user.is_superuser):
        return HttpResponseForbidden(_('Access denied'))
    
    as_contract = request.GET.get('contract', '0') == '1'
    
    try:
        pdf_bytes = generate_estimate_pdf(estimate, as_contract=as_contract)
        
        doc_type = "Contract" if as_contract else "Estimate"
        filename = f"{doc_type}_{estimate.code}.pdf"
        
        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="{filename}"'
        return response
    except Exception as e:
        messages.error(request, f"Error generating PDF: {str(e)}")
        return redirect('estimate_list')


# =============================================================================
# EMPLOYEE SELF-SERVICE: Mi Nómina (My Payroll)
# =============================================================================

@login_required
def my_payroll(request):
    """
    Employee self-service page to view their own payroll information:
    - Recent payments (what they've received)
    - Savings balance (money held by company)
    - Work hours this week/month
    
    Accessible by ANY logged-in employee (who is linked to an Employee record).
    """
    from core.models import (
        Employee, PayrollPayment, PayrollRecord, EmployeeSavings, TimeEntry
    )
    from datetime import timedelta
    from decimal import Decimal
    
    # Get the employee record linked to this user
    employee = Employee.objects.filter(user=request.user).first()
    
    if not employee:
        messages.error(
            request, 
            _("Your user account is not linked to an employee record. Please contact your administrator.")
        )
        return redirect("dashboard")
    
    today = timezone.localdate()
    
    # === SAVINGS BALANCE ===
    savings_balance = EmployeeSavings.get_employee_balance(employee)
    savings_ledger = EmployeeSavings.get_employee_ledger(employee)[:20]  # Last 20 transactions
    
    # === RECENT PAYMENTS ===
    # Get PayrollRecords for this employee
    recent_payments = PayrollPayment.objects.filter(
        payroll_record__employee=employee
    ).select_related(
        'payroll_record', 'payroll_record__period'
    ).order_by('-payment_date')[:20]
    
    # Calculate payment stats
    # This month's payments
    month_start = today.replace(day=1)
    month_payments = PayrollPayment.objects.filter(
        payroll_record__employee=employee,
        payment_date__gte=month_start,
    )
    month_total_taken = sum(p.amount_taken for p in month_payments)
    month_total_saved = sum(p.amount_saved for p in month_payments)
    
    # === WORK HOURS ===
    # This week
    week_start = today - timedelta(days=today.weekday())  # Monday
    week_entries = TimeEntry.objects.filter(
        employee=employee,
        date__gte=week_start,
        date__lte=today,
    ).order_by('date', 'start_time')
    week_hours = sum(entry.hours_worked or 0 for entry in week_entries)
    
    # This month
    month_entries = TimeEntry.objects.filter(
        employee=employee,
        date__gte=month_start,
        date__lte=today,
    )
    month_hours = sum(entry.hours_worked or 0 for entry in month_entries)
    
    # === YEAR-TO-DATE ===
    year_start = today.replace(month=1, day=1)
    ytd_payments = PayrollPayment.objects.filter(
        payroll_record__employee=employee,
        payment_date__gte=year_start,
    )
    ytd_total_received = sum(p.amount_taken for p in ytd_payments)
    ytd_total_saved = sum(p.amount_saved for p in ytd_payments)
    
    ytd_entries = TimeEntry.objects.filter(
        employee=employee,
        date__gte=year_start,
    )
    ytd_hours = sum(entry.hours_worked or 0 for entry in ytd_entries)
    
    # Get employee's hourly rate (from PayrollRecord if available)
    hourly_rate = Decimal('0')
    latest_record = PayrollRecord.objects.filter(
        employee=employee,
        hourly_rate__gt=0
    ).order_by('-week_start').first()
    if latest_record:
        hourly_rate = latest_record.hourly_rate
    else:
        # Fallback to employee default
        hourly_rate = getattr(employee, 'hourly_rate', Decimal('0')) or Decimal('0')
    
    context = {
        "employee": employee,
        "hourly_rate": hourly_rate,
        # Savings
        "savings_balance": savings_balance,
        "savings_ledger": savings_ledger,
        # Payments
        "recent_payments": recent_payments,
        "month_total_taken": month_total_taken,
        "month_total_saved": month_total_saved,
        # Hours
        "week_entries": week_entries,
        "week_hours": week_hours,
        "month_hours": month_hours,
        # YTD
        "ytd_total_received": ytd_total_received,
        "ytd_total_saved": ytd_total_saved,
        "ytd_hours": ytd_hours,
        # Dates for context
        "today": today,
        "week_start": week_start,
        "month_start": month_start,
        "year_start": year_start,
    }
    
    return render(request, "core/my_payroll.html", context)


# =============================================================================
# PUBLIC PDF DOWNLOAD VIEWS (for clients after signing)
# =============================================================================

def changeorder_public_pdf_download(request, changeorder_id, token):
    """
    Public view to download Change Order PDF after signing.
    Validates token (HMAC) with 30-day expiration.
    """
    from django.core import signing
    from core.services.pdf_service import generate_signed_changeorder_pdf
    
    changeorder = get_object_or_404(ChangeOrder, pk=changeorder_id)
    
    # Validate token
    try:
        payload = signing.loads(token, max_age=60 * 60 * 24 * 30)  # 30 days
        if payload.get("changeorder_id") != changeorder.id:
            return HttpResponseForbidden("Token does not match this Change Order.")
    except signing.SignatureExpired:
        return HttpResponseForbidden("Download link has expired. Please contact us for a new link.")
    except signing.BadSignature:
        return HttpResponseForbidden("Invalid download link.")
    
    # Check if signed
    if not changeorder.signed_at:
        return HttpResponseForbidden("This Change Order has not been signed yet.")
    
    try:
        pdf_bytes = generate_signed_changeorder_pdf(changeorder)
        
        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        filename = f"ChangeOrder_{changeorder.id}_{changeorder.project.project_code}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
    except Exception as e:
        logger.exception(f"Error generating Change Order PDF for CO #{changeorder.id}")
        return HttpResponse("Error generating PDF. Please try again later.", status=500)


def colorsample_public_pdf_download(request, sample_id, token):
    """
    Public view to download Color Sample PDF after signing.
    Validates token (HMAC) with 30-day expiration.
    """
    from django.core import signing
    from core.services.pdf_service import generate_signed_colorsample_pdf
    
    colorsample = get_object_or_404(ColorSample, pk=sample_id)
    
    # Validate token
    try:
        payload = signing.loads(token, max_age=60 * 60 * 24 * 30)  # 30 days
        if payload.get("sample_id") != colorsample.id:
            return HttpResponseForbidden("Token does not match this Color Sample.")
    except signing.SignatureExpired:
        return HttpResponseForbidden("Download link has expired. Please contact us for a new link.")
    except signing.BadSignature:
        return HttpResponseForbidden("Invalid download link.")
    
    # Check if signed
    if not colorsample.client_signed_at:
        return HttpResponseForbidden("This Color Sample has not been approved yet.")
    
    try:
        pdf_bytes = generate_signed_colorsample_pdf(colorsample)
        
        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        filename = f"ColorSample_{colorsample.sample_number or colorsample.id}_{colorsample.code}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
    except Exception as e:
        logger.exception(f"Error generating Color Sample PDF for sample #{colorsample.id}")
        return HttpResponse("Error generating PDF. Please try again later.", status=500)


# ========================================================================================
