"""
Tests for Module 29: Pre-Task Library (ActivityTemplate)
Tests cover Q29.1-Q29.7: Search, Versioning, Factory methods
"""

import pytest
from django.contrib.auth.models import User

from core.models import ActivityTemplate


@pytest.mark.django_db
class TestActivityTemplateSearch:
    """Tests for fuzzy search functionality (Q29.1-Q29.3)"""

    def test_search_by_name(self):
        """Test search finds templates by name"""
        user = User.objects.create_user("testuser", "test@test.com", "pass")

        ActivityTemplate.objects.create(name="Wall Preparation", category="PREP", created_by=user)
        ActivityTemplate.objects.create(name="Interior Painting", category="PAINT", created_by=user)

        results = ActivityTemplate.search("Wall")
        assert results.count() == 1
        assert results.first().name == "Wall Preparation"

    def test_search_by_description(self):
        """Test search finds templates by description"""
        user = User.objects.create_user("testuser", "test@test.com", "pass")

        ActivityTemplate.objects.create(
            name="Prep Work", category="PREP", description="Surface preparation for painting", created_by=user
        )

        results = ActivityTemplate.search("Surface")
        assert results.count() == 1
        assert "Surface" in results.first().description

    def test_search_by_tips(self):
        """Test search finds templates by tips"""
        user = User.objects.create_user("testuser", "test@test.com", "pass")

        ActivityTemplate.objects.create(
            name="Staining", category="STAIN", tips="Always use grain filler first", created_by=user
        )

        results = ActivityTemplate.search("grain filler")
        assert results.count() == 1
        assert "grain filler" in results.first().tips

    def test_search_with_category_filter(self):
        """Test search can filter by category"""
        user = User.objects.create_user("testuser", "test@test.com", "pass")

        ActivityTemplate.objects.create(name="Paint Prep", category="PREP", created_by=user)
        ActivityTemplate.objects.create(name="Paint Application", category="PAINT", created_by=user)

        results = ActivityTemplate.search("Paint", category="PREP")
        assert results.count() == 1
        assert results.first().category == "PREP"

    def test_search_excludes_inactive(self):
        """Test search only returns active templates by default"""
        user = User.objects.create_user("testuser", "test@test.com", "pass")

        ActivityTemplate.objects.create(name="Active Template", category="PREP", is_active=True, created_by=user)
        ActivityTemplate.objects.create(name="Inactive Template", category="PREP", is_active=False, created_by=user)

        results = ActivityTemplate.search("Template")
        assert results.count() == 1
        assert results.first().name == "Active Template"

    def test_search_case_insensitive(self):
        """Test search is case-insensitive"""
        user = User.objects.create_user("testuser", "test@test.com", "pass")

        ActivityTemplate.objects.create(name="SURFACE PREP", category="PREP", created_by=user)

        results = ActivityTemplate.search("surface")
        assert results.count() == 1

        results2 = ActivityTemplate.search("SURFACE")
        assert results2.count() == 1


@pytest.mark.django_db
class TestActivityTemplateVersioning:
    """Tests for versioning system (Q29.4)"""

    def test_default_version_is_one(self):
        """Test new templates start at version 1"""
        user = User.objects.create_user("testuser", "test@test.com", "pass")

        template = ActivityTemplate.objects.create(name="Test Template", category="PREP", created_by=user)

        assert template.version == 1
        assert template.is_latest_version is True
        assert template.parent_template is None

    def test_create_new_version(self):
        """Test creating a new version of a template"""
        user = User.objects.create_user("testuser", "test@test.com", "pass")
        editor = User.objects.create_user("editor", "editor@test.com", "pass")

        original = ActivityTemplate.objects.create(
            name="Original Template", category="PREP", description="Original description", created_by=user
        )

        new_version = original.create_new_version(updated_by=editor, version_notes="Updated steps and materials")

        # Check new version
        assert new_version.version == 2
        assert new_version.is_latest_version is True
        assert new_version.parent_template == original
        assert new_version.created_by == editor
        assert new_version.version_notes == "Updated steps and materials"

        # Check original is marked as old
        original.refresh_from_db()
        assert original.is_latest_version is False

    def test_version_copies_all_fields(self):
        """Test new version copies all relevant fields"""
        user = User.objects.create_user("testuser", "test@test.com", "pass")

        original = ActivityTemplate.objects.create(
            name="Complex Template",
            category="PAINT",
            description="Test description",
            time_estimate=5.5,
            steps=["Step 1", "Step 2"],
            materials_list=["Paint", "Brush"],
            tools_list=["Roller"],
            tips="Important tips",
            common_errors="Common mistakes",
            difficulty_level="intermediate",
            completion_points=25,
            created_by=user,
        )

        new_version = original.create_new_version(updated_by=user)

        assert new_version.name == original.name
        assert new_version.category == original.category
        assert new_version.description == original.description
        assert new_version.time_estimate == original.time_estimate
        assert new_version.steps == ["Step 1", "Step 2"]
        assert new_version.materials_list == ["Paint", "Brush"]
        assert new_version.tips == original.tips
        assert new_version.difficulty_level == original.difficulty_level

    def test_multiple_versions(self):
        """Test creating multiple versions"""
        user = User.objects.create_user("testuser", "test@test.com", "pass")

        v1 = ActivityTemplate.objects.create(name="Test", category="PREP", created_by=user)

        v2 = v1.create_new_version(updated_by=user, version_notes="Version 2")
        v3 = v2.create_new_version(updated_by=user, version_notes="Version 3")

        assert v3.version == 3
        assert v3.parent_template == v1  # Points to original
        assert v3.is_latest_version is True

        v1.refresh_from_db()
        v2.refresh_from_db()
        assert v1.is_latest_version is False
        assert v2.is_latest_version is False

    def test_search_returns_only_latest_versions(self):
        """Test search returns only latest versions by default"""
        user = User.objects.create_user("testuser", "test@test.com", "pass")

        v1 = ActivityTemplate.objects.create(name="Test Template", category="PREP", created_by=user)
        v2 = v1.create_new_version(updated_by=user)

        results = ActivityTemplate.search("Test")
        assert results.count() == 1
        assert results.first() == v2
        assert results.first().version == 2


@pytest.mark.django_db
class TestActivityTemplateFactories:
    """Tests for factory methods (Q29.5-Q29.7)"""

    def test_create_prep_template(self):
        """Test PREP template factory"""
        user = User.objects.create_user("testuser", "test@test.com", "pass")

        template = ActivityTemplate.create_prep_template(name="Surface Prep", creator=user)

        assert template.name == "Surface Prep"
        assert template.category == "PREP"
        assert template.created_by == user
        assert template.time_estimate == 4.0
        assert template.difficulty_level == "beginner"
        assert "Clear and protect area" in template.steps
        assert "Drop cloths" in template.materials_list
        assert "Sandpaper" in template.tools_list

    def test_create_paint_template(self):
        """Test PAINT template factory"""
        user = User.objects.create_user("testuser", "test@test.com", "pass")

        template = ActivityTemplate.create_paint_template(name="Interior Paint", creator=user)

        assert template.name == "Interior Paint"
        assert template.category == "PAINT"
        assert template.created_by == user
        assert template.time_estimate == 6.0
        assert template.difficulty_level == "intermediate"
        assert "Cut in edges and corners" in template.steps
        assert "Paint" in template.materials_list
        assert "Brushes" in template.tools_list

    def test_create_cleanup_template(self):
        """Test CLEANUP template factory"""
        user = User.objects.create_user("testuser", "test@test.com", "pass")

        template = ActivityTemplate.create_cleanup_template(name="Site Cleanup", creator=user)

        assert template.name == "Site Cleanup"
        assert template.category == "CLEANUP"
        assert template.created_by == user
        assert template.time_estimate == 2.0
        assert template.difficulty_level == "beginner"
        assert "Remove all tape and protection" in template.steps
        assert "Trash bags" in template.materials_list
        assert "Vacuum" in template.tools_list

    def test_factory_allows_overrides(self):
        """Test factory methods accept custom parameters"""
        user = User.objects.create_user("testuser", "test@test.com", "pass")

        template = ActivityTemplate.create_prep_template(
            name="Custom Prep",
            creator=user,
            time_estimate=8.0,
            difficulty_level="advanced",
            tips="Special technique required",
        )

        assert template.time_estimate == 8.0
        assert template.difficulty_level == "advanced"
        assert template.tips == "Special technique required"
        # Other defaults still apply
        assert template.category == "PREP"

    def test_factory_creates_searchable_templates(self):
        """Test factory-created templates are searchable"""
        user = User.objects.create_user("testuser", "test@test.com", "pass")

        ActivityTemplate.create_prep_template("Wall Prep", creator=user)
        ActivityTemplate.create_paint_template("Wall Paint", creator=user)
        ActivityTemplate.create_cleanup_template("Final Cleanup", creator=user)

        results = ActivityTemplate.search("Wall")
        assert results.count() == 2

        results_prep = ActivityTemplate.search("Wall", category="PREP")
        assert results_prep.count() == 1

    def test_factory_templates_start_at_version_one(self):
        """Test factory-created templates have correct version"""
        user = User.objects.create_user("testuser", "test@test.com", "pass")

        template = ActivityTemplate.create_prep_template("Test", creator=user)

        assert template.version == 1
        assert template.is_latest_version is True
        assert template.parent_template is None


@pytest.mark.django_db
class TestActivityTemplateIntegration:
    """Integration tests combining multiple features"""

    def test_search_factory_and_version_workflow(self):
        """Test complete workflow: factory -> search -> version"""
        user = User.objects.create_user("testuser", "test@test.com", "pass")
        editor = User.objects.create_user("editor", "editor@test.com", "pass")

        # Create with factory
        v1 = ActivityTemplate.create_prep_template("Room Prep", creator=user)

        # Search finds it
        results = ActivityTemplate.search("Room")
        assert results.count() == 1
        assert results.first() == v1

        # Create new version
        v2 = v1.create_new_version(updated_by=editor, version_notes="Improved steps")

        # Search now returns v2 only
        results = ActivityTemplate.search("Room")
        assert results.count() == 1
        assert results.first() == v2
        assert results.first().version == 2

    def test_string_representation_with_version(self):
        """Test __str__ shows version number"""
        user = User.objects.create_user("testuser", "test@test.com", "pass")

        v1 = ActivityTemplate.objects.create(name="Test", category="PREP", created_by=user)
        v2 = v1.create_new_version(updated_by=user)

        assert str(v1) == "Preparation - Test"
        assert str(v2) == "Preparation - Test (v2)"
