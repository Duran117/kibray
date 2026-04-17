"""Meeting minutes views — CRUD, comments."""
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


