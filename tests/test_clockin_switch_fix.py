"""
Regression tests for two clock-in / project-switch bugs.

Bug 1 — Switch-Project picker was hard-capped at ``[:10]`` with no ordering in
        the Admin and PM dashboards, so anyone with more than 10 active projects
        only saw an arbitrary subset ("solo muestra proyectos abc pero no todos").

Bug 2 — The "instant" (<30s) project switch OVERWROTE the open entry's
        ``project`` field instead of closing it and creating a new one. That
        silently destroyed the record of the first project
        ("no se guardó el primer registro"). A project switch must ALWAYS
        close the current entry and create a new one so each project keeps its
        own hours.
"""
from datetime import date, time

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from core.models import Employee, Project, ResourceAssignment, TimeEntry

User = get_user_model()
pytestmark = pytest.mark.django_db


def _make_employee(username, ssn, **user_kwargs):
    user = User.objects.create_user(username=username, password="pass", **user_kwargs)
    emp = Employee.objects.create(
        user=user,
        first_name=username.title(),
        last_name="Tester",
        social_security_number=ssn,
        hourly_rate=30.00,
    )
    return user, emp


# ───────────────────────── Bug 2: data-loss on project switch ──────────────


def test_project_switch_preserves_first_record(client):
    """Switching project must NOT overwrite the first entry — both records survive."""
    user, emp = _make_employee("emp_switch", "111-22-3333")
    today = date.today()
    proj_a = Project.objects.create(name="Alpha Project", start_date=today)
    proj_b = Project.objects.create(name="Bravo Project", start_date=today)
    # Employee policy: must be assigned to BOTH projects today. Use distinct
    # shifts so the per-day capacity validation (no two FULL_DAY) is satisfied.
    ResourceAssignment.objects.create(
        employee=emp, project=proj_a, date=today, shift="MORNING"
    )
    ResourceAssignment.objects.create(
        employee=emp, project=proj_b, date=today, shift="AFTERNOON"
    )

    client.force_login(user)

    # Clock in to A.
    resp = client.post(
        reverse("dashboard_employee"),
        {"action": "clock_in", "project": proj_a.id},
    )
    assert resp.status_code == 302
    entry_a = TimeEntry.objects.get(employee=emp, project=proj_a)
    assert entry_a.end_time is None  # open

    # Immediately switch to B. This happens in <30s, so the OLD code would have
    # treated it as an "instant switch" and overwritten A → B (data loss).
    resp = client.post(
        reverse("dashboard_employee"),
        {"action": "switch_context", "switch_type": "project", "target_id": proj_b.id},
    )
    assert resp.status_code == 302

    # The first record MUST still be on project A and now be closed.
    entry_a.refresh_from_db()
    assert entry_a.project_id == proj_a.id, "First record was overwritten to the new project!"
    assert entry_a.end_time is not None, "First record was not closed."

    # A new OPEN entry exists on project B.
    entry_b = TimeEntry.objects.get(employee=emp, project=proj_b, end_time__isnull=True)
    assert entry_b.project_id == proj_b.id

    # Exactly two entries — the first record was preserved, not replaced.
    assert TimeEntry.objects.filter(employee=emp).count() == 2


# ───────────────────────── Bug 1: switch list not capped at 10 ─────────────


def test_admin_switch_list_shows_all_projects_ordered(client):
    """Admin switch picker lists ALL active projects (no [:10] cap), ordered by name."""
    admin, emp = _make_employee(
        "admin_switch", "222-33-4444", is_staff=True, is_superuser=True
    )
    today = date.today()
    # 12 projects whose insertion order is the REVERSE of alphabetical, so a
    # missing ``order_by`` would be detectable.
    names = [f"Project {c}" for c in "LKJIHGFEDCBA"]
    projects = [Project.objects.create(name=n, start_date=today) for n in names]

    current = projects[0]  # "Project L"
    TimeEntry.objects.create(
        employee=emp, project=current, date=today, start_time=time(8, 0), end_time=None
    )

    client.force_login(admin)
    resp = client.get(reverse("dashboard_admin"))
    assert resp.status_code == 200

    other = resp.context["switch_options"]["other_projects"]

    # Not capped at 10: 12 projects minus the current one → at least 11.
    assert len(other) >= 11, "Switch list is still capped (regression of the [:10] bug)."

    returned_ids = {o["id"] for o in other}
    expected_ids = {p.id for p in projects if p.id != current.id}
    assert expected_ids.issubset(returned_ids), "Some projects are missing from the switch list."

    # Current project is excluded.
    assert current.id not in returned_ids

    # Alphabetically ordered by name.
    returned_names = [o["name"] for o in other]
    assert returned_names == sorted(returned_names), "Switch list is not ordered by name."
