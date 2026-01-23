from decimal import Decimal

from django.db.models import Avg, Sum
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import (
    ClientProjectAccess,
    Project,
    TimeEntry,
)


class ProjectDashboardView(APIView):
    """Aggregated metrics for a single project (execution + quality + financial).
    Response keys kept flat per domain for fast client rendering.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request: Request, project_id: int):
        project = get_object_or_404(Project, pk=project_id)
        # Tasks (count by status separately to avoid aggregate edge cases)
        tasks_qs = project.tasks.exclude(status="Cancelled")
        task_pending = tasks_qs.filter(status="Pending").count()
        task_in_progress = tasks_qs.filter(status="In Progress").count()
        task_completed = tasks_qs.filter(status="Completed").count()
        touchups_open = tasks_qs.filter(is_touchup=True).exclude(status="Completed").count()
        task_total = task_pending + task_in_progress + task_completed

        # Damage Reports
        damages = project.damage_reports.all()
        damage_open = damages.filter(status="open").count()
        damage_in_progress = damages.filter(status="in_progress").count()
        damage_resolved = damages.filter(status="resolved").count()

        # Color Samples
        colors = project.color_samples.all()
        colors_proposed = colors.filter(status="proposed").count()
        colors_review = colors.filter(status="review").count()
        colors_approved = colors.filter(status="approved").count()
        colors_rejected = colors.filter(status="rejected").count()

        # Site Photos
        photos_count = project.sitephoto_set.count() if hasattr(project, "sitephoto_set") else 0

        # Schedule progress (average percent of items)
        schedule_items = project.schedule_items.all()
        avg_schedule_progress = int(schedule_items.aggregate(a=Avg("percent_complete"))["a"] or 0)

        # Time / Labor (labor_cost computed dynamically via @property, not a DB field)
        time_entries = (
            project.timeentry_set.all()
            if hasattr(project, "timeentry_set")
            else TimeEntry.objects.filter(project=project)
        )
        hours_logged = time_entries.aggregate(total=Sum("hours_worked"))["total"] or Decimal("0")
        labor_cost = Decimal("0")
        for entry in time_entries.select_related("employee"):
            labor_cost += entry.labor_cost

        # Financial
        total_income = project.incomes.aggregate(total=Sum("amount"))["total"] or Decimal("0")
        total_expenses = project.expenses.aggregate(total=Sum("amount"))["total"] or Decimal("0")
        profit = total_income - total_expenses
        budget_total = project.budget_total
        budget_remaining = project.budget_remaining
        profit_margin = (profit / total_income * 100) if total_income > 0 else Decimal("0")

        # Weather coverage (days cached)
        weather_days = (
            project.weather_snapshots.count() if hasattr(project, "weather_snapshots") else 0
        )

        # Recent activity (limited list)
        # Recent activity (fetch minimal fields to reduce model instantiation)
        recent_activity: list[dict] = []
        for t in tasks_qs.order_by("-id").values("title", "status")[:3]:
            recent_activity.append({"type": "task", **t})
        for d in damages.order_by("-reported_at").values("title", "severity", "status")[:2]:
            recent_activity.append({"type": "damage", **d})
        for c in colors.order_by("-created_at").values("code", "status")[:2]:
            recent_activity.append({"type": "color", **c})

        # NOTE Performance: Reduced task counting from N separate count() queries to one aggregate; schedule & labor simplified.

        return Response(
            {
                "project": {
                    "id": project.id,
                    "name": project.name,
                    "client": project.client,
                    "budget_total": budget_total,
                    "budget_remaining": budget_remaining,
                },
                "tasks": {
                    "total": task_total,
                    "pending": task_pending,
                    "in_progress": task_in_progress,
                    "completed": task_completed,
                    "touchups_open": touchups_open,
                },
                "damage_reports": {
                    "open": damage_open,
                    "in_progress": damage_in_progress,
                    "resolved": damage_resolved,
                },
                "color_samples": {
                    "proposed": colors_proposed,
                    "review": colors_review,
                    "approved": colors_approved,
                    "rejected": colors_rejected,
                },
                "photos": {
                    "count": photos_count,
                },
                "schedule": {
                    "avg_progress_percent": avg_schedule_progress,
                },
                "labor": {
                    "hours_logged": hours_logged,
                    "estimated_labor_cost": labor_cost,
                },
                "financial": {
                    "income": total_income,
                    "expenses": total_expenses,
                    "profit": profit,
                    "profit_margin_percent": profit_margin,
                },
                "weather": {
                    "cached_days": weather_days,
                },
                "recent_activity": recent_activity,
            }
        )


class ClientDashboardView(APIView):
    """Dashboard for a client user summarizing accessible projects and approval items."""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request):
        user = request.user
        access_qs = ClientProjectAccess.objects.filter(user=user).select_related("project")
        projects_data: list[dict] = []
        pending_color_reviews = 0
        pending_touchups = 0

        for access in access_qs:
            p = access.project
            tasks_qs = p.tasks.all()
            touchups = tasks_qs.filter(is_touchup=True).exclude(status="Completed").count()
            colors_review = p.color_samples.filter(status="review").count()
            pending_color_reviews += colors_review
            pending_touchups += touchups
            damages_open = p.damage_reports.filter(status="open").count()

            projects_data.append(
                {
                    "id": p.id,
                    "name": p.name,
                    "budget_total": p.budget_total,
                    "budget_remaining": p.budget_remaining,
                    "touchups_open": touchups,
                    "color_review": colors_review,
                    "damages_open": damages_open,
                }
            )

        return Response(
            {
                "projects": projects_data,
                "totals": {
                    "projects_count": len(projects_data),
                    "pending_color_reviews": pending_color_reviews,
                    "pending_touchups": pending_touchups,
                },
            }
        )
