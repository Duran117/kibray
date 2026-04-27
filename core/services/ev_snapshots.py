"""Phase D3 — Earned Value snapshots & forecasting.

Builds on top of ``core.services.earned_value.compute_project_ev`` to:

* Compute industry-standard EVM forecasts (EAC, ETC, VAC, SV, CV).
* Persist daily ``EVSnapshot`` rows (one per ``project`` per ``date``,
  upsert-style) so the UI / reports / Celery beat can read trended
  performance data over time.
* Expose a bulk helper used by the ``core.tasks.generate_daily_ev_snapshots``
  Celery task that runs every evening.

Forecast formulas (PMI / PMBOK):

* SV  = EV − PV
* CV  = EV − AC
* EAC = BAC / CPI                (defaults to BAC when CPI is missing)
* ETC = max(EAC − AC, 0)
* VAC = BAC − EAC
* %complete = EV / BAC × 100
* %spent    = AC / BAC × 100

All money fields are kept as ``Decimal`` to match the model schema; ``None``
inputs / divisions by zero are normalised to ``Decimal('0')`` so the row is
always insertable.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Iterable

from django.db import transaction
from django.utils import timezone

from core.models import EVSnapshot, Project
from core.services.earned_value import compute_project_ev


ZERO = Decimal("0")
ONE_HUNDRED = Decimal("100")


# ---------------------------------------------------------------------------
# Forecast (pure)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ForecastResult:
    spi: Decimal
    cpi: Decimal
    schedule_variance: Decimal  # SV
    cost_variance: Decimal  # CV
    estimate_at_completion: Decimal  # EAC
    estimate_to_complete: Decimal  # ETC
    variance_at_completion: Decimal  # VAC
    percent_complete: Decimal
    percent_spent: Decimal

    def as_dict(self) -> dict:
        return {
            "spi": self.spi,
            "cpi": self.cpi,
            "schedule_variance": self.schedule_variance,
            "cost_variance": self.cost_variance,
            "estimate_at_completion": self.estimate_at_completion,
            "estimate_to_complete": self.estimate_to_complete,
            "variance_at_completion": self.variance_at_completion,
            "percent_complete": self.percent_complete,
            "percent_spent": self.percent_spent,
        }


def _to_decimal(value) -> Decimal:
    if value is None:
        return ZERO
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def compute_forecast(
    *,
    bac,
    ev,
    ac,
    pv,
    spi=None,
    cpi=None,
) -> ForecastResult:
    """Pure forecast computation. Accepts numbers or ``None`` for any input.

    ``bac`` (Budget at Completion) defaults to the project baseline total.
    When CPI is missing or zero the EAC defaults to BAC (we cannot project a
    cost overrun without efficiency data).
    """
    bac_d = _to_decimal(bac)
    ev_d = _to_decimal(ev)
    ac_d = _to_decimal(ac)
    pv_d = _to_decimal(pv)
    spi_d = _to_decimal(spi) if spi is not None else (ev_d / pv_d if pv_d else ZERO)
    cpi_d = _to_decimal(cpi) if cpi is not None else (ev_d / ac_d if ac_d else ZERO)

    sv = ev_d - pv_d
    cv = ev_d - ac_d

    if cpi_d and cpi_d > 0:
        eac = bac_d / cpi_d
    else:
        eac = bac_d

    etc = eac - ac_d
    if etc < 0:
        etc = ZERO
    vac = bac_d - eac

    percent_complete = (ev_d / bac_d * ONE_HUNDRED) if bac_d else ZERO
    percent_spent = (ac_d / bac_d * ONE_HUNDRED) if bac_d else ZERO

    # EVSnapshot.spi / cpi are NUMERIC(5,3); cap to avoid OverflowError.
    spi_d = _cap(spi_d, max_value=Decimal("99.999"))
    cpi_d = _cap(cpi_d, max_value=Decimal("99.999"))
    percent_complete = _cap(percent_complete, max_value=Decimal("999.99"))
    percent_spent = _cap(percent_spent, max_value=Decimal("999.99"))

    return ForecastResult(
        spi=spi_d,
        cpi=cpi_d,
        schedule_variance=sv,
        cost_variance=cv,
        estimate_at_completion=eac,
        estimate_to_complete=etc,
        variance_at_completion=vac,
        percent_complete=percent_complete,
        percent_spent=percent_spent,
    )


def _cap(value: Decimal, *, max_value: Decimal) -> Decimal:
    if value > max_value:
        return max_value
    if value < -max_value:
        return -max_value
    return value


# ---------------------------------------------------------------------------
# Snapshot persistence
# ---------------------------------------------------------------------------


@transaction.atomic
def create_snapshot(project, as_of=None, *, ev_summary=None) -> EVSnapshot:
    """Compute current EV + forecast and upsert an ``EVSnapshot`` row.

    Idempotent for ``(project, as_of)`` thanks to the unique constraint on
    the model: re-running the same day overwrites the previous values.
    """
    if as_of is None:
        as_of = timezone.now().date()
    if ev_summary is None:
        ev_summary = compute_project_ev(project, as_of=as_of)

    bac = ev_summary.get("baseline_total") or ZERO
    forecast = compute_forecast(
        bac=bac,
        ev=ev_summary.get("EV"),
        ac=ev_summary.get("AC"),
        pv=ev_summary.get("PV"),
        spi=ev_summary.get("SPI"),
        cpi=ev_summary.get("CPI"),
    )

    defaults = {
        "planned_value": _to_decimal(ev_summary.get("PV")),
        "earned_value": _to_decimal(ev_summary.get("EV")),
        "actual_cost": _to_decimal(ev_summary.get("AC")),
        **forecast.as_dict(),
    }

    snapshot, _created = EVSnapshot.objects.update_or_create(
        project=project,
        date=as_of,
        defaults=defaults,
    )
    return snapshot


def bulk_create_snapshots(
    as_of=None,
    *,
    project_qs: Iterable[Project] | None = None,
) -> list[EVSnapshot]:
    """Generate snapshots for many projects in a single Celery cycle.

    By default operates over every ``Project``; pass ``project_qs`` to
    restrict (e.g. only active projects).
    """
    if as_of is None:
        as_of = timezone.now().date()
    if project_qs is None:
        project_qs = Project.objects.all()

    created: list[EVSnapshot] = []
    for project in project_qs:
        try:
            snap = create_snapshot(project, as_of=as_of)
        except Exception:  # pragma: no cover — defensive, individual project failures should not abort the batch
            import logging

            logging.getLogger(__name__).exception(
                "ev_snapshot failed for project %s", project.pk
            )
            continue
        created.append(snap)
    return created
