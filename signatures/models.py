from __future__ import annotations

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models


class Signature(models.Model):
    """Represents a user's digital signature on a document or record.

    Phase D4 — adds an optional GenericForeignKey (``content_type`` +
    ``object_id``) so a signature can attach to *any* model in the project
    (Estimate, Contract, ChangeOrder, ColorSample, MeetingMinute, …) without
    requiring a dedicated FK column per document type.

    Both fields are nullable for backwards compatibility with existing rows
    created before the GFK was introduced.
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

    # ---- Phase D4: GenericForeignKey to any document model ----------------
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="+",
        help_text="ContentType of the document being signed (Phase D4 GFK)",
    )
    object_id = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Primary key of the signed document (Phase D4 GFK)",
    )
    content_object = GenericForeignKey("content_type", "object_id")

    class Meta:
        ordering = ["-signed_at"]
        indexes = [
            models.Index(fields=["signer", "signed_at"]),
            models.Index(fields=["content_type", "object_id"], name="sig_gfk_idx"),
        ]

    def __str__(self) -> str:  # pragma: no cover - trivial
        return f"Signature({self.signer_id}, {self.title})"

