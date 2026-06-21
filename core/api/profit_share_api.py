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
    accrue_for_project,
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
    """Read access for the transparency views: profit-share members + director.

    Membership is account-based (``is_profit_share_member``), so a Project
    Manager who is a socio reaches these endpoints while KEEPING their PM role.
    The legacy ``partner`` role still works via that helper's fallback.
    """

    message = "Partner or director role required."

    def has_permission(self, request, view):
        u = request.user
        return access.is_director(u) or access.is_profit_share_member(u)


def _project_status(project) -> str:
    return "real" if project.end_date is not None else "estimado"


def _safe_accrue(project) -> dict:
    """Run accrual and return a small JSON-safe summary.

    Never raises: accrual must not be able to break the flag toggle / recalc
    request. On failure we report it instead of 500-ing the endpoint.
    """
    try:
        result = accrue_for_project(project)
        return {
            "posted": result.posted,
            "reason": result.reason,
            "entries_created": result.entries_created,
            "fraction": str(result.fraction),
            "net_realized": str(result.net_realized),
        }
    except Exception as exc:  # pragma: no cover - defensive
        return {"posted": False, "reason": "error", "error": str(exc)}


def _project_socios(project, me_user) -> list:
    """Per-project transparency roster: each ACTIVE socio (the 60% pool) with
    what they've accrued ON THIS project so far.

    This is intentionally per-PROJECT distribution data (the "reparto") — never
    global balances and never anyone's withdrawals/advances, which stay private
    to each member's own "My Earnings". The director (40%) and the business
    account (company deduction) are surfaced elsewhere in the payload, so they
    are excluded here to keep this strictly the pool of socios.
    """
    accrued_by_acc = {
        s.account_id: s.accrued
        for s in ProjectAccrualState.objects.filter(project=project)
    }
    socio_accounts = (
        PartnerAccount.objects.filter(
            is_business=False, is_active_socio=True, owner__isnull=False
        )
        .select_related("owner")
        .order_by("owner__first_name", "owner__last_name", "owner__username")
    )
    roster = []
    for acc in socio_accounts:
        owner = acc.owner
        if access.is_director(owner):
            continue  # the director's 40% is shown separately as director_share
        roster.append(
            {
                "name": owner.get_full_name() or owner.username,
                "accrued": str(accrued_by_acc.get(acc.id, Decimal("0.00"))),
                "is_me": owner.id == getattr(me_user, "id", None),
            }
        )
    return roster



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
            "socios": _project_socios(project, request.user),
            "note": "Taxes and reinvestment are not deducted here.",
        }
        # Director-only detail: where the overhead goes.
        if director:
            payload["distribution"]["direction_overhead_destination"] = (
                fin.direction_overhead_destination
            )
        return Response(payload)


class SetProfitShareView(APIView):
    """Director-only: mark/unmark a project as part of the profit-share.

    When a project is INCLUDED, we immediately run the (idempotent) accrual so
    any payments it already collected on/after the cutoff are reflected at once.
    Without this, including a project that has historical payments would show
    nothing until the *next* payment — which looks broken to the partners. The
    accrual is wrapped so it can never block the flag toggle itself.
    """

    permission_classes = [IsDirector]

    def post(self, request, project_id):
        project = get_object_or_404(Project, pk=project_id)
        included = bool(request.data.get("in_profit_share", True))
        project.in_profit_share = included
        project.save(update_fields=["in_profit_share"])

        accrual = None
        if included:
            accrual = _safe_accrue(project)
        return Response(
            {
                "id": project.id,
                "in_profit_share": project.in_profit_share,
                "accrual": accrual,
            }
        )


class RecalcProjectView(APIView):
    """Director-only: re-run the idempotent accrual for an included project.

    Useful after editing rates / the cutoff date, or to pick up historical
    payments. Because accrual posts only the delta vs. what was already accrued,
    re-running is always safe (no duplicates); a rate change simply trues the
    balances up or down.
    """

    permission_classes = [IsDirector]

    def post(self, request, project_id):
        project = get_object_or_404(Project, pk=project_id)
        if not project.in_profit_share:
            return Response(
                {"detail": "This project is not part of the profit-share."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response({"accrual": _safe_accrue(project)})



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
# Membership (director-only) — make a user a socio WITHOUT changing their role
# ─────────────────────────────────────────────────────────────────────────────
class MemberSetView(APIView):
    """Director-only: turn a user into a profit-share socio, or stop them being one.

    Activating creates (or reactivates) the user's ``PartnerAccount`` with
    ``is_active_socio=True``. The user KEEPS their existing role (e.g. a Project
    Manager stays a PM with every permission/view) — only how they are paid
    changes. Deactivating sets ``is_active_socio=False`` but PRESERVES the
    account, its balance and its ledger history, so past earnings/withdrawals
    remain auditable and a future reactivation resumes the same account.

    Adding/removing a socio changes the size of the 60% pool for FUTURE
    accruals; it does NOT retroactively re-split already-accrued projects. The
    director can true a specific project up/down with the per-project Recalc.
    """

    permission_classes = [IsDirector]

    def post(self, request):
        from django.contrib.auth import get_user_model

        user_id = request.data.get("user_id")
        is_socio = bool(request.data.get("is_socio", True))
        target = get_object_or_404(get_user_model(), pk=user_id)

        # The director's split is separate from the 60% socio pool — never put
        # the director (owner/admin) into the pool by mistake.
        if access.is_director(target):
            return Response(
                {"detail": "The director is not a pool socio."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        account, _created = PartnerAccount.objects.get_or_create(
            owner=target,
            defaults={"is_business": False, "is_active_socio": is_socio},
        )
        if account.is_active_socio != is_socio:
            account.is_active_socio = is_socio
            account.save(update_fields=["is_active_socio"])

        return Response(
            {
                "user_id": target.id,
                "account_id": account.id,
                "is_active_socio": account.is_active_socio,
                "balance": str(account.balance),
            }
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
