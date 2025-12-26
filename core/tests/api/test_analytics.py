"""
API Tests for Analytics
"""
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from core.models import Project, Task, ChangeOrder, ClientOrganization, ClientContact


class AnalyticsAPITestCase(APITestCase):
    """Test case for Analytics API endpoints"""
    
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
            billing_email='analytics@test.com',
            billing_address='789 Analytics Blvd',
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
            end_date='2024-12-31',
            budget_total=100000,
            total_expenses=50000
        )
        
        # Create tasks
        Task.objects.create(
            project=self.project,
            title='Task 1',
            status='Pendiente',
            priority='high',
            created_by=self.user
        )
        Task.objects.create(
            project=self.project,
            title='Task 2',
            status='Completada',
            priority='medium',
            created_by=self.user
        )
        
        # Create change order
        ChangeOrder.objects.create(
            project=self.project,
            description='Test CO',
            amount=5000,
            status='pending'
        )
        
        # Obtain JWT token
        response = self.client.post(
            reverse('token_obtain_pair'),
            {'username': 'testuser', 'password': 'testpass123'},
            format='json'
        )
        self.token = response.data.get('access')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
    
    def test_get_analytics(self):
        """Test getting global analytics"""
        url = reverse('nav-analytics-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('kpis', response.data)
        self.assertIn('budget_chart', response.data)
        self.assertIn('project_progress', response.data)
        self.assertIn('task_distribution', response.data)
    
    def test_time_range_filter(self):
        """Test analytics with time range filter"""
        url = f"{reverse('nav-analytics-list')}?range=7d"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['time_range'], '7d')
    
    def test_project_analytics(self):
        """Test getting project-specific analytics"""
        url = f"{reverse('nav-analytics-project-analytics')}?project_id={self.project.id}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('project_id', response.data)
        self.assertIn('tasks_summary', response.data)
        self.assertIn('changeorders_summary', response.data)
    
    def test_project_analytics_missing_id(self):
        """Test project analytics without project_id"""
        url = reverse('nav-analytics-project-analytics')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
