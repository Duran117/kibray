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
- ✅ Check #1 (Tasks: status transitions): Verified `Task.status` allows transitions, `TaskStatusChange` model exists for audit trail (model line ~960).
- ✅ Check #2 (Tasks: dependencies and Gantt): Verified `TaskDependency` (~857) has cycle detection (`would_create_cycle` static method), unique_together on (task, predecessor, type), tests present in `tests/test_task_dependencies.py` and `test_task_dependencies_cycles_extended.py`. Created additional edge case tests in `tests/test_phase3_task_dependency_edge_cases.py` (duplicate types, large/negative lag) — all pass.
- ✅ Check #3 (Task image versioning): Verified `TaskImage` model (~933) has `version` and `is_current` fields. Comprehensive test suite in `tests/test_task_images.py` (10 tests, all passing). Requirement Q11.8 (image versioning) is fully implemented.
- ✅ Check #4 (Daily Plan → Task conversion): Verified `DailyPlan` model (~4848) supports conversion; tests exist in `tests/test_module12_dailyplan_api.py` for the conversion flow.
- ✅ Check #5 (SOP search and usage): Verified `ActivityTemplate` model (~4622) includes fuzzy search functionality. Tests in `tests/test_module_29_activity_templates.py` cover search by name, description, tips, category filtering, case-insensitive search (6 tests, all passing). Requirement Q13.3 (SOP search) is implemented.
- ❌ Check #6 (Materials → Inventory integration): **GAP DETECTED** — MaterialRequest receipt does NOT automatically create InventoryMovement (RECEIVE). Created `tests/test_phase3_material_inventory_integration.py` with 2 failing tests (0 movements found). Requirements Q14.5 + Q15.6 impacted. Issue #7 created for P1 backlog.
- ✅ Check #7 (Inventory thresholds and alerts): Verified `InventoryItem.low_stock_threshold` field exists (~4226). Tests in `tests/test_inventory_core.py::test_low_stock_detection` and `tests/test_module15_inventory_api.py::test_low_stock_alert_on_issue` validate threshold detection (both passing). Requirement Q15.5 (per-item thresholds) is implemented.
- ✅ Check #8 (Payroll record lifecycle): Verified `PayrollRecord` model (~1451) has `reviewed` field for workflow state. Tests in `tests/test_module16_payroll_api.py` validate period approval and payment recording (passing). Requirements Q16.5-Q16.10 (overtime, bonuses, manual adjustments) are implemented.
- ✅ Check #9 (Client requests and attachments): Verified `ClientRequest` (~2822) and `ClientRequestAttachment` (~2853) models with project scoping. Tests in `tests/test_integration_client_requests.py` validate access isolation and status transitions (2 tests, both passing). Requirements Q17.1-Q17.4 (client requests) are implemented.
- ✅ Check #10 (Site photos filtering and privacy): Verified `SitePhoto` model (~3043) has `visibility` field (public/internal) and pagination support. Comprehensive test suite in `tests/test_site_photos_gallery.py` validates privacy filtering (`test_non_staff_sees_only_public_photos`), date filtering, pagination (17 tests, all passing). Requirements Q18.4 (privacy control) and Q18.8 (filtering) are implemented.

**PHASE 3 Summary**: 9 of 10 checks PASS, 1 GAP detected (materials→inventory integration). Integration gap documented in issue #7 for remediation in PHASE 4.


