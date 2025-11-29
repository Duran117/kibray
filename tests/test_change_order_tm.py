"""
Tests for Time & Materials (T&M) Change Order billing logic.
"""
import pytest
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta

from core.models import (
    Project, Employee, ChangeOrder, TimeEntry, Expense,
    CostCode, InvoiceLine, Invoice
)
from core.services.financial_service import ChangeOrderService


@pytest.fixture
def project(db):
    """Create test project with default billing rate."""
    return Project.objects.create(
        project_code='TEST-TM-001',
        name='T&M Test Project',
        client='Test Client',
        start_date=timezone.now().date(),
        end_date=timezone.now().date() + timedelta(days=90),
        budget_total=Decimal('100000.00'),
        default_co_labor_rate=Decimal('50.00')
    )


@pytest.fixture
def employee(db, django_user_model):
    """Create test employee."""
    user = django_user_model.objects.create_user(
        username='testworker',
        password='pass123'
    )
    return Employee.objects.create(
        user=user,
        first_name='Test',
        last_name='Worker',
        hourly_rate=Decimal('25.00')
    )


@pytest.fixture
def cost_code(db):
    """Create test cost code."""
    return CostCode.objects.create(
        code='LAB-001',
        name='Labor - General',
        category='labor',
        active=True
    )


@pytest.mark.django_db
class TestChangeOrderValidation:
    """Test ChangeOrder model validation for T&M."""
    
    def test_fixed_co_allows_nonzero_amount(self, project):
        """Fixed price COs can have any amount."""
        co = ChangeOrder(
            project=project,
            description='Fixed CO',
            pricing_type='FIXED',
            amount=Decimal('5000.00'),
            status='draft'
        )
        co.clean()  # Should not raise
        co.save()
        assert co.amount == Decimal('5000.00')
    
    def test_tm_co_requires_zero_amount(self, project):
        """T&M COs must have amount=0."""
        from django.core.exceptions import ValidationError
        co = ChangeOrder(
            project=project,
            description='T&M CO',
            pricing_type='T_AND_M',
            amount=Decimal('1000.00'),
            billing_hourly_rate=Decimal('65.00'),
            status='draft'
        )
        with pytest.raises(ValidationError) as exc_info:
            co.clean()
        assert 'amount' in exc_info.value.message_dict
        assert 'Tiempo y Materiales' in str(exc_info.value)
    
    def test_tm_co_accepts_zero_amount(self, project):
        """T&M COs with amount=0 pass validation."""
        co = ChangeOrder(
            project=project,
            description='T&M CO',
            pricing_type='T_AND_M',
            amount=Decimal('0.00'),
            billing_hourly_rate=Decimal('65.00'),
            status='draft'
        )
        co.clean()  # Should not raise
        co.save()
        assert co.amount == Decimal('0.00')


@pytest.mark.django_db
class TestChangeOrderService:
    """Test ChangeOrderService billing calculations."""
    
    def test_fixed_co_returns_simple_total(self, project):
        """FIXED COs return straightforward amount."""
        co = ChangeOrder.objects.create(
            project=project,
            description='Fixed CO',
            pricing_type='FIXED',
            amount=Decimal('5000.00'),
            status='approved'
        )
        result = ChangeOrderService.get_billable_amount(co)
        assert result['type'] == 'FIXED'
        assert result['total'] == Decimal('5000.00')
    
    def test_tm_co_no_entries_returns_zero(self, project):
        """T&M CO with no TimeEntries/Expenses returns zero."""
        co = ChangeOrder.objects.create(
            project=project,
            description='T&M CO Empty',
            pricing_type='T_AND_M',
            amount=Decimal('0.00'),
            billing_hourly_rate=Decimal('65.00'),
            material_markup_pct=Decimal('20.00'),
            status='approved'
        )
        result = ChangeOrderService.get_billable_amount(co)
        assert result['type'] == 'T_AND_M'
        assert result['labor_hours'] == Decimal('0')
        assert result['labor_total'] == Decimal('0.00')
        assert result['raw_material_cost'] == Decimal('0.00')
        assert result['material_total'] == Decimal('0.00')
        assert result['grand_total'] == Decimal('0.00')
    
    def test_tm_co_calculates_labor_correctly(self, project, employee, cost_code):
        """T&M CO computes labor from unbilled TimeEntries."""
        co = ChangeOrder.objects.create(
            project=project,
            description='T&M CO Labor',
            pricing_type='T_AND_M',
            amount=Decimal('0.00'),
            billing_hourly_rate=Decimal('70.00'),
            status='approved'
        )
        # Create 10 hours of work
        TimeEntry.objects.create(
            employee=employee,
            project=project,
            change_order=co,
            date=timezone.now().date(),
            start_time=timezone.now().time(),
            end_time=(timezone.now() + timedelta(hours=5)).time(),
            hours_worked=Decimal('5.00'),
            cost_code=cost_code
        )
        TimeEntry.objects.create(
            employee=employee,
            project=project,
            change_order=co,
            date=timezone.now().date(),
            start_time=timezone.now().time(),
            end_time=(timezone.now() + timedelta(hours=5)).time(),
            hours_worked=Decimal('5.00'),
            cost_code=cost_code
        )
        
        result = ChangeOrderService.get_billable_amount(co)
        assert result['labor_hours'] == Decimal('10.00')
        assert result['labor_total'] == Decimal('700.00')  # 10 * 70
        assert result['billing_rate'] == Decimal('70.00')
    
    def test_tm_co_calculates_materials_with_markup(self, project):
        """T&M CO applies markup to material expenses."""
        co = ChangeOrder.objects.create(
            project=project,
            description='T&M CO Materials',
            pricing_type='T_AND_M',
            amount=Decimal('0.00'),
            billing_hourly_rate=Decimal('60.00'),
            material_markup_pct=Decimal('25.00'),
            status='approved'
        )
        # Add expenses
        Expense.objects.create(
            project=project,
            change_order=co,
            amount=Decimal('1000.00'),
            project_name='Materials',
            date=timezone.now().date(),
            category='MATERIALES'
        )
        Expense.objects.create(
            project=project,
            change_order=co,
            amount=Decimal('500.00'),
            project_name='More Materials',
            date=timezone.now().date(),
            category='MATERIALES'
        )
        
        result = ChangeOrderService.get_billable_amount(co)
        assert result['raw_material_cost'] == Decimal('1500.00')
        # 1500 * 1.25 = 1875
        assert result['material_total'] == Decimal('1875.00')
        assert result['material_markup_pct'] == Decimal('25.00')
    
    def test_tm_co_full_calculation(self, project, employee, cost_code):
        """T&M CO with labor + materials calculates correctly."""
        co = ChangeOrder.objects.create(
            project=project,
            description='T&M CO Full',
            pricing_type='T_AND_M',
            amount=Decimal('0.00'),
            billing_hourly_rate=Decimal('80.00'),
            material_markup_pct=Decimal('30.00'),
            status='approved'
        )
        # 8 hours labor
        TimeEntry.objects.create(
            employee=employee,
            project=project,
            change_order=co,
            date=timezone.now().date(),
            start_time=timezone.now().time(),
            hours_worked=Decimal('8.00'),
            cost_code=cost_code
        )
        # $2000 materials
        Expense.objects.create(
            project=project,
            change_order=co,
            amount=Decimal('2000.00'),
            project_name='Materials',
            date=timezone.now().date(),
            category='MATERIALES'
        )
        
        result = ChangeOrderService.get_billable_amount(co)
        assert result['labor_hours'] == Decimal('8.00')
        assert result['labor_total'] == Decimal('640.00')  # 8 * 80
        assert result['raw_material_cost'] == Decimal('2000.00')
        assert result['material_total'] == Decimal('2600.00')  # 2000 * 1.30
        assert result['grand_total'] == Decimal('3240.00')  # 640 + 2600
    
    def test_tm_co_excludes_already_billed_entries(self, project, employee, cost_code):
        """T&M CO excludes TimeEntries/Expenses that already have invoice_line set."""
        co = ChangeOrder.objects.create(
            project=project,
            description='T&M CO Partial',
            pricing_type='T_AND_M',
            amount=Decimal('0.00'),
            billing_hourly_rate=Decimal('50.00'),
            status='approved'
        )
        # Create invoice and line
        invoice = Invoice.objects.create(
            project=project,
            date_issued=timezone.now().date(),
            due_date=timezone.now().date() + timedelta(days=30),
            total_amount=Decimal('0.00'),
            status='DRAFT'
        )
        line = InvoiceLine.objects.create(
            invoice=invoice,
            description='Previous billing',
            amount=Decimal('100.00')
        )
        
        # Already billed
        TimeEntry.objects.create(
            employee=employee,
            project=project,
            change_order=co,
            date=timezone.now().date(),
            start_time=timezone.now().time(),
            hours_worked=Decimal('3.00'),
            cost_code=cost_code,
            invoice_line=line
        )
        # Not yet billed
        TimeEntry.objects.create(
            employee=employee,
            project=project,
            change_order=co,
            date=timezone.now().date(),
            start_time=timezone.now().time(),
            hours_worked=Decimal('5.00'),
            cost_code=cost_code
        )
        
        result = ChangeOrderService.get_billable_amount(co)
        # Should only count the 5 unbilled hours
        assert result['labor_hours'] == Decimal('5.00')
        assert result['labor_total'] == Decimal('250.00')
        assert len(result['time_entries']) == 1
    
    def test_effective_billing_rate_fallback(self, project):
        """get_effective_billing_rate uses fallback hierarchy."""
        # Test 1: billing_hourly_rate set
        co1 = ChangeOrder.objects.create(
            project=project,
            description='Test 1',
            pricing_type='T_AND_M',
            amount=Decimal('0.00'),
            billing_hourly_rate=Decimal('85.00'),
            labor_rate_override=Decimal('70.00')
        )
        assert co1.get_effective_billing_rate() == Decimal('85.00')
        
        # Test 2: billing_hourly_rate=0, use labor_rate_override
        co2 = ChangeOrder.objects.create(
            project=project,
            description='Test 2',
            pricing_type='T_AND_M',
            amount=Decimal('0.00'),
            billing_hourly_rate=Decimal('0.00'),
            labor_rate_override=Decimal('75.00')
        )
        assert co2.get_effective_billing_rate() == Decimal('75.00')
        
        # Test 3: no overrides, use project default
        co3 = ChangeOrder.objects.create(
            project=project,
            description='Test 3',
            pricing_type='T_AND_M',
            amount=Decimal('0.00'),
            billing_hourly_rate=Decimal('0.00')
        )
        assert co3.get_effective_billing_rate() == project.default_co_labor_rate
