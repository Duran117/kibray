"""
Tests for HOA Resident Portal.

Covers:
  - Portal landing / identification flow
  - Session cookie creation & validation
  - Dashboard display
  - Touch-up creation from portal (with photos, floor plan pin)
  - Touch-up detail view
  - Portal logout
  - Staff management (create portal, toggle, manage units)
"""

import uuid

import pytest
from django.test import TestCase, Client
from django.urls import reverse

from core.models import (
    FloorPlan,
    Notification,
    Project,
    ProjectUnit,
    ResidentPortal,
    ResidentSession,
    TouchUp,
    TouchUpPhoto,
)


@pytest.fixture
def staff_user(db):
    from django.contrib.auth.models import User
    user = User.objects.create_user("pm_user", "pm@test.com", "pass1234")
    user.profile.role = "project_manager"
    user.profile.save()
    return user


@pytest.fixture
def admin_user(db):
    from django.contrib.auth.models import User
    user = User.objects.create_user("admin_user", "admin@test.com", "pass1234", is_superuser=True)
    return user


@pytest.fixture
def project(db, staff_user):
    return Project.objects.create(name="Test HOA Community")


@pytest.fixture
def portal(db, project, staff_user):
    return ResidentPortal.objects.create(
        project=project,
        created_by=staff_user,
        is_active=True,
        welcome_message="Welcome to the resident portal!",
        allow_photo_upload=True,
    )


@pytest.fixture
def units(db, project):
    u1 = ProjectUnit.objects.create(project=project, identifier="101", floor=1)
    u2 = ProjectUnit.objects.create(project=project, identifier="102", floor=1)
    u3 = ProjectUnit.objects.create(project=project, identifier="201", floor=2)
    return [u1, u2, u3]


@pytest.fixture
def resident_session(db, portal):
    import secrets
    return ResidentSession.objects.create(
        portal=portal,
        name="John Doe",
        unit="101",
        email="john@test.com",
        phone="555-1234",
        session_key=secrets.token_urlsafe(32),
    )


# ─── LANDING / IDENTIFY ────────────────────────────────────────────────────

@pytest.mark.django_db
class TestPortalLanding:

    def test_landing_page_loads(self, portal, units):
        c = Client()
        url = reverse("portal_landing", kwargs={"token": portal.token})
        resp = c.get(url)
        assert resp.status_code == 200
        assert "Welcome to the resident portal!" in resp.content.decode()
        # Units should appear as select options
        assert "101" in resp.content.decode()
        assert "201" in resp.content.decode()

    def test_landing_inactive_portal_404(self, portal):
        portal.is_active = False
        portal.save()
        c = Client()
        url = reverse("portal_landing", kwargs={"token": portal.token})
        resp = c.get(url)
        assert resp.status_code == 404

    def test_landing_bad_token_404(self, portal):
        c = Client()
        url = reverse("portal_landing", kwargs={"token": uuid.uuid4()})
        resp = c.get(url)
        assert resp.status_code == 404

    def test_landing_with_session_redirects_to_dashboard(self, portal, resident_session):
        c = Client()
        c.cookies[f"portal_{portal.token}"] = resident_session.session_key
        url = reverse("portal_landing", kwargs={"token": portal.token})
        resp = c.get(url)
        assert resp.status_code == 302
        assert "dashboard" in resp.url


@pytest.mark.django_db
class TestPortalIdentify:

    def test_identify_success(self, portal, units):
        c = Client()
        url = reverse("portal_identify", kwargs={"token": portal.token})
        resp = c.post(url, {
            "name": "Jane Smith",
            "unit": "101",
            "email": "jane@test.com",
            "phone": "555-9999",
        })
        assert resp.status_code == 302
        assert "dashboard" in resp.url
        # Check cookie was set
        cookie_name = f"portal_{portal.token}"
        assert cookie_name in resp.cookies
        # Check session created
        assert ResidentSession.objects.filter(portal=portal, name="Jane Smith").exists()

    def test_identify_missing_name(self, portal):
        c = Client()
        url = reverse("portal_identify", kwargs={"token": portal.token})
        resp = c.post(url, {"name": "", "unit": "101"})
        assert resp.status_code == 200  # Re-renders form with errors
        assert ResidentSession.objects.count() == 0

    def test_identify_required_fields(self, portal):
        portal.require_unit = True
        portal.require_email = True
        portal.require_phone = True
        portal.save()
        c = Client()
        url = reverse("portal_identify", kwargs={"token": portal.token})
        # Missing unit, email, phone
        resp = c.post(url, {"name": "Test User"})
        assert resp.status_code == 200
        assert ResidentSession.objects.count() == 0

    def test_identify_get_redirects(self, portal):
        c = Client()
        url = reverse("portal_identify", kwargs={"token": portal.token})
        resp = c.get(url)
        assert resp.status_code == 302  # Redirects to landing


# ─── DASHBOARD ──────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestPortalDashboard:

    def test_dashboard_without_session_redirects(self, portal):
        c = Client()
        url = reverse("portal_dashboard", kwargs={"token": portal.token})
        resp = c.get(url)
        assert resp.status_code == 302
        assert "portal" in resp.url

    def test_dashboard_loads_with_touchups(self, portal, resident_session, project):
        # Create a touch-up for this resident
        tu = TouchUp.objects.create(
            project=project,
            title="Paint peeling in hallway",
            resident_name=resident_session.name,
            resident_unit=resident_session.unit,
            status="open",
        )

        c = Client()
        c.cookies[f"portal_{portal.token}"] = resident_session.session_key
        url = reverse("portal_dashboard", kwargs={"token": portal.token})
        resp = c.get(url)
        assert resp.status_code == 200
        content = resp.content.decode()
        assert "Paint peeling in hallway" in content
        assert resident_session.name in content

    def test_dashboard_only_shows_own_touchups(self, portal, resident_session, project):
        # Resident's own
        TouchUp.objects.create(
            project=project, title="My issue",
            resident_name="John Doe", resident_unit="101",
        )
        # Someone else's
        TouchUp.objects.create(
            project=project, title="Other issue",
            resident_name="Other Person", resident_unit="999",
        )

        c = Client()
        c.cookies[f"portal_{portal.token}"] = resident_session.session_key
        url = reverse("portal_dashboard", kwargs={"token": portal.token})
        resp = c.get(url)
        content = resp.content.decode()
        assert "My issue" in content
        assert "Other issue" not in content


# ─── CREATE TOUCH-UP ────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestPortalCreateTouchup:

    def test_create_touchup_success(self, portal, resident_session, project, admin_user):
        c = Client()
        c.cookies[f"portal_{portal.token}"] = resident_session.session_key
        url = reverse("portal_create_touchup", kwargs={"token": portal.token})
        resp = c.post(url, {
            "title": "Ceiling stain in unit 101",
            "description": "Brown stain near the window",
            "priority": "high",
        })
        assert resp.status_code == 302  # Redirect to dashboard
        tu = TouchUp.objects.get(title="Ceiling stain in unit 101")
        assert tu.resident_name == "John Doe"
        assert tu.resident_unit == "101"
        assert tu.resident_email == "john@test.com"
        assert tu.priority == "high"
        assert tu.created_by is None  # No Django user

    def test_create_touchup_notifications(self, portal, resident_session, project, admin_user):
        c = Client()
        c.cookies[f"portal_{portal.token}"] = resident_session.session_key
        url = reverse("portal_create_touchup", kwargs={"token": portal.token})
        c.post(url, {"title": "Notify test"})
        # Admin should get a notification
        assert Notification.objects.filter(
            user=admin_user,
            notification_type="touchup",
        ).exists()

    def test_create_touchup_with_floor_plan(self, portal, resident_session, project):
        from django.core.files.uploadedfile import SimpleUploadedFile
        import io
        from PIL import Image

        # Create a small test image for floor plan
        img_io = io.BytesIO()
        img = Image.new("RGB", (100, 100), "white")
        img.save(img_io, format="PNG")
        img_io.seek(0)

        fp = FloorPlan.objects.create(
            project=project,
            name="Ground Floor",
            level="1",
            image=SimpleUploadedFile("floor.png", img_io.read(), content_type="image/png"),
            is_current=True,
        )

        c = Client()
        c.cookies[f"portal_{portal.token}"] = resident_session.session_key
        url = reverse("portal_create_touchup", kwargs={"token": portal.token})
        resp = c.post(url, {
            "title": "Pin test",
            "floor_plan_id": fp.id,
            "pin_x": "0.3456",
            "pin_y": "0.7890",
        })
        assert resp.status_code == 302
        tu = TouchUp.objects.get(title="Pin test")
        assert tu.floor_plan == fp
        assert float(tu.pin_x) == pytest.approx(0.3456, abs=0.001)
        assert float(tu.pin_y) == pytest.approx(0.7890, abs=0.001)

    def test_create_touchup_empty_title_redirects(self, portal, resident_session):
        c = Client()
        c.cookies[f"portal_{portal.token}"] = resident_session.session_key
        url = reverse("portal_create_touchup", kwargs={"token": portal.token})
        resp = c.post(url, {"title": ""})
        assert resp.status_code == 302  # Redirects without creating
        assert TouchUp.objects.count() == 0

    def test_create_touchup_no_session_redirects(self, portal):
        c = Client()
        url = reverse("portal_create_touchup", kwargs={"token": portal.token})
        resp = c.post(url, {"title": "Should not work"})
        assert resp.status_code == 302
        assert TouchUp.objects.count() == 0

    def test_create_touchup_only_post(self, portal, resident_session):
        c = Client()
        c.cookies[f"portal_{portal.token}"] = resident_session.session_key
        url = reverse("portal_create_touchup", kwargs={"token": portal.token})
        resp = c.get(url)
        assert resp.status_code == 405  # Method Not Allowed


# ─── TOUCH-UP DETAIL ────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestPortalTouchupDetail:

    def test_detail_loads(self, portal, resident_session, project):
        tu = TouchUp.objects.create(
            project=project, title="Detail test",
            resident_name="John Doe", resident_unit="101", status="open",
        )
        c = Client()
        c.cookies[f"portal_{portal.token}"] = resident_session.session_key
        url = reverse("portal_touchup_detail", kwargs={"token": portal.token, "touchup_id": tu.id})
        resp = c.get(url)
        assert resp.status_code == 200
        assert "Detail test" in resp.content.decode()

    def test_detail_other_resident_redirects(self, portal, resident_session, project):
        tu = TouchUp.objects.create(
            project=project, title="Other's touchup",
            resident_name="Different Person", resident_unit="999", status="open",
        )
        c = Client()
        c.cookies[f"portal_{portal.token}"] = resident_session.session_key
        url = reverse("portal_touchup_detail", kwargs={"token": portal.token, "touchup_id": tu.id})
        resp = c.get(url)
        assert resp.status_code == 302  # Redirected to dashboard

    def test_detail_no_session_redirects(self, portal, project):
        tu = TouchUp.objects.create(
            project=project, title="No session test",
            resident_name="John Doe", resident_unit="101",
        )
        c = Client()
        url = reverse("portal_touchup_detail", kwargs={"token": portal.token, "touchup_id": tu.id})
        resp = c.get(url)
        assert resp.status_code == 302


# ─── LOGOUT ─────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestPortalLogout:

    def test_logout_clears_cookie(self, portal, resident_session):
        c = Client()
        c.cookies[f"portal_{portal.token}"] = resident_session.session_key
        url = reverse("portal_logout", kwargs={"token": portal.token})
        resp = c.get(url)
        assert resp.status_code == 302
        # Cookie should be deleted (max-age=0)
        cookie = resp.cookies.get(f"portal_{portal.token}")
        assert cookie is not None
        assert cookie["max-age"] == 0


# ─── STAFF MANAGEMENT ──────────────────────────────────────────────────────

@pytest.mark.django_db
class TestPortalManage:

    def test_manage_requires_login(self, project):
        c = Client()
        url = reverse("portal_manage", kwargs={"project_id": project.id})
        resp = c.get(url)
        assert resp.status_code == 302
        assert "login" in resp.url

    def test_manage_creates_portal_on_first_visit(self, project, staff_user):
        c = Client()
        c.login(username="pm_user", password="pass1234")
        assert not ResidentPortal.objects.filter(project=project).exists()
        url = reverse("portal_manage", kwargs={"project_id": project.id})
        resp = c.get(url)
        assert resp.status_code == 200
        assert ResidentPortal.objects.filter(project=project).exists()

    def test_manage_toggle_active(self, project, staff_user, portal):
        c = Client()
        c.login(username="pm_user", password="pass1234")
        url = reverse("portal_manage", kwargs={"project_id": project.id})
        assert portal.is_active is True
        c.post(url, {"action": "toggle_active"})
        portal.refresh_from_db()
        assert portal.is_active is False

    def test_manage_update_settings(self, project, staff_user, portal):
        c = Client()
        c.login(username="pm_user", password="pass1234")
        url = reverse("portal_manage", kwargs={"project_id": project.id})
        c.post(url, {
            "action": "update_settings",
            "welcome_message": "Updated welcome!",
            "require_unit": "on",
            "allow_photo_upload": "on",
        })
        portal.refresh_from_db()
        assert portal.welcome_message == "Updated welcome!"
        assert portal.require_unit is True
        assert portal.require_email is False
        assert portal.allow_photo_upload is True

    def test_manage_add_unit(self, project, staff_user, portal):
        c = Client()
        c.login(username="pm_user", password="pass1234")
        url = reverse("portal_manage", kwargs={"project_id": project.id})
        c.post(url, {
            "action": "add_unit",
            "identifier": "301",
            "floor": "3",
        })
        assert ProjectUnit.objects.filter(project=project, identifier="301").exists()

    def test_manage_bulk_add_units(self, project, staff_user, portal):
        c = Client()
        c.login(username="pm_user", password="pass1234")
        url = reverse("portal_manage", kwargs={"project_id": project.id})
        c.post(url, {
            "action": "bulk_add_units",
            "bulk_units": "A1\nA2\nA3\n",
        })
        assert ProjectUnit.objects.filter(project=project).count() == 3

    def test_manage_delete_unit(self, project, staff_user, portal, units):
        c = Client()
        c.login(username="pm_user", password="pass1234")
        url = reverse("portal_manage", kwargs={"project_id": project.id})
        c.post(url, {
            "action": "delete_unit",
            "unit_id": units[0].id,
        })
        assert not ProjectUnit.objects.filter(pk=units[0].id).exists()
        assert ProjectUnit.objects.filter(project=project).count() == 2
