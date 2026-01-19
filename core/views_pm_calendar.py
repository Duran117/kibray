"""
PM Calendar Views
Vista de calendario personalizada para Project Managers que muestra:
- Proyectos asignados con progreso
- Pipeline de proyectos futuros
- Días bloqueados (vacaciones, días personales)
- Carga de trabajo visualizada
- Próximas deadlines y milestones
"""

from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import (
    Invoice,
    PMBlockedDay,
    Profile,
    Project,
    Task,
)

from .services.schedule_unified import get_upcoming_milestones, get_project_progress


@login_required
def pm_calendar_view(request):
    """
    Personal calendar view for Project Managers.
    Shows assigned projects, workload, blocked days, and upcoming deadlines.
    """
    user = request.user

    # Check if user is a Project Manager
    try:
        profile = user.profile
        if (
            profile.role not in ["project_manager", "admin"]
            and not user.is_staff
            and not user.is_superuser
        ):
            messages.error(request, "Vista solo disponible para Project Managers")
            return redirect("dashboard")
    except Profile.DoesNotExist:
        # If no profile, check if staff/superuser
        if not user.is_staff and not user.is_superuser:
            messages.error(request, "Vista solo disponible para Project Managers")
            return redirect("dashboard")

    today = timezone.localdate()

    # Get PM assigned projects (active)
    assigned_projects = (
        Project.objects.filter(pm_assignments__pm=user, is_archived=False)
        .annotate(
            task_count=Count("tasks"),
            completed_tasks=Count("tasks", filter=Q(tasks__status="Completada")),
        )
        .select_related()
        .prefetch_related("pm_assignments")
        .order_by("-start_date")
    )

    # Calculate progress for each project
    for project in assigned_projects:
        if project.task_count > 0:
            project.progress_pct = int((project.completed_tasks / project.task_count) * 100)
        else:
            # Try to get progress from schedule items
            schedule_items = project.schedule_items.all()
            if schedule_items.exists():
                avg_pct = sum(item.percent_complete for item in schedule_items) / len(
                    schedule_items
                )
                project.progress_pct = int(avg_pct)
            else:
                project.progress_pct = 0

        # Add status badge color
        if project.progress_pct >= 100:
            project.status_color = "success"
        elif project.progress_pct >= 70:
            project.status_color = "info"
        elif project.progress_pct >= 40:
            project.status_color = "warning"
        else:
            project.status_color = "danger"

    # Get pipeline projects (pending start)
    pipeline_projects = (
        Project.objects.filter(pm_assignments__pm=user, is_archived=False, start_date__gt=today)
        .select_related()
        .order_by("start_date")[:5]
    )

    # Get blocked days (past week to next 3 months)
    date_range_start = today - timedelta(days=7)
    date_range_end = today + timedelta(days=90)

    blocked_days = PMBlockedDay.objects.filter(
        pm=user, date__gte=date_range_start, date__lte=date_range_end
    ).order_by("date")

    # Get upcoming deadlines
    upcoming_deadlines = []

    # Invoices due (next 30 days)
    invoices = (
        Invoice.objects.filter(
            project__pm_assignments__pm=user,
            due_date__gte=today,
            due_date__lte=today + timedelta(days=30),
            status__in=["SENT", "VIEWED", "APPROVED", "PARTIAL"],
        )
        .select_related("project")
        .order_by("due_date")[:10]
    )

    for invoice in invoices:
        days_until = (invoice.due_date - today).days
        urgency = "danger" if days_until <= 3 else "warning" if days_until <= 7 else "info"

        upcoming_deadlines.append(
            {
                "date": invoice.due_date,
                "title": f"Invoice #{invoice.invoice_number}",
                "project": invoice.project.name,
                "project_id": invoice.project.id,
                "type": "invoice",
                "icon": "💵",
                "urgency": urgency,
                "badge_class": "bg-rose-100 text-rose-700"
                if urgency == "danger"
                else "bg-amber-100 text-amber-700"
                if urgency == "warning"
                else "bg-sky-100 text-sky-700",
                "days_until": days_until,
            }
        )

    # Schedule milestones (next 30 days) - using unified service
    milestones = get_upcoming_milestones(user=user, days_ahead=30)[:10]

    for milestone in milestones:
        days_until = (milestone['date'] - today).days
        urgency = "danger" if days_until <= 3 else "warning" if days_until <= 7 else "info"

        upcoming_deadlines.append(
            {
                "date": milestone['date'],
                "title": f"Milestone: {milestone['title']}",
                "project": milestone['project_name'],
                "project_id": milestone['project'].id,
                "type": "milestone",
                "icon": "🚧",
                "urgency": urgency,
                "badge_class": "bg-rose-100 text-rose-700"
                if urgency == "danger"
                else "bg-amber-100 text-amber-700"
                if urgency == "warning"
                else "bg-sky-100 text-sky-700",
                "days_until": days_until,
            }
        )

    # High priority tasks due soon
    urgent_tasks = (
        Task.objects.filter(
            project__pm_assignments__pm=user,
            priority__in=["high", "urgent"],
            status__in=["Pendiente", "En Progreso"],
            due_date__isnull=False,
            due_date__gte=today,
            due_date__lte=today + timedelta(days=14),
        )
        .select_related("project")
        .order_by("due_date")[:10]
    )

    for task in urgent_tasks:
        days_until = (task.due_date - today).days
        urgency = "danger" if days_until <= 2 else "warning" if days_until <= 5 else "info"

        upcoming_deadlines.append(
            {
                "date": task.due_date,
                "title": f"Task: {task.title}",
                "project": task.project.name,
                "project_id": task.project.id,
                "type": "task",
                "icon": "📋",
                "urgency": urgency,
                "badge_class": "bg-rose-100 text-rose-700"
                if urgency == "danger"
                else "bg-amber-100 text-amber-700"
                if urgency == "warning"
                else "bg-sky-100 text-sky-700",
                "days_until": days_until,
                "priority": task.priority,
            }
        )

    # Sort all deadlines by date
    upcoming_deadlines.sort(key=lambda x: x["date"])

    # Calculate workload score
    # Formula: (active projects * 20) + (urgent tasks * 5) + (milestones in next 7 days * 10)
    active_count = assigned_projects.count()
    urgent_task_count = Task.objects.filter(
        project__pm_assignments__pm=user,
        priority__in=["high", "urgent"],
        status__in=["Pendiente", "En Progreso"],
    ).count()
    # Use unified service for milestones count
    upcoming_milestone_count = len(get_upcoming_milestones(user=user, days_ahead=7))

    workload_score = min(
        (active_count * 20) + (urgent_task_count * 5) + (upcoming_milestone_count * 10), 100
    )

    if workload_score < 40:
        workload_level = "Low"
        workload_color = "success"
    elif workload_score < 70:
        workload_level = "Medium"
        workload_color = "warning"
    else:
        workload_level = "High"
        workload_color = "danger"

    context = {
        "title": "Mi Calendario - PM",
        "assigned_projects": assigned_projects,
        "pipeline_projects": pipeline_projects,
        "blocked_days": blocked_days,
        "upcoming_deadlines": upcoming_deadlines[:15],  # Top 15
        "workload_score": workload_score,
        "workload_level": workload_level,
        "workload_color": workload_color,
        "today": today,
        "active_count": active_count,
        "urgent_task_count": urgent_task_count,
        "upcoming_milestone_count": upcoming_milestone_count,
    }

    return render(request, "core/pm_calendar.html", context)


@login_required
@require_POST
def pm_block_day(request):
    """
    Block a day for PM (vacation, personal, etc.)
    AJAX endpoint
    """
    try:
        profile = request.user.profile
        if (
            profile.role not in ["project_manager", "admin"]
            and not request.user.is_staff
            and not request.user.is_superuser
        ):
            return JsonResponse({"success": False, "error": "Permiso denegado"}, status=403)
    except Profile.DoesNotExist:
        if not request.user.is_staff and not request.user.is_superuser:
            return JsonResponse({"success": False, "error": "Permiso denegado"}, status=403)

    date_str = request.POST.get("date")
    reason = request.POST.get("reason", "vacation")
    notes = request.POST.get("notes", "")
    is_full_day = request.POST.get("is_full_day", "true").lower() == "true"
    start_time = request.POST.get("start_time") or None
    end_time = request.POST.get("end_time") or None

    if not date_str:
        return JsonResponse({"success": False, "error": "Fecha requerida"}, status=400)

    try:
        # Check if day already blocked
        existing = PMBlockedDay.objects.filter(pm=request.user, date=date_str).first()
        if existing:
            return JsonResponse(
                {
                    "success": False,
                    "error": f"El día {date_str} ya está bloqueado como {existing.get_reason_display()}",
                },
                status=400,
            )

        blocked_day = PMBlockedDay.objects.create(
            pm=request.user,
            date=date_str,
            reason=reason,
            notes=notes,
            is_full_day=is_full_day,
            start_time=start_time,
            end_time=end_time,
        )

        return JsonResponse(
            {
                "success": True,
                "message": f"Día {date_str} bloqueado correctamente",
                "blocked_day": {
                    "id": blocked_day.id,
                    "date": str(blocked_day.date),
                    "reason": blocked_day.get_reason_display(),
                    "is_full_day": blocked_day.is_full_day,
                },
            }
        )
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=400)


@login_required
@require_POST
def pm_unblock_day(request, blocked_day_id):
    """
    Remove a blocked day
    """
    blocked_day = get_object_or_404(PMBlockedDay, id=blocked_day_id)

    # Verify ownership
    if (
        blocked_day.pm != request.user
        and not request.user.is_staff
        and not request.user.is_superuser
    ):
        return JsonResponse({"success": False, "error": "Permiso denegado"}, status=403)

    date_str = str(blocked_day.date)
    blocked_day.delete()

    return JsonResponse({"success": True, "message": f"Día {date_str} desbloqueado correctamente"})


@login_required
def pm_calendar_api_data(request):
    """
    API endpoint for PM Calendar data (for AJAX calendar rendering)
    Returns events in FullCalendar format
    """
    try:
        profile = request.user.profile
        if (
            profile.role not in ["project_manager", "admin"]
            and not request.user.is_staff
            and not request.user.is_superuser
        ):
            return JsonResponse({"error": "Permiso denegado"}, status=403)
    except Profile.DoesNotExist:
        if not request.user.is_staff and not request.user.is_superuser:
            return JsonResponse({"error": "Permiso denegado"}, status=403)

    user = request.user
    today = timezone.localdate()

    # Get date range from query params (for FullCalendar)
    start_str = request.GET.get("start")
    end_str = request.GET.get("end")

    if start_str and end_str:
        try:
            from datetime import datetime

            # Handle potential ISO format variations
            start_date = datetime.fromisoformat(start_str.replace("Z", "")).date()
            end_date = datetime.fromisoformat(end_str.replace("Z", "")).date()
        except (ValueError, TypeError):
            # Fallback if date parsing fails
            start_date = today - timedelta(days=30)
            end_date = today + timedelta(days=90)
    else:
        start_date = today - timedelta(days=30)
        end_date = today + timedelta(days=90)

    events = []

    # Blocked days
    blocked_days = PMBlockedDay.objects.filter(pm=user, date__gte=start_date, date__lte=end_date)

    for blocked in blocked_days:
        events.append(
            {
                "id": f"blocked-{blocked.id}",
                "title": f"⛔ {blocked.get_reason_display()}",
                "start": str(blocked.date),
                "end": str(blocked.date),
                "allDay": blocked.is_full_day,
                "backgroundColor": "#dc3545",
                "borderColor": "#dc3545",
                "textColor": "#ffffff",
                "extendedProps": {
                    "type": "blocked",
                    "reason": blocked.reason,
                    "notes": blocked.notes,
                    "blocked_day_id": blocked.id,
                },
            }
        )

    # Project milestones - using unified service
    from .services.schedule_unified import get_schedule_items_for_date_range
    
    milestone_items = get_schedule_items_for_date_range(
        start_date=start_date,
        end_date=end_date,
        user=user,
    )
    milestones = [m for m in milestone_items if m.get('is_milestone')]

    for milestone in milestones:
        status = milestone.get('status', 'planned')
        color = (
            "#ffc107"
            if status == "planned"
            else "#17a2b8"
            if status == "in_progress"
            else "#28a745"
        )

        events.append(
            {
                "id": f"milestone-{milestone['source']}-{milestone['id']}",
                "title": f"🚧 {milestone['title']}",
                "start": str(milestone['start_date']),
                "end": str(milestone.get('end_date') or milestone['start_date']),
                "backgroundColor": color,
                "borderColor": color,
                "textColor": "#ffffff",
                "extendedProps": {
                    "type": "milestone",
                    "project": milestone['project_name'],
                    "project_id": milestone['project'].id,
                    "status": status,
                    "percent_complete": milestone.get('progress', 0),
                },
            }
        )

    # Invoices due
    invoices = Invoice.objects.filter(
        project__pm_assignments__pm=user,
        due_date__gte=start_date,
        due_date__lte=end_date,
        status__in=["SENT", "VIEWED", "APPROVED", "PARTIAL"],
    ).select_related("project")

    for invoice in invoices:
        days_until = (invoice.due_date - today).days
        color = "#dc3545" if days_until <= 3 else "#ffc107" if days_until <= 7 else "#17a2b8"

        events.append(
            {
                "id": f"invoice-{invoice.id}",
                "title": f"💵 Invoice #{invoice.invoice_number}",
                "start": str(invoice.due_date),
                "end": str(invoice.due_date),
                "backgroundColor": color,
                "borderColor": color,
                "textColor": "#ffffff",
                "extendedProps": {
                    "type": "invoice",
                    "project": invoice.project.name,
                    "project_id": invoice.project.id,
                    "amount": float(invoice.total_amount),
                    "days_until": days_until,
                },
            }
        )

    # High priority tasks with due dates
    tasks = Task.objects.filter(
        project__pm_assignments__pm=user,
        priority__in=["high", "urgent"],
        status__in=["Pendiente", "En Progreso"],
        due_date__isnull=False,
        due_date__gte=start_date,
        due_date__lte=end_date,
    ).select_related("project")

    for task in tasks:
        color = "#dc3545" if task.priority == "urgent" else "#fd7e14"

        events.append(
            {
                "id": f"task-{task.id}",
                "title": f"📋 {task.title}",
                "start": str(task.due_date),
                "end": str(task.due_date),
                "backgroundColor": color,
                "borderColor": color,
                "textColor": "#ffffff",
                "extendedProps": {
                    "type": "task",
                    "project": task.project.name,
                    "project_id": task.project.id,
                    "priority": task.priority,
                    "status": task.status,
                },
            }
        )

    return JsonResponse(events, safe=False)
