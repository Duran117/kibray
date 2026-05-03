"""Chat & comment views — channels, messages."""
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


# =============================
# Project Chat (Premium)
# =============================


def _ensure_default_channels(project, user):
    group, __ = ChatChannel.objects.get_or_create(
        project=project,
        name="Group",
        defaults={"channel_type": "group", "is_default": True, "created_by": user},
    )
    direct, __ = ChatChannel.objects.get_or_create(
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
            messages.error(request, _("No tienes acceso a este canal."))
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
                messages.error(request, _("El nombre del canal es requerido."))
        
        elif action == "invite":
            username = (request.POST.get("username") or "").strip()
            from django.contrib.auth.models import User as DjangoUser
            try:
                u = DjangoUser.objects.get(username=username)
                channel.participants.add(u)
                messages.success(request, _("%(username)s invitado al canal.") % {"username": username})
            except DjangoUser.DoesNotExist:
                messages.error(request, _("Usuario no encontrado."))
            return redirect("project_chat_premium_channel", project_id=project.id, channel_id=channel.id)
        
        elif action == "delete_channel":
            if channel.is_default:
                messages.error(request, _("No puedes eliminar el canal por defecto."))
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
            messages.error(request, _("No tienes acceso a este proyecto."))
            return redirect("dashboard_client")
    elif not request.user.is_staff and not has_access:
        messages.error(request, _("Acceso denegado."))
        return redirect("dashboard")

    if request.method == "POST":
        text = request.POST.get("text", "").strip()
        image = request.FILES.get("image")

        if not text and not image:
            messages.error(request, _("Debes agregar texto o imagen."))
            return redirect("client_project_view", project_id=project_id)

        Comment.objects.create(
            project=project, user=request.user, text=text or "Imagen adjunta", image=image
        )

        messages.success(request, _("Comentario agregado exitosamente."))
        return redirect("client_project_view", project_id=project_id)

    return render(request, "core/agregar_comentario.html", {"project": project})


