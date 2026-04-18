# Kibray Roadmap (Reduced Plan)

Date: 2025-11-25

This roadmap focuses only on pending phases and ordered activities. Completed phases (FASE 1–2, core parts of FASE 3, and implemented dashboards/automation/security/tests) are omitted for brevity.

## Current Focus
- Set one focus at a time (update this line): Clients & Communication (FASE 5)

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
- Tests: unit per new model, integration for critical flows, E2E for main workflows; optional load testing
- Documentation: REQUIREMENTS_DOCUMENTATION.md, API docs, user guides
- Deployment: checklist and backup scripts (pg_dump for prod)

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

