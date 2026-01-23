"""
Tests for MÓDULO 21: Damage Reports Workflow (FASE 6)
Comprehensive testing of damage report lifecycle, assignment, and change order conversion.
"""

import base64
from datetime import date
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient

from core.models import (
    ChangeOrder,
    ClientProjectAccess,
    DamagePhoto,
    DamageReport,
    FloorPlan,
    Notification,
    PlanPin,
    Project,
    Task,
)

User = get_user_model()

# 1x1 PNG base64 for testing
VALID_PNG_BASE64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def admin_user(db):
    return User.objects.create_user(username="admin", password="pass", is_staff=True, is_superuser=True)


@pytest.fixture
def regular_user(db):
    return User.objects.create_user(username="user", password="pass")


@pytest.fixture
def assignee_user(db):
    return User.objects.create_user(username="assignee", password="pass")


@pytest.fixture
def project(db):
    return Project.objects.create(
        name="Damage Test Project", client="TestCo", start_date=date.today(), address="123 Damage St"
    )


@pytest.fixture
def floor_plan(db, project, admin_user):
    """Create a floor plan for pin-linked damages"""
    image_bytes = base64.b64decode(VALID_PNG_BASE64)
    upload = SimpleUploadedFile("plan.png", image_bytes, content_type="image/png")

    return FloorPlan.objects.create(project=project, name="Floor 1", level=1, image=upload, created_by=admin_user)


@pytest.fixture
def damage_report(db, project, admin_user):
    """Create a basic damage report"""
    return DamageReport.objects.create(
        project=project,
        title="Water Damage in Bathroom",
        description="Leak from ceiling",
        category="plumbing",
        severity="high",
        status="open",
        estimated_cost=Decimal("2500.00"),
        reported_by=admin_user,
        location_detail="Master Bath - Ceiling",
    )


# ============================================================================
# CRUD Tests
# ============================================================================


@pytest.mark.django_db
def test_create_damage_report(api_client, admin_user, project):
    """Test creating a new damage report"""
    api_client.force_authenticate(user=admin_user)

    res = api_client.post(
        "/api/v1/damage-reports/",
        {
            "project": project.id,
            "title": "Cracked Tile",
            "description": "Floor tile cracked in kitchen",
            "category": "cosmetic",
            "severity": "low",
            "location_detail": "Kitchen - Near Sink",
        },
        format="json",
    )

    assert res.status_code == 201, f"Failed: {res.data}"
    assert res.data["title"] == "Cracked Tile"
    assert res.data["category"] == "cosmetic"
    assert res.data["severity"] == "low"
    assert res.data["status"] == "open"  # Default status
    assert res.data["reported_by_name"] is not None

    # Verify auto-task was created
    assert res.data["auto_task_id"] is not None
    task = Task.objects.get(id=res.data["auto_task_id"])
    assert "Repair: Cracked Tile" in task.title


@pytest.mark.django_db
def test_list_damage_reports(api_client, admin_user, damage_report):
    """Test listing damage reports"""
    api_client.force_authenticate(user=admin_user)

    res = api_client.get("/api/v1/damage-reports/")

    assert res.status_code == 200
    assert len(res.data) >= 1
    assert res.data[0]["title"] == "Water Damage in Bathroom"


@pytest.mark.django_db
def test_get_single_damage_report(api_client, admin_user, damage_report):
    """Test retrieving single damage report with photos"""
    api_client.force_authenticate(user=admin_user)

    res = api_client.get(f"/api/v1/damage-reports/{damage_report.id}/")

    assert res.status_code == 200
    assert res.data["id"] == damage_report.id
    assert res.data["title"] == "Water Damage in Bathroom"
    assert "photos" in res.data
    assert res.data["photo_count"] == 0


@pytest.mark.django_db
def test_update_damage_report(api_client, admin_user, damage_report):
    """Test updating damage report"""
    api_client.force_authenticate(user=admin_user)

    res = api_client.patch(
        f"/api/v1/damage-reports/{damage_report.id}/",
        {"description": "Updated: Severe leak from ceiling", "root_cause": "Pipe burst"},
        format="json",
    )

    assert res.status_code == 200
    assert "Updated:" in res.data["description"]
    assert res.data["root_cause"] == "Pipe burst"


@pytest.mark.django_db
def test_delete_damage_report(api_client, admin_user, damage_report):
    """Test deleting damage report"""
    api_client.force_authenticate(user=admin_user)

    res = api_client.delete(f"/api/v1/damage-reports/{damage_report.id}/")

    assert res.status_code == 204
    assert not DamageReport.objects.filter(id=damage_report.id).exists()


# ============================================================================
# Photo Upload Tests
# ============================================================================


@pytest.mark.django_db
def test_add_photo_to_damage(api_client, admin_user, damage_report):
    """Test uploading photo to damage report"""
    api_client.force_authenticate(user=admin_user)

    image_bytes = base64.b64decode(VALID_PNG_BASE64)
    upload = SimpleUploadedFile("damage.png", image_bytes, content_type="image/png")

    res = api_client.post(
        f"/api/v1/damage-reports/{damage_report.id}/add-photo/",
        {"image": upload, "notes": "Ceiling water stain"},
        format="multipart",
    )

    assert res.status_code == 201
    assert "image" in res.data
    assert res.data["notes"] == "Ceiling water stain"

    # Verify photo was saved
    damage_report.refresh_from_db()
    assert damage_report.photos.count() == 1


@pytest.mark.django_db
def test_add_photo_without_image_fails(api_client, admin_user, damage_report):
    """Test photo upload requires image file"""
    api_client.force_authenticate(user=admin_user)

    res = api_client.post(
        f"/api/v1/damage-reports/{damage_report.id}/add-photo/", {"notes": "No image provided"}, format="multipart"
    )

    assert res.status_code == 400
    assert "image" in res.data["detail"].lower()


# ============================================================================
# Workflow Tests: Assignment
# ============================================================================


@pytest.mark.django_db
def test_assign_damage_to_user(api_client, admin_user, assignee_user, damage_report):
    """Test assigning damage report to a user"""
    api_client.force_authenticate(user=admin_user)

    res = api_client.post(
        f"/api/v1/damage-reports/{damage_report.id}/assign/", {"assigned_to": assignee_user.id}, format="json"
    )

    assert res.status_code == 200
    assert res.data["assigned_to"] == assignee_user.id
    assert res.data["assigned_to_name"] == assignee_user.get_full_name()

    # Verify notification was created
    notification = Notification.objects.filter(user=assignee_user, notification_type="damage_assigned").first()
    assert notification is not None
    assert "Damage Assigned" in notification.title


@pytest.mark.django_db
def test_assign_without_user_id_fails(api_client, admin_user, damage_report):
    """Test assignment requires user ID"""
    api_client.force_authenticate(user=admin_user)

    res = api_client.post(f"/api/v1/damage-reports/{damage_report.id}/assign/", {}, format="json")

    assert res.status_code == 400
    assert "assigned_to" in res.data["error"].lower()


@pytest.mark.django_db
def test_assign_to_nonexistent_user_fails(api_client, admin_user, damage_report):
    """Test assignment to non-existent user fails"""
    api_client.force_authenticate(user=admin_user)

    res = api_client.post(f"/api/v1/damage-reports/{damage_report.id}/assign/", {"assigned_to": 99999}, format="json")

    assert res.status_code == 404
    assert "not found" in res.data["error"].lower()


# ============================================================================
# Workflow Tests: Assessment
# ============================================================================


@pytest.mark.django_db
def test_assess_damage(api_client, admin_user, damage_report):
    """Test assessing damage (update severity and cost)"""
    api_client.force_authenticate(user=admin_user)

    res = api_client.post(
        f"/api/v1/damage-reports/{damage_report.id}/assess/",
        {"severity": "critical", "estimated_cost": 5000.00},
        format="json",
    )

    assert res.status_code == 200
    assert res.data["severity"] == "critical"
    assert Decimal(res.data["estimated_cost"]) == Decimal("5000.00")

    # Verify auto-task priority updated
    damage_report.refresh_from_db()
    assert damage_report.auto_task.priority == "high"


@pytest.mark.django_db
def test_assess_with_invalid_cost_fails(api_client, admin_user, damage_report):
    """Test assessment with invalid cost value"""
    api_client.force_authenticate(user=admin_user)

    res = api_client.post(
        f"/api/v1/damage-reports/{damage_report.id}/assess/", {"estimated_cost": "not-a-number"}, format="json"
    )

    assert res.status_code == 400
    assert "cost" in res.data["error"].lower()


# ============================================================================
# Workflow Tests: Approval
# ============================================================================


@pytest.mark.django_db
def test_approve_damage_as_staff(api_client, admin_user, assignee_user, damage_report):
    """Test approving damage (staff only)"""
    api_client.force_authenticate(user=admin_user)

    # Assign first so approve can auto-start
    damage_report.assigned_to = assignee_user
    damage_report.save()

    res = api_client.post(f"/api/v1/damage-reports/{damage_report.id}/approve/", {}, format="json")

    assert res.status_code == 200
    assert res.data["status"] == "in_progress"
    assert res.data["in_progress_at"] is not None


@pytest.mark.django_db
def test_approve_as_non_staff_fails(api_client, regular_user, damage_report):
    """Test non-staff cannot approve damages"""
    api_client.force_authenticate(user=regular_user)

    res = api_client.post(f"/api/v1/damage-reports/{damage_report.id}/approve/", {}, format="json")

    assert res.status_code == 403
    assert "staff" in res.data["error"].lower()


@pytest.mark.django_db
def test_approve_resolved_damage_fails(api_client, admin_user, damage_report):
    """Test cannot approve already resolved damage"""
    api_client.force_authenticate(user=admin_user)

    damage_report.status = "resolved"
    damage_report.save()

    res = api_client.post(f"/api/v1/damage-reports/{damage_report.id}/approve/", {}, format="json")

    assert res.status_code == 400
    assert "resolved" in res.data["error"].lower()


# ============================================================================
# Workflow Tests: Start Work
# ============================================================================


@pytest.mark.django_db
def test_start_work_on_damage(api_client, admin_user, damage_report):
    """Test marking damage as in_progress"""
    api_client.force_authenticate(user=admin_user)

    res = api_client.post(f"/api/v1/damage-reports/{damage_report.id}/start-work/", {}, format="json")

    assert res.status_code == 200
    assert res.data["status"] == "in_progress"
    assert res.data["in_progress_at"] is not None


@pytest.mark.django_db
def test_start_work_on_resolved_fails(api_client, admin_user, damage_report):
    """Test cannot start work on resolved damage"""
    api_client.force_authenticate(user=admin_user)

    damage_report.status = "resolved"
    damage_report.save()

    res = api_client.post(f"/api/v1/damage-reports/{damage_report.id}/start-work/", {}, format="json")

    assert res.status_code == 400


# ============================================================================
# Workflow Tests: Resolution
# ============================================================================


@pytest.mark.django_db
def test_resolve_damage(api_client, admin_user, damage_report):
    """Test marking damage as resolved"""
    api_client.force_authenticate(user=admin_user)

    res = api_client.post(
        f"/api/v1/damage-reports/{damage_report.id}/resolve/",
        {"resolution_notes": "Fixed leak and repainted ceiling"},
        format="json",
    )

    assert res.status_code == 200
    assert res.data["status"] == "resolved"
    assert res.data["resolved_at"] is not None

    # Verify auto-task completed
    damage_report.refresh_from_db()
    assert damage_report.auto_task.status == "Completed"

    # Verify notification sent to reporter
    notification = Notification.objects.filter(
        user=damage_report.reported_by, notification_type="damage_resolved"
    ).first()
    assert notification is not None


@pytest.mark.django_db
def test_resolve_already_resolved_fails(api_client, admin_user, damage_report):
    """Test cannot resolve already resolved damage"""
    api_client.force_authenticate(user=admin_user)

    damage_report.status = "resolved"
    damage_report.save()

    res = api_client.post(f"/api/v1/damage-reports/{damage_report.id}/resolve/", {}, format="json")

    assert res.status_code == 400


# ============================================================================
# Workflow Tests: Change Order Conversion
# ============================================================================


@pytest.mark.django_db
def test_convert_damage_to_change_order(api_client, admin_user, damage_report):
    """Test converting damage report to Change Order"""
    api_client.force_authenticate(user=admin_user)

    res = api_client.post(
        f"/api/v1/damage-reports/{damage_report.id}/convert-to-co/",
        {"co_title": "CO: Water Damage Repair", "co_description": "Full bathroom ceiling repair"},
        format="json",
    )

    assert res.status_code == 201
    assert "damage_report" in res.data
    assert "change_order" in res.data

    # Verify Change Order was created
    co = ChangeOrder.objects.get(id=res.data["change_order"]["id"])
    assert co.title == "CO: Water Damage Repair"
    assert co.amount == damage_report.estimated_cost
    assert co.status == "draft"

    # Verify damage report linked to CO
    assert res.data["damage_report"]["linked_co_id"] == co.id


@pytest.mark.django_db
def test_convert_without_title_uses_default(api_client, admin_user, damage_report):
    """Test CO conversion uses damage title if not provided"""
    api_client.force_authenticate(user=admin_user)

    res = api_client.post(f"/api/v1/damage-reports/{damage_report.id}/convert-to-co/", {}, format="json")

    assert res.status_code == 201
    co_title = res.data["change_order"]["title"]
    assert "Repair:" in co_title
    assert damage_report.title in co_title


@pytest.mark.django_db
def test_convert_to_co_as_non_staff_fails(api_client, regular_user, damage_report):
    """Test non-staff cannot convert to CO"""
    api_client.force_authenticate(user=regular_user)

    res = api_client.post(f"/api/v1/damage-reports/{damage_report.id}/convert-to-co/", {}, format="json")

    assert res.status_code == 403


@pytest.mark.django_db
def test_convert_to_co_twice_fails(api_client, admin_user, damage_report):
    """Test cannot create multiple COs for same damage"""
    api_client.force_authenticate(user=admin_user)

    # First conversion
    res1 = api_client.post(f"/api/v1/damage-reports/{damage_report.id}/convert-to-co/", {}, format="json")
    assert res1.status_code == 201

    # Second conversion
    res2 = api_client.post(f"/api/v1/damage-reports/{damage_report.id}/convert-to-co/", {}, format="json")
    assert res2.status_code == 400
    assert "already created" in res2.data["error"].lower()


# ============================================================================
# Filtering Tests
# ============================================================================


@pytest.mark.django_db
def test_filter_by_severity(api_client, admin_user, project):
    """Test filtering damages by severity"""
    api_client.force_authenticate(user=admin_user)

    # Create damages with different severities
    DamageReport.objects.create(project=project, title="Low 1", severity="low", reported_by=admin_user)
    DamageReport.objects.create(project=project, title="High 1", severity="high", reported_by=admin_user)
    DamageReport.objects.create(project=project, title="Critical 1", severity="critical", reported_by=admin_user)

    res = api_client.get("/api/v1/damage-reports/", {"severity": "critical"})

    assert res.status_code == 200
    assert len(res.data) == 1
    assert res.data[0]["severity"] == "critical"


@pytest.mark.django_db
def test_filter_by_status(api_client, admin_user, project):
    """Test filtering damages by status"""
    api_client.force_authenticate(user=admin_user)

    DamageReport.objects.create(project=project, title="Open 1", status="open", reported_by=admin_user)
    DamageReport.objects.create(project=project, title="Progress 1", status="in_progress", reported_by=admin_user)
    DamageReport.objects.create(project=project, title="Resolved 1", status="resolved", reported_by=admin_user)

    res = api_client.get("/api/v1/damage-reports/", {"status": "in_progress"})

    assert res.status_code == 200
    assert all(r["status"] == "in_progress" for r in res.data)


@pytest.mark.django_db
def test_filter_by_assignee(api_client, admin_user, assignee_user, project):
    """Test filtering damages by assigned user"""
    api_client.force_authenticate(user=admin_user)

    DamageReport.objects.create(project=project, title="Assigned 1", assigned_to=assignee_user, reported_by=admin_user)
    DamageReport.objects.create(project=project, title="Unassigned 1", reported_by=admin_user)

    res = api_client.get("/api/v1/damage-reports/", {"assigned_to": assignee_user.id})

    assert res.status_code == 200
    assert all(r["assigned_to"] == assignee_user.id for r in res.data)


@pytest.mark.django_db
def test_search_by_title(api_client, admin_user, project):
    """Test searching damages by title"""
    api_client.force_authenticate(user=admin_user)

    DamageReport.objects.create(project=project, title="Kitchen Floor Crack", reported_by=admin_user)
    DamageReport.objects.create(project=project, title="Bathroom Wall Damage", reported_by=admin_user)

    res = api_client.get("/api/v1/damage-reports/", {"search": "Kitchen"})

    assert res.status_code == 200
    assert len(res.data) == 1
    assert "Kitchen" in res.data[0]["title"]


# ============================================================================
# Analytics Tests
# ============================================================================


@pytest.mark.django_db
def test_damage_analytics(api_client, admin_user, project):
    """Test damage reports analytics endpoint"""
    api_client.force_authenticate(user=admin_user)

    # Create diverse damages
    DamageReport.objects.create(
        project=project, title="D1", severity="low", status="open", category="cosmetic", reported_by=admin_user
    )
    DamageReport.objects.create(
        project=project,
        title="D2",
        severity="high",
        status="in_progress",
        category="structural",
        reported_by=admin_user,
    )
    DamageReport.objects.create(
        project=project, title="D3", severity="critical", status="resolved", category="plumbing", reported_by=admin_user
    )

    res = api_client.get("/api/v1/damage-reports/analytics/", {"project": project.id})

    assert res.status_code == 200
    assert "severity" in res.data
    assert "status" in res.data
    assert "category" in res.data
    assert res.data["total"] == 3
    assert res.data["severity"]["low"] == 1
    assert res.data["severity"]["high"] == 1
    assert res.data["status"]["open"] == 1


# ============================================================================
# Integration Tests: Complete Workflow
# ============================================================================


@pytest.mark.django_db
def test_complete_damage_lifecycle(api_client, admin_user, assignee_user, project):
    """Test complete damage report lifecycle from creation to resolution"""
    api_client.force_authenticate(user=admin_user)

    # 1. Create damage
    create_res = api_client.post(
        "/api/v1/damage-reports/",
        {
            "project": project.id,
            "title": "Complete Workflow Test",
            "description": "Testing full lifecycle",
            "category": "electrical",
            "severity": "medium",
            "estimated_cost": 1000.00,
        },
        format="json",
    )

    assert create_res.status_code == 201
    damage_id = create_res.data["id"]

    # 2. Assign to user
    assign_res = api_client.post(
        f"/api/v1/damage-reports/{damage_id}/assign/", {"assigned_to": assignee_user.id}, format="json"
    )
    assert assign_res.status_code == 200

    # 3. Assess severity
    assess_res = api_client.post(
        f"/api/v1/damage-reports/{damage_id}/assess/", {"severity": "high", "estimated_cost": 1500.00}, format="json"
    )
    assert assess_res.status_code == 200

    # 4. Approve
    approve_res = api_client.post(f"/api/v1/damage-reports/{damage_id}/approve/", {}, format="json")
    assert approve_res.status_code == 200
    assert approve_res.data["status"] == "in_progress"

    # 5. Resolve
    resolve_res = api_client.post(f"/api/v1/damage-reports/{damage_id}/resolve/", {}, format="json")
    assert resolve_res.status_code == 200
    assert resolve_res.data["status"] == "resolved"

    # Verify final state
    damage = DamageReport.objects.get(id=damage_id)
    assert damage.status == "resolved"
    assert damage.assigned_to == assignee_user
    assert damage.auto_task.status == "Completed"
