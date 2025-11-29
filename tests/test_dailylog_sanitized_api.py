import pytest
from datetime import date
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from core.models import Project, ClientProjectAccess, DailyLog

User = get_user_model()

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def staff_user(db):
    return User.objects.create_user(username="dl_staff", password="x", is_staff=True)

@pytest.fixture
def regular_user(db):
    return User.objects.create_user(username="dl_user", password="x")

@pytest.fixture
def project(db):
    return Project.objects.create(name="DLProj", client="ACME", start_date=date.today(), address="123 Main St")

@pytest.fixture
def dailylog(db, project, staff_user):
    # Align with current DailyLog fields; using minimal required ones
    return DailyLog.objects.create(project=project, date=date.today(), created_by=staff_user)

@pytest.mark.django_db
def test_dailylog_sanitized_visibility(api_client, staff_user, regular_user, project, dailylog):
    # Staff sees
    api_client.force_authenticate(user=staff_user)
    res = api_client.get("/api/v1/daily-logs-sanitized/")
    assert res.status_code == 200
    data = res.data if isinstance(res.data, list) else res.data.get("results", res.data)
    # Support pagination vs plain list
    items = data if isinstance(data, list) else []
    assert any((item.get("id") == dailylog.id) for item in items)

    # Regular user needs access
    api_client.force_authenticate(user=regular_user)
    res = api_client.get("/api/v1/daily-logs-sanitized/")
    assert res.status_code == 200
    data = res.data if isinstance(res.data, list) else res.data.get("results", res.data)
    items = data if isinstance(data, list) else []
    assert not any((item.get("id") == dailylog.id) for item in items)

    # Grant access
    ClientProjectAccess.objects.create(user=regular_user, project=project, role="client")
    res = api_client.get("/api/v1/daily-logs-sanitized/")
    assert res.status_code == 200
    data = res.data if isinstance(res.data, list) else res.data.get("results", res.data)
    items = data if isinstance(data, list) else []
    assert any((item.get("id") == dailylog.id) for item in items)
