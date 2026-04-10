"""
Client Schedule Views
Shows project schedule to clients using the React Gantt component (read-only).
Also provides legacy API endpoints for backward compatibility.
"""

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, render

from .models import Project, ScheduleItemV2, ClientProjectAccess


# ---------------------------------------------------------------------------
# Reusable access check
# ---------------------------------------------------------------------------

def _has_project_access(user, project):
    """Check if user can view this project's schedule.

    Grants access to:
    1. Staff / superuser
    2. PM assigned to the project
    3. Client with explicit ClientProjectAccess
    4. Legacy: client CharField match
    """
    if user.is_staff or user.is_superuser:
        return True

    profile = getattr(user, "profile", None)
    if not profile:
        return False

    if profile.role == "project_manager":
        return project.pm_assignments.filter(user=user).exists()

    if profile.role == "client":
        if ClientProjectAccess.objects.filter(user=user, project=project).exists():
            return True
        if project.client and project.client.strip().lower() in (
            user.email.lower(),
            user.get_full_name().lower(),
            user.username.lower(),
        ):
            return True

    return False


# ---------------------------------------------------------------------------
# Main view — React Gantt read-only
# ---------------------------------------------------------------------------

@login_required
def client_project_calendar_view(request, project_id):
    """Client schedule view — mounts the React Gantt in read-only mode."""
    project = get_object_or_404(Project, id=project_id)

    if not _has_project_access(request.user, project):
        return HttpResponseForbidden("You do not have access to this schedule.")

    return render(request, "core/client_project_schedule.html", {
        "project": project,
    })


# ---------------------------------------------------------------------------
# Legacy API endpoints (kept for backward compatibility)
# ---------------------------------------------------------------------------

@login_required
def client_calendar_api_data(request, project_id):
    """JSON events for FullCalendar (legacy). Kept for any external consumers."""
    project = get_object_or_404(Project, id=project_id)

    if not _has_project_access(request.user, project):
        return JsonResponse({"error": "Not authorized"}, status=403)

    STATUS_COLORS = {
        "done": ("#10b981", "white"),
        "in_progress": ("#f59e0b", "#000"),
        "blocked": ("#ef4444", "white"),
    }
    STATUS_LABELS = {
        "planned": "Planned",
        "in_progress": "In Progress",
        "blocked": "Blocked",
        "done": "Completed",
    }

    items = ScheduleItemV2.objects.filter(
        project=project, is_personal=False,
    ).select_related("phase")
    events = []

    for item in items:
        if not item.start_date:
            continue
        color, text_color = STATUS_COLORS.get(item.status, ("#64748b", "white"))
        events.append({
            "id": item.id,
            "title": f"{'🎯' if item.is_milestone else '📋'} {item.name}",
            "start": item.start_date.isoformat(),
            "end": item.end_date.isoformat() if item.end_date else None,
            "backgroundColor": color,
            "borderColor": color,
            "textColor": text_color,
            "extendedProps": {
                "description": item.description,
                "status": STATUS_LABELS.get(item.status, item.status),
                "progress": item.progress,
                "phase": item.phase.name if item.phase else None,
                "is_milestone": item.is_milestone,
            },
        })

    return JsonResponse({
        "events": events,
        "project": {
            "name": project.name,
            "start_date": project.start_date.isoformat() if project.start_date else None,
            "end_date": project.end_date.isoformat() if project.end_date else None,
        },
    })


@login_required
def client_calendar_milestone_detail(request, item_id):
    """AJAX detail for a single schedule item (legacy)."""
    item = get_object_or_404(ScheduleItemV2, id=item_id)

    if not _has_project_access(request.user, item.project):
        return JsonResponse({"error": "Not authorized"}, status=403)

    STATUS_LABELS = {
        "planned": "Planned",
        "in_progress": "In Progress",
        "blocked": "Blocked",
        "done": "Completed",
    }

    tasks = item.tasks.all()
    return JsonResponse({
        "id": item.id,
        "title": item.name,
        "description": item.description,
        "status": STATUS_LABELS.get(item.status, item.status),
        "progress": item.progress,
        "is_milestone": item.is_milestone,
        "planned_start": item.start_date.isoformat() if item.start_date else None,
        "planned_end": item.end_date.isoformat() if item.end_date else None,
        "phase": item.phase.name if item.phase else None,
        "tasks": [{"id": t.id, "title": t.title, "status": t.status} for t in tasks[:5]],
        "tasks_count": tasks.count(),
    })
