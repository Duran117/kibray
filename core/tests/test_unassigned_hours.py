import pytest
from datetime import date, time
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone

from core.models import Employee, Project, TimeEntry

User = get_user_model()


@pytest.fixture
def admin_user(db):
    user = User.objects.create_user(
        username="admin_tester",
        password="pass1234",
        email="admin@example.com",
        is_staff=True,
    )
    Employee.objects.create(
        user=user,
        first_name="Admin",
        last_name="Tester",
        social_security_number="999-99-9999",
        hourly_rate=Decimal("30.00"),
    )
    return user


@pytest.fixture
def sample_project(db):
    return Project.objects.create(
        name="Sample Project",
        client="Test Client",
        start_date=timezone.localdate(),
        end_date=timezone.localdate(),
    )


@pytest.fixture
def unassigned_entry(db, admin_user):
    employee = admin_user.employee_profile
    return TimeEntry.objects.create(
        employee=employee,
        project=None,
        date=date.today(),
        start_time=time(8, 0),
        end_time=time(12, 0),
        hours_worked=Decimal("4.0"),
    )


@pytest.mark.django_db
def test_unassigned_hours_page_loads(client, admin_user, unassigned_entry):
    client.force_login(admin_user)
    url = reverse("unassigned_hours_hub")
    response = client.get(url)
    html = response.content.decode()
    assert response.status_code == 200
    assert "Horas sin proyecto" in html
    # Weekly grid shows 7 columns (D d)
    assert unassigned_entry.date.strftime("%d") in html
    # Navigation buttons and filter controls
    assert "bi-arrow-left" in html
    assert "bi-arrow-right" in html
    assert "name=\"employee\"" in html
    assert "name=\"week\"" in html
    assert "name=\"project\"" in html
    assert "name=\"cost_code\"" in html
    assert "CSV" in html


@pytest.mark.django_db
def test_can_assign_unassigned_entry(client, admin_user, sample_project, unassigned_entry):
    client.force_login(admin_user)
    url = reverse("unassigned_hours_hub")
    payload = {
        "action": "update",
        "entry_id": str(unassigned_entry.id),
        "employee": str(unassigned_entry.employee_id),
        "project": str(sample_project.id),
        "date": unassigned_entry.date.strftime("%Y-%m-%d"),
        "start_time": "08:00",
        "end_time": "12:00",
        "hours_worked": "4.0",
        "change_order": "",
        "cost_code": "",
        "notes": "Fix assignment",
    }
    response = client.post(url, payload, follow=True)
    assert response.status_code == 200
    unassigned_entry.refresh_from_db()
    assert unassigned_entry.project_id == sample_project.id


@pytest.mark.django_db
def test_can_delete_unassigned_entry(client, admin_user, unassigned_entry):
    client.force_login(admin_user)
    url = reverse("unassigned_hours_hub")
    payload = {"action": "delete", "entry_id": str(unassigned_entry.id)}
    response = client.post(url, payload, follow=True)
    assert response.status_code == 200
    assert not TimeEntry.objects.filter(id=unassigned_entry.id).exists()


@pytest.mark.django_db
def test_can_create_new_unassigned_entry(client, admin_user):
    client.force_login(admin_user)
    url = reverse("unassigned_hours_hub")
    payload = {
        "action": "create",
        "employee": str(admin_user.employee_profile.id),
        "project": "",
        "date": timezone.localdate().strftime("%Y-%m-%d"),
        "start_time": "09:00",
        "end_time": "11:00",
        "hours_worked": "2.0",
        "change_order": "",
        "cost_code": "",
        "notes": "Nueva entrada",
    }
    response = client.post(url, payload, follow=True)
    assert response.status_code == 200
    assert TimeEntry.objects.filter(employee=admin_user.employee_profile, project__isnull=True).exists()


@pytest.mark.django_db
def test_csv_export(client, admin_user, unassigned_entry):
    client.force_login(admin_user)
    url = reverse("unassigned_hours_hub")
    response = client.get(url + "?export=csv")
    assert response.status_code == 200
    assert response["Content-Type"].startswith("text/csv")
    body = response.content.decode()
    assert "employee" in body.splitlines()[0].lower()
    assert str(unassigned_entry.employee.first_name) in body
