"""
Project-related viewsets for the Kibray API
"""

from decimal import Decimal

from django.db import models
from django.db.models import Q
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.api.filter_classes import ProjectFilter
from core.api.permission_classes import IsProjectMember
from core.api.serializer_classes import (
    ProjectBudgetSummarySerializer,
    ProjectCreateUpdateSerializer,
    ProjectDetailSerializer,
    ProjectListSerializer,
    ProjectStatsSerializer,
)
from core.models import Project


class ProjectViewSet(viewsets.ModelViewSet):
    """
    ViewSet for projects with full CRUD operations
    """

    queryset = Project.objects.select_related(
        "billing_organization", "project_lead"
    ).prefetch_related("observers")
    permission_classes = [IsAuthenticated]
    filterset_class = ProjectFilter
    search_fields = ["name", "address", "description", "client"]
    ordering_fields = ["name", "start_date", "end_date", "created_at"]
    ordering = ["name"]

    def get_queryset(self):
        """Filter queryset based on user permissions"""
        queryset = super().get_queryset()
        user = self.request.user

        # Superusers see all projects
        if user.is_superuser or user.is_staff:
            return queryset

        # Filter to projects where user is lead or observer
        # Note: This uses ClientContact, which may have a link to User
        return queryset.filter(Q(project_lead__user=user) | Q(observers__user=user)).distinct()

    def get_serializer_class(self):
        if self.action == "list":
            return ProjectListSerializer
        elif self.action == "retrieve":
            return ProjectDetailSerializer
        elif self.action in ["create", "update", "partial_update"]:
            return ProjectCreateUpdateSerializer
        return ProjectDetailSerializer

    def get_permissions(self):
        """Add project-specific permissions for certain actions"""
        if self.action in ["retrieve", "update", "partial_update", "destroy"]:
            return [IsAuthenticated(), IsProjectMember()]
        return super().get_permissions()

    @action(detail=False, methods=["get"])
    def assigned_projects(self, request):
        """Get projects where user is assigned"""
        user = request.user
        queryset = (
            Project.objects.filter(Q(project_lead__user=user) | Q(observers__user=user))
            .distinct()
            .order_by("name")
        )

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = ProjectListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = ProjectListSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def stats(self, request, pk=None):
        """Get detailed statistics for a project"""
        project = self.get_object()

        # Calculate statistics
        tasks = project.tasks.all()
        total_tasks = tasks.count()
        completed_tasks = tasks.filter(status="Completed").count()
        in_progress_tasks = tasks.filter(status="In Progress").count()

        # Budget calculations
        total_budget = float(project.budget_total or 0)
        spent_budget = float(project.total_expenses or 0)
        budget_variance = total_budget - spent_budget

        data = {
            "project_id": project.id,
            "project_name": project.name,
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "in_progress_tasks": in_progress_tasks,
            "total_budget": total_budget,
            "spent_budget": spent_budget,
            "budget_variance": budget_variance,
        }

        serializer = ProjectStatsSerializer(data)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def budget_overview(self, request):
        """Budget overview for all projects (lightweight aggregation)."""
        projects = self.get_queryset().annotate(
            expense_total=models.functions.Coalesce(models.Sum("expenses__amount"), Decimal("0.00"))
        )
        summaries = []
        for project in projects:
            percent_spent = round(
                (project.expense_total / project.budget_total * 100)
                if project.budget_total > 0
                else 0,
                2,
            )
            summaries.append(
                {
                    "project_id": project.id,
                    "project_name": project.name,
                    "budget_total": project.budget_total,
                    "budget_labor": project.budget_labor,
                    "budget_materials": project.budget_materials,
                    "budget_other": project.budget_other,
                    "total_expenses": project.expense_total,
                    "budget_remaining": project.budget_total - project.expense_total,
                    "percent_spent": percent_spent,
                    "is_over_budget": project.expense_total > project.budget_total,
                }
            )
        return Response(ProjectBudgetSummarySerializer(summaries, many=True).data)

    @action(detail=True, methods=["get"], url_path="critical-path")
    def critical_path(self, request, pk=None):
        """Critical Path Method (CPM) analysis for the project.

        Phase D2 — runs forward/backward passes over ``TaskDependency`` and
        returns earliest/latest schedules, slack and the critical chain.

        Query params:
        - ``durations``: optional comma-separated overrides ``id:minutes``
          (used mainly by tests). Example: ``?durations=1:60,2:120``
        """
        from core.services.critical_path import (
            CriticalPathCycleError,
            compute_critical_path,
        )

        project = self.get_object()

        overrides: dict[int, int] = {}
        raw = request.query_params.get("durations", "")
        if raw:
            for chunk in raw.split(","):
                chunk = chunk.strip()
                if not chunk or ":" not in chunk:
                    continue
                tid, mins = chunk.split(":", 1)
                try:
                    overrides[int(tid)] = int(mins)
                except (TypeError, ValueError):
                    continue

        try:
            result = compute_critical_path(project.id, durations=overrides or None)
        except CriticalPathCycleError as exc:
            return Response(
                {"error": "cycle_detected", "detail": str(exc)},
                status=400,
            )
        return Response(result)

    @action(detail=True, methods=["get"], url_path="ev-snapshots")
    def ev_snapshots(self, request, pk=None):
        """List historical Earned Value snapshots for the project (Phase D3).

        Query params:
        - ``since``: optional ISO date (``YYYY-MM-DD``); only return snapshots
          on or after this date.
        - ``limit``: optional max rows (default 90, capped at 365).
        """
        from datetime import date as date_cls

        project = self.get_object()
        qs = project.ev_snapshots.all().order_by("-date")

        since_raw = request.query_params.get("since")
        if since_raw:
            try:
                since = date_cls.fromisoformat(since_raw)
                qs = qs.filter(date__gte=since)
            except ValueError:
                return Response({"error": "invalid_since", "detail": since_raw}, status=400)

        try:
            limit = int(request.query_params.get("limit", 90))
        except (TypeError, ValueError):
            limit = 90
        limit = max(1, min(limit, 365))
        qs = qs[:limit]

        rows = [
            {
                "date": s.date.isoformat(),
                "PV": str(s.planned_value),
                "EV": str(s.earned_value),
                "AC": str(s.actual_cost),
                "SPI": str(s.spi),
                "CPI": str(s.cpi),
                "SV": str(s.schedule_variance),
                "CV": str(s.cost_variance),
                "EAC": str(s.estimate_at_completion),
                "ETC": str(s.estimate_to_complete),
                "VAC": str(s.variance_at_completion),
                "percent_complete": str(s.percent_complete),
                "percent_spent": str(s.percent_spent),
            }
            for s in qs
        ]
        return Response({"project_id": project.id, "count": len(rows), "snapshots": rows})

    @action(
        detail=True,
        methods=["post"],
        url_path="ev-snapshots/generate",
    )
    def ev_snapshots_generate(self, request, pk=None):
        """Force an immediate Earned Value snapshot for the project (Phase D3).

        Useful for QA / dashboards that need fresh data outside the 18:00
        Celery beat run. Idempotent for the current day (upsert).
        """
        from core.services.ev_snapshots import create_snapshot

        project = self.get_object()
        snap = create_snapshot(project)
        return Response(
            {
                "project_id": project.id,
                "date": snap.date.isoformat(),
                "PV": str(snap.planned_value),
                "EV": str(snap.earned_value),
                "AC": str(snap.actual_cost),
                "SPI": str(snap.spi),
                "CPI": str(snap.cpi),
                "EAC": str(snap.estimate_at_completion),
                "ETC": str(snap.estimate_to_complete),
                "VAC": str(snap.variance_at_completion),
                "percent_complete": str(snap.percent_complete),
                "percent_spent": str(snap.percent_spent),
            },
            status=201,
        )

    def perform_create(self, serializer):
        """Set created_by on project creation"""
        # Note: Current Project model doesn't have created_by field
        # This is for future compatibility
        serializer.save()
