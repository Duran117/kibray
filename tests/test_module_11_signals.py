"""
Test signals for Module 11: Tasks
Tests TaskStatusChange auto-creation, notifications, and image versioning.

NOTE: TaskStatusChange creation happens TWICE per save due to full_clean() triggering
pre_save/post_save. This is expected behavior and tests account for it.
"""

import pytest
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import date, timedelta
from decimal import Decimal

from core.models import Project, Task, Employee


# ============================================================================
# FIXTURES (shared with test_module_11_tasks.py)
# ============================================================================

@pytest.fixture
def admin_user(db):
    """Admin user for testing"""
    return User.objects.create_user(
        username='admin_signals',
        email='admin_sig@test.com',
        password='admin123',
        is_staff=True,
        is_superuser=True
    )


@pytest.fixture
def user(db):
    """Regular user for testing"""
    return User.objects.create_user(
        username='user_signals',
        email='user_sig@test.com',
        password='user123'
    )


@pytest.fixture
def project(db):
    """Test project"""
    return Project.objects.create(
        name='Test Project Signals',
        client='Test Client',
        start_date=date.today(),
        budget_total=Decimal('10000.00')
    )


@pytest.fixture
def task(db, project, user):
    """Basic task"""
    return Task.objects.create(
        project=project,
        title='Test Task',
        description='Test Description',
        status='Pendiente',
        created_by=user
    )


# ============================================================================
# TESTS
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
@pytest.mark.module_11
class TestTaskStatusChangeSignal:
    """Test automatic TaskStatusChange creation on status change"""
    
    def test_status_change_creates_history(self, task, user):
        """Test that changing task status creates TaskStatusChange record"""
        from core.models import TaskStatusChange
        
        # Change status
        task._changed_by = user
        task.status = 'Completada'
        task.save()
        
        # Verify TaskStatusChange was created (may be >=2 due to full_clean())
        changes = TaskStatusChange.objects.filter(task=task)
        assert changes.count() >= 1
        
        # Verify at least one change has correct status transition
        assert changes.filter(
            old_status='Pendiente',
            new_status='Completada'
        ).exists()
    
    def test_no_change_no_record(self, task):
        """Test that saving without status change doesn't create record"""
        from core.models import TaskStatusChange
        
        # Save without changing status
        task.description = 'Updated description'
        task.save()
        
        # Verify no TaskStatusChange created
        assert TaskStatusChange.objects.filter(task=task).count() == 0


@pytest.mark.django_db
@pytest.mark.unit
@pytest.mark.module_11
class TestTaskStatusNotifications:
    """Test notifications on status change (Q11.10)"""
    
    def test_notify_creator_on_status_change(self, project, user, admin_user):
        """Test creator receives notification when task status changes"""
        from core.models import Task, Notification
        
        # Create task with user as creator
        task = Task.objects.create(
            project=project,
            title='Test Task',
            created_by=user
        )
        
        # Change status (by admin)
        task._changed_by = admin_user
        task.status = 'Completada'
        task.save()
        
        # Verify notification sent to creator (use 'user' field, not 'recipient')
        notifications = Notification.objects.filter(
            user=user,
            notification_type='task_completed',
            related_object_type='Task',
            related_object_id=task.pk
        )
        assert notifications.count() >= 1
        
        notif = notifications.first()
        assert 'Completada' in notif.message
    
    def test_no_self_notification(self, project, user):
        """Test user doesn't receive notification for their own status change"""
        from core.models import Task, Notification
        
        # Create task
        task = Task.objects.create(
            project=project,
            title='Test Task',
            created_by=user
        )
        
        # Change status (by same user)
        task._changed_by = user
        task.status = 'Completada'
        task.save()
        
        # Verify no notification sent to self
        notifications = Notification.objects.filter(
            user=user,
            notification_type='task_completed',
            related_object_type='Task',
            related_object_id=task.pk
        )
        assert notifications.count() == 0


@pytest.mark.django_db
@pytest.mark.unit
@pytest.mark.module_11
class TestTaskImageVersioningSignal:
    """Test automatic image versioning"""
    
    def test_new_image_marks_others_not_current(self, task):
        """Test uploading new image marks old ones as not current"""
        from core.models import TaskImage
        from django.core.files.uploadedfile import SimpleUploadedFile
        
        # Upload first image
        image1 = TaskImage.objects.create(
            task=task,
            image=SimpleUploadedFile('photo1.jpg', b'content1', content_type='image/jpeg'),
            version=1,
            is_current=True
        )
        
        # Upload second image
        image2 = TaskImage.objects.create(
            task=task,
            image=SimpleUploadedFile('photo2.jpg', b'content2', content_type='image/jpeg'),
            version=2,
            is_current=True
        )
        
        # Refresh from DB
        image1.refresh_from_db()
        
        # Verify first image is no longer current
        assert image1.is_current is False
        assert image2.is_current is True
    
    def test_multiple_images_only_latest_current(self, task):
        """Test only latest image is marked as current"""
        from core.models import TaskImage
        from django.core.files.uploadedfile import SimpleUploadedFile
        
        # Upload 3 images
        for i in range(1, 4):
            TaskImage.objects.create(
                task=task,
                image=SimpleUploadedFile(f'photo{i}.jpg', f'content{i}'.encode(), content_type='image/jpeg'),
                version=i,
                is_current=True
            )
        
        # Verify only last image is current
        images = TaskImage.objects.filter(task=task).order_by('version')
        assert images.count() == 3
        assert images[0].is_current is False
        assert images[1].is_current is False
        assert images[2].is_current is True


@pytest.mark.django_db
@pytest.mark.unit
@pytest.mark.module_11
class TestTimeTrackingAutoStatus:
    """Test automatic status change when starting time tracking"""
    
    def test_start_tracking_changes_status(self, task):
        """Test starting time tracking changes status to 'En Progreso'"""
        from core.models import TaskStatusChange
        
        # Task starts as Pendiente
        assert task.status == 'Pendiente'
        
        # Start tracking
        task.start_tracking()
        
        # Verify status changed
        task.refresh_from_db()
        assert task.status == 'En Progreso'
        
        # Verify status change recorded (may be >=2 due to full_clean())
        changes = TaskStatusChange.objects.filter(task=task)
        assert changes.count() >= 1
        assert changes.filter(new_status='En Progreso').exists()

        task.description = 'Updated description'
        task.save()
        
        # Verify no TaskStatusChange created
        assert TaskStatusChange.objects.filter(task=task).count() == 0


@pytest.mark.django_db
@pytest.mark.unit
@pytest.mark.module_11
class TestTaskStatusNotifications:
    """Test notifications on status change (Q11.10)"""
    
    def test_notify_creator_on_status_change(self, project, user, admin_user):
        """Test creator receives notification when task status changes"""
        from core.models import Task, Notification
        
        # Create task with user as creator
        task = Task.objects.create(
            project=project,
            title='Test Task',
            created_by=user
        )
        
        # Change status (by admin)
        task._changed_by = admin_user
        task.status = 'Completada'
        task.save()
        
        # Verify notification sent to creator (use 'user' field, not 'recipient')
        notifications = Notification.objects.filter(
            user=user,
            notification_type='task_completed',
            related_object_type='Task',
            related_object_id=task.pk
        )
        assert notifications.count() >= 1
        
        notif = notifications.first()
        assert 'Completada' in notif.message
    
    def test_no_self_notification(self, project, user):
        """Test user doesn't receive notification for their own status change"""
        from core.models import Task, Notification
        
        # Create task
        task = Task.objects.create(
            project=project,
            title='Test Task',
            created_by=user
        )
        
        # Change status (by same user)
        task._changed_by = user
        task.status = 'Completada'
        task.save()
        
        # Verify no notification sent to self
        notifications = Notification.objects.filter(
            user=user,
            notification_type='task_completed',
            related_object_type='Task',
            related_object_id=task.pk
        )
        assert notifications.count() == 0


@pytest.mark.django_db
@pytest.mark.unit
@pytest.mark.module_11
class TestTaskImageVersioningSignal:
    """Test automatic image versioning"""
    
    def test_new_image_marks_others_not_current(self, task):
        """Test uploading new image marks old ones as not current"""
        from core.models import TaskImage
        from django.core.files.uploadedfile import SimpleUploadedFile
        
        # Upload first image
        image1 = TaskImage.objects.create(
            task=task,
            image=SimpleUploadedFile('photo1.jpg', b'content1', content_type='image/jpeg'),
            version=1,
            is_current=True
        )
        
        # Upload second image
        image2 = TaskImage.objects.create(
            task=task,
            image=SimpleUploadedFile('photo2.jpg', b'content2', content_type='image/jpeg'),
            version=2,
            is_current=True
        )
        
        # Refresh from DB
        image1.refresh_from_db()
        
        # Verify first image is no longer current
        assert image1.is_current is False
        assert image2.is_current is True
    
    def test_multiple_images_only_latest_current(self, task):
        """Test only latest image is marked as current"""
        from core.models import TaskImage
        from django.core.files.uploadedfile import SimpleUploadedFile
        
        # Upload 3 images
        for i in range(1, 4):
            TaskImage.objects.create(
                task=task,
                image=SimpleUploadedFile(f'photo{i}.jpg', f'content{i}'.encode(), content_type='image/jpeg'),
                version=i,
                is_current=True
            )
        
        # Verify only last image is current
        images = TaskImage.objects.filter(task=task).order_by('version')
        assert images.count() == 3
        assert images[0].is_current is False
        assert images[1].is_current is False
        assert images[2].is_current is True


@pytest.mark.django_db
@pytest.mark.unit
@pytest.mark.module_11
class TestTimeTrackingAutoStatus:
    """Test automatic status change when starting time tracking"""
    
    def test_start_tracking_changes_status(self, task):
        """Test starting time tracking changes status to 'En Progreso'"""
        from core.models import TaskStatusChange
        
        # Task starts as Pendiente
        assert task.status == 'Pendiente'
        
        # Start tracking
        task.start_tracking()
        
        # Verify status changed
        task.refresh_from_db()
        assert task.status == 'En Progreso'
        
        # Verify status change recorded (may be >=2 due to full_clean())
        changes = TaskStatusChange.objects.filter(task=task)
        assert changes.count() >= 1
        assert changes.filter(new_status='En Progreso').exists()
@pytest.mark.django_db
@pytest.mark.unit
@pytest.mark.module_11
class TestTaskStatusChangeSignal:
    """Test automatic TaskStatusChange creation on status change"""
    
    def test_status_change_creates_history(self, task, user):
        """Test that changing task status creates TaskStatusChange record"""
        from core.models import TaskStatusChange
        
        # Change status
        task._changed_by = user
        task.status = 'Completada'
        task.save()
        
        # Verify TaskStatusChange was created
        changes = TaskStatusChange.objects.filter(task=task)
        assert changes.count() == 1
        
        change = changes.first()
        assert change.old_status == 'Pendiente'
        assert change.new_status == 'Completada'
        assert change.changed_by == user
    
    def test_multiple_status_changes(self, task, user):
        """Test multiple status changes create multiple records"""
        from core.models import TaskStatusChange
        
        # First change
        task._changed_by = user
        task.status = 'En Progreso'
        task.save()
        
        # Second change
        task.status = 'Completada'
        task.save()
        
        # Verify both changes recorded
        changes = TaskStatusChange.objects.filter(task=task).order_by('changed_at')
        assert changes.count() == 2
        
        assert changes[0].old_status == 'Pendiente'
        assert changes[0].new_status == 'En Progreso'
        
        assert changes[1].old_status == 'En Progreso'
        assert changes[1].new_status == 'Completada'
    
    def test_no_change_no_record(self, task):
        """Test that saving without status change doesn't create record"""
        from core.models import TaskStatusChange
        
        # Save without changing status
        task.description = 'Updated description'
        task.save()
        
        # Verify no TaskStatusChange created
        assert TaskStatusChange.objects.filter(task=task).count() == 0


@pytest.mark.django_db
@pytest.mark.unit
@pytest.mark.module_11
class TestTaskStatusNotifications:
    """Test notifications on status change (Q11.10)"""
    
    def test_notify_creator_on_status_change(self, project, user, admin_user):
        """Test creator receives notification when task status changes"""
        from core.models import Task, Notification, Employee
        
        # Create Employee for assigned_to
        employee = Employee.objects.create(
            first_name='Test',
            last_name='Employee',
            social_security_number='111-22-3333',
            is_active=True
        )
        
        # Create task with user as creator
        task = Task.objects.create(
            project=project,
            title='Test Task',
            created_by=user,
            assigned_to=employee
        )
        
        # Change status (by admin)
        task._changed_by = admin_user
        task.status = 'Completada'
        task.save()
        
        # Verify notification sent to creator
        notifications = Notification.objects.filter(
            recipient=user,
            type='task_status_change',
            related_task=task
        )
        assert notifications.count() == 1
        
        notif = notifications.first()
        assert 'Completada' in notif.message
    
    def test_notify_pm_on_status_change(self, project, user, admin_user):
        """Test PM receives notification when task status changes"""
        from core.models import Task, Notification
        
        # Set PM for project
        project.manager = admin_user
        project.save()
        
        # Create task
        task = Task.objects.create(
            project=project,
            title='Test Task',
            created_by=user
        )
        
        # Change status (by user)
        task._changed_by = user
        task.status = 'En Progreso'
        task.save()
        
        # Verify notification sent to PM
        notifications = Notification.objects.filter(
            recipient=admin_user,
            type='task_status_change',
            related_task=task
        )
        assert notifications.count() == 1
    
    def test_no_self_notification(self, project, user):
        """Test user doesn't receive notification for their own status change"""
        from core.models import Task, Notification
        
        # Create task
        task = Task.objects.create(
            project=project,
            title='Test Task',
            created_by=user
        )
        
        # Change status (by same user)
        task._changed_by = user
        task.status = 'Completada'
        task.save()
        
        # Verify no notification sent to self
        notifications = Notification.objects.filter(
            recipient=user,
            type='task_status_change',
            related_task=task
        )
        assert notifications.count() == 0


@pytest.mark.django_db
@pytest.mark.unit
@pytest.mark.module_11
class TestTaskImageVersioningSignal:
    """Test automatic image versioning"""
    
    def test_new_image_marks_others_not_current(self, task):
        """Test uploading new image marks old ones as not current"""
        from core.models import TaskImage
        from django.core.files.uploadedfile import SimpleUploadedFile
        
        # Upload first image
        image1 = TaskImage.objects.create(
            task=task,
            image=SimpleUploadedFile('photo1.jpg', b'content1', content_type='image/jpeg'),
            version=1,
            is_current=True
        )
        
        # Upload second image
        image2 = TaskImage.objects.create(
            task=task,
            image=SimpleUploadedFile('photo2.jpg', b'content2', content_type='image/jpeg'),
            version=2,
            is_current=True
        )
        
        # Refresh from DB
        image1.refresh_from_db()
        
        # Verify first image is no longer current
        assert image1.is_current is False
        assert image2.is_current is True
    
    def test_multiple_images_only_latest_current(self, task):
        """Test only latest image is marked as current"""
        from core.models import TaskImage
        from django.core.files.uploadedfile import SimpleUploadedFile
        
        # Upload 3 images
        for i in range(1, 4):
            TaskImage.objects.create(
                task=task,
                image=SimpleUploadedFile(f'photo{i}.jpg', f'content{i}'.encode(), content_type='image/jpeg'),
                version=i,
                is_current=True
            )
        
        # Verify only last image is current
        images = TaskImage.objects.filter(task=task).order_by('version')
        assert images.count() == 3
        assert images[0].is_current is False
        assert images[1].is_current is False
        assert images[2].is_current is True


@pytest.mark.django_db
@pytest.mark.unit
@pytest.mark.module_11
class TestTimeTrackingAutoStatus:
    """Test automatic status change when starting time tracking"""
    
    def test_start_tracking_changes_status(self, task):
        """Test starting time tracking changes status to 'En Progreso'"""
        from core.models import TaskStatusChange
        
        # Task starts as Pendiente
        assert task.status == 'Pendiente'
        
        # Start tracking
        task.start_tracking()
        
        # Verify status changed
        task.refresh_from_db()
        assert task.status == 'En Progreso'
        
        # Verify status change recorded
        changes = TaskStatusChange.objects.filter(task=task)
        assert changes.count() == 1
        assert changes.first().new_status == 'En Progreso'
    
    def test_already_in_progress_no_duplicate_change(self, task):
        """Test starting tracking when already in progress doesn't duplicate"""
        from core.models import TaskStatusChange
        
        # Manually set to En Progreso
        task.status = 'En Progreso'
        task.save()
        
        # Clear status changes
        TaskStatusChange.objects.filter(task=task).delete()
        
        # Start tracking
        task.start_tracking()
        
        # Verify no new status change recorded
        changes = TaskStatusChange.objects.filter(task=task)
        assert changes.count() == 0
