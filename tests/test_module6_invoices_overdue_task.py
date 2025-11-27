from datetime import date, timedelta

import pytest
from django.utils import timezone


@pytest.mark.django_db
class TestInvoiceOverdueTask:
    def test_marks_past_due_invoices_as_overdue(self):
        from core.models import Invoice, Project
        from core.tasks import check_overdue_invoices

        # Use date.today() for reliable date arithmetic in tests
        today = date.today()
        project = Project.objects.create(name="Overdue Proj", client="Client", start_date=today)

        # Create invoice with explicit past due_date (yesterday)
        inv = Invoice.objects.create(
            project=project,
            invoice_number="INV-OD-1",
            date_issued=today - timedelta(days=10),
            due_date=today - timedelta(days=1),  # Yesterday
            status="APPROVED",
            total_amount=1000,
        )

        result = check_overdue_invoices()
        inv.refresh_from_db()

        assert result["updated"] >= 1, f"Expected at least 1 updated, got {result['updated']}"
        assert inv.status == "OVERDUE", f"Expected OVERDUE, got {inv.status}"

    def test_does_not_touch_not_due_or_paid(self):
        from core.models import Invoice, Project
        from core.tasks import check_overdue_invoices

        # Use date.today() for reliable date arithmetic
        today = date.today()
        project = Project.objects.create(name="OnTime Proj", client="Client", start_date=today)

        ontime = Invoice.objects.create(
            project=project,
            invoice_number="INV-ONTIME",
            date_issued=today,
            due_date=today + timedelta(days=3),  # Future
            status="SENT",
            total_amount=500,
        )
        paid = Invoice.objects.create(
            project=project,
            invoice_number="INV-PAID",
            date_issued=today - timedelta(days=10),
            due_date=today - timedelta(days=5),  # Past, but already PAID
            status="PAID",
            total_amount=700,
        )

        result = check_overdue_invoices()
        ontime.refresh_from_db()
        paid.refresh_from_db()

        # No updates expected from these
        assert ontime.status == "SENT"
        assert paid.status == "PAID"
