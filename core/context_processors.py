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
        profile = getattr(user, "profile", None)
        role = getattr(profile, "role", None)

        # Unread notifications (with security filter for clients)
        notification_qs = Notification.objects.filter(user=user, is_read=False)
        if role == "client":
            client_project_ids = list(
                user.project_accesses.filter(is_active=True).values_list('project_id', flat=True)
            )
            notification_qs = notification_qs.filter(
                Q(project_id__in=client_project_ids) | Q(project__isnull=True)
            )
        badges["unread_notifications_count"] = notification_qs.count()

        # Staff/admin-only badges
        if user.is_staff:
            badges["unassigned_time_count"] = TimeEntry.objects.filter(project__isnull=True).count()
            badges["pending_materials_count"] = MaterialRequest.objects.filter(status="pending").count()
            badges["open_issues_count"] = Issue.objects.filter(status__in=["open", "in_progress"]).count()
            # ChangeOrder uses `status` field, not `approval_status`
            badges["pending_approvals_count"] = ChangeOrder.objects.filter(status="pending").count()
            badges["new_client_tasks_count"] = Task.objects.filter(
                status="Pending", created_by__profile__role="client"
            ).count()
            badges["color_samples_review_count"] = ColorSample.objects.filter(
                status__in=["proposed", "review"]
            ).count()
        elif role == "client":
            from django.utils import timezone
            recent_cutoff = timezone.now() - timezone.timedelta(days=3)
            badges["completed_tasks_client_count"] = Task.objects.filter(
                project__client=user.username,
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
    - Employees: Only see projects they are assigned to (via ResourceAssignment)
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
        elif profile and profile.role == "employee" and not request.user.is_staff:
            # Employees only see projects they are assigned to
            from core.models import ResourceAssignment
            employee = getattr(request.user, "employee_profile", None)
            if employee:
                assigned_project_ids = (
                    ResourceAssignment.objects.filter(employee=employee)
                    .values_list("project_id", flat=True)
                    .distinct()
                )
                projects = list(
                    Project.objects.filter(
                        id__in=assigned_project_ids, is_archived=False
                    ).order_by("-start_date")[:5]
                )
            else:
                projects = []
        else:
            # Staff, admin, PM - show recent active projects
            projects = list(
                Project.objects.filter(is_archived=False)
                .order_by("-start_date")[:5]
            )
        
        return {"recent_projects": projects}
    except Exception:
        return {"recent_projects": []}
