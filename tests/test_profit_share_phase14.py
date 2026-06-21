"""Phase 14 — Director Panel end-to-end: every button works and PERSISTS.

A capstone integration test that drives the whole director workflow through the
real HTTP endpoints, in the order a director would use them, and asserts that
each action saved a real record. If any director button silently failed to
persist, this breaks.
"""
from __future__ import annotations

from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient

from core import access
from core.models import (
    LedgerEntry,
    PartnerAccount,
    Profile,
    Project,
    RateConfig,
)

User = get_user_model()


def _user(username, role):
    u = User.objects.create_user(username=username, password="x")
    Profile.objects.update_or_create(user=u, defaults={"role": role})
    u.refresh_from_db()
    return u


@pytest.mark.django_db
def test_director_panel_full_workflow_persists_everything():
    api = APIClient()
    director = _user("p14_director", access.ROLE_OWNER)
    pm_a = _user("p14_pm_a", access.ROLE_PM)
    pm_b = _user("p14_pm_b", access.ROLE_PM)
    api.force_authenticate(director)

    member_url = reverse("api-profit-share-member-set")

    # 1) Add two PMs as socios (role unchanged, accounts created + active).
    r = api.post(member_url, {"user_id": pm_a.id, "is_socio": True}, format="json")
    assert r.status_code == 200 and r.data["is_active_socio"] is True
    acc_a_id = r.data["account_id"]
    r = api.post(member_url, {"user_id": pm_b.id, "is_socio": True}, format="json")
    assert r.status_code == 200
    assert PartnerAccount.objects.filter(is_business=False, is_active_socio=True).count() == 2
    pm_a.refresh_from_db()
    assert access.get_role(pm_a) == access.ROLE_PM          # role untouched
    assert access.is_profit_share_member(pm_a) is True

    # 2) Include a project in the profit-share.
    project = Project.objects.create(name="P14 Project")
    r = api.post(
        reverse("api-profit-share-project-set", args=[project.id]),
        {"in_profit_share": True}, format="json",
    )
    assert r.status_code == 200
    project.refresh_from_db()
    assert project.in_profit_share is True

    # 3) Save the rate configuration (persists to the singleton).
    r = api.put(
        reverse("api-profit-share-rates"),
        {"director_split_pct": "45.00", "company_overhead_pct": "10.00"},
        format="json",
    )
    assert r.status_code == 200
    cfg = RateConfig.load()
    assert cfg.director_split_pct == Decimal("45.00")
    assert cfg.company_overhead_pct == Decimal("10.00")

    # 4) Record an advance paid by Zelle (saves a signed LedgerEntry + balance).
    r = api.post(
        reverse("api-profit-share-account-advance", args=[acc_a_id]),
        {"amount": "250.00", "payment_method": "ZELLE", "payment_reference": "z-14"},
        format="json",
    )
    assert r.status_code == 201
    entry = LedgerEntry.objects.get(pk=r.data["entry_id"])
    assert entry.type == LedgerEntry.TYPE_ADVANCE
    assert entry.amount == Decimal("-250.00")
    assert entry.payment_method == "ZELLE" and entry.payment_reference == "z-14"
    acc_a = PartnerAccount.objects.get(pk=acc_a_id)
    assert acc_a.balance == Decimal("-250.00")

    # 5) Recalc the included project (idempotent, must not error).
    r = api.post(reverse("api-profit-share-project-recalc", args=[project.id]), {}, format="json")
    assert r.status_code == 200
    assert "accrual" in r.data

    # 6) Deactivate socio B — account preserved, only the flag flips.
    r = api.post(member_url, {"user_id": pm_b.id, "is_socio": False}, format="json")
    assert r.status_code == 200 and r.data["is_active_socio"] is False
    assert PartnerAccount.objects.filter(owner=pm_b).exists() is True

    # 7) Socio A sees their own statement (with the Zelle withdrawal + method)
    #    and the transparent per-project roster.
    api.force_authenticate(pm_a)
    summary = api.get(reverse("api-profit-share-me-summary"))
    assert summary.status_code == 200
    assert summary.data["balance"] == "-250.00"
    ledger = api.get(reverse("api-profit-share-me-ledger"))
    adv = [e for e in ledger.data["results"] if e["type"] == "ADVANCE"][0]
    assert adv["payment_method"] == "ZELLE"
    breakdown = api.get(reverse("api-profit-share-project-breakdown", args=[project.id]))
    assert breakdown.status_code == 200
    assert any(s["is_me"] for s in breakdown.data["socios"])
