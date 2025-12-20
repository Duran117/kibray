from datetime import datetime, timedelta
import json
import logging

from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_POST

from .models import (
    Employee,
    PMBlockedDay,
    Project,
    ScheduleCategory,
    ScheduleItem,
    Task,
)

try:
    from .models import MeetingMinute
except Exception:  # pragma: no cover - optional model
    MeetingMinute = None

logger = logging.getLogger(__name__)

@login_required
def calendar_wizard_view(request):
    """
    Render the Calendar Wizard for creating/editing events.
    """
    projects = Project.objects.filter(is_archived=False)
    if not request.user.is_superuser:
        # Filter projects where user is PM or has access
        projects = projects.filter(
            Q(pm_assignments__pm=request.user) |
            Q(client_accesses__user=request.user)
        ).distinct()

    context = {
        'projects': projects,
        'event_types': [
            ('task', 'Task'),
            ('milestone', 'Milestone'),
            ('meeting', 'Meeting'),
            ('blocked', 'Blocked Day')
        ]
    }
    return render(request, "core/wizards/calendar_wizard.html", context)

@login_required
@require_POST
def calendar_wizard_save(request):
    """
    Save event from wizard.
    """
    try:
        data = json.loads(request.body)
        event_type = data.get('type')

        if event_type == 'task':
            return save_task_event(data, request.user)
        elif event_type == 'blocked':
            return save_blocked_day(data, request.user)
        elif event_type == 'milestone':
            return save_milestone_event(data, request.user)
        elif event_type == 'meeting':
            return save_meeting_event(data, request.user)

        return JsonResponse({'success': False, 'error': 'Unknown event type'})

    except Exception as e:
        logger.error(f"Calendar Wizard Error: {e}")
        return JsonResponse({'success': False, 'error': str(e)})

def save_task_event(data, user):
    project_id = data.get('project_id')
    title = data.get('title')
    data.get('start_date')
    end_date = data.get('end_date')

    project = get_object_or_404(Project, pk=project_id)

    # Try to find employee profile for assignment
    assigned_employee = None
    if hasattr(user, 'employee_profile'):
        assigned_employee = user.employee_profile
    else:
        # Fallback: try to find by email or create dummy/admin employee if needed
        # For now, if no employee profile, we might leave it null or handle error
        # But Task.assigned_to expects an Employee instance.
        # Let's try to find one by email
        assigned_employee = Employee.objects.filter(email=user.email).first()

    if not assigned_employee:
         # Critical: Task requires an Employee.
         # If the current user is an admin without an employee profile, we can't assign the task to them directly in this model.
         # We will try to find ANY employee or raise a clear error.
         # Ideally, the UI should allow selecting an assignee.
         # For this wizard (MVP), we'll try to assign to the first available employee or fail gracefully.
         assigned_employee = Employee.objects.filter(user=user).first()

    # Allow unassigned tasks if no employee profile found (e.g. Admin creating task)
    # if not assigned_employee:
    #    return JsonResponse({'success': False, 'error': 'Current user has no Employee profile to assign task.'})

    # Create Task
    task = Task.objects.create(
        project=project,
        title=title,
        # start_date is not a field in Task model, using due_date as end_date
        # If start_date is needed, we might need to add it or use created_at/schedule
        due_date=end_date,
        assigned_to=assigned_employee,
        created_by=user
    )

    return JsonResponse({'success': True, 'event_id': task.id, 'type': 'task'})


def _get_default_schedule_category(project):
    """Return a schedule category for the project, creating a minimalist default if missing."""
    category = project.schedule_categories.order_by('order', 'id').first()
    if category:
        return category
    return ScheduleCategory.objects.create(project=project, name="General", order=0)


def save_milestone_event(data, user):
    project_id = data.get('project_id')
    title = data.get('title')
    start_date = data.get('start_date')
    end_date = data.get('end_date') or start_date

    project = get_object_or_404(Project, pk=project_id)
    category = _get_default_schedule_category(project)

    planned_start = datetime.strptime(start_date, '%Y-%m-%d').date()
    planned_end = datetime.strptime(end_date, '%Y-%m-%d').date()

    milestone = ScheduleItem.objects.create(
        project=project,
        category=category,
        title=title,
        planned_start=planned_start,
        planned_end=planned_end,
        is_milestone=True,
        status='NOT_STARTED',
        percent_complete=0,
        description='',
        order=0,
    )

    return JsonResponse({'success': True, 'event_id': milestone.id, 'type': 'milestone'})


def save_meeting_event(data, user):
    if MeetingMinute is None:
        return JsonResponse({'success': False, 'error': 'Meeting model not available'})

    project_id = data.get('project_id')
    title = data.get('title')
    start_date = data.get('start_date')

    project = get_object_or_404(Project, pk=project_id)
    meeting_date = datetime.strptime(start_date, '%Y-%m-%d').date()

    meeting = MeetingMinute.objects.create(
        project=project,
        date=meeting_date,
        content=title or '',
        attendees='',
        created_by=user,
    )

    return JsonResponse({'success': True, 'event_id': meeting.id, 'type': 'meeting'})

def save_blocked_day(data, user):
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    reason = data.get('reason', 'Personal')

    # Handle range
    start = datetime.strptime(start_date, '%Y-%m-%d').date()
    end = datetime.strptime(end_date, '%Y-%m-%d').date()

    current = start
    created_ids = []

    while current <= end:
        blocked, _ = PMBlockedDay.objects.get_or_create(
            pm=user,
            date=current,
            defaults={'reason': reason}
        )
        created_ids.append(blocked.id)
        current += timedelta(days=1)

    return JsonResponse({'success': True, 'ids': created_ids, 'type': 'blocked'})
