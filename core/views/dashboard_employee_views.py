"""Employee dashboard views — daily worker dashboard."""
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





@login_required
def dashboard_employee(request):
    """Dashboard simple para empleados: qué hacer hoy, clock in/out, materiales"""
    # legacy flag kept for compatibility; value is handled by router/templates
    _is_legacy = request.GET.get("legacy", "false").lower() == "true"
    # Obtener empleado ligado al usuario
    employee = Employee.objects.filter(user=request.user).first()
    if not employee:
        messages.error(request, _("Tu usuario no está vinculado a un empleado."))
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
