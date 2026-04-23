# Kibray Roadmap (Reduced Plan)

Date: 2026-04-23 (updated after Phase E1+E1.3 completion)

This roadmap focuses only on pending phases and ordered activities. Completed phases (FASE 1–2, core parts of FASE 3, and implemented dashboards/automation/security/tests) are omitted for brevity.

## Current Focus
- Set one focus at a time (update this line): Phase E2 — Documentation refresh; Phase E3 — Deployment

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
- 🔄 E1.3.a Stabilize E2E (unify creds, remove hardcoded venv path, add npm scripts, replace hard sleeps)
- ⏳ E1.3.b Add E2E for financial flows (Invoice list/payment, Client portal)
- 🔄 E2 Documentation: REQUIREMENTS_DOCUMENTATION.md, API docs refresh, user guides
- ⏳ E3 Deployment: checklist and backup scripts (pg_dump for prod), Railway env validation

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

