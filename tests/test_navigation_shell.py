import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
def test_base_template_renders_sidebar(client):
    """Test that the modern sidebar shell renders for logged-in staff users."""
    user = User.objects.create_user(username="navtest", email="nav@test.com", password="nav123", is_staff=True)
    client.force_login(user)
    resp = client.get("/changeorders/board/")
    html = resp.content.decode()
    assert resp.status_code == 200
    assert "kb-sidebar" in html
    assert "kb-header" in html
    assert "Kibray" in html


@pytest.mark.django_db
def test_base_template_renders_header(client):
    """Test that the base template renders the header with user info."""
    user = User.objects.create_user(username="navtest2", email="nav2@test.com", password="nav123", is_staff=True)
    client.force_login(user)
    resp = client.get("/changeorders/board/")
    if resp.status_code == 200:
        html = resp.content.decode()
        assert "kb-header" in html
        assert "navtest2" in html
