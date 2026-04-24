#!/usr/bin/env python3
"""
check_railway_env.py — Phase E3 deployment helper

Validates that the current shell (or Railway environment) has the variables
that ``kibray_backend.settings.production`` actually reads. Designed to be run:

  • Locally before ``git push origin main`` (catches missing vars early).
  • On the Railway shell (``railway run python check_railway_env.py``).
  • From CI as a smoke step.

Exit codes:
  0  — all required vars present, no warnings
  1  — at least one REQUIRED var missing
  2  — REQUIRED vars present but warnings raised (use ``--strict`` to also fail)

Usage:
  python check_railway_env.py            # human-readable report
  python check_railway_env.py --json     # machine-readable
  python check_railway_env.py --strict   # treat warnings as errors

This script has no third-party dependencies and only stdlib imports, so it can
run on a fresh Railway shell before any pip install completes.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass, field
from typing import Callable, Optional


# --------------------------------------------------------------------------- #
# Variable catalogue — kept in sync with kibray_backend/settings/production.py
# --------------------------------------------------------------------------- #


@dataclass
class EnvVar:
    name: str
    required: bool
    purpose: str
    validator: Optional[Callable[[str], Optional[str]]] = None
    sensitive: bool = False
    group: str = "core"


def _non_empty(value: str) -> Optional[str]:
    return None if value.strip() else "value is empty"


def _is_false_string(value: str) -> Optional[str]:
    if value.strip().lower() in {"false", "0", "no", "off"}:
        return None
    return f"expected False-ish in production, got '{value}'"


def _looks_like_url(value: str) -> Optional[str]:
    if value.startswith(("http://", "https://", "postgres://", "postgresql://", "redis://")):
        return None
    return f"does not look like a URL ('{value[:30]}…')"


def _comma_list_non_empty(value: str) -> Optional[str]:
    parts = [p.strip() for p in value.split(",") if p.strip()]
    return None if parts else "comma list parses to zero entries"


def _min_length(min_len: int) -> Callable[[str], Optional[str]]:
    def _v(value: str) -> Optional[str]:
        if len(value) < min_len:
            return f"length {len(value)} < required {min_len}"
        return None

    return _v


CATALOGUE: list[EnvVar] = [
    # --- Core Django ---
    EnvVar("DJANGO_SETTINGS_MODULE", True, "Django settings module", _non_empty, group="core"),
    EnvVar(
        "DJANGO_SECRET_KEY",
        True,
        "Django SECRET_KEY (cryptographic signing)",
        _min_length(32),
        sensitive=True,
        group="core",
    ),
    EnvVar("DEBUG", False, "Should be False or unset in production", _is_false_string, group="core"),
    EnvVar(
        "ALLOWED_HOSTS",
        True,
        "Comma-separated host whitelist",
        _comma_list_non_empty,
        group="core",
    ),
    # --- Database ---
    EnvVar(
        "DATABASE_URL",
        True,
        "PostgreSQL DSN (Railway provides automatically)",
        _looks_like_url,
        sensitive=True,
        group="db",
    ),
    # --- Cache / Celery broker ---
    EnvVar(
        "REDIS_URL",
        False,
        "Redis URL for cache + Celery broker",
        _looks_like_url,
        sensitive=True,
        group="cache",
    ),
    EnvVar(
        "CELERY_TASK_ALWAYS_EAGER",
        False,
        "Force eager Celery tasks (must be False in prod)",
        _is_false_string,
        group="cache",
    ),
    # --- CORS / CSRF ---
    EnvVar(
        "CORS_ALLOWED_ORIGINS",
        True,
        "Comma-separated CORS origins (frontend hosts)",
        _comma_list_non_empty,
        group="security",
    ),
    EnvVar(
        "CSRF_TRUSTED_ORIGINS",
        True,
        "Comma-separated CSRF trusted origins",
        _comma_list_non_empty,
        group="security",
    ),
    # --- Email ---
    EnvVar("EMAIL_HOST", True, "SMTP server hostname", _non_empty, group="email"),
    EnvVar("EMAIL_PORT", False, "SMTP port (default 587)", group="email"),
    EnvVar("EMAIL_HOST_USER", True, "SMTP username", _non_empty, sensitive=True, group="email"),
    EnvVar(
        "EMAIL_HOST_PASSWORD",
        True,
        "SMTP password / app token",
        _non_empty,
        sensitive=True,
        group="email",
    ),
    EnvVar("DEFAULT_FROM_EMAIL", False, "Default sender address", group="email"),
    # --- Storage (optional, only if USE_S3=True) ---
    EnvVar(
        "USE_S3",
        False,
        "Toggle S3 storage (defaults to False on Railway)",
        group="storage",
    ),
    EnvVar(
        "AWS_ACCESS_KEY_ID",
        False,
        "Required only when USE_S3=True",
        sensitive=True,
        group="storage",
    ),
    EnvVar(
        "AWS_SECRET_ACCESS_KEY",
        False,
        "Required only when USE_S3=True",
        sensitive=True,
        group="storage",
    ),
    EnvVar(
        "AWS_STORAGE_BUCKET_NAME",
        False,
        "Required only when USE_S3=True",
        group="storage",
    ),
    EnvVar("AWS_S3_REGION_NAME", False, "Defaults to us-east-1", group="storage"),
    # --- Observability ---
    EnvVar(
        "SENTRY_DSN",
        False,
        "Sentry DSN (recommended for production)",
        _looks_like_url,
        sensitive=True,
        group="observability",
    ),
    EnvVar(
        "SENTRY_ENVIRONMENT",
        False,
        "Sentry environment label (defaults to 'production')",
        group="observability",
    ),
    # --- Misc ---
    EnvVar("API_BASE_URL", False, "Public API base URL for OpenAPI schema", group="misc"),
]


# --------------------------------------------------------------------------- #
# Conditional rules
# --------------------------------------------------------------------------- #


def _conditional_rules(env: dict[str, str]) -> list[str]:
    """Cross-variable rules that can't be expressed in the catalogue alone."""
    errors: list[str] = []

    # If USE_S3 is True, the AWS_* trio becomes mandatory.
    if env.get("USE_S3", "False").strip().lower() in {"true", "1", "yes", "on"}:
        for needed in ("AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_STORAGE_BUCKET_NAME"):
            if not env.get(needed, "").strip():
                errors.append(f"USE_S3=True but {needed} is missing")

    # DJANGO_SETTINGS_MODULE should resolve to a production-ish module.
    dsm = env.get("DJANGO_SETTINGS_MODULE", "")
    if dsm and "production" not in dsm and "staging" not in dsm:
        errors.append(
            f"DJANGO_SETTINGS_MODULE='{dsm}' does not look like a prod/staging module"
        )

    return errors


# --------------------------------------------------------------------------- #
# Report
# --------------------------------------------------------------------------- #


@dataclass
class CheckResult:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    present: dict[str, str] = field(default_factory=dict)  # name -> redacted value
    missing_required: list[str] = field(default_factory=list)
    missing_optional: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "errors": self.errors,
            "warnings": self.warnings,
            "missing_required": self.missing_required,
            "missing_optional": self.missing_optional,
            "present_count": len(self.present),
            "present": self.present,
        }


def _redact(name: str, value: str, sensitive: bool) -> str:
    if not sensitive:
        return value if len(value) <= 60 else value[:57] + "…"
    if len(value) <= 8:
        return "***"
    return f"{value[:4]}…{value[-2:]} (len={len(value)})"


def run_checks(env: Optional[dict[str, str]] = None) -> CheckResult:
    env = env if env is not None else dict(os.environ)
    result = CheckResult()

    for var in CATALOGUE:
        raw = env.get(var.name)
        if raw is None or raw == "":
            if var.required:
                result.missing_required.append(var.name)
                result.errors.append(f"MISSING REQUIRED: {var.name} — {var.purpose}")
            else:
                result.missing_optional.append(var.name)
            continue

        result.present[var.name] = _redact(var.name, raw, var.sensitive)

        if var.validator is not None:
            problem = var.validator(raw)
            if problem is not None:
                msg = f"{var.name}: {problem}"
                if var.required:
                    result.errors.append(msg)
                else:
                    result.warnings.append(msg)

    for msg in _conditional_rules(env):
        result.errors.append(msg)

    return result


def render_human(result: CheckResult) -> str:
    lines: list[str] = []
    lines.append("=" * 72)
    lines.append("Kibray — Railway / production environment validation")
    lines.append("=" * 72)
    lines.append("")
    lines.append(f"Variables present : {len(result.present)}")
    lines.append(f"Missing required  : {len(result.missing_required)}")
    lines.append(f"Missing optional  : {len(result.missing_optional)}")
    lines.append(f"Errors            : {len(result.errors)}")
    lines.append(f"Warnings          : {len(result.warnings)}")
    lines.append("")

    if result.present:
        lines.append("✓ Present (values redacted for sensitive vars):")
        for name in sorted(result.present):
            lines.append(f"    {name} = {result.present[name]}")
        lines.append("")

    if result.missing_required:
        lines.append("✗ MISSING REQUIRED:")
        for name in result.missing_required:
            purpose = next((v.purpose for v in CATALOGUE if v.name == name), "")
            lines.append(f"    {name}  — {purpose}")
        lines.append("")

    if result.missing_optional:
        lines.append("· Missing optional (OK to skip if you're not using the feature):")
        for name in result.missing_optional:
            purpose = next((v.purpose for v in CATALOGUE if v.name == name), "")
            lines.append(f"    {name}  — {purpose}")
        lines.append("")

    if result.errors:
        lines.append("ERRORS:")
        for e in result.errors:
            lines.append(f"  ✗ {e}")
        lines.append("")

    if result.warnings:
        lines.append("WARNINGS:")
        for w in result.warnings:
            lines.append(f"  ! {w}")
        lines.append("")

    if not result.errors and not result.warnings:
        lines.append("✅ Environment looks healthy for production deploy.")
    elif not result.errors:
        lines.append("⚠️  No blocking errors, but warnings should be reviewed.")
    else:
        lines.append("❌ Blocking errors detected — DO NOT deploy until fixed.")

    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate Kibray production environment variables."
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text.")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings as failures (exit 2 → 1).",
    )
    args = parser.parse_args(argv)

    result = run_checks()

    if args.json:
        print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    else:
        print(render_human(result))

    if result.errors:
        return 1
    if result.warnings and args.strict:
        return 1
    if result.warnings:
        return 2
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
