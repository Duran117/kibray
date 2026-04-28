# Kibray Roadmap (Reduced Plan)

Date: 2026-04-27 (updated after EV sparkline canvas renderer)

This roadmap focuses only on pending phases and ordered activities. Completed phases (FASE 1–2, core parts of FASE 3, and implemented dashboards/automation/security/tests) are omitted for brevity.

## Current Focus
- Set one focus at a time (update this line): **Phase D fully complete** (D1 ✅ + D2 ✅ + D3 ✅ + D4 ✅) + signed_contract_pdf async ✅ + generic `auto_save_pdf_async` ✅ + Phase D dashboard widgets ✅ + EV trend sparkline (data + canvas renderer) ✅. Next pick = (a) interactive Critical Path drill-down page (full Gantt highlight + slack table) consuming `/api/projects/<id>/critical-path/`, (b) sparkline tooltip / hover state using the existing `data-labels`/`data-ev`/`data-pv` attributes, or (c) move on to next backlog area.

## Recent Progress (April 2026)
- ✅ **EV sparkline canvas renderer** (post sparkline data widget):
  - `core/static/core/js/ev_sparkline.js` — new zero-dependency vanilla
    canvas renderer (~120 LoC) that finds every
    `<canvas data-testid="ev-sparkline-canvas">`, parses the JSON
    `data-spi` / `data-cpi` arrays, normalises both series to a shared
    y-axis padded to always include the 1.000 baseline, and draws two
    thin lines (SPI = indigo-500, CPI = rose-500) plus a dashed
    on-budget reference line. HiDPI-safe (devicePixelRatio scaling),
    debounced re-render on window resize, exposes
    `window.kibrayEvSparkline.{renderAll,renderOne}` for tests / manual
    debugging.
  - `core/templates/core/components/_project_phase_d_widgets.html` —
    `{% load static %}` + conditional
    `<script src="{% static 'core/js/ev_sparkline.js' %}" defer>` only
    when `ev_sparkline` truthy (overview pages without snapshots stay
    asset-free).
  - Tests: `tests/test_dashboard_widgets_phase_d.py` — +3 tests:
    script tag present + deferred when sparkline data exists, script tag
    absent when no sparkline, static asset well-formed (exists,
    exposes `kibrayEvSparkline`, references the data attributes the
    template emits, balanced braces / parens cheap-syntax sanity).
  - Validation: full suite **1450 passed / 17 skipped** (was 1447, +3
    new, 0 regressions); 3× determinism loop on dashboard widgets:
    29/29 each (~49s).

- ✅ **EV trend sparkline widget** (post Phase D dashboard widgets):
  - `core/services/dashboard_widgets.py::get_ev_sparkline(project, days=30)`
    — returns the last N `EVSnapshot` rows in chronological order with
    JSON-safe `str(Decimal)` arrays for `labels`/`spi`/`cpi`/`ev`/`pv`,
    plus `first`/`last` convenience points for delta calculation. Returns
    `None` when there are fewer than 2 snapshots (single point isn't a
    trend). Window clamped to `[2, 365]` and falls back to default on
    invalid input. Exception-safe (returns `None` on lookup failure).
  - `core/views/project_overview_views.py::project_overview` adds
    `ev_sparkline` to the template context.
  - `core/templates/core/components/_project_phase_d_widgets.html` —
    sparkline section appended to the EV card: caption with day-window +
    point count + SPI delta, plus a `<canvas data-testid="ev-sparkline-canvas">`
    with `data-labels`/`data-spi`/`data-cpi`/`data-ev`/`data-pv` JSON
    attributes ready for a Chart.js / minimal renderer to consume. Hidden
    when fewer than 2 snapshots.
  - Tests: `tests/test_dashboard_widgets_phase_d.py` — 12 new sparkline
    tests covering: no-snapshots → None, single-snapshot → None, 2+
    snapshots returned chronologically (out-of-order insert verified),
    window clamping (above max → 365, below min → 2, invalid → default),
    exception → None, JSON round-trip safety, and end-to-end overview
    integration (context key always exposed, canvas rendered with data,
    canvas omitted when only one snapshot).
  - Validation: full suite **1447 passed / 17 skipped** (was 1435, +12
    new, 0 regressions); 3× determinism loop on widgets + critical_path
    + ev_snapshots tests: 75/75 each (~51s).

- ✅ **Phase D dashboard widgets** (Earned Value + Critical Path):
  - `core/services/dashboard_widgets.py` — new module with two
    exception-safe accessors:
    * `get_ev_widget(project)` — returns the latest persisted
      `EVSnapshot` summary plus a status badge (`healthy` / `at_risk` /
      `critical` / `unknown`) classified from min(SPI, CPI). Returns
      `None` if the project has no snapshots yet.
    * `get_critical_path_widget(project)` — wraps `compute_critical_path`,
      caps the preview list at 8 critical tasks (`preview_truncated`
      flag), and degrades to a `{error: "cycle_detected"}` dict on
      `CriticalPathCycleError` so the template can render an inline
      warning instead of crashing the page.
  - `core/views/project_overview_views.py::project_overview` — adds
    `ev_widget` + `critical_path_widget` to the template context (still
    None when no data — UI handles placeholder).
  - `core/templates/core/components/_project_phase_d_widgets.html` — new
    partial rendering side-by-side EV health card (SPI / CPI / %
    complete + PV/EV/AC/EAC/VAC dl) and Critical Path summary card
    (duration hours, critical-task count, preview list with truncation
    indicator). All hooks have `data-testid` attributes for QA.
  - `core/templates/core/project_overview.html` — includes the partial
    right after the existing KPI grid.
  - Tests: `tests/test_dashboard_widgets_phase_d.py` — 14 tests.
    EV: no-snapshot returns None, latest-only selection, status
    classification (healthy/at_risk/critical), exception isolation.
    Critical Path: no-tasks → None, basic chain summary shape, preview
    truncation at the 8-task cap, `CriticalPathCycleError` → error
    dict, unexpected exception → None. End-to-end: project_overview
    exposes both context keys, renders empty placeholders without data,
    renders EV badge + SPI/CPI cells with snapshot, renders CP
    badge + preview list with a chained TaskDependency.
  - Validation: full suite **1435 passed / 17 skipped** (was 1421, +14
    new, 0 regressions); 3× determinism loop on widgets + critical_path
    + ev_snapshots tests: 63/63 each (~50s).

- ✅ **Generic `auto_save_pdf_async` migration** (post signed-contract):
  - `core/tasks.py::auto_save_pdf_async(doc_kind, doc_id, user_id, **opts)` —
    new `@shared_task(bind=True, max_retries=2, default_retry_delay=30)`
    backed by an explicit dispatch table for `invoice` / `estimate` /
    `changeorder` / `colorsample`. Filters helper kwargs to the allowed
    set per kind (defensive — extra/foreign keys are dropped, never
    raised). Returns `{doc_kind, doc_id, project_file_id}` on success or
    an `error`-keyed dict on terminal failure.
  - Migrated 4 request-thread callsites to dispatch via
    `transaction.on_commit`:
    1. `core/views/financial_views.py::invoice_mark_sent` — defer Invoice
       PDF auto-save after status flip to SENT.
    2. `core/views/contract_views.py::proposal_public_view` (client
       approval) — defer Estimate PDF (`as_contract=True`) auto-save.
    3. `core/views/financial_views.py::estimate_detail` (contract creation
       fallback) — defer legacy Estimate-as-Contract PDF.
    4. `core/views/financial_views.py::estimate_detail` (regenerate_pdf
       action for non-approved estimates) — defer regular Estimate PDF.
  - Tests: `tests/test_auto_save_pdf_async.py` — 11 tests.
  - Validation: full suite 1421 passed / 17 skipped (was 1410, +11 new,
    0 regressions); 3× determinism loop: 96/96 each.


- ✅ **Async signed-contract PDF migration** (post Phase D):
  - `core/services/contract_service.py::ContractService.sign_contract` —
    new `async_pdf: bool = True` parameter; when True, uses
    `transaction.on_commit(...)` to enqueue
    `core.tasks.generate_signed_contract_pdf_async.delay(contract_id, user_id)`
    so the HTTP signing request returns immediately. Inline path preserved
    for `async_pdf=False` (tests / management commands).
  - Module-level `sign_contract` wrapper forwards the new flag.
  - `core/tasks.py::generate_signed_contract_pdf_async` — new
    `@shared_task(bind=True, max_retries=2, default_retry_delay=30)` that
    loads the contract, calls `ContractService.generate_signed_contract_pdf`,
    attaches the resulting `ProjectFile` to `contract.signed_pdf_file`, and
    creates a `Notification` on success/failure.
  - Tests: `tests/test_signed_contract_async.py` — 13 tests covering
    dispatch default, on_commit + Celery `.delay` enqueue, inline fallback,
    `generate_signed_pdf=False` short-circuit, unsignable contracts raising
    before dispatch, module-level wrapper forwarding, missing-contract,
    success path (notification + ProjectFile attachment), generator-returns-
    None, render-exception → MaxRetries → notification, and
    no-user-no-notification.
  - Validation: full suite **1410 passed / 17 skipped** (was 1397, +13 new);
    3× determinism loop on contract+signature+report tests: 56/56 each.
- ✅ **Phase D4 — Signature GenericForeignKey**:
  - `signatures/models.py`: added optional `content_type` (FK to ContentType) +
    `object_id` + `content_object` GFK so any model (Estimate, Contract,
    ChangeOrder, ColorSample, MeetingMinute, Project, …) can attach
    signatures without dedicated FK columns. New compound index
    `sig_gfk_idx`. Both fields nullable for backwards compat.
  - Migration `signatures/0003_signature_content_type_signature_object_id_and_more.py`.
  - `SignatureSerializer`: exposes derived `content_type_label` (e.g.
    `core.project`) for one-shot rendering.
  - `SignatureViewSet`: list filters `?content_type=`, `?content_type_label=`,
    `?object_id=` (bad values short-circuit to empty). New `for-object`
    action `GET /api/v1/signatures/for-object/?content_type_label=app.model&object_id=N`.
  - 16 new tests across 5 classes (model GFK round-trip + null compat;
    serializer derived field; list filters + isolation; for-object happy +
    400/404 validation paths + auth; create over the wire with GFK).
  - Suite: 1381 → **1397 passed**, 0 regressions. 3-iteration determinism
    loop on Phase D tests: 104/104 each (~58s).
- ✅ **Phase D1 — Payroll workflow state machine**:
  - `core/services/payroll_workflow.py`: explicit state-machine over the
    existing 4 states (`draft → under_review → approved → paid`) with
    `submit_for_review`, `approve`, `mark_paid`, `reopen` transitions.
    `PayrollTransitionError` raised on illegal source; `paid` is terminal;
    `reopen` clears `approved_by`/`approved_at`. All transitions
    idempotent. Backwards compat: `draft → approved` allowed (legacy
    single-step approval used by existing tests/UI).
  - `PayrollPeriodViewSet` REST: `submit-for-review`, `mark-paid`,
    `reopen`, `legal-transitions` actions; existing `approve` rewired to
    use the workflow service. Returns `409 Conflict` on illegal
    transitions with the offending current_status echoed back.
  - 34 new tests across 6 classes (state-machine matrix 11 cases via
    parametrize, each transition's happy-path/idempotency/illegal-source,
    reopen audit-clearing, full lifecycle through API, 409 on illegal,
    auth required).
  - Suite: 1347 → **1381 passed**, 0 regressions. 3-iteration determinism
    loop on payroll/EV/CPM tests: 84/84 each (~55-62s).
- ✅ **Phase D3 — Earned Value Snapshots & Forecasting**:
  - `core/services/ev_snapshots.py`: pure `compute_forecast` (SV/CV/EAC/ETC/VAC,
    %complete, %spent) + `create_snapshot` (idempotent upsert per project/day)
    + `bulk_create_snapshots` for the daily Celery batch. Caps SPI/CPI to fit
    NUMERIC(5,3); ETC clamped ≥ 0; division-by-zero safe.
  - `core.tasks.generate_daily_ev_snapshots` Celery task scheduled at 18:00
    via `kibray_backend/celery_config.py` (after employee clock-out).
  - REST: `GET /api/v1/projects/{id}/ev-snapshots/?since=YYYY-MM-DD&limit=N`
    (descending, capped at 365) + `POST .../ev-snapshots/generate/` for
    on-demand regeneration.
  - 26 new tests across 6 classes (forecast formulas incl. CPI=0.5/2/None,
    BAC=0, ETC clamping, NUMERIC overflow capping; persistence idempotency;
    bulk iteration + queryset filter; Celery task end-to-end + beat-schedule
    guard; endpoints with since/limit/auth).
  - Suite: 1321 → **1347 passed**, 0 regressions. 3-iteration determinism
    loop on related tests: 80/80 each (~51-59s).
- ✅ **Phase D2 — Critical Path Method**:
  - `core/services/critical_path.py`: pure CPM algorithm (forward/backward
    pass, slack, FS/SS/FF/SF + lag) + Django integration with default
    duration resolver (tracked_seconds → started/completed window → 480 min
    fallback). Topological sort raises `CriticalPathCycleError`.
  - `ProjectViewSet.critical_path` REST action (`GET /api/v1/projects/{id}/critical-path/`)
    with `?durations=id:min,id:min` overrides; returns 400 on cycle.
  - 23 new tests across 7 classes (linear, parallel, diamond, all 4
    dep-types + lag, slack, cycles, edge filtering, Django integration,
    endpoint auth/payload/overrides).
  - Suite: 1298 → **1321 passed**, 0 regressions. 3-iteration determinism
    loop on related tests: 62/62 each (~55-60s).
- ✅ **Phase E** (full): tag `v2026.04-phase-e` — 17 commits, suite 1040 → 1271
- ✅ **Phase C — Celery audit** (2 passes): ghost-task fix, dead-app removal,
  9 guard tests, orphan resolution. 22 real tasks, 15 scheduled, 0 orphans.
- ✅ **Phase C — Reports foundation** (`docs/REPORTS_AUDIT.md`):
  - `core/services/report_registry.py`: tiny pluggable registry with
    permission gate + typed errors
  - `core/services/report_generators.py`: 5 PDF adapters auto-register
    (estimate, contract, signed contract, change order, color sample)
  - `core.tasks.generate_report_async`: generic worker task — perm-gated,
    retries (2x / 30 s), persists to default_storage, creates Notification
    on done/fail. Routes to existing `reports` celery queue.
  - 18 new tests covering registry/permissions/async happy + 4 error paths
  - Suite: 1280 → **1298 passed**, 0 regressions

## Recent Progress (April 2026)
- ✅ **Phase D1**: Security patch — `pypdf 6.2.0 → 6.10.2` (18 CVEs)
- ✅ **Phase E1.1**: Unit tests for 5 lowest-coverage view modules
  - `security_decorators` 0% → 94% (+33 tests)
  - `payroll_views` 2.8% → 63% (+25 tests)
  - `task_views` 6.2% → 61% (+33 tests)
  - `financial_views` 7.9% → 37% (+54 tests)
  - `client_mgmt_views` 16.2% → 72% (+54 tests)
- ✅ **Phase E1.2**: Cross-module integration tests — 8 flows, +16 tests
  (Invoice→Payment→Income, Multi-payment→PAID, CO↔Invoice, Client portal touch-up,
  Project cascade, ColorApproval+notifications, Estimate-prefixed numbering, Org-link delete-block)
- ✅ **Phase E1.3**: Playwright E2E suite review — 18 specs / 1,426 LOC catalogued
  (see `docs/E2E_REVIEW.md` — 4 critical, 6 medium, 3 low findings)
- 📊 **Test suite**: 1040 → **1255 passed**, 0 regressions, 17 skipped, ~7 min runtime

## Ordered Pending Activities

### Phase A: Clients & Communication (FASE 5)
- Clients (Portal)
  - Role-based restrictions
  - Request types: Material, Change Order (CO), Info
  - File uploads (sandboxed + quotas)
  - Multi-project access controls
- Communication
  - Project/global chat
  - @mentions with entity linking
  - File/photo attachments
  - Admin-only message deletion

### Phase B: Visual & Collaboration (FASE 6)
- Site Photos
  - GPS auto-tagging, gallery, link with Damage Reports
- Color Samples
  - KPISM numbering, room grouping, approval workflow
  - Digital signature integration hook
- Floor Plans
  - Pin migration tooling
  - Canvas annotations polish
  - Multi-device support hardening
- Damage Reports
  - Category system & workflow states
  - Photo evidence, optional CO integration, pattern analytics

### Phase C: Administration & Reports (FASE 7)
- Cost Codes
  - Hierarchy, auto-assignment, validation rules, consolidation reports
- Automation
  - Celery tasks audit consolidation
  - Notification system hardening
  - Scheduled jobs review
- Reports
  - Permission-based data access
  - Async generation
  - PDF/Excel/CSV exports
  - Scheduling

### Phase D: Financial & Advanced (FASE 4 + FASE 8)
- Payroll
  - Unify PayrollRecord vs PayrollEntry
  - Draft → Reviewed → Approved → Paid
  - Deductions (future)
  - Expenses integration
- Task Dependencies (Q11.6/Q11.7)
  - Gantt dependencies, critical path, validation
- EVM Dynamic Recalculation
  - Schedule change triggers, PV recalculation, forecasting, dashboard widgets
- Digital Signatures
  - Signature model, canvas interface, cryptographic verification
  - Generic relations, legal audit trail

### Phase E: Testing & Documentation (FASE 9–10)
- ✅ E1.1 Unit tests for low-coverage view modules (5 modules, +199 tests)
- ✅ E1.2 Cross-module integration tests (8 flows, +16 tests)
- ✅ E1.3 Playwright E2E suite static review (`docs/E2E_REVIEW.md`)
- ✅ E1.3.a Stabilize E2E (shared creds helper, env-driven config, npm scripts — commit ca077a9d)
- ✅ E1.3.b Financial flows E2E smoke (`tests/e2e/financial.spec.js` — commit 620b0d67)
- ✅ E2 Documentation: README badges/status refreshed, API_ENDPOINTS_REFERENCE header
  refreshed (commit 2138a4de); PHASE_E_COMPLETION_REPORT.md
- ✅ E3 Deployment: `docs/DEPLOYMENT_CHECKLIST.md` actionable one-pager;
  pg_dump backup script already present (`scripts/backup_postgres.sh`)
- ⏳ E2 follow-up: REQUIREMENTS_DOCUMENTATION.md refresh (lower priority)
- ⏳ E3 follow-up: enhance check_railway_env (file currently absent — create on demand)

## Memory Map (Keep Me Aligned)
- Architecture
  - Touch-ups: Task(is_touchup=True), PlanPin multipurpose, TouchUpPin UI gated
  - Pins: auto-task only for touchup/alert/damage; notes/colors informational
- Must-keep rules
  - Serializer compat: map legacy inputs; save() blocks deprecated direct use
  - Celery: eager in tests; broker-safe fallback for DailyPlan weather
  - Task status logging via signals only; avoid duplicates
- Quick checks before switching focus
  - Tests green, feature flags correct, no legacy route references
- Backlog anchors (phases)
  - A: Clients & Communication
  - B: Visual & Collaboration
  - C: Admin & Reports
  - D: Financial & Advanced
  - E: Testing & Docs

