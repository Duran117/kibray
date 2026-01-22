"""
Client Calendar View
Dedicated calendar view for clients showing project schedule
in a visual, clean and easy to understand format.
Uses Gantt V2 models (SchedulePhaseV2, ScheduleItemV2).
"""

from django.contrib.auth.decorators import login_required
from django.db.models import Avg
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone

from .models import Project, ScheduleItemV2, SchedulePhaseV2, ClientProjectAccess


@login_required
def client_project_calendar_view(request, project_id):
    """
    Calendar view for clients.
    Shows project schedule in a beautiful and simple format.
    Only relevant information for clients (no costs, internal notes).
    Uses Gantt V2 models.
    """
    project = get_object_or_404(Project, id=project_id)

    # Check if client has access to the project
    profile = getattr(request.user, "profile", None)

    # Allow access to:
    # 1. Staff/Admin
    # 2. PM assigned to project
    # 3. Client with ClientProjectAccess
    # 4. Legacy: client field on project
    has_access = False

    if request.user.is_staff or request.user.is_superuser:
        has_access = True
    elif profile:
        if profile.role == "project_manager" and project.pm_assignments.filter(user=request.user).exists():
            has_access = True
        elif profile.role == "client":
            # Check modern ClientProjectAccess
            if ClientProjectAccess.objects.filter(user=request.user, project=project).exists():
                has_access = True
            # Also check legacy client field
            elif project.client and project.client.user == request.user:
                has_access = True

    if not has_access:
        return HttpResponseForbidden("You do not have access to this calendar.")

    # Obtener items del Gantt V2 (información visible para cliente)
    schedule_items = ScheduleItemV2.objects.filter(
        project=project
    ).select_related("phase", "assigned_to").order_by("start_date")

    # Obtener fases del proyecto (Gantt V2)
    phases = SchedulePhaseV2.objects.filter(project=project).order_by("order")

    # Calcular estadísticas del proyecto
    today = timezone.localdate()
    total_items = schedule_items.count()
    completed_items = schedule_items.filter(status="done").count()
    in_progress_items = schedule_items.filter(status="in_progress").count()

    # Calcular progreso general como promedio de progreso de items
    avg_progress = schedule_items.aggregate(avg=Avg("progress"))["avg"]
    overall_progress = int(avg_progress) if avg_progress else 0

    # Calcular días restantes basado en la fecha más lejana de items
    last_end = schedule_items.order_by("-end_date").first()
    if last_end and last_end.end_date:
        days_remaining = (last_end.end_date - today).days
    elif project.end_date:
        days_remaining = (project.end_date - today).days
    else:
        days_remaining = None

    # Preparar datos para el template
    context = {
        "project": project,
        "phases": phases,  # Renamed from categories
        "schedule_items": schedule_items,
        "overall_progress": overall_progress,
        "completed_items": completed_items,
        "in_progress_items": in_progress_items,
        "total_items": total_items,
        "days_remaining": days_remaining,
        "title": f"Cronograma - {project.name}",
        "today": today,
    }

    return render(request, "core/client_project_calendar.html", context)


@login_required
def client_calendar_api_data(request, project_id):
    """
    API endpoint returning calendar data in JSON format
    for FullCalendar.js. Uses Gantt V2 models.
    """
    project = get_object_or_404(Project, id=project_id)

    # Verify access (same check as main view)
    profile = getattr(request.user, "profile", None)
    has_access = False

    if request.user.is_staff or request.user.is_superuser:
        has_access = True
    elif profile:
        if profile.role == "project_manager" and project.pm_assignments.filter(user=request.user).exists():
            has_access = True
        elif profile.role == "client":
            # Check modern ClientProjectAccess
            if ClientProjectAccess.objects.filter(user=request.user, project=project).exists():
                has_access = True
            # Also check legacy client field
            elif project.client and project.client.user == request.user:
                has_access = True

    if not has_access:
        return JsonResponse({"error": "Not authorized"}, status=403)

    # Get schedule items from Gantt V2
    schedule_items = ScheduleItemV2.objects.filter(
        project=project
    ).select_related("phase")

    # Prepare events for FullCalendar
    events = []

    for item in schedule_items:
        # Color según estado - Premium palette
        if item.status == "done":
            color = "#10b981"  # Emerald - Completado
            text_color = "white"
        elif item.status == "in_progress":
            color = "#f59e0b"  # Amber - En progreso
            text_color = "#000"
        elif item.status == "blocked":
            color = "#ef4444"  # Red - Bloqueado
            text_color = "white"
        else:  # planned
            color = "#64748b"  # Slate - Planificado
            text_color = "white"

        # Icono según si es milestone
        icon = "🎯" if item.is_milestone else "📋"

        # Status display
        status_display = {
            "planned": "Planificado",
            "in_progress": "En Progreso",
            "blocked": "Bloqueado",
            "done": "Completado",
        }.get(item.status, item.status)

        event = {
            "id": item.id,
            "title": f"{icon} {item.name}",
            "start": item.start_date.isoformat() if item.start_date else None,
            "end": item.end_date.isoformat() if item.end_date else None,
            "backgroundColor": color,
            "borderColor": color,
            "textColor": text_color,
            "extendedProps": {
                "description": item.description,
                "status": status_display,
                "progress": item.progress,
                "phase": item.phase.name if item.phase else None,
                "is_milestone": item.is_milestone,
            },
        }

        # Solo agregar eventos con fechas válidas
        if event["start"]:
            events.append(event)

    return JsonResponse(
        {
            "events": events,
            "project": {
                "name": project.name,
                "start_date": project.start_date.isoformat() if project.start_date else None,
                "end_date": project.end_date.isoformat() if project.end_date else None,
            },
        }
    )


@login_required
def client_calendar_milestone_detail(request, item_id):
    """
    AJAX view returning milestone/item details
    to display in modal or popover.
    Uses Gantt V2 model.
    """
    item = get_object_or_404(ScheduleItemV2, id=item_id)

    # Verify access to project
    project = item.project
    profile = getattr(request.user, "profile", None)
    has_access = False

    if request.user.is_staff or request.user.is_superuser:
        has_access = True
    elif profile:
        if profile.role == "project_manager" and project.pm_assignments.filter(user=request.user).exists():
            has_access = True
        elif profile.role == "client":
            # Check modern ClientProjectAccess
            if ClientProjectAccess.objects.filter(user=request.user, project=project).exists():
                has_access = True
            # Also check legacy client field
            elif project.client and project.client.user == request.user:
                has_access = True

    if not has_access:
        return JsonResponse({"error": "Not authorized"}, status=403)

    # Get linked tasks (if any) from Gantt V2
    tasks = item.tasks.all()

    # Status display mapping
    status_display = {
        "planned": "Planificado",
        "in_progress": "En Progreso",
        "blocked": "Bloqueado",
        "done": "Completado",
    }.get(item.status, item.status)

    data = {
        "id": item.id,
        "title": item.name,  # V2 uses 'name' instead of 'title'
        "description": item.description,
        "status": status_display,
        "progress": item.progress,  # V2 uses 'progress' instead of 'percent_complete'
        "is_milestone": item.is_milestone,
        "planned_start": item.start_date.isoformat() if item.start_date else None,  # V2 field names
        "planned_end": item.end_date.isoformat() if item.end_date else None,
        "phase": item.phase.name if item.phase else None,  # V2 uses 'phase' instead of 'category'
        "tasks": [
            {
                "id": task.id,
                "title": task.title,
                "status": task.status,
            }
            for task in tasks[:5]  # Maximum 5 tasks
        ],
        "tasks_count": tasks.count(),
    }

    return JsonResponse(data)
