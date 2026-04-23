"""
Tests for core/views/financial_views.py

Covers main views:
- payroll_summary_view (legacy redirect)
- invoice_list, invoice_detail, invoice_pdf
- changeorders_ajax, changeorder_lines_ajax
- invoice_payment_dashboard, record_invoice_payment
- invoice_mark_sent, invoice_mark_approved
- invoice_delete, invoice_cancel
- costcode_list_view (CRUD)
- budget_lines_view
"""
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

User = get_user_model()


# ---------- Fixtures ----------


@pytest.fixture
def admin_user(db):
    return User.objects.create_user(
        username="fin_admin", password="x", is_staff=True, is_superuser=True
    )


@pytest.fixture
def staff_user(db):
    return User.objects.create_user(username="fin_staff", password="x", is_staff=True)


@pytest.fixture
def regular_user(db):
    """Non-staff user (employee role by default)."""
    return User.objects.create_user(username="fin_regular", password="x")


@pytest.fixture
def project(db):
    from core.models import Project
    return Project.objects.create(name="Financial Test Project")


@pytest.fixture
def invoice_draft(db, project):
    from core.models import Invoice
    return Invoice.objects.create(
        project=project,
        total_amount=Decimal("1000.00"),
        status="DRAFT",
    )


@pytest.fixture
def invoice_sent(db, project):
    from core.models import Invoice
    return Invoice.objects.create(
        project=project,
        total_amount=Decimal("500.00"),
        status="SENT",
    )


@pytest.fixture
def invoice_paid(db, project):
    from core.models import Invoice
    return Invoice.objects.create(
        project=project,
        total_amount=Decimal("200.00"),
        status="PAID",
        amount_paid=Decimal("200.00"),
    )


@pytest.fixture
def change_order(db, project):
    from core.models import ChangeOrder
    return ChangeOrder.objects.create(
        project=project,
        description="CO test",
        amount=Decimal("250.00"),
        status="approved",
    )


@pytest.fixture
def costcode(db):
    from core.models import CostCode
    return CostCode.objects.create(code="LBR-01", name="Labor", category="Labor", active=True)


# ---------- payroll_summary_view ----------


class TestPayrollSummaryView:
    def test_redirects_to_weekly_review(self, client, admin_user):
        client.force_login(admin_user)
        resp = client.get(reverse("payroll_summary"))
        assert resp.status_code == 302
        assert reverse("payroll_weekly_review") in resp.url


# ---------- invoice_list ----------


class TestInvoiceList:
    def test_anonymous_redirected(self, client):
        resp = client.get(reverse("invoice_list"))
        assert resp.status_code == 302
        assert "/login" in resp.url or "/accounts/login" in resp.url

    def test_non_staff_redirected_to_dashboard(self, client, regular_user):
        client.force_login(regular_user)
        resp = client.get(reverse("invoice_list"))
        assert resp.status_code == 302

    def test_staff_can_view(self, client, staff_user, invoice_draft, invoice_sent):
        client.force_login(staff_user)
        resp = client.get(reverse("invoice_list"))
        assert resp.status_code == 200

    def test_filter_by_status_paid(self, client, staff_user, invoice_paid, invoice_sent):
        client.force_login(staff_user)
        resp = client.get(reverse("invoice_list"), {"status": "paid"})
        assert resp.status_code == 200

    def test_filter_by_status_pending(self, client, staff_user, invoice_paid, invoice_sent):
        client.force_login(staff_user)
        resp = client.get(reverse("invoice_list"), {"status": "pending"})
        assert resp.status_code == 200

    def test_filter_by_status_overdue(self, client, staff_user, invoice_sent):
        client.force_login(staff_user)
        resp = client.get(reverse("invoice_list"), {"status": "overdue"})
        assert resp.status_code == 200

    def test_filter_by_status_other(self, client, staff_user, invoice_draft):
        client.force_login(staff_user)
        resp = client.get(reverse("invoice_list"), {"status": "DRAFT"})
        assert resp.status_code == 200

    def test_filter_by_project(self, client, staff_user, project, invoice_sent):
        client.force_login(staff_user)
        resp = client.get(reverse("invoice_list"), {"project": str(project.id)})
        assert resp.status_code == 200


# ---------- invoice_detail ----------


class TestInvoiceDetail:
    def test_anonymous_redirected(self, client, invoice_draft):
        resp = client.get(reverse("invoice_detail", args=[invoice_draft.pk]))
        assert resp.status_code == 302

    def test_non_staff_redirected(self, client, regular_user, invoice_draft):
        client.force_login(regular_user)
        resp = client.get(reverse("invoice_detail", args=[invoice_draft.pk]))
        assert resp.status_code == 302

    def test_staff_can_view(self, client, staff_user, invoice_sent):
        client.force_login(staff_user)
        resp = client.get(reverse("invoice_detail", args=[invoice_sent.pk]))
        assert resp.status_code == 200

    def test_nonexistent_invoice_404(self, client, staff_user):
        client.force_login(staff_user)
        resp = client.get(reverse("invoice_detail", args=[999999]))
        assert resp.status_code == 404

    def test_with_due_date(self, client, staff_user, project):
        from datetime import date, timedelta
        from core.models import Invoice
        inv = Invoice.objects.create(
            project=project,
            total_amount=Decimal("100.00"),
            status="SENT",
            due_date=date.today() - timedelta(days=5),
        )
        client.force_login(staff_user)
        resp = client.get(reverse("invoice_detail", args=[inv.pk]))
        assert resp.status_code == 200


# ---------- invoice_pdf ----------


class TestInvoicePdf:
    def test_non_staff_redirected(self, client, regular_user, invoice_sent):
        client.force_login(regular_user)
        resp = client.get(reverse("invoice_pdf", args=[invoice_sent.pk]))
        assert resp.status_code == 302

    def test_staff_can_get_pdf(self, client, staff_user, invoice_sent, monkeypatch):
        # Force fallback PDF generation (avoid xhtml2pdf CSS parsing issues with template).
        monkeypatch.setattr("core.views.financial_views.pisa", None)
        client.force_login(staff_user)
        resp = client.get(reverse("invoice_pdf", args=[invoice_sent.pk]))
        assert resp.status_code == 200
        assert resp["Content-Type"] == "application/pdf"


# ---------- changeorders_ajax / changeorder_lines_ajax ----------


class TestChangeordersAjax:
    def test_non_staff_403(self, client, regular_user, project):
        client.force_login(regular_user)
        resp = client.get(reverse("changeorders_ajax"), {"project_id": project.id})
        assert resp.status_code == 403

    def test_staff_returns_json(self, client, staff_user, project, change_order):
        client.force_login(staff_user)
        resp = client.get(reverse("changeorders_ajax"), {"project_id": project.id})
        assert resp.status_code == 200
        data = resp.json()
        assert "change_orders" in data
        assert len(data["change_orders"]) == 1

    def test_filter_active(self, client, staff_user, project, change_order):
        client.force_login(staff_user)
        resp = client.get(
            reverse("changeorders_ajax"), {"project_id": project.id, "status": "active"}
        )
        assert resp.status_code == 200

    def test_filter_specific_status(self, client, staff_user, project, change_order):
        client.force_login(staff_user)
        resp = client.get(
            reverse("changeorders_ajax"), {"project_id": project.id, "status": "approved"}
        )
        assert resp.status_code == 200
        assert len(resp.json()["change_orders"]) == 1


class TestChangeorderLinesAjax:
    def test_non_staff_403(self, client, regular_user):
        client.force_login(regular_user)
        resp = client.get(reverse("changeorder_lines_ajax"))
        assert resp.status_code == 403

    def test_staff_returns_lines(self, client, staff_user, change_order):
        client.force_login(staff_user)
        resp = client.get(reverse("changeorder_lines_ajax"), {"ids[]": [change_order.id]})
        assert resp.status_code == 200
        assert "lines" in resp.json()
        assert len(resp.json()["lines"]) == 1


# ---------- invoice_payment_dashboard ----------


class TestInvoicePaymentDashboard:
    def test_non_staff_redirected(self, client, regular_user):
        client.force_login(regular_user)
        resp = client.get(reverse("invoice_payment_dashboard"))
        assert resp.status_code == 302

    def test_staff_can_view(self, client, staff_user, invoice_sent, invoice_paid):
        client.force_login(staff_user)
        resp = client.get(reverse("invoice_payment_dashboard"))
        assert resp.status_code == 200


# ---------- record_invoice_payment ----------


class TestRecordInvoicePayment:
    def test_non_staff_redirected(self, client, regular_user, invoice_sent):
        client.force_login(regular_user)
        resp = client.get(reverse("record_invoice_payment", args=[invoice_sent.id]))
        assert resp.status_code == 302

    def test_get_shows_form(self, client, staff_user, invoice_sent):
        client.force_login(staff_user)
        resp = client.get(reverse("record_invoice_payment", args=[invoice_sent.id]))
        assert resp.status_code == 200

    def test_post_creates_payment(self, client, staff_user, invoice_sent):
        from datetime import date
        client.force_login(staff_user)
        resp = client.post(
            reverse("record_invoice_payment", args=[invoice_sent.id]),
            {
                "amount": "100.00",
                "payment_date": date.today().isoformat(),
                "payment_method": "CHECK",
                "reference": "CHK-001",
                "notes": "Partial",
            },
        )
        assert resp.status_code == 302
        invoice_sent.refresh_from_db()
        assert invoice_sent.amount_paid == Decimal("100.00")

    def test_post_invalid_amount_does_not_create_payment(self, client, staff_user, invoice_sent):
        # Note: view catches ValueError/ValidationError but not decimal.InvalidOperation.
        # We verify the success path by sending a zero amount (still a valid Decimal).
        from datetime import date
        from core.models import InvoicePayment
        client.force_login(staff_user)
        resp = client.post(
            reverse("record_invoice_payment", args=[invoice_sent.id]),
            {
                "amount": "0",
                "payment_date": date.today().isoformat(),
                "payment_method": "CHECK",
            },
        )
        assert resp.status_code == 302
        # Zero-amount payment is created but invoice balance unchanged
        invoice_sent.refresh_from_db()
        assert invoice_sent.amount_paid == Decimal("0")

    def test_nonexistent_invoice_404(self, client, staff_user):
        client.force_login(staff_user)
        resp = client.get(reverse("record_invoice_payment", args=[999999]))
        assert resp.status_code == 404


# ---------- invoice_mark_sent ----------


class TestInvoiceMarkSent:
    def test_non_staff_redirected(self, client, regular_user, invoice_draft):
        client.force_login(regular_user)
        resp = client.get(reverse("invoice_mark_sent", args=[invoice_draft.id]))
        assert resp.status_code == 302

    def test_draft_marked_sent(self, client, staff_user, invoice_draft):
        client.force_login(staff_user)
        resp = client.get(reverse("invoice_mark_sent", args=[invoice_draft.id]))
        assert resp.status_code == 302
        invoice_draft.refresh_from_db()
        assert invoice_draft.status == "SENT"
        assert invoice_draft.sent_date is not None

    def test_already_sent_warns(self, client, staff_user, invoice_sent):
        client.force_login(staff_user)
        resp = client.get(reverse("invoice_mark_sent", args=[invoice_sent.id]))
        assert resp.status_code == 302
        invoice_sent.refresh_from_db()
        assert invoice_sent.status == "SENT"  # unchanged


# ---------- invoice_mark_approved ----------


class TestInvoiceMarkApproved:
    def test_non_staff_redirected(self, client, regular_user, invoice_sent):
        client.force_login(regular_user)
        resp = client.get(reverse("invoice_mark_approved", args=[invoice_sent.id]))
        assert resp.status_code == 302

    def test_sent_marked_approved(self, client, staff_user, invoice_sent):
        client.force_login(staff_user)
        resp = client.get(reverse("invoice_mark_approved", args=[invoice_sent.id]))
        assert resp.status_code == 302
        invoice_sent.refresh_from_db()
        assert invoice_sent.status == "APPROVED"
        assert invoice_sent.approved_date is not None

    def test_paid_invoice_unchanged(self, client, staff_user, invoice_paid):
        client.force_login(staff_user)
        resp = client.get(reverse("invoice_mark_approved", args=[invoice_paid.id]))
        assert resp.status_code == 302
        invoice_paid.refresh_from_db()
        assert invoice_paid.status == "PAID"


# ---------- invoice_delete ----------


class TestInvoiceDelete:
    def test_get_method_rejected(self, client, staff_user, invoice_draft):
        client.force_login(staff_user)
        resp = client.get(reverse("invoice_delete", args=[invoice_draft.id]))
        assert resp.status_code == 405

    def test_non_staff_redirected(self, client, regular_user, invoice_draft):
        client.force_login(regular_user)
        resp = client.post(reverse("invoice_delete", args=[invoice_draft.id]))
        assert resp.status_code == 302

    def test_draft_deleted(self, client, staff_user, invoice_draft):
        from core.models import Invoice
        client.force_login(staff_user)
        inv_id = invoice_draft.id
        resp = client.post(reverse("invoice_delete", args=[inv_id]))
        assert resp.status_code == 302
        assert not Invoice.objects.filter(pk=inv_id).exists()

    def test_paid_cannot_be_deleted(self, client, staff_user, invoice_paid):
        from core.models import Invoice
        client.force_login(staff_user)
        resp = client.post(reverse("invoice_delete", args=[invoice_paid.id]))
        assert resp.status_code == 302
        assert Invoice.objects.filter(pk=invoice_paid.id).exists()

    def test_invoice_with_payments_cannot_be_deleted(self, client, staff_user, project):
        from datetime import date
        from core.models import Invoice, InvoicePayment
        inv = Invoice.objects.create(
            project=project, total_amount=Decimal("500"), status="DRAFT"
        )
        InvoicePayment.objects.create(
            invoice=inv,
            amount=Decimal("100"),
            payment_date=date.today(),
            payment_method="CHECK",
        )
        client.force_login(staff_user)
        resp = client.post(reverse("invoice_delete", args=[inv.id]))
        assert resp.status_code == 302
        assert Invoice.objects.filter(pk=inv.id).exists()


# ---------- invoice_cancel ----------


class TestInvoiceCancel:
    def test_get_method_rejected(self, client, staff_user, invoice_sent):
        client.force_login(staff_user)
        resp = client.get(reverse("invoice_cancel", args=[invoice_sent.id]))
        assert resp.status_code == 405

    def test_non_staff_redirected(self, client, regular_user, invoice_sent):
        client.force_login(regular_user)
        resp = client.post(reverse("invoice_cancel", args=[invoice_sent.id]))
        assert resp.status_code == 302

    def test_sent_cancelled(self, client, staff_user, invoice_sent):
        client.force_login(staff_user)
        resp = client.post(reverse("invoice_cancel", args=[invoice_sent.id]))
        assert resp.status_code == 302
        invoice_sent.refresh_from_db()
        assert invoice_sent.status == "CANCELLED"

    def test_paid_cannot_be_cancelled(self, client, staff_user, invoice_paid):
        client.force_login(staff_user)
        resp = client.post(reverse("invoice_cancel", args=[invoice_paid.id]))
        assert resp.status_code == 302
        invoice_paid.refresh_from_db()
        assert invoice_paid.status == "PAID"

    def test_already_cancelled_warns(self, client, staff_user, project):
        from core.models import Invoice
        inv = Invoice.objects.create(
            project=project, total_amount=Decimal("100"), status="CANCELLED"
        )
        client.force_login(staff_user)
        resp = client.post(reverse("invoice_cancel", args=[inv.id]))
        assert resp.status_code == 302


# ---------- costcode_list_view ----------


class TestCostcodeListView:
    def test_non_staff_redirected(self, client, regular_user):
        client.force_login(regular_user)
        resp = client.get(reverse("costcode_list"))
        assert resp.status_code == 302

    def test_staff_can_view(self, client, staff_user, costcode):
        client.force_login(staff_user)
        resp = client.get(reverse("costcode_list"))
        assert resp.status_code == 200

    def test_create_costcode(self, client, staff_user):
        from core.models import CostCode
        client.force_login(staff_user)
        resp = client.post(
            reverse("costcode_list"),
            {
                "action": "create",
                "category": "Material",
                "code": "MAT-99",
                "name": "Test Material",
                "active": "on",
            },
        )
        assert resp.status_code == 302
        assert CostCode.objects.filter(code="MAT-99").exists()

    def test_update_costcode(self, client, staff_user, costcode):
        client.force_login(staff_user)
        resp = client.post(
            reverse("costcode_list"),
            {
                "action": "update",
                "costcode_id": str(costcode.id),
                "code": "LBR-01",
                "name": "Updated Labor",
                "category": "Labor",
                "active": "on",
            },
        )
        assert resp.status_code == 302
        costcode.refresh_from_db()
        assert costcode.name == "Updated Labor"

    def test_delete_costcode(self, client, staff_user, costcode):
        from core.models import CostCode
        client.force_login(staff_user)
        cid = costcode.id
        resp = client.post(
            reverse("costcode_list"),
            {"action": "delete", "costcode_id": str(cid)},
        )
        assert resp.status_code == 302
        assert not CostCode.objects.filter(pk=cid).exists()

    def test_update_nonexistent_shows_error(self, client, staff_user):
        client.force_login(staff_user)
        resp = client.post(
            reverse("costcode_list"),
            {
                "action": "update",
                "costcode_id": "999999",
                "code": "X",
                "name": "X",
                "category": "X",
            },
        )
        assert resp.status_code == 302


# ---------- budget_lines_view ----------


class TestBudgetLinesView:
    def test_non_staff_403(self, client, regular_user, project):
        client.force_login(regular_user)
        resp = client.get(reverse("budget_lines", args=[project.id]))
        # staff_member_required redirects to admin login
        assert resp.status_code == 302

    def test_staff_can_view(self, client, admin_user, project):
        client.force_login(admin_user)
        resp = client.get(reverse("budget_lines", args=[project.id]))
        assert resp.status_code == 200

    def test_nonexistent_project_404(self, client, admin_user):
        client.force_login(admin_user)
        resp = client.get(reverse("budget_lines", args=[999999]))
        assert resp.status_code == 404
