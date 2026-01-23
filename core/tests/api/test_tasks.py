"""
API Tests for Tasks
"""
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from core.models import Task, Project, Employee, ClientOrganization, ClientContact


class TaskAPITestCase(APITestCase):
    """Test case for Task API endpoints"""
    
    def setUp(self):
        """Set up test data"""
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        # Create organization and contact
        self.org = ClientOrganization.objects.create(
            name='Test Org',
            billing_email='org@test.com',
            billing_address='456 Test Ave',
            is_active=True
        )
        self.contact = ClientContact.objects.create(
            organization=self.org,
            user=self.user
        )
        
        # Create test project
        self.project = Project.objects.create(
            name='Test Project',
            project_lead=self.contact,
            start_date='2024-01-01',
            end_date='2024-12-31'
        )
        
        # Create employee
        self.employee = Employee.objects.create(
            user=self.user,
            first_name='Test',
            last_name='Employee',
            social_security_number='123-45-6789',
            hourly_rate=25.00,
            is_active=True
        )
        
        # Create test task
        self.task = Task.objects.create(
            project=self.project,
            title='Test Task',
            description='Test Description',
            status='Pending',
            priority='medium',
            due_date=timezone.now().date() + timezone.timedelta(days=7),
            created_by=self.user,
            assigned_to=self.employee
        )
        
        # Obtain JWT token
        response = self.client.post(
            reverse('token_obtain_pair'),
            {'username': 'testuser', 'password': 'testpass123'},
            format='json'
        )
        self.token = response.data.get('access')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
    
    def test_list_tasks(self):
        """Test listing tasks"""
        url = reverse('task-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data['results']), 1)
    
    def test_create_task(self):
        """Test creating a new task"""
        url = reverse('task-list')
        data = {
            'project': self.project.id,
            'title': 'New Task',
            'description': 'New Description',
            'status': 'Pending',
            'priority': 'high',
            'due_date': (timezone.now().date() + timezone.timedelta(days=10)).isoformat(),
            'assigned_to': self.employee.id
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Task.objects.count(), 2)
    
    def test_update_task(self):
        """Test updating a task"""
        url = reverse('task-detail', kwargs={'pk': self.task.pk})
        data = {'title': 'Updated Task'}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.task.refresh_from_db()
        self.assertEqual(self.task.title, 'Updated Task')
    
    def test_my_tasks(self):
        """Test getting tasks assigned to current user"""
        url = reverse('task-my-tasks')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_overdue_tasks(self):
        """Test getting overdue tasks"""
        url = reverse('task-overdue')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_filter_by_status(self):
        """Test filtering tasks by status"""
        url = f"{reverse('task-list')}?status=Pending"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_update_status_action(self):
        """Test update_status action"""
        url = reverse('task-update-status', kwargs={'pk': self.task.pk})
        data = {'status': 'Completed'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, 'Completed')
