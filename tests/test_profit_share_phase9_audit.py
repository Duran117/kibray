"""Phase 9 — final leak / security audit (consolidated gate).

End-to-end checks that tie the accrual engine (Phase 4) to the leak-proof API
(Phase 7): real client payments accrue per-member balances, and each member can
read ONLY their own money through the API. Plus the highest-risk negative paths
and the "a socio is never a project cost" invariant, asserted full-stack.

If any of these break, money is either leaking across members or being computed
on a wrong base — so this file is the last gate before shipping.
"""
from __future__ import annotations

from datetime import date, time, timedelta
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient

from core import access
from core.models import (
    Employee,
    Invoice,
    InvoicePayment,
    LedgerEntry,
    PartnerAccount,
    Project,
    RateConfig,
    TimeEntry,
)
from core.services.profit_share_service import (
    accrue_for_project,
    compute_project_financials,
    record_advance,
)

User = get_user_model()


# ─────────────────────────────────────────────────────────────────────────────
# Shared setup
# ─────────────────────────────────────────────────────────────────────────────
@pytest.fixture
def world(db):
    """Owner (director) + two active socios + business account + today cutoff."""
    cfg = RateConfig.load()
    cfg.profit_share_start_date = date.today()
    cfg.save()

    owner = User.objects.create_user("ps9_owner", password="x")
    owner.profile.role = access.ROLE_OWNER
    owner.profile.save()

    s1 = User.objects.create_user("ps9_s1", password="x")
    s1.profile.role = access.ROLE_PARTNER
    s1.profile.save()
    s2 = User.objects.create_user("ps9_s2", password="x")
    s2.profile.role = access.ROLE_PARTNER
    s2.profile.save()

    return {
        "cfg": cfg,
        "owner": owner,
        "s1": s1,
        "s2": s2,
        "director": PartnerAccount.director(),
        "a1": PartnerAccount.for_partner(s1),
        "a2": PartnerAccount.for_partner(s2),
        "biz": PartnerAccount.business(),
    }


def _project(in_share=True, **kw):
    defaults = dict(
        name="PS9 Project",
        budget_total=Decimal("100000.00"),
        budget_materials=Decimal("20000.00"),
        budget_labor=Decimal("30000.00"),
        in_profit_share=in_share,
    )
    defaults.update(kw)
    return Project.objects.create(**defaults)


def _invoice(project, total="100000.00"):
    return Invoice.objects.create(
        project=project, total_amount=Decimal(total),
        date_issued=date.today(), status="APPROVED",
    )


# ─────────────────────────────────────────────────────────────────────────────
# 1) End-to-end cross-member isolation: payment → accrual → API (self only)
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.django_db
class TestEndToEndCrossMemberIsolation:
    def test_payment_accrues_then_each_socio_reads_only_own(self, world):
        p = _project()
        inv = _invoice(p)
        # Full payment via the hook → accrual fires for the included project.
        InvoicePayment.objects.create(
            invoice=inv, amount=Decimal("100000.00"), payment_date=date.today(),
        )

        # Both socios accrued the same per_socio (8550) at this point...
        a1 = PartnerAccount.objects.get(pk=world["a1"].pk)
        a2 = PartnerAccount.objects.get(pk=world["a2"].pk)
        assert a1.balance == Decimal("8550.00")
        assert a2.balance == Decimal("8550.00")

        # ...now differentiate them so a leak would be unmistakable.
        record_advance(a2, Decimal("550.00"), note="draw")  # a2 → 8000
        a2.refresh_from_db()
        assert a2.balance == Decimal("8000.00")

        api = APIClient()

        # socio1 sees ONLY their own numbers.
        api.force_authenticate(world["s1"])
        s1_sum = api.get(reverse("api-profit-share-me-summary"))
        assert s1_sum.data["balance"] == "8550.00"
        s1_led = api.get(reverse("api-profit-share-me-ledger"))
        assert len(s1_led.data["results"]) == 1  # one accrual, no advance

        # socio2 sees ONLY their own (different) numbers.
        api.force_authenticate(world["s2"])
        s2_sum = api.get(reverse("api-profit-share-me-summary"))
        assert s2_sum.data["balance"] == "8000.00"
        s2_led = api.get(reverse("api-profit-share-me-ledger"))
        assert len(s2_led.data["results"]) == 2  # accrual + advance

        # The two balances are different → neither response carries the other's.
        assert s1_sum.data["balance"] != s2_sum.data["balance"]

    def test_by_project_is_per_member(self, world):
        p = _project()
        inv = _invoice(p)
        InvoicePayment.objects.create(
            invoice=inv, amount=Decimal("100000.00"), payment_date=date.today(),
        )
        api = APIClient()
        api.force_authenticate(world["s1"])
        resp = api.get(reverse("api-profit-share-me-by-project"))
        assert resp.status_code == 200
        assert len(resp.data["results"]) == 1
        assert resp.data["results"][0]["accrued"] == "8550.00"


# ─────────────────────────────────────────────────────────────────────────────
# 2) Invariant: a socio is NEVER a project cost (full-stack)
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.django_db
class TestSocioNeverACostInvariant:
    def test_socio_hours_do_not_increase_other_labor(self, world):
        p = _project()

        # Plain crew (no linked user) logs hours → must count as cost.
        crew = Employee.objects.create(
            first_name="CrewA", last_name="Worker",
            social_security_number="900-00-0001",
            hourly_rate=Decimal("25.00"), is_active=True,
        )
        TimeEntry.objects.create(
            employee=crew, project=p, date=date.today(),
            start_time=time(8, 0), end_time=time(16, 0),
        )
        baseline = compute_project_financials(p, use_actuals=True).other_labor
        assert baseline > 0  # crew labor counted

        # A socio-linked employee logs the SAME hours → must add ZERO cost.
        socio_emp = Employee.objects.create(
            first_name="SocioA", last_name="Partner",
            social_security_number="900-00-0002",
            hourly_rate=Decimal("25.00"), is_active=True, user=world["s1"],
        )
        TimeEntry.objects.create(
            employee=socio_emp, project=p, date=date.today(),
            start_time=time(8, 0), end_time=time(16, 0),
        )
        after = compute_project_financials(p, use_actuals=True).other_labor
        assert after == baseline  # socio hours are not a cost


# ─────────────────────────────────────────────────────────────────────────────
# 3) Negative paths: nothing accrues when it must not
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.django_db
class TestNegativePathsConsolidated:
    def _zero_balances(self, world):
        return all(
            PartnerAccount.objects.get(pk=world[k].pk).balance == Decimal("0.00")
            for k in ("director", "a1", "a2", "biz")
        )

    def test_payment_before_cutoff_does_not_accrue(self, world):
        p = _project()
        inv = _invoice(p)
        InvoicePayment.objects.create(
            invoice=inv, amount=Decimal("100000.00"),
            payment_date=date.today() - timedelta(days=1),  # before cutoff
        )
        assert self._zero_balances(world)
        assert LedgerEntry.objects.count() == 0

    def test_project_not_included_does_not_accrue(self, world):
        p = _project(in_share=False)
        inv = _invoice(p)
        InvoicePayment.objects.create(
            invoice=inv, amount=Decimal("100000.00"), payment_date=date.today(),
        )
        assert self._zero_balances(world)
        # Explicit engine call also refuses.
        assert accrue_for_project(p).reason == "not_in_profit_share"

    def test_zero_contract_does_not_accrue(self, world):
        # No budget_total and no estimate → contract 0 → cannot accrue.
        p = _project(budget_total=Decimal("0.00"))
        inv = _invoice(p)
        InvoicePayment.objects.create(
            invoice=inv, amount=Decimal("5000.00"), payment_date=date.today(),
        )
        assert self._zero_balances(world)
        assert accrue_for_project(p).reason == "contract_non_positive"


# ─────────────────────────────────────────────────────────────────────────────
# 4) R1/R4 — including a project (or recalc) picks up HISTORICAL payments
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.django_db
class TestIncludeAccruesHistorical:
    def test_marking_included_accrues_past_payment(self, world):
        """A project that already collected BEFORE being included should accrue
        the moment the director includes it (R1) — not wait for a new payment."""
        # Start excluded; the payment hook must NOT accrue.
        p = _project(in_share=False)
        inv = _invoice(p)
        InvoicePayment.objects.create(
            invoice=inv, amount=Decimal("100000.00"), payment_date=date.today(),
        )
        a1 = PartnerAccount.objects.get(pk=world["a1"].pk)
        assert a1.balance == Decimal("0.00")  # excluded → nothing yet

        # Director includes it via the API → R1 accrues historical payment now.
        api = APIClient()
        api.force_authenticate(world["owner"])
        resp = api.post(
            reverse("api-profit-share-project-set", args=[p.id]),
            {"in_profit_share": True},
            format="json",
        )
        assert resp.status_code == 200
        assert resp.data["accrual"]["posted"] is True
        a1.refresh_from_db()
        assert a1.balance == Decimal("8550.00")  # full per_socio, 100% collected

    def test_recalc_is_idempotent(self, world):
        """Recalc on an already-current project posts nothing new (R4 safe)."""
        p = _project()
        inv = _invoice(p)
        InvoicePayment.objects.create(
            invoice=inv, amount=Decimal("100000.00"), payment_date=date.today(),
        )
        entries_before = LedgerEntry.objects.count()

        api = APIClient()
        api.force_authenticate(world["owner"])
        resp = api.post(
            reverse("api-profit-share-project-recalc", args=[p.id]), {}, format="json"
        )
        assert resp.status_code == 200
        assert resp.data["accrual"]["posted"] is False
        assert resp.data["accrual"]["reason"] == "no_change"
        assert LedgerEntry.objects.count() == entries_before  # no duplicates

