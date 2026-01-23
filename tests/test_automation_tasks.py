from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
from django.contrib.auth.models import User
from django.utils import timezone

from core.models import Notification, Project, Task, WeatherSnapshot


@pytest.mark.django_db
def test_update_daily_weather_snapshots():
    """Test weather snapshot creation for active projects."""
    # Create active project
    today = date.today()
    project = Project.objects.create(
        name="Weather Test Project",
        address="123 Main St",
        start_date=today - timedelta(days=10),
        end_date=today + timedelta(days=30),
    )

    # Run task
    from core.tasks import update_daily_weather_snapshots

    result = update_daily_weather_snapshots()

    # Verify snapshot created
    assert result["created"] >= 1
    snapshot = WeatherSnapshot.objects.filter(project=project, date=today).first()
    assert snapshot is not None
    assert snapshot.source == "open-meteo"
    assert snapshot.temperature_max is not None
    assert snapshot.conditions_text is not None


@pytest.mark.django_db
def test_alert_high_priority_touchups_threshold():
    """Test alert generation for projects exceeding touch-up threshold."""
    # Create user and project
    admin = User.objects.create_user(username="admin", is_staff=True, password="pass")
    project = Project.objects.create(name="Touch-up Test", start_date=date.today())

    # Create 4 high-priority touch-ups (above threshold of 3)
    for i in range(4):
        Task.objects.create(project=project, title=f"Touchup {i}", status="Pending", is_touchup=True, priority="high")

    # Run task
    from core.tasks import alert_high_priority_touchups

    result = alert_high_priority_touchups()

    # Verify alert sent to admin
    assert result["alerts_sent"] >= 1
    notif = Notification.objects.filter(
        user=admin, notification_type="task_alert", related_object_id=project.id
    ).first()
    assert notif is not None
    assert "4 high-priority touch-up" in notif.message


@pytest.mark.django_db
def test_alert_high_priority_touchups_below_threshold():
    """Test no alert when touch-ups are below threshold."""
    # Create project with only 2 high-priority touchups (below threshold)
    project = Project.objects.create(name="Low Touch-up", start_date=date.today())

    for i in range(2):
        Task.objects.create(project=project, title=f"Touchup {i}", status="Pending", is_touchup=True, priority="high")

    # Run task
    from core.tasks import alert_high_priority_touchups

    result = alert_high_priority_touchups()

    # Verify no alerts sent (or if sent, not for this project)
    notifs = Notification.objects.filter(notification_type="task_alert", related_object_id=project.id)
    assert notifs.count() == 0
