import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from core.models import Notification, Project, Employee


@pytest.mark.django_db
class TestNotificationAPIAuthentication:
    """Tests de autenticación para API de notificaciones."""

    def test_notification_list_requires_authentication(self):
        """Verificar que GET /api/v1/notifications/ requiere autenticación."""
        client = APIClient()
        response = client.get("/api/v1/notifications/")
        assert response.status_code == 401, "Debe requerir autenticación"

    def test_count_unread_requires_authentication(self):
        """Verificar que GET /api/v1/notifications/count_unread/ requiere autenticación."""
        client = APIClient()
        response = client.get("/api/v1/notifications/count_unread/")
        assert response.status_code == 401, "Debe requerir autenticación"

    def test_mark_read_requires_authentication(self):
        """Verificar que POST /api/v1/notifications/{id}/mark_read/ requiere autenticación."""
        client = APIClient()
        response = client.post("/api/v1/notifications/1/mark_read/")
        assert response.status_code == 401, "Debe requerir autenticación"

    def test_mark_all_read_requires_authentication(self):
        """Verificar que POST /api/v1/notifications/mark_all_read/ requiere autenticación."""
        client = APIClient()
        response = client.post("/api/v1/notifications/mark_all_read/")
        assert response.status_code == 401, "Debe requerir autenticación"


@pytest.mark.django_db
class TestNotificationAPIFunctionality:
    """Tests de funcionalidad para API de notificaciones."""

    @pytest.fixture
    def user(self):
        """Usuario de prueba."""
        return User.objects.create_user(username="testuser", password="testpass123")

    @pytest.fixture
    def other_user(self):
        """Otro usuario para aislar notificaciones."""
        return User.objects.create_user(username="otheruser", password="testpass123")

    @pytest.fixture
    def client(self, user):
        """Cliente autenticado."""
        client = APIClient()
        client.force_authenticate(user=user)
        return client

    @pytest.fixture
    def notifications(self, user):
        """Crear notificaciones de prueba."""
        return [
            Notification.objects.create(
                user=user,
                notification_type="INFO",
                title=f"Notification {i}",
                message=f"Test message {i}",
                is_read=(i % 2 == 0),  # Alternadas leídas/no leídas
            )
            for i in range(1, 6)
        ]

    def test_notification_list_success(self, client, notifications):
        """Verificar que GET /api/v1/notifications/ retorna notificaciones del usuario."""
        response = client.get("/api/v1/notifications/")
        assert response.status_code == 200
        data = response.json()

        # Validar estructura
        assert isinstance(data, list) or ("results" in data), "Debe ser lista o tener 'results'"
        results = data if isinstance(data, list) else data["results"]
        assert len(results) == 5, "Debe retornar 5 notificaciones"

        # Validar campos obligatorios
        for notif in results:
            assert "id" in notif
            assert "notification_type" in notif
            assert "title" in notif
            assert "message" in notif
            assert "is_read" in notif
            assert "created_at" in notif
            assert isinstance(notif["is_read"], bool)

    def test_notification_list_isolated_by_user(self, client, user, other_user):
        """Verificar que cada usuario solo ve sus propias notificaciones."""
        # Crear notificaciones para ambos usuarios
        Notification.objects.create(user=user, notification_type="INFO", title="User1 Notif", message="Test")
        Notification.objects.create(user=other_user, notification_type="INFO", title="User2 Notif", message="Test")

        response = client.get("/api/v1/notifications/")
        assert response.status_code == 200
        data = response.json()
        results = data if isinstance(data, list) else data["results"]

        # Debe ver solo 1 notificación (la suya)
        assert len(results) == 1
        assert results[0]["title"] == "User1 Notif"

    def test_count_unread_success(self, client, notifications):
        """Verificar que GET /api/v1/notifications/count_unread/ retorna conteo correcto."""
        response = client.get("/api/v1/notifications/count_unread/")
        assert response.status_code == 200
        data = response.json()

        assert "unread_count" in data
        assert isinstance(data["unread_count"], int)
        # 3 no leídas (índices impares: 1, 3, 5)
        assert data["unread_count"] == 3

    def test_count_unread_empty(self, client, user):
        """Verificar conteo con base de datos vacía."""
        response = client.get("/api/v1/notifications/count_unread/")
        assert response.status_code == 200
        data = response.json()
        assert data["unread_count"] == 0

    def test_mark_read_success(self, client, notifications):
        """Verificar que POST /api/v1/notifications/{id}/mark_read/ marca como leída."""
        unread_notif = notifications[0]  # Primera es no leída (índice 1, impar)
        assert not unread_notif.is_read

        response = client.post(f"/api/v1/notifications/{unread_notif.id}/mark_read/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"

        # Verificar en DB
        unread_notif.refresh_from_db()
        assert unread_notif.is_read, "Debe estar marcada como leída"

    def test_mark_read_invalid_notification(self, client):
        """Verificar comportamiento con notificación inexistente."""
        response = client.post("/api/v1/notifications/99999/mark_read/")
        assert response.status_code == 404

    def test_mark_all_read_success(self, client, notifications, user):
        """Verificar que POST /api/v1/notifications/mark_all_read/ marca todas como leídas."""
        # Verificar estado inicial
        unread_count = Notification.objects.filter(user=user, is_read=False).count()
        assert unread_count == 3, "Deben haber 3 no leídas inicialmente"

        response = client.post("/api/v1/notifications/mark_all_read/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"

        # Verificar en DB
        unread_count_after = Notification.objects.filter(user=user, is_read=False).count()
        assert unread_count_after == 0, "Todas deben estar leídas"

        total_count = Notification.objects.filter(user=user).count()
        assert total_count == 5, "Deben seguir existiendo las 5 notificaciones"

    def test_mark_all_read_empty_database(self, client):
        """Verificar mark_all_read con base de datos vacía."""
        response = client.post("/api/v1/notifications/mark_all_read/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"


@pytest.mark.django_db
class TestNotificationDataValidation:
    """Tests de validación de datos retornados."""

    @pytest.fixture
    def user(self):
        return User.objects.create_user(username="testuser", password="testpass123")

    @pytest.fixture
    def client(self, user):
        client = APIClient()
        client.force_authenticate(user=user)
        return client

    @pytest.fixture
    def project(self):
        """Proyecto de prueba para notificaciones relacionadas."""
        return Project.objects.create(name="Test Project", start_date="2025-01-01")

    def test_notification_with_related_object(self, client, user, project):
        """Verificar notificación con objeto relacionado."""
        notif = Notification.objects.create(
            user=user,
            notification_type="PROJECT",
            title="Project Update",
            message="Project has been updated",
            related_object_type="project",
            related_object_id=project.id,
        )

        response = client.get("/api/v1/notifications/")
        assert response.status_code == 200
        data = response.json()
        results = data if isinstance(data, list) else data["results"]

        assert len(results) == 1
        result = results[0]
        assert result["related_object_type"] == "project"
        assert result["related_object_id"] == project.id

    def test_notification_types(self, client, user):
        """Verificar diferentes tipos de notificaciones."""
        types = ["INFO", "WARNING", "ERROR", "SUCCESS", "PROJECT", "TASK", "PAYMENT"]

        for ntype in types:
            Notification.objects.create(
                user=user, notification_type=ntype, title=f"{ntype} notification", message="Test"
            )

        response = client.get("/api/v1/notifications/")
        assert response.status_code == 200
        data = response.json()
        results = data if isinstance(data, list) else data["results"]

        assert len(results) == len(types)
        returned_types = {n["notification_type"] for n in results}
        assert returned_types == set(types)

    def test_notification_ordering(self, client, user):
        """Verificar que notificaciones están ordenadas por created_at DESC."""
        import time

        notifs = []
        for i in range(3):
            notifs.append(
                Notification.objects.create(
                    user=user, notification_type="INFO", title=f"Notification {i}", message="Test"
                )
            )
            time.sleep(0.01)  # Pequeño delay para asegurar orden

        response = client.get("/api/v1/notifications/")
        assert response.status_code == 200
        data = response.json()
        results = data if isinstance(data, list) else data["results"]

        # Debe estar en orden descendente (más reciente primero)
        assert results[0]["title"] == "Notification 2"
        assert results[1]["title"] == "Notification 1"
        assert results[2]["title"] == "Notification 0"


@pytest.mark.django_db
class TestNotificationIntegration:
    """Tests de integración con otros componentes del sistema."""

    @pytest.fixture
    def admin_user(self):
        return User.objects.create_superuser(username="admin", password="admin123", email="admin@test.com")

    @pytest.fixture
    def regular_user(self):
        return User.objects.create_user(username="regular", password="testpass123")

    def test_all_notification_endpoints_accessible(self, admin_user):
        """Verificar que todos los endpoints de notificaciones están accesibles."""
        client = APIClient()
        client.force_authenticate(user=admin_user)

        # Crear notificación de prueba
        notif = Notification.objects.create(user=admin_user, notification_type="INFO", title="Test", message="Test")

        endpoints = [
            ("/api/v1/notifications/", "GET"),
            ("/api/v1/notifications/count_unread/", "GET"),
            (f"/api/v1/notifications/{notif.id}/mark_read/", "POST"),
            ("/api/v1/notifications/mark_all_read/", "POST"),
        ]

        for endpoint, method in endpoints:
            if method == "GET":
                response = client.get(endpoint)
            else:
                response = client.post(endpoint)

            assert response.status_code in [200, 201], f"{method} {endpoint} debe ser accesible"

    def test_notification_isolation_between_users(self, admin_user, regular_user):
        """Verificar aislamiento completo entre usuarios."""
        # Admin crea notificaciones
        admin_notif = Notification.objects.create(
            user=admin_user, notification_type="INFO", title="Admin Notification", message="Admin only"
        )

        # Regular user crea notificaciones
        regular_notif = Notification.objects.create(
            user=regular_user, notification_type="INFO", title="Regular Notification", message="Regular only"
        )

        # Admin client
        admin_client = APIClient()
        admin_client.force_authenticate(user=admin_user)

        # Regular client
        regular_client = APIClient()
        regular_client.force_authenticate(user=regular_user)

        # Admin debe ver solo su notificación
        admin_response = admin_client.get("/api/v1/notifications/")
        admin_data = admin_response.json()
        admin_results = admin_data if isinstance(admin_data, list) else admin_data["results"]
        assert len(admin_results) == 1
        assert admin_results[0]["title"] == "Admin Notification"

        # Regular debe ver solo su notificación
        regular_response = regular_client.get("/api/v1/notifications/")
        regular_data = regular_response.json()
        regular_results = regular_data if isinstance(regular_data, list) else regular_data["results"]
        assert len(regular_results) == 1
        assert regular_results[0]["title"] == "Regular Notification"

        # Regular user no debe poder marcar como leída la notificación del admin
        regular_mark_response = regular_client.post(f"/api/v1/notifications/{admin_notif.id}/mark_read/")
        assert regular_mark_response.status_code == 404, "No debe poder acceder a notificaciones de otros usuarios"
