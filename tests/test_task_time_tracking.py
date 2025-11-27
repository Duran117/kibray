"""
Tests para Task Time Tracking (Q11.13)
Módulo 11 - FASE 2
"""

import pytest
from datetime import timedelta
from django.contrib.auth.models import User
from django.utils import timezone
from core.models import Project, Task, Employee, TimeEntry


@pytest.fixture
def user():
    return User.objects.create_user(username="trackuser", password="testpass123")


@pytest.fixture
def employee(user):
    return Employee.objects.create(
        user=user,
        first_name="Time",
        last_name="Tracker",
        hourly_rate=25.00
    )


@pytest.fixture
def project():
    from datetime import date
    return Project.objects.create(
        name="Time Tracking Project",
        start_date=date.today()
    )


@pytest.mark.django_db
@pytest.mark.unit
@pytest.mark.module_11
class TestTaskTimeTracking:
    """Tests para time tracking integrado en tareas (Q11.13)"""

    def test_task_initial_time_is_zero(self, project, user):
        """Nueva tarea tiene time_tracked_seconds=0 y started_at=None"""
        task = Task.objects.create(
            project=project,
            title="New task",
            created_by=user
        )
        
        assert task.time_tracked_seconds == 0
        assert task.started_at is None
        assert task.get_time_tracked_hours() == 0

    def test_start_tracking(self, project, user):
        """start_tracking() inicia el timer y cambia status a En Progreso"""
        task = Task.objects.create(
            project=project,
            title="Trackable task",
            status="Pendiente",
            created_by=user,
            is_touchup=False
        )
        
        result = task.start_tracking()
        
        assert result is True
        assert task.started_at is not None
        assert task.status == "En Progreso"

    def test_start_tracking_touch_up_fails(self, project, user):
        """Touch-ups no usan tracking interno, start_tracking debe fallar"""
        touchup = Task.objects.create(
            project=project,
            title="Touch-up",
            is_touchup=True,
            created_by=user
        )
        
        result = touchup.start_tracking()
        
        assert result is False
        assert touchup.started_at is None

    def test_start_tracking_with_pending_dependency_fails(self, project, user):
        """No puede iniciar tracking si hay dependencias pendientes"""
        dep = Task.objects.create(
            project=project,
            title="Dependency",
            status="Pendiente",
            created_by=user
        )
        
        task = Task.objects.create(
            project=project,
            title="Dependent task",
            created_by=user,
            is_touchup=False
        )
        task.dependencies.add(dep)
        
        result = task.start_tracking()
        
        assert result is False
        assert task.started_at is None

    def test_stop_tracking(self, project, user):
        """stop_tracking() detiene el timer y acumula tiempo"""
        task = Task.objects.create(
            project=project,
            title="Task",
            created_by=user,
            is_touchup=False
        )
        
        # Iniciar tracking
        task.start_tracking()
        start_time = task.started_at
        
        # Simular trabajo por 5 segundos
        task.started_at = timezone.now() - timedelta(seconds=5)
        task.save()
        
        # Detener tracking
        elapsed = task.stop_tracking()
        
        assert elapsed is not None
        assert elapsed >= 5
        assert task.time_tracked_seconds >= 5
        assert task.started_at is None  # Se resetea

    def test_stop_tracking_accumulates_time(self, project, user):
        """Múltiples sesiones de tracking acumulan tiempo total"""
        task = Task.objects.create(
            project=project,
            title="Task",
            created_by=user,
            is_touchup=False
        )
        
        # Primera sesión: 10 segundos
        task.start_tracking()
        task.started_at = timezone.now() - timedelta(seconds=10)
        task.save()
        task.stop_tracking()
        
        first_total = task.time_tracked_seconds
        assert first_total >= 10
        
        # Segunda sesión: 15 segundos más
        task.status = "En Progreso"
        task.save()
        task.start_tracking()
        task.started_at = timezone.now() - timedelta(seconds=15)
        task.save()
        task.stop_tracking()
        
        assert task.time_tracked_seconds >= (first_total + 15)

    def test_get_time_tracked_hours(self, project, user):
        """Convertir segundos a horas decimales"""
        task = Task.objects.create(
            project=project,
            title="Task",
            created_by=user
        )
        
        # Simular 3600 segundos = 1 hora
        task.time_tracked_seconds = 3600
        task.save()
        
        assert task.get_time_tracked_hours() == 1.0
        
        # 7200 segundos = 2 horas
        task.time_tracked_seconds = 7200
        task.save()
        
        assert task.get_time_tracked_hours() == 2.0
        
        # 5400 segundos = 1.5 horas
        task.time_tracked_seconds = 5400
        task.save()
        
        assert task.get_time_tracked_hours() == 1.5

    def test_get_time_entries_hours(self, project, user, employee):
        """Sumar horas de TimeEntry vinculadas a la tarea"""
        task = Task.objects.create(
            project=project,
            title="Task",
            created_by=user
        )
        
        # Crear time entries
        from datetime import date, time
        TimeEntry.objects.create(
            employee=employee,
            project=project,
            task=task,
            date=date.today(),
            start_time=time(9, 0),
            end_time=time(11, 30),
            hours_worked=2.5
        )
        TimeEntry.objects.create(
            employee=employee,
            project=project,
            task=task,
            date=date.today(),
            start_time=time(13, 0),
            end_time=time(16, 0),
            hours_worked=3.0
        )
        
        total = task.get_time_entries_hours()
        assert total == 5.5

    def test_total_hours_property(self, project, user, employee):
        """total_hours combina tracking interno + time entries"""
        from datetime import date
        
        task = Task.objects.create(
            project=project,
            title="Task",
            created_by=user
        )
        
        # Tracking interno: 2 horas (7200 segundos)
        task.time_tracked_seconds = 7200
        task.save()
        
        # Time entry: 3 horas
        from datetime import time
        TimeEntry.objects.create(
            employee=employee,
            project=project,
            task=task,
            date=date.today(),
            start_time=time(9, 0),
            end_time=time(12, 0),
            hours_worked=3.0
        )
        
        assert task.total_hours == 5.0  # 2 + 3

    def test_stop_tracking_minimum_elapsed(self, project, user):
        """stop_tracking con tiempo <1 segundo registra 1 segundo mínimo"""
        task = Task.objects.create(
            project=project,
            title="Task",
            created_by=user,
            is_touchup=False
        )
        
        task.start_tracking()
        # Inmediatamente detener (< 1 segundo)
        elapsed = task.stop_tracking()
        
        assert elapsed == 1
        assert task.time_tracked_seconds >= 1

    def test_already_started_tracking_does_nothing(self, project, user):
        """Intentar start_tracking cuando ya está corriendo no hace nada"""
        task = Task.objects.create(
            project=project,
            title="Task",
            created_by=user,
            is_touchup=False
        )
        
        task.start_tracking()
        first_start = task.started_at
        
        # Intentar iniciar de nuevo
        result = task.start_tracking()
        
        assert result is False
        assert task.started_at == first_start  # No cambió

    def test_time_tracking_with_task_completion(self, project, user):
        """Completar tarea mientras hay tracking activo"""
        task = Task.objects.create(
            project=project,
            title="Task",
            created_by=user,
            is_touchup=False
        )
        
        task.start_tracking()
        task.started_at = timezone.now() - timedelta(seconds=30)
        task.save()
        
        # Detener antes de completar
        task.stop_tracking()
        
        task.status = "Completada"
        task.completed_at = timezone.now()
        task.save()
        
        assert task.time_tracked_seconds >= 30
        assert task.status == "Completada"
