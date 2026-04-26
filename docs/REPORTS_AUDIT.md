# Reports Audit (Phase C — Reports foundation)

**Date:** 2026-04-26  
**Scope:** Discovery of all report-like surfaces + introduction of an
async-capable, permission-gated **report registry** to consolidate them.

---

## TL;DR

| Item | Status |
|---|---|
| Dedicated `reports/` Django app | **never created** (URL still has `# TODO: Module reports not created yet`) |
| Report-style API endpoints | 2 (Aging, Inventory Valuation) — sync, JSON only |
| PDF generators (in `core.services.pdf_service`) | 5 (estimate, contract, signed contract, change order, color sample) — **all synchronous** in views |
| Ad-hoc CSV exports | 5 (project progress ×3, budget wizard, unassigned hours) |
| Async infra | celery `task_routes` already routes `core.tasks.generate_*` → `reports` queue |
| **NEW**: report registry | `core/services/report_registry.py` |
| **NEW**: built-in adapters | `core/services/report_generators.py` (5 PDFs auto-registered) |
| **NEW**: generic Celery task | `core.tasks.generate_report_async` (retry, perm-gated, notification on done/fail) |
| Tests | `tests/test_report_registry.py` — 18/18 passing |
| Suite after change | **1,298 passed**, 0 regressions (was 1,280) |

---

## 1. Existing report-like surfaces

### 1.1 API endpoints (sync, JSON)

| Endpoint | View | Permission | Notes |
|---|---|---|---|
| `GET /api/inventory/valuation/` | `InventoryValuationReportView` | `IsStaffOrAdmin` | OK |
| `GET /api/financial/aging-report/` | `InvoiceAgingReportAPIView` | `IsStaffOrAdmin` | OK |

Both return JSON only — no PDF/Excel/CSV variants. **Backlog:** wrap in
registry adapters so `?format=pdf` / `?format=csv` becomes a one-liner.

### 1.2 PDF generators (sync, blocking the request)

All five live in `core/services/pdf_service.py` and are called inline
from view handlers. They take 0.5–4 s each, blocking the worker.

| Generator | Currently invoked from |
|---|---|
| `generate_estimate_pdf_reportlab` | `pdf_service.py:336` (own dispatcher) |
| `generate_contract_pdf_reportlab` | `contract_service.py:133` |
| `generate_signed_contract_pdf_reportlab` | `contract_service.py:243` |
| `generate_changeorder_pdf_reportlab` | `changeorder_views.py:460,906,931,972` |
| `generate_colorsample_pdf_reportlab` | `pdf_service.py:2467` (own dispatcher) |

### 1.3 CSV exports (sync, ad-hoc)

| Endpoint | Function | Concern |
|---|---|---|
| project progress CSV (3 variants) | `core/views/project_progress_views.py:204,252,452` | OK, small payloads |
| budget wizard CSV | `core/views_budget_wizard.py:226` | OK |
| unassigned hours CSV | `core/views_unassigned_hours.py:216` | OK |

These are small + already work; no migration planned. Future work could
unify them under the registry as `*_csv` adapters once the foundation
is proven.

---

## 2. New foundation

### 2.1 `core/services/report_registry.py`

A small, dependency-free registry. Each report declares:

```python
register(
    "estimate_pdf",
    generator=_estimate_adapter,        # callable(**kwargs) -> bytes
    content_type="application/pdf",
    file_extension="pdf",
    allowed_roles=StaffRoles,           # frozenset of role strings
    description="Estimate document for client review.",
)
```

Public API:
- `register(name, *, generator, content_type, file_extension, allowed_roles, description)`
- `unregister(name)` — primarily for tests
- `get(name) -> ReportSpec`
- `list_reports() -> list[ReportSpec]` — sorted, useful for an admin UI
- `render(name, *, user, **kwargs) -> bytes` — enforces permissions then runs
- `resolve_user_role(user) -> (role, is_superuser, is_staff)`

Errors are typed:
- `ReportNotFound` — unknown name
- `ReportPermissionDenied` — user lacks role

### 2.2 `core/services/report_generators.py`

Adapters that wrap the 5 existing PDF generators so they can be invoked
by name + JSON-serialisable kwargs (object id) inside a Celery task.
Auto-registers on import; idempotent.

| Registry name | Adapter target | Allowed roles |
|---|---|---|
| `estimate_pdf` | `generate_estimate_pdf_reportlab` | StaffRoles |
| `contract_pdf` | `generate_contract_pdf_reportlab` | StaffRoles |
| `signed_contract_pdf` | `generate_signed_contract_pdf_reportlab` | StaffRoles |
| `changeorder_pdf` | `generate_changeorder_pdf_reportlab` | StaffRoles |
| `colorsample_pdf` | `generate_colorsample_pdf_reportlab` | StaffOrDesignRoles |

`StaffRoles = {admin, project_manager, general_manager}`  
`StaffOrDesignRoles = StaffRoles + {designer, superintendent}`  
Superusers and `is_staff` users always bypass role checks.

### 2.3 `core.tasks.generate_report_async`

Generic worker task — one entry point for every registered report.

```python
generate_report_async.delay("estimate_pdf", user_id=42, estimate_id=123)
```

Behaviour:
- Looks up the user; missing user → error result, no notification
- Looks up the report; unknown → `Notification("Report unavailable")`
- Calls `render()` (perm-gated); denied → `Notification("Report denied")`
- Generator raises → `self.retry()` up to 2x with 30 s backoff;
  exhausted → `Notification("Report failed")`
- Success → writes to `default_storage` at
  `reports/<user_id>/<report>_<YYYYMMDD_HHMMSS>.<ext>` and creates
  `Notification("Report ready")` with `link_url=download_url`

Routing: `core.tasks.generate_*` already maps to the `reports` queue
(`celery_config.py:128`).

### 2.4 Tests — `tests/test_report_registry.py` (18)

| Class | Tests |
|---|---|
| `TestRegistry` | round-trip, unknown raises, list contains 5 built-ins, blank name, non-callable, idempotent re-register, conflict raises |
| `TestPermissions` | superuser bypass, staff bypass, plain denied, kwargs pass-through, role resolver edge cases |
| `TestGenerateReportAsync` | happy path (file + notification), unknown report, permission denied, missing user, generator failure → retries exhausted |

---

## 3. Migration path (incremental, opt-in)

The five sync view handlers stay as-is for now (no behaviour change).
When a caller wants async + notification UX, the change is one line:

```python
# Before — blocks the request thread for ~2 s
pdf_bytes = generate_changeorder_pdf_reportlab(co)

# After — fires off to celery; the user gets a bell notification
generate_report_async.delay("changeorder_pdf", request.user.id, changeorder_id=co.id)
return Response({"queued": True}, status=202)
```

Migration order (suggested):
1. Heavier PDFs first: `signed_contract_pdf`, `colorsample_pdf` (image-heavy)
2. The two JSON-only API report endpoints — add `?format=pdf` adapters
3. The 5 ad-hoc CSV exports — wrap as `*_csv` adapters

---

## 4. Backlog (non-blocking)

1. **Persisted `ReportJob` model** (`status`, `path`, `requested_by`,
   `created_at`, `completed_at`) so the user can list past reports —
   currently relies on Notifications + storage path only.
2. **Admin UI**: `/admin/reports/` listing `list_reports()` + a "Run as
   me" button for superusers (debug helper).
3. **JSON+PDF dual response** for the existing Aging / Inventory Valuation
   endpoints via `?format=pdf` query param.
4. **Excel exports** — add a single `_xlsx` content_type once `openpyxl`
   adapters land.
5. **Scheduling** — extend `ReportSpec` with optional `schedule` so beat
   can fire predefined reports for management.
6. **Cleanup task** — `cleanup_old_reports` (e.g. delete `reports/*`
   older than 30 days) once the registry has real production traffic.
