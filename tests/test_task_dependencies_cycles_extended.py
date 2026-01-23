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
    return User.objects.create_user(username="admin2", password="pass", is_staff=True)


@pytest.fixture
def project(db):
    return Project.objects.create(name="DepProj2", client="Client", start_date=date.today(), address="Addr")


@pytest.fixture
def tasks(db, project, admin_user):
    a = Task.objects.create(project=project, title="X", status="Pending", created_by=admin_user)
    b = Task.objects.create(project=project, title="Y", status="Pending", created_by=admin_user)
    c = Task.objects.create(project=project, title="Z", status="Pending", created_by=admin_user)
    return a, b, c


@pytest.mark.django_db
def test_duplicate_dependency_same_type_rejected(api_client, admin_user, tasks):
    api_client.force_authenticate(user=admin_user)
    a, b, _ = tasks
    first = api_client.post(
        "/api/v1/task-dependencies/", {"task": b.id, "predecessor": a.id, "type": "FS"}, format="json"
    )
    assert first.status_code == 201
    dup = api_client.post(
        "/api/v1/task-dependencies/", {"task": b.id, "predecessor": a.id, "type": "FS"}, format="json"
    )
    # Should violate unique_together
    assert dup.status_code in (400, 422)


@pytest.mark.django_db
def test_duplicate_dependency_different_type_allowed(api_client, admin_user, tasks):
    api_client.force_authenticate(user=admin_user)
    a, b, _ = tasks
    fs = api_client.post("/api/v1/task-dependencies/", {"task": b.id, "predecessor": a.id, "type": "FS"}, format="json")
    assert fs.status_code == 201
    ss = api_client.post("/api/v1/task-dependencies/", {"task": b.id, "predecessor": a.id, "type": "SS"}, format="json")
    assert ss.status_code == 201
    # Ensure both rows exist
    deps = TaskDependency.objects.filter(task=b, predecessor=a).values_list("type", flat=True)
    assert set(deps) == {"FS", "SS"}


@pytest.mark.django_db
def test_cycle_detection_with_mixed_types(api_client, admin_user, tasks):
    api_client.force_authenticate(user=admin_user)
    a, b, c = tasks
    api_client.post("/api/v1/task-dependencies/", {"task": b.id, "predecessor": a.id, "type": "FS"}, format="json")
    api_client.post("/api/v1/task-dependencies/", {"task": c.id, "predecessor": b.id, "type": "SS"}, format="json")
    # Attempt closing cycle with different type
    cycle = api_client.post(
        "/api/v1/task-dependencies/", {"task": a.id, "predecessor": c.id, "type": "FF"}, format="json"
    )
    assert cycle.status_code == 400


@pytest.mark.django_db
def test_would_create_cycle_static_method(tasks):
    a, b, c = tasks
    # Build A->B, B->C manually
    TaskDependency.objects.create(task=b, predecessor=a, type="FS")
    TaskDependency.objects.create(task=c, predecessor=b, type="FS")
    # Proposed C->A should detect cycle
    assert TaskDependency.would_create_cycle(a.id, c.id) is True
    # Proposed A->C (no direct path C->A yet) should be False
    assert TaskDependency.would_create_cycle(c.id, a.id) is False


@pytest.mark.django_db
def test_dependency_lag_update(api_client, admin_user, tasks):
    api_client.force_authenticate(user=admin_user)
    a, b, _ = tasks
    res = api_client.post(
        "/api/v1/task-dependencies/", {"task": b.id, "predecessor": a.id, "type": "FS", "lag_minutes": 0}, format="json"
    )
    assert res.status_code == 201
    dep_id = res.data["id"]
    # Update lag
    patch = api_client.patch(f"/api/v1/task-dependencies/{dep_id}/", {"lag_minutes": 120}, format="json")
    assert patch.status_code == 200
    assert patch.data["lag_minutes"] == 120
