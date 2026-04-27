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
    "get_critical_path_widget",
    "CRITICAL_PATH_PREVIEW_LIMIT",
]
