
from django.db import transaction
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import Employee, Task

STATUS_CHOICES = {"Pendiente", "En Progreso", "En Revisión", "Completada", "Cancelada"}
PRIORITY_CHOICES = {"low", "medium", "high", "urgent"}
# Accept alias used in template prompt
PRIORITY_ALIASES = {"normal": "medium"}

class BulkTaskUpdateAPIView(APIView):
    """Bulk update Tasks (assign/status/priority).

    Expected JSON payload:
    {
        "task_ids": [1,2,3],
        "action": "assign" | "status" | "priority",
        "value": "15"  # employee id OR status string OR priority string
    }

    Notes:
    - Iterates and saves each task individually so model signals/status history run.
    - Returns list of updated task IDs and failures with reasons.
    - Supports 'normal' priority alias mapping to 'medium'.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.data or {}
        task_ids: list[int] = data.get("task_ids", [])
        action: str = data.get("action", "").strip()
        value = data.get("value")

        if not isinstance(task_ids, list) or len(task_ids) == 0:
            return Response({"error": "task_ids must be a non-empty list"}, status=status.HTTP_400_BAD_REQUEST)
        if action not in {"assign", "status", "priority"}:
            return Response({"error": "Invalid action"}, status=status.HTTP_400_BAD_REQUEST)
        if value in (None, ""):
            return Response({"error": "value is required"}, status=status.HTTP_400_BAD_REQUEST)

        tasks = Task.objects.filter(id__in=task_ids)
        found_ids = set(tasks.values_list("id", flat=True))
        missing = [tid for tid in task_ids if tid not in found_ids]

        updated: list[int] = []
        failed: list[dict[str, str]] = []

        # Pre-fetch employee if needed
        employee_obj = None
        if action == "assign":
            try:
                employee_obj = Employee.objects.get(pk=value)
            except Exception:
                failed.append({"value": str(value), "reason": "Employee not found"})
                return Response({"updated": [], "failed": failed, "missing": missing, "action": action}, status=status.HTTP_400_BAD_REQUEST)

        if action == "status" and value not in STATUS_CHOICES:
            return Response({"error": f"Invalid status '{value}'"}, status=status.HTTP_400_BAD_REQUEST)

        if action == "priority":
            mapped = PRIORITY_ALIASES.get(str(value).lower(), str(value).lower())
            if mapped not in PRIORITY_CHOICES:
                return Response({"error": f"Invalid priority '{value}'"}, status=status.HTTP_400_BAD_REQUEST)
            value = mapped

        # Iterate & apply
        for task in tasks.select_related("assigned_to"):
            try:
                with transaction.atomic():
                    if action == "assign":
                        task.assigned_to = employee_obj
                    elif action == "status":
                        task.status = value
                    elif action == "priority":
                        task.priority = value
                    task.save()  # triggers model validation & signals
                    updated.append(task.id)
            except Exception as e:
                failed.append({"task_id": task.id, "reason": str(e)})

        return Response(
            {
                "action": action,
                "value": value,
                "updated_count": len(updated),
                "updated": updated,
                "failed": failed,
                "missing": missing,
            },
            status=status.HTTP_200_OK,
        )
