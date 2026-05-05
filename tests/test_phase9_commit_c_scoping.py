"""
Phase 9 Commit C — regression tests proving project-scoped UI/API queries.

These tests guard against re-introduction of the leak gaps closed in
Commit C: ClockInForm, ProjectViewSet, TimeEntryViewSet, project_list_view,
expense_create_view, FinancialDashboardView.

The setup creates 3 projects (A, B, C) and 4 users:
  - admin   (sees all)
  - pm_a    (PM assigned only to A)
  - emp_b   (employee with TimeEntry only on B)
  - client_c (client with ClientProjectAccess only on C)

Each test asserts that the user can see ONLY their own projects through
the public-facing surface — not the full set.
"""
from __future__ import annotations

from datetime import date

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from core.forms import ClockInForm
from core.models import (
    ClientProjectAccess,
    Employee,
    Project,
    ProjectManagerAssignment,
    TimeEntry,
)

User = get_user_model()


def _mk_user(username, *, role=None, is_staff=False, is_superuser=False):
    u = User.objects.create_user(
        username=username, password="x",
        is_staff=is_staff, is_superuser=is_superuser,
    )
    if role:
        u.profile.role = role
        u.profile.save()
    return u


@pytest.fixture
def world():
    p_a = Project.objects.create(name="C-Proj-A", start_date=date.today())
    p_b = Project.objects.create(name="C-Proj-B", start_date=date.today())
    p_c = Project.objects.create(name="C-Proj-C", start_date=date.today())

    admin = _mk_user("c_admin", role="admin", is_staff=True, is_superuser=True)

    pm_a = _mk_user("c_pm_a", role="project_manager")
    ProjectManagerAssignment.objects.create(project=p_a, pm=pm_a, role="pm")

    emp_b = _mk_user("c_emp_b", role="employee")
    e = Employee.objects.create(
        user=emp_b, first_name="E", last_name="B",
        social_security_number="C-22-22", hourly_rate=20,
    )
    TimeEntry.objects.create(
        employee=e, project=p_b, date=date.today(), start_time="08:00",
    )

    client_c = _mk_user("c_client_c", role="client")
    ClientProjectAccess.objects.create(
        user=client_c, project=p_c, role="viewer", is_active=True,
    )

    return {
        "p_a": p_a, "p_b": p_b, "p_c": p_c,
        "admin": admin, "pm_a": pm_a, "emp_b": emp_b, "client_c": client_c,
    }


# ─────────────── ClockInForm ───────────────
class TestClockInFormScoping:
    def test_no_user_no_available_returns_empty(self):
        """G3 fail-closed: no user kwarg → empty queryset (was Project.all)."""
        form = ClockInForm()
        assert form.fields["project"].queryset.count() == 0

    def test_admin_user_sees_all(self, world):
        form = ClockInForm(user=world["admin"])
        ids = set(form.fields["project"].queryset.values_list("pk", flat=True))
        assert ids == {world["p_a"].pk, world["p_b"].pk, world["p_c"].pk}

    def test_pm_user_sees_only_assigned(self, world):
        form = ClockInForm(user=world["pm_a"])
        ids = set(form.fields["project"].queryset.values_list("pk", flat=True))
        assert ids == {world["p_a"].pk}

    def test_employee_user_sees_only_worked(self, world):
        form = ClockInForm(user=world["emp_b"])
        ids = set(form.fields["project"].queryset.values_list("pk", flat=True))
        assert ids == {world["p_b"].pk}

    def test_explicit_available_overrides_user(self, world):
        """If both available_projects and user are passed, available wins."""
        only_c = Project.objects.filter(pk=world["p_c"].pk)
        form = ClockInForm(user=world["admin"], available_projects=only_c)
        ids = set(form.fields["project"].queryset.values_list("pk", flat=True))
        assert ids == {world["p_c"].pk}


# ─────────────── ProjectViewSet (DRF) ───────────────
class TestProjectViewSetScoping:
    def test_admin_sees_all_via_api(self, world):
        api = APIClient()
        api.force_authenticate(user=world["admin"])
        res = api.get("/api/v1/projects/")
        assert res.status_code == 200
        ids = {p["id"] for p in res.data["results"]}
        assert ids == {world["p_a"].pk, world["p_b"].pk, world["p_c"].pk}

    def test_pm_only_sees_assigned_via_api(self, world):
        api = APIClient()
        api.force_authenticate(user=world["pm_a"])
        res = api.get("/api/v1/projects/")
        assert res.status_code == 200
        ids = {p["id"] for p in res.data["results"]}
        assert ids == {world["p_a"].pk}

    def test_client_only_sees_own_via_api(self, world):
        api = APIClient()
        api.force_authenticate(user=world["client_c"])
        res = api.get("/api/v1/projects/")
        assert res.status_code == 200
        ids = {p["id"] for p in res.data["results"]}
        assert ids == {world["p_c"].pk}

    def test_employee_only_sees_worked_via_api(self, world):
        api = APIClient()
        api.force_authenticate(user=world["emp_b"])
        res = api.get("/api/v1/projects/")
        assert res.status_code == 200
        ids = {p["id"] for p in res.data["results"]}
        assert ids == {world["p_b"].pk}

    def test_pm_cannot_retrieve_other_project(self, world):
        """PM_A must get 404 trying to access Project B directly."""
        api = APIClient()
        api.force_authenticate(user=world["pm_a"])
        res = api.get(f"/api/v1/projects/{world['p_b'].pk}/")
        assert res.status_code == 404

    def test_client_isolation_404(self, world):
        """Client_C must get 404 trying to access Project A."""
        api = APIClient()
        api.force_authenticate(user=world["client_c"])
        res = api.get(f"/api/v1/projects/{world['p_a'].pk}/")
        assert res.status_code == 404


# ─────────────── TimeEntryViewSet (DRF) ───────────────
class TestTimeEntryViewSetScoping:
    def test_admin_sees_all_entries(self, world):
        api = APIClient()
        api.force_authenticate(user=world["admin"])
        res = api.get("/api/v1/time-entries/")
        assert res.status_code == 200
        if isinstance(res.data, dict) and "results" in res.data:
            results = res.data["results"]
        else:
            results = res.data
        # Should at least see the seeded entry on B
        assert any(
            isinstance(e, dict) and e.get("project") == world["p_b"].pk
            for e in results
        )

    def test_pm_does_not_see_entries_on_unassigned_project(self, world):
        """PM_A must not see B's TimeEntries."""
        api = APIClient()
        api.force_authenticate(user=world["pm_a"])
        res = api.get("/api/v1/time-entries/")
        assert res.status_code == 200
        # Response may be paginated dict {"results": [...]} or a bare list
        if isinstance(res.data, dict) and "results" in res.data:
            results = res.data["results"]
        else:
            results = res.data
        for e in results:
            assert isinstance(e, dict), f"Unexpected response shape: {res.data!r}"
            assert e.get("project") != world["p_b"].pk
