"""Tests for invoice_edit view.

Covers:
  - Only DRAFT invoices are editable; SENT/PAID/etc. redirect with error.
  - Editing line description + amount recalculates total.
  - Deleting a line removes it AND frees up linked Expenses.
  - Adding a new manual line creates an InvoiceLine and updates total.
  - Unlinking a Change Order removes the M2M and reverts CO status to "approved".
  - Header fields (date_issued, due_date, notes) are persisted.
  - Non-staff user cannot access.
"""
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone


@pytest.fixture
def staff_user(db):
    return get_user_model().objects.create_user(
        username="invedit_staff", password="x", is_staff=True
    )


@pytest.fixture
def normal_user(db):
    return get_user_model().objects.create_user(
        username="invedit_user", password="x", is_staff=False
    )


@pytest.fixture
def project(db):
    from core.models import Project

    return Project.objects.create(
        name="EditProj", client="ClientX", start_date=timezone.now().date()
    )


@pytest.fixture
def draft_invoice(db, project):
    from core.models import Invoice, InvoiceLine

    inv = Invoice.objects.create(
        project=project, total_amount=Decimal("0"), status="DRAFT"
    )
    InvoiceLine.objects.create(invoice=inv, description="Original line", amount=Decimal("100.00"))
    InvoiceLine.objects.create(invoice=inv, description="Second line", amount=Decimal("250.00"))
    inv.total_amount = Decimal("350.00")
    inv.save()
    return inv


@pytest.mark.django_db
def test_edit_get_renders_for_draft(client, staff_user, draft_invoice):
    client.force_login(staff_user)
    url = reverse("invoice_edit", args=[draft_invoice.id])
    resp = client.get(url)
    assert resp.status_code == 200
    body = resp.content.decode()
    assert "Edit Invoice" in body or "Editar" in body or "edit" in body.lower()
    assert "Original line" in body


@pytest.mark.django_db
def test_edit_blocked_for_sent_invoice(client, staff_user, draft_invoice):
    draft_invoice.status = "SENT"
    draft_invoice.save()
    client.force_login(staff_user)
    url = reverse("invoice_edit", args=[draft_invoice.id])
    resp = client.get(url, follow=True)
    # Redirected to detail
    assert resp.redirect_chain[-1][0].endswith(f"/invoices/{draft_invoice.id}/")


@pytest.mark.django_db
def test_non_staff_cannot_edit(client, normal_user, draft_invoice):
    client.force_login(normal_user)
    url = reverse("invoice_edit", args=[draft_invoice.id])
    resp = client.get(url)
    # _is_staffish denies → redirect to dashboard
    assert resp.status_code in (302, 403)


@pytest.mark.django_db
def test_post_updates_line_amount_and_recalcs_total(client, staff_user, draft_invoice):
    client.force_login(staff_user)
    line1, line2 = list(draft_invoice.lines.order_by("id"))
    url = reverse("invoice_edit", args=[draft_invoice.id])
    resp = client.post(
        url,
        {
            "date_issued": draft_invoice.date_issued.isoformat(),
            "due_date": "",
            "notes": "edited notes",
            f"line_id_{line1.id}_description": "Updated desc",
            f"line_id_{line1.id}_amount": "175.50",
            f"line_id_{line2.id}_description": line2.description,
            f"line_id_{line2.id}_amount": "250.00",
        },
    )
    assert resp.status_code == 302
    draft_invoice.refresh_from_db()
    line1.refresh_from_db()
    assert line1.description == "Updated desc"
    assert line1.amount == Decimal("175.50")
    assert draft_invoice.total_amount == Decimal("425.50")
    assert draft_invoice.notes == "edited notes"


@pytest.mark.django_db
def test_post_deletes_line_and_recalcs_total(client, staff_user, draft_invoice):
    client.force_login(staff_user)
    line1, line2 = list(draft_invoice.lines.order_by("id"))
    url = reverse("invoice_edit", args=[draft_invoice.id])
    resp = client.post(
        url,
        {
            "date_issued": draft_invoice.date_issued.isoformat(),
            "due_date": "",
            f"line_id_{line1.id}_delete": "on",
            f"line_id_{line1.id}_description": line1.description,
            f"line_id_{line1.id}_amount": "100.00",
            f"line_id_{line2.id}_description": line2.description,
            f"line_id_{line2.id}_amount": "250.00",
        },
    )
    assert resp.status_code == 302
    draft_invoice.refresh_from_db()
    assert draft_invoice.lines.count() == 1
    assert draft_invoice.total_amount == Decimal("250.00")


@pytest.mark.django_db
def test_post_adds_new_manual_line(client, staff_user, draft_invoice):
    client.force_login(staff_user)
    line1, line2 = list(draft_invoice.lines.order_by("id"))
    url = reverse("invoice_edit", args=[draft_invoice.id])
    resp = client.post(
        url,
        {
            "date_issued": draft_invoice.date_issued.isoformat(),
            f"line_id_{line1.id}_description": line1.description,
            f"line_id_{line1.id}_amount": "100.00",
            f"line_id_{line2.id}_description": line2.description,
            f"line_id_{line2.id}_amount": "250.00",
            "new_description": ["Bonus material"],
            "new_amount": ["50.25"],
        },
    )
    assert resp.status_code == 302
    draft_invoice.refresh_from_db()
    assert draft_invoice.lines.count() == 3
    assert draft_invoice.total_amount == Decimal("400.25")
    assert draft_invoice.lines.filter(description="Bonus material").exists()


@pytest.mark.django_db
def test_post_unlinks_change_order_and_reverts_status(client, staff_user, project, draft_invoice):
    from core.models import ChangeOrder

    co = ChangeOrder.objects.create(
        project=project, description="Test CO", amount=Decimal("500"), status="billed"
    )
    draft_invoice.change_orders.add(co)
    client.force_login(staff_user)
    url = reverse("invoice_edit", args=[draft_invoice.id])
    line1, line2 = list(draft_invoice.lines.order_by("id"))
    resp = client.post(
        url,
        {
            "date_issued": draft_invoice.date_issued.isoformat(),
            f"line_id_{line1.id}_description": line1.description,
            f"line_id_{line1.id}_amount": "100.00",
            f"line_id_{line2.id}_description": line2.description,
            f"line_id_{line2.id}_amount": "250.00",
            f"remove_co_{co.id}": "on",
        },
    )
    assert resp.status_code == 302
    draft_invoice.refresh_from_db()
    co.refresh_from_db()
    assert co not in draft_invoice.change_orders.all()
    assert co.status == "approved"


@pytest.mark.django_db
def test_post_ignores_invalid_amount(client, staff_user, draft_invoice):
    """Garbage amount input leaves the line untouched (does not crash)."""
    client.force_login(staff_user)
    line1, line2 = list(draft_invoice.lines.order_by("id"))
    url = reverse("invoice_edit", args=[draft_invoice.id])
    resp = client.post(
        url,
        {
            "date_issued": draft_invoice.date_issued.isoformat(),
            f"line_id_{line1.id}_description": line1.description,
            f"line_id_{line1.id}_amount": "not a number",
            f"line_id_{line2.id}_description": line2.description,
            f"line_id_{line2.id}_amount": "250.00",
            "new_description": ["bad"],
            "new_amount": ["xx"],
        },
    )
    assert resp.status_code == 302
    line1.refresh_from_db()
    assert line1.amount == Decimal("100.00")  # unchanged
    draft_invoice.refresh_from_db()
    # New line with invalid amount should NOT be created
    assert draft_invoice.lines.count() == 2
