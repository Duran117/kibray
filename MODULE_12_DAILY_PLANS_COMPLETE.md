# Module 12: Daily Plans API — Complete

This module introduces Daily Plans and Planned Activities to enforce next‑day planning, capture weather context, and convert planned work into real project tasks.

## What’s included

- Models: DailyPlan, PlannedActivity (plus ActivityCompletion helper)
- Endpoints: CRUD + actions to fetch weather, add activities, convert to tasks, compute productivity, and check materials
- Serializers: DailyPlanSerializer, PlannedActivitySerializer with write‑only assigned_employee_ids
- Routes: `/api/daily-plans/` and `/api/planned-activities/` registered in `core/api/urls.py`

## Data model (high‑level)

- DailyPlan
  - project, plan_date, status (DRAFT/PUBLISHED/IN_PROGRESS/COMPLETED/SKIPPED)
  - completion_deadline, created_by, timestamps
  - weather_data, weather_fetched_at
  - no_planning_reason, admin_approved (+ approver, approved_at)
  - actual_hours_worked, estimated_hours_total
  - Methods: is_overdue(), fetch_weather(), convert_activities_to_tasks(), calculate_productivity_score(), auto_consume_materials()
- PlannedActivity
  - daily_plan (FK), title, description, order
  - assigned_employees (M2M), is_group_activity
  - estimated_hours, actual_hours
  - materials_needed (JSON list of strings), materials_checked, material_shortage
  - Links: schedule_item (optional), activity_template (optional), converted_task (optional)
  - Methods: get_time_variance(), check_materials()

See `core/models.py` for complete definitions and inline docs.

## Endpoints

All endpoints require authentication (IsAuthenticated). Standard CRUD is available for both resources via DRF viewsets.

### Daily Plans

- List: GET `/api/daily-plans/?project=<id>&status=<STATUS>`
- Retrieve: GET `/api/daily-plans/{id}/`
- Create: POST `/api/daily-plans/`
- Update: PUT/PATCH `/api/daily-plans/{id}/`
- Delete: DELETE `/api/daily-plans/{id}/`
- Actions:
  - Fetch weather: POST `/api/daily-plans/{id}/fetch_weather`
  - Convert planned activities to tasks: POST `/api/daily-plans/{id}/convert_activities`
  - Productivity score: GET `/api/daily-plans/{id}/productivity`
  - Add activity: POST `/api/daily-plans/{id}/add_activity`

Filters: `project`, `plan_date`, `status`, `admin_approved`
Ordering: `plan_date`, `created_at`, `updated_at` (default `-plan_date`)

#### Create Daily Plan (example)

Request JSON:
{
  "project": 12,
  "plan_date": "2025-11-26",
  "completion_deadline": "2025-11-25T17:00:00Z",
  "status": "DRAFT",
  "estimated_hours_total": 8.0
}

Response 201 contains the plan plus derived fields:
- `project_name`, `is_overdue`, `productivity_score`, nested `activities` (empty initially)

#### Fetch Weather

POST `/api/daily-plans/{id}/fetch_weather`

- Uses `DailyPlan.fetch_weather()` (lat/lon placeholder until geocoding is added)
- Requires `project.address`; returns 400 if not set or provider fails
- Response: `{ "weather": { ... }, "weather_fetched_at": "..." }`

#### Add Activity to a Plan

POST `/api/daily-plans/{id}/add_activity`

Body fields (all optional unless noted):
- title (required), description, order
- assigned_employee_ids: [int, ...] (write‑only; sets M2M)
- is_group_activity (default true)
- estimated_hours, actual_hours
- materials_needed: ["Paint:White:2gal", "Tape:3roll", ...]
- schedule_item (id), activity_template (id)

Response: PlannedActivity with computed fields: `assigned_employee_names`, `schedule_item_title`, `activity_template_name`, `converted_task_id`.

#### Convert Activities to Tasks

POST `/api/daily-plans/{id}/convert_activities`

- Skips activities already marked `COMPLETED`
- Creates `Task` objects linked to the plan’s project
- Assigns first listed employee to each created task (simple rule; can be extended)
- Links back via `PlannedActivity.converted_task`
- Response: `{ "created_count": N, "tasks": [ ... ] }`

#### Productivity Score

GET `/api/daily-plans/{id}/productivity`

- Returns `{ "productivity_score": <number|null> }`
- Score = estimated_hours_total / actual_hours_worked * 100

### Planned Activities

- List: GET `/api/planned-activities/?daily_plan=<id>&status=<STATUS>`
- Retrieve: GET `/api/planned-activities/{id}/`
- Create: POST `/api/planned-activities/`
- Update: PUT/PATCH `/api/planned-activities/{id}/`
- Delete: DELETE `/api/planned-activities/{id}/`
- Actions:
  - Check materials availability: POST `/api/planned-activities/{id}/check_materials`

Filters: `daily_plan`, `status`
Search: `title`, `description`
Ordering: `order`, `created_at`, `updated_at` (default `order`)

#### Materials Check

POST `/api/planned-activities/{id}/check_materials`

- Parses `materials_needed` strings into name and quantities (robust to format issues)
- Looks up project inventory and sets `materials_checked` and `material_shortage`
- Appends shortage details to `description` if shortages are detected
- Response: `{ materials_checked, material_shortage, description }`

## Serializer notes

- PlannedActivitySerializer
  - Write: `assigned_employee_ids` (list[int])
  - Read: `assigned_employee_names`, `schedule_item_title`, `activity_template_name`, `converted_task_id`
- DailyPlanSerializer
  - Read: `project_name`, `is_overdue`, `productivity_score`, nested `activities`

## Compatibility and assumptions

- Weather provider is accessed via `core.services.weather.weather_service`; geocoding for project address is TBD. If no address, `fetch_weather` returns 400 with message.
- Converting activities to tasks uses a simple first-employee assignment rule; adjust business logic as needed.
- Inventory checks rely on `InventoryItem`, `InventoryLocation`, and `ProjectInventory` models being present.

## Quick test ideas

- Create a plan, add one or two activities, run `check_materials`, then `convert_activities`, and verify tasks were created.
- Set `estimated_hours_total` and `actual_hours_worked` to validate `productivity` result.
- Set `project.address` and call `fetch_weather` to store weather data.

## References

- Routes: `core/api/urls.py`
- Views: `core/api/views.py` — `DailyPlanViewSet`, `PlannedActivityViewSet`
- Serializers: `core/api/serializers.py`
- Models: `core/models.py`
