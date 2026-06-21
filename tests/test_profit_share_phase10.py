"""Phase 10 — "socio" is the PartnerAccount, not the role.

The business rule changed: a Project Manager becomes a profit-share socio
*without* losing their PM role. They keep every PM permission and view; only
the way they get paid changes (hourly wage → share of project net). The source
of truth for "is a profit-share member" is therefore an ACTIVE, non-business
``PartnerAccount`` — not ``Profile.role``.

This module proves the four formerly role-coupled behaviors now follow the
account, while the legacy ``partner`` role still works for backward compat:

  1. ``access.is_profit_share_member``  — account OR legacy role.
  2. payroll exclusion (``exclude_profit_share_members``).
  3. project labor cost (``_crew_labor_cost``) — a socio is never a cost.
  4. "My Earnings" access + the sidebar entry.

Crucially: a PM who becomes a socio STILL passes ``is_admin_or_pm`` (keeps
operational access), and becoming a member grants NO operational access on its
own.
"""
from __future__ import annotations

from datetime import date, time
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from core import access
from core.models import Employee, PartnerAccount, Profile, Project, TimeEntry
from core.nav import build_global_nav
from core.services.profit_share_service import (
    _crew_labor_cost,
    exclude_profit_share_members,
)

User = get_user_model()


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────
def _user(username, role, *, is_staff=False):
    u = User.objects.create_user(username=username, password="x", is_staff=is_staff)
    Profile.objects.update_or_create(user=u, defaults={"role": role})
    u.refresh_from_db()
    return u


def _emp(first, last, ssn, *, user=None, rate="25.00"):
    return Employee.objects.create(
        first_name=first, last_name=last, social_security_number=ssn,
        hourly_rate=Decimal(rate), is_active=True, user=user,
    )


def _activate_socio(user):
    """Mark a user as an ACTIVE socio (account-based), keeping their role."""
    return PartnerAccount.for_partner(user)  # is_active_socio=True by default


def _deactivate_socio(user):
    acc = PartnerAccount.for_partner(user)
    acc.is_active_socio = False
    acc.save(update_fields=["is_active_socio"])
    return acc


def _profit_share_section(sections):
    for s in sections:
        if s.title == "Profit Share":
            return s
    return None


# ─────────────────────────────────────────────────────────────────────────────
# 1. is_profit_share_member — the new predicate
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.django_db
class TestIsProfitShareMember:
    def test_pm_with_active_account_is_member_and_keeps_role(self):
        pm = _user("p10_pm_active", access.ROLE_PM)
        _activate_socio(pm)
        assert access.is_profit_share_member(pm) is True
        # The role is UNTOUCHED — still a project manager.
        assert access.get_role(pm) == access.ROLE_PM

    def test_pm_without_account_is_not_member(self):
        pm = _user("p10_pm_plain", access.ROLE_PM)
        assert access.is_profit_share_member(pm) is False

    def test_pm_with_inactive_account_is_not_member(self):
        pm = _user("p10_pm_inactive", access.ROLE_PM)
        _deactivate_socio(pm)
        assert access.is_profit_share_member(pm) is False

    def test_legacy_partner_role_is_member_without_account(self):
        # Backward compatibility: data promoted before the account switch.
        legacy = _user("p10_legacy", access.ROLE_PARTNER)
        # No PartnerAccount exists, but the legacy role alone still counts.
        assert PartnerAccount.objects.filter(owner=legacy).exists() is False
        assert access.is_profit_share_member(legacy) is True

    def test_director_owner_is_not_a_member(self):
        owner = _user("p10_owner", access.ROLE_OWNER)
        # Even with the director's own (inactive) account, not a pool member.
        PartnerAccount.objects.create(owner=owner, is_active_socio=False)
        assert access.is_profit_share_member(owner) is False
        assert access.is_director(owner) is True

    def test_anonymous_is_not_member(self):
        from django.contrib.auth.models import AnonymousUser

        assert access.is_profit_share_member(AnonymousUser()) is False


# ─────────────────────────────────────────────────────────────────────────────
# 2. Membership grants NO operational access; PM keeps theirs
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.django_db
class TestSeparationOfConcerns:
    def test_pm_socio_keeps_operational_access(self):
        pm = _user("p10_pm_ops", access.ROLE_PM)
        _activate_socio(pm)
        # The whole point: a PM-socio still passes the operational gate.
        assert access.is_admin_or_pm(pm) is True

    def test_membership_alone_grants_no_operational_access(self):
        # A legacy partner-role user (a "pure" socio, no PM role) must NOT
        # inherit operational access just by being a profit-share member.
        socio = _user("p10_pure_socio", access.ROLE_PARTNER)
        assert access.is_profit_share_member(socio) is True
        assert access.is_admin_or_pm(socio) is False
        assert access.is_internal(socio) is False


# ─────────────────────────────────────────────────────────────────────────────
# 3. Payroll exclusion follows the account
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.django_db
class TestPayrollExclusion:
    def test_pm_with_active_account_is_excluded(self):
        pm = _user("p10_pay_active", access.ROLE_PM)
        _activate_socio(pm)
        e = _emp("PayActive", "Pm", "200-00-0001", user=pm)
        ids = set(exclude_profit_share_members(Employee.objects.all())
                  .values_list("id", flat=True))
        assert e.id not in ids

    def test_pm_without_account_stays_in_payroll(self):
        pm = _user("p10_pay_plain", access.ROLE_PM)
        e = _emp("PayPlain", "Pm", "200-00-0002", user=pm)
        ids = set(exclude_profit_share_members(Employee.objects.all())
                  .values_list("id", flat=True))
        assert e.id in ids

    def test_pm_with_inactive_account_returns_to_payroll(self):
        pm = _user("p10_pay_inactive", access.ROLE_PM)
        _deactivate_socio(pm)
        e = _emp("PayInactive", "Pm", "200-00-0003", user=pm)
        ids = set(exclude_profit_share_members(Employee.objects.all())
                  .values_list("id", flat=True))
        assert e.id in ids

    def test_legacy_partner_role_still_excluded(self):
        legacy = _user("p10_pay_legacy", access.ROLE_PARTNER)
        e = _emp("PayLegacy", "Socio", "200-00-0004", user=legacy)
        ids = set(exclude_profit_share_members(Employee.objects.all())
                  .values_list("id", flat=True))
        assert e.id not in ids

    def test_plain_crew_without_user_is_kept(self):
        e = _emp("PayCrew", "Worker", "200-00-0005")  # no user
        ids = set(exclude_profit_share_members(Employee.objects.all())
                  .values_list("id", flat=True))
        assert e.id in ids


# ─────────────────────────────────────────────────────────────────────────────
# 4. A socio's hours are never a project cost (follows the account)
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.django_db
class TestCrewLaborCost:
    def _clock(self, employee, project):
        # 8:00–16:30 = 8.5h gross − 0.5h lunch = 8.0h net; at $25/h → $200.00.
        return TimeEntry.objects.create(
            employee=employee, project=project, date=date.today(),
            start_time=time(8, 0), end_time=time(16, 30),
        )

    def test_plain_pm_hours_count_as_cost(self):
        p = Project.objects.create(name="P10 Cost A")
        pm = _user("p10_cost_plain", access.ROLE_PM)
        e = _emp("CostPlain", "Pm", "201-00-0001", user=pm)
        self._clock(e, p)
        assert _crew_labor_cost(p) == Decimal("200.00")

    def test_active_socio_hours_excluded_from_cost(self):
        p = Project.objects.create(name="P10 Cost B")
        pm = _user("p10_cost_socio", access.ROLE_PM)
        e = _emp("CostSocio", "Pm", "201-00-0002", user=pm)
        self._clock(e, p)
        _activate_socio(pm)
        # Same person, same hours — but now a socio → cost drops to zero.
        assert _crew_labor_cost(p) == Decimal("0.00")

    def test_toggling_account_flips_the_cost(self):
        p = Project.objects.create(name="P10 Cost C")
        pm = _user("p10_cost_toggle", access.ROLE_PM)
        e = _emp("CostToggle", "Pm", "201-00-0003", user=pm)
        self._clock(e, p)
        assert _crew_labor_cost(p) == Decimal("200.00")
        _activate_socio(pm)
        assert _crew_labor_cost(p) == Decimal("0.00")
        _deactivate_socio(pm)
        assert _crew_labor_cost(p) == Decimal("200.00")


# ─────────────────────────────────────────────────────────────────────────────
# 5. "My Earnings" access + sidebar entry follow the account
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.django_db
class TestMyEarningsAccess:
    def test_pm_with_active_account_can_open_my_earnings(self, client):
        pm = _user("p10_view_socio", access.ROLE_PM)
        _activate_socio(pm)
        client.force_login(pm)
        resp = client.get(reverse("profit_share_my_earnings"))
        assert resp.status_code == 200

    def test_pm_without_account_is_redirected(self, client):
        pm = _user("p10_view_plain", access.ROLE_PM)
        client.force_login(pm)
        resp = client.get(reverse("profit_share_my_earnings"))
        assert resp.status_code == 302


@pytest.mark.django_db
class TestSidebarEntry:
    def test_pm_with_active_account_sees_my_earnings(self):
        pm = _user("p10_nav_socio", access.ROLE_PM)
        _activate_socio(pm)
        section = _profit_share_section(build_global_nav(pm))
        assert section is not None
        labels = [i.label for i in section.items]
        assert labels == ["My Earnings"]

    def test_pm_without_account_has_no_profit_share_section(self):
        pm = _user("p10_nav_plain", access.ROLE_PM)
        assert _profit_share_section(build_global_nav(pm)) is None

    def test_director_sees_full_profit_share_section(self):
        owner = _user("p10_nav_owner", access.ROLE_OWNER)
        section = _profit_share_section(build_global_nav(owner))
        assert section is not None
        labels = [i.label for i in section.items]
        assert "Director Panel" in labels
        assert "Calculator" in labels
        assert "My Earnings" in labels
