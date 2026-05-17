"""Client must never land on the admin/PM project workspace.

Regression: 2026-05-17 — a client clicking on a project from the
sidebar's "My Projects" was being shown the internal admin
`project_overview` page (financials hub, EV/critical-path widgets,
PM tools, …). Two independent gaps caused it:

1. ``core/nav.py.build_global_nav()`` built the client's "My
   Projects" links pointing at the ``project_overview`` url name
   (the admin/PM view) instead of ``client_project_view``.
2. The ``project_overview`` view itself happily rendered for any
   client with ``ClientProjectAccess`` because the access layer
   correctly allowed them to *view* it. The view had no
   role-based redirect, so every other admin breadcrumb / back-
   button / dashboard link that resolves to ``project_overview``
   would also have leaked the admin dashboard to clients.

Both layers are now locked in:
  * the nav builder emits ``client_project_view`` for clients;
  * the view itself redirects clients to ``client_project_view``
    as a defense-in-depth catch-all.
"""
from __future__ import annotations

from datetime import date

import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse

from core.models import ClientProjectAccess, Project

User = get_user_model()
pytestmark = pytest.mark.django_db


@pytest.fixture
def client_user(db):
    u = User.objects.create_user("nav_client", "nc@x", "x")
    u.profile.role = "client"
    u.profile.save()
    return u


@pytest.fixture
def admin_user(db):
    u = User.objects.create_user(
        "nav_admin", "na@x", "x", is_staff=True, is_superuser=True,
    )
    u.profile.role = "admin"
    u.profile.save()
    return u


@pytest.fixture
def project(db):
    return Project.objects.create(
        name="Client-Routing Project",
        start_date=date.today(),
    )


@pytest.fixture
def project_with_client_access(project, client_user):
    ClientProjectAccess.objects.create(
        user=client_user, project=project, role="viewer", is_active=True,
    )
    return project


# ─── Sidebar nav builder ──────────────────────────────────────────────
class TestClientNavLinks:
    """The "My Projects" entries in the client sidebar must point at
    the client-facing project view, NOT the admin/PM workspace."""

    def test_client_my_projects_link_uses_client_view(
        self, client_user, project_with_client_access,
    ):
        from core.nav import build_global_nav

        sections = build_global_nav(client_user)
        my_projects = [s for s in sections if s.title == "My Projects"]
        assert my_projects, "Client should have a 'My Projects' section"

        for item in my_projects[0].items:
            assert item.url_name == "client_project_view", (
                f"Client nav item '{item.label}' points at "
                f"'{item.url_name}' — must be 'client_project_view'."
            )


# ─── View-level defense-in-depth redirect ─────────────────────────────
class TestProjectOverviewRedirectsClients:
    """No matter how a client lands on /projects/<id>/overview/
    (sidebar regression, stale bookmark, admin's link in an email,
    breadcrumb of a permitted sub-page, …) they must be bounced to
    the client view."""

    def test_client_with_access_is_redirected_to_client_view(
        self, client_user, project_with_client_access,
    ):
        c = Client()
        c.force_login(client_user)
        resp = c.get(
            reverse("project_overview",
                    kwargs={"project_id": project_with_client_access.id})
        )
        assert resp.status_code == 302
        assert resp.url == reverse(
            "client_project_view",
            kwargs={"project_id": project_with_client_access.id},
        )

    def test_client_without_access_still_redirected_safely(
        self, client_user, project,
    ):
        """Client w/o ClientProjectAccess must NOT see the admin
        page; they get bounced (to the client view or dashboard)."""
        c = Client()
        c.force_login(client_user)
        resp = c.get(
            reverse("project_overview", kwargs={"project_id": project.id})
        )
        assert resp.status_code == 302
        # Either route is safe; both are client-facing.
        assert resp.url.startswith(("/proyecto/", "/dashboard/client"))

    def test_admin_still_sees_admin_overview(
        self, admin_user, project,
    ):
        """The redirect must only fire for the 'client' role —
        admin/PM/staff still get the full workspace."""
        c = Client()
        c.force_login(admin_user)
        resp = c.get(
            reverse("project_overview", kwargs={"project_id": project.id})
        )
        # 200 (rendered) or eventual 302 to a normal admin destination —
        # but NEVER to client_project_view.
        if resp.status_code == 302:
            assert "/proyecto/" not in resp.url, (
                "Admin must not be redirected to the client view."
            )
        else:
            assert resp.status_code == 200
