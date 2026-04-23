"""
E1.2 Integration tests — cross-module flows.

These tests exercise complete business flows that span multiple models,
signals and views. They verify that the modules work together correctly,
not just in isolation.

Flows covered:
1. Invoice → Payment → Income → Status auto-update
2. Multiple partial payments → Invoice marked PAID
3. ChangeOrder → Invoice link → Cancel preserves CO
4. Client → ClientProjectAccess → Touch-up creation
5. Project deletion cascades to Invoices/COs/ColorSamples
6. ColorApproval.approve() updates state + notifies PMs
7. Estimate → Invoice numbering uses estimate code prefix
8. Organization → Project billing link → block delete
"""
from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


# ---------- Shared fixtures ----------


@pytest.fixture
def admin_user(db):
    return User.objects.create_user(
        username="int_admin", password="x", is_staff=True, is_superuser=True
    )


@pytest.fixture
def pm_user(db):
    """User with project_manager role to receive notifications."""
    from core.models import Profile
    u = User.objects.create_user(username="int_pm", password="x")
    Profile.objects.update_or_create(user=u, defaults={"role": "project_manager"})
    u.refresh_from_db()
    return u


@pytest.fixture
def client_user(db):
    from core.models import Profile
    u = User.objects.create_user(
        username="int_client",
        password="x",
        email="intclient@test.com",
        first_name="Int",
        last_name="Client",
    )
    Profile.objects.update_or_create(user=u, defaults={"role": "client"})
    u.refresh_from_db()
    return u


@pytest.fixture
def project(db):
    from core.models import Project
    return Project.objects.create(name="Integration Project", client="Acme Corp")


# =====================================================
# FLOW 1: Invoice → Payment → Income → Status update
# =====================================================


class TestInvoicePaymentIntegration:
    def test_payment_creates_income_and_updates_invoice(self, project, admin_user):
        """Single payment: amount_paid increments, Income auto-created."""
        from core.models import Income, Invoice, InvoicePayment

        inv = Invoice.objects.create(
            project=project, total_amount=Decimal("1000.00"), status="SENT"
        )
        assert inv.amount_paid == Decimal("0")

        pay = InvoicePayment.objects.create(
            invoice=inv,
            amount=Decimal("400.00"),
            payment_date=date.today(),
            payment_method="CHECK",
            reference="CHK-100",
            recorded_by=admin_user,
        )

        inv.refresh_from_db()
        assert inv.amount_paid == Decimal("400.00")
        # Status moves to PARTIAL
        assert inv.status == "PARTIAL"
        # Income auto-created and linked
        assert pay.income is not None
        assert pay.income.amount == Decimal("400.00")
        assert Income.objects.filter(project=project).count() == 1

    def test_full_payment_marks_invoice_paid(self, project):
        """Payment matching total → status PAID, paid_date set."""
        from core.models import Invoice, InvoicePayment

        inv = Invoice.objects.create(
            project=project, total_amount=Decimal("500.00"), status="SENT"
        )
        InvoicePayment.objects.create(
            invoice=inv, amount=Decimal("500.00"), payment_date=date.today()
        )

        inv.refresh_from_db()
        assert inv.amount_paid == Decimal("500.00")
        assert inv.status == "PAID"
        assert inv.paid_date is not None

    def test_multiple_partial_payments_complete_invoice(self, project):
        """Two partials totaling full amount → PAID."""
        from core.models import Income, Invoice, InvoicePayment

        inv = Invoice.objects.create(
            project=project, total_amount=Decimal("300.00"), status="SENT"
        )
        InvoicePayment.objects.create(
            invoice=inv, amount=Decimal("100.00"), payment_date=date.today()
        )
        inv.refresh_from_db()
        assert inv.status == "PARTIAL"

        InvoicePayment.objects.create(
            invoice=inv, amount=Decimal("200.00"), payment_date=date.today()
        )
        inv.refresh_from_db()
        assert inv.amount_paid == Decimal("300.00")
        assert inv.status == "PAID"
        # Two Income records created (one per payment)
        assert Income.objects.filter(project=project).count() == 2

    def test_overpayment_not_negative_balance(self, project):
        """balance_due property never negative."""
        from core.models import Invoice, InvoicePayment

        inv = Invoice.objects.create(
            project=project, total_amount=Decimal("100.00"), status="SENT"
        )
        InvoicePayment.objects.create(
            invoice=inv, amount=Decimal("150.00"), payment_date=date.today()
        )
        inv.refresh_from_db()
        assert inv.balance_due == Decimal("0")
        assert inv.status == "PAID"


# =====================================================
# FLOW 2: ChangeOrder ↔ Invoice link
# =====================================================


class TestChangeOrderInvoiceIntegration:
    def test_changeorder_linked_to_invoice_via_m2m(self, project):
        """CO can be linked to multiple invoices through M2M."""
        from core.models import ChangeOrder, Invoice

        co = ChangeOrder.objects.create(
            project=project, description="Extra paint", amount=Decimal("200.00"),
            status="approved",
        )
        inv = Invoice.objects.create(
            project=project, total_amount=Decimal("200.00"), status="DRAFT"
        )
        inv.change_orders.add(co)

        assert co.invoices.count() == 1
        assert inv.change_orders.first() == co

    def test_invoice_cancel_does_not_delete_changeorder(self, client, admin_user, project):
        """Cancelling invoice keeps the CO intact."""
        from django.urls import reverse
        from core.models import ChangeOrder, Invoice

        co = ChangeOrder.objects.create(
            project=project, description="Tile work", amount=Decimal("400.00"),
            status="approved",
        )
        inv = Invoice.objects.create(
            project=project, total_amount=Decimal("400.00"), status="SENT"
        )
        inv.change_orders.add(co)

        client.force_login(admin_user)
        client.post(reverse("invoice_cancel", args=[inv.id]))

        inv.refresh_from_db()
        assert inv.status == "CANCELLED"
        # CO still exists
        assert ChangeOrder.objects.filter(pk=co.id).exists()


# =====================================================
# FLOW 3: Client + ClientProjectAccess + Touch-up
# =====================================================


class TestClientPortalTouchUpFlow:
    def test_client_with_access_creates_touchup_via_view(
        self, client, client_user, project
    ):
        """Client granted project access can submit a touch-up."""
        from django.urls import reverse
        from core.models import ClientProjectAccess, TouchUp

        ClientProjectAccess.objects.create(
            user=client_user, project=project, role="client"
        )
        client.force_login(client_user)
        resp = client.post(
            reverse("agregar_tarea", args=[project.id]),
            {"title": "Fix corner", "description": "Small chip in living room"},
        )
        # Redirects on success
        assert resp.status_code == 302
        # Touch-up was created
        assert TouchUp.objects.filter(project=project, title="Fix corner").exists()

    def test_client_without_access_blocked(self, client, client_user, project):
        """Client without ClientProjectAccess cannot submit touch-ups."""
        from django.urls import reverse
        from core.models import TouchUp

        client.force_login(client_user)
        resp = client.post(
            reverse("agregar_tarea", args=[project.id]),
            {"title": "Should fail", "description": "no access"},
        )
        # View returns 403/redirect or just doesn't create
        assert not TouchUp.objects.filter(title="Should fail").exists()


# =====================================================
# FLOW 4: Project cascade delete
# =====================================================


class TestProjectCascadeDelete:
    def test_deleting_project_cascades_invoices_cos_color_samples(self, project):
        """Project.delete() cascades to its child records."""
        from core.models import (
            ChangeOrder,
            ColorSample,
            Invoice,
            InvoicePayment,
        )

        inv = Invoice.objects.create(
            project=project, total_amount=Decimal("100.00"), status="DRAFT"
        )
        co = ChangeOrder.objects.create(
            project=project, description="x", amount=Decimal("50.00")
        )
        cs = ColorSample.objects.create(project=project, name="Sky Blue")
        # Add a payment so cascade includes it too
        pay = InvoicePayment.objects.create(
            invoice=inv, amount=Decimal("100.00"), payment_date=date.today()
        )

        inv_id, co_id, cs_id, pay_id = inv.id, co.id, cs.id, pay.id
        project.delete()

        assert not Invoice.objects.filter(pk=inv_id).exists()
        assert not ChangeOrder.objects.filter(pk=co_id).exists()
        assert not ColorSample.objects.filter(pk=cs_id).exists()
        assert not InvoicePayment.objects.filter(pk=pay_id).exists()


# =====================================================
# FLOW 5: ColorApproval.approve() + Notifications
# =====================================================


class TestColorApprovalNotificationFlow:
    def test_approve_sets_status_and_notifies_pms(self, project, admin_user, pm_user):
        """approve() updates state, sets approver/signed_at, sends Notification to PMs."""
        from core.models import ColorApproval, Notification

        approval = ColorApproval.objects.create(
            project=project, color_name="Coastal Fog", status="PENDING"
        )

        before_count = Notification.objects.filter(user=pm_user).count()
        approval.approve(approver=admin_user)
        approval.refresh_from_db()

        assert approval.status == "APPROVED"
        assert approval.approved_by == admin_user
        assert approval.signed_at is not None
        # PM notified
        after_count = Notification.objects.filter(user=pm_user).count()
        assert after_count == before_count + 1
        notif = Notification.objects.filter(user=pm_user).latest("id")
        assert notif.notification_type == "color_approved"
        assert "Coastal Fog" in notif.message

    def test_reject_appends_reason_to_notes(self, project, admin_user):
        from core.models import ColorApproval

        approval = ColorApproval.objects.create(
            project=project, color_name="Tomato Red", status="PENDING", notes="initial"
        )
        approval.reject(approver=admin_user, reason="too saturated")
        approval.refresh_from_db()

        assert approval.status == "REJECTED"
        assert approval.approved_by == admin_user
        assert "too saturated" in approval.notes
        assert "initial" in approval.notes


# =====================================================
# FLOW 6: Estimate-prefixed Invoice numbering
# =====================================================


class TestInvoiceNumberingFromEstimate:
    def test_invoice_uses_estimate_code_when_approved_estimate_exists(self, project):
        """Approved Estimate → next Invoice number uses its code prefix."""
        from core.models import Estimate, Invoice

        Estimate.objects.create(
            project=project, code="EST-INTG", version=1, approved=True
        )
        inv = Invoice.objects.create(project=project, total_amount=Decimal("100"))
        assert inv.invoice_number.startswith("EST-INTG-INV")

    def test_invoice_falls_back_to_client_initials_without_estimate(self, project):
        from core.models import Invoice

        inv = Invoice.objects.create(project=project, total_amount=Decimal("100"))
        # client="Acme Corp" → initials AC
        assert inv.invoice_number.startswith("AC-")


# =====================================================
# FLOW 7: Organization billing link blocks delete
# =====================================================


class TestOrganizationProjectLinkFlow:
    def test_org_with_linked_project_cannot_be_deleted_via_view(
        self, client, admin_user, project
    ):
        from django.urls import reverse
        from core.models import ClientOrganization

        org = ClientOrganization.objects.create(
            name="Linked Co", billing_address="addr", billing_email="b@x.com"
        )
        project.billing_organization = org
        project.save()

        client.force_login(admin_user)
        resp = client.post(
            reverse("organization_delete", args=[org.id]),
            {"action": "delete"},
        )
        assert resp.status_code == 302
        # Org still exists due to dependency check
        assert ClientOrganization.objects.filter(pk=org.id).exists()

    def test_org_unlinked_project_can_be_deleted(self, client, admin_user):
        from django.urls import reverse
        from core.models import ClientOrganization

        org = ClientOrganization.objects.create(
            name="Free Co", billing_address="a", billing_email="f@x.com"
        )
        client.force_login(admin_user)
        resp = client.post(
            reverse("organization_delete", args=[org.id]),
            {"action": "delete"},
        )
        assert resp.status_code == 302
        assert not ClientOrganization.objects.filter(pk=org.id).exists()


# =====================================================
# FLOW 8: Overdue auto-detection on payment update
# =====================================================


class TestOverdueAutoDetection:
    def test_overdue_invoice_marked_on_status_update(self, project):
        """Past due_date with balance > 0 → status auto-marks OVERDUE."""
        from core.models import Invoice, InvoicePayment

        inv = Invoice.objects.create(
            project=project,
            total_amount=Decimal("500"),
            status="SENT",
            due_date=date.today() - timedelta(days=10),
        )
        # Trigger update_status via a tiny payment
        InvoicePayment.objects.create(
            invoice=inv, amount=Decimal("1.00"), payment_date=date.today()
        )
        inv.refresh_from_db()
        assert inv.status == "OVERDUE"
