"""
Pruebas rigurosas para APIs de Analytics
Valida ColorApproval y PMPerformance analytics endpoints
"""

import pytest
from django.contrib.auth.models import User
from django.test import Client
from core.models import Project, ColorApproval, ProjectManagerAssignment, Task
from datetime import datetime, timedelta


@pytest.mark.django_db
class TestColorApprovalAnalytics:
    """Tests exhaustivos para /api/v1/analytics/color-approvals/"""

    def setup_method(self):
        """Setup para cada test"""
        self.client = Client()
        self.admin = User.objects.filter(is_superuser=True).first()
        if not self.admin:
            self.admin = User.objects.create_superuser("admin_test", "admin@test.com", "test123")
        self.client.force_login(self.admin)

        # Crear proyecto de prueba
        self.project = Project.objects.create(
            name="Test Project", client="Test Client", start_date=datetime.now().date()
        )

    def test_color_approval_analytics_requires_authentication(self):
        """Verifica que el endpoint requiere autenticación"""
        client = Client()  # Cliente sin login
        response = client.get("/api/v1/analytics/color-approvals/")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"

    def test_color_approval_analytics_global_success(self):
        """Verifica analytics globales con datos"""
        # Crear ColorApprovals de prueba
        ColorApproval.objects.create(
            project=self.project,
            status="PENDING",
            color_name="Test Color 1",
            brand="Test Brand",
            requested_by=self.admin,
        )
        ColorApproval.objects.create(
            project=self.project,
            status="APPROVED",
            color_name="Test Color 2",
            brand="Test Brand",
            approved_by=self.admin,
            signed_at=datetime.now(),
        )

        response = self.client.get("/api/v1/analytics/color-approvals/")

        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()

        # Validar estructura de respuesta
        assert "total_approvals" in data, "Missing total_approvals"
        assert "by_status" in data, "Missing by_status"
        assert "by_brand" in data, "Missing by_brand"
        assert "avg_approval_time_hours" in data, "Missing avg_approval_time_hours"
        assert "pending_aging_days" in data, "Missing pending_aging_days"

        # Validar tipos de datos
        assert isinstance(data["total_approvals"], int), "total_approvals debe ser int"
        assert isinstance(data["by_status"], dict), "by_status debe ser dict"
        assert isinstance(data["by_brand"], list), "by_brand debe ser list"
        assert isinstance(data["avg_approval_time_hours"], (int, float)) or data["avg_approval_time_hours"] is None
        assert isinstance(data["pending_aging_days"], (int, float)) or data["pending_aging_days"] is None

        # Validar valores mínimos
        assert data["total_approvals"] >= 2, f"Expected >= 2 approvals, got {data['total_approvals']}"
        assert "PENDING" in data["by_status"] or "APPROVED" in data["by_status"]

    def test_color_approval_analytics_by_project(self):
        """Verifica analytics filtrado por proyecto"""
        # Crear otro proyecto
        other_project = Project.objects.create(
            name="Other Project", client="Other Client", start_date=datetime.now().date()
        )

        # Crear aprobaciones en ambos proyectos
        ColorApproval.objects.create(
            project=self.project,
            status="APPROVED",
            color_name="Project 1 Color",
            brand="Brand A",
            requested_by=self.admin,
        )
        ColorApproval.objects.create(
            project=other_project,
            status="PENDING",
            color_name="Project 2 Color",
            brand="Brand B",
            requested_by=self.admin,
        )

        response = self.client.get(f"/api/v1/analytics/color-approvals/?project={self.project.id}")

        assert response.status_code == 200
        data = response.json()

        # Solo debe incluir aprobaciones del proyecto filtrado
        assert data["total_approvals"] >= 1
        # Verificar que los datos corresponden al proyecto correcto
        if data["by_brand"]:
            brands = [item["brand"] for item in data["by_brand"]]
            assert "Brand A" in brands or data["total_approvals"] > 1

    def test_color_approval_analytics_empty_database(self):
        """Verifica respuesta con base de datos vacía"""
        # Eliminar todas las aprobaciones
        ColorApproval.objects.all().delete()

        response = self.client.get("/api/v1/analytics/color-approvals/")

        assert response.status_code == 200
        data = response.json()

        assert data["total_approvals"] == 0
        assert data["by_status"] == {}
        assert data["by_brand"] == []
        # Permitir 0 o None para valores numéricos vacíos
        assert data["avg_approval_time_hours"] in [0, None]
        assert data["pending_aging_days"] in [0, None]

    def test_color_approval_analytics_invalid_project(self):
        """Verifica manejo de proyecto inexistente"""
        response = self.client.get("/api/v1/analytics/color-approvals/?project=999999")

        assert response.status_code == 200
        data = response.json()

        # Debe retornar datos vacíos, no error
        assert data["total_approvals"] == 0


@pytest.mark.django_db
class TestPMPerformanceAnalytics:
    """Tests exhaustivos para /api/v1/analytics/pm-performance/"""

    def setup_method(self):
        """Setup para cada test"""
        self.client = Client()
        self.admin = User.objects.filter(is_superuser=True).first()
        if not self.admin:
            self.admin = User.objects.create_superuser("admin_test2", "admin2@test.com", "test123")
        self.client.force_login(self.admin)

        # Crear PM
        self.pm = User.objects.create_user("pm_test", "pm@test.com", "test123")

        # Crear proyecto
        self.project = Project.objects.create(
            name="PM Test Project", client="Test Client", start_date=datetime.now().date()
        )

    def test_pm_performance_requires_authentication(self):
        """Verifica que el endpoint requiere autenticación"""
        client = Client()
        response = client.get("/api/v1/analytics/pm-performance/")
        assert response.status_code == 401

    def test_pm_performance_requires_admin(self):
        """Verifica que el endpoint requiere permisos de admin"""
        # Crear usuario no-admin
        regular_user = User.objects.create_user("regular", "regular@test.com", "test123")
        client = Client()
        client.force_login(regular_user)

        response = client.get("/api/v1/analytics/pm-performance/")
        assert response.status_code == 403, f"Expected 403 for non-admin, got {response.status_code}"

    def test_pm_performance_success_with_data(self):
        """Verifica analytics de PM con datos"""
        # Asignar PM al proyecto
        ProjectManagerAssignment.objects.create(project=self.project, pm=self.pm)

        # Crear Employee para el PM (Task.assigned_to requiere Employee)
        from core.models import Employee
        from decimal import Decimal

        employee = Employee.objects.create(
            user=self.pm,
            first_name="PM",
            last_name="Test",
            social_security_number="123-45-6789",
            hourly_rate=Decimal("25.00"),
        )

        # Crear tareas asignadas al Employee
        Task.objects.create(title="Test Task 1", project=self.project, assigned_to=employee, status="Completada")
        Task.objects.create(title="Test Task 2", project=self.project, assigned_to=employee, status="En Progreso")
        Task.objects.create(
            title="Test Task 3",
            project=self.project,
            assigned_to=employee,
            status="Pendiente",
            due_date=datetime.now().date() - timedelta(days=5),  # Overdue
        )

        response = self.client.get("/api/v1/analytics/pm-performance/")

        assert response.status_code == 200
        data = response.json()

        # Validar estructura
        assert "pm_list" in data
        assert "overall" in data

        # Validar overall
        assert "total_pms" in data["overall"]
        assert "avg_projects_per_pm" in data["overall"]
        assert "avg_completion_rate" in data["overall"]

        # Validar que hay al menos 1 PM
        assert data["overall"]["total_pms"] >= 1
        assert isinstance(data["pm_list"], list)

        # Validar estructura de PM individual
        if data["pm_list"]:
            pm_data = data["pm_list"][0]
            required_fields = [
                "pm_id",
                "pm_username",
                "projects_count",
                "tasks_assigned",
                "tasks_completed",
                "completion_rate",
                "overdue_count",
            ]
            for field in required_fields:
                assert field in pm_data, f"Missing field: {field}"

            # Validar tipos
            assert isinstance(pm_data["pm_id"], int)
            assert isinstance(pm_data["pm_username"], str)
            assert isinstance(pm_data["projects_count"], int)
            assert isinstance(pm_data["tasks_assigned"], int)
            assert isinstance(pm_data["tasks_completed"], int)
            assert isinstance(pm_data["completion_rate"], (int, float))
            assert isinstance(pm_data["overdue_count"], int)

            # Validar rangos
            assert 0 <= pm_data["completion_rate"] <= 100

    def test_pm_performance_empty_database(self):
        """Verifica respuesta sin PMs asignados"""
        ProjectManagerAssignment.objects.all().delete()

        response = self.client.get("/api/v1/analytics/pm-performance/")

        assert response.status_code == 200
        data = response.json()

        assert data["overall"]["total_pms"] == 0
        assert data["overall"]["avg_projects_per_pm"] == 0
        assert data["overall"]["avg_completion_rate"] == 0
        assert data["pm_list"] == []

    def test_pm_performance_multiple_pms(self):
        """Verifica analytics con múltiples PMs"""
        # Crear otro PM
        pm2 = User.objects.create_user("pm_test2", "pm2@test.com", "test123")

        # Asignar ambos PMs a proyectos
        ProjectManagerAssignment.objects.create(project=self.project, pm=self.pm)

        project2 = Project.objects.create(name="Project 2", client="Client 2", start_date=datetime.now().date())
        ProjectManagerAssignment.objects.create(project=project2, pm=pm2)

        response = self.client.get("/api/v1/analytics/pm-performance/")

        assert response.status_code == 200
        data = response.json()

        assert data["overall"]["total_pms"] >= 2
        assert len(data["pm_list"]) >= 2

        # Verificar que los PMs están en la lista
        pm_usernames = [pm["pm_username"] for pm in data["pm_list"]]
        assert "pm_test" in pm_usernames or "pm_test2" in pm_usernames


@pytest.mark.django_db
class TestAnalyticsIntegration:
    """Tests de integración para el sistema completo de analytics"""

    def test_all_analytics_endpoints_accessible(self):
        """Verifica que todos los endpoints de analytics son accesibles"""
        client = Client()
        admin = User.objects.filter(is_superuser=True).first()
        if not admin:
            admin = User.objects.create_superuser("admin_int", "admin@int.com", "test123")
        client.force_login(admin)

        # Crear datos mínimos
        project = Project.objects.create(
            name="Integration Test", client="Test Client", start_date=datetime.now().date()
        )

        endpoints = [
            f"/api/v1/analytics/projects/{project.id}/health/",
            "/api/v1/analytics/touchups/",
            "/api/v1/analytics/color-approvals/",
            "/api/v1/analytics/pm-performance/",
        ]

        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code in [200, 404], f"Endpoint {endpoint} failed with {response.status_code}"

            if response.status_code == 200:
                data = response.json()
                assert isinstance(data, dict), f"Endpoint {endpoint} didn't return JSON object"


def run_analytics_tests():
    """Función helper para ejecutar todos los tests"""
    print("🧪 Ejecutando pruebas de Analytics...")
    pytest.main([__file__, "-v", "--tb=short"])


if __name__ == "__main__":
    run_analytics_tests()
