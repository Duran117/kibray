from dataclasses import dataclass
from datetime import timedelta
from decimal import Decimal
from typing import Any

from django.conf import settings
from django.core.cache import cache
from django.db.models import F, Q, Sum
from django.utils import timezone

from core.models import (
    ChangeOrder,
    Expense,
    Invoice,
    PayrollRecord,
    Project,
    ProjectInventory,
    TimeEntry,
)


class ChangeOrderService:
    """Financial helper for Change Orders including Time & Materials billing calculations."""

    @staticmethod
    def get_billable_amount(change_order: ChangeOrder) -> dict[str, Any]:
        """
        Return billable amount or detailed breakdown depending on pricing type.
        FIXED: returns {'type': 'FIXED', 'total': amount}
        T_AND_M: returns breakdown dict with labor/material details.
        Unbilled TimeEntries & Expenses are those without invoice_line set.
        """
        if change_order.pricing_type == "FIXED":
            return {
                "type": "FIXED",
                "total": change_order.amount,
            }

        # T&M mode
        billing_rate = change_order.get_effective_billing_rate()
        material_markup_pct = change_order.material_markup_percent or Decimal("0")

        # TimeEntries without InvoiceLine: check invoiceline_set (reverse FK from InvoiceLine.time_entry)
        # Since InvoiceLine has time_entry FK, the reverse relation is time_entry.invoiceline (singular by convention)
        # But without explicit related_name, Django creates invoiceline_set or uses the model name lowercase
        # Let's use the model name: InvoiceLine -> time_entry creates reverse as 'invoiceline' (lowercase model name)
        time_qs = change_order.time_entries.exclude(invoiceline__isnull=False)
        expenses_qs = change_order.expenses.exclude(invoiceline__isnull=False)

        labor_hours = sum((te.hours_worked or Decimal("0")) for te in time_qs)
        labor_total = (labor_hours * billing_rate).quantize(Decimal("0.01"))

        raw_material_cost = expenses_qs.aggregate(s=Sum("amount"))["s"] or Decimal("0.00")
        material_total = (
            raw_material_cost * (Decimal("1.00") + material_markup_pct / Decimal("100"))
        ).quantize(Decimal("0.01"))

        return {
            "type": "T_AND_M",
            "billing_rate": billing_rate,
            "material_markup_pct": material_markup_pct,
            "labor_hours": labor_hours,
            "labor_total": labor_total,
            "raw_material_cost": raw_material_cost,
            "material_total": material_total,
            "grand_total": labor_total + material_total,
            "time_entries": list(time_qs),
            "expenses": list(expenses_qs),
        }


@dataclass
class CashFlowProjectionRow:
    label: str
    expected_income: Decimal
    expected_expense: Decimal

    @property
    def net(self) -> Decimal:
        return self.expected_income - self.expected_expense


class FinancialAnalyticsService:
    """Centralized analytics for executive BI dashboard.

    Simplified heuristics (future refinement notes inline):
      - Expected Income: invoices due in horizon (collectible statuses).
      - Expected Expense: avg weekly payroll (last 4 weeks) + avg weekly materials (heuristic filter).
      - Project Margin: (Invoiced - (Labor + Material)) / Invoiced.
      - Burn Rate: avg daily (expenses + payroll) last 30 days.
    """

    COLLECTIBLE_INVOICE_STATUSES = ["SENT", "VIEWED", "APPROVED", "PARTIAL"]

    def __init__(self, as_of=None):
        self.as_of = as_of or timezone.localdate()

    # Cash Flow Projection -------------------------------------------------
    def get_cash_flow_projection(self, days: int = 30) -> dict[str, Any]:
        cache_key = f"fa:cashflow:{self.as_of.isoformat()}:{days}"
        cached = cache.get(cache_key)
        if cached:
            return cached
        horizon_end = self.as_of + timedelta(days=days)
        invoices = (
            Invoice.objects.filter(
                due_date__gte=self.as_of,
                due_date__lte=horizon_end,
                status__in=self.COLLECTIBLE_INVOICE_STATUSES,
            )
            .values("due_date")
            .annotate(amount=Sum("total_amount"))
        )
        income_by_week: dict[str, Decimal] = {}
        for inv in invoices:
            due = inv["due_date"]
            wk = f"W{due.isocalendar().week}"
            income_by_week[wk] = income_by_week.get(wk, Decimal("0")) + (
                inv["amount"] or Decimal("0")
            )

        four_weeks_ago = self.as_of - timedelta(weeks=4)
        payroll = PayrollRecord.objects.filter(
            week_start__gte=four_weeks_ago, week_end__lte=self.as_of
        )
        total_payroll = payroll.aggregate(t=Sum("net_pay"))["t"] or Decimal("0")
        avg_weekly_payroll = total_payroll / Decimal("4") if total_payroll > 0 else Decimal("0")

        material_expenses = Expense.objects.filter(
            date__gte=four_weeks_ago, date__lte=self.as_of
        ).filter(Q(category__icontains="material") | Q(description__icontains="material"))
        total_material = material_expenses.aggregate(t=Sum("amount"))["t"] or Decimal("0")
        avg_weekly_material = total_material / Decimal("4") if total_material > 0 else Decimal("0")

        rows: list[CashFlowProjectionRow] = []
        cursor = self.as_of
        while cursor <= horizon_end:
            wk = f"W{cursor.isocalendar().week}"
            expected_income = income_by_week.get(wk, Decimal("0"))
            expected_expense = avg_weekly_payroll + avg_weekly_material
            rows.append(CashFlowProjectionRow(wk, expected_income, expected_expense))
            cursor += timedelta(days=7)

        chart = {
            "labels": [r.label for r in rows],
            "income": [float(r.expected_income) for r in rows],
            "expense": [float(r.expected_expense) for r in rows],
            "net": [float(r.net) for r in rows],
        }
        payload = {"rows": rows, "chart": chart}
        cache_ttl = getattr(settings, "BI_CACHE_TTL", 300)
        cache.set(cache_key, payload, cache_ttl)
        return payload

    # Project Margins ------------------------------------------------------
    def get_project_margins(self) -> list[dict[str, Any]]:
        cache_key = "fa:project_margins"
        cached = cache.get(cache_key)
        if cached:
            return cached
        data: list[dict[str, Any]] = []
        # Filter active projects (end_date is None or in the future)
        for p in Project.objects.filter(
            Q(end_date__isnull=True) | Q(end_date__gte=self.as_of)
        ).order_by("name"):
            invoiced = p.invoices.aggregate(t=Sum("total_amount"))["t"] or Decimal("0")
            labor_cost = p.timeentry_set.aggregate(
                t=Sum(F("hours_worked") * F("employee__hourly_rate"))
            )["t"] or Decimal("0")
            material_cost = p.expenses.filter(
                Q(category__icontains="material") | Q(description__icontains="material")
            ).aggregate(t=Sum("amount"))["t"] or Decimal("0")
            total_cost = labor_cost + material_cost
            margin_pct = float(((invoiced - total_cost) / invoiced * 100) if invoiced > 0 else 0.0)
            data.append(
                {
                    "project_id": p.id,
                    "project_name": p.name,
                    "invoiced": float(invoiced),
                    "labor_cost": float(labor_cost),
                    "material_cost": float(material_cost),
                    "total_cost": float(total_cost),
                    "margin_pct": margin_pct,
                }
            )
        cache_ttl = getattr(settings, "BI_CACHE_TTL", 300)
        cache.set(cache_key, data, cache_ttl)
        return data

    # Company Health KPIs --------------------------------------------------
    def get_company_health_kpis(self) -> dict[str, Any]:
        cache_key = f"fa:kpis:{self.as_of.isoformat()}"
        cached = cache.get(cache_key)
        if cached:
            return cached
        income_sum = Project.objects.aggregate(t=Sum("total_income"))["t"] or Decimal("0")
        expense_sum = Project.objects.aggregate(t=Sum("total_expenses"))["t"] or Decimal("0")
        net_profit = income_sum - expense_sum
        # Refined receivables: optimized with DB expression (balance > 0)
        from django.db.models import Case, DecimalField, Value, When

        receivables_qs = Invoice.objects.filter(
            status__in=self.COLLECTIBLE_INVOICE_STATUSES
        ).aggregate(
            remaining=Sum(
                Case(
                    When(
                        total_amount__gt=F("amount_paid"), then=F("total_amount") - F("amount_paid")
                    ),
                    default=Value(0),
                    output_field=DecimalField(),
                )
            )
        )
        remaining = receivables_qs["remaining"] or Decimal("0")
        horizon_start = self.as_of - timedelta(days=30)
        expenses_30 = Expense.objects.filter(
            date__gte=horizon_start, date__lte=self.as_of
        ).aggregate(t=Sum("amount"))["t"] or Decimal("0")
        payroll_30 = PayrollRecord.objects.filter(week_start__gte=horizon_start).aggregate(
            t=Sum("net_pay")
        )["t"] or Decimal("0")
        burn_rate = (
            (expenses_30 + payroll_30) / Decimal("30")
            if (expenses_30 + payroll_30) > 0
            else Decimal("0")
        )
        data = {
            "net_profit": float(net_profit),
            "total_receivables": float(remaining),
            "burn_rate": float(burn_rate),
        }
        cache_ttl = getattr(settings, "BI_CACHE_TTL", 300)
        cache.set(cache_key, data, cache_ttl)
        return data

    # Inventory Risk -------------------------------------------------------
    def get_inventory_risk_items(self) -> list[dict[str, Any]]:
        cache_key = "fa:inventory_risk"
        cached = cache.get(cache_key)
        if cached:
            return cached
        items: list[dict[str, Any]] = []
        for s in ProjectInventory.objects.select_related(
            "item", "location", "location__project"
        ).all():
            threshold = s.threshold() or s.item.get_effective_threshold()
            if threshold and s.quantity < threshold:
                items.append(
                    {
                        "item_id": s.item.id,
                        "item_name": s.item.name,
                        "project_id": getattr(s.location.project, "id", None),
                        "project": getattr(s.location.project, "name", None),
                        "location": s.location.name,
                        "quantity": float(s.quantity),
                        "threshold": float(threshold),
                    }
                )
        cache_ttl = getattr(settings, "BI_CACHE_TTL", 300)
        cache.set(cache_key, items, cache_ttl)
        return items

    # Top Performing Employees --------------------------------------------
    def get_top_performing_employees(self, limit: int = 5) -> list[dict[str, Any]]:
        start = self.as_of.replace(day=1)
        end = self.as_of
        entries = (
            TimeEntry.objects.filter(date__gte=start, date__lte=end)
            .values("employee__id", "employee__first_name", "employee__last_name")
            .annotate(
                total_hours=Sum("hours_worked"),
                billable_hours=Sum("hours_worked", filter=Q(change_order__isnull=False)),
            )
        )
        ranked = []
        for e in entries:
            total = e["total_hours"] or Decimal("0")
            billable = e["billable_hours"] or Decimal("0")
            pct = float((billable / total * 100) if total > 0 else 0.0)
            ranked.append(
                {
                    "employee_id": e["employee__id"],
                    "name": f"{e['employee__first_name']} {e['employee__last_name']}",
                    "total_hours": float(total),
                    "billable_hours": float(billable),
                    "productivity_pct": pct,
                }
            )
        ranked.sort(key=lambda r: r["productivity_pct"], reverse=True)
        return ranked[:limit]
