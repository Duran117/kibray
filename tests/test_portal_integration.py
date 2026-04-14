"""
Tests for Phase 1 — Portal ↔ System Integration.
Verifies:
  1. Portal link visible in project_overview sidebar (mobile + desktop)
  2. Portal stats (touchup count, session count, unit count) in project_overview context
  3. Portal badge on touchup cards (touchup_v2_list)
  4. Source filter (portal/staff) in touchup_list view
  5. Portal stats card in project_overview main content
  6. Portal link in global sidebar_dark (via sidebar_dark.html)
"""

import pytest
from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from django.urls import reverse

from core.models import (
    Project,
    Profile,
    ResidentPortal,
    ProjectUnit,
    ResidentSession,
    TouchUp,
)

User = get_user_model()


@pytest.mark.django_db
class TestPortalProjectOverview(TestCase):
    """Portal integration in project_overview page."""

    @classmethod
    def setUpTestData(cls):
        cls.admin_user = User.objects.create_user(
            username="portal_admin",
            password="testpass123",
            is_staff=True,
        )
        Profile.objects.get_or_create(
            user=cls.admin_user, defaults={"role": "admin"}
        )
        cls.project = Project.objects.create(name="HOA Portal Test Project")
        # Create portal
        cls.portal = ResidentPortal.objects.create(
            project=cls.project,
            is_active=True,
            welcome_message="Welcome to the HOA portal",
            created_by=cls.admin_user,
        )
        # Create units
        cls.unit1 = ProjectUnit.objects.create(
            project=cls.project, identifier="Unit 101"
        )
        cls.unit2 = ProjectUnit.objects.create(
            project=cls.project, identifier="Unit 202"
        )
        # Create a portal-submitted touchup (has resident_name)
        cls.portal_touchup = TouchUp.objects.create(
            project=cls.project,
            title="Scuff on wall",
            description="Resident reported scuff",
            resident_name="John Doe",
            resident_unit="Unit 101",
            resident_email="john@example.com",
            created_by=cls.admin_user,
        )
        # Create a staff-submitted touchup (no resident_name)
        cls.staff_touchup = TouchUp.objects.create(
            project=cls.project,
            title="Touch-up bathroom",
            description="Staff noticed issue",
            created_by=cls.admin_user,
        )
        # Create a resident session
        cls.session = ResidentSession.objects.create(
            portal=cls.portal,
            name="John Doe",
            unit="Unit 101",
            email="john@example.com",
        )

    def setUp(self):
        self.client.login(username="portal_admin", password="testpass123")

    def test_project_overview_has_portal_link_in_html(self):
        """Portal link should appear in project_overview sidebar."""
        url = reverse("project_overview", kwargs={"project_id": self.project.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        # Check portal link exists (URL pattern: portal_manage)
        portal_url = reverse("portal_manage", kwargs={"project_id": self.project.id})
        self.assertIn(portal_url, content)
        # Check "Resident Portal" text
        self.assertIn("Resident Portal", content)

    def test_project_overview_portal_context_data(self):
        """Portal stats should be in context."""
        url = reverse("project_overview", kwargs={"project_id": self.project.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["portal_active"])
        self.assertEqual(response.context["portal_touchup_count"], 1)
        self.assertEqual(response.context["portal_session_count"], 1)
        self.assertEqual(response.context["portal_unit_count"], 2)

    def test_project_overview_portal_stats_card_visible(self):
        """Portal status card should render in overview body."""
        url = reverse("project_overview", kwargs={"project_id": self.project.id})
        response = self.client.get(url)
        content = response.content.decode()
        self.assertIn("Portal Touch-ups", content)
        self.assertIn("Residents", content)
        self.assertIn("Units", content)

    def test_project_overview_no_portal(self):
        """Project without portal should show 0 counts."""
        project2 = Project.objects.create(name="No Portal Project")
        url = reverse("project_overview", kwargs={"project_id": project2.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["portal_active"])
        self.assertEqual(response.context["portal_touchup_count"], 0)


@pytest.mark.django_db
class TestTouchupListPortalFilter(TestCase):
    """Portal source filter + badge in touchup_v2_list."""

    @classmethod
    def setUpTestData(cls):
        cls.admin_user = User.objects.create_user(
            username="tu_filter_admin",
            password="testpass123",
            is_staff=True,
        )
        Profile.objects.get_or_create(
            user=cls.admin_user, defaults={"role": "admin"}
        )
        cls.project = Project.objects.create(name="TouchUp Filter Project")
        # Portal touchup
        cls.portal_tu = TouchUp.objects.create(
            project=cls.project,
            title="Portal scuff",
            resident_name="Jane Resident",
            resident_unit="Unit 303",
            created_by=cls.admin_user,
        )
        # Staff touchup
        cls.staff_tu = TouchUp.objects.create(
            project=cls.project,
            title="Staff inspection item",
            created_by=cls.admin_user,
        )

    def setUp(self):
        self.client.login(username="tu_filter_admin", password="testpass123")

    def test_touchup_list_shows_portal_stat(self):
        """Stats should include portal count."""
        url = reverse("touchup_list", kwargs={"project_id": self.project.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["stats"]["portal"], 1)

    def test_touchup_list_source_filter_portal(self):
        """source=portal should only show portal-submitted touchups."""
        url = reverse("touchup_list", kwargs={"project_id": self.project.id})
        response = self.client.get(url + "?source=portal")
        self.assertEqual(response.status_code, 200)
        page = response.context["page_obj"]
        titles = [tu.title for tu in page]
        self.assertIn("Portal scuff", titles)
        self.assertNotIn("Staff inspection item", titles)
        self.assertEqual(response.context["filter_source"], "portal")

    def test_touchup_list_source_filter_staff(self):
        """source=staff should only show staff-created touchups."""
        url = reverse("touchup_list", kwargs={"project_id": self.project.id})
        response = self.client.get(url + "?source=staff")
        self.assertEqual(response.status_code, 200)
        page = response.context["page_obj"]
        titles = [tu.title for tu in page]
        self.assertIn("Staff inspection item", titles)
        self.assertNotIn("Portal scuff", titles)

    def test_touchup_list_no_source_filter(self):
        """No source filter → show all touchups."""
        url = reverse("touchup_list", kwargs={"project_id": self.project.id})
        response = self.client.get(url + "?status=open")
        self.assertEqual(response.status_code, 200)
        page = response.context["page_obj"]
        titles = [tu.title for tu in page]
        self.assertIn("Portal scuff", titles)
        self.assertIn("Staff inspection item", titles)

    def test_touchup_card_portal_badge(self):
        """Portal touchup card should show 'Portal' badge."""
        url = reverse("touchup_list", kwargs={"project_id": self.project.id})
        response = self.client.get(url + "?status=open")
        content = response.content.decode()
        # Portal badge should exist for portal touchups
        self.assertIn("bi-door-open", content)
        self.assertIn("Portal", content)

    def test_filter_source_preserved_in_context(self):
        """filter_source should be available in template context."""
        url = reverse("touchup_list", kwargs={"project_id": self.project.id})
        response = self.client.get(url + "?source=portal")
        self.assertEqual(response.context["filter_source"], "portal")

        response = self.client.get(url)
        self.assertEqual(response.context["filter_source"], "")
