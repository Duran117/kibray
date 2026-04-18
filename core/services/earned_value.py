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


def compute_project_ev(project, as_of=None, prefetched_ac=None):
    """Compute EVM metrics for a single project.

    Args:
        project: Project instance.
        as_of: date for computation (default today).
        prefetched_ac: Optional Decimal pre-calculated AC (Actual Cost). When
            calling this in a loop over many projects, prefer
            ``bulk_compute_actual_costs(projects, as_of)`` to compute all ACs
            in 3 queries total instead of 3 per project.
    """
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

    # EV (último progreso por línea) — use prefetched progress_points if available
    for bl in lines:
        # If progress_points were prefetched, filter in Python to avoid N+1.
        # Otherwise fall back to a DB query.
        if "progress_points" in getattr(bl, "_prefetched_objects_cache", {}):
            candidates = [p for p in bl.progress_points.all() if p.date <= as_of]
            prog = max(candidates, key=lambda p: p.date) if candidates else None
        else:
            prog = bl.progress_points.filter(date__lte=as_of).order_by("-date").first()
        if prog:
            ev += (bl.baseline_amount or 0) * (Decimal(prog.percent_complete) / Decimal("100"))

    # AC: bulk-pre-computed cost (preferred) OR per-project fallback (legacy)
    if prefetched_ac is not None:
        ac = Decimal(prefetched_ac)
    else:
        # Expenses
        exp_qs = Expense.objects.filter(project=project, date__lte=as_of)
        for e in exp_qs:
            ac += Decimal(e.amount or 0)

        # Payroll (PayrollRecord — costos de nómina por proyecto)
        payroll_qs = PayrollRecord.objects.filter(week_end__lte=as_of)
        for pr in payroll_qs:
            project_hours = pr.project_hours or {}
            project_id_str = str(project.id)
            if project_id_str in project_hours:
                hours = Decimal(str(project_hours[project_id_str].get("hours", 0)))
                rate = Decimal(str(pr.effective_rate()))
                ac += hours * rate
            elif not project_hours:
                ac += Decimal(str(pr.net_pay or 0))

        # TimeEntry: legacy code referenced ``t.hourly_rate`` which does not
        # exist on the TimeEntry model — getattr fallback returned 0, so this
        # branch never contributed to AC. Preserved as no-op for parity.

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


def bulk_compute_actual_costs(project_ids, as_of=None):
    """Compute Actual Cost (AC) for many projects in a constant number of queries.

    Returns: dict {project_id: Decimal AC}.

    Replaces the per-project Expense/Payroll/TimeEntry loops inside
    ``compute_project_ev`` when iterating over many projects (dashboards).
    """
    from django.db.models import F, Sum, DecimalField
    from django.db.models.functions import Coalesce

    if as_of is None:
        as_of = timezone.now().date()

    project_ids = list(project_ids)
    if not project_ids:
        return {}

    ac_by_project = {pid: Decimal("0") for pid in project_ids}

    # Expenses — one grouped query
    exp_rows = (
        Expense.objects.filter(project_id__in=project_ids, date__lte=as_of)
        .values("project_id")
        .annotate(total=Coalesce(Sum("amount"), Decimal("0"), output_field=DecimalField()))
    )
    for row in exp_rows:
        ac_by_project[row["project_id"]] += Decimal(row["total"] or 0)

    # TimeEntry intentionally skipped — legacy code referenced a non-existent
    # ``hourly_rate`` field on TimeEntry, so it never contributed to AC.

    # Payroll — one query, attributed via project_hours JSON or net_pay fallback
    payroll_qs = PayrollRecord.objects.filter(week_end__lte=as_of)
    for pr in payroll_qs:
        project_hours = pr.project_hours or {}
        if project_hours:
            try:
                rate = Decimal(str(pr.effective_rate()))
            except Exception:
                rate = Decimal("0")
            for pid_str, info in project_hours.items():
                try:
                    pid = int(pid_str)
                except (TypeError, ValueError):
                    continue
                if pid not in ac_by_project:
                    continue
                hours = Decimal(str((info or {}).get("hours", 0)))
                ac_by_project[pid] += hours * rate
        else:
            # Legacy fallback: full net_pay attributed to every project (matches
            # the legacy per-project loop semantics).
            net = Decimal(str(pr.net_pay or 0))
            for pid in ac_by_project:
                ac_by_project[pid] += net

    return ac_by_project
