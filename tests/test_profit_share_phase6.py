"""Phase 6 — payroll/savings exclude socios & director.

The three profit-share members no longer draw an hourly wage, so they must NOT
appear in the weekly payroll review or the savings ledger. Their TimeEntry
check-ins remain fully functional (metrics only). Normal crew is untouched.
"""
from __future__ import annotations

from datetime import date, time
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from core import access
from core.models import Employee, Profile, Project, TimeEntry
from core.services.profit_share_service import exclude_profit_share_members

User = get_user_model()


def _user(username, role):
    u = User.objects.create_user(username=username, password="x")
    Profile.objects.update_or_create(user=u, defaults={"role": role})
    u.refresh_from_db()
    return u


def _emp(first, last, ssn, *, user=None):
    return Employee.objects.create(
        first_name=first, last_name=last, social_security_number=ssn,
        hourly_rate=Decimal("25.00"), is_active=True, user=user,
    )


@pytest.fixture
def crew(db):
    # Distinctive sentinel names so body-substring assertions can't collide
    # with unrelated UI chrome (e.g. the "Director Panel" nav item).
    return _emp("CrewKeep", "Worker", "100-00-0001")  # no user → always payroll


@pytest.fixture
def socio_emp(db):
    u = _user("p6_socio", access.ROLE_PARTNER)
    return _emp("SocioHidden", "Partner", "100-00-0002", user=u)


@pytest.fixture
def director_emp(db):
    u = _user("p6_owner", access.ROLE_OWNER)
    return _emp("DirectorHidden", "Owner", "100-00-0003", user=u)


@pytest.fixture
def admin_user(db):
    return User.objects.create_user(
        username="p6_admin", password="x", is_staff=True, is_superuser=True
    )


@pytest.mark.django_db
class TestExcludeHelper:
    def test_helper_excludes_partner_and_owner_keeps_crew(
        self, crew, socio_emp, director_emp
    ):
        ids = set(
            exclude_profit_share_members(Employee.objects.all()).values_list(
                "id", flat=True
            )
        )
        assert crew.id in ids
        assert socio_emp.id not in ids
        assert director_emp.id not in ids

    def test_employee_role_is_not_excluded(self):
        u = _user("p6_regular", access.ROLE_EMPLOYEE)
        e = _emp("Reg", "Ular", "100-00-0004", user=u)
        ids = set(
            exclude_profit_share_members(Employee.objects.all()).values_list(
                "id", flat=True
            )
        )
        assert e.id in ids


@pytest.mark.django_db
class TestPayrollViewExcludesMembers:
    def test_weekly_review_hides_socio_and_director(
        self, client, admin_user, crew, socio_emp, director_emp
    ):
        client.force_login(admin_user)
        resp = client.get(reverse("payroll_weekly_review"))
        assert resp.status_code == 200
        body = resp.content.decode()
        assert "CrewKeep" in body            # crew is listed
        assert "SocioHidden" not in body      # socio excluded
        assert "DirectorHidden" not in body   # director excluded

    def test_savings_ledger_hides_socio(
        self, client, admin_user, crew, socio_emp
    ):
        client.force_login(admin_user)
        resp = client.get(reverse("employee_savings_ledger"))
        assert resp.status_code == 200
        body = resp.content.decode()
        assert "SocioHidden" not in body


@pytest.mark.django_db
class TestSocioCheckInStillWorks:
    def test_socio_timeentry_is_untouched(self, socio_emp):
        """A socio can still clock in; their TimeEntry is metrics-only and is
        not affected by the payroll exclusion."""
        p = Project.objects.create(name="P6 Project")
        te = TimeEntry.objects.create(
            employee=socio_emp, project=p, date=date.today(),
            start_time=time(8, 0), end_time=time(16, 30),
        )
        assert TimeEntry.objects.filter(pk=te.pk).exists()
        te.refresh_from_db()
        assert te.hours_worked and te.hours_worked > 0
