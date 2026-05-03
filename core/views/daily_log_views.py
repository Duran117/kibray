"""Daily log views — CRUD."""
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
        messages.error(request, _("No tienes permiso para ver Daily Logs"))
        return redirect("dashboard_employee")

    # Clientes: verificar acceso al proyecto Y que esté publicado
    if role == "client":
        has_access, redirect_url = _check_user_project_access(request.user, log.project)
        if not has_access:
            messages.error(request, _("You don't have access to this project."))
            return redirect("dashboard_client")
        if not log.is_published:
            messages.error(request, _("Este Daily Log no está disponible"))
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
        messages.error(request, _("You don't have permission to delete Daily Logs"))
        return redirect("daily_log_detail", log_id=log.id)

    if request.method == "POST":
        project_id = log.project_id
        log.delete()
        messages.success(request, _("Daily Log deleted successfully"))
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
        messages.error(request, _("Only PM can create Daily Logs"))
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


