import pytest
from datetime import date
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from core.models import Project

User = get_user_model()

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def staff_user(db):
    return User.objects.create_user(username="mm_staff", password="x", is_staff=True)

@pytest.fixture
def project(db):
    return Project.objects.create(name="MMProj", client="ACME", start_date=date.today(), address="123 Main St")

@pytest.mark.django_db
def test_meeting_minute_crud_and_convert(api_client, staff_user, project):
    api_client.force_authenticate(user=staff_user)

    # Create minute
    res = api_client.post(
        "/api/v1/meeting-minutes/",
        {"project": project.id, "date": str(date.today()), "attendees": "Alice,Bob", "content": "Discuss"},
        format="json",
    )
    assert res.status_code in (200, 201)
    mm_id = res.data["id"]

    # Read
    res = api_client.get(f"/api/v1/meeting-minutes/{mm_id}/")
    assert res.status_code == 200

    # Convert to task
    res = api_client.post(
        f"/api/v1/meeting-minutes/{mm_id}/create_task/",
        {"text": "Follow up vendor"},
        format="json",
    )
    assert res.status_code in (200, 201)
    assert res.data.get("title", "").startswith("Follow up")

    # Update
    res = api_client.patch(f"/api/v1/meeting-minutes/{mm_id}/", {"attendees": "Alice,Bob,Carol"}, format="json")
    assert res.status_code == 200

    # Delete
    res = api_client.delete(f"/api/v1/meeting-minutes/{mm_id}/")
    assert res.status_code in (200, 204)
