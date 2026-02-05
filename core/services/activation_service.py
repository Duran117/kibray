"""
Project Activation Service
Automates transition from Sales (Estimate) to Production (Schedule, Budget, Tasks, Invoices).

This service handles the conversion of approved estimates into operational entities:
- ScheduleItemV2 for Gantt visualization (V2 system)
- BudgetLines for financial control
- Tasks for daily operations
- Invoices for deposits/advances
"""

from datetime import timedelta
from decimal import Decimal
from typing import Any, List, Optional, Tuple

from django.db import transaction
from django.utils import timezone

from core.models import (
    BudgetLine,
    Estimate,
    EstimateLine,
    Invoice,
    InvoiceLine,
    Project,
    SchedulePhaseV2,
    ScheduleItemV2,
    Task,
)


class ProjectActivationService:
    """Service for activating projects from approved estimates."""

    def __init__(self, project: Project, estimate: Estimate):
        """
        Initialize service with project and estimate.

        Args:
            project: Target project
            estimate: Source estimate (should be approved)
        """
        self.project = project
        self.estimate = estimate

    def validate_estimate(self) -> Tuple[bool, Optional[str]]:
        """
        Validate that estimate is ready for activation.

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not self.estimate.approved:
            return False, "El estimado debe estar aprobado antes de activar el proyecto"

        if not self.estimate.lines.exists():
            return False, "El estimado no tiene líneas para procesar"

        return True, None

    @transaction.atomic
    def create_schedule_from_estimate(
        self,
        start_date,
        items_to_schedule: Optional[List[EstimateLine]] = None,
        selected_line_ids: Optional[List[int]] = None,
    ) -> list[ScheduleItemV2]:
        """
        Create ScheduleItemV2 from EstimateLines.

        Args:
            start_date: Project start date
            items_to_schedule: Optional list of specific lines to schedule.
                             If None, schedules all estimate lines.

        Returns:
            List of created ScheduleItemV2
        """
        # Get or create default phase
        phase, _ = SchedulePhaseV2.objects.get_or_create(
            project=self.project, name="General", defaults={"order": 0}
        )

        # Determine which lines to schedule (precedence: explicit IDs > provided queryset > all)
        if selected_line_ids is not None:
            lines_to_process = self.estimate.lines.filter(id__in=selected_line_ids)
        elif items_to_schedule is None:
            lines_to_process = self.estimate.lines.all()
        else:
            lines_to_process = items_to_schedule

        created_items = []
        current_date = start_date

        def _add_business_days(d, days: int):
            """Add business days (Mon-Fri)."""
            result = d
            added = 0
            while added < days:
                result += timedelta(days=1)
                if result.weekday() < 5:  # 0=Mon .. 4=Fri
                    added += 1
            return result

        for idx, line in enumerate(lines_to_process, start=1):
            # Duration: interpret qty as hours if labor, else default 8h (1 day)
            labor_hours = (
                float(line.qty) if line.cost_code and line.cost_code.category == "labor" else 8.0
            )
            duration_days = max(1, int((labor_hours + 7) // 8))  # ceiling division
            end_date = _add_business_days(
                current_date, duration_days - 1
            )  # duration of 1 day ends same day

            # Create title from line description or cost code
            title = (
                line.description
                or f"{line.cost_code.name if line.cost_code else 'Item'} - {line.qty} {line.unit}"
            )

            schedule_item = ScheduleItemV2.objects.create(
                project=self.project,
                phase=phase,
                name=title[:200],  # Limit to model max_length
                description=line.description or "",
                start_date=current_date,
                end_date=end_date,
                status="planned",
                progress=0,
                order=idx,
            )

            created_items.append(schedule_item)

            # Sequential scheduling: next item starts after previous ends
            current_date = end_date + timedelta(days=1)

        return created_items

    @transaction.atomic
    def create_budget_from_estimate(self) -> list[BudgetLine]:
        """
        Create BudgetLines from EstimateLines.

        Copies costs and quantities to budget for financial tracking.

        Returns:
            List of created BudgetLines
        """
        # Clean previous budget lines (spec requirement: reset baseline before regeneration)
        BudgetLine.objects.filter(project=self.project).delete()
        created_lines = []

        for line in self.estimate.lines.all():
            # Calculate direct cost and round to 2 decimal places
            total_cost = line.direct_cost().quantize(Decimal("0.01"))

            budget_line = BudgetLine.objects.create(
                project=self.project,
                cost_code=line.cost_code,
                description=line.description
                or f"{line.cost_code.name if line.cost_code else 'Item'}",
                qty=line.qty,
                unit=line.unit,
                unit_cost=total_cost / line.qty if line.qty > 0 else Decimal("0"),
                baseline_amount=total_cost,
                revised_amount=total_cost,
            )

            created_lines.append(budget_line)

        return created_lines

    @transaction.atomic
    def create_tasks_from_schedule(
        self, schedule_items: list[ScheduleItemV2], assigned_to=None
    ) -> list[Task]:
        """
        Create operational Tasks from ScheduleItemV2.

        Args:
            schedule_items: List of schedule items to convert
            assigned_to: Optional employee to assign tasks to

        Returns:
            List of created Tasks
        """
        created_tasks = []

        for schedule_item in schedule_items:
            task = Task.objects.create(
                project=self.project,
                title=schedule_item.name,
                description=schedule_item.description or "",
                status="Pending",
                priority="medium",
                due_date=schedule_item.end_date,
                assigned_to=assigned_to,
            )

            created_tasks.append(task)

        return created_tasks

    def _calculate_estimate_total(self) -> Decimal:
        """
        Calculate total proposed price for the estimate.
        Includes markup, overhead, and profit.
        """
        direct_cost = sum(line.direct_cost() for line in self.estimate.lines.all())
        material_markup = (
            (direct_cost * (self.estimate.markup_material / 100))
            if self.estimate.markup_material
            else 0
        )
        labor_markup = (
            (direct_cost * (self.estimate.markup_labor / 100)) if self.estimate.markup_labor else 0
        )
        overhead = (
            (direct_cost * (self.estimate.overhead_pct / 100)) if self.estimate.overhead_pct else 0
        )
        profit = (
            (direct_cost * (self.estimate.target_profit_pct / 100))
            if self.estimate.target_profit_pct
            else 0
        )
        total = direct_cost + material_markup + labor_markup + overhead + profit
        return total

    @transaction.atomic
    def create_deposit_invoice(self, deposit_percent: int, due_date=None) -> Optional[Invoice]:
        """
        Create deposit/advance invoice.

        Args:
            deposit_percent: Percentage of estimate total (0-100)
            due_date: Optional due date for invoice

        Returns:
            Created Invoice or None if deposit_percent is 0
        """
        if deposit_percent <= 0 or deposit_percent > 100:
            return None

        # Calculate estimate total
        estimate_total = self._calculate_estimate_total()
        deposit_amount = estimate_total * Decimal(deposit_percent) / Decimal("100")

        # Create invoice
        invoice = Invoice.objects.create(
            project=self.project,
            invoice_number=self._generate_invoice_number(),
            date_issued=timezone.now().date(),
            due_date=due_date or (timezone.now().date() + timedelta(days=30)),
            status="DRAFT",
            invoice_type="deposit",
            total_amount=deposit_amount.quantize(Decimal("0.01")),
        )

        # Create single line item for deposit
        InvoiceLine.objects.create(
            invoice=invoice,
            description=f"Anticipo del proyecto ({deposit_percent}%)",
            amount=deposit_amount.quantize(Decimal("0.01")),
        )

        return invoice

    def _generate_invoice_number(self) -> str:
        """Generate unique invoice number."""
        from django.db.models import Max

        last_invoice = Invoice.objects.aggregate(Max("id"))["id__max"] or 0
        return f"INV-{last_invoice + 1:05d}"

    @transaction.atomic
    def activate_project(
        self,
        start_date,
        create_schedule: bool = True,
        create_budget: bool = True,
        create_tasks: bool = False,
        deposit_percent: int = 0,
        items_to_schedule: Optional[List[EstimateLine]] = None,
        selected_line_ids: Optional[List[int]] = None,
        assigned_to=None,
    ) -> dict[str, Any]:
        """
        Complete project activation workflow.

        Args:
            start_date: Project start date
            create_schedule: Whether to create schedule items
            create_budget: Whether to create budget lines
            create_tasks: Whether to create operational tasks
            deposit_percent: Deposit invoice percentage (0-100)
            items_to_schedule: Optional specific lines to schedule
            assigned_to: Optional user to assign tasks to

        Returns:
            Dictionary with created entities and summary
        """
        # Validate estimate
        is_valid, error = self.validate_estimate()
        if not is_valid:
            raise ValueError(error)

        result = {
            "schedule_items": [],
            "budget_lines": [],
            "tasks": [],
            "invoice": None,
            "summary": {},
        }

        # Create schedule
        if create_schedule:
            schedule_items = self.create_schedule_from_estimate(
                start_date=start_date,
                items_to_schedule=items_to_schedule,
                selected_line_ids=selected_line_ids,
            )
            result["schedule_items"] = schedule_items

            # Create tasks from schedule if requested
            if create_tasks:
                tasks = self.create_tasks_from_schedule(
                    schedule_items=schedule_items, assigned_to=assigned_to
                )
                result["tasks"] = tasks

        # Create budget
        if create_budget:
            budget_lines = self.create_budget_from_estimate()
            result["budget_lines"] = budget_lines

        # Create deposit invoice
        if deposit_percent > 0:
            invoice = self.create_deposit_invoice(deposit_percent=deposit_percent)
            result["invoice"] = invoice

        # Generate summary
        result["summary"] = {
            "schedule_items_count": len(result["schedule_items"]),
            "budget_lines_count": len(result["budget_lines"]),
            "tasks_count": len(result["tasks"]),
            "invoice_created": result["invoice"] is not None,
            "invoice_amount": result["invoice"].total_amount if result["invoice"] else Decimal("0"),
            "estimate_total": self._calculate_estimate_total(),
        }

        return result
