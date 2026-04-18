# Kibray — Architecture Reference

> **Last updated:** 2025-12 — after Phases 1-8 refactor (legacy_views split, dashboard/project split, test infrastructure, performance audit).

## 1. High-level layout

```
kibray/
├── kibray_backend/          # Django project (settings, root urls, wsgi)
├── core/                    # Main app — models, views, templates, urls
│   ├── models/              # Domain models
│   ├── views/               # 40 modular view files (see §3)
│   ├── templates/core/      # HTML templates (Tailwind + Bootstrap 5)
│   ├── urls.py              # URL routes
│   └── ...
├── tests/                   # Pytest suite (906 tests passing)
├── docs/                    # All project documentation
└── manage.py
```

**Settings module:** `kibray_backend.settings` (NOT `kibray.settings`).
**Default branch:** `main`.

## 2. Tech stack

| Layer        | Tech                                           |
|--------------|------------------------------------------------|
| Backend      | Django 5.x, Python 3.11                        |
| DB           | PostgreSQL (prod) / SQLite (dev)               |
| Frontend     | Django templates + Tailwind CSS + Bootstrap 5  |
| i18n         | gettext (es / en), `django.utils.translation`  |
| Tests        | pytest, pytest-django, pytest-cov              |
| Auth         | Django sessions, role-based (`UserProfile.role`) |
| Background   | Celery (optional)                              |
| Deployment   | Railway (`railway.json`, `Procfile`)           |

## 3. View architecture (40 modules)

The original `legacy_views.py` (17,764 lines!) was split during Phase 8 into 40 focused modules. Three remain as **shim modules** that only re-export from sub-modules to preserve backward compatibility with existing imports.

### 3.1 Shim modules (re-exports only)

| File                       | Lines | Re-exports from                                                                                                         |
|----------------------------|------:|-------------------------------------------------------------------------------------------------------------------------|
| `legacy_views.py`          | 32    | All Phase-8a-d sub-modules (kept until callers migrate)                                                                 |
| `dashboard_views.py`       | 32    | `dashboard_admin_views`, `dashboard_client_views`, `dashboard_employee_views`, `dashboard_pm_views`, `dashboard_designer_views`, `dashboard_shared_views` |
| `project_views.py`         | 30    | `project_crud_views`, `project_overview_views`, `project_client_portal_views`, `project_finance_views`                  |

### 3.2 Domain modules

#### Dashboards (6 modules)
- `dashboard_admin_views.py` (626) — admin KPIs, system health, user management
- `dashboard_pm_views.py` (594) — project-manager view (active projects, tasks, RFIs)
- `dashboard_employee_views.py` (534) — assignments, hours, daily-plan
- `dashboard_client_views.py` (330) — client portal landing
- `dashboard_designer_views.py` (130) — designer-specific feed
- `dashboard_shared_views.py` (221) — common widgets, role router

#### Projects (4 modules)
- `project_crud_views.py` (425) — create / update / delete / list
- `project_client_portal_views.py` (544) — client-facing project pages
- `project_finance_views.py` (414) — budget / costs / margin
- `project_overview_views.py` (301) — gantt / progress overview

#### Financials & Operations
- `financial_views.py` (1,412) — invoices, payments, AR/AP
- `payroll_views.py` (683) — timesheets, paychecks
- `expense_income_views.py` (527)
- `contract_views.py` (421)
- `changeorder_views.py` (980)

#### Field operations
- `daily_plan_views.py` (1,151)
- `daily_log_views.py` (294)
- `materials_views.py` (1,089)
- `task_views.py` (584)
- `schedule_views.py` (456)
- `project_progress_views.py` (481)
- `damage_report_views.py` (240)
- `site_photo_views.py` (175)

#### Touch-up & color
- `touchup_v2_views.py` (685) — current touch-up subsystem
- `touchup_legacy_views.py` (749) — kept for historical data
- `color_floor_views.py` (735)

#### Communication & docs
- `chat_views.py` (255)
- `meeting_minutes_views.py` (256)
- `rfi_issue_risk_views.py` (216)
- `file_views.py` (1,137)

#### Misc / Other
- `client_mgmt_views.py` (698)
- `portal_views.py` (425)
- `misc_views.py` (926) — settings, language, profile, root redirects
- `bi_views.py` (36)
- `strategic_planning_views.py` (180) + `strategic_planning_frontend.py` (71)
- `_helpers.py` (310) — **shared helpers; NOT a view module** (auth checks, role helpers, query helpers)

### 3.3 Module conventions

- Every view module imports shared helpers from `core.views._helpers`.
- Every view function/CBV requires `@login_required` (audited in Phase C, enforced in CI by smoke test).
- Templates live under `core/templates/core/` and follow Tailwind-first conventions for new pages; Bootstrap 5 retained where legacy CSS still depends on it.
- Translatable strings use `gettext_lazy as _` at module-level, `gettext as _` inside view bodies.

## 4. Test infrastructure

Located in `tests/`. Run with `python -m pytest tests/ -x -q`.

| File                                | Purpose                                                                                       |
|-------------------------------------|-----------------------------------------------------------------------------------------------|
| `tests/test_url_smoke.py`           | Walks every URL pattern via `get_resolver()`, hits as superuser. Catches 5xx regressions.    |
| `tests/test_performance_audit.py`   | Counts SQL queries per critical page (`CaptureQueriesContext`). Fails on N+1 regressions.   |
| `tests/test_*.py` (model/feature)   | Unit & integration tests per app feature.                                                     |

**Current baseline:** 906 tests passing. URL smoke covers 1,032 routes (806 skipped for token-only or webhook URLs).

### 4.1 Performance budgets (enforced)

| URL name             | Budget | Current |
|----------------------|-------:|--------:|
| `dashboard`          | 30     | 8       |
| `dashboard_admin`    | 50     | 40      |
| `dashboard_pm`       | 50     | 31      |
| `dashboard_employee` | 50     | 13      |
| `project_list`       | 30     | 12      |
| `invoice_list`       | 30     | 20      |
| `client_list`        | 30     | 13      |

If a future change pushes a view over budget, `test_performance_audit.py` fails CI with the top-5 SQL patterns of the regression — diagnose with `select_related` / `prefetch_related`.

## 5. URL & permission model

- All non-public URLs require `@login_required`.
- Role gating done via `_helpers.is_admin / is_pm / is_employee / is_client / is_designer`.
- `UserProfile.role` is the source of truth (never `User.is_staff` for app permissions; only Django admin uses that).
- See `docs/ROLE_PERMISSIONS_REFERENCE.md` for the full matrix.

## 6. i18n

- `LANGUAGE_CODE = 'es'` default; `en` available.
- Switching: `core/views/misc_views.py::set_language_view` (Django 4.0-compatible, sets `settings.LANGUAGE_COOKIE_NAME` in session).
- `.po` files under `locale/` per language. Use `python manage.py makemessages -l en` after string changes.
- `TIME_ZONE = "America/Denver"`.

## 7. Conventions for new code

1. **Add a view → place in the matching domain module** (or create a new module if a new domain). NEVER add to `legacy_views.py` shim.
2. **Decorate with `@login_required`** and any role check.
3. **Use `select_related` / `prefetch_related`** for any ForeignKey/M2M iterated in a template.
4. **Add a translatable string** — wrap in `_()`.
5. **Run `pytest -x -q`** before commit. Smoke + perf tests must stay green.
6. **Templates**: Tailwind-first for new pages; reuse `core/templates/core/components/` partials.
7. **Commit message** prefix with phase or feature (e.g. `Phase 9: …`, `feat(invoices): …`).

## 8. Reference docs

| Topic                   | File                                          |
|-------------------------|-----------------------------------------------|
| Project quick start     | `docs/QUICK_START.md`                         |
| Deployment (Railway)    | `docs/DEPLOYMENT_MASTER.md`                   |
| API endpoints           | `docs/API_ENDPOINTS_REFERENCE.md`             |
| Role / permissions      | `docs/ROLE_PERMISSIONS_REFERENCE.md`          |
| Modules spec            | `docs/MODULES_SPECIFICATIONS.md`              |
| Security                | `docs/SECURITY_COMPREHENSIVE.md`              |
| Roadmap                 | `docs/ROADMAP.md`                             |
| Translation guide       | `docs/CONTRIBUTING_TRANSLATIONS.md`           |

---

*This document is the canonical architecture reference after the 2025-12 refactor cycle. Update it when the module map changes.*
