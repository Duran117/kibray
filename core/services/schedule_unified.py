"""
Unified Schedule Service
========================
Provides unified access to schedule data from both V1 (legacy) and V2 (new) systems.
Prefers V2 data when available, falls back to V1 for backwards compatibility.
"""

from datetime import date, timedelta
from typing import Any, Dict, List, Optional

from django.db.models import Q, Sum
from django.contrib.auth.models import User

from core.models import (
    Project,
    # V1 (Legacy) models
    Schedule,
    ScheduleCategory,
    ScheduleItem,
    # V2 (New) models
    SchedulePhaseV2,
    ScheduleItemV2,
    ScheduleTaskV2,
)


def get_project_schedule_data(project: Project) -> Dict[str, Any]:
    """
    Get unified schedule data for a project.
    Returns phases/items from V2 if available, otherwise from V1.
    """
    # Try V2 first
    v2_phases = SchedulePhaseV2.objects.filter(project=project).prefetch_related('items')
    
    if v2_phases.exists():
        return _get_v2_schedule_data(project, v2_phases)
    
    # Fall back to V1
    return _get_v1_schedule_data(project)


def _get_v2_schedule_data(project: Project, phases) -> Dict[str, Any]:
    """Get schedule data from V2 models."""
    phases_data = []
    all_items = []
    
    for phase in phases:
        items = phase.items.all()
        items_data = []
        
        for item in items:
            item_data = {
                'id': item.id,
                'title': item.name,
                'description': item.description,
                'start_date': item.start_date,
                'end_date': item.end_date,
                'status': item.status,
                'progress': item.progress,
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
        
        phases_data.append({
            'id': phase.id,
            'name': phase.name,
            'color': phase.color,
            'order': phase.order,
            'start_date': phase.start_date,
            'end_date': phase.end_date,
            'items': items_data,
            'items_count': len(items_data),
            'source': 'v2',
        })
    
    # Calculate overall progress
    total_items = len(all_items)
    if total_items > 0:
        avg_progress = sum(i['progress'] for i in all_items) / total_items
    else:
        avg_progress = 0
    
    return {
        'phases': phases_data,
        'items': all_items,
        'total_items': total_items,
        'avg_progress': avg_progress,
        'source': 'v2',
    }


def _get_v1_schedule_data(project: Project) -> Dict[str, Any]:
    """Get schedule data from V1 (legacy) models."""
    categories = ScheduleCategory.objects.filter(project=project).prefetch_related('schedule_items')
    
    phases_data = []
    all_items = []
    
    for category in categories:
        items = category.schedule_items.all()
        items_data = []
        
        for item in items:
            item_data = {
                'id': item.id,
                'title': item.title,
                'description': item.description or '',
                'start_date': item.planned_start,
                'end_date': item.planned_end,
                'status': _map_v1_status(item.status),
                'progress': item.percent_complete or 0,
                'is_milestone': item.is_milestone,
                'assigned_to': item.assigned_to,
                'assigned_to_name': item.assigned_to.get_full_name() if item.assigned_to else None,
                'color': item.color or category.color or '#6B7280',
                'phase_id': category.id,
                'phase_name': category.name,
                'source': 'v1',
            }
            items_data.append(item_data)
            all_items.append(item_data)
        
        phases_data.append({
            'id': category.id,
            'name': category.name,
            'color': category.color or '#6B7280',
            'order': category.order or 0,
            'start_date': min((i['start_date'] for i in items_data), default=None),
            'end_date': max((i['end_date'] for i in items_data), default=None),
            'items': items_data,
            'items_count': len(items_data),
            'source': 'v1',
        })
    
    # Also get orphan items (without category)
    orphan_items = ScheduleItem.objects.filter(project=project, category__isnull=True)
    for item in orphan_items:
        item_data = {
            'id': item.id,
            'title': item.title,
            'description': item.description or '',
            'start_date': item.planned_start,
            'end_date': item.planned_end,
            'status': _map_v1_status(item.status),
            'progress': item.percent_complete or 0,
            'is_milestone': item.is_milestone,
            'assigned_to': item.assigned_to,
            'assigned_to_name': item.assigned_to.get_full_name() if item.assigned_to else None,
            'color': item.color or '#6B7280',
            'phase_id': None,
            'phase_name': 'Uncategorized',
            'source': 'v1',
        }
        all_items.append(item_data)
    
    # Calculate overall progress
    total_items = len(all_items)
    if total_items > 0:
        avg_progress = sum(i['progress'] for i in all_items) / total_items
    else:
        avg_progress = 0
    
    return {
        'phases': phases_data,
        'items': all_items,
        'total_items': total_items,
        'avg_progress': avg_progress,
        'source': 'v1',
    }


def _map_v1_status(status: str) -> str:
    """Map V1 status to V2 status format."""
    mapping = {
        'NOT_STARTED': 'planned',
        'IN_PROGRESS': 'in_progress',
        'COMPLETED': 'done',
        'ON_HOLD': 'blocked',
    }
    return mapping.get(status, 'planned')


def get_upcoming_milestones(
    project: Optional[Project] = None,
    user: Optional[User] = None,
    days_ahead: int = 30,
) -> List[Dict[str, Any]]:
    """
    Get upcoming milestones from both V1 and V2 systems.
    
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
            'phase_name': item.phase.name,
            'status': item.status,
            'assigned_to': item.assigned_to,
            'source': 'v2',
        })
    
    # Query V1 milestones
    v1_query = ScheduleItem.objects.filter(
        is_milestone=True,
        planned_start__gte=today,
        planned_start__lte=end_date,
        status__in=['NOT_STARTED', 'IN_PROGRESS'],
    ).select_related('project', 'category', 'assigned_to')
    
    if project:
        v1_query = v1_query.filter(project=project)
    if user:
        v1_query = v1_query.filter(project__pm_assignments__pm=user)
    
    # Exclude V1 milestones if V2 data exists for the same project
    v2_project_ids = set(m['project'].id for m in milestones)
    
    for item in v1_query:
        if item.project_id in v2_project_ids:
            continue  # Skip V1 if V2 exists for this project
        
        milestones.append({
            'id': item.id,
            'title': item.title,
            'date': item.planned_start,
            'project': item.project,
            'project_name': item.project.name,
            'phase_name': item.category.name if item.category else 'Uncategorized',
            'status': _map_v1_status(item.status),
            'assigned_to': item.assigned_to,
            'source': 'v1',
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
    
    v2_project_ids = set()
    
    for item in v2_query:
        v2_project_ids.add(item.project_id)
        items.append({
            'id': item.id,
            'title': item.name,
            'description': item.description,
            'start_date': item.start_date,
            'end_date': item.end_date,
            'project': item.project,
            'project_name': item.project.name,
            'phase_name': item.phase.name,
            'status': item.status,
            'progress': item.progress,
            'is_milestone': item.is_milestone,
            'assigned_to': item.assigned_to,
            'color': item.color,
            'source': 'v2',
        })
    
    # Query V1 items (excluding projects that have V2 data)
    v1_query = ScheduleItem.objects.filter(
        Q(planned_start__lte=end_date, planned_end__gte=start_date)
    ).select_related('project', 'category', 'assigned_to')
    
    if project:
        v1_query = v1_query.filter(project=project)
    if user:
        v1_query = v1_query.filter(project__pm_assignments__pm=user)
    
    for item in v1_query:
        if item.project_id in v2_project_ids:
            continue  # Skip V1 if V2 exists
        
        items.append({
            'id': item.id,
            'title': item.title,
            'description': item.description or '',
            'start_date': item.planned_start,
            'end_date': item.planned_end,
            'project': item.project,
            'project_name': item.project.name,
            'phase_name': item.category.name if item.category else 'Uncategorized',
            'status': _map_v1_status(item.status),
            'progress': item.percent_complete or 0,
            'is_milestone': item.is_milestone,
            'assigned_to': item.assigned_to,
            'color': item.color or '#6B7280',
            'source': 'v1',
        })
    
    return items


def get_project_progress(project: Project) -> Dict[str, Any]:
    """
    Calculate project progress from schedule data.
    Prefers V2 data if available.
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
    completed = sum(1 for i in items if i['status'] == 'done' or i['progress'] >= 100)
    in_progress = sum(1 for i in items if i['status'] == 'in_progress' and i['progress'] < 100)
    planned = sum(1 for i in items if i['status'] == 'planned' and i['progress'] == 0)
    
    # Calculate weighted progress
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


def migrate_v1_to_v2(project: Project, dry_run: bool = True) -> Dict[str, Any]:
    """
    Migrate V1 schedule data to V2 for a project.
    
    Args:
        project: The project to migrate
        dry_run: If True, don't actually create records, just return what would be created
    
    Returns:
        Summary of migration
    """
    if has_v2_schedule(project):
        return {
            'success': False,
            'message': 'Project already has V2 schedule data',
            'phases_created': 0,
            'items_created': 0,
        }
    
    categories = ScheduleCategory.objects.filter(project=project).prefetch_related('schedule_items')
    
    phases_to_create = []
    items_to_create = []
    
    for category in categories:
        phase_data = {
            'project': project,
            'name': category.name,
            'color': category.color or '#4F46E5',
            'order': category.order or 0,
        }
        
        items = category.schedule_items.all()
        if items:
            phase_data['start_date'] = min(i.planned_start for i in items if i.planned_start)
            phase_data['end_date'] = max(i.planned_end for i in items if i.planned_end)
        
        phases_to_create.append({
            'phase_data': phase_data,
            'items': list(items),
            'category_id': category.id,
        })
    
    if dry_run:
        return {
            'success': True,
            'dry_run': True,
            'phases_to_create': len(phases_to_create),
            'items_to_create': sum(len(p['items']) for p in phases_to_create),
            'details': [
                {
                    'phase_name': p['phase_data']['name'],
                    'items_count': len(p['items']),
                }
                for p in phases_to_create
            ],
        }
    
    # Actually create the records
    phases_created = 0
    items_created = 0
    
    for phase_info in phases_to_create:
        phase = SchedulePhaseV2.objects.create(**phase_info['phase_data'])
        phases_created += 1
        
        for item in phase_info['items']:
            ScheduleItemV2.objects.create(
                project=project,
                phase=phase,
                name=item.title,
                description=item.description or '',
                start_date=item.planned_start,
                end_date=item.planned_end,
                status=_map_v1_status(item.status),
                progress=item.percent_complete or 0,
                is_milestone=item.is_milestone,
                assigned_to=item.assigned_to,
                color=item.color or phase.color,
                order=item.order or 0,
            )
            items_created += 1
    
    return {
        'success': True,
        'dry_run': False,
        'phases_created': phases_created,
        'items_created': items_created,
    }
