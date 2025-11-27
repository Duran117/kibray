"""
Focused API tests for Module 11 (Tasks)
Covers serializer write-paths and custom actions to raise coverage.
"""

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from core.models import Project, Task


@pytest.fixture
def api_client(db):
    return APIClient()


@pytest.fixture
def user(db, django_user_model):
    return django_user_model.objects.create_user(username="apiuser", password="pass12345")


@pytest.fixture
def project(db):
    from datetime import date

    return Project.objects.create(name="API Project", start_date=date.today())


@pytest.mark.django_db
@pytest.mark.api
@pytest.mark.module_11
def test_task_create_with_dependencies_and_priority_due_date(api_client, user, project):
    api_client.force_authenticate(user=user)

    # Create dependency tasks
    dep1 = Task.objects.create(project=project, title="Dep 1")
    dep2 = Task.objects.create(project=project, title="Dep 2", status="Completada")

    payload = {
        "project": project.id,
        "title": "Main Task",
        "description": "Created via API",
        "priority": "urgent",
        "due_date": "2030-01-15",
        "dependencies": [dep1.id, dep2.id],
    }

    resp = api_client.post("/api/v1/tasks/", data=payload, format="json")
    assert resp.status_code in (201, 200)
    data = resp.json()
    assert data["title"] == "Main Task"
    assert data["priority"] == "urgent"
    assert data["due_date"] == "2030-01-15"
    assert set(data["dependencies_ids"]) == {dep1.id, dep2.id}
    assert data["reopen_events_count"] == 0


@pytest.mark.django_db
@pytest.mark.api
@pytest.mark.module_11
def test_task_update_dependencies_via_serializer(api_client, user, project):
    api_client.force_authenticate(user=user)

    depA = Task.objects.create(project=project, title="Dep A")
    depB = Task.objects.create(project=project, title="Dep B")
    t = Task.objects.create(project=project, title="Has deps")

    # Set both deps
    resp = api_client.patch(
        f"/api/v1/tasks/{t.id}/",
        data={"dependencies": [depA.id, depB.id]},
        format="json",
    )
    assert resp.status_code in (200, 202)
    data = resp.json()
    assert set(data["dependencies_ids"]) == {depA.id, depB.id}

    # Now keep only A
    resp = api_client.patch(
        f"/api/v1/tasks/{t.id}/",
        data={"dependencies": [depA.id]},
        format="json",
    )
    assert resp.status_code in (200, 202)
    data = resp.json()
    assert set(data["dependencies_ids"]) == {depA.id}


@pytest.mark.django_db
@pytest.mark.api
@pytest.mark.module_11
def test_task_reopen_action_increments_counter(api_client, user, project):
    api_client.force_authenticate(user=user)

    task = Task.objects.create(
        project=project,
        title="Completed",
        status="Completada",
        completed_at=timezone.now(),
        created_by=user,
    )

    # Reopen via action
    resp = api_client.post(f"/api/v1/tasks/{task.id}/reopen/", data={"notes": "QA found issues"}, format="json")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["new_status"] in ["En Progreso", "Pendiente"]
    assert data["reopen_events_count"] >= 1


@pytest.mark.django_db
@pytest.mark.api
@pytest.mark.module_11
def test_task_start_stop_tracking_actions(api_client, user, project):
    api_client.force_authenticate(user=user)

    task = Task.objects.create(project=project, title="Track Me", status="Pendiente")

    # Start tracking
    r1 = api_client.post(f"/api/v1/tasks/{task.id}/start_tracking/")
    assert r1.status_code == 200
    data1 = r1.json()
    assert data1["status"] == "ok"
    assert data1["started_at"]

    # Stop tracking
    r2 = api_client.post(f"/api/v1/tasks/{task.id}/stop_tracking/")
    assert r2.status_code == 200
    data2 = r2.json()
    assert data2["status"] == "ok"
    assert data2["elapsed_seconds"] >= 1
    assert data2["total_hours"] >= 0


@pytest.mark.django_db
@pytest.mark.api
@pytest.mark.module_11
def test_task_add_remove_dependency_actions(api_client, user, project):
    api_client.force_authenticate(user=user)

    dep = Task.objects.create(project=project, title="Dependency")
    t = Task.objects.create(project=project, title="Has actions")

    # Add dependency
    r_add = api_client.post(f"/api/v1/tasks/{t.id}/add_dependency/", data={"dependency_id": dep.id}, format="json")
    assert r_add.status_code == 200
    assert dep.id in r_add.json().get("dependencies", [])

    # Remove dependency
    r_rem = api_client.post(
        f"/api/v1/tasks/{t.id}/remove_dependency/", data={"dependency_id": dep.id}, format="json"
    )
    assert r_rem.status_code == 200
    assert dep.id not in r_rem.json().get("dependencies", [])


@pytest.mark.django_db
@pytest.mark.api
@pytest.mark.module_11
def test_task_time_summary_endpoint(api_client, user, project):
    api_client.force_authenticate(user=user)

    t = Task.objects.create(project=project, title="Summary")
    r = api_client.get(f"/api/v1/tasks/{t.id}/time_summary/")
    assert r.status_code == 200
    data = r.json()
    for key in [
        "task_id",
        "task_title",
        "internal_tracking_hours",
        "time_entry_hours",
        "total_hours",
        "employee_breakdown",
        "is_tracking_active",
        "reopen_count",
    ]:
        assert key in data


@pytest.mark.django_db
@pytest.mark.api
@pytest.mark.module_11
def test_touchup_board_structure(api_client, user, project):
    api_client.force_authenticate(user=user)

    # Create some touch-up tasks
    Task.objects.create(project=project, title="T1", is_touchup=True)
    Task.objects.create(project=project, title="T2", is_touchup=True, status="En Progreso")
    Task.objects.create(project=project, title="T3", is_touchup=True, status="Completada")

    r = api_client.get("/api/v1/tasks/touchup_board/")
    assert r.status_code == 200
    data = r.json()
    assert "columns" in data and "totals" in data
    assert len(data["columns"]) == 3


@pytest.mark.django_db
@pytest.mark.api
@pytest.mark.module_11
def test_tasks_gantt_endpoint(api_client, user, project):
    api_client.force_authenticate(user=user)

    t1 = Task.objects.create(project=project, title="Gantt 1")
    t2 = Task.objects.create(project=project, title="Gantt 2")

    r = api_client.get("/api/v1/tasks/gantt/")
    assert r.status_code == 200
    data = r.json()
    assert "tasks" in data and "dependencies" in data
    ids = {t["id"] for t in data["tasks"]}
    assert t1.id in ids and t2.id in ids
