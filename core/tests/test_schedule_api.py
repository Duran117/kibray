import json
from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from django.contrib.auth import get_user_model

from core.models import Project, SchedulePhaseV2, ScheduleItemV2, Task


@pytest.mark.django_db
def test_master_schedule_api_returns_projects_items_and_events():
    today = timezone.localdate()
    User = get_user_model()
    user = User.objects.create_user(username="admin", password="pass", is_staff=True)

    project = Project.objects.create(
        name="Test Project",
        client="ACME",
        start_date=today,
        end_date=today + timedelta(days=30),
    )

    phase = SchedulePhaseV2.objects.create(project=project, name="Phase 1", order=0)
    ScheduleItemV2.objects.create(
        project=project,
        phase=phase,
        name="Milestone A",
        start_date=today + timedelta(days=1),
        end_date=today + timedelta(days=3),
        status="in_progress",
        progress=40,
        is_milestone=True,
    )

    Task.objects.create(
        project=project,
        title="Urgent task",
        due_date=today + timedelta(days=2),
        priority="high",
    )

    client = APIClient()
    client.force_authenticate(user=user)
    url = reverse("api-schedule-master")

    response = client.get(url)
    assert response.status_code == 200

    data = response.json()
    assert data["metadata"]["total_projects"] == 1
    assert data["metadata"]["total_schedule_items"] == 1

    assert len(data["projects"]) == 1
    assert any(ev.get("type") == "schedule_item" for ev in data["events"])
    assert any(ev.get("type") == "task" for ev in data["events"])
