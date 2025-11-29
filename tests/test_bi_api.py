"""Tests for BI Analytics API endpoints."""
import pytest
from decimal import Decimal
from datetime import date, timedelta, time
from django.urls import reverse
from rest_framework.test import APIClient
from django.contrib.auth.models import User
from django.utils import timezone

from core.models import (
    Project, Employee, TimeEntry, Expense, Invoice, 
    PayrollRecord, InventoryItem, InventoryLocation, ProjectInventory
)


@pytest.fixture
def api_client():
    """Create API client."""
    return APIClient()


@pytest.fixture
def admin_user(db):
    """Create admin user."""
    user = User.objects.create_user(
        username="admin",
        email="admin@test.com",
        password="testpass123",
        is_staff=True,
        is_superuser=True
    )
    return user


@pytest.fixture
def test_data(db):
    """Create test data for BI analytics."""
    today = timezone.localdate()
    
    # Project
    project = Project.objects.create(
        name="BI Test Project",
        start_date=today - timedelta(days=10),
        total_income=Decimal("0"),
        total_expenses=Decimal("0"),
    )
    
    # Employee
    employee = Employee.objects.create(
        first_name="Test",
        last_name="Employee",
        social_security_number="SSN-BI-123",
        hourly_rate=Decimal("50.00"),
    )
    
    # TimeEntry (billable)
    TimeEntry.objects.create(
        employee=employee,
        project=project,
        date=today,
        start_time=time(8, 0),
        end_time=time(12, 0),
        hours_worked=Decimal("4.00"),
    )
    
    # Expense (material)
    Expense.objects.create(
        project=project,
        amount=Decimal("200.00"),
        project_name="BI Test Project",
        date=today - timedelta(days=5),
        category="MATERIALES",
        description="Test material expense",
    )
    
    # Invoice with partial payment
    invoice = Invoice.objects.create(
        project=project,
        invoice_number="INV-BI-001",
        date_issued=today,
        due_date=today + timedelta(days=7),
        total_amount=Decimal("2000.00"),
        status="SENT",
        amount_paid=Decimal("500.00"),
    )
    
    # PayrollRecord
    PayrollRecord.objects.create(
        employee=employee,
        week_start=today - timedelta(days=14),
        week_end=today - timedelta(days=8),
        hourly_rate=Decimal("50.00"),
        total_hours=Decimal("10.00"),
        net_pay=Decimal("500.00"),
    )
    
    # Inventory low stock
    item = InventoryItem.objects.create(
        name="Test Paint",
        category="PINTURA",
        default_threshold=Decimal("10")
    )
    loc = InventoryLocation.objects.create(name="Test Location", project=project)
    ProjectInventory.objects.create(item=item, location=loc, quantity=Decimal("3"))
    
    return {
        "project": project,
        "employee": employee,
        "invoice": invoice,
        "item": item,
    }


@pytest.mark.django_db
class TestBIAnalyticsAPI:
    """Test BI Analytics API endpoints."""
    
    def test_kpis_endpoint_requires_auth(self, api_client):
        """Test that KPIs endpoint requires authentication."""
        url = reverse("bi-analytics-company-kpis")
        response = api_client.get(url)
        assert response.status_code == 401
    
    def test_kpis_endpoint_success(self, api_client, admin_user, test_data):
        """Test KPIs endpoint returns correct data."""
        api_client.force_authenticate(user=admin_user)
        url = reverse("bi-analytics-company-kpis")
        
        from django.core.cache import cache
        cache.clear()  # Clear cached KPIs
        
        response = api_client.get(url)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "net_profit" in data
        assert "total_receivables" in data
        assert "burn_rate" in data
        
        # Receivables should be 1500 (2000 - 500 paid)
        assert data["total_receivables"] == 1500.0
    
    def test_cash_flow_endpoint_success(self, api_client, admin_user, test_data):
        """Test cash flow projection endpoint."""
        api_client.force_authenticate(user=admin_user)
        url = reverse("bi-analytics-cash-flow-projection")
        
        from django.core.cache import cache
        cache.clear()
        
        response = api_client.get(url, {"days": 14})
        
        assert response.status_code == 200
        data = response.json()
        
        assert "rows" in data
        assert "chart" in data
        assert isinstance(data["rows"], list)
        assert "labels" in data["chart"]
        assert "income" in data["chart"]
        assert "expense" in data["chart"]
    
    def test_margins_endpoint_success(self, api_client, admin_user, test_data):
        """Test project margins endpoint."""
        api_client.force_authenticate(user=admin_user)
        url = reverse("bi-analytics-project-margins")
        
        from django.core.cache import cache
        cache.clear()
        
        response = api_client.get(url)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "projects" in data
        assert isinstance(data["projects"], list)
        
        # Should include our test project
        project_names = [p["project_name"] for p in data["projects"]]
        assert "BI Test Project" in project_names
    
    def test_inventory_risk_endpoint_success(self, api_client, admin_user, test_data):
        """Test inventory risk endpoint."""
        api_client.force_authenticate(user=admin_user)
        url = reverse("bi-analytics-inventory-risk")
        
        from django.core.cache import cache
        cache.clear()
        
        response = api_client.get(url)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "items" in data
        assert isinstance(data["items"], list)
        
        # Should include our low-stock item
        item_names = [item["item_name"] for item in data["items"]]
        assert "Test Paint" in item_names
    
    def test_top_performers_endpoint_success(self, api_client, admin_user, test_data):
        """Test top performers endpoint."""
        api_client.force_authenticate(user=admin_user)
        url = reverse("bi-analytics-top-performers")
        
        response = api_client.get(url, {"limit": 10})
        
        assert response.status_code == 200
        data = response.json()
        
        assert "employees" in data
        assert isinstance(data["employees"], list)
    
    def test_kpis_with_custom_date(self, api_client, admin_user, test_data):
        """Test KPIs endpoint with custom as_of date."""
        api_client.force_authenticate(user=admin_user)
        url = reverse("bi-analytics-company-kpis")
        
        from django.core.cache import cache
        cache.clear()
        
        custom_date = (timezone.localdate() - timedelta(days=5)).strftime("%Y-%m-%d")
        response = api_client.get(url, {"as_of": custom_date})
        
        assert response.status_code == 200
        data = response.json()
        assert "net_profit" in data
    
    def test_invalid_date_format(self, api_client, admin_user):
        """Test that invalid date format returns 400."""
        api_client.force_authenticate(user=admin_user)
        url = reverse("bi-analytics-company-kpis")
        
        response = api_client.get(url, {"as_of": "invalid-date"})
        
        assert response.status_code == 400
        assert "error" in response.json()
    
    def test_invalid_days_parameter(self, api_client, admin_user):
        """Test that invalid days parameter returns 400."""
        api_client.force_authenticate(user=admin_user)
        url = reverse("bi-analytics-cash-flow-projection")
        
        response = api_client.get(url, {"days": "not-a-number"})
        
        assert response.status_code == 400
        assert "error" in response.json()
