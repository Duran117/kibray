from __future__ import annotations

from django.db import models


class ReportTemplate(models.Model):
    """Simple report template definition for server-side rendering.

    For now we keep it minimal: a name, a slug, and a JSON config blob.
    """

    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=64, unique=True)
    config = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:  # pragma: no cover
        return self.name
