"""
Tests for Gap E: Advanced Financial Reporting API & Gap F: Client Portal API

Combined tests for financial and client portal endpoints.
"""

import pytest
from decimal import Decimal
from datetime import timedelta
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient

from core.models import (
    Invoice,
    Project,
    Expense,
    ClientProjectAccess
)

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def staff_user():
    return User.objects.create_user(username="staffuser", password="testpass", is_staff=True)


@pytest.fixture
def client_user():
    return User.objects.create_user(username="clientuser", password="testpass", is_staff=False)


@pytest.fixture
def project():
    return Project.objects.create(
        name="Test Project",
        client="Test Client",
        start_date=timezone.now().date(),
        budget_total=Decimal("50000.00"),
        budget_labor=Decimal("20000.00"),
        budget_materials=Decimal("25000.00"),
        budget_other=Decimal("5000.00")
    )


@pytest.fixture
def setup_invoice_data(project):
    """Create invoices with different statuses and ages."""
    today = timezone.now().date()
    
    # Current invoice (15 days old)
    inv1 = Invoice.objects.create(
        project=project,
        invoice_number="INV-2025-001",
        date_issued=today - timedelta(days=15),
        due_date=today + timedelta(days=15),
        total_amount=Decimal("5000.00"),
        amount_paid=Decimal("0"),
        status="SENT"
    )
    
    # 45 days old (31-60 bucket)
    inv2 = Invoice.objects.create(
        project=project,
        invoice_number="INV-2025-002",
        date_issued=today - timedelta(days=45),
        due_date=today - timedelta(days=15),
        total_amount=Decimal("7500.00"),
        amount_paid=Decimal("3000.00"),
        status="PARTIAL"
    )
    
    # 75 days old (61-90 bucket)
    inv3 = Invoice.objects.create(
        project=project,
        invoice_number="INV-2025-003",
        date_issued=today - timedelta(days=75),
        due_date=today - timedelta(days=45),
        total_amount=Decimal("3000.00"),
        amount_paid=Decimal("0"),
        status="OVERDUE"
    )
    
    # 120 days old (90+ bucket)
    inv4 = Invoice.objects.create(
        project=project,
        invoice_number="INV-2025-004",
        date_issued=today - timedelta(days=120),
        due_date=today - timedelta(days=90),
        total_amount=Decimal("2000.00"),
        amount_paid=Decimal("0"),
        status="OVERDUE"
    )
    
    return {
        "current": inv1,
        "30_60": inv2,
        "60_90": inv3,
        "over_90": inv4
    }


# =============================================================================
# GAP E: ADVANCED FINANCIAL REPORTING TESTS
# =============================================================================


@pytest.mark.django_db
def test_invoice_aging_report(api_client, staff_user, setup_invoice_data):
    """Test aging report API endpoint."""
    api_client.force_authenticate(user=staff_user)
    
    response = api_client.get("/api/v1/financial/aging-report/")
    
    assert response.status_code == 200
    data = response.json()
    
    # Check structure
    assert "report_date" in data
    assert "aging_buckets" in data
    assert "totals" in data
    assert "grand_total" in data
    assert "summary" in data
    
    # Check buckets exist
    assert "current" in data["aging_buckets"]
    assert "30_60" in data["aging_buckets"]
    assert "60_90" in data["aging_buckets"]
    assert "over_90" in data["aging_buckets"]
    
    # Check invoice counts
    assert len(data["aging_buckets"]["current"]) == 1
    assert len(data["aging_buckets"]["30_60"]) == 1
    assert len(data["aging_buckets"]["60_90"]) == 1
    assert len(data["aging_buckets"]["over_90"]) == 1
    
    # Check totals (balance_due considers partial payment)
    # inv1: 5000 - 0 = 5000
    # inv2: 7500 - 3000 = 4500  
    # inv3: 3000 - 0 = 3000
    # inv4: 2000 - 0 = 2000
    # Total: 14500
    assert Decimal(data["grand_total"]) == Decimal("14500.00")


@pytest.mark.django_db
def test_cash_flow_projection(api_client, staff_user, setup_invoice_data, project):
    """Test cash flow projection API endpoint."""
    api_client.force_authenticate(user=staff_user)
    
    # Add some expenses
    Expense.objects.create(
        project=project,
        category="LABOR",
        description="Labor costs",
        amount=Decimal("15000.00"),
        date=timezone.now().date()
    )
    
    response = api_client.get("/api/v1/financial/cash-flow-projection/")
    
    assert response.status_code == 200
    data = response.json()
    
    # Check structure
    assert "projection_date" in data
    assert "inflows" in data
    assert "outflows" in data
    assert "net_projection" in data
    assert "health_indicator" in data
    
    # Check inflows
    assert "total_expected" in data["inflows"]
    assert "by_week" in data["inflows"]
    
    # Check outflows
    assert "projected_expenses" in data["outflows"]
    assert "projects" in data["outflows"]


@pytest.mark.django_db
def test_budget_variance_analysis(api_client, staff_user, project):
    """Test budget variance analysis API endpoint."""
    api_client.force_authenticate(user=staff_user)
    
    # Add expenses
    Expense.objects.create(
        project=project,
        category="LABOR",
        description="Labor",
        amount=Decimal("18000.00"),
        date=timezone.now().date()
    )
    
    Expense.objects.create(
        project=project,
        category="MATERIALES",
        description="Materials",
        amount=Decimal("22000.00"),
        date=timezone.now().date()
    )
    
    response = api_client.get("/api/v1/financial/budget-variance/")
    
    assert response.status_code == 200
    data = response.json()
    
    # Check structure
    assert "summary" in data
    assert "projects" in data
    
    # Check summary
    assert "total_projects" in data["summary"]
    assert "total_budget" in data["summary"]
    assert "total_actual" in data["summary"]
    assert "overall_variance" in data["summary"]
    
    # Check project data
    assert len(data["projects"]) >= 1
    
    project_data = data["projects"][0]
    assert "budget" in project_data
    assert "actual" in project_data
    assert "variance" in project_data
    assert "status" in project_data
    
    # Verify calculations
    assert Decimal(project_data["actual"]["total"]) == Decimal("40000.00")
    assert Decimal(project_data["budget"]["total"]) == Decimal("50000.00")
    assert project_data["status"] == "under_budget"


@pytest.mark.django_db
def test_budget_variance_single_project(api_client, staff_user, project):
    """Test budget variance for specific project."""
    api_client.force_authenticate(user=staff_user)
    
    response = api_client.get(f"/api/v1/financial/budget-variance/?project={project.id}")
    
    assert response.status_code == 200
    data = response.json()
    
    assert len(data["projects"]) == 1
    assert data["projects"][0]["project_id"] == project.id


@pytest.mark.django_db
def test_financial_endpoints_require_auth(api_client):
    """Test all financial endpoints require authentication."""
    endpoints = [
        "/api/v1/financial/aging-report/",
        "/api/v1/financial/cash-flow-projection/",
        "/api/v1/financial/budget-variance/"
    ]
    
    for endpoint in endpoints:
        response = api_client.get(endpoint)
        assert response.status_code == 401


# =============================================================================
# GAP F: CLIENT PORTAL TESTS
# =============================================================================


@pytest.mark.django_db
def test_client_invoice_list(api_client, client_user, project, setup_invoice_data):
    """Test client invoice list endpoint."""
    # Grant client access to project
    ClientProjectAccess.objects.create(
        user=client_user,
        project=project,
        role="client"
    )
    
    api_client.force_authenticate(user=client_user)
    
    response = api_client.get("/api/v1/client/invoices/")
    
    assert response.status_code == 200
    data = response.json()
    
    # Check structure
    assert "invoices" in data
    assert "total_count" in data
    assert "accessible_projects" in data
    
    # Should see all invoices for accessible project
    assert data["total_count"] == 4
    assert len(data["invoices"]) == 4
    
    # Check invoice data structure
    invoice = data["invoices"][0]
    assert "id" in invoice
    assert "invoice_number" in invoice
    assert "project" in invoice
    assert "date_issued" in invoice
    assert "total_amount" in invoice
    assert "balance_due" in invoice
    assert "status" in invoice
    assert "can_approve" in invoice


@pytest.mark.django_db
def test_client_invoice_list_status_filter(api_client, client_user, project, setup_invoice_data):
    """Test client invoice list with status filter."""
    ClientProjectAccess.objects.create(user=client_user, project=project, role="client")
    api_client.force_authenticate(user=client_user)
    
    response = api_client.get("/api/v1/client/invoices/?status=SENT")
    
    assert response.status_code == 200
    data = response.json()
    
    # Should only see SENT invoices
    assert data["total_count"] == 1
    assert data["invoices"][0]["status"] == "SENT"


@pytest.mark.django_db
def test_client_invoice_approval(api_client, client_user, project, setup_invoice_data):
    """Test client can approve invoice."""
    ClientProjectAccess.objects.create(user=client_user, project=project, role="client")
    api_client.force_authenticate(user=client_user)
    
    invoice = setup_invoice_data["current"]  # SENT status
    
    response = api_client.post(f"/api/v1/client/invoices/{invoice.id}/approve/")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["message"] == "Invoice approved successfully"
    assert data["invoice"]["status"] == "APPROVED"
    
    # Verify in database
    invoice.refresh_from_db()
    assert invoice.status == "APPROVED"
    assert invoice.approved_date is not None


@pytest.mark.django_db
def test_client_invoice_approval_no_access(api_client, client_user, project, setup_invoice_data):
    """Test client cannot approve invoice without access."""
    api_client.force_authenticate(user=client_user)
    
    invoice = setup_invoice_data["current"]
    
    response = api_client.post(f"/api/v1/client/invoices/{invoice.id}/approve/")
    
    assert response.status_code == 403
    assert "do not have access" in response.json()["error"]


@pytest.mark.django_db
def test_client_cannot_approve_paid_invoice(api_client, client_user, project):
    """Test client cannot approve already paid invoice."""
    ClientProjectAccess.objects.create(user=client_user, project=project, role="client")
    api_client.force_authenticate(user=client_user)
    
    # Create paid invoice
    invoice = Invoice.objects.create(
        project=project,
        invoice_number="INV-PAID",
        date_issued=timezone.now().date(),
        total_amount=Decimal("1000.00"),
        amount_paid=Decimal("1000.00"),
        status="PAID"
    )
    
    response = api_client.post(f"/api/v1/client/invoices/{invoice.id}/approve/")
    
    assert response.status_code == 400
    assert "cannot be approved" in response.json()["error"]


@pytest.mark.django_db
def test_client_portal_requires_auth(api_client):
    """Test client portal endpoints require authentication."""
    response = api_client.get("/api/v1/client/invoices/")
    assert response.status_code == 401
    
    response = api_client.post("/api/v1/client/invoices/1/approve/")
    assert response.status_code == 401


@pytest.mark.django_db
def test_client_invoice_list_no_access(api_client, client_user):
    """Test client with no project access sees empty list."""
    api_client.force_authenticate(user=client_user)
    
    response = api_client.get("/api/v1/client/invoices/")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["total_count"] == 0
    assert len(data["invoices"]) == 0
    assert len(data["accessible_projects"]) == 0
