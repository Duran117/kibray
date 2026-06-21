"""Phase 13 — payment method on advances/withdrawals (check / Zelle / ...).

Money going OUT can be paid different ways ("va variando"): a check, a Zelle
transfer, cash, a bank transfer, etc. Each advance/withdrawal now records HOW it
was paid plus an optional reference (check number, Zelle confirmation), and the
socio sees it on their own statement.
"""
from __future__ import annotations

from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient

from core import access
from core.models import LedgerEntry, PartnerAccount, Profile
from core.services.profit_share_service import record_advance

User = get_user_model()


def _user(username, role):
    u = User.objects.create_user(username=username, password="x")
    Profile.objects.update_or_create(user=u, defaults={"role": role})
    u.refresh_from_db()
    return u


@pytest.fixture
def api():
    return APIClient()


@pytest.fixture
def director(db):
    return _user("p13_director", access.ROLE_OWNER)


@pytest.fixture
def account(db):
    return PartnerAccount.for_partner(_user("p13_socio", access.ROLE_PM))


def _advance_url(account):
    return reverse("api-profit-share-account-advance", args=[account.id])


# ─────────────────────────────────────────────────────────────────────────────
# Service primitive
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.django_db
class TestRecordAdvancePaymentFields:
    def test_stores_method_and_reference(self, account):
        result = record_advance(
            account, Decimal("100.00"),
            payment_method=LedgerEntry.METHOD_CHECK, payment_reference="1234",
        )
        e = LedgerEntry.objects.get(pk=result.entry_id)
        assert e.payment_method == "CHECK"
        assert e.payment_reference == "1234"

    def test_defaults_to_blank(self, account):
        result = record_advance(account, Decimal("50.00"))
        e = LedgerEntry.objects.get(pk=result.entry_id)
        assert e.payment_method == ""
        assert e.payment_reference == ""


# ─────────────────────────────────────────────────────────────────────────────
# Advance endpoint
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.django_db
class TestAdvanceEndpointPaymentMethod:
    def test_records_zelle_with_reference(self, api, director, account):
        api.force_authenticate(director)
        resp = api.post(
            _advance_url(account),
            {"amount": "200.00", "payment_method": "ZELLE", "payment_reference": "conf-9"},
            format="json",
        )
        assert resp.status_code == 201
        assert resp.data["payment_method"] == "ZELLE"
        assert resp.data["payment_reference"] == "conf-9"
        e = LedgerEntry.objects.get(pk=resp.data["entry_id"])
        assert e.payment_method == "ZELLE"
        assert e.payment_reference == "conf-9"

    def test_method_is_case_insensitive(self, api, director, account):
        api.force_authenticate(director)
        resp = api.post(
            _advance_url(account),
            {"amount": "10.00", "payment_method": "check"},
            format="json",
        )
        assert resp.status_code == 201
        assert resp.data["payment_method"] == "CHECK"

    def test_invalid_method_is_rejected(self, api, director, account):
        api.force_authenticate(director)
        resp = api.post(
            _advance_url(account),
            {"amount": "10.00", "payment_method": "BITCOIN"},
            format="json",
        )
        assert resp.status_code == 400
        assert LedgerEntry.objects.filter(account=account).count() == 0

    def test_blank_method_is_allowed(self, api, director, account):
        api.force_authenticate(director)
        resp = api.post(_advance_url(account), {"amount": "10.00"}, format="json")
        assert resp.status_code == 201
        e = LedgerEntry.objects.get(pk=resp.data["entry_id"])
        assert e.payment_method == ""


# ─────────────────────────────────────────────────────────────────────────────
# The socio sees the method on their own statement
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.django_db
class TestMyLedgerExposesMethod:
    def test_ledger_includes_payment_fields(self, api, director, account):
        record_advance(
            account, Decimal("75.00"),
            payment_method=LedgerEntry.METHOD_ZELLE, payment_reference="z-1",
        )
        api.force_authenticate(account.owner)
        resp = api.get(reverse("api-profit-share-me-ledger"))
        assert resp.status_code == 200
        adv = [r for r in resp.data["results"] if r["type"] == "ADVANCE"][0]
        assert adv["payment_method"] == "ZELLE"
        assert adv["payment_reference"] == "z-1"


@pytest.mark.django_db
class TestModelChoices:
    def test_choices_include_check_and_zelle(self):
        codes = {c for c, _ in LedgerEntry.PAYMENT_METHOD_CHOICES}
        assert {"CHECK", "ZELLE"} <= codes
