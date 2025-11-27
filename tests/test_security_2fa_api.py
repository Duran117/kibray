import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from core.models import TwoFactorProfile

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    return User.objects.create_user(username="twofa", password="pass123", email="twofa@example.com")


@pytest.mark.django_db
class Test2FATOTPAPI:
    def test_setup_enable_and_login_with_otp(self, api_client, user, monkeypatch):
        # Authenticate to set up 2FA
        api_client.force_authenticate(user=user)
        # Setup: get secret and otpauth_uri
        res_setup = api_client.post("/api/v1/2fa/setup/", {}, format="json")
        assert res_setup.status_code == 200
        secret = res_setup.data["secret"]
        # Compute current OTP using the same algorithm as model
        prof = TwoFactorProfile.get_or_create_for_user(user)
        prof.secret = secret
        # Enable 2FA by sending OTP
        current_otp = TwoFactorProfile._totp(secret)  # type: ignore[attr-defined]
        res_enable = api_client.post("/api/v1/2fa/enable/", {"otp": current_otp}, format="json")
        assert res_enable.status_code == 200
        # Logout API client (stop force auth)
        api_client.force_authenticate(user=None)

        # Attempt login without OTP should fail now
        res_login_no_otp = api_client.post(
            "/api/v1/auth/login/", {"username": "twofa", "password": "pass123"}, format="json"
        )
        assert res_login_no_otp.status_code in (400, 401)

        # Login with OTP should succeed
        otp = TwoFactorProfile._totp(secret)  # type: ignore[attr-defined]
        res_login = api_client.post(
            "/api/v1/auth/login/", {"username": "twofa", "password": "pass123", "otp": otp}, format="json"
        )
        assert res_login.status_code == 200
        assert "access" in res_login.data and "refresh" in res_login.data

    def test_login_without_2fa_still_works(self, api_client, db):
        u = User.objects.create_user(username="plain", password="pw12345")
        res = api_client.post("/api/v1/auth/login/", {"username": "plain", "password": "pw12345"}, format="json")
        assert res.status_code == 200
        assert "access" in res.data
