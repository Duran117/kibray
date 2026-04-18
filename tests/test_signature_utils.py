"""Tests for core.signature_utils — covers create/verify/bulk/export paths."""
from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest


# ---------- verify_signature ----------

def test_verify_signature_no_attribute():
    """Entity without digital_signature attribute → 'Entity not signable'."""
    from core.signature_utils import verify_signature

    entity = object()  # no attrs
    is_valid, msg = verify_signature(entity)
    assert is_valid is False
    assert msg == "Entity not signable"


def test_verify_signature_no_signature():
    """Entity with digital_signature=None → 'No digital signature found'."""
    from core.signature_utils import verify_signature

    entity = MagicMock()
    entity.digital_signature = None
    # MagicMock has every attribute, so explicitly remove it for the first check:
    # we want hasattr(entity, 'digital_signature') == True but value is None.
    is_valid, msg = verify_signature(entity)
    assert is_valid is False
    assert msg == "No digital signature found"


def test_verify_signature_missing_snapshot_method():
    """Entity with signature but no get_signature_snapshot → returns False."""
    from core.signature_utils import verify_signature

    entity = MagicMock(spec=["digital_signature"])
    entity.digital_signature = MagicMock()  # truthy
    is_valid, msg = verify_signature(entity)
    assert is_valid is False
    assert "get_signature_snapshot" in msg


def test_verify_signature_delegates_to_model():
    """When all preconditions met, delegates to digital_signature.verify_integrity()."""
    from core.signature_utils import verify_signature

    entity = MagicMock()
    entity.digital_signature.verify_integrity.return_value = (True, "ok")
    # Make hasattr(entity, 'get_signature_snapshot') truthy
    entity.get_signature_snapshot = lambda: {}
    result = verify_signature(entity)
    assert result == (True, "ok")
    entity.digital_signature.verify_integrity.assert_called_once()


# ---------- bulk_verify_signatures ----------

def test_bulk_verify_signatures_all_unsigned():
    """Queryset of unsigned entities → all in 'unsigned' bucket."""
    from core.signature_utils import bulk_verify_signatures

    e1 = MagicMock(spec=["id", "digital_signature"])
    e1.id = 1
    e1.digital_signature = None
    e2 = MagicMock(spec=["id", "digital_signature"])
    e2.id = 2
    e2.digital_signature = None

    qs = MagicMock()
    qs.count.return_value = 2
    qs.__iter__ = lambda self: iter([e1, e2])

    result = bulk_verify_signatures(qs)
    assert result["total"] == 2
    assert result["unsigned"] == 2
    assert result["valid"] == 0
    assert result["invalid"] == 0
    assert len(result["details"]) == 2


# ---------- export_signature_proof ----------

def test_export_signature_proof_unsigned_returns_error_json():
    """Unsigned entity → JSON string with error key."""
    from core.signature_utils import export_signature_proof

    entity = MagicMock(spec=["id", "digital_signature", "__class__"])
    entity.id = 42
    entity.digital_signature = None
    out = export_signature_proof(entity)
    parsed = json.loads(out)
    assert parsed["error"] == "No digital signature found"
    assert parsed["entity_id"] == 42
