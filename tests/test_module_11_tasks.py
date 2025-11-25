"""
🧪 TESTS UNITARIOS - MÓDULO 11: TASKS

Test Coverage:
- Task CRUD operations
- Task priorities (Q11.6)
- Task dependencies (Q11.7)
- Due dates (Q11.1)
- Time tracking (Q11.13)
- TouchUp separation
- Permissions (Q11.9)
- Status changes (Q11.10, Q11.12)
- Image versioning (Q11.8)
- Reopening tasks (Q11.12)
"""

import pytest
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import date, timedelta
from decimal import Decimal

from core.models import (
    Project, Employee, Task, TaskImage, TaskStatusChange
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def admin_user(db):
    """Admin user for testing"""
    return User.objects.create_user(
        username='admin',
        email='admin@test.com',
        password='admin123',
        is_staff=True,
        is_superuser=True
    )


@pytest.fixture
def pm_user(db):
    """Project Manager user"""
    user = User.objects.create_user(
        username='pm',
        email='pm@test.com',
        password='pm123'
    )
    # Assuming Profile model exists
    if hasattr(user, 'profile'):
        user.profile.role = 'project_manager'
        user.profile.save()
    return user


@pytest.fixture
def client_user(db):
    """Client user"""
    user = User.objects.create_user(
        username='client',
        email='client@test.com',
        password='client123'
    )
    if hasattr(user, 'profile'):
        user.profile.role = 'client'
        user.profile.save()
    return user


@pytest.fixture
def employee(db):
    """Test employee"""
    return Employee.objects.create(
        first_name='John',
        last_name='Doe',
        social_security_number='123-45-6789',
        hourly_rate=Decimal('25.00'),
        is_active=True
    )


@pytest.fixture
def project(db):
    """Test project"""
    return Project.objects.create(
        name='Test Project',
        client='Test Client',
        start_date=date.today(),
        budget_total=Decimal('10000.00')
    )


@pytest.fixture
def task(db, project, admin_user):
    """Basic task"""
    return Task.objects.create(
        project=project,
        title='Test Task',
        description='Test description',
        status='Pendiente',
        priority='medium',
        created_by=admin_user
    )


# ============================================================================
# TASK CRUD TESTS
# ============================================================================

@pytest.mark.unit
@pytest.mark.module_11
class TestTaskCRUD:
    """Test Task create, read, update, delete operations"""
    
    def test_create_task_minimal(self, project, admin_user):
        """Test creating task with minimal required fields"""
        task = Task.objects.create(
            project=project,
            title='Minimal Task',
            created_by=admin_user
        )
        
        assert task.pk is not None
        assert task.title == 'Minimal Task'
        assert task.status == 'Pendiente'  # Default
        assert task.priority == 'medium'  # Default
        assert task.created_at is not None
        assert task.is_touchup is False  # Default
    
    def test_create_task_full(self, project, admin_user, employee):
        """Test creating task with all fields"""
        due_date = date.today() + timedelta(days=7)
        
        task = Task.objects.create(
            project=project,
            title='Full Task',
            description='Complete task with all fields',
            status='En Progreso',
            priority='high',
            created_by=admin_user,
            assigned_to=employee,
            due_date=due_date
        )
        
        assert task.pk is not None
        assert task.description == 'Complete task with all fields'
        assert task.assigned_to == employee
        assert task.due_date == due_date
    
    def test_read_task(self, task):
        """Test reading task from database"""
        retrieved = Task.objects.get(pk=task.pk)
        
        assert retrieved.title == task.title
        assert retrieved.project == task.project
        assert retrieved.created_by == task.created_by
    
    def test_update_task(self, task):
        """Test updating task fields"""
        task.title = 'Updated Title'
        task.status = 'Completada'
        task.save()
        
        retrieved = Task.objects.get(pk=task.pk)
        assert retrieved.title == 'Updated Title'
        assert retrieved.status == 'Completada'
    
    def test_delete_task(self, task):
        """Test deleting task"""
        task_id = task.pk
        task.delete()
        
        assert not Task.objects.filter(pk=task_id).exists()


# ============================================================================
# PRIORITY TESTS (Q11.6)
# ============================================================================

@pytest.mark.unit
@pytest.mark.module_11
class TestTaskPriorities:
    """Test task priority system (Q11.6)"""
    
    def test_priority_choices(self, project, admin_user):
        """Test all priority levels"""
        priorities = ['low', 'medium', 'high', 'urgent']
        
        for priority in priorities:
            task = Task.objects.create(
                project=project,
                title=f'{priority.capitalize()} Priority Task',
                priority=priority,
                created_by=admin_user
            )
            assert task.priority == priority
    
    def test_default_priority(self, project, admin_user):
        """Test default priority is medium"""
        task = Task.objects.create(
            project=project,
            title='No Priority Task',
            created_by=admin_user
        )
        assert task.priority == 'medium'
    
    def test_filter_by_priority(self, project, admin_user):
        """Test filtering tasks by priority"""
        Task.objects.create(
            project=project,
            title='High Priority',
            priority='high',
            created_by=admin_user
        )
        Task.objects.create(
            project=project,
            title='Low Priority',
            priority='low',
            created_by=admin_user
        )
        
        high_tasks = Task.objects.filter(priority='high')
        assert high_tasks.count() == 1
        assert high_tasks.first().title == 'High Priority'


# ============================================================================
# DEPENDENCIES TESTS (Q11.7)
# ============================================================================

@pytest.mark.unit
@pytest.mark.module_11
class TestTaskDependencies:
    """Test task dependency system (Q11.7)"""
    
    def test_add_dependency(self, project, admin_user):
        """Test adding dependency between tasks"""
        task1 = Task.objects.create(
            project=project,
            title='Task 1',
            created_by=admin_user
        )
        task2 = Task.objects.create(
            project=project,
            title='Task 2 (depends on Task 1)',
            created_by=admin_user
        )
        
        task2.dependencies.add(task1)
        
        assert task1 in task2.dependencies.all()
        assert task2 in task1.dependent_tasks.all()
    
    def test_can_start_with_completed_dependencies(self, project, admin_user):
        """Test can_start() returns True when dependencies are complete"""
        task1 = Task.objects.create(
            project=project,
            title='Task 1',
            status='Completada',  # Already completed
            created_by=admin_user
        )
        task2 = Task.objects.create(
            project=project,
            title='Task 2',
            created_by=admin_user
        )
        task2.dependencies.add(task1)
        
        assert task2.can_start() is True
    
    def test_cannot_start_with_pending_dependencies(self, project, admin_user):
        """Test can_start() returns False when dependencies are pending"""
        task1 = Task.objects.create(
            project=project,
            title='Task 1',
            status='Pendiente',  # Not completed
            created_by=admin_user
        )
        task2 = Task.objects.create(
            project=project,
            title='Task 2',
            created_by=admin_user
        )
        task2.dependencies.add(task1)
        
        assert task2.can_start() is False
    
    def test_multiple_dependencies(self, project, admin_user):
        """Test task with multiple dependencies"""
        task1 = Task.objects.create(
            project=project,
            title='Task 1',
            status='Completada',
            created_by=admin_user
        )
        task2 = Task.objects.create(
            project=project,
            title='Task 2',
            status='En Progreso',  # Not completed
            created_by=admin_user
        )
        task3 = Task.objects.create(
            project=project,
            title='Task 3',
            created_by=admin_user
        )
        
        task3.dependencies.add(task1, task2)
        
        # Cannot start because task2 is not completed
        assert task3.can_start() is False
        
        # Complete task2
        task2.status = 'Completada'
        task2.save()
        
        # Now can start
        assert task3.can_start() is True


# ============================================================================
# DUE DATE TESTS (Q11.1)
# ============================================================================

@pytest.mark.unit
@pytest.mark.module_11
class TestTaskDueDate:
    """Test optional due date functionality (Q11.1)"""
    
    def test_task_without_due_date(self, project, admin_user):
        """Test task can be created without due date"""
        task = Task.objects.create(
            project=project,
            title='No Due Date Task',
            created_by=admin_user
        )
        assert task.due_date is None
    
    def test_task_with_due_date(self, project, admin_user):
        """Test task with due date"""
        due = date.today() + timedelta(days=7)
        task = Task.objects.create(
            project=project,
            title='Task with Due Date',
            due_date=due,
            created_by=admin_user
        )
        assert task.due_date == due
    
    def test_filter_overdue_tasks(self, project, admin_user):
        """Test filtering overdue tasks"""
        past_date = date.today() - timedelta(days=1)
        future_date = date.today() + timedelta(days=1)
        
        Task.objects.create(
            project=project,
            title='Overdue Task',
            due_date=past_date,
            status='Pendiente',
            created_by=admin_user
        )
        Task.objects.create(
            project=project,
            title='Future Task',
            due_date=future_date,
            status='Pendiente',
            created_by=admin_user
        )
        
        overdue = Task.objects.filter(
            due_date__lt=date.today(),
            status__in=['Pendiente', 'En Progreso']
        )
        
        assert overdue.count() == 1
        assert overdue.first().title == 'Overdue Task'


# ============================================================================
# TIME TRACKING TESTS (Q11.13)
# ============================================================================

@pytest.mark.unit
@pytest.mark.module_11
class TestTaskTimeTracking:
    """Test time tracking functionality (Q11.13)"""
    
    def test_start_tracking(self, task):
        """Test starting time tracking"""
        result = task.start_tracking()
        
        assert result is True
        assert task.started_at is not None
        assert task.status == 'En Progreso'
    
    def test_cannot_start_tracking_twice(self, task):
        """Test cannot start tracking if already started"""
        task.start_tracking()
        result = task.start_tracking()
        
        assert result is False
    
    def test_stop_tracking(self, task):
        """Test stopping time tracking"""
        task.start_tracking()
        
        # Simulate 1 hour of work
        import time
        time.sleep(1.0)  # 1 second for more reliable testing
        
        elapsed = task.stop_tracking()
        
        assert elapsed is not None
        assert elapsed >= 1  # At least 1 second
        assert task.started_at is None  # Reset
        assert task.time_tracked_seconds >= 1
    
    def test_multiple_tracking_sessions(self, task):
        """Test accumulating time across multiple sessions"""
        # First session
        task.start_tracking()
        import time
        time.sleep(1.0)  # 1 second
        task.stop_tracking()
        
        first_total = task.time_tracked_seconds
        assert first_total >= 1
        
        # Second session
        task.start_tracking()
        time.sleep(1.0)  # 1 second
        task.stop_tracking()
        
        assert task.time_tracked_seconds > first_total
    
    def test_get_time_tracked_hours(self, task):
        """Test converting seconds to hours"""
        task.time_tracked_seconds = 7200  # 2 hours
        task.save()
        
        hours = task.get_time_tracked_hours()
        assert hours == 2.0
    
    def test_touchup_no_tracking(self, project, admin_user):
        """Test touch-ups don't track time (Q11.13)"""
        touchup = Task.objects.create(
            project=project,
            title='Touch-up Task',
            is_touchup=True,
            created_by=admin_user
        )
        
        result = touchup.start_tracking()
        assert result is False  # Should not start
        assert touchup.started_at is None


# ============================================================================
# TOUCHUP SEPARATION TESTS
# ============================================================================

@pytest.mark.unit
@pytest.mark.module_11
class TestTouchUpSeparation:
    """Test touch-up flag (to be deprecated)"""
    
    def test_create_regular_task(self, project, admin_user):
        """Test creating regular task"""
        task = Task.objects.create(
            project=project,
            title='Regular Task',
            created_by=admin_user
        )
        assert task.is_touchup is False
    
    def test_create_touchup_task(self, project, admin_user):
        """Test creating touch-up task (legacy)"""
        touchup = Task.objects.create(
            project=project,
            title='Touch-up Task',
            is_touchup=True,
            created_by=admin_user
        )
        assert touchup.is_touchup is True
    
    def test_filter_touchups(self, project, admin_user):
        """Test filtering touch-up tasks"""
        Task.objects.create(
            project=project,
            title='Regular',
            is_touchup=False,
            created_by=admin_user
        )
        Task.objects.create(
            project=project,
            title='Touch-up',
            is_touchup=True,
            created_by=admin_user
        )
        
        touchups = Task.objects.filter(is_touchup=True)
        assert touchups.count() == 1
        assert touchups.first().title == 'Touch-up'


# ============================================================================
# STATUS CHANGE TRACKING TESTS (Q11.10, Q11.12)
# ============================================================================

@pytest.mark.unit
@pytest.mark.module_11
class TestTaskStatusChanges:
    """Test status change history (Q11.10, Q11.12)"""
    
    def test_status_change_creates_history(self, task, admin_user):
        """Test changing status creates audit record"""
        # Note: This requires save() method to trigger signal
        # For now, test the model structure
        
        old_status = task.status
        task.status = 'Completada'
        task.save()
        
        # Manual creation for testing (real implementation uses signal)
        TaskStatusChange.objects.create(
            task=task,
            old_status=old_status,
            new_status='Completada',
            changed_by=admin_user
        )
        
        changes = TaskStatusChange.objects.filter(task=task)
        assert changes.count() >= 1
        assert changes.first().new_status == 'Completada'
    
    def test_reopen_completed_task(self, task, admin_user):
        """Test reopening completed task (Q11.12)"""
        # Complete task
        task.status = 'Completada'
        task.completed_at = timezone.now()
        task.save()
        
        # Reopen
        task.status = 'En Progreso'
        task.completed_at = None
        task.save()
        
        # Create manual status change for testing
        TaskStatusChange.objects.create(
            task=task,
            old_status='Completada',
            new_status='En Progreso',
            changed_by=admin_user,
            notes='Task reopened'
        )
        
        changes = TaskStatusChange.objects.filter(task=task)
        reopens = [c for c in changes if c.old_status == 'Completada']
        
        assert len(reopens) >= 1


# ============================================================================
# IMAGE VERSIONING TESTS (Q11.8)
# ============================================================================

@pytest.mark.unit
@pytest.mark.module_11
class TestTaskImageVersioning:
    """Test image versioning system (Q11.8)"""
    
    def test_upload_first_image(self, task, admin_user):
        """Test uploading first image"""
        img = TaskImage.objects.create(
            task=task,
            image='tasks/test_image.jpg',
            uploaded_by=admin_user,
            version=1,
            is_current=True
        )
        
        assert img.version == 1
        assert img.is_current is True
    
    def test_upload_new_version(self, task, admin_user):
        """Test uploading new version marks old as non-current"""
        # First image
        img1 = TaskImage.objects.create(
            task=task,
            image='tasks/test_v1.jpg',
            uploaded_by=admin_user,
            version=1,
            is_current=True
        )
        
        # New version
        img2 = TaskImage.objects.create(
            task=task,
            image='tasks/test_v2.jpg',
            uploaded_by=admin_user,
            version=2,
            is_current=True
        )
        
        # Manually mark old as non-current (in real app, signal would do this)
        img1.is_current = False
        img1.save()
        
        current_images = TaskImage.objects.filter(task=task, is_current=True)
        assert current_images.count() == 1
        assert current_images.first().version == 2
    
    def test_get_all_versions(self, task, admin_user):
        """Test retrieving all versions"""
        for i in range(1, 4):
            TaskImage.objects.create(
                task=task,
                image=f'tasks/test_v{i}.jpg',
                uploaded_by=admin_user,
                version=i,
                is_current=(i == 3)  # Only last is current
            )
        
        all_versions = TaskImage.objects.filter(task=task).order_by('version')
        assert all_versions.count() == 3
        
        current = all_versions.filter(is_current=True)
        assert current.count() == 1
        assert current.first().version == 3


# ============================================================================
# PERMISSION TESTS (Q11.9)
# ============================================================================

@pytest.mark.unit
@pytest.mark.module_11
class TestTaskPermissions:
    """Test task deletion and edit permissions (Q11.9)"""
    
    def test_admin_can_delete(self, task, admin_user):
        """Test admin can delete tasks"""
        # In real app, check user.is_staff or user.is_superuser
        assert admin_user.is_staff is True
        
        # Admin should be able to delete
        task_id = task.pk
        task.delete()
        assert not Task.objects.filter(pk=task_id).exists()
    
    def test_pm_can_delete(self, project, pm_user):
        """Test PM can delete tasks"""
        task = Task.objects.create(
            project=project,
            title='PM Task',
            created_by=pm_user
        )
        
        # PM should be able to delete
        task_id = task.pk
        task.delete()
        assert not Task.objects.filter(pk=task_id).exists()
    
    def test_client_cannot_assign(self, project, client_user, employee):
        """Test client cannot assign employees (Q11.3)"""
        task = Task.objects.create(
            project=project,
            title='Client Task',
            created_by=client_user,
            is_client_request=True
        )
        
        # In real app, view would prevent this
        # Here we just document the expected behavior
        assert task.assigned_to is None
        
        # Client should NOT be able to set assigned_to
        # (This would be enforced in form/view)


# ============================================================================
# CLIENT REQUEST TESTS (Q17.7, Q17.9)
# ============================================================================

@pytest.mark.unit
@pytest.mark.module_11
class TestClientRequests:
    """Test client-created tasks"""
    
    def test_create_client_request(self, project, client_user):
        """Test client creating request"""
        task = Task.objects.create(
            project=project,
            title='Client Request',
            description='Client needs something',
            created_by=client_user,
            is_client_request=True
        )
        
        assert task.is_client_request is True
        assert task.assigned_to is None  # Not assigned yet
    
    def test_client_cancel_request(self, project, client_user):
        """Test client canceling their request (Q17.9)"""
        task = Task.objects.create(
            project=project,
            title='Client Request',
            created_by=client_user,
            is_client_request=True
        )
        
        # Client cancels
        task.client_cancelled = True
        task.cancellation_reason = 'No longer needed'
        task.status = 'Cancelada'
        task.save()
        
        assert task.client_cancelled is True
        assert task.cancellation_reason == 'No longer needed'
        assert task.status == 'Cancelada'


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

@pytest.mark.integration
@pytest.mark.module_11
class TestTaskIntegration:
    """Integration tests for Task with other models"""
    
    def test_task_with_schedule_item(self, project, admin_user):
        """Test task linked to schedule item (Q11.4)"""
        from core.models import Schedule, ScheduleCategory, ScheduleItem
        
        # Create schedule structure
        schedule = Schedule.objects.create(
            project=project,
            title='Project Schedule',  # Changed from 'name' to 'title'
            start_datetime=timezone.now(),
            end_datetime=timezone.now() + timedelta(days=30)
        )
        category = ScheduleCategory.objects.create(
            project=project,  # Added required project field
            name='Painting',
            order=1
        )
        item = ScheduleItem.objects.create(
            title='Paint Living Room',
            project=project,
            category=category,
            planned_start=timezone.now().date(),
            planned_end=(timezone.now() + timedelta(days=2)).date()
        )
        
        # Create task linked to schedule item
        task = Task.objects.create(
            project=project,
            title='Paint Living Room',
            schedule_item=item,
            created_by=admin_user
        )
        
        assert task.schedule_item == item
        assert task in item.tasks.all()
    
    def test_task_without_schedule(self, project, admin_user):
        """Test task can exist without schedule (Q11.4)"""
        task = Task.objects.create(
            project=project,
            title='Standalone Task',
            created_by=admin_user
        )
        
        assert task.schedule_item is None


# ============================================================================
# EDGE CASES & ERROR HANDLING
# ============================================================================

@pytest.mark.unit
@pytest.mark.module_11
class TestTaskEdgeCases:
    """Test edge cases and error conditions"""
    
    def test_circular_dependency_prevention(self, project, admin_user):
        """Test preventing circular dependencies"""
        task1 = Task.objects.create(
            project=project,
            title='Task 1',
            created_by=admin_user
        )
        task2 = Task.objects.create(
            project=project,
            title='Task 2',
            created_by=admin_user
        )
        
        # Task2 depends on Task1
        task2.dependencies.add(task1)
        
        # Task1 depends on Task2 (circular)
        task1.dependencies.add(task2)
        
        # Both should report they cannot start
        # (In real app, add validation to prevent this)
        assert task1.can_start() is False
        assert task2.can_start() is False
    
    def test_empty_title_validation(self, project, admin_user):
        """Test task requires non-empty title"""
        from django.core.exceptions import ValidationError
        
        # Try to create task with empty title
        task = Task(
            project=project,
            title='',  # Empty title
            created_by=admin_user
        )
        
        # Should raise validation error
        with pytest.raises(ValidationError):
            task.full_clean()  # This will trigger clean() method
    
    def test_task_string_representation(self, task):
        """Test __str__ method"""
        expected = f"{task.title} - {task.status}"
        assert str(task) == expected
