"""
Digital Signature Utilities
Gap A Resolution: Cryptographic signature verification for legal compliance
"""

import hashlib
import json
from typing import Any, Dict, Optional

from django.db.models import Model

from signatures.models import Signature as DigitalSignature


def create_signature(
    entity: Model,
    signer,
    ip_address: Optional[str] = None,
    signature_canvas_data: Optional[str] = None,
    user_agent: Optional[str] = None,
    geolocation: Optional[Dict[str, float]] = None,
) -> DigitalSignature:
    """
    Generic signature creation for any signable entity.

    Args:
        entity: Django model instance (must have get_signature_snapshot method)
        signer: User creating the signature
        ip_address: IP address of signer
        signature_canvas_data: Optional JSON vector data from signature pad
        user_agent: Browser user agent string
        geolocation: Optional {'lat': float, 'lng': float}

    Returns:
        DigitalSignature instance

    Raises:
        AttributeError: If entity doesn't have get_signature_snapshot method
    """
    from signatures.models import Signature as BaseSignature

    if not hasattr(entity, "get_signature_snapshot"):
        raise AttributeError(
            f"{entity.__class__.__name__} must implement get_signature_snapshot() method"
        )

    # Get entity type from model name and map to choices
    class_name = entity.__class__.__name__
    entity_type_map = {
        "ColorSample": "color_sample",
        "ChangeOrder": "change_order",
    }
    entity_type = entity_type_map.get(class_name, "change_order")

    # Generate snapshot
    snapshot = entity.get_signature_snapshot()

    # Compute hash from snapshot (static function)
    snapshot_str = json.dumps(snapshot, sort_keys=True)
    content_hash = hashlib.sha256(snapshot_str.encode()).hexdigest()

    # Create base signature
    base_sig = BaseSignature.objects.create(
        signer=signer,
        title=f"{entity.__class__.__name__} #{entity.id}",
        hash_alg="sha256",
        content_hash=content_hash,
        note=f"Digital signature for {entity}",
    )

    # Create enhanced signature
    digital_sig = DigitalSignature.objects.create(
        base_signature=base_sig,
        entity_type=entity_type,
        entity_id=entity.id,
        signer=signer,
        ip_address=ip_address,
        signature_data=signature_canvas_data or "",
        document_snapshot=snapshot,
        signed_hash=content_hash,
        user_agent=user_agent or "",
        geolocation=geolocation,
    )

    return digital_sig


def verify_signature(entity: Model) -> tuple:
    """
    Verify the integrity of a signed entity.

    Compares current document state with signed snapshot to detect tampering.
    Uses cryptographic hash comparison (SHA256).

    Args:
        entity: Model instance (ColorSample, ChangeOrder, etc.)

    Returns:
        Tuple: (is_valid: bool, message: str)

    Raises:
        AttributeError: If entity doesn't have digital_signature or get_signature_snapshot
    """
    if not hasattr(entity, "digital_signature"):
        return False, "Entity not signable"

    if not entity.digital_signature:
        return False, "No digital signature found"

    if not hasattr(entity, "get_signature_snapshot"):
        return False, "Entity missing get_signature_snapshot method"

    # Use the model's verify_integrity method
    return entity.digital_signature.verify_integrity()


def bulk_verify_signatures(queryset) -> dict[str, Any]:
    """
    Verify signatures for multiple entities at once.

    Args:
        queryset: Django QuerySet of entities with digital_signature relationship

    Returns:
        {
            'total': int,
            'valid': int,
            'invalid': int,
            'unsigned': int,
            'details': [
                {'id': int, 'valid': bool, 'changed_fields': list},
                ...
            ]
        }
    """
    results = {"total": queryset.count(), "valid": 0, "invalid": 0, "unsigned": 0, "details": []}

    for entity in queryset:
        if not hasattr(entity, "digital_signature") or not entity.digital_signature:
            results["unsigned"] += 1
            results["details"].append({"id": entity.id, "is_valid": False, "message": "unsigned"})
            continue

        is_valid, message = verify_signature(entity)

        if is_valid:
            results["valid"] += 1
        else:
            results["invalid"] += 1

        results["details"].append(
            {
                "id": entity.id,
                "is_valid": is_valid,
                "message": message,
                "signed_at": str(entity.digital_signature.timestamp),
                "signer": entity.digital_signature.signer.username,
            }
        )

    return results


def export_signature_proof(entity: Model, format: str = "json") -> dict[str, Any]:
    """
    Export signature proof for legal documentation.

    Args:
        entity: Signed entity
        format: 'json' or 'pdf' (future)

    Returns:
        {
            'entity_type': str,
            'entity_id': int,
            'signed_hash': str,
            'document_snapshot': dict,
            'signer': str,
            'timestamp': str,
            'ip_address': str,
            'verification': dict,
            'legal_notice': str
        }
    """
    if not hasattr(entity, "digital_signature") or not entity.digital_signature:
        # Return error in JSON format rather than raising exception
        return json.dumps(
            {
                "error": "No digital signature found",
                "entity_type": entity.__class__.__name__,
                "entity_id": entity.id,
            }
        )

    sig = entity.digital_signature
    is_valid, message = verify_signature(entity)

    from django.utils import timezone

    proof = {
        "entity_type": sig.entity_type,
        "entity_id": sig.entity_id,
        "signed_hash": sig.signed_hash,
        "document_snapshot": sig.document_snapshot,
        "signer": sig.signer.username,
        "timestamp": sig.timestamp.isoformat(),
        "ip_address": sig.ip_address,
        "verification_status": {
            "is_valid": is_valid,
            "message": message,
            "verified_at": str(sig.verified_at) if sig.verified_at else None,
            "verification_count": sig.verification_count,
        },
        "legal_notice": (
            "This document was digitally signed using SHA256 cryptographic hashing. "
            "Any modification to the document after signing will be detected during verification."
        ),
        "export_timestamp": timezone.now().isoformat(),
    }

    if format == "json":
        return json.dumps(proof, indent=2)

    # Future: PDF export
    return proof

    return proof
