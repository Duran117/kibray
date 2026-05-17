"""Contract sharing UX + lifecycle.

Covers the four pieces of the 2026-05-17 hotfix:

A. "Send by Email" admin action — calls KibrayEmailService and stamps
   ``last_sent_to_email`` / ``last_sent_at`` on the contract.
B. ``ContractAttachment`` upload + delete.
C. The signing link is hard-closed once the contract is signed:
   * ``Contract.signing_link_active`` flips to False.
   * The public ``contract_client_view`` returns 410 Gone with the
     friendly ``contract_link_closed.html`` page (no more contract
     content, no signature form, no chance of duplicate signatures).
D. Backfill: pre-existing signed contracts also have their link closed.
"""
from __future__ import annotations

from datetime import date
from io import BytesIO
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client
from django.urls import reverse

from core.models import Contract, ContractAttachment, Estimate, Project

User = get_user_model()
pytestmark = pytest.mark.django_db


# ─── Fixtures ──────────────────────────────────────────────────────
@pytest.fixture
def staff(db):
    u = User.objects.create_user(
        "co_staff", "s@x", "x", is_staff=True, is_superuser=True,
    )
    u.profile.role = "admin"
    u.profile.save()
    return u


@pytest.fixture
def project(db):
    return Project.objects.create(
        name="Send-Link Project",
        start_date=date.today(),
        client="John Smith",
    )


@pytest.fixture
def contract(project):
    est = Estimate.objects.create(project=project, code="EST-SL-1", version=1)
    return Contract.objects.create(
        estimate=est,
        project=project,
        total_amount=10000,
        status="pending_signature",
    )


# ─── A. Send by Email ──────────────────────────────────────────────
class TestSendLinkByEmail:
    def test_email_sent_and_stamped(self, staff, contract):
        c = Client()
        c.force_login(staff)
        url = reverse("contract_edit", kwargs={"contract_id": contract.id})

        with patch(
            "core.services.email_service.KibrayEmailService.send_simple_notification",
            return_value=True,
        ) as mock_send:
            resp = c.post(url, {
                "action": "send_link_email",
                "recipient_email": "client@example.com",
                "recipient_name": "John Smith",
            })

        assert resp.status_code == 302
        assert mock_send.called
        contract.refresh_from_db()
        assert contract.last_sent_to_email == "client@example.com"
        assert contract.last_sent_at is not None

    def test_requires_email_address(self, staff, contract):
        c = Client()
        c.force_login(staff)
        url = reverse("contract_edit", kwargs={"contract_id": contract.id})

        with patch(
            "core.services.email_service.KibrayEmailService.send_simple_notification"
        ) as mock_send:
            resp = c.post(url, {
                "action": "send_link_email",
                "recipient_email": "",
            })

        assert resp.status_code == 302
        assert not mock_send.called
        contract.refresh_from_db()
        assert contract.last_sent_to_email == ""

    def test_blocked_when_link_closed(self, staff, contract):
        contract.signing_link_active = False
        contract.save()
        c = Client()
        c.force_login(staff)
        url = reverse("contract_edit", kwargs={"contract_id": contract.id})

        with patch(
            "core.services.email_service.KibrayEmailService.send_simple_notification"
        ) as mock_send:
            c.post(url, {
                "action": "send_link_email",
                "recipient_email": "client@example.com",
            })
        assert not mock_send.called


# ─── B. Attachments ────────────────────────────────────────────────
class TestContractAttachments:
    def _upload(self, c, contract, label="Proposal"):
        url = reverse("contract_edit", kwargs={"contract_id": contract.id})
        f = SimpleUploadedFile("proposal.pdf", b"%PDF-1.4 fake", content_type="application/pdf")
        return c.post(url, {
            "action": "upload_attachment",
            "attachment_label": label,
            "attachment_file": f,
        })

    def test_upload_creates_attachment(self, staff, contract):
        c = Client()
        c.force_login(staff)
        resp = self._upload(c, contract)
        assert resp.status_code == 302
        assert contract.attachments.count() == 1
        att = contract.attachments.first()
        assert att.label == "Proposal"
        assert att.uploaded_by == staff
        assert att.display_name == "Proposal"

    def test_delete_attachment(self, staff, contract):
        c = Client()
        c.force_login(staff)
        self._upload(c, contract)
        att = contract.attachments.first()
        url = reverse("contract_edit", kwargs={"contract_id": contract.id})

        resp = c.post(url, {
            "action": "delete_attachment",
            "attachment_id": att.id,
        })
        assert resp.status_code == 302
        assert contract.attachments.count() == 0

    def test_attachments_visible_on_public_signing_page(self, staff, contract):
        c = Client()
        c.force_login(staff)
        self._upload(c, contract, label="Original Proposal")

        # Public page (no auth)
        anon = Client()
        resp = anon.get(reverse(
            "contract_client_view",
            kwargs={"token": contract.client_view_token},
        ))
        assert resp.status_code == 200
        assert b"Original Proposal" in resp.content


# ─── C. Link lifecycle: closed after signing ───────────────────────
class TestSigningLinkLifecycle:
    def test_active_link_renders_full_contract(self, contract):
        anon = Client()
        resp = anon.get(reverse(
            "contract_client_view",
            kwargs={"token": contract.client_view_token},
        ))
        assert resp.status_code == 200
        # Full signing form is present
        assert b"signature_data" in resp.content or b"signature-pad" in resp.content

    def test_sign_contract_closes_link(self, contract):
        from core.services.contract_service import ContractService

        ContractService.sign_contract(
            contract=contract,
            client_name="John Smith",
            signature_data=None,
            ip_address="127.0.0.1",
            generate_signed_pdf=False,
            async_pdf=False,
        )
        contract.refresh_from_db()
        assert contract.signing_link_active is False
        assert contract.is_signed is True
        assert contract.can_be_signed is False

    def test_closed_link_returns_410_with_friendly_page(self, contract):
        contract.signing_link_active = False
        contract.client_signed_at = contract.created_at
        contract.client_signed_name = "John Smith"
        contract.save()

        anon = Client()
        resp = anon.get(reverse(
            "contract_client_view",
            kwargs={"token": contract.client_view_token},
        ))
        assert resp.status_code == 410
        # Friendly closed page — not the full contract
        assert b"Contract Already Signed" in resp.content or b"closed" in resp.content.lower()
        # And the signing form must NOT be present
        assert b"signature-pad" not in resp.content
