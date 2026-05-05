"""
Phase 9 Commit D — regression tests proving DRF serializer write-side
scoping via AccessibleProjectField.

Closes the write side of gap G3: legacy serializers used
``serializers.PrimaryKeyRelatedField(queryset=Project.objects.all())``,
which let any authenticated user POST a Task / ChangeOrder /
ScheduleItemV2 attaching it to ANY project's id.

The 3 affected serializers are now backed by AccessibleProjectField,
which scopes the queryset per request.user via core.access.

World setup mirrors Commit C's:
  - admin    (sees all)
  - pm_a     (PM assigned only to project A)
  - emp_b    (employee with TimeEntry only on B)
  - client_c (client with ClientProjectAccess only on C)
"""
from __future__ import annotations

from datetime import date

import pytest
from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework.test import APIRequestFactory, force_authenticate

from core.api.serializer_classes.access_fields import AccessibleProjectField


class _FieldWrap(serializers.Serializer):
    """Minimal serializer to bind AccessibleProjectField for direct tests."""
    project = AccessibleProjectField(allow_null=True, required=False)


def _bound_field(context):
    return _FieldWrap(context=context).fields["project"]
from core.api.serializer_classes.changeorder_serializers import (
    ChangeOrderCreateUpdateSerializer,
)
from core.api.serializer_classes.schedule_v2_serializers import (
    ScheduleItemV2WriteSerializer,
)
from core.api.serializer_classes.task_serializers import TaskCreateUpdateSerializer
from core.models import (
    ClientProjectAccess,
    Employee,
    Project,
    ProjectManagerAssignment,
    TimeEntry,
)

User = get_user_model()


def _mk_user(username, *, role=None, is_staff=False, is_superuser=False):
    u = User.objects.create_user(
        username=username, password="x",
        is_staff=is_staff, is_superuser=is_superuser,
    )
    if role:
        u.profile.role = role
        u.profile.save()
    return u


@pytest.fixture
def world():
    p_a = Project.objects.create(name="D-Proj-A", start_date=date.today())
    p_b = Project.objects.create(name="D-Proj-B", start_date=date.today())
    p_c = Project.objects.create(name="D-Proj-C", start_date=date.today())

    admin = _mk_user("d_admin", role="admin", is_staff=True, is_superuser=True)

    pm_a = _mk_user("d_pm_a", role="project_manager")
    ProjectManagerAssignment.objects.create(project=p_a, pm=pm_a, role="pm")

    emp_b = _mk_user("d_emp_b", role="employee")
    e = Employee.objects.create(
        user=emp_b, first_name="E", last_name="B",
        social_security_number="D-22-22", hourly_rate=20,
    )
    TimeEntry.objects.create(
        employee=e, project=p_b, date=date.today(), start_time="08:00",
    )

    client_c = _mk_user("d_client_c", role="client")
    ClientProjectAccess.objects.create(
        user=client_c, project=p_c, role="viewer", is_active=True,
    )

    return {
        "p_a": p_a, "p_b": p_b, "p_c": p_c,
        "admin": admin, "pm_a": pm_a, "emp_b": emp_b, "client_c": client_c,
        "employee": e,
    }


def _request_for(user):
    """Build a fake DRF request authenticated as the given user."""
    factory = APIRequestFactory()
    req = factory.post("/")
    if user is not None:
        force_authenticate(req, user=user)
        # APIRequestFactory.force_authenticate marks the django HttpRequest;
        # serializers expect a DRF Request — wrap via the view machinery's
        # simpler shortcut: just set .user directly.
        req.user = user
    return req


# ─────────────── AccessibleProjectField (low-level) ───────────────
class TestAccessibleProjectFieldDirect:
    def test_no_context_returns_empty(self):
        f = _bound_field(context={})
        assert list(f.get_queryset()) == []

    def test_anonymous_request_returns_empty(self, world):
        factory = APIRequestFactory()
        req = factory.post("/")
        # Default Django HttpRequest has no .user; getattr fallback → None.
        f = _bound_field(context={"request": req})
        assert list(f.get_queryset()) == []

    def test_admin_sees_all(self, world):
        f = _bound_field(context={"request": _request_for(world["admin"])})
        ids = set(f.get_queryset().values_list("pk", flat=True))
        assert ids == {world["p_a"].pk, world["p_b"].pk, world["p_c"].pk}

    def test_pm_sees_only_assigned(self, world):
        f = _bound_field(context={"request": _request_for(world["pm_a"])})
        ids = set(f.get_queryset().values_list("pk", flat=True))
        assert ids == {world["p_a"].pk}

    def test_client_sees_only_own(self, world):
        f = _bound_field(context={"request": _request_for(world["client_c"])})
        ids = set(f.get_queryset().values_list("pk", flat=True))
        assert ids == {world["p_c"].pk}


# ─────────────── TaskCreateUpdateSerializer ───────────────
class TestTaskSerializerScoping:
    def _payload(self, project_id):
        return {"title": "x", "project": project_id}

    def test_admin_can_post_to_any_project(self, world):
        ctx = {"request": _request_for(world["admin"])}
        for p in (world["p_a"], world["p_b"], world["p_c"]):
            s = TaskCreateUpdateSerializer(data=self._payload(p.pk), context=ctx)
            s.is_valid()
            assert "project" not in s.errors, (
                f"admin rejected on p={p.pk}: {s.errors}"
            )

    def test_pm_can_post_to_assigned_project(self, world):
        ctx = {"request": _request_for(world["pm_a"])}
        s = TaskCreateUpdateSerializer(
            data=self._payload(world["p_a"].pk), context=ctx
        )
        s.is_valid()
        assert "project" not in s.errors

    def test_pm_cannot_post_to_unassigned_project(self, world):
        """G3 write-side: PM_A must NOT be able to attach a Task to project B."""
        ctx = {"request": _request_for(world["pm_a"])}
        s = TaskCreateUpdateSerializer(
            data=self._payload(world["p_b"].pk), context=ctx
        )
        s.is_valid()
        assert "project" in s.errors

    def test_client_cannot_post_to_other_clients_project(self, world):
        """Cross-tenant: client_c must NOT be able to create a Task on project A."""
        ctx = {"request": _request_for(world["client_c"])}
        s = TaskCreateUpdateSerializer(
            data=self._payload(world["p_a"].pk), context=ctx
        )
        s.is_valid()
        assert "project" in s.errors

    def test_employee_cannot_post_to_unworked_project(self, world):
        ctx = {"request": _request_for(world["emp_b"])}
        s = TaskCreateUpdateSerializer(
            data=self._payload(world["p_c"].pk), context=ctx
        )
        s.is_valid()
        assert "project" in s.errors

    def test_no_context_rejects_all(self, world):
        """Fail-closed: no request context → every project id rejected."""
        s = TaskCreateUpdateSerializer(
            data=self._payload(world["p_a"].pk), context={}
        )
        s.is_valid()
        assert "project" in s.errors


# ─────────────── ChangeOrderCreateUpdateSerializer ───────────────
class TestChangeOrderSerializerScoping:
    def _payload(self, project_id):
        return {
            "project": project_id,
            "description": "x",
            "amount": "100.00",
        }

    def test_admin_can_post_to_any_project(self, world):
        ctx = {"request": _request_for(world["admin"])}
        for p in (world["p_a"], world["p_b"], world["p_c"]):
            s = ChangeOrderCreateUpdateSerializer(
                data=self._payload(p.pk), context=ctx
            )
            s.is_valid()
            assert "project" not in s.errors, (
                f"admin rejected on p={p.pk}: {s.errors}"
            )

    def test_pm_can_post_to_assigned_project(self, world):
        ctx = {"request": _request_for(world["pm_a"])}
        s = ChangeOrderCreateUpdateSerializer(
            data=self._payload(world["p_a"].pk), context=ctx
        )
        s.is_valid()
        assert "project" not in s.errors

    def test_pm_cannot_post_to_unassigned_project(self, world):
        ctx = {"request": _request_for(world["pm_a"])}
        s = ChangeOrderCreateUpdateSerializer(
            data=self._payload(world["p_b"].pk), context=ctx
        )
        s.is_valid()
        assert "project" in s.errors

    def test_client_cannot_attach_change_order_to_other_project(self, world):
        ctx = {"request": _request_for(world["client_c"])}
        s = ChangeOrderCreateUpdateSerializer(
            data=self._payload(world["p_a"].pk), context=ctx
        )
        s.is_valid()
        assert "project" in s.errors


# ─────────────── ScheduleItemV2WriteSerializer ───────────────
class TestScheduleItemV2SerializerScoping:
    def _payload(self, project_id):
        # ScheduleItemV2 minimal payload — project nullable so we always pass it
        # explicitly to validate the field-level queryset scoping.
        return {
            "project": project_id,
            "title": "x",
        }

    def test_admin_can_post_to_any_project(self, world):
        ctx = {"request": _request_for(world["admin"])}
        for p in (world["p_a"], world["p_b"], world["p_c"]):
            s = ScheduleItemV2WriteSerializer(data=self._payload(p.pk), context=ctx)
            # We only assert that the project field passes validation; other
            # required fields may still raise — so check the project key
            # specifically rather than overall is_valid().
            s.is_valid()
            assert "project" not in s.errors, (
                f"admin rejected on p={p.pk}: {s.errors}"
            )

    def test_pm_cannot_post_to_unassigned_project(self, world):
        ctx = {"request": _request_for(world["pm_a"])}
        s = ScheduleItemV2WriteSerializer(
            data=self._payload(world["p_b"].pk), context=ctx
        )
        s.is_valid()
        assert "project" in s.errors

    def test_pm_can_post_to_assigned_project(self, world):
        ctx = {"request": _request_for(world["pm_a"])}
        s = ScheduleItemV2WriteSerializer(
            data=self._payload(world["p_a"].pk), context=ctx
        )
        s.is_valid()
        assert "project" not in s.errors

    def test_client_cannot_attach_to_other_project(self, world):
        ctx = {"request": _request_for(world["client_c"])}
        s = ScheduleItemV2WriteSerializer(
            data=self._payload(world["p_a"].pk), context=ctx
        )
        s.is_valid()
        assert "project" in s.errors

    def test_null_project_allowed_when_user_anonymous_context_missing(self, world):
        """allow_null=True: omitting project entirely should not produce a
        'project not in queryset' error even with no context."""
        s = ScheduleItemV2WriteSerializer(data={"title": "x"}, context={})
        s.is_valid()
        assert "project" not in s.errors
