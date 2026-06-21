"""Phase 5 — advances / withdrawals (money OUT, director-authorized).

Verifies the ledger primitive: withdrawals to zero, advances that go negative
(loan), input validation, and that a later accrual pays the negative down.
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model

from core import access
from core.models import (
    Invoice,
    InvoicePayment,
    LedgerEntry,
    PartnerAccount,
    Project,
    RateConfig,
)
from core.services.profit_share_service import record_advance

User = get_user_model()


@pytest.fixture
def socio_account(db):
    cfg = RateConfig.load()
    cfg.profit_share_start_date = date.today()
    cfg.save()
    u = User.objects.create_user("ps5_socio", password="x")
    u.profile.role = access.ROLE_PARTNER
    u.profile.save()
    return PartnerAccount.for_partner(u)


@pytest.mark.django_db
class TestAdvance:
    def test_withdrawal_reduces_balance_to_zero(self, socio_account):
        socio_account.balance = Decimal("1000.00")
        socio_account.save()
        result = record_advance(socio_account, Decimal("1000.00"), note="cash out")
        assert result.new_balance == Decimal("0.00")
        assert result.left_negative is False
        acc = PartnerAccount.objects.get(pk=socio_account.pk)
        assert acc.balance == Decimal("0.00")

    def test_advance_can_go_negative(self, socio_account):
        result = record_advance(socio_account, Decimal("500.00"), note="loan")
        assert result.new_balance == Decimal("-500.00")
        assert result.left_negative is True

    def test_advance_posts_negative_ledger_entry(self, socio_account):
        record_advance(socio_account, Decimal("250.00"))
        entry = LedgerEntry.objects.filter(
            account=socio_account, type=LedgerEntry.TYPE_ADVANCE
        ).latest("created_at")
        assert entry.amount == Decimal("-250.00")
        assert entry.running_balance == Decimal("-250.00")
        assert entry.project_id is None

    def test_zero_or_negative_amount_rejected(self, socio_account):
        with pytest.raises(ValueError):
            record_advance(socio_account, Decimal("0.00"))
        with pytest.raises(ValueError):
            record_advance(socio_account, Decimal("-10.00"))


@pytest.mark.django_db
class TestFutureAccrualPaysDownNegative:
    def test_accrual_offsets_prior_advance(self, socio_account):
        # Director + business + a second socio so accrual has full participant set.
        owner = User.objects.create_user("ps5_owner", password="x")
        owner.profile.role = access.ROLE_OWNER
        owner.profile.save()
        PartnerAccount.director()
        PartnerAccount.business()
        u2 = User.objects.create_user("ps5_socio2", password="x")
        u2.profile.role = access.ROLE_PARTNER
        u2.profile.save()
        PartnerAccount.for_partner(u2)

        # Socio takes a 1,000 advance → balance −1,000.
        record_advance(socio_account, Decimal("1000.00"))
        assert PartnerAccount.objects.get(pk=socio_account.pk).balance == Decimal("-1000.00")

        # A project pays 50% → socio accrues 4,275 (open/estimate, 2 socios).
        p = Project.objects.create(
            name="PS5 Project", budget_total=Decimal("100000.00"),
            budget_materials=Decimal("20000.00"), budget_labor=Decimal("30000.00"),
            in_profit_share=True,
        )
        inv = Invoice.objects.create(
            project=p, total_amount=Decimal("100000.00"),
            date_issued=date.today(), status="APPROVED",
        )
        InvoicePayment.objects.create(
            invoice=inv, amount=Decimal("50000.00"), payment_date=date.today(),
        )

        # −1,000 + 4,275 = 3,275 (accrual paid the advance down automatically).
        assert PartnerAccount.objects.get(pk=socio_account.pk).balance == Decimal("3275.00")
