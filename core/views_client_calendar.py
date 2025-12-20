"""
Client Calendar View
Vista de calendario dedicada para clientes que muestra el cronograma
del proyecto de forma visual, limpia y fácil de entender.
"""

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone

from .models import Project, ScheduleItem


@login_required
def client_project_calendar_view(request, project_id):
    """
    Calendar view específica para clientes.
    Muestra cronograma del proyecto de forma hermosa y simple.
    Solo información relevante para el cliente (sin costos, notas internas).
    """
    project = get_object_or_404(Project, id=project_id)

    # Verificar que el cliente tiene acceso al proyecto
    profile = getattr(request.user, 'profile', None)

    # Permitir acceso a:
    # 1. Cliente del proyecto
    # 2. Staff/Admin
    # 3. PM asignado
    has_access = False

    if request.user.is_staff or request.user.is_superuser:
        has_access = True
    elif profile:
        if profile.role == 'client' and project.client and project.client.user == request.user:
            has_access = True
        elif profile.role == 'project_manager' and project.pm_assignments.filter(user=request.user).exists():
            # Verificar si es PM del proyecto
            has_access = True

    if not has_access:
        return HttpResponseForbidden("No tienes acceso a este calendario.")

    # Obtener milestones y fases principales (información visible para cliente)
    schedule_items = project.schedule_items.select_related(
        'category'
    ).order_by('planned_start')

    # Obtener categorías (fases del proyecto)
    categories = project.schedule_categories.filter(
        parent__isnull=True  # Solo categorías de nivel superior
    ).order_by('order')

    # Calcular estadísticas del proyecto
    today = timezone.localdate()
    total_items = schedule_items.count()
    completed_items = schedule_items.filter(status='DONE').count()
    in_progress_items = schedule_items.filter(status='IN_PROGRESS').count()

    overall_progress = int(completed_items / total_items * 100) if total_items > 0 else 0

    # Calcular días restantes
    days_remaining = (project.end_date - today).days if project.end_date else None

    # Preparar datos para el template
    context = {
        'project': project,
        'categories': categories,
        'schedule_items': schedule_items,
        'overall_progress': overall_progress,
        'completed_items': completed_items,
        'in_progress_items': in_progress_items,
        'total_items': total_items,
        'days_remaining': days_remaining,
        'title': f'Cronograma - {project.name}',
        'today': today,
    }

    return render(request, 'core/client_project_calendar.html', context)


@login_required
def client_calendar_api_data(request, project_id):
    """
    API endpoint que devuelve datos del calendario en formato JSON
    para FullCalendar.js
    """
    project = get_object_or_404(Project, id=project_id)

    # Verificar acceso (mismo check que la vista principal)
    profile = getattr(request.user, 'profile', None)
    has_access = False

    if request.user.is_staff or request.user.is_superuser:
        has_access = True
    elif profile:
        has_access = (
            (profile.role == 'client' and project.client and project.client.user == request.user)
            or (profile.role == 'project_manager' and project.pm_assignments.filter(user=request.user).exists())
        )

    if not has_access:
        return JsonResponse({'error': 'No autorizado'}, status=403)

    # Obtener schedule items
    schedule_items = project.schedule_items.select_related('category')

    # Preparar eventos para FullCalendar
    events = []

    for item in schedule_items:
        # Color según estado
        if item.status == 'DONE':
            color = '#28a745'  # Verde - Completado
            text_color = 'white'
        elif item.status == 'IN_PROGRESS':
            color = '#ffc107'  # Amarillo - En progreso
            text_color = '#000'
        elif item.status == 'BLOCKED':
            color = '#dc3545'  # Rojo - Bloqueado
            text_color = 'white'
        else:  # NOT_STARTED
            color = '#6c757d'  # Gris - No iniciado
            text_color = 'white'

        # Icono según si es milestone
        icon = '🎯' if item.is_milestone else '📋'

        event = {
            'id': item.id,
            'title': f"{icon} {item.title}",
            'start': item.planned_start.isoformat() if item.planned_start else None,
            'end': item.planned_end.isoformat() if item.planned_end else None,
            'backgroundColor': color,
            'borderColor': color,
            'textColor': text_color,
            'extendedProps': {
                'description': item.description,
                'status': item.get_status_display(),
                'progress': item.percent_complete,
                'category': item.category.name if item.category else None,
                'is_milestone': item.is_milestone,
                # NO incluir: cost_code, estimate_line, internal_notes
            }
        }

        # Solo agregar eventos con fechas válidas
        if event['start']:
            events.append(event)

    return JsonResponse({
        'events': events,
        'project': {
            'name': project.name,
            'start_date': project.start_date.isoformat() if project.start_date else None,
            'end_date': project.end_date.isoformat() if project.end_date else None,
        }
    })


@login_required
def client_calendar_milestone_detail(request, item_id):
    """
    Vista AJAX que devuelve detalles de un milestone/item
    para mostrar en modal o popover.
    """
    item = get_object_or_404(ScheduleItem, id=item_id)

    # Verificar acceso al proyecto
    project = item.project
    profile = getattr(request.user, 'profile', None)
    has_access = False

    if request.user.is_staff or request.user.is_superuser:
        has_access = True
    elif profile:
        has_access = (
            (profile.role == 'client' and project.client and project.client.user == request.user)
            or (profile.role == 'project_manager' and project.pm_assignments.filter(user=request.user).exists())
        )

    if not has_access:
        return JsonResponse({'error': 'No autorizado'}, status=403)

    # Obtener tareas vinculadas (si existen)
    tasks = item.tasks.all()

    data = {
        'id': item.id,
        'title': item.title,
        'description': item.description,
        'status': item.get_status_display(),
        'progress': item.percent_complete,
        'is_milestone': item.is_milestone,
        'planned_start': item.planned_start.isoformat() if item.planned_start else None,
        'planned_end': item.planned_end.isoformat() if item.planned_end else None,
        'actual_start': item.actual_start.isoformat() if item.actual_start else None,
        'actual_end': item.actual_end.isoformat() if item.actual_end else None,
        'category': item.category.name if item.category else None,
        'tasks': [
            {
                'id': task.id,
                'title': task.title,
                'status': task.status,
                'priority': task.priority,
            }
            for task in tasks[:5]  # Máximo 5 tareas
        ],
        'tasks_count': tasks.count(),
    }

    return JsonResponse(data)
