"""Phase 4 — accrual engine (idempotent, anti-conflict).

The most safety-critical phase. Verifies that posting deltas via
ProjectAccrualState makes accrual safe under re-runs, double-submits, and
partial payments, and that the cutoff rules are honored.
"""
from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model

from core import access
from core.models import (
    Expense,
    Invoice,
    InvoicePayment,
    LedgerEntry,
    PartnerAccount,
    Project,
    RateConfig,
)
from core.services.profit_share_service import accrue_for_project

User = get_user_model()


@pytest.fixture
def setup_accounts(db):
    """Owner (director) + two active socios + business account + rates."""
    cfg = RateConfig.load()
    cfg.profit_share_start_date = date.today()
    cfg.save()

    owner = User.objects.create_user("ps4_owner", password="x")
    owner.profile.role = access.ROLE_OWNER
    owner.profile.save()

    s1 = User.objects.create_user("ps4_socio1", password="x")
    s1.profile.role = access.ROLE_PARTNER
    s1.profile.save()
    s2 = User.objects.create_user("ps4_socio2", password="x")
    s2.profile.role = access.ROLE_PARTNER
    s2.profile.save()

    director = PartnerAccount.director()  # creates owner account
    a1 = PartnerAccount.for_partner(s1)
    a2 = PartnerAccount.for_partner(s2)
    biz = PartnerAccount.business()
    return {
        "cfg": cfg, "owner": owner, "s1": s1, "s2": s2,
        "director": director, "a1": a1, "a2": a2, "biz": biz,
    }


def _project(in_share=True, **kw):
    defaults = dict(
        name="PS4 Project",
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


def _balances(setup):
    return (
        PartnerAccount.objects.get(pk=setup["director"].pk).balance,
        PartnerAccount.objects.get(pk=setup["a1"].pk).balance,
        PartnerAccount.objects.get(pk=setup["a2"].pk).balance,
        PartnerAccount.objects.get(pk=setup["biz"].pk).balance,
    )


@pytest.mark.django_db
class TestAccrualMath:
    def test_partial_payment_prorata(self, setup_accounts):
        """50% collected → half of each full share (open project = estimate)."""
        p = _project()
        inv = _invoice(p)
        # Payment via the hook (in_profit_share=True triggers accrual).
        InvoicePayment.objects.create(
            invoice=inv, amount=Decimal("50000.00"), payment_date=date.today(),
        )
        director, a1, a2, biz = _balances(setup_accounts)
        assert director == Decimal("5700.00")   # 11400 × 0.5
        assert a1 == Decimal("4275.00")          # 8550 × 0.5
        assert a2 == Decimal("4275.00")
        assert biz == Decimal("4000.00")         # direction_overhead 8000 × 0.5

    def test_full_payment_full_shares(self, setup_accounts):
        p = _project()
        inv = _invoice(p)
        InvoicePayment.objects.create(
            invoice=inv, amount=Decimal("100000.00"), payment_date=date.today(),
        )
        director, a1, a2, biz = _balances(setup_accounts)
        assert director == Decimal("11400.00")
        assert a1 == Decimal("8550.00")
        assert a2 == Decimal("8550.00")
        assert biz == Decimal("8000.00")


@pytest.mark.django_db
class TestIdempotencyAndConflicts:
    def test_rerun_accrual_creates_no_duplicate(self, setup_accounts):
        p = _project()
        inv = _invoice(p)
        InvoicePayment.objects.create(
            invoice=inv, amount=Decimal("50000.00"), payment_date=date.today(),
        )
        entries_after_payment = LedgerEntry.objects.count()
        balances_before = _balances(setup_accounts)

        # Explicit re-run: must be a no-op (delta=0 everywhere).
        result = accrue_for_project(p)
        assert result.posted is False
        assert result.reason == "no_change"
        assert LedgerEntry.objects.count() == entries_after_payment
        assert _balances(setup_accounts) == balances_before

    def test_incremental_payment_posts_only_delta(self, setup_accounts):
        p = _project()
        inv = _invoice(p)
        InvoicePayment.objects.create(
            invoice=inv, amount=Decimal("50000.00"), payment_date=date.today(),
        )
        entries_first = LedgerEntry.objects.count()
        # Second payment brings fraction 0.5 → 1.0; only the delta is posted.
        InvoicePayment.objects.create(
            invoice=inv, amount=Decimal("50000.00"), payment_date=date.today(),
        )
        director, a1, a2, biz = _balances(setup_accounts)
        assert director == Decimal("11400.00")
        assert a1 == Decimal("8550.00")
        assert biz == Decimal("8000.00")
        # One more delta-entry batch per account, not a full re-post.
        assert LedgerEntry.objects.count() > entries_first

    def test_overpayment_clamped_to_full_net(self, setup_accounts):
        """Collecting more than the contract never accrues beyond 100% net."""
        p = _project()
        inv = _invoice(p, total="100000.00")
        InvoicePayment.objects.create(
            invoice=inv, amount=Decimal("100000.00"), payment_date=date.today(),
        )
        InvoicePayment.objects.create(
            invoice=inv, amount=Decimal("50000.00"), payment_date=date.today(),
        )
        director, a1, a2, biz = _balances(setup_accounts)
        # Still exactly the full shares — fraction clamped at 1.0.
        assert director == Decimal("11400.00")
        assert a1 == Decimal("8550.00")
        assert biz == Decimal("8000.00")


@pytest.mark.django_db
class TestCutoffRules:
    def test_payment_before_start_date_does_not_accrue(self, setup_accounts):
        p = _project()
        inv = _invoice(p)
        # Payment dated yesterday (before cutoff = today) → excluded.
        InvoicePayment.objects.create(
            invoice=inv, amount=Decimal("50000.00"),
            payment_date=date.today() - timedelta(days=1),
        )
        director, a1, a2, biz = _balances(setup_accounts)
        assert (director, a1, a2, biz) == (
            Decimal("0.00"), Decimal("0.00"), Decimal("0.00"), Decimal("0.00")
        )

    def test_project_not_in_profit_share_does_not_accrue(self, setup_accounts):
        p = _project(in_share=False)
        inv = _invoice(p)
        InvoicePayment.objects.create(
            invoice=inv, amount=Decimal("50000.00"), payment_date=date.today(),
        )
        director, a1, a2, biz = _balances(setup_accounts)
        assert (director, a1, a2, biz) == (
            Decimal("0.00"), Decimal("0.00"), Decimal("0.00"), Decimal("0.00")
        )
        # And a direct call confirms the skip reason.
        assert accrue_for_project(p).reason == "not_in_profit_share"

    def test_zero_contract_does_not_accrue(self, setup_accounts):
        p = _project(budget_total=Decimal("0.00"))
        inv = _invoice(p, total="0.00")
        InvoicePayment.objects.create(
            invoice=inv, amount=Decimal("0.00") + Decimal("10.00"),
            payment_date=date.today(),
        )
        assert accrue_for_project(p).reason == "contract_non_positive"


@pytest.mark.django_db
class TestLossAtCloseSharesNegative:
    def test_real_loss_drives_negative_balances(self, setup_accounts):
        """Closed project (end_date set) with huge actual cost → negative net →
        accrual posts negative deltas (socios share a real loss)."""
        p = _project(end_date=date.today(),
                     budget_materials=Decimal("0"), budget_labor=Decimal("0"))
        Expense.objects.create(
            project=p, project_name=p.name, amount=Decimal("90000.00"),
            date=date.today(), category="MATERIALES",
        )
        inv = _invoice(p)
        InvoicePayment.objects.create(
            invoice=inv, amount=Decimal("100000.00"), payment_date=date.today(),
        )
        director, a1, a2, biz = _balances(setup_accounts)
        assert director < 0  # real loss flows to the director share
        assert a1 < 0        # and to the socios
        assert a2 < 0


@pytest.mark.django_db
class TestNoTimingNegativeWhileOpen:
    def test_open_project_balances_never_negative_from_timing(self, setup_accounts):
        """While OPEN we use the (positive) estimate net, so progressive
        payments only ever ADD to socio balances — no timing-driven negative."""
        p = _project()  # open, positive estimate net
        inv = _invoice(p)
        prev = Decimal("-1")
        for chunk in ["10000.00", "20000.00", "30000.00"]:
            InvoicePayment.objects.create(
                invoice=inv, amount=Decimal(chunk), payment_date=date.today(),
            )
            a1 = PartnerAccount.objects.get(pk=setup_accounts["a1"].pk).balance
            assert a1 >= 0          # never negative
            assert a1 >= prev       # monotonically non-decreasing
            prev = a1
