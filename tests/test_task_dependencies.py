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
    return User.objects.create_user(username="admin", password="pass", is_staff=True)


@pytest.fixture
def project(db):
    return Project.objects.create(name="DepProj", client="Client", start_date=date.today(), address="Addr")


@pytest.fixture
def tasks(db, project, admin_user):
    a = Task.objects.create(project=project, title="A", status="Pending", created_by=admin_user)
    b = Task.objects.create(project=project, title="B", status="Pending", created_by=admin_user)
    c = Task.objects.create(project=project, title="C", status="Pending", created_by=admin_user)
    return a, b, c


@pytest.mark.django_db
def test_create_fs_dependency(api_client, admin_user, tasks):
    api_client.force_authenticate(user=admin_user)
    a, b, _ = tasks
    res = api_client.post(
        "/api/v1/task-dependencies/", {"task": b.id, "predecessor": a.id, "type": "FS", "lag_minutes": 0}, format="json"
    )
    assert res.status_code == 201, res.data
    dep = TaskDependency.objects.get(id=res.data["id"])
    assert dep.task_id == b.id and dep.predecessor_id == a.id


@pytest.mark.django_db
def test_prevent_self_dependency(api_client, admin_user, tasks):
    api_client.force_authenticate(user=admin_user)
    a, _, _ = tasks
    res = api_client.post(
        "/api/v1/task-dependencies/", {"task": a.id, "predecessor": a.id, "type": "FS"}, format="json"
    )
    assert res.status_code == 400


@pytest.mark.django_db
def test_cycle_detection(api_client, admin_user, tasks):
    api_client.force_authenticate(user=admin_user)
    a, b, c = tasks
    # A->B, B->C, try C->A should fail
    api_client.post("/api/v1/task-dependencies/", {"task": b.id, "predecessor": a.id, "type": "FS"}, format="json")
    api_client.post("/api/v1/task-dependencies/", {"task": c.id, "predecessor": b.id, "type": "FS"}, format="json")
    res = api_client.post(
        "/api/v1/task-dependencies/", {"task": a.id, "predecessor": c.id, "type": "FS"}, format="json"
    )
    assert res.status_code == 400


@pytest.mark.django_db
def test_gantt_endpoint(api_client, admin_user, project, tasks):
    api_client.force_authenticate(user=admin_user)
    res = api_client.get(f"/api/v1/tasks/gantt/?project={project.id}")
    assert res.status_code == 200
    assert "tasks" in res.data and "dependencies" in res.data
