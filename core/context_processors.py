from django.conf import settings


def company(request):
    """Injects company branding info into all templates."""
    return {
        "company": {
            "name": "Kibray Paint & Stain LLC",
            "address_line1": "P.O Box 25881",
            "city_state_zip": "Silverthorne, CO 80498",
            "phone": "970-333-4872",
            "email": "jduran@kibraypainting.net",
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
        from core.models import ChangeOrder, ColorSample, Issue, MaterialRequest, Notification, Task, TimeEntry

        # Notificaciones no leídas (prioridad)
        badges["unread_notifications_count"] = Notification.objects.filter(user=request.user, is_read=False).count()

        # Unassigned time entries (no project assigned)
        badges["unassigned_time_count"] = TimeEntry.objects.filter(project__isnull=True).count()

        # Pending material requests
        badges["pending_materials_count"] = MaterialRequest.objects.filter(status="pending").count()

        # Open issues
        badges["open_issues_count"] = Issue.objects.filter(status__in=["open", "in_progress"]).count()

        # Pending change order approvals (if user is admin/staff)
        if request.user.is_staff:
            badges["pending_approvals_count"] = ChangeOrder.objects.filter(approval_status="pending").count()
            # Nuevas tareas creadas por clientes en estado Pendiente
            badges["new_client_tasks_count"] = Task.objects.filter(
                status="Pendiente", created_by__profile__role="client"
            ).count()
            # Muestras de color en revisión para aprobación
            badges["color_samples_review_count"] = ColorSample.objects.filter(status__in=["proposed", "review"]).count()
        else:
            # Para usuarios cliente: tareas completadas recientemente (últimos 3 días)
            if hasattr(request.user, "profile") and request.user.profile.role == "client":
                from django.utils import timezone

                recent_cutoff = timezone.now() - timezone.timedelta(days=3)
                badges["completed_tasks_client_count"] = Task.objects.filter(
                    project__client=request.user.username, status="Completada", completed_at__gte=recent_cutoff
                ).count()
    except Exception:
        # If models don't exist or error occurs, silently ignore
        pass

    return {"badges": badges}
