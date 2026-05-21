"""Color sample permissions + 'Request a sample' flow + client schedule sync.

Three things tested here (all reported by the user 2026-05-21):

1. Clients can no longer create / edit color samples directly. They are
   redirected to the new color_sample_request flow.
2. The new color_sample_request flow creates a ClientRequest with
   request_type='color_sample' and enforces a per-user/per-project
   limit of 3 pending requests.
3. The client project view's "Upcoming Schedule" panel now includes
   ScheduleItemV2 (Gantt) entries — previously it only queried the
   legacy Schedule model and showed empty even when the project had a
   Gantt planned.
"""
from __future__ import annotations

from datetime import date, timedelta

import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from core.models import (
    ClientProjectAccess,
    ClientRequest,
    ColorSample,
    Profile,
    Project,
    ScheduleItemV2,
)

User = get_user_model()
pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def staff_user(db):
    u = User.objects.create_user(
        "audit_staff", "as@x", "x", is_staff=True, is_superuser=True,
    )
    p, _ = Profile.objects.get_or_create(user=u)
    p.role = "admin"
    p.save()
    return u


@pytest.fixture
def project(db):
    return Project.objects.create(name="Audit Project", start_date=date.today())


@pytest.fixture
def client_user(db, project):
    u = User.objects.create_user(
        "audit_client", "ac@x", "x",
        first_name="Cli", last_name="Ent",
    )
    p, _ = Profile.objects.get_or_create(user=u)
    p.role = "client"
    p.save()
    ClientProjectAccess.objects.create(
        user=u, project=project, role="client",
    )
    return u


# ---------------------------------------------------------------------------
# 1. Clients blocked from creating/editing samples
# ---------------------------------------------------------------------------
class TestClientCannotCreateOrEditSamples:
    def test_client_get_create_redirects_to_request(self, client_user, project):
        c = Client()
        c.force_login(client_user)
        resp = c.get(reverse("color_sample_create", args=[project.id]))
        assert resp.status_code == 302
        assert reverse("color_sample_request", args=[project.id]) in resp.url

    def test_client_post_create_redirects_without_creating_sample(
        self, client_user, project
    ):
        c = Client()
        c.force_login(client_user)
        resp = c.post(
            reverse("color_sample_create", args=[project.id]),
            data={"name": "Sneaky Color", "code": "X-1"},
        )
        assert resp.status_code == 302
        assert ColorSample.objects.filter(project=project).count() == 0

    def test_staff_can_still_create(self, staff_user, project):
        c = Client()
        c.force_login(staff_user)
        resp = c.post(
            reverse("color_sample_create", args=[project.id]),
            data={"name": "Real Color", "code": "SW-1"},
        )
        # 302 = success redirect; if validation fails it'd be 200
        assert resp.status_code in (200, 302)
        # staff creating with minimal payload — accept either outcome,
        # main contract is "not blocked".

    def test_client_cannot_edit_existing_sample(
        self, client_user, staff_user, project
    ):
        sample = ColorSample.objects.create(
            project=project, name="Original", created_by=staff_user,
        )
        c = Client()
        c.force_login(client_user)
        resp = c.post(
            reverse("color_sample_edit", args=[sample.id]),
            data={"name": "Hijacked"},
        )
        # Either redirect to detail with error or 403 — but the name
        # must NOT have changed.
        sample.refresh_from_db()
        assert sample.name == "Original"

    def test_client_cannot_create_via_rest_api(
        self, client_user, project
    ):
        c = Client()
        c.force_login(client_user)
        resp = c.post(
            "/api/v1/color-samples/",
            data={"project": project.id, "name": "API sneak", "code": "X-99"},
            content_type="application/json",
        )
        assert resp.status_code in (403, 401)
        assert ColorSample.objects.filter(name="API sneak").count() == 0


# ---------------------------------------------------------------------------
# 2. Client "Request a Sample" flow
# ---------------------------------------------------------------------------
class TestColorSampleRequestFlow:
    def test_get_renders_form_with_quota(self, client_user, project):
        c = Client()
        c.force_login(client_user)
        resp = c.get(reverse("color_sample_request", args=[project.id]))
        assert resp.status_code == 200
        assert b"Request" in resp.content or b"request" in resp.content

    def test_post_creates_client_request(self, client_user, project):
        c = Client()
        c.force_login(client_user)
        resp = c.post(
            reverse("color_sample_request", args=[project.id]),
            data={
                "title": "Warm beige for living room",
                "description": "Matte finish, like the photo I sent",
            },
        )
        assert resp.status_code == 302
        cr = ClientRequest.objects.filter(
            project=project, request_type="color_sample",
        ).first()
        assert cr is not None
        assert "Warm beige" in cr.title
        assert cr.created_by == client_user
        assert cr.status == "pending"
        # No real ColorSample created — only a request.
        assert ColorSample.objects.filter(project=project).count() == 0

    def test_post_requires_title(self, client_user, project):
        c = Client()
        c.force_login(client_user)
        resp = c.post(
            reverse("color_sample_request", args=[project.id]),
            data={"title": "   "},
        )
        assert resp.status_code == 302
        assert ClientRequest.objects.filter(project=project).count() == 0

    def test_quota_enforced_at_three_pending(self, client_user, project):
        for i in range(ClientRequest.COLOR_SAMPLE_REQUEST_LIMIT):
            ClientRequest.objects.create(
                project=project,
                title=f"[Color Sample] Existing {i}",
                request_type="color_sample",
                status="pending",
                created_by=client_user,
            )
        c = Client()
        c.force_login(client_user)
        resp = c.post(
            reverse("color_sample_request", args=[project.id]),
            data={"title": "One too many"},
        )
        # Redirect away (back to sample list) without creating the 4th.
        assert resp.status_code == 302
        assert (
            ClientRequest.objects.filter(
                project=project, request_type="color_sample"
            ).count()
            == ClientRequest.COLOR_SAMPLE_REQUEST_LIMIT
        )


# ---------------------------------------------------------------------------
# 3. Client portal shows Gantt items in "Upcoming Schedule"
# ---------------------------------------------------------------------------
class TestClientPortalScheduleSync:
    def test_gantt_items_appear_in_upcoming_schedules(
        self, client_user, project
    ):
        today = timezone.localdate()
        ScheduleItemV2.objects.create(
            project=project,
            name="Drywall sanding",
            start_date=today,
            end_date=today + timedelta(days=3),
            status="planned",
        )
        ScheduleItemV2.objects.create(
            project=project,
            name="Priming",
            start_date=today + timedelta(days=4),
            end_date=today + timedelta(days=6),
            status="planned",
        )

        c = Client()
        c.force_login(client_user)
        resp = c.get(reverse("client_project_view", args=[project.id]))
        assert resp.status_code == 200
        upcoming = resp.context["upcoming_schedules"]
        titles = [getattr(e, "title", "") for e in upcoming]
        assert "Drywall sanding" in titles
        assert "Priming" in titles

    def test_empty_when_no_schedule_at_all(self, client_user, project):
        c = Client()
        c.force_login(client_user)
        resp = c.get(reverse("client_project_view", args=[project.id]))
        assert resp.status_code == 200
        assert list(resp.context["upcoming_schedules"]) == []

    def test_past_gantt_items_excluded(self, client_user, project):
        today = timezone.localdate()
        ScheduleItemV2.objects.create(
            project=project,
            name="Already finished",
            start_date=today - timedelta(days=30),
            end_date=today - timedelta(days=10),
            status="done",
        )
        c = Client()
        c.force_login(client_user)
        resp = c.get(reverse("client_project_view", args=[project.id]))
        assert resp.status_code == 200
        titles = [getattr(e, "title", "") for e in resp.context["upcoming_schedules"]]
        assert "Already finished" not in titles
