"""Project invitation / access notification flow.

Feature (2026-05-21): staff want to prepare a project dashboard first
(photos, schedule, estimate) BEFORE notifying the client. So:

* When adding an EXISTING user via ``project_add_owner`` with the
  "send credentials" checkbox ticked, we now send a "Project access
  granted" notification (no password).
* A new ``project_send_invitation`` endpoint lets staff (re)send the
  invitation on-demand from the project's add-owner page.
  - If the user has never logged in, we regenerate a temp password
    and send the full welcome+credentials email.
  - Otherwise we send the access-granted notification.
"""
from __future__ import annotations

from datetime import date

import pytest
from django.contrib.auth import get_user_model
from django.core import mail
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from core.models import ClientProjectAccess, Profile, Project

User = get_user_model()
pytestmark = pytest.mark.django_db


@pytest.fixture
def staff(db):
    u = User.objects.create_user(
        "inv_staff", "is@x", "x", is_staff=True, is_superuser=True,
        first_name="Sara", last_name="Admin",
    )
    p, _ = Profile.objects.get_or_create(user=u)
    p.role = "admin"
    p.save()
    return u


@pytest.fixture
def project(db):
    return Project.objects.create(name="Invite Project", start_date=date.today())


def _make_client(username, email, first="Carl", last="Owner", *, logged_in=False):
    u = User.objects.create_user(
        username, email, "knownpassword",
        first_name=first, last_name=last,
    )
    p, _ = Profile.objects.get_or_create(user=u)
    p.role = "client"
    p.save()
    if logged_in:
        u.last_login = timezone.now()
        u.save(update_fields=["last_login"])
    return u


def _grant(user, project, role="client"):
    return ClientProjectAccess.objects.create(
        user=user, project=project, role=role,
    )


class TestProjectAddOwnerExistingUserNotification:
    def test_existing_user_with_send_credentials_sends_notification(
        self, staff, project, settings
    ):
        settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
        mail.outbox = []
        existing = _make_client(
            "existing_c", "existing@example.com", "Existing", "Client",
            logged_in=True,
        )

        c = Client()
        c.force_login(staff)
        resp = c.post(
            reverse("project_add_owner", args=[project.id]),
            data={
                "email": existing.email,
                "first_name": "Existing",
                "last_name": "Client",
                "phone": "",
                "access_role": "client",
                "send_credentials": "on",
            },
            follow=False,
        )
        # redirect → success
        assert resp.status_code == 302
        assert len(mail.outbox) == 1
        m = mail.outbox[0]
        assert existing.email in m.to
        assert "access" in m.subject.lower() or project.name in m.subject
        # password must NOT be included for an existing user
        body = m.body.lower()
        assert "knownpassword" not in body

    def test_existing_user_without_send_credentials_sends_nothing(
        self, staff, project, settings
    ):
        settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
        mail.outbox = []
        existing = _make_client(
            "silent_c", "silent@example.com", logged_in=True,
        )

        c = Client()
        c.force_login(staff)
        resp = c.post(
            reverse("project_add_owner", args=[project.id]),
            data={
                "email": existing.email,
                "first_name": existing.first_name,
                "last_name": existing.last_name,
                "phone": "",
                "access_role": "client",
                # send_credentials NOT in POST → False
            },
            follow=False,
        )
        assert resp.status_code == 302
        assert len(mail.outbox) == 0


class TestProjectSendInvitationEndpoint:
    def test_send_invitation_to_never_logged_in_user_uses_welcome_email(
        self, staff, project, settings
    ):
        settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
        mail.outbox = []
        u = _make_client("newbie_c", "newbie@example.com", logged_in=False)
        access = _grant(u, project, role="client")
        original_password_hash = u.password

        c = Client()
        c.force_login(staff)
        resp = c.post(
            reverse("project_send_invitation", args=[project.id, access.id])
        )
        assert resp.status_code == 302
        assert len(mail.outbox) == 1
        m = mail.outbox[0]
        assert u.email in m.to
        # welcome email contains the brand-new temp password — verify
        # a fresh password was set (hash changed)
        u.refresh_from_db()
        assert u.password != original_password_hash

    def test_send_invitation_to_returning_user_uses_notification_email(
        self, staff, project, settings
    ):
        settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
        mail.outbox = []
        u = _make_client("veteran_c", "veteran@example.com", logged_in=True)
        access = _grant(u, project, role="owner")
        original_password_hash = u.password

        c = Client()
        c.force_login(staff)
        resp = c.post(
            reverse("project_send_invitation", args=[project.id, access.id])
        )
        assert resp.status_code == 302
        assert len(mail.outbox) == 1
        m = mail.outbox[0]
        assert u.email in m.to
        assert project.name in m.subject
        # password must NOT have been rotated
        u.refresh_from_db()
        assert u.password == original_password_hash

    def test_send_invitation_requires_post(self, staff, project):
        u = _make_client("c1", "c1@example.com")
        access = _grant(u, project)
        c = Client()
        c.force_login(staff)
        resp = c.get(
            reverse("project_send_invitation", args=[project.id, access.id])
        )
        assert resp.status_code == 405

    def test_send_invitation_requires_staff(self, project):
        u = _make_client("c2", "c2@example.com")
        access = _grant(u, project)
        non_staff = User.objects.create_user("nope", "n@x", "x")
        c = Client()
        c.force_login(non_staff)
        resp = c.post(
            reverse("project_send_invitation", args=[project.id, access.id])
        )
        # staff_member_required redirects to admin login
        assert resp.status_code in (302, 403)

    def test_send_invitation_404_when_access_belongs_to_other_project(
        self, staff, project
    ):
        other = Project.objects.create(name="Other", start_date=date.today())
        u = _make_client("c3", "c3@example.com")
        access = _grant(u, other)  # belongs to OTHER project
        c = Client()
        c.force_login(staff)
        resp = c.post(
            reverse("project_send_invitation", args=[project.id, access.id])
        )
        assert resp.status_code == 404

    def test_send_invitation_rejects_user_without_email(
        self, staff, project, settings
    ):
        settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
        mail.outbox = []
        u = User.objects.create_user("noemail", "", "x", first_name="No", last_name="Mail")
        Profile.objects.get_or_create(user=u, defaults={"role": "client"})
        access = _grant(u, project)
        c = Client()
        c.force_login(staff)
        resp = c.post(
            reverse("project_send_invitation", args=[project.id, access.id])
        )
        assert resp.status_code == 302  # redirects with error message
        assert len(mail.outbox) == 0
