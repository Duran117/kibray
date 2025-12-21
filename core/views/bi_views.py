from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.utils import timezone

from core.services.financial_service import FinancialAnalyticsService


@login_required
def executive_bi_dashboard(request: HttpRequest) -> HttpResponse:
    """Executive BI Dashboard (Module 21).

    Provides consolidated high-level KPIs, cash flow forecast, project margin
    outliers, top performers, and inventory risk in a single dense view.
    """
    service = FinancialAnalyticsService()

    cash_flow = service.get_cash_flow_projection(days=30)
    margins = service.get_project_margins()
    kpis = service.get_company_health_kpis()
    top_employees = service.get_top_performing_employees(limit=8)
    inventory_risk = service.get_inventory_risk_items()

    low_margin_projects = [m for m in margins if m["margin_pct"] < 15.0]
    high_margin_projects = sorted(margins, key=lambda m: m["margin_pct"], reverse=True)[:5]

    context = {
        "today": timezone.localdate(),
        "kpis": kpis,
        "cash_flow_chart_data": cash_flow["chart"],
        "low_margin_projects": low_margin_projects,
        "high_margin_projects": high_margin_projects,
        "top_performing_employees": top_employees,
        "inventory_risk_items": inventory_risk,
    }
    return render(request, "core/dashboard_bi.html", context)
