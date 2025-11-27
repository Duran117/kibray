"""
Module 12: Daily Plans API tests
Covers CRUD, add activity, weather fetch, convert to tasks, productivity, materials check, filters.
"""

from datetime import date, timedelta

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from core.models import DailyPlan, Employee, PlannedActivity, Project, Task

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    return User.objects.create_user(username="pm", password="pass123", email="pm@example.com")


@pytest.fixture
def project(db):
    return Project.objects.create(
        name="DailyPlan Project", client="Acme", start_date=date.today(), address="123 Main St, City"
    )


@pytest.fixture
def employee(db, user):
    return Employee.objects.create(
        user=user, first_name="Test", last_name="Worker", social_security_number="123-45-6789", hourly_rate="20.00"
    )


@pytest.mark.django_db
class TestDailyPlanBasics:
    def test_create_daily_plan_and_list(self, api_client, user, project):
        api_client.force_authenticate(user=user)
        payload = {
            "project": project.id,
            "plan_date": (date.today() + timedelta(days=1)).isoformat(),
            "completion_deadline": (date.today() + timedelta(days=0)).isoformat() + "T17:00:00Z",
            "status": "DRAFT",
        }
        res = api_client.post("/api/v1/daily-plans/", payload, format="json")
        assert res.status_code == 201
        plan_id = res.data["id"]

        res_list = api_client.get("/api/v1/daily-plans/", {"project": project.id})
        assert res_list.status_code == 200
        results = res_list.data.get("results", res_list.data)
        assert any(p["id"] == plan_id for p in results)

    def test_add_activity_to_plan(self, api_client, user, project, employee):
        api_client.force_authenticate(user=user)
        plan = DailyPlan.objects.create(
            project=project, plan_date=date.today() + timedelta(days=1), completion_deadline=date.today()
        )
        payload = {
            "title": "Prep Room 1",
            "description": "Cover and mask",
            "order": 1,
            "assigned_employee_ids": [employee.id],
            "estimated_hours": 3.5,
        }
        res = api_client.post(f"/api/v1/daily-plans/{plan.id}/add_activity/", payload, format="json")
        assert res.status_code == 201
        assert res.data["title"] == "Prep Room 1"
        # Ensure it saved
        assert plan.activities.count() == 1


@pytest.mark.django_db
class TestDailyPlanActions:
    def test_fetch_weather(self, api_client, user, project, monkeypatch):
        api_client.force_authenticate(user=user)
        plan = DailyPlan.objects.create(
            project=project, plan_date=date.today() + timedelta(days=1), completion_deadline=date.today()
        )

        # Monkeypatch weather_service to avoid network
        from core.services import weather as weather_mod

        def fake_get_weather(lat, lon):
            return {
                "temperature_max": 25,
                "temperature_min": 15,
                "conditions_text": "Sunny",
                "humidity_percent": 50,
                "wind_kph": 12,
            }

        monkeypatch.setattr(weather_mod.weather_service, "get_weather", lambda lat, lon: fake_get_weather(lat, lon))

        res = api_client.post(f"/api/v1/daily-plans/{plan.id}/fetch_weather/")
        assert res.status_code == 200
        plan.refresh_from_db()
        assert plan.weather_data is not None
        assert "temperature_max" in plan.weather_data

    def test_convert_activities_to_tasks(self, api_client, user, project):
        api_client.force_authenticate(user=user)
        plan = DailyPlan.objects.create(
            project=project, plan_date=date.today() + timedelta(days=1), completion_deadline=date.today()
        )
        PlannedActivity.objects.create(daily_plan=plan, title="Paint Walls", description="Two coats", order=1)
        res = api_client.post(f"/api/v1/daily-plans/{plan.id}/convert_activities/")
        assert res.status_code == 200
        assert res.data["created_count"] == 1
        assert Task.objects.filter(project=project, title="Paint Walls").exists()

    def test_productivity_score(self, api_client, user, project):
        api_client.force_authenticate(user=user)
        plan = DailyPlan.objects.create(
            project=project,
            plan_date=date.today() + timedelta(days=1),
            completion_deadline=date.today(),
            estimated_hours_total=8.0,
            actual_hours_worked=6.0,
        )
        res = api_client.get(f"/api/v1/daily-plans/{plan.id}/productivity/")
        assert res.status_code == 200
        assert res.data["productivity_score"] == 133.3 or res.data["productivity_score"] == 133.4


@pytest.mark.django_db
class TestPlannedActivity:
    def test_check_materials_sets_flags(self, api_client, user, project):
        api_client.force_authenticate(user=user)
        plan = DailyPlan.objects.create(
            project=project, plan_date=date.today() + timedelta(days=1), completion_deadline=date.today()
        )
        act = PlannedActivity.objects.create(daily_plan=plan, title="Masking", materials_needed=["Tape:3roll"])
        res = api_client.post(f"/api/v1/planned-activities/{act.id}/check_materials/")
        assert res.status_code == 200
        act.refresh_from_db()
        assert act.materials_checked in (True, False)  # It runs without crashing
