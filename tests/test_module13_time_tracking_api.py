"""
Module 13: Time Tracking & Variance Analytics

Covers:
- TimeEntry API: create with start/end times computes hours; stop action
- Summary endpoint: aggregate hours by project/task/employee
- PlannedActivity variance: uses estimated vs actual (from converted_task time entries)
- DailyPlan recompute_actual_hours: sums hours from linked tasks' time entries
"""
import pytest
from datetime import date, time, timedelta
from decimal import Decimal
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from core.models import Project, Employee, Task, DailyPlan, PlannedActivity, TimeEntry

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    return User.objects.create_user(username='pm13', password='pass123', email='pm13@example.com')


@pytest.fixture
def employee(db):
    return Employee.objects.create(
        first_name='Ana', last_name='Lopez', social_security_number='999-11-2222', hourly_rate='25.00'
    )


@pytest.fixture
def project(db):
    return Project.objects.create(name='TT Project', client='ACME', start_date=date.today())


@pytest.mark.django_db
class TestTimeEntryAPI:
    def test_create_time_entry_computes_hours(self, api_client, user, employee, project):
        api_client.force_authenticate(user=user)
        payload = {
            'employee': employee.id,
            'project': project.id,
            'date': date.today().isoformat(),
            'start_time': '08:00:00',
            'end_time': '13:30:00'  # crosses lunch window; 5.5h - 0.5 lunch = 5.0h
        }
        res = api_client.post('/api/v1/time-entries/', payload, format='json')
        assert res.status_code == 201
        assert res.data['hours_worked'] in ['5.00', 5.0]

    def test_stop_action_sets_end_and_hours(self, api_client, user, employee, project):
        api_client.force_authenticate(user=user)
        # Create open entry
        payload = {
            'employee': employee.id,
            'project': project.id,
            'date': date.today().isoformat(),
            'start_time': '14:00:00'
        }
        res = api_client.post('/api/v1/time-entries/', payload, format='json')
        assert res.status_code == 201
        entry_id = res.data['id']
        # Stop at 18:30
        stop_res = api_client.post(f'/api/v1/time-entries/{entry_id}/stop/', {'end_time': '18:30:00'}, format='json')
        assert stop_res.status_code == 200
        assert stop_res.data['hours_worked'] in ['4.50', 4.5]

    def test_summary_by_task(self, api_client, user, employee, project):
        api_client.force_authenticate(user=user)
        # Create a task and time entries
        task = Task.objects.create(project=project, title='Paint', status='Pendiente', priority='medium', created_by=user)
        TimeEntry.objects.create(employee=employee, project=project, task=task, date=date.today(), start_time=time(8,0), end_time=time(12,0))
        TimeEntry.objects.create(employee=employee, project=project, task=task, date=date.today(), start_time=time(13,0), end_time=time(15,0))
        res = api_client.get('/api/v1/time-entries/summary/?group=task&project=' + str(project.id))
        assert res.status_code == 200
        assert any(row['task'] == task.id and Decimal(row['total_hours']) == Decimal('6.00') for row in res.data)


@pytest.mark.django_db
class TestVarianceAndPlanRollup:
    def test_planned_activity_variance_via_converted_task(self, api_client, user, employee, project):
        api_client.force_authenticate(user=user)
        plan = DailyPlan.objects.create(project=project, plan_date=date.today()+timedelta(days=1), completion_deadline=date.today())
        act = PlannedActivity.objects.create(daily_plan=plan, title='Prep', estimated_hours=Decimal('4.00'))
        # Convert to task
        task = Task.objects.create(project=project, title='Prep', status='Pendiente', priority='medium', created_by=user)
        act.converted_task = task
        act.save()
        # Time entries totaling 3.50h
        TimeEntry.objects.create(employee=employee, project=project, task=task, date=date.today(), start_time=time(8,0), end_time=time(10,0))
        TimeEntry.objects.create(employee=employee, project=project, task=task, date=date.today(), start_time=time(10,30), end_time=time(12,0))
        # Variance endpoint
        res = api_client.get(f'/api/v1/planned-activities/{act.id}/variance/')
        assert res.status_code == 200
        assert res.data['variance_hours'] in [0.5, 0.50]  # 4.0 - 3.5 = 0.5
        assert res.data['is_efficient'] is True

    def test_daily_plan_recompute_actual_hours(self, api_client, user, employee, project):
        api_client.force_authenticate(user=user)
        plan = DailyPlan.objects.create(project=project, plan_date=date.today()+timedelta(days=1), completion_deadline=date.today(), estimated_hours_total=Decimal('8.00'))
        # Activities and tasks
        act1 = PlannedActivity.objects.create(daily_plan=plan, title='Walls', estimated_hours=Decimal('3.00'))
        act2 = PlannedActivity.objects.create(daily_plan=plan, title='Ceiling', estimated_hours=Decimal('5.00'))
        t1 = Task.objects.create(project=project, title='Walls', status='Pendiente', priority='medium', created_by=user)
        t2 = Task.objects.create(project=project, title='Ceiling', status='Pendiente', priority='medium', created_by=user)
        act1.converted_task = t1; act1.save()
        act2.converted_task = t2; act2.save()
        # Time entries sum to 7.00
        TimeEntry.objects.create(employee=employee, project=project, task=t1, date=date.today(), start_time=time(8,0), end_time=time(11,0))  # 3h
        TimeEntry.objects.create(employee=employee, project=project, task=t2, date=date.today(), start_time=time(12,0), end_time=time(16,0)) # 4h
        # Recompute
        res = api_client.post(f'/api/v1/daily-plans/{plan.id}/recompute_actual_hours/')
        assert res.status_code == 200
        assert res.data['actual_hours_worked'] in [7.0, 7, '7.00']
        # Productivity should reflect 8/7*100 ~ 114.3
        prod = api_client.get(f'/api/v1/daily-plans/{plan.id}/productivity/')
        assert prod.status_code == 200
        assert 114.2 <= float(prod.data['productivity_score']) <= 114.4
