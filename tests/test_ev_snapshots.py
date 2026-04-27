"""Tests for Phase D3 — EV Snapshots & Forecasting.

Covers:
* Pure ``compute_forecast`` formulas (CPI=1, CPI=0.5, CPI=2, missing CPI, BAC=0,
  negative variances, capping for NUMERIC(5,3) overflow).
* ``create_snapshot`` persistence (creates row, idempotent upsert per day).
* ``bulk_create_snapshots`` iterating multiple projects.
* Celery task ``core.tasks.generate_daily_ev_snapshots`` end-to-end.
* Beat schedule guard: task is registered.
* REST endpoints — list (auth, since/limit filters, payload shape) and
  generate (POST creates, idempotent).
"""

from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from core.models import (
    BudgetLine,
    BudgetProgress,
    CostCode,
    EVSnapshot,
    Expense,
    Project,
)
from core.services.ev_snapshots import (
    bulk_create_snapshots,
    compute_forecast,
    create_snapshot,
)

User = get_user_model()


# ---------------------------------------------------------------------------
# Pure forecast formulas
# ---------------------------------------------------------------------------


class TestComputeForecastFormulas:
    def test_perfect_performance_cpi_one(self):
        f = compute_forecast(bac=1000, ev=500, ac=500, pv=500)
        assert f.cpi == Decimal("1")
        assert f.spi == Decimal("1")
        assert f.cost_variance == Decimal("0")
        assert f.schedule_variance == Decimal("0")
        assert f.estimate_at_completion == Decimal("1000")
        assert f.estimate_to_complete == Decimal("500")
        assert f.variance_at_completion == Decimal("0")

    def test_cost_overrun_cpi_half_doubles_eac(self):
        # CPI=0.5 → EAC = BAC / 0.5 = 2*BAC
        f = compute_forecast(bac=1000, ev=500, ac=1000, pv=500)
        assert f.cpi == Decimal("0.5")
        assert f.cost_variance == Decimal("-500")
        assert f.estimate_at_completion == Decimal("2000")
        assert f.estimate_to_complete == Decimal("1000")
        assert f.variance_at_completion == Decimal("-1000")

    def test_underrun_cpi_two_halves_eac(self):
        f = compute_forecast(bac=1000, ev=500, ac=250, pv=500)
        assert f.cpi == Decimal("2")
        assert f.estimate_at_completion == Decimal("500")
        assert f.variance_at_completion == Decimal("500")
        assert f.estimate_to_complete == Decimal("250")

    def test_missing_cpi_falls_back_to_bac(self):
        # AC=0 → CPI undefined → EAC defaults to BAC
        f = compute_forecast(bac=1000, ev=200, ac=0, pv=400)
        assert f.cpi == Decimal("0")
        assert f.estimate_at_completion == Decimal("1000")
        assert f.estimate_to_complete == Decimal("1000")

    def test_zero_bac_no_division_by_zero(self):
        f = compute_forecast(bac=0, ev=0, ac=0, pv=0)
        assert f.estimate_at_completion == Decimal("0")
        assert f.percent_complete == Decimal("0")
        assert f.percent_spent == Decimal("0")

    def test_etc_never_negative(self):
        # AC > EAC → ETC clamped to 0
        f = compute_forecast(bac=100, ev=100, ac=500, pv=100)
        assert f.estimate_to_complete == Decimal("0")

    def test_schedule_behind_negative_sv(self):
        f = compute_forecast(bac=1000, ev=200, ac=200, pv=500)
        assert f.schedule_variance == Decimal("-300")
        assert f.spi == Decimal("0.4")

    def test_percent_complete_and_spent(self):
        f = compute_forecast(bac=1000, ev=250, ac=400, pv=300)
        assert f.percent_complete == Decimal("25.000")  # 25%
        assert f.percent_spent == Decimal("40.000")  # 40%

    def test_explicit_spi_cpi_override(self):
        # When SPI/CPI are passed they take precedence over computed values.
        f = compute_forecast(bac=1000, ev=500, ac=500, pv=500, spi=Decimal("0.8"), cpi=Decimal("1.25"))
        assert f.spi == Decimal("0.8")
        assert f.cpi == Decimal("1.25")
        assert f.estimate_at_completion == Decimal("800")  # 1000 / 1.25

    def test_caps_extreme_indices_to_fit_decimal_5_3(self):
        # SPI/CPI columns are NUMERIC(5,3) → max 99.999. EV=10000, AC=1 → CPI=10000.
        f = compute_forecast(bac=1000, ev=10000, ac=1, pv=1)
        assert f.cpi == Decimal("99.999")
        assert f.spi == Decimal("99.999")


# ---------------------------------------------------------------------------
# Fixtures for persistence + endpoint tests
# ---------------------------------------------------------------------------


@pytest.fixture
def admin_user(db):
    return User.objects.create_user(
        username="ev_admin", password="pass", is_staff=True, is_superuser=True
    )


@pytest.fixture
def project(db):
    return Project.objects.create(
        name="EV Project",
        client="Client X",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 1, 31),
        address="addr",
    )


@pytest.fixture
def project_with_budget(db, project):
    cc = CostCode.objects.create(code="LAB100", name="Labor")
    line = BudgetLine.objects.create(
        project=project,
        cost_code=cc,
        description="Line",
        qty=Decimal("10"),
        unit_cost=Decimal("100"),
        planned_start=date(2026, 1, 1),
        planned_finish=date(2026, 1, 31),
    )
    if not line.baseline_amount:
        line.baseline_amount = Decimal("1000")
        line.save(update_fields=["baseline_amount"])
    BudgetProgress.objects.create(
        budget_line=line,
        date=date(2026, 1, 15),
        percent_complete=Decimal("50"),
        qty_completed=Decimal("5"),
    )
    Expense.objects.create(
        project=project,
        amount=Decimal("400"),
        date=date(2026, 1, 10),
        description="materials",
    )
    return project


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------


class TestCreateSnapshot:
    def test_creates_row_with_full_metrics(self, project_with_budget):
        snap = create_snapshot(project_with_budget, as_of=date(2026, 1, 20))
        assert snap.pk is not None
        assert snap.date == date(2026, 1, 20)
        assert snap.earned_value == Decimal("500.00")  # 50% of 1000
        assert snap.actual_cost == Decimal("400.00")
        assert snap.cpi == Decimal("1.250")  # 500/400
        assert snap.estimate_at_completion == Decimal("800.00")  # 1000/1.25

    def test_idempotent_same_date_updates_existing(self, project_with_budget):
        snap1 = create_snapshot(project_with_budget, as_of=date(2026, 1, 20))
        # Override with explicit summary having different EV — should overwrite same row.
        snap2 = create_snapshot(
            project_with_budget,
            as_of=date(2026, 1, 20),
            ev_summary={
                "baseline_total": Decimal("1000"),
                "PV": Decimal("500"),
                "EV": Decimal("700"),
                "AC": Decimal("400"),
                "SPI": None,
                "CPI": None,
            },
        )
        assert snap1.pk == snap2.pk
        assert EVSnapshot.objects.filter(project=project_with_budget, date=date(2026, 1, 20)).count() == 1
        snap2.refresh_from_db()
        assert snap2.earned_value == Decimal("700")

    def test_different_dates_create_separate_rows(self, project_with_budget):
        create_snapshot(project_with_budget, as_of=date(2026, 1, 19))
        create_snapshot(project_with_budget, as_of=date(2026, 1, 20))
        assert EVSnapshot.objects.filter(project=project_with_budget).count() == 2

    def test_handles_empty_project(self, project):
        snap = create_snapshot(project, as_of=date(2026, 1, 20))
        assert snap.earned_value == Decimal("0")
        assert snap.planned_value == Decimal("0")
        assert snap.actual_cost == Decimal("0")
        assert snap.estimate_at_completion == Decimal("0")


class TestBulkCreateSnapshots:
    def test_iterates_all_projects(self, db):
        p1 = Project.objects.create(name="A", client="c", start_date=date(2026, 1, 1), address="x")
        p2 = Project.objects.create(name="B", client="c", start_date=date(2026, 1, 1), address="x")
        snaps = bulk_create_snapshots(as_of=date(2026, 1, 20))
        assert {s.project_id for s in snaps} == {p1.id, p2.id}

    def test_respects_project_qs_filter(self, db):
        p1 = Project.objects.create(name="A", client="c", start_date=date(2026, 1, 1), address="x")
        Project.objects.create(name="B", client="c", start_date=date(2026, 1, 1), address="x")
        snaps = bulk_create_snapshots(
            as_of=date(2026, 1, 20),
            project_qs=Project.objects.filter(pk=p1.pk),
        )
        assert len(snaps) == 1
        assert snaps[0].project_id == p1.id


# ---------------------------------------------------------------------------
# Celery task
# ---------------------------------------------------------------------------


class TestCeleryTask:
    def test_generate_daily_ev_snapshots_runs(self, project_with_budget):
        from core.tasks import generate_daily_ev_snapshots

        result = generate_daily_ev_snapshots()
        assert result["snapshots"] >= 1
        assert EVSnapshot.objects.filter(project=project_with_budget).exists()

    def test_task_registered_in_beat_schedule(self):
        from kibray_backend.celery_config import app

        scheduled = {entry["task"] for entry in app.conf.beat_schedule.values()}
        assert "core.tasks.generate_daily_ev_snapshots" in scheduled


# ---------------------------------------------------------------------------
# REST endpoints
# ---------------------------------------------------------------------------


@pytest.fixture
def api_client():
    return APIClient()


class TestEVSnapshotsListEndpoint:
    def test_list_returns_snapshots_descending(self, api_client, admin_user, project_with_budget):
        create_snapshot(project_with_budget, as_of=date(2026, 1, 18))
        create_snapshot(project_with_budget, as_of=date(2026, 1, 19))
        create_snapshot(project_with_budget, as_of=date(2026, 1, 20))

        api_client.force_authenticate(user=admin_user)
        url = f"/api/v1/projects/{project_with_budget.id}/ev-snapshots/"
        res = api_client.get(url)
        assert res.status_code == 200
        body = res.data
        assert body["project_id"] == project_with_budget.id
        assert body["count"] == 3
        dates = [s["date"] for s in body["snapshots"]]
        assert dates == ["2026-01-20", "2026-01-19", "2026-01-18"]
        # Payload shape includes all key metrics
        first = body["snapshots"][0]
        for key in ("PV", "EV", "AC", "SPI", "CPI", "EAC", "ETC", "VAC", "percent_complete"):
            assert key in first

    def test_since_filter(self, api_client, admin_user, project_with_budget):
        create_snapshot(project_with_budget, as_of=date(2026, 1, 18))
        create_snapshot(project_with_budget, as_of=date(2026, 1, 20))
        api_client.force_authenticate(user=admin_user)
        url = f"/api/v1/projects/{project_with_budget.id}/ev-snapshots/?since=2026-01-19"
        res = api_client.get(url)
        assert res.status_code == 200
        assert res.data["count"] == 1
        assert res.data["snapshots"][0]["date"] == "2026-01-20"

    def test_invalid_since_returns_400(self, api_client, admin_user, project_with_budget):
        api_client.force_authenticate(user=admin_user)
        url = f"/api/v1/projects/{project_with_budget.id}/ev-snapshots/?since=not-a-date"
        res = api_client.get(url)
        assert res.status_code == 400
        assert res.data["error"] == "invalid_since"

    def test_limit_caps_results(self, api_client, admin_user, project_with_budget):
        for i in range(5):
            create_snapshot(project_with_budget, as_of=date(2026, 1, 10) + timedelta(days=i))
        api_client.force_authenticate(user=admin_user)
        url = f"/api/v1/projects/{project_with_budget.id}/ev-snapshots/?limit=2"
        res = api_client.get(url)
        assert res.status_code == 200
        assert res.data["count"] == 2

    def test_requires_authentication(self, api_client, project_with_budget):
        url = f"/api/v1/projects/{project_with_budget.id}/ev-snapshots/"
        res = api_client.get(url)
        assert res.status_code in (401, 403)


class TestEVSnapshotsGenerateEndpoint:
    def test_post_creates_snapshot(self, api_client, admin_user, project_with_budget):
        api_client.force_authenticate(user=admin_user)
        url = f"/api/v1/projects/{project_with_budget.id}/ev-snapshots/generate/"
        res = api_client.post(url)
        assert res.status_code == 201
        assert res.data["project_id"] == project_with_budget.id
        assert "EV" in res.data and "EAC" in res.data
        assert EVSnapshot.objects.filter(project=project_with_budget).count() == 1

    def test_post_idempotent_same_day(self, api_client, admin_user, project_with_budget):
        api_client.force_authenticate(user=admin_user)
        url = f"/api/v1/projects/{project_with_budget.id}/ev-snapshots/generate/"
        api_client.post(url)
        api_client.post(url)
        assert EVSnapshot.objects.filter(project=project_with_budget).count() == 1

    def test_post_requires_authentication(self, api_client, project_with_budget):
        url = f"/api/v1/projects/{project_with_budget.id}/ev-snapshots/generate/"
        res = api_client.post(url)
        assert res.status_code in (401, 403)
