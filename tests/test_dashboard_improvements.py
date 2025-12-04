"""
Tests para las mejoras del dashboard:
- Morning Briefing
- Quick View Modals
- Action Categorization
- Filter Functionality
"""
import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from core.models import TimeEntry, MaterialRequest, Issue, RFI, Project, Employee, ChangeOrder
from datetime import date, time

User = get_user_model()


@pytest.fixture
def staff_user(db):
    """Usuario staff para PM dashboard"""
    return User.objects.create_user(
        username="pm_user",
        email="pm@test.com",
        password="pm123",
        is_staff=True,
        is_superuser=False,
    )


@pytest.fixture
def admin_user(db):
    """Usuario admin para admin dashboard"""
    return User.objects.create_user(
        username="admin_user",
        email="admin@test.com",
        password="admin123",
        is_staff=True,
        is_superuser=True,
    )


@pytest.fixture
def test_project(db):
    """Proyecto de prueba"""
    return Project.objects.create(
        name="Test Project",
        start_date=date.today(),
        is_archived=False
    )


@pytest.fixture
def test_employee(db, staff_user):
    """Empleado vinculado a usuario staff"""
    return Employee.objects.create(
        user=staff_user,
        first_name="PM",
        last_name="Test",
        hourly_rate=25.0
    )


class TestMorningBriefingPM:
    """Tests para Morning Briefing en PM Dashboard"""
    
    def test_morning_briefing_appears_on_pm_dashboard(self, client, staff_user):
        """El Morning Briefing debe aparecer en el PM dashboard"""
        client.force_login(staff_user)
        response = client.get(reverse('dashboard_pm'))
        
        assert response.status_code == 200
        assert 'morning_briefing' in response.context
        assert isinstance(response.context['morning_briefing'], list)
    
    def test_morning_briefing_shows_unassigned_time(self, client, staff_user, test_project, test_employee):
        """Briefing debe mostrar time entries sin CO"""
        # Crear time entry sin change order
        TimeEntry.objects.create(
            employee=test_employee,
            project=test_project,
            date=date.today(),
            start_time=time(8, 0),
            end_time=time(12, 0),
            change_order=None  # Sin CO
        )
        
        client.force_login(staff_user)
        response = client.get(reverse('dashboard_pm'))
        
        briefing = response.context['morning_briefing']
        assert len(briefing) > 0
        
        # Buscar item de unassigned time
        unassigned_items = [item for item in briefing if 'unassigned time' in item['text'].lower() or 'sin change order' in item['text'].lower()]
        assert len(unassigned_items) == 1
        # El action_label puede estar en español o inglés dependiendo del idioma activo
        assert 'Assign' in unassigned_items[0]['action_label'] or 'Asignar' in unassigned_items[0]['action_label']
        assert unassigned_items[0]['category'] == 'problems'
    
    def test_morning_briefing_severity_thresholds(self, client, staff_user, test_project, test_employee):
        """Severity debe cambiar según umbrales"""
        # Crear 6 time entries sin CO (>= 5 = danger)
        for i in range(6):
            TimeEntry.objects.create(
                employee=test_employee,
                project=test_project,
                date=date.today(),
                start_time=time(i, 0),
                end_time=time(i, 30),
                change_order=None
            )
        
        client.force_login(staff_user)
        response = client.get(reverse('dashboard_pm'))
        
        briefing = response.context['morning_briefing']
        unassigned_items = [item for item in briefing if 'unassigned time' in item['text'].lower() or 'sin change order' in item['text'].lower()]
        
        assert len(unassigned_items) == 1
        assert unassigned_items[0]['severity'] == 'danger'  # >= 5 = danger


class TestMorningBriefingAdmin:
    """Tests para Morning Briefing en Admin Dashboard"""
    
    def test_morning_briefing_appears_on_admin_dashboard(self, client, admin_user):
        """El Morning Briefing debe aparecer en el Admin dashboard"""
        client.force_login(admin_user)
        response = client.get(reverse('dashboard_admin'))
        
        assert response.status_code == 200
        assert 'morning_briefing' in response.context
        assert isinstance(response.context['morning_briefing'], list)
    
    def test_morning_briefing_shows_pending_cos(self, client, admin_user, test_project):
        """Briefing debe mostrar COs pendientes"""
        # Crear 2 COs pendientes
        ChangeOrder.objects.create(
            project=test_project,
            description="Test CO 1",
            status="pending"
        )
        ChangeOrder.objects.create(
            project=test_project,
            description="Test CO 2",
            status="pending"
        )
        
        client.force_login(admin_user)
        response = client.get(reverse('dashboard_admin'))
        
        briefing = response.context['morning_briefing']
        co_items = [item for item in briefing if 'change orders' in item['text'].lower() or 'esperando aprobación' in item['text'].lower()]
        
        assert len(co_items) == 1
        assert 'awaiting approval' in co_items[0]['text'].lower() or 'esperando aprobación' in co_items[0]['text'].lower()
        # El action_label puede estar en español o inglés
        assert 'Approve' in co_items[0]['action_label'] or 'Aprobar' in co_items[0]['action_label'] or 'Aprobado' in co_items[0]['action_label']


class TestFilterFunctionality:
    """Tests para filtros de dashboard"""
    
    def test_filter_all_shows_all_categories(self, client, staff_user):
        """Filtro 'all' debe mostrar todas las categorías"""
        client.force_login(staff_user)
        response = client.get(reverse('dashboard_pm') + '?filter=all')
        
        assert response.status_code == 200
        assert response.context['active_filter'] == 'all'
        # El template debe renderizar todas las categorías
        content = response.content.decode()
        assert 'Planning' in content
        assert 'Operations' in content
        assert 'Documents & Plans' in content
    
    def test_filter_problems_only_shows_problems(self, client, staff_user, test_project, test_employee):
        """Filtro 'problems' debe filtrar briefing items"""
        # Crear time entry sin CO (problema)
        TimeEntry.objects.create(
            employee=test_employee,
            project=test_project,
            date=date.today(),
            start_time=time(8, 0),
            end_time=time(12, 0),
            change_order=None
        )
        
        # Crear material request (approval, no problema)
        MaterialRequest.objects.create(
            project=test_project,
            requested_by=staff_user,
            status="pending"
        )
        
        client.force_login(staff_user)
        response = client.get(reverse('dashboard_pm') + '?filter=problems')
        
        assert response.status_code == 200
        assert response.context['active_filter'] == 'problems'
        
        briefing = response.context['morning_briefing']
        # Solo deben aparecer items con category='problems'
        for item in briefing:
            assert item['category'] == 'problems'
    
    def test_filter_approvals_only_shows_approvals(self, client, staff_user, test_project):
        """Filtro 'approvals' debe filtrar briefing items"""
        # Crear material request (approval)
        MaterialRequest.objects.create(
            project=test_project,
            requested_by=staff_user,
            status="pending"
        )
        
        client.force_login(staff_user)
        response = client.get(reverse('dashboard_pm') + '?filter=approvals')
        
        assert response.status_code == 200
        assert response.context['active_filter'] == 'approvals'
        
        briefing = response.context['morning_briefing']
        # Solo deben aparecer items con category='approvals'
        for item in briefing:
            assert item['category'] == 'approvals'
    
    def test_filter_buttons_highlight_active(self, client, staff_user):
        """Los botones de filtro deben indicar el filtro activo"""
        client.force_login(staff_user)
        response = client.get(reverse('dashboard_pm') + '?filter=problems')
        
        content = response.content.decode()
        # El botón activo debe tener clases diferentes
        assert 'border-red-500' in content  # Active state for problems button


class TestQuickViewModal:
    """Tests para Quick View modals"""
    
    def test_briefing_items_have_modal_data(self, client, staff_user, test_project, test_employee):
        """Cada item del briefing debe tener datos para el modal"""
        TimeEntry.objects.create(
            employee=test_employee,
            project=test_project,
            date=date.today(),
            start_time=time(8, 0),
            end_time=time(12, 0),
            change_order=None
        )
        
        client.force_login(staff_user)
        response = client.get(reverse('dashboard_pm'))
        
        briefing = response.context['morning_briefing']
        for item in briefing:
            # Cada item debe tener los campos necesarios para el modal
            assert 'text' in item
            assert 'action_url' in item
            assert 'action_label' in item
            assert 'severity' in item


class TestActionCategorization:
    """Tests para categorización de acciones"""
    
    def test_pm_dashboard_has_categorized_actions(self, client, staff_user):
        """PM dashboard debe tener acciones categorizadas"""
        client.force_login(staff_user)
        response = client.get(reverse('dashboard_pm'))
        
        content = response.content.decode()
        
        # Verificar que existen las categorías
        assert 'Planning' in content
        assert 'Operations' in content
        assert 'Documents & Plans' in content
    
    def test_admin_dashboard_has_categorized_actions(self, client, admin_user):
        """Admin dashboard debe tener acciones categorizadas"""
        client.force_login(admin_user)
        response = client.get(reverse('dashboard_admin'))
        
        content = response.content.decode()
        
        # Verificar que existen las categorías
        assert 'Approvals & Actions' in content
        assert 'Finance' in content
        assert 'Planning & Analytics' in content
        assert 'Project Management' in content


class TestBriefingItemStructure:
    """Tests para estructura de items del briefing"""
    
    def test_briefing_item_has_required_fields(self, client, staff_user, test_project, test_employee):
        """Cada item del briefing debe tener estructura correcta"""
        TimeEntry.objects.create(
            employee=test_employee,
            project=test_project,
            date=date.today(),
            start_time=time(8, 0),
            end_time=time(12, 0),
            change_order=None
        )
        
        client.force_login(staff_user)
        response = client.get(reverse('dashboard_pm'))
        
        briefing = response.context['morning_briefing']
        
        for item in briefing:
            # Verificar estructura del dict
            assert isinstance(item, dict)
            assert 'text' in item
            assert 'severity' in item
            assert 'action_url' in item
            assert 'action_label' in item
            assert 'category' in item
            
            # Verificar valores válidos
            assert item['severity'] in ['danger', 'warning', 'info']
            assert item['category'] in ['problems', 'approvals']
            # Los textos pueden ser strings o lazy translations, verificar que tengan contenido
            assert item['text']
            assert item['action_url']
            assert item['action_label']
