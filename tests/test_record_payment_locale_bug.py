"""Regression tests for the invoice "record payment" 500 + income data bugs.

Root cause (found 2026-06-21): the app runs in a Spanish locale, so Django
localizes Decimals in templates with a COMMA decimal separator. The record
payment form rendered the default amount as e.g. ``1.234,56`` and the view fed
that straight into ``Decimal(...)`` → ``InvalidOperation`` → HTTP 500, with
nothing saved ("como si no se guardara").

Also fixed here:
  * the auto-created ``Income`` stored the InvoicePayment's English method code
    (e.g. "CHECK"), which is not a valid ``Income.payment_method`` choice;
  * two change-order amount parsers silently turned localized amounts into 0.

These tests fail without the fix and pass with it.
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import translation

from core.models import Income, Invoice, InvoicePayment
from core.views._helpers import parse_money

User = get_user_model()


@pytest.fixture
def staff_user(db):
    return User.objects.create_user(username="rp_staff", password="x", is_staff=True)


@pytest.fixture
def invoice(db):
    from core.models import Project

    project = Project.objects.create(name="Record Payment Project")
    return Invoice.objects.create(
        project=project, total_amount=Decimal("1234.56"), status="SENT"
    )


# ─────────────────────────────────────────────────────────────────────────────
# parse_money — the shared, locale-tolerant parser
# ─────────────────────────────────────────────────────────────────────────────
class TestParseMoney:
    @pytest.mark.parametrize(
        "raw,expected",
        [
            ("1234.56", Decimal("1234.56")),   # plain
            ("1.234,56", Decimal("1234.56")),  # es: dot thousands, comma decimal
            ("1,234.56", Decimal("1234.56")),  # en: comma thousands, dot decimal
            ("500,00", Decimal("500.00")),     # es: lone comma decimal
            ("500.00", Decimal("500.00")),     # en: lone dot decimal
            ("1000", Decimal("1000")),         # integer
            ("$1,234.56", Decimal("1234.56")),  # currency symbol
            ("  42  ", Decimal("42")),          # whitespace
            ("-50,5", Decimal("-50.5")),        # negative + es decimal
            ("1.000.000,00", Decimal("1000000.00")),  # es millions
        ],
    )
    def test_parses_localized_forms(self, raw, expected):
        assert parse_money(raw) == expected

    def test_blank_raises(self):
        from django.core.exceptions import ValidationError

        with pytest.raises(ValidationError):
            parse_money("")
        with pytest.raises(ValidationError):
            parse_money(None)

    def test_blank_allowed_returns_none(self):
        assert parse_money("", allow_blank=True) is None
        assert parse_money(None, allow_blank=True) is None

    def test_garbage_raises(self):
        from django.core.exceptions import ValidationError

        with pytest.raises(ValidationError):
            parse_money("abc")


# ─────────────────────────────────────────────────────────────────────────────
# The form renders an UNLOCALIZED default amount (period, not comma)
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.django_db
class TestFormRendersUnlocalized:
    def test_default_amount_uses_period_not_comma(self, client, staff_user, invoice):
        client.force_login(staff_user)
        with translation.override("es"):
            resp = client.get(reverse("record_invoice_payment", args=[invoice.id]))
        assert resp.status_code == 200
        body = resp.content.decode()
        # The number input default must be a dot-decimal so <input type=number>
        # and Decimal() both accept it.
        assert 'value="1234.56"' in body
        assert 'value="1.234,56"' not in body
        assert 'value="1234,56"' not in body


# ─────────────────────────────────────────────────────────────────────────────
# POST: the actual 500 regression — localized amounts must save, not crash
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.django_db
class TestPostLocalizedAmount:
    def test_spanish_amount_with_comma_is_saved(self, client, staff_user, invoice):
        client.force_login(staff_user)
        resp = client.post(
            reverse("record_invoice_payment", args=[invoice.id]),
            {
                "amount": "1.234,56",  # what the localized form/user submits
                "payment_date": date.today().isoformat(),
                "payment_method": "CHECK",
                "reference": "CHK-9",
            },
        )
        # No 500 — a clean redirect to the dashboard.
        assert resp.status_code == 302
        assert reverse("invoice_payment_dashboard") in resp.url
        invoice.refresh_from_db()
        assert invoice.amount_paid == Decimal("1234.56")
        assert invoice.status == "PAID"

    def test_plain_amount_still_works(self, client, staff_user, invoice):
        client.force_login(staff_user)
        resp = client.post(
            reverse("record_invoice_payment", args=[invoice.id]),
            {
                "amount": "1000.00",
                "payment_date": date.today().isoformat(),
                "payment_method": "CASH",
            },
        )
        assert resp.status_code == 302
        invoice.refresh_from_db()
        assert invoice.amount_paid == Decimal("1000.00")

    def test_invalid_amount_does_not_500_and_creates_nothing(
        self, client, staff_user, invoice
    ):
        client.force_login(staff_user)
        resp = client.post(
            reverse("record_invoice_payment", args=[invoice.id]),
            {
                "amount": "not-a-number",
                "payment_date": date.today().isoformat(),
                "payment_method": "CHECK",
            },
        )
        assert resp.status_code == 302  # graceful redirect, NOT 500
        invoice.refresh_from_db()
        assert invoice.amount_paid == Decimal("0")
        assert InvoicePayment.objects.filter(invoice=invoice).count() == 0

    def test_zero_amount_is_rejected(self, client, staff_user, invoice):
        client.force_login(staff_user)
        resp = client.post(
            reverse("record_invoice_payment", args=[invoice.id]),
            {"amount": "0", "payment_date": date.today().isoformat(), "payment_method": "CHECK"},
        )
        assert resp.status_code == 302
        assert InvoicePayment.objects.filter(invoice=invoice).count() == 0

    def test_empty_payment_date_falls_back_to_today(self, client, staff_user, invoice):
        client.force_login(staff_user)
        resp = client.post(
            reverse("record_invoice_payment", args=[invoice.id]),
            {"amount": "100.00", "payment_date": "", "payment_method": "CHECK"},
        )
        assert resp.status_code == 302
        pay = InvoicePayment.objects.get(invoice=invoice)
        assert pay.payment_date == date.today()


# ─────────────────────────────────────────────────────────────────────────────
# The auto-created Income gets a VALID (Spanish) payment_method
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.django_db
class TestIncomeMethodMapping:
    @pytest.mark.parametrize(
        "ip_method,income_method",
        [
            ("CHECK", "CHEQUE"),
            ("CASH", "EFECTIVO"),
            ("TRANSFER", "TRANSFERENCIA"),
            ("CARD", "OTRO"),
            ("OTHER", "OTRO"),
        ],
    )
    def test_method_is_mapped_to_income_choices(self, invoice, ip_method, income_method):
        pay = InvoicePayment.objects.create(
            invoice=invoice, amount=Decimal("10.00"),
            payment_date=date.today(), payment_method=ip_method,
        )
        assert pay.income is not None
        assert pay.income.payment_method == income_method
        valid = {c for c, _ in Income._meta.get_field("payment_method").choices}
        assert pay.income.payment_method in valid
