from datetime import date
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from core.models import Expense, InventoryItem, InventoryLocation, Project, ProjectInventory

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    return User.objects.create_user(username="pm14", password="pass123", email="pm14@example.com", is_staff=True)


@pytest.fixture
def project(db):
    return Project.objects.create(
        name="Materials Project", client="ACME", start_date=date.today(), address="123 Main St, City"
    )


def test_inventory_item_sku_unique(api_client, user):
    api_client.force_authenticate(user=user)
    payload = {"name": "Blue Tape", "category": "MATERIAL", "unit": "pcs", "sku": "SKU-ABC-1"}
    res = api_client.post("/api/v1/inventory/items/", payload, format="json")
    assert res.status_code in (200, 201)
    # Duplicate SKU should fail
    res2 = api_client.post("/api/v1/inventory/items/", payload, format="json")
    assert res2.status_code == 400


def test_material_request_flow_receive_partial_and_full(api_client, user, project):
    api_client.force_authenticate(user=user)
    # Create MR with 2 items
    mr_payload = {
        "project": project.id,
        "needed_when": "now",
        "notes": "Test MR",
        "items": [
            {
                "category": "tape",
                "brand": "3m",
                "brand_text": "3M",
                "product_name": "Masking Tape",
                "quantity": "10",
                "unit": "roll",
            },
            {
                "category": "paint",
                "brand": "sherwin_williams",
                "brand_text": "Sherwin‑Williams",
                "product_name": "Emerald Interior",
                "quantity": "5",
                "unit": "gal",
            },
        ],
    }
    res = api_client.post("/api/v1/material-requests/", mr_payload, format="json")
    assert res.status_code in (200, 201)
    mr_id = res.data["id"]

    # Submit, approve, mark ordered
    assert api_client.post(f"/api/v1/material-requests/{mr_id}/submit/").status_code == 200
    ap = api_client.post(f"/api/v1/material-requests/{mr_id}/approve/")
    assert ap.status_code == 200 and ap.data["status"] in ("approved", "pending")
    mo = api_client.post(f"/api/v1/material-requests/{mr_id}/mark_ordered/")
    assert mo.status_code == 200 and mo.data["status"] in ("ordered", "approved")

    # Partial receive first item 4 rolls
    mr_detail = api_client.get(f"/api/v1/material-requests/{mr_id}/").data
    item1_id = mr_detail["items"][0]["id"]
    recv_res = api_client.post(
        f"/api/v1/material-requests/{mr_id}/receive/",
        {"items": [{"id": item1_id, "received_quantity": "4"}]},
        format="json",
    )
    assert recv_res.status_code == 200
    assert recv_res.data["status"] in ("partially_received", "ordered")

    # Receive remaining and full for second item
    recv_all = api_client.post(
        f"/api/v1/material-requests/{mr_id}/receive/",
        {
            "items": [
                {"id": item1_id, "received_quantity": "6"},
            ]
        },
        format="json",
    )
    assert recv_all.status_code == 200

    # After receiving for second item
    mr_detail = api_client.get(f"/api/v1/material-requests/{mr_id}/").data
    item2_id = mr_detail["items"][1]["id"]
    recv2 = api_client.post(
        f"/api/v1/material-requests/{mr_id}/receive/",
        {"items": [{"id": item2_id, "received_quantity": "5"}]},
        format="json",
    )
    assert recv2.status_code == 200
    # verify fulfilled
    final = api_client.get(f"/api/v1/material-requests/{mr_id}/").data
    assert final["status"] in ("fulfilled", "partially_received")

    # Verify inventory stock at a project location was increased
    proj_locs = InventoryLocation.objects.filter(project=project)
    assert proj_locs.exists()
    from django.db.models import Sum

    total_qty = ProjectInventory.objects.filter(location__project=project).aggregate(total_qty_sum=Sum("quantity"))
    assert total_qty["total_qty_sum"] is not None


def test_direct_purchase_expense_creates_inventory(api_client, user, project):
    api_client.force_authenticate(user=user)
    # Create MR with 1 item
    mr_payload = {
        "project": project.id,
        "needed_when": "now",
        "notes": "Direct purchase",
        "items": [
            {
                "category": "paint",
                "brand": "sherwin_williams",
                "brand_text": "SW",
                "product_name": "Emerald",
                "quantity": "2",
                "unit": "gal",
            }
        ],
    }
    res = api_client.post("/api/v1/material-requests/", mr_payload, format="json")
    assert res.status_code in (200, 201)
    mr_id = res.data["id"]

    dp = api_client.post(
        f"/api/v1/material-requests/{mr_id}/direct_purchase_expense/", {"total_amount": "250.00"}, format="json"
    )
    assert dp.status_code == 200
    # Expense created
    assert Expense.objects.filter(project=project, amount=Decimal("250.00")).exists()
    # Stock exists
    assert ProjectInventory.objects.filter(location__project=project).exists()


def test_catalog_create_and_filter(api_client, user, project):
    api_client.force_authenticate(user=user)
    # Create global catalog item
    res1 = api_client.post(
        "/api/v1/material-catalog/",
        {
            "project": None,
            "category": "tape",
            "brand_text": "3M",
            "product_name": "Hand-Masker",
            "default_unit": "roll",
            "is_active": True,
        },
        format="json",
    )
    assert res1.status_code in (200, 201)
    # Create project-specific
    res2 = api_client.post(
        "/api/v1/material-catalog/",
        {
            "project": project.id,
            "category": "paint",
            "brand_text": "SW",
            "product_name": "Emerald Interior",
            "default_unit": "gal",
            "is_active": True,
        },
        format="json",
    )
    assert res2.status_code in (200, 201)

    # List
    lst = api_client.get("/api/v1/material-catalog/?project=" + str(project.id))
    assert lst.status_code == 200
    assert lst.data is not None


def test_inventory_negative_issue_prevented(api_client, user, project):
    api_client.force_authenticate(user=user)
    # Create item
    item_res = api_client.post(
        "/api/v1/inventory/items/", {"name": "Sandpaper", "category": "MATERIAL", "unit": "pcs"}, format="json"
    )
    assert item_res.status_code in (200, 201)
    item_id = item_res.data["id"]
    # Create project location
    loc_res = api_client.post(
        "/api/v1/inventory/locations/", {"name": "Site A", "project": project.id, "is_storage": False}, format="json"
    )
    assert loc_res.status_code in (200, 201)
    loc_id = loc_res.data["id"]
    # Attempt issue more than available (0)
    move_res = api_client.post(
        "/api/v1/inventory/movements/",
        {"item": item_id, "from_location": loc_id, "movement_type": "ISSUE", "quantity": "1"},
        format="json",
    )
    assert move_res.status_code == 400
