"""
Tests for core/views/payroll_views.py

Covers the 4 view functions:
- payroll_weekly_review (admin-only weekly payroll review/approval)
- payroll_record_payment (record payment for a PayrollRecord)
- payroll_payment_history (list payment history)
- employee_savings_ledger (employee savings/withdrawals)

Strategy: smoke tests (auth, GET, basic POST) using Django test client.
Heavy POST flows are covered via direct model + view interaction.
"""
from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

User = get_user_model()


# ---------- Fixtures ----------

@pytest.fixture
def admin_user(db):
    return User.objects.create_user(
        username="pay_admin", password="x", is_staff=True, is_superuser=True
    )


@pytest.fixture
def employee_user(db):
    from core.models import Profile
    u = User.objects.create_user(username="pay_emp_user", password="x")
    Profile.objects.update_or_create(user=u, defaults={"role": "employee"})
    u.refresh_from_db()
    return u


@pytest.fixture
def employee(db):
    from core.models import Employee
    return Employee.objects.create(
        first_name="Test",
        last_name="Worker",
        social_security_number="111-22-3333",
        hourly_rate=Decimal("25.00"),
        is_active=True,
    )


@pytest.fixture
def employee2(db):
    from core.models import Employee
    return Employee.objects.create(
        first_name="Other",
        last_name="Person",
        social_security_number="999-88-7777",
        hourly_rate=Decimal("30.00"),
        is_active=True,
    )


@pytest.fixture
def week_start():
    """Monday of the current week."""
    today = date.today()
    return today - timedelta(days=today.weekday())


@pytest.fixture
def payroll_record(db, employee, admin_user, week_start):
    from core.models import PayrollPeriod, PayrollRecord
    period, _ = PayrollPeriod.objects.get_or_create(
        week_start=week_start,
        week_end=week_start + timedelta(days=6),
        defaults={"created_by": admin_user},
    )
    return PayrollRecord.objects.create(
        period=period,
        employee=employee,
        week_start=week_start,
        week_end=week_start + timedelta(days=6),
        total_hours=Decimal("40.00"),
        hourly_rate=Decimal("25.00"),
        total_pay=Decimal("1000.00"),
    )


# ---------- payroll_weekly_review ----------

class TestPayrollWeeklyReview:
    def test_anonymous_redirected(self, client):
        url = reverse("payroll_weekly_review")
        resp = client.get(url)
        assert resp.status_code == 302
        assert "/login" in resp.url or "/accounts/login" in resp.url

    def test_employee_denied(self, client, employee_user):
        client.force_login(employee_user)
        url = reverse("payroll_weekly_review")
        resp = client.get(url)
        # Should redirect to dashboard (admin-only)
        assert resp.status_code == 302

    def test_admin_can_view(self, client, admin_user, employee):
        client.force_login(admin_user)
        url = reverse("payroll_weekly_review")
        resp = client.get(url)
        assert resp.status_code == 200

    def test_admin_can_view_specific_week(self, client, admin_user, week_start):
        client.force_login(admin_user)
        url = reverse("payroll_weekly_review") + f"?week_start={week_start.isoformat()}"
        resp = client.get(url)
        assert resp.status_code == 200

    def test_invalid_week_start_falls_back_to_current(self, client, admin_user):
        client.force_login(admin_user)
        url = reverse("payroll_weekly_review") + "?week_start=not-a-date"
        resp = client.get(url)
        assert resp.status_code == 200

    def test_post_update_records_no_data(self, client, admin_user, employee):
        """POST with action=update_records but no time entries — should not error."""
        client.force_login(admin_user)
        url = reverse("payroll_weekly_review")
        resp = client.post(url, {"action": "update_records"})
        # Either redirect or success render; must not 500
        assert resp.status_code in (200, 302)


# ---------- payroll_record_payment ----------

class TestPayrollRecordPayment:
    def test_anonymous_redirected(self, client, payroll_record):
        url = reverse("payroll_record_payment", args=[payroll_record.id])
        resp = client.get(url)
        assert resp.status_code == 302

    def test_employee_denied(self, client, employee_user, payroll_record):
        client.force_login(employee_user)
        url = reverse("payroll_record_payment", args=[payroll_record.id])
        resp = client.get(url)
        assert resp.status_code == 302

    def test_admin_get_renders_form(self, client, admin_user, payroll_record):
        client.force_login(admin_user)
        url = reverse("payroll_record_payment", args=[payroll_record.id])
        resp = client.get(url)
        assert resp.status_code == 200

    def test_nonexistent_record_returns_404(self, client, admin_user):
        client.force_login(admin_user)
        url = reverse("payroll_record_payment", args=[999999])
        resp = client.get(url)
        assert resp.status_code == 404

    def test_post_valid_payment_creates_payment(self, client, admin_user, payroll_record):
        from core.models import PayrollPayment
        client.force_login(admin_user)
        url = reverse("payroll_record_payment", args=[payroll_record.id])
        resp = client.post(url, {
            "amount": "1000.00",
            "amount_taken": "1000.00",
            "amount_saved": "0",
            "payment_date": date.today().isoformat(),
            "payment_method": "check",
            "check_number": "1234",
            "notes": "Test payment",
        })
        # Should redirect to weekly review on success
        assert resp.status_code == 302
        assert PayrollPayment.objects.filter(payroll_record=payroll_record).count() == 1

    def test_post_invalid_split_shows_error(self, client, admin_user, payroll_record):
        """amount_taken + amount_saved != amount → error and no payment created."""
        from core.models import PayrollPayment
        client.force_login(admin_user)
        url = reverse("payroll_record_payment", args=[payroll_record.id])
        resp = client.post(url, {
            "amount": "1000.00",
            "amount_taken": "500.00",
            "amount_saved": "100.00",  # mismatch: 500+100 != 1000
            "payment_date": date.today().isoformat(),
            "payment_method": "check",
        })
        # Redirect back to same page with error message
        assert resp.status_code == 302
        assert PayrollPayment.objects.filter(payroll_record=payroll_record).count() == 0

    def test_post_with_savings_creates_payment(self, client, admin_user, payroll_record):
        from core.models import PayrollPayment
        client.force_login(admin_user)
        url = reverse("payroll_record_payment", args=[payroll_record.id])
        resp = client.post(url, {
            "amount": "1000.00",
            "amount_taken": "700.00",
            "amount_saved": "300.00",
            "payment_date": date.today().isoformat(),
            "payment_method": "cash",
        })
        assert resp.status_code == 302
        p = PayrollPayment.objects.filter(payroll_record=payroll_record).first()
        assert p is not None
        assert p.amount_saved == Decimal("300.00")


# ---------- payroll_payment_history ----------

class TestPayrollPaymentHistory:
    def test_anonymous_redirected(self, client):
        url = reverse("payroll_payment_history")
        resp = client.get(url)
        assert resp.status_code == 302

    def test_employee_denied(self, client, employee_user):
        client.force_login(employee_user)
        url = reverse("payroll_payment_history")
        resp = client.get(url)
        assert resp.status_code == 302

    def test_admin_view_all(self, client, admin_user, payroll_record):
        client.force_login(admin_user)
        url = reverse("payroll_payment_history")
        resp = client.get(url)
        assert resp.status_code == 200

    def test_admin_view_specific_employee(self, client, admin_user, employee, payroll_record):
        client.force_login(admin_user)
        url = reverse("payroll_payment_history_employee", args=[employee.id])
        resp = client.get(url)
        assert resp.status_code == 200

    def test_nonexistent_employee_returns_404(self, client, admin_user):
        client.force_login(admin_user)
        url = reverse("payroll_payment_history_employee", args=[999999])
        resp = client.get(url)
        assert resp.status_code == 404


# ---------- employee_savings_ledger ----------

class TestEmployeeSavingsLedger:
    def test_anonymous_redirected(self, client):
        url = reverse("employee_savings_ledger")
        resp = client.get(url)
        assert resp.status_code == 302

    def test_employee_denied(self, client, employee_user):
        client.force_login(employee_user)
        url = reverse("employee_savings_ledger")
        resp = client.get(url)
        assert resp.status_code == 302

    def test_admin_view_all(self, client, admin_user, employee):
        client.force_login(admin_user)
        url = reverse("employee_savings_ledger")
        resp = client.get(url)
        assert resp.status_code == 200

    def test_admin_view_specific_employee(self, client, admin_user, employee):
        client.force_login(admin_user)
        url = reverse("employee_savings_ledger_employee", args=[employee.id])
        resp = client.get(url)
        assert resp.status_code == 200

    def test_post_withdrawal_creates_record(self, client, admin_user, employee):
        """First create savings, then withdraw."""
        from core.models import EmployeeSavings
        # Seed a deposit so balance > 0
        EmployeeSavings.objects.create(
            employee=employee,
            amount=Decimal("500.00"),
            transaction_type="deposit",
            date=date.today(),
            notes="seed",
            recorded_by=admin_user,
        )
        client.force_login(admin_user)
        url = reverse("employee_savings_ledger")
        resp = client.post(url, {
            "action": "withdrawal",
            "employee_id": str(employee.id),
            "amount": "100.00",
            "date": date.today().isoformat(),
            "notes": "Test withdrawal",
        })
        # Should render or redirect — must not 500
        assert resp.status_code in (200, 302)
        # Withdrawal should be recorded
        assert EmployeeSavings.objects.filter(
            employee=employee, transaction_type="withdrawal"
        ).count() == 1

    def test_post_overdraft_without_confirm_warns(self, client, admin_user, employee):
        """Withdrawal > balance without confirm_overdraft should NOT create record."""
        from core.models import EmployeeSavings
        client.force_login(admin_user)
        url = reverse("employee_savings_ledger")
        resp = client.post(url, {
            "action": "withdrawal",
            "employee_id": str(employee.id),
            "amount": "100.00",
            "date": date.today().isoformat(),
            "notes": "Trying overdraft",
        })
        assert resp.status_code in (200, 302)
        # No withdrawal created (only warning)
        assert EmployeeSavings.objects.filter(
            employee=employee, transaction_type="withdrawal"
        ).count() == 0

    def test_post_overdraft_with_confirm_creates_record(self, client, admin_user, employee):
        from core.models import EmployeeSavings
        client.force_login(admin_user)
        url = reverse("employee_savings_ledger")
        resp = client.post(url, {
            "action": "withdrawal",
            "employee_id": str(employee.id),
            "amount": "100.00",
            "date": date.today().isoformat(),
            "notes": "Confirmed overdraft",
            "confirm_overdraft": "yes",
        })
        assert resp.status_code in (200, 302)
        w = EmployeeSavings.objects.filter(
            employee=employee, transaction_type="withdrawal"
        ).first()
        assert w is not None
        assert "[OVERDRAFT]" in w.notes


# ---------- NEW: "Save All" to savings + Manual Deposit (anti-conflict) ----------

def _make_time_entry(employee, day, start="08:00", end="16:30"):
    """Create a TimeEntry yielding 8.0h (08:00–16:30 minus 0.5h lunch)."""
    from datetime import datetime
    from core.models import TimeEntry
    return TimeEntry.objects.create(
        employee=employee,
        date=day,
        start_time=datetime.strptime(start, "%H:%M").time(),
        end_time=datetime.strptime(end, "%H:%M").time(),
    )


def _day_fields(employee, week_start, day, start="08:00", end="16:30"):
    """Build the per-day start/end POST fields the real form always submits.

    Without these, the weekly-review handler treats the day as 'cleared' and
    DELETES the existing TimeEntry. The real browser form always posts the
    existing times, so tests must mirror that to preserve hours.
    """
    idx = (day - week_start).days
    return {
        f"start_{employee.id}_{idx}": start,
        f"end_{employee.id}_{idx}": end,
    }


class TestSaveAllToSavings:
    """'Save All' = send the full check to savings in one click.

    Validates the happy path plus the anti-conflict guards the user demanded:
    no duplicates on double-submit, and no paying something already saved.
    """

    def test_save_all_sends_full_check_to_savings(self, client, admin_user, employee, week_start):
        from core.models import PayrollPayment, EmployeeSavings, PayrollRecord
        _make_time_entry(employee, week_start)  # 8h -> $200
        client.force_login(admin_user)
        url = reverse("payroll_weekly_review") + f"?week_start={week_start.isoformat()}"
        resp = client.post(url, {
            "action": "update_records",
            f"pay_action_{employee.id}": "save_all",
            f"pay_date_{employee.id}": week_start.isoformat(),
            **_day_fields(employee, week_start, week_start),
        })
        assert resp.status_code in (200, 302)
        record = PayrollRecord.objects.get(employee=employee, week_start=week_start)
        assert record.total_pay == Decimal("200.00")
        # Exactly one payment, 100% saved, nothing taken
        pay = PayrollPayment.objects.filter(payroll_record=record)
        assert pay.count() == 1
        assert pay.first().amount_taken == Decimal("0")
        assert pay.first().amount_saved == Decimal("200.00")
        # Deposit reflected in savings balance; record now fully settled
        assert EmployeeSavings.get_employee_balance(employee) == Decimal("200.00")
        assert record.balance_due() == Decimal("0")

    def test_save_all_double_submit_no_duplicate(self, client, admin_user, employee, week_start):
        """Submitting 'Save All' twice must NOT create a second deposit."""
        from core.models import PayrollPayment, EmployeeSavings, PayrollRecord
        _make_time_entry(employee, week_start)
        client.force_login(admin_user)
        url = reverse("payroll_weekly_review") + f"?week_start={week_start.isoformat()}"
        data = {
            "action": "update_records",
            f"pay_action_{employee.id}": "save_all",
            f"pay_date_{employee.id}": week_start.isoformat(),
            **_day_fields(employee, week_start, week_start),
        }
        client.post(url, data)
        client.post(url, data)  # duplicate submit
        record = PayrollRecord.objects.get(employee=employee, week_start=week_start)
        assert PayrollPayment.objects.filter(payroll_record=record).count() == 1
        assert EmployeeSavings.get_employee_balance(employee) == Decimal("200.00")

    def test_save_all_then_pay_is_blocked(self, client, admin_user, employee, week_start):
        """After saving the full check, a later normal payment must be ignored
        (balance already settled) — cannot pay something already saved."""
        from core.models import PayrollPayment, PayrollRecord
        _make_time_entry(employee, week_start)
        client.force_login(admin_user)
        url = reverse("payroll_weekly_review") + f"?week_start={week_start.isoformat()}"
        client.post(url, {
            "action": "update_records",
            f"pay_action_{employee.id}": "save_all",
            f"pay_date_{employee.id}": week_start.isoformat(),
            **_day_fields(employee, week_start, week_start),
        })
        # Attempt a normal payment afterwards
        client.post(url, {
            "action": "update_records",
            f"pay_action_{employee.id}": "pay",
            f"paid_{employee.id}": "200.00",
            f"pay_date_{employee.id}": week_start.isoformat(),
            **_day_fields(employee, week_start, week_start),
        })
        record = PayrollRecord.objects.get(employee=employee, week_start=week_start)
        # Still only the original save_all payment
        assert PayrollPayment.objects.filter(payroll_record=record).count() == 1
        assert record.balance_due() == Decimal("0")

    def test_normal_pay_still_works_with_action_pay(self, client, admin_user, employee, week_start):
        """Regression: explicit pay_action='pay' must behave like before."""
        from core.models import PayrollPayment, PayrollRecord
        _make_time_entry(employee, week_start)
        client.force_login(admin_user)
        url = reverse("payroll_weekly_review") + f"?week_start={week_start.isoformat()}"
        client.post(url, {
            "action": "update_records",
            f"pay_action_{employee.id}": "pay",
            f"paid_{employee.id}": "200.00",
            f"pay_date_{employee.id}": week_start.isoformat(),
            **_day_fields(employee, week_start, week_start),
        })
        record = PayrollRecord.objects.get(employee=employee, week_start=week_start)
        pay = PayrollPayment.objects.filter(payroll_record=record).first()
        assert pay is not None
        assert pay.amount_taken == Decimal("200.00")
        assert pay.amount_saved == Decimal("0")


class TestManualDeposit:
    """Manual deposit button on the savings ledger (deposits OUTSIDE payroll)."""

    def test_manual_deposit_creates_savings(self, client, admin_user, employee):
        from core.models import EmployeeSavings
        client.force_login(admin_user)
        url = reverse("employee_savings_ledger")
        resp = client.post(url, {
            "action": "deposit",
            "employee_id": str(employee.id),
            "amount": "150.00",
            "date": date.today().isoformat(),
            "notes": "Cash handed to hold",
        })
        assert resp.status_code in (200, 302)
        deposits = EmployeeSavings.objects.filter(
            employee=employee, transaction_type="deposit"
        )
        assert deposits.count() == 1
        assert deposits.first().amount == Decimal("150.00")
        assert EmployeeSavings.get_employee_balance(employee) == Decimal("150.00")

    def test_manual_deposit_rejects_zero(self, client, admin_user, employee):
        """A zero/negative deposit must be rejected (no record created)."""
        from core.models import EmployeeSavings
        client.force_login(admin_user)
        url = reverse("employee_savings_ledger")
        resp = client.post(url, {
            "action": "deposit",
            "employee_id": str(employee.id),
            "amount": "0",
            "date": date.today().isoformat(),
        })
        assert resp.status_code in (200, 302)
        assert EmployeeSavings.objects.filter(
            employee=employee, transaction_type="deposit"
        ).count() == 0

    def test_manual_deposit_does_not_double_count_with_payroll(
        self, client, admin_user, employee, week_start
    ):
        """A manual deposit is independent from payroll auto-deposits:
        balance = payroll savings + manual deposit (no overlap)."""
        from core.models import EmployeeSavings, PayrollPayment, PayrollRecord
        _make_time_entry(employee, week_start)
        client.force_login(admin_user)
        review_url = reverse("payroll_weekly_review") + f"?week_start={week_start.isoformat()}"
        # Save full $200 check via payroll
        client.post(review_url, {
            "action": "update_records",
            f"pay_action_{employee.id}": "save_all",
            f"pay_date_{employee.id}": week_start.isoformat(),
            **_day_fields(employee, week_start, week_start),
        })
        # Add an independent manual deposit of $50
        ledger_url = reverse("employee_savings_ledger")
        client.post(ledger_url, {
            "action": "deposit",
            "employee_id": str(employee.id),
            "amount": "50.00",
            "date": date.today().isoformat(),
            "notes": "extra",
        })
        # Total balance = 200 (payroll) + 50 (manual) = 250, no double count
        assert EmployeeSavings.get_employee_balance(employee) == Decimal("250.00")
        record = PayrollRecord.objects.get(employee=employee, week_start=week_start)
        assert PayrollPayment.objects.filter(payroll_record=record).count() == 1
