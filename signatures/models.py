from __future__ import annotations

from django.conf import settings
from django.db import models


class Signature(models.Model):
    """Represents a user's digital signature on a document or record.

    Keep scope minimal and isolated. Link to user, store a small blob (optional),
    and an integrity hash to verify content.
    """

    signer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="signatures"
    )
    title = models.CharField(max_length=255, help_text="Short label for the signed item")
    signed_at = models.DateTimeField(auto_now_add=True)
    hash_alg = models.CharField(max_length=32, default="sha256")
    content_hash = models.CharField(max_length=128, help_text="Hex digest of signed content")
    note = models.TextField(blank=True)
    file = models.FileField(upload_to="signatures/", blank=True, null=True)

    class Meta:
        ordering = ["-signed_at"]
        indexes = [
            models.Index(fields=["signer", "signed_at"]),
        ]

    def __str__(self) -> str:  # pragma: no cover - trivial
        return f"Signature({self.signer_id}, {self.title})"
