"""
Tests for Module 29: Pre-Task Library API
Tests fuzzy search, category filtering, bulk import, usage tracking, and favorites.
"""

import json

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient

from core.models import Project, TaskTemplate

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    return User.objects.create_user(username="testuser", password="testpass123", email="test@example.com")


@pytest.fixture
def project(db, user):
    from datetime import date

    return Project.objects.create(name="Test Project", client="Test Client", start_date=date.today())


@pytest.fixture
def templates(db, user):
    """Create sample templates for testing"""
    templates = [
        TaskTemplate.objects.create(
            title="Prepare walls for painting",
            description="Sand and prime all interior walls",
            category="preparation",
            default_priority="high",
            estimated_hours=8.0,
            tags=["sanding", "priming", "walls"],
            checklist=["Check surface condition", "Sand walls", "Apply primer"],
            sop_reference="https://example.com/sop/wall-prep",
            created_by=user,
            usage_count=15,
            is_favorite=True,
        ),
        TaskTemplate.objects.create(
            title="Paint bedroom walls",
            description="Apply two coats of latex paint to bedroom",
            category="painting",
            default_priority="medium",
            estimated_hours=6.0,
            tags=["painting", "latex", "bedroom"],
            checklist=["First coat", "Second coat", "Touch ups"],
            created_by=user,
            usage_count=10,
        ),
        TaskTemplate.objects.create(
            title="Final inspection",
            description="Complete final walkthrough and inspection",
            category="inspection",
            default_priority="high",
            estimated_hours=2.0,
            tags=["inspection", "quality", "final"],
            checklist=["Check all rooms", "Document issues", "Client approval"],
            sop_reference="https://example.com/sop/final-inspection",
            created_by=user,
            usage_count=5,
        ),
        TaskTemplate.objects.create(
            title="Clean work area",
            description="Remove debris and clean all surfaces",
            category="cleanup",
            default_priority="low",
            estimated_hours=3.0,
            tags=["cleanup", "debris"],
            checklist=["Remove trash", "Sweep floors", "Wipe surfaces"],
            created_by=user,
            usage_count=20,
            is_favorite=True,
        ),
    ]
    return templates


@pytest.mark.django_db
class TestTaskTemplateFuzzySearch:
    """Test fuzzy search with trigram similarity"""

    def test_fuzzy_search_by_title(self, api_client, user, templates):
        """Test fuzzy search matches title with typos"""
        api_client.force_authenticate(user=user)

        # Search for "wall" - should match "Prepare walls for painting" and "Paint bedroom walls"
        response = api_client.get("/api/v1/task-templates/fuzzy_search/", {"q": "wall"})

        assert response.status_code == 200
        assert response.data["count"] >= 1
        # Should find templates with "wall" in title
        titles = [r["title"] for r in response.data["results"]]
        assert any("wall" in t.lower() for t in titles)

    def test_fuzzy_search_by_description(self, api_client, user, templates):
        """Test fuzzy search matches description content"""
        api_client.force_authenticate(user=user)

        response = api_client.get("/api/v1/task-templates/fuzzy_search/", {"q": "latex paint"})

        assert response.status_code == 200
        assert response.data["count"] >= 1

    def test_fuzzy_search_minimum_length(self, api_client, user, templates):
        """Test fuzzy search requires minimum 2 characters"""
        api_client.force_authenticate(user=user)

        response = api_client.get("/api/v1/task-templates/fuzzy_search/", {"q": "a"})

        assert response.status_code == 400
        assert "error" in response.data

    def test_fuzzy_search_limit(self, api_client, user, templates):
        """Test fuzzy search respects limit parameter"""
        api_client.force_authenticate(user=user)

        response = api_client.get("/api/v1/task-templates/fuzzy_search/", {"q": "wall", "limit": 1})

        assert response.status_code == 200
        assert len(response.data["results"]) <= 1


@pytest.mark.django_db
class TestTaskTemplateFiltering:
    """Test category, tag, favorite, and SOP filtering"""

    def test_filter_by_category(self, api_client, user, templates):
        """Test filtering by category"""
        api_client.force_authenticate(user=user)

        response = api_client.get("/api/v1/task-templates/", {"category": "preparation"})

        assert response.status_code == 200
        results = response.data.get("results", response.data)
        assert len(results) >= 1
        assert all(r["category"] == "preparation" for r in results)

    def test_filter_by_tags(self, api_client, user, templates):
        """Test filtering by tags"""
        api_client.force_authenticate(user=user)

        response = api_client.get("/api/v1/task-templates/", {"tags": "inspection"})

        assert response.status_code == 200
        results = response.data.get("results", response.data)
        assert len(results) >= 1
        assert all("inspection" in r["tags"] for r in results)

    def test_filter_by_multiple_tags(self, api_client, user, templates):
        """Test filtering by multiple comma-separated tags"""
        api_client.force_authenticate(user=user)

        response = api_client.get("/api/v1/task-templates/", {"tags": "painting,latex"})

        assert response.status_code == 200
        results = response.data.get("results", response.data)
        # Should have both tags
        for result in results:
            assert "painting" in result["tags"] and "latex" in result["tags"]

    def test_filter_by_favorites(self, api_client, user, templates):
        """Test filtering by is_favorite"""
        api_client.force_authenticate(user=user)

        response = api_client.get("/api/v1/task-templates/", {"is_favorite": "true"})

        assert response.status_code == 200
        results = response.data.get("results", response.data)
        assert len(results) >= 2  # We created 2 favorites
        assert all(r["is_favorite"] for r in results)

    def test_filter_by_has_sop(self, api_client, user, templates):
        """Test filtering by has_sop"""
        api_client.force_authenticate(user=user)

        response = api_client.get("/api/v1/task-templates/", {"has_sop": "true"})

        assert response.status_code == 200
        results = response.data.get("results", response.data)
        assert len(results) >= 2  # We created 2 with SOP
        assert all(r["sop_reference"] for r in results)


@pytest.mark.django_db
class TestTaskTemplateSorting:
    """Test ordering by usage_count, last_used, etc."""

    def test_default_ordering_by_usage(self, api_client, user, templates):
        """Test default ordering is by usage_count descending"""
        api_client.force_authenticate(user=user)

        response = api_client.get("/api/v1/task-templates/")

        assert response.status_code == 200
        results = response.data.get("results", response.data)

        # Should be ordered by usage_count desc
        usage_counts = [r["usage_count"] for r in results]
        assert usage_counts == sorted(usage_counts, reverse=True)

    def test_order_by_last_used(self, api_client, user, templates):
        """Test ordering by last_used"""
        api_client.force_authenticate(user=user)

        # Update last_used for one template
        template = templates[0]
        template.last_used = timezone.now()
        template.save()

        response = api_client.get("/api/v1/task-templates/", {"ordering": "-last_used"})

        assert response.status_code == 200


@pytest.mark.django_db
class TestTaskTemplateUsageTracking:
    """Test automatic usage tracking when creating tasks"""

    def test_create_task_increments_usage(self, api_client, user, project, templates):
        """Test creating task increments usage_count and updates last_used"""
        api_client.force_authenticate(user=user)

        template = templates[0]
        initial_count = template.usage_count
        initial_last_used = template.last_used

        response = api_client.post(f"/api/v1/task-templates/{template.id}/create_task/", {"project_id": project.id})

        assert response.status_code == 201
        assert "id" in response.data

        # Refresh template from DB
        template.refresh_from_db()
        assert template.usage_count == initial_count + 1
        assert template.last_used is not None
        if initial_last_used:
            assert template.last_used > initial_last_used


@pytest.mark.django_db
class TestTaskTemplateFavorites:
    """Test favorite toggle functionality"""

    def test_toggle_favorite(self, api_client, user, templates):
        """Test toggling is_favorite status"""
        api_client.force_authenticate(user=user)

        template = templates[1]  # Not initially favorite
        assert not template.is_favorite

        # Toggle ON
        response = api_client.post(f"/api/v1/task-templates/{template.id}/toggle_favorite/")

        assert response.status_code == 200
        assert response.data["is_favorite"] is True

        # Toggle OFF
        response = api_client.post(f"/api/v1/task-templates/{template.id}/toggle_favorite/")

        assert response.status_code == 200
        assert response.data["is_favorite"] is False


@pytest.mark.django_db
class TestTaskTemplateBulkImport:
    """Test bulk import from JSON and CSV"""

    def test_bulk_import_json(self, api_client, user):
        """Test bulk import with JSON format"""
        api_client.force_authenticate(user=user)

        templates_data = [
            {
                "title": "New Template 1",
                "description": "Description 1",
                "category": "preparation",
                "default_priority": "high",
                "estimated_hours": 5.0,
                "tags": ["tag1", "tag2"],
                "checklist": ["item1", "item2"],
            },
            {
                "title": "New Template 2",
                "description": "Description 2",
                "category": "painting",
                "default_priority": "medium",
                "estimated_hours": 3.0,
                "tags": ["tag3"],
                "checklist": ["item3"],
            },
        ]

        response = api_client.post(
            "/api/v1/task-templates/bulk_import/", {"format": "json", "templates": templates_data}, format="json"
        )

        assert response.status_code == 201
        assert response.data["created"] == 2
        assert response.data["failed"] == 0

    def test_bulk_import_validation_errors(self, api_client, user):
        """Test bulk import with validation errors"""
        api_client.force_authenticate(user=user)

        templates_data = [
            {
                "title": "Valid Template",
                "description": "Valid description",
                "category": "preparation",
                "default_priority": "high",
            },
            {
                # Missing required title
                "description": "Missing title",
                "category": "painting",
            },
        ]

        response = api_client.post(
            "/api/v1/task-templates/bulk_import/", {"format": "json", "templates": templates_data}, format="json"
        )

        # Should create valid ones, report errors for invalid
        assert response.data["created"] >= 1
        assert response.data["failed"] >= 1
        assert len(response.data["errors"]) >= 1


@pytest.mark.django_db
class TestTaskTemplateSerializer:
    """Test serializer includes new fields"""

    def test_serializer_includes_category(self, api_client, user, templates):
        """Test serializer includes category and category_display"""
        api_client.force_authenticate(user=user)

        response = api_client.get(f"/api/v1/task-templates/{templates[0].id}/")

        assert response.status_code == 200
        assert "category" in response.data
        assert "category_display" in response.data
        assert response.data["category"] == "preparation"

    def test_serializer_includes_usage_stats(self, api_client, user, templates):
        """Test serializer includes usage_count and last_used"""
        api_client.force_authenticate(user=user)

        response = api_client.get(f"/api/v1/task-templates/{templates[0].id}/")

        assert response.status_code == 200
        assert "usage_count" in response.data
        assert "last_used" in response.data
        assert response.data["usage_count"] == 15

    def test_serializer_includes_favorite(self, api_client, user, templates):
        """Test serializer includes is_favorite"""
        api_client.force_authenticate(user=user)

        response = api_client.get(f"/api/v1/task-templates/{templates[0].id}/")

        assert response.status_code == 200
        assert "is_favorite" in response.data
        assert response.data["is_favorite"] is True

    def test_serializer_includes_sop(self, api_client, user, templates):
        """Test serializer includes sop_reference"""
        api_client.force_authenticate(user=user)

        response = api_client.get(f"/api/v1/task-templates/{templates[0].id}/")

        assert response.status_code == 200
        assert "sop_reference" in response.data
        assert response.data["sop_reference"] == "https://example.com/sop/wall-prep"
