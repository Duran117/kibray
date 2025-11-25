import pytest
from datetime import date
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from core.models import Project, Task, Employee

User = get_user_model()

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def user(db):
    return User.objects.create_user(username='pm_board', password='pass123', email='pm_board@example.com')

@pytest.fixture
def employee(db, user):
    return Employee.objects.create(
        user=user,
        first_name='Ana',
        last_name='Pérez',
        social_security_number='555-12-3456',
        hourly_rate='25.00'
    )

@pytest.fixture
def project(db):
    return Project.objects.create(name='Board Project', client='ACME', start_date=date.today())

@pytest.mark.django_db
class TestTouchupBoardAPI:
    def test_board_grouping_and_project_filter(self, api_client, user, project, employee):
        api_client.force_authenticate(user=user)
        other_project = Project.objects.create(name='Other', client='X', start_date=date.today())
        # Create touch-ups for project
        t1 = Task.objects.create(project=project, title='TU 1', is_touchup=True, status='Pendiente', priority='high', assigned_to=employee)
        t2 = Task.objects.create(project=project, title='TU 2', is_touchup=True, status='En Progreso', priority='medium')
        t3 = Task.objects.create(project=project, title='TU 3', is_touchup=True, status='Completada', priority='low')
        # Non-touchup and other project touchup
        Task.objects.create(project=project, title='Normal', is_touchup=False, status='Pendiente')
        Task.objects.create(project=other_project, title='Other TU', is_touchup=True, status='Pendiente')

        res = api_client.get('/api/v1/tasks/touchup_board/', {'project': project.id})
        assert res.status_code == 200
        cols = res.data['columns']
        # Expect 3 columns in fixed order
        keys = [c['key'] for c in cols]
        assert keys == ['Pendiente', 'En Progreso', 'Completada']
        # Counts
        totals = res.data['totals']
        assert totals['pending'] == 1
        assert totals['in_progress'] == 1
        assert totals['completed'] == 1
        assert totals['total'] == 3
        # Verify items belong to project and are touchups
        for col in cols:
            for item in col['items']:
                assert item['project'] == project.id
                assert item['is_touchup'] is True

    def test_board_assigned_to_me_filter(self, api_client, user, project, employee):
        api_client.force_authenticate(user=user)
        # Touch-ups: one assigned to employee (linked to user), one unassigned
        t1 = Task.objects.create(project=project, title='Mine', is_touchup=True, status='Pendiente', assigned_to=employee)
        t2 = Task.objects.create(project=project, title='Not mine', is_touchup=True, status='Pendiente')
        res = api_client.get('/api/v1/tasks/touchup_board/', {'project': project.id, 'assigned_to_me': 'true'})
        assert res.status_code == 200
        cols = res.data['columns']
        # All tasks in board should be assigned to current user's employee
        found_ids = [it['id'] for c in cols for it in c['items']]
        assert t1.id in found_ids
        assert t2.id not in found_ids
