"""Profit-share calculation service (Phase 3) — PURE, no DB writes.

Computes, for a project, the exact distribution cascade:

    net = contract_amount
        − materials
        − other_labor          (hourly crew only; SOCIOS are never a cost)
        − company_overhead      (contract × company_overhead_pct)
        − direction_overhead    (contract × direction_overhead_pct)
        − callback_reserve      (contract × callback_reserve_pct)
        − bad_debt_reserve      (contract × bad_debt_reserve_pct)

    director_share = net × director_split_pct        (the owner's 40%)
    partner_pool   = net − director_share            (the 60%)
    per_socio      = partner_pool / (active socios)

Sources (reusing existing models — no new cost tables):
    contract_amount = approved Estimate total (Σ EstimateLine.total_price)
                      or project.budget_total fallback, PLUS approved COs.
    materials  → est: project.budget_materials | actual: Σ Expense(MATERIALES)
    other_labor→ est: project.budget_labor     | actual: crew TimeEntry cost
                 (hours × rate, EXCLUDING socios/owner) + Σ Expense(MANO_OBRA)

Overhead label is neutral ("overhead"). This module performs NO accrual and
touches NO ledger; Phase 4 consumes these numbers and posts deltas.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from decimal import ROUND_HALF_UP, Decimal

from django.db import transaction
from django.db.models import DecimalField, ExpressionWrapper, F, Q, Sum

from core.access import ROLE_OWNER, ROLE_PARTNER

CENTS = Decimal("0.01")
ZERO = Decimal("0.00")

#: Change-order statuses that represent a real, client-agreed addition to the
#: contract value (drafts/pending are excluded).
CONTRACT_CO_STATUSES = ("approved", "sent", "billed", "paid")

#: Expense categories used as direct cost inputs. Everything else (insurance,
#: office, food, storage…) is intentionally absorbed by company_overhead.
MATERIAL_CATEGORY = "MATERIALES"
LABOR_CATEGORY = "MANO_OBRA"


def _q(value) -> Decimal:
    """Quantize to cents, half-up. Accepts Decimal/int/float/None."""
    if value is None:
        return ZERO
    if not isinstance(value, Decimal):
        value = Decimal(str(value))
    return value.quantize(CENTS, rounding=ROUND_HALF_UP)


# ─────────────────────────────────────────────────────────────────────────────
# Contract amount = approved estimate (+ fallback) + approved change orders
# ─────────────────────────────────────────────────────────────────────────────
def _estimate_total(project) -> Decimal:
    """Total of the most-recent APPROVED estimate's lines.

    Falls back to ``project.budget_total`` when there is no approved estimate
    (or it has no lines), so a project without a formal estimate still has a
    contract base.
    """
    approved = (
        project.estimates.filter(approved=True).order_by("-version").first()
    )
    if approved is not None:
        total = sum((line.total_price for line in approved.lines.all()), ZERO)
        if total and total > 0:
            return _q(total)
    return _q(getattr(project, "budget_total", ZERO))


def _approved_co_total(project) -> Decimal:
    """Sum of client-agreed change orders.

    FIXED → ``amount``. T&M → billable ``grand_total`` from ChangeOrderService.
    """
    # Local import avoids a circular import at module load.
    from core.services.financial_service import ChangeOrderService

    total = ZERO
    cos = project.change_orders.filter(status__in=CONTRACT_CO_STATUSES)
    for co in cos:
        if co.pricing_type == "FIXED":
            total += co.amount or ZERO
        else:  # T_AND_M
            billable = ChangeOrderService.get_billable_amount(co)
            total += billable.get("grand_total") or billable.get("total") or ZERO
    return _q(total)


def compute_contract_amount(project) -> Decimal:
    """Project contract value = approved estimate (+budget fallback) + COs."""
    return _q(_estimate_total(project) + _approved_co_total(project))


# ─────────────────────────────────────────────────────────────────────────────
# Cost inputs
# ─────────────────────────────────────────────────────────────────────────────
def _actual_materials(project) -> Decimal:
    total = project.expenses.filter(category=MATERIAL_CATEGORY).aggregate(
        t=Sum("amount")
    )["t"]
    return _q(total)


def _crew_labor_cost(project) -> Decimal:
    """Hourly crew labor for the project: Σ hours × employee.hourly_rate.

    CRITICAL: excludes any employee whose linked user is a SOCIO (partner) or
    the OWNER — socios are never a project cost. Employees without a linked
    user (plain crew) are always included.
    """
    cost_expr = ExpressionWrapper(
        F("hours_worked") * F("employee__hourly_rate"),
        output_field=DecimalField(max_digits=14, decimal_places=2),
    )
    qs = (
        project.timeentry_set.filter(hours_worked__isnull=False)
        .exclude(employee__user__profile__role__in=[ROLE_PARTNER, ROLE_OWNER])
    )
    total = qs.aggregate(t=Sum(cost_expr))["t"]
    return _q(total)


def _subcontract_labor(project) -> Decimal:
    """Subcontracted labor logged as Expense(MANO_OBRA).

    Disjoint from crew TimeEntry by convention: payroll crew → TimeEntry,
    subcontractors → Expense(MANO_OBRA). Avoids double counting.
    """
    total = project.expenses.filter(category=LABOR_CATEGORY).aggregate(
        t=Sum("amount")
    )["t"]
    return _q(total)


def _actual_other_labor(project) -> Decimal:
    return _q(_crew_labor_cost(project) + _subcontract_labor(project))


def _count_active_socios() -> int:
    from core.models import PartnerAccount

    return PartnerAccount.objects.filter(
        is_business=False, is_active_socio=True, owner__isnull=False
    ).count()


def exclude_profit_share_members(employee_qs):
    """Exclude socios (partner) and the director (owner) from an Employee qs.

    These members no longer draw an hourly wage and must NOT appear in payroll
    or savings. Their TimeEntry check-ins are untouched (metrics only). Plain
    crew (no linked user, or any non partner/owner role) is always kept.
    """
    return employee_qs.exclude(
        user__profile__role__in=[ROLE_PARTNER, ROLE_OWNER]
    )


# ─────────────────────────────────────────────────────────────────────────────
# Result container
# ─────────────────────────────────────────────────────────────────────────────
@dataclass
class ProjectFinancials:
    use_actuals: bool
    contract_amount: Decimal
    materials: Decimal
    other_labor: Decimal
    company_overhead: Decimal
    direction_overhead: Decimal
    callback_reserve: Decimal
    bad_debt_reserve: Decimal
    net: Decimal
    director_share: Decimal
    partner_pool: Decimal
    per_socio: Decimal
    active_socios: int
    direction_overhead_destination: str
    can_accrue: bool

    def as_dict(self) -> dict:
        d = asdict(self)
        # Decimals → str for safe JSON/serialization at the edges.
        for k, v in d.items():
            if isinstance(v, Decimal):
                d[k] = str(v)
        return d


# ─────────────────────────────────────────────────────────────────────────────
# Main entry point
# ─────────────────────────────────────────────────────────────────────────────
def compute_project_financials(
    project,
    *,
    use_actuals: bool = False,
    rate_config=None,
    active_socios: int | None = None,
) -> ProjectFinancials:
    """Compute the full distribution breakdown for a project (pure).

    Args:
        use_actuals: when True (closed project), pull real costs from Expense/
            TimeEntry; when False (projection), use the budget_* estimates.
        rate_config: optional RateConfig; defaults to the singleton.
        active_socios: optional override of the active-socio count.

    Guards:
        - contract_amount <= 0 → ``can_accrue=False`` and a zeroed net split
          (prevents negatives from unsigned/empty contracts).
        - active_socios == 0 → per_socio = 0 (no division by zero).

    Note: ``net`` itself MAY be negative for a closed project with a real loss;
    that is intentional and flows through to the split (socios share the loss).
    """
    if rate_config is None:
        from core.models import RateConfig

        rate_config = RateConfig.load()
    if active_socios is None:
        active_socios = _count_active_socios()

    contract = compute_contract_amount(project)

    if use_actuals:
        materials = _actual_materials(project)
        other_labor = _actual_other_labor(project)
    else:
        materials = _q(getattr(project, "budget_materials", ZERO))
        other_labor = _q(getattr(project, "budget_labor", ZERO))

    def pct(p) -> Decimal:
        return _q(contract * (p / Decimal("100")))

    company_overhead = pct(rate_config.company_overhead_pct)
    direction_overhead = pct(rate_config.direction_overhead_pct)
    callback_reserve = pct(rate_config.callback_reserve_pct)
    bad_debt_reserve = pct(rate_config.bad_debt_reserve_pct)

    # Guard: a non-positive contract cannot accrue anything.
    can_accrue = contract > 0
    if not can_accrue:
        return ProjectFinancials(
            use_actuals=use_actuals,
            contract_amount=contract,
            materials=materials,
            other_labor=other_labor,
            company_overhead=ZERO,
            direction_overhead=ZERO,
            callback_reserve=ZERO,
            bad_debt_reserve=ZERO,
            net=ZERO,
            director_share=ZERO,
            partner_pool=ZERO,
            per_socio=ZERO,
            active_socios=active_socios,
            direction_overhead_destination=rate_config.direction_overhead_destination,
            can_accrue=False,
        )

    net = _q(
        contract
        - materials
        - other_labor
        - company_overhead
        - direction_overhead
        - callback_reserve
        - bad_debt_reserve
    )

    director_share = _q(net * (rate_config.director_split_pct / Decimal("100")))
    partner_pool = _q(net - director_share)
    per_socio = _q(partner_pool / active_socios) if active_socios > 0 else ZERO

    return ProjectFinancials(
        use_actuals=use_actuals,
        contract_amount=contract,
        materials=materials,
        other_labor=other_labor,
        company_overhead=company_overhead,
        direction_overhead=direction_overhead,
        callback_reserve=callback_reserve,
        bad_debt_reserve=bad_debt_reserve,
        net=net,
        director_share=director_share,
        partner_pool=partner_pool,
        per_socio=per_socio,
        active_socios=active_socios,
        direction_overhead_destination=rate_config.direction_overhead_destination,
        can_accrue=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Accrual (Phase 4) — IDEMPOTENT. Posts only the delta vs. ProjectAccrualState.
# ─────────────────────────────────────────────────────────────────────────────
@dataclass
class AccrualResult:
    """Outcome of an accrual run (for transparency/testing)."""

    posted: bool
    reason: str = ""
    fraction: Decimal = ZERO
    net_realized: Decimal = ZERO
    entries_created: int = 0


def _qualifying_payments_total(project, start_date) -> Decimal:
    """Σ InvoicePayment.amount for this project on/after the cutoff date.

    This reuses the EXISTING payment model — there is no parallel ledger of
    "amount collected". Payments before the cutoff never qualify.
    """
    from core.models import InvoicePayment

    total = InvoicePayment.objects.filter(
        invoice__project=project, payment_date__gte=start_date
    ).aggregate(t=Sum("amount"))["t"]
    return _q(total)


def accrue_for_project(project) -> AccrualResult:
    """Recompute and post profit-share accrual for a project (idempotent).

    Flow:
        skip if not project.in_profit_share
        skip if contract_amount <= 0
        qualifying = Σ payments(project, date >= start_date)
        fraction   = min(qualifying / contract, 1.0)        # clamp [0,1]
        net_realized = net(use_actuals = project closed) × fraction
        for each account (director, active socios, business/director overhead):
            target = full_share × fraction
            delta  = target − ProjectAccrualState.accrued
            if delta != 0: post LedgerEntry(ACCRUAL, delta); balance += delta

    Idempotency: re-running on the same payments yields delta=0 everywhere, so
    NO duplicate entries are created. Posting the delta (not the absolute) is
    what makes repeated calls / double-submits safe.

    Concurrency: the whole posting runs inside a transaction with row locks on
    the touched ProjectAccrualState / PartnerAccount rows.
    """
    from core.models import (
        LedgerEntry,
        PartnerAccount,
        ProjectAccrualState,
        RateConfig,
    )

    if not getattr(project, "in_profit_share", False):
        return AccrualResult(posted=False, reason="not_in_profit_share")

    cfg = RateConfig.load()
    contract = compute_contract_amount(project)
    if contract <= 0:
        return AccrualResult(posted=False, reason="contract_non_positive")

    qualifying = _qualifying_payments_total(project, cfg.profit_share_start_date)
    if qualifying <= 0:
        return AccrualResult(posted=False, reason="no_qualifying_payments")

    raw_fraction = qualifying / contract
    fraction = raw_fraction if raw_fraction < Decimal("1") else Decimal("1")

    use_actuals = project.end_date is not None

    with transaction.atomic():
        # Lock the active socio accounts so the count + per_socio are consistent
        # with what we post, even under concurrent payments.
        socio_accounts = list(
            PartnerAccount.objects.select_for_update().filter(
                is_business=False, is_active_socio=True, owner__isnull=False
            )
        )
        active_socios = len(socio_accounts)

        fin = compute_project_financials(
            project,
            use_actuals=use_actuals,
            rate_config=cfg,
            active_socios=active_socios,
        )
        if not fin.can_accrue:
            return AccrualResult(posted=False, reason="cannot_accrue")

        net_realized = _q(fin.net * fraction)

        # Build target accruals per account.
        targets: list[tuple[PartnerAccount, Decimal]] = []

        director = PartnerAccount.director()
        if director is not None:
            director = PartnerAccount.objects.select_for_update().get(pk=director.pk)
            targets.append((director, _q(fin.director_share * fraction)))

        for acc in socio_accounts:
            targets.append((acc, _q(fin.per_socio * fraction)))

        overhead_realized = _q(fin.direction_overhead * fraction)
        if cfg.direction_overhead_destination == RateConfig.DESTINATION_BUSINESS:
            biz = PartnerAccount.objects.select_for_update().get(
                pk=PartnerAccount.business().pk
            )
            targets.append((biz, overhead_realized))
        elif director is not None:
            # Direction overhead also goes to the director account.
            targets.append((director, overhead_realized))

        # Aggregate targets per account (director may appear twice).
        per_account: dict[int, tuple[PartnerAccount, Decimal]] = {}
        for acc, amount in targets:
            if acc.pk in per_account:
                existing_acc, existing_amt = per_account[acc.pk]
                per_account[acc.pk] = (existing_acc, _q(existing_amt + amount))
            else:
                per_account[acc.pk] = (acc, amount)

        entries_created = 0
        for acc, target in per_account.values():
            state, _created = ProjectAccrualState.objects.select_for_update().get_or_create(
                project=project, account=acc
            )
            delta = _q(target - state.accrued)
            if delta == 0:
                continue
            new_balance = _q(acc.balance + delta)
            LedgerEntry.objects.create(
                account=acc,
                project=project,
                type=LedgerEntry.TYPE_ACCRUAL,
                amount=delta,
                running_balance=new_balance,
                note=(
                    f"Accrual {project.name}: {fraction:.4f} collected"
                    f"{' (actuals)' if use_actuals else ' (estimate)'}"
                ),
            )
            acc.balance = new_balance
            acc.save(update_fields=["balance"])
            state.accrued = target
            state.save(update_fields=["accrued"])
            entries_created += 1

    return AccrualResult(
        posted=entries_created > 0,
        reason="ok" if entries_created > 0 else "no_change",
        fraction=_q(fraction),
        net_realized=net_realized,
        entries_created=entries_created,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Advances / withdrawals (Phase 5) — director-authorized money OUT.
# ─────────────────────────────────────────────────────────────────────────────
@dataclass
class AdvanceResult:
    entry_id: int
    new_balance: Decimal
    left_negative: bool


def record_advance(account, amount, *, note: str = "", recorded_by=None) -> AdvanceResult:
    """Record an advance/withdrawal (money OUT) on a partner account.

    A single mechanic covers both cases:
      - Withdrawal: the partner takes available balance (stays >= 0).
      - Advance/loan: the director lets the balance go NEGATIVE.

    The amount is supplied positive and posted as a negative ``LedgerEntry``
    (type ADVANCE). Negative balances are allowed by design; future accruals
    pay them down automatically (Phase 4 adds positive deltas to the balance).

    ``left_negative`` lets the UI warn "this leaves the account at −$X".

    NOTE: authorization (director-only) is enforced at the endpoint/view layer
    (Phase 7), not here — this is the pure ledger primitive.
    """
    from core.models import LedgerEntry, PartnerAccount

    amount = _q(amount)
    if amount <= 0:
        raise ValueError("Advance amount must be greater than zero.")

    with transaction.atomic():
        acc = PartnerAccount.objects.select_for_update().get(pk=account.pk)
        new_balance = _q(acc.balance - amount)
        entry = LedgerEntry.objects.create(
            account=acc,
            project=None,
            type=LedgerEntry.TYPE_ADVANCE,
            amount=_q(-amount),
            running_balance=new_balance,
            note=note or "Advance / withdrawal",
        )
        acc.balance = new_balance
        acc.save(update_fields=["balance"])

    return AdvanceResult(
        entry_id=entry.pk,
        new_balance=new_balance,
        left_negative=new_balance < 0,
    )
