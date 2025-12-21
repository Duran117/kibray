from datetime import timedelta
from decimal import Decimal
from typing import Any

from django.db.models import Count, Q
from django.utils import timezone

from core.models import (
    ColorApproval,
    Project,
    ProjectManagerAssignment,
    Task,
)


def get_project_health_metrics(project_id: int) -> dict[str, Any]:
    """
    Comprehensive project health analytics.

    Returns:
        - completion_percentage: % of tasks completed
        - budget_status: { total, spent, remaining, variance_pct }
        - timeline_status: { start, end, days_total, days_elapsed, days_remaining, on_track }
        - risk_indicators: { overdue_tasks, budget_overrun, behind_schedule }
        - task_summary: { total, completed, in_progress, pending, cancelled }
        - recent_activity: last 7 days task completions
    """
    try:
        project = Project.objects.get(id=project_id)
    except Project.DoesNotExist:
        return {"error": "Project not found"}

    # Task metrics
    tasks = project.tasks.all()
    total_tasks = tasks.count()
    completed = tasks.filter(status="Completada").count()
    in_progress = tasks.filter(status="En Progreso").count()
    pending = tasks.filter(status="Pendiente").count()
    cancelled = tasks.filter(status="Cancelada").count()
    overdue = tasks.filter(
        Q(status__in=["Pendiente", "En Progreso"]) & Q(due_date__lt=timezone.now().date())
    ).count()

    completion_pct = (completed / total_tasks * 100) if total_tasks > 0 else 0

    # Budget metrics
    budget_total = project.budget_total or Decimal("0")
    total_expenses = project.total_expenses or Decimal("0")
    budget_remaining = budget_total - total_expenses
    variance_pct = ((budget_total - total_expenses) / budget_total * 100) if budget_total > 0 else 0

    # Timeline metrics
    start_date = project.start_date
    end_date = project.end_date
    today = timezone.now().date()
    if start_date and end_date:
        days_total = (end_date - start_date).days
        days_elapsed = (today - start_date).days
        days_remaining = (end_date - today).days
        schedule_pct = (days_elapsed / days_total * 100) if days_total > 0 else 0
        on_track = completion_pct >= schedule_pct - 5  # 5% tolerance
    else:
        days_total = days_elapsed = days_remaining = None
        on_track = None

    # Recent activity
    seven_days_ago = timezone.now() - timedelta(days=7)
    recent_completions = tasks.filter(status="Completada", completed_at__gte=seven_days_ago).count()

    # Risk flags
    budget_overrun = total_expenses > budget_total
    behind_schedule = on_track is False if on_track is not None else False

    return {
        "project_id": project_id,
        "project_name": project.name,
        "completion_percentage": round(completion_pct, 2),
        "budget": {
            "total": float(budget_total),
            "spent": float(total_expenses),
            "remaining": float(budget_remaining),
            "variance_pct": round(variance_pct, 2),
        },
        "timeline": {
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None,
            "days_total": days_total,
            "days_elapsed": days_elapsed,
            "days_remaining": days_remaining,
            "on_track": on_track,
        },
        "task_summary": {
            "total": total_tasks,
            "completed": completed,
            "in_progress": in_progress,
            "pending": pending,
            "cancelled": cancelled,
        },
        "risk_indicators": {
            "overdue_tasks": overdue,
            "budget_overrun": budget_overrun,
            "behind_schedule": behind_schedule,
        },
        "recent_activity": {"completions_last_7_days": recent_completions},
    }


def get_touchup_analytics(project_id: int = None) -> dict[str, Any]:
    """
    Touch-up task analytics with trends and performance metrics.

    Returns:
        - total_touchups: count
        - by_status: { pending, in_progress, completed, cancelled }
        - by_priority: { low, medium, high, urgent }
        - completion_rate: %
        - avg_resolution_time: hours
        - trends: last 30 days daily completions
    """
    qs = Task.objects.filter(is_touchup=True)
    if project_id:
        qs = qs.filter(project_id=project_id)

    total = qs.count()
    if total == 0:
        return {
            "total_touchups": 0,
            "by_status": {},
            "by_priority": {},
            "completion_rate": 0,
            "avg_resolution_time_hours": 0,
            "trends": [],
        }

    # Status breakdown
    by_status = qs.values("status").annotate(count=Count("id")).order_by("-count")
    status_dict = {item["status"]: item["count"] for item in by_status}

    # Priority breakdown
    by_priority = qs.values("priority").annotate(count=Count("id")).order_by("-count")
    priority_dict = {item["priority"]: item["count"] for item in by_priority}

    # Completion rate
    completed = status_dict.get("Completada", 0)
    completion_rate = (completed / total * 100) if total > 0 else 0

    # Avg resolution time (created → completed)
    completed_tasks = qs.filter(status="Completada", completed_at__isnull=False)
    resolution_times = []
    for task in completed_tasks:
        delta = task.completed_at - task.created_at
        resolution_times.append(delta.total_seconds() / 3600)  # hours
    avg_resolution = sum(resolution_times) / len(resolution_times) if resolution_times else 0

    # Trends: last 30 days
    thirty_days_ago = timezone.now() - timedelta(days=30)
    daily_completions = (
        completed_tasks.filter(completed_at__gte=thirty_days_ago)
        .extra(select={"day": "DATE(completed_at)"})
        .values("day")
        .annotate(count=Count("id"))
        .order_by("day")
    )
    trends = [{"date": str(item["day"]), "count": item["count"]} for item in daily_completions]

    return {
        "total_touchups": total,
        "by_status": status_dict,
        "by_priority": priority_dict,
        "completion_rate": round(completion_rate, 2),
        "avg_resolution_time_hours": round(avg_resolution, 2),
        "trends": trends,
    }


def get_color_approval_analytics(project_id: int = None) -> dict[str, Any]:
    """
    Color approval workflow metrics.

    Returns:
        - total_approvals: count
        - by_status: { PENDING, APPROVED, REJECTED }
        - by_brand: top brands with counts
        - avg_approval_time_hours: from creation to approval
        - pending_aging: oldest pending approval days
    """
    qs = ColorApproval.objects.all()
    if project_id:
        qs = qs.filter(project_id=project_id)

    total = qs.count()
    if total == 0:
        return {
            "total_approvals": 0,
            "by_status": {},
            "by_brand": [],
            "avg_approval_time_hours": 0,
            "pending_aging_days": 0,
        }

    # Status breakdown
    by_status = qs.values("status").annotate(count=Count("id")).order_by("-count")
    status_dict = {item["status"]: item["count"] for item in by_status}

    # Brand breakdown (top 10)
    by_brand = qs.values("brand").annotate(count=Count("id")).order_by("-count")[:10]
    brand_list = [{"brand": item["brand"], "count": item["count"]} for item in by_brand]

    # Avg approval time
    approved = qs.filter(status="APPROVED", signed_at__isnull=False)
    approval_times = []
    for approval in approved:
        delta = approval.signed_at - approval.created_at
        approval_times.append(delta.total_seconds() / 3600)
    avg_approval = sum(approval_times) / len(approval_times) if approval_times else 0

    # Pending aging (oldest pending)
    oldest_pending = qs.filter(status="PENDING").order_by("created_at").first()
    if oldest_pending:
        age_delta = timezone.now() - oldest_pending.created_at
        pending_aging = age_delta.days
    else:
        pending_aging = 0

    return {
        "total_approvals": total,
        "by_status": status_dict,
        "by_brand": brand_list,
        "avg_approval_time_hours": round(avg_approval, 2),
        "pending_aging_days": pending_aging,
    }


def get_pm_performance_analytics() -> dict[str, Any]:
    """
    Project Manager workload and performance metrics.

    Returns:
        - pm_list: [{ pm_id, pm_username, projects_count, tasks_assigned, tasks_completed, completion_rate, overdue_count }]
        - overall: { total_pms, avg_projects_per_pm, avg_completion_rate }
    """
    pms = (
        ProjectManagerAssignment.objects.values("pm", "pm__username")
        .annotate(projects_count=Count("project", distinct=True))
        .order_by("-projects_count")
    )

    pm_data = []
    for pm_item in pms:
        pm_id = pm_item["pm"]
        pm_username = pm_item["pm__username"]
        projects = pm_item["projects_count"]

        # Tasks in PM's projects
        pm_projects = ProjectManagerAssignment.objects.filter(pm_id=pm_id).values_list(
            "project_id", flat=True
        )
        tasks = Task.objects.filter(project_id__in=pm_projects)
        tasks_assigned = tasks.count()
        tasks_completed = tasks.filter(status="Completada").count()
        completion_rate = (tasks_completed / tasks_assigned * 100) if tasks_assigned > 0 else 0
        overdue = tasks.filter(
            Q(status__in=["Pendiente", "En Progreso"]) & Q(due_date__lt=timezone.now().date())
        ).count()

        pm_data.append(
            {
                "pm_id": pm_id,
                "pm_username": pm_username,
                "projects_count": projects,
                "tasks_assigned": tasks_assigned,
                "tasks_completed": tasks_completed,
                "completion_rate": round(completion_rate, 2),
                "overdue_count": overdue,
            }
        )

    # Overall stats
    total_pms = len(pm_data)
    avg_projects = sum(p["projects_count"] for p in pm_data) / total_pms if total_pms > 0 else 0
    avg_completion = sum(p["completion_rate"] for p in pm_data) / total_pms if total_pms > 0 else 0

    return {
        "pm_list": pm_data,
        "overall": {
            "total_pms": total_pms,
            "avg_projects_per_pm": round(avg_projects, 2),
            "avg_completion_rate": round(avg_completion, 2),
        },
    }
