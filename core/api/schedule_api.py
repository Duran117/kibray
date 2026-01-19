"""
Master Schedule Center API
Provides unified data for Strategic Gantt (Projects timeline) and Tactical Calendar (Daily events).
"""

from datetime import date, timedelta
from decimal import Decimal

from django.db.models import Prefetch
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.api.serializer_classes.schedule_v2_serializers import (
    ProjectMinimalSerializer,
    ScheduleDependencyV2Serializer,
    ScheduleDependencyV2WriteSerializer,
    ScheduleItemV2Serializer,
    ScheduleItemV2WriteSerializer,
    SchedulePhaseV2Serializer,
    SchedulePhaseV2WriteSerializer,
    ScheduleTaskV2Serializer,
    ScheduleTaskV2WriteSerializer,
)
from core.models import (
    Project,
    ScheduleDependencyV2,
    ScheduleItemV2,
    SchedulePhaseV2,
    ScheduleTaskV2,
)


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

    from core.models import ChangeOrder, Invoice, Project, ScheduleItem

    # Optional models (keep resilient)
    try:
        from core.models import Task as task_model  # noqa: N813
    except Exception:
        task_model = None
    try:
        from core.models import MeetingMinute as meeting_minute_model  # noqa: N813
    except Exception:
        meeting_minute_model = None
    try:
        from core.models import ClientRequest as client_request_model  # noqa: N813
    except Exception:
        client_request_model = None
    try:
        from core.models import MaterialRequest as material_request_model  # noqa: N813
    except Exception:
        material_request_model = None

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
    colors = [
        "#3b82f6",
        "#10b981",
        "#f59e0b",
        "#ef4444",
        "#8b5cf6",
        "#ec4899",
        "#06b6d4",
        "#84cc16",
    ]

    # Import Gantt progress service
    from core.services.schedule_unified import get_project_progress

    for idx, project in enumerate(active_projects):
        # Use Gantt V2/V1 progress
        gantt_progress = get_project_progress(project)
        progress_pct = int(gantt_progress.get('progress_percent', 0))
        
        # Fallback to tasks if no Gantt data
        if gantt_progress.get('total_items', 0) == 0:
            total_tasks = project.tasks.count()
            completed_tasks = project.tasks.filter(status="Completada").count()
            progress_pct = int(completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

        pm_name = "No PM assigned"
        client_name = project.client or "No Client"

        projects_data.append(
            {
                "id": project.id,
                "name": project.name,
                "start_date": project.start_date.isoformat()
                if project.start_date
                else today.isoformat(),
                "end_date": project.end_date.isoformat()
                if project.end_date
                else (project.start_date + timedelta(days=90)).isoformat()
                if project.start_date
                else (today + timedelta(days=90)).isoformat(),
                "progress_pct": progress_pct,
                "gantt_progress": gantt_progress,
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
        "BLOCKED": "#ef4444",  # red-500
        "DONE": "#10b981",  # emerald-500
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
    if task_model is not None:
        tasks = (
            task_model.objects.filter(
                due_date__isnull=False,
                due_date__gte=start_range,
                due_date__lte=end_range,
                status__in=["Pendiente", "En Progreso", "En Revisión"],
            )
            .select_related("project")
            .order_by("due_date")
        )
        for task in tasks:
            color = (
                "#ef4444"
                if task.priority == "urgent"
                else "#fb923c"
                if task.priority == "high"
                else "#3b82f6"
            )
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
    if meeting_minute_model is not None:
        meetings = meeting_minute_model.objects.filter(
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
    if client_request_model is not None:
        client_requests = client_request_model.objects.filter(
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
    if material_request_model is not None:
        material_requests = material_request_model.objects.filter(
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


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_project_gantt_v2(request, project_id=None):
    """Gantt v2 read-only endpoint (phases → items → tasks, deps aparte) por proyecto."""

    project_param = project_id or request.query_params.get("project")
    if not project_param:
        return Response({"error": "project id is required"}, status=400)

    assigned_param = request.query_params.get("assigned_to")
    start_param = request.query_params.get("start_date")
    end_param = request.query_params.get("end_date")

    def parse_date_or_none(value):
        if not value:
            return None
        try:
            return date.fromisoformat(value)
        except Exception:
            return None

    start_filter = parse_date_or_none(start_param)
    end_filter = parse_date_or_none(end_param)

    project = Project.objects.filter(id=project_param).first()
    if not project:
        return Response({"error": "project not found"}, status=404)

    items_qs = (
        ScheduleItemV2.objects.select_related("phase", "assigned_to", "project")
        .prefetch_related("tasks")
        .filter(project=project)
    )

    # Filtros: asignado y rango de fechas (intersección)
    if assigned_param and assigned_param.lower() != "all":
        items_qs = items_qs.filter(assigned_to_id=assigned_param)

    if start_filter and end_filter:
        items_qs = items_qs.filter(start_date__lte=end_filter, end_date__gte=start_filter)
    elif start_filter:
        items_qs = items_qs.filter(end_date__gte=start_filter)
    elif end_filter:
        items_qs = items_qs.filter(start_date__lte=end_filter)

    phases = (
        SchedulePhaseV2.objects.filter(project=project)
        .prefetch_related(
            Prefetch(
                "items",
                queryset=items_qs.order_by("order", "id"),
            )
        )
        .order_by("order", "id")
    )

    # Limitar dependencias a los items filtrados (si aplica)
    filtered_item_ids = set()
    for p in phases:
        for it in p.items.all():
            filtered_item_ids.add(it.id)

    dependencies = (
        ScheduleDependencyV2.objects.filter(
            source_item__project=project, target_item__project=project
        )
        .select_related("source_item", "target_item")
        .order_by("source_item_id", "target_item_id")
    )

    if filtered_item_ids:
        dependencies = dependencies.filter(
            source_item_id__in=filtered_item_ids, target_item_id__in=filtered_item_ids
        )

    phases_data = SchedulePhaseV2Serializer(phases, many=True).data
    deps_data = ScheduleDependencyV2Serializer(dependencies, many=True).data
    project_data = ProjectMinimalSerializer(project).data

    # Totals for quick client-side metrics
    items_count = sum(len(p.get("items", [])) for p in phases_data)
    tasks_count = sum(len(i.get("tasks", [])) for p in phases_data for i in p.get("items", []))

    # Calculate project progress based on weighted stages
    all_phases = SchedulePhaseV2.objects.filter(project=project)
    total_stage_weight = sum(float(p.weight_percent) for p in all_phases)
    
    if total_stage_weight > 0:
        project_progress = sum(
            float(p.weight_percent) * p.calculated_progress / 100 
            for p in all_phases
        )
    else:
        # Fallback: simple average if no weights assigned
        if all_phases.exists():
            project_progress = sum(p.calculated_progress for p in all_phases) / all_phases.count()
        else:
            project_progress = 0

    return Response(
        {
            "project": project_data,
            "phases": phases_data,
            "dependencies": deps_data,
            "metadata": {
                "items_count": items_count,
                "tasks_count": tasks_count,
                "dependencies_count": len(deps_data),
                "project_progress": round(project_progress, 2),
                "total_stage_weight": round(total_stage_weight, 2),
            },
        }
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_schedule_phase_v2(request):
    serializer = SchedulePhaseV2WriteSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    phase = serializer.save()
    return Response(SchedulePhaseV2Serializer(phase).data, status=201)


@api_view(["PATCH", "DELETE"])
@permission_classes([IsAuthenticated])
def update_schedule_phase_v2(request, phase_id: int):
    phase = SchedulePhaseV2.objects.filter(id=phase_id).first()
    if not phase:
        return Response({"error": "phase not found"}, status=404)
    
    if request.method == "DELETE":
        phase.delete()
        return Response(status=204)
    
    serializer = SchedulePhaseV2WriteSerializer(phase, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    phase = serializer.save()
    return Response(SchedulePhaseV2Serializer(phase).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_schedule_item_v2(request):
    serializer = ScheduleItemV2WriteSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    item = serializer.save()
    return Response(ScheduleItemV2Serializer(item).data, status=201)


@api_view(["PATCH", "DELETE"])
@permission_classes([IsAuthenticated])
def update_schedule_item_v2(request, item_id: int):
    item = ScheduleItemV2.objects.filter(id=item_id).first()
    if not item:
        return Response({"error": "item not found"}, status=404)
    
    if request.method == "DELETE":
        item.delete()
        return Response(status=204)
    
    serializer = ScheduleItemV2WriteSerializer(item, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    item = serializer.save()
    return Response(ScheduleItemV2Serializer(item).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_schedule_task_v2(request):
    serializer = ScheduleTaskV2WriteSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    task = serializer.save()
    return Response(ScheduleTaskV2Serializer(task).data, status=201)


@api_view(["PATCH", "DELETE"])
@permission_classes([IsAuthenticated])
def update_schedule_task_v2(request, task_id: int):
    task = ScheduleTaskV2.objects.filter(id=task_id).first()
    if not task:
        return Response({"error": "task not found"}, status=404)
    
    if request.method == "DELETE":
        task.delete()
        return Response(status=204)
    
    serializer = ScheduleTaskV2WriteSerializer(task, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    task = serializer.save()
    return Response(ScheduleTaskV2Serializer(task).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_schedule_dependency_v2(request):
    serializer = ScheduleDependencyV2WriteSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    dep = serializer.save()
    return Response(ScheduleDependencyV2Serializer(dep).data, status=201)


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_schedule_dependency_v2(request, dependency_id: int):
    dep = ScheduleDependencyV2.objects.filter(id=dependency_id).first()
    if not dep:
        return Response({"error": "dependency not found"}, status=404)
    dep.delete()
    return Response(status=204)
