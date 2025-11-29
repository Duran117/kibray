from decimal import Decimal
from typing import Dict, Any

from django.db.models import Sum

from core.models import ChangeOrder


class ChangeOrderService:
    """Financial helper for Change Orders including Time & Materials billing calculations."""

    @staticmethod
    def get_billable_amount(change_order: ChangeOrder) -> Dict[str, Any]:
        """
        Return billable amount or detailed breakdown depending on pricing type.
        FIXED: returns {'type': 'FIXED', 'total': amount}
        T_AND_M: returns breakdown dict with labor/material details.
        Unbilled TimeEntries & Expenses are those without invoice_line set.
        """
        if change_order.pricing_type == 'FIXED':
            return {
                'type': 'FIXED',
                'total': change_order.amount,
            }

        # T&M mode
        billing_rate = change_order.get_effective_billing_rate()
        material_markup_pct = change_order.material_markup_pct or Decimal('0')

        time_qs = change_order.time_entries.filter(invoice_line__isnull=True)
        expenses_qs = change_order.expenses.filter(invoice_line__isnull=True)

        labor_hours = sum((te.hours_worked or Decimal('0')) for te in time_qs)
        labor_total = (labor_hours * billing_rate).quantize(Decimal('0.01'))

        raw_material_cost = expenses_qs.aggregate(s=Sum('amount'))['s'] or Decimal('0.00')
        material_total = (raw_material_cost * (Decimal('1.00') + material_markup_pct / Decimal('100'))).quantize(Decimal('0.01'))

        return {
            'type': 'T_AND_M',
            'billing_rate': billing_rate,
            'material_markup_pct': material_markup_pct,
            'labor_hours': labor_hours,
            'labor_total': labor_total,
            'raw_material_cost': raw_material_cost,
            'material_total': material_total,
            'grand_total': labor_total + material_total,
            'time_entries': list(time_qs),
            'expenses': list(expenses_qs),
        }
