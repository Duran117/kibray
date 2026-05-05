"""
core/api/serializer_classes/access_fields.py — DRF fields that scope
their queryset per request.user via core.access.

Usage:
    from .access_fields import AccessibleProjectField

    class TaskCreateUpdateSerializer(serializers.ModelSerializer):
        project = AccessibleProjectField()
        ...

Phase 9 fix (G3 — write side): legacy serializers used
``serializers.PrimaryKeyRelatedField(queryset=Project.objects.all())``,
which validated incoming project_id against EVERY project in the system,
not just the ones the user can access. A malicious or curious client
could POST a Task / ChangeOrder / ScheduleItemV2 attaching it to ANY
project's id and have DRF accept it.
"""
from __future__ import annotations

from rest_framework import serializers

from core.models import Project


class AccessibleProjectField(serializers.PrimaryKeyRelatedField):
    """PrimaryKeyRelatedField that limits choices to the request user's
    accessible projects.

    Falls back to Project.objects.none() if no request is present in the
    serializer context, or if the user is anonymous. This is fail-closed
    by design — any DRF call without proper context will reject all
    project ids rather than allow any.
    """

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("queryset", Project.objects.none())
        super().__init__(*args, **kwargs)

    def get_queryset(self):
        from core.access import accessible_projects

        request = self.context.get("request") if self.context else None
        user = getattr(request, "user", None) if request else None
        if user is None or not getattr(user, "is_authenticated", False):
            return Project.objects.none()
        return accessible_projects(user)


__all__ = ["AccessibleProjectField"]
