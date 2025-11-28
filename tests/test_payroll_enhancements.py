import pytest
from decimal import Decimal
from datetime import date, timedelta
from django.contrib.auth import get_user_model
from core.models import Employee, PayrollPeriod, PayrollRecord, TaxProfile, Project
from core.services.payroll_recompute import recompute_period

User = get_user_model()

@pytest.fixture
def admin(db):
    return User.objects.create_user(username="adminpay", password="x", email="a@b.com", is_staff=True)

@pytest.fixture
def employee(db):
    return Employee.objects.create(first_name="Ana", last_name="Lopez", social_security_number="222-33-4444", hourly_rate="25.00")

@pytest.fixture
def tax_profile(db):
    return TaxProfile.objects.create(name="Std Flat", method="flat", flat_rate=Decimal("10.00"))

@pytest.fixture
def week_bounds():
    start = date(2025, 11, 17)
    end = start + timedelta(days=6)
    return start, end

@pytest.mark.django_db
def test_recompute_with_tax(admin, employee, tax_profile, week_bounds):
    employee.tax_profile = tax_profile
    employee.save()
    ws, we = week_bounds
    project = Project.objects.create(name="PX", start_date=ws)
    period = PayrollPeriod.objects.create(week_start=ws, week_end=we, created_by=admin)
    record = PayrollRecord.objects.create(
        period=period,
        employee=employee,
        week_start=ws,
        week_end=we,
        total_hours=Decimal("45.00"),
        hourly_rate=Decimal("25.00"),
        bonus=Decimal("100.00"),
        deductions=Decimal("50.00"),
        tax_withheld=Decimal("0.00"),
    )
    count = recompute_period(period)
    assert count == 1
    record.refresh_from_db()
    # Regular 40h + 5h overtime @ 1.5 * 25 = 37.5 => overtime pay 187.5
    # Regular pay 40 * 25 = 1000
    # Gross = 1000 + 187.5 + 100 bonus = 1287.5
    # Tax 10% = 128.75
    # Net = 1287.5 - 50 - 128.75 = 1108.75
    assert record.gross_pay.quantize(Decimal('0.01')) == Decimal('1287.50')
    assert record.tax_withheld == Decimal('128.75')
    assert record.net_pay == Decimal('1108.75')
    assert record.total_pay == record.net_pay
    assert record.recalculated_at is not None
    period.refresh_from_db()
    assert period.recomputed_at is not None

@pytest.mark.django_db
def test_period_lock_blocks_adjust(admin, employee, week_bounds):
    ws, we = week_bounds
    period = PayrollPeriod.objects.create(week_start=ws, week_end=we, created_by=admin, locked=True)
    record = PayrollRecord.objects.create(
        period=period,
        employee=employee,
        week_start=ws,
        week_end=we,
        total_hours=Decimal("10.00"),
        hourly_rate=Decimal("25.00"),
    )
    with pytest.raises(ValueError):
        record.manual_adjust(adjusted_by=admin, reason="test", total_hours=Decimal("12.00"))

@pytest.mark.django_db
def test_audit_log_created(admin, employee, week_bounds):
    ws, we = week_bounds
    period = PayrollPeriod.objects.create(week_start=ws, week_end=we, created_by=admin)
    record = PayrollRecord.objects.create(
        period=period,
        employee=employee,
        week_start=ws,
        week_end=we,
        total_hours=Decimal("10.00"),
        hourly_rate=Decimal("25.00"),
    )
    record.manual_adjust(adjusted_by=admin, reason="rate update", hourly_rate=Decimal("26.00"))
    assert record.audits.count() == 1
    audit = record.audits.first()
    assert 'hourly_rate' in audit.changes
    assert audit.changes['hourly_rate']['old'] == '25.00'
    assert audit.changes['hourly_rate']['new'] == '26.00'
