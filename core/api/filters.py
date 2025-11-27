"""
Django-filter configurations for the Kibray API

Enables complex filtering on list endpoints for iOS app queries
"""

import django_filters

from core.models import (
    ChangeOrder,
    Expense,
    Income,
    Invoice,
    Project,
    Task,
    TimeEntry,
)


class ProjectFilter(django_filters.FilterSet):
    """
    Filter projects by various criteria

    Examples:
    - /api/projects/?status=active
    - /api/projects/?start_date__gte=2025-01-01
    - /api/projects/?client__icontains=Smith
    """

    name = django_filters.CharFilter(lookup_expr="icontains")
    client = django_filters.CharFilter(lookup_expr="icontains")
    start_date__gte = django_filters.DateFilter(field_name="start_date", lookup_expr="gte")
    start_date__lte = django_filters.DateFilter(field_name="start_date", lookup_expr="lte")
    end_date__gte = django_filters.DateFilter(field_name="end_date", lookup_expr="gte")
    end_date__lte = django_filters.DateFilter(field_name="end_date", lookup_expr="lte")

    class Meta:
        model = Project
        fields = ["name", "client", "start_date", "end_date"]


class TimeEntryFilter(django_filters.FilterSet):
    """
    Filter time entries by employee, project, date range

    Examples:
    - /api/time-entries/?employee=5
    - /api/time-entries/?project=10
    - /api/time-entries/?date__gte=2025-01-01&date__lte=2025-01-31
    """

    employee = django_filters.NumberFilter(field_name="employee__id")
    project = django_filters.NumberFilter(field_name="project__id")
    date__gte = django_filters.DateFilter(field_name="date", lookup_expr="gte")
    date__lte = django_filters.DateFilter(field_name="date", lookup_expr="lte")

    class Meta:
        model = TimeEntry
        fields = ["employee", "project", "date"]


class ExpenseFilter(django_filters.FilterSet):
    """
    Filter expenses by category, project, date range
    """

    project = django_filters.NumberFilter(field_name="project__id")
    category = django_filters.ChoiceFilter(choices=Expense._meta.get_field("category").choices)
    date__gte = django_filters.DateFilter(field_name="date", lookup_expr="gte")
    date__lte = django_filters.DateFilter(field_name="date", lookup_expr="lte")
    amount__gte = django_filters.NumberFilter(field_name="amount", lookup_expr="gte")
    amount__lte = django_filters.NumberFilter(field_name="amount", lookup_expr="lte")

    class Meta:
        model = Expense
        fields = ["project", "category", "date", "amount"]


class IncomeFilter(django_filters.FilterSet):
    """
    Filter incomes by project, payment method, date range
    """

    project = django_filters.NumberFilter(field_name="project__id")
    payment_method = django_filters.ChoiceFilter(choices=Income._meta.get_field("payment_method").choices)
    date__gte = django_filters.DateFilter(field_name="date", lookup_expr="gte")
    date__lte = django_filters.DateFilter(field_name="date", lookup_expr="lte")

    class Meta:
        model = Income
        fields = ["project", "payment_method", "date"]


class TaskFilter(django_filters.FilterSet):
    """
    Filter tasks by status, assignment, project
    """

    project = django_filters.NumberFilter(field_name="project__id")
    assigned_to = django_filters.NumberFilter(field_name="assigned_to__id")
    status = django_filters.CharFilter(field_name="status")
    is_touchup = django_filters.BooleanFilter()

    class Meta:
        model = Task
        fields = ["project", "assigned_to", "status", "is_touchup"]


class ChangeOrderFilter(django_filters.FilterSet):
    """
    Filter change orders by project, status
    """

    project = django_filters.NumberFilter(field_name="project__id")
    status = django_filters.CharFilter(field_name="status")

    class Meta:
        model = ChangeOrder
        fields = ["project", "status"]


class InvoiceFilter(django_filters.FilterSet):
    """
    Filter invoices by project, status, date_issued
    """

    project = django_filters.NumberFilter(field_name="project__id")
    status = django_filters.CharFilter(field_name="status")
    date_issued__gte = django_filters.DateFilter(field_name="date_issued", lookup_expr="gte")
    date_issued__lte = django_filters.DateFilter(field_name="date_issued", lookup_expr="lte")

    class Meta:
        model = Invoice
        fields = ["project", "status"]
