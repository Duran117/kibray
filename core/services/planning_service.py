"""
Planning Service - Intelligent suggestions for Daily Planning.

Provides smart recommendations from Schedule items to help PMs
create effective daily plans.
"""

from datetime import date, timedelta
from typing import Any

from core.models import Project, ScheduleItemV2


def get_suggested_items_for_date(project: Project, target_date: date) -> list[dict[str, Any]]:
    """
    Get schedule items that should be active on the target date.

    Returns items where target_date falls within [start_date, end_date].
    Includes progress, days remaining, and urgency indicators.

    Args:
        project: The project to search
        target_date: The date to check (typically tomorrow for daily planning)

    Returns:
        List of dictionaries with:
        - id: ScheduleItemV2 ID
        - title: Item name
        - description: Item description
        - status: Current status
        - progress: Progress percentage (0-100)
        - start_date: Start date
        - end_date: End date
        - days_remaining: Days until end_date
        - days_elapsed: Days since start_date
        - total_days: Total duration in days
        - is_urgent: True if less than 3 days remaining
        - is_behind: True if progress < expected progress
        - phase_name: Phase name for grouping
    """
    # Query for items where target_date is within the planned range
    items = (
        ScheduleItemV2.objects.filter(
            project=project,
            start_date__isnull=False,
            end_date__isnull=False,
            start_date__lte=target_date,
            end_date__gte=target_date,
        )
        .exclude(
            status="done"  # Don't suggest completed items
        )
        .select_related("phase", "assigned_to")
        .order_by("end_date", "order")
    )

    suggestions = []

    for item in items:
        # Calculate time metrics
        days_remaining = (item.end_date - target_date).days
        days_elapsed = (target_date - item.start_date).days
        total_days = (item.end_date - item.start_date).days + 1

        # Calculate expected progress (linear assumption)
        expected_progress = int(days_elapsed / total_days * 100) if total_days > 0 else 0

        # Determine urgency and status
        is_urgent = days_remaining <= 2
        is_behind = item.progress < expected_progress - 10  # 10% tolerance

        suggestions.append(
            {
                "id": item.id,
                "title": item.name,
                "description": item.description,
                "status": item.status,
                "status_display": item.status.replace("_", " ").title(),
                "percent_complete": item.progress,
                "planned_start": item.start_date,
                "planned_end": item.end_date,
                "days_remaining": days_remaining,
                "days_elapsed": days_elapsed,
                "total_days": total_days,
                "is_urgent": is_urgent,
                "is_behind": is_behind,
                "is_milestone": item.is_milestone,
                "category_name": item.phase.name if item.phase else "Sin categoría",
                "expected_progress": expected_progress,
            }
        )

    return suggestions


def calculate_activity_priority(
    days_remaining: int, percent_complete: int, is_milestone: bool = False
) -> str:
    """
    Calculate priority level for an activity.

    Args:
        days_remaining: Days until planned_end
        percent_complete: Current progress percentage
        is_milestone: Whether this is a milestone

    Returns:
        Priority level: 'critical', 'high', 'medium', 'low'
    """
    # Milestones always get high priority
    if is_milestone:
        if days_remaining <= 2:
            return "critical"
        return "high"

    # Critical: urgent deadline with low progress
    if days_remaining <= 1 and percent_complete < 80:
        return "critical"

    # High: approaching deadline or behind schedule
    if days_remaining <= 2 or (days_remaining <= 5 and percent_complete < 50):
        return "high"

    # Medium: normal progress
    if days_remaining <= 7:
        return "medium"

    # Low: plenty of time
    return "low"


def get_activities_summary(project: Project, start_date: date, end_date: date) -> dict[str, Any]:
    """
    Get summary statistics for activities in a date range.

    Useful for weekly planning views.

    Args:
        project: Project to analyze
        start_date: Start of range
        end_date: End of range

    Returns:
        Dictionary with summary statistics
    """
    items = ScheduleItemV2.objects.filter(
        project=project,
        start_date__lte=end_date,
        end_date__gte=start_date,
    ).exclude(status="done")

    total_items = items.count()
    urgent_items = items.filter(end_date__lte=start_date + timedelta(days=2)).count()
    in_progress_items = items.filter(status="in_progress").count()
    blocked_items = items.filter(status="blocked").count()

    # Calculate average progress
    if total_items > 0:
        avg_progress = sum(item.progress for item in items) / total_items
    else:
        avg_progress = 0

    return {
        "total_items": total_items,
        "urgent_items": urgent_items,
        "in_progress_items": in_progress_items,
        "blocked_items": blocked_items,
        "avg_progress": round(avg_progress, 1),
        "date_range": {
            "start": start_date,
            "end": end_date,
        },
    }
