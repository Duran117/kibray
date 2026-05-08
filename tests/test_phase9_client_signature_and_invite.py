"""End-to-end tests for the client-facing flows that the user
explicitly asked us to verify "100% sin errores":

1. The base_modern.html template no longer leaks a multi-line
   {# #} comment into the rendered page (regression of the bug
   visible in the May-7 screenshot).
2. The contract client view (public, token-based) renders, then
   accepts a POSTed signature, persists the signature image,
   stamps client_signed_at + client_signed_name + IP, and flips
   contract.status to 'signed'.
3. The "Invite Client to Dashboard" entry point (`project_add_owner`)
   is reachable from the project menu and creates a User +
   ClientProjectAccess in one POST, with the welcome credential
   email being attempted exactly once.
"""
from __future__ import annotations

import base64
import uuid
from decimal import Decimal
from unittest import mock

import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse

from core.models import (
    ClientProjectAccess,
    Contract,
    Estimate,
    Project,
)

User = get_user_model()
pytestmark = pytest.mark.django_db


# ─── Fixtures ────────────────────────────────────────────────────────
@pytest.fixture
def admin_user():
    u = User.objects.create_user(
        "n_admin_e2e", "a@x", "x", is_staff=True, is_superuser=True,
    )
    u.profile.role = "admin"
    u.profile.save()
    return u


@pytest.fixture
def project():
    from datetime import date
    return Project.objects.create(
        name="Sign-Flow Project",
        start_date=date.today(),
    )


@pytest.fixture
def signable_contract(project):
    estimate = Estimate.objects.create(
        project=project, version=1, approved=True,
        code=f"KPTE{uuid.uuid4().hex[:4].upper()}",
    )
    return Contract.objects.create(
        estimate=estimate,
        project=project,
        contract_number=f"C-{uuid.uuid4().hex[:6]}",
        status="pending_signature",
        total_amount=Decimal("12000.00"),
        client_view_token=uuid.uuid4().hex,
    )


# ─── 1. Template comment-leak regression ─────────────────────────────
class TestBaseModernNoCommentLeak:
    """The May-7 bug: a multi-line ``{# ... #}`` comment in
    base_modern.html was rendered as visible text because Django's
    ``{# #}`` only supports single-line comments. The fix is to use
    ``{% comment %}...{% endcomment %}`` for multi-line blocks.
    This test prevents the regression."""

    def test_base_template_has_no_unclosed_singleline_comments(self):
        import os
        import re

        path = os.path.join(
            "core", "templates", "core", "base_modern.html",
        )
        with open(path) as f:
            for ln, line in enumerate(f, 1):
                # A `{#` with no matching `#}` on the same line is
                # always a bug — Django will render it raw.
                if "{#" in line and "#}" not in line:
                    pytest.fail(
                        f"Unclosed single-line {{# #}} comment at "
                        f"{path}:{ln}: {line.rstrip()}\n"
                        f"Use {{% comment %}}...{{% endcomment %}} "
                        f"for multi-line comments."
                    )

    def test_admin_dashboard_does_not_leak_template_comment(
        self, admin_user, client: Client,
    ):
        client.force_login(admin_user)
        resp = client.get(reverse("dashboard"))
        assert resp.status_code in (200, 302)
        if resp.status_code == 200:
            body = resp.content.decode("utf-8", errors="ignore")
            # The leaked text from the screenshot.
            assert "sidebar_dark.html was removed" not in body
            assert "phase9_nav_sections" not in body or (
                # OK if it appears inside an HTML attribute / JS,
                # but it must NOT appear as raw text leak.
                "{#" not in body and "#}" not in body
            )


# ─── 2. Contract signing — full happy-path E2E ──────────────────────
class TestContractClientSignFlow:

    def test_get_renders_signing_page(self, signable_contract):
        c = Client()
        url = reverse(
            "contract_client_view",
            kwargs={"token": signable_contract.client_view_token},
        )
        resp = c.get(url)
        assert resp.status_code == 200
        body = resp.content.decode()
        # Signature pad + form must be present.
        assert "signature-pad" in body
        assert 'name="action"' in body
        assert 'value="sign"' in body
        assert 'name="client_name"' in body

    def test_post_sign_persists_signature_and_flips_status(
        self, signable_contract,
    ):
        c = Client()
        url = reverse(
            "contract_client_view",
            kwargs={"token": signable_contract.client_view_token},
        )

        # 1×1 transparent PNG as data URL.
        png_bytes = (
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
            b"\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
            b"\x00\x00\x00\rIDATx\x9cc\xfc\xcf\xc0\x00\x00\x00\x03"
            b"\x00\x01\xb6\xc6\x86\xc4\x00\x00\x00\x00IEND\xaeB`\x82"
        )
        sig_data_url = (
            "data:image/png;base64," + base64.b64encode(png_bytes).decode()
        )

        # Patch the async PDF dispatcher so the test does not require
        # a Celery worker.
        with mock.patch(
            "core.services.contract_service.transaction.on_commit",
            side_effect=lambda fn: None,
        ):
            resp = c.post(url, {
                "action": "sign",
                "client_name": "Jane Q. Client",
                "signature_data": sig_data_url,
            })

        assert resp.status_code in (200, 302)

        signable_contract.refresh_from_db()
        assert signable_contract.status == "signed"
        assert signable_contract.client_signed_name == "Jane Q. Client"
        assert signable_contract.client_signed_at is not None
        assert signable_contract.client_signature  # FieldFile is truthy
        # Signature file must actually be on disk (or storage).
        assert signable_contract.client_signature.size > 0

    def test_post_sign_without_name_does_not_sign(
        self, signable_contract,
    ):
        c = Client()
        url = reverse(
            "contract_client_view",
            kwargs={"token": signable_contract.client_view_token},
        )
        resp = c.post(url, {
            "action": "sign",
            "client_name": "",
            "signature_data": "",
        })
        assert resp.status_code == 200
        signable_contract.refresh_from_db()
        assert signable_contract.status == "pending_signature"
        assert signable_contract.client_signed_at is None


# ─── 3. Invite Client (project_add_owner) ───────────────────────────
class TestInviteClientFromProjectMenu:

    def test_invite_link_present_in_project_overview(
        self, admin_user, project, client,
    ):
        client.force_login(admin_user)
        resp = client.get(
            reverse("project_overview", kwargs={"project_id": project.id})
        )
        assert resp.status_code == 200
        body = resp.content.decode()
        invite_url = reverse(
            "project_add_owner", kwargs={"project_id": project.id}
        )
        assert invite_url in body
        # The new menu entry label must be discoverable.
        assert "Invite Client" in body

    def test_invite_creates_user_and_grants_access(
        self, admin_user, project, client,
    ):
        client.force_login(admin_user)
        url = reverse(
            "project_add_owner", kwargs={"project_id": project.id},
        )

        # Patch the email send so the test doesn't hit SMTP.
        with mock.patch(
            "core.services.email_service.KibrayEmailService."
            "send_welcome_credentials",
            return_value=True,
        ) as send_mock:
            resp = client.post(url, {
                "first_name": "Nora",
                "last_name": "NewClient",
                "email": f"nora_{uuid.uuid4().hex[:6]}@example.com",
                "phone": "555-1234",
                "access_role": "client",
                "send_credentials": "on",
            }, follow=True)

        assert resp.status_code == 200

        # User now exists.
        new_user = User.objects.filter(first_name="Nora").last()
        assert new_user is not None
        # ClientProjectAccess granted to the project.
        assert ClientProjectAccess.objects.filter(
            user=new_user, project=project,
        ).exists()
        # Welcome email attempted exactly once.
        assert send_mock.call_count == 1
