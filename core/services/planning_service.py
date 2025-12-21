"""
Planning Service - Intelligent suggestions for Daily Planning.

Provides smart recommendations from Schedule items to help PMs
create effective daily plans.
"""

from datetime import date, timedelta
from typing import Any

from core.models import Project, ScheduleItem


def get_suggested_items_for_date(project: Project, target_date: date) -> list[dict[str, Any]]:
    """
    Get schedule items that should be active on the target date.

    Returns items where target_date falls within [planned_start, planned_end].
    Includes progress, days remaining, and urgency indicators.

    Args:
        project: The project to search
        target_date: The date to check (typically tomorrow for daily planning)

    Returns:
        List of dictionaries with:
        - id: ScheduleItem ID
        - title: Item title
        - description: Item description
        - status: Current status
        - percent_complete: Progress percentage (0-100)
        - planned_start: Start date
        - planned_end: End date
        - days_remaining: Days until planned_end
        - days_elapsed: Days since planned_start
        - total_days: Total duration in days
        - is_urgent: True if less than 3 days remaining
        - is_behind: True if percent_complete < expected progress
        - category_name: Category name for grouping
    """
    # Query for items where target_date is within the planned range
    items = (
        ScheduleItem.objects.filter(
            project=project,
            planned_start__isnull=False,
            planned_end__isnull=False,
            planned_start__lte=target_date,
            planned_end__gte=target_date,
        )
        .exclude(
            status="DONE"  # Don't suggest completed items
        )
        .select_related("category", "cost_code")
        .order_by("planned_end", "order")
    )

    suggestions = []

    for item in items:
        # Calculate time metrics
        days_remaining = (item.planned_end - target_date).days
        days_elapsed = (target_date - item.planned_start).days
        total_days = (item.planned_end - item.planned_start).days + 1

        # Calculate expected progress (linear assumption)
        expected_progress = int(days_elapsed / total_days * 100) if total_days > 0 else 0

        # Determine urgency and status
        is_urgent = days_remaining <= 2
        is_behind = item.percent_complete < expected_progress - 10  # 10% tolerance

        suggestions.append(
            {
                "id": item.id,
                "title": item.title,
                "description": item.description,
                "status": item.status,
                "status_display": item.get_status_display(),
                "percent_complete": item.percent_complete,
                "planned_start": item.planned_start,
                "planned_end": item.planned_end,
                "days_remaining": days_remaining,
                "days_elapsed": days_elapsed,
                "total_days": total_days,
                "is_urgent": is_urgent,
                "is_behind": is_behind,
                "is_milestone": item.is_milestone,
                "category_name": item.category.name if item.category else "Sin categoría",
                "cost_code": item.cost_code.code if item.cost_code else None,
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
    items = ScheduleItem.objects.filter(
        project=project,
        planned_start__lte=end_date,
        planned_end__gte=start_date,
    ).exclude(status="DONE")

    total_items = items.count()
    urgent_items = items.filter(planned_end__lte=start_date + timedelta(days=2)).count()
    in_progress_items = items.filter(status="IN_PROGRESS").count()
    blocked_items = items.filter(status="BLOCKED").count()

    # Calculate average progress
    if total_items > 0:
        avg_progress = sum(item.percent_complete for item in items) / total_items
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
