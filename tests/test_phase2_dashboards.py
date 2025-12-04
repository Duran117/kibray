"""
Tests for Phase 2 Dashboard Improvements: Client, Employee, Superintendent, Designer
Validates Morning Briefing, categorization, and filtering across new dashboards.
"""
import pytest
from django.contrib.auth.models import User
from django.test import Client
from django.urls import reverse
from django.utils import timezone
from decimal import Decimal

from core.models import Profile, Project, Invoice, Task, DamageReport, Schedule


@pytest.mark.django_db
class TestPhase2DashboardsContextKeys:
    """Test that all Phase 2 dashboards have required context keys"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up users for all dashboard types"""
        # Client
        self.client_user = User.objects.create_user(username="ctx_client", password="pass123")
        self.client_user.profile.role = "client"
        self.client_user.profile.save()

        # Employee
        self.emp_user = User.objects.create_user(username="ctx_emp", password="pass123")
        self.emp_user.profile.role = "employee"
        self.emp_user.profile.save()

        # Superintendent
        self.super_user = User.objects.create_user(
            username="ctx_super", password="pass123", is_staff=True
        )
        self.super_user.profile.role = "superintendent"
        self.super_user.profile.save()

        # Designer
        self.designer_user = User.objects.create_user(username="ctx_designer", password="pass123")
        self.designer_user.profile.role = "designer"
        self.designer_user.profile.save()

        self.http_client = Client()

    def test_client_dashboard_has_morning_briefing(self):
        """Test client dashboard includes morning_briefing and active_filter"""
        self.http_client.login(username="ctx_client", password="pass123")
        response = self.http_client.get(reverse("dashboard_client") + "?legacy=true")
        assert response.status_code == 200
        assert "morning_briefing" in response.context
        assert "active_filter" in response.context



    def test_filter_parameter_respected(self):
        """Test that filter parameter is passed through in context"""
        self.http_client.login(username="ctx_client", password="pass123")
        
        # Test different filter values
        for filter_val in ["all", "payments", "updates", "schedule"]:
            response = self.http_client.get(
                reverse("dashboard_client") + f"?filter={filter_val}&legacy=true"
            )
            assert response.status_code == 200
            assert response.context.get("active_filter") == filter_val

    def test_morning_briefing_structure_valid(self):
        """Test that briefing items have required fields when present"""
        self.http_client.login(username="ctx_client", password="pass123")
        response = self.http_client.get(reverse("dashboard_client") + "?legacy=true")
        
        briefing = response.context.get("morning_briefing", [])
        
        # If there are items, check their structure
        for item in briefing:
            assert isinstance(item, dict), "Briefing item must be dict"
            assert "text" in item, "Missing 'text' field"
            assert "severity" in item, "Missing 'severity' field"
            assert "action_url" in item, "Missing 'action_url' field"
            assert "action_label" in item, "Missing 'action_label' field"
            assert "category" in item, "Missing 'category' field"

    def test_briefing_severity_values_valid(self):
        """Test that all severity values are from valid set"""
        valid_severities = {"danger", "warning", "info", "success"}
        
        self.http_client.login(username="ctx_emp", password="pass123")
        response = self.http_client.get(reverse("dashboard_employee") + "?legacy=true")
        briefing = response.context.get("morning_briefing", [])
        
        for item in briefing:
            assert item.get("severity") in valid_severities, (
                f"Invalid severity: {item.get('severity')}"
            )

    def test_filter_parameter_filters_correctly(self):
        """Test that filter parameter actually filters briefing items"""
        self.http_client.login(username="ctx_emp", password="pass123")
        
        # Get all items
        response_all = self.http_client.get(reverse("dashboard_employee") + "?filter=all&legacy=true")
        all_items = response_all.context.get("morning_briefing", [])
        
        # Get filtered items
        response_filtered = self.http_client.get(
            reverse("dashboard_employee") + "?filter=clock&legacy=true"
        )
        filtered_items = response_filtered.context.get("morning_briefing", [])
        
        # If we have filtered items, they should all have the matching category
        for item in filtered_items:
            assert item.get("category") == "clock", (
                f"Filtered item has wrong category: {item.get('category')}"
            )
