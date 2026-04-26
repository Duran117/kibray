"""
Report registry — Phase C / Reports foundation.

Provides a tiny pluggable registry so any module can declare an asynchronous
report (PDF/CSV/Excel) without each having to re-implement permission
checks, error handling and Celery wiring.

The actual Celery task lives in `core.tasks.generate_report_async`. This
module only owns:
  - the registry (name -> generator + permission)
  - permission resolution helper
  - lookup helpers used by the task and any management command

Why a registry instead of free-form tasks?
  * Centralises permission enforcement (no chance to forget it)
  * Makes it trivial to list available reports for an admin UI
  * Keeps the async task small and dumb (it just looks up + dispatches)
  * Tested in isolation, no Django request needed
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Iterable

# Permission roles that can run a given report. Mirrors the roles used by
# `core.api.permission_classes.role_permissions` so we stay consistent.
StaffRoles = frozenset({"admin", "project_manager", "general_manager"})
StaffOrDesignRoles = StaffRoles | frozenset({"designer", "superintendent"})
AnyAuthenticated = frozenset({"*"})  # sentinel: any logged-in user


class ReportNotFound(LookupError):
    """Raised when an unknown report name is requested."""


class ReportPermissionDenied(PermissionError):
    """Raised when a user is not allowed to run a registered report."""


@dataclass(frozen=True)
class ReportSpec:
    """Description of one registered report."""

    name: str
    generator: Callable[..., bytes]
    content_type: str
    file_extension: str
    allowed_roles: frozenset[str]
    description: str = ""

    def is_allowed_for(self, role: str | None, *, is_superuser: bool = False, is_staff: bool = False) -> bool:
        if is_superuser or is_staff:
            return True
        if "*" in self.allowed_roles:
            return bool(role)  # any authenticated role
        return role in self.allowed_roles


_REGISTRY: dict[str, ReportSpec] = {}


def register(
    name: str,
    *,
    generator: Callable[..., bytes],
    content_type: str,
    file_extension: str,
    allowed_roles: Iterable[str] = StaffRoles,
    description: str = "",
) -> ReportSpec:
    """Register a new report. Idempotent for the same (name, generator) pair."""
    if not name or not name.strip():
        raise ValueError("Report name is required")
    if not callable(generator):
        raise TypeError("generator must be callable")
    spec = ReportSpec(
        name=name,
        generator=generator,
        content_type=content_type,
        file_extension=file_extension.lstrip("."),
        allowed_roles=frozenset(allowed_roles),
        description=description.strip(),
    )
    existing = _REGISTRY.get(name)
    if existing and existing.generator is not generator:
        raise ValueError(
            f"Report {name!r} already registered with a different generator"
        )
    _REGISTRY[name] = spec
    return spec


def unregister(name: str) -> None:
    """Remove a report — primarily used by tests to clean up."""
    _REGISTRY.pop(name, None)


def get(name: str) -> ReportSpec:
    """Return the spec for `name` or raise ReportNotFound."""
    try:
        return _REGISTRY[name]
    except KeyError as exc:  # noqa: BLE001
        raise ReportNotFound(f"No report registered under {name!r}") from exc


def list_reports() -> list[ReportSpec]:
    """Return all registered reports, sorted by name."""
    return sorted(_REGISTRY.values(), key=lambda s: s.name)


def resolve_user_role(user: Any) -> tuple[str | None, bool, bool]:
    """
    Inspect a Django user and return (role, is_superuser, is_staff).

    Kept here (not in views) so the celery task can run permission checks
    without depending on DRF.
    """
    if user is None:
        return (None, False, False)
    is_superuser = bool(getattr(user, "is_superuser", False))
    is_staff = bool(getattr(user, "is_staff", False))
    profile = getattr(user, "profile", None)
    role = getattr(profile, "role", None) if profile else None
    return (role, is_superuser, is_staff)


def render(name: str, *, user: Any = None, **kwargs: Any) -> bytes:
    """
    Look up the report, enforce permissions, and run the generator.

    Raises:
      - ReportNotFound: unknown name
      - ReportPermissionDenied: user lacks role
      - whatever the generator raises (bubbled up so the task can log it)
    """
    spec = get(name)
    role, is_superuser, is_staff = resolve_user_role(user)
    if not spec.is_allowed_for(role, is_superuser=is_superuser, is_staff=is_staff):
        raise ReportPermissionDenied(
            f"User role {role!r} cannot run report {name!r}"
        )
    return spec.generator(**kwargs)
