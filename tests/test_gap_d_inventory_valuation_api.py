"""
Tests for Gap D: Inventory Valuation Methods API

Tests for:
- Inventory valuation report endpoint
- COGS calculation endpoint  
- Item-level valuation report
- FIFO/LIFO/AVG cost calculations via API
"""

import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient

from core.models import (
    InventoryItem,
    InventoryLocation,
    InventoryMovement,
    ProjectInventory,
    Project
)

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user():
    return User.objects.create_user(username="testuser", password="testpass123", is_staff=True)


@pytest.fixture
def project():
    from django.utils import timezone
    return Project.objects.create(
        name="Test Project",
        client="Test Client",
        start_date=timezone.now().date(),
        budget_total=Decimal("10000.00")
    )


@pytest.fixture
def warehouse():
    return InventoryLocation.objects.create(name="Main Warehouse", is_storage=True)


@pytest.fixture
def setup_inventory_data(user, warehouse, project):
    """Setup inventory data with multiple items and purchase history."""
    # Create items with different valuation methods
    fifo_item = InventoryItem.objects.create(
        name="Paint - White (FIFO)",
        sku="PAINT-WHITE-FIFO",
        category="PINTURA",
        valuation_method="FIFO",
        average_cost=Decimal("25.00")
    )
    
    lifo_item = InventoryItem.objects.create(
        name="Paint - Blue (LIFO)",
        sku="PAINT-BLUE-LIFO",
        category="PINTURA",
        valuation_method="LIFO",
        average_cost=Decimal("30.00")
    )
    
    avg_item = InventoryItem.objects.create(
        name="Brush Set (AVG)",
        sku="BRUSH-SET-AVG",
        category="HERRAMIENTA",
        valuation_method="AVG",
        average_cost=Decimal("15.00")
    )
    
    # Create purchase movements with different costs
    # FIFO item: 3 purchases
    mov1 = InventoryMovement.objects.create(
        item=fifo_item,
        to_location=warehouse,
        movement_type="RECEIVE",
        quantity=Decimal("10"),
        unit_cost=Decimal("20.00"),
        reason="Initial purchase",
        created_by=user,
        applied=True
    )
    mov1.created_at = timezone.now() - timedelta(days=30)
    mov1.save()
    
    mov2 = InventoryMovement.objects.create(
        item=fifo_item,
        to_location=warehouse,
        movement_type="RECEIVE",
        quantity=Decimal("10"),
        unit_cost=Decimal("25.00"),
        reason="Second purchase",
        created_by=user,
        applied=True
    )
    mov2.created_at = timezone.now() - timedelta(days=15)
    mov2.save()
    
    mov3 = InventoryMovement.objects.create(
        item=fifo_item,
        to_location=warehouse,
        movement_type="RECEIVE",
        quantity=Decimal("10"),
        unit_cost=Decimal("30.00"),
        reason="Recent purchase",
        created_by=user,
        applied=True
    )
    
    # LIFO item: 2 purchases
    InventoryMovement.objects.create(
        item=lifo_item,
        to_location=warehouse,
        movement_type="RECEIVE",
        quantity=Decimal("20"),
        unit_cost=Decimal("28.00"),
        reason="Bulk purchase",
        created_by=user,
        applied=True
    )
    
    InventoryMovement.objects.create(
        item=lifo_item,
        to_location=warehouse,
        movement_type="RECEIVE",
        quantity=Decimal("15"),
        unit_cost=Decimal("32.00"),
        reason="Recent purchase",
        created_by=user,
        applied=True
    )
    
    # AVG item: 1 purchase
    InventoryMovement.objects.create(
        item=avg_item,
        to_location=warehouse,
        movement_type="RECEIVE",
        quantity=Decimal("50"),
        unit_cost=Decimal("15.00"),
        reason="Bulk order",
        created_by=user,
        applied=True
    )
    
    # Create stock records
    ProjectInventory.objects.create(item=fifo_item, location=warehouse, quantity=Decimal("30"))
    ProjectInventory.objects.create(item=lifo_item, location=warehouse, quantity=Decimal("35"))
    ProjectInventory.objects.create(item=avg_item, location=warehouse, quantity=Decimal("50"))
    
    return {
        "fifo_item": fifo_item,
        "lifo_item": lifo_item,
        "avg_item": avg_item,
        "warehouse": warehouse
    }


# =============================================================================
# Test: Inventory Valuation Report
# =============================================================================


@pytest.mark.django_db
def test_inventory_valuation_report(api_client, user, setup_inventory_data):
    """Test comprehensive inventory valuation report endpoint."""
    api_client.force_authenticate(user=user)
    
    response = api_client.get("/api/v1/inventory/valuation-report/")
    
    assert response.status_code == 200
    data = response.json()
    
    # Check report structure
    assert "report_date" in data
    assert "summary" in data
    assert "by_category" in data
    assert "aging_analysis" in data
    assert "items" in data
    
    # Check summary
    assert data["summary"]["total_items"] == 3
    assert Decimal(data["summary"]["total_value"]) > 0
    
    # Check category breakdown
    assert "Pintura" in data["by_category"]
    # Note: "HERRAMIENTA" displays as "Herramientas" (plural)
    assert "Herramientas" in data["by_category"] or "Herramienta" in data["by_category"]
    
    # Check aging analysis
    assert "0-30_days" in data["aging_analysis"]
    assert "31-60_days" in data["aging_analysis"]
    
    # Check items detail
    assert len(data["items"]) == 3
    
    # Verify each item has required fields
    for item in data["items"]:
        assert "id" in item
        assert "name" in item
        assert "sku" in item
        assert "category" in item
        assert "valuation_method" in item
        assert "quantity" in item
        assert "total_value" in item


@pytest.mark.django_db
def test_inventory_valuation_report_unauthorized(api_client):
    """Test valuation report requires authentication."""
    response = api_client.get("/api/v1/inventory/valuation-report/")
    assert response.status_code == 401


# =============================================================================
# Test: Item Valuation Report
# =============================================================================


@pytest.mark.django_db
def test_item_valuation_report_fifo(api_client, user, setup_inventory_data):
    """Test item-level valuation report for FIFO item."""
    api_client.force_authenticate(user=user)
    
    fifo_item = setup_inventory_data["fifo_item"]
    
    response = api_client.get(f"/api/v1/inventory/items/{fifo_item.id}/valuation_report/")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["item_id"] == fifo_item.id
    assert data["item_name"] == fifo_item.name
    assert data["valuation_method"] == "FIFO"
    assert Decimal(data["total_quantity"]) == Decimal("30")
    
    # Check cost breakdown
    assert "cost_breakdown" in data
    assert "fifo" in data["cost_breakdown"]
    assert "lifo" in data["cost_breakdown"]
    assert "avg" in data["cost_breakdown"]
    
    # FIFO should use oldest costs first
    # 10@20 + 10@25 + 10@30 = 200 + 250 + 300 = 750
    assert Decimal(data["cost_breakdown"]["fifo"]) == Decimal("750.00")
    
    # Check recent purchases
    assert "recent_purchases" in data
    assert len(data["recent_purchases"]) > 0


@pytest.mark.django_db
def test_item_valuation_report_lifo(api_client, user, setup_inventory_data):
    """Test item-level valuation report for LIFO item."""
    api_client.force_authenticate(user=user)
    
    lifo_item = setup_inventory_data["lifo_item"]
    
    response = api_client.get(f"/api/v1/inventory/items/{lifo_item.id}/valuation_report/")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["valuation_method"] == "LIFO"
    assert Decimal(data["total_quantity"]) == Decimal("35")
    
    # LIFO should use newest costs first
    # 15@32 + 20@28 = 480 + 560 = 1040
    assert Decimal(data["cost_breakdown"]["lifo"]) == Decimal("1040.00")


@pytest.mark.django_db
def test_item_valuation_report_avg(api_client, user, setup_inventory_data):
    """Test item-level valuation report for AVG item."""
    api_client.force_authenticate(user=user)
    
    avg_item = setup_inventory_data["avg_item"]
    
    response = api_client.get(f"/api/v1/inventory/items/{avg_item.id}/valuation_report/")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["valuation_method"] == "AVG"
    assert Decimal(data["total_quantity"]) == Decimal("50")
    
    # AVG: 50 * 15.00 = 750.00
    assert Decimal(data["cost_breakdown"]["avg"]) == Decimal("750.00")
    assert Decimal(data["average_cost"]) == Decimal("15.00")


# =============================================================================
# Test: COGS Calculation
# =============================================================================


@pytest.mark.django_db
def test_calculate_cogs_fifo(api_client, user, setup_inventory_data):
    """Test COGS calculation for FIFO item."""
    api_client.force_authenticate(user=user)
    
    fifo_item = setup_inventory_data["fifo_item"]
    
    response = api_client.post(
        f"/api/v1/inventory/items/{fifo_item.id}/calculate_cogs/",
        data={"quantity": "15"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["item_id"] == fifo_item.id
    assert Decimal(data["quantity"]) == Decimal("15")
    assert data["valuation_method"] == "FIFO"
    
    # FIFO: first 10@20 + 5@25 = 200 + 125 = 325
    assert Decimal(data["total_cogs"]) == Decimal("325.00")
    
    # Unit COGS: 325 / 15 = 21.67 (rounded)
    unit_cogs = Decimal(data["unit_cogs"])
    assert unit_cogs > Decimal("21.60") and unit_cogs < Decimal("21.70")


@pytest.mark.django_db
def test_calculate_cogs_lifo(api_client, user, setup_inventory_data):
    """Test COGS calculation for LIFO item."""
    api_client.force_authenticate(user=user)
    
    lifo_item = setup_inventory_data["lifo_item"]
    
    response = api_client.post(
        f"/api/v1/inventory/items/{lifo_item.id}/calculate_cogs/",
        data={"quantity": "20"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["valuation_method"] == "LIFO"
    
    # LIFO: first 15@32 + 5@28 = 480 + 140 = 620
    assert Decimal(data["total_cogs"]) == Decimal("620.00")
    
    # Unit COGS: 620 / 20 = 31.00
    assert Decimal(data["unit_cogs"]) == Decimal("31.00")


@pytest.mark.django_db
def test_calculate_cogs_avg(api_client, user, setup_inventory_data):
    """Test COGS calculation for AVG item."""
    api_client.force_authenticate(user=user)
    
    avg_item = setup_inventory_data["avg_item"]
    
    response = api_client.post(
        f"/api/v1/inventory/items/{avg_item.id}/calculate_cogs/",
        data={"quantity": "25"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["valuation_method"] == "AVG"
    
    # AVG: 25 * 15.00 = 375.00
    assert Decimal(data["total_cogs"]) == Decimal("375.00")
    assert Decimal(data["unit_cogs"]) == Decimal("15.00")


@pytest.mark.django_db
def test_calculate_cogs_invalid_quantity(api_client, user, setup_inventory_data):
    """Test COGS calculation with invalid quantity."""
    api_client.force_authenticate(user=user)
    
    item = setup_inventory_data["fifo_item"]
    
    # Test zero quantity
    response = api_client.post(
        f"/api/v1/inventory/items/{item.id}/calculate_cogs/",
        data={"quantity": "0"}
    )
    assert response.status_code == 400
    assert "must be greater than zero" in response.json()["error"]
    
    # Test negative quantity
    response = api_client.post(
        f"/api/v1/inventory/items/{item.id}/calculate_cogs/",
        data={"quantity": "-10"}
    )
    assert response.status_code == 400
    
    # Test invalid format
    response = api_client.post(
        f"/api/v1/inventory/items/{item.id}/calculate_cogs/",
        data={"quantity": "invalid"}
    )
    assert response.status_code == 400
    assert "Invalid quantity format" in response.json()["error"]


@pytest.mark.django_db
def test_calculate_cogs_unauthorized(api_client, setup_inventory_data):
    """Test COGS calculation requires authentication."""
    item = setup_inventory_data["fifo_item"]
    
    response = api_client.post(
        f"/api/v1/inventory/items/{item.id}/calculate_cogs/",
        data={"quantity": "10"}
    )
    assert response.status_code == 401


# =============================================================================
# Test: Edge Cases
# =============================================================================


@pytest.mark.django_db
def test_valuation_report_no_inventory(api_client, user):
    """Test valuation report with no inventory items."""
    api_client.force_authenticate(user=user)
    
    response = api_client.get("/api/v1/inventory/valuation-report/")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["summary"]["total_items"] == 0
    assert data["summary"]["total_value"] == "0"
    assert len(data["items"]) == 0


@pytest.mark.django_db
def test_item_valuation_no_purchases(api_client, user, warehouse):
    """Test item valuation report with no purchase history."""
    api_client.force_authenticate(user=user)
    
    # Create item with no purchases
    item = InventoryItem.objects.create(
        name="No Purchases Item",
        sku="NO-PURCHASE",
        category="MATERIAL",
        valuation_method="FIFO",
        average_cost=Decimal("10.00")
    )
    
    ProjectInventory.objects.create(
        item=item,
        location=warehouse,
        quantity=Decimal("5")
    )
    
    response = api_client.get(f"/api/v1/inventory/items/{item.id}/valuation_report/")
    
    assert response.status_code == 200
    data = response.json()
    
    # Should use average cost
    assert Decimal(data["current_value"]) == Decimal("50.00")  # 5 * 10
    assert len(data["recent_purchases"]) == 0
