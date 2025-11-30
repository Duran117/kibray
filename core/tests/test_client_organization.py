"""
Tests for Navigation System Phase 1: Client Organization and Contact models.
"""

from decimal import Decimal

import pytest
from django.contrib.auth.models import User

from core.models import (
    ClientContact,
    ClientOrganization,
    Project,
)


@pytest.fixture
def user(db):
    """Create a test user."""
    return User.objects.create_user(
        username="testuser",
        email="test@example.com",
        first_name="Test",
        last_name="User",
        password="testpass123",
    )


@pytest.fixture
def user2(db):
    """Create another test user."""
    return User.objects.create_user(
        username="testuser2",
        email="test2@example.com",
        first_name="Second",
        last_name="User",
        password="testpass123",
    )


@pytest.fixture
def organization(db, user):
    """Create a test client organization."""
    return ClientOrganization.objects.create(
        name="New West Partners",
        legal_name="New West Partners LLC",
        tax_id="12-3456789",
        billing_address="123 Main St",
        billing_city="Denver",
        billing_state="CO",
        billing_zip="80202",
        billing_email="billing@newwestpartners.com",
        billing_phone="303-555-1234",
        payment_terms_days=30,
        is_active=True,
        created_by=user,
    )


@pytest.fixture
def client_contact(db, user, organization):
    """Create a test client contact."""
    return ClientContact.objects.create(
        user=user,
        organization=organization,
        role="project_lead",
        job_title="Project Director",
        department="Construction",
        phone_direct="303-555-1111",
        phone_mobile="303-555-2222",
        preferred_contact_method="email",
        can_approve_change_orders=True,
        can_view_financials=True,
        can_create_tasks=True,
        can_approve_colors=False,
        receive_daily_reports=True,
        receive_invoice_notifications=True,
        is_active=True,
    )


@pytest.fixture
def project(db, organization, client_contact):
    """Create a test project with organization and contact."""
    from datetime import date

    project = Project(
        name="Test Project",
        start_date=date.today(),
        billing_organization=organization,
        project_lead=client_contact,
        budget_total=Decimal("100000.00"),
    )
    project.save()
    return project


class TestClientOrganization:
    """Tests for ClientOrganization model."""

    def test_create_organization(self, organization):
        """Test creating a client organization."""
        assert organization.pk is not None
        assert organization.name == "New West Partners"
        assert organization.billing_email == "billing@newwestpartners.com"
        assert organization.payment_terms_days == 30

    def test_organization_str(self, organization):
        """Test organization string representation."""
        assert str(organization) == "New West Partners"

    def test_organization_active_projects_count(self, organization, project):
        """Test counting active projects."""
        count = organization.active_projects_count
        assert count >= 0

    def test_organization_total_contract_value(self, organization, project):
        """Test total contract value calculation."""
        total = organization.total_contract_value
        assert total == Decimal("100000.00")

    def test_organization_outstanding_balance(self, organization, project):
        """Test outstanding balance calculation."""
        balance = organization.outstanding_balance
        assert balance >= Decimal("0.00")


class TestClientContact:
    """Tests for ClientContact model."""

    def test_create_contact(self, client_contact):
        """Test creating a client contact."""
        assert client_contact.pk is not None
        assert client_contact.role == "project_lead"
        assert client_contact.job_title == "Project Director"

    def test_contact_str_with_organization(self, client_contact):
        """Test contact string representation with organization."""
        expected = "Test User (New West Partners)"
        assert str(client_contact) == expected

    def test_contact_str_without_organization(self, db, user2):
        """Test contact string representation without organization."""
        contact = ClientContact.objects.create(
            user=user2,
            organization=None,
            role="observer",
        )
        expected = "Second User"
        assert str(contact) == expected

    def test_contact_permission_flags(self, client_contact):
        """Test default permission flags."""
        assert client_contact.can_approve_change_orders is True
        assert client_contact.can_view_financials is True
        assert client_contact.can_create_tasks is True
        assert client_contact.can_approve_colors is False

    def test_assigned_projects(self, client_contact, project):
        """Test assigned_projects property."""
        projects = list(client_contact.assigned_projects)
        assert len(projects) == 1
        assert projects[0] == project

    def test_observable_projects(self, db, client_contact, project, user2):
        """Test observable_projects property."""
        # Create observer contact
        observer = ClientContact.objects.create(
            user=user2,
            role="observer",
        )
        project.observers.add(observer)

        # Check observable projects
        projects = list(observer.observable_projects)
        assert len(projects) == 1
        assert projects[0] == project

    def test_has_project_access_as_lead(self, client_contact, project):
        """Test project access for project lead."""
        assert client_contact.has_project_access(project) is True

    def test_has_project_access_as_observer(self, db, project, user2):
        """Test project access for observer."""
        observer = ClientContact.objects.create(
            user=user2,
            role="observer",
        )
        project.observers.add(observer)
        assert observer.has_project_access(project) is True

    def test_no_project_access(self, db, project, user2):
        """Test no project access for unrelated contact."""
        unrelated = ClientContact.objects.create(
            user=user2,
            role="observer",
        )
        assert unrelated.has_project_access(project) is False


class TestProjectBillingEntity:
    """Tests for Project.get_billing_entity method."""

    def test_billing_entity_from_organization(self, project):
        """Test billing entity from organization."""
        entity = project.get_billing_entity()
        assert entity is not None
        assert entity["type"] == "organization"
        assert entity["name"] == "New West Partners"
        assert entity["email"] == "billing@newwestpartners.com"
        assert entity["payment_terms"] == 30

    def test_billing_entity_from_contact(self, db, client_contact):
        """Test billing entity from contact when no organization."""
        from datetime import date

        project = Project(
            name="Individual Project",
            start_date=date.today(),
            billing_organization=None,
            project_lead=client_contact,
        )
        project.save()

        entity = project.get_billing_entity()
        assert entity is not None
        assert entity["type"] == "individual"
        assert entity["name"] == "Test User"
        assert entity["email"] == "test@example.com"
        assert entity["payment_terms"] == 30

    def test_billing_entity_none(self, db):
        """Test billing entity when neither organization nor contact set."""
        from datetime import date

        project = Project(
            name="No Billing Project",
            start_date=date.today(),
        )
        project.save()

        entity = project.get_billing_entity()
        assert entity is None

    def test_project_observers(self, project, user2, db):
        """Test adding observers to project."""
        observer = ClientContact.objects.create(
            user=user2,
            role="observer",
        )
        project.observers.add(observer)

        assert observer in project.observers.all()
        assert project in observer.observable_projects
