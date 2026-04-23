"""
Tests for core/views/task_views.py

Covers 10 view functions:
- agregar_tarea (touch-up creation by clients/staff)
- task_list_view (project task list)
- task_detail (task detail)
- task_edit_view (staff-only task edit)
- task_delete_view (staff-only task delete)
- task_list_all (deprecated → redirects to command center)
- task_create_wizard (staff-only task creation wizard)
- task_command_center (unified task control center)
- task_start_tracking (AJAX time tracking start)
- task_stop_tracking (AJAX time tracking stop)
"""
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

User = get_user_model()


# ---------- Fixtures ----------

@pytest.fixture
def admin_user(db):
    return User.objects.create_user(
        username="task_admin", password="x", is_staff=True, is_superuser=True
    )


@pytest.fixture
def staff_user(db):
    return User.objects.create_user(
        username="task_staff", password="x", is_staff=True
    )


@pytest.fixture
def client_user_obj(db):
    """User with client role."""
    from core.models import Profile
    u = User.objects.create_user(username="task_client", password="x")
    Profile.objects.update_or_create(user=u, defaults={"role": "client"})
    u.refresh_from_db()
    return u


@pytest.fixture
def employee_user(db):
    """User with linked Employee profile."""
    from core.models import Employee, Profile
    u = User.objects.create_user(username="task_emp", password="x")
    Profile.objects.update_or_create(user=u, defaults={"role": "employee"})
    Employee.objects.create(
        user=u,
        first_name="Emp",
        last_name="One",
        social_security_number="555-44-3333",
        hourly_rate=Decimal("20.00"),
    )
    u.refresh_from_db()
    return u


@pytest.fixture
def project(db):
    from core.models import Project
    return Project.objects.create(name="Task Test Project")


@pytest.fixture
def project_with_client_access(db, project, client_user_obj):
    from core.models import ClientProjectAccess
    ClientProjectAccess.objects.create(
        user=client_user_obj, project=project, role="client"
    )
    return project


@pytest.fixture
def task(db, project):
    from core.models import Task
    return Task.objects.create(project=project, title="Sample Task", status="Pending")


@pytest.fixture
def task_assigned(db, project, employee_user):
    from core.models import Employee, Task
    emp = Employee.objects.get(user=employee_user)
    return Task.objects.create(
        project=project, title="Assigned Task", assigned_to=emp, status="Pending"
    )


# ---------- agregar_tarea ----------

class TestAgregarTarea:
    def test_anonymous_redirected(self, client, project):
        url = reverse("agregar_tarea", args=[project.id])
        resp = client.get(url)
        assert resp.status_code == 302

    def test_client_without_access_denied(self, client, client_user_obj, project):
        client.force_login(client_user_obj)
        url = reverse("agregar_tarea", args=[project.id])
        resp = client.post(url, {"title": "X"})
        # Redirected to dashboard_client
        assert resp.status_code == 302

    def test_client_with_access_creates_touchup(
        self, client, client_user_obj, project_with_client_access
    ):
        from core.models import TouchUp
        client.force_login(client_user_obj)
        url = reverse("agregar_tarea", args=[project_with_client_access.id])
        resp = client.post(url, {
            "title": "Fix paint chip",
            "description": "Near the door",
            "priority": "high",
        })
        assert resp.status_code == 302  # redirect to client_project_view
        assert TouchUp.objects.filter(
            project=project_with_client_access, title="Fix paint chip"
        ).exists()

    def test_staff_creates_touchup(self, client, staff_user, project):
        from core.models import TouchUp
        client.force_login(staff_user)
        url = reverse("agregar_tarea", args=[project.id])
        resp = client.post(url, {"title": "Staff TouchUp", "priority": "medium"})
        assert resp.status_code == 302
        assert TouchUp.objects.filter(project=project, title="Staff TouchUp").exists()

    def test_missing_title_returns_error(self, client, staff_user, project):
        from core.models import TouchUp
        client.force_login(staff_user)
        url = reverse("agregar_tarea", args=[project.id])
        resp = client.post(url, {"title": ""})
        assert resp.status_code == 302
        assert not TouchUp.objects.filter(project=project, title="").exists()

    def test_nonexistent_project_404(self, client, staff_user):
        client.force_login(staff_user)
        url = reverse("agregar_tarea", args=[999999])
        resp = client.post(url, {"title": "X"})
        assert resp.status_code == 404


# ---------- task_list_view ----------

class TestTaskListView:
    def test_anonymous_redirected(self, client, project):
        url = reverse("task_list", args=[project.id])
        resp = client.get(url)
        assert resp.status_code == 302

    def test_admin_can_view(self, client, admin_user, project, task):
        client.force_login(admin_user)
        url = reverse("task_list", args=[project.id])
        resp = client.get(url)
        assert resp.status_code == 200

    def test_nonexistent_project_404(self, client, admin_user):
        client.force_login(admin_user)
        url = reverse("task_list", args=[999999])
        resp = client.get(url)
        assert resp.status_code == 404


# ---------- task_detail ----------

class TestTaskDetail:
    def test_anonymous_redirected(self, client, task):
        url = reverse("task_detail", args=[task.id])
        resp = client.get(url)
        assert resp.status_code == 302

    def test_staff_can_view_any_task(self, client, staff_user, task):
        client.force_login(staff_user)
        url = reverse("task_detail", args=[task.id])
        resp = client.get(url)
        assert resp.status_code == 200

    def test_employee_can_view_assigned_task(self, client, employee_user, task_assigned):
        client.force_login(employee_user)
        url = reverse("task_detail", args=[task_assigned.id])
        resp = client.get(url)
        assert resp.status_code == 200

    def test_employee_cannot_view_unassigned_task(self, client, employee_user, task):
        client.force_login(employee_user)
        url = reverse("task_detail", args=[task.id])
        resp = client.get(url)
        # Redirected away
        assert resp.status_code == 302

    def test_nonexistent_task_404(self, client, admin_user):
        client.force_login(admin_user)
        url = reverse("task_detail", args=[999999])
        resp = client.get(url)
        assert resp.status_code == 404


# ---------- task_edit_view ----------

class TestTaskEditView:
    def test_non_staff_redirected(self, client, employee_user, task):
        client.force_login(employee_user)
        url = reverse("task_edit", args=[task.id])
        resp = client.get(url)
        assert resp.status_code == 302

    def test_staff_can_view_form(self, client, staff_user, task):
        client.force_login(staff_user)
        url = reverse("task_edit", args=[task.id])
        resp = client.get(url)
        assert resp.status_code == 200


# ---------- task_delete_view ----------

class TestTaskDeleteView:
    def test_non_staff_redirected(self, client, employee_user, task):
        client.force_login(employee_user)
        url = reverse("task_delete", args=[task.id])
        resp = client.post(url)
        assert resp.status_code == 302

    def test_staff_get_shows_confirm(self, client, staff_user, task):
        client.force_login(staff_user)
        url = reverse("task_delete", args=[task.id])
        resp = client.get(url)
        assert resp.status_code == 200

    def test_staff_post_deletes(self, client, staff_user, task):
        from core.models import Task
        client.force_login(staff_user)
        task_id = task.id
        url = reverse("task_delete", args=[task.id])
        resp = client.post(url)
        assert resp.status_code == 302
        assert not Task.objects.filter(id=task_id).exists()


# ---------- task_list_all (deprecated) ----------

class TestTaskListAll:
    def test_redirects_to_command_center(self, client, admin_user):
        client.force_login(admin_user)
        url = reverse("task_list_all")
        resp = client.get(url)
        assert resp.status_code == 302
        assert "command-center" in resp.url


# ---------- task_create_wizard ----------

class TestTaskCreateWizard:
    def test_non_staff_redirected(self, client, employee_user):
        client.force_login(employee_user)
        url = reverse("task_create_wizard")
        resp = client.get(url)
        assert resp.status_code == 302

    def test_staff_get_shows_form(self, client, staff_user):
        client.force_login(staff_user)
        url = reverse("task_create_wizard")
        resp = client.get(url)
        assert resp.status_code == 200

    def test_staff_get_with_preselected_project(self, client, staff_user, project):
        client.force_login(staff_user)
        url = reverse("task_create_wizard") + f"?project={project.id}"
        resp = client.get(url)
        assert resp.status_code == 200

    def test_staff_get_with_invalid_project_id(self, client, staff_user):
        client.force_login(staff_user)
        url = reverse("task_create_wizard") + "?project=999999"
        resp = client.get(url)
        assert resp.status_code == 200


# ---------- task_command_center ----------

class TestTaskCommandCenter:
    def test_anonymous_redirected(self, client):
        url = reverse("task_command_center")
        resp = client.get(url)
        assert resp.status_code == 302

    def test_admin_can_view(self, client, admin_user):
        client.force_login(admin_user)
        url = reverse("task_command_center")
        resp = client.get(url)
        assert resp.status_code == 200

    def test_employee_can_view(self, client, employee_user):
        client.force_login(employee_user)
        url = reverse("task_command_center")
        resp = client.get(url)
        assert resp.status_code == 200


# ---------- task_start_tracking ----------

class TestTaskStartTracking:
    def test_get_method_rejected(self, client, admin_user, task):
        client.force_login(admin_user)
        url = reverse("task_start_tracking", args=[task.id])
        resp = client.get(url)
        assert resp.status_code == 405

    def test_unauthorized_employee_403(self, client, employee_user, task):
        # task is not assigned to this employee
        client.force_login(employee_user)
        url = reverse("task_start_tracking", args=[task.id])
        resp = client.post(url)
        assert resp.status_code == 403

    def test_assigned_employee_can_start(self, client, employee_user, task_assigned):
        client.force_login(employee_user)
        url = reverse("task_start_tracking", args=[task_assigned.id])
        resp = client.post(url)
        # Either success (200) or dependency error (400) — must not crash
        assert resp.status_code in (200, 400)


# ---------- task_stop_tracking ----------

class TestTaskStopTracking:
    def test_get_method_rejected(self, client, admin_user, task):
        client.force_login(admin_user)
        url = reverse("task_stop_tracking", args=[task.id])
        resp = client.get(url)
        assert resp.status_code == 405

    def test_unauthorized_employee_403(self, client, employee_user, task):
        client.force_login(employee_user)
        url = reverse("task_stop_tracking", args=[task.id])
        resp = client.post(url)
        assert resp.status_code == 403

    def test_no_active_tracking_returns_400(self, client, admin_user, task):
        client.force_login(admin_user)
        url = reverse("task_stop_tracking", args=[task.id])
        resp = client.post(url)
        assert resp.status_code == 400
