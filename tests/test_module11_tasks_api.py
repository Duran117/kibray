from datetime import date, time

import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APIClient

from core.models import Employee, Project, Task, TaskStatusChange, TimeEntry


@pytest.mark.django_db
class TestModule11TaskAPI:
    def setup_method(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="pm", password="pass123")
        self.client.login(username="pm", password="pass123")
        self.project = Project.objects.create(name="Test Project", start_date=date.today())
        self.employee_user = User.objects.create_user(username="emp", password="pass123")
        self.employee = Employee.objects.create(
            user=self.employee_user, first_name="Emp", last_name="User", social_security_number="123", hourly_rate=25
        )

    def create_task(self, title="Task A", **kwargs):
        data = {
            "project": self.project,
            "title": title,
            "description": "Desc",
            "status": "Pendiente",
            "priority": "medium",
        }
        data.update(kwargs)
        return Task.objects.create(**data)

    def test_add_and_remove_dependency(self):
        parent = self.create_task("Parent Task")
        child = self.create_task("Child Task")
        url_add = reverse("task-add-dependency", args=[child.id])
        resp = self.client.post(url_add, {"dependency_id": parent.id}, format="json")
        assert resp.status_code == 200
        child.refresh_from_db()
        assert parent in child.dependencies.all()
        url_remove = reverse("task-remove-dependency", args=[child.id])
        resp2 = self.client.post(url_remove, {"dependency_id": parent.id}, format="json")
        assert resp2.status_code == 200
        child.refresh_from_db()
        assert parent not in child.dependencies.all()

    def test_reopen_creates_status_change(self):
        task = self.create_task("Closing Task", status="Completada")
        url = reverse("task-reopen", args=[task.id])
        resp = self.client.post(url, {"notes": "Need more work"}, format="json")
        assert resp.status_code == 200
        task.refresh_from_db()
        assert task.status in ["Pendiente", "En Progreso"]
        assert TaskStatusChange.objects.filter(task=task, old_status="Completada").exists()

    def test_start_and_stop_tracking(self):
        task = self.create_task("Track Task")
        # start tracking
        start_url = reverse("task-start-tracking", args=[task.id])
        resp = self.client.post(start_url, {}, format="json")
        assert resp.status_code == 200
        task.refresh_from_db()
        assert task.started_at is not None
        # stop tracking
        stop_url = reverse("task-stop-tracking", args=[task.id])
        resp2 = self.client.post(stop_url, {}, format="json")
        assert resp2.status_code == 200
        task.refresh_from_db()
        assert task.started_at is None
        assert task.time_tracked_seconds > 0

    def test_hours_summary(self):
        task = self.create_task("Hours Task")
        # Add a TimeEntry linked to task
        TimeEntry.objects.create(
            employee=self.employee,
            project=self.project,
            task=task,
            date=date.today(),
            start_time=time(8, 0),
            end_time=time(10, 0),
        )
        url = reverse("task-hours-summary", args=[task.id])
        resp = self.client.get(url)
        assert resp.status_code == 200
        data = resp.json()
        assert "total_hours" in data
        assert data["time_entries_hours"] > 0

    def test_add_image_versioning(self):
        task = self.create_task("Image Task")
        url = reverse("task-add-image", args=[task.id])
        # Simulate upload using a small in-memory file
        from django.core.files.uploadedfile import SimpleUploadedFile

        image_file = SimpleUploadedFile("test.jpg", b"filecontent", content_type="image/jpeg")
        resp = self.client.post(url, {"image": image_file, "caption": "First"}, format="multipart")
        assert resp.status_code == 200
        v1 = resp.json()["version"]
        # Upload second version
        image_file2 = SimpleUploadedFile("test2.jpg", b"filecontent2", content_type="image/jpeg")
        resp2 = self.client.post(url, {"image": image_file2, "caption": "Second"}, format="multipart")
        assert resp2.status_code == 200
        v2 = resp2.json()["version"]
        assert v2 == v1 + 1
        # Ensure previous current flag cleared
        assert task.images.filter(is_current=True).count() == 1
