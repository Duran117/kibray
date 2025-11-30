import json
from datetime import date
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from core.models import Project, Task, Employee

@pytest.mark.django_db
def test_bulk_task_assign_priority_status():
    User = get_user_model()
    user = User.objects.create_user(username="bulkuser", password="testpass", is_staff=True)
    client = APIClient()
    client.force_authenticate(user=user)

    project = Project.objects.create(name="Bulk Project", start_date=date.today())

    # Employee for assignment
    emp = Employee.objects.create(
        first_name="Emp",
        last_name="One",
        social_security_number="SSN123",
        hourly_rate=Decimal("20.00"),
    )

    tasks = [
        Task.objects.create(project=project, title=f"Task {i}") for i in range(3)
    ]
    task_ids = [t.id for t in tasks]

    # Bulk assign
    r = client.post(
        "/api/v1/tasks/bulk-update/",
        {"task_ids": task_ids, "action": "assign", "value": emp.id},
        format="json",
    )
    assert r.status_code == 200, r.content
    assert r.data["updated_count"] == 3
    for t in Task.objects.filter(id__in=task_ids):
        assert t.assigned_to == emp

    # Bulk priority (alias 'normal' -> 'medium')
    r2 = client.post(
        "/api/v1/tasks/bulk-update/",
        {"task_ids": task_ids, "action": "priority", "value": "normal"},
        format="json",
    )
    assert r2.status_code == 200
    for t in Task.objects.filter(id__in=task_ids):
        assert t.priority == "medium"

    # Bulk status change
    r3 = client.post(
        "/api/v1/tasks/bulk-update/",
        {"task_ids": task_ids, "action": "status", "value": "En Progreso"},
        format="json",
    )
    assert r3.status_code == 200
    for t in Task.objects.filter(id__in=task_ids):
        assert t.status == "En Progreso"

    # Invalid priority
    r_bad = client.post(
        "/api/v1/tasks/bulk-update/",
        {"task_ids": task_ids, "action": "priority", "value": "invalid"},
        format="json",
    )
    assert r_bad.status_code == 400
    assert "Invalid priority" in json.dumps(r_bad.data)

    # Invalid status
    r_bad2 = client.post(
        "/api/v1/tasks/bulk-update/",
        {"task_ids": task_ids, "action": "status", "value": "XYZ"},
        format="json",
    )
    assert r_bad2.status_code == 400
    assert "Invalid status" in json.dumps(r_bad2.data)
