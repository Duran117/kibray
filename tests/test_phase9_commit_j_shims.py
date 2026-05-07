"""
Phase 9 Commit J — equivalence tests for the deprecation shims.

After Commit J, the legacy role helpers in
``core.views._helpers`` and the ``is_staffish`` utility in
``core.security_decorators`` are thin shims that delegate to
``core.access``. This suite **locks in the equivalence forever**:
if anyone changes the canonical layer or the shim and the two go
out of sync, these tests fail loudly.

Coverage:
  - ``_is_admin_user(u)`` ≡ ``is_admin(u) or u.is_staff``
  - ``_is_staffish(u)``  ≡ ``is_admin(u) or is_pm(u) or u.is_staff``
  - ``_is_pm_or_admin(u)`` ≡ ``_is_staffish(u)``
  - ``security_decorators.is_staffish(u)`` ≡ same as above
  - ``_check_user_project_access(u, p)`` returns (True, None) iff
    ``can_view_project(u, p)`` is True (after assigned_to fallback).

We exercise every Phase 9 role × every relevant project-access
configuration to catch any drift between the canonical layer and
the shims.
"""
from __future__ import annotations

from datetime import date

import pytest
from django.contrib.auth import get_user_model

from core.access import (
    can_view_project,
    is_admin,
    is_pm,
)
from core.models import (
    ClientProjectAccess,
    Employee,
    Project,
    ProjectManagerAssignment,
    TimeEntry,
)
from core.security_decorators import is_staffish as sd_is_staffish
from core.views._helpers import (
    _check_user_project_access,
    _is_admin_user,
    _is_pm_or_admin,
    _is_staffish,
)

User = get_user_model()


pytestmark = pytest.mark.django_db


@pytest.fixture
def users():
    """One user per relevant Phase 9 role configuration."""
    out = {}

    # Anonymous-ish (we use AnonymousUser separately)
    out["admin"] = User.objects.create_user(
        "j_admin", "j_admin@x", "x", is_staff=True, is_superuser=True,
    )
    out["admin"].profile.role = "admin"
    out["admin"].profile.save()

    out["staff_only"] = User.objects.create_user(
        "j_staff", "j_staff@x", "x", is_staff=True,
    )
    # default profile.role = 'employee' from post_save signal
    out["staff_only"].profile.role = "employee"
    out["staff_only"].profile.save()

    out["pm"] = User.objects.create_user("j_pm", "j_pm@x", "x")
    out["pm"].profile.role = "project_manager"
    out["pm"].profile.save()

    out["employee"] = User.objects.create_user("j_emp", "j_emp@x", "x")
    out["employee"].profile.role = "employee"
    out["employee"].profile.save()

    out["client"] = User.objects.create_user("j_client", "j_client@x", "x")
    out["client"].profile.role = "client"
    out["client"].profile.save()

    out["owner"] = User.objects.create_user("j_owner", "j_owner@x", "x")
    out["owner"].profile.role = "owner"
    out["owner"].profile.save()

    out["designer"] = User.objects.create_user("j_design", "j_design@x", "x")
    out["designer"].profile.role = "designer"
    out["designer"].profile.save()

    return out


# ─── _is_admin_user ──────────────────────────────────────────────────
class TestIsAdminUserShim:
    """``_is_admin_user`` ≡ ``is_admin(u) or u.is_staff``."""

    @pytest.mark.parametrize("role_key,expected", [
        ("admin", True),       # superuser=True → is_admin=True
        ("staff_only", True),  # is_staff=True → shim accepts
        ("pm", False),
        ("employee", False),
        ("client", False),
        ("owner", False),
        ("designer", False),
    ])
    def test_matches_canonical_or_staff(self, users, role_key, expected):
        u = users[role_key]
        canonical = is_admin(u) or bool(u.is_staff)
        assert _is_admin_user(u) == expected
        assert _is_admin_user(u) == canonical, (
            f"Shim/canonical drift for {role_key}: "
            f"shim={_is_admin_user(u)} canonical={canonical}"
        )


# ─── _is_staffish / _is_pm_or_admin / sd_is_staffish ─────────────────
class TestStaffishShims:
    """All three legacy 'staffish' aliases must agree, and must equal
    ``is_admin(u) or is_pm(u) or u.is_staff``.
    """

    @pytest.mark.parametrize("role_key,expected", [
        ("admin", True),       # superuser+is_staff
        ("staff_only", True),  # is_staff alone qualifies
        ("pm", True),          # PM role qualifies
        ("employee", False),
        ("client", False),
        ("owner", False),      # 'owner' is NOT in the legacy staffish set
        ("designer", False),
    ])
    def test_legacy_staffish_truth_table(self, users, role_key, expected):
        u = users[role_key]
        assert _is_staffish(u) == expected
        assert _is_pm_or_admin(u) == expected
        assert sd_is_staffish(u) == expected

    def test_all_three_aliases_agree_for_every_user(self, users):
        for key, u in users.items():
            a = _is_staffish(u)
            b = _is_pm_or_admin(u)
            c = sd_is_staffish(u)
            assert a == b == c, (
                f"Staffish aliases disagree for {key}: "
                f"_is_staffish={a} _is_pm_or_admin={b} sd.is_staffish={c}"
            )

    def test_matches_canonical_composition(self, users):
        for key, u in users.items():
            canonical = is_admin(u) or is_pm(u) or bool(u.is_staff)
            assert _is_staffish(u) == canonical, (
                f"Shim/canonical drift for {key}: "
                f"shim={_is_staffish(u)} canonical={canonical}"
            )


# ─── _check_user_project_access ──────────────────────────────────────
class TestCheckUserProjectAccessShim:
    """``_check_user_project_access(u, p)`` returns (True, None) iff
    the user can canonically view the project (or matches the legacy
    assigned_to back-compat).
    """

    @pytest.fixture
    def world(self, users):
        p = Project.objects.create(name="J-World", start_date=date.today())
        # PM assignment for j_pm
        ProjectManagerAssignment.objects.create(
            project=p, pm=users["pm"], role="pm",
        )
        # Employee with a TimeEntry on p
        emp = Employee.objects.create(
            user=users["employee"], first_name="J", last_name="Emp",
            social_security_number="J-1-1", hourly_rate=20,
        )
        TimeEntry.objects.create(
            employee=emp, project=p, date=date.today(), start_time="08:00",
        )
        # Client with explicit access to p
        ClientProjectAccess.objects.create(
            user=users["client"], project=p, role="viewer", is_active=True,
        )
        # An UNRELATED project nobody but admin should reach
        p_other = Project.objects.create(
            name="J-World-Other", start_date=date.today(),
        )
        return {"p": p, "p_other": p_other}

    @pytest.mark.parametrize("role_key,project_key,expected_ok", [
        # Admin reaches everything
        ("admin", "p", True),
        ("admin", "p_other", True),
        # Staff-only reaches everything (via is_staff)
        ("staff_only", "p", True),
        ("staff_only", "p_other", True),
        # PM reaches assigned project, NOT unrelated
        ("pm", "p", True),
        ("pm", "p_other", False),
        # Employee reaches project they have time on, NOT others
        ("employee", "p", True),
        ("employee", "p_other", False),
        # Client reaches their explicit-access project, NOT others
        ("client", "p", True),
        ("client", "p_other", False),
        # Internal roles (designer/owner/superintendent) currently default to
        # full project access per core.access.can_view_project — this is the
        # documented Phase 9 behavior ("default; tighten when business rules
        # clarify"). The shim must mirror it exactly.
        ("designer", "p", True),
        ("designer", "p_other", True),
        ("owner", "p", True),
        ("owner", "p_other", True),
    ])
    def test_truth_table_matches_can_view_project(
        self, users, world, role_key, project_key, expected_ok,
    ):
        u = users[role_key]
        p = world[project_key]
        ok, redirect_name = _check_user_project_access(u, p)
        # Boolean must match expectation.
        assert ok == expected_ok, (
            f"{role_key} @ {project_key}: shim={ok} expected={expected_ok}"
        )
        # When denied, redirect must be role-aware.
        if not ok:
            from core.access import is_client
            assert redirect_name == ("dashboard_client" if is_client(u) else "dashboard")
        else:
            assert redirect_name is None

    def test_shim_strictly_implies_canonical_for_all_users(self, users, world):
        """If the shim says True (and the user isn't an assigned_to
        back-compat hit), the canonical layer must also say True.
        Catches accidental widening.
        """
        for key, u in users.items():
            for pk in ("p", "p_other"):
                p = world[pk]
                ok, _ = _check_user_project_access(u, p)
                if ok and not (
                    hasattr(p, "assigned_to")
                    and p.assigned_to.filter(id=u.id).exists()
                ):
                    assert can_view_project(u, p), (
                        f"Shim widened access for {key} @ {pk}: "
                        "shim says OK but canonical disagrees"
                    )


# ─── Deprecation banners are present ─────────────────────────────────
class TestDeprecationBannersPresent:
    """Lock in the docstring banners so future readers know to migrate."""

    def test_helpers_banners(self):
        from core.views import _helpers as h
        for name in (
            "_is_admin_user", "_is_staffish", "_is_pm_or_admin",
            "_check_user_project_access", "_require_admin_or_redirect",
            "_require_roles",
        ):
            doc = getattr(h, name).__doc__ or ""
            assert "DEPRECATED" in doc, (
                f"{name} missing DEPRECATED banner — Phase 9 Commit J "
                "requires every shim to be marked for migration."
            )

    def test_security_decorators_banners(self):
        from core import security_decorators as sd
        for name in ("is_staffish", "require_role", "require_project_access"):
            doc = getattr(sd, name).__doc__ or ""
            assert "DEPRECATED" in doc, (
                f"security_decorators.{name} missing DEPRECATED banner."
            )
