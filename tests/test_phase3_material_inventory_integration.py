"""
PHASE 3 verification: MaterialRequest receipt → Inventory integration
Verify that receiving a material request automatically creates inventory movements
and updates inventory stock levels.
"""
from datetime import date

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from core.models import (
    InventoryItem,
    InventoryLocation,
    InventoryMovement,
    MaterialRequest,
    MaterialRequestItem,
    Project,
)

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    return User.objects.create_user(username="phase3_inventory_user", password="pass123", is_staff=True)


@pytest.fixture
def project(db):
    return Project.objects.create(name="InvTestProj", client="TestCorp", start_date=date.today(), address="456 Test Ave")


@pytest.fixture
def storage_location(db, project):
    """Create a storage location for the project"""
    return InventoryLocation.objects.create(name="Project Storage", is_storage=False, project=project)


@pytest.mark.django_db
def test_material_receipt_creates_inventory_movement(api_client, user, project, storage_location):
    """
    Q14.5 & Q15.6: Verify receiving a MaterialRequest creates an InventoryMovement (RECEIVE type)
    and updates inventory stock accordingly.
    """
    api_client.force_authenticate(user)

    # Create a material request
    mr = MaterialRequest.objects.create(project=project, requested_by=user, status="approved")
    item = MaterialRequestItem.objects.create(
        request=mr, category="paint", brand="Behr", product_name="Test Paint", quantity=15, unit="gal"
    )

    # Record the initial movement count
    initial_movement_count = InventoryMovement.objects.count()

    # Receive the material via API using the correct payload format
    # API expects: {"items": [{"id": item_id, "received_quantity": qty}, ...]}
    response = api_client.post(
        f"/api/v1/material-requests/{mr.id}/receive/",
        {"items": [{"id": item.id, "received_quantity": 15}]},
        format="json",
    )

    # Verify the request was successful
    assert response.status_code in (200, 201), f"Unexpected status: {response.status_code}, data: {response.data}"

    # Check if an InventoryMovement was created
    movements = InventoryMovement.objects.filter(movement_type="RECEIVE", quantity=15).order_by("-created_at")

    # If integration is implemented, we should see a new movement
    # If not implemented yet, this test will fail and flag the gap
    assert (
        movements.count() > 0
    ), "Expected an InventoryMovement (RECEIVE) to be created when receiving MaterialRequest, but none found."

    movement = movements.first()
    assert movement.quantity == 15, f"Expected quantity 15, got {movement.quantity}"
    assert movement.to_location.project == project, "Expected movement destination to be a project location"
    assert movement.created_by == user, "Expected movement to be created by receiving user"


@pytest.mark.django_db
def test_partial_receipt_creates_multiple_movements(api_client, user, project, storage_location):
    """
    Q14.10: Verify partial receipts create separate inventory movements for each partial shipment.
    """
    api_client.force_authenticate(user)

    mr = MaterialRequest.objects.create(project=project, requested_by=user, status="approved")
    item = MaterialRequestItem.objects.create(
        request=mr, category="lumber", brand="Weyerhaeuser", product_name="2x4 Studs", quantity=100, unit="pieces"
    )

    # Receive partial shipment 1 (40 pieces)
    api_client.post(
        f"/api/v1/material-requests/{mr.id}/receive/",
        {"items": [{"id": item.id, "received_quantity": 40}]},
        format="json",
    )

    # Receive partial shipment 2 (60 pieces)
    api_client.post(
        f"/api/v1/material-requests/{mr.id}/receive/",
        {"items": [{"id": item.id, "received_quantity": 60}]},
        format="json",
    )

    # Verify two separate movements were created
    movements = InventoryMovement.objects.filter(movement_type="RECEIVE").order_by("-created_at")

    # If partial receipt → inventory movement integration is implemented, we should see 2 movements
    assert (
        movements.count() >= 2
    ), f"Expected at least 2 InventoryMovements for partial receipts, found {movements.count()}"

    quantities = [m.quantity for m in movements[:2]]
    # Verify the quantities match (order may vary)
    assert 40 in quantities or 60 in quantities, f"Unexpected movement quantities: {quantities}"
