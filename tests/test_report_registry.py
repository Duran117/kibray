"""
Tests for the report registry + async generation pipeline.

Covers:
  - Pure registry behaviour (register / get / list / unregister)
  - Permission gate (role + superuser/staff bypass)
  - Adapter auto-registration (5 built-in PDFs)
  - Async task happy path (mock generator -> file written + Notification)
  - Async task error paths (unknown report, permission denied, generator
    failure with retries exhausted, missing user)

The PDF generators themselves are NOT exercised here — they are slow and
covered by their own integration tests. We register a tiny synchronous
adapter that returns a known byte string, so we can assert the storage
+ notification side-effects deterministically.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.core.files.storage import default_storage

from core.services.report_registry import (
    ReportNotFound,
    ReportPermissionDenied,
    StaffRoles,
    get,
    list_reports,
    register,
    render,
    resolve_user_role,
    unregister,
)

User = get_user_model()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def fake_report():
    """Register a deterministic adapter for the duration of a single test."""
    name = "__test_fake_report__"

    def _gen(*, payload: bytes = b"hello", **_):
        return payload

    register(
        name,
        generator=_gen,
        content_type="application/octet-stream",
        file_extension="bin",
        allowed_roles=StaffRoles,
        description="Test-only adapter.",
    )
    yield name
    unregister(name)


@pytest.fixture
def admin_user(db):
    return User.objects.create_user(
        username="report_admin", password="x", is_staff=True
    )


@pytest.fixture
def plain_user(db):
    return User.objects.create_user(username="report_plain", password="x")


# ---------------------------------------------------------------------------
# Registry behaviour
# ---------------------------------------------------------------------------


class TestRegistry:
    def test_register_and_get_round_trip(self, fake_report):
        spec = get(fake_report)
        assert spec.name == fake_report
        assert spec.file_extension == "bin"
        assert spec.content_type == "application/octet-stream"

    def test_get_unknown_raises(self):
        with pytest.raises(ReportNotFound):
            get("no_such_report__xyz")

    def test_list_reports_includes_built_ins(self):
        # `report_generators` auto-registers on import.
        from core.services import report_generators  # noqa: F401

        names = {s.name for s in list_reports()}
        for expected in {
            "estimate_pdf",
            "contract_pdf",
            "signed_contract_pdf",
            "changeorder_pdf",
            "colorsample_pdf",
        }:
            assert expected in names, f"{expected} should be registered"

    def test_register_rejects_blank_name(self):
        with pytest.raises(ValueError):
            register("   ", generator=lambda **_: b"", content_type="x", file_extension="x")

    def test_register_rejects_non_callable(self):
        with pytest.raises(TypeError):
            register("bad", generator="not_callable", content_type="x", file_extension="x")  # type: ignore[arg-type]

    def test_double_register_same_generator_is_idempotent(self):
        gen = lambda **_: b"ok"  # noqa: E731
        register("__dup__", generator=gen, content_type="x", file_extension="x")
        register("__dup__", generator=gen, content_type="x", file_extension="x")
        unregister("__dup__")

    def test_double_register_different_generator_raises(self):
        register("__dup2__", generator=lambda **_: b"a", content_type="x", file_extension="x")
        with pytest.raises(ValueError):
            register(
                "__dup2__", generator=lambda **_: b"b", content_type="x", file_extension="x"
            )
        unregister("__dup2__")


# ---------------------------------------------------------------------------
# Permission gate
# ---------------------------------------------------------------------------


class TestPermissions:
    def test_superuser_bypasses_role_check(self, fake_report, db):
        su = User.objects.create_superuser(username="su", email="su@x.x", password="x")
        assert render(fake_report, user=su) == b"hello"

    def test_staff_bypasses_role_check(self, fake_report, admin_user):
        assert render(fake_report, user=admin_user) == b"hello"

    def test_plain_user_denied(self, fake_report, plain_user):
        with pytest.raises(ReportPermissionDenied):
            render(fake_report, user=plain_user)

    def test_resolve_user_role_handles_missing_profile(self, plain_user):
        role, su, staff = resolve_user_role(plain_user)
        # Profile may be auto-created with default 'employee' role; either way
        # the helper must NOT crash and must report non-staff/non-superuser.
        assert role in (None, "employee")
        assert su is False
        assert staff is False

    def test_resolve_user_role_none(self):
        assert resolve_user_role(None) == (None, False, False)

    def test_kwargs_passed_through(self, fake_report, admin_user):
        assert render(fake_report, user=admin_user, payload=b"world") == b"world"


# ---------------------------------------------------------------------------
# Async task — generate_report_async
# ---------------------------------------------------------------------------


class TestGenerateReportAsync:
    def test_happy_path_writes_file_and_notifies(self, fake_report, admin_user):
        from core.models import Notification
        from core.tasks import generate_report_async

        result = generate_report_async(fake_report, admin_user.id, payload=b"abc123")

        assert result["status"] == "success"
        assert result["report"] == fake_report
        assert result["size_bytes"] == 6
        assert result["path"].startswith(f"reports/{admin_user.id}/")
        assert result["path"].endswith(".bin")

        # File on disk
        assert default_storage.exists(result["path"])
        with default_storage.open(result["path"], "rb") as fh:
            assert fh.read() == b"abc123"

        # Notification
        notif = Notification.objects.get(pk=result["notification_id"])
        assert notif.user == admin_user
        assert notif.title == "Report ready"
        assert notif.related_object_type == "report"

        # Cleanup
        default_storage.delete(result["path"])

    def test_unknown_report_creates_error_notification(self, admin_user):
        from core.models import Notification
        from core.tasks import generate_report_async

        result = generate_report_async("__no_such_report__", admin_user.id)
        assert result == {
            "status": "error",
            "error": "report_not_found",
            "report": "__no_such_report__",
        }
        assert Notification.objects.filter(
            user=admin_user, title="Report unavailable"
        ).exists()

    def test_permission_denied_creates_notification(self, fake_report, plain_user):
        from core.models import Notification
        from core.tasks import generate_report_async

        result = generate_report_async(fake_report, plain_user.id)
        assert result["status"] == "error"
        assert result["error"] == "permission_denied"
        assert Notification.objects.filter(
            user=plain_user, title="Report denied"
        ).exists()

    def test_missing_user_returns_error_without_notification(self, fake_report):
        from core.models import Notification
        from core.tasks import generate_report_async

        before = Notification.objects.count()
        result = generate_report_async(fake_report, 9_999_999)
        assert result == {
            "status": "error",
            "error": "user_not_found",
            "user_id": 9_999_999,
        }
        assert Notification.objects.count() == before

    def test_generator_failure_after_retries_creates_notification(self, admin_user):
        """
        With CELERY_TASK_ALWAYS_EAGER + EAGER_PROPAGATES, retries surface
        as MaxRetriesExceededError immediately. We register a generator
        that always raises and verify the failure path notifies the user.
        """
        from core.models import Notification
        from core.services.report_registry import register, unregister
        from core.tasks import generate_report_async

        name = "__always_fails__"

        def _boom(**_):
            raise RuntimeError("kaboom")

        register(
            name,
            generator=_boom,
            content_type="text/plain",
            file_extension="txt",
            allowed_roles=StaffRoles,
        )
        try:
            # Patch retry to short-circuit (eager mode raises on retry()).
            with patch.object(generate_report_async, "retry") as mock_retry:
                mock_retry.side_effect = generate_report_async.MaxRetriesExceededError("done")
                result = generate_report_async(name, admin_user.id)
            assert result["status"] == "error"
            assert result["error"] == "generation_failed"
            assert Notification.objects.filter(
                user=admin_user, title="Report failed"
            ).exists()
        finally:
            unregister(name)
