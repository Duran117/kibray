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
    return User.objects.create_user(username="photo_upl", password="pass123", email="u@example.com", is_staff=True)


@pytest.fixture
def project(db):
    return Project.objects.create(name="PhotosProj", client="ACME", start_date=date.today(), address="123 Main St")


@pytest.mark.django_db
def test_site_photo_upload_with_gps_and_link(api_client, user, project):
    api_client.force_authenticate(user=user)
    # Create damage report to link
    dr = DamageReport.objects.create(project=project, title="Scratch on wall", description="Near entrance")
    # Upload with provided GPS
    file_content = b"fake image bytes"
    upload = SimpleUploadedFile("photo.jpg", file_content, content_type="image/jpeg")
    res = api_client.post(
        "/api/v1/site-photos/",
        {
            "project": project.id,
            "image": upload,
            "caption": "Entrance photo",
            "location_lat": "37.7749",
            "location_lng": "-122.4194",
            "location_accuracy_m": "5.5",
            "damage_report": dr.id,
        },
        format="multipart",
    )
    assert res.status_code in (200, 201)
    pid = res.data["id"]
    # Detail includes GPS and linkage
    detail = api_client.get(f"/api/v1/site-photos/{pid}/")
    assert detail.status_code == 200
    assert detail.data["location_lat"] == "37.774900"
    assert detail.data["damage_report"] == dr.id


@pytest.mark.django_db
def test_site_photos_list_filter_by_project(api_client, user, project):
    api_client.force_authenticate(user=user)
    upload = SimpleUploadedFile("photo.jpg", b"bytes", content_type="image/jpeg")
    res = api_client.post(
        "/api/v1/site-photos/", {"project": project.id, "image": upload, "caption": "Test"}, format="multipart"
    )
    assert res.status_code in (200, 201)
    lst = api_client.get(f"/api/v1/site-photos/?project={project.id}")
    assert lst.status_code == 200
    # Handle paginated response
    if isinstance(lst.data, dict) and "results" in lst.data:
        assert len(lst.data["results"]) >= 1
    else:
        assert isinstance(lst.data, list)
        assert len(lst.data) >= 1
