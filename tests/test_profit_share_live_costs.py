"""Live-cost rules for profit-share (owner's clarifications, Jun 2026).

These lock in three behaviors the owner asked for explicitly:

1. EVERY expense logged on a project reduces its net — regardless of category
   (materials, food, insurance, office, other…). Company-wide fixed costs stay
   in the % rates; per-project expenses are real deductions.
2. Costs apply LIVE (the same day), not only when the project closes: saving a
   new expense re-accrues immediately, so everyone's share drops at once; and
   deleting an expense raises the net back.
3. The director IS the admin (no separate ``owner`` role needed). Their 40%
   accrues to THEIR account, and "My Earnings" shows it.
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from core import access
from core.models import (
    Expense,
    Invoice,
    InvoicePayment,
    PartnerAccount,
    Project,
    RateConfig,
)
from core.services.profit_share_service import compute_project_financials

User = get_user_model()


@pytest.fixture
def world(db):
    """Admin-as-director + two active socios + business account, today cutoff.

    Deliberately uses an ``admin`` role (NOT ``owner``) to prove the director =
    admin resolution path.
    """
    cfg = RateConfig.load()
    cfg.profit_share_start_date = date.today()
    cfg.save()

    admin = User.objects.create_user("plc_admin", password="x")
    admin.profile.role = access.ROLE_ADMIN
    admin.profile.save()

    s1 = User.objects.create_user("plc_s1", password="x")
    s1.profile.role = access.ROLE_PARTNER
    s1.profile.save()
    s2 = User.objects.create_user("plc_s2", password="x")
    s2.profile.role = access.ROLE_PARTNER
    s2.profile.save()

    return {
        "cfg": cfg,
        "admin": admin,
        "s1": s1,
        "s2": s2,
        "director": PartnerAccount.director(),  # resolves to the admin
        "a1": PartnerAccount.for_partner(s1),
        "a2": PartnerAccount.for_partner(s2),
        "biz": PartnerAccount.business(),
    }


def _project(in_share=True, **kw):
    defaults = dict(
        name="PLC Project",
        budget_total=Decimal("100000.00"),
        in_profit_share=in_share,
    )
    defaults.update(kw)
    return Project.objects.create(**defaults)


def _expense(project, amount, category):
    return Expense.objects.create(
        project=project, project_name=project.name,
        amount=Decimal(amount), date=date.today(), category=category,
    )


def _balance(acc):
    return PartnerAccount.objects.get(pk=acc.pk).balance


# ─────────────────────────────────────────────────────────────────────────────
# 1) Every category reduces the net (not just materials)
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.django_db
class TestEveryCategoryReducesNet:
    def test_non_material_expenses_lower_the_net(self, world):
        p = _project()

        base = compute_project_financials(p, use_actuals=True)
        assert base.materials == Decimal("0.00")
        assert base.other_expenses == Decimal("0.00")

        # Non-material categories the OLD model ignored — now they all count.
        _expense(p, "5000.00", "SEGURO")
        _expense(p, "2000.00", "OFICINA")
        _expense(p, "1000.00", "COMIDA")
        _expense(p, "500.00", "OTRO")
        # And a blank/unknown category must still count.
        _expense(p, "300.00", "")

        # Materials stay their own line; subcontract labor its own.
        _expense(p, "10000.00", "MATERIALES")
        _expense(p, "4000.00", "MANO_OBRA")

        fin = compute_project_financials(p, use_actuals=True)
        assert fin.materials == Decimal("10000.00")
        assert fin.other_labor == Decimal("4000.00")
        # 5000 + 2000 + 1000 + 500 + 300 = 8800 (everything that isn't
        # materials or subcontract labor, regardless of category).
        assert fin.other_expenses == Decimal("8800.00")

        # net = 100000 − 10000 − 4000 − 8800 − 8000 − 8000 − 5000 − 500
        assert fin.net == Decimal("55700.00")

    def test_every_expense_is_counted_exactly_once(self, world):
        """materials + other_labor + other_expenses == Σ all expenses."""
        p = _project()
        _expense(p, "111.11", "MATERIALES")
        _expense(p, "222.22", "MANO_OBRA")
        _expense(p, "333.33", "SEGURO")
        _expense(p, "44.44", "")  # blank category still counts

        fin = compute_project_financials(p, use_actuals=True)
        total = fin.materials + fin.other_labor + fin.other_expenses
        assert total == Decimal("711.10")  # 111.11+222.22+333.33+44.44


# ─────────────────────────────────────────────────────────────────────────────
# 2) Costs apply LIVE — saving/deleting an expense re-accrues immediately
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.django_db
class TestExpenseTriggersLiveAccrual:
    def _pay_full(self, world):
        p = _project()
        inv = Invoice.objects.create(
            project=p, total_amount=Decimal("100000.00"),
            date_issued=date.today(), status="APPROVED",
        )
        InvoicePayment.objects.create(
            invoice=inv, amount=Decimal("100000.00"), payment_date=date.today(),
        )
        return p

    def test_new_expense_lowers_everyones_share_same_day(self, world):
        p = self._pay_full(world)

        # No costs yet → net 78,500 → per_socio 23,550, director 31,400.
        assert _balance(world["a1"]) == Decimal("23550.00")
        assert _balance(world["a2"]) == Decimal("23550.00")
        assert _balance(world["director"]) == Decimal("31400.00")
        biz_before = _balance(world["biz"])

        # Owner logs a 50k material cost mid-project → shares MUST drop now.
        _expense(p, "50000.00", "MATERIALES")

        # net = 100000 − 50000 − fixed(21500) = 28,500.
        assert _balance(world["a1"]) == Decimal("8550.00")
        assert _balance(world["a2"]) == Decimal("8550.00")
        assert _balance(world["director"]) == Decimal("11400.00")
        # The fixed % deduction (direction overhead → business) is contract-based
        # and must NOT move when project costs change.
        assert _balance(world["biz"]) == biz_before

    def test_any_category_triggers_the_drop(self, world):
        p = self._pay_full(world)
        assert _balance(world["a1"]) == Decimal("23550.00")

        # A NON-material expense must also trigger a live re-accrual.
        _expense(p, "30000.00", "SEGURO")

        # net = 100000 − 30000 − 21500 = 48,500 → per_socio 14,550.
        assert _balance(world["a1"]) == Decimal("14550.00")

    def test_deleting_an_expense_raises_the_net_back(self, world):
        p = self._pay_full(world)
        exp = _expense(p, "50000.00", "MATERIALES")
        assert _balance(world["a1"]) == Decimal("8550.00")

        # Removing the cost restores the net (and the shares) the same day.
        exp.delete()
        assert _balance(world["a1"]) == Decimal("23550.00")
        assert _balance(world["director"]) == Decimal("31400.00")


# ─────────────────────────────────────────────────────────────────────────────
# 3) Director = admin: the account exists and receives the 40%
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.django_db
class TestDirectorIsAdmin:
    def test_director_account_resolves_to_the_admin(self, world):
        director = PartnerAccount.director()
        assert director is not None
        assert director.owner == world["admin"]
        assert director.is_active_socio is False  # not part of the 60% pool
        assert access.is_director(world["admin"]) is True

    def test_superuser_without_role_still_resolves_as_director(self, db):
        su = User.objects.create_user("plc_su", password="x", is_superuser=True)
        # No owner/admin role anywhere → falls back to the superuser.
        director = PartnerAccount.director()
        assert director is not None
        assert director.owner == su

    def test_my_earnings_shows_the_admin_their_account(self, world, client):
        client.force_login(world["admin"])
        resp = client.get(reverse("profit_share_my_earnings"))
        assert resp.status_code == 200
        # The fix: an admin-director is no longer told "you have no account".
        assert resp.context["is_director"] is True
        assert resp.context["has_account"] is True
        assert b"don&#x27;t have a profit-share account" not in resp.content

    def test_director_40_percent_accrues_to_admin_account(self, world):
        p = _project()
        inv = Invoice.objects.create(
            project=p, total_amount=Decimal("100000.00"),
            date_issued=date.today(), status="APPROVED",
        )
        InvoicePayment.objects.create(
            invoice=inv, amount=Decimal("100000.00"), payment_date=date.today(),
        )
        # 40% of net (78,500 with no costs) = 31,400 → in the ADMIN's account.
        assert _balance(world["director"]) == Decimal("31400.00")
        assert PartnerAccount.director().owner == world["admin"]

    def test_director_not_shown_as_toggleable_socio(self, world, client):
        client.force_login(world["admin"])
        resp = client.get(reverse("profit_share_director_panel"))
        assert resp.status_code == 200
        content = resp.content.decode()
        # An active socio IS in the membership table...
        assert f'data-member-user="{world["s1"].id}"' in content
        # ...but the director is NOT toggleable there (shown only in balances).
        assert f'data-member-user="{world["admin"].id}"' not in content

    def test_cannot_make_director_a_socio(self, world):
        from rest_framework.test import APIClient

        api = APIClient()
        api.force_authenticate(world["admin"])
        resp = api.post(
            reverse("api-profit-share-member-set"),
            {"user_id": world["admin"].id, "is_socio": True},
            format="json",
        )
        assert resp.status_code == 400
        # The director account stays out of the 60% pool.
        assert PartnerAccount.director().is_active_socio is False
