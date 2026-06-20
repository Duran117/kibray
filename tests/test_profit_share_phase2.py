"""Phase 2 — profit-share model layer.

Locks in the additive models and the critical cutoff guarantee that all
existing projects stay OUT of the distribution (in_profit_share defaults False).
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from core.models import (
    LedgerEntry,
    PartnerAccount,
    Project,
    ProjectAccrualState,
    RateConfig,
)

User = get_user_model()


@pytest.mark.django_db
class TestRateConfigSingleton:
    def test_load_creates_singleton_with_defaults(self):
        cfg = RateConfig.load()
        assert cfg.pk == 1
        assert cfg.company_overhead_pct == Decimal("8.00")
        assert cfg.direction_overhead_pct == Decimal("8.00")
        assert cfg.callback_reserve_pct == Decimal("5.00")
        assert cfg.bad_debt_reserve_pct == Decimal("0.50")
        assert cfg.director_split_pct == Decimal("40.00")
        assert cfg.direction_overhead_destination == RateConfig.DESTINATION_BUSINESS

    def test_start_date_defaults_to_today(self):
        cfg = RateConfig.load()
        assert cfg.profit_share_start_date == date.today()

    def test_load_is_idempotent_single_row(self):
        a = RateConfig.load()
        a.director_split_pct = Decimal("45.00")
        a.save()
        b = RateConfig.load()
        assert b.pk == 1
        assert b.director_split_pct == Decimal("45.00")
        assert RateConfig.objects.count() == 1

    def test_save_forces_pk_1(self):
        cfg = RateConfig(profit_share_start_date=date(2026, 6, 20))
        cfg.save()
        assert cfg.pk == 1
        # A second instance also collapses onto pk=1
        cfg2 = RateConfig(profit_share_start_date=date(2026, 1, 1))
        cfg2.save()
        assert cfg2.pk == 1
        assert RateConfig.objects.count() == 1

    def test_percentage_out_of_range_rejected(self):
        cfg = RateConfig.load()
        cfg.director_split_pct = Decimal("150.00")
        with pytest.raises(ValidationError):
            cfg.clean()

    def test_negative_percentage_rejected(self):
        cfg = RateConfig.load()
        cfg.company_overhead_pct = Decimal("-1.00")
        with pytest.raises(ValidationError):
            cfg.clean()


@pytest.mark.django_db
class TestPartnerAccount:
    def test_business_account_created_once(self):
        a = PartnerAccount.business()
        b = PartnerAccount.business()
        assert a.pk == b.pk
        assert a.is_business is True
        assert a.owner_id is None
        assert PartnerAccount.objects.filter(is_business=True).count() == 1

    def test_for_partner_creates_and_reuses(self):
        u = User.objects.create_user("socio1", password="x")
        a = PartnerAccount.for_partner(u)
        b = PartnerAccount.for_partner(u)
        assert a.pk == b.pk
        assert a.owner_id == u.id
        assert a.is_business is False
        assert a.is_active_socio is True

    def test_business_with_owner_is_invalid(self):
        u = User.objects.create_user("socio2", password="x")
        acc = PartnerAccount(is_business=True, owner=u)
        with pytest.raises(ValidationError):
            acc.clean()

    def test_non_business_without_owner_is_invalid(self):
        acc = PartnerAccount(is_business=False, owner=None)
        with pytest.raises(ValidationError):
            acc.clean()

    def test_balance_can_be_negative(self):
        u = User.objects.create_user("socio3", password="x")
        acc = PartnerAccount.for_partner(u)
        acc.balance = Decimal("-500.00")
        acc.save()
        acc.refresh_from_db()
        assert acc.balance == Decimal("-500.00")


@pytest.mark.django_db
class TestLedgerEntry:
    def test_create_accrual_entry(self):
        u = User.objects.create_user("socio4", password="x")
        acc = PartnerAccount.for_partner(u)
        p = Project.objects.create(name="Ledger Project")
        e = LedgerEntry.objects.create(
            account=acc, project=p, type=LedgerEntry.TYPE_ACCRUAL,
            amount=Decimal("1000.00"), running_balance=Decimal("1000.00"),
            note="first accrual",
        )
        assert e.pk is not None
        assert e.type == "ACCRUAL"
        assert acc.entries.count() == 1

    def test_advance_entry_is_negative(self):
        u = User.objects.create_user("socio5", password="x")
        acc = PartnerAccount.for_partner(u)
        e = LedgerEntry.objects.create(
            account=acc, type=LedgerEntry.TYPE_ADVANCE,
            amount=Decimal("-200.00"), running_balance=Decimal("-200.00"),
        )
        assert e.amount == Decimal("-200.00")
        assert e.project_id is None


@pytest.mark.django_db
class TestProjectAccrualState:
    def test_unique_per_project_account(self):
        from django.db import IntegrityError, transaction

        u = User.objects.create_user("socio6", password="x")
        acc = PartnerAccount.for_partner(u)
        p = Project.objects.create(name="Accrual State Project")
        ProjectAccrualState.objects.create(project=p, account=acc, accrued=Decimal("100"))
        with pytest.raises(IntegrityError):
            with transaction.atomic():
                ProjectAccrualState.objects.create(
                    project=p, account=acc, accrued=Decimal("200")
                )

    def test_accrued_defaults_zero(self):
        u = User.objects.create_user("socio7", password="x")
        acc = PartnerAccount.for_partner(u)
        p = Project.objects.create(name="Accrual Default Project")
        st = ProjectAccrualState.objects.create(project=p, account=acc)
        assert st.accrued == Decimal("0.00")


@pytest.mark.django_db
class TestProjectCutoffFlag:
    def test_in_profit_share_defaults_false(self):
        p = Project.objects.create(name="Cutoff Project")
        assert p.in_profit_share is False

    def test_existing_projects_all_excluded(self):
        """Simulate the migration guarantee: any project created without
        explicitly opting in is excluded."""
        for i in range(3):
            Project.objects.create(name=f"Legacy {i}")
        assert Project.objects.filter(in_profit_share=True).count() == 0
