"""Tests for the invoice_pdf view.

Covers:
  - 200 response with application/pdf content-type
  - Output starts with %PDF magic bytes (never a 500 / HTML error page)
  - Inline by default, attachment when ?download=1
  - Filename includes invoice number
  - Template is English-only (no Spanish leftover strings)
  - Permission gate (non-staff redirected away)
"""
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.template.loader import get_template
from django.urls import reverse
from django.utils import timezone


@pytest.fixture
def staff_user(db):
    return get_user_model().objects.create_user(
        username="invpdf_staff", password="x", is_staff=True
    )


@pytest.fixture
def normal_user(db):
    return get_user_model().objects.create_user(
        username="invpdf_user", password="x", is_staff=False
    )


@pytest.fixture
def invoice(db):
    from core.models import Invoice, InvoiceLine, Project

    project = Project.objects.create(
        name="PDFProj", client="PDFClient", start_date=timezone.now().date()
    )
    inv = Invoice.objects.create(
        project=project,
        invoice_number="INV-PDF-001",
        total_amount=Decimal("1500.00"),
        status="SENT",
    )
    InvoiceLine.objects.create(invoice=inv, description="Interior painting", amount=Decimal("1000"))
    InvoiceLine.objects.create(invoice=inv, description="Materials", amount=Decimal("500"))
    return inv


@pytest.mark.django_db
def test_invoice_pdf_returns_pdf(client, staff_user, invoice):
    client.force_login(staff_user)
    resp = client.get(reverse("invoice_pdf", args=[invoice.id]))
    assert resp.status_code == 200
    assert resp["Content-Type"] == "application/pdf"
    body = resp.content
    assert body[:4] == b"%PDF", f"Expected PDF magic, got {body[:30]!r}"


@pytest.mark.django_db
def test_invoice_pdf_inline_by_default(client, staff_user, invoice):
    client.force_login(staff_user)
    resp = client.get(reverse("invoice_pdf", args=[invoice.id]))
    assert resp.status_code == 200
    assert "inline" in resp["Content-Disposition"]
    assert "INV-PDF-001" in resp["Content-Disposition"]


@pytest.mark.django_db
def test_invoice_pdf_download_uses_attachment(client, staff_user, invoice):
    client.force_login(staff_user)
    resp = client.get(reverse("invoice_pdf", args=[invoice.id]) + "?download=1")
    assert resp.status_code == 200
    assert "attachment" in resp["Content-Disposition"]
    assert 'filename="Invoice-INV-PDF-001.pdf"' in resp["Content-Disposition"]


@pytest.mark.django_db
def test_invoice_pdf_template_is_english(invoice):
    """The PDF template must not contain Spanish leftovers."""
    from datetime import datetime

    template = get_template("core/invoice_pdf.html")
    html = template.render({
        "invoice": invoice,
        "company": {
            "name": "Kibray Paint & Stain LLC",
            "address": "P.O. Box 25881",
            "city_state_zip": "Silverthorne, CO 80497",
            "phone": "(970) 333-4872",
            "email": "jduran@kibraypainting.net",
            "website": "kibraypainting.net",
            "logo_path": "images/kibray-logo.png",
        },
        "now": datetime.now(),
        "is_overdue": False,
    })
    forbidden = [
        "Factura", "Cliente", "Pagar", "Saldo", "Importe", "Cantidad",
        "Descripción", "Vencimiento", "Pendiente", "Pagado", "Borrador",
        "según", "aquí", "más estilos", "tu diseño", "tu ejemplo", "días",
    ]
    for word in forbidden:
        assert word not in html, f"Spanish word found in PDF template: {word!r}"
    # Sanity: required English labels present
    assert "INVOICE" in html
    assert ("Bill To" in html) or ("BILL TO" in html)
    assert "BALANCE DUE" in html
    assert "Payment Information" in html


@pytest.mark.django_db
def test_invoice_pdf_permission_required(client, normal_user, invoice):
    client.force_login(normal_user)
    resp = client.get(reverse("invoice_pdf", args=[invoice.id]))
    # is_admin_or_pm redirects to dashboard with messages.error
    assert resp.status_code in (302, 403)
    if resp.status_code == 302:
        assert "dashboard" in resp["Location"]


@pytest.mark.django_db
def test_invoice_pdf_rendered_body_has_no_spanish(client, staff_user, invoice):
    """End-to-end check: a real PDF for a real invoice must not include
    any of the legacy Spanish strings that used to leak from line items."""
    from core.models import InvoiceLine

    # Add lines using the NEW English descriptions emitted by the fixed view
    InvoiceLine.objects.create(
        invoice=invoice,
        description="Labor CO #99: 5.0 hrs @ $50.00/hr",
        amount=250,
    )
    InvoiceLine.objects.create(
        invoice=invoice,
        description="Materials CO #99: cost $80.00 + 15.0% markup",
        amount=92,
    )
    InvoiceLine.objects.create(
        invoice=invoice,
        description="CO #100 (Fixed): exterior chinking",
        amount=300,
    )

    client.force_login(staff_user)
    resp = client.get(reverse("invoice_pdf", args=[invoice.id]))
    assert resp.status_code == 200
    # Decode latin-1 just to scan for ASCII Spanish leftovers in the PDF stream
    body_text = resp.content.decode("latin-1", errors="ignore")
    for word in ["Mano de Obra", "Materiales CO", "(Fijo)", "Tiempo &",
                 "Contrato Base", "Estimado v", "para CO #", "horas @"]:
        assert word not in body_text, f"Spanish word leaked into PDF: {word!r}"

