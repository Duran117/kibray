import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient

from core.models import ClientProjectAccess, ColorSample, DamageReport, Project, Task


@pytest.mark.django_db(transaction=True)
def test_project_dashboard_basic():
    # Ensure clean slate
    Project.objects.all().delete()
    Task.objects.all().delete()

    user = User.objects.create_user(username="admin", password="pass")
    project = Project.objects.create(name="Proj A", start_date="2025-01-01")
    # Seed tasks
    Task.objects.create(project=project, title="T1", status="Pending")
    Task.objects.create(project=project, title="T2", status="In Progress")
    Task.objects.create(project=project, title="T3", status="Completed", is_touchup=True)

    # Color samples
    ColorSample.objects.create(project=project, code="C1", status="proposed")
    ColorSample.objects.create(project=project, code="C2", status="review")
    ColorSample.objects.create(project=project, code="C3", status="approved")

    # Damage report (auto-creates a repair task per DamageReport.save() Q21.4 feature)
    DamageReport.objects.create(project=project, title="Scratch", severity="low", status="open")

    client = APIClient()
    client.force_authenticate(user=user)
    url = f"/api/v1/dashboards/projects/{project.id}/"
    resp = client.get(url)
    assert resp.status_code == 200
    data = resp.json()
    assert data["project"]["id"] == project.id
    # Expect 4 tasks: 3 manual + 1 auto-created from damage report
    assert data["tasks"]["total"] == 4
    assert "damage_reports" in data
    assert "financial" in data


@pytest.mark.django_db
def test_client_dashboard_access():
    client_user = User.objects.create_user(username="client1", password="pass")
    project = Project.objects.create(name="Client Proj", start_date="2025-01-02")
    # Grant access
    ClientProjectAccess.objects.create(user=client_user, project=project, role="client")
    # Touch-up task & color review
    Task.objects.create(project=project, title="TouchUp", status="Pending", is_touchup=True)
    ColorSample.objects.create(project=project, code="X1", status="review")

    api = APIClient()
    api.force_authenticate(user=client_user)
    resp = api.get("/api/v1/dashboards/client/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["totals"]["projects_count"] == 1
    assert data["totals"]["pending_touchups"] == 1
    assert data["totals"]["pending_color_reviews"] == 1
