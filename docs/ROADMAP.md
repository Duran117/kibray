# Kibray Roadmap (Reduced Plan)

Date: 2026-04-27 (updated after Phase D2 Critical Path)

This roadmap focuses only on pending phases and ordered activities. Completed phases (FASE 1–2, core parts of FASE 3, and implemented dashboards/automation/security/tests) are omitted for brevity.

## Current Focus
- Set one focus at a time (update this line): Phase D2 — Critical Path ✅; next pick = Phase D3 (EVM snapshots/forecasting) OR Phase D1 (Payroll workflow states), OR migrate first heavy PDF (signed_contract_pdf) to async at callsite.

## Recent Progress (April 2026)
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

