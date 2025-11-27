"""
MÓDULO 20: Floor Plans - Comprehensive Test Suite
Tests for pin versioning, migration, annotations, and client commenting.
"""

import base64
from datetime import date
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient

from core.models import ClientProjectAccess, FloorPlan, PlanPin, PlanPinAttachment, Project

User = get_user_model()

# Valid 1x1 PNG image
VALID_PNG_BASE64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def admin_user(db):
    return User.objects.create_user(
        username="admin_plans", password="pass123", email="admin@example.com", is_staff=True
    )


@pytest.fixture
def regular_user(db):
    return User.objects.create_user(
        username="client_plans", password="pass123", email="client@example.com", is_staff=False
    )


@pytest.fixture
def project(db):
    return Project.objects.create(
        name="Versioning Project", client="BuildCo", start_date=date.today(), address="789 Blueprint St"
    )


@pytest.fixture
def project_access(db, regular_user, project):
    """Grant regular user access to project"""
    return ClientProjectAccess.objects.create(user=regular_user, project=project, role="client", can_comment=True)


@pytest.fixture
def floor_plan(db, project, admin_user):
    """Create a floor plan with image"""
    image_bytes = base64.b64decode(VALID_PNG_BASE64)
    upload = SimpleUploadedFile("plan.png", image_bytes, content_type="image/png")

    return FloorPlan.objects.create(project=project, name="Ground Floor", level=0, image=upload, created_by=admin_user)


# ============================================================================
# CRUD Tests
# ============================================================================


@pytest.mark.django_db
def test_create_floor_plan(api_client, admin_user, project):
    """Test creating a new floor plan"""
    api_client.force_authenticate(user=admin_user)

    image_bytes = base64.b64decode(VALID_PNG_BASE64)
    upload = SimpleUploadedFile("new_plan.png", image_bytes, content_type="image/png")

    res = api_client.post(
        "/api/v1/floor-plans/",
        {"project": project.id, "name": "First Floor", "level": 1, "level_identifier": "Level 1", "image": upload},
        format="multipart",
    )

    assert res.status_code in (200, 201), f"Failed: {res.data}"
    assert res.data["name"] == "First Floor"
    assert res.data["level"] == 1
    assert res.data["version"] == 1
    assert res.data["is_current"] == True


@pytest.mark.django_db
def test_list_floor_plans(api_client, admin_user, project, floor_plan):
    """Test listing floor plans"""
    api_client.force_authenticate(user=admin_user)

    res = api_client.get(f"/api/v1/floor-plans/?project={project.id}")
    assert res.status_code == 200

    # No pagination for floor plans
    assert isinstance(res.data, list)
    assert len(res.data) >= 1
    assert res.data[0]["id"] == floor_plan.id


@pytest.mark.django_db
def test_get_floor_plan_with_pins(api_client, admin_user, floor_plan):
    """Test retrieving floor plan includes nested pins"""
    api_client.force_authenticate(user=admin_user)

    # Create a pin
    pin = PlanPin.objects.create(
        plan=floor_plan, x=Decimal("0.5"), y=Decimal("0.5"), title="Test Pin", pin_type="note", created_by=admin_user
    )

    res = api_client.get(f"/api/v1/floor-plans/{floor_plan.id}/")
    assert res.status_code == 200
    assert "pins" in res.data
    assert len(res.data["pins"]) == 1
    assert res.data["pins"][0]["title"] == "Test Pin"
    assert res.data["pin_count"] == 1


@pytest.mark.django_db
def test_update_floor_plan(api_client, admin_user, floor_plan):
    """Test updating floor plan metadata"""
    api_client.force_authenticate(user=admin_user)

    res = api_client.patch(
        f"/api/v1/floor-plans/{floor_plan.id}/",
        {"name": "Updated Ground Floor", "level_identifier": "Ground"},
        format="json",
    )

    assert res.status_code == 200
    assert res.data["name"] == "Updated Ground Floor"
    assert res.data["level_identifier"] == "Ground"


@pytest.mark.django_db
def test_delete_floor_plan(api_client, admin_user, floor_plan):
    """Test deleting a floor plan"""
    api_client.force_authenticate(user=admin_user)

    plan_id = floor_plan.id
    res = api_client.delete(f"/api/v1/floor-plans/{plan_id}/")
    assert res.status_code == 204

    # Verify deleted
    assert not FloorPlan.objects.filter(id=plan_id).exists()


# ============================================================================
# Versioning Tests
# ============================================================================


@pytest.mark.django_db
def test_create_new_version(api_client, admin_user, floor_plan):
    """Test creating a new version of a floor plan"""
    api_client.force_authenticate(user=admin_user)

    # Create some pins on original plan
    PlanPin.objects.create(
        plan=floor_plan,
        x=Decimal("0.3"),
        y=Decimal("0.4"),
        title="Original Pin",
        pin_type="note",
        created_by=admin_user,
    )

    # Create new version
    image_bytes = base64.b64decode(VALID_PNG_BASE64)
    upload = SimpleUploadedFile("plan_v2.png", image_bytes, content_type="image/png")

    res = api_client.post(f"/api/v1/floor-plans/{floor_plan.id}/create-version/", {"image": upload}, format="multipart")

    assert res.status_code == 201
    assert res.data["version"] == 2
    assert res.data["is_current"] is True

    # Verify old plan marked as not current
    floor_plan.refresh_from_db()
    assert floor_plan.is_current is False
    assert floor_plan.replaced_by_id == res.data["id"]

    # Verify pins marked as pending migration
    pin = PlanPin.objects.get(title="Original Pin")
    assert pin.status == "pending_migration"


@pytest.mark.django_db
def test_create_version_without_image_fails(api_client, admin_user, floor_plan):
    """Test creating version without image fails"""
    api_client.force_authenticate(user=admin_user)

    res = api_client.post(f"/api/v1/floor-plans/{floor_plan.id}/create-version/", {}, format="json")

    assert res.status_code == 400
    assert "image" in res.data["error"].lower()


@pytest.mark.django_db
def test_get_migratable_pins(api_client, admin_user, floor_plan):
    """Test getting list of pins pending migration"""
    api_client.force_authenticate(user=admin_user)

    # Create pins
    PlanPin.objects.create(
        plan=floor_plan, x=Decimal("0.2"), y=Decimal("0.3"), title="Pin 1", pin_type="note", created_by=admin_user
    )
    PlanPin.objects.create(
        plan=floor_plan, x=Decimal("0.5"), y=Decimal("0.6"), title="Pin 2", pin_type="alert", created_by=admin_user
    )

    # Create new version
    image_bytes = base64.b64decode(VALID_PNG_BASE64)
    upload = SimpleUploadedFile("v2.png", image_bytes, content_type="image/png")

    new_version_res = api_client.post(
        f"/api/v1/floor-plans/{floor_plan.id}/create-version/", {"image": upload}, format="multipart"
    )

    new_plan_id = new_version_res.data["id"]

    # Get migratable pins
    res = api_client.get(f"/api/v1/floor-plans/{new_plan_id}/migratable-pins/")

    assert res.status_code == 200
    assert res.data["count"] == 2
    assert len(res.data["pins"]) == 2


# ============================================================================
# Pin Migration Tests
# ============================================================================


@pytest.mark.django_db
def test_migrate_pins(api_client, admin_user, floor_plan):
    """Test migrating pins from old version to new"""
    api_client.force_authenticate(user=admin_user)

    # Create pins on original
    pin1 = PlanPin.objects.create(
        plan=floor_plan,
        x=Decimal("0.2"),
        y=Decimal("0.3"),
        title="Migrate Me 1",
        pin_type="touchup",
        created_by=admin_user,
    )
    pin2 = PlanPin.objects.create(
        plan=floor_plan,
        x=Decimal("0.7"),
        y=Decimal("0.8"),
        title="Migrate Me 2",
        pin_type="color",
        created_by=admin_user,
    )

    # Create new version
    image_bytes = base64.b64decode(VALID_PNG_BASE64)
    upload = SimpleUploadedFile("v2.png", image_bytes, content_type="image/png")

    new_version_res = api_client.post(
        f"/api/v1/floor-plans/{floor_plan.id}/create-version/", {"image": upload}, format="multipart"
    )

    new_plan_id = new_version_res.data["id"]

    # Migrate pins with new coordinates
    migrate_res = api_client.post(
        f"/api/v1/floor-plans/{new_plan_id}/migrate-pins/",
        {
            "pin_mappings": [
                {"old_pin_id": pin1.id, "new_x": 0.25, "new_y": 0.35},
                {"old_pin_id": pin2.id, "new_x": 0.75, "new_y": 0.85},
            ]
        },
        format="json",
    )

    assert migrate_res.status_code == 200
    assert migrate_res.data["migrated_count"] == 2
    assert len(migrate_res.data["pins"]) == 2

    # Verify old pins marked as migrated
    pin1.refresh_from_db()
    pin2.refresh_from_db()
    assert pin1.status == "migrated"
    assert pin2.status == "migrated"
    assert pin1.migrated_to is not None
    assert pin2.migrated_to is not None

    # Verify new pins created with correct coordinates
    new_pins = PlanPin.objects.filter(plan_id=new_plan_id, status="active").order_by("id")
    assert new_pins.count() == 2
    # First migrated pin (from pin1)
    migrated_pin1 = new_pins[0]
    assert str(migrated_pin1.x) == "0.2500"
    assert str(migrated_pin1.y) == "0.3500"
    assert migrated_pin1.title == "Migrate Me 1"
    # Second migrated pin (from pin2)
    migrated_pin2 = new_pins[1]
    assert str(migrated_pin2.x) == "0.7500"
    assert str(migrated_pin2.y) == "0.8500"
    assert migrated_pin2.title == "Migrate Me 2"


@pytest.mark.django_db
def test_migrate_pins_without_mappings_fails(api_client, admin_user, floor_plan):
    """Test migrating without pin_mappings fails"""
    api_client.force_authenticate(user=admin_user)

    res = api_client.post(f"/api/v1/floor-plans/{floor_plan.id}/migrate-pins/", {}, format="json")

    assert res.status_code == 400
    assert "pin_mappings" in res.data["error"].lower()


# ============================================================================
# Pin CRUD Tests
# ============================================================================


@pytest.mark.django_db
def test_create_pin(api_client, admin_user, floor_plan):
    """Test creating a pin on a floor plan"""
    api_client.force_authenticate(user=admin_user)

    res = api_client.post(
        "/api/v1/plan-pins/",
        {
            "plan": floor_plan.id,
            "x": "0.45",
            "y": "0.67",
            "title": "New Pin",
            "description": "Test pin description",
            "pin_type": "note",
        },
        format="json",
    )

    assert res.status_code in (200, 201)
    assert res.data["title"] == "New Pin"
    assert res.data["pin_type"] == "note"
    assert res.data["status"] == "active"


@pytest.mark.django_db
def test_update_pin(api_client, admin_user, floor_plan):
    """Test updating pin metadata"""
    api_client.force_authenticate(user=admin_user)

    pin = PlanPin.objects.create(
        plan=floor_plan, x=Decimal("0.5"), y=Decimal("0.5"), title="Original", pin_type="note", created_by=admin_user
    )

    res = api_client.patch(
        f"/api/v1/plan-pins/{pin.id}/", {"title": "Updated Pin", "description": "New description"}, format="json"
    )

    assert res.status_code == 200
    assert res.data["title"] == "Updated Pin"
    assert res.data["description"] == "New description"


@pytest.mark.django_db
def test_delete_pin(api_client, admin_user, floor_plan):
    """Test deleting a pin"""
    api_client.force_authenticate(user=admin_user)

    pin = PlanPin.objects.create(
        plan=floor_plan, x=Decimal("0.5"), y=Decimal("0.5"), title="To Delete", pin_type="note", created_by=admin_user
    )

    pin_id = pin.id
    res = api_client.delete(f"/api/v1/plan-pins/{pin_id}/")
    assert res.status_code == 204

    # Verify deleted
    assert not PlanPin.objects.filter(id=pin_id).exists()


# ============================================================================
# Client Commenting Tests
# ============================================================================


@pytest.mark.django_db
def test_add_comment_to_pin(api_client, admin_user, floor_plan):
    """Test adding a client comment to a pin"""
    api_client.force_authenticate(user=admin_user)

    pin = PlanPin.objects.create(
        plan=floor_plan,
        x=Decimal("0.5"),
        y=Decimal("0.5"),
        title="Commented Pin",
        pin_type="note",
        created_by=admin_user,
    )

    res = api_client.post(f"/api/v1/plan-pins/{pin.id}/comment/", {"comment": "This needs attention"}, format="json")

    assert res.status_code == 200
    assert "client_comments" in res.data
    assert len(res.data["client_comments"]) == 1
    assert res.data["client_comments"][0]["comment"] == "This needs attention"
    assert res.data["client_comments"][0]["user"] == admin_user.username


@pytest.mark.django_db
def test_add_multiple_comments(api_client, admin_user, regular_user, floor_plan, project_access):
    """Test adding multiple comments from different users"""
    api_client.force_authenticate(user=admin_user)

    pin = PlanPin.objects.create(
        plan=floor_plan,
        x=Decimal("0.5"),
        y=Decimal("0.5"),
        title="Multi Comment Pin",
        pin_type="alert",
        created_by=admin_user,
    )

    # Admin comment
    api_client.post(f"/api/v1/plan-pins/{pin.id}/comment/", {"comment": "First comment"}, format="json")

    # Client comment
    api_client.force_authenticate(user=regular_user)
    res = api_client.post(f"/api/v1/plan-pins/{pin.id}/comment/", {"comment": "Second comment"}, format="json")

    assert res.status_code == 200
    assert len(res.data["client_comments"]) == 2
    assert res.data["client_comments"][1]["user"] == regular_user.username


@pytest.mark.django_db
def test_comment_without_text_fails(api_client, admin_user, floor_plan):
    """Test adding empty comment fails"""
    api_client.force_authenticate(user=admin_user)

    pin = PlanPin.objects.create(
        plan=floor_plan, x=Decimal("0.5"), y=Decimal("0.5"), title="Pin", pin_type="note", created_by=admin_user
    )

    res = api_client.post(f"/api/v1/plan-pins/{pin.id}/comment/", {"comment": ""}, format="json")

    assert res.status_code == 400


# ============================================================================
# Annotations Tests
# ============================================================================


@pytest.mark.django_db
def test_update_annotations(api_client, admin_user, floor_plan):
    """Test updating canvas annotations on pin attachment"""
    api_client.force_authenticate(user=admin_user)

    pin = PlanPin.objects.create(
        plan=floor_plan,
        x=Decimal("0.5"),
        y=Decimal("0.5"),
        title="Annotated Pin",
        pin_type="damage",
        created_by=admin_user,
    )

    # Create attachment
    image_bytes = base64.b64decode(VALID_PNG_BASE64)
    upload = SimpleUploadedFile("attachment.png", image_bytes, content_type="image/png")

    attachment = PlanPinAttachment.objects.create(pin=pin, image=upload)

    # Update annotations
    res = api_client.post(
        f"/api/v1/plan-pins/{pin.id}/update-annotations/",
        {
            "attachment_id": attachment.id,
            "annotations": {
                "shapes": [{"type": "circle", "x": 100, "y": 200, "radius": 50}],
                "text": [{"content": "Fix this", "x": 150, "y": 250}],
            },
        },
        format="json",
    )

    assert res.status_code == 200
    assert res.data["success"] is True

    # Verify annotations saved
    attachment.refresh_from_db()
    assert "shapes" in attachment.annotations
    assert len(attachment.annotations["shapes"]) == 1


@pytest.mark.django_db
def test_update_annotations_without_attachment_id_fails(api_client, admin_user, floor_plan):
    """Test updating annotations without attachment_id fails"""
    api_client.force_authenticate(user=admin_user)

    pin = PlanPin.objects.create(
        plan=floor_plan, x=Decimal("0.5"), y=Decimal("0.5"), title="Pin", pin_type="note", created_by=admin_user
    )

    res = api_client.post(f"/api/v1/plan-pins/{pin.id}/update-annotations/", {"annotations": {}}, format="json")

    assert res.status_code == 400


# ============================================================================
# Filtering Tests
# ============================================================================


@pytest.mark.django_db
def test_filter_pins_by_type(api_client, admin_user, floor_plan):
    """Test filtering pins by pin_type"""
    api_client.force_authenticate(user=admin_user)

    # Create pins of different types
    PlanPin.objects.create(plan=floor_plan, x=Decimal("0.1"), y=Decimal("0.1"), pin_type="note", created_by=admin_user)
    PlanPin.objects.create(
        plan=floor_plan, x=Decimal("0.2"), y=Decimal("0.2"), pin_type="touchup", created_by=admin_user
    )
    PlanPin.objects.create(
        plan=floor_plan, x=Decimal("0.3"), y=Decimal("0.3"), pin_type="damage", created_by=admin_user
    )

    # Filter by touchup
    res = api_client.get(f"/api/v1/plan-pins/?plan={floor_plan.id}&pin_type=touchup")
    assert res.status_code == 200
    assert isinstance(res.data, list)
    assert len(res.data) == 1
    assert res.data[0]["pin_type"] == "touchup"


@pytest.mark.django_db
def test_filter_pins_by_status(api_client, admin_user, floor_plan):
    """Test filtering pins by migration status"""
    api_client.force_authenticate(user=admin_user)

    # Create active and archived pins
    PlanPin.objects.create(plan=floor_plan, x=Decimal("0.1"), y=Decimal("0.1"), status="active", created_by=admin_user)
    PlanPin.objects.create(
        plan=floor_plan, x=Decimal("0.2"), y=Decimal("0.2"), status="archived", created_by=admin_user
    )

    # Filter by active
    res = api_client.get(f"/api/v1/plan-pins/?plan={floor_plan.id}&status=active")
    assert res.status_code == 200
    assert len(res.data) == 1
    assert res.data[0]["status"] == "active"


# ============================================================================
# Access Control Tests
# ============================================================================


@pytest.mark.django_db
def test_non_staff_sees_only_accessible_plans(api_client, regular_user, project, project_access, floor_plan):
    """Test non-staff users only see plans from accessible projects"""
    api_client.force_authenticate(user=regular_user)

    # Create another project without access
    other_project = Project.objects.create(name="Other", client="Other", start_date=date.today())

    image_bytes = base64.b64decode(VALID_PNG_BASE64)
    FloorPlan.objects.create(
        project=other_project,
        name="Restricted Plan",
        level=0,
        image=SimpleUploadedFile("r.png", image_bytes, content_type="image/png"),
    )

    # Regular user should only see accessible project plans
    res = api_client.get("/api/v1/floor-plans/")
    assert res.status_code == 200
    assert len(res.data) == 1
    assert res.data[0]["id"] == floor_plan.id


@pytest.mark.django_db
def test_non_staff_sees_only_accessible_pins(api_client, regular_user, project, project_access, floor_plan):
    """Test non-staff users only see pins from accessible projects"""
    api_client.force_authenticate(user=regular_user)

    # Create another project without access
    other_project = Project.objects.create(name="Other", client="Other", start_date=date.today())

    image_bytes = base64.b64decode(VALID_PNG_BASE64)
    other_plan = FloorPlan.objects.create(
        project=other_project,
        name="Other Plan",
        level=0,
        image=SimpleUploadedFile("o.png", image_bytes, content_type="image/png"),
    )

    # Create pins in both projects
    accessible_pin = PlanPin.objects.create(plan=floor_plan, x=Decimal("0.5"), y=Decimal("0.5"), title="Accessible")

    PlanPin.objects.create(plan=other_plan, x=Decimal("0.5"), y=Decimal("0.5"), title="Restricted")

    # Regular user should only see accessible pin
    res = api_client.get("/api/v1/plan-pins/")
    assert res.status_code == 200
    assert len(res.data) == 1
    assert res.data[0]["id"] == accessible_pin.id
