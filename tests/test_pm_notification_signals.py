"""
Test Project Manager notifications on task status change (Q11.10)
"""

from datetime import date
from decimal import Decimal

import pytest
from django.contrib.auth.models import User

from core.models import Project, ProjectManagerAssignment, Task, Notification


@pytest.fixture
def admin_user(db):
    """Admin user for testing"""
    return User.objects.create_user(
        username="admin_pm_test",
        email="admin@test.com",
        password="admin123",
        is_staff=True,
        is_superuser=True
    )


@pytest.fixture
def task_creator(db):
    """Regular user who creates tasks"""
    return User.objects.create_user(
        username="task_creator",
        email="creator@test.com",
        password="creator123"
    )


@pytest.fixture
def pm_user(db):
    """Project manager user"""
    return User.objects.create_user(
        username="pm_user",
        email="pm@test.com",
        password="pm123"
    )


@pytest.fixture
def project(db):
    """Test project"""
    return Project.objects.create(
        name="Test Project PM",
        client="Test Client",
        start_date=date.today(),
        budget_total=Decimal("10000.00")
    )


@pytest.mark.django_db
@pytest.mark.unit
@pytest.mark.module_11
class TestProjectManagerNotifications:
    """Test PM notifications on task status changes (Q11.10)"""

    def test_pm_receives_notification_on_task_status_change(
        self, project, task_creator, pm_user, admin_user
    ):
        """Test that PM receives notification when task status changes"""
        # Assign PM to project
        ProjectManagerAssignment.objects.create(
            project=project,
            pm=pm_user,
            role="project_manager"
        )

        # Create task
        task = Task.objects.create(
            project=project,
            title="Test Task for PM Notification",
            description="Testing PM notifications",
            status="Pendiente",
            created_by=task_creator
        )

        # Clear any notifications from task creation
        Notification.objects.all().delete()

        # Change task status (by admin)
        task._changed_by = admin_user
        task.status = "En Progreso"
        task.save()

        # Verify PM received notification
        pm_notifications = Notification.objects.filter(
            user=pm_user,
            related_object_type="Task",
            related_object_id=task.pk
        )
        assert pm_notifications.count() >= 1

        # Verify notification content
        notif = pm_notifications.first()
        assert "En Progreso" in notif.message
        assert task.title in notif.message

    def test_multiple_pms_receive_notifications(
        self, project, task_creator, admin_user
    ):
        """Test that all PMs assigned to project receive notifications"""
        # Create two PM users
        pm1 = User.objects.create_user(
            username="pm1",
            email="pm1@test.com",
            password="pm123"
        )
        pm2 = User.objects.create_user(
            username="pm2",
            email="pm2@test.com",
            password="pm123"
        )

        # Assign both PMs to project
        ProjectManagerAssignment.objects.create(
            project=project,
            pm=pm1,
            role="project_manager"
        )
        ProjectManagerAssignment.objects.create(
            project=project,
            pm=pm2,
            role="lead_pm"
        )

        # Create task
        task = Task.objects.create(
            project=project,
            title="Multi-PM Task",
            status="Pendiente",
            created_by=task_creator
        )

        # Clear notifications
        Notification.objects.all().delete()

        # Change status
        task._changed_by = admin_user
        task.status = "Completada"
        task.save()

        # Verify both PMs received notifications
        pm1_notifs = Notification.objects.filter(
            user=pm1,
            related_object_type="Task",
            related_object_id=task.pk
        )
        pm2_notifs = Notification.objects.filter(
            user=pm2,
            related_object_type="Task",
            related_object_id=task.pk
        )

        assert pm1_notifs.count() >= 1
        assert pm2_notifs.count() >= 1

    def test_pm_does_not_receive_self_notification(
        self, project, pm_user
    ):
        """Test PM doesn't receive notification for their own status change"""
        # Assign PM to project
        ProjectManagerAssignment.objects.create(
            project=project,
            pm=pm_user,
            role="project_manager"
        )

        # Create task
        task = Task.objects.create(
            project=project,
            title="PM Self-Change Task",
            status="Pendiente",
            created_by=pm_user
        )

        # Clear notifications
        Notification.objects.all().delete()

        # PM changes status themselves
        task._changed_by = pm_user
        task.status = "Completada"
        task.save()

        # Verify PM did not receive notification
        pm_notifications = Notification.objects.filter(
            user=pm_user,
            related_object_type="Task",
            related_object_id=task.pk
        )
        assert pm_notifications.count() == 0

    def test_project_without_pm_no_errors(
        self, project, task_creator, admin_user
    ):
        """Test that project without PM assignment doesn't cause errors"""
        # Create task (project has no PM assigned)
        task = Task.objects.create(
            project=project,
            title="No PM Task",
            status="Pendiente",
            created_by=task_creator
        )

        # Clear notifications
        Notification.objects.all().delete()

        # Change status - should not cause error
        task._changed_by = admin_user
        task.status = "En Progreso"
        task.save()

        # Only creator should receive notification, no PM notifications
        all_notifs = Notification.objects.filter(
            related_object_type="Task",
            related_object_id=task.pk
        )
        assert all_notifs.count() >= 1  # At least creator received notification
        
        # Verify notification went to creator
        creator_notifs = all_notifs.filter(user=task_creator)
        assert creator_notifs.count() >= 1

    def test_creator_and_pm_both_receive_notifications(
        self, project, task_creator, pm_user, admin_user
    ):
        """Test both creator and PM receive distinct notifications"""
        # Assign PM to project
        ProjectManagerAssignment.objects.create(
            project=project,
            pm=pm_user,
            role="project_manager"
        )

        # Create task
        task = Task.objects.create(
            project=project,
            title="Dual Notification Task",
            status="Pendiente",
            created_by=task_creator
        )

        # Clear notifications
        Notification.objects.all().delete()

        # Change status (by admin, not creator or PM)
        task._changed_by = admin_user
        task.status = "En Progreso"
        task.save()

        # Verify both received notifications
        creator_notifs = Notification.objects.filter(
            user=task_creator,
            related_object_type="Task",
            related_object_id=task.pk
        )
        pm_notifs = Notification.objects.filter(
            user=pm_user,
            related_object_type="Task",
            related_object_id=task.pk
        )

        assert creator_notifs.count() >= 1, "Creator should receive notification"
        assert pm_notifs.count() >= 1, "PM should receive notification"

        # Verify distinct notifications
        assert creator_notifs.first().user == task_creator
        assert pm_notifs.first().user == pm_user
