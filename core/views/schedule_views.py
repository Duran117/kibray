"""Schedule views — extracted from legacy_views.py in Phase 8."""
from core.views._helpers import *  # noqa: F401, F403
from core.views._helpers import (
    _check_user_project_access,
    _is_staffish,
    _require_admin_or_redirect,
    logger,
)
from django.utils.translation import gettext_lazy as _  # noqa: F811


@login_required
def schedule_create_view(request):
    profile = getattr(request.user, "profile", None)
    role = getattr(profile, "role", "employee")
    if role not in ["admin", "superuser", "project_manager"]:
        return redirect("dashboard")

    if request.method == "POST":
        form = ScheduleForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("dashboard")
    else:
        form = ScheduleForm()
    return render(request, "core/schedule_form.html", {"form": form})


@login_required


@login_required
def project_schedule_view(request, project_id: int):
    """
    Vista de cronograma del proyecto.
    Redirige a clientes a la vista hermosa y simplificada.
    PM/Admin ven la vista completa con todos los detalles.
    """
    project = get_object_or_404(Project, pk=project_id)
    
    # SECURITY: Check project access
    has_access, redirect_url = _check_user_project_access(request.user, project)
    if not has_access:
        messages.error(request, _("Access denied."))
        return redirect(redirect_url or "dashboard")
    
    profile = getattr(request.user, "profile", None)

    # Si es cliente, redirigir a la vista hermosa
    if profile and profile.role == "client":
        return redirect(reverse("client_project_calendar", kwargs={"project_id": project_id}))

    # Para PM/Admin: Vista completa
    if ScheduleForm:
        form = ScheduleForm(request.POST or None)
        if request.method == "POST" and _is_staffish(request.user) and form.is_valid():
            s = form.save(commit=False)
            s.project = project
            s.save()
            return redirect("project_schedule", project_id=project.id)
        elif request.method == "POST" and not _is_staffish(request.user):
            messages.error(request, _("Only staff can modify the schedule."))
            return redirect("project_schedule", project_id=project.id)
    else:
        form = None

    schedules = (
        Schedule.objects.filter(project=project).order_by("start_datetime") if Schedule else []
    )

    # También incluir ScheduleItems modernos
    schedule_items = project.schedule_items.select_related("category").order_by("planned_start")
    categories = project.schedule_categories.filter(parent__isnull=True).order_by("order")

    return render(
        request,
        "core/project_schedule.html",
        {
            "project": project,
            "form": form,
            "schedules": schedules,
            "schedule_items": schedule_items,
            "categories": categories,
        },
    )


@login_required


# ========================================
@login_required
def schedule_generator_view(request, project_id):
    """
    Vista del generador de cronograma jerárquico.
    - Lista categorías e ítems existentes
    - Permite generar automáticamente desde estimado aprobado
    - CRUD inline para categorías e ítems
    """
    project = get_object_or_404(Project, id=project_id)

    # SECURITY: Only staff or project managers can access schedule generator
    if not _is_staffish(request.user):
        messages.error(request, _("Access denied."))
        return redirect("dashboard")

    # Check permissions (staff or project manager)
    user_profile = getattr(request.user, "profile", None)
    can_manage = bool(
        request.user.is_staff
        or (user_profile and getattr(user_profile, "role", None) in ["project_manager"])
    )

    # Get approved estimate for generation
    approved_estimate = project.estimates.filter(approved=True).order_by("-version").first()

    # Handle POST actions
    if request.method == "POST":
        action = request.POST.get("action")

        # Generate from estimate
        if action == "generate_from_estimate" and approved_estimate and can_manage:
            return _generate_schedule_from_estimate(request, project, approved_estimate)

        # Create phase
        elif action == "create_category" and can_manage:
            form = SchedulePhaseForm(request.POST)
            if form.is_valid():
                phase = form.save(commit=False)
                phase.project = project
                phase.save()
                messages.success(request, f'Fase "{phase.name}" creada.')
                return redirect("schedule_generator", project_id=project.id)
            else:
                messages.error(request, "Error al crear fase.")

        # Create item
        elif action == "create_item" and can_manage:
            # Permitir crear fase al vuelo si viene 'new_category_name'
            new_cat_name = (request.POST.get("new_category_name") or "").strip()
            phase_id = request.POST.get("phase")

            # Validate: must have either existing phase OR new phase name
            if not phase_id and not new_cat_name:
                messages.error(
                    request,
                    "Debes seleccionar una fase existente o escribir el nombre de una nueva.",
                )
                return redirect("schedule_generator", project_id=project.id)

            if new_cat_name and not phase_id:
                phase = SchedulePhaseV2.objects.create(project=project, name=new_cat_name, order=0)
                phase_id = phase.id

            # Create item directly with V2
            name = request.POST.get("name") or request.POST.get("title")
            description = request.POST.get("description", "")
            start_date = request.POST.get("start_date") or request.POST.get("planned_start")
            end_date = request.POST.get("end_date") or request.POST.get("planned_end")
            
            if name and start_date and end_date and phase_id:
                phase = SchedulePhaseV2.objects.get(id=phase_id)
                item = ScheduleItemV2.objects.create(
                    project=project,
                    phase=phase,
                    name=name,
                    description=description,
                    start_date=start_date,
                    end_date=end_date,
                    status="planned",
                    progress=0,
                )
                messages.success(request, f'Ítem "{item.name}" creado.')
            else:
                messages.error(request, "Error al crear ítem. Verifica los campos.")
            return redirect("schedule_generator", project_id=project.id)

        # Update item progress
        elif action == "recalc_progress":
            item_id = request.POST.get("item_id")
            if item_id:
                item = get_object_or_404(ScheduleItemV2, id=item_id, project=project)
                # V2 uses calculated_progress property
                messages.success(
                    request,
                    _("Progreso recalculado: %(percent)s%%") % {"percent": item.calculated_progress},
                )
                return redirect("schedule_generator", project_id=project.id)

    # GET: render form and data
    phases = (
        SchedulePhaseV2.objects.filter(project=project)
        .prefetch_related("items")
        .order_by("order", "name")
    )
    orphan_items = ScheduleItemV2.objects.filter(project=project, phase__isnull=True).order_by(
        "order", "name"
    )

    context = {
        "project": project,
        "phases": phases,
        "categories": phases,  # Keep 'categories' for template compatibility
        "orphan_items": orphan_items,
        "approved_estimate": approved_estimate,
        "can_manage": can_manage,
    }

    return render(request, "core/schedule_generator.html", context)


def _generate_schedule_from_estimate(request, project, estimate):
    """
    Auto-genera fases e ítems V2 desde un estimado aprobado.
    Agrupa por cost_code.category y crea ScheduleItemV2 por cada EstimateLine.
    """
    try:
        with transaction.atomic():
            created_phases = {}
            created_items = 0

            # Get all estimate lines grouped by cost code category
            lines = estimate.lines.select_related("cost_code").order_by(
                "cost_code__category", "cost_code__code"
            )

            for line in lines:
                cc = line.cost_code
                phase_name = cc.category.capitalize() if cc.category else "General"

                # Get or create phase
                if phase_name not in created_phases:
                    phase, created = SchedulePhaseV2.objects.get_or_create(
                        project=project,
                        name=phase_name,
                        defaults={"order": len(created_phases)},
                    )
                    created_phases[phase_name] = phase
                else:
                    phase = created_phases[phase_name]

                # Create schedule item from estimate line
                item_name = f"{cc.code} - {line.description or cc.name}"

                # Check if already exists
                existing = ScheduleItemV2.objects.filter(
                    project=project, phase=phase, name=item_name
                ).first()

                if not existing:
                    # Default dates from project
                    start_date = project.start_date or timezone.now().date()
                    end_date = project.end_date or (start_date + timedelta(days=30))
                    
                    ScheduleItemV2.objects.create(
                        project=project,
                        phase=phase,
                        name=item_name,
                        description=line.description or "",
                        order=created_items,
                        cost_code=cc,
                        status="planned",
                        progress=0,
                        start_date=start_date,
                        end_date=end_date,
                    )
                    created_items += 1

            messages.success(
                request,
                f"Generado: {len(created_phases)} fases y {created_items} ítems desde el estimado {estimate.code}.",
            )
    except Exception as e:
        messages.error(request, _("Error al generar cronograma: %(error)s") % {"error": str(e)})

    return redirect("schedule_generator", project_id=project.id)


@login_required
def schedule_category_edit(request, category_id):
    """Edit schedule phase (V2)."""
    phase = get_object_or_404(SchedulePhaseV2, id=category_id)
    project = phase.project

    if not (request.user.is_staff or request.user == project.client):
        return HttpResponseForbidden()

    if request.method == "POST":
        form = SchedulePhaseForm(request.POST, instance=phase)
        if form.is_valid():
            form.save()
            messages.success(request, f'Fase "{phase.name}" actualizada.')
            return redirect("schedule_generator", project_id=project.id)
    else:
        form = SchedulePhaseForm(instance=phase)

    return render(
        request,
        "core/schedule_category_form.html",
        {
            "form": form,
            "category": phase,
            "project": project,
        },
    )


@login_required
def schedule_category_delete(request, category_id):
    """Delete schedule phase (V2)."""
    phase = get_object_or_404(SchedulePhaseV2, id=category_id)
    project = phase.project

    if not (request.user.is_staff or request.user == project.client):
        return HttpResponseForbidden()

    if request.method == "POST":
        phase_name = phase.name
        phase.delete()
        messages.success(request, f'Fase "{phase_name}" eliminada.')
        return redirect("schedule_generator", project_id=project.id)

    return render(
        request,
        "core/schedule_category_confirm_delete.html",
        {
            "category": category,
            "project": project,
        },
    )


@login_required
def schedule_item_edit(request, item_id):
    """Edit schedule item."""
    item = get_object_or_404(ScheduleItem, id=item_id)
    project = item.project

    if not (request.user.is_staff or request.user == project.client):
        return HttpResponseForbidden()

    if request.method == "POST":
        form = ScheduleItemForm(request.POST, instance=item, project=project)
        if form.is_valid():
            form.save()
            messages.success(request, f'Ítem "{item.title}" actualizado.')
            return redirect("schedule_generator", project_id=project.id)
    else:
        form = ScheduleItemForm(instance=item, project=project)

    return render(
        request,
        "core/schedule_item_form.html",
        {
            "form": form,
            "item": item,
            "project": project,
        },
    )


@login_required
def schedule_item_delete(request, item_id):
    """Delete schedule item."""
    item = get_object_or_404(ScheduleItem, id=item_id)
    project = item.project

    if not (request.user.is_staff or request.user == project.client):
        return HttpResponseForbidden()

    if request.method == "POST":
        item_title = item.title
        item.delete()
        messages.success(request, f'Ítem "{item_title}" eliminado.')
        return redirect("schedule_generator", project_id=project.id)

    return render(
        request,
        "core/schedule_item_confirm_delete.html",
        {
            "item": item,
            "project": project,
        },
    )


@login_required
def project_schedule_ics(request, project_id):
    """
    Export project schedule as ICS (iCalendar) file.
    Compatible with Google Calendar, Outlook, Apple Calendar, etc.
    """
    from core.services.calendar_sync import generate_ical_for_project

    project = get_object_or_404(Project, id=project_id)

    # Generate iCal content
    ical_data = generate_ical_for_project(project)

    # Return as downloadable file
    response = HttpResponse(ical_data, content_type="text/calendar; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="{project.name}_schedule.ics"'
    return response


@login_required
def project_schedule_google_calendar(request, project_id):
    """
    Generate instructions and links for adding schedule to Google Calendar.
    """
    from core.services.calendar_sync import create_calendar_subscription_url

    project = get_object_or_404(Project, id=project_id)
    subscription_url = create_calendar_subscription_url(project, request)

    context = {
        "project": project,
        "subscription_url": subscription_url,
        "ics_url": reverse("project_schedule_ics", kwargs={"project_id": project.id}),
    }

    return render(request, "core/schedule_google_calendar.html", context)


@login_required
def schedule_gantt_react_view(request, project_id):
    """
    Render the React-based Gantt chart for project schedule.
    Uses the new unified KibrayGantt React component.
    """
    project = get_object_or_404(Project, id=project_id)

    # Check permissions (staff or project manager)
    user_profile = getattr(request.user, "profile", None)
    can_manage = bool(
        request.user.is_staff
        or (user_profile and getattr(user_profile, "role", None) in ["project_manager", "admin", "superuser"])
    )

    if not can_manage:
        return HttpResponseForbidden("No tienes permisos para ver este cronograma.")

    # Get team members for task assignment (only actual employees, not clients)
    team_members = Employee.objects.filter(
        is_active=True
    ).order_by('first_name', 'last_name')

    context = {
        "project": project,
        "can_edit": can_manage,
        "team_members": team_members,
        "disable_notification_center": True,  # Avoid React conflicts with Gantt bundle
    }

    return render(request, "schedule_gantt_react.html", context)

