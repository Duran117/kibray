"""
Dashboard widget helpers — Phase D follow-up.

Lightweight, cached-friendly accessors on top of:
* ``EVSnapshot`` (latest persisted Earned Value row per project)
* ``compute_critical_path`` (CPM analysis)

Designed for synchronous server-rendered template contexts (e.g. the
project overview page) so the templates stay dumb and we don't recompute
heavy things per page load. Each helper:

* Returns ``None`` (or a stable empty dict) on missing data — never
  raises — so the widget can render a "no data yet" placeholder.
* Catches its own exceptions and logs at ``warning`` level. We never
  want a CPM cycle or an EV math hiccup to take down the project page.
"""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Earned Value
# ---------------------------------------------------------------------------


def _ev_status_label(spi: Decimal | None, cpi: Decimal | None) -> str:
    """Human label for the EV health badge (green/amber/red).

    Rules:
    * ``healthy`` if both indices ≥ 0.95
    * ``at_risk`` if either is between 0.80 and 0.95
    * ``critical`` if either is < 0.80
    * ``unknown`` if either index is missing
    """
    if spi is None or cpi is None:
        return "unknown"
    worst = min(Decimal(spi), Decimal(cpi))
    if worst >= Decimal("0.95"):
        return "healthy"
    if worst >= Decimal("0.80"):
        return "at_risk"
    return "critical"


def get_ev_widget(project) -> dict[str, Any] | None:
    """Return latest persisted EV snapshot summary or ``None``.

    Cheap — a single ``EVSnapshot`` row lookup ordered by ``-date``.
    Used by the project overview template to render the EV health card.
    """
    try:
        snap = (
            project.ev_snapshots.order_by("-date").first()
            if hasattr(project, "ev_snapshots")
            else None
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("get_ev_widget: snapshot lookup failed for project=%s: %s",
                       getattr(project, "id", "?"), exc)
        return None

    if snap is None:
        return None

    return {
        "date": snap.date,
        "PV": snap.planned_value,
        "EV": snap.earned_value,
        "AC": snap.actual_cost,
        "SPI": snap.spi,
        "CPI": snap.cpi,
        "SV": snap.schedule_variance,
        "CV": snap.cost_variance,
        "EAC": snap.estimate_at_completion,
        "ETC": snap.estimate_to_complete,
        "VAC": snap.variance_at_completion,
        "percent_complete": snap.percent_complete,
        "percent_spent": snap.percent_spent,
        "status": _ev_status_label(snap.spi, snap.cpi),
    }


# Sparkline window — 30d gives a nice balance between trend visibility and
# query weight (a single indexed scan over EVSnapshot).
EV_SPARKLINE_DEFAULT_DAYS = 30
EV_SPARKLINE_MAX_DAYS = 365


def get_ev_sparkline(project, days: int = EV_SPARKLINE_DEFAULT_DAYS) -> dict[str, Any] | None:
    """Return a tiny EV trend payload for an inline sparkline.

    Picks the last ``days`` ``EVSnapshot`` rows (default 30, capped at 365)
    in **chronological** order so the front-end can plot points left→right
    without re-sorting. Returns ``None`` if there are fewer than two
    snapshots — a single point isn't a trend, and the EV card already
    shows the latest values.

    Payload shape::

        {
            "days": 30,                # window requested (clamped)
            "count": 17,               # actual rows returned
            "labels": ["2026-04-01", ...],
            "spi":   ["1.020", ...],   # str(Decimal) — JSON-safe
            "cpi":   ["0.985", ...],
            "ev":    ["12500.00", ...],
            "pv":    ["12000.00", ...],
            "first": {date, SPI, CPI, EV, PV},   # convenience for delta calc
            "last":  {date, SPI, CPI, EV, PV},
        }
    """
    try:
        days = int(days)
    except (TypeError, ValueError):
        days = EV_SPARKLINE_DEFAULT_DAYS
    days = max(2, min(days, EV_SPARKLINE_MAX_DAYS))

    try:
        if not hasattr(project, "ev_snapshots"):
            return None
        # Take the most-recent N then reverse for chronological order.
        recent = list(project.ev_snapshots.order_by("-date")[:days])
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "get_ev_sparkline: lookup failed for project=%s: %s",
            getattr(project, "id", "?"),
            exc,
        )
        return None

    if len(recent) < 2:
        return None

    recent.reverse()  # chronological

    def _point(s):
        return {
            "date": s.date.isoformat(),
            "SPI": str(s.spi),
            "CPI": str(s.cpi),
            "EV": str(s.earned_value),
            "PV": str(s.planned_value),
        }

    return {
        "days": days,
        "count": len(recent),
        "labels": [s.date.isoformat() for s in recent],
        "spi": [str(s.spi) for s in recent],
        "cpi": [str(s.cpi) for s in recent],
        "ev": [str(s.earned_value) for s in recent],
        "pv": [str(s.planned_value) for s in recent],
        "first": _point(recent[0]),
        "last": _point(recent[-1]),
    }


# ---------------------------------------------------------------------------
# Critical Path
# ---------------------------------------------------------------------------


# Cap how many critical tasks we hand to the template — we only want a
# preview list with "view all" link; rendering hundreds is pointless.
CRITICAL_PATH_PREVIEW_LIMIT = 8


def get_critical_path_widget(project) -> dict[str, Any] | None:
    """Return a small Critical Path summary for the overview page.

    Returns ``None`` if the project has no tasks at all (so the widget can
    render a placeholder). On cycle / unexpected error returns a dict with
    ``error`` key — the template can still show a friendly message.
    """
    from core.services.critical_path import (
        CriticalPathCycleError,
        compute_critical_path,
    )

    try:
        result = compute_critical_path(project.id)
    except CriticalPathCycleError as exc:
        logger.warning(
            "get_critical_path_widget: cycle in project=%s: %s",
            getattr(project, "id", "?"),
            exc,
        )
        return {
            "error": "cycle_detected",
            "task_count": 0,
            "critical_count": 0,
            "duration_minutes": 0,
            "duration_hours": 0,
            "preview": [],
        }
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "get_critical_path_widget: failed for project=%s: %s",
            getattr(project, "id", "?"),
            exc,
        )
        return None

    tasks = result.get("tasks") or []
    if not tasks:
        return None

    critical_ids = set(result.get("critical_path_ids") or [])
    critical_tasks = [t for t in tasks if t.get("is_critical")]

    # Order critical tasks by ES (already sorted by run_cpm) and take preview.
    preview = [
        {
            "task_id": t["task_id"],
            "title": t["title"],
            "duration_minutes": t["duration_minutes"],
            "slack_minutes": t["slack_minutes"],
        }
        for t in critical_tasks[:CRITICAL_PATH_PREVIEW_LIMIT]
    ]

    duration = result.get("project_duration_minutes") or 0

    return {
        "task_count": len(tasks),
        "critical_count": len(critical_ids),
        "duration_minutes": duration,
        "duration_hours": round(duration / 60, 1) if duration else 0,
        "preview": preview,
        "preview_truncated": len(critical_tasks) > CRITICAL_PATH_PREVIEW_LIMIT,
    }


__all__ = [
    "get_ev_widget",
    "get_ev_sparkline",
    "get_critical_path_widget",
    "CRITICAL_PATH_PREVIEW_LIMIT",
    "EV_SPARKLINE_DEFAULT_DAYS",
]
