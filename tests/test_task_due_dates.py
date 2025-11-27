"""
Tests para Task Due Dates y Alertas (Q11.1)
Módulo 11 - FASE 2
"""

import pytest
from datetime import date, timedelta
from django.contrib.auth.models import User
from core.models import Project, Task


@pytest.fixture
def user():
    return User.objects.create_user(username="dueuser", password="testpass123")


@pytest.fixture
def project():
    return Project.objects.create(
        name="Due Date Test Project",
        start_date=date.today()
    )


@pytest.mark.django_db
@pytest.mark.unit
@pytest.mark.module_11
class TestTaskDueDates:
    """Tests para fechas de vencimiento de tareas (Q11.1)"""

    def test_task_without_due_date(self, project, user):
        """Una tarea puede crearse sin due_date (opcional)"""
        task = Task.objects.create(
            project=project,
            title="Task without due date",
            created_by=user
        )
        assert task.due_date is None

    def test_task_with_due_date(self, project, user):
        """Crear tarea con due_date específica"""
        future_date = date.today() + timedelta(days=7)
        task = Task.objects.create(
            project=project,
            title="Task with due date",
            due_date=future_date,
            created_by=user
        )
        assert task.due_date == future_date

    def test_filter_tasks_by_due_date(self, project, user):
        """Filtrar tareas por due_date"""
        today = date.today()
        tomorrow = today + timedelta(days=1)
        next_week = today + timedelta(days=7)
        
        task1 = Task.objects.create(project=project, title="Due today", due_date=today, created_by=user)
        task2 = Task.objects.create(project=project, title="Due tomorrow", due_date=tomorrow, created_by=user)
        task3 = Task.objects.create(project=project, title="Due next week", due_date=next_week, created_by=user)
        
        due_tomorrow = Task.objects.filter(due_date=tomorrow)
        assert due_tomorrow.count() == 1
        assert due_tomorrow.first() == task2

    def test_overdue_tasks(self, project, user):
        """Identificar tareas vencidas (overdue)"""
        yesterday = date.today() - timedelta(days=1)
        last_week = date.today() - timedelta(days=7)
        tomorrow = date.today() + timedelta(days=1)
        
        overdue1 = Task.objects.create(
            project=project, title="Overdue 1", due_date=yesterday, 
            status="Pendiente", created_by=user
        )
        overdue2 = Task.objects.create(
            project=project, title="Overdue 2", due_date=last_week, 
            status="En Progreso", created_by=user
        )
        not_overdue = Task.objects.create(
            project=project, title="Future", due_date=tomorrow, 
            status="Pendiente", created_by=user
        )
        completed = Task.objects.create(
            project=project, title="Completed", due_date=yesterday, 
            status="Completada", created_by=user
        )
        
        # Overdue: tareas no completadas con due_date < today
        overdue_tasks = Task.objects.filter(
            due_date__lt=date.today()
        ).exclude(status="Completada")
        
        assert overdue_tasks.count() == 2
        assert overdue1 in overdue_tasks
        assert overdue2 in overdue_tasks

    def test_due_soon_tasks(self, project, user):
        """Identificar tareas que vencen pronto (próximos 3 días)"""
        today = date.today()
        tomorrow = today + timedelta(days=1)
        day_after = today + timedelta(days=2)
        next_week = today + timedelta(days=7)
        
        due_soon1 = Task.objects.create(project=project, title="Soon 1", due_date=tomorrow, created_by=user)
        due_soon2 = Task.objects.create(project=project, title="Soon 2", due_date=day_after, created_by=user)
        not_soon = Task.objects.create(project=project, title="Later", due_date=next_week, created_by=user)
        
        # Due soon: próximos 3 días
        threshold = today + timedelta(days=3)
        due_soon = Task.objects.filter(
            due_date__gte=today,
            due_date__lte=threshold
        ).exclude(status="Completada")
        
        assert due_soon.count() == 2

    def test_update_due_date(self, project, user):
        """Actualizar due_date de una tarea existente"""
        task = Task.objects.create(
            project=project,
            title="Updateable task",
            due_date=date.today(),
            created_by=user
        )
        
        new_date = date.today() + timedelta(days=5)
        task.due_date = new_date
        task.save()
        task.refresh_from_db()
        
        assert task.due_date == new_date

    def test_remove_due_date(self, project, user):
        """Permitir eliminar due_date (cambiar a None)"""
        task = Task.objects.create(
            project=project,
            title="Task with due date",
            due_date=date.today() + timedelta(days=3),
            created_by=user
        )
        
        task.due_date = None
        task.save()
        task.refresh_from_db()
        
        assert task.due_date is None

    def test_order_by_due_date(self, project, user):
        """Ordenar tareas por due_date"""
        today = date.today()
        
        task1 = Task.objects.create(project=project, title="T1", due_date=today + timedelta(days=5), created_by=user)
        task2 = Task.objects.create(project=project, title="T2", due_date=today + timedelta(days=1), created_by=user)
        task3 = Task.objects.create(project=project, title="T3", due_date=today + timedelta(days=3), created_by=user)
        
        ordered = Task.objects.filter(project=project).order_by("due_date")
        assert ordered[0] == task2  # Día 1
        assert ordered[1] == task3  # Día 3
        assert ordered[2] == task1  # Día 5

    def test_priority_with_due_date(self, project, user):
        """Combinar prioridad con due_date para ordenamiento"""
        today = date.today()
        
        # Urgente con due date lejana
        urgent = Task.objects.create(
            project=project, title="Urgent", 
            priority="urgent", due_date=today + timedelta(days=10),
            created_by=user
        )
        
        # Media prioridad con due date cercana
        medium = Task.objects.create(
            project=project, title="Medium", 
            priority="medium", due_date=today + timedelta(days=1),
            created_by=user
        )
        
        # Ambos campos están presentes y se pueden usar para ordenamiento
        assert urgent.priority == "urgent"
        assert medium.due_date < urgent.due_date

    def test_completed_task_with_past_due_date_not_overdue(self, project, user):
        """Tarea completada con due_date pasada NO es overdue"""
        past_date = date.today() - timedelta(days=5)
        
        task = Task.objects.create(
            project=project,
            title="Completed past due",
            due_date=past_date,
            status="Completada",
            created_by=user
        )
        
        overdue_tasks = Task.objects.filter(
            due_date__lt=date.today()
        ).exclude(status="Completada")
        
        assert task not in overdue_tasks
