"""Phase 11 — the "Make a PM a socio" button (membership management).

The director turns a Project Manager into a profit-share socio (and back) with
one click, WITHOUT changing the PM's role. Backed by ``MemberSetView`` and the
``_socio_candidates`` picker on the Director Panel.

Guarantees proven here:
  * activating creates/reactivates an ACTIVE PartnerAccount; the role is
    untouched and the user becomes a profit-share member;
  * deactivating preserves the account, its balance and its ledger history;
  * reactivation reuses the SAME account (same balance) — no data loss;
  * only the director may call it; the director can't be added to the pool;
  * the panel picker lists plain PMs and excludes active socios.
"""
from __future__ import annotations

from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient

from core import access
from core.models import LedgerEntry, PartnerAccount, Profile
from core.services.profit_share_service import record_advance
from core.views.profit_share_views import _socio_candidates

User = get_user_model()

URL = reverse("api-profit-share-member-set")


def _user(username, role, *, is_staff=False):
    u = User.objects.create_user(username=username, password="x", is_staff=is_staff)
    Profile.objects.update_or_create(user=u, defaults={"role": role})
    u.refresh_from_db()
    return u


@pytest.fixture
def api():
    return APIClient()


@pytest.fixture
def director(db):
    return _user("p11_director", access.ROLE_OWNER)


@pytest.fixture
def pm(db):
    return _user("p11_pm", access.ROLE_PM)


# ─────────────────────────────────────────────────────────────────────────────
# Endpoint: activate / deactivate
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.django_db
class TestMemberSetEndpoint:
    def test_director_activates_pm_as_socio_keeping_role(self, api, director, pm):
        api.force_authenticate(director)
        resp = api.post(URL, {"user_id": pm.id, "is_socio": True}, format="json")
        assert resp.status_code == 200
        assert resp.data["is_active_socio"] is True
        # Role UNTOUCHED, but now a profit-share member.
        pm.refresh_from_db()
        assert access.get_role(pm) == access.ROLE_PM
        assert access.is_profit_share_member(pm) is True
        acc = PartnerAccount.objects.get(owner=pm)
        assert acc.is_active_socio is True
        assert acc.is_business is False

    def test_director_deactivates_socio(self, api, director, pm):
        api.force_authenticate(director)
        api.post(URL, {"user_id": pm.id, "is_socio": True}, format="json")
        resp = api.post(URL, {"user_id": pm.id, "is_socio": False}, format="json")
        assert resp.status_code == 200
        assert resp.data["is_active_socio"] is False
        assert access.is_profit_share_member(pm) is False

    def test_deactivation_preserves_balance_and_history(self, api, director, pm):
        api.force_authenticate(director)
        api.post(URL, {"user_id": pm.id, "is_socio": True}, format="json")
        acc = PartnerAccount.objects.get(owner=pm)
        # Give the account a non-trivial balance + a ledger entry.
        record_advance(acc, Decimal("300.00"), note="test", recorded_by=director)
        acc.refresh_from_db()
        balance_before = acc.balance
        entries_before = LedgerEntry.objects.filter(account=acc).count()
        assert entries_before == 1

        api.post(URL, {"user_id": pm.id, "is_socio": False}, format="json")
        acc.refresh_from_db()
        assert acc.balance == balance_before          # money untouched
        assert LedgerEntry.objects.filter(account=acc).count() == entries_before

    def test_reactivation_reuses_same_account(self, api, director, pm):
        api.force_authenticate(director)
        api.post(URL, {"user_id": pm.id, "is_socio": True}, format="json")
        acc1 = PartnerAccount.objects.get(owner=pm)
        record_advance(acc1, Decimal("120.00"), recorded_by=director)
        api.post(URL, {"user_id": pm.id, "is_socio": False}, format="json")
        api.post(URL, {"user_id": pm.id, "is_socio": True}, format="json")
        acc2 = PartnerAccount.objects.get(owner=pm)
        assert acc2.pk == acc1.pk                      # same account
        assert acc2.is_active_socio is True
        assert acc2.balance == Decimal("-120.00")      # balance carried over

    def test_idempotent_activate(self, api, director, pm):
        api.force_authenticate(director)
        api.post(URL, {"user_id": pm.id, "is_socio": True}, format="json")
        api.post(URL, {"user_id": pm.id, "is_socio": True}, format="json")
        assert PartnerAccount.objects.filter(owner=pm).count() == 1


# ─────────────────────────────────────────────────────────────────────────────
# Endpoint: authorization & guards
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.django_db
class TestMemberSetGuards:
    def test_pm_cannot_manage_members(self, api, pm):
        other = _user("p11_other", access.ROLE_PM)
        api.force_authenticate(pm)
        resp = api.post(URL, {"user_id": other.id, "is_socio": True}, format="json")
        assert resp.status_code == 403

    def test_employee_cannot_manage_members(self, api):
        emp = _user("p11_emp", access.ROLE_EMPLOYEE)
        target = _user("p11_target", access.ROLE_PM)
        api.force_authenticate(emp)
        resp = api.post(URL, {"user_id": target.id, "is_socio": True}, format="json")
        assert resp.status_code == 403

    def test_anonymous_cannot_manage_members(self, api, pm):
        resp = api.post(URL, {"user_id": pm.id, "is_socio": True}, format="json")
        assert resp.status_code in (401, 403)

    def test_cannot_make_the_director_a_pool_socio(self, api, director):
        api.force_authenticate(director)
        owner2 = _user("p11_owner2", access.ROLE_OWNER)
        resp = api.post(URL, {"user_id": owner2.id, "is_socio": True}, format="json")
        assert resp.status_code == 400
        assert PartnerAccount.objects.filter(owner=owner2).exists() is False

    def test_unknown_user_is_404(self, api, director):
        api.force_authenticate(director)
        resp = api.post(URL, {"user_id": 999999, "is_socio": True}, format="json")
        assert resp.status_code == 404


# ─────────────────────────────────────────────────────────────────────────────
# Director Panel picker
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.django_db
class TestSocioCandidates:
    def test_plain_pm_is_a_candidate(self, pm):
        ids = set(_socio_candidates().values_list("id", flat=True))
        assert pm.id in ids

    def test_active_socio_pm_is_excluded(self, pm):
        PartnerAccount.for_partner(pm)  # active
        ids = set(_socio_candidates().values_list("id", flat=True))
        assert pm.id not in ids

    def test_inactive_ex_socio_pm_can_be_re_added(self, pm):
        acc = PartnerAccount.for_partner(pm)
        acc.is_active_socio = False
        acc.save(update_fields=["is_active_socio"])
        ids = set(_socio_candidates().values_list("id", flat=True))
        assert pm.id in ids

    def test_non_pm_roles_are_not_candidates(self):
        emp = _user("p11_cand_emp", access.ROLE_EMPLOYEE)
        client_u = _user("p11_cand_client", access.ROLE_CLIENT)
        ids = set(_socio_candidates().values_list("id", flat=True))
        assert emp.id not in ids
        assert client_u.id not in ids


@pytest.mark.django_db
class TestDirectorPanelRenders:
    def test_panel_shows_socios_card_and_picker(self, client, director, pm):
        client.force_login(director)
        resp = client.get(reverse("profit_share_director_panel"))
        assert resp.status_code == 200
        body = resp.content.decode()
        assert "Socios" in body                       # the membership card
        assert "Add as socio" in body                 # the add button
        assert pm.username in body or (pm.get_full_name() in body)  # candidate listed
