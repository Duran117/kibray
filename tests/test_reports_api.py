import pytest
from django.contrib.auth import get_user_model

from core.models import Expense, Income, Project

pytestmark = pytest.mark.django_db


def test_project_cost_summary_requires_auth(client):
    resp = client.get("/api/v1/reports/project-cost-summary/1/")
    assert resp.status_code in (401, 403)


def test_project_cost_summary_renders_csv(authenticated_client):
    client, user = authenticated_client
    # Create a project with income and expense
    from datetime import date

    project = Project.objects.create(name="Test Project", start_date=date.today())
    Income.objects.create(
        project=project, project_name="Test Project", amount=5000, date=date.today(), payment_method="TRANSFERENCIA"
    )
    Expense.objects.create(
        project=project,
        project_name="Test Project",
        amount=2000,
        date=date.today(),
        category="MATERIALES",
        description="Materials",
    )

    resp = client.get(f"/api/v1/reports/project-cost-summary/{project.id}/")
    assert resp.status_code == 200
    # Check for CSV format
    assert "text/csv" in resp.get("Content-Type", "")
    content = resp.content.decode("utf-8")
    assert "project_id" in content
    assert str(project.id) in content
    assert "5000" in content or "5000.00" in content
    assert "2000" in content or "2000.00" in content


def test_project_cost_summary_nonexistent_project(authenticated_client):
    """Non-existent project returns 404"""
    client, user = authenticated_client
    resp = client.get("/api/v1/reports/project-cost-summary/99999/")
    assert resp.status_code == 404


def test_project_cost_summary_method_not_allowed(authenticated_client):
    """POST/PUT/DELETE not allowed on report endpoint"""
    client, user = authenticated_client
    from datetime import date

    project = Project.objects.create(name="Test", start_date=date.today())

    post = client.post(f"/api/v1/reports/project-cost-summary/{project.id}/", data={})
    assert post.status_code == 405

    put = client.put(f"/api/v1/reports/project-cost-summary/{project.id}/", data={})
    assert put.status_code == 405


# ===== Fixtures =====
@pytest.fixture
def authenticated_client(client):
    User = get_user_model()
    user = User.objects.create_user(username="reportuser", password="pass123", email="report@example.com")
    assert client.login(username="reportuser", password="pass123")
    return client, user
