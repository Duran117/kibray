"""Client & organization management views — extracted from legacy_views.py in Phase 8."""
from core.views._helpers import *  # noqa: F401, F403
from core.views._helpers import (
    _check_user_project_access,
    _is_admin_user,
    _require_admin_or_redirect,
    logger,
)
from django.utils.translation import gettext_lazy as _  # noqa: F811



# ========================================
# GESTIÓN DE CLIENTES
# ========================================


@login_required
@staff_member_required
def client_list(request):
    """Lista de todos los clientes con búsqueda y filtros"""
    from core.models import ClientProjectAccess

    # Solo usuarios con perfil de cliente
    clients = (
        User.objects.filter(profile__role="client")
        .select_related("profile")
        .order_by("-date_joined")
    )

    # Búsqueda
    search_query = request.GET.get("search", "").strip()
    if search_query:
        clients = clients.filter(
            Q(first_name__icontains=search_query)
            | Q(last_name__icontains=search_query)
            | Q(email__icontains=search_query)
            | Q(username__icontains=search_query)
        )

    # Filtro por estado
    status_filter = request.GET.get("status", "")
    if status_filter == "active":
        clients = clients.filter(is_active=True)
    elif status_filter == "inactive":
        clients = clients.filter(is_active=False)

    # Agregar conteo de proyectos asignados
    clients_data = []
    for client in clients:
        project_count = ClientProjectAccess.objects.filter(user=client).count()
        clients_data.append({"user": client, "project_count": project_count})

    # Paginación
    paginator = Paginator(clients_data, 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "search_query": search_query,
        "status_filter": status_filter,
        "total_clients": clients.count(),
    }

    return render(request, "core/client_list.html", context)


@login_required
@staff_member_required
def client_create(request):
    """Crear nuevo cliente"""
    from core.forms import ClientCreationForm
    from core.services.email_service import KibrayEmailService

    if request.method == "POST":
        form = ClientCreationForm(request.POST)
        if form.is_valid():
            user = form.save()

            # Enviar email de bienvenida si está marcado
            if form.cleaned_data.get("send_welcome_email"):
                temp_password = form.temp_password
                try:
                    email_sent = KibrayEmailService.send_welcome_credentials(
                        to_email=user.email,
                        first_name=user.first_name,
                        email=user.email,
                        temp_password=temp_password,
                        login_url=request.build_absolute_uri('/login/'),
                        sender_name="Kibray Painting Team",
                        fail_silently=False
                    )
                    if email_sent:
                        messages.success(
                            request,
                            f"Cliente creado exitosamente. Se ha enviado un email con las credenciales de acceso a {user.email}",
                        )
                    else:
                        messages.warning(
                            request,
                            f"Cliente creado pero hubo un error al enviar el email. Contacta al cliente directamente.",
                        )
                except Exception as e:
                    messages.warning(
                        request,
                        f"Cliente creado pero hubo un error al enviar el email: {str(e)}. Contacta al cliente directamente para proporcionarle acceso.",
                    )
            else:
                # No mostrar contraseña en UI - solo indicar que se creó
                messages.success(
                    request,
                    _("Cliente creado exitosamente. Recuerda proporcionarle sus credenciales de acceso de forma segura."),
                )

            return redirect("client_detail", user_id=user.id)
    else:
        form = ClientCreationForm()

    return render(request, "core/client_form.html", {"form": form, "is_create": True})


@login_required
@staff_member_required
def client_detail(request, user_id):
    """Detalle de un cliente con sus proyectos asignados"""
    from core.models import ClientProjectAccess, ClientContact

    client = get_object_or_404(User, id=user_id)

    # Verificar que es un cliente
    if not hasattr(client, "profile") or client.profile.role != "client":
        messages.error(request, _("Este usuario no es un cliente."))
        return redirect("client_list")

    # Obtener ClientContact si existe (cliente corporativo)
    client_contact = ClientContact.objects.filter(user=client).select_related("organization").first()
    
    # Obtener proyectos asignados
    project_accesses = ClientProjectAccess.objects.filter(user=client).select_related("project")
    
    # Si tiene organización, obtener también proyectos de la organización
    organization_projects = []
    if client_contact and client_contact.organization:
        from core.models import Project
        organization_projects = Project.objects.filter(
            billing_organization=client_contact.organization
        ).exclude(
            id__in=project_accesses.values_list("project_id", flat=True)
        ).order_by("-created_at")[:10]

    # Actividad reciente
    recent_comments = (
        Comment.objects.filter(user=client)
        .select_related("task", "task__project")
        .order_by("-created_at")[:5]
    )

    # Tasks: Los clientes no son empleados, así que no pueden tener tasks asignadas directamente
    # Solo mostraremos las tasks que crearon o comentaron
    recent_tasks = []

    from core.models import ClientRequest

    recent_requests = (
        ClientRequest.objects.filter(created_by=client)
        .select_related("project")
        .order_by("-created_at")[:5]
    )

    context = {
        "client": client,
        "client_contact": client_contact,
        "organization": client_contact.organization if client_contact else None,
        "project_accesses": project_accesses,
        "organization_projects": organization_projects,
        "recent_comments": recent_comments,
        "recent_tasks": recent_tasks,
        "recent_requests": recent_requests,
    }

    return render(request, "core/client_detail.html", context)


@login_required
@staff_member_required
def client_edit(request, user_id):
    """Editar información de un cliente"""
    from core.forms import ClientEditForm

    client = get_object_or_404(User, id=user_id)

    # Verificar que es un cliente
    if not hasattr(client, "profile") or client.profile.role != "client":
        messages.error(request, _("Este usuario no es un cliente."))
        return redirect("client_list")

    if request.method == "POST":
        form = ClientEditForm(request.POST, instance=client)
        if form.is_valid():
            user = form.save()

            # Actualizar perfil
            if hasattr(user, "profile"):
                user.profile.language = form.cleaned_data.get("language", "en")
                user.profile.save()

            messages.success(request, _("Información del cliente actualizada exitosamente."))
            return redirect("client_detail", user_id=user.id)
    else:
        form = ClientEditForm(instance=client)

    return render(
        request, "core/client_form.html", {"form": form, "client": client, "is_create": False}
    )


@login_required
@staff_member_required
def client_delete(request, user_id):
    """Desactivar o eliminar un cliente (con confirmación)"""
    client = get_object_or_404(User, id=user_id)

    # Verificar que es un cliente
    if not hasattr(client, "profile") or client.profile.role != "client":
        messages.error(request, _("Este usuario no es un cliente."))
        return redirect("client_list")

    if request.method == "POST":
        action = request.POST.get("action", "deactivate")

        # SECURITY: Logging de auditoría para operaciones críticas

        audit_logger = logging.getLogger("django")
        audit_logger.warning(
            f"CLIENT_DELETE_ATTEMPT | Actor: {request.user.username} (ID:{request.user.id}) | "
            f"Target: {client.username} (ID:{client.id}) | Action: {action} | "
            f"IP: {request.META.get('REMOTE_ADDR')}"
        )

        if action == "deactivate":
            client.is_active = False
            client.save()
            messages.success(
                request,
                _("Cliente %(name)s desactivado exitosamente.") % {"name": client.get_full_name()},
            )
        elif action == "delete":
            # SECURITY: Verificar dependencias críticas antes de CASCADE delete
            from core.models import ClientProjectAccess, ClientRequest

            project_count = ClientProjectAccess.objects.filter(user=client).count()
            request_count = ClientRequest.objects.filter(created_by=client).count()
            comment_count = Comment.objects.filter(user=client).count()
            # Los clientes no son empleados, no pueden tener tareas asignadas
            task_count = 0

            if any([project_count, request_count, comment_count, task_count]):
                messages.error(
                    request,
                    f"❌ No se puede eliminar este cliente porque tiene datos asociados: "
                    f"{project_count} proyectos asignados, {request_count} solicitudes, "
                    f"{comment_count} comentarios. "
                    f'Usa "Desactivar" para preservar la integridad de los datos.',
                )
                return redirect("client_detail", user_id=client.id)

            client_name = client.get_full_name()
            client.delete()
            messages.success(
                request, _("Cliente %(name)s eliminado permanentemente.") % {"name": client_name}
            )
            return redirect("client_list")

        return redirect("client_detail", user_id=client.id)

    # GET: Mostrar estadísticas para confirmar
    from core.models import ClientProjectAccess, ClientRequest

    context = {
        "client": client,
        "project_count": ClientProjectAccess.objects.filter(user=client).count(),
        "request_count": ClientRequest.objects.filter(created_by=client).count(),
        "comment_count": Comment.objects.filter(user=client).count(),
        # Los clientes no tienen tareas asignadas (solo empleados)
        "task_count": 0,
    }

    return render(request, "core/client_delete_confirm.html", context)


@login_required
@staff_member_required
def client_reset_password(request, user_id):
    """Resetear contraseña de un cliente"""
    from core.forms import ClientPasswordResetForm
    from core.services.email_service import KibrayEmailService

    client = get_object_or_404(User, id=user_id)

    if not hasattr(client, "profile") or client.profile.role != "client":
        messages.error(request, _("Este usuario no es un cliente."))
        return redirect("client_list")

    if request.method == "POST":
        form = ClientPasswordResetForm(request.POST)
        if form.is_valid():
            new_password = form.cleaned_data["new_password"]
            client.set_password(new_password)
            client.save()

            # Enviar email notificando el cambio
            try:
                email_sent = KibrayEmailService.send_password_reset(
                    to_email=client.email,
                    email=client.email,
                    new_password=new_password,
                    login_url=request.build_absolute_uri('/login/'),
                    fail_silently=False
                )
                if email_sent:
                    messages.success(
                        request,
                        _("Contraseña actualizada y email enviado a %(email)s")
                        % {"email": client.email},
                    )
                else:
                    messages.warning(
                        request,
                        _("Contraseña actualizada pero hubo un error al enviar el email.")
                    )
            except Exception as e:
                messages.warning(
                    request,
                    _("Contraseña actualizada pero hubo un error al enviar el email: %(error)s")
                    % {"error": str(e)},
                )

            return redirect("client_detail", user_id=client.id)
    else:
        form = ClientPasswordResetForm()

    return render(request, "core/client_password_reset.html", {"form": form, "client": client})


@login_required
@staff_member_required
def client_assign_project(request, user_id):
    """Asignar o remover proyectos de un cliente"""
    from core.models import ClientProjectAccess

    client = get_object_or_404(User, id=user_id)

    if not hasattr(client, "profile") or client.profile.role != "client":
        messages.error(request, _("Este usuario no es un cliente."))
        return redirect("client_list")

    if request.method == "POST":
        project_id = request.POST.get("project_id")
        action = request.POST.get("action", "add")
        access_role = request.POST.get("access_role", "client")  # Get role from form

        if not project_id:
            messages.error(request, _("Proyecto no especificado."))
            return redirect("client_detail", user_id=client.id)

        project = get_object_or_404(Project, id=project_id)

        if action == "add":
            # Validate role
            valid_roles = [r[0] for r in ClientProjectAccess.ROLE_CHOICES]
            if access_role not in valid_roles:
                access_role = "client"
            
            access, created = ClientProjectAccess.objects.get_or_create(
                user=client,
                project=project,
                defaults={"role": access_role, "can_comment": True, "can_create_tasks": True},
            )
            if created:
                role_display = dict(ClientProjectAccess.ROLE_CHOICES).get(access_role, access_role)
                messages.success(
                    request, f'Cliente asignado al proyecto "{project.name}" como {role_display}.'
                )
            else:
                messages.info(request, f'El cliente ya tiene acceso al proyecto "{project.name}".')

        elif action == "remove":
            deleted_count, __ = ClientProjectAccess.objects.filter(
                user=client, project=project
            ).delete()
            if deleted_count > 0:
                messages.success(request, f'Acceso al proyecto "{project.name}" removido.')
            else:
                messages.info(request, _("El cliente no tenía acceso a ese proyecto."))
        
        elif action == "update_role":
            # Update existing access role
            access_role = request.POST.get("new_role", "client")
            valid_roles = [r[0] for r in ClientProjectAccess.ROLE_CHOICES]
            if access_role in valid_roles:
                updated = ClientProjectAccess.objects.filter(
                    user=client, project=project
                ).update(role=access_role)
                if updated:
                    role_display = dict(ClientProjectAccess.ROLE_CHOICES).get(access_role, access_role)
                    messages.success(request, f'Rol actualizado a {role_display} para "{project.name}".')

        return redirect("client_detail", user_id=client.id)

    # GET: Mostrar formulario con proyectos disponibles
    from core.models import ClientProjectAccess

    assigned_projects = ClientProjectAccess.objects.filter(user=client).values_list(
        "project_id", flat=True
    )
    available_projects = Project.objects.exclude(id__in=assigned_projects).order_by("name")

    context = {
        "client": client,
        "available_projects": available_projects,
        "role_choices": ClientProjectAccess.ROLE_CHOICES,  # Pass role choices to template
    }

    return render(request, "core/client_assign_project.html", context)


@login_required
@staff_member_required
def project_add_owner(request, project_id):
    """Agregar rápidamente un dueño/cliente a un proyecto.
    
    Crea automáticamente el usuario si no existe y le asigna acceso al proyecto.
    Opcionalmente envía las credenciales por email.
    """
    from core.forms import QuickAddProjectOwnerForm
    from core.models import ClientProjectAccess
    from core.services.email_service import KibrayEmailService
    
    project = get_object_or_404(Project, id=project_id)
    
    if request.method == "POST":
        form = QuickAddProjectOwnerForm(request.POST)
        if form.is_valid():
            user, temp_password, is_new_user = form.save(project=project, created_by=request.user)
            
            # Enviar email con credenciales si es nuevo usuario y se solicitó
            send_credentials = form.cleaned_data.get("send_credentials", True)
            if is_new_user and temp_password and send_credentials:
                try:
                    email_sent = KibrayEmailService.send_welcome_credentials(
                        to_email=user.email,
                        first_name=user.first_name,
                        email=user.email,
                        temp_password=temp_password,
                        login_url=request.build_absolute_uri('/login/'),
                        project_name=project.name,
                        sender_name=request.user.get_full_name() or request.user.username,
                        fail_silently=False
                    )
                    if email_sent:
                        messages.success(
                            request, 
                            f'Usuario "{user.get_full_name()}" creado y asignado al proyecto. '
                            f'Se enviaron las credenciales a {user.email}.'
                        )
                    else:
                        messages.warning(
                            request,
                            f'Usuario creado pero hubo un error al enviar el email. '
                            f'Contraseña temporal: {temp_password}'
                        )
                except Exception as e:
                    messages.warning(
                        request,
                        f'Usuario creado pero hubo un error al enviar el email: {e}. '
                        f'Contraseña temporal: {temp_password}'
                    )
            elif is_new_user:
                messages.success(
                    request, 
                    f'Usuario "{user.get_full_name()}" creado y asignado al proyecto. '
                    f'Contraseña temporal: {temp_password}'
                )
            else:
                access_role = form.cleaned_data.get("access_role", "client")
                role_display = dict(ClientProjectAccess.ROLE_CHOICES).get(access_role, access_role)
                messages.success(
                    request, 
                    f'Usuario existente "{user.get_full_name()}" asignado al proyecto como {role_display}.'
                )
            
            # Si es AJAX (modal), retornar JSON
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                from django.http import JsonResponse
                return JsonResponse({
                    'success': True,
                    'user_id': user.id,
                    'user_name': user.get_full_name(),
                    'is_new': is_new_user,
                })
            
            return redirect("project_overview", project_id=project.id)
        else:
            # Errores de formulario
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                from django.http import JsonResponse
                return JsonResponse({
                    'success': False,
                    'errors': form.errors,
                }, status=400)
    else:
        form = QuickAddProjectOwnerForm()
    
    # Obtener clientes/owners actuales del proyecto
    current_accesses = ClientProjectAccess.objects.filter(
        project=project
    ).select_related("user").order_by("-granted_at")
    
    context = {
        "project": project,
        "form": form,
        "current_accesses": current_accesses,
    }
    
    return render(request, "core/project_add_owner.html", context)


# ========================================
# GESTIÓN DE ORGANIZACIONES DE CLIENTES
# ========================================


@login_required
@staff_member_required
def organization_list(request):
    """Lista de todas las organizaciones de clientes"""
    from core.models import ClientOrganization

    organizations = ClientOrganization.objects.all().order_by("name")

    # Búsqueda
    search_query = request.GET.get("search", "").strip()
    if search_query:
        organizations = organizations.filter(
            Q(name__icontains=search_query)
            | Q(legal_name__icontains=search_query)
            | Q(billing_email__icontains=search_query)
            | Q(tax_id__icontains=search_query)
        )

    # Filtro por estado
    status_filter = request.GET.get("status", "")
    if status_filter == "active":
        organizations = organizations.filter(is_active=True)
    elif status_filter == "inactive":
        organizations = organizations.filter(is_active=False)

    # Paginación
    paginator = Paginator(organizations, 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "search_query": search_query,
        "status_filter": status_filter,
        "total_organizations": ClientOrganization.objects.count(),
    }

    return render(request, "core/organization_list.html", context)


@login_required
@staff_member_required
def organization_create(request):
    """Crear nueva organización de cliente"""
    from core.forms import ClientOrganizationForm

    if request.method == "POST":
        form = ClientOrganizationForm(request.POST)
        if form.is_valid():
            org = form.save(commit=False)
            org.created_by = request.user
            org.save()
            messages.success(request, f'Organización "{org.name}" creada exitosamente.')
            return redirect("organization_detail", org_id=org.id)
    else:
        form = ClientOrganizationForm()

    return render(request, "core/organization_form.html", {"form": form, "is_create": True})


@login_required
@staff_member_required
def organization_detail(request, org_id):
    """Detalle de una organización con sus contactos y proyectos"""
    from core.models import ClientOrganization, ClientContact

    org = get_object_or_404(ClientOrganization, id=org_id)

    # Contactos de esta organización
    contacts = ClientContact.objects.filter(organization=org).select_related("user")

    # Proyectos vinculados a esta organización
    projects = Project.objects.filter(billing_organization=org).order_by("-created_at")

    context = {
        "organization": org,
        "contacts": contacts,
        "projects": projects,
    }

    return render(request, "core/organization_detail.html", context)


@login_required
@staff_member_required
def organization_edit(request, org_id):
    """Editar organización existente"""
    from core.models import ClientOrganization
    from core.forms import ClientOrganizationForm

    org = get_object_or_404(ClientOrganization, id=org_id)

    if request.method == "POST":
        form = ClientOrganizationForm(request.POST, instance=org)
        if form.is_valid():
            form.save()
            messages.success(request, f'Organización "{org.name}" actualizada exitosamente.')
            return redirect("organization_detail", org_id=org.id)
    else:
        form = ClientOrganizationForm(instance=org)

    return render(
        request, "core/organization_form.html", {"form": form, "organization": org, "is_create": False}
    )


@login_required
@staff_member_required
def organization_delete(request, org_id):
    """Desactivar o eliminar una organización"""
    from core.models import ClientOrganization, ClientContact

    org = get_object_or_404(ClientOrganization, id=org_id)

    if request.method == "POST":
        action = request.POST.get("action", "deactivate")

        # Logging de auditoría
        audit_logger = logging.getLogger("django")
        audit_logger.warning(
            f"ORGANIZATION_DELETE_ATTEMPT | Actor: {request.user.username} (ID:{request.user.id}) | "
            f"Target: {org.name} (ID:{org.id}) | Action: {action} | "
            f"IP: {request.META.get('REMOTE_ADDR')}"
        )

        if action == "deactivate":
            org.is_active = False
            org.save()
            messages.success(request, f'Organización "{org.name}" desactivada exitosamente.')
        elif action == "delete":
            # Verificar dependencias
            contact_count = ClientContact.objects.filter(organization=org).count()
            project_count = Project.objects.filter(billing_organization=org).count()

            if contact_count > 0 or project_count > 0:
                messages.error(
                    request,
                    f"❌ No se puede eliminar esta organización porque tiene: "
                    f"{contact_count} contactos y {project_count} proyectos vinculados. "
                    f'Usa "Desactivar" para preservar la integridad de los datos.',
                )
                return redirect("organization_detail", org_id=org.id)

            org_name = org.name
            org.delete()
            messages.success(request, f'Organización "{org_name}" eliminada permanentemente.')
            return redirect("organization_list")

        return redirect("organization_detail", org_id=org.id)

    # GET: Mostrar estadísticas para confirmar
    context = {
        "organization": org,
        "contact_count": ClientContact.objects.filter(organization=org).count(),
        "project_count": Project.objects.filter(billing_organization=org).count(),
    }

    return render(request, "core/organization_delete_confirm.html", context)


# ========================================
# GESTIÓN DE PROYECTOS
# ========================================


