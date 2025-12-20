"""
Project filters for the Kibray API
"""
from django.db import models
import django_filters

from core.models import Project


class ProjectFilter(django_filters.FilterSet):
    """Filter for projects"""
    name = django_filters.CharFilter(lookup_expr='icontains')
    billing_organization = django_filters.NumberFilter(field_name='billing_organization__id')
    project_lead = django_filters.NumberFilter(field_name='project_lead__id')
    start_date_from = django_filters.DateFilter(field_name='start_date', lookup_expr='gte')
    start_date_to = django_filters.DateFilter(field_name='start_date', lookup_expr='lte')
    end_date_from = django_filters.DateFilter(field_name='end_date', lookup_expr='gte')
    end_date_to = django_filters.DateFilter(field_name='end_date', lookup_expr='lte')
    client = django_filters.CharFilter(lookup_expr='icontains')
    is_active = django_filters.BooleanFilter(method='filter_active')

    class Meta:
        model = Project
        fields = ['name', 'billing_organization', 'project_lead', 'client']

    def filter_active(self, queryset, name, value):
        """Filter active/inactive projects based on dates"""
        from django.utils import timezone
        today = timezone.now().date()

        if value:
            # Active: start_date <= today AND (end_date is None OR end_date >= today)
            return queryset.filter(start_date__lte=today).filter(
                models.Q(end_date__isnull=True) | models.Q(end_date__gte=today)
            )
        else:
            # Inactive: end_date < today
            return queryset.filter(end_date__lt=today)
