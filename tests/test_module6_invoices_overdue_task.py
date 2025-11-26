import pytest
from datetime import date, timedelta
from django.utils import timezone

@pytest.mark.django_db
class TestInvoiceOverdueTask:
    def test_marks_past_due_invoices_as_overdue(self):
        from core.models import Project, Invoice
        from core.tasks import check_overdue_invoices
        project = Project.objects.create(name="Overdue Proj", client="Client", start_date=timezone.now().date())
        inv = Invoice.objects.create(
            project=project,
            invoice_number="INV-OD-1",
            date_issued=timezone.now().date() - timedelta(days=10),
            due_date=timezone.now().date() - timedelta(days=1),
            status='APPROVED',
            total_amount=1000,
        )

        result = check_overdue_invoices()
        inv.refresh_from_db()

        assert result['updated'] >= 1
        assert inv.status == 'OVERDUE'

    def test_does_not_touch_not_due_or_paid(self):
        from core.models import Project, Invoice
        from core.tasks import check_overdue_invoices
        project = Project.objects.create(name="OnTime Proj", client="Client", start_date=timezone.now().date())
        ontime = Invoice.objects.create(
            project=project,
            invoice_number="INV-ONTIME",
            date_issued=timezone.now().date(),
            due_date=timezone.now().date() + timedelta(days=3),
            status='SENT',
            total_amount=500,
        )
        paid = Invoice.objects.create(
            project=project,
            invoice_number="INV-PAID",
            date_issued=timezone.now().date() - timedelta(days=10),
            due_date=timezone.now().date() - timedelta(days=5),
            status='PAID',
            total_amount=700,
        )

        result = check_overdue_invoices()
        ontime.refresh_from_db()
        paid.refresh_from_db()

        # No updates expected from these
        assert ontime.status == 'SENT'
        assert paid.status == 'PAID'
