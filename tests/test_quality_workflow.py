import pytest
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal

from core.models import Project, Task, Employee, Profile


@pytest.mark.django_db
def test_task_auto_in_review_on_100_progress():
    project = Project.objects.create(name="QC Project", start_date=timezone.now().date())
    emp = Employee.objects.create(first_name="Ana", last_name="Tester", social_security_number="123", hourly_rate=Decimal("20.00"))
    task = Task.objects.create(project=project, title="QC Task", assigned_to=emp, status="In Progress", progress_percent=0)
    task.progress_percent = 100
    task.save()
    assert task.status == "Under Review"


@pytest.mark.django_db
def test_task_approve_sets_completed_and_visible():
    project = Project.objects.create(name="QC Project", start_date=timezone.now().date())
    pm = User.objects.create(username="pm", is_staff=True)
    task = Task.objects.create(project=project, title="QC Approve", status="Under Review", progress_percent=100)
    task.approve_by_pm(pm)
    task.refresh_from_db()
    assert task.status == "Completed"
    assert task.is_visible_to_client is True
    assert task.completed_at is not None


@pytest.mark.django_db
def test_task_reject_sets_in_progress_and_increments_profile_rejections():
    project = Project.objects.create(name="QC Project", start_date=timezone.now().date())
    user = User.objects.create(username="worker")
    Profile.objects.filter(user=user).update(role="employee")
    emp = Employee.objects.create(user=user, first_name="Ana", last_name="Tester", social_security_number="456", hourly_rate=Decimal("20.00"))
    task = Task.objects.create(project=project, title="QC Reject", assigned_to=emp, status="Under Review", progress_percent=100)
    task.reject_by_pm(user, reason="Needs rework")
    task.refresh_from_db()
    prof = Profile.objects.get(user=user)
    assert task.status == "In Progress"
    assert task.progress_percent == 50
    assert prof.rejections_count >= 1


@pytest.mark.django_db
def test_task_dependency_warning_flag():
    project = Project.objects.create(name="QC Project", start_date=timezone.now().date())
    t1 = Task.objects.create(project=project, title="Predecessor", status="Pending")
    t2 = Task.objects.create(project=project, title="Successor", status="Pending")
    # Set predecessor not completed
    t2.dependencies.add(t1)
    assert t2.can_start() is False
