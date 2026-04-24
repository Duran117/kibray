"""
Guard tests for the Celery beat_schedule.

These tests would have caught the Phase C bug (12 ghost tasks scheduled
against names that did not exist in core/tasks.py) at CI time. They are
lightweight and import-only — no broker required.
"""

from __future__ import annotations

import pytest

from kibray_backend.celery_config import app

# Force task registration. autodiscover only runs when Celery app starts; in
# pure unit tests we import the tasks module explicitly so app.tasks is
# populated before the asserts below.
import core.tasks  # noqa: F401


def test_beat_schedule_is_non_empty() -> None:
    """Sanity: we have at least one scheduled task."""
    assert app.conf.beat_schedule, "beat_schedule must not be empty"


def test_every_beat_entry_resolves_to_registered_task() -> None:
    """
    Each beat entry's `task` field must match a registered Celery task.

    Catches typos and "ghost" task names that previously caused
    silent NotRegistered errors in production.
    """
    registered = set(app.tasks.keys())
    bad: list[tuple[str, str]] = []
    for beat_name, entry in app.conf.beat_schedule.items():
        task_name = entry["task"]
        if task_name not in registered:
            bad.append((beat_name, task_name))

    assert not bad, (
        "Beat schedule references unregistered tasks (ghosts):\n"
        + "\n".join(f"  - {name!r} -> {task!r}" for name, task in bad)
    )


def test_every_beat_entry_has_a_schedule() -> None:
    """Each entry must declare a 'schedule' (crontab or numeric seconds)."""
    missing = [name for name, entry in app.conf.beat_schedule.items() if "schedule" not in entry]
    assert not missing, f"beat entries missing 'schedule' key: {missing}"


def test_no_duplicate_task_targets_in_schedule() -> None:
    """
    Soft check: a beat task should not be scheduled under two different names
    unless intentional. Currently we expect zero duplicates.
    """
    seen: dict[str, str] = {}
    duplicates: list[tuple[str, str, str]] = []
    for beat_name, entry in app.conf.beat_schedule.items():
        task = entry["task"]
        if task in seen:
            duplicates.append((task, seen[task], beat_name))
        else:
            seen[task] = beat_name
    assert not duplicates, (
        "A task is scheduled under multiple beat names:\n"
        + "\n".join(f"  - {t!r} via {a!r} and {b!r}" for t, a, b in duplicates)
    )


@pytest.mark.parametrize(
    "expected_task",
    [
        # Spot-check a few that must remain scheduled. If any of these is
        # removed the test forces an explicit decision in the PR.
        "core.tasks.check_overdue_invoices",
        "core.tasks.update_invoice_statuses",
        "core.tasks.send_pending_notifications",
        "core.tasks.cleanup_old_notifications",
        "core.tasks.cleanup_stale_user_status",
    ],
)
def test_critical_tasks_are_scheduled(expected_task: str) -> None:
    scheduled_tasks = {entry["task"] for entry in app.conf.beat_schedule.values()}
    assert (
        expected_task in scheduled_tasks
    ), f"{expected_task!r} dropped from beat_schedule — was that intentional?"
