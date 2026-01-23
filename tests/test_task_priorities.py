"""
Tests para Task Priorities (Q11.6)
Módulo 11 - FASE 2
"""

import pytest
from django.contrib.auth.models import User
from core.models import Project, Task


@pytest.fixture
def user():
    return User.objects.create_user(username="testuser", password="testpass123")


@pytest.fixture
def project():
    from datetime import date

    return Project.objects.create(name="Test Project", start_date=date.today(), description="Priority testing project")


@pytest.mark.django_db
@pytest.mark.unit
@pytest.mark.module_11
class TestTaskPriorities:
    """Tests para sistema de priorización de tareas"""

    def test_default_priority_is_medium(self, project, user):
        """Una tarea sin prioridad especificada debe ser 'medium'"""
        task = Task.objects.create(project=project, title="Task sin prioridad", created_by=user)
        assert task.priority == "medium"

    def test_create_task_with_each_priority(self, project, user):
        """Crear tareas con cada nivel de prioridad"""
        priorities = ["low", "medium", "high", "urgent"]
        for priority in priorities:
            task = Task.objects.create(project=project, title=f"Task {priority}", priority=priority, created_by=user)
            assert task.priority == priority

    def test_filter_by_priority(self, project, user):
        """Filtrar tareas por prioridad"""
        Task.objects.create(project=project, title="Low 1", priority="low", created_by=user)
        Task.objects.create(project=project, title="High 1", priority="high", created_by=user)
        Task.objects.create(project=project, title="High 2", priority="high", created_by=user)
        Task.objects.create(project=project, title="Urgent", priority="urgent", created_by=user)

        high_tasks = Task.objects.filter(priority="high")
        assert high_tasks.count() == 2

        urgent_tasks = Task.objects.filter(priority="urgent")
        assert urgent_tasks.count() == 1

    def test_order_by_priority_custom(self, project, user):
        """Ordenar tareas por prioridad (custom ordering)"""
        t1 = Task.objects.create(project=project, title="Low", priority="low", created_by=user)
        t2 = Task.objects.create(project=project, title="High", priority="high", created_by=user)
        t3 = Task.objects.create(project=project, title="Medium", priority="medium", created_by=user)
        t4 = Task.objects.create(project=project, title="Urgent", priority="urgent", created_by=user)

        # Orden esperado: urgent > high > medium > low
        from django.db.models import Case, When, IntegerField

        priority_order = Case(
            When(priority="urgent", then=0),
            When(priority="high", then=1),
            When(priority="medium", then=2),
            When(priority="low", then=3),
            output_field=IntegerField(),
        )

        sorted_tasks = Task.objects.filter(project=project).order_by(priority_order)
        assert sorted_tasks[0].priority == "urgent"
        assert sorted_tasks[1].priority == "high"
        assert sorted_tasks[2].priority == "medium"
        assert sorted_tasks[3].priority == "low"

    def test_change_priority(self, project, user):
        """Cambiar la prioridad de una tarea existente"""
        task = Task.objects.create(project=project, title="Changeable task", priority="low", created_by=user)
        assert task.priority == "low"

        task.priority = "urgent"
        task.save()
        task.refresh_from_db()

        assert task.priority == "urgent"

    def test_priority_with_dependencies(self, project, user):
        """Tareas de alta prioridad pueden tener dependencias de baja prioridad"""
        low_task = Task.objects.create(
            project=project, title="Low priority dependency", priority="low", created_by=user, status="Completed"
        )

        high_task = Task.objects.create(project=project, title="High priority task", priority="high", created_by=user)
        high_task.dependencies.add(low_task)

        assert high_task.priority == "high"
        assert high_task.can_start()  # La dependencia está completada

    def test_urgent_tasks_count(self, project, user):
        """Contar tareas urgentes para dashboard"""
        Task.objects.create(project=project, title="U1", priority="urgent", created_by=user)
        Task.objects.create(project=project, title="U2", priority="urgent", created_by=user)
        Task.objects.create(project=project, title="H1", priority="high", created_by=user)

        urgent_count = Task.objects.filter(priority="urgent", status="Pending").count()
        assert urgent_count == 2

    def test_priority_choices_are_valid(self):
        """Verificar que las opciones de prioridad están definidas correctamente"""
        from core.models import Task

        expected_priorities = {"low", "medium", "high", "urgent"}
        actual_priorities = {choice[0] for choice in Task.PRIORITY_CHOICES}

        assert actual_priorities == expected_priorities

    def test_priority_display_name(self, project, user):
        """Verificar que el display name de prioridad funciona (i18n)"""
        task = Task.objects.create(project=project, title="Display test", priority="urgent", created_by=user)

        # get_priority_display() debe retornar el label traducido
        display = task.get_priority_display()
        assert display in ["Urgente", "Urgent"]  # Depende del idioma activo
