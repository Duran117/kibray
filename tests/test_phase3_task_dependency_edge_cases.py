"""
PHASE 3 verification: Additional edge case tests for TaskDependency
- Multiple dependencies of the same type between two tasks should be rejected
- Lag time boundary cases
"""
from datetime import date

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from core.models import Project, Task, TaskDependency

User = get_user_model()


@pytest.fixture
def api_client(db):
    return APIClient()


@pytest.fixture
def admin_user(db):
    return User.objects.create_user(username="admin_phase3", password="pass", is_staff=True)


@pytest.fixture
def project(db):
    return Project.objects.create(name="Phase3TestProj", client="TestClient", start_date=date.today(), address="Addr")


@pytest.fixture
def tasks(db, project, admin_user):
    a = Task.objects.create(project=project, title="TaskA", status="Pendiente", created_by=admin_user)
    b = Task.objects.create(project=project, title="TaskB", status="Pendiente", created_by=admin_user)
    return a, b


@pytest.mark.django_db
def test_duplicate_dependency_type_rejected(api_client, admin_user, tasks):
    """Q11.7 edge case: Cannot create duplicate dependency (task, predecessor, type) combo."""
    api_client.force_authenticate(user=admin_user)
    a, b = tasks
    # Create FS dependency A -> B
    res1 = api_client.post(
        "/api/v1/task-dependencies/", {"task": b.id, "predecessor": a.id, "type": "FS", "lag_minutes": 0}, format="json"
    )
    assert res1.status_code == 201, res1.data
    # Try creating duplicate FS A -> B (should fail due to unique_together)
    res2 = api_client.post(
        "/api/v1/task-dependencies/", {"task": b.id, "predecessor": a.id, "type": "FS", "lag_minutes": 10}, format="json"
    )
    assert res2.status_code == 400, "Duplicate dependency (same task, predecessor, type) should be rejected"


@pytest.mark.django_db
def test_large_positive_lag(api_client, admin_user, tasks):
    """Q11.7 edge case: Large positive lag (e.g., 1 month = 43200 minutes) should be allowed."""
    api_client.force_authenticate(user=admin_user)
    a, b = tasks
    large_lag = 43200  # 30 days in minutes
    res = api_client.post(
        "/api/v1/task-dependencies/", {"task": b.id, "predecessor": a.id, "type": "FS", "lag_minutes": large_lag}, format="json"
    )
    assert res.status_code == 201, res.data
    dep = TaskDependency.objects.get(id=res.data["id"])
    assert dep.lag_minutes == large_lag


@pytest.mark.django_db
def test_negative_lag_allowed(api_client, admin_user, tasks):
    """Q11.7 edge case: Negative lag (overlap) should be allowed (e.g., -120 means start 2h before predecessor ends)."""
    api_client.force_authenticate(user=admin_user)
    a, b = tasks
    negative_lag = -120  # 2 hours overlap
    res = api_client.post(
        "/api/v1/task-dependencies/", {"task": b.id, "predecessor": a.id, "type": "FS", "lag_minutes": negative_lag}, format="json"
    )
    assert res.status_code == 201, res.data
    dep = TaskDependency.objects.get(id=res.data["id"])
    assert dep.lag_minutes == negative_lag
