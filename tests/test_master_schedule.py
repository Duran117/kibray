"""
Tests for Master Schedule Center
Validates view access control, API (legacy + V2), and frontend rendering.
"""
from datetime import date, timedelta

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient

from core.models import Project, ScheduleItemV2, SchedulePhaseV2

User = get_user_model()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def admin_user(db):
    return User.objects.create_user(
        username="admin_test", password="testpass123",
        is_staff=True, is_superuser=True,
    )


@pytest.fixture
def regular_user(db):
    return User.objects.create_user(
        username="regular_test", password="testpass123",
        is_staff=False, is_superuser=False,
    )


@pytest.fixture
def test_project(db):
    return Project.objects.create(
        name="Test Project Alpha",
        start_date=date.today() - timedelta(days=30),
        end_date=date.today() + timedelta(days=60),
        is_archived=False,
    )


@pytest.fixture
def test_phase(db, test_project):
    return SchedulePhaseV2.objects.create(
        project=test_project, name="Phase 1", color="#3b82f6", order=0,
    )


@pytest.fixture
def test_item(db, test_project, test_phase):
    return ScheduleItemV2.objects.create(
        project=test_project, phase=test_phase, name="Foundation",
        start_date=date.today(), end_date=date.today() + timedelta(days=14),
        status="in_progress", progress=30, order=0,
    )


# ---------------------------------------------------------------------------
# View access control
# ---------------------------------------------------------------------------

class TestMasterScheduleAccess:

    def test_anonymous_user_redirected(self, client):
        url = reverse("master_schedule_center")
        response = client.get(url)
        assert response.status_code == 302
        assert "/login/" in response.url

    def test_regular_user_denied(self, client, regular_user):
        client.force_login(regular_user)
        url = reverse("master_schedule_center")
        response = client.get(url)
        assert response.status_code == 302
        assert response.url == reverse("dashboard")

    def test_admin_user_allowed(self, client, admin_user):
        client.force_login(admin_user)
        url = reverse("master_schedule_center")
        response = client.get(url)
        assert response.status_code == 200
        assert "Master Schedule" in response.content.decode()

    def test_staff_user_allowed(self, client, db):
        staff = User.objects.create_user(
            username="staff_test", password="testpass123", is_staff=True,
        )
        client.force_login(staff)
        url = reverse("master_schedule_center")
        response = client.get(url)
        assert response.status_code == 200


# ---------------------------------------------------------------------------
# Legacy API  /api/v1/schedule/master/
# ---------------------------------------------------------------------------

class TestMasterScheduleLegacyAPI:

    def test_api_requires_authentication(self, client):
        response = client.get("/api/v1/schedule/master/")
        assert response.status_code in [302, 401, 403]

    def test_api_returns_valid_structure(self, client, admin_user, test_project):
        client.force_login(admin_user)
        response = client.get("/api/v1/schedule/master/")
        assert response.status_code == 200
        data = response.json()
        assert "projects" in data
        assert "events" in data
        assert "metadata" in data

    def test_api_excludes_archived_projects(self, client, admin_user, test_project):
        Project.objects.create(
            name="Archived", start_date=date.today(),
            end_date=date.today() + timedelta(days=30), is_archived=True,
        )
        client.force_login(admin_user)
        data = client.get("/api/v1/schedule/master/").json()
        names = {p["name"] for p in data["projects"]}
        assert "Archived" not in names
        assert test_project.name in names


# ---------------------------------------------------------------------------
# V2 API  /api/v1/gantt/v2/master/  (React Gantt)
# ---------------------------------------------------------------------------

class TestMasterGanttV2API:

    def test_requires_staff(self, db):
        regular = User.objects.create_user(username="u", password="p")
        api = APIClient()
        api.force_authenticate(user=regular)
        resp = api.get("/api/v1/gantt/v2/master/")
        assert resp.status_code == 403

    def test_staff_can_access(self, db, admin_user):
        api = APIClient()
        api.force_authenticate(user=admin_user)
        resp = api.get("/api/v1/gantt/v2/master/")
        assert resp.status_code == 200

    def test_returns_v2_structure(self, admin_user, test_project, test_item):
        api = APIClient()
        api.force_authenticate(user=admin_user)
        data = api.get("/api/v1/gantt/v2/master/").json()
        assert "phases" in data
        assert "dependencies" in data
        assert "metadata" in data
        assert len(data["phases"]) >= 1
        phase = data["phases"][0]
        assert phase["name"] == test_project.name
        assert "items" in phase
        assert len(phase["items"]) == 1
        assert phase["items"][0]["name"] == "Foundation"

    def test_excludes_archived(self, admin_user, test_project, test_item):
        Project.objects.create(
            name="Old", start_date=date.today(),
            end_date=date.today() + timedelta(days=10), is_archived=True,
        )
        api = APIClient()
        api.force_authenticate(user=admin_user)
        data = api.get("/api/v1/gantt/v2/master/").json()
        names = {p["name"] for p in data["phases"]}
        assert "Old" not in names

    def test_metadata_counts(self, admin_user, test_project, test_item):
        api = APIClient()
        api.force_authenticate(user=admin_user)
        data = api.get("/api/v1/gantt/v2/master/").json()
        assert data["metadata"]["items_count"] == 1


# ---------------------------------------------------------------------------
# Frontend rendering (React Gantt template)
# ---------------------------------------------------------------------------

class TestMasterScheduleFrontend:

    def test_page_includes_gantt_container(self, client, admin_user):
        client.force_login(admin_user)
        content = client.get(reverse("master_schedule_center")).content.decode()
        assert 'id="gantt-app-root"' in content

    def test_page_includes_react_bundle(self, client, admin_user):
        client.force_login(admin_user)
        content = client.get(reverse("master_schedule_center")).content.decode()
        assert "gantt-app.iife.js" in content

    def test_page_mounts_master_mode(self, client, admin_user):
        client.force_login(admin_user)
        content = client.get(reverse("master_schedule_center")).content.decode()
        assert "mode: 'master'" in content
        assert "canEdit: true" in content
