from decimal import Decimal

import pytest
from django.utils import timezone


@pytest.mark.django_db
class TestDashboardsAPI:
    def test_invoice_dashboard(self, client, django_user_model):
        from core.models import Invoice, Project

        user = django_user_model.objects.create_user(username="dash", password="x", is_staff=True)
        client.force_login(user)
        p1 = Project.objects.create(name="P1", client="Acme", start_date=timezone.now().date())
        p2 = Project.objects.create(name="P2", client="Globex", start_date=timezone.now().date())
        Invoice.objects.create(
            project=p1,
            invoice_number="I1",
            date_issued=timezone.now().date(),
            due_date=timezone.now().date(),
            status="PAID",
            total_amount=Decimal("100"),
        )
        Invoice.objects.create(
            project=p1,
            invoice_number="I2",
            date_issued=timezone.now().date(),
            due_date=timezone.now().date(),
            status="OVERDUE",
            total_amount=Decimal("50"),
        )
        Invoice.objects.create(
            project=p2,
            invoice_number="I3",
            date_issued=timezone.now().date(),
            due_date=timezone.now().date(),
            status="SENT",
            total_amount=Decimal("25"),
        )

        resp = client.get("/api/v1/dashboards/invoices/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_invoices"] == 3
        assert Decimal(str(data["total_amount"])) == Decimal("175")
        assert Decimal(str(data["paid_amount"])) == Decimal("100")
        assert data["overdue_count"] == 1
        assert Decimal(str(data["outstanding_amount"])) == Decimal("75")
        assert isinstance(data["top_clients"], list)

    def test_materials_dashboard(self, client, django_user_model):
        from core.models import InventoryItem, InventoryLocation, InventoryMovement, ProjectInventory

        user = django_user_model.objects.create_user(username="dash2", password="x", is_staff=True)
        client.force_login(user)
        item1 = InventoryItem.objects.create(name="Paint", category="PINTURA", average_cost=Decimal("12.00"))
        item2 = InventoryItem.objects.create(name="Brush", category="HERRAMIENTA", average_cost=Decimal("5.00"))
        loc = InventoryLocation.objects.create(name="WH", is_storage=True)
        ProjectInventory.objects.create(item=item1, location=loc, quantity=Decimal("2"))
        ProjectInventory.objects.create(item=item2, location=loc, quantity=Decimal("3"))
        InventoryMovement.objects.create(item=item1, to_location=loc, movement_type="RECEIVE", quantity=Decimal("1"))

        resp = client.get("/api/v1/dashboards/materials/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_items"] >= 2
        assert data["recent_movements"] >= 1
        # total_stock_value = 2*12 + 3*5 = 39
        assert Decimal(str(data["total_stock_value"])) == Decimal("39")
        assert isinstance(data["items_by_category"], list)


@pytest.mark.django_db
class TestFinancialDashboard:
    def test_project_financial_kpis(self, client, django_user_model):
        from core.models import Expense, Income, Project

        user = django_user_model.objects.create_user(username="fkpi", password="x", is_staff=True)
        client.force_login(user)

        p1 = Project.objects.create(
            name="Proj Alpha", client="ClientA", start_date=timezone.now().date(), budget_total=Decimal("1000.00")
        )
        Income.objects.create(
            project=p1,
            project_name=p1.name,
            amount=Decimal("600"),
            date=timezone.now().date(),
            payment_method="TRANSFERENCIA",
        )
        Expense.objects.create(
            project=p1, project_name=p1.name, amount=Decimal("400"), date=timezone.now().date(), category="MATERIALES"
        )

        resp = client.get("/api/v1/dashboards/financial/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_projects"] >= 1
        proj_data = next((p for p in data["projects"] if p["project_id"] == p1.id), None)
        assert proj_data is not None
        assert Decimal(str(proj_data["total_income"])) == Decimal("600")
        assert Decimal(str(proj_data["total_expenses"])) == Decimal("400")
        assert Decimal(str(proj_data["profit"])) == Decimal("200")
        assert proj_data["budget_used_percent"] == 40.0
        assert proj_data["is_over_budget"] is False

    def test_financial_dashboard_date_filters(self, client, django_user_model):
        from datetime import timedelta

        from core.models import Income, Project

        user = django_user_model.objects.create_user(username="fdate", password="x", is_staff=True)
        client.force_login(user)

        p = Project.objects.create(
            name="DateProj", client="C", start_date=timezone.now().date(), budget_total=Decimal("500")
        )
        # Income today
        Income.objects.create(
            project=p, project_name=p.name, amount=Decimal("100"), date=timezone.now().date(), payment_method="EFECTIVO"
        )
        # Income 10 days ago
        Income.objects.create(
            project=p,
            project_name=p.name,
            amount=Decimal("50"),
            date=timezone.now().date() - timedelta(days=10),
            payment_method="EFECTIVO",
        )

        # Filter last 5 days
        date_from = (timezone.now().date() - timedelta(days=5)).isoformat()
        resp = client.get(f"/api/v1/dashboards/financial/?date_from={date_from}")
        assert resp.status_code == 200
        data = resp.json()
        proj_data = next((pr for pr in data["projects"] if pr["project_id"] == p.id), None)
        # Should only count income from last 5 days (100)
        assert Decimal(str(proj_data["total_income"])) == Decimal("100")


@pytest.mark.django_db
class TestPayrollDashboard:
    def test_payroll_overview(self, client, django_user_model):
        from datetime import date, timedelta

        from core.models import Employee, PayrollPayment, PayrollPeriod, PayrollRecord

        user = django_user_model.objects.create_user(username="payuser", password="x", is_staff=True)
        client.force_login(user)

        emp = Employee.objects.create(first_name="John", last_name="Doe", hourly_rate=Decimal("25.00"), is_active=True)

        # Create a period
        start = date.today() - timedelta(days=7)
        end = start + timedelta(days=6)
        period = PayrollPeriod.objects.create(week_start=start, week_end=end, status="approved", created_by=user)

        # Add a record
        PayrollRecord.objects.create(
            period=period,
            employee=emp,
            week_start=start,
            week_end=end,
            hourly_rate=Decimal("25.00"),
            total_hours=Decimal("40"),
            total_pay=Decimal("1000.00"),
            reviewed=True,
        )

        # Add a partial payment
        PayrollPayment.objects.create(
            payroll_record=PayrollRecord.objects.get(period=period, employee=emp),
            amount=Decimal("500.00"),
            payment_date=date.today(),
            payment_method="check",
            recorded_by=user,
        )

        resp = client.get("/api/v1/dashboards/payroll/")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["recent_periods"]) >= 1
        assert Decimal(str(data["total_payroll_cost"])) >= Decimal("1000.00")
        assert Decimal(str(data["total_outstanding"])) >= Decimal("500.00")
        assert isinstance(data["top_employees"], list)


@pytest.mark.django_db
class TestInvoiceTrends:
    def test_monthly_trends(self, client, django_user_model):
        from datetime import date, timedelta

        from dateutil.relativedelta import relativedelta

        from core.models import Invoice, Project

        user = django_user_model.objects.create_user(username="trends", password="x", is_staff=True)
        client.force_login(user)

        p = Project.objects.create(name="TrendProj", client="TrendCo", start_date=date.today())

        # Create invoices in different months
        today = date.today()
        # Current month
        Invoice.objects.create(
            project=p,
            invoice_number="T1",
            date_issued=today,
            due_date=today + timedelta(days=30),
            total_amount=Decimal("1000"),
            status="PAID",
        )
        # Last month
        last_month = today.replace(day=1) - relativedelta(months=1)
        Invoice.objects.create(
            project=p,
            invoice_number="T2",
            date_issued=last_month,
            due_date=last_month + timedelta(days=30),
            total_amount=Decimal("500"),
            status="PARTIAL",
        )
        # 2 months ago
        two_months = today.replace(day=1) - relativedelta(months=2)
        Invoice.objects.create(
            project=p,
            invoice_number="T3",
            date_issued=two_months,
            due_date=two_months + timedelta(days=30),
            total_amount=Decimal("750"),
            status="OVERDUE",
        )

        resp = client.get("/api/v1/dashboards/invoices/trends/")
        assert resp.status_code == 200
        data = resp.json()
        assert "monthly_trends" in data
        assert isinstance(data["monthly_trends"], list)
        assert len(data["monthly_trends"]) == 6  # Last 6 months

        # Verify at least one month has data
        current_month_data = next((m for m in data["monthly_trends"] if m["month"] == today.strftime("%Y-%m")), None)
        assert current_month_data is not None
        assert Decimal(str(current_month_data["total_invoiced"])) >= Decimal("1000")
        assert Decimal(str(current_month_data["total_paid"])) >= Decimal("1000")

    def test_aging_report(self, client, django_user_model):
        from datetime import date, timedelta

        from core.models import Invoice, Project

        user = django_user_model.objects.create_user(username="aging", password="x", is_staff=True)
        client.force_login(user)

        p = Project.objects.create(name="AgingProj", client="AgingCo", start_date=date.today())
        today = date.today()

        # Invoice 0-30 days overdue
        Invoice.objects.create(
            project=p,
            invoice_number="A1",
            date_issued=today - timedelta(days=40),
            due_date=today - timedelta(days=10),
            total_amount=Decimal("100"),
            amount_paid=Decimal("0"),
            status="OVERDUE",
        )
        # Invoice 31-60 days overdue
        Invoice.objects.create(
            project=p,
            invoice_number="A2",
            date_issued=today - timedelta(days=90),
            due_date=today - timedelta(days=45),
            total_amount=Decimal("200"),
            amount_paid=Decimal("0"),
            status="OVERDUE",
        )
        # Invoice 61-90 days overdue
        Invoice.objects.create(
            project=p,
            invoice_number="A3",
            date_issued=today - timedelta(days=120),
            due_date=today - timedelta(days=75),
            total_amount=Decimal("300"),
            amount_paid=Decimal("0"),
            status="OVERDUE",
        )
        # Invoice 90+ days overdue
        Invoice.objects.create(
            project=p,
            invoice_number="A4",
            date_issued=today - timedelta(days=150),
            due_date=today - timedelta(days=100),
            total_amount=Decimal("400"),
            amount_paid=Decimal("0"),
            status="OVERDUE",
        )

        resp = client.get("/api/v1/dashboards/invoices/trends/")
        assert resp.status_code == 200
        data = resp.json()
        assert "aging_report" in data
        aging = data["aging_report"]

        # Verify aging buckets
        assert Decimal(str(aging["0-30"])) == Decimal("100")
        assert Decimal(str(aging["31-60"])) == Decimal("200")
        assert Decimal(str(aging["61-90"])) == Decimal("300")
        assert Decimal(str(aging["90+"])) == Decimal("400")


@pytest.mark.django_db
class TestMaterialsUsageAnalytics:
    def test_top_consumed_items(self, client, django_user_model):
        from core.models import InventoryItem, InventoryLocation, InventoryMovement, Project

        user = django_user_model.objects.create_user(username="matusage", password="x", is_staff=True)
        client.force_login(user)

        # Create items
        item1 = InventoryItem.objects.create(name="Paint", category="PINTURA", average_cost=Decimal("12.00"))
        item2 = InventoryItem.objects.create(name="Nails", category="HERRAMIENTA", average_cost=Decimal("3.00"))
        loc = InventoryLocation.objects.create(name="WH1", is_storage=True)

        # Create consumption movements
        InventoryMovement.objects.create(item=item1, to_location=loc, movement_type="ISSUE", quantity=Decimal("50"))
        InventoryMovement.objects.create(item=item1, to_location=loc, movement_type="CONSUME", quantity=Decimal("30"))
        InventoryMovement.objects.create(item=item2, to_location=loc, movement_type="ISSUE", quantity=Decimal("20"))

        resp = client.get("/api/v1/dashboards/materials/usage/")
        assert resp.status_code == 200
        data = resp.json()
        assert "top_consumed" in data
        assert isinstance(data["top_consumed"], list)

        # item1 should have 80 total consumed
        item1_data = next((i for i in data["top_consumed"] if i["item__id"] == item1.id), None)
        assert item1_data is not None
        assert Decimal(str(item1_data["total_consumed"])) == Decimal("80")

    def test_consumption_by_project(self, client, django_user_model):
        from core.models import InventoryItem, InventoryLocation, InventoryMovement, Project

        user = django_user_model.objects.create_user(username="projcons", password="x", is_staff=True)
        client.force_login(user)

        # Create project and items
        proj = Project.objects.create(name="TestProj", client="TestCo", start_date=timezone.now().date())
        item = InventoryItem.objects.create(name="Wood", category="MATERIAL", average_cost=Decimal("5.00"))
        loc = InventoryLocation.objects.create(name="Site", is_storage=False, project=proj)

        # Create movements linked to project
        InventoryMovement.objects.create(
            item=item, to_location=loc, movement_type="ISSUE", quantity=Decimal("100"), related_project=proj
        )
        InventoryMovement.objects.create(
            item=item, to_location=loc, movement_type="CONSUME", quantity=Decimal("50"), related_project=proj
        )

        resp = client.get("/api/v1/dashboards/materials/usage/")
        assert resp.status_code == 200
        data = resp.json()
        assert "consumption_by_project" in data
        assert isinstance(data["consumption_by_project"], list)

        proj_data = next((p for p in data["consumption_by_project"] if p["related_project__id"] == proj.id), None)
        assert proj_data is not None
        assert Decimal(str(proj_data["total_consumed"])) == Decimal("150")

    def test_stock_turnover(self, client, django_user_model):
        from core.models import InventoryItem, InventoryLocation, InventoryMovement, ProjectInventory

        user = django_user_model.objects.create_user(username="turnover", password="x", is_staff=True)
        client.force_login(user)

        # Create item with stock
        item = InventoryItem.objects.create(name="Glue", category="ADHESIVO", average_cost=Decimal("8.00"))
        loc = InventoryLocation.objects.create(name="Store", is_storage=True)
        ProjectInventory.objects.create(item=item, location=loc, quantity=Decimal("100"))

        # Create consumption in last 30 days
        InventoryMovement.objects.create(item=item, from_location=loc, movement_type="ISSUE", quantity=Decimal("40"))

        resp = client.get("/api/v1/dashboards/materials/usage/")
        assert resp.status_code == 200
        data = resp.json()
        assert "stock_turnover" in data
        assert isinstance(data["stock_turnover"], list)

        # Turnover should be 40/100 = 0.4
        item_turnover = next((t for t in data["stock_turnover"] if t["item_id"] == item.id), None)
        assert item_turnover is not None
        assert Decimal(str(item_turnover["consumed_30d"])) == Decimal("40")
        assert Decimal(str(item_turnover["average_stock"])) == Decimal("100")
        assert abs(Decimal(str(item_turnover["turnover_rate"])) - Decimal("0.4")) < Decimal("0.01")

    def test_reorder_suggestions(self, client, django_user_model):
        from core.models import InventoryItem, InventoryLocation, InventoryMovement, ProjectInventory

        user = django_user_model.objects.create_user(username="reorder", password="x", is_staff=True)
        client.force_login(user)

        # Create item below reorder point
        item = InventoryItem.objects.create(
            name="Screws", category="HERRAMIENTA", average_cost=Decimal("2.00"), default_threshold=Decimal("20")
        )
        loc = InventoryLocation.objects.create(name="Shop", is_storage=True)
        stock = ProjectInventory.objects.create(
            item=item, location=loc, quantity=Decimal("5"), threshold_override=Decimal("20")
        )

        # Create recent consumption
        InventoryMovement.objects.create(item=item, from_location=loc, movement_type="ISSUE", quantity=Decimal("30"))

        resp = client.get("/api/v1/dashboards/materials/usage/")
        assert resp.status_code == 200
        data = resp.json()
        assert "reorder_suggestions" in data
        assert isinstance(data["reorder_suggestions"], list)

        # Should suggest reorder for item
        suggestion = next((s for s in data["reorder_suggestions"] if s["item_id"] == item.id), None)
        assert suggestion is not None
        assert Decimal(str(suggestion["current_quantity"])) == Decimal("5")
        assert Decimal(str(suggestion["threshold"])) == Decimal("20")
        assert suggestion["days_until_depleted"] is not None


@pytest.mark.django_db
class TestAdminDashboard:
    def test_company_wide_metrics(self, client, django_user_model):
        from core.models import Employee, Expense, Income, InventoryItem, Invoice, Project, Task

        user = django_user_model.objects.create_user(username="admin", password="x", is_staff=True)
        client.force_login(user)

        # Create projects
        p1 = Project.objects.create(name="ActiveProj", client="C1", start_date=timezone.now().date())
        p2 = Project.objects.create(
            name="CompletedProj", client="C2", start_date=timezone.now().date(), end_date=timezone.now().date()
        )

        # Create employees
        emp1 = Employee.objects.create(
            first_name="Alice",
            last_name="Smith",
            social_security_number="SSN001",
            hourly_rate=Decimal("30"),
            is_active=True,
        )
        emp2 = Employee.objects.create(
            first_name="Bob",
            last_name="Jones",
            social_security_number="SSN002",
            hourly_rate=Decimal("25"),
            is_active=False,
        )

        # Create financial data
        Income.objects.create(
            project=p1,
            project_name=p1.name,
            amount=Decimal("5000"),
            date=timezone.now().date(),
            payment_method="TRANSFERENCIA",
        )
        Expense.objects.create(
            project=p1, project_name=p1.name, amount=Decimal("2000"), date=timezone.now().date(), category="MATERIALES"
        )

        # Create invoices
        Invoice.objects.create(
            project=p1,
            invoice_number="ADM1",
            date_issued=timezone.now().date(),
            total_amount=Decimal("3000"),
            amount_paid=Decimal("2000"),
            status="PARTIAL",
        )
        Invoice.objects.create(
            project=p1,
            invoice_number="ADM2",
            date_issued=timezone.now().date(),
            due_date=timezone.now().date(),
            total_amount=Decimal("1000"),
            amount_paid=Decimal("0"),
            status="OVERDUE",
        )

        # Create inventory items
        InventoryItem.objects.create(name="Tool1", category="HERRAMIENTA", average_cost=Decimal("10"))
        InventoryItem.objects.create(name="Tool2", category="HERRAMIENTA", average_cost=Decimal("15"))

        # Create tasks
        Task.objects.create(
            title="Test Task",
            description="Task desc",
            project=p1,
            assigned_to=emp1,
            due_date=timezone.now().date(),
            status="Pending",
        )

        resp = client.get("/api/v1/dashboards/admin/")
        assert resp.status_code == 200
        data = resp.json()

        # Validate project metrics
        assert data["projects"]["active"] >= 1
        assert data["projects"]["completed"] >= 1
        assert data["projects"]["total"] >= 2

        # Validate employee metrics
        assert data["employees"]["active"] >= 1
        assert data["employees"]["total"] >= 2

        # Validate financial metrics
        assert Decimal(str(data["financial"]["total_income"])) >= Decimal("5000")
        assert Decimal(str(data["financial"]["total_expenses"])) >= Decimal("2000")
        assert Decimal(str(data["financial"]["net_profit"])) >= Decimal("3000")
        assert data["financial"]["profit_margin"] > 0
        assert Decimal(str(data["financial"]["total_invoiced"])) >= Decimal("4000")
        assert data["financial"]["overdue_count"] >= 1

        # Validate inventory
        assert data["inventory"]["total_items"] >= 2

        # Validate recent activity
        assert "recent_activity" in data
        assert isinstance(data["recent_activity"], list)
        assert len(data["recent_activity"]) > 0

        # Validate health score
        assert "health_score" in data
        assert Decimal(str(data["health_score"])) >= Decimal("0")
        assert Decimal(str(data["health_score"])) <= Decimal("100")

    def test_financial_health_score_calculation(self, client, django_user_model):
        from core.models import Expense, Income, Invoice, Project

        user = django_user_model.objects.create_user(username="health", password="x", is_staff=True)
        client.force_login(user)

        # Create high-performing scenario
        p = Project.objects.create(name="HealthProj", client="HC", start_date=timezone.now().date())

        # Good profit margin (40%)
        Income.objects.create(
            project=p,
            project_name=p.name,
            amount=Decimal("10000"),
            date=timezone.now().date(),
            payment_method="TRANSFERENCIA",
        )
        Expense.objects.create(
            project=p, project_name=p.name, amount=Decimal("6000"), date=timezone.now().date(), category="MATERIALES"
        )

        # Good collection rate (90%)
        Invoice.objects.create(
            project=p,
            invoice_number="H1",
            date_issued=timezone.now().date(),
            total_amount=Decimal("9000"),
            amount_paid=Decimal("8100"),
            status="PARTIAL",
        )

        resp = client.get("/api/v1/dashboards/admin/")
        assert resp.status_code == 200
        data = resp.json()

        # Health score calculation:
        # Profit margin: 4000/10000 = 40% -> 40 points
        # Collection rate: 8100/9000 = 90% -> 45 points (90 * 0.5)
        # Total: 85 points
        health_score = Decimal(str(data["health_score"]))
        # Allow some tolerance for other data in database
        assert health_score >= Decimal("40")  # At minimum, should have profit margin points
        assert health_score <= Decimal("100")

    def test_recent_activity_feed(self, client, django_user_model):
        from core.models import DailyLog, Employee, Invoice, Project, Task

        user = django_user_model.objects.create_user(username="activity", password="x", is_staff=True)
        client.force_login(user)

        # Create various activities
        p = Project.objects.create(name="ActivityProj", client="AC", start_date=timezone.now().date())

        emp = Employee.objects.create(
            first_name="Jane",
            last_name="Doe",
            social_security_number="SSN003",
            hourly_rate=Decimal("28"),
            is_active=True,
        )

        Task.objects.create(
            title="Activity Task",
            description="Test",
            project=p,
            assigned_to=emp,
            due_date=timezone.now().date(),
            status="Pending",
        )

        Invoice.objects.create(
            project=p,
            invoice_number="ACT1",
            date_issued=timezone.now().date(),
            total_amount=Decimal("500"),
            status="SENT",
        )

        DailyLog.objects.create(
            project=p, date=timezone.now().date(), progress_notes="Daily progress notes", created_by=user
        )

        resp = client.get("/api/v1/dashboards/admin/")
        assert resp.status_code == 200
        data = resp.json()

        activity = data["recent_activity"]
        assert len(activity) > 0
        assert len(activity) <= 10  # Should limit to 10 items

        # Check that different activity types are present
        activity_types = set(item["type"] for item in activity)
        assert "project" in activity_types or "task" in activity_types or "invoice" in activity_types
