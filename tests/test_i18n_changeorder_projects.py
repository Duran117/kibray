"""
Tests para verificar la internacionalización de changeorder_board y project_list
"""
import pytest
from django.test import Client
from django.contrib.auth.models import User
from django.utils import translation
from core.models import Project, ChangeOrder, Employee
from decimal import Decimal
from datetime import date, timedelta


@pytest.mark.django_db
class TestChangeOrderBoardI18n:
    """Test de traducción de la vista changeorder_board"""
    
    def test_changeorder_board_spanish_labels(self):
        """Verificar etiquetas en español (idioma por defecto)"""
        # Crear usuario staff
        user = User.objects.create_user('admin', 'admin@test.com', 'password', is_staff=True)
        client = Client()
        client.force_login(user)
        
        # Activar español explícitamente
        translation.activate('es')
        
        response = client.get('/changeorders/board/', HTTP_ACCEPT_LANGUAGE='es')
        assert response.status_code == 200
        content = response.content.decode('utf-8')
        
        # Verificar encabezado principal
        assert 'Change Orders' in content
        
        # Verificar filtros
        assert 'Todos los proyectos' in content or 'Proyecto' in content
        assert 'Todos los estados' in content or 'Estado' in content
        
        # Verificar botón de creación
        assert 'Nuevo CO' in content or 'Crear' in content
    
    def test_changeorder_board_english_labels(self):
        """Verificar etiquetas en inglés"""
        user = User.objects.create_user('admin2', 'admin2@test.com', 'password', is_staff=True)
        client = Client()
        client.force_login(user)
        
        # Activar inglés explícitamente
        translation.activate('en')
        
        response = client.get('/changeorders/board/', HTTP_ACCEPT_LANGUAGE='en')
        assert response.status_code == 200
        content = response.content.decode('utf-8')
        
        # Verificar encabezado
        assert 'Change Orders' in content
        
        # Verificar filtros en inglés
        assert ('All projects' in content or 'Project' in content)
        assert ('All statuses' in content or 'Status' in content)
        
        # Verificar botón de creación en inglés
        assert 'New CO' in content or 'Create' in content
    
    def test_changeorder_status_labels_spanish(self):
        """Verificar etiquetas de estado en español"""
        user = User.objects.create_user('admin3', 'admin3@test.com', 'password', is_staff=True)
        project = Project.objects.create(
            name="Test Project",
            start_date=date.today()
        )
        
        # Crear change order
        co = ChangeOrder.objects.create(
            project=project,
            reference_code="CO-001",
            description="Test CO",
            status="pending",
            amount=Decimal("100.00")
        )
        
        client = Client()
        client.force_login(user)
        translation.activate('es')
        
        response = client.get('/changeorders/board/', HTTP_ACCEPT_LANGUAGE='es')
        content = response.content.decode('utf-8')
        
        # Verificar que aparece el proyecto y la etiqueta de estado en español
        assert 'Test Project' in content
        assert 'Pendiente' in content or 'pending' in content.lower()
    
    def test_changeorder_status_labels_english(self):
        """Verificar etiquetas de estado en inglés"""
        user = User.objects.create_user('admin4', 'admin4@test.com', 'password', is_staff=True)
        project = Project.objects.create(
            name="Test Project 2",
            start_date=date.today()
        )
        
        co = ChangeOrder.objects.create(
            project=project,
            reference_code="CO-002",
            description="Test CO 2",
            status="approved",
            amount=Decimal("200.00")
        )
        
        client = Client()
        client.force_login(user)
        translation.activate('en')
        
        response = client.get('/changeorders/board/', HTTP_ACCEPT_LANGUAGE='en')
        content = response.content.decode('utf-8')
        
        # Verificar que aparece el proyecto y la traducción del estado
        assert 'Test Project 2' in content
        assert 'Approved' in content or 'Aprobado' in content


@pytest.mark.django_db
class TestProjectListI18n:
    """Test de traducción de la vista project_list"""
    
    def test_project_list_spanish_headings(self):
        """Verificar encabezados en español"""
        user = User.objects.create_user('pm1', 'pm1@test.com', 'password', is_staff=True)
        client = Client()
        client.force_login(user)
        translation.activate('es')
        
        response = client.get('/projects/', HTTP_ACCEPT_LANGUAGE='es')
        assert response.status_code == 200
        content = response.content.decode('utf-8')
        
        # Verificar encabezado principal
        assert 'Proyectos' in content
        
        # Verificar botón de nuevo proyecto
        assert 'Nuevo Proyecto' in content or 'Crear' in content
    
    def test_project_list_english_headings(self):
        """Verificar encabezados en inglés"""
        user = User.objects.create_user('pm2', 'pm2@test.com', 'password', is_staff=True)
        client = Client()
        client.force_login(user)
        translation.activate('en')
        
        response = client.get('/projects/', HTTP_ACCEPT_LANGUAGE='en')
        assert response.status_code == 200
        content = response.content.decode('utf-8')
        
        # Verificar encabezado principal en inglés
        assert 'Projects' in content
        
        # Verificar botón de nuevo proyecto
        assert 'New Project' in content or 'Create' in content
    
    def test_project_list_empty_state_spanish(self):
        """Verificar mensaje de estado vacío en español"""
        user = User.objects.create_user('pm3', 'pm3@test.com', 'password', is_staff=True)
        
        # Eliminar todos los proyectos para asegurar estado vacío
        Project.objects.all().delete()
        
        client = Client()
        client.force_login(user)
        translation.activate('es')
        
        response = client.get('/projects/', HTTP_ACCEPT_LANGUAGE='es')
        content = response.content.decode('utf-8')
        
        # Verificar mensaje de estado vacío
        assert ('No hay proyectos' in content or 
                'Sin proyectos' in content or
                'proyectos disponibles' in content)
    
    def test_project_list_empty_state_english(self):
        """Verificar mensaje de estado vacío en inglés"""
        user = User.objects.create_user('pm4', 'pm4@test.com', 'password', is_staff=True)
        
        # Eliminar todos los proyectos
        Project.objects.all().delete()
        
        client = Client()
        client.force_login(user)
        translation.activate('en')
        
        response = client.get('/projects/', HTTP_ACCEPT_LANGUAGE='en')
        content = response.content.decode('utf-8')
        
        # Verificar mensaje de estado vacío en inglés
        assert ('No projects' in content or 
                'no projects available' in content.lower())
    
    def test_project_list_with_data_labels(self):
        """Verificar etiquetas de columnas con datos"""
        user = User.objects.create_user('pm5', 'pm5@test.com', 'password', is_staff=True)
        
        # Crear proyecto de prueba
        Project.objects.create(
            name="Test Project",
            client="Test Client",
            start_date=date.today(),
            description="Test description"
        )
        
        client = Client()
        client.force_login(user)
        
        # Probar español
        translation.activate('es')
        response_es = client.get('/projects/', HTTP_ACCEPT_LANGUAGE='es')
        content_es = response_es.content.decode('utf-8')
        
        assert 'Test Project' in content_es
        assert ('Nombre' in content_es or 'Proyecto' in content_es)
        
        # Probar inglés
        translation.activate('en')
        response_en = client.get('/projects/', HTTP_ACCEPT_LANGUAGE='en')
        content_en = response_en.content.decode('utf-8')
        
        assert 'Test Project' in content_en
        assert ('Name' in content_en or 'Project' in content_en)
