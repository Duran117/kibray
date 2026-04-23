"""
Tests for core/views/client_mgmt_views.py

Covers:
- client_list, client_create (GET), client_detail, client_edit (GET),
  client_delete (GET/POST), client_reset_password (GET),
  client_assign_project (GET/POST add/remove)
- project_add_owner (GET)
- organization_list, organization_create (GET), organization_detail,
  organization_edit (GET), organization_delete (GET/POST)
"""
import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

User = get_user_model()


# ---------- Fixtures ----------


@pytest.fixture
def admin_user(db):
    return User.objects.create_user(
        username="cm_admin", password="x", is_staff=True, is_superuser=True
    )


@pytest.fixture
def regular_user(db):
    return User.objects.create_user(username="cm_regular", password="x")


@pytest.fixture
def client_user_obj(db):
    """User with client profile role."""
    from core.models import Profile
    u = User.objects.create_user(
        username="cm_client",
        password="x",
        email="client@test.com",
        first_name="Client",
        last_name="One",
    )
    Profile.objects.update_or_create(user=u, defaults={"role": "client"})
    u.refresh_from_db()
    return u


@pytest.fixture
def non_client_user(db):
    """User who has profile but not client role."""
    from core.models import Profile
    u = User.objects.create_user(username="cm_employee", password="x")
    Profile.objects.update_or_create(user=u, defaults={"role": "employee"})
    u.refresh_from_db()
    return u


@pytest.fixture
def project(db):
    from core.models import Project
    return Project.objects.create(name="ClientMgmt Project")


@pytest.fixture
def organization(db):
    from core.models import ClientOrganization
    return ClientOrganization.objects.create(
        name="Test Org",
        billing_address="123 Test St",
        billing_email="billing@test.com",
    )


# ========================================
# CLIENT LIST
# ========================================


class TestClientList:
    def test_anonymous_redirected(self, client):
        resp = client.get(reverse("client_list"))
        assert resp.status_code == 302

    def test_non_staff_redirected(self, client, regular_user):
        client.force_login(regular_user)
        resp = client.get(reverse("client_list"))
        assert resp.status_code == 302  # staff_member_required → admin login

    def test_staff_can_view(self, client, admin_user, client_user_obj):
        client.force_login(admin_user)
        resp = client.get(reverse("client_list"))
        assert resp.status_code == 200

    def test_search_filter(self, client, admin_user, client_user_obj):
        client.force_login(admin_user)
        resp = client.get(reverse("client_list"), {"search": "Client"})
        assert resp.status_code == 200

    def test_status_filter_active(self, client, admin_user, client_user_obj):
        client.force_login(admin_user)
        resp = client.get(reverse("client_list"), {"status": "active"})
        assert resp.status_code == 200

    def test_status_filter_inactive(self, client, admin_user, client_user_obj):
        client.force_login(admin_user)
        resp = client.get(reverse("client_list"), {"status": "inactive"})
        assert resp.status_code == 200


# ========================================
# CLIENT CREATE
# ========================================


class TestClientCreate:
    def test_non_staff_redirected(self, client, regular_user):
        client.force_login(regular_user)
        resp = client.get(reverse("client_create"))
        assert resp.status_code == 302

    def test_get_shows_form(self, client, admin_user):
        client.force_login(admin_user)
        resp = client.get(reverse("client_create"))
        assert resp.status_code == 200


# ========================================
# CLIENT DETAIL
# ========================================


class TestClientDetail:
    def test_non_staff_redirected(self, client, regular_user, client_user_obj):
        client.force_login(regular_user)
        resp = client.get(reverse("client_detail", args=[client_user_obj.id]))
        assert resp.status_code == 302

    def test_staff_can_view(self, client, admin_user, client_user_obj):
        client.force_login(admin_user)
        resp = client.get(reverse("client_detail", args=[client_user_obj.id]))
        assert resp.status_code == 200

    def test_non_client_user_redirects(self, client, admin_user, non_client_user):
        client.force_login(admin_user)
        resp = client.get(reverse("client_detail", args=[non_client_user.id]))
        assert resp.status_code == 302
        assert reverse("client_list") in resp.url

    def test_nonexistent_404(self, client, admin_user):
        client.force_login(admin_user)
        resp = client.get(reverse("client_detail", args=[999999]))
        assert resp.status_code == 404


# ========================================
# CLIENT EDIT
# ========================================


class TestClientEdit:
    def test_non_staff_redirected(self, client, regular_user, client_user_obj):
        client.force_login(regular_user)
        resp = client.get(reverse("client_edit", args=[client_user_obj.id]))
        assert resp.status_code == 302

    def test_get_shows_form(self, client, admin_user, client_user_obj):
        client.force_login(admin_user)
        resp = client.get(reverse("client_edit", args=[client_user_obj.id]))
        assert resp.status_code == 200

    def test_non_client_user_redirects(self, client, admin_user, non_client_user):
        client.force_login(admin_user)
        resp = client.get(reverse("client_edit", args=[non_client_user.id]))
        assert resp.status_code == 302


# ========================================
# CLIENT DELETE
# ========================================


class TestClientDelete:
    def test_non_staff_redirected(self, client, regular_user, client_user_obj):
        client.force_login(regular_user)
        resp = client.get(reverse("client_delete", args=[client_user_obj.id]))
        assert resp.status_code == 302

    def test_get_shows_confirm(self, client, admin_user, client_user_obj):
        client.force_login(admin_user)
        resp = client.get(reverse("client_delete", args=[client_user_obj.id]))
        assert resp.status_code == 200

    def test_post_deactivate(self, client, admin_user, client_user_obj):
        client.force_login(admin_user)
        resp = client.post(
            reverse("client_delete", args=[client_user_obj.id]),
            {"action": "deactivate"},
        )
        assert resp.status_code == 302
        client_user_obj.refresh_from_db()
        assert client_user_obj.is_active is False

    def test_post_delete_no_dependencies(self, client, admin_user, client_user_obj):
        client.force_login(admin_user)
        cid = client_user_obj.id
        resp = client.post(
            reverse("client_delete", args=[cid]),
            {"action": "delete"},
        )
        assert resp.status_code == 302
        assert not User.objects.filter(pk=cid).exists()

    def test_post_delete_with_dependencies_blocked(
        self, client, admin_user, client_user_obj, project
    ):
        from core.models import ClientProjectAccess
        ClientProjectAccess.objects.create(
            user=client_user_obj, project=project, role="client"
        )
        client.force_login(admin_user)
        cid = client_user_obj.id
        resp = client.post(
            reverse("client_delete", args=[cid]),
            {"action": "delete"},
        )
        assert resp.status_code == 302
        assert User.objects.filter(pk=cid).exists()  # not deleted

    def test_non_client_user_redirects(self, client, admin_user, non_client_user):
        client.force_login(admin_user)
        resp = client.get(reverse("client_delete", args=[non_client_user.id]))
        assert resp.status_code == 302


# ========================================
# CLIENT RESET PASSWORD
# ========================================


class TestClientResetPassword:
    def test_non_staff_redirected(self, client, regular_user, client_user_obj):
        client.force_login(regular_user)
        resp = client.get(reverse("client_reset_password", args=[client_user_obj.id]))
        assert resp.status_code == 302

    def test_get_shows_form(self, client, admin_user, client_user_obj):
        client.force_login(admin_user)
        resp = client.get(reverse("client_reset_password", args=[client_user_obj.id]))
        assert resp.status_code == 200

    def test_non_client_user_redirects(self, client, admin_user, non_client_user):
        client.force_login(admin_user)
        resp = client.get(reverse("client_reset_password", args=[non_client_user.id]))
        assert resp.status_code == 302


# ========================================
# CLIENT ASSIGN PROJECT
# ========================================


class TestClientAssignProject:
    def test_non_staff_redirected(self, client, regular_user, client_user_obj):
        client.force_login(regular_user)
        resp = client.get(reverse("client_assign_project", args=[client_user_obj.id]))
        assert resp.status_code == 302

    def test_get_shows_form(self, client, admin_user, client_user_obj, project):
        client.force_login(admin_user)
        resp = client.get(reverse("client_assign_project", args=[client_user_obj.id]))
        assert resp.status_code == 200

    def test_post_add_creates_access(self, client, admin_user, client_user_obj, project):
        from core.models import ClientProjectAccess
        client.force_login(admin_user)
        resp = client.post(
            reverse("client_assign_project", args=[client_user_obj.id]),
            {"project_id": str(project.id), "action": "add", "access_role": "client"},
        )
        assert resp.status_code == 302
        assert ClientProjectAccess.objects.filter(
            user=client_user_obj, project=project
        ).exists()

    def test_post_add_invalid_role_defaults(self, client, admin_user, client_user_obj, project):
        from core.models import ClientProjectAccess
        client.force_login(admin_user)
        resp = client.post(
            reverse("client_assign_project", args=[client_user_obj.id]),
            {"project_id": str(project.id), "action": "add", "access_role": "INVALID"},
        )
        assert resp.status_code == 302
        access = ClientProjectAccess.objects.get(user=client_user_obj, project=project)
        assert access.role == "client"

    def test_post_add_existing_shows_info(self, client, admin_user, client_user_obj, project):
        from core.models import ClientProjectAccess
        ClientProjectAccess.objects.create(
            user=client_user_obj, project=project, role="client"
        )
        client.force_login(admin_user)
        resp = client.post(
            reverse("client_assign_project", args=[client_user_obj.id]),
            {"project_id": str(project.id), "action": "add"},
        )
        assert resp.status_code == 302

    def test_post_remove(self, client, admin_user, client_user_obj, project):
        from core.models import ClientProjectAccess
        ClientProjectAccess.objects.create(
            user=client_user_obj, project=project, role="client"
        )
        client.force_login(admin_user)
        resp = client.post(
            reverse("client_assign_project", args=[client_user_obj.id]),
            {"project_id": str(project.id), "action": "remove"},
        )
        assert resp.status_code == 302
        assert not ClientProjectAccess.objects.filter(
            user=client_user_obj, project=project
        ).exists()

    def test_post_remove_nonexistent_access(self, client, admin_user, client_user_obj, project):
        client.force_login(admin_user)
        resp = client.post(
            reverse("client_assign_project", args=[client_user_obj.id]),
            {"project_id": str(project.id), "action": "remove"},
        )
        assert resp.status_code == 302

    def test_post_update_role(self, client, admin_user, client_user_obj, project):
        from core.models import ClientProjectAccess
        access = ClientProjectAccess.objects.create(
            user=client_user_obj, project=project, role="client"
        )
        client.force_login(admin_user)
        resp = client.post(
            reverse("client_assign_project", args=[client_user_obj.id]),
            {
                "project_id": str(project.id),
                "action": "update_role",
                "new_role": "owner",
            },
        )
        assert resp.status_code == 302
        access.refresh_from_db()
        assert access.role == "owner"

    def test_post_missing_project_id(self, client, admin_user, client_user_obj):
        client.force_login(admin_user)
        resp = client.post(
            reverse("client_assign_project", args=[client_user_obj.id]),
            {"action": "add"},
        )
        assert resp.status_code == 302

    def test_non_client_user_redirects(self, client, admin_user, non_client_user):
        client.force_login(admin_user)
        resp = client.get(reverse("client_assign_project", args=[non_client_user.id]))
        assert resp.status_code == 302


# ========================================
# PROJECT ADD OWNER
# ========================================


class TestProjectAddOwner:
    def test_non_staff_redirected(self, client, regular_user, project):
        client.force_login(regular_user)
        resp = client.get(reverse("project_add_owner", args=[project.id]))
        assert resp.status_code == 302

    def test_get_shows_form(self, client, admin_user, project):
        client.force_login(admin_user)
        resp = client.get(reverse("project_add_owner", args=[project.id]))
        assert resp.status_code == 200

    def test_nonexistent_project_404(self, client, admin_user):
        client.force_login(admin_user)
        resp = client.get(reverse("project_add_owner", args=[999999]))
        assert resp.status_code == 404


# ========================================
# ORGANIZATION VIEWS
# ========================================


class TestOrganizationList:
    def test_non_staff_redirected(self, client, regular_user):
        client.force_login(regular_user)
        resp = client.get(reverse("organization_list"))
        assert resp.status_code == 302

    def test_staff_can_view(self, client, admin_user, organization):
        client.force_login(admin_user)
        resp = client.get(reverse("organization_list"))
        assert resp.status_code == 200

    def test_search_filter(self, client, admin_user, organization):
        client.force_login(admin_user)
        resp = client.get(reverse("organization_list"), {"search": "Test"})
        assert resp.status_code == 200

    def test_status_filter_active(self, client, admin_user, organization):
        client.force_login(admin_user)
        resp = client.get(reverse("organization_list"), {"status": "active"})
        assert resp.status_code == 200

    def test_status_filter_inactive(self, client, admin_user, organization):
        client.force_login(admin_user)
        resp = client.get(reverse("organization_list"), {"status": "inactive"})
        assert resp.status_code == 200


class TestOrganizationCreate:
    def test_non_staff_redirected(self, client, regular_user):
        client.force_login(regular_user)
        resp = client.get(reverse("organization_create"))
        assert resp.status_code == 302

    def test_get_shows_form(self, client, admin_user):
        client.force_login(admin_user)
        resp = client.get(reverse("organization_create"))
        assert resp.status_code == 200


class TestOrganizationDetail:
    def test_non_staff_redirected(self, client, regular_user, organization):
        client.force_login(regular_user)
        resp = client.get(reverse("organization_detail", args=[organization.id]))
        assert resp.status_code == 302

    def test_staff_can_view(self, client, admin_user, organization):
        client.force_login(admin_user)
        resp = client.get(reverse("organization_detail", args=[organization.id]))
        assert resp.status_code == 200

    def test_nonexistent_404(self, client, admin_user):
        client.force_login(admin_user)
        resp = client.get(reverse("organization_detail", args=[999999]))
        assert resp.status_code == 404


class TestOrganizationEdit:
    def test_non_staff_redirected(self, client, regular_user, organization):
        client.force_login(regular_user)
        resp = client.get(reverse("organization_edit", args=[organization.id]))
        assert resp.status_code == 302

    def test_get_shows_form(self, client, admin_user, organization):
        client.force_login(admin_user)
        resp = client.get(reverse("organization_edit", args=[organization.id]))
        assert resp.status_code == 200


class TestOrganizationDelete:
    def test_non_staff_redirected(self, client, regular_user, organization):
        client.force_login(regular_user)
        resp = client.get(reverse("organization_delete", args=[organization.id]))
        assert resp.status_code == 302

    def test_get_shows_confirm(self, client, admin_user, organization):
        client.force_login(admin_user)
        resp = client.get(reverse("organization_delete", args=[organization.id]))
        assert resp.status_code == 200

    def test_post_deactivate(self, client, admin_user, organization):
        client.force_login(admin_user)
        resp = client.post(
            reverse("organization_delete", args=[organization.id]),
            {"action": "deactivate"},
        )
        assert resp.status_code == 302
        organization.refresh_from_db()
        assert organization.is_active is False

    def test_post_delete_no_dependencies(self, client, admin_user, organization):
        from core.models import ClientOrganization
        client.force_login(admin_user)
        oid = organization.id
        resp = client.post(
            reverse("organization_delete", args=[oid]),
            {"action": "delete"},
        )
        assert resp.status_code == 302
        assert not ClientOrganization.objects.filter(pk=oid).exists()

    def test_post_delete_with_project_blocked(self, client, admin_user, organization, project):
        from core.models import ClientOrganization
        project.billing_organization = organization
        project.save()
        client.force_login(admin_user)
        oid = organization.id
        resp = client.post(
            reverse("organization_delete", args=[oid]),
            {"action": "delete"},
        )
        assert resp.status_code == 302
        assert ClientOrganization.objects.filter(pk=oid).exists()
