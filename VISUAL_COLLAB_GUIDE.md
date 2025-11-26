# Visual & Collaboration Guide

This guide covers the Visual & Collaboration stack: Site Photos, Color Samples, Floor Plans & Pins, and Damage Reports. It includes API endpoints, workflow details, and quick usage tips.

## Site Photos

- Model: `core.models.SitePhoto`
- Key fields:
  - `project` (FK), `image`, `thumbnail` (auto), `caption`, `notes`
  - GPS: `location_lat`, `location_lng`, `location_accuracy_m`
  - Linkage: `damage_report` (FK), `photo_type` (before/progress/after/defect/reference)
  - Metadata: `created_by`, `created_at`
- Endpoints:
  - POST `/api/v1/site-photos/` (multipart or JSON)
  - GET `/api/v1/site-photos/?project={id}&damage_report={id}&photo_type=...&start=YYYY-MM-DD&end=YYYY-MM-DD`
- Notes:
  - Serializer attempts EXIF GPS extraction if image contains GPS data.
  - API accepts test bytes for `image` to simplify automated tests.

Example upload (multipart):
- Fields: `project`, `image`, optional `caption`, `location_lat`, `location_lng`, `location_accuracy_m`, `damage_report`

## Color Samples

- Model: `core.models.ColorSample`
- Workflow:
  - Status: `proposed` → `review` → `approved` or `rejected`
  - KPISM-like numbering in `sample_number` (e.g., `ACMEM10001`)
  - Approval generates `approval_signature` and stores `approval_ip`
- Endpoints:
  - GET `/api/v1/color-samples/`
  - POST `/api/v1/color-samples/{id}/approve/` `{ signature_ip?: string }`
  - POST `/api/v1/color-samples/{id}/reject/` `{ reason: string }`
- Response fields include: `sample_number`, `version`, `approved_by`, `approved_at`, `approval_signature`, `rejected_by`, `rejected_at`.

## Floor Plans & Pins

- Models: `core.models.FloorPlan`, `core.models.PlanPin`
- Highlights:
  - Pins: normalized coordinates (`x`,`y`) 0..1, types: note/touchup/color/alert/damage
  - Auto-task creation for `touchup`, `alert`, `damage`
  - Versioning for floor plans; pins support migration linkages
  - Client comments supported on pins (`client_comments` JSON array)
- Endpoints:
  - GET `/api/v1/floor-plans/` (pagination disabled; includes pins)
  - GET `/api/v1/plan-pins/?plan={id}&pin_type=damage` (pagination disabled)
  - POST `/api/v1/plan-pins/{id}/comment/` `{ comment: string }`

## Damage Reports

- Model: `core.models.DamageReport`
- Fields:
  - `project`, optional `plan` and `pin`
  - `title`, `description`, `category` (structural/cosmetic/safety/electrical/plumbing/hvac/other)
  - `severity` (low/medium/high/critical), `status` (open/in_progress/resolved)
  - `estimated_cost`, `assigned_to`, audit timestamps, auto-created `auto_task`
- Evidence:
  - `core.models.DamagePhoto` with `image`, `notes`
- Endpoints:
  - CRUD: `/api/v1/damage-reports/`
  - POST `/api/v1/damage-reports/{id}/add_photo/` (multipart: `image`, optional `notes`)
  - GET `/api/v1/damage-reports/analytics/?project={id}` → `{ severity, status, category, total }`
- Behavior:
  - New open reports auto-create a repair task (`auto_task`)
  - Status transitions track `in_progress_at` and `resolved_at`

## Permissions & Client Portal

- Client users can be granted per-project access via `ClientProjectAccess (role, can_comment, can_create_tasks)`.
- API enforces visibility for client users on client-facing resources (e.g., Client Requests).

## Testing & Dev Tips

- Tests for each module are in `tests/`, including API and integration cases.
- Image uploads in tests can use placeholder bytes for simplicity.
- Pagination is disabled for high-traffic list endpoints (pins, plans, site photos) to simplify clients.

## Changelog (recent)

- Site Photos: GPS accuracy, damage report link, API filters.
- Color Samples: approvals with signature IP, KPISM numbering, approve/reject actions.
- Floor Plans: pin filters by type, comment action, pagination disabled.
- Damage Reports: categories, workflow, evidence attachments, analytics endpoint.
