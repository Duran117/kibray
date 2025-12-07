"""
Strategic Planner Views
Module 25 Part B: Executive Planning & Productivity System
"""
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.utils.translation import gettext_lazy as _, gettext
from django.db import transaction
from django.core.exceptions import ValidationError
from datetime import datetime, timedelta
from icalendar import Calendar, Event as ICalEvent
import uuid
import json

from .models import (
    LifeVision, ExecutiveHabit, DailyRitualSession, 
    PowerAction, HabitCompletion, DailyFocusSession, FocusTask
)
from django.contrib.auth import get_user_model
from .services.planner_ai import PlannerAI

User = get_user_model()


@login_required
def quick_planner_entry(request):
    """
    Entry point for strategic planning - shows mode selector.
    User chooses between Quick Mode (AI-assisted) or Full Ritual.
    """
    if not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({
            'error': gettext('This feature is only available for Admin/PM users.')
        }, status=403)
    
    return render(request, 'core/quick_planner.html')


@login_required
def strategic_ritual_wizard(request):
    """
    Render the Strategic Ritual wizard interface.
    This is the main entry point for executive daily planning.
    """
    # Check if user is admin/staff
    if not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({
            'error': gettext('This feature is only available for Admin/PM users.')
        }, status=403)
    
    # Check if ritual already exists for today
    today = timezone.now().date()
    existing_ritual = DailyRitualSession.objects.filter(
        user=request.user,
        date=today
    ).first()
    
    context = {
        'existing_ritual': existing_ritual,
        'has_ritual_today': existing_ritual is not None
    }
    
    return render(request, 'core/strategic_ritual.html', context)


@login_required
@require_http_methods(["GET"])
def get_active_habits(request):
    """
    API endpoint: Get all active habits for current user.
    Used in Step 2 of the wizard.
    """
    habits = ExecutiveHabit.objects.filter(
        user=request.user,
        is_active=True
    ).values('id', 'title', 'frequency')
    
    return JsonResponse(list(habits), safe=False)


@login_required
@require_http_methods(["GET"])
def get_random_vision(request):
    """
    API endpoint: Get a random Life Vision to display as anchor.
    Used in Step 3 of the wizard.
    """
    vision = LifeVision.objects.filter(
        user=request.user
    ).order_by('?').first()
    
    if vision:
        return JsonResponse({
            'id': vision.id,
            'title': vision.title,
            'scope': vision.get_scope_display(),
            'deep_why': vision.deep_why,
            'progress_pct': vision.progress_pct
        })
    else:
        return JsonResponse({}, status=404)


@login_required
@require_http_methods(["POST"])
@transaction.atomic
def complete_ritual(request):
    """
    API endpoint: Complete the ritual and save all data.
    Called when user finishes Step 7 (Battle Plan).
    """
    import json
    
    try:
        data = json.loads(request.body)
        today = timezone.now().date()
        
        # Create or update ritual session
        ritual, created = DailyRitualSession.objects.update_or_create(
            user=request.user,
            date=today,
            defaults={
                'physiology_check': data.get('physiology_check', False),
                'gratitude_entries': data.get('gratitude', []),
                'daily_intention': data.get('daily_intention', ''),
                'energy_level': data.get('energy_level', 5),
                'habits_checked': data.get('habits', []),
                'completed_at': timezone.now()
            }
        )
        
        # Create PowerActions from impact items
        frog_id = data.get('frog_id')
        impact_items = data.get('impact_items', [])
        micro_steps = data.get('micro_steps', [])
        frog_start = data.get('frog_start')
        frog_end = data.get('frog_end')
        
        # Delete existing power actions for this session
        ritual.power_actions.all().delete()
        
        # Create power actions
        for idx, item in enumerate(impact_items):
            is_frog = (item['id'] == frog_id)
            
            # Parse time blocking for frog
            scheduled_start = None
            scheduled_end = None
            if is_frog and frog_start and frog_end:
                try:
                    scheduled_start = timezone.make_aware(
                        datetime.combine(today, datetime.strptime(frog_start, '%H:%M').time())
                    )
                    scheduled_end = timezone.make_aware(
                        datetime.combine(today, datetime.strptime(frog_end, '%H:%M').time())
                    )
                except (ValueError, TypeError):
                    pass
            
            power_action = PowerAction.objects.create(
                session=ritual,
                title=item['text'],
                is_80_20=True,  # All items in impact column are 80/20
                is_frog=is_frog,
                impact_reason="High-impact action identified in daily ritual",
                micro_steps=micro_steps if is_frog else [],
                scheduled_start=scheduled_start,
                scheduled_end=scheduled_end,
                status='SCHEDULED' if scheduled_start else 'DRAFT',
                order=idx
            )
        
        # Create habit completions
        habit_ids = data.get('habits', [])
        for habit_id in habit_ids:
            try:
                habit = ExecutiveHabit.objects.get(id=habit_id, user=request.user)
                HabitCompletion.objects.get_or_create(
                    habit=habit,
                    completed_date=today,
                    defaults={'session': ritual}
                )
            except ExecutiveHabit.DoesNotExist:
                continue
        
        return JsonResponse({
            'success': True,
            'ritual_id': ritual.id,
            'message': gettext('Ritual completed successfully!')
        })
        
    except ValidationError as e:
        return JsonResponse({
            'success': False,
            'error': gettext('%(error)s') % {'error': str(e)}
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': gettext('Unexpected error: %(error)s') % {'error': str(e)}
        }, status=500)


@login_required
@require_http_methods(["GET"])
def planner_calendar_feed(request, user_token):
    """
    Generate iCal feed for PowerActions.
    URL: /api/planner/feed/<user_token>.ics
    
    This allows external calendar apps to subscribe to PowerActions.
    """
    # Verify user token (in production, implement proper token validation)
    # For now, use a simple check based on user ID
    try:
        # Simple token: base64(user_id)
        import base64
        user_id = int(base64.b64decode(user_token).decode())
        user = User.objects.get(id=user_id)
    except (ValueError, User.DoesNotExist):
        return HttpResponse('Invalid token', status=404)
    
    # Create calendar
    cal = Calendar()
    cal.add('prodid', '-//Kibray Strategic Planner//EN')
    cal.add('version', '2.0')
    cal.add('x-wr-calname', f'{user.get_full_name()} - Strategic Actions')
    cal.add('x-wr-caldesc', 'High-impact PowerActions from Strategic Planner')
    
    # Get PowerActions from last 30 days and next 30 days
    start_date = timezone.now() - timedelta(days=30)
    end_date = timezone.now() + timedelta(days=30)
    
    power_actions = PowerAction.objects.filter(
        session__user=user,
        session__date__gte=start_date.date(),
        session__date__lte=end_date.date(),
        scheduled_start__isnull=False,
        scheduled_end__isnull=False
    ).select_related('session', 'linked_vision')
    
    # Add each PowerAction as an event
    for action in power_actions:
        event = ICalEvent()
        event.add('uid', str(action.ical_uid))
        event.add('summary', action.get_calendar_title())
        event.add('description', action.get_calendar_description())
        event.add('dtstart', action.scheduled_start)
        event.add('dtend', action.scheduled_end)
        event.add('dtstamp', action.created_at)
        
        # Add status
        if action.status == 'DONE':
            event.add('status', 'COMPLETED')
        else:
            event.add('status', 'CONFIRMED')
        
        # Add categories
        categories = ['Strategic Planning']
        if action.is_frog:
            categories.append('🐸 The Frog')
        if action.is_80_20:
            categories.append('⚡ High Impact')
        event.add('categories', categories)
        
        cal.add_component(event)
    
    # Return as iCalendar file
    response = HttpResponse(cal.to_ical(), content_type='text/calendar; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="{user.username}_strategic_planner.ics"'
    return response


@login_required
@require_http_methods(["GET"])
def today_ritual_summary(request):
    """
    API endpoint: Get summary of today's ritual for dashboard widget.
    Returns the Frog and its micro-steps progress.
    Supports both DailyRitualSession (Strategic Planner) and DailyFocusSession (Focus Wizard).
    """
    today = timezone.now().date()
    
    # 1. Try Strategic Ritual (DailyRitualSession)
    ritual = DailyRitualSession.objects.filter(
        user=request.user,
        date=today
    ).first()
    
    if ritual:
        frog = ritual.frog_action
        if not frog:
            return JsonResponse({
                'has_ritual': True,
                'has_frog': False,
                'message': 'Ritual completed but no Frog selected'
            })
        
        return JsonResponse({
            'has_ritual': True,
            'has_frog': True,
            'source': 'strategic_planner',
            'frog': {
                'id': frog.id,
                'title': frog.title,
                'status': frog.status,
                'is_completed': frog.status == 'DONE',
                'micro_steps': frog.micro_steps,
                'micro_steps_progress': frog.micro_steps_progress,
                'scheduled_start': frog.scheduled_start.isoformat() if frog.scheduled_start else None,
                'scheduled_end': frog.scheduled_end.isoformat() if frog.scheduled_end else None,
                'duration_minutes': frog.duration_minutes
            },
            'ritual': {
                'energy_level': ritual.energy_level,
                'total_actions': ritual.total_power_actions,
                'completed_actions': ritual.completed_power_actions,
                'high_impact_actions': ritual.high_impact_actions
            }
        })

    # 2. Try Focus Wizard (DailyFocusSession)
    focus_session = DailyFocusSession.objects.filter(
        user=request.user,
        date=today
    ).first()

    if focus_session:
        frog_task = focus_session.frog_task
        if not frog_task:
            return JsonResponse({
                'has_ritual': True,
                'has_frog': False,
                'message': 'Focus session completed but no Frog selected'
            })
        
        # Map FocusTask to same structure as PowerAction for frontend compatibility
        return JsonResponse({
            'has_ritual': True,
            'has_frog': True,
            'source': 'focus_wizard',
            'frog': {
                'id': frog_task.id,
                'title': frog_task.title,
                'status': 'DONE' if frog_task.is_completed else 'SCHEDULED',
                'is_completed': frog_task.is_completed,
                'micro_steps': frog_task.checklist if hasattr(frog_task, 'checklist') else [],
                'micro_steps_progress': 100 if frog_task.is_completed else 0, # FocusTask might not have progress calc
                'scheduled_start': frog_task.scheduled_start.isoformat() if frog_task.scheduled_start else None,
                'scheduled_end': frog_task.scheduled_end.isoformat() if frog_task.scheduled_end else None,
                'duration_minutes': 60 # Default or calc
            },
            'ritual': {
                'energy_level': focus_session.energy_level,
                'total_actions': focus_session.total_tasks,
                'completed_actions': focus_session.completed_tasks,
                'high_impact_actions': focus_session.high_impact_tasks
            }
        })

    return JsonResponse({
        'has_ritual': False,
        'message': 'No ritual completed today'
    })


@login_required
@require_http_methods(["POST"])
def toggle_power_action_status(request, action_id):
    """
    API endpoint: Toggle PowerAction OR FocusTask status.
    Used in dashboard widget to mark Frog as complete.
    """
    # 1. Try PowerAction
    try:
        action = PowerAction.objects.get(id=action_id, session__user=request.user)
        # Toggle status
        if action.status == 'DRAFT':
            action.status = 'SCHEDULED'
        elif action.status == 'SCHEDULED':
            action.status = 'DONE'
        elif action.status == 'DONE':
            action.status = 'SCHEDULED'
        action.save()
        return JsonResponse({
            'success': True,
            'new_status': action.status,
            'is_completed': action.status == 'DONE'
        })
    except PowerAction.DoesNotExist:
        pass

    # 2. Try FocusTask
    try:
        task = FocusTask.objects.get(id=action_id, session__user=request.user)
        task.is_completed = not task.is_completed
        task.save()
        return JsonResponse({
            'success': True,
            'new_status': 'DONE' if task.is_completed else 'SCHEDULED',
            'is_completed': task.is_completed
        })
    except FocusTask.DoesNotExist:
        return JsonResponse({'error': 'Action not found'}, status=404)


@login_required
@require_http_methods(["POST"])
def update_micro_step(request, action_id, step_index):
    """
    API endpoint: Toggle a specific micro-step completion.
    Used in dashboard widget to check off micro-steps.
    """
    # 1. Try PowerAction
    try:
        action = PowerAction.objects.get(id=action_id, session__user=request.user)
        if step_index < 0 or step_index >= len(action.micro_steps):
            return JsonResponse({'success': False, 'error': 'Invalid step index'}, status=400)
        
        action.micro_steps[step_index]['done'] = not action.micro_steps[step_index].get('done', False)
        action.save()
        return JsonResponse({
            'success': True,
            'step_done': action.micro_steps[step_index]['done'],
            'progress': action.micro_steps_progress
        })
    except PowerAction.DoesNotExist:
        pass

    # 2. Try FocusTask
    try:
        task = FocusTask.objects.get(id=action_id, session__user=request.user)
        if not task.checklist or step_index < 0 or step_index >= len(task.checklist):
            return JsonResponse({'success': False, 'error': 'Invalid step index'}, status=400)
        
        task.checklist[step_index]['done'] = not task.checklist[step_index].get('done', False)
        task.save()
        
        # Calculate progress manually for FocusTask
        total = len(task.checklist)
        done = sum(1 for item in task.checklist if item.get('done'))
        progress = int((done / total) * 100) if total > 0 else 0

        return JsonResponse({
            'success': True,
            'step_done': task.checklist[step_index]['done'],
            'progress': progress
        })
    except FocusTask.DoesNotExist:
        return JsonResponse({'error': 'Action not found'}, status=404)


@login_required
@require_http_methods(["GET"])
def planner_stats(request):
    """
    API endpoint: Get strategic planner statistics.
    - Vision progress
    - Habit streaks
    - Frog completion rate
    - Weekly ritual completion
    """
    # Ritual completion (last 7 days)
    last_7_days = [timezone.now().date() - timedelta(days=i) for i in range(7)]
    rituals_completed = DailyRitualSession.objects.filter(
        user=request.user,
        date__in=last_7_days,
        completed_at__isnull=False
    ).count()
    
    # Frog completion rate (last 30 days)
    last_30_days = timezone.now().date() - timedelta(days=30)
    total_frogs = PowerAction.objects.filter(
        session__user=request.user,
        session__date__gte=last_30_days,
        is_frog=True
    ).count()
    
    completed_frogs = PowerAction.objects.filter(
        session__user=request.user,
        session__date__gte=last_30_days,
        is_frog=True,
        status='DONE'
    ).count()
    
    frog_completion_rate = (completed_frogs / total_frogs * 100) if total_frogs > 0 else 0
    
    # Vision progress
    visions = LifeVision.objects.filter(user=request.user).values('title', 'progress_pct', 'scope')
    
    # Habit streaks (simplified - consecutive days)
    habits = ExecutiveHabit.objects.filter(user=request.user, is_active=True)
    habit_stats = []
    
    for habit in habits:
        # Get last completion
        last_completion = HabitCompletion.objects.filter(
            habit=habit
        ).order_by('-completed_date').first()
        
        # Count completions this month
        this_month_start = timezone.now().date().replace(day=1)
        completions_this_month = HabitCompletion.objects.filter(
            habit=habit,
            completed_date__gte=this_month_start
        ).count()
        
        habit_stats.append({
            'title': habit.title,
            'frequency': habit.frequency,
            'last_completion': last_completion.completed_date.isoformat() if last_completion else None,
            'completions_this_month': completions_this_month
        })
    
    return JsonResponse({
        'rituals_this_week': rituals_completed,
        'frog_completion_rate': round(frog_completion_rate, 1),
        'total_frogs_30d': total_frogs,
        'completed_frogs_30d': completed_frogs,
        'visions': list(visions),
        'habits': habit_stats
    })


# ============================================================================
# AI-ASSISTED PLANNING ENDPOINTS
# ============================================================================

@login_required
@require_http_methods(["POST"])
def ai_process_brain_dump(request):
    """
    AI endpoint: Process brain dump text and categorize tasks.
    
    POST /api/v1/planner/ai/process-dump/
    Body: {
        "text": "Brain dump text...",
        "energy_level": 7
    }
    
    Returns: {
        "high_impact": [...],
        "noise": [...],
        "summary": "..."
    }
    """
    try:
        data = json.loads(request.body)
        text = data.get('text', '')
        
        if not text or not text.strip():
            return JsonResponse({
                'error': 'Brain dump text is required'
            }, status=400)
        
        # Get user context
        visions = list(
            LifeVision.objects.filter(user=request.user)
            .values_list('title', flat=True)[:5]
        )
        
        user_context = {
            'visions': visions,
            'energy_level': data.get('energy_level', 5)
        }
        
        # Process with AI
        result = PlannerAI.process_brain_dump(text, user_context)
        
        return JsonResponse(result)
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error processing brain dump: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST"])
def ai_suggest_frog(request):
    """
    AI endpoint: Suggest which task should be "The Frog".
    
    POST /api/v1/planner/ai/suggest-frog/
    Body: {
        "high_impact_items": [{text: "...", reason: "..."}],
        "energy_level": 7
    }
    
    Returns: {
        "recommended_index": 0,
        "reasoning": "...",
        "alternative": "..."
    }
    """
    try:
        data = json.loads(request.body)
        items = data.get('high_impact_items', [])
        
        if not items:
            return JsonResponse({
                'error': 'No high-impact items provided'
            }, status=400)
        
        user_context = {
            'energy_level': data.get('energy_level', 5)
        }
        
        # Get AI suggestion
        result = PlannerAI.suggest_frog(items, user_context)
        
        return JsonResponse(result)
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error suggesting frog: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST"])
def ai_generate_micro_steps(request):
    """
    AI endpoint: Generate micro-steps for a task.
    
    POST /api/v1/planner/ai/generate-steps/
    Body: {
        "frog_title": "Task title",
        "context": "Optional context"
    }
    
    Returns: {
        "micro_steps": [
            {text: "Step 1", done: false},
            ...
        ]
    }
    """
    try:
        data = json.loads(request.body)
        frog_title = data.get('frog_title', '')
        
        if not frog_title or not frog_title.strip():
            return JsonResponse({
                'error': 'Frog title is required'
            }, status=400)
        
        context = data.get('context', '')
        
        # Generate steps with AI
        micro_steps = PlannerAI.generate_micro_steps(frog_title, context)
        
        return JsonResponse({
            'micro_steps': micro_steps
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error generating micro-steps: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST"])
def ai_suggest_time_blocks(request):
    """
    AI endpoint: Suggest optimal time blocks.
    
    POST /api/v1/planner/ai/suggest-time/
    Body: {
        "frog_title": "Task title",
        "energy_level": 7,
        "micro_steps": [...]
    }
    
    Returns: {
        "suggested_start": "09:00",
        "suggested_end": "11:00",
        "reasoning": "..."
    }
    """
    try:
        data = json.loads(request.body)
        frog_title = data.get('frog_title', '')
        energy_level = data.get('energy_level', 5)
        micro_steps = data.get('micro_steps', [])
        
        if not frog_title:
            return JsonResponse({
                'error': 'Frog title is required'
            }, status=400)
        
        # Get AI suggestion
        result = PlannerAI.suggest_time_blocks(frog_title, energy_level, micro_steps)
        
        return JsonResponse(result)
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error suggesting time blocks: {str(e)}'
        }, status=500)

