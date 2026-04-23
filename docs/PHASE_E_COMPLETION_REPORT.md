# Phase E — Test Hardening & Documentation (Completion Report)

**Period**: April 2026  
**Status**: E1.1 ✅ • E1.2 ✅ • E1.3 ✅ (review only) • E2 🔄 • E3 ⏳

---

## 1. Executive Summary

Phase E focused on **lifting test coverage** of the lowest-coverage business-critical modules and **stabilising the regression suite** before deployment hardening (Phase E3).

| Metric | Before | After | Δ |
|---|---|---|---|
| Tests passing | 1,040 | **1,255** | **+215** |
| Tests skipped | 17 | 17 | 0 |
| Test files added | — | **6** | +6 |
| Regressions introduced | — | **0** | ✅ |
| Suite runtime | ~6 min | ~7 min | +1 min |
| Coverage threshold | 35% (enforced) | 35% (enforced) | — |

All commits are linear on `main`, ready for `git push origin main` (7 commits ahead of origin at end of phase).

---

## 2. Phase E1.1 — View-Module Unit Tests

5 modules selected by **lowest line coverage** that are also business-critical:

| Module | LoC | Coverage Before | Coverage After | New tests |
|---|---|---|---|---|
| `core/security_decorators.py` | 121 | **0%** | **94%** | 33 |
| `core/views/payroll_views.py` | 290 | 2.8% | 63% | 25 |
| `core/views/task_views.py` | 264 | 6.2% | 61% | 33 |
| `core/views/financial_views.py` | 655 | 7.9% | 37% | 54 |
| `core/views/client_mgmt_views.py` | 304 | 16.2% | 72% | 54 |
| **Total** | **1,634** | — | — | **199** |

### Key technical patterns established

1. **Profile cache invalidation** — `user.profile` is a cached reverse OneToOne. When mutating role:
   ```python
   Profile.objects.update_or_create(user=u, defaults={"role": "client"})
   u.refresh_from_db()  # required to invalidate the cache
   ```
2. **`Http404` propagation in `RequestFactory`** — `RequestFactory` bypasses middleware, so `Http404` propagates as an exception:
   ```python
   with pytest.raises(Http404):
       my_view(request, pk=999999)
   ```
   Use `client.get()` instead when you need a real 404 response.
3. **PDF generation tests** — `xhtml2pdf` chokes on real templates. Patch `pisa` to force the fallback path:
   ```python
   monkeypatch.setattr("core.views.financial_views.pisa", None)
   ```
4. **Admin-vs-staff helpers** — `_is_staffish` (admin/PM/staff/superuser) vs `_is_admin_user`; `_require_admin_or_redirect` redirects to `dashboard` when failed.

### Test files created
- `tests/test_security_decorators.py` (commit `ea71c99f`)
- `tests/test_payroll_views.py` (commit `a3388dfe`)
- `tests/test_task_views.py` (commit `0b0d5f03`)
- `tests/test_financial_views.py` (commit `f794e205`)
- `tests/test_client_mgmt_views.py` (commit `a04e6716`)

---

## 3. Phase E1.2 — Cross-Module Integration

`tests/test_integration_flows.py` (commit `41050cd9`) — 16 tests covering 8 flows:

| Flow | Verifies |
|---|---|
| Invoice → Payment → Income | Single payment auto-creates `Income`, sets `PARTIAL` status |
| Full payment → PAID | `paid_date` set, status transitions correctly |
| Multi-partial → PAID | Two partials accumulate, two `Income` records |
| Overpayment | `balance_due` floored at 0, status PAID |
| ChangeOrder ↔ Invoice M2M | Bidirectional link via `change_orders` |
| Invoice cancel preserves CO | CO survives invoice cancellation |
| Client portal touch-up | `ClientProjectAccess` gates `agregar_tarea` view |
| Project cascade delete | Invoice/CO/ColorSample/InvoicePayment all removed |
| ColorApproval.approve() | Status set, signed_at set, PMs notified via `Notification` |
| ColorApproval.reject() | Status set, reason appended to notes |
| Estimate-prefixed numbering | Approved estimate code becomes invoice prefix |
| Client-initials fallback | "Acme Corp" → "AC-" prefix |
| Org-with-project delete blocked | Dependency check in `organization_delete` |
| Org without project deletable | Happy path |
| Overdue auto-detection | Past due_date with balance > 0 → status `OVERDUE` after `update_status()` |

---

## 4. Phase E1.3 — Playwright E2E Review

Static review only (no execution — would require server + browsers + seeded DB).

**Inventory**: 18 specs, ~28 tests, 1,426 LOC across 2 suites:
- Root suite (`tests/e2e/`): 12 specs, chromium+firefox+webkit, uses `auth.json` storageState
- Frontend suite (`frontend/tests/e2e/`): 6 specs, chromium-only, inline login per spec

**Findings**: 4 critical, 6 medium, 3 low — full report in `docs/E2E_REVIEW.md`.

**Top 3 critical issues**:
1. **Three sets of hardcoded credentials** in different specs — only one is auto-seeded
2. **`strategic_planner*.spec.ts` bypasses `auth.setup.js`** with its own login
3. **`frontend/playwright.config.ts` hardcodes absolute venv path** — won't work elsewhere

**Coverage gap**: Financial / billing / payroll have strong unit + integration coverage from E1.1+E1.2, but **zero E2E coverage** — biggest opportunity for E1.3.b.

---

## 5. Pending Work

### Phase E1.3.a — E2E Stabilization (recommended next)
- Unify credentials via shared helper using `process.env`
- Remove hardcoded venv path
- Add `npm run test:e2e` / `test:e2e:frontend` / `test:e2e:smoke`
- Replace hard `waitForTimeout` with selector-based waits (5 specs)
- Fix `darkmode.spec.js` silent-pass

### Phase E1.3.b — E2E Coverage Fill
- `invoice-list.spec.ts`, `invoice-payment.spec.ts`, `client-portal.spec.ts`
- Adopt `@smoke` tag convention

### Phase E2 — Documentation Refresh (in progress)
- ✅ `docs/ROADMAP.md` updated
- ✅ `docs/PHASE_E_COMPLETION_REPORT.md` (this file)
- ✅ `docs/E2E_REVIEW.md`
- ⏳ `REQUIREMENTS_DOCUMENTATION.md` consolidate
- ⏳ `API_README.md` regenerate from current routes
- ⏳ User guides for new flows

### Phase E3 — Deployment Hardening
- Production checklist
- `pg_dump` backup scripts
- Railway env validation script enhancement (`check_railway_env.py`)
- Smoke-test plan for post-deploy

---

## 6. Commit Log (Phase E)

```
41050cd9  Phase E1.2: Add 16 cross-module integration tests (8 flows)
a04e6716  Phase E1.1: Add 54 tests for client_mgmt_views (16.2% -> 72% coverage)
f794e205  Phase E1.1: Add 54 tests for financial_views (7.9% -> 37% coverage)
0b0d5f03  Phase E1.1: Add 33 tests for task_views (6.2% -> 61% coverage)
a3388dfe  Phase E1.1: Add 25 tests for payroll_views (2.8% -> 63% coverage)
ea71c99f  Phase E1.1: Add 33 tests for security_decorators (0% -> 94% coverage)
6ec4b839  Phase D1: Security patch - pypdf 6.2.0 -> 6.10.2 (18 CVEs fixed)  [previous baseline]
```

Plus pending E1.3 + E2 docs commits.
