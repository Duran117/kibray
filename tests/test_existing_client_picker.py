"""Existing-client picker on the "Add Owner/Client to Project" page.

UX request (2026-05-19): staff complained that picking a client that
already exists in the system required re-typing all their info. The
view now exposes a list of existing clients (excluding ones already
on this project) and the template shows a searchable picker that
auto-fills the form via JS.
"""
from __future__ import annotations

from datetime import date

import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse

from core.models import ClientProjectAccess, Profile, Project

User = get_user_model()
pytestmark = pytest.mark.django_db


@pytest.fixture
def staff(db):
    u = User.objects.create_user(
        "picker_staff", "ps@x", "x", is_staff=True, is_superuser=True,
    )
    p, _ = Profile.objects.get_or_create(user=u)
    p.role = "admin"
    p.save()
    return u


@pytest.fixture
def project(db):
    return Project.objects.create(
        name="Picker Project",
        start_date=date.today(),
    )


def _make_client(username, email, first, last):
    u = User.objects.create_user(
        username, email, "x",
        first_name=first, last_name=last,
    )
    p, _ = Profile.objects.get_or_create(user=u)
    p.role = "client"
    p.save()
    return u


class TestExistingClientPicker:
    def test_existing_clients_appear_in_context(self, staff, project):
        c1 = _make_client("alice_c", "alice@example.com", "Alice", "Wong")
        c2 = _make_client("bob_c", "bob@example.com", "Bob", "Lee")

        c = Client()
        c.force_login(staff)
        resp = c.get(reverse("project_add_owner", kwargs={"project_id": project.id}))

        assert resp.status_code == 200
        names = {x["email"] for x in resp.context["existing_clients"]}
        assert "alice@example.com" in names
        assert "bob@example.com" in names

    def test_clients_already_on_project_are_excluded(self, staff, project):
        already = _make_client("zoe_c", "zoe@example.com", "Zoe", "K")
        new = _make_client("yuri_c", "yuri@example.com", "Yuri", "P")
        ClientProjectAccess.objects.create(
            user=already, project=project, role="client", is_active=True,
        )

        c = Client()
        c.force_login(staff)
        resp = c.get(reverse("project_add_owner", kwargs={"project_id": project.id}))

        emails = {x["email"] for x in resp.context["existing_clients"]}
        assert "yuri@example.com" in emails
        assert "zoe@example.com" not in emails

    def test_clients_without_email_are_skipped(self, staff, project):
        no_email = User.objects.create_user(
            "no_email_c", email="", password="x",
            first_name="No", last_name="Email",
        )
        p, _ = Profile.objects.get_or_create(user=no_email)
        p.role = "client"
        p.save()

        c = Client()
        c.force_login(staff)
        resp = c.get(reverse("project_add_owner", kwargs={"project_id": project.id}))

        emails = {x["email"] for x in resp.context["existing_clients"]}
        assert "" not in emails

    def test_picker_renders_datalist_in_html(self, staff, project):
        _make_client("rita_c", "rita@example.com", "Rita", "Singh")
        c = Client()
        c.force_login(staff)
        resp = c.get(reverse("project_add_owner", kwargs={"project_id": project.id}))

        body = resp.content.decode("utf-8")
        assert "existing-clients-list" in body
        assert "rita@example.com" in body
        assert "Pick an existing client" in body

    def test_posting_existing_email_reuses_user(self, staff, project):
        """Picking an existing client + submit -> no new user, just access."""
        existing = _make_client("dan_c", "dan@example.com", "Dan", "Brown")
        before = User.objects.count()

        c = Client()
        c.force_login(staff)
        resp = c.post(
            reverse("project_add_owner", kwargs={"project_id": project.id}),
            {
                "first_name": "Dan",
                "last_name": "Brown",
                "email": "dan@example.com",
                "phone": "",
                "access_role": "client",
                # no send_credentials -> stays unchecked (default False on missing)
            },
        )

        assert resp.status_code == 302
        # Existing user reused — no new record created
        assert User.objects.count() == before
        # And the existing user now has project access
        assert ClientProjectAccess.objects.filter(
            user=existing, project=project,
        ).exists()
