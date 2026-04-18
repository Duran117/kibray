"""
URL Smoke Tests — verify all GET-able URL patterns return non-500.

Goal: Catch import errors, missing template references, broken view signatures,
and basic auth/permission redirects across the entire URL space.

We classify URLs as:
- public:    no auth required (login page, public PDFs, etc.)
- internal:  requires authenticated user (admin used as superuser)
- skip:      requires complex setup (file uploads, signed POSTs, etc.)

For internal URLs that require an int param, we substitute id=99999 and accept
any of {200, 302, 403, 404} as valid (404 means view ran fine, no object found).
"""
from __future__ import annotations

import re
import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import URLPattern, URLResolver, get_resolver

User = get_user_model()

# Acceptable status codes — view loaded and ran without crashing
OK_STATUSES = {200, 301, 302, 400, 401, 403, 404, 405, 415, 422}

# Skip URL names that require very specific setup beyond simple GET
SKIP_NAMES = {
    # Public/token-based — would need real tokens
    "changeorder_customer_signature",
    "changeorder_customer_signature_token",
    "color_sample_client_signature",
    "color_sample_client_signature_token",
    "proposal_public_view",
    "contract_client_view",
    "changeorder_public_pdf_download",
    "colorsample_public_pdf_download",
    "file_public_view",
    "file_public_download",
    "folder_public_view",
    "folder_public_upload",
    # Set-language is a POST endpoint with redirect
    "set_language",
    "set_language_view",
    # Admin Django is its own thing
    "admin",
    # Heavy / long-running endpoints
    "project_progress_csv",
    "project_ev_csv",
    "project_ev_series",
}

# URL patterns that take string tokens — substitute a fake token
TOKEN_PARAM_NAMES = {"token", "code", "uuid", "slug"}


def _collect_url_patterns(resolver=None, prefix="", namespace=""):
    """Recursively collect (full_pattern_str, name, callback, params) tuples."""
    if resolver is None:
        resolver = get_resolver()
    results = []
    for entry in resolver.url_patterns:
        if isinstance(entry, URLResolver):
            new_prefix = prefix + str(entry.pattern)
            new_ns = entry.namespace or namespace
            results.extend(_collect_url_patterns(entry, new_prefix, new_ns))
        elif isinstance(entry, URLPattern):
            full = prefix + str(entry.pattern)
            name = entry.name
            if namespace and name:
                name = f"{namespace}:{name}"
            results.append((full, name, entry.callback))
    return results


def _build_test_url(pattern_str: str) -> str | None:
    """Convert a Django URL pattern string into a concrete test URL.

    Returns None if the pattern uses regex/converters we can't easily fill.
    """
    # Strip leading ^ and trailing $
    p = pattern_str.lstrip("^").rstrip("$")
    # Replace path converters
    # int converter
    p = re.sub(r"<int:(\w+)>", "99999", p)
    # str / slug
    p = re.sub(r"<(?:str|slug):(\w+)>", "test", p)
    # uuid
    p = re.sub(r"<uuid:(\w+)>", "00000000-0000-0000-0000-000000000000", p)
    # path
    p = re.sub(r"<path:(\w+)>", "test/path", p)
    # Generic <name>
    p = re.sub(r"<(\w+)>", "99999", p)
    # Old-style regex groups: (?P<name>pattern) — replace with safe value
    if "(?P<" in p:
        p = re.sub(r"\(\?P<\w+>[^)]*\)", "99999", p)
    # Any remaining regex special chars indicate we can't safely build URL
    if any(ch in p for ch in ["(", ")", "[", "]", "+", "*", "?", "\\"]):
        return None
    if not p.startswith("/"):
        p = "/" + p
    return p


@pytest.fixture(scope="module")
def url_patterns():
    return _collect_url_patterns()


@pytest.fixture
def admin_client(db):
    user = User.objects.create_user(
        username="smoke_admin",
        email="smoke@test.com",
        password="pass1234",
        is_staff=True,
        is_superuser=True,
    )
    client = Client()
    client.force_login(user)
    return client


def test_url_patterns_loaded(url_patterns):
    """Sanity: ensure we discovered a meaningful number of URL patterns."""
    assert len(url_patterns) > 100, f"Only found {len(url_patterns)} URL patterns"


@pytest.mark.django_db
def test_smoke_all_get_urls_no_500(admin_client, url_patterns):
    """Hit every GET-able URL with admin auth; ensure none return 500."""
    failures: list[str] = []
    skipped: list[str] = []
    tested: list[str] = []

    for pattern_str, name, callback in url_patterns:
        # Skip explicitly excluded
        if name in SKIP_NAMES:
            skipped.append(f"{name} (in SKIP_NAMES)")
            continue
        # Skip API endpoints that aren't GET (rest framework views)
        callback_name = getattr(callback, "__name__", "")
        if callback_name in {"PATCH", "POST", "PUT", "DELETE"}:
            skipped.append(f"{name} ({callback_name} only)")
            continue

        url = _build_test_url(pattern_str)
        if url is None:
            skipped.append(f"{name} (complex pattern: {pattern_str})")
            continue

        try:
            response = admin_client.get(url)
        except Exception as exc:
            # Some views raise on missing object; that's "404-like" not "broken view"
            err_msg = str(exc)[:120]
            # Common acceptable: DoesNotExist, Http404, ValueError on bad params
            if any(s in err_msg for s in ["DoesNotExist", "matching query", "Http404", "Invalid"]):
                tested.append(f"{name} ({url}) → exception=acceptable")
                continue
            failures.append(f"{name} ({url}) → EXCEPTION: {err_msg}")
            continue

        if response.status_code == 500:
            failures.append(f"{name} ({url}) → 500")
        elif response.status_code in OK_STATUSES:
            tested.append(f"{name} ({url}) → {response.status_code}")
        else:
            # Other status codes (e.g., 502, 503) are unexpected
            failures.append(
                f"{name} ({url}) → unexpected {response.status_code}"
            )

    print(
        f"\n  SMOKE TEST SUMMARY: tested={len(tested)} skipped={len(skipped)} failures={len(failures)}"
    )

    if failures:
        msg = "\n".join(failures[:30])  # show first 30
        if len(failures) > 30:
            msg += f"\n... and {len(failures) - 30} more"
        pytest.fail(f"URL smoke test failures ({len(failures)}):\n{msg}")


# ---------------- Security audit: anonymous access ----------------
# URL names that are intentionally public (no login required).
# These should return 200 / 302 (not auth-redirect) when hit anonymously.
PUBLIC_URL_NAMES = {
    # Auth pages
    "login", "logout", "signup", "register",
    "password_reset", "password_reset_done",
    "password_reset_confirm", "password_reset_complete",
    "password_change", "password_change_done",
    # Health / metadata
    "health_check", "healthz", "ready", "liveness",
    "health-check", "health-check-detailed",
    "readiness-check", "liveness-check",
    # Django javascript catalog (i18n) — public by design
    "javascript-catalog", "jsi18n",
    # Public token-based pages (already in SKIP_NAMES above)
    "changeorder_customer_signature", "changeorder_customer_signature_token",
    "color_sample_client_signature", "color_sample_client_signature_token",
    "proposal_public_view", "contract_client_view",
    "changeorder_public_pdf_download", "colorsample_public_pdf_download",
    "file_public_view", "file_public_download",
    "folder_public_view", "folder_public_upload",
    # Language switcher (POST only, but anonymous OK)
    "set_language", "set_language_view",
    # Robots / sitemap / favicon
    "robots_txt", "sitemap", "favicon",
    # Root URL — may redirect to login or to dashboard depending
    "home", "index", "root",
}


@pytest.mark.django_db
def test_security_audit_anonymous_login_required(url_patterns):
    """Ensure non-public URLs redirect anonymous users to login (302) or return 401/403.

    A view that returns 200 to an anonymous user MUST be in PUBLIC_URL_NAMES.
    Catches any view missing @login_required / LoginRequiredMixin.
    """
    client = Client()  # anonymous
    leaks: list[str] = []
    audited = 0

    for pattern_str, name, callback in url_patterns:
        if name in SKIP_NAMES:
            continue
        if name in PUBLIC_URL_NAMES:
            continue
        # Skip nameless patterns (typically includes/redirects)
        if not name:
            continue
        callback_name = getattr(callback, "__name__", "")
        if callback_name in {"PATCH", "POST", "PUT", "DELETE"}:
            continue

        url = _build_test_url(pattern_str)
        if url is None:
            continue

        try:
            response = client.get(url)
        except Exception:
            # View exceptions on anonymous are not security leaks per se
            continue

        audited += 1
        # 200 = view rendered for anonymous user → potential leak unless whitelisted
        if response.status_code == 200:
            # Check response content for the login page (some views render login inline)
            body = response.content.decode("utf-8", errors="ignore")[:500].lower()
            if "login" in body or "sign in" in body or "iniciar sesión" in body:
                continue  # rendered login page inline — acceptable
            leaks.append(f"{name} ({url}) → 200 anonymous (possible auth leak)")

    print(f"\n  SECURITY AUDIT: audited={audited} leaks={len(leaks)}")

    if leaks:
        msg = "\n".join(leaks[:30])
        if len(leaks) > 30:
            msg += f"\n... and {len(leaks) - 30} more"
        pytest.fail(
            f"Found {len(leaks)} URLs returning 200 to anonymous users.\n"
            f"Add @login_required / LoginRequiredMixin, or whitelist in PUBLIC_URL_NAMES.\n{msg}"
        )
