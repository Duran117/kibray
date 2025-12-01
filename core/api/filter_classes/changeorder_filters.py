"""
ChangeOrder filters for the Kibray API
"""
import django_filters
from core.models import ChangeOrder


class ChangeOrderFilter(django_filters.FilterSet):
    """Filter for change orders"""
    reference_code = django_filters.CharFilter(field_name='reference_code', lookup_expr='icontains')
    status = django_filters.MultipleChoiceFilter(
        choices=[
            ('draft', 'Borrador'),
            ('pending', 'Pendiente'),
            ('approved', 'Aprobado'),
            ('sent', 'Enviado'),
            ('billed', 'Facturado'),
            ('paid', 'Pagado'),
        ]
    )
    project = django_filters.NumberFilter(field_name='project__id')
    amount_min = django_filters.NumberFilter(field_name='amount', lookup_expr='gte')
    amount_max = django_filters.NumberFilter(field_name='amount', lookup_expr='lte')
    submitted_date_from = django_filters.DateFilter(field_name='date_created', lookup_expr='gte')
    submitted_date_to = django_filters.DateFilter(field_name='date_created', lookup_expr='lte')
    
    class Meta:
        model = ChangeOrder
        fields = ['status', 'project']
