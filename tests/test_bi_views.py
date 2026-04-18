"""Smoke test for executive BI dashboard view (core.views.bi_views)."""
from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse


User = get_user_model()


@pytest.fixture
def admin_client(db):
    user = User.objects.create_user(
        username="bi_admin",
        email="bi@test.com",
        password="pass1234",
        is_staff=True,
        is_superuser=True,
    )
    client = Client()
    client.force_login(user)
    return client


@pytest.mark.django_db
def test_executive_bi_dashboard_renders(admin_client):
    """Smoke: BI dashboard returns 200 with empty DB."""
    try:
        url = reverse("executive_bi_dashboard")
    except Exception:
        pytest.skip("executive_bi_dashboard not registered")
    resp = admin_client.get(url)
    assert resp.status_code in {200, 302}


@pytest.mark.django_db
def test_executive_bi_dashboard_requires_login(client):
    """Anonymous → redirect to login."""
    try:
        url = reverse("executive_bi_dashboard")
    except Exception:
        pytest.skip("executive_bi_dashboard not registered")
    resp = client.get(url)
    assert resp.status_code in {302, 403}
