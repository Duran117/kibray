"""Tests for Phase D1 — Payroll workflow state machine.

Covers:
* Pure state-machine helpers (``can_transition`` / ``legal_targets``).
* Each transition (submit_for_review / approve / mark_paid / reopen) with
  happy-path, idempotency, and illegal-source guards (``PayrollTransitionError``).
* Reopen clears ``approved_by`` / ``approved_at``.
* REST endpoints (status, 409 on illegal transitions, payload shape, auth).
"""

from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from core.models import Employee, PayrollPeriod, PayrollRecord
from core.services.payroll_workflow import (
    APPROVED,
    DRAFT,
    PAID,
    PayrollTransitionError,
    UNDER_REVIEW,
    approve,
    can_transition,
    legal_targets,
    mark_paid,
    reopen,
    submit_for_review,
)

User = get_user_model()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def admin_user(db):
    return User.objects.create_user(
        username="payroll_admin",
        password="pass",
        is_staff=True,
        is_superuser=True,
    )


@pytest.fixture
def employee(db):
    return Employee.objects.create(
        first_name="Jane",
        last_name="Doe",
        hourly_rate=Decimal("25"),
    )


@pytest.fixture
def period(db, admin_user):
    return PayrollPeriod.objects.create(
        week_start=date(2026, 1, 5),
        week_end=date(2026, 1, 11),
        created_by=admin_user,
        status=DRAFT,
    )


@pytest.fixture
def period_with_record(db, period, employee, admin_user):
    PayrollRecord.objects.create(
        period=period,
        employee=employee,
        week_start=period.week_start,
        week_end=period.week_end,
        total_hours=Decimal("40"),
        hourly_rate=Decimal("25"),
        regular_hours=Decimal("40"),
        overtime_hours=Decimal("0"),
        gross_pay=Decimal("1000"),
        net_pay=Decimal("1000"),
        total_pay=Decimal("1000"),
    )
    return period


# ---------------------------------------------------------------------------
# Pure state-machine
# ---------------------------------------------------------------------------


class TestStateMachine:
    @pytest.mark.parametrize(
        "current,target,expected",
        [
            (DRAFT, UNDER_REVIEW, True),
            (DRAFT, APPROVED, True),  # legacy single-step approval allowed
            (DRAFT, PAID, False),
            (UNDER_REVIEW, APPROVED, True),
            (UNDER_REVIEW, DRAFT, True),  # reopen
            (UNDER_REVIEW, PAID, False),
            (APPROVED, PAID, True),
            (APPROVED, DRAFT, True),  # reopen
            (PAID, DRAFT, False),  # terminal
            (PAID, APPROVED, False),
            (PAID, UNDER_REVIEW, False),
        ],
    )
    def test_can_transition_matrix(self, period, current, target, expected):
        period.status = current
        assert can_transition(period, target) is expected

    def test_can_transition_unknown_target(self, period):
        period.status = DRAFT
        assert can_transition(period, "garbage") is False

    def test_legal_targets(self, period):
        period.status = DRAFT
        assert legal_targets(period) == frozenset({UNDER_REVIEW, APPROVED})
        period.status = UNDER_REVIEW
        assert legal_targets(period) == frozenset({DRAFT, APPROVED})
        period.status = APPROVED
        assert legal_targets(period) == frozenset({DRAFT, PAID})
        period.status = PAID
        assert legal_targets(period) == frozenset()


# ---------------------------------------------------------------------------
# Transition functions
# ---------------------------------------------------------------------------


class TestSubmitForReview:
    def test_draft_to_under_review(self, period_with_record, admin_user):
        submit_for_review(period_with_record, submitted_by=admin_user)
        period_with_record.refresh_from_db()
        assert period_with_record.status == UNDER_REVIEW

    def test_idempotent(self, period_with_record, admin_user):
        submit_for_review(period_with_record, submitted_by=admin_user)
        submit_for_review(period_with_record, submitted_by=admin_user)  # no-op
        assert period_with_record.status == UNDER_REVIEW

    def test_illegal_from_approved(self, period_with_record, admin_user):
        period_with_record.status = APPROVED
        period_with_record.save(update_fields=["status"])
        with pytest.raises(PayrollTransitionError):
            submit_for_review(period_with_record, submitted_by=admin_user)


class TestApprove:
    def test_under_review_to_approved(self, period_with_record, admin_user):
        period_with_record.status = UNDER_REVIEW
        period_with_record.save(update_fields=["status"])
        approve(period_with_record, approved_by=admin_user, skip_validation=True)
        period_with_record.refresh_from_db()
        assert period_with_record.status == APPROVED
        assert period_with_record.approved_by_id == admin_user.id
        assert period_with_record.approved_at is not None

    def test_idempotent(self, period_with_record, admin_user):
        period_with_record.status = UNDER_REVIEW
        period_with_record.save(update_fields=["status"])
        approve(period_with_record, approved_by=admin_user, skip_validation=True)
        approve(period_with_record, approved_by=admin_user, skip_validation=True)
        assert period_with_record.status == APPROVED

    def test_illegal_from_draft(self, period_with_record, admin_user):
        # period is in DRAFT; legacy single-step approve allowed too
        approve(period_with_record, approved_by=admin_user, skip_validation=True)
        assert period_with_record.status == APPROVED

    def test_illegal_from_paid(self, period_with_record, admin_user):
        period_with_record.status = PAID
        period_with_record.save(update_fields=["status"])
        with pytest.raises(PayrollTransitionError):
            approve(period_with_record, approved_by=admin_user, skip_validation=True)


class TestMarkPaid:
    def test_approved_to_paid(self, period_with_record, admin_user):
        period_with_record.status = APPROVED
        period_with_record.save(update_fields=["status"])
        mark_paid(period_with_record, paid_by=admin_user)
        period_with_record.refresh_from_db()
        assert period_with_record.status == PAID

    def test_idempotent(self, period_with_record, admin_user):
        period_with_record.status = PAID
        period_with_record.save(update_fields=["status"])
        mark_paid(period_with_record, paid_by=admin_user)  # no-op
        assert period_with_record.status == PAID

    def test_illegal_from_under_review(self, period_with_record, admin_user):
        period_with_record.status = UNDER_REVIEW
        period_with_record.save(update_fields=["status"])
        with pytest.raises(PayrollTransitionError):
            mark_paid(period_with_record, paid_by=admin_user)

    def test_illegal_from_draft(self, period_with_record, admin_user):
        with pytest.raises(PayrollTransitionError):
            mark_paid(period_with_record, paid_by=admin_user)


class TestReopen:
    def test_reopen_from_under_review(self, period_with_record, admin_user):
        period_with_record.status = UNDER_REVIEW
        period_with_record.save(update_fields=["status"])
        reopen(period_with_record, reopened_by=admin_user)
        period_with_record.refresh_from_db()
        assert period_with_record.status == DRAFT

    def test_reopen_from_approved_clears_audit(self, period_with_record, admin_user):
        # First do a real approve so approved_by/at get set
        period_with_record.status = UNDER_REVIEW
        period_with_record.save(update_fields=["status"])
        approve(period_with_record, approved_by=admin_user, skip_validation=True)
        period_with_record.refresh_from_db()
        assert period_with_record.approved_by_id == admin_user.id
        # Now reopen — audit should be cleared
        reopen(period_with_record, reopened_by=admin_user)
        period_with_record.refresh_from_db()
        assert period_with_record.status == DRAFT
        assert period_with_record.approved_by_id is None
        assert period_with_record.approved_at is None

    def test_idempotent(self, period_with_record, admin_user):
        reopen(period_with_record, reopened_by=admin_user)  # already DRAFT
        assert period_with_record.status == DRAFT

    def test_illegal_from_paid(self, period_with_record, admin_user):
        period_with_record.status = PAID
        period_with_record.save(update_fields=["status"])
        with pytest.raises(PayrollTransitionError):
            reopen(period_with_record, reopened_by=admin_user)


# ---------------------------------------------------------------------------
# REST endpoints
# ---------------------------------------------------------------------------


@pytest.fixture
def api_client():
    return APIClient()


class TestPayrollWorkflowEndpoints:
    def test_legal_transitions_endpoint(self, api_client, admin_user, period_with_record):
        api_client.force_authenticate(user=admin_user)
        url = f"/api/v1/payroll/periods/{period_with_record.id}/legal-transitions/"
        res = api_client.get(url)
        assert res.status_code == 200
        assert res.data["status"] == DRAFT
        assert set(res.data["legal_targets"]) == {UNDER_REVIEW, APPROVED}

    def test_full_lifecycle_via_api(self, api_client, admin_user, period_with_record):
        api_client.force_authenticate(user=admin_user)
        base = f"/api/v1/payroll/periods/{period_with_record.id}"

        # draft -> under_review
        r = api_client.post(f"{base}/submit-for-review/")
        assert r.status_code == 200
        assert r.data["status"] == UNDER_REVIEW

        # under_review -> approved
        r = api_client.post(f"{base}/approve/", {"skip_validation": True}, format="json")
        assert r.status_code == 200, r.data
        assert r.data["status"] == "approved"

        # approved -> paid
        r = api_client.post(f"{base}/mark-paid/")
        assert r.status_code == 200
        assert r.data["status"] == PAID

    def test_illegal_transition_returns_409(self, api_client, admin_user, period_with_record):
        api_client.force_authenticate(user=admin_user)
        base = f"/api/v1/payroll/periods/{period_with_record.id}"
        # Try to mark-paid on a draft (not approved) — illegal
        r = api_client.post(f"{base}/mark-paid/")
        assert r.status_code == 409
        assert r.data["current_status"] == DRAFT
        assert "Cannot move period" in r.data["error"]

    def test_reopen_endpoint(self, api_client, admin_user, period_with_record):
        period_with_record.status = APPROVED
        period_with_record.save(update_fields=["status"])
        api_client.force_authenticate(user=admin_user)
        r = api_client.post(f"/api/v1/payroll/periods/{period_with_record.id}/reopen/")
        assert r.status_code == 200
        assert r.data["status"] == DRAFT

    def test_paid_period_cannot_reopen_via_api(self, api_client, admin_user, period_with_record):
        period_with_record.status = PAID
        period_with_record.save(update_fields=["status"])
        api_client.force_authenticate(user=admin_user)
        r = api_client.post(f"/api/v1/payroll/periods/{period_with_record.id}/reopen/")
        assert r.status_code == 409

    def test_endpoints_require_authentication(self, api_client, period_with_record):
        url = f"/api/v1/payroll/periods/{period_with_record.id}/submit-for-review/"
        res = api_client.post(url)
        assert res.status_code in (401, 403)
