"""Unit tests for core/access.py — the canonical authorization module.

Phase 9 Commit A: validates the foundation module in isolation.
NO callers are modified yet; these tests just lock in the contract.
"""
from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied

from core import access
from core.models import (
    ClientProjectAccess,
    Employee,
    Project,
    ProjectManagerAssignment,
    ResourceAssignment,
    TimeEntry,
)

User = get_user_model()


def _mk_user(username, *, role=None, is_staff=False, is_superuser=False, email=""):
    u = User.objects.create_user(
        username=username, password="x", email=email,
        is_staff=is_staff, is_superuser=is_superuser,
    )
    if role:
        u.profile.role = role
        u.profile.save()
    return u


# ─────────────── Fixtures ───────────────
@pytest.fixture
def admin_user():
    return _mk_user("acc_admin", role=access.ROLE_ADMIN, is_staff=True, is_superuser=True)


@pytest.fixture
def staff_user():
    return _mk_user("acc_staff", is_staff=True)  # no role, just is_staff


@pytest.fixture
def pm_user():
    return _mk_user("acc_pm", role=access.ROLE_PM)


@pytest.fixture
def employee_user():
    return _mk_user("acc_emp", role=access.ROLE_EMPLOYEE)


@pytest.fixture
def client_user():
    return _mk_user("acc_client", role=access.ROLE_CLIENT, email="c@example.com")


@pytest.fixture
def other_client_user():
    return _mk_user("acc_other_client", role=access.ROLE_CLIENT, email="o@example.com")


@pytest.fixture
def projects():
    p1 = Project.objects.create(name="Acc Project A")
    p2 = Project.objects.create(name="Acc Project B")
    p3 = Project.objects.create(name="Acc Project C")
    return p1, p2, p3


# ─────────────── Layer 1: identity ───────────────
class TestRoleIdentity:
    def test_anonymous_returns_false_everywhere(self):
        anon = AnonymousUser()
        assert access.get_role(anon) is None
        assert not access.is_admin(anon)
        assert not access.is_pm(anon)
        assert not access.is_client(anon)
        assert not access.is_employee(anon)
        assert not access.is_internal(anon)
        assert not access.is_staffish(anon)

    def test_superuser_is_admin(self):
        u = _mk_user("su1", is_superuser=True)
        assert access.is_admin(u)
        assert access.is_internal(u)
        assert access.is_staffish(u)

    def test_admin_role(self, admin_user):
        assert access.is_admin(admin_user)
        assert access.is_internal(admin_user)
        assert access.get_role(admin_user) == access.ROLE_ADMIN

    def test_pm_role(self, pm_user):
        assert access.is_pm(pm_user)
        assert access.is_internal(pm_user)
        assert access.is_staffish(pm_user)
        assert not access.is_admin(pm_user)
        assert not access.is_client(pm_user)

    def test_employee_role(self, employee_user):
        assert access.is_employee(employee_user)
        assert not access.is_internal(employee_user)
        assert not access.is_staffish(employee_user)
        assert not access.is_client(employee_user)

    def test_client_role(self, client_user):
        assert access.is_client(client_user)
        assert not access.is_internal(client_user)
        assert not access.is_staffish(client_user)

    def test_staff_client_is_not_strict_client(self):
        """A staff user with role=client keeps staff powers; is_client() returns False."""
        u = _mk_user("staff_client", role=access.ROLE_CLIENT, is_staff=True)
        assert not access.is_client(u)
        assert access.is_internal(u)

    def test_is_staff_alone_is_not_admin(self, staff_user):
        assert not access.is_admin(staff_user)
        assert access.is_staffish(staff_user)


# ─────────────── Layer 2: project access ───────────────
class TestAccessibleProjects:
    def test_anonymous_sees_nothing(self, projects):
        assert access.accessible_projects(AnonymousUser()).count() == 0

    def test_admin_sees_all(self, admin_user, projects):
        assert access.accessible_projects(admin_user).count() == 3

    def test_staff_sees_all(self, staff_user, projects):
        assert access.accessible_projects(staff_user).count() == 3

    def test_pm_sees_only_assigned(self, pm_user, projects):
        p1, p2, p3 = projects
        ProjectManagerAssignment.objects.create(project=p1, pm=pm_user, role="pm")
        ProjectManagerAssignment.objects.create(project=p2, pm=pm_user, role="pm")
        ids = set(access.accessible_projects(pm_user).values_list("pk", flat=True))
        assert ids == {p1.pk, p2.pk}

    def test_pm_with_no_assignments_sees_none(self, pm_user, projects):
        assert access.accessible_projects(pm_user).count() == 0

    def test_employee_sees_via_resource_assignment(self, employee_user, projects):
        p1, p2, p3 = projects
        emp = Employee.objects.create(
            user=employee_user, first_name="E", last_name="One",
            social_security_number="111-11-1111", hourly_rate=20,
        )
        ResourceAssignment.objects.create(employee=emp, project=p1, date="2025-01-01")
        ids = set(access.accessible_projects(employee_user).values_list("pk", flat=True))
        assert ids == {p1.pk}

    def test_employee_sees_via_time_entry(self, employee_user, projects):
        p1, p2, p3 = projects
        emp = Employee.objects.create(
            user=employee_user, first_name="E", last_name="Two",
            social_security_number="222-22-2222", hourly_rate=20,
        )
        TimeEntry.objects.create(
            employee=emp, project=p2, date="2025-01-01", start_time="08:00",
        )
        ids = set(access.accessible_projects(employee_user).values_list("pk", flat=True))
        assert ids == {p2.pk}

    def test_employee_no_assignments_sees_none(self, employee_user, projects):
        Employee.objects.create(
            user=employee_user, first_name="E", last_name="None",
            social_security_number="333-33-3333", hourly_rate=20,
        )
        assert access.accessible_projects(employee_user).count() == 0

    def test_client_sees_via_explicit_access(self, client_user, projects):
        p1, p2, p3 = projects
        ClientProjectAccess.objects.create(
            user=client_user, project=p1, role="client", is_active=True,
        )
        ids = set(access.accessible_projects(client_user).values_list("pk", flat=True))
        assert ids == {p1.pk}

    def test_client_inactive_access_denied(self, client_user, projects):
        p1, p2, p3 = projects
        ClientProjectAccess.objects.create(
            user=client_user, project=p1, role="client", is_active=False,
        )
        assert access.accessible_projects(client_user).count() == 0

    def test_client_legacy_text_match(self, client_user, projects):
        p1, p2, p3 = projects
        p1.client = client_user.username
        p1.save()
        ids = set(access.accessible_projects(client_user).values_list("pk", flat=True))
        assert p1.pk in ids

    def test_client_isolation_cannot_see_other_clients_projects(
        self, client_user, other_client_user, projects
    ):
        """CRITICAL: client A must NOT see client B's project."""
        p1, p2, p3 = projects
        ClientProjectAccess.objects.create(
            user=client_user, project=p1, role="client", is_active=True,
        )
        ClientProjectAccess.objects.create(
            user=other_client_user, project=p2, role="client", is_active=True,
        )
        a_ids = set(access.accessible_projects(client_user).values_list("pk", flat=True))
        b_ids = set(access.accessible_projects(other_client_user).values_list("pk", flat=True))
        assert a_ids == {p1.pk}
        assert b_ids == {p2.pk}
        assert a_ids.isdisjoint(b_ids)


class TestCanViewProject:
    def test_admin_can_view_anything(self, admin_user, projects):
        for p in projects:
            assert access.can_view_project(admin_user, p)

    def test_pm_only_assigned(self, pm_user, projects):
        p1, p2, _ = projects
        ProjectManagerAssignment.objects.create(project=p1, pm=pm_user, role="pm")
        assert access.can_view_project(pm_user, p1)
        assert not access.can_view_project(pm_user, p2)

    def test_client_only_with_access(self, client_user, other_client_user, projects):
        p1, p2, _ = projects
        ClientProjectAccess.objects.create(
            user=client_user, project=p1, role="client", is_active=True,
        )
        assert access.can_view_project(client_user, p1)
        assert not access.can_view_project(client_user, p2)
        assert not access.can_view_project(other_client_user, p1)

    def test_anonymous_cannot_view(self, projects):
        assert not access.can_view_project(AnonymousUser(), projects[0])

    def test_none_project_denied(self, admin_user):
        assert not access.can_view_project(admin_user, None)


# ─────────────── Layer 3: capability checks ───────────────
class TestFinancialCapabilities:
    def test_admin_can_view_all_financials(self, admin_user, projects):
        p = projects[0]
        assert access.can_view_financials(admin_user, p)
        assert access.can_view_labor_cost(admin_user, p)
        assert access.can_view_profit(admin_user, p)
        assert access.can_view_expenses(admin_user, p)

    def test_pm_can_view_financials_for_assigned(self, pm_user, projects):
        p1, p2, _ = projects
        ProjectManagerAssignment.objects.create(project=p1, pm=pm_user, role="pm")
        assert access.can_view_financials(pm_user, p1)
        assert not access.can_view_financials(pm_user, p2)

    def test_pm_cannot_view_profit(self, pm_user, projects):
        p1 = projects[0]
        ProjectManagerAssignment.objects.create(project=p1, pm=pm_user, role="pm")
        assert not access.can_view_profit(pm_user, p1)
        # PM may see labor cost (operational); document this default
        assert access.can_view_labor_cost(pm_user, p1)

    def test_client_financials_gated_by_flag(self, client_user, projects):
        p1 = projects[0]
        cpa = ClientProjectAccess.objects.create(
            user=client_user, project=p1, role="viewer", is_active=True,
        )
        # 'viewer' role defaults can_view_financials=False
        assert not access.can_view_financials(client_user, p1)
        cpa.can_view_financials = True
        cpa.save()
        assert access.can_view_financials(client_user, p1)

    def test_client_never_sees_expenses(self, client_user, projects):
        """Expenses are internal cost data — never visible to clients even if
        they have can_view_financials=True."""
        p1 = projects[0]
        ClientProjectAccess.objects.create(
            user=client_user, project=p1, role="client",
            is_active=True, can_view_financials=True,
        )
        assert not access.can_view_expenses(client_user, p1)
        assert not access.can_view_labor_cost(client_user, p1)
        assert not access.can_view_profit(client_user, p1)

    def test_employee_never_sees_financials(self, employee_user, projects):
        p1 = projects[0]
        emp = Employee.objects.create(
            user=employee_user, first_name="E", last_name="X",
            social_security_number="999-99-9999", hourly_rate=20,
        )
        ResourceAssignment.objects.create(employee=emp, project=p1, date="2025-01-01")
        assert access.can_view_project(employee_user, p1)
        assert not access.can_view_financials(employee_user, p1)


class TestChangeOrderCapabilities:
    def test_co_price_follows_financial_gate(self, client_user, projects):
        from core.models import ChangeOrder
        p1 = projects[0]
        cpa = ClientProjectAccess.objects.create(
            user=client_user, project=p1, role="viewer", is_active=True,
        )
        # 'viewer' has can_view_financials=False but we manually grant approval
        cpa.can_approve_change_orders = True
        cpa.save()
        co = ChangeOrder.objects.create(project=p1, description="X", amount=100)
        assert access.can_view_change_order(client_user, co)
        assert not access.can_view_change_order_price(client_user, co)
        assert access.can_approve_change_order(client_user, co)


class TestConvenienceHelpers:
    def test_assert_can_view_project_raises(self, client_user, projects):
        with pytest.raises(PermissionDenied):
            access.assert_can_view_project(client_user, projects[0])

    def test_assert_can_view_project_passes(self, admin_user, projects):
        # No exception
        access.assert_can_view_project(admin_user, projects[0])

    def test_filter_by_project_access_admin(self, admin_user, projects):
        qs = Project.objects.all()
        assert access.filter_by_project_access(admin_user, qs).count() == 3

    def test_filter_by_project_access_anonymous(self, projects):
        qs = Project.objects.all()
        assert access.filter_by_project_access(AnonymousUser(), qs).count() == 0
