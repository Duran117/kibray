"""
Unified Schedule Service
========================
Provides unified access to schedule data from V2 system.
"""

from datetime import date, timedelta
from typing import Any, Dict, List, Optional

from django.db.models import Q, Sum
from django.contrib.auth.models import User

from core.models import (
    Project,
    # V2 models
    SchedulePhaseV2,
    ScheduleItemV2,
    ScheduleTaskV2,
)


def get_project_schedule_data(project: Project) -> Dict[str, Any]:
    """
    Get schedule data for a project from V2.
    """
    v2_phases = SchedulePhaseV2.objects.filter(project=project).prefetch_related('items')
    return _get_v2_schedule_data(project, v2_phases)


def _get_v2_schedule_data(project: Project, phases) -> Dict[str, Any]:
    """Get schedule data from V2 models."""
    phases_data = []
    all_items = []
    total_weight = 0
    weighted_progress = 0
    
    for phase in phases:
        items = phase.items.all()
        items_data = []
        
        for item in items:
            # Use calculated_progress - handles status='done' as 100%
            item_progress = item.calculated_progress
            # Double check: if status is done, ensure progress is 100
            if item.status == 'done':
                item_progress = 100
            
            item_data = {
                'id': item.id,
                'title': item.name,
                'description': item.description,
                'start_date': item.start_date,
                'end_date': item.end_date,
                'status': item.status,
                'progress': item_progress,
                'weight_percent': float(item.weight_percent),
                'is_milestone': item.is_milestone,
                'assigned_to': item.assigned_to,
                'assigned_to_name': item.assigned_to.get_full_name() if item.assigned_to else None,
                'color': item.color,
                'phase_id': phase.id,
                'phase_name': phase.name,
                'source': 'v2',
            }
            items_data.append(item_data)
            all_items.append(item_data)
        
        # Calculate phase progress using weights
        phase_progress = phase.calculated_progress
        
        phases_data.append({
            'id': phase.id,
            'name': phase.name,
            'color': phase.color,
            'order': phase.order,
            'weight_percent': float(phase.weight_percent),
            'start_date': phase.start_date,
            'end_date': phase.end_date,
            'items': items_data,
            'items_count': len(items_data),
            'calculated_progress': phase_progress,
            'source': 'v2',
        })
        
        # Accumulate for project-level weighted progress
        phase_weight = float(phase.weight_percent)
        total_weight += phase_weight
        weighted_progress += phase_weight * phase_progress / 100
    
    # Calculate overall progress (weighted by phase weights if available)
    total_items = len(all_items)
    if total_weight > 0:
        # Use weighted average if weights are assigned
        avg_progress = weighted_progress
    elif total_items > 0:
        # Fall back to simple average
        avg_progress = sum(i['progress'] for i in all_items) / total_items
    else:
        avg_progress = 0
    
    return {
        'phases': phases_data,
        'items': all_items,
        'total_items': total_items,
        'avg_progress': avg_progress,
        'total_weight': total_weight,
        'source': 'v2',
    }


def get_upcoming_milestones(
    project: Optional[Project] = None,
    user: Optional[User] = None,
    days_ahead: int = 30,
) -> List[Dict[str, Any]]:
    """
    Get upcoming milestones.
    
    Args:
        project: Filter by specific project
        user: Filter by PM user (projects assigned to them)
        days_ahead: How many days to look ahead
    """
    today = date.today()
    end_date = today + timedelta(days=days_ahead)
    milestones = []
    
    # Query V2 milestones
    v2_query = ScheduleItemV2.objects.filter(
        is_milestone=True,
        start_date__gte=today,
        start_date__lte=end_date,
        status__in=['planned', 'in_progress'],
    ).select_related('project', 'phase', 'assigned_to')
    
    if project:
        v2_query = v2_query.filter(project=project)
    if user:
        v2_query = v2_query.filter(project__pm_assignments__pm=user)
    
    for item in v2_query:
        milestones.append({
            'id': item.id,
            'title': item.name,
            'date': item.start_date,
            'project': item.project,
            'project_name': item.project.name,
            'phase_name': item.phase.name if item.phase else 'Sin fase',
            'status': item.status,
            'assigned_to': item.assigned_to,
            'source': 'v2',
        })
    
    # Sort by date
    milestones.sort(key=lambda x: x['date'])
    
    return milestones


def get_schedule_items_for_date_range(
    start_date: date,
    end_date: date,
    project: Optional[Project] = None,
    user: Optional[User] = None,
) -> List[Dict[str, Any]]:
    """
    Get all schedule items within a date range.
    """
    items = []
    
    # Query V2 items
    v2_query = ScheduleItemV2.objects.filter(
        Q(start_date__lte=end_date, end_date__gte=start_date)
    ).select_related('project', 'phase', 'assigned_to')
    
    if project:
        v2_query = v2_query.filter(project=project)
    if user:
        v2_query = v2_query.filter(project__pm_assignments__pm=user)
    
    for item in v2_query:
        items.append({
            'id': item.id,
            'title': item.name,
            'description': item.description,
            'start_date': item.start_date,
            'end_date': item.end_date,
            'project': item.project,
            'project_name': item.project.name,
            'phase_name': item.phase.name if item.phase else 'Sin fase',
            'status': item.status,
            'progress': item.progress,
            'is_milestone': item.is_milestone,
            'assigned_to': item.assigned_to,
            'color': item.color,
            'source': 'v2',
        })
    
    return items


def get_project_progress(project: Project) -> Dict[str, Any]:
    """
    Calculate project progress from schedule data.
    """
    schedule_data = get_project_schedule_data(project)
    
    total_items = schedule_data['total_items']
    
    if total_items == 0:
        return {
            'progress_percent': 0,
            'total_items': 0,
            'completed_items': 0,
            'in_progress_items': 0,
            'planned_items': 0,
            'source': schedule_data['source'],
        }
    
    items = schedule_data['items']
    
    # Count by status (use 'done' or 'completed' and progress >= 100)
    completed = sum(1 for i in items if i['status'] == 'done' or i.get('progress', 0) >= 100)
    in_progress = sum(1 for i in items if i['status'] == 'in_progress' and i.get('progress', 0) < 100)
    # Planned includes 'planned' and 'not_started'
    planned = sum(1 for i in items if i['status'] in ('planned', 'not_started') and i.get('progress', 0) == 0)
    
    # Use weighted progress from schedule_data
    avg_progress = schedule_data['avg_progress']
    
    return {
        'progress_percent': round(avg_progress, 1),
        'total_items': total_items,
        'completed_items': completed,
        'in_progress_items': in_progress,
        'planned_items': planned,
        'source': schedule_data['source'],
    }


def has_v2_schedule(project: Project) -> bool:
    """Check if project has V2 schedule data."""
    return SchedulePhaseV2.objects.filter(project=project).exists()


def get_upcoming_gantt_items(
    project: Project,
    days_ahead: int = 14,
    limit: int = 10,
) -> List[Dict[str, Any]]:
    """
    Get upcoming Gantt items (stages/items) for a project.
    Returns items with start_date in the next N days.
    This is for the project overview "Próximos Eventos" section.
    
    Args:
        project: The project to get items for
        days_ahead: How many days to look ahead (default 14)
        limit: Maximum number of items to return (default 10)
    """
    today = date.today()
    end_date = today + timedelta(days=days_ahead)
    items = []
    
    # Get V2 items
    v2_items = ScheduleItemV2.objects.filter(
        project=project,
        start_date__gte=today,
        start_date__lte=end_date,
    ).select_related('phase', 'assigned_to').order_by('start_date')[:limit]
    
    for item in v2_items:
        items.append({
            'id': item.id,
            'title': item.name,
            'start_date': item.start_date,
            'end_date': item.end_date,
            'phase_name': item.phase.name if item.phase else None,
            'phase_color': item.phase.color if item.phase else item.color,
            'status': item.status,
            'progress': item.progress,
            'is_milestone': item.is_milestone,
            'assigned_to': item.assigned_to,
            'color': item.color,
            'source': 'v2_gantt',
        })
    
    # If no items found in date range, get the next N items regardless of date
    if not items:
        v2_items_future = ScheduleItemV2.objects.filter(
            project=project,
            start_date__gt=today,
        ).select_related('phase', 'assigned_to').order_by('start_date')[:limit]
        
        for item in v2_items_future:
            items.append({
                'id': item.id,
                'title': item.name,
                'start_date': item.start_date,
                'end_date': item.end_date,
                'phase_name': item.phase.name if item.phase else None,
                'phase_color': item.phase.color if item.phase else item.color,
                'status': item.status,
                'progress': item.progress,
                'is_milestone': item.is_milestone,
                'assigned_to': item.assigned_to,
                'color': item.color,
                'source': 'v2_gantt',
            })
    
    return items
