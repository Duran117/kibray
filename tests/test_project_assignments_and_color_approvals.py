import io
import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from core.models import Project, ColorApproval, ProjectManagerAssignment

User = get_user_model()

@pytest.mark.django_db
def test_pm_assignment_creates_notification(admin_user):
    client = APIClient()
    client.force_authenticate(admin_user)
    # Create PM user
    pm = User.objects.create_user(username="pm1", password="pass")
    # Create project
    project = Project.objects.create(name="Test Project")
    # Assign PM via API
    url = reverse("project-manager-assignment-list") + "assign/"
    resp = client.post(url, {"project": project.id, "pm": pm.id}, format="json")
    assert resp.status_code == 201
    assignment = ProjectManagerAssignment.objects.get(project=project, pm=pm)
    # PM should have at least one notification
    assert assignment.pm.notification_set.count() >= 1

@pytest.mark.django_db
def test_color_approval_approve_and_reject_flow(admin_user):
    client = APIClient()
    client.force_authenticate(admin_user)
    # Create requester and project
    requester = User.objects.create_user(username="req1", password="pass")
    project = Project.objects.create(name="Color Project")
    # Create approval request
    url = reverse("color-approval-list")
    resp = client.post(url, {
        "project": project.id,
        "requested_by": requester.id,
        "color_name": "Ocean Blue",
        "color_code": "BLU-001",
        "brand": "BrandX",
        "location": "Living Room",
    }, format="json")
    assert resp.status_code in (200, 201)
    approval_id = resp.data.get("id") or ColorApproval.objects.latest("id").id

    # Approve with signature
    approve_url = reverse("color-approval-approve", args=[approval_id])
    signature_content = io.BytesIO(b"fake-signature-bytes")
    resp2 = client.post(approve_url, {"client_signature": signature_content}, format="multipart")
    assert resp2.status_code in (200, 201)
    assert resp2.data["status"] == "approved"

    # Reject (should transition back to rejected)
    reject_url = reverse("color-approval-reject", args=[approval_id])
    resp3 = client.post(reject_url, {"reason": "Client changed mind"}, format="json")
    assert resp3.status_code in (200, 201)
    assert resp3.data["status"] == "rejected"