from datetime import date
from decimal import Decimal

from django.utils import timezone

from core.models import Expense, TimeEntry


def line_planned_percent(line, as_of: date) -> Decimal:
    if not line.planned_start or not line.planned_finish:
        return Decimal("1")
    if as_of <= line.planned_start:
        return Decimal("0")
    if as_of >= line.planned_finish:
        return Decimal("1")
    total_days = (line.planned_finish - line.planned_start).days
    if total_days <= 0:
        return Decimal("1")
    done_days = (as_of - line.planned_start).days
    return Decimal(done_days) / Decimal(total_days)


def compute_project_ev(project, as_of=None):
    if as_of is None:
        as_of = timezone.now().date()

    baseline_total = Decimal("0")
    PV = Decimal("0")
    EV = Decimal("0")
    AC = Decimal("0")

    lines = list(project.budget_lines.all())
    for bl in lines:
        baseline_total += bl.baseline_amount or 0

    # PV (lineal por fechas plan)
    for bl in lines:
        planned_pct = line_planned_percent(bl, as_of)
        PV += (bl.baseline_amount or 0) * planned_pct

    # EV (último progreso por línea)
    for bl in lines:
        prog = bl.progress_points.filter(date__lte=as_of).order_by("-date").first()
        if prog:
            EV += (bl.baseline_amount or 0) * (Decimal(prog.percent_complete) / Decimal("100"))

    # AC: Expenses
    exp_qs = Expense.objects.filter(project=project, date__lte=as_of)
    for e in exp_qs:
        AC += Decimal(e.amount or 0)

    # AC: PayrollEntry (si existe el modelo)
    try:
        from core.models import PayrollEntry

        pe_qs = PayrollEntry.objects.filter(payroll__project=project, payroll__week_end__lte=as_of)
        for pe in pe_qs:
            hrs = Decimal(pe.hours_worked or 0)
            rate = Decimal(pe.hourly_rate or 0)
            AC += hrs * rate
    except Exception:
        pass

    # AC: TimeEntry (solo si tiene rate para no duplicar con nómina)
    try:
        te_qs = TimeEntry.objects.filter(project=project, date__lte=as_of)
        for t in te_qs:
            hrs = Decimal(getattr(t, "hours_worked", 0) or 0)
            rate = Decimal(getattr(t, "hourly_rate", 0) or 0)
            if rate:
                AC += hrs * rate
    except Exception:
        pass

    SPI = (EV / PV) if PV else None
    CPI = (EV / AC) if AC else None

    return {
        "date": as_of,
        "baseline_total": baseline_total,
        "PV": PV,
        "EV": EV,
        "AC": AC,
        "SPI": SPI,
        "CPI": CPI,
        "percent_complete_cost": (EV / baseline_total * 100) if baseline_total else None,
    }
