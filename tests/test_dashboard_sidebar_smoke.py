import pytest
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model

from core.models import Profile, Project, ClientProjectAccess

User = get_user_model()


@pytest.fixture
def client_user(db):
    user = User.objects.create_user(username="client1", email="client1@test.com", password="pass123")
    user.profile.role = "client"
    user.profile.save()
    return user


@pytest.fixture
def pm_user(db):
    user = User.objects.create_user(username="pm1", email="pm1@test.com", password="pass123", is_staff=True)
    user.profile.role = "project_manager"
    user.profile.save()
    return user


@pytest.fixture
def employee_user(db):
    user = User.objects.create_user(username="emp1", email="emp1@test.com", password="pass123")
    user.profile.role = "employee"
    user.profile.save()
    return user


@pytest.fixture
def admin_user(db):
    user = User.objects.create_user(
        username="admin1", email="admin1@test.com", password="pass123",
        is_staff=True, is_superuser=True,
    )
    user.profile.role = "admin"
    user.profile.save()
    return user


@pytest.fixture
def sample_project(db, client_user):
    return Project.objects.create(name="Demo Project", start_date=timezone.localdate(), client=client_user.username)


@pytest.fixture
def client_access(db, client_user, sample_project):
    return ClientProjectAccess.objects.create(user=client_user, project=sample_project, role="client")


class TestSidebarSmoke:
    def test_pm_dashboard_sidebar(self, client, pm_user):
        client.force_login(pm_user)
        resp = client.get(reverse("dashboard_pm"))
        html = resp.content.decode()
        assert resp.status_code == 200
        assert "Primary navigation" in html
        assert "kb-sidebar" in html

    def test_employee_dashboard_sidebar(self, client, employee_user):
        from core.models import Employee
        Employee.objects.create(
            user=employee_user, first_name="Emp", last_name="One",
            social_security_number="999-99-9999", hourly_rate=15.00,
        )
        client.force_login(employee_user)
        resp = client.get(reverse("dashboard_employee"))
        html = resp.content.decode()
        assert resp.status_code == 200
        # Employee dashboard renders with classic or modern shell
        assert "Time" in html or "Marca" in html or "Clock" in html

    def test_client_dashboard_sidebar(self, client, client_user, client_access):
        client.force_login(client_user)
        resp = client.get(reverse("dashboard_client"))
        html = resp.content.decode()
        assert resp.status_code == 200
        assert "kb-sidebar" in html or "Project" in html

    def test_admin_dashboard_sidebar(self, client, admin_user):
        client.force_login(admin_user)
        resp = client.get(reverse("dashboard_admin"))
        html = resp.content.decode()
        assert resp.status_code == 200
        assert "Admin" in html or "Django" in html
        assert "data-layout-root" in html
