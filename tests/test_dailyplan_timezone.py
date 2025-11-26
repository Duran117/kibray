import pytest
from datetime import timedelta
from django.utils import timezone

@pytest.mark.django_db
def test_dailyplan_completion_deadline_normalized(django_user_model):
    from core.models import Project, DailyPlan
    user = django_user_model.objects.create_user(username='dpuser', password='x')
    project = Project.objects.create(name='TZProj', client='ClientTZ', start_date=timezone.now().date())

    naive_deadline = (timezone.now() + timedelta(hours=2)).replace(tzinfo=None)
    dp = DailyPlan.objects.create(project=project, plan_date=timezone.now().date(), completion_deadline=naive_deadline, created_by=user)

    assert dp.completion_deadline.tzinfo is not None
    # Confirm aware comparison doesn't raise
    assert dp.completion_deadline > timezone.now() - timedelta(days=1)
