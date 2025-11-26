# Floor Plan Pins: UX and Guardrails

Date: 2025-11-25

This document outlines the multi-purpose Floor Plan pin behavior, creator/viewer UX split, and guardrails for auto-creating tasks.

## Pin Types and Behaviors

- note: Informational pin. No task auto-creation.
- color: Color-related pin. No task auto-creation. Can link to ColorSample.
- touchup: Triggers a Task with `is_touchup=True`, medium priority by default.
- alert: Triggers a Task (issue) with medium priority and PM notification.
- damage: Triggers a Task (issue) with high priority and PM notification.

## Auto-Task Creation

Implemented in `core/models.py:PlanPin.save()`:
- On create, if `pin_type` in [touchup, alert, damage] and no `linked_task`, a Task is created and linked.
- Tasks are created in the pin's plan project with a generated title and description including coordinates.
- Touch-up tasks have `is_touchup=True` for use on the Touch-up Board.
- Alerts and damages also trigger notifications to Project Managers.

## UX Split

- Creators:
  - Pins (note, alert, damage, color) are created via Floor Plan UI.
  - Touch-ups should be reviewed in the Touch-up Board (Tasks-only Kanban), not directly on the plan list.
- Viewers:
  - Floor Plan shows pins with type badges and optional attachments.
  - Touch-up Board provides workflow for `is_touchup=True` tasks.

## Guardrails

- Only [touchup, alert, damage] auto-create tasks. `note` and `color` never auto-create.
- `pin_type` is validated via model `choices`.
- `linked_task` is set only when auto-creating or explicitly linking; no implicit link for non-issue pins.

## Legacy TouchUpPin

- UI routes are gated behind the feature flag `TOUCHUP_PIN_ENABLED` (default: False).
- Use Task-based Touch-up Board instead (`core/api/views.py:touchup_board`).

## Testing

- See `tests/test_module28_touchups_board_api.py` and `tests/test_pin_detail_ajax.py`.
- Full suite validates task auto-creation and notifications.

