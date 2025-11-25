# Module 28: Touch-Ups Board API

Provides a kanban-style API to manage touch-up tasks.

Base: /api/v1/tasks/touchup_board/

Query params:
- project: Project ID (recommended)
- status: Comma-separated or repeated. Values: Pendiente, En Progreso, Completada
- priority: Comma-separated or repeated. Values: low, medium, high, urgent
- assigned_to: Employee ID
- assigned_to_me: true|false (maps current user to their Employee)

Response shape:
{
  "columns": [
    {"key":"Pendiente","title":"Pendiente","count":N,"items":[Task...]},
    {"key":"En Progreso","title":"En Progreso","count":M,"items":[Task...]},
    {"key":"Completada","title":"Completada","count":K,"items":[Task...]}
  ],
  "totals": {"total":T, "pending":N, "in_progress":M, "completed":K}
}

Notes:
- Only Task.is_touchup=True are included.
- Items use TaskSerializer, including assigned_to_name, priority, due_date, etc.
- Completing a touch-up still requires at least one photo via /api/v1/tasks/{id}/add_image/ then update_status.
