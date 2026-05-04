"""
Sidebar role-leak regression test (Phase 8 — Security).

Reported issue (verbatim from user, translated): when a CLIENT navigates inside
a project (e.g. they click a Daily-Logs link from a notification) the sidebar
shows the *full* operations menu — Daily Plans, Strategic, Tasks, Materials,
Damages, Issues, CO Board, Resident Portal, Financials… — exposing internal
features the client must not see. Backend rejects the actions, but the menu
items themselves leak the existence of those features.

We test the *template* directly by rendering ``core/components/sidebar_dark.html``
with a faked ``request`` that has a logged-in user of a given role + a project
in scope. This isolates the role-gating logic from view-level access checks
(which are tested elsewhere) and lets us cover client / employee / staff in a
fast, deterministic way.
"""
from __future__ import annotations

import pytest
from django.contrib.auth.models import User
from django.template.loader import render_to_string
from django.test import RequestFactory

from core.models import Profile, Project


pytestmark = pytest.mark.django_db


# ── URL fragments that must NEVER appear in a client's sidebar ────────────
CLIENT_FORBIDDEN_URL_FRAGMENTS = [
    "/planning/",                # Daily Plans dashboard (global)
    "/planner/strategic/",       # Strategic Planning
    "/changeorders/board",       # CO Board
    "/touchups-v2/",             # Touch-ups
    "/issues/",                  # Issues
    "/materials/requests/",      # Materials Requests
    "/portal/manage/",           # Resident Portal
    "/financials/",              # Financials Hub / Budget
    "/expenses/",                # Expenses
    "/incomes/",                 # Income
    "/invoices/builder/",        # Invoice builder
    "/schedule/gantt/",          # Gantt
    "/rfis/",                    # RFIs
    "/tasks/",                   # Tasks (internal task list)
    "/damages/",                 # Damages
]

# Same forbidden set for a non-staff employee
EMPLOYEE_FORBIDDEN_URL_FRAGMENTS = [
    "/planning/",
    "/planner/strategic/",
    "/financials/",
    "/expenses/",
    "/incomes/",
    "/invoices/builder/",
    "/changeorders/board",
    "/portal/manage/",
]

# Section titles a client must not see
CLIENT_FORBIDDEN_SECTION_TITLES = [
    "Planificación", "Planning", "Planificación Diaria",
    "Operaciones", "Operations",
    "Órdenes de Cambio", "Change Orders",
    "Financial", "Financiero",
]


# ── Helpers ────────────────────────────────────────────────────────────────
def _make_request(user):
    rf = RequestFactory()
    req = rf.get("/projects/1/daily-log/")
    req.user = user
    req.LANGUAGE_CODE = "en"
    return req


def _render_sidebar(user, project):
    return render_to_string(
        "core/components/sidebar_dark.html",
        {
            "project": project,
            "request": _make_request(user),
            "user": user,
        },
    )


def _make_user(*, username, role, is_staff=False, is_superuser=False):
    u = User.objects.create_user(
        username=username, password="pass1234",
        is_staff=is_staff, is_superuser=is_superuser,
    )
    # post_save signal auto-creates Profile(role='employee'); update to target role.
    Profile.objects.filter(user=u).update(role=role)
    # Bust the cached `.profile` relation so subsequent `u.profile.role` is fresh.
    if hasattr(u, "_profile_cache"):
        del u._profile_cache
    try:
        delattr(u, "profile")
    except AttributeError:
        pass
    return User.objects.get(pk=u.pk)


# ── Fixtures ───────────────────────────────────────────────────────────────
@pytest.fixture
def project(db):
    return Project.objects.create(name="Sidebar Audit Project")


@pytest.fixture
def client_user(db):
    return _make_user(username="sb_client", role="client")


@pytest.fixture
def employee_user(db):
    return _make_user(username="sb_emp", role="employee")


@pytest.fixture
def admin_user(db):
    return _make_user(
        username="sb_admin", role="admin", is_staff=True, is_superuser=True
    )


# ── Tests: CLIENT must not see the operations menu ─────────────────────────
class TestClientSidebarLeakage:
    def test_client_sidebar_hides_forbidden_url_fragments(
        self, client_user, project
    ):
        html = _render_sidebar(client_user, project)
        leaks = [f for f in CLIENT_FORBIDDEN_URL_FRAGMENTS if f in html]
        assert not leaks, (
            f"Client sidebar leaked forbidden URL fragments: {leaks}. "
            "The role-gated branch in sidebar_dark.html is missing or mis-applied."
        )

    def test_client_sidebar_hides_forbidden_section_titles(
        self, client_user, project
    ):
        html = _render_sidebar(client_user, project)
        leaked_titles = [
            t for t in CLIENT_FORBIDDEN_SECTION_TITLES
            if f">{t}<" in html
        ]
        assert not leaked_titles, (
            f"Client sidebar leaked forbidden section titles: {leaked_titles}"
        )

    def test_client_sidebar_includes_minimum_allowed_items(
        self, client_user, project
    ):
        html = _render_sidebar(client_user, project)
        # Items the client SHOULD see for their project
        assert "/daily-log/" in html, "Client must see Daily Logs link."
        assert "/colors/" in html, "Client must see Color Samples (for approval)."
        assert "/files/" in html, "Client must see Project Files."
        assert "/minutes/" in html, "Client must see Meeting Minutes."


# ── Tests: non-staff EMPLOYEE must not see PM/financial items ──────────────
class TestEmployeeSidebarLeakage:
    def test_employee_sidebar_hides_pm_and_financial_links(
        self, employee_user, project
    ):
        html = _render_sidebar(employee_user, project)
        leaks = [f for f in EMPLOYEE_FORBIDDEN_URL_FRAGMENTS if f in html]
        assert not leaks, (
            f"Employee (non-staff) sidebar leaked forbidden URL fragments: {leaks}"
        )

    def test_employee_sidebar_includes_work_items(self, employee_user, project):
        html = _render_sidebar(employee_user, project)
        # Employees DO see their own work items
        assert "/tasks/" in html, "Employee must see Tasks (their work)."
        assert "/files/" in html, "Employee must see project Files."


# ── Sanity: ADMIN sees the full operational menu ───────────────────────────
class TestAdminSidebarFull:
    def test_admin_sees_full_project_menu(self, admin_user, project):
        html = _render_sidebar(admin_user, project)
        # Admin must see all the formerly-leaked items
        assert "/planning/" in html
        assert "/financials/" in html
        assert "/changeorders/board" in html
        assert "/portal/manage/" in html
        assert "/issues/" in html


# ── Anonymous users: not tested directly because every project page is behind
# @login_required; the sidebar is never rendered for an unauthenticated request.
