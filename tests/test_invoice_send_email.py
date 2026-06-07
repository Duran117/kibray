"""
Tests for the "Email Invoice with PDF attached" feature.

Covers core/views/financial_views.py::invoice_send_email and the
KibrayEmailService attachment/cc plumbing.
"""
from decimal import Decimal

import pytest
from django.core import mail
from django.urls import reverse

from core.forms import InvoiceEmailForm
from core.services.email_service import KibrayEmailService

pytestmark = pytest.mark.django_db


# ---------- Fixtures ----------


@pytest.fixture
def admin_user(django_user_model):
    return django_user_model.objects.create_user(
        username="inv_admin", password="x", is_staff=True, is_superuser=True
    )


@pytest.fixture
def regular_user(django_user_model):
    return django_user_model.objects.create_user(username="inv_regular", password="x")


@pytest.fixture
def internal_pm_user(django_user_model):
    """Kibray-internal Project Manager (role=project_manager, NOT staff).

    Per policy, internal PMs must NOT email clients, so this user should be
    denied access to the invoice-send view.
    """
    from core.models import Profile

    u = django_user_model.objects.create_user(username="inv_internal_pm", password="x")
    Profile.objects.update_or_create(user=u, defaults={"role": "project_manager"})
    return u


@pytest.fixture
def project(db):
    from core.models import Project
    return Project.objects.create(name="Invoice Email Project")


@pytest.fixture
def invoice_draft(db, project):
    from core.models import Invoice
    return Invoice.objects.create(
        project=project, total_amount=Decimal("1234.56"), status="DRAFT"
    )


# ---------- Access control ----------


def test_send_requires_staff(client, regular_user, invoice_draft):
    client.force_login(regular_user)
    resp = client.get(reverse("invoice_send_email", args=[invoice_draft.pk]))
    # Non-staff are redirected to dashboard (access denied).
    assert resp.status_code == 302
    assert "dashboard" in resp.url


def test_internal_pm_cannot_send(client, internal_pm_user, invoice_draft):
    """Internal Kibray PMs are blocked — they must not contact clients."""
    client.force_login(internal_pm_user)
    resp = client.get(reverse("invoice_send_email", args=[invoice_draft.pk]))
    assert resp.status_code == 302
    assert "dashboard" in resp.url


# ---------- GET: form renders pre-filled ----------


def test_get_renders_form(client, admin_user, invoice_draft):
    client.force_login(admin_user)
    resp = client.get(reverse("invoice_send_email", args=[invoice_draft.pk]) + "?partial=1")
    assert resp.status_code == 200
    html = resp.content.decode()
    # The attached-PDF banner shows the filename.
    assert f"Invoice-{invoice_draft.invoice_number}.pdf" in html
    # The To / CC / Subject / Message fields are present.
    assert 'name="recipient"' in html
    assert 'name="cc"' in html
    assert 'name="subject"' in html
    assert 'name="message"' in html


def test_get_prefills_to_office_and_cc_client_pm(client, admin_user, django_user_model):
    """To = client's invoices/office mailbox; CC = client-side project manager.

    The billing organization's ``billing_email`` is the office/invoices inbox
    (the primary recipient). The project_lead is the client PM we work for and
    is pre-filled into CC so the admin doesn't type it by hand.
    """
    from core.models import ClientContact, ClientOrganization, Invoice, Project

    org = ClientOrganization.objects.create(
        name="Acme Corp", billing_email="invoices@acme.com"
    )
    pm_client = django_user_model.objects.create_user(
        username="acme_pm", password="x", email="pm@acme.com", first_name="Pat", last_name="Lee"
    )
    contact = ClientContact.objects.create(
        user=pm_client, organization=org, role="project_lead"
    )
    project = Project.objects.create(
        name="Acme Tower", billing_organization=org, project_lead=contact
    )
    invoice = Invoice.objects.create(
        project=project, total_amount=Decimal("500.00"), status="DRAFT"
    )

    client.force_login(admin_user)
    resp = client.get(reverse("invoice_send_email", args=[invoice.pk]) + "?partial=1")
    assert resp.status_code == 200
    html = resp.content.decode()
    # To pre-filled with the office/invoices email.
    assert 'value="invoices@acme.com"' in html
    # CC pre-filled with the client-side PM email.
    assert "pm@acme.com" in html


# ---------- POST: sends branded email with PDF attached + CC ----------


def test_post_sends_email_with_pdf_and_cc(client, admin_user, invoice_draft, settings):
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    settings.DEFAULT_FROM_EMAIL = "noreply@kibraypainting.us"
    settings.OFFICE_EMAIL = "office@kibraypainting.net"
    client.force_login(admin_user)
    mail.outbox = []

    resp = client.post(
        reverse("invoice_send_email", args=[invoice_draft.pk]),
        data={
            "subject": "Invoice #X - Kibray",
            "recipient": "client@example.com",
            "cc": "boss@example.com, accounting@example.com",
            "message": "Hello,\n\nHere is your invoice.\n\nThanks.",
        },
    )
    # Redirects back to the invoice detail on success.
    assert resp.status_code == 302
    assert reverse("invoice_detail", args=[invoice_draft.pk]) in resp.url

    assert len(mail.outbox) == 1
    msg = mail.outbox[0]
    assert msg.to == ["client@example.com"]
    assert msg.cc == ["boss@example.com", "accounting@example.com"]
    # Office is BCC'd automatically (hidden from the client).
    assert msg.bcc == ["office@kibraypainting.net"]
    assert msg.from_email == "noreply@kibraypainting.us"

    # PDF attachment present.
    assert len(msg.attachments) == 1
    filename, content, mimetype = msg.attachments[0]
    assert filename == f"Invoice-{invoice_draft.invoice_number}.pdf"
    assert mimetype == "application/pdf"
    assert content[:4] == b"%PDF"  # real PDF magic bytes

    # Branded HTML body (header banner + corporate signature).
    html_body = msg.alternatives[0][0]
    assert "KIBRAY" in html_body.upper()
    assert "jduran@kibraypainting.net" in html_body

    # DRAFT invoice flips to SENT.
    invoice_draft.refresh_from_db()
    assert invoice_draft.status == "SENT"
    assert invoice_draft.sent_date is not None
    assert invoice_draft.sent_by_id == admin_user.id


# ---------- POST: office is auto-BCC'd / de-duplicated ----------


def test_office_bccd_and_not_duplicated_when_equals_recipient(
    client, admin_user, invoice_draft, settings
):
    """If the client email IS the office email, don't BCC a duplicate copy."""
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    settings.OFFICE_EMAIL = "office@kibraypainting.net"
    client.force_login(admin_user)
    mail.outbox = []

    resp = client.post(
        reverse("invoice_send_email", args=[invoice_draft.pk]),
        data={
            # Recipient == office (case-insensitive) → no duplicate BCC.
            "recipient": "Office@Kibraypainting.net",
            "subject": "Invoice",
            "cc": "",
            "message": "Body",
        },
    )
    assert resp.status_code == 302
    assert len(mail.outbox) == 1
    assert mail.outbox[0].bcc == []


# ---------- POST: invalid CC is rejected (form re-rendered) ----------


def test_post_invalid_cc_rejected(client, admin_user, invoice_draft, settings):
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    client.force_login(admin_user)
    mail.outbox = []

    resp = client.post(
        reverse("invoice_send_email", args=[invoice_draft.pk]),
        data={
            "subject": "Invoice",
            "recipient": "client@example.com",
            "cc": "not-an-email",
            "message": "Body",
        },
    )
    # Form re-rendered (200), no email sent, invoice unchanged.
    assert resp.status_code == 200
    assert len(mail.outbox) == 0
    invoice_draft.refresh_from_db()
    assert invoice_draft.status == "DRAFT"


# ---------- AJAX (modal) submit flow ----------


def test_ajax_post_success_returns_json_redirect(client, admin_user, invoice_draft, settings):
    """AJAX success keeps the user in the modal, returning a JSON redirect."""
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    client.force_login(admin_user)
    mail.outbox = []

    resp = client.post(
        reverse("invoice_send_email", args=[invoice_draft.pk]),
        data={
            "subject": "Invoice",
            "recipient": "client@example.com",
            "cc": "",
            "message": "Body",
        },
        HTTP_X_REQUESTED_WITH="XMLHttpRequest",
    )
    assert resp.status_code == 200
    assert resp["content-type"].startswith("application/json")
    data = resp.json()
    assert data["ok"] is True
    assert reverse("invoice_detail", args=[invoice_draft.pk]) in data["redirect"]
    # Email actually sent and invoice advanced to SENT.
    assert len(mail.outbox) == 1
    invoice_draft.refresh_from_db()
    assert invoice_draft.status == "SENT"


def test_ajax_post_invalid_returns_400_partial(client, admin_user, invoice_draft, settings):
    """AJAX validation error returns a 400 + re-rendered form fragment."""
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    client.force_login(admin_user)
    mail.outbox = []

    resp = client.post(
        reverse("invoice_send_email", args=[invoice_draft.pk]),
        data={
            "subject": "Invoice",
            "recipient": "client@example.com",
            "cc": "not-an-email",
            "message": "Body",
        },
        HTTP_X_REQUESTED_WITH="XMLHttpRequest",
    )
    # 400 signals the client script to re-inject the modal body (not redirect).
    assert resp.status_code == 400
    assert b'name="cc"' in resp.content  # form fragment re-rendered
    assert len(mail.outbox) == 0
    invoice_draft.refresh_from_db()
    assert invoice_draft.status == "DRAFT"


# ---------- Form unit: CC parsing/validation ----------


def test_cc_form_parses_and_dedupes():
    form = InvoiceEmailForm(data={
        "subject": "S", "recipient": "a@b.com",
        "cc": "x@y.com,  x@y.com ; z@w.com",
        "message": "m",
    })
    assert form.is_valid(), form.errors
    assert form.cleaned_data["cc"] == ["x@y.com", "z@w.com"]


def test_cc_empty_is_ok():
    form = InvoiceEmailForm(data={
        "subject": "S", "recipient": "a@b.com", "cc": "", "message": "m",
    })
    assert form.is_valid(), form.errors
    assert form.cleaned_data["cc"] == []


# ---------- Backward compatibility: no attachment/cc still works ----------


def test_simple_notification_backward_compatible(settings):
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    settings.DEFAULT_FROM_EMAIL = "noreply@kibraypainting.us"
    mail.outbox = []
    ok = KibrayEmailService.send_simple_notification(
        to_emails=["x@example.com"],
        subject="Hi",
        message="Body",
    )
    assert ok is True
    assert len(mail.outbox) == 1
    assert mail.outbox[0].attachments == []
    assert mail.outbox[0].cc == []
    assert mail.outbox[0].bcc == []


def test_simple_notification_passes_bcc(settings):
    """The service forwards bcc through to the underlying message."""
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    settings.DEFAULT_FROM_EMAIL = "noreply@kibraypainting.us"
    mail.outbox = []
    ok = KibrayEmailService.send_simple_notification(
        to_emails=["x@example.com"],
        subject="Hi",
        message="Body",
        cc=["cc@example.com"],
        bcc=["office@kibraypainting.net"],
    )
    assert ok is True
    assert len(mail.outbox) == 1
    assert mail.outbox[0].cc == ["cc@example.com"]
    assert mail.outbox[0].bcc == ["office@kibraypainting.net"]
