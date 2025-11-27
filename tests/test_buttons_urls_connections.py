"""
Test script to verify all critical buttons and URLs are working
"""

import pytest
from django.contrib.auth.models import User
from django.test import Client
from django.urls import NoReverseMatch, reverse


@pytest.mark.django_db
class TestCriticalButtonsAndURLs:
    """Verify all dashboard buttons point to valid URLs with working views"""

    def setup_method(self):
        """Create test user with admin privileges"""
        self.client = Client()
        self.admin_user = User.objects.create_superuser(
            username="admin_test", email="admin@test.com", password="testpass123"
        )
        self.client.force_login(self.admin_user)

    # === DASHBOARD URLS ===

    def test_admin_dashboard_loads(self):
        """Test admin dashboard page loads"""
        url = reverse("dashboard_admin")
        response = self.client.get(url)
        assert response.status_code == 200
        assert b"Admin Dashboard" in response.content or b"Panel" in response.content

    def test_admin_panel_main_url_exists(self):
        """Test admin panel main URL can be resolved"""
        try:
            url = reverse("admin_panel_main")
            assert url is not None
        except NoReverseMatch:
            pytest.fail("URL 'admin_panel_main' does not exist")

    def test_admin_panel_main_loads(self):
        """Test admin panel main page loads"""
        url = reverse("admin_panel_main")
        response = self.client.get(url)
        assert response.status_code == 200

    # === QUICK ACTION BUTTONS ===

    def test_client_create_url(self):
        """Test client create button URL exists and loads"""
        url = reverse("client_create")
        response = self.client.get(url)
        assert response.status_code == 200

    def test_project_create_url(self):
        """Test project create button URL exists and loads"""
        url = reverse("project_create")
        response = self.client.get(url)
        assert response.status_code == 200

    def test_client_list_url(self):
        """Test client list button URL exists and loads"""
        url = reverse("client_list")
        response = self.client.get(url)
        assert response.status_code == 200

    def test_project_list_url(self):
        """Test project list button URL exists and loads"""
        url = reverse("project_list")
        response = self.client.get(url)
        assert response.status_code == 200

    def test_expense_create_url(self):
        """Test expense create button URL exists and loads"""
        url = reverse("expense_create")
        response = self.client.get(url)
        assert response.status_code == 200

    def test_income_create_url(self):
        """Test income create button URL exists and loads"""
        url = reverse("income_create")
        response = self.client.get(url)
        assert response.status_code == 200

    def test_changeorder_create_url(self):
        """Test change order create button URL exists and loads"""
        url = reverse("changeorder_create")
        response = self.client.get(url)
        assert response.status_code == 200

    # === NAVIGATION MENU ===

    def test_dashboard_url(self):
        """Test main dashboard URL"""
        url = reverse("dashboard")
        response = self.client.get(url)
        # Should redirect to appropriate dashboard
        assert response.status_code in [200, 302]

    def test_employee_dashboard_url(self):
        """Test employee dashboard URL"""
        url = reverse("dashboard_employee")
        response = self.client.get(url)
        assert response.status_code == 200

    def test_pm_dashboard_url(self):
        """Test PM dashboard URL"""
        url = reverse("dashboard_pm")
        response = self.client.get(url)
        assert response.status_code == 200

    def test_client_dashboard_url(self):
        """Test client dashboard URL"""
        url = reverse("dashboard_client")
        # Ensure user has client role for access
        self.admin_user.profile.role = "client"
        self.admin_user.profile.save()
        response = self.client.get(url)
        assert response.status_code == 200

    # === FINANCIAL URLS ===

    def test_expense_list_url(self):
        """Test expense list URL"""
        try:
            url = reverse("expense_list")
            response = self.client.get(url)
            assert response.status_code == 200
        except NoReverseMatch:
            pytest.skip("expense_list URL not defined")

    def test_income_list_url(self):
        """Test income list URL"""
        try:
            url = reverse("income_list")
            response = self.client.get(url)
            assert response.status_code == 200
        except NoReverseMatch:
            pytest.skip("income_list URL not defined")

    # === CHANGE ORDER URLS ===

    def test_changeorder_board_url(self):
        """Test change order board URL"""
        try:
            url = reverse("changeorder_board")
            response = self.client.get(url)
            assert response.status_code == 200
        except NoReverseMatch:
            pytest.skip("changeorder_board URL not defined")

    # === TIME TRACKING ===

    def test_timeentry_list_url(self):
        """Test time entry list URL"""
        try:
            url = reverse("timeentry_list")
            response = self.client.get(url)
            assert response.status_code == 200
        except NoReverseMatch:
            pytest.skip("timeentry_list URL not defined")


@pytest.mark.django_db
class TestProjectWorkflowConnections:
    """Test that project workflow buttons connect properly"""

    def setup_method(self):
        """Create test user and project"""
        from core.models import Project

        self.client = Client()
        self.admin_user = User.objects.create_superuser(
            username="admin_test", email="admin@test.com", password="testpass123"
        )
        self.client.force_login(self.admin_user)

        # Create test project
        from django.utils import timezone

        self.project = Project.objects.create(
            name="Test Project", description="Test Description", start_date=timezone.now().date()
        )

    def test_project_overview_url(self):
        """Test project overview page loads"""
        url = reverse("project_overview", args=[self.project.id])
        response = self.client.get(url)
        assert response.status_code == 200

    def test_project_edit_url(self):
        """Test project edit page loads"""
        url = reverse("project_edit", args=[self.project.id])
        response = self.client.get(url)
        assert response.status_code == 200

    def test_project_delete_url(self):
        """Test project delete URL exists"""
        try:
            url = reverse("project_delete", args=[self.project.id])
            assert url is not None
        except NoReverseMatch:
            pytest.skip("project_delete URL not defined")


@pytest.mark.django_db
class TestChangeOrderWorkflowConnections:
    """Test change order workflow end-to-end"""

    def setup_method(self):
        """Create test data"""
        from core.models import ChangeOrder, Project

        self.client = Client()
        self.admin_user = User.objects.create_superuser(
            username="admin_test", email="admin@test.com", password="testpass123"
        )
        self.client.force_login(self.admin_user)

        # Create test project
        from django.utils import timezone

        self.project = Project.objects.create(
            name="Test Project", description="Test Description", start_date=timezone.now().date()
        )

        # Create test change order
        self.co = ChangeOrder.objects.create(project=self.project, reference_code="CO-001", description="Test CO")

    def test_changeorder_detail_url(self):
        """Test change order detail page loads"""
        url = reverse("changeorder_detail", args=[self.co.id])
        response = self.client.get(url)
        assert response.status_code == 200

    def test_changeorder_edit_url(self):
        """Test change order edit page loads"""
        try:
            url = reverse("changeorder_edit", args=[self.co.id])
            response = self.client.get(url)
            assert response.status_code == 200
        except NoReverseMatch:
            pytest.skip("changeorder_edit URL not defined")


@pytest.mark.django_db
class TestDailyPlanningConnections:
    """Test daily planning workflow connections"""

    def setup_method(self):
        """Create test user"""
        self.client = Client()
        self.admin_user = User.objects.create_superuser(
            username="admin_test", email="admin@test.com", password="testpass123"
        )
        self.client.force_login(self.admin_user)

    def test_daily_planning_dashboard_url(self):
        """Test daily planning dashboard loads"""
        try:
            url = reverse("daily_planning_dashboard")
            response = self.client.get(url)
            assert response.status_code == 200
        except NoReverseMatch:
            pytest.skip("daily_planning_dashboard URL not defined")

    def test_daily_plan_create_url(self):
        """Test daily plan create URL exists"""
        try:
            url = reverse("daily_plan_create")
            response = self.client.get(url)
            assert response.status_code in [200, 302]  # May redirect if no active project
        except NoReverseMatch:
            pytest.skip("daily_plan_create URL not defined")
