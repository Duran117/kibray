"""
Locust Load Testing Script for Kibray API
Run with: locust -f locustfile.py --host=https://yourdomain.com
"""
from locust import HttpUser, task, between
import random
import json


class KibrayUser(HttpUser):
    """
    Simulates a typical Kibray user workflow
    """
    wait_time = between(1, 3)  # Wait 1-3 seconds between tasks
    
    def on_start(self):
        """
        Called when a user starts - performs login
        """
        # Login and get JWT token
        response = self.client.post(
            "/api/v1/auth/login/",
            json={
                "username": "testuser",
                "password": "testpass123"
            },
            catch_response=True,
        )
        
        if response.status_code == 200:
            data = response.json()
            self.token = data.get("access")
            self.headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
            }
            response.success()
        else:
            response.failure(f"Login failed with status {response.status_code}")
            self.headers = {}
    
    @task(3)
    def view_dashboard(self):
        """
        View main dashboard (high frequency task)
        """
        self.client.get(
            "/api/v1/dashboard/",
            headers=self.headers,
            name="/api/v1/dashboard/",
        )
    
    @task(5)
    def list_projects(self):
        """
        List all projects (very high frequency)
        """
        self.client.get(
            "/api/v1/projects/",
            headers=self.headers,
            name="/api/v1/projects/",
        )
    
    @task(2)
    def view_project_detail(self):
        """
        View specific project detail
        """
        project_id = random.randint(1, 50)  # Assuming 50 projects exist
        self.client.get(
            f"/api/v1/projects/{project_id}/",
            headers=self.headers,
            name="/api/v1/projects/[id]/",
        )
    
    @task(4)
    def list_tasks(self):
        """
        List tasks (high frequency)
        """
        self.client.get(
            "/api/v1/tasks/",
            headers=self.headers,
            name="/api/v1/tasks/",
        )
    
    @task(1)
    def create_task(self):
        """
        Create new task (medium frequency)
        """
        self.client.post(
            "/api/v1/tasks/",
            json={
                "title": f"Load Test Task {random.randint(1, 10000)}",
                "description": "Created by load test",
                "status": "pending",
                "priority": random.choice(["low", "medium", "high"]),
                "project": random.randint(1, 10),
            },
            headers=self.headers,
            name="/api/v1/tasks/ [POST]",
        )
    
    @task(2)
    def list_time_entries(self):
        """
        List time entries
        """
        self.client.get(
            "/api/v1/timeentries/",
            headers=self.headers,
            name="/api/v1/timeentries/",
        )
    
    @task(1)
    def create_time_entry(self):
        """
        Create time entry
        """
        self.client.post(
            "/api/v1/timeentries/",
            json={
                "date": "2025-01-15",
                "hours_worked": random.randint(1, 8),
                "description": "Load test entry",
                "project": random.randint(1, 10),
            },
            headers=self.headers,
            name="/api/v1/timeentries/ [POST]",
        )
    
    @task(2)
    def view_schedule(self):
        """
        View schedule/calendar
        """
        self.client.get(
            "/api/v1/schedules/",
            headers=self.headers,
            name="/api/v1/schedules/",
        )
    
    @task(1)
    def search(self):
        """
        Perform search
        """
        search_terms = ["project", "task", "invoice", "payment"]
        term = random.choice(search_terms)
        self.client.get(
            f"/api/v1/search/?q={term}",
            headers=self.headers,
            name="/api/v1/search/",
        )
    
    @task(1)
    def view_analytics(self):
        """
        View analytics/BI data
        """
        self.client.get(
            "/api/v1/bi/",
            headers=self.headers,
            name="/api/v1/bi/",
        )
    
    @task(1)
    def health_check(self):
        """
        Check API health (simulates monitoring)
        """
        self.client.get(
            "/api/v1/health/",
            name="/api/v1/health/",
        )


class AdminUser(HttpUser):
    """
    Simulates admin user with heavier operations
    """
    wait_time = between(2, 5)
    weight = 1  # 1 admin for every 10 regular users
    
    def on_start(self):
        """Login as admin"""
        response = self.client.post(
            "/api/v1/auth/login/",
            json={
                "username": "admin",
                "password": "adminpass123"
            },
            catch_response=True,
        )
        
        if response.status_code == 200:
            data = response.json()
            self.token = data.get("access")
            self.headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
            }
            response.success()
        else:
            response.failure(f"Admin login failed")
            self.headers = {}
    
    @task(2)
    def view_admin_dashboard(self):
        """View admin dashboard"""
        self.client.get(
            "/api/v1/admin-dashboard/",
            headers=self.headers,
            name="/api/v1/admin-dashboard/",
        )
    
    @task(1)
    def export_data(self):
        """Export large dataset (heavy operation)"""
        self.client.get(
            "/api/v1/projects/export/",
            headers=self.headers,
            name="/api/v1/projects/export/",
        )
    
    @task(1)
    def view_analytics_detailed(self):
        """View detailed analytics with date ranges"""
        self.client.get(
            "/api/v1/bi/?start_date=2025-01-01&end_date=2025-12-31",
            headers=self.headers,
            name="/api/v1/bi/ [detailed]",
        )
    
    @task(1)
    def bulk_operations(self):
        """Perform bulk updates"""
        task_ids = [random.randint(1, 100) for _ in range(5)]
        self.client.post(
            "/api/v1/tasks/bulk-update/",
            json={
                "task_ids": task_ids,
                "status": "completed",
            },
            headers=self.headers,
            name="/api/v1/tasks/bulk-update/",
        )


class APIOnlyUser(HttpUser):
    """
    Simulates API-only client (mobile app, integrations)
    """
    wait_time = between(0.5, 2)
    weight = 2  # 2 API users for every 10 regular users
    
    def on_start(self):
        """API authentication"""
        response = self.client.post(
            "/api/v1/auth/login/",
            json={
                "username": "apiuser",
                "password": "apipass123"
            },
        )
        
        if response.status_code == 200:
            data = response.json()
            self.token = data.get("access")
            self.headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
            }
        else:
            self.headers = {}
    
    @task(5)
    def sync_data(self):
        """Frequent data sync"""
        self.client.get(
            "/api/v1/projects/?fields=id,title,status&limit=100",
            headers=self.headers,
            name="/api/v1/projects/ [sync]",
        )
    
    @task(3)
    def push_updates(self):
        """Push updates from mobile"""
        self.client.patch(
            f"/api/v1/tasks/{random.randint(1, 100)}/",
            json={"status": random.choice(["pending", "in_progress", "completed"])},
            headers=self.headers,
            name="/api/v1/tasks/[id]/ [PATCH]",
        )
    
    @task(1)
    def upload_photo(self):
        """Upload photo (heavy operation)"""
        # Simulate file upload
        files = {
            'photo': ('test.jpg', b'fake_image_data' * 100, 'image/jpeg')
        }
        self.client.post(
            "/api/v1/photos/",
            files=files,
            headers={"Authorization": f"Bearer {self.token}"},
            name="/api/v1/photos/ [upload]",
        )
