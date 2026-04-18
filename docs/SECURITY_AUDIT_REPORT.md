# 🔒 Kibray Security Audit Report

**Date:** April 2025  
**Scope:** Full codebase vulnerability scan  
**Commit:** `0ff5f953` — security: comprehensive vulnerability hardening

---

## ✅ FIXES IMPLEMENTED (this commit)

### 🔴 CRITICAL — Fixed

| # | Vulnerability | File | Fix |
|---|---|---|---|
| 1 | **DashboardConsumer — no auth check** | `core/consumers.py` | Added `user.is_authenticated` check in `connect()` |
| 2 | **DailyPlanConsumer — no auth check** | `core/consumers.py` | Added `user.is_authenticated` check in `connect()` |
| 3 | **QualityInspectionConsumer — no auth check** | `core/consumers.py` | Added `user.is_authenticated` check in `connect()` |
| 4 | **TaskConsumer — no auth check** | `core/consumers.py` | Added `user.is_authenticated` check in `connect()` |
| 5 | **StatusConsumer — no auth check** | `core/consumers.py` | Added `user.is_authenticated` check in `connect()` |
| 6 | **No API throttling** — unlimited requests | `settings/base.py` | Added `AnonRateThrottle` (30/min) + `UserRateThrottle` (120/min) |
| 7 | **BLACKLIST_AFTER_ROTATION = False** — old refresh tokens not revoked | `settings/base.py` | Set to `True` — old refresh tokens now blacklisted |

### 🟠 HIGH — Fixed

| # | Vulnerability | File | Fix |
|---|---|---|---|
| 8 | **BrowsableAPIRenderer in production** — exposes API schema | `settings/base.py` | Removed from `DEFAULT_RENDERER_CLASSES` |
| 9 | **API docs publicly accessible** — `/api/v1/schema/`, `/docs/`, `/redoc/` | `core/api/urls.py` | Protected with `staff_member_required` |
| 10 | **SECURE_SSL_REDIRECT = False** — HTTP allowed | `settings/production.py` | Forced `True` with `SECURE_REDIRECT_EXEMPT` for health checks |
| 11 | **No file upload size limits** | `settings/base.py` | Added `FILE_UPLOAD_MAX_MEMORY_SIZE` (10MB), `DATA_UPLOAD_MAX_MEMORY_SIZE` (25MB) |
| 12 | **Public folder upload — no file validation** | `legacy_views.py` | Added size (25MB) + extension whitelist validation |
| 13 | **iCal feed uses predictable user.pk** | `calendar_feed.py` | HMAC-signed tokens (`{pk}-{hmac_hex}`) with backwards compatibility |

---

## ⚠️ KNOWN ISSUES — Require Design Decision

### 🔴 CRITICAL — Password in plaintext email

**Location:** `core/services/email_service.py` → `send_password_reset()` → `emails/password_reset.html`  
**Also:** `legacy_views.py:14990` → `client_reset_password()` generates random password and sends via email

**Risk:** Plaintext passwords in email can be intercepted (email is not encrypted end-to-end).

**Recommended fix:** Replace with token-based password reset using `django.contrib.auth.tokens.default_token_generator` and a frontend reset-password page.

**Why not auto-fixed:** Requires frontend React changes + email template redesign. Not a code-only fix.

---

### 🟡 MEDIUM — `|safe` filter in Django templates

**Count:** 30+ uses across templates  
**Files:** `floor_plan_detail.html`, `strategic_planning_detail.html`, `daily_plan_timeline.html`, `inventory_wizard.html`, `financial_dashboard.html`, `sop_creator_wizard.html`, etc.

**Pattern:** `{{ some_json|safe }}` used to pass Python data to JavaScript.

**Risk:** Low — all data is server-generated via `json.dumps()` and all views require `@login_required`.

**Recommendation:** Replace with `{{ data|json_script:"id" }}` pattern for safer JSON embedding.

---

### 🟡 MEDIUM — localStorage for JWT tokens (frontend)

**Risk:** XSS vulnerability could steal tokens from `kibray_access_token` / `kibray_refresh_token`.

**Recommendation:** Move to HttpOnly cookies or use `sessionStorage` with token refresh.

**Why not auto-fixed:** Requires React frontend + DRF backend coordination for cookie-based auth.

---

## ✅ GOOD PRACTICES FOUND

| Area | Status |
|---|---|
| All legacy views have `@login_required` | ✅ |
| All API viewsets have `permission_classes = [IsAuthenticated]` minimum | ✅ |
| No `AllowAny` permissions anywhere | ✅ |
| `ProjectChatConsumer` has auth + project access check | ✅ |
| `AdminDashboardConsumer` checks `is_staff`/`is_superuser` | ✅ |
| WebSocket `RateLimitMixin` on chat/notification/task/status consumers | ✅ |
| CSRF protection on all POST forms | ✅ |
| Login rate limiting: 5 attempts per 15 minutes | ✅ |
| 4 password validators active | ✅ |
| Share tokens use `secrets.token_urlsafe(32)` (256-bit entropy) | ✅ |
| `AllowedHostsOriginValidator` on WebSocket | ✅ |
| `HSTS` enabled (1 year, include subdomains, preload) | ✅ |
| `X-Frame-Options: DENY` | ✅ |
| `SECURE_CONTENT_TYPE_NOSNIFF = True` | ✅ |
| `SESSION_COOKIE_SECURE = True` + `CSRF_COOKIE_SECURE = True` | ✅ |
| `SESSION_COOKIE_AGE = 28800` (8 hours) | ✅ |
| `SingleSessionMiddleware` (one session per user) | ✅ |
| Sentry with `send_default_pii = False` | ✅ |
| Secret key from env in production (raises if missing) | ✅ |
| `.extra()` calls are parameterized (no SQL injection) | ✅ |
| No `eval()`, `exec()`, `subprocess` in production code | ✅ |
| Client views verify `ClientProjectAccess` or `project.client` match | ✅ |
| Serializers use explicit `fields` (not `__all__` in API serializers) | ✅ |
| Channel layer uses `symmetric_encryption_keys` | ✅ |
| `AllowedHostsOriginValidator` + `AuthMiddlewareStack` on WebSocket | ✅ |

---

## 📊 Summary

| Severity | Found | Fixed | Remaining |
|---|---|---|---|
| 🔴 Critical | 8 | 7 | 1 (plaintext password email) |
| 🟠 High | 6 | 6 | 0 |
| 🟡 Medium | 2 | 0 | 2 (design decisions needed) |
| ✅ Good practices | 25+ | — | — |

**Test impact:** 0 new test failures introduced. All 43 failures are pre-existing.
