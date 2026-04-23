"""
Tests for core/security_decorators.py

Covers all 8 public units:
- require_role
- ajax_login_required
- ajax_csrf_protect
- require_project_access
- rate_limit
- sanitize_json_input
- require_post_with_csrf
- is_staffish

Uses RequestFactory for fast, isolated decorator testing.
"""
import json

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.middleware import SessionMiddleware
from django.core.cache import cache
from django.http import HttpResponse, JsonResponse
from django.test import RequestFactory

from core.security_decorators import (
    ajax_csrf_protect,
    ajax_login_required,
    is_staffish,
    rate_limit,
    require_post_with_csrf,
    require_project_access,
    require_role,
    sanitize_json_input,
)

User = get_user_model()


# ---------- Helpers ----------

def _attach_session(request):
    """Attach a session and messages to a RequestFactory request."""
    SessionMiddleware(lambda r: None).process_request(request)
    request.session.save()
    setattr(request, "_messages", FallbackStorage(request))
    return request


def _ok_view(request, *args, **kwargs):
    return HttpResponse("OK")


# ---------- Fixtures ----------

@pytest.fixture
def factory():
    return RequestFactory()


@pytest.fixture
def anon_request(factory):
    req = factory.get("/")
    req.user = AnonymousUser()
    return _attach_session(req)


@pytest.fixture
def admin(db):
    u = User.objects.create_user(
        username="dec_admin", password="x", is_staff=True, is_superuser=True
    )
    return u


@pytest.fixture
def staff(db):
    return User.objects.create_user(
        username="dec_staff", password="x", is_staff=True, is_superuser=False
    )


def _make_user_with_role(username, role):
    """Create user and force-set Profile.role, invalidating the cached relation."""
    from core.models import Profile
    u = User.objects.create_user(username=username, password="x")
    Profile.objects.update_or_create(user=u, defaults={"role": role})
    # Invalidate cached OneToOne reverse accessor so user.profile reflects new role
    u.refresh_from_db()
    return u


@pytest.fixture
def employee(db):
    return _make_user_with_role("dec_emp", "employee")


@pytest.fixture
def pm(db):
    return _make_user_with_role("dec_pm", "project_manager")


@pytest.fixture
def client_user(db):
    return _make_user_with_role("dec_client", "client")


@pytest.fixture
def project(db):
    from core.models import Project
    return Project.objects.create(name="DecTest Project")


# ---------- require_role ----------

class TestRequireRole:
    def test_superuser_always_passes(self, factory, admin):
        view = require_role("admin")(_ok_view)
        req = factory.get("/")
        req.user = admin
        resp = view(req)
        assert resp.status_code == 200

    def test_staff_always_passes(self, factory, staff):
        view = require_role("admin")(_ok_view)
        req = factory.get("/")
        req.user = staff
        resp = view(req)
        assert resp.status_code == 200

    def test_matching_role_passes(self, factory, employee):
        view = require_role("employee", "admin")(_ok_view)
        req = factory.get("/")
        req.user = employee
        resp = view(req)
        assert resp.status_code == 200

    def test_wrong_role_denied(self, factory, client_user):
        view = require_role("admin", "project_manager")(_ok_view)
        req = factory.get("/")
        req.user = client_user
        resp = view(req)
        assert resp.status_code == 403

    def test_wrong_role_ajax_returns_json_403(self, factory, client_user):
        view = require_role("admin")(_ok_view)
        req = factory.get("/", HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        req.user = client_user
        resp = view(req)
        assert resp.status_code == 403
        assert isinstance(resp, JsonResponse)
        body = json.loads(resp.content)
        assert "error" in body

    def test_anonymous_redirected_by_login_required(self, factory):
        view = require_role("admin")(_ok_view)
        req = factory.get("/")
        req.user = AnonymousUser()
        resp = view(req)
        # login_required redirects (302)
        assert resp.status_code == 302


# ---------- ajax_login_required ----------

class TestAjaxLoginRequired:
    def test_authenticated_passes(self, factory, employee):
        view = ajax_login_required(_ok_view)
        req = factory.get("/")
        req.user = employee
        resp = view(req)
        assert resp.status_code == 200

    def test_anonymous_returns_401_json(self, factory):
        view = ajax_login_required(_ok_view)
        req = factory.get("/")
        req.user = AnonymousUser()
        resp = view(req)
        assert resp.status_code == 401
        assert isinstance(resp, JsonResponse)
        assert json.loads(resp.content) == {"error": "Authentication required"}


# ---------- ajax_csrf_protect ----------

class TestAjaxCsrfProtect:
    def test_passes_through_when_no_csrf_error(self, factory, employee):
        view = ajax_csrf_protect(_ok_view)
        req = factory.get("/")
        req.user = employee
        # GET requests bypass CSRF
        resp = view(req)
        assert resp.status_code == 200


# ---------- require_project_access ----------

class TestRequireProjectAccess:
    def _build(self, factory, user, project_id):
        view = require_project_access("project_id")(_ok_view)
        req = factory.get("/")
        req.user = user
        return view, req

    def test_superuser_passes(self, factory, admin, project):
        view, req = self._build(factory, admin, project.id)
        resp = view(req, project_id=project.id)
        assert resp.status_code == 200

    def test_staff_passes(self, factory, staff, project):
        view, req = self._build(factory, staff, project.id)
        resp = view(req, project_id=project.id)
        assert resp.status_code == 200

    def test_pm_passes(self, factory, pm, project):
        view, req = self._build(factory, pm, project.id)
        resp = view(req, project_id=project.id)
        assert resp.status_code == 200

    def test_client_without_access_denied(self, factory, client_user, project):
        view, req = self._build(factory, client_user, project.id)
        resp = view(req, project_id=project.id)
        assert resp.status_code == 403

    def test_client_with_explicit_access_passes(self, factory, client_user, project):
        from core.models import ClientProjectAccess
        ClientProjectAccess.objects.create(user=client_user, project=project, role="client")
        view, req = self._build(factory, client_user, project.id)
        resp = view(req, project_id=project.id)
        assert resp.status_code == 200

    def test_employee_denied(self, factory, employee, project):
        view, req = self._build(factory, employee, project.id)
        resp = view(req, project_id=project.id)
        assert resp.status_code == 403

    def test_missing_project_id_returns_400(self, factory, admin):
        view, req = self._build(factory, admin, None)
        resp = view(req)  # no project_id kwarg
        assert resp.status_code == 400

    def test_nonexistent_project_returns_404(self, factory, admin):
        from django.http import Http404
        view, req = self._build(factory, admin, 999999)
        # RequestFactory bypasses middleware; Http404 propagates as exception.
        # In production, Django middleware converts this to a 404 response.
        with pytest.raises(Http404):
            view(req, project_id=999999)

    def test_ajax_denied_returns_json(self, factory, client_user, project):
        view = require_project_access("project_id")(_ok_view)
        req = factory.get("/", HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        req.user = client_user
        resp = view(req, project_id=project.id)
        assert resp.status_code == 403
        assert isinstance(resp, JsonResponse)


# ---------- rate_limit ----------

class TestRateLimit:
    def setup_method(self):
        cache.clear()

    def teardown_method(self):
        cache.clear()

    def test_under_limit_allows(self, factory, employee):
        view = rate_limit(key_prefix="rl_test_a", max_requests=3, window_seconds=60)(_ok_view)
        req = factory.get("/")
        req.user = employee
        for _ in range(3):
            resp = view(req)
            assert resp.status_code == 200

    def test_over_limit_blocks(self, factory, employee):
        view = rate_limit(key_prefix="rl_test_b", max_requests=2, window_seconds=60)(_ok_view)
        req = factory.get("/")
        req.user = employee
        view(req)
        view(req)
        resp = view(req)
        assert resp.status_code == 403

    def test_over_limit_ajax_returns_429_json(self, factory, employee):
        view = rate_limit(key_prefix="rl_test_c", max_requests=1, window_seconds=60)(_ok_view)
        req = factory.get("/", HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        req.user = employee
        view(req)
        resp = view(req)
        assert resp.status_code == 429
        assert isinstance(resp, JsonResponse)

    def test_anonymous_uses_ip(self, factory):
        view = rate_limit(key_prefix="rl_test_d", max_requests=1, window_seconds=60)(_ok_view)
        req = factory.get("/", REMOTE_ADDR="1.2.3.4")
        req.user = AnonymousUser()
        resp1 = view(req)
        resp2 = view(req)
        assert resp1.status_code == 200
        assert resp2.status_code == 403


# ---------- sanitize_json_input ----------

class TestSanitizeJsonInput:
    def test_valid_json_sanitizes_strings(self, factory, employee):
        captured = {}

        def view(request):
            captured["data"] = getattr(request, "sanitized_json", None)
            return HttpResponse("OK")

        wrapped = sanitize_json_input(view)
        payload = {"name": "<script>alert(1)</script>", "nested": {"key": "<b>x</b>"}}
        req = factory.post(
            "/",
            data=json.dumps(payload),
            content_type="application/json",
        )
        req.user = employee
        resp = wrapped(req)
        assert resp.status_code == 200
        assert captured["data"]["name"] == "&lt;script&gt;alert(1)&lt;/script&gt;"
        assert captured["data"]["nested"]["key"] == "&lt;b&gt;x&lt;/b&gt;"

    def test_invalid_json_returns_400(self, factory, employee):
        wrapped = sanitize_json_input(_ok_view)
        req = factory.post("/", data="not-json{", content_type="application/json")
        req.user = employee
        resp = wrapped(req)
        assert resp.status_code == 400

    def test_get_request_passes_through(self, factory, employee):
        wrapped = sanitize_json_input(_ok_view)
        req = factory.get("/")
        req.user = employee
        resp = wrapped(req)
        assert resp.status_code == 200

    def test_list_values_sanitized(self, factory, employee):
        captured = {}

        def view(request):
            captured["data"] = request.sanitized_json
            return HttpResponse("OK")

        wrapped = sanitize_json_input(view)
        payload = {"items": ["<x>", "<y>"]}
        req = factory.post("/", data=json.dumps(payload), content_type="application/json")
        req.user = employee
        wrapped(req)
        assert captured["data"]["items"] == ["&lt;x&gt;", "&lt;y&gt;"]


# ---------- require_post_with_csrf ----------

class TestRequirePostWithCsrf:
    def test_get_method_rejected(self, factory, employee):
        view = require_post_with_csrf(_ok_view)
        req = factory.get("/")
        req.user = employee
        resp = view(req)
        assert resp.status_code == 405


# ---------- is_staffish ----------

class TestIsStaffish:
    def test_superuser_is_staffish(self, admin):
        assert is_staffish(admin) is True

    def test_staff_is_staffish(self, staff):
        assert is_staffish(staff) is True

    def test_pm_is_staffish(self, pm):
        assert is_staffish(pm) is True

    def test_employee_not_staffish(self, employee):
        assert is_staffish(employee) is False

    def test_client_not_staffish(self, client_user):
        assert is_staffish(client_user) is False

    def test_user_without_profile_not_staffish(self, db):
        from core.models import Profile
        u = User.objects.create_user(username="np_user", password="x")
        Profile.objects.filter(user=u).delete()
        # Re-fetch to clear cached relation
        u.refresh_from_db()
        assert is_staffish(u) is False
