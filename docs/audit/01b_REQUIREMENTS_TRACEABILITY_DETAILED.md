## PHASE 1 — DETAILED TRACEABILITY (selected anchors)

This file records concrete file:line anchors for key models, viewsets and tests that implement Modules 11–19. Use these anchors for quick manual verification.

Module 11 — Tasks (anchors)
- Model: `core/models.py` — `class Task` @ line ~541
- Dependencies: `core/models.py` — `class TaskDependency` @ line ~857
- Task images: `core/models.py` — `class TaskImage` @ line ~933
- Status changes: `core/models.py` — `class TaskStatusChange` @ line ~960
- API: `core/api/views.py` — `class TaskViewSet` @ line ~469
- Serializer: `core/api/serializers.py` — `class TaskSerializer` @ line ~310
- Tests: `tests/test_module_11_tasks.py` (multiple test classes)

Module 12 — Daily Plans
- Model: `core/models.py` — `class DailyPlan` @ line ~4848
- Activity templates: `core/models.py` — `class ActivityTemplate` @ line ~4622
- Consumer: `core/consumers.py` / `core/consumers_fixed.py` — `class DailyPlanConsumer` @ ~line 490
- API: `core/api/views.py` — `class DailyPlanViewSet` @ line ~2887
- Serializer: `core/api/serializers.py` — `class DailyPlanSerializer` @ line ~1454

Module 13 — SOPs
- Model: `core/models.py` — `class ActivityTemplate` @ line ~4622
- SOP reference files: `core/models.py` — `class SOPReferenceFile` @ line ~5422
- Admin: `core/admin.py` — `ActivityTemplateAdmin`, `SOPReferenceFileAdmin`

Module 14 — Materials
- Model: `core/models.py` — `class MaterialRequest` @ line ~2489
- Model items: `core/models.py` — `class MaterialRequestItem` @ line ~2878
- Catalog: `core/models.py` — `class MaterialCatalog` @ line ~3012
- API: `core/api/views.py` — `MaterialRequestViewSet` @ line ~3188

Module 15 — Inventory
- Model: `core/models.py` — `class InventoryItem` @ line ~4226
- Movements: `core/models.py` — `class InventoryMovement` @ line ~4450
- API: `core/api/views.py` — `InventoryItemViewSet` @ line ~3094

Module 16 — Payroll
- Model: `core/models.py` — `class PayrollRecord` @ line ~1451
- API: `core/api/views.py` — `class PayrollRecordViewSet` @ line ~1234

Module 17 — Clients
- Model: `core/models.py` — `class ClientRequest` @ line ~2822
- Attachments: `core/models.py` — `class ClientRequestAttachment` @ line ~2853
- API: `core/api/views.py` — `ClientRequestViewSet` @ line ~3256

Module 18 — Site Photos
- Model: `core/models.py` — `class SitePhoto` @ line ~3043
- API: `core/api/views.py` — `class SitePhotoViewSet` @ line ~3537
- Serializer: `core/api/serializers.py` — `class SitePhotoSerializer` @ line ~223

Module 19 — Color Samples / Approvals
- References in: `REQUIREMENTS_DOCUMENTATION.md` and `PANEL_REORGANIZATION_COMPLETE.md` (see docs), implementation touches in `core/models.py` and `core/api` code (search for `ColorSample` and `ColorApproval`).

How to use
- Open the file at the anchor and review methods, permissions and tests to confirm the requirement behavior.
