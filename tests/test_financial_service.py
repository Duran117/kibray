from decimal import Decimal
from datetime import date, timedelta, time
from django.test import TestCase
from django.utils import timezone

from core.services.financial_service import FinancialAnalyticsService
from core.models import Project, Employee, TimeEntry, Expense, Invoice, PayrollRecord, InventoryItem, InventoryLocation, ProjectInventory

class FinancialAnalyticsServiceTests(TestCase):
    def setUp(self):
        today = timezone.localdate()
        # Project
        self.project = Project.objects.create(
            name="Test Project",
            start_date=today - timedelta(days=10),
            total_income=Decimal("0"),
            total_expenses=Decimal("0"),
        )
        # Employee
        self.employee = Employee.objects.create(
            first_name="Ana",
            last_name="Dev",
            social_security_number="SSN-123",
            hourly_rate=Decimal("50.00"),
        )
        # TimeEntry (2h billable)
        TimeEntry.objects.create(
            employee=self.employee,
            project=self.project,
            date=today,
            start_time=time(8,0),
            end_time=time(10,0),
            hours_worked=Decimal("2.00"),
        )
        # Expense (material) last week
        Expense.objects.create(
            project=self.project,
            amount=Decimal("150.00"),
            project_name="Test Project",
            date=today - timedelta(days=7),
            category="MATERIALES",
            description="material purchase",
        )
        # Invoice due next week (collectible)
        self.invoice1 = Invoice.objects.create(
            project=self.project,
            invoice_number="INV-TEST-1",
            date_issued=today,
            due_date=today + timedelta(days=7),
            total_amount=Decimal("1000.00"),
            status="SENT",
            amount_paid=Decimal("200.00"),  # partial payment
        )
        # Another invoice fully paid should not contribute to receivables
        self.invoice2 = Invoice.objects.create(
            project=self.project,
            invoice_number="INV-TEST-2",
            date_issued=today,
            due_date=today + timedelta(days=3),
            total_amount=Decimal("500.00"),
            status="APPROVED",
            amount_paid=Decimal("500.00"),
        )
        # PayrollRecord in last month for burn rate
        PayrollRecord.objects.create(
            employee=self.employee,
            week_start=today - timedelta(days=14),
            week_end=today - timedelta(days=8),
            hourly_rate=Decimal("50.00"),
            total_hours=Decimal("10.00"),
            net_pay=Decimal("500.00"),
        )
        # Inventory low stock
        item = InventoryItem.objects.create(name="Primer", category="MATERIAL", default_threshold=Decimal("10"))
        loc = InventoryLocation.objects.create(name="Main", project=self.project)
        ProjectInventory.objects.create(item=item, location=loc, quantity=Decimal("2"))

        self.service = FinancialAnalyticsService(as_of=today)

    def test_cash_flow_projection_has_week_label(self):
        data = self.service.get_cash_flow_projection(days=14)
        chart = data["chart"]
        self.assertIn("labels", chart)
        # At least one week label included
        self.assertTrue(any(lbl.startswith("W") for lbl in chart["labels"]))
        # Income should reflect invoice1 total (1000) not including paid portion yet (total used in projection)
        self.assertIn(1000.0, chart["income"])  # float representation

    def test_company_health_kpis_refined_receivables(self):
        kpis = self.service.get_company_health_kpis()
        # Receivables should be remaining balance of invoice1 only: 1000 - 200 = 800
        self.assertEqual(kpis["total_receivables"], 800.0)

    def test_inventory_risk_items_includes_low_stock(self):
        items = self.service.get_inventory_risk_items()
        self.assertTrue(any(i["item_name"] == "Primer" for i in items))

    def test_project_margins_computation(self):
        margins = self.service.get_project_margins()
        proj = next((m for m in margins if m["project_id"] == self.project.id), None)
        self.assertIsNotNone(proj)
        # Invoiced sum should include both invoices (1000 + 500)
        self.assertEqual(int(proj["invoiced"]), 1500)
        # Labor cost should be > 0 given time entry
        self.assertGreater(proj["labor_cost"], 0.0)
        # Margin pct within plausible range
        self.assertGreaterEqual(proj["margin_pct"], -100.0)
        self.assertLessEqual(proj["margin_pct"], 100.0)
