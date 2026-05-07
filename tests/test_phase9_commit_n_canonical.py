"""Phase 9 Commit N — equivalence tests for the new canonical
narrow staff predicate ``core.access.is_admin_or_pm``.

Commit N promoted the post-Commit-J shims ``_is_staffish`` and
``_is_pm_or_admin`` (in ``core/views/_helpers.py``) plus the
top-level ``is_staffish`` utility in ``core/security_decorators.py``
to a single canonical implementation:

  * ``core.access.is_admin_or_pm(user) -> bool``

This predicate is **NARROWER** than ``core.access.is_staffish``:
``is_admin_or_pm`` deliberately excludes ``ROLE_OWNER``. That
distinction is load-bearing — 58 call sites across 8 view files
silently rely on owners NOT being treated as staff for things
like financial reviews, change-order approvals, daily-plan
edits and payroll. These tests lock that contract in.
"""
from __future__ import annotations

import os
import re

import pytest
from django.contrib.auth import get_user_model

from core.access import is_admin_or_pm, is_staffish
from core.security_decorators import is_staffish as sec_is_staffish
from core.views._helpers import _is_pm_or_admin, _is_staffish

User = get_user_model()
pytestmark = pytest.mark.django_db


# ─── Fixtures ────────────────────────────────────────────────────────
@pytest.fixture
def users():
    out = {}

    out["admin"] = User.objects.create_user(
        "n_admin", "a@x", "x", is_staff=True, is_superuser=True,
    )
    out["admin"].profile.role = "admin"
    out["admin"].profile.save()

    out["staff_only"] = User.objects.create_user(
        "n_staff", "s@x", "x", is_staff=True,
    )
    out["staff_only"].profile.role = "employee"
    out["staff_only"].profile.save()

    out["pm"] = User.objects.create_user("n_pm", "pm@x", "x")
    out["pm"].profile.role = "project_manager"
    out["pm"].profile.save()

    out["owner"] = User.objects.create_user("n_owner", "o@x", "x")
    out["owner"].profile.role = "owner"
    out["owner"].profile.save()

    out["employee"] = User.objects.create_user("n_emp", "e@x", "x")
    out["employee"].profile.role = "employee"
    out["employee"].profile.save()

    out["client"] = User.objects.create_user("n_client", "c@x", "x")
    out["client"].profile.role = "client"
    out["client"].profile.save()

    out["designer"] = User.objects.create_user("n_des", "d@x", "x")
    out["designer"].profile.role = "designer"
    out["designer"].profile.save()

    return out


# ─── is_admin_or_pm canonical truth table ────────────────────────────
class TestIsAdminOrPmCanonical:

    @pytest.mark.parametrize("role,expected", [
        ("admin", True),
        ("staff_only", True),  # is_staff alone passes
        ("pm", True),
        ("owner", False),       # ← THE WHOLE POINT OF COMMIT N
        ("employee", False),
        ("client", False),
        ("designer", False),
    ])
    def test_truth_table(self, users, role, expected):
        assert is_admin_or_pm(users[role]) is expected

    def test_anonymous_is_false(self):
        from django.contrib.auth.models import AnonymousUser
        assert is_admin_or_pm(AnonymousUser()) is False

    def test_none_is_false(self):
        assert is_admin_or_pm(None) is False


# ─── Lock in the semantic gap from is_staffish ───────────────────────
class TestIsStaffishVsIsAdminOrPmDifference:
    """``is_staffish`` and ``is_admin_or_pm`` are NOT aliases.
    The single point of divergence is ROLE_OWNER. Lock it in.
    """

    def test_owner_is_staffish_but_not_admin_or_pm(self, users):
        owner = users["owner"]
        assert is_staffish(owner) is True
        assert is_admin_or_pm(owner) is False

    @pytest.mark.parametrize("role", [
        "admin", "staff_only", "pm",
        "employee", "client", "designer",
    ])
    def test_agree_for_every_other_role(self, users, role):
        u = users[role]
        assert is_staffish(u) == is_admin_or_pm(u)


# ─── Shim equivalence ────────────────────────────────────────────────
class TestShimEquivalence:
    """All three forwarders must equal the canonical for every role."""

    @pytest.mark.parametrize("role", [
        "admin", "staff_only", "pm", "owner",
        "employee", "client", "designer",
    ])
    def test_helpers_is_staffish_equals_canonical(self, users, role):
        u = users[role]
        assert _is_staffish(u) == is_admin_or_pm(u)

    @pytest.mark.parametrize("role", [
        "admin", "staff_only", "pm", "owner",
        "employee", "client", "designer",
    ])
    def test_helpers_is_pm_or_admin_equals_canonical(self, users, role):
        u = users[role]
        assert _is_pm_or_admin(u) == is_admin_or_pm(u)

    @pytest.mark.parametrize("role", [
        "admin", "staff_only", "pm", "owner",
        "employee", "client", "designer",
    ])
    def test_security_decorators_is_staffish_equals_canonical(
        self, users, role,
    ):
        u = users[role]
        assert sec_is_staffish(u) == is_admin_or_pm(u)


# ─── Public API surface guardrail ────────────────────────────────────
class TestPublicApiSurface:

    def test_canonical_in_access_dunder_all(self):
        import core.access as access
        assert "is_admin_or_pm" in access.__all__

    def test_no_remaining_legacy_staffish_callers_in_views(self):
        """Once Commit N is merged, no file under core/views/ may
        call ``_is_staffish`` or ``_is_pm_or_admin`` (except the
        shims themselves and ``staff_required`` decorator, both in
        ``_helpers.py``). This test prevents regressions.
        """
        offenders: list[tuple[str, int, str]] = []
        pattern = re.compile(r"\b_is_staffish\b|\b_is_pm_or_admin\b")
        for root, _dirs, files in os.walk("core/views"):
            for fn in files:
                if not fn.endswith(".py"):
                    continue
                path = os.path.join(root, fn)
                if os.path.basename(path) == "_helpers.py":
                    continue  # shim definitions live here
                with open(path) as f:
                    for lineno, line in enumerate(f, 1):
                        if pattern.search(line):
                            offenders.append((path, lineno, line.rstrip()))

        assert not offenders, (
            "Phase 9 Commit N regression: legacy staffish helpers "
            "found in core/views/. Use core.access.is_admin_or_pm "
            "instead.\n"
            + "\n".join(f"  {p}:{ln}: {src}" for p, ln, src in offenders)
        )
