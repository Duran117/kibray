"""
API Tests for Projects
"""
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from core.models import Project, ClientOrganization, ClientContact


class ProjectAPITestCase(APITestCase):
    """Test case for Project API endpoints"""
    
    def setUp(self):
        """Set up test data"""
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        
        # Create organization
        self.org = ClientOrganization.objects.create(
            name='Test Organization',
            billing_email='org@example.com',
            billing_address='123 Main St',
            billing_phone='555-0100',
            is_active=True
        )
        
        # Create client contact
        self.contact = ClientContact.objects.create(
            organization=self.org,
            user=self.user
        )
        
        # Create test project
        self.project = Project.objects.create(
            name='Test Project',
            project_code='PRJ-2024-0001',
            billing_organization=self.org,
            project_lead=self.contact,
            start_date='2024-01-01',
            end_date='2024-12-31'
        )
        
        # Obtain JWT token
        response = self.client.post(
            reverse('token_obtain_pair'),
            {'username': 'testuser', 'password': 'testpass123'},
            format='json'
        )
        self.token = response.data.get('access')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
    
    def test_list_projects(self):
        """Test listing projects"""
        url = reverse('project-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data['results']), 1)
    
    def test_create_project(self):
        """Test creating a new project"""
        url = reverse('project-list')
        data = {
            'name': 'New Project',
            'project_code': 'PRJ-2024-0002',
            'billing_organization': self.org.id,
            'project_lead': self.contact.id,
            'start_date': '2024-02-01',
            'end_date': '2024-12-31'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Project.objects.count(), 2)
    
    def test_retrieve_project(self):
        """Test retrieving a single project"""
        url = reverse('project-detail', kwargs={'pk': self.project.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Test Project')
    
    def test_update_project(self):
        """Test updating a project"""
        url = reverse('project-detail', kwargs={'pk': self.project.pk})
        data = {'name': 'Updated Project'}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.project.refresh_from_db()
        self.assertEqual(self.project.name, 'Updated Project')
    
    def test_delete_project(self):
        """Test deleting a project"""
        url = reverse('project-detail', kwargs={'pk': self.project.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Project.objects.count(), 0)
    
    def test_assigned_projects(self):
        """Test getting assigned projects"""
        url = reverse('project-assigned-projects')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_filter_by_organization(self):
        """Test filtering projects by organization"""
        url = f"{reverse('project-list')}?billing_organization={self.org.id}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_search_projects(self):
        """Test searching projects"""
        url = f"{reverse('project-list')}?search=Test"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data['results']), 1)
    
    def test_permission_denied_without_auth(self):
        """Test that unauthenticated users cannot access"""
        self.client.credentials()  # Remove authentication
        url = reverse('project-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
