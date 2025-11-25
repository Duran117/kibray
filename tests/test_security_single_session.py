import pytest
from django.contrib.auth import get_user_model
from django.test import Client

User = get_user_model()

@pytest.mark.django_db
def test_single_active_session_enforced():
    # Create user
    user = User.objects.create_user(username='one', password='pwd123', email='one@example.com')

    # First client logs in
    c1 = Client()
    assert c1.login(username='one', password='pwd123')
    r1 = c1.get('/api/v1/notifications/')
    assert r1.status_code == 200

    # Second client logs in (should revoke first session)
    c2 = Client()
    assert c2.login(username='one', password='pwd123')
    r2 = c2.get('/api/v1/notifications/')
    assert r2.status_code == 200

    # First client should now be unauthorized for protected endpoints
    r1_after = c1.get('/api/v1/notifications/')
    assert r1_after.status_code in (401, 403)
