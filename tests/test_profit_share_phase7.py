"""Phase 7 — API endpoints: permissions & leak protection.

These tests are deliberately paranoid. The whole point of the profit-share API
is that money data NEVER leaks across members:

  * a socio sees ONLY their own earnings (summary / by-project / ledger);
  * a socio sees breakdowns of INCLUDED projects only, and never the
    direction-overhead DESTINATION (that lever is director-only);
  * only the director (owner/admin) can mark projects, post advances, or edit
    the rate configuration;
  * employees / anonymous users get nothing.

Overhead is asserted to surface under the NEUTRAL key ``overhead`` (never
``direction_overhead``) so the UI cannot accidentally reveal the lever.
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient

from core import access
from core.models import (
    LedgerEntry,
    PartnerAccount,
    Project,
    ProjectAccrualState,
    RateConfig,
)

User = get_user_model()


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────
def _mk_user(username: str, role: str) -> "User":
    u = User.objects.create_user(username, password="x")
    u.profile.role = role
    u.profile.save()
    return u


@pytest.fixture
def api():
    return APIClient()


@pytest.fixture
def cfg(db):
    c = RateConfig.load()
    c.profit_share_start_date = date.today()
    c.save()
    return c


@pytest.fixture
def director(db):
    return _mk_user("ps7_director", access.ROLE_OWNER)


@pytest.fixture
def employee(db):
    return _mk_user("ps7_employee", access.ROLE_EMPLOYEE)


@pytest.fixture
def socio_a(db):
    u = _mk_user("ps7_socio_a", access.ROLE_PARTNER)
    return PartnerAccount.for_partner(u)


@pytest.fixture
def socio_b(db):
    u = _mk_user("ps7_socio_b", access.ROLE_PARTNER)
    return PartnerAccount.for_partner(u)


@pytest.fixture
def included_project(db):
    return Project.objects.create(name="PS7 Included", in_profit_share=True)


@pytest.fixture
def excluded_project(db):
    return Project.objects.create(name="PS7 Excluded", in_profit_share=False)


def _seed_account(account: PartnerAccount, project: Project, amount: Decimal):
    """Give an account a realistic accrual: balance + ledger + accrual state."""
    account.balance = amount
    account.save(update_fields=["balance"])
    LedgerEntry.objects.create(
        account=account,
        project=project,
        type=LedgerEntry.TYPE_ACCRUAL,
        amount=amount,
        running_balance=amount,
        note="seed",
    )
    ProjectAccrualState.objects.update_or_create(
        project=project, account=account, defaults={"accrued": amount}
    )


# ─────────────────────────────────────────────────────────────────────────────
# Projects list
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.django_db
class TestProjectsList:
    URL = reverse("api-profit-share-projects")

    def test_director_sees_included_only(
        self, api, director, included_project, excluded_project
    ):
        api.force_authenticate(director)
        resp = api.get(self.URL)
        assert resp.status_code == 200
        names = {r["name"] for r in resp.data["results"]}
        assert "PS7 Included" in names
        assert "PS7 Excluded" not in names

    def test_socio_sees_included_only(
        self, api, socio_a, included_project, excluded_project
    ):
        api.force_authenticate(socio_a.owner)
        resp = api.get(self.URL)
        assert resp.status_code == 200
        names = {r["name"] for r in resp.data["results"]}
        assert names == {"PS7 Included"}

    def test_employee_forbidden(self, api, employee, included_project):
        api.force_authenticate(employee)
        assert api.get(self.URL).status_code == 403

    def test_anonymous_denied(self, api, included_project):
        assert api.get(self.URL).status_code in (401, 403)


# ─────────────────────────────────────────────────────────────────────────────
# Breakdown — the leak-sensitive transparency view
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.django_db
class TestBreakdown:
    def _url(self, project):
        return reverse(
            "api-profit-share-project-breakdown", args=[project.id]
        )

    def test_director_sees_destination(self, api, cfg, director, included_project):
        api.force_authenticate(director)
        resp = api.get(self._url(included_project))
        assert resp.status_code == 200
        assert "direction_overhead_destination" in resp.data["distribution"]

    def test_director_can_view_excluded(self, api, cfg, director, excluded_project):
        api.force_authenticate(director)
        assert api.get(self._url(excluded_project)).status_code == 200

    def test_socio_included_ok_but_no_destination(
        self, api, cfg, socio_a, included_project
    ):
        api.force_authenticate(socio_a.owner)
        resp = api.get(self._url(included_project))
        assert resp.status_code == 200
        # Leak guard: the destination lever is never exposed to a socio.
        assert "direction_overhead_destination" not in resp.data["distribution"]

    def test_socio_excluded_forbidden(self, api, cfg, socio_a, excluded_project):
        api.force_authenticate(socio_a.owner)
        assert api.get(self._url(excluded_project)).status_code == 403

    def test_employee_forbidden(self, api, cfg, employee, included_project):
        api.force_authenticate(employee)
        assert api.get(self._url(included_project)).status_code == 403

    def test_overhead_uses_neutral_label(self, api, cfg, director, included_project):
        api.force_authenticate(director)
        resp = api.get(self._url(included_project))
        cascade = resp.data["cascade"]
        assert "overhead" in cascade
        # The raw lever name must never surface in the payload.
        assert "direction_overhead" not in cascade


# ─────────────────────────────────────────────────────────────────────────────
# Set in_profit_share — director-only mutation
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.django_db
class TestSetProfitShare:
    def _url(self, project):
        return reverse("api-profit-share-project-set", args=[project.id])

    def test_director_can_mark(self, api, director, excluded_project):
        api.force_authenticate(director)
        resp = api.post(self._url(excluded_project), {"in_profit_share": True})
        assert resp.status_code == 200
        excluded_project.refresh_from_db()
        assert excluded_project.in_profit_share is True

    def test_director_can_unmark(self, api, director, included_project):
        api.force_authenticate(director)
        resp = api.post(self._url(included_project), {"in_profit_share": False})
        assert resp.status_code == 200
        included_project.refresh_from_db()
        assert included_project.in_profit_share is False

    def test_socio_forbidden(self, api, socio_a, excluded_project):
        api.force_authenticate(socio_a.owner)
        assert api.post(self._url(excluded_project), {}).status_code == 403
        excluded_project.refresh_from_db()
        assert excluded_project.in_profit_share is False

    def test_employee_forbidden(self, api, employee, excluded_project):
        api.force_authenticate(employee)
        assert api.post(self._url(excluded_project), {}).status_code == 403


# ─────────────────────────────────────────────────────────────────────────────
# Advances — director-only money movement
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.django_db
class TestAdvance:
    def _url(self, account):
        return reverse("api-profit-share-account-advance", args=[account.id])

    def test_director_advance_ok(self, api, director, socio_a):
        socio_a.balance = Decimal("1000.00")
        socio_a.save(update_fields=["balance"])
        api.force_authenticate(director)
        resp = api.post(self._url(socio_a), {"amount": "400.00", "note": "draw"})
        assert resp.status_code == 201
        assert resp.data["new_balance"] == "600.00"
        assert resp.data["left_negative"] is False
        socio_a.refresh_from_db()
        assert socio_a.balance == Decimal("600.00")

    def test_director_advance_can_go_negative_flag(self, api, director, socio_a):
        api.force_authenticate(director)
        resp = api.post(self._url(socio_a), {"amount": "50.00"})
        assert resp.status_code == 201
        assert resp.data["left_negative"] is True

    def test_amount_zero_rejected(self, api, director, socio_a):
        api.force_authenticate(director)
        assert api.post(self._url(socio_a), {"amount": "0"}).status_code == 400

    def test_amount_non_number_rejected(self, api, director, socio_a):
        api.force_authenticate(director)
        assert api.post(self._url(socio_a), {"amount": "abc"}).status_code == 400

    def test_socio_forbidden(self, api, socio_a):
        api.force_authenticate(socio_a.owner)
        resp = api.post(self._url(socio_a), {"amount": "100"})
        assert resp.status_code == 403
        socio_a.refresh_from_db()
        assert socio_a.balance == Decimal("0.00")


# ─────────────────────────────────────────────────────────────────────────────
# "My earnings" — must ALWAYS be scoped to the caller (no cross-member leak)
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.django_db
class TestMyEarningsLeakProtection:
    SUMMARY = reverse("api-profit-share-me-summary")
    BY_PROJECT = reverse("api-profit-share-me-by-project")
    LEDGER = reverse("api-profit-share-me-ledger")

    def test_summary_is_self_scoped(
        self, api, included_project, socio_a, socio_b
    ):
        _seed_account(socio_a, included_project, Decimal("1000.00"))
        _seed_account(socio_b, included_project, Decimal("2000.00"))

        api.force_authenticate(socio_a.owner)
        a = api.get(self.SUMMARY)
        assert a.status_code == 200
        assert a.data["total_accrued"] == "1000.00"
        assert a.data["balance"] == "1000.00"

        api.force_authenticate(socio_b.owner)
        b = api.get(self.SUMMARY)
        assert b.data["total_accrued"] == "2000.00"
        # The two socios never see each other's numbers.
        assert b.data["balance"] != a.data["balance"]

    def test_by_project_is_self_scoped(
        self, api, included_project, socio_a, socio_b
    ):
        _seed_account(socio_a, included_project, Decimal("1000.00"))
        _seed_account(socio_b, included_project, Decimal("2000.00"))

        api.force_authenticate(socio_a.owner)
        resp = api.get(self.BY_PROJECT)
        assert resp.status_code == 200
        assert len(resp.data["results"]) == 1
        assert resp.data["results"][0]["accrued"] == "1000.00"

    def test_ledger_is_self_scoped(
        self, api, included_project, socio_a, socio_b
    ):
        _seed_account(socio_a, included_project, Decimal("1000.00"))
        _seed_account(socio_b, included_project, Decimal("2000.00"))

        api.force_authenticate(socio_a.owner)
        resp = api.get(self.LEDGER)
        assert resp.status_code == 200
        amounts = {e["amount"] for e in resp.data["results"]}
        assert amounts == {"1000.00"}  # only own entry, never socio_b's 2000

    def test_member_without_account_gets_404(self, api, cfg, director):
        # The director fixture here has no PartnerAccount yet.
        api.force_authenticate(director)
        assert api.get(self.SUMMARY).status_code == 404

    def test_employee_forbidden(self, api, employee):
        api.force_authenticate(employee)
        assert api.get(self.SUMMARY).status_code == 403


# ─────────────────────────────────────────────────────────────────────────────
# Rate configuration — director-only
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.django_db
class TestRateConfig:
    URL = reverse("api-profit-share-rates")

    def test_director_get(self, api, cfg, director):
        api.force_authenticate(director)
        resp = api.get(self.URL)
        assert resp.status_code == 200
        assert "director_split_pct" in resp.data
        assert "direction_overhead_destination" in resp.data

    def test_director_put_updates(self, api, cfg, director):
        api.force_authenticate(director)
        resp = api.put(self.URL, {"director_split_pct": "45"}, format="json")
        assert resp.status_code == 200
        assert resp.data["director_split_pct"] == "45.00"
        RateConfig.load().refresh_from_db()
        assert RateConfig.load().director_split_pct == Decimal("45.00")

    def test_director_put_rejects_out_of_range(self, api, cfg, director):
        api.force_authenticate(director)
        resp = api.put(self.URL, {"director_split_pct": "150"}, format="json")
        assert resp.status_code == 400

    def test_socio_forbidden_get(self, api, cfg, socio_a):
        api.force_authenticate(socio_a.owner)
        assert api.get(self.URL).status_code == 403

    def test_socio_forbidden_put(self, api, cfg, socio_a):
        api.force_authenticate(socio_a.owner)
        resp = api.put(self.URL, {"director_split_pct": "10"}, format="json")
        assert resp.status_code == 403
