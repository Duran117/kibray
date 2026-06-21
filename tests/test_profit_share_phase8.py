"""Phase 8 — page views, access guards, and the calculator toggle.

Covers:
  * the new access helpers (is_director, require_director_or_redirect,
    require_profit_share_access_or_redirect);
  * page-level role gating (who gets 200 vs a redirect);
  * that each template actually renders;
  * the director-only ``use_actuals`` override on the breakdown endpoint
    (a socio can never reframe the numbers estimado⇄real).
"""
from __future__ import annotations

from datetime import date

import pytest
from django.contrib.auth import get_user_model
from django.test import RequestFactory
from django.urls import reverse
from rest_framework.test import APIClient

from core import access
from core.models import PartnerAccount, Project, RateConfig

User = get_user_model()


def _mk(username, role):
    u = User.objects.create_user(username, password="x")
    u.profile.role = role
    u.profile.save()
    return u


@pytest.fixture
def director(db):
    return _mk("ps8_director", access.ROLE_OWNER)


@pytest.fixture
def admin_director(db):
    return _mk("ps8_admin", access.ROLE_ADMIN)


@pytest.fixture
def socio(db):
    u = _mk("ps8_socio", access.ROLE_PARTNER)
    PartnerAccount.for_partner(u)
    return u


@pytest.fixture
def employee(db):
    return _mk("ps8_employee", access.ROLE_EMPLOYEE)


# ─────────────────────────────────────────────────────────────────────────────
# Access helpers (unit)
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.django_db
class TestAccessHelpers:
    def test_is_director_true_for_owner_and_admin(self, director, admin_director):
        assert access.is_director(director) is True
        assert access.is_director(admin_director) is True

    def test_is_director_false_for_socio_and_employee(self, socio, employee):
        assert access.is_director(socio) is False
        assert access.is_director(employee) is False

    def test_require_director_guard_allows_director(self, director):
        rf = RequestFactory()
        req = rf.get("/x")
        req.user = director
        assert access.require_director_or_redirect(req) is None

    def test_require_director_guard_blocks_socio(self, socio):
        # Wire up message storage so messages.error() in the guard works.
        from django.contrib.messages.storage.fallback import FallbackStorage

        rf = RequestFactory()
        req = rf.get("/x")
        req.user = socio
        req.session = {}
        req._messages = FallbackStorage(req)
        resp = access.require_director_or_redirect(req)
        assert resp is not None
        assert resp.status_code == 302

    def test_profit_share_access_guard_allows_socio_and_director(
        self, director, socio
    ):
        rf = RequestFactory()
        for u in (director, socio):
            req = rf.get("/x")
            req.user = u
            assert access.require_profit_share_access_or_redirect(req) is None


# ─────────────────────────────────────────────────────────────────────────────
# Page gating (integration)
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.django_db
class TestMyEarningsPage:
    URL = reverse("profit_share_my_earnings")

    def test_socio_gets_page(self, client, socio):
        client.force_login(socio)
        resp = client.get(self.URL)
        assert resp.status_code == 200
        assert b"My Earnings" in resp.content

    def test_director_gets_page(self, client, director):
        client.force_login(director)
        assert client.get(self.URL).status_code == 200

    def test_employee_redirected(self, client, employee):
        client.force_login(employee)
        resp = client.get(self.URL)
        assert resp.status_code == 302

    def test_anonymous_redirected_to_login(self, client):
        resp = client.get(self.URL)
        assert resp.status_code == 302


@pytest.mark.django_db
class TestDirectorPanelPage:
    URL = reverse("profit_share_director_panel")

    def test_director_gets_page(self, client, director):
        RateConfig.load()
        client.force_login(director)
        resp = client.get(self.URL)
        assert resp.status_code == 200
        assert b"Rate configuration" in resp.content

    def test_socio_redirected(self, client, socio):
        client.force_login(socio)
        assert client.get(self.URL).status_code == 302

    def test_employee_redirected(self, client, employee):
        client.force_login(employee)
        assert client.get(self.URL).status_code == 302


@pytest.mark.django_db
class TestCalculatorPage:
    URL = reverse("profit_share_calculator")

    def test_director_gets_page(self, client, director):
        Project.objects.create(name="Calc Project")
        client.force_login(director)
        resp = client.get(self.URL)
        assert resp.status_code == 200
        assert b"Calculator" in resp.content

    def test_socio_redirected(self, client, socio):
        client.force_login(socio)
        assert client.get(self.URL).status_code == 302


# ─────────────────────────────────────────────────────────────────────────────
# Calculator toggle: director-only use_actuals override
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.django_db
class TestUseActualsOverride:
    @pytest.fixture
    def project(self, db):
        # Open project (no end_date) → default mode is "estimado".
        RateConfig.load()
        return Project.objects.create(name="Override Project", in_profit_share=True)

    def _url(self, project):
        return reverse("api-profit-share-project-breakdown", args=[project.id])

    def test_director_can_force_real(self, project, director):
        api = APIClient()
        api.force_authenticate(director)
        default = api.get(self._url(project))
        assert default.data["mode"] == "estimado"
        forced = api.get(self._url(project) + "?use_actuals=true")
        assert forced.data["mode"] == "real"

    def test_socio_override_ignored(self, project, socio):
        api = APIClient()
        api.force_authenticate(socio)
        # Even if a socio passes use_actuals=true, the open project stays
        # "estimado" — the override is director-only.
        resp = api.get(self._url(project) + "?use_actuals=true")
        assert resp.status_code == 200
        assert resp.data["mode"] == "estimado"


# ─────────────────────────────────────────────────────────────────────────────
# Navigation gating
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.django_db
class TestNavGating:
    def _titles(self, user):
        from core.nav import build_global_nav

        return {s.title for s in build_global_nav(user)}

    def test_director_sees_profit_share_section(self, director):
        assert "Profit Share" in self._titles(director)

    def test_socio_sees_profit_share_section(self, socio):
        assert "Profit Share" in self._titles(socio)

    def test_employee_has_no_profit_share_section(self, employee):
        assert "Profit Share" not in self._titles(employee)

