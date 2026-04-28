"""
Phase D follow-up — Dashboard widgets tests
============================================

Covers:

* ``core.services.dashboard_widgets.get_ev_widget`` — returns latest
  ``EVSnapshot`` summary or ``None``; status badge classification.
* ``core.services.dashboard_widgets.get_critical_path_widget`` — wraps
  ``compute_critical_path`` with cycle/error guards and a preview cap.
* End-to-end: ``project_overview`` view exposes ``ev_widget`` and
  ``critical_path_widget`` in the rendered context, the partial template
  renders the right data-testid hooks, and degrades gracefully when no
  data exists.
"""

from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.test import Client as TestClient
from django.urls import reverse

from core.models import EVSnapshot, Project, Task, TaskDependency
from core.services import dashboard_widgets

pytestmark = pytest.mark.django_db


# ─── Fixtures ───────────────────────────────────────────────────────


@pytest.fixture
def admin_user(db):
    User = get_user_model()
    return User.objects.create_user(
        username="widget_admin", password="pw", is_staff=True
    )


@pytest.fixture
def project(db):
    return Project.objects.create(
        name="Widget Project",
        client="Client",
        start_date=date.today(),
        address="123 Test",
    )


def _make_snapshot(project, *, day_offset=0, spi="1.000", cpi="1.000",
                   pv="1000.00", ev="1000.00", ac="1000.00",
                   eac="1000.00", etc="0.00", vac="0.00",
                   pct_complete="50.00", pct_spent="50.00"):
    return EVSnapshot.objects.create(
        project=project,
        date=date.today() - timedelta(days=day_offset),
        planned_value=Decimal(pv),
        earned_value=Decimal(ev),
        actual_cost=Decimal(ac),
        spi=Decimal(spi),
        cpi=Decimal(cpi),
        schedule_variance=Decimal(ev) - Decimal(pv),
        cost_variance=Decimal(ev) - Decimal(ac),
        estimate_at_completion=Decimal(eac),
        estimate_to_complete=Decimal(etc),
        variance_at_completion=Decimal(vac),
        percent_complete=Decimal(pct_complete),
        percent_spent=Decimal(pct_spent),
    )


# ─── EV widget unit tests ───────────────────────────────────────────


class TestEvWidget:
    def test_no_snapshots_returns_none(self, project):
        assert dashboard_widgets.get_ev_widget(project) is None

    def test_returns_latest_snapshot_only(self, project):
        _make_snapshot(project, day_offset=2, ev="100.00")
        latest = _make_snapshot(project, day_offset=0, ev="900.00")
        out = dashboard_widgets.get_ev_widget(project)
        assert out is not None
        assert out["EV"] == latest.earned_value
        assert out["date"] == latest.date

    def test_status_healthy(self, project):
        _make_snapshot(project, spi="1.020", cpi="0.990")
        assert dashboard_widgets.get_ev_widget(project)["status"] == "healthy"

    def test_status_at_risk(self, project):
        _make_snapshot(project, spi="0.850", cpi="1.100")
        assert dashboard_widgets.get_ev_widget(project)["status"] == "at_risk"

    def test_status_critical(self, project):
        _make_snapshot(project, spi="0.700", cpi="1.000")
        assert dashboard_widgets.get_ev_widget(project)["status"] == "critical"

    def test_exception_returns_none(self, project):
        # Pass an object whose .ev_snapshots blows up.
        class Boom:
            id = 1

            @property
            def ev_snapshots(self):
                raise RuntimeError("nope")

        assert dashboard_widgets.get_ev_widget(Boom()) is None


# ─── Critical Path widget unit tests ────────────────────────────────


class TestCriticalPathWidget:
    def test_no_tasks_returns_none(self, project):
        assert dashboard_widgets.get_critical_path_widget(project) is None

    def test_basic_chain(self, project, admin_user):
        a = Task.objects.create(project=project, title="A", status="Pending", created_by=admin_user)
        b = Task.objects.create(project=project, title="B", status="Pending", created_by=admin_user)
        c = Task.objects.create(project=project, title="C", status="Pending", created_by=admin_user)
        TaskDependency.objects.create(task=b, predecessor=a, type="FS")
        TaskDependency.objects.create(task=c, predecessor=b, type="FS")

        out = dashboard_widgets.get_critical_path_widget(project)
        assert out is not None
        assert out["task_count"] == 3
        assert out["critical_count"] == 3
        assert out["duration_minutes"] > 0
        assert out["duration_hours"] == round(out["duration_minutes"] / 60, 1)
        # Preview list capped to 8 (only 3 here, so all show)
        assert len(out["preview"]) == 3
        assert out["preview_truncated"] is False
        for entry in out["preview"]:
            assert {"task_id", "title", "duration_minutes", "slack_minutes"} <= set(entry)

    def test_preview_truncates_at_cap(self, project, admin_user):
        prev = None
        # 12 chained tasks → all critical, only 8 in preview
        for i in range(12):
            t = Task.objects.create(
                project=project, title=f"T{i}", status="Pending", created_by=admin_user
            )
            if prev is not None:
                TaskDependency.objects.create(task=t, predecessor=prev, type="FS")
            prev = t

        out = dashboard_widgets.get_critical_path_widget(project)
        assert out["task_count"] == 12
        assert out["critical_count"] == 12
        assert len(out["preview"]) == dashboard_widgets.CRITICAL_PATH_PREVIEW_LIMIT == 8
        assert out["preview_truncated"] is True

    def test_cycle_returns_error_dict(self, project, admin_user, monkeypatch):
        # Force a CriticalPathCycleError without having to build a real cycle
        from core.services import critical_path as cp_mod

        def boom(project_id, **kw):
            raise cp_mod.CriticalPathCycleError("synthetic cycle")

        monkeypatch.setattr(
            "core.services.dashboard_widgets.compute_critical_path",
            boom,
            raising=False,
        )
        # Patch where the module imports it (lazy import inside the helper)
        import core.services.critical_path as real_cp
        monkeypatch.setattr(real_cp, "compute_critical_path", boom)

        out = dashboard_widgets.get_critical_path_widget(project)
        assert out["error"] == "cycle_detected"
        assert out["preview"] == []

    def test_unexpected_exception_returns_none(self, project, monkeypatch):
        import core.services.critical_path as real_cp

        def boom(project_id, **kw):
            raise RuntimeError("kaboom")

        monkeypatch.setattr(real_cp, "compute_critical_path", boom)
        assert dashboard_widgets.get_critical_path_widget(project) is None


# ─── End-to-end project_overview integration ────────────────────────


class TestProjectOverviewWidgets:
    def _login(self, admin_user):
        c = TestClient()
        c.login(username="widget_admin", password="pw")
        return c

    def test_overview_context_contains_widget_keys_when_empty(
        self, project, admin_user
    ):
        c = self._login(admin_user)
        resp = c.get(reverse("project_overview", kwargs={"project_id": project.id}))
        assert resp.status_code == 200
        # Both keys must exist in the context (even when value is None)
        assert "ev_widget" in resp.context
        assert "critical_path_widget" in resp.context
        assert resp.context["ev_widget"] is None
        assert resp.context["critical_path_widget"] is None
        # Empty placeholders rendered
        body = resp.content.decode()
        assert 'data-testid="ev-empty"' in body
        assert 'data-testid="cp-empty"' in body

    def test_overview_renders_ev_card_with_snapshot(self, project, admin_user):
        _make_snapshot(project, spi="0.850", cpi="0.900",
                       ev="500.00", pv="600.00", ac="550.00")
        c = self._login(admin_user)
        resp = c.get(reverse("project_overview", kwargs={"project_id": project.id}))
        assert resp.status_code == 200
        ctx_ev = resp.context["ev_widget"]
        assert ctx_ev is not None
        assert ctx_ev["status"] == "at_risk"
        body = resp.content.decode()
        assert 'data-testid="ev-status"' in body
        assert 'data-testid="ev-spi"' in body
        assert 'data-testid="ev-empty"' not in body

    def test_overview_renders_critical_path_card_with_chain(
        self, project, admin_user
    ):
        a = Task.objects.create(project=project, title="A", status="Pending", created_by=admin_user)
        b = Task.objects.create(project=project, title="B", status="Pending", created_by=admin_user)
        TaskDependency.objects.create(task=b, predecessor=a, type="FS")

        c = self._login(admin_user)
        resp = c.get(reverse("project_overview", kwargs={"project_id": project.id}))
        assert resp.status_code == 200
        cp = resp.context["critical_path_widget"]
        assert cp is not None
        assert cp["task_count"] == 2
        body = resp.content.decode()
        assert 'data-testid="cp-count"' in body
        assert 'data-testid="cp-preview"' in body
        assert 'data-testid="cp-empty"' not in body


# ─── EV sparkline unit tests ────────────────────────────────────────


class TestEvSparkline:
    def test_no_snapshots_returns_none(self, project):
        assert dashboard_widgets.get_ev_sparkline(project) is None

    def test_single_snapshot_returns_none(self, project):
        _make_snapshot(project, day_offset=0)
        assert dashboard_widgets.get_ev_sparkline(project) is None

    def test_two_snapshots_returns_chronological_payload(self, project):
        # Insert OUT OF ORDER to verify reverse() chronological sorting.
        _make_snapshot(project, day_offset=2, spi="0.900", cpi="0.910",
                       pv="100.00", ev="90.00", ac="99.00")
        _make_snapshot(project, day_offset=0, spi="1.020", cpi="1.030",
                       pv="200.00", ev="204.00", ac="198.00")

        out = dashboard_widgets.get_ev_sparkline(project)
        assert out is not None
        assert out["count"] == 2
        # Chronological: oldest first, newest last
        assert out["labels"][0] < out["labels"][1]
        assert out["spi"] == ["0.900", "1.020"]
        assert out["cpi"] == ["0.910", "1.030"]
        assert out["ev"] == ["90.00", "204.00"]
        assert out["pv"] == ["100.00", "200.00"]
        # first / last convenience points
        assert out["first"]["SPI"] == "0.900"
        assert out["last"]["SPI"] == "1.020"
        assert out["last"]["EV"] == "204.00"

    def test_days_clamps_window(self, project):
        # 5 snapshots spanning 5 days
        for i in range(5):
            _make_snapshot(project, day_offset=i, spi=f"1.0{i:02d}")
        # Request only last 3
        out = dashboard_widgets.get_ev_sparkline(project, days=3)
        assert out is not None
        assert out["days"] == 3
        assert out["count"] == 3
        # Should be the 3 MOST RECENT (offset 0,1,2) in chronological order
        assert out["labels"][-1] == date.today().isoformat()

    def test_days_below_minimum_clamps_to_two(self, project):
        for i in range(3):
            _make_snapshot(project, day_offset=i)
        out = dashboard_widgets.get_ev_sparkline(project, days=1)
        assert out is not None
        assert out["days"] == 2
        assert out["count"] == 2

    def test_days_above_maximum_clamps_to_365(self, project):
        for i in range(2):
            _make_snapshot(project, day_offset=i)
        out = dashboard_widgets.get_ev_sparkline(project, days=10_000)
        assert out is not None
        assert out["days"] == dashboard_widgets.EV_SPARKLINE_MAX_DAYS

    def test_invalid_days_falls_back_to_default(self, project):
        for i in range(2):
            _make_snapshot(project, day_offset=i)
        out = dashboard_widgets.get_ev_sparkline(project, days="not-a-number")
        assert out is not None
        assert out["days"] == dashboard_widgets.EV_SPARKLINE_DEFAULT_DAYS

    def test_exception_returns_none(self, project):
        from unittest import mock

        with mock.patch.object(
            type(project),
            "ev_snapshots",
            new=mock.PropertyMock(side_effect=RuntimeError("db down")),
        ):
            assert dashboard_widgets.get_ev_sparkline(project) is None

    def test_payload_is_json_safe(self, project):
        """All numeric values must be strings (Decimal is not JSON-safe)."""
        import json

        for i in range(3):
            _make_snapshot(project, day_offset=i, spi="1.000", cpi="0.990")
        out = dashboard_widgets.get_ev_sparkline(project)
        assert out is not None
        # Must round-trip through json without TypeError
        json.dumps(out)
        for k in ("spi", "cpi", "ev", "pv"):
            assert all(isinstance(v, str) for v in out[k])


class TestEvSparklineInOverview:
    def _login(self, user):
        c = TestClient()
        c.login(username=user.username, password="pw")
        return c

    def test_overview_exposes_ev_sparkline_context_key(
        self, project, admin_user
    ):
        c = self._login(admin_user)
        resp = c.get(reverse("project_overview", kwargs={"project_id": project.id}))
        assert resp.status_code == 200
        assert "ev_sparkline" in resp.context
        assert resp.context["ev_sparkline"] is None  # no snapshots yet

    def test_overview_renders_sparkline_canvas_when_data(
        self, project, admin_user
    ):
        _make_snapshot(project, day_offset=2)
        _make_snapshot(project, day_offset=0)

        c = self._login(admin_user)
        resp = c.get(reverse("project_overview", kwargs={"project_id": project.id}))
        assert resp.status_code == 200
        assert resp.context["ev_sparkline"] is not None
        body = resp.content.decode()
        assert 'data-testid="ev-sparkline"' in body
        assert 'data-testid="ev-sparkline-canvas"' in body
        assert 'data-testid="ev-sparkline-spi-last"' in body

    def test_overview_omits_sparkline_when_only_one_snapshot(
        self, project, admin_user
    ):
        _make_snapshot(project, day_offset=0)
        c = self._login(admin_user)
        resp = c.get(reverse("project_overview", kwargs={"project_id": project.id}))
        assert resp.status_code == 200
        assert resp.context["ev_sparkline"] is None
        body = resp.content.decode()
        assert 'data-testid="ev-sparkline-canvas"' not in body


class TestEvSparklineRendererScript:
    """Verify the vanilla canvas renderer is wired only when needed and
    that the static asset itself is well-formed."""

    def _login(self, user):
        c = TestClient()
        c.login(username=user.username, password="pw")
        return c

    def test_script_tag_present_when_sparkline_data_exists(
        self, project, admin_user
    ):
        _make_snapshot(project, day_offset=2)
        _make_snapshot(project, day_offset=0)
        c = self._login(admin_user)
        resp = c.get(reverse("project_overview", kwargs={"project_id": project.id}))
        body = resp.content.decode()
        assert 'data-testid="ev-sparkline-script"' in body
        assert "ev_sparkline.js" in body
        # Must be deferred so it doesn't block initial paint.
        assert "defer" in body[body.find('data-testid="ev-sparkline-script"') :
                                body.find('data-testid="ev-sparkline-script"') + 200]

    def test_script_tag_absent_when_no_sparkline(self, project, admin_user):
        c = self._login(admin_user)
        resp = c.get(reverse("project_overview", kwargs={"project_id": project.id}))
        body = resp.content.decode()
        assert 'data-testid="ev-sparkline-script"' not in body
        assert "ev_sparkline.js" not in body

    def test_renderer_static_file_is_well_formed(self):
        """Smoke check: file exists, is non-empty, exposes the global
        debug hook, and balanced braces (cheap syntax sanity)."""
        from pathlib import Path

        from django.conf import settings

        candidates = [
            Path(settings.BASE_DIR) / "core" / "static" / "core" / "js" / "ev_sparkline.js",
        ]
        path = next((p for p in candidates if p.exists()), None)
        assert path is not None, "ev_sparkline.js must ship as a static asset"
        src = path.read_text(encoding="utf-8")
        assert len(src) > 200
        # Public API the partial template / tests reach for.
        assert "kibrayEvSparkline" in src
        assert "renderAll" in src
        # Reads each data-* attribute the partial emits and the renderer
        # actually consumes. (`ev` / `pv` / `labels` are reserved for a
        # future tooltip; only `spi` and `cpi` are drawn today.)
        for attr in ("spi", "cpi"):
            assert f'"{attr}"' in src or f"'{attr}'" in src, (
                f"renderer must reference data-{attr}"
            )
        # Balanced braces / parens (no truncated file).
        assert src.count("{") == src.count("}")
        assert src.count("(") == src.count(")")
