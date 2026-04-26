"""
Report generator adapters — Phase C / Reports.

Wraps the existing synchronous PDF generators in `pdf_service` so they can
be invoked through the async report registry by name + JSON-serialisable
kwargs (typically just an object id).

Why adapters?
  * The original `generate_*_pdf_reportlab` functions take ORM instances,
    which can't be pickled into a Celery task body. Adapters take an `id`
    and load the object inside the worker.
  * Adapters can also enforce module-specific defaults (e.g. always pass
    `as_contract=True` when rendering a contract from an Estimate).
  * Centralises the "which permission can run which report" mapping in
    one file that's trivial to grep.

This module auto-registers when imported. The Celery task imports it
lazily so test isolation still works (callers can `unregister` in
fixtures).
"""

from __future__ import annotations

import logging
from typing import Any

from core.services.report_registry import StaffOrDesignRoles, StaffRoles, register

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Adapter helpers
# ---------------------------------------------------------------------------


def _load(model_label: str, pk: int) -> Any:
    """
    Resolve "app.Model" + pk to an instance, raising a clear error if
    missing. Imported lazily to keep this module import-cheap.
    """
    from django.apps import apps

    app_label, model_name = model_label.split(".")
    model = apps.get_model(app_label, model_name)
    if model is None:
        raise LookupError(f"Model {model_label!r} not found")
    try:
        return model.objects.get(pk=pk)
    except model.DoesNotExist as exc:
        raise LookupError(f"{model_label}(pk={pk}) does not exist") from exc


# ---------------------------------------------------------------------------
# Adapters (each must take **kwargs and return bytes)
# ---------------------------------------------------------------------------


def _estimate_adapter(*, estimate_id: int, as_contract: bool = False, **_: Any) -> bytes:
    from core.services.pdf_service import generate_estimate_pdf_reportlab

    estimate = _load("core.Estimate", estimate_id)
    return generate_estimate_pdf_reportlab(estimate, as_contract=as_contract)


def _contract_adapter(*, contract_id: int, **_: Any) -> bytes:
    from core.services.pdf_service import generate_contract_pdf_reportlab

    contract = _load("core.Contract", contract_id)
    return generate_contract_pdf_reportlab(contract)


def _signed_contract_adapter(*, contract_id: int, **_: Any) -> bytes:
    from core.services.pdf_service import generate_signed_contract_pdf_reportlab

    contract = _load("core.Contract", contract_id)
    return generate_signed_contract_pdf_reportlab(contract)


def _changeorder_adapter(*, changeorder_id: int, **_: Any) -> bytes:
    from core.services.pdf_service import generate_changeorder_pdf_reportlab

    changeorder = _load("core.ChangeOrder", changeorder_id)
    return generate_changeorder_pdf_reportlab(changeorder)


def _colorsample_adapter(*, colorsample_id: int, **_: Any) -> bytes:
    from core.services.pdf_service import generate_colorsample_pdf_reportlab

    colorsample = _load("core.ColorSample", colorsample_id)
    return generate_colorsample_pdf_reportlab(colorsample)


# ---------------------------------------------------------------------------
# Auto-registration (idempotent)
# ---------------------------------------------------------------------------


def register_all() -> None:
    """Idempotently register every built-in adapter."""
    register(
        "estimate_pdf",
        generator=_estimate_adapter,
        content_type="application/pdf",
        file_extension="pdf",
        allowed_roles=StaffRoles,
        description="Estimate document for client review.",
    )
    register(
        "contract_pdf",
        generator=_contract_adapter,
        content_type="application/pdf",
        file_extension="pdf",
        allowed_roles=StaffRoles,
        description="Unsigned contract PDF.",
    )
    register(
        "signed_contract_pdf",
        generator=_signed_contract_adapter,
        content_type="application/pdf",
        file_extension="pdf",
        allowed_roles=StaffRoles,
        description="Final signed contract with signature blocks.",
    )
    register(
        "changeorder_pdf",
        generator=_changeorder_adapter,
        content_type="application/pdf",
        file_extension="pdf",
        allowed_roles=StaffRoles,
        description="Change Order document with line items + photos.",
    )
    register(
        "colorsample_pdf",
        generator=_colorsample_adapter,
        content_type="application/pdf",
        file_extension="pdf",
        allowed_roles=StaffOrDesignRoles,
        description="Color Sample approval sheet (for designers + staff).",
    )


# Auto-register at import time. Tests that need a clean slate can use
# `core.services.report_registry.unregister` in fixtures.
register_all()
