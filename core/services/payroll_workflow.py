"""Phase D1 — Payroll workflow state machine.

The ``PayrollPeriod`` model already declares 4 states (``draft``,
``under_review``, ``approved``, ``paid``) and ships an ``approve()`` method,
but the rest of the lifecycle was missing: there was no way to submit a draft
for review, no way to mark an approved period as paid, no way to reopen an
approved period for corrections, and the existing ``approve()`` did not
enforce the state machine.

This module centralises the legal transitions:

    draft ──► under_review ──► approved ──► paid
       ▲           │              │
       └───────────┴──────────────┘   (reopen, while not paid)

Transitions are pure functions over a ``PayrollPeriod`` instance — no
migrations are required, the model already has every field we need
(``status``, ``approved_by``, ``approved_at``).
"""

from __future__ import annotations

import logging
from typing import Iterable

from django.utils import timezone

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# State machine
# ---------------------------------------------------------------------------

DRAFT = "draft"
UNDER_REVIEW = "under_review"
APPROVED = "approved"
PAID = "paid"

STATES: tuple[str, ...] = (DRAFT, UNDER_REVIEW, APPROVED, PAID)

# {source_state: {valid_target_states}}
_LEGAL_TRANSITIONS: dict[str, frozenset[str]] = {
    DRAFT: frozenset({UNDER_REVIEW, APPROVED}),  # APPROVED kept for legacy single-step flow
    UNDER_REVIEW: frozenset({DRAFT, APPROVED}),
    APPROVED: frozenset({DRAFT, PAID}),
    PAID: frozenset(),  # terminal
}


class PayrollTransitionError(Exception):
    """Raised when an illegal state transition is attempted."""


def can_transition(period, target_state: str) -> bool:
    """Return ``True`` if ``period.status`` may move to ``target_state``."""
    if target_state not in STATES:
        return False
    return target_state in _LEGAL_TRANSITIONS.get(period.status, frozenset())


def legal_targets(period) -> frozenset[str]:
    """Return the set of states ``period`` may transition into."""
    return _LEGAL_TRANSITIONS.get(period.status, frozenset())


def _require(period, allowed_sources: Iterable[str], target: str) -> None:
    if period.status not in allowed_sources:
        raise PayrollTransitionError(
            f"Cannot move period {period.pk} from {period.status!r} to {target!r}; "
            f"valid sources: {sorted(allowed_sources)}"
        )


# ---------------------------------------------------------------------------
# Transitions
# ---------------------------------------------------------------------------


def submit_for_review(period, submitted_by=None):
    """``draft`` → ``under_review``.

    Idempotent: calling it on an already-``under_review`` period is a no-op.
    """
    if period.status == UNDER_REVIEW:
        return period
    _require(period, {DRAFT}, UNDER_REVIEW)
    period.status = UNDER_REVIEW
    period.save(update_fields=["status"])
    logger.info(
        "payroll.workflow: period=%s draft -> under_review by=%s",
        period.pk,
        getattr(submitted_by, "pk", None),
    )
    return period


def approve(period, approved_by, *, skip_validation: bool = False):
    """``draft`` or ``under_review`` → ``approved``.

    Wraps the model's ``approve()`` (which already runs validation +
    persists ``approved_by`` / ``approved_at``) but enforces the source
    state. ``draft`` is accepted for backwards compatibility with the
    legacy single-step approval flow. Idempotent on already-approved
    periods.
    """
    if period.status == APPROVED:
        return period
    _require(period, {DRAFT, UNDER_REVIEW}, APPROVED)
    period.approve(approved_by=approved_by, skip_validation=skip_validation)
    logger.info(
        "payroll.workflow: period=%s %s -> approved by=%s",
        period.pk,
        period.status,
        getattr(approved_by, "pk", None),
    )
    return period


def mark_paid(period, paid_by=None):
    """``approved`` → ``paid``.

    Terminal state — once paid, no further transitions are allowed (call
    ``reopen`` first if you really need to undo). Idempotent.
    """
    if period.status == PAID:
        return period
    _require(period, {APPROVED}, PAID)
    period.status = PAID
    period.save(update_fields=["status"])
    logger.info(
        "payroll.workflow: period=%s approved -> paid by=%s",
        period.pk,
        getattr(paid_by, "pk", None),
    )
    return period


def reopen(period, reopened_by=None):
    """``under_review`` or ``approved`` → ``draft``.

    Clears ``approved_by`` / ``approved_at`` so the audit trail does not
    keep stale data. ``paid`` periods cannot be reopened — they are
    terminal. Idempotent on already-draft periods.
    """
    if period.status == DRAFT:
        return period
    _require(period, {UNDER_REVIEW, APPROVED}, DRAFT)
    period.status = DRAFT
    update_fields = ["status"]
    # Clear approval audit so the next approve() records the correct timestamp.
    if hasattr(period, "approved_by") and period.approved_by_id is not None:
        period.approved_by = None
        update_fields.append("approved_by")
    if hasattr(period, "approved_at") and period.approved_at is not None:
        period.approved_at = None
        update_fields.append("approved_at")
    period.save(update_fields=update_fields)
    logger.info(
        "payroll.workflow: period=%s reopened by=%s (now draft)",
        period.pk,
        getattr(reopened_by, "pk", None),
    )
    return period


__all__ = [
    "DRAFT",
    "UNDER_REVIEW",
    "APPROVED",
    "PAID",
    "STATES",
    "PayrollTransitionError",
    "can_transition",
    "legal_targets",
    "submit_for_review",
    "approve",
    "mark_paid",
    "reopen",
]
