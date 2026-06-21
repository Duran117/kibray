"""Profit-share API (Phase 7) — DRF endpoints with leak-proof permissions.

Endpoints (all under /api/):
    GET  profit-share/projects/                 included projects ("the list")
    GET  profit-share/projects/<id>/breakdown/  full cascade + split
    POST profit-share/projects/<id>/set/        mark in_profit_share (director)
    POST profit-share/accounts/<id>/advance/    advance/withdrawal (director)
    GET  profit-share/me/summary/               my totals (self only)
    GET  profit-share/me/by-project/            my accrual per project (self)
    GET  profit-share/me/ledger/                my movements (self)
    GET/PUT profit-share/rates/                 RateConfig (director)

Leak rules enforced here:
  - "me/*" is ALWAYS scoped to request.user's own PartnerAccount. A socio can
    never read another member's earnings.
  - breakdown shows the project cascade + the equal split (transparency), but
    the direction-overhead DESTINATION is hidden from non-directors, and no
    other member's global balance/advances are exposed. Overhead is a neutral
    cost line.
  - mutating endpoints (set/advance/rates) are director-only.
"""
from __future__ import annotations

from decimal import Decimal

from django.shortcuts import get_object_or_404
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from core import access
from core.models import (
    LedgerEntry,
    PartnerAccount,
    Project,
    ProjectAccrualState,
    RateConfig,
)
from core.services.profit_share_service import (
    compute_project_financials,
    record_advance,
)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers & permissions
# ─────────────────────────────────────────────────────────────────────────────
def _resolve_account(user):
    """The PartnerAccount owned by this user (socio or director), or None."""
    if not user or not user.is_authenticated:
        return None
    return PartnerAccount.objects.filter(owner=user).first()


class IsDirector(permissions.BasePermission):
    message = "Director (owner/admin) role required."

    def has_permission(self, request, view):
        return access.is_director(request.user)


class IsPartnerOrDirector(permissions.BasePermission):
    """Read access for the transparency views: partners and the director."""

    message = "Partner or director role required."

    def has_permission(self, request, view):
        u = request.user
        return access.is_director(u) or access.is_partner(u)


def _project_status(project) -> str:
    return "real" if project.end_date is not None else "estimado"


# ─────────────────────────────────────────────────────────────────────────────
# Project list & breakdown
# ─────────────────────────────────────────────────────────────────────────────
class ProfitShareProjectsListView(APIView):
    """The "list" of the new system: projects with in_profit_share=True."""

    permission_classes = [IsPartnerOrDirector]

    def get(self, request):
        projects = Project.objects.filter(in_profit_share=True).order_by("name")
        data = [
            {
                "id": p.id,
                "name": p.name,
                "client": p.client,
                "status": _project_status(p),
            }
            for p in projects
        ]
        return Response({"count": len(data), "results": data})


class ProjectBreakdownView(APIView):
    """Full distribution breakdown for an included project.

    Visible to the director (any project) and to partners (included projects
    only). Overhead is shown as a neutral cost line; the direction-overhead
    destination is included ONLY for the director.
    """

    permission_classes = [IsPartnerOrDirector]

    def get(self, request, project_id):
        project = get_object_or_404(Project, pk=project_id)
        director = access.is_director(request.user)

        # Partners may only see INCLUDED projects.
        if not director and not project.in_profit_share:
            return Response(
                {"detail": "This project is not part of the profit-share."},
                status=status.HTTP_403_FORBIDDEN,
            )

        use_actuals = project.end_date is not None
        # Director-only toggle for the cascade calculator: force estimado/real.
        # Partners always get the automatic per-project behavior (no override),
        # so the displayed numbers can never be quietly reframed for them.
        if director:
            override = request.query_params.get("use_actuals")
            if override is not None:
                use_actuals = str(override).lower() in ("1", "true", "yes", "real")
        fin = compute_project_financials(project, use_actuals=use_actuals)

        payload = {
            "project": {
                "id": project.id,
                "name": project.name,
                "status": _project_status(project),
                "in_profit_share": project.in_profit_share,
            },
            "mode": "real" if use_actuals else "estimado",
            "cascade": {
                "contract_amount": str(fin.contract_amount),
                "materials": str(fin.materials),
                "other_labor": str(fin.other_labor),
                "company_overhead": str(fin.company_overhead),
                "overhead": str(fin.direction_overhead),  # neutral label
                "callback_reserve": str(fin.callback_reserve),
                "bad_debt_reserve": str(fin.bad_debt_reserve),
                "net": str(fin.net),
            },
            "distribution": {
                "director_share": str(fin.director_share),
                "partner_pool": str(fin.partner_pool),
                "per_socio": str(fin.per_socio),
                "active_socios": fin.active_socios,
            },
            "note": "Taxes and reinvestment are not deducted here.",
        }
        # Director-only detail: where the overhead goes.
        if director:
            payload["distribution"]["direction_overhead_destination"] = (
                fin.direction_overhead_destination
            )
        return Response(payload)


class SetProfitShareView(APIView):
    """Director-only: mark/unmark a project as part of the profit-share."""

    permission_classes = [IsDirector]

    def post(self, request, project_id):
        project = get_object_or_404(Project, pk=project_id)
        included = bool(request.data.get("in_profit_share", True))
        project.in_profit_share = included
        project.save(update_fields=["in_profit_share"])
        return Response(
            {"id": project.id, "in_profit_share": project.in_profit_share}
        )


# ─────────────────────────────────────────────────────────────────────────────
# Advances (director-only)
# ─────────────────────────────────────────────────────────────────────────────
class AccountAdvanceView(APIView):
    permission_classes = [IsDirector]

    def post(self, request, account_id):
        account = get_object_or_404(PartnerAccount, pk=account_id)
        raw = request.data.get("amount")
        try:
            amount = Decimal(str(raw))
        except Exception:
            return Response(
                {"detail": "amount must be a number."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if amount <= 0:
            return Response(
                {"detail": "amount must be greater than zero."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        note = (request.data.get("note") or "").strip()
        result = record_advance(account, amount, note=note, recorded_by=request.user)
        return Response(
            {
                "entry_id": result.entry_id,
                "new_balance": str(result.new_balance),
                "left_negative": result.left_negative,
            },
            status=status.HTTP_201_CREATED,
        )


# ─────────────────────────────────────────────────────────────────────────────
# "My earnings" — ALWAYS scoped to request.user (no cross-member leakage)
# ─────────────────────────────────────────────────────────────────────────────
class MyEarningsSummaryView(APIView):
    permission_classes = [IsPartnerOrDirector]

    def get(self, request):
        account = _resolve_account(request.user)
        if account is None:
            return Response(
                {"detail": "No profit-share account for this user."},
                status=status.HTTP_404_NOT_FOUND,
            )
        entries = LedgerEntry.objects.filter(account=account)
        total_accrued = sum(
            (e.amount for e in entries if e.type == LedgerEntry.TYPE_ACCRUAL),
            Decimal("0.00"),
        )
        total_withdrawn = sum(
            (-e.amount for e in entries if e.type == LedgerEntry.TYPE_ADVANCE),
            Decimal("0.00"),
        )
        return Response(
            {
                "total_accrued": str(total_accrued),
                "total_withdrawn": str(total_withdrawn),
                "balance": str(account.balance),
            }
        )


class MyEarningsByProjectView(APIView):
    permission_classes = [IsPartnerOrDirector]

    def get(self, request):
        account = _resolve_account(request.user)
        if account is None:
            return Response(
                {"detail": "No profit-share account for this user."},
                status=status.HTTP_404_NOT_FOUND,
            )
        states = (
            ProjectAccrualState.objects.filter(account=account)
            .select_related("project")
            .order_by("project__name")
        )
        data = [
            {
                "project_id": s.project_id,
                "project": s.project.name,
                "accrued": str(s.accrued),
                "status": _project_status(s.project),
            }
            for s in states
        ]
        return Response({"count": len(data), "results": data})


class MyEarningsLedgerView(APIView):
    permission_classes = [IsPartnerOrDirector]

    def get(self, request):
        account = _resolve_account(request.user)
        if account is None:
            return Response(
                {"detail": "No profit-share account for this user."},
                status=status.HTTP_404_NOT_FOUND,
            )
        entries = (
            LedgerEntry.objects.filter(account=account)
            .select_related("project")
            .order_by("date", "created_at")
        )
        data = [
            {
                "id": e.id,
                "type": e.type,
                "amount": str(e.amount),
                "running_balance": str(e.running_balance),
                "project": e.project.name if e.project_id else None,
                "date": e.date.isoformat(),
                "note": e.note,
            }
            for e in entries
        ]
        return Response({"count": len(data), "results": data})


# ─────────────────────────────────────────────────────────────────────────────
# Rates (director-only)
# ─────────────────────────────────────────────────────────────────────────────
_RATE_FIELDS = [
    "company_overhead_pct",
    "direction_overhead_pct",
    "callback_reserve_pct",
    "bad_debt_reserve_pct",
    "director_split_pct",
]


class RateConfigView(APIView):
    permission_classes = [IsDirector]

    def _serialize(self, cfg):
        return {
            "company_overhead_pct": str(cfg.company_overhead_pct),
            "direction_overhead_pct": str(cfg.direction_overhead_pct),
            "callback_reserve_pct": str(cfg.callback_reserve_pct),
            "bad_debt_reserve_pct": str(cfg.bad_debt_reserve_pct),
            "director_split_pct": str(cfg.director_split_pct),
            "direction_overhead_destination": cfg.direction_overhead_destination,
            "profit_share_start_date": cfg.profit_share_start_date.isoformat(),
            "planning_annual_revenue": (
                str(cfg.planning_annual_revenue)
                if cfg.planning_annual_revenue is not None
                else None
            ),
        }

    def get(self, request):
        return Response(self._serialize(RateConfig.load()))

    def put(self, request):
        cfg = RateConfig.load()
        for field in _RATE_FIELDS:
            if field in request.data:
                try:
                    setattr(cfg, field, Decimal(str(request.data[field])))
                except Exception:
                    return Response(
                        {"detail": f"{field} must be a number."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
        if "direction_overhead_destination" in request.data:
            dest = request.data["direction_overhead_destination"]
            if dest not in (
                RateConfig.DESTINATION_DIRECTOR,
                RateConfig.DESTINATION_BUSINESS,
            ):
                return Response(
                    {"detail": "Invalid direction_overhead_destination."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            cfg.direction_overhead_destination = dest
        if "profit_share_start_date" in request.data:
            cfg.profit_share_start_date = request.data["profit_share_start_date"]
        try:
            cfg.full_clean()
        except Exception as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        cfg.save()
        # Reload so DecimalFields come back quantized (e.g. "45.00" not "45"),
        # giving the frontend a stable, consistent representation.
        cfg.refresh_from_db()
        return Response(self._serialize(cfg))
