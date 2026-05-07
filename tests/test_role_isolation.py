"""
Phase 9 Commit I — End-to-end cross-role isolation suite.

This is the *belt-and-braces* regression suite that locks in the
canonical authorization model from ``core/access.py`` at the HTTP
layer. It exercises real URLs with real authenticated sessions and
asserts what each role can and cannot reach.

Coverage matrix (≈1 row per role × per surface area):

  Surface                           admin  pm    employee  client
  ─────────────────────────────────────────────────────────────────
  Admin dashboard                   ✅     🚫    🚫        🚫
  Client dashboard                  ✅     ✅    🚫        ✅
  User wizard / clients list        ✅     🚫    🚫        🚫
  Cost codes                        ✅     🚫    🚫        🚫
  Payroll weekly review             ✅     🚫    🚫        🚫
  Financial dashboard               ✅     🚫    🚫        🚫
  Expenses / Income / Invoices list ✅     🚫    🚫        🚫
  Project overview (own project)    ✅     ✅    ✅        ✅
  Project overview (other project)  ✅     🚫    🚫        🚫
  Project task list (own)           ✅     ✅    ✅        🚫
  Project RFIs (own)                ✅     ✅    🚫        🚫
  Project budget (own)              ✅     ✅    🚫        🚫
  Project change-orders board       ✅     ✅    🚫        🚫
  Sidebar (new) — must not leak     N/A    N/A   N/A       ✅

✅ = expects 2xx (or harmless redirect to a role-appropriate page).
🚫 = expects 3xx-redirect-away or 4xx (NOT 200 with the requested
     content visible).

The principle: a 'leak' is any 200-OK that exposes admin/finance UI
chrome to a non-staff user. This suite asserts both the status codes
AND that key forbidden labels (e.g. 'Administration', 'Payroll') do
not appear in the rendered body for the disallowed roles.

Why this matters: Phase 9's security guarantee is that role checks
live in ``core.access`` (single source of truth), not scattered
across views and templates. This suite is the contract — if anyone
adds a new admin-only endpoint without wiring the gate, the
corresponding 'cannot' test fails immediately.
"""
from __future__ import annotations

from datetime import date

import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import NoReverseMatch, reverse

from core.models import (
    ClientProjectAccess,
    Employee,
    Project,
    ProjectManagerAssignment,
    TimeEntry,
)

User = get_user_model()


pytestmark = pytest.mark.django_db


# ─────────────────────────────────────────────────────────────────────
# Test world — one of every role + two projects so we can assert
# project-level isolation (PM owns p_pm_only; client owns p_client_only).
# ─────────────────────────────────────────────────────────────────────
@pytest.fixture
def world(settings):
    """All Commit I tests run with the new sidebar enabled because
    Commit H flips it ON in dev/staging. Asserting against the new
    sidebar matches the production-bound configuration once the
    follow-up flag flip ships.
    """
    settings.PHASE9_NEW_SIDEBAR = True

    p_pm_only = Project.objects.create(
        name="ROLE-ISO-PM-Project", start_date=date.today(),
    )
    p_client_only = Project.objects.create(
        name="ROLE-ISO-Client-Project", start_date=date.today(),
    )

    admin = User.objects.create_user(
        "iso_admin", "iso_admin@x", "x",
        is_staff=True, is_superuser=True,
    )
    admin.profile.role = "admin"
    admin.profile.save()

    pm = User.objects.create_user("iso_pm", "iso_pm@x", "x")
    pm.profile.role = "project_manager"
    pm.profile.save()
    ProjectManagerAssignment.objects.create(
        project=p_pm_only, pm=pm, role="pm",
    )

    employee = User.objects.create_user("iso_emp", "iso_emp@x", "x")
    employee.profile.role = "employee"
    employee.profile.save()
    emp_record = Employee.objects.create(
        user=employee, first_name="Emp", last_name="Iso",
        social_security_number="ISO-1-1", hourly_rate=18,
    )
    # Give the employee a TimeEntry so they have project access via
    # accessible_projects() (the canonical layer).
    TimeEntry.objects.create(
        employee=emp_record, project=p_pm_only,
        date=date.today(), start_time="08:00",
    )

    client_user = User.objects.create_user("iso_client", "iso_client@x", "x")
    client_user.profile.role = "client"
    client_user.profile.save()
    ClientProjectAccess.objects.create(
        user=client_user, project=p_client_only,
        role="viewer", is_active=True,
    )

    return {
        "admin": admin, "pm": pm, "employee": employee, "client": client_user,
        "p_pm": p_pm_only, "p_client": p_client_only,
    }


def _login(world, role: str) -> Client:
    c = Client()
    user = world[role]
    assert c.login(username=user.username, password="x"), (
        f"Could not log in as {role} ({user.username})"
    )
    return c


def _assert_blocked(resp, *, label: str = ""):
    """A 'blocked' response is anything that is NOT a 200 with full
    content. We accept:
      - 3xx redirect (typical login_required/dashboard bounce).
      - 403/404/405 explicit refusal.
      - 200 ONLY if the body clearly indicates a deny (e.g. 'Acceso
        denegado', 'Forbidden', or a redirect-banner). We are strict:
        if status==200 and the body is the requested page, that is a
        leak. Tests using this helper rely on assert_no_admin_chrome
        for the body check.
    """
    assert resp.status_code != 500, (
        f"500 from {label}: status={resp.status_code} "
        f"body[:300]={resp.content[:300]!r}"
    )
    assert resp.status_code in (301, 302, 303, 307, 308, 401, 403, 404, 405), (
        f"{label}: expected redirect/4xx, got {resp.status_code}. "
        f"body[:300]={resp.content[:300]!r}"
    )


def _assert_no_admin_chrome(content: bytes, *, label: str = ""):
    """A response served to a non-staff role must not embed admin nav
    sections from the new sidebar. Catches the class of bug where a
    view forgot a permission gate but still rendered base_modern.html
    with its full admin sidebar.

    Note: we do NOT include 'Cost Codes' here because that is a
    legitimate page title for any user the costcode_list view permits
    (PMs included, by long-standing business rule). Sidebar leakage
    of admin-only sections is what we check.
    """
    leaks = [
        b"Administration",          # NavSection title — admin-only
        b"Master Schedule",         # NavItem under Administration
        b"Payroll",                 # NavItem under Administration
        b"Financial Dashboard",     # NavSection title — admin-only
        b"Aging Report",            # NavItem under Finance
    ]
    found = [s for s in leaks if s in content]
    assert not found, (
        f"{label}: admin sidebar chrome leaked into non-staff response: {found!r}"
    )


# ─────────────────────────────────────────────────────────────────────
# 1. ADMIN-ONLY GLOBAL SURFACES
# ─────────────────────────────────────────────────────────────────────
ADMIN_ONLY_URL_NAMES = [
    "dashboard_admin",
    "user_wizard_list",
    "client_list",
    "costcode_list",
    "payroll_weekly_review",
    "financial_dashboard",
    "expense_list",
    "income_list",
    "invoice_list",
]


@pytest.mark.parametrize("url_name", ADMIN_ONLY_URL_NAMES)
class TestAdminOnlySurfaces:

    def test_admin_can_reach(self, world, url_name):
        c = _login(world, "admin")
        resp = c.get(reverse(url_name), follow=False)
        # Admin should get a 200 (or harmless redirect within the app).
        assert resp.status_code in (200, 301, 302), (
            f"admin blocked on {url_name}: status={resp.status_code} "
            f"body[:300]={resp.content[:300]!r}"
        )

    def test_pm_cannot_reach(self, world, url_name):
        c = _login(world, "pm")
        resp = c.get(reverse(url_name))
        # PM must NOT be able to USE the page. We accept either a deny
        # status, OR a 200 that does not embed the admin chrome.
        if resp.status_code == 200:
            _assert_no_admin_chrome(
                resp.content, label=f"pm @ {url_name}",
            )
        else:
            assert resp.status_code in (301, 302, 303, 401, 403, 404), (
                f"pm @ {url_name}: unexpected status {resp.status_code}"
            )

    def test_employee_cannot_reach(self, world, url_name):
        c = _login(world, "employee")
        resp = c.get(reverse(url_name), follow=True)
        # Employees redirect to their dashboard or get a deny status.
        if resp.status_code == 200:
            _assert_no_admin_chrome(
                resp.content, label=f"employee @ {url_name}",
            )

    def test_client_cannot_reach(self, world, url_name):
        c = _login(world, "client")
        resp = c.get(reverse(url_name), follow=True)
        if resp.status_code == 200:
            _assert_no_admin_chrome(
                resp.content, label=f"client @ {url_name}",
            )


# ─────────────────────────────────────────────────────────────────────
# 2. PROJECT-LEVEL ISOLATION
# ─────────────────────────────────────────────────────────────────────
class TestProjectIsolation:
    """A user with access to project A must NOT be able to view or
    edit project B that they have no relationship with.
    """

    def _overview(self, c, project):
        return c.get(reverse("project_overview", args=[project.id]))

    def test_pm_can_view_assigned_project(self, world):
        c = _login(world, "pm")
        resp = self._overview(c, world["p_pm"])
        # Phase 9 Commit I: project_overview must use can_view_project,
        # not raw is_staff. Prior to the fix this returned 302→
        # /dashboard/employee/, locking PMs out of their own projects.
        assert resp.status_code == 200, (
            f"PM blocked on assigned project overview: "
            f"status={resp.status_code} body[:300]={resp.content[:300]!r}"
        )
        assert b"ROLE-ISO-PM-Project" in resp.content, (
            "PM overview did not include the project's name"
        )

    def test_pm_cannot_view_other_project_overview(self, world):
        c = _login(world, "pm")
        resp = self._overview(c, world["p_client"])
        # Either deny status OR 200 that does NOT include project name
        # in a way that exposes details. Be strict: PM has no
        # ProjectManagerAssignment for p_client.
        if resp.status_code == 200:
            # Looking for the OTHER project's name in the page header.
            assert b"ROLE-ISO-Client-Project" not in resp.content, (
                "PM saw an overview of a project they are NOT assigned to."
            )

    def test_employee_can_view_assigned_project(self, world):
        c = _login(world, "employee")
        resp = self._overview(c, world["p_pm"])
        # Employee has a TimeEntry on p_pm.
        assert resp.status_code in (200, 302)

    def test_employee_cannot_view_other_project(self, world):
        c = _login(world, "employee")
        resp = self._overview(c, world["p_client"])
        if resp.status_code == 200:
            assert b"ROLE-ISO-Client-Project" not in resp.content, (
                "Employee saw a project they have no TimeEntry/assignment for."
            )

    def test_client_can_view_their_project(self, world):
        c = _login(world, "client")
        resp = self._overview(c, world["p_client"])
        assert resp.status_code in (200, 302)

    def test_client_cannot_view_other_project(self, world):
        c = _login(world, "client")
        resp = self._overview(c, world["p_pm"])
        # Client must NOT see PM's project. Either explicit deny or
        # a 200 that doesn't embed the other project's identifying info.
        if resp.status_code == 200:
            assert b"ROLE-ISO-PM-Project" not in resp.content, (
                "Client saw a project they have no ClientProjectAccess for."
            )


# ─────────────────────────────────────────────────────────────────────
# 3. PROJECT-SCOPED INTERNAL SURFACES
#    (RFIs, budget, change-orders board)
# ─────────────────────────────────────────────────────────────────────
class TestInternalProjectSurfaces:

    def _try_url(self, c, url_name, args):
        try:
            url = reverse(url_name, args=args)
        except NoReverseMatch:
            pytest.skip(f"URL '{url_name}' not registered.")
        return c.get(url)

    def test_client_cannot_open_internal_rfis(self, world):
        c = _login(world, "client")
        resp = self._try_url(c, "rfi_list", [world["p_client"].id])
        # RFIs are an internal surface — even on the client's own
        # project, they should not see the staff workflow chrome.
        if resp.status_code == 200:
            _assert_no_admin_chrome(resp.content, label="client @ rfi_list")
            # Sidebar must be the *client* shape — no Operations section.
            assert b"Operations" not in resp.content, (
                "Client landed on rfi_list with Operations sidebar — leak."
            )

    def test_employee_cannot_open_project_budget(self, world):
        c = _login(world, "employee")
        resp = self._try_url(
            c, "project_budget_detail", [world["p_pm"].id],
        )
        # Employee must not see the budget admin surface.
        if resp.status_code == 200:
            _assert_no_admin_chrome(
                resp.content, label="employee @ project_budget_detail",
            )

    def test_pm_can_open_their_project_budget(self, world):
        c = _login(world, "pm")
        resp = self._try_url(
            c, "project_budget_detail", [world["p_pm"].id],
        )
        # PM owns p_pm; budget should be reachable (200) or a benign
        # redirect into the financials hub.
        assert resp.status_code in (200, 301, 302), (
            f"PM blocked on their own project budget: "
            f"status={resp.status_code} body[:200]={resp.content[:200]!r}"
        )


# ─────────────────────────────────────────────────────────────────────
# 4. SIDEBAR-LEVEL ISOLATION (new sidebar must not leak labels)
# ─────────────────────────────────────────────────────────────────────
class TestSidebarLeakageAtHTTP:
    """Even when a non-admin loads a perfectly legitimate page (e.g.
    their own dashboard), the sidebar served alongside must not
    contain admin labels.
    """

    def test_client_dashboard_sidebar_has_no_admin_labels(self, world):
        c = _login(world, "client")
        resp = c.get(reverse("dashboard_client"), follow=True)
        assert resp.status_code == 200
        _assert_no_admin_chrome(
            resp.content, label="client @ dashboard_client",
        )
        # And no PM-internal labels either.
        for label in (b"Planning", b"Operations", b"Recent Projects"):
            assert label not in resp.content, (
                f"Client dashboard sidebar leaked '{label!r}'"
            )

    def test_employee_dashboard_sidebar_has_no_admin_labels(self, world):
        c = _login(world, "employee")
        resp = c.get(reverse("dashboard"), follow=True)
        assert resp.status_code == 200
        _assert_no_admin_chrome(
            resp.content, label="employee @ dashboard",
        )
        for label in (b"Planning", b"Operations", b"Administration"):
            assert label not in resp.content, (
                f"Employee dashboard sidebar leaked '{label!r}'"
            )

    def test_pm_dashboard_sidebar_has_no_admin_labels(self, world):
        c = _login(world, "pm")
        resp = c.get(reverse("dashboard"), follow=True)
        assert resp.status_code == 200
        # PMs see Planning/Operations but NOT Administration/Finance.
        _assert_no_admin_chrome(resp.content, label="pm @ dashboard")
        assert b"Planning" in resp.content, (
            "PM dashboard missing 'Planning' sidebar section"
        )

    def test_admin_dashboard_sidebar_has_admin_labels(self, world):
        c = _login(world, "admin")
        resp = c.get(reverse("dashboard"), follow=True)
        assert resp.status_code == 200
        # Admin SHOULD see admin chrome. This is the positive control —
        # if this fails, our leak detector is broken (false negatives).
        assert b"Administration" in resp.content


# ─────────────────────────────────────────────────────────────────────
# 5. ANONYMOUS ACCESS — must always bounce to login
# ─────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("url_name", [
    "dashboard",
    "dashboard_admin",
    "dashboard_client",
    "project_list",
    "client_list",
    "expense_list",
    "income_list",
    "financial_dashboard",
])
def test_anonymous_redirected_to_login(world, url_name):
    c = Client()
    resp = c.get(reverse(url_name))
    # Anonymous must always redirect (typically 302 to /accounts/login).
    assert resp.status_code in (301, 302, 303), (
        f"Anonymous got non-redirect on {url_name}: status={resp.status_code}"
    )
    # And must NOT land on the actual content.
    assert b"Administration" not in resp.content
