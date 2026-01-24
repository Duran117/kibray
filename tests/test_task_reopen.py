"""
Tests para Task Reopen Tracking (Q11.12)
Módulo 11 - FASE 2
"""

import pytest
from django.contrib.auth.models import User
from django.utils import timezone
from core.models import Project, Task, TaskStatusChange


@pytest.fixture
def user():
    return User.objects.create_user(username="reopenuser", password="testpass123")


@pytest.fixture
def user2():
    return User.objects.create_user(username="reopenuser2", password="testpass123")


@pytest.fixture
def project():
    from datetime import date

    return Project.objects.create(name="Reopen Test Project", start_date=date.today())


@pytest.mark.django_db
@pytest.mark.unit
@pytest.mark.module_11
class TestTaskReopenTracking:
    """Tests para histórico de reaperturas de tareas (Q11.12)"""

    def test_reopen_completed_task(self, project, user):
        """Reabrir una tarea completada"""
        task = Task.objects.create(
            project=project, title="Completed task", status="Completed", completed_at=timezone.now(), created_by=user
        )

        result = task.reopen(user=user, notes="Necesita revisión")

        assert result is True
        assert task.status == "In Progress"
        assert task.completed_at is None

    def test_reopen_non_completed_task_fails(self, project, user):
        """No se puede reabrir una tarea que no está completada"""
        task = Task.objects.create(project=project, title="Pending task", status="Pending", created_by=user)

        result = task.reopen(user=user)

        assert result is False
        assert task.status == "Pending"  # No cambió

    def test_reopen_creates_status_change_record(self, project, user):
        """Reabrir crea un registro en TaskStatusChange"""
        task = Task.objects.create(
            project=project, title="Task", status="Completed", completed_at=timezone.now(), created_by=user
        )

        # El signal ya creó un cambio al guardar como Completada
        initial_changes = task.status_changes.count()

        task.reopen(user=user, notes="Reabrir por error")

        # Debe haber al menos 1 cambio nuevo (el reopen)
        assert task.status_changes.count() > initial_changes

        # Buscar el cambio de reopen (más reciente)
        reopen_change = task.status_changes.filter(old_status="Completed").first()
        assert reopen_change is not None
        assert reopen_change.new_status in ["In Progress", "Pending"]
        assert reopen_change.notes == "Reabrir por error"

    def test_reopen_events_count_property(self, project, user):
        """reopen_events_count cuenta cuántas veces se reabrió"""
        task = Task.objects.create(project=project, title="Task", status="Pending", created_by=user)

        # Contar reaperturas desde Completada
        initial_reopen_count = task.reopen_events_count

        # Completar y reabrir
        task.status = "Completed"
        task.completed_at = timezone.now()
        task.save()
        task.reopen(user=user)

        assert task.reopen_events_count == initial_reopen_count + 1

        # Completar y reabrir de nuevo
        task.status = "Completed"
        task.completed_at = timezone.now()
        task.save()
        task.reopen(user=user)

        assert task.reopen_events_count == initial_reopen_count + 2

    def test_multiple_reopens_by_different_users(self, project, user, user2):
        """Múltiples reaperturas por diferentes usuarios"""
        task = Task.objects.create(
            project=project, title="Task", status="Completed", completed_at=timezone.now(), created_by=user
        )

        # Primera reapertura por user
        task.reopen(user=user, notes="Reopen 1")

        # Completar de nuevo
        task.status = "Completed"
        task.completed_at = timezone.now()
        task.save()

        # Segunda reapertura por user2
        task.reopen(user=user2, notes="Reopen 2")

        # Buscar cambios de reapertura específicamente
        reopen_changes = task.status_changes.filter(old_status="Completed").order_by("-changed_at")
        assert reopen_changes.count() >= 2
        # El más reciente debe tener notas de reopen
        latest = reopen_changes.first()
        assert "Reopen" in latest.notes or "Reapertura" in latest.notes

    def test_reopen_with_dependencies_sets_pendiente(self, project, user):
        """Reabrir con dependencias pendientes pone status=Pendiente"""
        dep = Task.objects.create(project=project, title="Dependency", status="Pending", created_by=user)

        task = Task.objects.create(
            project=project, title="Task", status="Completed", completed_at=timezone.now(), created_by=user
        )
        task.dependencies.add(dep)

        task.reopen(user=user)

        assert task.status == "Pending"  # No "In Progress" porque dep no está lista

    def test_reopen_without_dependencies_sets_en_progreso(self, project, user):
        """Reabrir sin dependencias pone status=En Progreso"""
        task = Task.objects.create(
            project=project, title="Task", status="Completed", completed_at=timezone.now(), created_by=user
        )

        task.reopen(user=user)

        assert task.status == "In Progress"

    def test_task_status_change_str(self, project, user):
        """Verificar __str__ de TaskStatusChange"""
        task = Task.objects.create(
            project=project, title="My Task", status="Completed", completed_at=timezone.now(), created_by=user
        )

        task.reopen(user=user, notes="Test")

        change = task.status_changes.first()
        # Check the __str__ format - now in English
        assert f"{task.title}:" in str(change)
        assert "Completed" in str(change) or "Completada" in str(change)
        assert "→" in str(change)

    def test_status_change_ordering(self, project, user):
        """TaskStatusChange se ordena por changed_at descendente"""
        task = Task.objects.create(project=project, title="Task", status="Pending", created_by=user)

        # Cambiar a En Progreso
        task.status = "In Progress"
        task.save()

        # Cambiar a Completada
        task.status = "Completed"
        task.completed_at = timezone.now()
        task.save()

        # Reabrir
        task.reopen(user=user)

        changes = list(task.status_changes.all())
        # Debe haber al menos 3 cambios
        assert len(changes) >= 3
        # El más reciente debe ser un cambio desde Completada
        assert changes[0].old_status == "Completed"

    def test_reopen_without_user(self, project, user):
        """Reabrir sin especificar usuario (changed_by=None)"""
        task = Task.objects.create(
            project=project, title="Task", status="Completed", completed_at=timezone.now(), created_by=user
        )

        task.reopen(user=None, notes="Sistema automático")

        change = task.status_changes.first()
        assert change.changed_by is None
        assert change.notes == "Sistema automático"

    def test_filter_tasks_with_multiple_reopens(self, project, user):
        """Filtrar tareas que han sido reabiertas múltiples veces"""
        # Tarea sin reaperturas
        task1 = Task.objects.create(project=project, title="T1", status="Completed", created_by=user)

        # Tarea con 1 reapertura
        task2 = Task.objects.create(project=project, title="T2", status="Pending", created_by=user)
        task2.status = "Completed"
        task2.save()
        task2.reopen(user=user)
        task2.status = "Completed"
        task2.save()

        # Tarea con 3 reaperturas
        task3 = Task.objects.create(project=project, title="T3", status="Pending", created_by=user)
        for _ in range(3):
            task3.status = "Completed"
            task3.save()
            task3.reopen(user=user)
        task3.status = "Completed"
        task3.save()

        # Verificar conteo de reaperturas
        assert task3.reopen_events_count >= 3
        assert task2.reopen_events_count >= 1
