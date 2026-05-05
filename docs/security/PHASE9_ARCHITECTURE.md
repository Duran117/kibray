# Phase 9 — Proposed Authorization Architecture

**Pairs with:** `PHASE9_AUDIT.md`
**Status:** Foundation (`core/access.py`) shipped this commit. Refactor of views/sidebar pending approval.

---

## 1. Design principles

1. **One source of truth.** A single module (`core/access.py`) defines every role check, project-access helper, and capability check. Decorators, view bodies, forms, serializers, context processors, sidebar — all read from it.
2. **Layered, not flat.** Five distinct layers, each with a clear job:
   - **Layer 1 — Role identity**: `is_admin(user)`, `is_pm(user)`, `is_employee(user)`, `is_client(user)`, `is_staffish(user)`.
   - **Layer 2 — Project access** (object-level): `can_view_project(user, project)`, `can_edit_project(user, project)`. Backed by `accessible_projects(user)` queryset helper.
   - **Layer 3 — Capability checks** (feature × project): `can_view_financials(user, project)`, `can_view_labor_cost(user, project)`, `can_view_change_order_price(user, co)`, `can_create_schedule_event(user, project)`, etc. Each is a small named function.
   - **Layer 4 — View protection**: decorators (`@admin_required`, `@project_access_required('project_id')`, `@capability_required('view_financials', 'project_id')`) plus mixins for class-based views.
   - **Layer 5 — Navigation**: a `nav.py` module that exposes `build_sidebar(user, project=None)` which returns a list of `MenuItem` objects, *each filtered through layers 1–3*. Sidebar template just iterates — zero `{% if role == ... %}`.
3. **Backend-first.** UI hiding is a *consequence* of the permission, never the gate. Every menu item resolves to a URL that is independently protected by Layer 4.
4. **Whitelist, not blacklist.** A view is forbidden by default; it explicitly opts in to who can see it. (Today's code is the inverse: open by default, with ad-hoc `if profile.role == 'client'` blacklist patches.)
5. **No string magic.** Constants in one place: `ROLE_ADMIN`, `ROLE_PM`, `ROLE_EMPLOYEE`, `ROLE_CLIENT`, etc. No more `"pm"` vs `"project_manager"` divergence.
6. **Backwards-compatible rollout.** `core/access.py` adds new helpers; it does not remove the old ones. Refactor views and templates in small commits, replacing old patterns with calls into `access`. Old helpers (`_is_admin_user`, `is_staffish`, `_require_admin_or_redirect`) become thin shims that delegate to `access` and emit `DeprecationWarning`. Eventually deleted.

---

## 2. Module layout

```
core/
├── access.py              # NEW — single source of truth (Layer 1, 2, 3 helpers)
├── access_decorators.py   # NEW — Layer 4 decorators + class-based mixins
├── nav.py                 # NEW — Layer 5 sidebar/menu builder (data, not template)
├── security_decorators.py # KEEP — re-exports access_decorators for compat; deprecated
├── views/_helpers.py      # SHRINK — delegates to access; old helpers become shims
├── api/permissions.py     # REWRITE — DRF permission classes built on access.py
└── context_processors.py  # SHRINK — `recent_projects` calls accessible_projects()
```

---

## 3. `core/access.py` — public surface (shipped this commit)

```python
# Role constants
ROLE_ADMIN          = "admin"
ROLE_OWNER          = "owner"
ROLE_PM             = "project_manager"
ROLE_EMPLOYEE       = "employee"
ROLE_CLIENT         = "client"
ROLE_DESIGNER       = "designer"
ROLE_SUPERINTENDENT = "superintendent"

INTERNAL_ROLES = {ROLE_ADMIN, ROLE_OWNER, ROLE_PM, ROLE_EMPLOYEE,
                  ROLE_DESIGNER, ROLE_SUPERINTENDENT}

# ── Layer 1: identity ──────────────────────────────
def get_role(user) -> str | None
def is_admin(user) -> bool             # superuser OR Profile.role == ROLE_ADMIN
def is_owner(user) -> bool             # Profile.role == ROLE_OWNER
def is_pm(user) -> bool                # Profile.role == ROLE_PM
def is_employee(user) -> bool          # Profile.role == ROLE_EMPLOYEE and not staff
def is_client(user) -> bool            # Profile.role == ROLE_CLIENT
def is_internal(user) -> bool          # any of admin/owner/pm/employee/designer/super
def is_staffish(user) -> bool          # admin OR pm OR is_staff (for "internal-tools" gate)

# ── Layer 2: project access ────────────────────────
def accessible_projects(user) -> QuerySet[Project]
def can_view_project(user, project) -> bool
def can_edit_project(user, project) -> bool
def get_client_access(user, project) -> ClientProjectAccess | None

# ── Layer 3: capabilities ──────────────────────────
# Financial
def can_view_financials(user, project) -> bool
def can_view_labor_cost(user, project) -> bool
def can_view_profit(user, project) -> bool
def can_view_expenses(user, project) -> bool
def can_view_incomes(user, project) -> bool
def can_view_budget(user, project) -> bool
# Schedule
def can_view_schedule(user, project) -> bool
def can_create_schedule_event(user, project) -> bool
def can_edit_schedule_event(user, event) -> bool
# Change orders
def can_view_change_order(user, co) -> bool
def can_create_change_order(user, project) -> bool
def can_approve_change_order(user, co) -> bool
def can_view_change_order_price(user, co) -> bool
# Internal / employee
def can_view_employee_data(user) -> bool
def can_view_internal_notes(user, project) -> bool
# Client portal
def can_access_client_portal(user, project) -> bool
def can_view_client_safe_data(user, project) -> bool

# ── Convenience ─────────────────────────────────────
def assert_can_view_project(user, project)  # raises PermissionDenied
def filter_by_project_access(user, qs, project_field="project")
```

### Decision rules (canonical)

- `accessible_projects(user)`:
  - admin / superuser / `is_staff` → `Project.objects.all()`
  - PM → projects via `ProjectManagerAssignment(pm=user)` ∪ projects whose `created_by=user` (back-compat fallback).
    *Open question — see audit Q1. For now: assigned + created. Easy to tighten later.*
  - employee → projects where the user has any `ResourceAssignment` or `TimeEntry`.
  - client → projects via `ClientProjectAccess(user=user, is_active=True)` ∪ projects whose `client` text-matches `username/email/full_name` (legacy soft-match, kept for back-compat).
  - others → `Project.objects.none()`.
- `can_view_project(user, project)` ↔ `project in accessible_projects(user)`. (Implementation: short-circuit per role to avoid full QuerySet evaluation.)
- `can_view_financials(user, project)`:
  - internal staff (admin/PM/owner) AND has project access → True.
  - employee → False (always).
  - client → True only if `ClientProjectAccess.can_view_financials=True`.
- `can_view_change_order_price(user, co)` = `can_view_financials(user, co.project)`.
- `can_view_labor_cost`, `can_view_profit` → admin/owner only (PM gets it only if explicitly enabled — for now: admin/owner only).
- `can_view_internal_notes` → internal only (no clients ever).

These rules are **specifications**; the actual code in `core/access.py` matches them line-by-line. Tests in `tests/test_access_helpers.py` lock them down.

---

## 4. `core/access_decorators.py` (next commit)

```python
@admin_required               # superuser or admin role; redirect with msg if not
@internal_required            # any internal role; redirect if client
@project_access_required("project_id")          # must pass can_view_project
@capability_required("view_financials", "project_id")
                              # generic Layer 3 gate
class AdminRequiredMixin:     # for class-based views
class ProjectAccessRequiredMixin: ...
class CapabilityRequiredMixin: ...
```

Returns 403 for AJAX (`X-Requested-With: XMLHttpRequest`), `redirect("dashboard")` with `messages.error()` for HTML.

---

## 5. `core/nav.py` (next commit) — sidebar refactor

```python
@dataclass
class MenuItem:
    key: str
    label: str
    url_name: str
    icon: str
    capability: str | None = None    # name of access.* function
    project_scoped: bool = False
    badge_key: str | None = None

GLOBAL_MENU: list[MenuItem] = [...]   # static config
PROJECT_MENU: list[MenuItem] = [...]  # static config

def build_sidebar(user, project=None) -> dict:
    """Filter menus by access.can_* + return sections {global, project, footer}."""
```

`sidebar_dark.html` becomes ~80 lines: a single `{% for section in sidebar.sections %}{% for item in section.items %}…{% endfor %}{% endfor %}`. Zero role conditionals in the template. **Same permission layer** as the backend — no drift possible.

---

## 6. Rollout plan (each = its own commit, each runs full pytest)

- **Commit A (this one)** — Add `core/access.py` + tests. **No callers modified.** Zero behavior change. Safe to merge.
- **Commit B** — Add `core/access_decorators.py` + tests. Add `assert_can_view_project` usage in 3 highest-risk views (`financial_dashboard`, `client_financials_view`, `expense_list`) as proof. Pytest must stay green.
- **Commit C** — Refactor 18 unscoped `Project.objects.all()` callsites to `accessible_projects(request.user)`. Pytest + manual smoke for admin/PM/client.
- **Commit D** — Fix `forms.py:931, 970` and 4 serializer `Project.objects.all()` queryset leaks.
- **Commit E** — Fix `api/permissions.py` `"pm"` → `ROLE_PM` constant; rewrite DRF classes on top of `access.py`.
- **Commit F** — Replace 38 inline `profile.role == "..."` checks with `is_*` / `can_*` calls. Mechanical; commit per file group.
- **Commit G** — Build `core/nav.py`. Render new sidebar template behind a feature flag; A/B against current sidebar.
- **Commit H** — Flip flag, delete old sidebar inline conditionals.
- **Commit I** — Add cross-role regression test suite (`tests/test_role_isolation.py`) — proves Client A can't read Client B's project, etc.
- **Commit J** — Mark `_is_admin_user`, `is_staffish`, `require_project_access` as deprecated shims (warn but still work). Final cleanup deferred to a separate session.

Estimated: 9 small commits, ~3–4 working sessions of ~2 hours each. Each commit individually revertible.

---

## 7. What this commit (A) actually contains

- `core/access.py` — full implementation of Layers 1, 2, 3.
- `tests/test_access_helpers.py` — ~30 unit tests covering every helper across all 4 roles + edge cases (superuser, no profile, deactivated `ClientProjectAccess`, role string mismatches).
- `docs/security/PHASE9_AUDIT.md` (this audit).
- `docs/security/PHASE9_ARCHITECTURE.md` (this proposal).

**No view, sidebar, form, serializer, decorator, or context processor is modified in this commit.** Pytest baseline (1475 passed, 17 skipped) must remain unchanged.

---

## 8. Decisions you should approve before Commit B

1. **PM scope** — Do PMs see *all projects* (current) or only *assigned + created* (proposed)? Default I'm using: assigned + created.
2. **Employee scope** — Do employees see all projects they have *any* time entry on, or only those *currently assigned* (`ResourceAssignment`)? Default I'm using: union (any time entry OR active assignment) — wider, safer for legitimate UX, still restrictive vs admin.
3. **Legacy text-match (`project.client == user.username`)** — Keep as fallback (proposed) or kill it now? Default I'm using: keep as fallback to avoid breaking pre-`ClientProjectAccess` data, but log a warning so you can migrate.
4. **`can_view_financials` for PM** — Always True for assigned project (proposed) or gated by a new explicit flag? Default I'm using: always True for assigned (matches current behavior).
5. **Designer / Superintendent** — Treated as `is_internal` (proposed) — so they get internal-staff capabilities scoped to their assigned projects. OK?

Reply with any "no" / changes; otherwise I proceed with these defaults in Commit B.
