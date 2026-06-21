"""Phase 1 — Partner role identity & no-collateral-access guarantees.

Locks in that ROLE_PARTNER is a pure identity:
  - is_partner() detects it
  - it is in ALL_ROLES (valid) but NOT in INTERNAL_ROLES (no internal tools)
  - a partner gets NO project access and NO financial capability *by role alone*

These tests are the safety net for "a socio never inherits broad access".
"""
from __future__ import annotations

import io

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.core.management import call_command
from django.core.management.base import CommandError

from core import access
from core.models import Profile, Project

User = get_user_model()


def _mk_user(username, *, role=None, is_staff=False, is_superuser=False, email=""):
    u = User.objects.create_user(
        username=username, password="x", email=email,
        is_staff=is_staff, is_superuser=is_superuser,
    )
    if role:
        u.profile.role = role
        u.profile.save()
    return u


@pytest.fixture
def partner_user():
    return _mk_user("ps_partner", role=access.ROLE_PARTNER, email="partner@example.com")


@pytest.mark.django_db
class TestPartnerIdentity:
    def test_constant_value(self):
        assert access.ROLE_PARTNER == "partner"

    def test_is_partner_true_for_partner(self, partner_user):
        assert access.is_partner(partner_user) is True

    def test_is_partner_false_for_other_roles(self):
        for role in [
            access.ROLE_ADMIN, access.ROLE_OWNER, access.ROLE_PM,
            access.ROLE_EMPLOYEE, access.ROLE_CLIENT, access.ROLE_DESIGNER,
            access.ROLE_SUPERINTENDENT,
        ]:
            u = _mk_user(f"ps_{role}", role=role)
            assert access.is_partner(u) is False, f"{role} should not be partner"

    def test_is_partner_false_for_anonymous(self):
        assert access.is_partner(AnonymousUser()) is False

    def test_get_role_returns_partner(self, partner_user):
        assert access.get_role(partner_user) == access.ROLE_PARTNER

    def test_partner_is_valid_role_choice(self):
        """'partner' must be a selectable Profile.role choice."""
        valid = {c[0] for c in Profile._meta.get_field("role").choices}
        assert "partner" in valid


@pytest.mark.django_db
class TestPartnerNoCollateralAccess:
    """A partner must NOT inherit internal/financial/project access by role."""

    def test_partner_in_all_roles_but_not_internal(self):
        assert access.ROLE_PARTNER in access.ALL_ROLES
        assert access.ROLE_PARTNER not in access.INTERNAL_ROLES

    def test_partner_is_not_internal(self, partner_user):
        assert access.is_internal(partner_user) is False

    def test_partner_is_not_staffish(self, partner_user):
        assert access.is_staffish(partner_user) is False

    def test_partner_is_not_admin_or_pm(self, partner_user):
        assert access.is_admin_or_pm(partner_user) is False

    def test_partner_is_not_admin_owner_pm_client_employee(self, partner_user):
        assert access.is_admin(partner_user) is False
        assert access.is_owner(partner_user) is False
        assert access.is_pm(partner_user) is False
        assert access.is_client(partner_user) is False
        assert access.is_employee(partner_user) is False

    def test_partner_has_no_project_access_by_default(self, partner_user):
        """Until Phase 7 wires explicit profit-share access, a partner sees
        zero projects and cannot view an arbitrary project by role alone."""
        p = Project.objects.create(name="PS Collateral Project")
        assert list(access.accessible_projects(partner_user)) == []
        assert access.can_view_project(partner_user, p) is False

    def test_partner_cannot_edit_project(self, partner_user):
        p = Project.objects.create(name="PS Edit Project")
        assert access.can_edit_project(partner_user, p) is False


@pytest.mark.django_db
class TestPromotePartnersCommand:
    """Idempotent promote_partners management command."""

    def test_promote_by_username(self):
        u = _mk_user("cmd_partner_a", role=access.ROLE_EMPLOYEE)
        call_command("promote_partners", "--user", "cmd_partner_a")
        u.profile.refresh_from_db()
        assert u.profile.role == access.ROLE_PARTNER

    def test_promote_by_email(self):
        u = _mk_user("cmd_partner_b", role=access.ROLE_EMPLOYEE, email="pb@example.com")
        call_command("promote_partners", "--email", "pb@example.com")
        u.profile.refresh_from_db()
        assert u.profile.role == access.ROLE_PARTNER

    def test_promote_is_idempotent(self):
        u = _mk_user("cmd_idem", role=access.ROLE_EMPLOYEE)
        call_command("promote_partners", "--user", "cmd_idem")
        call_command("promote_partners", "--user", "cmd_idem")  # second run = no-op
        u.profile.refresh_from_db()
        assert u.profile.role == access.ROLE_PARTNER

    def test_dry_run_changes_nothing(self):
        u = _mk_user("cmd_dry", role=access.ROLE_EMPLOYEE)
        call_command("promote_partners", "--user", "cmd_dry", "--dry-run")
        u.profile.refresh_from_db()
        assert u.profile.role == access.ROLE_EMPLOYEE  # unchanged

    def test_unknown_user_is_reported_but_known_still_promoted(self):
        u = _mk_user("cmd_known", role=access.ROLE_EMPLOYEE)
        out = io.StringIO()
        call_command(
            "promote_partners", "--user", "cmd_known",
            "--user", "does_not_exist_xyz", stdout=out,
        )
        u.profile.refresh_from_db()
        assert u.profile.role == access.ROLE_PARTNER
        assert "does_not_exist_xyz" in out.getvalue()

    def test_no_matches_raises(self):
        with pytest.raises(CommandError):
            call_command("promote_partners", "--user", "nobody_here_at_all")

    def test_no_selectors_raises(self):
        with pytest.raises(CommandError):
            call_command("promote_partners")

    def test_promotes_multiple_partners(self):
        a = _mk_user("cmd_multi_a", role=access.ROLE_EMPLOYEE)
        b = _mk_user("cmd_multi_b", role=access.ROLE_EMPLOYEE)
        call_command("promote_partners", "--user", "cmd_multi_a", "--user", "cmd_multi_b")
        a.profile.refresh_from_db()
        b.profile.refresh_from_db()
        assert a.profile.role == access.ROLE_PARTNER
        assert b.profile.role == access.ROLE_PARTNER

