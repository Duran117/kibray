"""Phase 9 Commit M — equivalence tests for the promoted canonical
view-helper functions in ``core.access``.

Commit M moved two helpers out of ``core/views/_helpers.py`` (where
they were post-Commit-J shims) into ``core.access`` proper:

  * ``check_project_access(user, project) -> (bool, redirect_name)``
  * ``require_admin_or_redirect(request) -> HttpResponse | None``

The legacy underscored names in ``core/views/_helpers.py`` are now
one-line forwarders to the canonical implementations. These tests
lock in the behavior contract for both APIs and assert byte-for-byte
equivalence between the new canonical names and the legacy shims.
"""
from __future__ import annotations

from datetime import date

import pytest
from django.contrib.auth import get_user_model
from django.test import RequestFactory

from core.access import check_project_access, require_admin_or_redirect
from core.models import (
    ClientProjectAccess,
    Employee,
    Project,
    ProjectManagerAssignment,
    TimeEntry,
)
from core.views._helpers import (
    _check_user_project_access,
    _require_admin_or_redirect,
)

User = get_user_model()
pytestmark = pytest.mark.django_db


# ─── Fixtures ────────────────────────────────────────────────────────
@pytest.fixture
def users():
    out = {}

    out["admin"] = User.objects.create_user(
        "m_admin", "a@x", "x", is_staff=True, is_superuser=True,
    )
    out["admin"].profile.role = "admin"
    out["admin"].profile.save()

    out["staff_only"] = User.objects.create_user(
        "m_staff", "s@x", "x", is_staff=True,
    )
    out["staff_only"].profile.role = "employee"
    out["staff_only"].profile.save()

    out["pm"] = User.objects.create_user("m_pm", "pm@x", "x")
    out["pm"].profile.role = "project_manager"
    out["pm"].profile.save()

    out["employee"] = User.objects.create_user("m_emp", "e@x", "x")
    out["employee"].profile.role = "employee"
    out["employee"].profile.save()

    out["client"] = User.objects.create_user("m_client", "c@x", "x")
    out["client"].profile.role = "client"
    out["client"].profile.save()

    return out


@pytest.fixture
def world(users):
    p = Project.objects.create(name="M-World", start_date=date.today())
    ProjectManagerAssignment.objects.create(
        project=p, pm=users["pm"], role="pm",
    )
    emp = Employee.objects.create(
        user=users["employee"], first_name="M", last_name="Emp",
        social_security_number="M-1-1", hourly_rate=20,
    )
    TimeEntry.objects.create(
        employee=emp, project=p, date=date.today(), start_time="08:00",
    )
    ClientProjectAccess.objects.create(
        user=users["client"], project=p, role="viewer", is_active=True,
    )
    p_other = Project.objects.create(
        name="M-World-Other", start_date=date.today(),
    )
    return {"p": p, "p_other": p_other}


# ─── check_project_access ────────────────────────────────────────────
class TestCheckProjectAccessCanonical:
    """Behavior contract for the new public API."""

    @pytest.mark.parametrize("role,project_key,expected_ok", [
        ("admin", "p", True),
        ("admin", "p_other", True),
        ("staff_only", "p", True),
        ("pm", "p", True),
        ("pm", "p_other", False),
        ("employee", "p", True),
        ("employee", "p_other", False),
        ("client", "p", True),
        ("client", "p_other", False),
    ])
    def test_truth_table(self, users, world, role, project_key, expected_ok):
        ok, dest = check_project_access(users[role], world[project_key])
        assert ok is expected_ok
        if ok:
            assert dest is None
        else:
            assert dest in {"dashboard", "dashboard_client"}

    def test_client_denied_routes_to_client_dashboard(self, users, world):
        ok, dest = check_project_access(users["client"], world["p_other"])
        assert ok is False
        assert dest == "dashboard_client"

    def test_non_client_denied_routes_to_dashboard(self, users, world):
        ok, dest = check_project_access(users["pm"], world["p_other"])
        assert ok is False
        assert dest == "dashboard"

    def test_assigned_to_back_compat(self, users, world):
        """When a user is in ``project.assigned_to`` they must be granted
        even if no other role-based path applies. This is the legacy
        ``assigned_to`` M2M back-compat."""
        # Try only if the back-compat M2M actually exists on the model.
        p = world["p_other"]
        if not hasattr(p, "assigned_to"):
            pytest.skip("project.assigned_to M2M not present in this build")
        u = users["employee"]
        # Without the M2M, employee has no path to p_other.
        assert check_project_access(u, p)[0] is False
        # Add via M2M and re-check.
        p.assigned_to.add(u)
        ok, dest = check_project_access(u, p)
        assert ok is True
        assert dest is None


class TestCheckProjectAccessShimEquivalence:
    """The legacy underscored name must keep returning identical results."""

    def test_shim_matches_canonical_for_every_user(self, users, world):
        for key, u in users.items():
            for pk in ("p", "p_other"):
                p = world[pk]
                assert _check_user_project_access(u, p) == check_project_access(u, p), (
                    f"shim/canonical drift for {key} @ {pk}"
                )


# ─── require_admin_or_redirect ───────────────────────────────────────
class TestRequireAdminOrRedirectCanonical:
    def _req(self, user):
        rf = RequestFactory()
        req = rf.get("/admin-only/")
        req.user = user
        # Required for `messages` framework.
        from django.contrib.messages.storage.fallback import FallbackStorage
        setattr(req, "session", {})
        setattr(req, "_messages", FallbackStorage(req))
        return req

    def test_admin_returns_none(self, users):
        assert require_admin_or_redirect(self._req(users["admin"])) is None

    def test_staff_only_returns_none(self, users):
        # is_staff users keep admin-tool access for back-compat.
        assert require_admin_or_redirect(self._req(users["staff_only"])) is None

    @pytest.mark.parametrize("role", ["pm", "employee", "client"])
    def test_non_admin_redirects_to_dashboard(self, users, role):
        resp = require_admin_or_redirect(self._req(users[role]))
        assert resp is not None
        assert resp.status_code == 302
        # redirect("dashboard") resolves to whatever URL the project
        # maps the name to; just confirm a Location header is present.
        assert resp["Location"]


class TestRequireAdminOrRedirectShimEquivalence:
    def _req(self, user):
        rf = RequestFactory()
        req = rf.get("/admin-only/")
        req.user = user
        from django.contrib.messages.storage.fallback import FallbackStorage
        setattr(req, "session", {})
        setattr(req, "_messages", FallbackStorage(req))
        return req

    @pytest.mark.parametrize("role", [
        "admin", "staff_only", "pm", "employee", "client",
    ])
    def test_shim_matches_canonical(self, users, role):
        u = users[role]
        canonical = require_admin_or_redirect(self._req(u))
        shim = _require_admin_or_redirect(self._req(u))
        # Both return None or both return a redirect with the same status.
        if canonical is None:
            assert shim is None
        else:
            assert shim is not None
            assert shim.status_code == canonical.status_code
            assert shim["Location"] == canonical["Location"]


# ─── Public API surface ──────────────────────────────────────────────
class TestPublicApiSurface:
    def test_canonical_names_exported_from_core_access(self):
        import core.access as ca
        assert "check_project_access" in ca.__all__
        assert "require_admin_or_redirect" in ca.__all__

    def test_no_remaining_legacy_callers_in_views(self):
        """Phase 9 Commit M migrated every caller. Future commits must
        not reintroduce calls to the underscored shims from
        ``core/views/`` — new code should import from ``core.access``.
        """
        import os
        import re
        offenders = []
        for root, _, files in os.walk("core/views"):
            for fn in files:
                if not fn.endswith(".py") or fn == "_helpers.py":
                    continue
                path = os.path.join(root, fn)
                src = open(path).read()
                for sym in (
                    "_check_user_project_access",
                    "_require_admin_or_redirect",
                ):
                    if re.search(rf"\b{sym}\b", src):
                        offenders.append(f"{path}: uses {sym}")
        assert not offenders, (
            "Legacy shim regressions detected — migrate new code to "
            "core.access.check_project_access / "
            "core.access.require_admin_or_redirect:\n"
            + "\n".join(offenders)
        )
