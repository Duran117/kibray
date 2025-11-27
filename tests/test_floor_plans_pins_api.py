from datetime import date

import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient

from core.models import FloorPlan, PlanPin, Project

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    return User.objects.create_user(username="planner", password="pass123", email="p@example.com", is_staff=True)


@pytest.fixture
def project(db):
    return Project.objects.create(name="FloorProj", client="ACME", start_date=date.today(), address="123 Main St")


@pytest.mark.django_db
def test_floor_plan_pins_filter_and_comment(api_client, user, project):
    api_client.force_authenticate(user=user)
    # Create plan
    plan = FloorPlan.objects.create(
        project=project, name="Level 0", image=SimpleUploadedFile("plan.png", b"bytes", content_type="image/png")
    )
    # Create pins
    p1 = PlanPin.objects.create(plan=plan, x=0.1234, y=0.5678, pin_type="note", title="Note here", created_by=user)
    p2 = PlanPin.objects.create(plan=plan, x=0.2234, y=0.6678, pin_type="damage", title="Scratch", created_by=user)
    # Filter by plan and type
    lst = api_client.get(f"/api/v1/plan-pins/?plan={plan.id}&pin_type=damage")
    assert lst.status_code == 200
    assert len(lst.data) == 1
    assert lst.data[0]["title"] == "Scratch"
    # Comment on pin
    res = api_client.post(f"/api/v1/plan-pins/{p2.id}/comment/", {"comment": "Please fix ASAP"}, format="json")
    assert res.status_code in (200, 201)
    assert res.data["id"] == p2.id
