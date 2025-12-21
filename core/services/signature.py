"""Utility helpers for customer-facing Change Order signature tokens.

Provides generation and validation of signed tokens using Django's
signing framework (HMAC + SECRET_KEY) with an expiration window.

These tokens allow secure, anonymous access to the public signature
form without exposing internal IDs or requiring authentication.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from django.core import signing
from django.utils import timezone

# Default expiration (days)
DEFAULT_EXPIRATION_DAYS = 7


@dataclass(frozen=True)
class SignatureTokenPayload:
    co: int  # ChangeOrder ID
    ts: float  # Unix timestamp of issuance

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SignatureTokenPayload:
        return cls(co=int(data["co"]), ts=float(data["ts"]))

    def to_dict(self) -> dict[str, Any]:
        return {"co": self.co, "ts": self.ts}


def generate_signature_token(
    changeorder_id: int, expires_in_days: int = DEFAULT_EXPIRATION_DAYS
) -> str:
    """Generate a signed token for a ChangeOrder signature link.

    The token embeds the ChangeOrder ID and issuance timestamp. Expiration
    is enforced at validation time using max_age.
    """
    payload = SignatureTokenPayload(co=changeorder_id, ts=timezone.now().timestamp())
    return signing.dumps(payload.to_dict())


def validate_signature_token(
    token: str, max_age_days: int = DEFAULT_EXPIRATION_DAYS
) -> SignatureTokenPayload:
    """Validate token integrity and expiration.

    Raises signing.BadSignature or signing.SignatureExpired on failure.
    Returns a structured payload object on success.
    """
    raw = signing.loads(token, max_age=max_age_days * 24 * 60 * 60)
    return SignatureTokenPayload.from_dict(raw)


__all__ = [
    "generate_signature_token",
    "validate_signature_token",
    "SignatureTokenPayload",
]
