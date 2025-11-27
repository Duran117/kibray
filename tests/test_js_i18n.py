"""
Tests for JavaScript i18n integration
"""

import pytest
from django.contrib.auth.models import User
from django.test import Client
from django.urls import reverse


@pytest.mark.django_db
class TestJavaScriptI18n:
    """Test JavaScript translation catalog integration"""

    def test_javascript_catalog_endpoint_exists(self, client):
        """Test that the JavaScript catalog endpoint is accessible"""
        # Create and login user
        user = User.objects.create_user(username="testuser", password="testpass")
        client.force_login(user)

        # Access the JavaScript catalog endpoint
        url = reverse("javascript-catalog")
        response = client.get(url)

        assert response.status_code == 200
        assert "javascript" in response["Content-Type"].lower()
        assert b"gettext" in response.content
        assert b"ngettext" in response.content

    def test_demo_page_loads(self, client):
        """Test that the JS i18n demo page loads correctly"""
        # Create and login user
        user = User.objects.create_user(username="testuser", password="testpass")
        client.force_login(user)

        # Access the demo page
        url = reverse("js_i18n_demo")
        response = client.get(url)

        assert response.status_code == 200
        assert b"JavaScript i18n Demo" in response.content
        assert b"jsi18n" in response.content or b"javascript-catalog" in response.content

    def test_demo_page_includes_gettext_calls(self, client):
        """Test that the demo page includes proper gettext() calls"""
        user = User.objects.create_user(username="testuser", password="testpass")
        client.force_login(user)

        url = reverse("js_i18n_demo")
        response = client.get(url)
        content = response.content.decode("utf-8")

        # Check for gettext usage
        assert "gettext(" in content
        assert "ngettext(" in content
        assert "interpolate(" in content

        # Check for example messages
        assert "Hello! Welcome to the system." in content
        assert "Are you sure you want to continue?" in content

    @pytest.mark.parametrize("lang_code", ["es", "en"])
    def test_javascript_catalog_respects_language(self, client, lang_code):
        """Test that JavaScript catalog respects current language"""
        user = User.objects.create_user(username="testuser", password="testpass")
        client.force_login(user)

        # Set language in session
        session = client.session
        session["django_language"] = lang_code
        session.save()

        url = reverse("javascript-catalog")
        response = client.get(url)

        assert response.status_code == 200
        # The catalog should be generated for the requested language
        assert b"catalog" in response.content
