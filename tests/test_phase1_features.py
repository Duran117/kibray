"""
Tests for Phase 1 implementation:
- Task.reopen() method
- DailyLog.instantiate_planned_templates()
- DailyLog.evaluate_completion()
- WeatherSnapshot caching and TTL

Run with:
    pytest tests/test_phase1_features.py -v
"""
import pytest
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch, MagicMock

from core.models import (
    Project, Task, TaskStatusChange, TaskTemplate,
    DailyLog, WeatherSnapshot
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def admin_user(db):
    """Admin user for testing"""
    return User.objects.create_user(
        username='admin_phase1',
        email='admin@phase1.com',
        password='admin123',
        is_staff=True,
        is_superuser=True
    )


@pytest.fixture
def regular_user(db):
    """Regular user for testing"""
    return User.objects.create_user(
        username='user_phase1',
        email='user@phase1.com',
        password='user123'
    )


@pytest.fixture
def project(db):
    """Test project"""
    return Project.objects.create(
        name='Test Project Phase 1',
        client='Test Client',
        start_date=date.today(),
        budget_total=Decimal('15000.00')
    )


@pytest.fixture
def task_template(db, admin_user):
    """Sample task template"""
    return TaskTemplate.objects.create(
        title='Preparar superficie',
        description='Lijar y limpiar área de trabajo',
        default_priority='high',
        estimated_hours=Decimal('4.0'),
        tags=['preparacion', 'superficie', 'lijado'],
        checklist=['Lijar', 'Aspirar polvo', 'Limpiar con trapo húmedo'],
        created_by=admin_user
    )


@pytest.fixture
def daily_log(db, project, admin_user):
    """Sample daily log"""
    return DailyLog.objects.create(
        project=project,
        date=date.today(),
        weather='Soleado',
        crew_count=5,
        created_by=admin_user
    )


# ============================================================================
# TESTS: Task.reopen()
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestTaskReopen:
    """Test Task.reopen() method (Q11.12)"""
    
    def test_reopen_completed_task(self, project, regular_user):
        """Test reopening a completed task clears completed_at and creates history"""
        # Create completed task
        task = Task.objects.create(
            project=project,
            title='Test Task',
            status='Completada',
            completed_at=timezone.now(),
            created_by=regular_user
        )
        
        # Reopen it
        result = task.reopen(user=regular_user, notes='Needs rework')
        
        assert result is True
        task.refresh_from_db()
        assert task.status in ['En Progreso', 'Pendiente']
        assert task.completed_at is None
        
        # Verify TaskStatusChange was created
        changes = TaskStatusChange.objects.filter(task=task)
        assert changes.count() >= 1
        change = changes.filter(old_status='Completada').first()
        assert change is not None
        assert change.changed_by == regular_user
        assert 'Reapertura' in change.notes or 'rework' in change.notes
    
    def test_reopen_non_completed_task_fails(self, project, regular_user):
        """Test that reopening a non-completed task returns False"""
        task = Task.objects.create(
            project=project,
            title='Pending Task',
            status='Pendiente',
            created_by=regular_user
        )
        
        result = task.reopen(user=regular_user)
        
        assert result is False
        task.refresh_from_db()
        assert task.status == 'Pendiente'
        assert TaskStatusChange.objects.filter(task=task).count() == 0
    
    def test_reopen_without_user(self, project, regular_user):
        """Test reopening without specifying user"""
        task = Task.objects.create(
            project=project,
            title='Test Task',
            status='Completada',
            completed_at=timezone.now(),
            created_by=regular_user
        )
        
        result = task.reopen(notes='System reopen')
        
        assert result is True
        task.refresh_from_db()
        assert task.completed_at is None
        
        # TaskStatusChange should exist but changed_by may be None
        changes = TaskStatusChange.objects.filter(task=task)
        assert changes.exists()


# ============================================================================
# TESTS: DailyLog Planning Methods
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestDailyLogPlanning:
    """Test DailyLog planning methods (instantiate_planned_templates, evaluate_completion)"""
    
    def test_instantiate_planned_templates(self, daily_log, task_template, admin_user):
        """Test creating tasks from planned templates"""
        # Add template to daily log
        daily_log.planned_templates.add(task_template)
        
        # Instantiate
        created_tasks = daily_log.instantiate_planned_templates(
            created_by=admin_user,
            assigned_to=None
        )
        
        assert len(created_tasks) == 1
        task = created_tasks[0]
        assert task.title == task_template.title
        assert task.description == task_template.description
        assert task.project == daily_log.project
        assert task.created_by == admin_user
        assert task in daily_log.planned_tasks.all()
    
    def test_instantiate_idempotent(self, daily_log, task_template, admin_user):
        """Test that instantiating twice doesn't create duplicates"""
        daily_log.planned_templates.add(task_template)
        
        # First instantiation
        created1 = daily_log.instantiate_planned_templates(created_by=admin_user)
        assert len(created1) == 1
        
        # Second instantiation should return empty (no duplicates)
        created2 = daily_log.instantiate_planned_templates(created_by=admin_user)
        assert len(created2) == 0
        
        # Verify only one task exists
        assert daily_log.planned_tasks.count() == 1
    
    def test_evaluate_completion_all_completed(self, daily_log, project, admin_user):
        """Test evaluation when all planned tasks are completed"""
        # Create and add completed tasks
        task1 = Task.objects.create(
            project=project,
            title='Task 1',
            status='Completada',
            created_by=admin_user
        )
        task2 = Task.objects.create(
            project=project,
            title='Task 2',
            status='Completada',
            created_by=admin_user
        )
        daily_log.planned_tasks.add(task1, task2)
        
        # Evaluate
        result = daily_log.evaluate_completion()
        
        assert result is True
        daily_log.refresh_from_db()
        assert daily_log.is_complete is True
        assert daily_log.incomplete_reason == ''
    
    def test_evaluate_completion_partial(self, daily_log, project, admin_user):
        """Test evaluation when some tasks are incomplete"""
        task1 = Task.objects.create(
            project=project,
            title='Task 1',
            status='Completada',
            created_by=admin_user
        )
        task2 = Task.objects.create(
            project=project,
            title='Task 2',
            status='En Progreso',
            created_by=admin_user
        )
        daily_log.planned_tasks.add(task1, task2)
        
        result = daily_log.evaluate_completion()
        
        assert result is False
        daily_log.refresh_from_db()
        assert daily_log.is_complete is False
        assert '1' in daily_log.incomplete_reason
        assert 'Faltan' in daily_log.incomplete_reason
    
    def test_evaluate_completion_no_tasks(self, daily_log):
        """Test evaluation when no tasks are planned"""
        result = daily_log.evaluate_completion()
        
        assert result is False
        daily_log.refresh_from_db()
        assert daily_log.is_complete is False
        assert 'No hay tareas' in daily_log.incomplete_reason


# ============================================================================
# TESTS: WeatherSnapshot
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestWeatherSnapshot:
    """Test WeatherSnapshot model and caching logic"""
    
    def test_create_weather_snapshot(self, project):
        """Test creating a weather snapshot"""
        snap = WeatherSnapshot.objects.create(
            project=project,
            date=date.today(),
            source='openweathermap',
            temperature_max=Decimal('28.5'),
            temperature_min=Decimal('18.2'),
            conditions_text='Partly cloudy',
            precipitation_mm=Decimal('0.0'),
            wind_kph=Decimal('12.5'),
            humidity_percent=65,
            latitude=Decimal('29.42410'),
            longitude=Decimal('-98.49360')
        )
        
        assert snap.project == project
        assert snap.date == date.today()
        assert snap.temperature_max == Decimal('28.5')
        assert snap.is_stale() is False  # Just created
    
    def test_is_stale_fresh_snapshot(self, project):
        """Test is_stale() returns False for recent snapshots"""
        snap = WeatherSnapshot.objects.create(
            project=project,
            date=date.today(),
            source='openweathermap',
            temperature_max=Decimal('25.0')
        )
        
        assert snap.is_stale(ttl_hours=6) is False
    
    def test_is_stale_old_snapshot(self, project):
        """Test is_stale() returns True for old snapshots"""
        snap = WeatherSnapshot.objects.create(
            project=project,
            date=date.today(),
            source='openweathermap',
            temperature_max=Decimal('25.0')
        )
        
        # Manually set fetched_at to 8 hours ago
        old_time = timezone.now() - timedelta(hours=8)
        WeatherSnapshot.objects.filter(pk=snap.pk).update(fetched_at=old_time)
        snap.refresh_from_db()
        
        assert snap.is_stale(ttl_hours=6) is True
    
    def test_unique_constraint(self, project):
        """Test unique_together constraint (project, date, source)"""
        WeatherSnapshot.objects.create(
            project=project,
            date=date.today(),
            source='openweathermap',
            temperature_max=Decimal('25.0')
        )
        
        # Creating duplicate should raise IntegrityError
        with pytest.raises(Exception):  # Django IntegrityError
            WeatherSnapshot.objects.create(
                project=project,
                date=date.today(),
                source='openweathermap',
                temperature_max=Decimal('26.0')
            )


# ============================================================================
# TESTS: Weather Service Integration
# ============================================================================

@pytest.mark.django_db
@pytest.mark.integration
class TestWeatherServiceIntegration:
    """Test weather service with snapshot caching"""
    
    @patch('core.services.weather.weather_service.get_weather')
    def test_get_or_create_snapshot_creates_new(self, mock_get_weather, project):
        """Test get_or_create_snapshot creates new snapshot when none exists"""
        from core.services.weather import get_or_create_snapshot
        
        # Mock weather service response
        mock_get_weather.return_value = {
            'temperature': 22.5,
            'condition': 'Clear',
            'humidity': 65,
            'wind_speed': 12.5,
            'description': 'Clear sky',
            'provider': 'openweathermap'
        }
        
        snap = get_or_create_snapshot(
            project=project,
            latitude=29.4241,
            longitude=-98.4936,
            date=timezone.now()
        )
        
        assert snap is not None
        assert snap.project == project
        assert snap.temperature_max == Decimal('22.5')
        assert snap.conditions_text == 'Clear sky'
        assert snap.humidity_percent == 65
        mock_get_weather.assert_called_once()
    
    @patch('core.services.weather.weather_service.get_weather')
    def test_get_or_create_snapshot_uses_cache(self, mock_get_weather, project):
        """Test get_or_create_snapshot uses existing fresh snapshot"""
        from core.services.weather import get_or_create_snapshot
        
        # Create fresh snapshot
        existing = WeatherSnapshot.objects.create(
            project=project,
            date=date.today(),
            source='openweathermap',
            temperature_max=Decimal('25.0'),
            conditions_text='Sunny'
        )
        
        snap = get_or_create_snapshot(
            project=project,
            latitude=29.4241,
            longitude=-98.4936,
            date=timezone.now()
        )
        
        assert snap.pk == existing.pk
        assert snap.temperature_max == Decimal('25.0')
        # Should not call weather service (cached)
        mock_get_weather.assert_not_called()


# ============================================================================
# TESTS: TaskTemplate
# ============================================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestTaskTemplate:
    """Test TaskTemplate model and create_task method"""
    
    def test_create_task_from_template(self, task_template, project, admin_user):
        """Test creating a task from template"""
        task = task_template.create_task(
            project=project,
            created_by=admin_user,
            assigned_to=None
        )
        
        assert task.title == task_template.title
        assert task.description == task_template.description
        assert task.priority == task_template.default_priority
        assert task.project == project
        assert task.created_by == admin_user
        assert task.status == 'Pendiente'
    
    def test_create_task_with_overrides(self, task_template, project, admin_user):
        """Test creating task with field overrides"""
        task = task_template.create_task(
            project=project,
            created_by=admin_user,
            extra_fields={
                'status': 'En Progreso',
                'priority': 'low'
            }
        )
        
        assert task.status == 'En Progreso'
        assert task.priority == 'low'
        assert task.title == task_template.title  # Still uses template title
