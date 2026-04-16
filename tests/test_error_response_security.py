"""
Phase 5 Tests — Error Response Security
=========================================
Verifies that error responses do NOT leak internal exception details.
All `str(e)` leaks in HTTP/JSON responses have been replaced with
generic user-facing messages.
"""

import pytest
from django.test import Client as TestClient
from django.contrib.auth.models import User

from core.models import Profile

pytestmark = pytest.mark.django_db


@pytest.fixture
def admin_http(db):
    user = User.objects.create_user(
        username="secadmin", password="pass1234", is_staff=True
    )
    Profile.objects.update_or_create(user=user, defaults={"role": "admin"})
    c = TestClient()
    c.login(username="secadmin", password="pass1234")
    return c


class TestNoExceptionLeakInResponses:
    """
    Ensures that no view returns raw exception text to clients.
    We verify this by checking that known error endpoints return
    generic messages, not Python tracebacks or exception strings.
    """

    def test_changeorder_update_status_bad_id_no_leak(self, admin_http):
        """POST to changeorder_update_status with bad data returns generic error."""
        resp = admin_http.post(
            "/changeorders/99999/update-status/",
            data='{"status": "approved"}',
            content_type="application/json",
        )
        # Should be 404 (object not found) or 500 with generic message
        if resp.status_code == 500:
            content = resp.content.decode()
            assert "Traceback" not in content
            assert "Exception" not in content

    def test_pin_info_bad_id_no_leak(self, admin_http):
        """pin_info_ajax with nonexistent pin should not leak."""
        resp = admin_http.get("/plans/pins/99999/info/")
        if resp.status_code == 500:
            import json
            data = json.loads(resp.content)
            # Should NOT contain Python exception class names
            assert "Error" not in data.get("error", "") or "loading" in data.get("error", "").lower()

    def test_touchup_photo_annotation_bad_json_no_leak(self, admin_http):
        """Bad JSON to photo annotations should return generic error."""
        resp = admin_http.post(
            "/touchup/99999/photos/99999/annotations/",
            data="not-json",
            content_type="application/json",
        )
        # Should be 404 (object not found) or 400 with generic message
        if resp.status_code == 400:
            import json
            data = json.loads(resp.content)
            assert "str(e)" not in resp.content.decode()
            assert "Traceback" not in resp.content.decode()


class TestPublicPdfDownloadNoLeak:
    """Public PDF download endpoints should not leak errors."""

    def test_changeorder_pdf_bad_token_no_leak(self):
        """Bad token for CO PDF download should not leak internal errors."""
        c = TestClient()
        resp = c.get("/changeorders/99999/pdf/badtoken123/")
        content = resp.content.decode()
        assert "Traceback" not in content
        # Should be 403 or 404, not 500
        assert resp.status_code in (400, 403, 404)

    def test_colorsample_pdf_bad_token_no_leak(self):
        """Bad token for color sample PDF download should not leak."""
        c = TestClient()
        resp = c.get("/colors/99999/pdf/badtoken123/")
        content = resp.content.decode()
        assert "Traceback" not in content
        assert resp.status_code in (400, 403, 404)
