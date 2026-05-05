# Phase 9 — Authorization Audit

**Date:** May 5, 2026
**Status:** Audit complete — implementation pending approval
**Author:** Authorization refactor pass

---

## 1. Phase 1 — What exists today (audit findings)

### 1.1 Role definitions (multiple sources of truth — biggest problem)

There are **at least 4 overlapping role concepts** in the codebase:

| Source | File | Roles | Used by |
|---|---|---|---|
| `Profile.role` | `core/models/__init__.py:1990` | `admin`, `owner`, `employee`, `project_manager`, `client`, `designer`, `superintendent` | sidebars, view guards, context processors |
| `ClientProjectAccess.role` | `core/models/__init__.py:2043` | `client`, `owner`, `external_pm`, `viewer` (per-project) | client portal only |
| `UserRolePermission.role` | `core/models/__init__.py:6106` (Q16.1 RBAC matrix) | broader set | declared but **not used** by any view |
| `Employee.role` | `core/models/__init__.py:9882` | `executive`, `accounting`, `owner`, … | payroll/dashboard only |
| Django built-ins | n/a | `is_superuser`, `is_staff` | mixed, inconsistently |
| `api/permissions.py` | DRF | uses `"pm"` (NOT `"project_manager"`) | API only — **role string mismatch with rest of app** |

**Bug confirmed:** `core/api/permissions.py:39` checks `profile.role in ["owner", "pm"]`, but the actual role string in `Profile.ROLE_CHOICES` is `"project_manager"`. So every `IsOwnerOrPM` API check is silently broken (always returns False for legitimate PMs).

### 1.2 Permission-check helpers that already exist

- `core/security_decorators.py` — `require_role`, `require_project_access`, `is_staffish`, `ajax_login_required`, `rate_limit`. **Used in some places, ignored in others.**
- `core/views/_helpers.py` — `_is_admin_user`, `_require_admin_or_redirect`, `_require_roles`, `_is_staffish`, `_user_can_access_project`. Used by some views in `core/views/*`, **but not by `core/views_*.py` flat modules**.
- `core/api/permissions.py` — DRF permission classes (broken role strings, see above).

**Three parallel permission systems** that don't share helpers, don't share role strings, and don't share definitions of "staff-like".

### 1.3 Sidebar / navigation

- Single template: `core/templates/core/components/sidebar_dark.html` (~575 lines).
- 38+ inline conditionals like `{% if role == 'client' %}`, `{% if user.is_staff or role == 'admin' %}`.
- Phase 8 (commit `9b03a635`) split the project-context block 3-way (client / employee / staff) and added regression tests, but **the rest of the sidebar still mixes role rules inline**.
- Visibility logic in template ≠ backend visibility (no shared source).
- `context_processors.py` has a separate `recent_projects` filter for clients/employees — different code path, different rules.

### 1.4 Querysets that are NOT scoped (data-leak surface)

| File | Line | Query |
|---|---|---|
| `core/api/views.py` | 2680 | `Project.objects.all()` |
| `core/api/views.py` | 3958 | `TimeEntry.objects.all()` |
| `core/api/views.py` | 5208 | `Invoice.objects.all()` |
| `core/api/views.py` | 5478 | `Project.objects.all()` |
| `core/forms.py` | 931, 970 | `Project.objects.all()` (form choices — a client opening this form sees all projects) |
| `core/api/serializer_classes/task_serializers.py` | 103 | `queryset=Project.objects.all()` |
| `core/api/serializer_classes/task_serializers.py` | 105 | `queryset=Employee.objects.all()` |
| `core/api/serializer_classes/schedule_v2_serializers.py` | 208 | `queryset=Project.objects.all()` |
| `core/api/serializer_classes/changeorder_serializers.py` | 75 | `queryset=Project.objects.all()` |
| `core/views_assignments.py` | 52, 138 | `Project.objects.all()` (HR-side, lower risk but still wrong) |
| `core/views_unassigned_hours.py` | 43 | `Project.objects.all()` |
| `core/views_timeentry_assignment.py` | 84 | `Project.objects.all()` |
| `core/views/expense_income_views.py` | 49, 177, 500 | `Project.objects.all()` |
| `core/views/project_crud_views.py` | 253 | `Project.objects.all()` |
| `core/views/dashboard_pm_views.py` | 555 | `Project.objects.all()` (PM dashboard — should be assigned-only) |
| `core/services/ev_snapshots.py` | 203 | `Project.objects.all()` (background; lower urgency) |

**Note:** Several of these are guarded upstream (admin-only views), so the queryset itself isn't the leak — but there's no enforcement; nothing prevents a future change from removing the guard while leaving the unscoped query.

### 1.5 Scattered ad-hoc role checks

38+ inline `profile.role == "client"` / `profile.role == "admin"` checks across:

- `core/views_financial.py` (3 admin checks — duplicated)
- `core/views_client_calendar.py`
- `core/views_notifications.py`
- `core/views/_helpers.py`
- `core/views/site_photo_views.py`
- `core/views/misc_views.py`
- `core/views/schedule_views.py`
- `core/views/file_views.py`
- `core/views/task_views.py`
- `core/views/project_client_portal_views.py`
- `core/views/color_floor_views.py`
- `core/views/chat_views.py`
- `core/api/permissions.py`
- `core/context_processors.py`

Several inline checks reuse the **legacy "client matches by username text"** pattern:

```python
project.client == request.user.username           # in security_decorators.py:130
client_text == user.email.lower() or ...          # in _helpers.py:184-187
project.client == request.user.username           # in client_financials_view
```

This is a **soft-string match** — fragile, undocumented, and inconsistent across files. Some places also check `email`, `username`, OR `full_name`; others only `username`.

### 1.6 Direct conclusions

- **There is no single source of truth for "what can this user see".** Every change to one role re-breaks another because the rules are duplicated 5+ ways across decorators, helpers, view bodies, sidebar template, context processor, and DRF permissions.
- **Financial guards are duplicated as inline 5-line `if` blocks** in `views_financial.py` (3×) and `views/misc_views.py`. None call `_require_admin_or_redirect`, even though that helper exists.
- **DRF API permissions use the wrong role string `"pm"`** and have been silently failing for PMs.
- **Several form QuerySets leak the full project list** to non-admin users (`forms.py:931, 970`).
- **Client-access detection has 3 different soft-match implementations** that may diverge.

---

## 2. Phase 2 — Target role/access matrix

Assumptions (challenge any of these and I'll revise):

- "Admin" = Django `is_superuser` OR `Profile.role == "admin"`.
- "Staff-like internal" = Admin OR `Profile.role == "project_manager"` OR `is_staff=True` flag.
  (`is_staff` mostly correlates with "internal employee with admin login"; we treat it as staff-like.)
- "Employee" = `Profile.role == "employee"` AND not `is_staff`.
- "Client" = `Profile.role == "client"` (no staff, no superuser).
- A user can be an admin OR a PM OR an employee OR a client. If multiple flags conflict, the *more privileged* wins (admin > pm > employee > client). This matches current sidebar behavior.

### 2.1 Capability matrix

Legend: ✅ allowed, ⚠️ allowed but project-scoped, ❌ denied, 🟡 client-safe filtered subset.

| Capability | Admin | PM | Employee | Client |
|---|:-:|:-:|:-:|:-:|
| Login | ✅ | ✅ | ✅ | ✅ |
| Global financial dashboard (`/finanzas/dashboard/`) | ✅ | ❌ | ❌ | ❌ |
| Company-wide expense list / income list | ✅ | ❌ | ❌ | ❌ |
| Admin tools (user mgmt, role mgmt) | ✅ | ❌ | ❌ | ❌ |
| All-projects list | ✅ | ⚠️ assigned only | ⚠️ assigned only | ⚠️ assigned only |
| Project detail (overview) | ✅ | ⚠️ assigned | ⚠️ assigned | 🟡 client-safe view |
| Project schedule/calendar (read) | ✅ | ⚠️ assigned | ⚠️ assigned | 🟡 read-only |
| Project schedule create/edit | ✅ | ⚠️ assigned | ❌ | ❌ |
| Project budget | ✅ | ⚠️ assigned | ❌ | ❌ (unless `can_view_financials`) |
| Project expenses | ✅ | ⚠️ assigned | ❌ | ❌ |
| Project incomes / invoices | ✅ | ⚠️ assigned | ❌ | 🟡 own invoices only if granted |
| Project labor cost / profit | ✅ | ⚠️ assigned | ❌ | ❌ (always) |
| Change orders (read) | ✅ | ⚠️ assigned | ❌ | 🟡 see+approve own |
| Change orders create | ✅ | ⚠️ assigned | ❌ | ❌ |
| Change order **price** visible | ✅ | ⚠️ assigned | ❌ | 🟡 only if `can_view_financials` |
| Change order approve | ✅ | ⚠️ assigned | ❌ | 🟡 if `can_approve_change_orders` |
| Photos / public documents | ✅ | ⚠️ assigned | ⚠️ assigned | 🟡 `is_public=True` only |
| Internal notes | ✅ | ⚠️ assigned | ❌ | ❌ |
| Employee directory / pay rates | ✅ | ❌ | ❌ | ❌ |
| Time entries (own) | ✅ | ⚠️ assigned | ✅ own only | ❌ |
| Time entries (others') | ✅ | ⚠️ assigned employees | ❌ | ❌ |
| Materials request (own project) | ✅ | ⚠️ assigned | ⚠️ assigned | ❌ |
| Client portal pages (`/portal/...`) | ✅ (impersonating allowed projects) | ❌ unless explicit access | ❌ | 🟡 own projects |
| Activity menu items | full | PM-safe ops | own work | client-safe only |
| Direct URL to forbidden view | 200 | 403/redirect | 403/redirect | 403/redirect |
| Manually crafting URL with another client's `project_id` | 200 | 403/redirect | 403/redirect | 403/redirect |

### 2.2 Open business questions to confirm with stakeholder

1. Should a PM see *all* projects in the global lists (current behavior), or only those they're assigned to via `ProjectManagerAssignment`? Current code = "all"; matrix above says "assigned only". **Default: assigned only** unless you say otherwise.
2. Can a PM see overall company financial dashboard? Current = no (admin-only). **Keep**.
3. Can an employee see other employees' time entries within projects they share? **Default: no.**
4. When a client has multiple projects, can they see a global "my projects" list? **Yes — but limited to their own.**

---

## 3. Phase 3 — Gap analysis (current vs target)

| # | Gap | Impact | Roles affected |
|---|---|---|---|
| G1 | Three role systems with mismatched strings (`"pm"` vs `"project_manager"`) | DRF API silently denies PMs | PM |
| G2 | No `core/access.py` — every view re-implements role/project access | Every refactor introduces regressions | All |
| G3 | Form QuerySets `Project.objects.all()` in `forms.py:931, 970` | A client editing certain forms would see *every* project in the dropdown | Client |
| G4 | API `Invoice.objects.all()`, `Project.objects.all()`, `TimeEntry.objects.all()` not scoped | API endpoints leak across tenants if a non-admin gets a token | PM, employee, client |
| G5 | `views_financial.py` has 3 duplicated 5-line admin guards instead of using `_require_admin_or_redirect` | Future refactor risk | All |
| G6 | Client-access soft-match (`project.client == username`) implemented 3 different ways | Drift bugs (client A sees project B because of email collision) | Client |
| G7 | Sidebar = 575-line template with 38+ role conditionals | Phase 8 had to rewrite one block; the rest will keep leaking until centralized | All |
| G8 | No object-level permission checks on shared detail views (`task_views.py`, `file_views.py`, etc.) for non-admin reads | Client/employee can craft `?id=X` URLs to view foreign objects | Client, employee |
| G9 | `is_client_view` flag on shared templates (`documents_workspace.html`) is opt-in by view, not enforced | If someone forgets the flag, internal upload UI renders for clients | Client |
| G10 | No tests covering "client A cannot read client B's project", "PM cannot read unassigned project", etc. | Regressions invisible | All |
| G11 | `ProjectManagerAssignment` exists but is rarely consulted; PMs effectively have global read | PM scope undefined | PM |
| G12 | `ChangeOrder` views don't differentiate `can_view_change_order_price` from `can_view_change_order` | Clients without financial access can still see prices | Client |

---

## 4. What is already good (don't break it)

- `Profile.role` model is fine as the canonical role field.
- `ClientProjectAccess` is a well-structured per-project ACL with explicit `can_view_financials`, `can_approve_change_orders`, etc. **Build on top of it.**
- `security_decorators.require_project_access` works as designed for the views that use it.
- `_helpers._user_can_access_project` already does the right soft-match logic (just needs to be the only implementation).
- Phase 8 sidebar 3-way split for project-context block is the right pattern; we'll generalize it.
- 1475 tests pass today — we have a baseline to defend.

---

## 5. Next phases

- **Phase 4** — Proposed architecture → see `PHASE9_ARCHITECTURE.md`.
- **Phase 5** — Land `core/access.py` foundation (no view edits yet) — *this commit*.
- **Phase 6+** — Refactor querysets, then views, then sidebar, then tests, **one slice at a time**, each in its own commit so regressions can be bisected.
