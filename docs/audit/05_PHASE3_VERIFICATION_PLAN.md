## PHASE 3 — VERIFICATION PLAN (targeted checks)

Generated: 2025-11-28

Goal
- Perform 10 focused requirement→implementation verifications using anchors to confirm behavior and edge cases; spin off micro-PRs when gaps are found.

Checks (10 targets)
1) Tasks: status transitions and reopen
   - Files: `core/models.py:Task` (~541), `tests/test_task_reopen.py`
   - Verify: allowed transitions, audit trail via `TaskStatusChange`.

2) Tasks: dependencies and Gantt
   - Files: `core/models.py:TaskDependency` (~857), `core/api/views.py:TaskGanttView`
   - Verify: no cycles allowed; ordering logic reflected in API.

3) Tasks: image versioning
   - Files: `core/models.py:TaskImage` (~933), `tests/test_task_images.py`
   - Verify: prior versions remain accessible; latest pointer updates.

4) Daily Plan → Task conversion
   - Files: `core/models.py:DailyPlan` (~4848), `tests/test_module12_dailyplan_api.py`
   - Verify: conversion creates tasks with correct assignees and dates.

5) SOP search and usage
   - Files: `core/models.py:ActivityTemplate` (~4622), `tests/test_module29_activity_templates.py`
   - Verify: fuzzy search and filtering; consider adding boundary tests.

6) Materials → Inventory integration
   - Files: `core/models.py:MaterialRequest` (~2489), `InventoryMovement` (~4450)
   - Verify: receiving requests updates inventory consistently.

7) Inventory thresholds and alerts
   - Files: `core/models.py:InventoryItem` (~4226)
   - Verify: low-stock detection paths; if missing, add tests.

8) Payroll record lifecycle
   - Files: `core/models.py:PayrollRecord` (~1451), `core/api/views.py:PayrollRecordViewSet`
   - Verify: draft→reviewed→paid flow; manual adjustments auditing.

9) Client requests and attachments
   - Files: `core/models.py:ClientRequest` (~2822), `ClientRequestAttachment` (~2853)
   - Verify: permissions and visibility per project scoping.

10) Site photos filtering and privacy
   - Files: `core/models.py:SitePhoto` (~3043), `core/api/views.py:SitePhotoViewSet`
   - Verify: privacy flags and date filters; pagination handling.

Execution
- Owner(s) pick 3–5 checks each; record outcomes inline below each item.
- For any gap found, open a small PR with a failing test first, then implementation.

Outcomes log
- (pending)
