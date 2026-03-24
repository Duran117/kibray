from datetime import date
from decimal import Decimal

from django.utils import timezone

from core.models import Expense, PayrollRecord, TimeEntry


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
    pv = Decimal("0")
    ev = Decimal("0")
    ac = Decimal("0")

    lines = list(project.budget_lines.all())
    for bl in lines:
        baseline_total += bl.baseline_amount or 0

    # PV (lineal por fechas plan)
    for bl in lines:
        planned_pct = line_planned_percent(bl, as_of)
        pv += (bl.baseline_amount or 0) * planned_pct

    # EV (último progreso por línea)
    for bl in lines:
        prog = bl.progress_points.filter(date__lte=as_of).order_by("-date").first()
        if prog:
            ev += (bl.baseline_amount or 0) * (Decimal(prog.percent_complete) / Decimal("100"))

    # AC: Expenses
    exp_qs = Expense.objects.filter(project=project, date__lte=as_of)
    for e in exp_qs:
        ac += Decimal(e.amount or 0)

    # AC: Payroll (PayrollRecord — costos de nómina por proyecto)
    payroll_qs = PayrollRecord.objects.filter(
        week_end__lte=as_of,
    )
    for pr in payroll_qs:
        # Use project_hours JSON breakdown if available, otherwise add full net_pay
        project_hours = pr.project_hours or {}
        project_id_str = str(project.id)
        if project_id_str in project_hours:
            hours = Decimal(str(project_hours[project_id_str].get("hours", 0)))
            rate = Decimal(str(pr.effective_rate()))
            ac += hours * rate
        elif not project_hours:
            # No breakdown available — attribute full pay if period overlaps project
            ac += Decimal(str(pr.net_pay or 0))

    # AC: TimeEntry (solo si tiene rate para no duplicar con nómina)
    te_qs = TimeEntry.objects.filter(project=project, date__lte=as_of)
    for t in te_qs:
        hrs = Decimal(getattr(t, "hours_worked", 0) or 0)
        rate = Decimal(getattr(t, "hourly_rate", 0) or 0)
        if rate:
            ac += hrs * rate

    spi = (ev / pv) if pv else None
    cpi = (ev / ac) if ac else None

    return {
        "date": as_of,
        "baseline_total": baseline_total,
        "PV": pv,
        "EV": ev,
        "AC": ac,
        "SPI": spi,
        "CPI": cpi,
        "percent_complete_cost": (ev / baseline_total * 100) if baseline_total else None,
    }
