"""
Tests for Module 12: Daily Plans
Tests workflow transitions, activity conversion, productivity tracking, and material consumption
"""
import pytest
from datetime import date, datetime, timedelta
from decimal import Decimal
from django.utils import timezone
from django.contrib.auth.models import User
from core.models import (
    Project,
    DailyPlan,
    PlannedActivity,
    Task,
    Employee,
    ActivityTemplate,
    InventoryItem,
    InventoryLocation,
    InventoryMovement,
    ProjectInventory,
    ScheduleCategory,
    ScheduleItem,
)


@pytest.mark.django_db
class TestDailyPlanWorkflow:
    """Test status transitions and workflow rules"""
    
    def test_initial_status_is_draft(self):
        """Test new plans start in DRAFT status"""
        user = User.objects.create_user('testuser', 'test@test.com', 'pass')
        project = Project.objects.create(
            name="Test Project",
            start_date=date.today()
        )
        plan = DailyPlan.objects.create(
            project=project,
            plan_date=date.today(),
            created_by=user,
            completion_deadline=timezone.now() + timedelta(days=1)
        )
        
        assert plan.status == 'DRAFT'
    
    def test_transition_draft_to_published(self):
        """Test DRAFT → PUBLISHED transition"""
        user = User.objects.create_user('testuser', 'test@test.com', 'pass')
        project = Project.objects.create(
            name="Test Project",
            start_date=date.today()
        )
        plan = DailyPlan.objects.create(
            project=project,
            plan_date=date.today(),
            created_by=user,
            completion_deadline=timezone.now() + timedelta(days=1),
            status='DRAFT'
        )
        
        plan.status = 'PUBLISHED'
        plan.save()
        plan.refresh_from_db()
        
        assert plan.status == 'PUBLISHED'
    
    def test_transition_published_to_in_progress(self):
        """Test PUBLISHED → IN_PROGRESS transition"""
        user = User.objects.create_user('testuser', 'test@test.com', 'pass')
        project = Project.objects.create(
            name="Test Project",
            start_date=date.today()
        )
        plan = DailyPlan.objects.create(
            project=project,
            plan_date=date.today(),
            created_by=user,
            completion_deadline=timezone.now() + timedelta(days=1),
            status='PUBLISHED'
        )
        
        plan.status = 'IN_PROGRESS'
        plan.save()
        plan.refresh_from_db()
        
        assert plan.status == 'IN_PROGRESS'
    
    def test_transition_in_progress_to_completed(self):
        """Test IN_PROGRESS → COMPLETED transition"""
        user = User.objects.create_user('testuser', 'test@test.com', 'pass')
        project = Project.objects.create(
            name="Test Project",
            start_date=date.today()
        )
        plan = DailyPlan.objects.create(
            project=project,
            plan_date=date.today(),
            created_by=user,
            completion_deadline=timezone.now() + timedelta(days=1),
            status='IN_PROGRESS'
        )
        
        plan.status = 'COMPLETED'
        plan.save()
        plan.refresh_from_db()
        
        assert plan.status == 'COMPLETED'
    
    def test_is_overdue_when_past_deadline_and_draft(self):
        """Test is_overdue() returns True when past deadline"""
        user = User.objects.create_user('testuser', 'test@test.com', 'pass')
        project = Project.objects.create(
            name="Test Project",
            start_date=date.today()
        )
        plan = DailyPlan.objects.create(
            project=project,
            plan_date=date.today(),
            created_by=user,
            completion_deadline=timezone.now() - timedelta(hours=1),
            status='DRAFT'
        )
        
        assert plan.is_overdue() is True
    
    def test_is_not_overdue_when_published(self):
        """Test is_overdue() returns False when not DRAFT"""
        user = User.objects.create_user('testuser', 'test@test.com', 'pass')
        project = Project.objects.create(
            name="Test Project",
            start_date=date.today()
        )
        plan = DailyPlan.objects.create(
            project=project,
            plan_date=date.today(),
            created_by=user,
            completion_deadline=timezone.now() - timedelta(hours=1),
            status='PUBLISHED'
        )
        
        assert plan.is_overdue() is False


@pytest.mark.django_db
class TestActivityToTaskConversion:
    """Test converting planned activities to tasks"""
    
    def test_convert_single_activity_to_task(self):
        """Test basic activity to task conversion"""
        user = User.objects.create_user('testuser', 'test@test.com', 'pass')
        project = Project.objects.create(
            name="Test Project",
            start_date=date.today()
        )
        plan = DailyPlan.objects.create(
            project=project,
            plan_date=date.today(),
            created_by=user,
            completion_deadline=timezone.now() + timedelta(days=1)
        )
        
        activity = PlannedActivity.objects.create(
            daily_plan=plan,
            title="Paint living room",
            description="Apply primer and first coat",
            estimated_hours=Decimal('8.00'),
            status='PENDING'
        )
        
        tasks = plan.convert_activities_to_tasks(user)
        
        assert len(tasks) == 1
        assert tasks[0].title == "Paint living room"
        assert tasks[0].project == project
        assert tasks[0].due_date == plan.plan_date
        
        activity.refresh_from_db()
        assert activity.converted_task == tasks[0]
    
    def test_convert_multiple_activities(self):
        """Test converting multiple activities"""
        user = User.objects.create_user('testuser', 'test@test.com', 'pass')
        project = Project.objects.create(
            name="Test Project",
            start_date=date.today()
        )
        plan = DailyPlan.objects.create(
            project=project,
            plan_date=date.today(),
            created_by=user,
            completion_deadline=timezone.now() + timedelta(days=1)
        )
        
        activity1 = PlannedActivity.objects.create(
            daily_plan=plan,
            title="Prep walls",
            status='PENDING'
        )
        activity2 = PlannedActivity.objects.create(
            daily_plan=plan,
            title="Paint walls",
            status='PENDING'
        )
        
        tasks = plan.convert_activities_to_tasks(user)
        
        assert len(tasks) == 2
        assert tasks[0].title == "Prep walls"
        assert tasks[1].title == "Paint walls"
    
    def test_skip_completed_activities(self):
        """Test completed activities are not converted"""
        user = User.objects.create_user('testuser', 'test@test.com', 'pass')
        project = Project.objects.create(
            name="Test Project",
            start_date=date.today()
        )
        plan = DailyPlan.objects.create(
            project=project,
            plan_date=date.today(),
            created_by=user,
            completion_deadline=timezone.now() + timedelta(days=1)
        )
        
        activity1 = PlannedActivity.objects.create(
            daily_plan=plan,
            title="Already done",
            status='COMPLETED'
        )
        activity2 = PlannedActivity.objects.create(
            daily_plan=plan,
            title="Not done",
            status='PENDING'
        )
        
        tasks = plan.convert_activities_to_tasks(user)
        
        assert len(tasks) == 1
        assert tasks[0].title == "Not done"
    
    def test_convert_activity_with_employee_assignment(self):
        """Test employee assignment is transferred to task"""
        user = User.objects.create_user('testuser', 'test@test.com', 'pass')
        project = Project.objects.create(
            name="Test Project",
            start_date=date.today()
        )
        plan = DailyPlan.objects.create(
            project=project,
            plan_date=date.today(),
            created_by=user,
            completion_deadline=timezone.now() + timedelta(days=1)
        )
        
        employee = Employee.objects.create(
            user=user,
            hire_date=date.today(),
            hourly_rate=Decimal('20.00')
        )
        
        activity = PlannedActivity.objects.create(
            daily_plan=plan,
            title="Paint walls",
            status='PENDING'
        )
        activity.assigned_employees.add(employee)
        
        tasks = plan.convert_activities_to_tasks(user)
        
        assert len(tasks) == 1
        assert tasks[0].assigned_to == employee  # Task.assigned_to is Employee
    
    def test_convert_activity_with_schedule_link(self):
        """Test schedule item link is preserved"""
        user = User.objects.create_user('testuser', 'test@test.com', 'pass')
        project = Project.objects.create(
            name="Test Project",
            start_date=date.today()
        )
        plan = DailyPlan.objects.create(
            project=project,
            plan_date=date.today(),
            created_by=user,
            completion_deadline=timezone.now() + timedelta(days=1)
        )
        # Create ScheduleCategory and ScheduleItem (hierarchical schedule)
        category = ScheduleCategory.objects.create(project=project, name="Painting")
        schedule_item = ScheduleItem.objects.create(project=project, category=category, title="Paint interior")
        
        activity = PlannedActivity.objects.create(
            daily_plan=plan,
            title="Paint day 1",
            schedule_item=schedule_item,
            status='PENDING'
        )
        
        tasks = plan.convert_activities_to_tasks(user)
        
        assert len(tasks) == 1
        assert tasks[0].schedule_item == schedule_item


@pytest.mark.django_db
class TestProductivityTracking:
    """Test productivity calculation and tracking"""
    
    def test_productivity_score_perfect_match(self):
        """Test 100% score when estimated == actual"""
        user = User.objects.create_user('testuser', 'test@test.com', 'pass')
        project = Project.objects.create(
            name="Test Project",
            start_date=date.today()
        )
        plan = DailyPlan.objects.create(
            project=project,
            plan_date=date.today(),
            created_by=user,
            completion_deadline=timezone.now() + timedelta(days=1),
            estimated_hours_total=Decimal('8.00'),
            actual_hours_worked=Decimal('8.00')
        )
        
        score = plan.calculate_productivity_score()
        
        assert score == 100.0
    
    def test_productivity_score_more_efficient(self):
        """Test >100% score when work done faster than estimated"""
        user = User.objects.create_user('testuser', 'test@test.com', 'pass')
        project = Project.objects.create(
            name="Test Project",
            start_date=date.today()
        )
        plan = DailyPlan.objects.create(
            project=project,
            plan_date=date.today(),
            created_by=user,
            completion_deadline=timezone.now() + timedelta(days=1),
            estimated_hours_total=Decimal('8.00'),
            actual_hours_worked=Decimal('6.00')
        )
        
        score = plan.calculate_productivity_score()
        
        assert score == 133.3  # 8/6 * 100 = 133.3
    
    def test_productivity_score_less_efficient(self):
        """Test <100% score when work took longer than estimated"""
        user = User.objects.create_user('testuser', 'test@test.com', 'pass')
        project = Project.objects.create(
            name="Test Project",
            start_date=date.today()
        )
        plan = DailyPlan.objects.create(
            project=project,
            plan_date=date.today(),
            created_by=user,
            completion_deadline=timezone.now() + timedelta(days=1),
            estimated_hours_total=Decimal('8.00'),
            actual_hours_worked=Decimal('10.00')
        )
        
        score = plan.calculate_productivity_score()
        
        assert score == 80.0  # 8/10 * 100 = 80
    
    def test_productivity_score_null_when_no_data(self):
        """Test None returned when data is missing"""
        user = User.objects.create_user('testuser', 'test@test.com', 'pass')
        project = Project.objects.create(
            name="Test Project",
            start_date=date.today()
        )
        plan = DailyPlan.objects.create(
            project=project,
            plan_date=date.today(),
            created_by=user,
            completion_deadline=timezone.now() + timedelta(days=1)
        )
        
        score = plan.calculate_productivity_score()
        
        assert score is None
    
    def test_productivity_score_with_zero_actual_hours(self):
        """Test 100% returned when actual hours is 0"""
        user = User.objects.create_user('testuser', 'test@test.com', 'pass')
        project = Project.objects.create(
            name="Test Project",
            start_date=date.today()
        )
        plan = DailyPlan.objects.create(
            project=project,
            plan_date=date.today(),
            created_by=user,
            completion_deadline=timezone.now() + timedelta(days=1),
            estimated_hours_total=Decimal('8.00'),
            actual_hours_worked=Decimal('0.00')
        )
        
        score = plan.calculate_productivity_score()
        
        assert score == 100.0


@pytest.mark.django_db
class TestMaterialConsumption:
    """Test automatic material consumption"""
    
    def test_auto_consume_materials_basic(self):
        """Test basic material consumption"""
        user = User.objects.create_user('testuser', 'test@test.com', 'pass')
        project = Project.objects.create(
            name="Test Project",
            start_date=date.today()
        )
        plan = DailyPlan.objects.create(
            project=project,
            plan_date=date.today(),
            created_by=user,
            completion_deadline=timezone.now() + timedelta(days=1)
        )
        
        # Create inventory location and item
        location = InventoryLocation.objects.create(
            name="Project Site",
            project=project
        )
        
        item = InventoryItem.objects.create(
            name="Tape",
            sku="TAPE001",
            category="MATERIAL",
            unit="rolls"
        )
        
        # Create ProjectInventory with stock
        ProjectInventory.objects.create(
            item=item,
            location=location,
            quantity=Decimal('100')
        )
        
        # Consume materials
        consumption_data = {'Tape': 10}
        movements = plan.auto_consume_materials(consumption_data, user)
        
        assert len(movements) == 1
        assert movements[0].item == item
        assert movements[0].quantity == Decimal('10')
        assert movements[0].movement_type == 'CONSUME'
    
    def test_auto_consume_multiple_materials(self):
        """Test consuming multiple materials at once"""
        user = User.objects.create_user('testuser', 'test@test.com', 'pass')
        project = Project.objects.create(
            name="Test Project",
            start_date=date.today()
        )
        plan = DailyPlan.objects.create(
            project=project,
            plan_date=date.today(),
            created_by=user,
            completion_deadline=timezone.now() + timedelta(days=1)
        )
        
        location = InventoryLocation.objects.create(
            name="Project Site",
            project=project
        )
        
        tape = InventoryItem.objects.create(
            name="Tape",
            sku="TAPE001",
            category="MATERIAL",
            unit="rolls"
        )
        
        paint = InventoryItem.objects.create(
            name="Paint - White",
            sku="PAINT001",
            category="PINTURA",
            unit="gallons"
        )
        
        # Create ProjectInventory for both items
        ProjectInventory.objects.create(
            item=tape,
            location=location,
            quantity=Decimal('100')
        )
        ProjectInventory.objects.create(
            item=paint,
            location=location,
            quantity=Decimal('50')
        )
        
        consumption_data = {
            'Tape': 10,
            'Paint': 2
        }
        movements = plan.auto_consume_materials(consumption_data, user)
        
        assert len(movements) == 2
    
    def test_auto_consume_skips_nonexistent_materials(self):
        """Test graceful handling of materials not in inventory"""
        user = User.objects.create_user('testuser', 'test@test.com', 'pass')
        project = Project.objects.create(
            name="Test Project",
            start_date=date.today()
        )
        plan = DailyPlan.objects.create(
            project=project,
            plan_date=date.today(),
            created_by=user,
            completion_deadline=timezone.now() + timedelta(days=1)
        )
        
        location = InventoryLocation.objects.create(
            name="Project Site",
            project=project
        )
        
        consumption_data = {'NonExistentMaterial': 10}
        movements = plan.auto_consume_materials(consumption_data, user)
        
        assert len(movements) == 0
    
    def test_auto_consume_without_location(self):
        """Test returns empty list when no location exists"""
        user = User.objects.create_user('testuser', 'test@test.com', 'pass')
        project = Project.objects.create(
            name="Test Project",
            start_date=date.today()
        )
        plan = DailyPlan.objects.create(
            project=project,
            plan_date=date.today(),
            created_by=user,
            completion_deadline=timezone.now() + timedelta(days=1)
        )
        
        consumption_data = {'Tape': 10}
        movements = plan.auto_consume_materials(consumption_data, user)
        
        assert len(movements) == 0


@pytest.mark.django_db
class TestPlannedActivityTracking:
    """Test time tracking and variance on PlannedActivity"""
    
    def test_activity_time_variance_under_budget(self):
        """Test time variance when activity finishes early"""
        user = User.objects.create_user('testuser', 'test@test.com', 'pass')
        project = Project.objects.create(
            name="Test Project",
            start_date=date.today()
        )
        plan = DailyPlan.objects.create(
            project=project,
            plan_date=date.today(),
            created_by=user,
            completion_deadline=timezone.now() + timedelta(days=1)
        )
        
        activity = PlannedActivity.objects.create(
            daily_plan=plan,
            title="Paint walls",
            estimated_hours=Decimal('8.00'),
            actual_hours=Decimal('6.00')
        )
        
        variance = activity.get_time_variance()
        
        assert variance['variance_hours'] == 2.0  # 2 hours under
        assert variance['variance_percentage'] == 25.0  # 25% faster
        assert variance['is_efficient'] is True
    
    def test_activity_time_variance_over_budget(self):
        """Test time variance when activity takes longer"""
        user = User.objects.create_user('testuser', 'test@test.com', 'pass')
        project = Project.objects.create(
            name="Test Project",
            start_date=date.today()
        )
        plan = DailyPlan.objects.create(
            project=project,
            plan_date=date.today(),
            created_by=user,
            completion_deadline=timezone.now() + timedelta(days=1)
        )
        
        activity = PlannedActivity.objects.create(
            daily_plan=plan,
            title="Paint walls",
            estimated_hours=Decimal('8.00'),
            actual_hours=Decimal('10.00')
        )
        
        variance = activity.get_time_variance()
        
        assert variance['variance_hours'] == -2.0  # 2 hours over
        assert variance['variance_percentage'] == -25.0  # 25% slower
        assert variance['is_efficient'] is False
    
    def test_activity_time_variance_null_when_no_data(self):
        """Test None returned when hours not tracked"""
        user = User.objects.create_user('testuser', 'test@test.com', 'pass')
        project = Project.objects.create(
            name="Test Project",
            start_date=date.today()
        )
        plan = DailyPlan.objects.create(
            project=project,
            plan_date=date.today(),
            created_by=user,
            completion_deadline=timezone.now() + timedelta(days=1)
        )
        
        activity = PlannedActivity.objects.create(
            daily_plan=plan,
            title="Paint walls"
        )
        
        variance = activity.get_time_variance()
        
        assert variance is None
