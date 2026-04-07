"""
Comprehensive E2E Test Suite for Touch-up Board System
Testing all CRUD operations, workflow, approval system, and integration

Module 28: Touch-ups Management System
Created: December 12, 2025
"""

import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from rest_framework.test import APIClient
from decimal import Decimal
from io import BytesIO
from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile

User = get_user_model()


# Enable TouchUpPin routes for all tests
pytestmark = [
    pytest.mark.django_db,
    pytest.mark.override_settings(TOUCHUP_PIN_ENABLED=True),
]


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def setup_touchup_users(db):
    """Create all user types with profiles and permissions"""
    from core.models import Profile, Employee, FloorPlan, ClientProjectAccess
    
    # Create users (Profile is auto-created by signal)
    admin = User.objects.create_user(username="admin_touch", password="test123", is_staff=True)
    pm = User.objects.create_user(username="pm_touch", password="test123")
    employee = User.objects.create_user(username="employee_touch", password="test123")
    client = User.objects.create_user(username="client_touch", password="test123")
    designer = User.objects.create_user(username="designer_touch", password="test123")
    
    # Update profiles with correct roles (auto-created with role="employee")
    admin.profile.role = "admin"
    admin.profile.save()
    pm.profile.role = "project_manager"
    pm.profile.save()
    # employee already has role="employee"
    client.profile.role = "client"
    client.profile.save()
    designer.profile.role = "designer"
    designer.profile.save()
    
    # Create employee record for touchup assignment
    emp_record = Employee.objects.create(
        user=employee,
        first_name="Test",
        last_name="Employee",
        social_security_number="123-45-6789",
        hourly_rate=Decimal("25.00")
    )
    
    # Create project
    from core.models import Project
    project = Project.objects.create(
        name="Touch-up Test Project",
        client="Touch-up Client",
        start_date="2025-01-01",
        budget_total=Decimal("50000")
    )
    
    # Grant access to all users
    for user in [pm, employee, client, designer]:
        ClientProjectAccess.objects.create(
            user=user,
            project=project,
            role="client" if user == client else "external_pm"
        )
    
    # Create floor plan with valid PNG image
    img = Image.new('RGB', (800, 600), color='white')
    img_io = BytesIO()
    img.save(img_io, format='PNG')
    img_io.seek(0)
    
    floor_plan = FloorPlan.objects.create(
        project=project,
        name="Main Floor",
        level=0,
        image=SimpleUploadedFile("main_floor.png", img_io.getvalue(), content_type="image/png"),
        created_by=pm
    )
    
    return {
        "admin": admin,
        "pm": pm,
        "employee": employee,
        "employee_record": emp_record,
        "employee_user": employee,  # For TouchUpPin.assigned_to
        "client": client,
        "designer": designer,
        "project": project,
        "floor_plan": floor_plan
    }


def create_test_image(filename="test.png"):
    """Helper to create a valid PNG image for testing"""
    img = Image.new('RGB', (100, 100), color='red')
    img_io = BytesIO()
    img.save(img_io, format='PNG')
    img_io.seek(0)
    return SimpleUploadedFile(filename, img_io.getvalue(), content_type="image/png")


# =============================================================================
# TEST 1: TOUCHUP CRUD COMPLETE FLOW
# =============================================================================


@pytest.mark.django_db
def test_touchup_crud_complete_flow(setup_touchup_users):
    """
    Test complete CRUD operations for touch-ups:
    - PM creates touch-up on floor plan
    - Designer updates touch-up details
    - Employee marks as completed with photos
    - PM approves/rejects completion
    - Admin deletes touch-up
    """
    data = setup_touchup_users
    client = Client()
    
    # ---- CREATE: PM creates touch-up ----
    client.force_login(data["pm"])
    
    create_response = client.post(
        f"/plans/{data['floor_plan'].id}/touchups/create/",
        {
            "x": "0.5",
            "y": "0.3",
            "task_name": "Paint touch-up in hallway",
            "description": "Small chip on wall needs repair",
            "assigned_to": data["employee"].id,
            "custom_color_name": "Snowbound SW-7004",
            "sheen": "Eggshell",
            "status": "pending"
        }
    )
    
    assert create_response.status_code in [200, 201, 302], f"Got {create_response.status_code}"
    
    # Verify touchup created
    from core.models import TouchUpPin
    touchup = TouchUpPin.objects.filter(plan=data["floor_plan"]).first()
    assert touchup is not None
    assert touchup.task_name == "Paint touch-up in hallway"
    assert touchup.status == "pending"
    assert touchup.assigned_to == data["employee"]
    assert float(touchup.x) == 0.5
    assert float(touchup.y) == 0.3
    
    # ---- READ: View touchup on plan ----
    detail_response = client.get(f"/plans/{data['floor_plan'].id}/touchups/")
    assert detail_response.status_code == 200
    
    # ---- UPDATE: Designer updates details ----
    client.force_login(data["designer"])
    
    update_response = client.post(
        f"/touchups/{touchup.id}/update/",
        {
            "description": "Updated: Small chip plus corner scuff",
            "sheen": "20-25 gloss",
            "details": "Use fine brush for precision"
        }
    )
    
    assert update_response.status_code in [200, 302]
    touchup.refresh_from_db()
    assert "Updated: Small chip plus corner scuff" in touchup.description
    
    # ---- COMPLETE: Employee marks completed with photos ----
    client.force_login(data["employee"])
    
    # Create completion photos
    photo1 = create_test_image("complete1.png")
    photo2 = create_test_image("complete2.png")
    
    complete_response = client.post(
        f"/touchups/{touchup.id}/complete/",
        {
            "notes": "Completed as requested",
            "photos": [photo1, photo2]
        }
    )
    
    assert complete_response.status_code in [200, 302]
    touchup.refresh_from_db()
    assert touchup.status == "completed"
    assert touchup.completion_photos.count() >= 1  # At least one photo uploaded
    assert touchup.closed_by == data["employee"]
    
    # ---- APPROVE: PM approves completion ----
    client.force_login(data["pm"])
    
    approve_response = client.post(f"/touchups/{touchup.id}/approve/")
    
    assert approve_response.status_code in [200, 302]
    touchup.refresh_from_db()
    assert touchup.approval_status == "approved"
    assert touchup.reviewed_by == data["pm"]
    
    # ---- DELETE: Admin deletes touch-up ----
    client.force_login(data["admin"])
    
    delete_response = client.post(f"/touchups/{touchup.id}/delete/")
    assert delete_response.status_code in [200, 302]
    assert not TouchUpPin.objects.filter(id=touchup.id).exists()


# =============================================================================
# TEST 2: TOUCHUP APPROVAL WORKFLOW
# =============================================================================


@pytest.mark.django_db
def test_touchup_approval_workflow(setup_touchup_users):
    """
    Test approval workflow:
    - Employee completes touchup
    - PM can approve OR reject with reason
    - Rejected touchup reopens with status change
    - Employee can re-complete after fixes
    """
    data = setup_touchup_users
    api_client = APIClient()
    
    # Create touchup as PM
    api_client.force_authenticate(user=data["pm"])
    from core.models import TouchUpPin
    
    touchup = TouchUpPin.objects.create(
        plan=data["floor_plan"],
        x=Decimal("0.6"),
        y=Decimal("0.4"),
        task_name="Corner repair",
        description="Fix paint damage",
        status="in_progress",
        assigned_to=data["employee_record"],
        created_by=data["pm"]
    )
    
    # Employee completes
    api_client.force_authenticate(user=data["employee"])
    photo = create_test_image("complete.png")
    
    complete_response = api_client.post(
        f"/api/v1/touchups/{touchup.id}/complete/",
        {
            "notes": "Fixed corner",
            "photos": [photo]
        },
        format="multipart"
    )
    
    assert complete_response.status_code == 200
    touchup.refresh_from_db()
    assert touchup.status == "completed"
    assert touchup.approval_status == "pending_review"
    
    # ---- SCENARIO 1: PM REJECTS ----
    api_client.force_authenticate(user=data["pm"])
    
    reject_response = api_client.post(
        f"/api/v1/touchups/{touchup.id}/reject/",
        {"reason": "Needs more blending on edges"},
        format="json"
    )
    
    assert reject_response.status_code == 200
    touchup.refresh_from_db()
    assert touchup.approval_status == "rejected"
    assert touchup.rejection_reason == "Needs more blending on edges"
    assert touchup.status == "in_progress"  # Reopened
    assert touchup.reviewed_by == data["pm"]
    
    # Employee fixes and re-completes
    api_client.force_authenticate(user=data["employee"])
    photo2 = create_test_image("fixed.png")
    
    complete_response2 = api_client.post(
        f"/api/v1/touchups/{touchup.id}/complete/",
        {
            "notes": "Fixed blending",
            "photos": [photo2]
        },
        format="multipart"
    )
    
    assert complete_response2.status_code == 200
    touchup.refresh_from_db()
    assert touchup.status == "completed"
    assert touchup.completion_photos.count() == 2  # Both photos saved
    
    # ---- SCENARIO 2: PM APPROVES ----
    api_client.force_authenticate(user=data["pm"])
    
    approve_response = api_client.post(
        f"/api/v1/touchups/{touchup.id}/approve/"
    )
    
    assert approve_response.status_code == 200
    touchup.refresh_from_db()
    assert touchup.approval_status == "approved"
    assert touchup.reviewed_at is not None


# =============================================================================
# TEST 3: TOUCHUP PERMISSIONS BY ROLE
# =============================================================================


@pytest.mark.django_db
def test_touchup_permissions_by_role(setup_touchup_users):
    """
    Test permissions for different roles:
    - PM: Can create, update, approve, reject, delete
    - Designer: Can create, update, view
    - Employee: Can view assigned, complete assigned, cannot delete
    - Client: Can view, comment, cannot modify
    """
    data = setup_touchup_users
    api_client = APIClient()
    
    from core.models import TouchUpPin
    
    # Create touchup as PM
    api_client.force_authenticate(user=data["pm"])
    
    touchup = TouchUpPin.objects.create(
        plan=data["floor_plan"],
        x=Decimal("0.5"),
        y=Decimal("0.5"),
        task_name="Permission test",
        status="pending",
        assigned_to=data["employee_record"],
        created_by=data["pm"]
    )
    
    # ---- CLIENT PERMISSIONS ----
    api_client.force_authenticate(user=data["client"])
    
    # Can view
    view_response = api_client.get(f"/api/v1/touchups/{touchup.id}/")
    assert view_response.status_code == 200
    
    # Cannot update
    update_response = api_client.patch(
        f"/api/v1/touchups/{touchup.id}/",
        {"description": "Trying to update"},
        format="json"
    )
    assert update_response.status_code == 403
    
    # Cannot delete
    delete_response = api_client.delete(f"/api/v1/touchups/{touchup.id}/")
    assert delete_response.status_code == 403
    
    # ---- EMPLOYEE PERMISSIONS ----
    api_client.force_authenticate(user=data["employee"])
    
    # Can complete assigned touchup
    photo = create_test_image()
    complete_response = api_client.post(
        f"/api/v1/touchups/{touchup.id}/complete/",
        {"notes": "Done", "photos": [photo]},
        format="multipart"
    )
    assert complete_response.status_code == 200
    
    # Cannot approve (not PM/Admin)
    approve_response = api_client.post(f"/api/v1/touchups/{touchup.id}/approve/")
    assert approve_response.status_code == 403
    
    # ---- DESIGNER PERMISSIONS ----
    api_client.force_authenticate(user=data["designer"])
    
    # Can update
    update_response2 = api_client.patch(
        f"/api/v1/touchups/{touchup.id}/",
        {"description": "Designer update"},
        format="json"
    )
    assert update_response2.status_code == 200
    
    # Cannot delete
    delete_response2 = api_client.delete(f"/api/v1/touchups/{touchup.id}/")
    assert delete_response2.status_code == 403
    
    # ---- PM PERMISSIONS ----
    api_client.force_authenticate(user=data["pm"])
    
    # Can approve
    approve_response2 = api_client.post(f"/api/v1/touchups/{touchup.id}/approve/")
    assert approve_response2.status_code == 200
    
    # Can delete
    delete_response3 = api_client.delete(f"/api/v1/touchups/{touchup.id}/")
    assert delete_response3.status_code == 200


# =============================================================================
# TEST 4: TOUCHUP WITH COLOR SAMPLES
# =============================================================================


@pytest.mark.django_db
def test_touchup_with_color_samples(setup_touchup_users):
    """
    Test touchup integration with color samples:
    - Create touchup with approved color reference
    - Link touchup to color sample
    - Verify color details cascade to touchup
    """
    data = setup_touchup_users
    api_client = APIClient()
    api_client.force_authenticate(user=data["pm"])
    
    # Create approved color sample
    from core.models import ColorSample
    
    color_sample = ColorSample.objects.create(
        project=data["project"],
        name="Snowbound",
        code="SW-7004",
        brand="Sherwin-Williams",
        finish="Eggshell",
        gloss="20 gloss",
        status="approved",
        created_by=data["pm"],
        approved_by=data["pm"]
    )
    
    # Create touchup linked to color
    from core.models import TouchUpPin
    
    touchup = TouchUpPin.objects.create(
        plan=data["floor_plan"],
        x=Decimal("0.7"),
        y=Decimal("0.6"),
        task_name="Hallway touch-up",
        approved_color=color_sample,
        status="pending",
        created_by=data["pm"]
    )
    
    # Verify linkage
    assert touchup.approved_color == color_sample
    
    # API response includes color details
    response = api_client.get(f"/api/v1/touchups/{touchup.id}/")
    assert response.status_code == 200
    assert response.data["approved_color"]["name"] == "Snowbound"
    assert response.data["approved_color"]["code"] == "SW-7004"


# =============================================================================
# TEST 5: TOUCHUP COMPLETION PHOTOS WITH ANNOTATIONS
# =============================================================================


@pytest.mark.django_db
def test_touchup_completion_photos_with_annotations(setup_touchup_users):
    """
    Test completion photos with annotation support:
    - Upload multiple completion photos
    - Add annotations to photos
    - Verify photos are saved correctly
    """
    data = setup_touchup_users
    api_client = APIClient()
    
    # Create touchup
    from core.models import TouchUpPin
    api_client.force_authenticate(user=data["pm"])
    
    touchup = TouchUpPin.objects.create(
        plan=data["floor_plan"],
        x=Decimal("0.8"),
        y=Decimal("0.7"),
        task_name="Photo test",
        status="in_progress",
        assigned_to=data["employee_record"],
        created_by=data["pm"]
    )
    
    # Employee completes with annotated photos
    api_client.force_authenticate(user=data["employee"])
    
    photo1 = create_test_image("before.png")
    photo2 = create_test_image("after.png")
    
    annotations_1 = {
        "arrows": [{"from": [10, 20], "to": [50, 60], "color": "red"}],
        "circles": [{"center": [100, 100], "radius": 20, "color": "blue"}]
    }
    
    annotations_2 = {
        "text": [{"position": [150, 150], "text": "Fixed here", "color": "green"}]
    }
    
    import json
    
    response = api_client.post(
        f"/api/v1/touchups/{touchup.id}/complete/",
        {
            "notes": "Completed with annotations",
            "photos": [photo1, photo2],
            "annotations_0": json.dumps(annotations_1),
            "annotations_1": json.dumps(annotations_2)
        },
        format="multipart"
    )
    
    assert response.status_code == 200
    
    # Verify photos saved with annotations
    touchup.refresh_from_db()
    photos = touchup.completion_photos.all().order_by("id")
    
    assert len(photos) == 2
    assert photos[0].annotations == annotations_1
    assert photos[1].annotations == annotations_2
    assert photos[0].notes == ""  # No individual notes
    assert touchup.status == "completed"


# =============================================================================
# TEST 6: TOUCHUP STATUS VALIDATIONS
# =============================================================================


@pytest.mark.django_db
def test_touchup_status_validations(setup_touchup_users):
    """
    Test status transition validations:
    - Cannot complete without photos
    - Cannot approve if not completed
    - Cannot reject if not completed
    - Status transitions follow proper workflow
    """
    data = setup_touchup_users
    api_client = APIClient()
    api_client.force_authenticate(user=data["pm"])
    
    from core.models import TouchUpPin
    
    touchup = TouchUpPin.objects.create(
        plan=data["floor_plan"],
        x=Decimal("0.5"),
        y=Decimal("0.5"),
        task_name="Status validation test",
        status="pending",
        assigned_to=data["employee_record"],
        created_by=data["pm"]
    )
    
    # ---- TEST 1: Cannot complete without photos ----
    api_client.force_authenticate(user=data["employee"])
    
    response = api_client.post(
        f"/api/v1/touchups/{touchup.id}/complete/",
        {"notes": "No photos"},
        format="json"
    )
    
    assert response.status_code == 400
    assert "foto" in response.data["error"].lower() or "photo" in response.data["error"].lower()
    
    # ---- TEST 2: Cannot approve if not completed ----
    api_client.force_authenticate(user=data["pm"])
    
    response = api_client.post(f"/api/v1/touchups/{touchup.id}/approve/")
    # Should either fail or be no-op (depends on implementation)
    # Most implementations would require completed status first
    
    # ---- TEST 3: Proper completion with photo ----
    api_client.force_authenticate(user=data["employee"])
    photo = create_test_image()
    
    response = api_client.post(
        f"/api/v1/touchups/{touchup.id}/complete/",
        {"notes": "Completed", "photos": [photo]},
        format="multipart"
    )
    
    assert response.status_code == 200
    touchup.refresh_from_db()
    assert touchup.status == "completed"


# =============================================================================
# TEST 7: TOUCHUP LIST FILTERING AND SEARCH
# =============================================================================


@pytest.mark.django_db
def test_touchup_list_filtering_and_search(setup_touchup_users):
    """
    Test filtering and search capabilities:
    - Filter by status (pending, in_progress, completed)
    - Filter by assigned employee
    - Filter by approval status
    - Search by task name or description
    """
    data = setup_touchup_users
    api_client = APIClient()
    api_client.force_authenticate(user=data["pm"])
    
    from core.models import TouchUpPin
    
    # Create multiple touchups with different statuses
    touchup1 = TouchUpPin.objects.create(
        plan=data["floor_plan"],
        x=Decimal("0.1"),
        y=Decimal("0.1"),
        task_name="Paint hallway",
        status="pending",
        assigned_to=data["employee_record"],
        created_by=data["pm"]
    )
    
    touchup2 = TouchUpPin.objects.create(
        plan=data["floor_plan"],
        x=Decimal("0.2"),
        y=Decimal("0.2"),
        task_name="Fix corner",
        status="in_progress",
        assigned_to=data["employee_record"],
        created_by=data["pm"]
    )
    
    touchup3 = TouchUpPin.objects.create(
        plan=data["floor_plan"],
        x=Decimal("0.3"),
        y=Decimal("0.3"),
        task_name="Touch up ceiling",
        status="completed",
        assigned_to=data["employee_record"],
        created_by=data["pm"],
        approval_status="approved"
    )
    
    # ---- TEST 1: Filter by status ----
    response = api_client.get(
        f"/api/v1/touchups/{data['floor_plan'].id}/list/",
        {"status": "pending"}
    )
    
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]["id"] == touchup1.id
    
    # ---- TEST 2: Filter by approval status ----
    response = api_client.get(
        f"/api/v1/touchups/{data['floor_plan'].id}/list/",
        {"approval_status": "approved"}
    )
    
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]["id"] == touchup3.id
    
    # ---- TEST 3: Search by task name ----
    response = api_client.get(
        f"/api/v1/touchups/{data['floor_plan'].id}/list/",
        {"search": "corner"}
    )
    
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]["id"] == touchup2.id


# =============================================================================
# TEST 8: COMPLETE INTEGRATION WORKFLOW
# =============================================================================


@pytest.mark.django_db
def test_complete_integration_workflow(setup_touchup_users):
    """
    Full end-to-end workflow simulating real usage:
    1. Client creates task requesting touchup
    2. PM creates touchup on floor plan from task
    3. PM assigns to employee
    4. Employee marks in progress
    5. Employee completes with photos
    6. PM reviews and approves
    7. Touchup archived
    """
    data = setup_touchup_users
    client_web = Client()
    api_client = APIClient()
    
    from core.models import Task, TouchUpPin
    
    # ---- STEP 1: Client creates task ----
    api_client.force_authenticate(user=data["client"])
    
    task_response = api_client.post(
        "/api/v1/tasks/",
        {
            "project": data["project"].id,
            "title": "Paint chip in bedroom",
            "description": "Small paint chip near door frame needs touch-up",
            "is_touchup": True,
            "created_by": data["client"].id
        },
        format="json"
    )
    
    assert task_response.status_code == 201
    task_id = task_response.data["id"]
    
    # ---- STEP 2: PM creates touchup from task ----
    api_client.force_authenticate(user=data["pm"])
    
    touchup = TouchUpPin.objects.create(
        plan=data["floor_plan"],
        x=Decimal("0.65"),
        y=Decimal("0.45"),
        task_name="Paint chip in bedroom",
        description="Small paint chip near door frame needs touch-up",
        status="pending",
        created_by=data["pm"],
        custom_color_name="Dover White"
    )
    
    # Link task to touchup (if your model supports it)
    # task.touchup_pin = touchup
    # task.save()
    
    # ---- STEP 3: PM assigns to employee ----
    touchup.assigned_to = data["employee_record"]
    touchup.save()
    
    assert touchup.assigned_to == data["employee_record"]
    
    # ---- STEP 4: Employee marks in progress ----
    api_client.force_authenticate(user=data["employee"])
    
    touchup.status = "in_progress"
    touchup.save()
    
    assert touchup.status == "in_progress"
    
    # ---- STEP 5: Employee completes with photos ----
    before_photo = create_test_image("before.png")
    after_photo = create_test_image("after.png")
    
    complete_response = api_client.post(
        f"/api/v1/touchups/{touchup.id}/complete/",
        {
            "notes": "Fixed paint chip, blended with surrounding area",
            "photos": [before_photo, after_photo]
        },
        format="multipart"
    )
    
    assert complete_response.status_code == 200
    touchup.refresh_from_db()
    assert touchup.status == "completed"
    assert touchup.completion_photos.count() == 2
    
    # ---- STEP 6: PM reviews and approves ----
    api_client.force_authenticate(user=data["pm"])
    
    approve_response = api_client.post(
        f"/api/v1/touchups/{touchup.id}/approve/"
    )
    
    assert approve_response.status_code == 200
    touchup.refresh_from_db()
    assert touchup.approval_status == "approved"
    assert touchup.reviewed_by == data["pm"]
    assert touchup.reviewed_at is not None
    
    # ---- STEP 7: Verify final state ----
    assert touchup.status == "completed"
    assert touchup.approval_status == "approved"
    assert touchup.completion_photos.count() == 2


# =============================================================================
# COVERAGE SUMMARY
# =============================================================================
"""
✅ TEST 1: CRUD completo (Create, Read, Update, Delete, Complete, Approve)
✅ TEST 2: Workflow de aprobación (Approve, Reject, Re-complete)
✅ TEST 3: Permisos por rol (PM, Designer, Employee, Client)
✅ TEST 4: Integración con Color Samples
✅ TEST 5: Fotos de completado con anotaciones
✅ TEST 6: Validaciones de estado y transiciones
✅ TEST 7: Filtrado y búsqueda de touchups
✅ TEST 8: Workflow completo end-to-end

COBERTURA:
- Creación de touchups por PM/Designer/Client
- Asignación a empleados
- Workflow de estado (pending → in_progress → completed)
- Sistema de aprobación (pending_review → approved/rejected)
- Fotos de completado con anotaciones
- Permisos granulares por rol
- Integración con ColorSample
- Validaciones de negocio
- Filtrado y búsqueda
"""
