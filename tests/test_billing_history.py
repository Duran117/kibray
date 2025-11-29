"""
Tests for Change Order billing history view.
"""
import pytest
from datetime import date, datetime, time
from decimal import Decimal
from django.urls import reverse
from core.models import (
    Project, ChangeOrder, Employee, CostCode, TimeEntry, 
    Expense, Invoice, InvoiceLine
)


@pytest.fixture
def project(db):
    """Create a test project."""
    return Project.objects.create(
        name="Test Project",
        client="Test Client",
        start_date=date(2024, 1, 1),
        budget_labor=Decimal("100000.00"),
        budget_materials=Decimal("50000.00")
    )


@pytest.fixture
def employee(db, django_user_model):
    """Create a test employee."""
    user = django_user_model.objects.create_user(
        username="testemployee",
        email="test@example.com",
        password="testpass123"
    )
    return Employee.objects.create(user=user, hourly_rate=Decimal("50.00"))


@pytest.fixture
def cost_code(db):
    """Create a test cost code."""
    return CostCode.objects.create(code="TEST-001")


@pytest.fixture
def tm_change_order(db, project):
    """Create a T&M Change Order."""
    return ChangeOrder.objects.create(
        project=project,
        description="T&M Change Order",
        amount=Decimal("0.00"),
        pricing_type='T_AND_M',
        billing_hourly_rate=Decimal("75.00"),
        material_markup_pct=Decimal("20.00"),
        status='billed'
    )


@pytest.fixture
def invoice(db, project):
    """Create a test invoice."""
    return Invoice.objects.create(
        project=project,
        total_amount=Decimal("1000.00"),
        status='SENT'
    )


@pytest.mark.django_db
class TestBillingHistoryView:
    """Tests for the billing history view."""

    def test_billing_history_view_accessible(self, client, django_user_model, tm_change_order):
        """Test that billing history view is accessible."""
        user = django_user_model.objects.create_user(
            username="testuser",
            password="testpass123"
        )
        client.login(username="testuser", password="testpass123")
        
        url = reverse('changeorder_billing_history', args=[tm_change_order.id])
        response = client.get(url)
        
        assert response.status_code == 200
        assert 'changeorder' in response.context
        assert response.context['changeorder'] == tm_change_order

    def test_billing_history_shows_labor_lines(
        self, client, django_user_model, tm_change_order, invoice, 
        employee, cost_code
    ):
        """Test that billing history correctly displays labor invoice lines."""
        user = django_user_model.objects.create_user(
            username="testuser",
            password="testpass123"
        )
        client.login(username="testuser", password="testpass123")
        
        # Create labor invoice line
        labor_line = InvoiceLine.objects.create(
            invoice=invoice,
            description="Labor - Week 1",
            amount=Decimal("750.00"),
            time_entry=None  # Will be set below
        )
        
        # Create time entries linked to this invoice line
        time_entry = TimeEntry.objects.create(
            employee=employee,
            project=tm_change_order.project,
            change_order=tm_change_order,
            cost_code=cost_code,
            date=date(2024, 1, 10),
            hours_worked=Decimal("10.00"),
            cost_rate_snapshot=Decimal("50.00"),
            start_time=datetime.combine(date(2024, 1, 10), time(8, 0)),
            end_time=datetime.combine(date(2024, 1, 10), time(18, 0)),
            invoice_line=None  # invoice_line doesn't exist on TimeEntry
        )
        
        # Link the time entry to the invoice line
        labor_line.time_entry = time_entry
        labor_line.save()
        
        url = reverse('changeorder_billing_history', args=[tm_change_order.id])
        response = client.get(url)
        
        assert response.status_code == 200
        assert len(response.context['labor_lines']) == 1
        assert response.context['labor_lines'][0]['invoice_line'] == labor_line
        assert response.context['labor_lines'][0]['time_entries'] == [time_entry]

    def test_billing_history_shows_material_lines(
        self, client, django_user_model, tm_change_order, invoice
    ):
        """Test that billing history correctly displays material invoice lines."""
        user = django_user_model.objects.create_user(
            username="testuser",
            password="testpass123"
        )
        client.login(username="testuser", password="testpass123")
        
        # Create material invoice line
        material_line = InvoiceLine.objects.create(
            invoice=invoice,
            description="Materials - Paint & Supplies",
            amount=Decimal("1200.00"),
            expense=None  # Will be set below
        )
        
        # Create expense linked to this invoice line
        expense = Expense.objects.create(
            project=tm_change_order.project,
            change_order=tm_change_order,
            description="Paint supplies",
            amount=Decimal("1000.00"),
            category="Materials",
            date=date(2024, 1, 15),
            invoice_line=None  # invoice_line doesn't exist on Expense
        )
        
        # Link the expense to the invoice line
        material_line.expense = expense
        material_line.save()
        
        url = reverse('changeorder_billing_history', args=[tm_change_order.id])
        response = client.get(url)
        
        assert response.status_code == 200
        assert len(response.context['material_lines']) == 1
        assert response.context['material_lines'][0]['invoice_line'] == material_line
        assert response.context['material_lines'][0]['expenses'] == [expense]

    def test_billing_history_calculates_totals_correctly(
        self, client, django_user_model, tm_change_order, invoice,
        employee, cost_code
    ):
        """Test that billing history calculates totals correctly."""
        user = django_user_model.objects.create_user(
            username="testuser",
            password="testpass123"
        )
        client.login(username="testuser", password="testpass123")
        
        # Create labor line with time entry
        labor_line = InvoiceLine.objects.create(
            invoice=invoice,
            description="Labor",
            amount=Decimal("750.00")
        )
        time_entry = TimeEntry.objects.create(
            employee=employee,
            project=tm_change_order.project,
            change_order=tm_change_order,
            cost_code=cost_code,
            date=date(2024, 1, 10),
            hours_worked=Decimal("10.00"),
            start_time=datetime.combine(date(2024, 1, 10), time(8, 0)),
            end_time=datetime.combine(date(2024, 1, 10), time(18, 0))
        )
        labor_line.time_entry = time_entry
        labor_line.save()
        
        # Create material line with expense
        material_line = InvoiceLine.objects.create(
            invoice=invoice,
            description="Materials",
            amount=Decimal("1200.00")
        )
        expense = Expense.objects.create(
            project=tm_change_order.project,
            change_order=tm_change_order,
            description="Paint",
            amount=Decimal("1000.00"),
            date=date(2024, 1, 15)
        )
        material_line.expense = expense
        material_line.save()
        
        url = reverse('changeorder_billing_history', args=[tm_change_order.id])
        response = client.get(url)
        
        assert response.status_code == 200
        assert response.context['grand_total'] == Decimal("1950.00")

    def test_billing_history_empty_state(
        self, client, django_user_model, tm_change_order
    ):
        """Test billing history shows empty state when no invoices exist."""
        user = django_user_model.objects.create_user(
            username="testuser",
            password="testpass123"
        )
        client.login(username="testuser", password="testpass123")
        
        url = reverse('changeorder_billing_history', args=[tm_change_order.id])
        response = client.get(url)
        
        assert response.status_code == 200
        assert len(response.context['labor_lines']) == 0
        assert len(response.context['material_lines']) == 0
        assert response.context['grand_total'] == 0

    def test_billing_history_requires_login(self, client, tm_change_order):
        """Test that billing history requires authentication."""
        url = reverse('changeorder_billing_history', args=[tm_change_order.id])
        response = client.get(url)
        
        # Should redirect to login
        assert response.status_code == 302
        assert '/login/' in response.url or '/accounts/login/' in response.url
