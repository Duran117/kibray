from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import models
from django.utils import timezone

from core.models import Expense, Project, WarrantyTicket


class Command(BaseCommand):
    help = "Simulate warranty scenario: archive closed project, create warranty ticket, record expense, and print profit vs warranty loss."

    def handle(self, *args, **options):
        # 1. Create a closed project "Old House"
        project, _ = Project.objects.get_or_create(
            name="Old House",
            defaults={
                "start_date": timezone.now().date(),
                "end_date": timezone.now().date(),
                "total_income": Decimal("1000.00"),
                "total_expenses": Decimal("700.00"),
            },
        )

        # 2. Archive it
        project.archive_project()

        # 3. Create a WarrantyTicket for "Leaking pipe"
        ticket = WarrantyTicket.objects.create(
            project=project,
            issue_description="Leaking pipe",
            priority="urgent",
        )

        # 4. Create an Expense of $50 linked to that Warranty Ticket
        Expense.objects.create(
            project=None,
            project_name=project.name,
            amount=Decimal("50.00"),
            date=timezone.now().date(),
            category="MATERIALES",
            description="Repair materials",
            warranty_ticket=ticket,
        )

        # 5. Print: "Project Profit vs. Warranty Loss"
        profit = project.profit()
        warranty_loss = ticket.expenses.aggregate(total=models.Sum("amount")).get("total") or Decimal("0.00")
        self.stdout.write(self.style.SUCCESS(
            f"Project Profit vs. Warranty Loss: {profit} vs {warranty_loss}"
        ))
