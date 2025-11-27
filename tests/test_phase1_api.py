"""
Integration tests for Phase 1 API endpoints:
- DailyLog planning operations (instantiate, evaluate)
- TaskTemplate CRUD and create_task action
- WeatherSnapshot retrieval

Run with:
    pytest tests/test_phase1_api.py -v
"""

from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from core.models import DailyLog, Employee, Project, Task, TaskTemplate, WeatherSnapshot

# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def api_client():
    """API client for making requests"""
    return APIClient()


@pytest.fixture
def admin_user(db):
    """Admin user with auth token"""
    user = User.objects.create_user(
        username="admin_api", email="admin@api.com", password="admin123", is_staff=True, is_superuser=True
    )
    return user


@pytest.fixture
def authenticated_client(api_client, admin_user):
    """API client authenticated as admin"""
    api_client.force_authenticate(user=admin_user)
    return api_client


@pytest.fixture
def project(db):
    """Test project"""
    return Project.objects.create(
        name="API Test Project", client="API Client", start_date=date.today(), budget_total=Decimal("20000.00")
    )


@pytest.fixture
def employee(db):
    """Test employee"""
    return Employee.objects.create(
        first_name="John",
        last_name="Worker",
        social_security_number="123-45-6789",
        hourly_rate=Decimal("25.00"),
        is_active=True,
    )


@pytest.fixture
def task_template(db, admin_user):
    """Sample task template"""
    return TaskTemplate.objects.create(
        title="API Test Template",
        description="Template for API testing",
        default_priority="high",
        estimated_hours=Decimal("3.0"),
        tags=["test", "api"],
        checklist=["Step 1", "Step 2"],
        created_by=admin_user,
    )


@pytest.fixture
def daily_log(db, project, admin_user):
    """Sample daily log"""
    return DailyLog.objects.create(
        project=project, date=date.today(), weather="Clear", crew_count=4, created_by=admin_user
    )


# ============================================================================
# TESTS: DailyLog Planning API
# ============================================================================


@pytest.mark.django_db
@pytest.mark.api
class TestDailyLogPlanningAPI:
    """Test DailyLog planning endpoints"""

    def test_list_daily_logs(self, authenticated_client, daily_log):
        """Test listing daily logs"""
        response = authenticated_client.get("/api/v1/daily-logs/")

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) >= 1
        assert any(log["id"] == daily_log.id for log in response.data["results"])

    def test_create_daily_log(self, authenticated_client, project):
        """Test creating a daily log"""
        data = {"project": project.id, "date": date.today().isoformat(), "weather": "Sunny", "crew_count": 5}

        response = authenticated_client.post("/api/v1/daily-logs/", data)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["project"] == project.id
        assert response.data["weather"] == "Sunny"

    def test_instantiate_templates(self, authenticated_client, daily_log, task_template, employee):
        """Test instantiating planned templates"""
        # Add template to daily log
        daily_log.planned_templates.add(task_template)

        url = f"/api/v1/daily-logs/{daily_log.id}/instantiate_templates/"
        data = {"assigned_to_id": employee.id}

        response = authenticated_client.post(url, data)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "ok"
        assert response.data["created_count"] == 1
        assert len(response.data["tasks"]) == 1

        # Verify task was created
        task = Task.objects.get(title=task_template.title, project=daily_log.project)
        assert task is not None
        assert task.assigned_to == employee

    def test_evaluate_completion(self, authenticated_client, daily_log, project, admin_user):
        """Test evaluating daily log completion"""
        # Create completed task
        task = Task.objects.create(project=project, title="Completed Task", status="Completada", created_by=admin_user)
        daily_log.planned_tasks.add(task)

        url = f"/api/v1/daily-logs/{daily_log.id}/evaluate_completion/"
        response = authenticated_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "ok"
        assert response.data["is_complete"] is True
        assert response.data["summary"]["total"] == 1
        assert response.data["summary"]["completed"] == 1

    def test_get_weather(self, authenticated_client, daily_log, project):
        """Test getting weather for daily log"""
        # Create weather snapshot
        snapshot = WeatherSnapshot.objects.create(
            project=project,
            date=daily_log.date,
            source="test",
            temperature_max=Decimal("25.0"),
            conditions_text="Clear",
        )

        url = f"/api/v1/daily-logs/{daily_log.id}/weather/"
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == snapshot.id
        assert response.data["temperature_max"] == "25.00"


# ============================================================================
# TESTS: TaskTemplate API
# ============================================================================


@pytest.mark.django_db
@pytest.mark.api
class TestTaskTemplateAPI:
    """Test TaskTemplate endpoints"""

    def test_list_task_templates(self, authenticated_client, task_template):
        """Test listing task templates"""
        response = authenticated_client.get("/api/v1/task-templates/")

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) >= 1

    def test_create_task_template(self, authenticated_client):
        """Test creating a task template"""
        data = {
            "title": "New Template",
            "description": "Test description",
            "default_priority": "medium",
            "estimated_hours": "2.5",
            "tags": ["new", "test"],
            "checklist": ["Item 1", "Item 2"],
        }

        response = authenticated_client.post("/api/v1/task-templates/", data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["title"] == "New Template"
        assert response.data["default_priority"] == "medium"

    def test_search_task_templates(self, authenticated_client, task_template):
        """Test searching task templates"""
        response = authenticated_client.get("/api/v1/task-templates/?search=API")

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) >= 1
        assert any("API" in tpl["title"] for tpl in response.data["results"])

    def test_create_task_from_template(self, authenticated_client, task_template, project, employee):
        """Test creating a task from template via API"""
        url = f"/api/v1/task-templates/{task_template.id}/create_task/"
        data = {"project_id": project.id, "assigned_to_id": employee.id}

        response = authenticated_client.post(url, data)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["title"] == task_template.title
        assert response.data["project"] == project.id

        # Verify task exists
        task = Task.objects.get(id=response.data["id"])
        assert task.title == task_template.title
        assert task.assigned_to == employee


# ============================================================================
# TESTS: WeatherSnapshot API
# ============================================================================


@pytest.mark.django_db
@pytest.mark.api
class TestWeatherSnapshotAPI:
    """Test WeatherSnapshot endpoints"""

    def test_list_weather_snapshots(self, authenticated_client, project):
        """Test listing weather snapshots"""
        WeatherSnapshot.objects.create(
            project=project, date=date.today(), source="test", temperature_max=Decimal("28.0")
        )

        response = authenticated_client.get("/api/v1/weather-snapshots/")

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) >= 1

    def test_filter_by_project(self, authenticated_client, project):
        """Test filtering weather snapshots by project"""
        WeatherSnapshot.objects.create(
            project=project, date=date.today(), source="test", temperature_max=Decimal("28.0")
        )

        response = authenticated_client.get(f"/api/v1/weather-snapshots/?project={project.id}")

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) >= 1
        assert all(snap["project"] == project.id for snap in response.data["results"])

    def test_by_project_date(self, authenticated_client, project):
        """Test getting snapshot by project and date"""
        snapshot = WeatherSnapshot.objects.create(
            project=project, date=date.today(), source="test", temperature_max=Decimal("30.0"), conditions_text="Hot"
        )

        url = f"/api/v1/weather-snapshots/by_project_date/?project_id={project.id}&date={date.today().isoformat()}"
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == snapshot.id
        assert response.data["temperature_max"] == "30.00"

    def test_by_project_date_not_found(self, authenticated_client, project):
        """Test getting snapshot when none exists"""
        future_date = (date.today() + timedelta(days=30)).isoformat()
        url = f"/api/v1/weather-snapshots/by_project_date/?project_id={project.id}&date={future_date}"

        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND


# ============================================================================
# TESTS: Authentication
# ============================================================================


@pytest.mark.django_db
@pytest.mark.api
class TestAPIAuthentication:
    """Test API authentication requirements"""

    def test_unauthenticated_access_denied(self, api_client):
        """Test that unauthenticated requests are denied"""
        response = api_client.get("/api/v1/daily-logs/")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_authenticated_access_allowed(self, authenticated_client):
        """Test that authenticated requests are allowed"""
        response = authenticated_client.get("/api/v1/daily-logs/")

        assert response.status_code == status.HTTP_200_OK
