from django.conf import settings


def legacy_shell(request):
    """Expose a global `legacy_shell` flag to templates.

    This is used as a transitional mechanism: when `?legacy=true` is present,
    pages can render without the modern sidebar (`kb-sidebar`) while we
    incrementally migrate/retire legacy shells.
    """

    return {"legacy_shell": bool(request.GET.get("legacy"))}


def company(request):
    """Injects company branding info into all templates."""
    return {
        "company": {
            "name": "Kibray Paint & Stain LLC",
            "address_line1": "P.O. Box 25881",
            "city_state_zip": "Silverthorne, CO 80497",
            "phone": "(970) 333-4872",
            "email": "jduran@kibraypainting.net",
            "website": "kibraypainting.net",
            "logo_path": "brand/logo.svg",
        }
    }


def onesignal_config(request):
    """Injects OneSignal configuration into templates."""
    return {
        "ONESIGNAL_APP_ID": getattr(settings, "ONESIGNAL_APP_ID", ""),
        "ONESIGNAL_SAFARI_WEB_ID": getattr(settings, "ONESIGNAL_SAFARI_WEB_ID", ""),
    }


def notification_badges(request):
    """Provides notification counts for navigation badges."""
    from django.db.models import Q
    
    badges = {
        "unassigned_time_count": 0,
        "pending_materials_count": 0,
        "open_issues_count": 0,
        "pending_approvals_count": 0,
        "new_client_tasks_count": 0,
        "completed_tasks_client_count": 0,
        "color_samples_review_count": 0,
        "unread_notifications_count": 0,
    }

    if not request.user.is_authenticated:
        return {"badges": badges}

    try:
        from core.models import (
            ChangeOrder,
            ColorSample,
            Issue,
            MaterialRequest,
            Notification,
            Task,
            TimeEntry,
        )

        user = request.user
        
        # Notificaciones no leídas (con filtro de seguridad para clientes)
        notification_qs = Notification.objects.filter(user=user, is_read=False)
        
        # For clients, only count notifications for their assigned projects
        if hasattr(user, 'profile') and user.profile.role == 'client':
            client_project_ids = list(user.assigned_projects.values_list('id', flat=True))
            notification_qs = notification_qs.filter(
                Q(project_id__in=client_project_ids) | Q(project__isnull=True)
            )
        
        badges["unread_notifications_count"] = notification_qs.count()

        # Unassigned time entries (no project assigned)
        badges["unassigned_time_count"] = TimeEntry.objects.filter(project__isnull=True).count()

        # Pending material requests
        badges["pending_materials_count"] = MaterialRequest.objects.filter(status="pending").count()

        # Open issues
        badges["open_issues_count"] = Issue.objects.filter(
            status__in=["open", "in_progress"]
        ).count()

        # Pending change order approvals (if user is admin/staff)
        if user.is_staff:
            badges["pending_approvals_count"] = ChangeOrder.objects.filter(
                approval_status="pending"
            ).count()
            # Nuevas tareas creadas por clientes en estado Pendiente
            badges["new_client_tasks_count"] = Task.objects.filter(
                status="Pending", created_by__profile__role="client"
            ).count()
            # Muestras de color en revisión para aprobación
            badges["color_samples_review_count"] = ColorSample.objects.filter(
                status__in=["proposed", "review"]
            ).count()
        else:
            # Para usuarios cliente: tareas completadas recientemente (últimos 3 días)
            if hasattr(user, "profile") and user.profile.role == "client":
                from django.utils import timezone

                recent_cutoff = timezone.now() - timezone.timedelta(days=3)
                badges["completed_tasks_client_count"] = Task.objects.filter(
                    project__client=request.user.username,
                    status="Completed",
                    completed_at__gte=recent_cutoff,
                ).count()
    except Exception:
        # If models don't exist or error occurs, silently ignore
        pass

    return {"badges": badges}


def recent_projects(request):
    """Provides recent projects filtered by user role for sidebar navigation.
    
    - Clients: Only see projects they have access to
    - Staff/Admin/PM: See all recent projects
    """
    if not request.user.is_authenticated:
        return {"recent_projects": []}

    try:
        from core.models import Project

        profile = getattr(request.user, "profile", None)
        
        # If user is a client, only show their projects
        if profile and profile.role == "client":
            # Get projects via ClientProjectAccess
            access_projects = Project.objects.filter(client_accesses__user=request.user)
            # Get projects via legacy client field
            legacy_projects = Project.objects.filter(client=request.user.username)
            # Combine both querysets and get recent ones
            projects = list(access_projects.union(legacy_projects).order_by("-start_date")[:5])
        else:
            # Staff, admin, PM - show recent active projects
            projects = list(
                Project.objects.filter(is_archived=False)
                .order_by("-start_date")[:5]
            )
        
        return {"recent_projects": projects}
    except Exception:
        return {"recent_projects": []}
