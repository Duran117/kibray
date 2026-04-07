from datetime import date, timedelta

import pytest
from django.apps import apps
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()


def get_model(model_name):
    return apps.get_model("core", model_name)


@pytest.fixture
def api_client():
    user = User.objects.create_user(username="pm_gantt", password="pass123", email="pm@example.com")
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def project():
    Project = get_model("Project")
    return Project.objects.create(name="Gantt V2 Project", start_date=date.today())


@pytest.fixture
def phase(project):
    SchedulePhaseV2 = get_model("SchedulePhaseV2")
    return SchedulePhaseV2.objects.create(project=project, name="Phase 1", order=1)


def make_item(phase, project, name, start_offset, end_offset, assigned_to=None, order=0):
    ScheduleItemV2 = get_model("ScheduleItemV2")
    return ScheduleItemV2.objects.create(
        project=project,
        phase=phase,
        name=name,
        start_date=date.today() + timedelta(days=start_offset),
        end_date=date.today() + timedelta(days=end_offset),
        assigned_to=assigned_to,
        order=order,
    )


@pytest.mark.django_db
class TestGanttV2ReadOnly:
    def test_returns_items_and_dependencies_without_filters(self, api_client, project, phase):
        user_a = User.objects.create_user(username="assignee_a")
        user_b = User.objects.create_user(username="assignee_b")

        item_a = make_item(phase, project, "Item A", 0, 5, assigned_to=user_a, order=1)
        item_b = make_item(phase, project, "Item B", 3, 9, assigned_to=user_b, order=2)

        ScheduleTaskV2 = get_model("ScheduleTaskV2")
        ScheduleDependencyV2 = get_model("ScheduleDependencyV2")

        ScheduleTaskV2.objects.create(item=item_a, title="Task A1", order=1)
        ScheduleTaskV2.objects.create(item=item_b, title="Task B1", order=1)
        ScheduleDependencyV2.objects.create(source_item=item_a, target_item=item_b)

        res = api_client.get(f"/api/v1/gantt/v2/projects/{project.id}/")

        assert res.status_code == 200
        data = res.json()
        assert data["metadata"]["items_count"] == 2
        assert data["metadata"]["dependencies_count"] == 1
        assert len(data["phases"]) == 1
        assert len(data["phases"][0]["items"]) == 2
        assert len(data["dependencies"]) == 1

    def test_filters_by_assigned_user_and_trims_dependencies(self, api_client, project, phase):
        user_a = User.objects.create_user(username="assignee_a")
        user_b = User.objects.create_user(username="assignee_b")

        item_a = make_item(phase, project, "Item A", 0, 5, assigned_to=user_a, order=1)
        item_b = make_item(phase, project, "Item B", 0, 5, assigned_to=user_b, order=2)
        ScheduleDependencyV2 = get_model("ScheduleDependencyV2")
        ScheduleDependencyV2.objects.create(source_item=item_a, target_item=item_b)

        res = api_client.get(f"/api/v1/gantt/v2/projects/{project.id}/?assigned_to={user_a.id}")

        assert res.status_code == 200
        data = res.json()
        assert data["metadata"]["items_count"] == 1
        assert len(data["phases"][0]["items"]) == 1
        # Dependency trimmed because target not included in filtered set
        assert data["metadata"]["dependencies_count"] == 0
        assert len(data["dependencies"]) == 0

    def test_filters_by_date_range_overlap(self, api_client, project, phase):
        user_a = User.objects.create_user(username="assignee_a")
        item_in = make_item(phase, project, "In Range", 0, 4, assigned_to=user_a, order=1)
        item_out = make_item(phase, project, "Out of Range", 10, 15, order=2)
        ScheduleTaskV2 = get_model("ScheduleTaskV2")
        ScheduleDependencyV2 = get_model("ScheduleDependencyV2")
        ScheduleTaskV2.objects.create(item=item_in, title="Task In", order=1)
        ScheduleDependencyV2.objects.create(source_item=item_in, target_item=item_out)

        start = date.today() + timedelta(days=-1)
        end = date.today() + timedelta(days=6)
        res = api_client.get(
            f"/api/v1/gantt/v2/projects/{project.id}/?start_date={start.isoformat()}&end_date={end.isoformat()}"
        )

        assert res.status_code == 200
        data = res.json()
        assert data["metadata"]["items_count"] == 1
        items = data["phases"][0]["items"]
        assert len(items) == 1
        assert items[0]["name"] == "In Range"
        # Dependency trimmed because target item is outside filtered range
        assert data["metadata"]["dependencies_count"] == 0
        assert len(data["dependencies"]) == 0
