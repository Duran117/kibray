# PHASE 1 — GAPS BACKLOG (initial, prioritized)

Generated: 2025-11-28

This backlog lists missing or partial features discovered during the Phase 1 traceability pass. Priority and effort are initial estimates for triage.

- [P0] Digital signature for color/sample approvals (High)
  - Why: Requirements call for legal signatures for color approvals. No clear implementation of cryptographic/legally-sound signature storage found.
  - Impact: Legal exposure for change approvals.
  - Suggested action: Design signature capture (image + signer metadata + timestamp + hash) and export to signed PDF. Create spike and small PR.

- [P1] Payroll: tax/withholding and multi-rate overtime engine (Medium)
  - Why: PayrollRecord exists, but advanced payroll rules are not present.
  - Impact: Payroll correctness for client accounting.
  - Suggested action: Add configurable payroll rules + unit tests; or integrate with an external payroll provider export.

- [P2] Inventory valuation policies (FIFO/LIFO/avg) (Medium)
  - Why: Inventory models exist but valuation strategy is unspecified.
  - Suggested action: Add valuation field and a calculation utility; update reports/API.

- [P2] SOP full-text search & UX polish (Low)
  - Why: Activity templates exist; search may be limited.
  - Suggested action: Add tests for fuzzy search and an API endpoint improvement if needed.

- [P1] Detect-secrets baseline & CI gating (Low-Medium)
  - Why: `detect-secrets` output contains vendor/.venv noise; add baseline to ignore expected items and enable CI gating.
  - Suggested action: Run `detect-secrets scan --update .secrets.baseline` with curated ignores; commit baseline to repo and add CI check.

- [P1] Tests: Increase coverage for boundary/edge cases in modules 13, 16 and 19 (Medium)
  - Why: Some features have limited or no tests for error and permission cases.
  - Suggested action: Create 2–4 unit tests per module focusing on permission and failure modes.

How to use
- Create GitHub issues for each P0/P1 item and link to this doc. Prefer small PRs with focused changes and tests.
