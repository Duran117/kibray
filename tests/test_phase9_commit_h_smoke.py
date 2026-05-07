"""
Phase 9 Commit H — Integration smoke test for the new role-aware sidebar.

Asserts that with PHASE9_NEW_SIDEBAR=True, every role can hit a
representative page and the page renders the new sidebar template
(``data-sidebar="phase9"``) without raising a 500.

This is the regression guard the staging flip relies on. If any role
produces a TemplateSyntaxError, NoReverseMatch, or unhandled exception
in the new nav code path, this test will catch it before the deploy.
"""
from __future__ import annotations

from datetime import date

import pytest
from django.contrib.auth import get_user_model
from django.test import Client, override_settings
from django.urls import reverse

from core.models import (
    ClientProjectAccess,
    Employee,
    Project,
    ProjectManagerAssignment,
    TimeEntry,
)

User = get_user_model()


def _mk(username, *, role=None, is_staff=False, is_superuser=False):
    u = User.objects.create_user(
        username=username, password="x",
        is_staff=is_staff, is_superuser=is_superuser,
    )
    if role:
        u.profile.role = role
        u.profile.save()
    return u


@pytest.fixture
def world(db):
    p = Project.objects.create(name="H-Proj-A", start_date=date.today())
    p_client = Project.objects.create(name="H-Proj-B", start_date=date.today())

    admin = _mk("h_admin", role="admin", is_superuser=True, is_staff=True)
    pm = _mk("h_pm", role="project_manager")
    ProjectManagerAssignment.objects.create(project=p, pm=pm, role="pm")

    emp = _mk("h_emp", role="employee")
    e = Employee.objects.create(
        user=emp, first_name="E", last_name="H",
        social_security_number="H-9-9", hourly_rate=18,
    )
    TimeEntry.objects.create(
        employee=e, project=p, date=date.today(), start_time="08:00",
    )

    client_u = _mk("h_client", role="client")
    ClientProjectAccess.objects.create(
        user=client_u, project=p_client, role="viewer", is_active=True,
    )

    return {
        "p": p, "p_client": p_client,
        "admin": admin, "pm": pm, "emp": emp, "client": client_u,
    }


@pytest.fixture
def flag_on(settings):
    settings.PHASE9_NEW_SIDEBAR = True


@pytest.fixture
def flag_off(settings):
    settings.PHASE9_NEW_SIDEBAR = False


@pytest.mark.usefixtures("flag_on")
class TestNewSidebarRendersForAllRoles:
    """With the flag ON, every role must successfully render their
    landing page using the new sidebar component.

    The smoke check is intentionally minimal:
      - HTTP status is 2xx or 3xx (NOT 5xx)
      - Either the new sidebar marker is present, OR the response is
        a redirect to a role-appropriate landing page.
    """

    def _login(self, client, user):
        assert client.login(username=user.username, password="x"), (
            f"Failed to log in as {user.username}"
        )

    def _follow_and_assert_no_500(self, client, url):
        resp = client.get(url, follow=True)
        assert resp.status_code < 500, (
            f"500 from {url}: status={resp.status_code}\n"
            f"content head: {resp.content[:500]!r}"
        )
        return resp

    def test_admin_dashboard_renders_new_sidebar(self, client, world):
        self._login(client, world["admin"])
        resp = self._follow_and_assert_no_500(client, reverse("dashboard"))
        assert resp.status_code == 200
        assert b'data-sidebar="phase9"' in resp.content, (
            "Admin dashboard did not render the new sidebar"
        )
        # Admin must see the Administration section title.
        assert b"Administration" in resp.content

    def test_pm_dashboard_renders_new_sidebar(self, client, world):
        self._login(client, world["pm"])
        resp = self._follow_and_assert_no_500(client, reverse("dashboard"))
        assert resp.status_code == 200
        assert b'data-sidebar="phase9"' in resp.content
        assert b"Planning" in resp.content
        # PM must NOT see Administration section.
        assert b"Administration" not in resp.content

    def test_employee_dashboard_renders_new_sidebar(self, client, world):
        self._login(client, world["emp"])
        resp = self._follow_and_assert_no_500(client, reverse("dashboard"))
        # Employee may be redirected to a different landing page; just
        # ensure no 500 and the eventually-rendered page uses new sidebar.
        assert resp.status_code == 200
        assert b'data-sidebar="phase9"' in resp.content
        # Employee must NOT see admin sections.
        for forbidden in (b"Administration", b"Finance", b"Analytics", b"Planning"):
            assert forbidden not in resp.content, (
                f"Employee leak: '{forbidden!r}' visible in sidebar"
            )

    def test_client_dashboard_renders_new_sidebar(self, client, world):
        self._login(client, world["client"])
        # Clients are routed to dashboard_client; hit it directly.
        url = reverse("dashboard_client")
        resp = self._follow_and_assert_no_500(client, url)
        assert resp.status_code == 200
        assert b'data-sidebar="phase9"' in resp.content
        # Client must NOT see staff/admin sections.
        for forbidden in (
            b"Administration", b"Finance", b"Analytics",
            b"Planning", b"Operations",
        ):
            assert forbidden not in resp.content, (
                f"Client leak: '{forbidden!r}' visible in sidebar"
            )


@pytest.mark.usefixtures("flag_off")
class TestLegacySidebarStillRendersWhenFlagOff:
    """Belt-and-braces: with the flag off, the legacy sidebar must
    still render. This protects production until Commit H is shipped
    there.
    """

    def test_admin_dashboard_uses_legacy_when_flag_off(self, client, db):
        admin = _mk("h_admin_off", role="admin", is_superuser=True, is_staff=True)
        client.login(username="h_admin_off", password="x")
        resp = client.get(reverse("dashboard"), follow=True)
        assert resp.status_code == 200
        # The new sidebar marker must be absent.
        assert b'data-sidebar="phase9"' not in resp.content


# ─────────────── DEV / STAGING settings sanity ───────────────
class TestDevAndStagingDefaultFlagOn:
    """The Commit H wiring sets PHASE9_NEW_SIDEBAR=True by default in
    development.py and staging.py. Production.py must still default
    OFF until a follow-up commit explicitly flips it.
    """

    def test_development_settings_default_flag_on(self):
        import importlib
        import os

        # Snapshot + clear any env override so we test the defaults.
        prev = os.environ.pop("PHASE9_NEW_SIDEBAR", None)
        try:
            import kibray_backend.settings.development as dev_mod
            importlib.reload(dev_mod)
            assert dev_mod.PHASE9_NEW_SIDEBAR is True, (
                "development.py must default PHASE9_NEW_SIDEBAR=True "
                "so local devs always exercise the new sidebar"
            )
        finally:
            if prev is not None:
                os.environ["PHASE9_NEW_SIDEBAR"] = prev

    def test_staging_settings_default_flag_on(self):
        """We can't import staging.py in CI (it inherits production.py
        which raises without DJANGO_SECRET_KEY), so verify textually
        that the file enables the flag by default.
        """
        from pathlib import Path
        src = (
            Path(__file__).resolve().parent.parent
            / "kibray_backend" / "settings" / "staging.py"
        ).read_text(encoding="utf-8")
        assert 'PHASE9_NEW_SIDEBAR = os.environ.get("PHASE9_NEW_SIDEBAR", "1") == "1"' in src, (
            "staging.py must default PHASE9_NEW_SIDEBAR=True (env default '1')"
        )

    def test_production_settings_default_flag_off(self):
        """Production must NOT auto-enable until a separate commit
        explicitly flips it after staging soak.
        """
        import importlib
        import os

        prev = os.environ.pop("PHASE9_NEW_SIDEBAR", None)
        try:
            # production.py reads from base.py which defaults False;
            # production.py itself must not override that to True.
            import kibray_backend.settings.base as base_mod
            importlib.reload(base_mod)
            assert base_mod.PHASE9_NEW_SIDEBAR is False, (
                "base.py / production must default PHASE9_NEW_SIDEBAR=False "
                "until staging soak completes."
            )
        finally:
            if prev is not None:
                os.environ["PHASE9_NEW_SIDEBAR"] = prev
