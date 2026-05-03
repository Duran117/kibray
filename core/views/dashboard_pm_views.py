"""PM (Project Manager) dashboard views."""
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





# --- DASHBOARD PM ---
@login_required
def dashboard_pm(request):
    """Dashboard operacional para PM: materiales, planning, issues, tiempo sin CO"""
    # SECURITY: Only PMs, admins, and superusers can access
    profile = getattr(request.user, "profile", None)
    role = getattr(profile, "role", None) if profile else None
    if not (request.user.is_superuser or role in ("admin", "project_manager") or request.user.is_staff):
        messages.error(request, _("Acceso solo para PM/Staff."))
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
