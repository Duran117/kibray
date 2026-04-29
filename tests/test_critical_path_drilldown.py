"""
Phase D follow-up — Critical Path drill-down page tests
========================================================

Covers:

* URL routing for ``project_critical_path``.
* Permission gating (staff-only, mirrors ``project_overview``).
* Empty / populated / cycle states all return 200 with the right
  ``data-testid`` hooks.
* ``?critical_only=1`` filters the rendered table.
* Gantt-style bar offsets/widths are derived from the CPM result.
* Overview widget exposes the drill-down link to the new page.
"""

from datetime import date

import pytest
from django.contrib.auth import get_user_model
from django.test import Client as TestClient
from django.urls import reverse

from core.models import Project, Task, TaskDependency

pytestmark = pytest.mark.django_db


# ─── Fixtures ───────────────────────────────────────────────────────


@pytest.fixture
def staff_user(db):
    User = get_user_model()
    return User.objects.create_user(
        username="cpm_staff", password="pw", is_staff=True
    )


@pytest.fixture
def regular_user(db):
    User = get_user_model()
    return User.objects.create_user(
        username="cpm_regular", password="pw", is_staff=False
    )


@pytest.fixture
def project(db):
    return Project.objects.create(
        name="CPM Project",
        client="Client",
        start_date=date.today(),
        address="123 Test",
    )


@pytest.fixture
def chain(project, staff_user):
    """3-task linear chain A → B → C; all should be critical."""
    a = Task.objects.create(
        project=project, title="A", status="Pending", created_by=staff_user
    )
    b = Task.objects.create(
        project=project, title="B", status="Pending", created_by=staff_user
    )
    c = Task.objects.create(
        project=project, title="C", status="Pending", created_by=staff_user
    )
    TaskDependency.objects.create(task=b, predecessor=a, type="FS")
    TaskDependency.objects.create(task=c, predecessor=b, type="FS")
    return a, b, c


def _login(staff_user):
    c = TestClient()
    c.login(username="cpm_staff", password="pw")
    return c


# ─── Routing & permission ──────────────────────────────────────────


class TestRoutingAndPermissions:
    def test_url_resolves(self, project):
        url = reverse(
            "project_critical_path", kwargs={"project_id": project.id}
        )
        assert url == f"/projects/{project.id}/critical-path/"

    def test_anonymous_redirected_to_login(self, project):
        c = TestClient()
        url = reverse(
            "project_critical_path", kwargs={"project_id": project.id}
        )
        resp = c.get(url)
        assert resp.status_code == 302
        assert "/login" in resp["Location"]

    def test_non_staff_redirected(self, project, regular_user):
        c = TestClient()
        c.login(username="cpm_regular", password="pw")
        resp = c.get(
            reverse("project_critical_path", kwargs={"project_id": project.id})
        )
        # Helper redirects to dashboard_employee for non-staff
        assert resp.status_code == 302

    def test_staff_gets_200(self, project, staff_user):
        c = _login(staff_user)
        resp = c.get(
            reverse("project_critical_path", kwargs={"project_id": project.id})
        )
        assert resp.status_code == 200

    def test_unknown_project_404(self, staff_user):
        c = _login(staff_user)
        resp = c.get(
            reverse("project_critical_path", kwargs={"project_id": 999_999})
        )
        assert resp.status_code == 404


# ─── Empty / populated / cycle states ──────────────────────────────


class TestRenderStates:
    def test_empty_project_renders_placeholder(self, project, staff_user):
        c = _login(staff_user)
        resp = c.get(
            reverse("project_critical_path", kwargs={"project_id": project.id})
        )
        assert resp.status_code == 200
        body = resp.content.decode()
        assert 'data-testid="cpm-empty"' in body
        assert 'data-testid="cpm-table"' not in body
        assert resp.context["task_count"] == 0
        assert resp.context["critical_count"] == 0

    def test_chain_renders_full_table(self, project, staff_user, chain):
        a, b, c_task = chain
        c = _login(staff_user)
        resp = c.get(
            reverse("project_critical_path", kwargs={"project_id": project.id})
        )
        assert resp.status_code == 200
        body = resp.content.decode()
        assert 'data-testid="cpm-table"' in body
        # 3 rows + critical badges (all 3 on the chain are critical)
        assert body.count('data-testid="cpm-row"') == 3
        assert body.count('data-testid="cpm-critical-badge"') == 3
        assert resp.context["task_count"] == 3
        assert resp.context["critical_count"] == 3

    def test_chain_renders_gantt_bars(self, project, staff_user, chain):
        c = _login(staff_user)
        resp = c.get(
            reverse("project_critical_path", kwargs={"project_id": project.id})
        )
        body = resp.content.decode()
        assert 'data-testid="cpm-gantt"' in body
        assert body.count('data-testid="cpm-gantt-row"') == 3
        # Bars should have non-decreasing offsets along the chain
        bars = resp.context["bars"]
        offsets = [b["offset_pct"] for b in bars]
        assert offsets == sorted(offsets)
        # All chain tasks are critical → CSS class present
        assert all(b["is_critical"] for b in bars)

    def test_critical_only_filter_excludes_non_critical(
        self, project, staff_user, chain
    ):
        a, b, c_task = chain
        # Add a parallel task with no dependencies — it gets ES=0,LF=project_finish
        # so it actually becomes critical too. Use a dependency to force slack.
        d = Task.objects.create(
            project=project, title="D-side", status="Pending", created_by=staff_user
        )
        # D depends on A but nothing depends on D → D will have slack
        TaskDependency.objects.create(task=d, predecessor=a, type="FS")
        c = _login(staff_user)
        resp_all = c.get(
            reverse("project_critical_path", kwargs={"project_id": project.id})
        )
        resp_crit = c.get(
            reverse("project_critical_path", kwargs={"project_id": project.id})
            + "?critical_only=1"
        )
        body_all = resp_all.content.decode()
        body_crit = resp_crit.content.decode()
        # All-view shows D
        assert "D-side" in body_all
        # Critical-only view excludes D
        assert "D-side" not in body_crit
        # Toggle link flips
        assert 'data-testid="cpm-toggle-critical"' in body_all
        assert 'data-testid="cpm-toggle-all"' in body_crit

    def test_cycle_returns_friendly_error(self, project, staff_user, monkeypatch):
        from core.services import critical_path as cp_mod

        def boom(project_id, **kw):
            raise cp_mod.CriticalPathCycleError("synthetic cycle")

        monkeypatch.setattr(cp_mod, "compute_critical_path", boom)
        c = _login(staff_user)
        resp = c.get(
            reverse("project_critical_path", kwargs={"project_id": project.id})
        )
        assert resp.status_code == 200
        body = resp.content.decode()
        assert 'data-testid="cpm-cycle-error"' in body
        assert resp.context["cpm_error"] is not None
        assert resp.context["task_count"] == 0


# ─── Overview widget link ───────────────────────────────────────────


class TestOverviewLink:
    def test_overview_widget_links_to_drilldown(self, project, staff_user):
        c = _login(staff_user)
        resp = c.get(reverse("project_overview", kwargs={"project_id": project.id}))
        assert resp.status_code == 200
        body = resp.content.decode()
        assert 'data-testid="cp-drilldown-link"' in body
        expected = reverse(
            "project_critical_path", kwargs={"project_id": project.id}
        )
        assert expected in body
