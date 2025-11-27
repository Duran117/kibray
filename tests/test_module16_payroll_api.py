from datetime import date, timedelta

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from core.models import Employee, PayrollPeriod, PayrollRecord, Project

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    return User.objects.create_user(username="payadmin", password="pass123", email="payadmin@example.com")


@pytest.fixture
def employee(db):
    return Employee.objects.create(
        first_name="Jon", last_name="Snow", social_security_number="111-22-3333", hourly_rate="30.00"
    )


@pytest.fixture
def week_bounds():
    start = date(2025, 11, 17)  # Monday
    end = start + timedelta(days=6)
    return start, end


@pytest.mark.django_db
class TestPayrollAPI:
    def test_period_approve_and_record_payment(self, api_client, user, employee, week_bounds):
        api_client.force_authenticate(user=user)
        week_start, week_end = week_bounds
        # Ensure at least one project exists for expense linkage
        Project.objects.create(name="Payroll Project", client="ACME", start_date=week_start)
        # Create period
        p_res = api_client.post(
            "/api/v1/payroll/periods/",
            {"week_start": week_start.isoformat(), "week_end": week_end.isoformat(), "notes": "Test period"},
            format="json",
        )
        assert p_res.status_code == 201
        period_id = p_res.data["id"]
        # Create record
        r_res = api_client.post(
            "/api/v1/payroll/records/",
            {
                "period": period_id,
                "employee": employee.id,
                "week_start": week_start.isoformat(),
                "week_end": week_end.isoformat(),
                "total_hours": "42.00",
                "hourly_rate": "30.00",
                "regular_hours": "40.00",
                "overtime_hours": "2.00",
                "bonus": "50.00",
                "deductions": "10.00",
                "tax_withheld": "0.00",
                "total_pay": "0.00",  # will be recalculated in UI normally
            },
            format="json",
        )
        assert r_res.status_code == 201
        rec_id = r_res.data["id"]
        # Manual adjust: set the final pay directly to simulate computed values
        adj = api_client.post(
            f"/api/v1/payroll/records/{rec_id}/manual_adjust/",
            {"reason": "set totals", "updates": {"gross_pay": "1310.00", "net_pay": "1300.00", "total_pay": "1300.00"}},
            format="json",
        )
        assert adj.status_code == 200
        # Approve period (skip validation to avoid time entry checks)
        a_res = api_client.post(
            f"/api/v1/payroll/periods/{period_id}/approve/", {"skip_validation": True}, format="json"
        )
        assert a_res.status_code == 200
        # Create partial payment
        pay_res = api_client.post(
            "/api/v1/payroll/payments/",
            {
                "payroll_record": rec_id,
                "amount": "500.00",
                "payment_date": week_end.isoformat(),
                "payment_method": "check",
                "check_number": "1001",
            },
            format="json",
        )
        assert pay_res.status_code in (201, 200)
        # Fetch record and verify balances
        r_get = api_client.get(f"/api/v1/payroll/records/{rec_id}/")
        assert r_get.status_code == 200
        assert float(r_get.data["amount_paid"]) == 500.0
        assert float(r_get.data["balance_due"]) == 800.0
        # Create expense linkage
        exp_res = api_client.post(f"/api/v1/payroll/records/{rec_id}/create_expense/", {}, format="json")
        assert exp_res.status_code == 200
        assert "expense_id" in exp_res.data
