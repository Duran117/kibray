"""
Test Suite for Executive Focus Workflow (Module 25 - Productivity)
Tests models, API endpoints, wizard workflow, and iCal feed generation.
"""
import json
from datetime import datetime, timedelta
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from core.models import DailyFocusSession, FocusTask

User = get_user_model()


class FocusWorkflowModelsTest(TestCase):
    """Test Focus Workflow models"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        self.today = timezone.localdate()
    
    def test_create_daily_focus_session(self):
        """Test creating a daily focus session"""
        session = DailyFocusSession.objects.create(
            user=self.user,
            date=self.today,
            energy_level=7,
            notes="Feeling productive today!"
        )
        
        self.assertEqual(session.user, self.user)
        self.assertEqual(session.energy_level, 7)
        self.assertEqual(session.total_tasks, 0)
    
    def test_energy_level_validation(self):
        """Test energy level must be 1-10"""
        from django.core.exceptions import ValidationError
        
        # Should fail with energy_level = 11
        session = DailyFocusSession(
            user=self.user,
            date=self.today,
            energy_level=11
        )
        with self.assertRaises(ValidationError):
            session.full_clean()
    
    def test_create_focus_task(self):
        """Test creating a focus task"""
        session = DailyFocusSession.objects.create(
            user=self.user,
            date=self.today,
            energy_level=5
        )
        
        task = FocusTask.objects.create(
            session=session,
            title="Complete project proposal",
            description="Finish the Q1 proposal for ABC Corp",
            is_high_impact=True,
            impact_reason="This will bring in $50K revenue",
            is_frog=True,
            checklist=[
                {"text": "Research requirements", "done": False},
                {"text": "Write draft", "done": False},
                {"text": "Get approval", "done": False}
            ],
            scheduled_start=timezone.now() + timedelta(hours=1),
            scheduled_end=timezone.now() + timedelta(hours=3)
        )
        
        self.assertEqual(task.title, "Complete project proposal")
        self.assertTrue(task.is_high_impact)
        self.assertTrue(task.is_frog)
        self.assertEqual(task.checklist_total, 3)
        self.assertEqual(task.checklist_completed, 0)
        self.assertEqual(task.checklist_progress, 0)
        self.assertEqual(task.duration_minutes, 120)
    
    def test_only_one_frog_per_session(self):
        """Test that only one Frog task is allowed per session"""
        from django.core.exceptions import ValidationError
        
        session = DailyFocusSession.objects.create(
            user=self.user,
            date=self.today,
            energy_level=5
        )
        
        # Create first frog
        FocusTask.objects.create(
            session=session,
            title="Frog 1",
            is_high_impact=True,
            impact_reason="Important",
            is_frog=True
        )
        
        # Try to create second frog - should fail
        task2 = FocusTask(
            session=session,
            title="Frog 2",
            is_high_impact=True,
            impact_reason="Also important",
            is_frog=True
        )
        
        with self.assertRaises(ValidationError):
            task2.full_clean()
    
    def test_frog_must_be_high_impact(self):
        """Test that Frog task must also be High Impact"""
        from django.core.exceptions import ValidationError
        
        session = DailyFocusSession.objects.create(
            user=self.user,
            date=self.today,
            energy_level=5
        )
        
        task = FocusTask(
            session=session,
            title="Low impact frog",
            is_high_impact=False,
            is_frog=True
        )
        
        with self.assertRaises(ValidationError):
            task.full_clean()
    
    def test_high_impact_requires_reason(self):
        """Test that High Impact tasks require impact_reason"""
        from django.core.exceptions import ValidationError
        
        session = DailyFocusSession.objects.create(
            user=self.user,
            date=self.today,
            energy_level=5
        )
        
        task = FocusTask(
            session=session,
            title="High impact task",
            is_high_impact=True,
            impact_reason=""  # Empty reason
        )
        
        with self.assertRaises(ValidationError):
            task.full_clean()
    
    def test_calendar_title_formatting(self):
        """Test calendar title includes emoji"""
        session = DailyFocusSession.objects.create(
            user=self.user,
            date=self.today,
            energy_level=5
        )
        
        frog_task = FocusTask.objects.create(
            session=session,
            title="My Frog Task",
            is_high_impact=True,
            impact_reason="Critical",
            is_frog=True
        )
        
        high_impact_task = FocusTask.objects.create(
            session=session,
            title="My High Impact Task",
            is_high_impact=True,
            impact_reason="Important"
        )
        
        regular_task = FocusTask.objects.create(
            session=session,
            title="Regular Task"
        )
        
        self.assertEqual(frog_task.get_calendar_title(), "🐸 My Frog Task")
        self.assertEqual(high_impact_task.get_calendar_title(), "⚡ My High Impact Task")
        self.assertEqual(regular_task.get_calendar_title(), "Regular Task")


class FocusWorkflowAPITest(TestCase):
    """Test Focus Workflow API endpoints"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        self.today = timezone.localdate()
    
    def test_create_session_via_api(self):
        """Test creating a focus session via API"""
        url = reverse('focus-session-list')
        data = {
            'date': str(self.today),
            'energy_level': 8,
            'notes': 'Ready to crush it!',
            'tasks': [
                {
                    'title': 'Task 1',
                    'is_high_impact': True,
                    'impact_reason': 'Will generate revenue',
                    'is_frog': True,
                    'checklist': [
                        {'text': 'Step 1', 'done': False},
                        {'text': 'Step 2', 'done': False}
                    ],
                    'scheduled_start': (timezone.now() + timedelta(hours=1)).isoformat(),
                    'scheduled_end': (timezone.now() + timedelta(hours=2)).isoformat()
                },
                {
                    'title': 'Task 2',
                    'is_high_impact': True,
                    'impact_reason': 'Important for client',
                    'is_frog': False
                }
            ]
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(DailyFocusSession.objects.count(), 1)
        self.assertEqual(FocusTask.objects.count(), 2)
        
        session = DailyFocusSession.objects.first()
        self.assertEqual(session.energy_level, 8)
        self.assertEqual(session.total_tasks, 2)
        self.assertEqual(session.high_impact_tasks, 2)
    
    def test_get_today_session(self):
        """Test retrieving today's session"""
        session = DailyFocusSession.objects.create(
            user=self.user,
            date=self.today,
            energy_level=6
        )
        
        url = reverse('focus-session-today')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], session.id)
    
    def test_focus_stats(self):
        """Test focus stats endpoint"""
        # Create some test data
        session = DailyFocusSession.objects.create(
            user=self.user,
            date=self.today,
            energy_level=7
        )
        
        FocusTask.objects.create(
            session=session,
            title="Task 1",
            is_high_impact=True,
            impact_reason="Important",
            is_frog=True,
            is_completed=True
        )
        
        FocusTask.objects.create(
            session=session,
            title="Task 2",
            is_high_impact=True,
            impact_reason="Also important"
        )
        
        url = reverse('focus-stats')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_sessions'], 1)
        self.assertEqual(response.data['total_tasks'], 2)
        self.assertEqual(response.data['completed_tasks'], 1)
        self.assertEqual(response.data['total_frogs'], 1)
        self.assertEqual(response.data['completed_frogs'], 1)
        self.assertEqual(response.data['frog_completion_rate'], 100.0)


class FocusWizardViewTest(TestCase):
    """Test Focus Wizard page"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
    
    def test_wizard_requires_login(self):
        """Test wizard requires authentication"""
        self.client.logout()
        url = reverse('focus_wizard')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_wizard_renders(self):
        """Test wizard page renders correctly"""
        url = reverse('focus_wizard')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Executive Focus Wizard')
        self.assertContains(response, 'Brain Dump')
        self.assertContains(response, '80/20 Filter')
        self.assertContains(response, 'The Frog')
        self.assertContains(response, 'Battle Plan')


class CalendarFeedTest(TestCase):
    """Test iCal calendar feed generation"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        session = DailyFocusSession.objects.create(
            user=self.user,
            date=timezone.localdate(),
            energy_level=7
        )
        
        # Create a frog task with schedule
        FocusTask.objects.create(
            session=session,
            title="My Frog Task",
            description="This is the most important task",
            is_high_impact=True,
            impact_reason="Will unlock major revenue",
            is_frog=True,
            checklist=[
                {"text": "Step 1", "done": False},
                {"text": "Step 2", "done": True}
            ],
            scheduled_start=timezone.now() + timedelta(days=1, hours=9),
            scheduled_end=timezone.now() + timedelta(days=1, hours=11)
        )
    
    def test_calendar_feed_generates(self):
        """Test that calendar feed generates without errors"""
        url = reverse('focus-calendar-feed', kwargs={'user_token': self.user.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/calendar; charset=utf-8')
        
        # Check content includes calendar data
        content = response.content.decode('utf-8')
        self.assertIn('BEGIN:VCALENDAR', content)
        self.assertIn('BEGIN:VEVENT', content)
        self.assertIn('🐸 My Frog Task', content)
        self.assertIn('END:VCALENDAR', content)
    
    def test_invalid_token_returns_404(self):
        """Test invalid token returns 404"""
        url = reverse('focus-calendar-feed', kwargs={'user_token': 99999})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 404)
