from __future__ import annotations

from dataclasses import dataclass

from core.models import Project


@dataclass
class RenderResult:
    content_type: str
    body: bytes


def render_project_cost_summary(project: Project) -> RenderResult:
    """Render a minimal project cost summary as CSV bytes.

    This is a stub implementation that can be expanded.
    """
    # Compute simple totals (placeholder logic)
    total_income = sum(i.amount for i in project.incomes.all())
    total_expense = sum(e.amount for e in project.expenses.all())
    profit = total_income - total_expense
    rows = [
        ["project_id", project.id],
        ["project_name", project.name],
        ["total_income", f"{total_income:.2f}"],
        ["total_expense", f"{total_expense:.2f}"],
        ["profit", f"{profit:.2f}"],
    ]
    csv = "\n".join([f"{k},{v}" for k, v in rows]).encode("utf-8")
    return RenderResult(content_type="text/csv", body=csv)
