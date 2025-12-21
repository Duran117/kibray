"""
API Views for Executive Focus Workflow (Module 25 - Productivity)
Implements Pareto Principle + Eat That Frog methodology with calendar sync
"""

from datetime import timedelta
import logging

from django.db import models
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.api.serializers import (
    DailyFocusSessionSerializer,
    FocusSessionCreateSerializer,
    FocusTaskSerializer,
)
from core.models import DailyFocusSession, FocusTask

logger = logging.getLogger(__name__)


class DailyFocusSessionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Daily Focus Sessions.
    Users can only access their own sessions.
    """

    serializer_class = DailyFocusSessionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter to current user's sessions"""
        return (
            DailyFocusSession.objects.filter(user=self.request.user)
            .prefetch_related("focus_tasks")
            .order_by("-date")
        )

    def create(self, request, *args, **kwargs):
        """Create a new session with tasks"""
        logger.info(f"Creating focus session for user {request.user.id}")
        logger.debug(f"Request data: {request.data}")

        try:
            serializer = FocusSessionCreateSerializer(
                data=request.data, context={"request": request}
            )

            if not serializer.is_valid():
                logger.error(f"Validation errors: {serializer.errors}")
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            session = serializer.save()
            logger.info(f"Session {session.id} created successfully")

            # Return full session data
            response_serializer = DailyFocusSessionSerializer(session)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.exception(f"Error creating focus session: {e}")
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=["get"])
    def today(self, request):
        """Get today's focus session"""
        today = timezone.localdate()
        session = (
            DailyFocusSession.objects.filter(user=request.user, date=today)
            .prefetch_related("focus_tasks")
            .first()
        )

        if session:
            serializer = self.get_serializer(session)
            return Response(serializer.data)

        return Response({"detail": "No session for today yet."}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=["get"])
    def this_week(self, request):
        """Get this week's sessions"""
        today = timezone.localdate()
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)

        sessions = (
            DailyFocusSession.objects.filter(
                user=request.user, date__gte=week_start, date__lte=week_end
            )
            .prefetch_related("focus_tasks")
            .order_by("date")
        )

        serializer = self.get_serializer(sessions, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def complete_task(self, request, pk=None):
        """Mark a task as completed"""
        session = self.get_object()
        task_id = request.data.get("task_id")

        try:
            task = session.focus_tasks.get(id=task_id)
            task.is_completed = True
            task.save()

            serializer = FocusTaskSerializer(task)
            return Response(serializer.data)
        except FocusTask.DoesNotExist:
            return Response(
                {"detail": "Task not found in this session."}, status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=["post"])
    def update_checklist(self, request, pk=None):
        """Update checklist progress for a task"""
        session = self.get_object()
        task_id = request.data.get("task_id")
        checklist = request.data.get("checklist")

        try:
            task = session.focus_tasks.get(id=task_id)
            task.checklist = checklist
            task.save()

            serializer = FocusTaskSerializer(task)
            return Response(serializer.data)
        except FocusTask.DoesNotExist:
            return Response(
                {"detail": "Task not found in this session."}, status=status.HTTP_404_NOT_FOUND
            )


class FocusTaskViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Focus Tasks.
    Users can only access tasks from their own sessions.
    """

    serializer_class = FocusTaskSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter to current user's tasks"""
        return (
            FocusTask.objects.filter(session__user=self.request.user)
            .select_related("session")
            .order_by("-session__date", "order")
        )

    @action(detail=False, methods=["get"])
    def upcoming(self, request):
        """Get upcoming scheduled tasks (next 7 days)"""
        now = timezone.now()
        week_from_now = now + timedelta(days=7)

        tasks = (
            FocusTask.objects.filter(
                session__user=request.user,
                scheduled_start__gte=now,
                scheduled_start__lte=week_from_now,
                is_completed=False,
            )
            .select_related("session")
            .order_by("scheduled_start")
        )

        serializer = self.get_serializer(tasks, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def frog_history(self, request):
        """Get history of all Frog tasks"""
        days = int(request.query_params.get("days", 30))
        start_date = timezone.localdate() - timedelta(days=days)

        tasks = (
            FocusTask.objects.filter(
                session__user=request.user, session__date__gte=start_date, is_frog=True
            )
            .select_related("session")
            .order_by("-session__date")
        )

        serializer = self.get_serializer(tasks, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["patch"])
    def toggle_complete(self, request, pk=None):
        """Toggle task completion status"""
        task = self.get_object()
        task.is_completed = not task.is_completed
        task.save()

        serializer = self.get_serializer(task)
        return Response(serializer.data)

    @action(detail=True, methods=["patch"])
    def update_time_block(self, request, pk=None):
        """Update task time block"""
        task = self.get_object()

        scheduled_start = request.data.get("scheduled_start")
        scheduled_end = request.data.get("scheduled_end")

        if scheduled_start:
            task.scheduled_start = scheduled_start
        if scheduled_end:
            task.scheduled_end = scheduled_end

        task.save()

        serializer = self.get_serializer(task)
        return Response(serializer.data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def focus_stats(request):
    """
    Get productivity stats for the user.
    Returns aggregated data about focus sessions and tasks.
    """
    user = request.user
    days = int(request.query_params.get("days", 30))
    start_date = timezone.localdate() - timedelta(days=days)

    # Get sessions in date range
    sessions = DailyFocusSession.objects.filter(user=user, date__gte=start_date).prefetch_related(
        "focus_tasks"
    )

    # Calculate stats
    total_sessions = sessions.count()
    total_tasks = sum(s.total_tasks for s in sessions)
    completed_tasks = sum(s.completed_tasks for s in sessions)
    completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

    # Frog stats
    frog_tasks = FocusTask.objects.filter(
        session__user=user, session__date__gte=start_date, is_frog=True
    )
    total_frogs = frog_tasks.count()
    completed_frogs = frog_tasks.filter(is_completed=True).count()
    frog_completion_rate = (completed_frogs / total_frogs * 100) if total_frogs > 0 else 0

    # Average energy level
    avg_energy = sessions.aggregate(avg=models.Avg("energy_level"))["avg"] or 0

    # High impact tasks
    high_impact_tasks = FocusTask.objects.filter(
        session__user=user, session__date__gte=start_date, is_high_impact=True
    ).count()

    return Response(
        {
            "period_days": days,
            "total_sessions": total_sessions,
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "completion_rate": round(completion_rate, 1),
            "total_frogs": total_frogs,
            "completed_frogs": completed_frogs,
            "frog_completion_rate": round(frog_completion_rate, 1),
            "high_impact_tasks": high_impact_tasks,
            "avg_energy_level": round(avg_energy, 1),
        }
    )
