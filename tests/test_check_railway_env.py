"""
Phase E3 — tests for scripts/check_railway_env.py

Validates the env-validation helper used in the deployment checklist. Pure
stdlib; no Django involvement.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = ROOT / "scripts" / "check_railway_env.py"


@pytest.fixture(scope="module")
def module():
    spec = importlib.util.spec_from_file_location("check_railway_env", SCRIPT_PATH)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    # Required so @dataclass can find the module via sys.modules.
    sys.modules["check_railway_env"] = mod
    spec.loader.exec_module(mod)
    return mod


# A baseline env that satisfies every required var so individual tests can
# poke holes in it.
GOOD_ENV: dict[str, str] = {
    "DJANGO_SETTINGS_MODULE": "kibray_backend.settings.production",
    "DJANGO_SECRET_KEY": "x" * 50,
    "DEBUG": "False",
    "ALLOWED_HOSTS": "kibray.com,www.kibray.com",
    "DATABASE_URL": "postgres://u:p@host:5432/db",
    "CORS_ALLOWED_ORIGINS": "https://kibray.com",
    "CSRF_TRUSTED_ORIGINS": "https://kibray.com",
    "EMAIL_HOST": "smtp.example.com",
    "EMAIL_HOST_USER": "noreply@example.com",
    "EMAIL_HOST_PASSWORD": "supersecret",
}


def test_clean_env_passes(module):
    result = module.run_checks(env=dict(GOOD_ENV))
    assert result.errors == [], result.errors
    assert not result.missing_required


def test_missing_required_is_error(module):
    env = dict(GOOD_ENV)
    env.pop("DJANGO_SECRET_KEY")
    result = module.run_checks(env=env)
    assert "DJANGO_SECRET_KEY" in result.missing_required
    assert any("DJANGO_SECRET_KEY" in e for e in result.errors)


def test_short_secret_key_is_error(module):
    env = dict(GOOD_ENV, DJANGO_SECRET_KEY="too_short")
    result = module.run_checks(env=env)
    assert any("DJANGO_SECRET_KEY" in e and "length" in e for e in result.errors)


def test_debug_true_is_warning_not_error(module):
    env = dict(GOOD_ENV, DEBUG="True")
    result = module.run_checks(env=env)
    # DEBUG is optional so the validator hit becomes a warning, not an error.
    assert any("DEBUG" in w for w in result.warnings)
    assert not any("DEBUG" in e for e in result.errors)


def test_use_s3_requires_aws_trio(module):
    env = dict(GOOD_ENV, USE_S3="True")  # AWS_* deliberately absent
    result = module.run_checks(env=env)
    msgs = " | ".join(result.errors)
    assert "AWS_ACCESS_KEY_ID" in msgs
    assert "AWS_SECRET_ACCESS_KEY" in msgs
    assert "AWS_STORAGE_BUCKET_NAME" in msgs


def test_use_s3_with_full_aws_passes(module):
    env = dict(
        GOOD_ENV,
        USE_S3="True",
        AWS_ACCESS_KEY_ID="AKIA....",
        AWS_SECRET_ACCESS_KEY="secret",
        AWS_STORAGE_BUCKET_NAME="kibray-prod",
    )
    result = module.run_checks(env=env)
    # Should still pass (no S3-related errors)
    assert not any("AWS_" in e for e in result.errors)


def test_dev_settings_module_flagged(module):
    env = dict(GOOD_ENV, DJANGO_SETTINGS_MODULE="kibray_backend.settings.development")
    result = module.run_checks(env=env)
    assert any("does not look like a prod/staging module" in e for e in result.errors)


def test_bad_database_url_is_error(module):
    env = dict(GOOD_ENV, DATABASE_URL="not-a-url")
    result = module.run_checks(env=env)
    assert any("DATABASE_URL" in e for e in result.errors)


def test_empty_allowed_hosts_is_error(module):
    env = dict(GOOD_ENV, ALLOWED_HOSTS=" , ,")
    result = module.run_checks(env=env)
    assert any("ALLOWED_HOSTS" in e for e in result.errors)


def test_sensitive_values_are_redacted(module):
    env = dict(GOOD_ENV, DJANGO_SECRET_KEY="abcdefghij" * 5)
    result = module.run_checks(env=env)
    presented = result.present["DJANGO_SECRET_KEY"]
    assert "abcdefghij" not in presented
    assert "len=" in presented


def test_human_render_contains_summary(module):
    result = module.run_checks(env=dict(GOOD_ENV))
    out = module.render_human(result)
    assert "Variables present" in out
    assert "Environment looks healthy" in out


def test_json_serialisation_round_trip(module):
    result = module.run_checks(env=dict(GOOD_ENV))
    payload = json.dumps(result.to_dict())
    parsed = json.loads(payload)
    assert "present" in parsed and "errors" in parsed
    assert parsed["missing_required"] == []


def test_main_returns_zero_on_clean_env(module, monkeypatch, capsys):
    for key in list(module.os.environ):
        monkeypatch.delenv(key, raising=False)
    for k, v in GOOD_ENV.items():
        monkeypatch.setenv(k, v)
    rc = module.main([])
    captured = capsys.readouterr()
    assert rc == 0
    assert "healthy" in captured.out


def test_main_returns_one_on_missing_required(module, monkeypatch, capsys):
    for key in list(module.os.environ):
        monkeypatch.delenv(key, raising=False)
    env = dict(GOOD_ENV)
    env.pop("DATABASE_URL")
    for k, v in env.items():
        monkeypatch.setenv(k, v)
    rc = module.main([])
    assert rc == 1


def test_main_strict_promotes_warning_to_failure(module, monkeypatch, capsys):
    for key in list(module.os.environ):
        monkeypatch.delenv(key, raising=False)
    env = dict(GOOD_ENV, DEBUG="True")
    for k, v in env.items():
        monkeypatch.setenv(k, v)
    rc_default = module.main([])
    assert rc_default == 2  # warnings only
    rc_strict = module.main(["--strict"])
    assert rc_strict == 1


def test_main_json_output(module, monkeypatch, capsys):
    for key in list(module.os.environ):
        monkeypatch.delenv(key, raising=False)
    for k, v in GOOD_ENV.items():
        monkeypatch.setenv(k, v)
    module.main(["--json"])
    out = capsys.readouterr().out
    parsed = json.loads(out)
    assert parsed["missing_required"] == []
    assert parsed["present_count"] >= len(GOOD_ENV)
