from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.db.models import Q
import json
import logging
from datetime import datetime, timedelta

from .models import Project, Task, ScheduleItem, PMBlockedDay, Employee

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
        # Add other types as needed
        
        return JsonResponse({'success': False, 'error': 'Unknown event type'})
        
    except Exception as e:
        logger.error(f"Calendar Wizard Error: {e}")
        return JsonResponse({'success': False, 'error': str(e)})

def save_task_event(data, user):
    project_id = data.get('project_id')
    title = data.get('title')
    start_date = data.get('start_date')
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
         
    if not assigned_employee:
        return JsonResponse({'success': False, 'error': 'Current user has no Employee profile to assign task.'})

    # Create Task
    task = Task.objects.create(
        project=project,
        title=title,
        # start_date is not a field in Task model, using due_date as end_date
        # If start_date is needed, we might need to add it or use created_at/schedule
        due_date=end_date,
        assigned_to=assigned_employee
    )
    
    return JsonResponse({'success': True, 'event_id': task.id, 'type': 'task'})

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
