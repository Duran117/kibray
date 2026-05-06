"""
Phase 9 Commit G — regression tests for core/nav.py role-aware menu builder.

Covers:
  - build_global_nav / build_project_nav per role:
      anonymous, admin, pm, employee, client.
  - Item URL resolution succeeds (or gracefully falls back to '#').
  - Sections are empty for users without permission.
  - phase9_nav context processor:
      * returns {} when flag off (preserves legacy behavior)
      * returns enabled+sections when flag on
      * scopes by request._phase9_project when present.
  - **Negative**: a client building project_nav for a project they
    don't own still gets the *client menu shape* (the caller is
    responsible for the access gate; nav.py only decides shape).
  - **Negative**: anonymous → empty in both global and project nav.
"""
from __future__ import annotations

from datetime import date

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.test import override_settings
from django.test.client import RequestFactory

from core.models import (
    ClientProjectAccess,
    Employee,
    Project,
    ProjectManagerAssignment,
    TimeEntry,
)
from core.nav import (
    NavItem,
    NavSection,
    build_global_nav,
    build_project_nav,
    phase9_nav,
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
def world():
    p_a = Project.objects.create(name="G-Proj-A", start_date=date.today())
    p_b = Project.objects.create(name="G-Proj-B", start_date=date.today())

    admin = _mk("g_admin", role="admin", is_superuser=True, is_staff=True)

    pm = _mk("g_pm", role="project_manager")
    ProjectManagerAssignment.objects.create(project=p_a, pm=pm, role="pm")

    emp = _mk("g_emp", role="employee")
    e = Employee.objects.create(
        user=emp, first_name="E", last_name="G",
        social_security_number="G-9-9", hourly_rate=18,
    )
    TimeEntry.objects.create(
        employee=e, project=p_a, date=date.today(), start_time="08:00",
    )

    client_u = _mk("g_client", role="client")
    ClientProjectAccess.objects.create(
        user=client_u, project=p_b, role="viewer", is_active=True,
    )

    return {
        "p_a": p_a, "p_b": p_b,
        "admin": admin, "pm": pm, "emp": emp, "client": client_u,
    }


# ─────────────── DATACLASSES ───────────────
class TestDataclasses:
    def test_navitem_url_resolves(self):
        item = NavItem("Dashboard", "dashboard", icon="bi-house")
        url = item.url
        assert isinstance(url, str)
        # 'dashboard' is a real URL name; we don't pin the value to
        # avoid coupling tests to URL paths.
        assert url and url != "#"

    def test_navitem_url_unknown_falls_back_to_hash(self):
        item = NavItem("X", "definitely_not_a_real_url_name_x9z")
        assert item.url == "#"

    def test_navitem_external_url_takes_precedence(self):
        item = NavItem("Ext", "dashboard", external_url="https://x.test/")
        assert item.url == "https://x.test/"

    def test_navsection_truthiness(self):
        empty = NavSection("S", [])
        full = NavSection("S", [NavItem("X", "dashboard")])
        assert not empty
        assert full

    def test_navitem_no_url_name(self):
        assert NavItem("Label", url_name=None).url == "#"


# ─────────────── GLOBAL NAV — per role ───────────────
class TestGlobalNav:
    def test_anonymous_returns_empty(self):
        assert build_global_nav(AnonymousUser()) == []

    def test_none_user_returns_empty(self):
        assert build_global_nav(None) == []

    def test_admin_sees_admin_sections(self, db, world):
        sections = build_global_nav(world["admin"])
        titles = [s.title for s in sections]
        # Admin must have at minimum: Home, Planning, Operations, Administration, Finance, Analytics.
        assert "Home" in titles
        assert "Administration" in titles
        assert "Finance" in titles
        assert "Analytics" in titles

    def test_pm_sees_planning_not_admin(self, db, world):
        sections = build_global_nav(world["pm"])
        titles = [s.title for s in sections]
        assert "Home" in titles
        assert "Planning" in titles
        assert "Operations" in titles
        # PM is NOT admin → must NOT see admin sections
        assert "Administration" not in titles
        assert "Finance" not in titles

    def test_employee_sees_minimal_menu(self, db, world):
        sections = build_global_nav(world["emp"])
        titles = [s.title for s in sections]
        # Employee gets Home + their own projects only — no Planning/Admin/etc.
        assert "Home" in titles
        assert "Planning" not in titles
        assert "Administration" not in titles
        assert "Operations" not in titles
        # Their assigned project should appear under "My Projects".
        assert "My Projects" in titles
        my_proj_section = next(s for s in sections if s.title == "My Projects")
        labels = [i.label for i in my_proj_section.items]
        assert world["p_a"].name in labels
        assert world["p_b"].name not in labels  # Not assigned

    def test_client_sees_only_dashboard_and_own_projects(self, db, world):
        sections = build_global_nav(world["client"])
        titles = [s.title for s in sections]
        assert "Home" in titles
        # Client must NOT see Planning/Operations/Administration/Finance.
        for forbidden in ("Planning", "Operations", "Administration", "Finance", "Analytics"):
            assert forbidden not in titles, (
                f"Client must not see '{forbidden}' section; got {titles}"
            )
        # They DO see "My Projects" with only their access.
        assert "My Projects" in titles
        my_proj = next(s for s in sections if s.title == "My Projects")
        labels = [i.label for i in my_proj.items]
        assert world["p_b"].name in labels
        assert world["p_a"].name not in labels

    def test_client_homepage_points_to_dashboard_client(self, db, world):
        sections = build_global_nav(world["client"])
        home = next(s for s in sections if s.title == "Home")
        urls = [i.url_name for i in home.items]
        assert "dashboard_client" in urls
        assert "dashboard" not in urls  # Internal dashboard


# ─────────────── PROJECT NAV — per role ───────────────
class TestProjectNav:
    def test_anonymous_returns_empty(self, db, world):
        assert build_project_nav(AnonymousUser(), world["p_a"]) == []

    def test_none_project_returns_empty(self, db, world):
        assert build_project_nav(world["admin"], None) == []

    def test_admin_sees_full_project_menu(self, db, world):
        sections = build_project_nav(world["admin"], world["p_a"])
        titles = [s.title for s in sections]
        assert "Project" in titles
        assert "Financials" in titles
        assert "Operations" in titles

    def test_pm_sees_full_project_menu(self, db, world):
        sections = build_project_nav(world["pm"], world["p_a"])
        titles = [s.title for s in sections]
        assert "Financials" in titles
        assert "Operations" in titles

    def test_employee_sees_only_basic_project(self, db, world):
        sections = build_project_nav(world["emp"], world["p_a"])
        titles = [s.title for s in sections]
        assert titles == ["Project"]  # No Financials, no Operations
        labels = [i.label for i in sections[0].items]
        # Sensitive items must NOT be in the employee project menu.
        for forbidden in ("Schedule", "RFIs", "Minutes"):
            assert forbidden not in labels

    def test_client_sees_only_client_project(self, db, world):
        sections = build_project_nav(world["client"], world["p_b"])
        titles = [s.title for s in sections]
        assert titles == ["Project"]
        labels = [i.label for i in sections[0].items]
        # Allowed for clients
        assert "Overview" in labels
        assert "Files" in labels
        assert "Color Samples" in labels
        # Forbidden in client menu shape
        for forbidden in ("Schedule", "RFIs", "Tasks", "Damages"):
            assert forbidden not in labels

    def test_client_menu_shape_is_consistent_even_for_other_project(self, db, world):
        """nav.py only decides MENU SHAPE — caller must enforce
        access. So a client passed a project they don't own still
        gets the client menu shape. We pin this so callers aren't
        accidentally relying on nav.py to be a security boundary.
        """
        sections = build_project_nav(world["client"], world["p_a"])
        titles = [s.title for s in sections]
        assert titles == ["Project"]
        labels = [i.label for i in sections[0].items]
        assert "Schedule" not in labels  # client shape, regardless of project


# ─────────────── CONTEXT PROCESSOR ───────────────
class TestPhase9NavContextProcessor:
    def _req(self, user=None):
        rf = RequestFactory()
        req = rf.get("/")
        req.user = user if user is not None else AnonymousUser()
        return req

    @override_settings(PHASE9_NEW_SIDEBAR=False)
    def test_flag_off_returns_empty_dict(self, db, world):
        req = self._req(world["admin"])
        assert phase9_nav(req) == {}

    @override_settings(PHASE9_NEW_SIDEBAR=True)
    def test_anonymous_user_with_flag_on_returns_empty_sections(self):
        req = self._req(None)
        out = phase9_nav(req)
        assert out["phase9_nav_enabled"] is True
        assert out["phase9_nav_sections"] == []

    @override_settings(PHASE9_NEW_SIDEBAR=True)
    def test_admin_request_returns_admin_global_nav(self, db, world):
        req = self._req(world["admin"])
        out = phase9_nav(req)
        assert out["phase9_nav_enabled"] is True
        titles = [s.title for s in out["phase9_nav_sections"]]
        assert "Administration" in titles

    @override_settings(PHASE9_NEW_SIDEBAR=True)
    def test_request_with_phase9_project_uses_project_nav(self, db, world):
        req = self._req(world["client"])
        req._phase9_project = world["p_b"]
        out = phase9_nav(req)
        titles = [s.title for s in out["phase9_nav_sections"]]
        # Project nav for client → only "Project" section
        assert titles == ["Project"]

    @override_settings(PHASE9_NEW_SIDEBAR=True)
    def test_employee_request_excludes_admin_sections(self, db, world):
        req = self._req(world["emp"])
        out = phase9_nav(req)
        titles = [s.title for s in out["phase9_nav_sections"]]
        for forbidden in ("Administration", "Finance", "Analytics", "Planning"):
            assert forbidden not in titles


# ─────────────── REGRESSION: legacy template still default ───────────────
def test_default_settings_keep_legacy_sidebar(settings):
    """Until Commit H, the new sidebar must remain OPT-IN.
    Setting must default to False so production keeps rendering
    sidebar_dark.html.
    """
    # Reload setting from base.py — pytest-django may have overridden it.
    import importlib
    import kibray_backend.settings.base as base
    importlib.reload(base)
    assert base.PHASE9_NEW_SIDEBAR is False, (
        "PHASE9_NEW_SIDEBAR must default OFF until Commit H flips it "
        "after staging QA."
    )
