"""Phase 12 — per-project transparency + the account-based API permission fix.

Two things land here:

1. The breakdown endpoint now returns a ``socios`` roster so every member can
   see the full per-project reparto: company deduction, director share, and
   each socio's accrued-on-this-project. This is intentionally transparent —
   but it exposes ONLY per-project distribution, never anyone's global balance
   or withdrawals (those stay private in each member's own ledger).

2. Regression guard for the Phase-1 decoupling: the DRF permission
   ``IsPartnerOrDirector`` is now account-based, so a PM-socio (PM role + active
   account) can actually read the profit-share API. A plain PM (no account)
   still cannot.
"""
from __future__ import annotations

from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient

from core import access
from core.models import PartnerAccount, Profile, Project, ProjectAccrualState

User = get_user_model()


def _user(username, role):
    u = User.objects.create_user(username=username, password="x")
    Profile.objects.update_or_create(user=u, defaults={"role": role})
    u.refresh_from_db()
    return u


def _socio(username):
    """A PM-role user who is an ACTIVE socio (account-based)."""
    return PartnerAccount.for_partner(_user(username, access.ROLE_PM))


def _breakdown_url(project):
    return reverse("api-profit-share-project-breakdown", args=[project.id])


@pytest.fixture
def api():
    return APIClient()


@pytest.fixture
def director(db):
    return _user("p12_director", access.ROLE_OWNER)


@pytest.fixture
def included_project(db):
    return Project.objects.create(name="P12 Included", in_profit_share=True)


# ─────────────────────────────────────────────────────────────────────────────
# Transparency: the socios roster on the breakdown
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.django_db
class TestBreakdownSocios:
    def test_lists_every_active_socio_by_name(self, api, included_project):
        a = _socio("p12_a")
        b = _socio("p12_b")
        api.force_authenticate(a.owner)
        resp = api.get(_breakdown_url(included_project))
        assert resp.status_code == 200
        names = {s["name"] for s in resp.data["socios"]}
        assert a.owner.username in names
        assert b.owner.username in names

    def test_is_me_flag_is_scoped_to_caller(self, api, included_project):
        a = _socio("p12_me_a")
        _socio("p12_me_b")
        api.force_authenticate(a.owner)
        resp = api.get(_breakdown_url(included_project))
        mine = [s for s in resp.data["socios"] if s["is_me"]]
        assert len(mine) == 1
        assert mine[0]["name"] == a.owner.username

    def test_director_is_never_in_the_socios_pool(self, api, director, included_project):
        _socio("p12_dir_socio")
        # Even an explicitly active account owned by the director is excluded:
        PartnerAccount.objects.create(owner=director, is_active_socio=True)
        api.force_authenticate(director)
        resp = api.get(_breakdown_url(included_project))
        names = {s["name"] for s in resp.data["socios"]}
        assert director.username not in names

    def test_business_account_is_never_in_socios(self, api, included_project):
        _socio("p12_biz_socio")
        PartnerAccount.business()  # ensure the business account exists
        api.force_authenticate(_socio("p12_biz_caller").owner)
        resp = api.get(_breakdown_url(included_project))
        assert all(s["name"] != "Business Account" for s in resp.data["socios"])

    def test_accrued_reflects_project_accrual_state(self, api, included_project):
        a = _socio("p12_accrued")
        ProjectAccrualState.objects.create(
            project=included_project, account=a, accrued=Decimal("123.45")
        )
        api.force_authenticate(a.owner)
        resp = api.get(_breakdown_url(included_project))
        mine = [s for s in resp.data["socios"] if s["is_me"]][0]
        assert mine["accrued"] == "123.45"

    def test_socio_with_no_payments_shows_zero(self, api, included_project):
        a = _socio("p12_zero")
        api.force_authenticate(a.owner)
        resp = api.get(_breakdown_url(included_project))
        mine = [s for s in resp.data["socios"] if s["is_me"]][0]
        assert mine["accrued"] == "0.00"


# ─────────────────────────────────────────────────────────────────────────────
# Transparency must NOT become a leak: no balances / withdrawals / lever
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.django_db
class TestBreakdownNoLeak:
    def test_socios_entries_expose_only_safe_fields(self, api, included_project):
        _socio("p12_safe_b")
        api.force_authenticate(_socio("p12_safe_a").owner)
        resp = api.get(_breakdown_url(included_project))
        assert resp.data["socios"]  # non-empty
        for s in resp.data["socios"]:
            assert set(s.keys()) == {"name", "accrued", "is_me"}

    def test_destination_lever_still_hidden_from_socio(self, api, included_project):
        api.force_authenticate(_socio("p12_lever").owner)
        resp = api.get(_breakdown_url(included_project))
        assert "direction_overhead_destination" not in resp.data["distribution"]


# ─────────────────────────────────────────────────────────────────────────────
# Regression: account-based API permission (the Phase-1 fix)
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.django_db
class TestPmSocioApiAccess:
    def test_pm_socio_can_read_the_api(self, api, included_project):
        a = _socio("p12_api_ok")
        api.force_authenticate(a.owner)
        assert api.get(reverse("api-profit-share-me-summary")).status_code == 200
        assert api.get(reverse("api-profit-share-projects")).status_code == 200
        assert api.get(_breakdown_url(included_project)).status_code == 200

    def test_plain_pm_without_account_is_forbidden(self, api, included_project):
        pm = _user("p12_api_plain", access.ROLE_PM)
        api.force_authenticate(pm)
        assert api.get(reverse("api-profit-share-me-summary")).status_code == 403
        assert api.get(reverse("api-profit-share-projects")).status_code == 403
        assert api.get(_breakdown_url(included_project)).status_code == 403


# ─────────────────────────────────────────────────────────────────────────────
# My Earnings page surfaces the transparency section
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.django_db
class TestMyEarningsRendersDistribution:
    def test_distribution_section_present_for_socio(self, client, included_project):
        a = _socio("p12_view")
        client.force_login(a.owner)
        resp = client.get(reverse("profit_share_my_earnings"))
        assert resp.status_code == 200
        assert "Distribution by project" in resp.content.decode()
