"""
Tests for Master Schedule Center
Validates view access control, API data structure, and frontend rendering.
"""
import json
from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from core.models import Project

User = get_user_model()


@pytest.fixture
def admin_user(db):
    """Create an admin user for testing."""
    return User.objects.create_user(
        username="admin_test",
        email="admin@test.com",
        password="testpass123",
        is_staff=True,
        is_superuser=True,
    )


@pytest.fixture
def regular_user(db):
    """Create a regular user without admin privileges."""
    return User.objects.create_user(
        username="regular_test",
        email="regular@test.com",
        password="testpass123",
        is_staff=False,
        is_superuser=False,
    )


@pytest.fixture
def test_project(db, admin_user):
    """Create a test project with schedule dates."""
    project = Project.objects.create(
        name="Test Project Alpha",
        start_date=date.today() - timedelta(days=30),
        end_date=date.today() + timedelta(days=60),
        is_archived=False,
    )
    return project


class TestMasterScheduleAccess:
    """Test access control for Master Schedule Center."""
    
    def test_anonymous_user_redirected(self, client):
        """Anonymous users should be redirected to login."""
        url = reverse("master_schedule_center")
        response = client.get(url)
        assert response.status_code == 302
        assert "/login/" in response.url
    
    def test_regular_user_denied(self, client, regular_user):
        """Regular users without admin/staff privileges should be denied."""
        client.force_login(regular_user)
        url = reverse("master_schedule_center")
        response = client.get(url)
        # Should redirect to dashboard with error message
        assert response.status_code == 302
        assert response.url == reverse("dashboard")
    
    def test_admin_user_allowed(self, client, admin_user):
        """Admin users should access the Master Schedule Center."""
        client.force_login(admin_user)
        url = reverse("master_schedule_center")
        response = client.get(url)
        assert response.status_code == 200
        assert "Master Schedule Center" in response.content.decode()
    
    def test_staff_user_allowed(self, client, db):
        """Staff users should access the Master Schedule Center."""
        staff_user = User.objects.create_user(
            username="staff_test",
            password="testpass123",
            is_staff=True,
            is_superuser=False,
        )
        client.force_login(staff_user)
        url = reverse("master_schedule_center")
        response = client.get(url)
        assert response.status_code == 200


class TestMasterScheduleAPI:
    """Test Master Schedule API data endpoint."""
    
    def test_api_requires_authentication(self, client):
        """API endpoint should require authentication."""
        url = "/api/v1/schedule/master/"
        response = client.get(url)
        # DRF or custom auth: should return 401 or redirect to login
        assert response.status_code in [302, 401, 403]
    
    def test_api_returns_valid_structure(self, client, admin_user, test_project):
        """API should return JSON with projects, events, and metadata."""
        client.force_login(admin_user)
        url = "/api/v1/schedule/master/"
        response = client.get(url)
        
        assert response.status_code == 200
        data = response.json()
        
        # Check structure
        assert "projects" in data
        assert "events" in data
        assert "metadata" in data
        
        # Check metadata
        assert "total_projects" in data["metadata"]
        assert "total_events" in data["metadata"]
        assert "date_range" in data["metadata"]
        
        # Check projects structure if data exists
        if data["projects"]:
            project = data["projects"][0]
            assert "id" in project
            assert "name" in project
            assert "start_date" in project
            assert "end_date" in project
            assert "progress_pct" in project
            assert "color" in project
            assert "pm_name" in project
            assert "client_name" in project
            assert "url" in project
    
    def test_api_includes_active_projects_only(self, client, admin_user, test_project):
        """API should only return active, non-archived projects."""
        # Create archived project
        archived_project = Project.objects.create(
            name="Archived Project",
            start_date=date.today() - timedelta(days=90),
            end_date=date.today() - timedelta(days=30),
            is_archived=True,
        )
        
        client.force_login(admin_user)
        url = "/api/v1/schedule/master/"
        response = client.get(url)
        
        assert response.status_code == 200
        data = response.json()
        
        # Check that archived project is not included
        project_names = {p["name"] for p in data["projects"]}
        assert "Archived Project" not in project_names
        assert test_project.name in project_names


class TestMasterScheduleFrontend:
    """Test frontend rendering and JavaScript functionality."""
    
    def test_page_renders_toggle_buttons(self, client, admin_user):
        """Page should render Gantt and Calendar toggle buttons."""
        client.force_login(admin_user)
        url = reverse("master_schedule_center")
        response = client.get(url)
        
        content = response.content.decode()
        assert "Gantt View" in content
        assert "Calendar View" in content
        assert 'data-view="gantt"' in content
        assert 'data-view="calendar"' in content
    
    def test_page_includes_fullcalendar(self, client, admin_user):
        """Page should include FullCalendar library."""
        client.force_login(admin_user)
        url = reverse("master_schedule_center")
        response = client.get(url)
        
        content = response.content.decode()
        assert "fullcalendar" in content.lower()
        assert 'id="calendar"' in content
    
    def test_page_includes_gantt_container(self, client, admin_user):
        """Page should include Gantt chart container."""
        client.force_login(admin_user)
        url = reverse("master_schedule_center")
        response = client.get(url)
        
        content = response.content.decode()
        assert 'id="ganttView"' in content or 'id="ganttContent"' in content
    
    def test_page_includes_stats_section(self, client, admin_user):
        """Page should include statistics section."""
        client.force_login(admin_user)
        url = reverse("master_schedule_center")
        response = client.get(url)
        
        content = response.content.decode()
        assert "Active Projects" in content or "statProjects" in content
        assert "Upcoming Events" in content or "statEvents" in content
    
    def test_page_includes_legend(self, client, admin_user):
        """Page should include event type legend."""
        client.force_login(admin_user)
        url = reverse("master_schedule_center")
        response = client.get(url)
        
        content = response.content.decode()
        # Check for event type labels
        assert "Invoices" in content or "Invoice" in content
        assert "Change Orders" in content or "Change Order" in content
        assert "Tasks" in content or "Task" in content
        assert "Meetings" in content or "Meeting" in content
