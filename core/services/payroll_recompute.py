"""Payroll period recompute service (Gap B).
Recalculates payroll records: splits hours, overtime, gross/net, tax withholding.
"""
from decimal import Decimal

from django.utils import timezone

from core.models import PayrollPeriod
from core.services.payroll_tax import calculate_tax

RECORD_FIELDS_FOR_RECALC = [
    "total_hours", "regular_hours", "overtime_hours", "gross_pay", "net_pay", "total_pay", "tax_withheld"
]

def recompute_period(period: PayrollPeriod, force: bool = False) -> int:
    """Recompute all records in a PayrollPeriod. Returns count of recomputed records.
    Skips if locked unless force.
    """
    if period.locked and not force:
        raise ValueError("Period is locked; use force=True to override.")

    count = 0
    for record in period.records.select_related("employee", "employee__tax_profile"):
        # Split hours
        record.split_hours_regular_overtime()
        # Calculate pay components
        record.calculate_total_pay()
        # Tax withholding
        profile = getattr(record.employee, "tax_profile", None)
        if profile:
            record.tax_withheld = calculate_tax(profile, record.gross_pay)
            # Recompute net after tax if needed
            record.net_pay = (record.gross_pay - record.deductions - record.tax_withheld).quantize(Decimal("0.01"))
            record.total_pay = record.net_pay
        record.recalculated_at = timezone.now()
        record.save(update_fields=[
            "regular_hours", "overtime_hours", "gross_pay", "net_pay", "total_pay", "tax_withheld", "recalculated_at"
        ])
        count += 1

    period.recomputed_at = timezone.now()
    period.save(update_fields=["recomputed_at"])
    return count
