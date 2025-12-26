"""
FINANCIAL VIEWS - Advanced Financial Reporting & Analytics
Created: 2025-11-13
Purpose: Executive dashboards, aging reports, productivity metrics, export functions
"""

import csv
from datetime import datetime, timedelta
from decimal import Decimal
import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import F, Q, Sum
from django.db.models.functions import Coalesce, TruncMonth
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .models import (
    ChangeOrder,
    Employee,
    EmployeePerformanceMetric,
    Expense,
    Income,
    Invoice,
    Project,
    TimeEntry,
)

# ===========================
# FINANCIAL EXECUTIVE DASHBOARD
# ===========================


@login_required
def financial_dashboard(request):
    """
    Executive financial dashboard with KPIs, charts, and alerts.
    Shows: Revenue, Profit Margin, Cash Flow, Outstanding AR, Alerts
    SOLO ACCESIBLE POR ADMIN/SUPERUSER
    """
    # Solo admin/superuser puede acceder
    if not (request.user.is_superuser or (hasattr(request.user, 'profile') and request.user.profile.role == 'admin')):
        messages.error(request, "No tienes permiso para acceder a esta función.")
        return redirect("dashboard")
    
    today = timezone.now().date()
    current_year = today.year

    # ========== KPIs ==========

    # YTD Revenue (paid invoices only)
    ytd_revenue = Invoice.objects.filter(date_issued__year=current_year, status="paid").aggregate(
        total=Coalesce(Sum("total_amount"), Decimal("0.00"))
    )["total"]

    # YTD Expenses
    ytd_expenses = Expense.objects.filter(date__year=current_year).aggregate(
        total=Coalesce(Sum("amount"), Decimal("0.00"))
    )["total"]

    # Profit Margin
    if ytd_revenue > 0:
        profit_margin = float((ytd_revenue - ytd_expenses) / ytd_revenue * 100)
    else:
        profit_margin = 0.0

    # Outstanding AR (Accounts Receivable)
    outstanding_ar = Invoice.objects.filter(
        status__in=["sent", "viewed", "approved", "partial"]
    ).aggregate(total=Coalesce(Sum("total_amount"), Decimal("0.00")))["total"]

    # Cash Flow this month
    month_start = today.replace(day=1)
    month_income = Income.objects.filter(date__gte=month_start, date__lte=today).aggregate(
        total=Coalesce(Sum("amount"), Decimal("0.00"))
    )["total"]

    month_expenses = Expense.objects.filter(date__gte=month_start, date__lte=today).aggregate(
        total=Coalesce(Sum("amount"), Decimal("0.00"))
    )["total"]

    cash_flow = month_income - month_expenses

    # ========== CHARTS DATA ==========

    # Revenue trend (last 12 months)
    twelve_months_ago = today - timedelta(days=365)
    revenue_by_month = (
        Invoice.objects.filter(date_issued__gte=twelve_months_ago, status="paid")
        .annotate(month=TruncMonth("date_issued"))
        .values("month")
        .annotate(total=Sum("total_amount"))
        .order_by("month")
    )

    revenue_trend = {
        "labels": [item["month"].strftime("%b %Y") for item in revenue_by_month],
        "data": [float(item["total"]) for item in revenue_by_month],
    }

    # Profit per project (top 10 active)
    active_projects = (
        Project.objects.filter(end_date__isnull=True)
        .annotate(
            calc_revenue=Coalesce(
                Sum("invoices__total_amount", filter=Q(invoices__status="paid")), Decimal("0.00")
            ),
            calc_expenses=Coalesce(Sum("expenses__amount"), Decimal("0.00")),
            calc_profit=F("calc_revenue") - F("calc_expenses"),
        )
        .order_by("-calc_profit")[:10]
    )

    profit_per_project = {
        "labels": [p.name for p in active_projects],
        "data": [float(p.calc_profit) for p in active_projects],  # type: ignore
    }

    # Expenses breakdown (this year by category)
    expenses_by_category = (
        Expense.objects.filter(date__year=current_year)
        .values("category")
        .annotate(total=Sum("amount"))
        .order_by("-total")
    )

    expenses_breakdown = {
        "labels": [item["category"] for item in expenses_by_category],
        "data": [float(item["total"]) for item in expenses_by_category],
    }

    # ========== ALERTS ==========

    alerts = []

    # Overdue invoices (>30 days)
    overdue_threshold = today - timedelta(days=30)
    overdue_invoices = Invoice.objects.filter(
        status__in=["sent", "viewed", "approved"], date_issued__lt=overdue_threshold
    )

    if overdue_invoices.exists():
        total_overdue = overdue_invoices.aggregate(Sum("total_amount"))["total_amount__sum"]
        alerts.append(
            {
                "type": "warning",
                "message": f"{overdue_invoices.count()} facturas vencidas (>{30} días) - Total: ${total_overdue:,.2f}",
                "action_url": "/invoices/?status=overdue",
                "action_text": "Ver facturas",
            }
        )

    # Projects over budget
    over_budget_projects = []
    for project in Project.objects.filter(end_date__isnull=True):
        if project.budget_total > 0:
            total_expenses = project.expense_set.aggregate(Sum("amount"))["amount__sum"] or 0
            if total_expenses > project.budget_total:
                variance = total_expenses - project.budget_total
                over_budget_projects.append(
                    {
                        "name": project.name,
                        "budget": project.budget_total,
                        "actual": total_expenses,
                        "variance": variance,
                        "percentage": (variance / project.budget_total * 100)
                        if project.budget_total > 0
                        else 0,
                    }
                )

    if over_budget_projects:
        alerts.append(
            {
                "type": "danger",
                "message": f"{len(over_budget_projects)} proyectos sobre presupuesto",
                "action_url": "/projects/",
                "action_text": "Ver proyectos",
            }
        )

    # Pending change orders awaiting approval
    pending_cos = ChangeOrder.objects.filter(status="pending").count()

    if pending_cos > 0:
        alerts.append(
            {
                "type": "info",
                "message": f"{pending_cos} órdenes de cambio pendientes de aprobación",
                "action_url": "/changeorders/",
                "action_text": "Revisar",
            }
        )

    context = {
        # KPIs
        "ytd_revenue": ytd_revenue,
        "ytd_expenses": ytd_expenses,
        "profit_margin": profit_margin,
        "outstanding_ar": outstanding_ar,
        "cash_flow": cash_flow,
        # Charts
        "revenue_trend": json.dumps(revenue_trend),
        "profit_per_project": json.dumps(profit_per_project),
        "expenses_breakdown": json.dumps(expenses_breakdown),
        # Alerts & Details
        "alerts": alerts,
        "over_budget_projects": over_budget_projects,
        "overdue_invoices": overdue_invoices,
    }

    return render(request, "core/financial_dashboard.html", context)


# ===========================
# INVOICE AGING REPORT
# ===========================


@login_required
def invoice_aging_report(request):
    """
    Invoice aging report showing unpaid invoices by age buckets.
    Buckets: Current (0-30), 31-60, 61-90, 90+ days
    """
    today = timezone.now().date()

    aging_buckets = {
        "current": [],  # 0-30 días
        "30_60": [],  # 31-60 días
        "60_90": [],  # 61-90 días
        "over_90": [],  # >90 días
    }

    unpaid_invoices = (
        Invoice.objects.filter(status__in=["SENT", "VIEWED", "APPROVED", "PARTIAL"])
        .select_related("project")
        .order_by("date_issued")
    )

    for invoice in unpaid_invoices:
        days_outstanding = (today - invoice.date_issued).days

        if days_outstanding <= 30:
            aging_buckets["current"].append(invoice)
        elif days_outstanding <= 60:
            aging_buckets["30_60"].append(invoice)
        elif days_outstanding <= 90:
            aging_buckets["60_90"].append(invoice)
        else:
            aging_buckets["over_90"].append(invoice)

    # Calculate totals
    totals = {}
    for bucket_name, invoices in aging_buckets.items():
        totals[bucket_name] = sum(inv.total_amount for inv in invoices)

    grand_total = sum(totals.values())

    # Calculate percentages
    percentages = {}
    if grand_total > 0:
        for bucket_name, total in totals.items():
            percentages[bucket_name] = float(total / grand_total * 100)
    else:
        percentages = dict.fromkeys(totals.keys(), 0.0)

    context = {
        "aging_buckets": aging_buckets,
        "totals": totals,
        "percentages": percentages,
        "grand_total": grand_total,
        "report_date": today,
    }

    return render(request, "core/invoice_aging_report.html", context)


# ===========================
# PRODUCTIVITY DASHBOARD
# ===========================


@login_required
def productivity_dashboard(request):
    """
    Employee productivity metrics dashboard.
    Shows: Billable hours %, top performers, efficiency trends
    SOLO ACCESIBLE POR ADMIN/SUPERUSER
    """
    # Solo admin/superuser puede acceder
    if not (request.user.is_superuser or (hasattr(request.user, 'profile') and request.user.profile.role == 'admin')):
        messages.error(request, "No tienes permiso para acceder a esta función.")
        return redirect("dashboard")
    
    # Filter by date range (default: this month)
    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")

    if not start_date or not end_date:
        today = timezone.now().date()
        start_date = today.replace(day=1)
        end_date = today
    else:
        start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_date, "%Y-%m-%d").date()

    # ========== OVERALL METRICS ==========

    # Total hours vs billable hours
    time_entries = TimeEntry.objects.filter(date__gte=start_date, date__lte=end_date)

    total_hours = time_entries.aggregate(total=Coalesce(Sum("hours_worked"), Decimal("0.00")))[
        "total"
    ]

    billable_hours = time_entries.filter(change_order__isnull=False).aggregate(  # Assigned to a CO
        total=Coalesce(Sum("hours_worked"), Decimal("0.00"))
    )["total"]

    productivity_rate = float(billable_hours / total_hours * 100) if total_hours > 0 else 0.0

    # ========== EMPLOYEE RANKINGS ==========

    employees = (
        Employee.objects.filter(is_active=True)
        .annotate(
            total_hours=Coalesce(
                Sum(
                    "timeentry__hours_worked",
                    filter=Q(timeentry__date__gte=start_date, timeentry__date__lte=end_date),
                ),
                Decimal("0.00"),
            ),
            billable_hours=Coalesce(
                Sum(
                    "timeentry__hours_worked",
                    filter=Q(
                        timeentry__date__gte=start_date,
                        timeentry__date__lte=end_date,
                        timeentry__change_order__isnull=False,
                    ),
                ),
                Decimal("0.00"),
            ),
        )
        .filter(total_hours__gt=0)
        .order_by("-total_hours")
    )

    # Calculate productivity manually to avoid division by zero in DB
    top_performers = []
    for emp in employees[:10]:
        emp.productivity = float(emp.billable_hours / emp.total_hours * 100) if emp.total_hours > 0 else 0
        top_performers.append(emp)
    
    # Sort by productivity
    top_performers = sorted(top_performers, key=lambda x: x.productivity, reverse=True)
    
    bottom_performers = sorted(top_performers, key=lambda x: x.productivity)[:5] if top_performers else []

    # ========== CHARTS ==========
    # Calculate weekly productivity using Python (DB-agnostic)
    from collections import defaultdict
    weekly_data = defaultdict(lambda: {'total': Decimal('0'), 'billable': Decimal('0')})
    
    for entry in time_entries.values('date', 'hours_worked', 'change_order'):
        week_num = entry['date'].isocalendar()[1]
        weekly_data[week_num]['total'] += entry['hours_worked'] or Decimal('0')
        if entry['change_order']:
            weekly_data[week_num]['billable'] += entry['hours_worked'] or Decimal('0')
    
    # Sort by week number
    sorted_weeks = sorted(weekly_data.items())
    
    productivity_trend = {
        "labels": [f"Semana {week}" for week, _ in sorted_weeks],
        "total_hours": [float(data['total']) for _, data in sorted_weeks],
        "billable_hours": [float(data['billable']) for _, data in sorted_weeks],
    }

    context = {
        "start_date": start_date,
        "end_date": end_date,
        "total_hours": total_hours,
        "billable_hours": billable_hours,
        "productivity_rate": productivity_rate,
        "top_performers": top_performers,
        "bottom_performers": bottom_performers,
        "productivity_trend": json.dumps(productivity_trend),
    }

    return render(request, "core/productivity_dashboard.html", context)


# ===========================
# FINANCIAL EXPORT (para QuickBooks)
# ===========================


@login_required
def export_financial_data(request):
    """
    Export financial data to CSV for importing into QuickBooks or Excel.
    Formats: Income, Expenses, Invoices
    """
    export_type = request.GET.get("type", "expenses")  # expenses, income, invoices
    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")

    # Parse dates
    if start_date and end_date:
        start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
    else:
        # Default: This year
        today = timezone.now().date()
        start_date = today.replace(month=1, day=1)
        end_date = today

    response = HttpResponse(content_type="text/csv")

    if export_type == "expenses":
        response["Content-Disposition"] = (
            f'attachment; filename="expenses_{start_date}_{end_date}.csv"'
        )
        writer = csv.writer(response)

        # Header
        writer.writerow(
            ["Date", "Project", "Category", "Description", "Amount", "Vendor", "Receipt"]
        )

        # Data
        expenses = Expense.objects.filter(date__gte=start_date, date__lte=end_date).order_by("date")

        for expense in expenses:
            writer.writerow(
                [
                    expense.date.strftime("%Y-%m-%d"),
                    expense.project.name if expense.project else "",
                    expense.category,
                    expense.description,
                    float(expense.amount),
                    expense.vendor or "",
                    "Yes" if expense.receipt else "No",
                ]
            )

    elif export_type == "income":
        response["Content-Disposition"] = (
            f'attachment; filename="income_{start_date}_{end_date}.csv"'
        )
        writer = csv.writer(response)

        # Header
        writer.writerow(
            ["Date", "Project", "Amount", "Payment Method", "Reference", "Invoice Number"]
        )

        # Data
        incomes = Income.objects.filter(date__gte=start_date, date__lte=end_date).order_by("date")

        for income in incomes:
            writer.writerow(
                [
                    income.date.strftime("%Y-%m-%d"),
                    income.project.name if income.project else "",
                    float(income.amount),
                    income.payment_method,
                    income.reference_number or "",
                    income.invoice.invoice_number if income.invoice else "",
                ]
            )

    elif export_type == "invoices":
        response["Content-Disposition"] = (
            f'attachment; filename="invoices_{start_date}_{end_date}.csv"'
        )
        writer = csv.writer(response)

        # Header
        writer.writerow(
            [
                "Invoice Number",
                "Date Issued",
                "Date Due",
                "Project",
                "Client",
                "Total Amount",
                "Status",
                "Amount Paid",
                "Balance",
            ]
        )

        # Data
        invoices = Invoice.objects.filter(
            date_issued__gte=start_date, date_issued__lte=end_date
        ).order_by("date_issued")

        for invoice in invoices:
            amount_paid = invoice.payments.aggregate(Sum("amount"))["amount__sum"] or Decimal(
                "0.00"
            )
            balance = invoice.total_amount - amount_paid

            writer.writerow(
                [
                    invoice.invoice_number,
                    invoice.date_issued.strftime("%Y-%m-%d"),
                    invoice.date_due.strftime("%Y-%m-%d") if invoice.date_due else "",
                    invoice.project.name if invoice.project else "",
                    invoice.project.client if invoice.project else "",
                    float(invoice.total_amount),
                    invoice.status,
                    float(amount_paid),
                    float(balance),
                ]
            )

    return response


# ===========================
# EMPLOYEE PERFORMANCE (para bonos)
# ===========================


@login_required
def employee_performance_review(request, employee_id=None):
    """
    View employee performance metrics for bonus evaluation.
    Shows annual summary and allows setting bonus amounts.
    SOLO ACCESIBLE POR ADMIN/SUPERUSER
    """
    # Solo admin/superuser puede acceder
    if not (request.user.is_superuser or (hasattr(request.user, 'profile') and request.user.profile.role == 'admin')):
        messages.error(request, "No tienes permiso para acceder a esta función.")
        return redirect("dashboard")
    
    year = int(request.GET.get("year", timezone.now().year))

    if employee_id:
        # Single employee view
        employee = get_object_or_404(Employee, id=employee_id)

        # Get or create annual metric
        metric, created = EmployeePerformanceMetric.objects.get_or_create(
            employee=employee,
            year=year,
            month__isnull=True,  # Annual metric
        )

        # Auto-calculate metrics
        _update_employee_metrics(metric, year)

        if request.method == "POST":
            # Update manual ratings and bonus
            metric.quality_rating = request.POST.get("quality_rating")
            metric.attitude_rating = request.POST.get("attitude_rating")
            metric.teamwork_rating = request.POST.get("teamwork_rating")
            metric.bonus_amount = request.POST.get("bonus_amount")
            metric.bonus_notes = request.POST.get("bonus_notes", "")
            metric.save()

            return redirect("employee_performance_review", employee_id=employee_id)

        context = {
            "employee": employee,
            "metric": metric,
            "year": year,
        }

        return render(request, "core/employee_performance_detail.html", context)

    else:
        # All employees summary
        employees = Employee.objects.filter(is_active=True)

        metrics = []
        for employee in employees:
            metric, created = EmployeePerformanceMetric.objects.get_or_create(
                employee=employee, year=year, month__isnull=True
            )
            _update_employee_metrics(metric, year)
            metrics.append(metric)

        # Sort by overall score
        metrics.sort(key=lambda m: m.overall_score, reverse=True)

        context = {
            "metrics": metrics,
            "year": year,
            "years": range(timezone.now().year, timezone.now().year - 5, -1),
        }

        return render(request, "core/employee_performance_list.html", context)


def _update_employee_metrics(metric, year):
    """
    Helper function to auto-calculate employee performance metrics.
    """
    # Get all time entries for the year
    time_entries = TimeEntry.objects.filter(employee=metric.employee, date__year=year)

    # Hours
    metric.total_hours_worked = time_entries.aggregate(Sum("hours_worked"))[
        "hours_worked__sum"
    ] or Decimal("0.00")

    metric.billable_hours = time_entries.filter(change_order__isnull=False).aggregate(
        Sum("hours_worked")
    )["hours_worked__sum"] or Decimal("0.00")

    if metric.total_hours_worked > 0:
        metric.productivity_rate = metric.billable_hours / metric.total_hours_worked * 100

    # Attendance (simplified - assumes 1 entry per day worked)
    metric.days_worked = time_entries.values("date").distinct().count()

    metric.save()
