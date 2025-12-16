"""
Master Schedule Center API
Provides unified data for Strategic Gantt (Projects timeline) and Tactical Calendar (Daily events).
"""
from datetime import timedelta
from decimal import Decimal
from django.db.models import Q, Sum, Count, F
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_master_schedule_data(request):
    """Unified data source for Master Schedule (Gantt + Calendar).

    Response keys:
    - projects: strategic Gantt rows
    - schedule_items: per-project granular items (milestones/phases)
    - events: tactical events for calendar (invoices, COs, tasks, milestones)
    - metadata: counts and date range
    """

    from core.models import ChangeOrder, Invoice, Project, ScheduleItem, ScheduleCategory

    # Optional models (keep resilient)
    try:
        from core.models import Task
    except Exception:
        Task = None
    try:
        from core.models import MeetingMinute
    except Exception:
        MeetingMinute = None
    try:
        from core.models import ClientRequest
    except Exception:
        ClientRequest = None
    try:
        from core.models import MaterialRequest
    except Exception:
        MaterialRequest = None

    today = timezone.localdate()
    start_range = today - timedelta(days=30)
    end_range = today + timedelta(days=120)

    # === STRATEGIC GANTT: Projects ===
    projects_data = []
    active_projects = (
        Project.objects.filter(is_archived=False)
        .prefetch_related("tasks")
        .order_by("start_date", "id")
    )

    # Color palette for projects (cycle)
    colors = ["#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6", "#ec4899", "#06b6d4", "#84cc16"]

    for idx, project in enumerate(active_projects):
        total_tasks = project.tasks.count()
        completed_tasks = project.tasks.filter(status="Completada").count()
        progress_pct = int((completed_tasks / total_tasks * 100)) if total_tasks > 0 else 0

        pm_name = "No PM assigned"
        client_name = project.client or "No Client"

        projects_data.append(
            {
                "id": project.id,
                "name": project.name,
                "start_date": project.start_date.isoformat() if project.start_date else today.isoformat(),
                "end_date": project.end_date.isoformat()
                if project.end_date
                else (project.start_date + timedelta(days=90)).isoformat() if project.start_date else (today + timedelta(days=90)).isoformat(),
                "progress_pct": progress_pct,
                "color": colors[idx % len(colors)],
                "pm_name": pm_name,
                "client_name": client_name,
                "url": f"/projects/{project.id}/overview/",
            }
        )

    # === Granular schedule items (per project) ===
    schedule_items_data = []
    schedule_items_qs = (
        ScheduleItem.objects.filter(project__is_archived=False)
        .select_related("project", "category")
        .order_by("project_id", "order", "id")
    )

    status_colors = {
        "NOT_STARTED": "#cbd5e1",  # slate-300
        "IN_PROGRESS": "#3b82f6",  # blue-500
        "BLOCKED": "#ef4444",      # red-500
        "DONE": "#10b981",         # emerald-500
    }

    for item in schedule_items_qs:
        start_date = item.planned_start or item.planned_end or today
        end_date = item.planned_end or item.planned_start or start_date
        schedule_items_data.append(
            {
                "id": item.id,
                "project": item.project_id,
                "title": item.title,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "percent_complete": item.percent_complete,
                "status": item.status,
                "is_milestone": item.is_milestone,
                "category": item.category_id,
                "category_name": item.category.name if item.category else None,
                "color": status_colors.get(item.status, "#94a3b8"),
                # Use existing Django route (singular) to avoid 404s when clicking details
                "url": f"/schedule/item/{item.id}/edit/",
            }
        )

    # === Tactical Calendar Events ===
    events_data = []

    # Invoices due
    invoices = (
        Invoice.objects.filter(
            due_date__gte=start_range,
            due_date__lte=end_range,
            status__in=["SENT", "VIEWED", "APPROVED", "PARTIAL"],
        )
        .select_related("project")
        .order_by("due_date")
    )

    for invoice in invoices:
        events_data.append(
            {
                "title": f"💵 Invoice #{invoice.invoice_number} Due",
                "start": invoice.due_date.isoformat(),
                "end": invoice.due_date.isoformat(),
                "type": "invoice",
                "color": "#dc2626",
                "url": f"/invoices/{invoice.id}/",
                "description": f"${Decimal(invoice.total_amount):,} - {invoice.project.name if invoice.project else 'N/A'}",
            }
        )

    # Change Orders
    change_orders = (
        ChangeOrder.objects.filter(
            date_created__gte=start_range,
            date_created__lte=end_range,
            status__in=["pending", "approved", "sent", "billed"],
        )
        .select_related("project")
        .order_by("date_created")
    )

    for co in change_orders:
        start_date = co.date_created.date() if hasattr(co.date_created, "date") else co.date_created
        events_data.append(
            {
                "title": f"🔧 CO #{co.id}",
                "start": start_date.isoformat(),
                "end": start_date.isoformat(),
                "type": "change_order",
                "color": "#f59e0b",
                "url": f"/changeorder/{co.id}/",
                "description": f"{(co.description or '')[:60]}... - {co.project.name if co.project else 'N/A'}",
            }
        )

    # Schedule items (milestones and phases)
    for item in schedule_items_data:
        events_data.append(
            {
                "title": ("🚧 " if item["is_milestone"] else "🗂️ ") + item["title"],
                "start": item["start_date"],
                "end": item["end_date"],
                "type": "schedule_item",
                "color": item["color"],
                "url": item["url"],
                "description": f"{item['category_name'] or 'Schedule'} · {item['percent_complete']}%",
            }
        )

    # Tasks with due dates
    if Task is not None:
        tasks = (
            Task.objects.filter(
                due_date__isnull=False,
                due_date__gte=start_range,
                due_date__lte=end_range,
                status__in=["Pendiente", "En Progreso", "En Revisión"],
            )
            .select_related("project")
            .order_by("due_date")
        )
        for task in tasks:
            color = "#ef4444" if task.priority == "urgent" else "#fb923c" if task.priority == "high" else "#3b82f6"
            events_data.append(
                {
                    "title": f"📋 {task.title}",
                    "start": task.due_date.isoformat(),
                    "end": task.due_date.isoformat(),
                    "type": "task",
                    "color": color,
                    "url": f"/tasks/{task.id}/",
                    "description": f"{task.project.name if task.project else 'N/A'} · {task.priority}",
                }
            )

    # Meetings
    if MeetingMinute is not None:
        meetings = MeetingMinute.objects.filter(
            date__gte=start_range,
            date__lte=end_range,
        ).order_by("date")
        for meeting in meetings:
            events_data.append(
                {
                    "title": f"📅 Meeting: {meeting.title}",
                    "start": meeting.date.isoformat(),
                    "end": meeting.date.isoformat(),
                    "type": "meeting",
                    "color": "#8b5cf6",
                    "url": f"/meeting-minutes/{meeting.id}/",
                    "description": (meeting.summary or "")[:80],
                }
            )

    # Client Requests
    if ClientRequest is not None:
        client_requests = ClientRequest.objects.filter(
            created_at__date__gte=start_range,
            created_at__date__lte=end_range,
        ).order_by("created_at")
        for req in client_requests:
            start_date = req.created_at.date()
            events_data.append(
                {
                    "title": f"🙋 Client Request #{req.id}",
                    "start": start_date.isoformat(),
                    "end": start_date.isoformat(),
                    "type": "client_request",
                    "color": "#10b981",
                    "url": f"/client-requests/{req.id}/",
                    "description": (req.subject or "")[:80],
                }
            )

    # Material Requests
    if MaterialRequest is not None:
        material_requests = MaterialRequest.objects.filter(
            created_at__date__gte=start_range,
            created_at__date__lte=end_range,
        ).order_by("created_at")
        for mr in material_requests:
            start_date = mr.created_at.date()
            # Not all deployments have a "description" field; fall back to notes/blank
            mr_description = getattr(mr, "description", None) or getattr(mr, "notes", "") or ""
            events_data.append(
                {
                    "title": f"📦 Material Request #{mr.id}",
                    "start": start_date.isoformat(),
                    "end": start_date.isoformat(),
                    "type": "material_request",
                    "color": "#06b6d4",
                    "url": f"/material-requests/{mr.id}/",
                    "description": mr_description[:80],
                }
            )

    events_data.sort(key=lambda x: x["start"])

    return Response(
        {
            "projects": projects_data,
            "schedule_items": schedule_items_data,
            "events": events_data,
            "metadata": {
                "total_projects": len(projects_data),
                "total_events": len(events_data),
                "total_schedule_items": len(schedule_items_data),
                "date_range": {
                    "start": start_range.isoformat(),
                    "end": end_range.isoformat(),
                },
            },
        }
    )
