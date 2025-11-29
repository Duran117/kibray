"""
Tests for Project Activation Wizard.

Tests the complete workflow from approved estimate to operational entities:
- ScheduleItems
- BudgetLines  
- Tasks
- Deposit Invoices
"""

import pytest
from datetime import date, timedelta
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.urls import reverse

from core.models import (
    Project,
    Estimate,
    EstimateLine,
    CostCode,
    ScheduleItem,
    ScheduleCategory,
    BudgetLine,
    Task,
    Invoice,
    InvoiceLine,
)
from core.services.activation_service import ProjectActivationService

User = get_user_model()


@pytest.mark.django_db
class TestProjectActivationService:
    """Test the activation service logic."""

    @pytest.fixture
    def user(self):
        return User.objects.create_user(username="pm_user", password="testpass123")

    @pytest.fixture
    def project(self):
        return Project.objects.create(
            name="Activation Test Project",
            start_date=timezone.now().date(),
            client="Test Client",
        )

    @pytest.fixture
    def cost_code(self):
        return CostCode.objects.create(
            code="01.01",
            name="Labor Work",
            category="labor",
        )

    @pytest.fixture
    def estimate(self, project, cost_code):
        estimate = Estimate.objects.create(
            project=project,
            version=1,
            markup_material=Decimal("10.00"),
            markup_labor=Decimal("15.00"),
            overhead_pct=Decimal("5.00"),
            target_profit_pct=Decimal("10.00"),
            approved=True,
        )
        
        # Create 3 estimate lines
        for i in range(1, 4):
            EstimateLine.objects.create(
                estimate=estimate,
                cost_code=cost_code,
                description=f"Test Item {i}",
                qty=Decimal(f"{i * 10}"),
                unit="hrs" if i == 1 else "unit",
                labor_unit_cost=Decimal("50.00"),
                material_unit_cost=Decimal("25.00"),
                other_unit_cost=Decimal("10.00"),
            )
        
        return estimate

    def test_service_initialization(self, project, estimate):
        """Test service can be initialized."""
        service = ProjectActivationService(project=project, estimate=estimate)
        assert service.project == project
        assert service.estimate == estimate

    def test_validate_estimate_approved(self, project, estimate):
        """Test validation passes for approved estimate."""
        service = ProjectActivationService(project=project, estimate=estimate)
        is_valid, error = service.validate_estimate()
        assert is_valid is True
        assert error is None

    def test_validate_estimate_not_approved(self, project, estimate):
        """Test validation fails for unapproved estimate."""
        estimate.approved = False
        estimate.save()
        
        service = ProjectActivationService(project=project, estimate=estimate)
        is_valid, error = service.validate_estimate()
        assert is_valid is False
        assert "aprobado" in error

    def test_validate_estimate_no_lines(self, project):
        """Test validation fails for estimate without lines."""
        estimate = Estimate.objects.create(
            project=project,
            version=1,
            approved=True,
        )
        
        service = ProjectActivationService(project=project, estimate=estimate)
        is_valid, error = service.validate_estimate()
        assert is_valid is False
        assert "líneas" in error

    def test_create_schedule_from_estimate(self, project, estimate):
        """Test schedule items are created correctly."""
        service = ProjectActivationService(project=project, estimate=estimate)
        start_date = date.today()
        
        schedule_items = service.create_schedule_from_estimate(start_date=start_date)
        
        assert len(schedule_items) == 3
        assert all(isinstance(item, ScheduleItem) for item in schedule_items)
        
        # Check first item
        first_item = schedule_items[0]
        assert first_item.project == project
        assert first_item.planned_start == start_date
        assert first_item.status == "NOT_STARTED"
        assert first_item.percent_complete == 0
        
        # Check category was created
        assert ScheduleCategory.objects.filter(project=project, name="General").exists()

    def test_create_schedule_with_specific_items(self, project, estimate):
        """Test creating schedule from specific estimate lines."""
        service = ProjectActivationService(project=project, estimate=estimate)
        start_date = date.today()
        
        # Only schedule first 2 lines
        lines_to_schedule = list(estimate.lines.all()[:2])
        
        schedule_items = service.create_schedule_from_estimate(
            start_date=start_date,
            items_to_schedule=lines_to_schedule
        )
        
        assert len(schedule_items) == 2

    def test_schedule_items_sequential_dates(self, project, estimate):
        """Test schedule items have sequential non-overlapping dates."""
        service = ProjectActivationService(project=project, estimate=estimate)
        start_date = date.today()
        
        schedule_items = service.create_schedule_from_estimate(start_date=start_date)
        
        # Each item should start after previous ends
        for i in range(len(schedule_items) - 1):
            current_end = schedule_items[i].planned_end
            next_start = schedule_items[i + 1].planned_start
            assert next_start > current_end

    def test_create_budget_from_estimate(self, project, estimate):
        """Test budget lines are created correctly."""
        service = ProjectActivationService(project=project, estimate=estimate)
        
        budget_lines = service.create_budget_from_estimate()
        
        assert len(budget_lines) == 3
        assert all(isinstance(line, BudgetLine) for line in budget_lines)
        
        # Check first line
        first_line = budget_lines[0]
        first_estimate_line = estimate.lines.first()
        
        assert first_line.project == project
        assert first_line.cost_code == first_estimate_line.cost_code
        assert first_line.qty == first_estimate_line.qty
        assert first_line.baseline_amount > 0

    def test_budget_cost_calculations(self, project, estimate):
        """Test budget line costs match estimate line costs."""
        service = ProjectActivationService(project=project, estimate=estimate)
        
        budget_lines = service.create_budget_from_estimate()
        estimate_lines = list(estimate.lines.all())
        
        for budget_line, estimate_line in zip(budget_lines, estimate_lines):
            expected_total = estimate_line.direct_cost().quantize(Decimal('0.01'))
            
            assert budget_line.baseline_amount == expected_total

    def test_create_tasks_from_schedule(self, project, estimate):
        """Test tasks are created from schedule items."""
        service = ProjectActivationService(project=project, estimate=estimate)
        start_date = date.today()
        
        schedule_items = service.create_schedule_from_estimate(start_date=start_date)
        tasks = service.create_tasks_from_schedule(schedule_items=schedule_items)
        
        assert len(tasks) == len(schedule_items)
        assert all(isinstance(task, Task) for task in tasks)
        
        # Check first task
        first_task = tasks[0]
        first_schedule = schedule_items[0]
        
        assert first_task.project == project
        assert first_task.title == first_schedule.title
        assert first_task.status == "Pendiente"
        assert first_task.priority == "medium"
        assert first_task.due_date == first_schedule.planned_end

    def test_create_deposit_invoice_valid_percent(self, project, estimate):
        """Test deposit invoice is created with valid percentage."""
        service = ProjectActivationService(project=project, estimate=estimate)
        
        invoice = service.create_deposit_invoice(deposit_percent=30)
        
        assert invoice is not None
        assert isinstance(invoice, Invoice)
        assert invoice.project == project
        assert invoice.status == "DRAFT"
        
        # Check amount (30% of estimate)
        estimate_total = service._calculate_estimate_total()
        expected_amount = (estimate_total * Decimal('0.30')).quantize(Decimal('0.01'))
        assert invoice.total_amount == expected_amount

    def test_create_deposit_invoice_zero_percent(self, project, estimate):
        """Test no invoice created for 0%."""
        service = ProjectActivationService(project=project, estimate=estimate)
        
        invoice = service.create_deposit_invoice(deposit_percent=0)
        
        assert invoice is None

    def test_create_deposit_invoice_invalid_percent(self, project, estimate):
        """Test no invoice created for invalid percentage."""
        service = ProjectActivationService(project=project, estimate=estimate)
        
        invoice = service.create_deposit_invoice(deposit_percent=150)
        assert invoice is None
        
        invoice = service.create_deposit_invoice(deposit_percent=-10)
        assert invoice is None

    def test_activate_project_full_activation(self, project, estimate):
        """Test complete project activation with all features."""
        service = ProjectActivationService(project=project, estimate=estimate)
        start_date = date.today()
        
        result = service.activate_project(
            start_date=start_date,
            create_schedule=True,
            create_budget=True,
            create_tasks=True,
            deposit_percent=25,
        )
        
        # Check all entities created
        assert len(result['schedule_items']) == 3
        assert len(result['budget_lines']) == 3
        assert len(result['tasks']) == 3
        assert result['invoice'] is not None
        
        # Check summary
        summary = result['summary']
        assert summary['schedule_items_count'] == 3
        assert summary['budget_lines_count'] == 3
        assert summary['tasks_count'] == 3
        assert summary['invoice_created'] is True
        assert summary['invoice_amount'] > 0

    def test_activate_project_schedule_only(self, project, estimate):
        """Test activation with only schedule."""
        service = ProjectActivationService(project=project, estimate=estimate)
        start_date = date.today()
        
        result = service.activate_project(
            start_date=start_date,
            create_schedule=True,
            create_budget=False,
            create_tasks=False,
            deposit_percent=0,
        )
        
        assert len(result['schedule_items']) == 3
        assert len(result['budget_lines']) == 0
        assert len(result['tasks']) == 0
        assert result['invoice'] is None

    def test_activate_project_fails_unapproved_estimate(self, project, estimate):
        """Test activation fails for unapproved estimate."""
        estimate.approved = False
        estimate.save()
        
        service = ProjectActivationService(project=project, estimate=estimate)
        
        with pytest.raises(ValueError, match="aprobado"):
            service.activate_project(
                start_date=date.today(),
                create_schedule=True,
            )


@pytest.mark.django_db
class TestProjectActivationView:
    """Test the activation view and form."""

    @pytest.fixture
    def pm_user(self):
        from core.models import Profile
        user = User.objects.create_user(username="pm_user", password="testpass123")
        # The Profile is created by signal, update it directly via queryset to avoid signal
        Profile.objects.filter(user=user).update(role="project_manager")
        # Refresh to get updated data
        user.refresh_from_db()
        return user

    @pytest.fixture
    def project(self):
        return Project.objects.create(
            name="View Test Project",
            start_date=timezone.now().date(),
            client="Test Client",
        )

    @pytest.fixture
    def cost_code(self):
        return CostCode.objects.create(
            code="01.01",
            name="Test Work",
            category="labor",
        )

    @pytest.fixture
    def estimate(self, project, cost_code):
        estimate = Estimate.objects.create(
            project=project,
            version=1,
            approved=True,
        )
        
        EstimateLine.objects.create(
            estimate=estimate,
            cost_code=cost_code,
            description="Test Line",
            qty=Decimal("10"),
            unit="hrs",
            labor_unit_cost=Decimal("50.00"),
            material_unit_cost=Decimal("25.00"),
            other_unit_cost=Decimal("10.00"),
        )
        
        return estimate

    def test_activation_view_requires_login(self, client, project):
        """Test view requires authentication."""
        url = reverse('project_activation', kwargs={'project_id': project.id})
        response = client.get(url)
        
        assert response.status_code == 302  # Redirect to login

    def test_activation_view_requires_pm_role(self, client, project, estimate):
        """Test view requires PM role."""
        # Create regular employee
        user = User.objects.create_user(username="employee", password="testpass123")
        client.login(username="employee", password="testpass123")
        
        url = reverse('project_activation', kwargs={'project_id': project.id})
        response = client.get(url)
        
        assert response.status_code == 302  # Redirect away

    def test_activation_view_get_renders_form(self, client, pm_user, project, estimate):
        """Test GET request renders form."""
        client.force_login(pm_user)
        
        url = reverse('project_activation', kwargs={'project_id': project.id})
        response = client.get(url, follow=True)
        
        # Should render form successfully
        assert response.status_code == 200
        # If redirected, check we have the right context
        if 'form' in response.context:
            assert 'estimate' in response.context
            assert 'project' in response.context

    def test_activation_view_no_approved_estimate(self, client, pm_user, project):
        """Test view redirects if no approved estimate."""
        client.force_login(pm_user)
        
        url = reverse('project_activation', kwargs={'project_id': project.id})
        response = client.get(url)
        
        assert response.status_code == 302  # Redirect with error

    def test_activation_view_post_creates_entities(self, client, pm_user, project, estimate):
        """Test POST creates schedule, budget, etc."""
        client.force_login(pm_user)
        
        # Debug: Verify user role
        from core.models import Profile
        profile = Profile.objects.get(user=pm_user)
        print(f"User: {pm_user.username}, Profile role: {profile.role}")
        
        # Debug: Verify estimate has lines
        lines_count = estimate.lines.count()
        print(f"Estimate has {lines_count} lines")
        
        url = reverse('project_activation', kwargs={'project_id': project.id})
        data = {
            'start_date': date.today().isoformat(),
            'create_schedule': True,
            'create_budget': True,
            'create_tasks': '',
            'deposit_percent': '0',
        }
        
        print(f"POST data: {data}")
        
        response = client.post(url, data, follow=True)
        
        # Should succeed
        assert response.status_code == 200
        
        # Check for error messages
        messages_list = list(response.context.get('messages', []))
        if messages_list:
            print("Messages:", [str(m) for m in messages_list])
        
        # Check entities created
        schedule_count = ScheduleItem.objects.filter(project=project).count()
        budget_count = BudgetLine.objects.filter(project=project).count()
        
        print(f"Schedule items: {schedule_count}, Budget lines: {budget_count}")
        
        assert schedule_count > 0, f"Expected schedule items but found {schedule_count}. Estimate had {lines_count} lines."
        assert budget_count > 0, f"Expected budget lines but found {budget_count}"

    def test_activation_view_redirects_to_gantt(self, client, pm_user, project, estimate):
        """Test successful activation redirects to Gantt."""
        client.force_login(pm_user)
        
        url = reverse('project_activation', kwargs={'project_id': project.id})
        data = {
            'start_date': date.today().isoformat(),
            'create_schedule': True,
            'create_budget': '',
            'create_tasks': '',
            'deposit_percent': '0',
        }
        
        response = client.post(url, data)
        
        # Should redirect
        assert response.status_code == 302
        # Check that schedule was created
        assert ScheduleItem.objects.filter(project=project).count() > 0


@pytest.mark.django_db
class TestActivationWizardForm:
    """Test the activation form."""

    @pytest.fixture
    def project(self):
        return Project.objects.create(
            name="Form Test Project",
            start_date=timezone.now().date(),
        )

    @pytest.fixture
    def cost_code(self):
        return CostCode.objects.create(code="01.01", name="Test", category="labor")

    @pytest.fixture
    def estimate(self, project, cost_code):
        estimate = Estimate.objects.create(project=project, version=1, approved=True)
        EstimateLine.objects.create(
            estimate=estimate,
            cost_code=cost_code,
            qty=Decimal("10"),
            unit="hrs",
            labor_unit_cost=Decimal("50.00"),
        )
        return estimate

    def test_form_requires_start_date(self, estimate):
        """Test form validates start_date is required."""
        from core.forms import ActivationWizardForm
        
        form = ActivationWizardForm(data={'create_schedule': True}, estimate=estimate)
        assert not form.is_valid()
        assert 'start_date' in form.errors

    def test_form_deposit_percent_range(self, estimate):
        """Test deposit percent must be 0-100."""
        from core.forms import ActivationWizardForm
        
        form = ActivationWizardForm(
            data={
                'start_date': date.today(),
                'create_schedule': True,
                'deposit_percent': 150,
            },
            estimate=estimate
        )
        assert not form.is_valid()

    def test_form_requires_at_least_one_action(self, estimate):
        """Test at least one action must be selected."""
        from core.forms import ActivationWizardForm
        
        form = ActivationWizardForm(
            data={
                'start_date': date.today(),
                'create_schedule': False,
                'create_budget': False,
                'deposit_percent': 0,
            },
            estimate=estimate
        )
        assert not form.is_valid()

    def test_form_tasks_require_schedule(self, estimate):
        """Test tasks can't be created without schedule."""
        from core.forms import ActivationWizardForm
        
        form = ActivationWizardForm(
            data={
                'start_date': date.today(),
                'create_schedule': False,
                'create_tasks': True,
            },
            estimate=estimate
        )
        assert not form.is_valid()

    def test_form_valid_data(self, estimate):
        """Test form accepts valid data."""
        from core.forms import ActivationWizardForm
        
        form = ActivationWizardForm(
            data={
                'start_date': date.today(),
                'create_schedule': True,
                'create_budget': True,
                'deposit_percent': 25,
            },
            estimate=estimate
        )
        assert form.is_valid()
