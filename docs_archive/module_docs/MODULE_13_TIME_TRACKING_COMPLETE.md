# Module 13: Time Tracking & Variance Analytics — Complete

This module adds a focused TimeEntry API and analytics actions that roll up time from tasks into daily plans and compute variance for planned activities.

## What’s included

- API endpoints for TimeEntry with actions:
  - stop: close an open time entry and compute hours
  - summary: aggregate total hours by employee, project, or task
- Analytics wiring
  - DailyPlan.recompute_actual_hours action: sums time from tasks converted from the plan’s activities
  - PlannedActivity.variance action: compares estimated vs actual hours (using model field or aggregated time entries of the converted task)
- Tests: `tests/test_module13_time_tracking_api.py` (5 passing)

Routes are registered in `core/api/urls.py` as `/api/v1/time-entries/`.

## Data flow

- Time entries may optionally link to a `Task`; when present, hours contribute to:
  - Task-level totals (via aggregation)
  - DailyPlan rollups when the task is linked via `converted_task` from a `PlannedActivity`
- Lunch deduction logic is applied at model level in `TimeEntry.save()`:
  - If an entry spans 12:30 and lasts at least 5 hours, 0.5h is deducted.

## Endpoints

All endpoints require authentication.

- List: GET `/api/v1/time-entries/?employee=..&project=..&date__gte=..&date__lte=..`
- Retrieve: GET `/api/v1/time-entries/{id}/`
- Create: POST `/api/v1/time-entries/`
- Update: PUT/PATCH `/api/v1/time-entries/{id}/`
- Delete: DELETE `/api/v1/time-entries/{id}/`
- Actions:
  - Stop a time entry: POST `/api/v1/time-entries/{id}/stop/` with optional `{ "end_time": "HH:MM[:SS]" }`
  - Summary by group: GET `/api/v1/time-entries/summary/?group=employee|project|task&project=<id>&employee=<id>`

Example create:
{
  "employee": 7,
  "project": 12,
  "task": 101,
  "date": "2025-11-25",
  "start_time": "08:00:00",
  "end_time": "13:30:00"
}

Response includes computed `hours_worked` (e.g., "5.00").

## Analytics actions

- DailyPlan: POST `/api/v1/daily-plans/{id}/recompute_actual_hours/`
  - Aggregates `hours_worked` from all time entries of tasks linked via `activities.converted_task`
  - Updates `actual_hours_worked` and returns the value and task count considered

- PlannedActivity: GET `/api/v1/planned-activities/{id}/variance/`
  - If `actual_hours` is not set on the activity, aggregates hours from `converted_task` time entries
  - Returns `variance_hours`, `variance_percentage`, `is_efficient`

## Serializer

- `TimeEntrySerializer` exposes computed helper fields:
  - `employee_name`, `project_name`, `task_title`

## Notes

- No migrations were needed for this module; it reuses existing `TimeEntry`.
- Summary endpoint returns totals as strings for JSON-safe decimal handling.

## Tests

- `tests/test_module13_time_tracking_api.py` validates:
  - Hours computation on create
  - Stop action behavior
  - Summary by task
  - Variance for planned activities
  - Daily plan rollup and productivity alignment

All tests pass locally as part of the focused run for this module.
