"""
Task filters for the Kibray API
"""
from django.db import models
from django.utils import timezone
import django_filters

from core.models import Task


class TaskFilter(django_filters.FilterSet):
    """Filter for tasks"""
    title = django_filters.CharFilter(lookup_expr='icontains')
    description = django_filters.CharFilter(lookup_expr='icontains')
    status = django_filters.MultipleChoiceFilter(
        choices=[
            ('Pendiente', 'Pendiente'),
            ('En Progreso', 'En Progreso'),
            ('Completada', 'Completada'),
            ('Cancelada', 'Cancelada'),
        ]
    )
    priority = django_filters.MultipleChoiceFilter(
        choices=[
            ('low', 'Baja'),
            ('medium', 'Media'),
            ('high', 'Alta'),
            ('urgent', 'Urgente'),
        ]
    )
    assigned_to = django_filters.NumberFilter(field_name='assigned_to__id')
    project = django_filters.NumberFilter(field_name='project__id')
    due_date_from = django_filters.DateFilter(field_name='due_date', lookup_expr='gte')
    due_date_to = django_filters.DateFilter(field_name='due_date', lookup_expr='lte')
    is_overdue = django_filters.BooleanFilter(method='filter_overdue')
    created_by = django_filters.NumberFilter(field_name='created_by__id')

    class Meta:
        model = Task
        fields = ['status', 'priority', 'assigned_to', 'project']

    def filter_overdue(self, queryset, name, value):
        """Filter overdue tasks"""
        today = timezone.now().date()

        if value:
            # Overdue: due_date < today AND status != 'Completada'
            return queryset.filter(due_date__lt=today).exclude(status='Completada')
        else:
            # Not overdue: due_date >= today OR status == 'Completada'
            return queryset.filter(
                models.Q(due_date__gte=today) | models.Q(status='Completada')
            )
