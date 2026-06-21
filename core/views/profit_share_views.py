"""Profit-share page views (Phase 8).

Server-rendered Django pages that host the profit-share UI. The heavy data is
loaded by AJAX from the leak-proof ``/api/v1/profit-share/`` endpoints; these
views only render the shell + the minimal server-side context that forms need
(account/project pickers), and enforce role access via ``core.access`` guards.

Pages:
  * ``profit_share_my_earnings``  — socio/director: "Mis Ganancias".
  * ``profit_share_director_panel`` — director: included projects, balances,
    business cash, advances, rate configuration.
  * ``profit_share_calculator``   — director: cascade calculator with an
    estimado/real toggle (overhead shown neutrally).
"""
from __future__ import annotations

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from core import access
from core.models import PartnerAccount, Project, RateConfig


@login_required
def profit_share_my_earnings(request):
    """"Mis Ganancias" — a socio sees ONLY their own numbers (enforced by the
    API). The director may also open it to view their own account."""
    guard = access.require_profit_share_access_or_redirect(request)
    if guard is not None:
        return guard

    has_account = PartnerAccount.objects.filter(owner=request.user).exists()
    context = {
        "is_director": access.is_director(request.user),
        "has_account": has_account,
    }
    return render(request, "core/profit_share/my_earnings.html", context)


@login_required
def profit_share_director_panel(request):
    """Director cockpit: included projects, member balances, business cash,
    advances, and the rate configuration. Director-only."""
    guard = access.require_director_or_redirect(request)
    if guard is not None:
        return guard

    accounts = (
        PartnerAccount.objects.select_related("owner")
        .order_by("-is_business", "owner__first_name", "owner__last_name")
    )
    projects = Project.objects.order_by("name").values(
        "id", "name", "in_profit_share", "end_date"
    )
    project_rows = [
        {
            "id": p["id"],
            "name": p["name"],
            "in_profit_share": p["in_profit_share"],
            "status": "real" if p["end_date"] is not None else "estimado",
        }
        for p in projects
    ]
    context = {
        "accounts": accounts,
        "projects": project_rows,
        "rate_config": RateConfig.load(),
        "business_account": PartnerAccount.business(),
    }
    return render(request, "core/profit_share/director_panel.html", context)


@login_required
def profit_share_calculator(request):
    """Cascade calculator with estimado/real toggle. Director-only."""
    guard = access.require_director_or_redirect(request)
    if guard is not None:
        return guard

    projects = Project.objects.order_by("name").values(
        "id", "name", "in_profit_share", "end_date"
    )
    project_rows = [
        {
            "id": p["id"],
            "name": p["name"],
            "in_profit_share": p["in_profit_share"],
            "status": "real" if p["end_date"] is not None else "estimado",
        }
        for p in projects
    ]
    context = {"projects": project_rows}
    return render(request, "core/profit_share/calculator.html", context)
