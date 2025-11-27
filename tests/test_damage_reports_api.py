from datetime import date

import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient

from core.models import DamageReport, Project

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    return User.objects.create_user(username="damage_user", password="pass123", email="d@example.com", is_staff=True)


@pytest.fixture
def project(db):
    return Project.objects.create(name="DamageProj", client="ACME", start_date=date.today(), address="123 Main St")


@pytest.mark.django_db
def test_damage_report_create_add_photo_and_analytics(api_client, user, project):
    api_client.force_authenticate(user=user)
    # Create report
    res = api_client.post(
        "/api/v1/damage-reports/",
        {
            "project": project.id,
            "title": "Broken tile",
            "description": "Tile cracked in kitchen",
            "category": "cosmetic",
            "severity": "medium",
            "status": "open",
            "location_detail": "Kitchen - floor",
        },
        format="multipart",
    )
    assert res.status_code in (200, 201)
    rid = res.data["id"]
    # Add photo
    upload = SimpleUploadedFile("damage.jpg", b"bytes", content_type="image/jpeg")
    res2 = api_client.post(
        f"/api/v1/damage-reports/{rid}/add_photo/", {"image": upload, "notes": "Initial evidence"}, format="multipart"
    )
    assert res2.status_code in (200, 201)
    # Analytics
    stats = api_client.get(f"/api/v1/damage-reports/analytics/?project={project.id}")
    assert stats.status_code == 200
    data = stats.data
    assert data["total"] >= 1
    assert "medium" in data["severity"]
    assert "open" in data["status"]
