"""
Tests for the public proposal approval workflow.

Tests the external client-facing proposal approval flow with no authentication required.
"""

import uuid
from decimal import Decimal

import pytest
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from core.models import CostCode, Estimate, EstimateLine, Profile, Project, Proposal


@pytest.fixture
def client_user(db, django_user_model):
    """Create a client user."""
    return django_user_model.objects.create_user(
        username="client_user", password="testpass123"
    )


@pytest.fixture
def pm_user(db, django_user_model):
    """Create a PM user."""
    user = django_user_model.objects.create_user(
        username="pm_user", password="testpass123"
    )
    Profile.objects.filter(user=user).update(role="pm")
    return user


@pytest.fixture
def project(db):
    """Create a test project."""
    return Project.objects.create(
        name="Test Project",
    start_date=timezone.now().date(),
        client="Test Client",
    )


@pytest.fixture
def cost_code(db):
    """Create a test cost code."""
    return CostCode.objects.create(
    code="01.01", name="Test Item", category="labor"
    )


@pytest.fixture
def estimate_with_proposal(db, project, cost_code):
    """Create an estimate with a proposal."""
    estimate = Estimate.objects.create(
        project=project,
        version=1,
        markup_material=Decimal("10.00"),
        markup_labor=Decimal("15.00"),
        overhead_pct=Decimal("5.00"),
        target_profit_pct=Decimal("10.00"),
        approved=False,
    )
    
    # Add estimate lines
    EstimateLine.objects.create(
        estimate=estimate,
        cost_code=cost_code,
        qty=Decimal("10.00"),
        unit="unit",
        labor_unit_cost=Decimal("100.00"),
        material_unit_cost=Decimal("50.00"),
        other_unit_cost=Decimal("0.00"),
        description="Test line item",
    )
    
    # Create proposal with unique token
    proposal = Proposal.objects.create(
        estimate=estimate,
        client_view_token=uuid.uuid4(),
        issued_at=timezone.now(),
        accepted=False,
    )
    
    return estimate, proposal


@pytest.mark.django_db
class TestProposalPublicView:
    """Test the public proposal view and approval flow."""
    
    def test_valid_token_renders_proposal(self, estimate_with_proposal):
        """Test that a valid token renders the proposal details."""
        estimate, proposal = estimate_with_proposal
        client = Client()
        
        url = reverse("proposal_public", kwargs={"token": str(proposal.client_view_token)})
        response = client.get(url)
        
        assert response.status_code == 200
        assert "Test Project" in response.content.decode()
        assert "Test Client" in response.content.decode()
        assert "Aprobar Presupuesto" in response.content.decode()
        
        # Check that totals are calculated and present
        assert "$" in response.content.decode()
        assert "Total" in response.content.decode()
    
    def test_invalid_token_returns_404(self):
        """Test that an invalid token returns a 404 response."""
        client = Client()
        invalid_token = str(uuid.uuid4())
        
        url = reverse("proposal_public", kwargs={"token": invalid_token})
        response = client.get(url)
        
        assert response.status_code == 404
        assert "no encontrada" in response.content.decode()
    
    def test_approve_proposal_updates_state(self, estimate_with_proposal):
        """Test that approving a proposal updates Proposal and Estimate state."""
        estimate, proposal = estimate_with_proposal
        client = Client()
        
        url = reverse("proposal_public", kwargs={"token": str(proposal.client_view_token)})
        
        # POST approval
        response = client.post(url, {"action": "approve"})
        
        assert response.status_code == 200
        
        # Refresh from DB
        proposal.refresh_from_db()
        estimate.refresh_from_db()
        
        assert proposal.accepted is True
        assert proposal.accepted_at is not None
        assert estimate.approved is True
        
        # Check success message in response
        assert "aprobación" in response.content.decode()
    
    def test_reject_proposal_registers_feedback(self, estimate_with_proposal):
        """Test that rejecting a proposal registers client feedback."""
        estimate, proposal = estimate_with_proposal
        client = Client()
        
        url = reverse("proposal_public", kwargs={"token": str(proposal.client_view_token)})
        
        feedback_text = "Please reduce the price by 10%"
        
        # POST rejection with feedback
        response = client.post(url, {"action": "reject", "feedback": feedback_text})
        
        assert response.status_code == 200
        
        # Refresh from DB
        proposal.refresh_from_db()
        
        assert proposal.client_comment == feedback_text
        assert proposal.accepted is False
        assert proposal.accepted_at is None
        
        # Check message in response
        assert "comentarios" in response.content.decode()
    
    def test_approved_proposal_shows_banner(self, estimate_with_proposal):
        """Test that an already approved proposal shows the approved banner."""
        estimate, proposal = estimate_with_proposal
        
        # Approve the proposal
        proposal.accepted = True
        proposal.accepted_at = timezone.now()
        proposal.save()
        
        client = Client()
        url = reverse("proposal_public", kwargs={"token": str(proposal.client_view_token)})
        response = client.get(url)
        
        assert response.status_code == 200
        assert "Presupuesto Aprobado" in response.content.decode()
        # Buttons should not be present (or disabled)
    
    def test_line_items_displayed_correctly(self, estimate_with_proposal, cost_code):
        """Test that estimate line items are displayed correctly in the template."""
        estimate, proposal = estimate_with_proposal
        
        # Add another line
        EstimateLine.objects.create(
            estimate=estimate,
            cost_code=cost_code,
            qty=Decimal("5.00"),
            unit="unit",
            labor_unit_cost=Decimal("200.00"),
            material_unit_cost=Decimal("100.00"),
            other_unit_cost=Decimal("50.00"),
            description="Second line item",
        )
        
        client = Client()
        url = reverse("proposal_public", kwargs={"token": str(proposal.client_view_token)})
        response = client.get(url)
        
        content = response.content.decode()
        
        # Check both line items are present
        assert "Test line item" in content
        assert "Second line item" in content
        assert "01.01" in content  # Cost code
        
        # Check quantities (European format with comma)
        assert "10,00" in content
        assert "5,00" in content
    
    def test_markups_and_overhead_displayed(self, estimate_with_proposal):
        """Test that markups, overhead, and profit are displayed correctly."""
        estimate, proposal = estimate_with_proposal
        
        client = Client()
        url = reverse("proposal_public", kwargs={"token": str(proposal.client_view_token)})
        response = client.get(url)
        
        content = response.content.decode()
        
        # Check that markup percentages are shown (European format with comma)
        assert "10,00%" in content  # markup_material
        assert "15,00%" in content  # markup_labor
        assert "5,00%" in content   # overhead_pct
        
        # Check labels
        assert "Markup Materiales" in content
        assert "Markup Mano de Obra" in content
        assert "Overhead" in content
        assert "Ganancia" in content
    
    def test_no_authentication_required(self, estimate_with_proposal):
        """Test that the view is accessible without authentication."""
        estimate, proposal = estimate_with_proposal
        
        # Use a fresh client with no session
        client = Client()
        url = reverse("proposal_public", kwargs={"token": str(proposal.client_view_token)})
        
        response = client.get(url)
        
        # Should render successfully without redirect to login
        assert response.status_code == 200
        assert "login" not in response.url if hasattr(response, 'url') else True
