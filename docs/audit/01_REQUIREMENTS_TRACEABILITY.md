## PHASE 1 — REQUIREMENTS → CODE TRACEABILITY

Generated: 2025-11-28

Purpose
- Produce an initial, machine-readable and human-friendly traceability map from the canonical requirements documents to candidate implementation files and tests.

Methodology
- Source documents examined: `REQUIREMENTS_DOCUMENTATION.md`, `CLARIFICATION_QUESTIONS_MODULES_11-27.md`, `PANEL_REORGANIZATION_COMPLETE.md`.
- Automated heuristics used: case-insensitive token search for model/view/serializer names and matching tests. Evidence includes model definitions, API viewsets, serializers, forms and tests.
- This is an initial, conservative mapping: "Candidate implementation" means the repo contains code that appears to implement the requirement; further manual review may be needed to confirm behavior and edge cases.

Summary (Modules 11–19)

Module 11 — Tasks
- Requirements: task CRUD, priorities, dependencies, image versioning, touch-up separation, time tracking, comments, reopen, notifications.
- Candidate implementation files:
  - `core/models.py` — `Task`, `TaskDependency`, `TaskImage`, `TaskStatusChange`, `TaskTemplate` (lines ~541, 857, 933, 960, 986)
  - `core/api/views.py` — `TaskViewSet`, `TaskDependencyViewSet`, `TaskGanttView` (views)
  - `core/api/serializers.py` — `TaskSerializer`, `TaskDependencySerializer`
  - `core/forms.py` — `TaskForm`
  - Tests: `tests/test_module_11_tasks.py`, `tests/test_module_11_signals.py`, `tests/test_module11_tasks_api.py` (multiple test classes)
  - Admin: `core/admin.py` (TaskTemplateAdmin, RecurringTaskAdmin)

Module 12 — Daily Plans
- Requirements: daily plan creation, conversion to tasks, historical plans, weather, editable after publish.
- Candidate implementation files:
  - `core/models.py` — `DailyPlan`, `ActivityTemplate`, `RecurringTask`
  - `core/consumers.py` / `core/consumers_fixed.py` — `DailyPlanConsumer` (websocket consumer)
  - `core/api/views.py` — `DailyPlanViewSet`
  - `core/api/serializers.py` — `DailyPlanSerializer`
  - Tests: `tests/test_module_12_daily_plans.py`, `tests/test_time_daily_sop_workflows.py`

Module 13 — SOPs (Activity templates)
- Requirements: SOP catalog, versioning, checklists, search.
- Candidate implementation files:
  - `core/models.py` — `ActivityTemplate`, `TaskTemplate` (ActivityTemplate alias)
  - `core/forms.py` — `ActivityTemplateForm`
  - `core/admin.py` — `ActivityTemplateAdmin`, `SOPReferenceFileAdmin`
  - Tests: `tests/test_module29_activity_templates.py`

Module 14 — Materials
- Requirements: material catalog, requests, approvals, inventory linkage.
- Candidate implementation files:
  - `core/models.py` — `MaterialRequest`, `MaterialRequestItem`, `MaterialCatalog`
  - `core/api/views.py` — `MaterialRequestViewSet`, `MaterialCatalogViewSet`
  - Admin: `core/admin.py` — `MaterialRequestAdmin`, `MaterialCatalogAdmin`

Module 15 — Inventory
- Requirements: inventory item, movements, transfers, thresholds and alerts.
- Candidate implementation files:
  - `core/models.py` — `InventoryItem`, `InventoryMovement`
  - `core/api/views.py` — `InventoryItemViewSet`, `InventoryMovementViewSet`
  - Forms: `core/forms.py` — `InventoryMovementForm`
  - Tests: `tests/test_module15_inventory_api.py`

Module 16 — Payroll
- Requirements: payroll records, period handling, manual edits, export.
- Candidate implementation files:
  - `core/models.py` — `PayrollRecord`
  - `core/api/views.py` — `PayrollRecordViewSet`
  - `core/forms.py` — `PayrollRecordForm`

Module 17 — Clients
- Requirements: client creation, access control, requests and attachments, project-scoped access.
- Candidate implementation files:
  - `core/models.py` — `ClientRequest`, `ClientRequestAttachment`, `ClientProjectAccess`
  - `core/forms.py` — `ClientCreationForm`, `ClientEditForm`
  - `core/api/views.py` — `ClientRequestViewSet`, `ClientRequestAttachmentViewSet`

Module 18 — Site Photos
- Requirements: upload, versioning, GPS metadata, privacy flags, thumbnails.
- Candidate implementation files:
  - `core/models.py` — `SitePhoto`, `TouchUpCompletionPhoto`
  - `core/forms.py` — `SitePhotoForm`, `TouchUpCompletionForm`
  - `core/api/views.py` — `SitePhotoViewSet`
  - Tests: `tests/test_site_photos_api.py`, other photo-related tests

Module 19 — Color Samples / Approvals
- Requirements: samples lifecycle, approvals (digital signature requested), grouping, legal export.
- Candidate implementation files:
  - `core/models.py` and API endpoints include color/approval fields; see `REQUIREMENTS_DOCUMENTATION.md` and `PANEL_REORGANIZATION_COMPLETE.md` for flow. Tests and UI references exist in `tests/` and `templates`.

Notes & assumptions
- Where migrations reference a model (e.g. `core/migrations/00xx_*`) that confirms historical implementation; the presence of viewsets/serializers + tests indicates a mature feature.
- This document is intentionally conservative: it lists candidate implementation artifacts for manual verification.

Next steps (recommended)
1. Manual verification: for each mapped requirement, open the model, view and tests and confirm exact behavior (edge cases: permissions, notifications, workflow approvals).
2. For items marked in the gaps backlog create issues and, where low-risk, small PRs.
3. Add unique requirement IDs to `REQUIREMENTS_DOCUMENTATION.md` (anchorable headings) to simplify machine mapping in future runs.

Artifacts referenced by this traceability run
- `docs/audit/02_COMPLETION_MATRIX.md` — generated alongside this traceability file (high-level implementation status)
- `docs/audit/03_GAPS_BACKLOG.md` — prioritized backlog for missing/partial features

Generated-by: automated audit pass (local repo scan)
