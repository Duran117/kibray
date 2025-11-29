import pytest
from decimal import Decimal
from django.contrib.auth.models import User
from rest_framework.test import APIClient

from core.models import (
    Project,
    InventoryLocation,
    InventoryItem,
    ProjectInventory,
    MaterialRequest,
    ProjectManagerAssignment,
)

pytestmark = pytest.mark.django_db


def make_user(username="worker", is_staff=False):
    return User.objects.create_user(username=username, password="pass", is_staff=is_staff)


def test_report_usage_success():
    user = make_user()
    project = Project.objects.create(name="Proj A", start_date="2025-01-01")
    ProjectManagerAssignment.objects.create(project=project, pm=make_user("pm", is_staff=True))
    location = InventoryLocation.objects.create(name="Site", project=project)
    item = InventoryItem.objects.create(name="Masking Tape", category="MATERIAL", unit="unit")
    ProjectInventory.objects.create(item=item, location=location, quantity=Decimal("10"))

    client = APIClient()
    client.force_authenticate(user)
    resp = client.post("/api/v1/field-materials/report-usage/", {
        "item_id": item.id,
        "project_id": project.id,
        "quantity": "3"
    }, format='json')
    assert resp.status_code == 201, resp.content
    data = resp.json()
    assert data["success"] is True
    assert str(data["consumed_quantity"]) in ["3", "3.00"]

    # Remaining quantity should be 7
    stock = ProjectInventory.objects.get(item=item, location=location)
    assert stock.quantity == Decimal("7")


def test_report_usage_insufficient_stock():
    user = make_user("worker2")
    project = Project.objects.create(name="Proj B", start_date="2025-01-01")
    location = InventoryLocation.objects.create(name="Site", project=project)
    item = InventoryItem.objects.create(name="Brush", category="MATERIAL", unit="unit")
    ProjectInventory.objects.create(item=item, location=location, quantity=Decimal("2"))

    client = APIClient()
    client.force_authenticate(user)
    resp = client.post("/api/v1/field-materials/report-usage/", {
        "item_id": item.id,
        "project_id": project.id,
        "quantity": "5"
    }, format='json')
    assert resp.status_code == 400
    data = resp.json()
    assert data["success"] is False
    assert "insuficiente" in data.get("error", "") or "Insuficiente" in data.get("error", "")


def test_quick_request_creates_material_request():
    user = make_user("worker3")
    project = Project.objects.create(name="Proj C", start_date="2025-01-01")

    client = APIClient()
    client.force_authenticate(user)
    resp = client.post("/api/v1/field-materials/quick-request/", {
        "project_id": project.id,
        "item_name": "Pintura Blanca",
        "quantity": "4",
        "urgency": True,
        "notes": "Necesario para sala"
    }, format='json')
    assert resp.status_code == 201, resp.content
    data = resp.json()
    assert data["success"] is True
    mr = MaterialRequest.objects.get(id=data["id"])  # QuickMaterialRequestSerializer returns id
    assert mr.status == "pending"
    assert mr.needed_when == "now"


def test_project_stock_listing():
    user = make_user("worker4")
    project = Project.objects.create(name="Proj D", start_date="2025-01-01")
    location = InventoryLocation.objects.create(name="Site", project=project)
    item = InventoryItem.objects.create(name="Gloves", category="MATERIAL", unit="unit")
    ProjectInventory.objects.create(item=item, location=location, quantity=Decimal("5"))

    client = APIClient()
    client.force_authenticate(user)
    resp = client.get(f"/api/v1/field-materials/project-stock/?project_id={project.id}")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert any(row["item_name"] == "Gloves" for row in data)
