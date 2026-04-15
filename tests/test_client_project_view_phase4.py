"""
Phase 4 Tests — Client Project View Hardening
===============================================
Verifies the new context variables and template sections added in Phase 4:
- pending_contracts (contracts awaiting client signature)
- pending_change_orders (COs awaiting client signature)
- pending_color_samples (color samples awaiting client approval)
- recent_daily_logs (published daily logs)
- unread_notifications (notification badge count)
- Action Required banner rendering
- Security: non-client user is denied access
"""

import uuid
from decimal import Decimal

import pytest
from django.test import Client as TestClient
from django.contrib.auth.models import User
from django.utils import timezone

from core.models import (
    ClientProjectAccess,
    ChangeOrder,
    ColorSample,
    Contract,
    DailyLog,
    Estimate,
    Notification,
    Profile,
    Project,
)

pytestmark = pytest.mark.django_db


# ─── Fixtures ───────────────────────────────────────────────────────


@pytest.fixture
def client_user(db):
    user = User.objects.create_user(username="testclient", password="pass1234")
    Profile.objects.update_or_create(user=user, defaults={"role": "client"})
    return user


@pytest.fixture
def other_user(db):
    user = User.objects.create_user(username="outsider", password="pass1234")
    Profile.objects.update_or_create(user=user, defaults={"role": "client"})
    return user


@pytest.fixture
def admin_user(db):
    user = User.objects.create_user(username="admin1", password="pass1234", is_staff=True)
    Profile.objects.update_or_create(user=user, defaults={"role": "admin"})
    return user


@pytest.fixture
def project(db):
    return Project.objects.create(name="Phase4 Test Project")


@pytest.fixture
def access(client_user, project):
    return ClientProjectAccess.objects.create(
        user=client_user, project=project, role="client"
    )


@pytest.fixture
def http(client_user):
    c = TestClient()
    c.login(username="testclient", password="pass1234")
    return c


@pytest.fixture
def estimate(project):
    return Estimate.objects.create(
        project=project,
        version=1,
        approved=True,
        code=f"KPTT{uuid.uuid4().hex[:4].upper()}",
    )


# ─── Helper ─────────────────────────────────────────────────────────


def _url(project):
    from django.urls import reverse
    return reverse("client_project_view", kwargs={"project_id": project.id})


# ─── Tests ───────────────────────────────────────────────────────────


class TestClientProjectViewAccess:
    """Security checks."""

    def test_client_with_access_sees_200(self, http, project, access):
        resp = http.get(_url(project))
        assert resp.status_code == 200

    def test_client_without_access_redirected(self, http, project):
        """Client without ClientProjectAccess must NOT see the page."""
        resp = http.get(_url(project))
        # Should redirect (302 or 403-equivalent redirect)
        assert resp.status_code in (302, 403)

    def test_unauthenticated_redirected_to_login(self, project):
        c = TestClient()
        resp = c.get(_url(project))
        assert resp.status_code == 302
        assert "/login" in resp.url or "/accounts/login" in resp.url

    def test_admin_can_access(self, admin_user, project):
        """Staff/admin should be able to access any project view."""
        c = TestClient()
        c.login(username="admin1", password="pass1234")
        resp = c.get(_url(project))
        assert resp.status_code == 200


class TestPendingContracts:
    """Contracts pending signature appear in context and template."""

    def test_pending_contract_in_context(self, http, project, access, estimate):
        contract = Contract.objects.create(
            estimate=estimate,
            project=project,
            contract_number=f"C-{uuid.uuid4().hex[:6]}",
            status="pending_signature",
            total_amount=Decimal("5000.00"),
            client_view_token=uuid.uuid4().hex,
        )
        resp = http.get(_url(project))
        assert resp.status_code == 200
        assert contract in resp.context["pending_contracts"]

    def test_signed_contract_not_in_pending(self, http, project, access, estimate):
        Contract.objects.create(
            estimate=estimate,
            project=project,
            contract_number=f"C-{uuid.uuid4().hex[:6]}",
            status="signed",
            total_amount=Decimal("5000.00"),
            client_view_token=uuid.uuid4().hex,
        )
        resp = http.get(_url(project))
        assert resp.status_code == 200
        assert len(resp.context["pending_contracts"]) == 0

    def test_action_required_banner_with_pending_contract(self, http, project, access, estimate):
        Contract.objects.create(
            estimate=estimate,
            project=project,
            contract_number=f"C-{uuid.uuid4().hex[:6]}",
            status="pending_signature",
            total_amount=Decimal("5000.00"),
            client_view_token=uuid.uuid4().hex,
        )
        resp = http.get(_url(project))
        content = resp.content.decode()
        # Banner renders — check for EN or ES text (i18n)
        low = content.lower()
        assert "action required" in low or "acción requerida" in low
        assert "contract" in low or "contrato" in low


class TestPendingChangeOrders:
    """Change orders awaiting client signature."""

    def test_pending_co_in_context(self, http, project, access):
        co = ChangeOrder.objects.create(
            project=project,
            description="Add extra coat",
            amount=Decimal("1200.00"),
            status="approved",
            # No signature — pending client sign
        )
        resp = http.get(_url(project))
        assert resp.status_code == 200
        assert co in resp.context["pending_change_orders"]

    def test_signed_co_not_in_pending(self, http, project, access):
        ChangeOrder.objects.create(
            project=project,
            description="Already signed CO",
            amount=Decimal("500.00"),
            status="approved",
            signed_at=timezone.now(),
            signature_image="sig.png",
        )
        resp = http.get(_url(project))
        assert resp.status_code == 200
        assert len(resp.context["pending_change_orders"]) == 0

    def test_action_required_banner_with_pending_co(self, http, project, access):
        ChangeOrder.objects.create(
            project=project,
            description="Pending CO",
            amount=Decimal("800.00"),
            status="approved",
        )
        resp = http.get(_url(project))
        content = resp.content.decode()
        low = content.lower()
        assert "change order" in low or "orden de cambio" in low


class TestPendingColorSamples:
    """Color samples pending client approval."""

    def test_pending_sample_in_context(self, http, project, access):
        sample = ColorSample.objects.create(
            project=project,
            name="Navajo White",
            status="proposed",
        )
        resp = http.get(_url(project))
        assert resp.status_code == 200
        assert sample in resp.context["pending_color_samples"]

    def test_approved_sample_not_in_pending(self, http, project, access):
        ColorSample.objects.create(
            project=project,
            name="Approved Color",
            status="approved",
        )
        resp = http.get(_url(project))
        assert resp.status_code == 200
        assert len(resp.context["pending_color_samples"]) == 0


class TestRecentDailyLogs:
    """Published daily logs visible to client."""

    def test_published_log_in_context(self, http, project, access):
        log = DailyLog.objects.create(
            project=project,
            date=timezone.localdate(),
            is_published=True,
            accomplishments="Primed all rooms",
        )
        resp = http.get(_url(project))
        assert resp.status_code == 200
        assert log in resp.context["recent_daily_logs"]

    def test_unpublished_log_not_in_context(self, http, project, access):
        DailyLog.objects.create(
            project=project,
            date=timezone.localdate(),
            is_published=False,
        )
        resp = http.get(_url(project))
        assert resp.status_code == 200
        assert len(resp.context["recent_daily_logs"]) == 0

    def test_daily_logs_section_rendered(self, http, project, access):
        DailyLog.objects.create(
            project=project,
            date=timezone.localdate(),
            is_published=True,
            accomplishments="Finished exterior trim",
        )
        resp = http.get(_url(project))
        content = resp.content.decode()
        low = content.lower()
        assert "daily progress" in low or "progreso diario" in low


class TestUnreadNotifications:
    """Notification badge count."""

    def test_unread_count_in_context(self, http, project, access, client_user):
        for i in range(3):
            Notification.objects.create(
                user=client_user,
                project=project,
                message=f"Test notification {i}",
                is_read=False,
            )
        resp = http.get(_url(project))
        assert resp.status_code == 200
        assert resp.context["unread_notifications"] == 3

    def test_read_notifications_not_counted(self, http, project, access, client_user):
        Notification.objects.create(
            user=client_user,
            project=project,
            message="Already read",
            is_read=True,
        )
        resp = http.get(_url(project))
        assert resp.status_code == 200
        assert resp.context["unread_notifications"] == 0

    def test_unread_badge_rendered(self, http, project, access, client_user):
        Notification.objects.create(
            user=client_user,
            project=project,
            message="New update",
            is_read=False,
        )
        resp = http.get(_url(project))
        content = resp.content.decode()
        low = content.lower()
        assert "unread notification" in low or "notificación" in low


class TestNoActionRequired:
    """When nothing is pending, banner should NOT render."""

    def test_no_banner_when_nothing_pending(self, http, project, access):
        resp = http.get(_url(project))
        content = resp.content.decode()
        low = content.lower()
        assert "action required" not in low or "acción requerida" not in low
        # The definitive check: the banner div should NOT be present
        assert "from-amber-50 to-orange-50" not in content
