import pytest
from django.utils import timezone
from django.contrib.auth.models import User
from core.models import Project, DailyPlan, PlannedActivity, InventoryItem, InventoryLocation, ProjectInventory, Employee
from datetime import date, timedelta

@pytest.mark.django_db
def test_daily_plan_overdue_flag():
    user = User.objects.create_user(username='pm1', password='x', email='pm@example.com')
    proj = Project.objects.create(name='Proj A', start_date=date.today())
    plan = DailyPlan.objects.create(
        project=proj,
        plan_date=date.today() + timedelta(days=1),
        created_by=user,
        status='DRAFT',
        completion_deadline=timezone.now() - timedelta(hours=1),
    )
    assert plan.is_overdue() is True
    plan.status = 'SUBMITTED'
    plan.save()
    assert plan.is_overdue() is False

@pytest.mark.django_db
def test_material_check_sufficient():
    user = User.objects.create_user(username='pm2', password='x')
    emp_user = User.objects.create_user(username='e1', password='x')
    emp = Employee.objects.create(user=emp_user, first_name='E', last_name='One', social_security_number='123', hourly_rate=10)
    proj = Project.objects.create(name='Proj B', start_date=date.today())
    plan = DailyPlan.objects.create(project=proj, plan_date=date.today()+timedelta(days=1), created_by=user, completion_deadline=timezone.now()+timedelta(hours=1))
    item = InventoryItem.objects.create(name='Masking Tape', category='MATERIAL', unit='roll')
    storage = InventoryLocation.objects.create(name='Central', project=None, is_storage=True)
    ProjectInventory.objects.create(item=item, location=storage, quantity=5)
    act = PlannedActivity.objects.create(daily_plan=plan, title='Covering windows', order=1, materials_needed=["Masking Tape:3roll"])
    act.assigned_employees.add(emp)
    act.check_materials()
    act.refresh_from_db()
    assert act.materials_checked is True
    assert act.material_shortage is False

@pytest.mark.django_db
def test_material_check_shortage():
    user = User.objects.create_user(username='pm3', password='x')
    proj = Project.objects.create(name='Proj C', start_date=date.today())
    plan = DailyPlan.objects.create(project=proj, plan_date=date.today()+timedelta(days=1), created_by=user, completion_deadline=timezone.now()+timedelta(hours=1))
    InventoryItem.objects.create(name='Roller Cover', category='MATERIAL', unit='unit')
    # No inventory created => zero available
    act = PlannedActivity.objects.create(daily_plan=plan, title='Paint prep', order=1, materials_needed=["Roller Cover:2unit"])
    act.check_materials()
    act.refresh_from_db()
    assert act.materials_checked is True
    assert act.material_shortage is True
