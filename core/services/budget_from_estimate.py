"""
Service to auto-generate Budget Lines from an approved Estimate.

Flow:
1. Client approves Estimate (proposal_public_view)
2. System creates BudgetLines from EstimateLines
3. BudgetLine.baseline_amount = EstimateLine.total_price * (1 - profit_margin)
   Default profit margin is 30% (configurable per project)
"""
from decimal import Decimal, ROUND_HALF_UP
import logging

logger = logging.getLogger(__name__)

DEFAULT_PROFIT_MARGIN = Decimal("0.30")  # 30% default margin


def round_money(value):
    """Round to 2 decimal places for money values."""
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def create_budget_from_estimate(estimate, profit_margin=None):
    """
    Create BudgetLines from an approved Estimate.
    
    Args:
        estimate: Estimate instance (should be approved)
        profit_margin: Decimal (0-1), default 0.30 (30%)
    
    Returns:
        list of created BudgetLine instances
    """
    from core.models import BudgetLine, EstimateLine
    
    if profit_margin is None:
        # Could make this configurable per project in the future
        profit_margin = DEFAULT_PROFIT_MARGIN
    
    project = estimate.project
    created_lines = []
    
    # Get all estimate lines
    estimate_lines = estimate.lines.select_related('cost_code').all()
    
    if not estimate_lines:
        logger.warning(f"No estimate lines found for Estimate {estimate.code}")
        return created_lines
    
    for est_line in estimate_lines:
        # Check if budget line already exists for this cost code in this project
        existing = BudgetLine.objects.filter(
            project=project,
            cost_code=est_line.cost_code
        ).first()
        
        # Calculate budget amount (estimate price - profit margin)
        estimate_price = Decimal(str(est_line.total_price or 0))
        budget_amount = round_money(estimate_price * (Decimal("1") - profit_margin))
        
        if existing:
            # Update existing budget line
            existing.description = est_line.description or existing.description
            existing.qty = est_line.qty
            existing.unit = est_line.unit
            # Unit cost is the total budget divided by qty
            if est_line.qty and est_line.qty > 0:
                existing.unit_cost = round_money(budget_amount / est_line.qty)
            else:
                existing.unit_cost = budget_amount
            existing.baseline_amount = budget_amount
            existing.revised_amount = budget_amount
            existing.save()
            
            # Link estimate line to budget line
            est_line.budget_line = existing
            est_line.save(update_fields=['budget_line'])
            
            created_lines.append(existing)
            logger.info(f"Updated BudgetLine for {est_line.cost_code.code}: ${budget_amount}")
        else:
            # Create new budget line
            # Calculate unit_cost from total / qty
            unit_cost = Decimal("0")
            if est_line.qty and est_line.qty > 0:
                unit_cost = round_money(budget_amount / est_line.qty)
            
            budget_line = BudgetLine.objects.create(
                project=project,
                cost_code=est_line.cost_code,
                description=est_line.description,
                qty=est_line.qty,
                unit=est_line.unit,
                unit_cost=unit_cost,
                baseline_amount=budget_amount,
                revised_amount=budget_amount,
            )
            
            # Link estimate line to budget line
            est_line.budget_line = budget_line
            est_line.save(update_fields=['budget_line'])
            
            created_lines.append(budget_line)
            logger.info(f"Created BudgetLine for {est_line.cost_code.code}: ${budget_amount}")
    
    logger.info(
        f"Created/updated {len(created_lines)} budget lines for Estimate {estimate.code} "
        f"with {profit_margin*100}% profit margin"
    )
    
    return created_lines


def sync_budget_for_approved_estimates(project=None):
    """
    Utility function to sync budget lines for all approved estimates.
    Useful for migrating existing projects that have approved estimates
    but no budget lines created.
    
    Args:
        project: Optional Project instance. If None, processes all projects.
    
    Returns:
        dict with results by project
    """
    from core.models import Estimate
    
    results = {}
    
    if project:
        estimates = Estimate.objects.filter(project=project, approved=True)
    else:
        estimates = Estimate.objects.filter(approved=True)
    
    for estimate in estimates:
        try:
            budget_lines = create_budget_from_estimate(estimate)
            results[estimate.code] = {
                'status': 'success',
                'budget_lines_count': len(budget_lines),
            }
        except Exception as e:
            results[estimate.code] = {
                'status': 'error',
                'error': str(e),
            }
            logger.error(f"Failed to sync budget for Estimate {estimate.code}: {e}")
    
    return results


def get_estimate_to_budget_summary(estimate, profit_margin=None):
    """
    Get a preview of what budget lines would be created.
    Useful for showing user before approval.
    
    Returns:
        list of dicts with estimate_line, budget_amount, profit_amount
    """
    if profit_margin is None:
        profit_margin = DEFAULT_PROFIT_MARGIN
    
    summary = []
    for est_line in estimate.lines.select_related('cost_code').all():
        estimate_price = Decimal(str(est_line.total_price or 0))
        profit_amount = round_money(estimate_price * profit_margin)
        budget_amount = round_money(estimate_price - profit_amount)
        
        summary.append({
            'cost_code': est_line.cost_code.code,
            'cost_code_name': est_line.cost_code.name,
            'description': est_line.description,
            'estimate_price': round_money(estimate_price),
            'profit_margin_pct': float(profit_margin * 100),
            'profit_amount': profit_amount,
            'budget_amount': budget_amount,
        })
    
    return summary
