"""Payroll tax calculation utilities (Gap B).

Supports flat and tiered tax profiles.
"""

from decimal import Decimal

from core.models import TaxProfile


def calculate_tax(profile: TaxProfile, gross: Decimal) -> Decimal:
    """Compute tax withheld using TaxProfile."""
    if not profile or not profile.active:
        return Decimal("0.00")
    return profile.compute_tax(gross)


def preview_tiered(profile: TaxProfile, gross: Decimal) -> dict:
    """Return breakdown of tiered computation for UI/debug."""
    if profile.method != "tiered":
        return {"method": profile.method, "tax": str(calculate_tax(profile, gross)), "tiers": []}
    tax = Decimal("0")
    remaining = gross
    last_limit = Decimal("0")
    parts = []
    sorted_tiers = sorted(profile.tiers, key=lambda b: b.get("up_to") or 10**12)
    for bracket in sorted_tiers:
        limit_raw = bracket.get("up_to")
        limit = Decimal(str(limit_raw)) if limit_raw is not None else None
        rate = Decimal(str(bracket.get("rate", 0)))
        span = remaining if limit is None else min(remaining, limit - last_limit)
        if span <= 0:
            continue
        part_tax = span * rate / Decimal("100")
        tax += part_tax
        parts.append({"span": str(span), "rate": str(rate), "tax": str(part_tax)})
        remaining -= span
        if limit is not None:
            last_limit = limit
        if remaining <= 0:
            break
    return {"method": "tiered", "tax": str(tax.quantize(Decimal("0.01"))), "parts": parts}
