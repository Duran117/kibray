"""Unit tests for core/access_decorators.py and core/api/permissions.py.

Phase 9 Commit B: locks in the contract for the decorator layer and the
DRF permission layer that delegate to core.access.
"""
from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.test import RequestFactory

from core import access
from core.access_decorators import (
    require_admin,
    require_can_view_financials,
    require_internal,
    require_project_access,
    require_role,
    require_staffish,
)
from core.api.permissions import (
    CanAccessProject,
    IsAdminOrPM,
    IsOwner,
    IsOwnerOrPM,
    IsOwnerOrPMOrSuperintendent,
    IsOwnerOrReadOnly,
)
from core.models import (
    ClientProjectAccess,
    Project,
    ProjectManagerAssignment,
)

User = get_user_model()
rf = RequestFactory()


def _mk_user(username, *, role=None, is_staff=False, is_superuser=False):
    u = User.objects.create_user(
        username=username, password="x",
        is_staff=is_staff, is_superuser=is_superuser,
    )
    if role:
        u.profile.role = role
        u.profile.save()
    return u


def _request(user, method="get", path="/"):
    req = getattr(rf, method)(path)
    req.user = user
    return req


# ─────────────── Fixtures ───────────────
@pytest.fixture
def admin_user():
    return _mk_user("dec_admin", role=access.ROLE_ADMIN, is_staff=True, is_superuser=True)


@pytest.fixture
def pm_user():
    return _mk_user("dec_pm", role=access.ROLE_PM)


@pytest.fixture
def owner_user():
    return _mk_user("dec_owner", role=access.ROLE_OWNER)


@pytest.fixture
def super_user():
    return _mk_user("dec_super", role=access.ROLE_SUPERINTENDENT)


@pytest.fixture
def employee_user():
    return _mk_user("dec_emp", role=access.ROLE_EMPLOYEE)


@pytest.fixture
def client_user():
    return _mk_user("dec_client", role=access.ROLE_CLIENT)


@pytest.fixture
def project():
    return Project.objects.create(name="Dec Project")


# ─────────────── Decorator tests ───────────────
class TestRequireAdmin:
    def test_admin_passes(self, admin_user):
        @require_admin
        def view(request):
            return HttpResponse("ok")
        resp = view(_request(admin_user))
        assert resp.status_code == 200

    def test_pm_denied(self, pm_user):
        @require_admin
        def view(request):
            return HttpResponse("ok")
        with pytest.raises(PermissionDenied):
            view(_request(pm_user))

    def test_anonymous_redirects_to_login(self):
        @require_admin
        def view(request):
            return HttpResponse("ok")
        resp = view(_request(AnonymousUser()))
        # login_required → 302 redirect
        assert resp.status_code == 302


class TestRequireRole:
    def test_matching_role_passes(self, pm_user):
        @require_role(access.ROLE_PM)
        def view(request):
            return HttpResponse("ok")
        resp = view(_request(pm_user))
        assert resp.status_code == 200

    def test_non_matching_role_denied(self, employee_user):
        @require_role(access.ROLE_PM)
        def view(request):
            return HttpResponse("ok")
        with pytest.raises(PermissionDenied):
            view(_request(employee_user))

    def test_admin_always_passes(self, admin_user):
        @require_role(access.ROLE_PM)
        def view(request):
            return HttpResponse("ok")
        resp = view(_request(admin_user))
        assert resp.status_code == 200

    def test_unknown_role_raises_at_decoration(self):
        with pytest.raises(ValueError):
            @require_role("bogus_role")
            def view(request):
                return HttpResponse("ok")

    def test_multi_role(self, employee_user, pm_user):
        @require_role(access.ROLE_PM, access.ROLE_EMPLOYEE)
        def view(request):
            return HttpResponse("ok")
        assert view(_request(employee_user)).status_code == 200
        assert view(_request(pm_user)).status_code == 200


class TestRequireInternal:
    def test_pm_passes(self, pm_user):
        @require_internal
        def view(request):
            return HttpResponse("ok")
        assert view(_request(pm_user)).status_code == 200

    def test_client_denied(self, client_user):
        @require_internal
        def view(request):
            return HttpResponse("ok")
        with pytest.raises(PermissionDenied):
            view(_request(client_user))

    def test_employee_denied(self, employee_user):
        @require_internal
        def view(request):
            return HttpResponse("ok")
        with pytest.raises(PermissionDenied):
            view(_request(employee_user))


class TestRequireStaffish:
    def test_admin_passes(self, admin_user):
        @require_staffish
        def view(request):
            return HttpResponse("ok")
        assert view(_request(admin_user)).status_code == 200

    def test_employee_denied(self, employee_user):
        @require_staffish
        def view(request):
            return HttpResponse("ok")
        with pytest.raises(PermissionDenied):
            view(_request(employee_user))


class TestRequireProjectAccess:
    def test_admin_can_access(self, admin_user, project):
        @require_project_access()
        def view(request, project_id, project=None):
            assert project is not None
            assert project.pk == project_id
            return HttpResponse("ok")
        assert view(_request(admin_user), project_id=project.pk).status_code == 200

    def test_pm_unassigned_denied(self, pm_user, project):
        @require_project_access()
        def view(request, project_id, project=None):
            return HttpResponse("ok")
        with pytest.raises(PermissionDenied):
            view(_request(pm_user), project_id=project.pk)

    def test_pm_assigned_passes(self, pm_user, project):
        ProjectManagerAssignment.objects.create(project=project, pm=pm_user, role="pm")

        @require_project_access()
        def view(request, project_id, project=None):
            return HttpResponse("ok")
        assert view(_request(pm_user), project_id=project.pk).status_code == 200

    def test_client_no_access_denied(self, client_user, project):
        @require_project_access()
        def view(request, project_id, project=None):
            return HttpResponse("ok")
        with pytest.raises(PermissionDenied):
            view(_request(client_user), project_id=project.pk)

    def test_missing_project_404(self, admin_user):
        @require_project_access()
        def view(request, project_id, project=None):
            return HttpResponse("ok")
        from django.http import Http404
        with pytest.raises(Http404):
            view(_request(admin_user), project_id=999999)

    def test_custom_project_arg(self, admin_user, project):
        @require_project_access(project_arg="pid")
        def view(request, pid, project=None):
            return HttpResponse("ok")
        assert view(_request(admin_user), pid=project.pk).status_code == 200


class TestRequireCanViewFinancials:
    def test_admin_passes(self, admin_user, project):
        @require_can_view_financials()
        def view(request, project_id, project=None):
            return HttpResponse("ok")
        assert view(_request(admin_user), project_id=project.pk).status_code == 200

    def test_employee_denied(self, employee_user, project):
        @require_can_view_financials()
        def view(request, project_id, project=None):
            return HttpResponse("ok")
        with pytest.raises(PermissionDenied):
            view(_request(employee_user), project_id=project.pk)

    def test_client_without_flag_denied(self, client_user, project):
        ClientProjectAccess.objects.create(
            user=client_user, project=project, role="viewer", is_active=True,
        )

        @require_can_view_financials()
        def view(request, project_id, project=None):
            return HttpResponse("ok")
        with pytest.raises(PermissionDenied):
            view(_request(client_user), project_id=project.pk)


# ─────────────── DRF permission tests (G1 fix) ───────────────
class TestDRFPermissions:
    """The legacy code used 'pm' but Profile.role is 'project_manager'.
    These tests prove PMs are now correctly granted access (G1 fix)."""

    def test_IsOwnerOrPM_pm_allowed(self, pm_user):
        """REGRESSION GUARD: PM was silently denied before Phase 9."""
        assert IsOwnerOrPM().has_permission(_request(pm_user), None) is True

    def test_IsOwnerOrPM_owner_allowed(self, owner_user):
        assert IsOwnerOrPM().has_permission(_request(owner_user), None) is True

    def test_IsOwnerOrPM_admin_allowed(self, admin_user):
        assert IsOwnerOrPM().has_permission(_request(admin_user), None) is True

    def test_IsOwnerOrPM_employee_denied(self, employee_user):
        assert IsOwnerOrPM().has_permission(_request(employee_user), None) is False

    def test_IsOwnerOrPM_anonymous_denied(self):
        assert IsOwnerOrPM().has_permission(_request(AnonymousUser()), None) is False

    def test_IsOwner_only_owner(self, owner_user, pm_user, employee_user):
        p = IsOwner()
        assert p.has_permission(_request(owner_user), None) is True
        assert p.has_permission(_request(pm_user), None) is False
        assert p.has_permission(_request(employee_user), None) is False

    def test_IsOwner_admin_passes(self, admin_user):
        assert IsOwner().has_permission(_request(admin_user), None) is True

    def test_IsOwnerOrPMOrSuperintendent(self, super_user, employee_user, pm_user):
        p = IsOwnerOrPMOrSuperintendent()
        assert p.has_permission(_request(super_user), None) is True
        assert p.has_permission(_request(pm_user), None) is True
        assert p.has_permission(_request(employee_user), None) is False

    def test_IsAdminOrPM_pm_allowed(self, pm_user):
        """REGRESSION GUARD: PM was previously OK here (used 'project_manager'
        string), but make sure rewrite preserved the behavior."""
        assert IsAdminOrPM().has_permission(_request(pm_user), None) is True

    def test_IsAdminOrPM_employee_denied(self, employee_user):
        assert IsAdminOrPM().has_permission(_request(employee_user), None) is False

    def test_IsOwnerOrReadOnly_get_any_user(self, employee_user):
        assert IsOwnerOrReadOnly().has_permission(
            _request(employee_user, method="get"), None
        ) is True

    def test_IsOwnerOrReadOnly_post_only_owner(self, owner_user, pm_user):
        p = IsOwnerOrReadOnly()
        assert p.has_permission(_request(owner_user, method="post"), None) is True
        assert p.has_permission(_request(pm_user, method="post"), None) is False


class TestCanAccessProject:
    def test_admin_can_access(self, admin_user, project):
        assert CanAccessProject().has_object_permission(
            _request(admin_user), None, project
        ) is True

    def test_pm_unassigned_denied(self, pm_user, project):
        assert CanAccessProject().has_object_permission(
            _request(pm_user), None, project
        ) is False

    def test_pm_assigned_allowed(self, pm_user, project):
        ProjectManagerAssignment.objects.create(project=project, pm=pm_user, role="pm")
        assert CanAccessProject().has_object_permission(
            _request(pm_user), None, project
        ) is True

    def test_client_with_access(self, client_user, project):
        ClientProjectAccess.objects.create(
            user=client_user, project=project, role="viewer", is_active=True,
        )
        assert CanAccessProject().has_object_permission(
            _request(client_user), None, project
        ) is True

    def test_client_without_access_denied(self, client_user, project):
        assert CanAccessProject().has_object_permission(
            _request(client_user), None, project
        ) is False

    def test_object_with_project_attribute(self, admin_user, project):
        """LEGACY BUG FIX: old code did `obj if hasattr(obj, "project") else obj`
        which always returned obj, never the related project. Verify the new
        implementation correctly resolves obj.project."""
        from core.models import ChangeOrder
        co = ChangeOrder.objects.create(project=project, description="X", amount=10)
        assert CanAccessProject().has_object_permission(
            _request(admin_user), None, co
        ) is True

    def test_object_with_no_project_relation_denied(self, admin_user):
        class FakeObj:
            pass
        assert CanAccessProject().has_object_permission(
            _request(admin_user), None, FakeObj()
        ) is False
