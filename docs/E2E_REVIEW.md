# Phase E1.3 — Playwright E2E Review

**Date**: April 2026  
**Reviewer**: Phase E test-hardening pass  
**Scope**: Static review of 18 spec files across 2 suites (1,426 LOC total)

---

## 1. Suite Inventory

### Suite A — Root (`tests/e2e/`) — 12 specs / 14 tests

| # | Spec | Tests | LOC | Auth strategy | Target route | Notes |
|---|---|---|---|---|---|---|
| 1 | `auth.setup.js` | setup | 28 | Creates `admin_playwright`/`admin123`, saves `auth.json` | `/login/` | Shared storageState for chromium/firefox/webkit |
| 2 | `calendar.spec.js` | 1 | 8 | storageState | `/calendar` | Smoke: month name visible |
| 3 | `chat.spec.js` | 1 | 8 | storageState | `/chat` | Smoke: "team chat" text |
| 4 | `darkmode.spec.js` | 1 | 14 | storageState | `/` | Theme toggle (skips if absent) |
| 5 | `dashboard_shell.spec.js` | 2 | 34 | storageState | `/dashboard/admin/`, `/dashboard/designer/` | Modern shell + no horizontal overflow @ 360px |
| 6 | `filemanager.spec.js` | 1 | 39 | storageState | `/files` | Heavily instrumented (debug logging) |
| 7 | `globalsearch.spec.js` | 1 | 18 | storageState | `/files` + Cmd+K | `[data-testid="global-search"]` |
| 8 | `notifications.spec.js` | 1 | 11 | storageState | `/files` | `[data-testid="notification-center"]` |
| 9 | `reports.spec.js` | 1 | 8 | storageState | `/reports` | "report generator" text |
| 10 | `responsive.spec.js` | 3 | 21 | storageState | `/files` | iPhone12 / iPad / Desktop snapshots |
| 11 | `usermanagement.spec.js` | 1 | 8 | storageState | (TBD) | Smoke |
| 12 | `strategic_planner.spec.ts` | ~6 | 208 | **Hardcodes `admin`/`Kibray2025!Admin`** ⚠️ | `/planner/strategic/` | Bypasses auth.setup |
| 13 | `strategic_planner_full.spec.ts` | ~3 | 114 | **Same hardcoded creds** ⚠️ | `/planner/strategic/` | Bypasses auth.setup |

**Config**: `playwright.config.js` — `fullyParallel: true`, runs across **chromium + firefox + webkit** (3× run multiplier).

### Suite B — Frontend (`frontend/tests/e2e/`) — 6 specs / ~14 tests

| # | Spec | Tests | LOC | Auth strategy | Target route | Notes |
|---|---|---|---|---|---|---|
| 1 | `color-approvals.spec.ts` | 1+ | 145 | Inline login `admin`/`admin123` | `/admin/login/` then API POST | Creates approvals via `/api/v1/color-approvals/` |
| 2 | `gantt.spec.ts` | 1 | 74 | Inline login `admin`/`admin123` | `#gantt-app-root` | Waits for React mount |
| 3 | `notification-center.spec.ts` | 1 | 128 | Inline login `admin`/`admin123` | `/dashboard/` → `#notification-root` | `test.describe.serial` |
| 4 | `pm-assignments.spec.ts` | 1 | 106 | Inline login + API POST | `/api/v1/project-manager-assignments/assign/` | |
| 5 | `touchup-board.spec.ts` | 1 | 192 | Inline login `admin`/`admin123` | `/projects/1/touchups-react/` → `#touchup-root` | Polls `data-mounted="1"` attribute |
| 6 | `ui-flows.spec.ts` | 5 | 290 | (assumes pre-auth) | `/touchups`, etc. | 5 sub-tests for kanban behaviour |

**Config**: `frontend/playwright.config.ts` — `fullyParallel: false`, `workers: 1`, **chromium only**, hardcoded venv path in `webServer.command`.

---

## 2. Findings

### 🔴 Critical

| ID | Issue | Affected | Impact |
|---|---|---|---|
| C1 | **Three sets of hardcoded credentials**: `admin_playwright/admin123`, `admin/admin123`, `admin/Kibray2025!Admin` | All specs | CI fragility — only `auth.setup.js` actually creates its user. The other two creds assume a manually-seeded `admin` superuser exists. |
| C2 | `strategic_planner*.spec.ts` lives under `tests/e2e` but **bypasses `auth.setup.js`** with its own login helper | 2 specs (322 LOC) | Defeats the storageState pattern; if `Kibray2025!Admin` user doesn't exist, all 9 strategic planner tests fail at `beforeEach` |
| C3 | Frontend `webServer.command` hardcodes absolute path `/Users/jesus/Documents/kibray/.venv/bin/python` | `frontend/playwright.config.ts` | Will break on any other dev machine or CI |
| C4 | No `package.json` script wires E2E (`test:e2e`, `test:e2e:frontend`) | Both suites | Discoverability — devs must remember `npx playwright test` from each dir |

### 🟡 Medium

| ID | Issue | Affected | Impact |
|---|---|---|---|
| M1 | **Pytest `addopts="-k 'not e2e'"`** correctly excludes them — but there is also a stray `tests/e2e/test_playwright_hello.py` collected by pytest (unrelated to Playwright JS) | pytest config | Confirmed harmless; document intent |
| M2 | Many specs use `await page.waitForTimeout(2000-3000)` (hard sleeps) instead of waiting on selectors | `filemanager`, `globalsearch`, `notifications`, `responsive`, `touchup-board` | Flaky on slow CI; should use `waitFor`/`toBeVisible` |
| M3 | `darkmode.spec.js` silently passes when toggle not found (no assertion run) | `darkmode.spec.js` | False positive |
| M4 | `usermanagement.spec.js` is 8 LOC — likely incomplete stub | `usermanagement.spec.js` | Coverage gap |
| M5 | API helpers (`createApproval`, `createAssignment`) issue real `POST` mutations on shared DB without cleanup | `color-approvals`, `pm-assignments` | Test data accumulation; should use a fresh DB or `afterEach` cleanup |
| M6 | Both suites assume `project_id=1` exists in the DB | `touchup-board`, `pm-assignments`, `color-approvals`, `ui-flows` | Hard-codes seed assumption |

### 🟢 Low

- L1: `filemanager.spec.js` retains debug `console.log` instrumentation — should be removed once stable.
- L2: No `tags` (`@smoke`, `@critical`) for selective execution.
- L3: HTML reporter set to `open: 'never'` is correct for CI; verify gitignore covers `playwright-report/` and `test-results/`.

---

## 3. Coverage Map vs. Application

| Application Module | E2E Coverage | Spec |
|---|---|---|
| Auth / Login | ✅ via setup | `auth.setup.js` |
| Admin Dashboard | ✅ smoke | `dashboard_shell.spec.js` |
| Designer Dashboard | ✅ smoke | `dashboard_shell.spec.js` |
| Calendar | ✅ smoke only | `calendar.spec.js` |
| Chat | ✅ smoke only | `chat.spec.js` |
| Reports | ✅ smoke only | `reports.spec.js` |
| File Manager (React) | ✅ mount only | `filemanager.spec.js` |
| Global Search (Cmd+K) | ✅ open modal | `globalsearch.spec.js` |
| Notification Center | ✅ + interactions | `notifications.spec.js`, `notification-center.spec.ts` |
| Touch-up Board | ✅ + 5 flows | `touchup-board.spec.ts`, `ui-flows.spec.ts` |
| Strategic Planner | ✅ deep (9 tests) | `strategic_planner*.spec.ts` |
| Gantt | ✅ mount | `gantt.spec.ts` |
| Color Approvals | ✅ create + approve | `color-approvals.spec.ts` |
| PM Assignments | ✅ assign | `pm-assignments.spec.ts` |
| Theme / Dark Mode | ⚠️ optional | `darkmode.spec.js` |
| Responsive | ✅ 3 viewports | `responsive.spec.js` |
| **GAPS** | ❌ no E2E | Invoices, Payments, Cost Codes, Estimates, Client Portal, Organizations, Payroll, Daily Plan, Time Entry, Change Orders |

---

## 4. Recommendations (priority order)

### Phase E1.3.a — Stabilize (low effort, high value)

1. **Unify credentials**: refactor all specs to import a single `tests/e2e/_helpers/auth.ts` exporting `ADMIN_USER`/`ADMIN_PASS` from `process.env` with sensible defaults matching `auth.setup.js`. Update `strategic_planner*` to use the shared storageState.
2. **Remove hardcoded venv path** in `frontend/playwright.config.ts` → use `process.env.PYTHON ?? 'python3'`.
3. **Add npm scripts** to root `package.json`:
   ```json
   "test:e2e": "playwright test",
   "test:e2e:frontend": "cd frontend && playwright test",
   "test:e2e:smoke": "playwright test --grep @smoke"
   ```
4. **Replace hard sleeps** with `expect(...).toBeVisible({ timeout: ... })` in the 5 specs flagged in M2.
5. **Fix `darkmode.spec.js`** to fail when toggle is absent (or `test.skip`).

### Phase E1.3.b — Fill gaps (medium effort)

6. Add **smoke specs** for the financial flows already covered by integration tests:
   - `invoice-list.spec.ts` — list loads, filters work
   - `invoice-payment.spec.ts` — record payment → status PAID
   - `client-portal.spec.ts` — client logs in, sees only assigned project
7. Add an **`@smoke` tag** convention so CI can run a 2-minute smoke before the full suite.

### Phase E1.3.c — Hygiene (ongoing)

8. Add `afterEach` cleanup or run each spec inside a Django **test transaction reset** (e.g., a custom fixture that hits a `/_test/reset/` endpoint).
9. Remove debug instrumentation from `filemanager.spec.js`.
10. Document in `tests/e2e/README.md` how to run locally + CI matrix expectations.

---

## 5. Status Summary

- **Inventory complete**: 18 specs, ~28 individual tests, 1,426 LOC.
- **Static health**: 4 critical, 6 medium, 3 low issues found.
- **Execution status**: NOT executed in this session (requires running Django server + 3 browsers + seeded DB). Recommend running once locally after recommendations 1-3 are applied.
- **Coverage gap**: Financial / billing / payroll modules have **strong unit + integration coverage** (Phase E1.1+E1.2) but **zero E2E coverage** — biggest opportunity area.

---

**Next**: Phase E2 — refresh ROADMAP, README, API docs to reflect Phase E completion (215 new tests, 1255 total).
