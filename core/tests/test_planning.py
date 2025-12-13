from datetime import date, timedelta

import pytest
from django.contrib.auth.models import User
from django.utils import timezone

from core.models import (
    DailyPlan,
    Employee,
    InventoryItem,
    InventoryLocation,
    PlannedActivity,
    Project,
    ProjectInventory,
)


@pytest.mark.django_db
def test_daily_plan_overdue_flag():
    user = User.objects.create_user(username="pm1", password="x", email="pm@example.com")
    proj = Project.objects.create(name="Proj A", start_date=date.today())
    plan = DailyPlan.objects.create(
        project=proj,
        plan_date=date.today() + timedelta(days=1),
        created_by=user,
        status="DRAFT",
        completion_deadline=timezone.now() - timedelta(hours=1),
    )
    assert plan.is_overdue() is True
    plan.status = "SUBMITTED"
    plan.save()
    assert plan.is_overdue() is False


@pytest.mark.django_db
def test_material_check_sufficient():
    user = User.objects.create_user(username="pm2", password="x")
    emp_user = User.objects.create_user(username="e1", password="x")
    emp = Employee.objects.create(
        user=emp_user, first_name="E", last_name="One", social_security_number="123", hourly_rate=10
    )
    proj = Project.objects.create(name="Proj B", start_date=date.today())
    plan = DailyPlan.objects.create(
        project=proj,
        plan_date=date.today() + timedelta(days=1),
        created_by=user,
        completion_deadline=timezone.now() + timedelta(hours=1),
    )
    item = InventoryItem.objects.create(name="Masking Tape", category="MATERIAL", unit="roll")
    storage = InventoryLocation.objects.create(name="Central", project=None, is_storage=True)
    ProjectInventory.objects.create(item=item, location=storage, quantity=5)
    act = PlannedActivity.objects.create(
        daily_plan=plan, title="Covering windows", order=1, materials_needed=["Masking Tape:3roll"]
    )
    act.assigned_employees.add(emp)
    act.check_materials()
    act.refresh_from_db()
    assert act.materials_checked is True
    assert act.material_shortage is False


@pytest.mark.django_db
def test_material_check_shortage():
    user = User.objects.create_user(username="pm3", password="x")
    proj = Project.objects.create(name="Proj C", start_date=date.today())
    plan = DailyPlan.objects.create(
        project=proj,
        plan_date=date.today() + timedelta(days=1),
        created_by=user,
        completion_deadline=timezone.now() + timedelta(hours=1),
    )
    InventoryItem.objects.create(name="Roller Cover", category="MATERIAL", unit="unit")
    # No inventory created => zero available
    act = PlannedActivity.objects.create(
        daily_plan=plan, title="Paint prep", order=1, materials_needed=["Roller Cover:2unit"]
    )
    act.check_materials()
    act.refresh_from_db()
    assert act.materials_checked is True
    assert act.material_shortage is True


# ============================================================================
# PHASE 1 & 2 E2E TESTS: Employee Assignment & Check-in Validation
# ============================================================================

@pytest.mark.django_db
def test_employee_dashboard_filters_projects_by_daily_plan_assignment():
    """
    Phase 1: Employee dashboard should only show projects where employee
    is assigned via PlannedActivity for today's date.
    """
    from django.test import Client
    
    # Setup users
    pm_user = User.objects.create_user(username="pm_test", password="testpass")
    emp_user = User.objects.create_user(username="cesar", password="testpass")
    emp_user2 = User.objects.create_user(username="candido", password="testpass")
    
    # Setup employees
    cesar = Employee.objects.create(
        user=emp_user,
        first_name="César",
        last_name="González",
        social_security_number="111-11-1111",
        hourly_rate=25.00
    )
    
    candido = Employee.objects.create(
        user=emp_user2,
        first_name="Cándido",
        last_name="Martínez",
        social_security_number="222-22-2222",
        hourly_rate=25.00
    )
    
    # Setup projects
    project_a = Project.objects.create(name="Proyecto A", start_date=date.today())
    project_b = Project.objects.create(name="Proyecto B", start_date=date.today())
    
    # Create today's daily plan for Project A with César assigned
    today = date.today()
    plan_a = DailyPlan.objects.create(
        project=project_a,
        plan_date=today,
        created_by=pm_user,
        status="PUBLISHED",
        completion_deadline=timezone.now() + timedelta(hours=8)
    )
    
    activity_a = PlannedActivity.objects.create(
        daily_plan=plan_a,
        title="Paint exterior walls",
        order=1,
        estimated_hours=8
    )
    activity_a.assigned_employees.add(cesar)  # César assigned to Project A today
    
    # Create today's daily plan for Project B WITHOUT Cándido
    plan_b = DailyPlan.objects.create(
        project=project_b,
        plan_date=today,
        created_by=pm_user,
        status="PUBLISHED",
        completion_deadline=timezone.now() + timedelta(hours=8)
    )
    
    activity_b = PlannedActivity.objects.create(
        daily_plan=plan_b,
        title="Install windows",
        order=1,
        estimated_hours=6
    )
    activity_b.assigned_employees.add(cesar)  # Only César, not Cándido
    
    # Test César can see both projects (he's assigned to both)
    client = Client()
    client.login(username="cesar", password="testpass")
    response = client.get('/dashboard/employee/')
    
    assert response.status_code == 200
    assert 'my_projects_today' in response.context
    cesar_projects = list(response.context['my_projects_today'])
    assert len(cesar_projects) == 2
    assert project_a in cesar_projects
    assert project_b in cesar_projects
    
    # Test Cándido sees NO projects (not assigned to any)
    client.logout()
    client.login(username="candido", password="testpass")
    response = client.get('/dashboard/employee/')
    
    assert response.status_code == 200
    candido_projects = list(response.context['my_projects_today'])
    assert len(candido_projects) == 0
    assert response.context['has_assignments_today'] is False


@pytest.mark.django_db
def test_employee_cannot_checkin_to_unassigned_project():
    """
    Phase 1: Employee should NOT be able to check-in to a project
    where they're not assigned via PlannedActivity for today.
    """
    from django.test import Client
    from core.models import TimeEntry, CostCode
    
    # Setup
    pm_user = User.objects.create_user(username="pm", password="pass")
    emp_user = User.objects.create_user(username="jose", password="pass")
    
    jose = Employee.objects.create(
        user=emp_user,
        first_name="José",
        last_name="López",
        social_security_number="333-33-3333",
        hourly_rate=25.00
    )
    
    project_a = Project.objects.create(name="Project A", start_date=date.today())
    project_b = Project.objects.create(name="Project B", start_date=date.today())
    
    cost_code = CostCode.objects.create(code="LABOR", name="General Labor")
    
    # José assigned only to Project A today
    today = date.today()
    plan_a = DailyPlan.objects.create(
        project=project_a,
        plan_date=today,
        created_by=pm_user,
        status="PUBLISHED",
        completion_deadline=timezone.now() + timedelta(hours=8)
    )
    
    activity = PlannedActivity.objects.create(
        daily_plan=plan_a,
        title="Prep work",
        order=1
    )
    activity.assigned_employees.add(jose)
    
    client = Client()
    client.login(username="jose", password="pass")
    
    # ✅ Test: Check-in to Project A (assigned) should succeed
    response = client.post('/dashboard/employee/', {
        'action': 'clock_in',
        'project': project_a.id,
        'cost_code': cost_code.id,
        'notes': 'Starting work'
    })
    
    assert response.status_code == 302  # Redirect after success
    assert TimeEntry.objects.filter(employee=jose, project=project_a).exists()
    
    # Clean up for next test
    TimeEntry.objects.filter(employee=jose).delete()
    
    # ❌ Test: Check-in to Project B (NOT assigned) should FAIL
    response = client.post('/dashboard/employee/', {
        'action': 'clock_in',
        'project': project_b.id,
        'cost_code': cost_code.id,
        'notes': 'Trying unauthorized work'
    })
    
    assert response.status_code == 302  # Redirects with error
    assert not TimeEntry.objects.filter(employee=jose, project=project_b).exists()


@pytest.mark.django_db
def test_copy_yesterday_team_to_today():
    """
    Phase 2: 'Copy Yesterday's Team' button should copy all employees
    from yesterday's activities to today's activities.
    """
    from django.test import Client
    
    # Setup
    pm_user = User.objects.create_user(username="pm_copy", password="pass")
    pm_user.is_staff = True
    pm_user.save()
    
    # Create 3 employees
    emp1_user = User.objects.create_user(username="emp1", password="pass")
    emp2_user = User.objects.create_user(username="emp2", password="pass")
    emp3_user = User.objects.create_user(username="emp3", password="pass")
    
    emp1 = Employee.objects.create(
        user=emp1_user, first_name="Worker", last_name="One",
        social_security_number="111", hourly_rate=20
    )
    emp2 = Employee.objects.create(
        user=emp2_user, first_name="Worker", last_name="Two",
        social_security_number="222", hourly_rate=20
    )
    emp3 = Employee.objects.create(
        user=emp3_user, first_name="Worker", last_name="Three",
        social_security_number="333", hourly_rate=20
    )
    
    project = Project.objects.create(name="Test Project", start_date=date.today())
    
    # Create YESTERDAY's plan with 2 activities, employees assigned
    yesterday = date.today() - timedelta(days=1)
    yesterday_plan = DailyPlan.objects.create(
        project=project,
        plan_date=yesterday,
        created_by=pm_user,
        status="COMPLETED",
        completion_deadline=timezone.now() - timedelta(hours=24)
    )
    
    yesterday_act1 = PlannedActivity.objects.create(
        daily_plan=yesterday_plan,
        title="Yesterday Activity 1",
        order=1
    )
    yesterday_act1.assigned_employees.set([emp1, emp2])
    
    yesterday_act2 = PlannedActivity.objects.create(
        daily_plan=yesterday_plan,
        title="Yesterday Activity 2",
        order=2
    )
    yesterday_act2.assigned_employees.set([emp2, emp3])  # emp2 and emp3
    
    # Create TODAY's plan with 3 activities, NO employees assigned yet
    today = date.today()
    today_plan = DailyPlan.objects.create(
        project=project,
        plan_date=today,
        created_by=pm_user,
        status="DRAFT",
        completion_deadline=timezone.now() + timedelta(hours=8)
    )
    
    today_act1 = PlannedActivity.objects.create(
        daily_plan=today_plan,
        title="Today Activity 1",
        order=1
    )
    today_act2 = PlannedActivity.objects.create(
        daily_plan=today_plan,
        title="Today Activity 2",
        order=2
    )
    today_act3 = PlannedActivity.objects.create(
        daily_plan=today_plan,
        title="Today Activity 3",
        order=3
    )
    
    # Verify today's activities have NO employees yet
    assert today_act1.assigned_employees.count() == 0
    assert today_act2.assigned_employees.count() == 0
    assert today_act3.assigned_employees.count() == 0
    
    # Execute "Copy Yesterday's Team" action
    client = Client()
    client.login(username="pm_copy", password="pass")
    
    response = client.post(f'/planning/{today_plan.id}/edit/', {
        'action': 'copy_yesterday_team'
    })
    
    assert response.status_code == 302  # Redirect after success
    
    # Refresh from DB
    today_act1.refresh_from_db()
    today_act2.refresh_from_db()
    today_act3.refresh_from_db()
    
    # ✅ Verify ALL 3 employees (emp1, emp2, emp3) are now assigned to ALL today's activities
    assert today_act1.assigned_employees.count() == 3
    assert today_act2.assigned_employees.count() == 3
    assert today_act3.assigned_employees.count() == 3
    
    # Verify specific employees
    assert set(today_act1.assigned_employees.all()) == {emp1, emp2, emp3}
    assert set(today_act2.assigned_employees.all()) == {emp1, emp2, emp3}
    assert set(today_act3.assigned_employees.all()) == {emp1, emp2, emp3}


@pytest.mark.django_db
def test_copy_yesterday_team_no_yesterday_plan():
    """
    Phase 2: Should show warning when no yesterday plan exists.
    """
    from django.test import Client
    
    pm_user = User.objects.create_user(username="pm_no_yesterday", password="pass")
    pm_user.is_staff = True
    pm_user.save()
    
    project = Project.objects.create(name="Project X", start_date=date.today())
    
    # Create ONLY today's plan (no yesterday)
    today = date.today()
    today_plan = DailyPlan.objects.create(
        project=project,
        plan_date=today,
        created_by=pm_user,
        status="DRAFT",
        completion_deadline=timezone.now() + timedelta(hours=8)
    )
    
    client = Client()
    client.login(username="pm_no_yesterday", password="pass")
    
    response = client.post(f'/planning/{today_plan.id}/edit/', {
        'action': 'copy_yesterday_team'
    }, follow=True)
    
    # Should redirect with warning message
    assert response.status_code == 200
    messages = list(response.context['messages'])
    assert len(messages) > 0
    assert 'No plan found' in str(messages[0])
