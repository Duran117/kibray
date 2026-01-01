from django.db import transaction
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import Employee, Task, FloorPlan
from core.notifications import notify_task_created

STATUS_CHOICES = {"Pendiente", "En Progreso", "En Revisión", "Completada", "Cancelada"}
PRIORITY_CHOICES = {"low", "medium", "high", "urgent"}
# Accept alias used in template prompt
PRIORITY_ALIASES = {"normal": "medium"}


class TaskDetailAPIView(APIView):
    """Get detailed task information for modal display.
    
    Returns task data including:
    - Basic info (title, description, status, priority, etc.)
    - Assignee information
    - Project information
    - Attached image URL
    - Floor plan pin information (if linked to touch-up board)
    - Time tracking data
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, task_id):
        try:
            task = Task.objects.select_related(
                "project", "assigned_to", "created_by"
            ).prefetch_related("dependencies").get(id=task_id)
        except Task.DoesNotExist:
            return Response({"error": "Task not found"}, status=status.HTTP_404_NOT_FOUND)
        
        # Get floor plan pin if exists (touch-up linked to floor plan)
        floor_plan_pin = None
        try:
            from core.models import PlanPin
            pin = PlanPin.objects.filter(linked_task=task).select_related("floor_plan").first()
            if pin and pin.floor_plan:
                floor_plan_pin = {
                    "id": pin.id,
                    "floor_plan_id": pin.floor_plan.id,
                    "floor_plan_name": pin.floor_plan.name,
                    "floor_plan_image": pin.floor_plan.image.url if pin.floor_plan.image else None,
                    "x_percent": pin.x_percent,
                    "y_percent": pin.y_percent,
                    "label": pin.label,
                }
        except Exception:
            pass
        
        # Build response data
        data = {
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "status": task.status,
            "priority": task.priority,
            "priority_display": task.get_priority_display(),
            "is_touchup": task.is_touchup,
            "project_id": task.project_id,
            "project_name": task.project.name if task.project else None,
            "assigned_to_id": task.assigned_to_id,
            "assigned_to_name": f"{task.assigned_to.first_name} {task.assigned_to.last_name}" if task.assigned_to else None,
            "created_by_name": task.created_by.get_full_name() if task.created_by else None,
            "created_at": task.created_at.isoformat() if task.created_at else None,
            "due_date": task.due_date.isoformat() if task.due_date else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            "image_url": task.image.url if task.image else None,
            "floor_plan_pin": floor_plan_pin,
            "time_tracked_seconds": task.time_tracked_seconds,
            "time_tracked_hours": round(task.time_tracked_seconds / 3600, 2) if task.time_tracked_seconds else 0,
            "dependencies": [
                {"id": dep.id, "title": dep.title, "status": dep.status}
                for dep in task.dependencies.all()
            ],
        }
        
        return Response(data)


class BulkTaskAssignAPIView(APIView):
    """Bulk assign tasks to an employee with notification.
    
    Expected JSON payload:
    {
        "task_ids": [1, 2, 3],
        "employee_id": 15
    }
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        data = request.data or {}
        task_ids = data.get("task_ids", [])
        employee_id = data.get("employee_id")
        
        if not isinstance(task_ids, list) or len(task_ids) == 0:
            return Response(
                {"error": "task_ids must be a non-empty list"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not employee_id:
            return Response(
                {"error": "employee_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            employee = Employee.objects.get(pk=employee_id)
        except Employee.DoesNotExist:
            return Response(
                {"error": "Employee not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        tasks = Task.objects.filter(id__in=task_ids)
        updated = []
        
        for task in tasks:
            old_assignee = task.assigned_to
            task.assigned_to = employee
            task.save()
            updated.append(task.id)
            
            # Send notification if assignee changed
            if old_assignee != employee:
                try:
                    notify_task_created(task, request.user)
                except Exception:
                    pass  # Don't fail bulk operation for notification errors
        
        return Response({
            "success": True,
            "updated_count": len(updated),
            "updated": updated,
            "employee_name": f"{employee.first_name} {employee.last_name}"
        })


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
            return Response(
                {"error": "task_ids must be a non-empty list"}, status=status.HTTP_400_BAD_REQUEST
            )
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
                return Response(
                    {"updated": [], "failed": failed, "missing": missing, "action": action},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        if action == "status" and value not in STATUS_CHOICES:
            return Response(
                {"error": f"Invalid status '{value}'"}, status=status.HTTP_400_BAD_REQUEST
            )

        if action == "priority":
            mapped = PRIORITY_ALIASES.get(str(value).lower(), str(value).lower())
            if mapped not in PRIORITY_CHOICES:
                return Response(
                    {"error": f"Invalid priority '{value}'"}, status=status.HTTP_400_BAD_REQUEST
                )
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
