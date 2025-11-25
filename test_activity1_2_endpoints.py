#!/usr/bin/env python3
"""
Test script para verificar todos los endpoints de Activity 1 y 2
Corre este script con: python3 test_activity1_2_endpoints.py
"""
import os
import time
import pytest

# Pytest-django will handle setup; keep fallback for direct script execution
if 'DJANGO_SETTINGS_MODULE' not in os.environ:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kibray_backend.settings')
try:
    import django
    if not django.apps.apps.ready:
        django.setup()
except Exception:
    pass

from django.test import Client
from django.contrib.auth.models import User
from core.models import Project, Task, DailyPlan, MaterialRequest, InventoryItem, Employee
from decimal import Decimal
from datetime import date, timedelta

def print_test(name, passed, message=""):
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status}: {name}")
    if message:
        print(f"   {message}")

@pytest.mark.django_db
def test_task_time_tracking():
    """Test Activity 1: Task time tracking endpoints"""
    print("\n=== Testing Task Time Tracking (Activity 1) ===")
    
    client = Client()
    
    # Create test user and employee
    user = User.objects.filter(is_staff=True).first()
    if not user:
        user = User.objects.create_user('testadmin', 'test@test.com', 'password', is_staff=True)
    
    # Get or create employee
    employee = Employee.objects.filter(user=user).first()
    if not employee:
        employee = Employee.objects.create(
            user=user,
            first_name="Test",
            last_name="Admin",
            social_security_number="999-99-9999",
            hourly_rate=Decimal("25.00")
        )
    
    project = Project.objects.first()
    if not project:
        print_test("Task Time Tracking", False, "No projects found in database")
        return
    
    # Create test task
    task = Task.objects.create(
        project=project,
        title="Test Task for Time Tracking",
        description="Auto-generated test task",
        status="Pendiente",
        created_by=user,
        assigned_to=employee,
        is_touchup=False
    )
    
    # Login
    client.force_login(user)
    
    # Test 1: Start tracking
    response = client.post(f'/tasks/{task.id}/start-tracking/')
    if response.status_code == 200:
        data = response.json()
        test_passed = data.get('success') == True
        print_test("POST /tasks/<id>/start-tracking/", test_passed, 
                   f"Response: {data}")
    else:
        print_test("POST /tasks/<id>/start-tracking/", False, 
                   f"Status: {response.status_code}")
    
    # Refresh task
    task.refresh_from_db()
    
    # Wait a bit to simulate actual work time
    time.sleep(2)
    
    # Test 2: Stop tracking
    if task.started_at:
        response = client.post(f'/tasks/{task.id}/stop-tracking/')
        if response.status_code == 200:
            data = response.json()
            test_passed = data.get('success') == True
            print_test("POST /tasks/<id>/stop-tracking/", test_passed,
                       f"Elapsed: {data.get('elapsed_seconds')}s, Total: {data.get('total_hours')}h")
        else:
            print_test("POST /tasks/<id>/stop-tracking/", False,
                       f"Status: {response.status_code}")
    
    # Refresh and verify
    task.refresh_from_db()
    print_test("Time accumulated correctly", task.time_tracked_seconds > 0,
               f"Tracked: {task.time_tracked_seconds}s = {task.get_time_tracked_hours()}h")
    
    # Cleanup
    task.delete()

@pytest.mark.django_db
def test_daily_plan_endpoints():
    """Test Activity 1: Daily plan endpoints"""
    print("\n=== Testing Daily Plan Endpoints (Activity 1) ===")
    
    client = Client()
    user = User.objects.filter(is_staff=True).first()
    if not user:
        print_test("Daily Plans", False, "No admin users found")
        return
    
    project = Project.objects.first()
    if not project:
        print_test("Daily Plans", False, "No projects found")
        return
    
    client.force_login(user)
    
    # Create test daily plan
    plan = DailyPlan.objects.create(
        project=project,
        plan_date=date.today() + timedelta(days=1),
        created_by=user,
        completion_deadline=django.utils.timezone.now() + timedelta(hours=24),
        status='PUBLISHED'
    )
    
    # Test 1: Fetch weather
    response = client.post(f'/planning/{plan.id}/fetch-weather/')
    if response.status_code == 200:
        data = response.json()
        print_test("POST /planning/<id>/fetch-weather/", 
                   data.get('success') == True,
                   f"Weather: {data.get('weather_data')}")
    else:
        print_test("POST /planning/<id>/fetch-weather/", False,
                   f"Status: {response.status_code}")
    
    # Test 2: Convert activities (should return empty list if no activities)
    response = client.post(f'/planning/{plan.id}/convert-activities/')
    if response.status_code == 200:
        data = response.json()
        print_test("POST /planning/<id>/convert-activities/",
                   'tasks_created' in data,
                   f"Tasks created: {data.get('tasks_created', 0)}")
    else:
        print_test("POST /planning/<id>/convert-activities/", False,
                   f"Status: {response.status_code}")
    
    # Test 3: Productivity score
    plan.estimated_hours_total = Decimal('8.0')
    plan.actual_hours_worked = Decimal('7.5')
    plan.save()
    
    response = client.get(f'/planning/{plan.id}/productivity/')
    if response.status_code == 200:
        data = response.json()
        print_test("GET /planning/<id>/productivity/",
                   'productivity_score' in data,
                   f"Score: {data.get('productivity_score')}%")
    else:
        print_test("GET /planning/<id>/productivity/", False,
                   f"Status: {response.status_code}")
    
    # Cleanup
    plan.delete()

def test_material_request_workflow():
    """Test Activity 2: Material request workflow"""
    print("\n=== Testing Material Request Workflow (Activity 2) ===")
    
    client = Client()
    user = User.objects.filter(is_staff=True).first()
    if not user:
        print_test("Material Requests", False, "No admin users found")
        return
    
    project = Project.objects.first()
    if not project:
        print_test("Material Requests", False, "No projects found")
        return
    
    client.force_login(user)
    
    # Create test material request with items
    from core.models import MaterialRequestItem
    mat_request = MaterialRequest.objects.create(
        project=project,
        requested_by=user,
        status='draft',
        needed_when='now'
    )
    
    # Add a test item
    MaterialRequestItem.objects.create(
        request=mat_request,
        category="paint",
        product_name="Test Material",
        quantity=Decimal("10"),
        unit="gal",
        brand_text="Generic Brand"
    )
    
    # Test 1: Submit for approval
    response = client.post(f'/materials/requests/{mat_request.id}/submit/')
    test_passed = response.status_code in [200, 302]
    mat_request.refresh_from_db()
    print_test("POST /materials/requests/<id>/submit/",
               test_passed and mat_request.status == 'pending',
               f"Status changed to: {mat_request.status}")
    
    # Test 2: Approve request
    response = client.post(f'/materials/requests/{mat_request.id}/approve/')
    test_passed = response.status_code in [200, 302]
    mat_request.refresh_from_db()
    print_test("POST /materials/requests/<id>/approve/",
               test_passed and mat_request.status == 'approved',
               f"Status: {mat_request.status}, Approved by: {mat_request.approved_by}")
    
    # Test 3: Create expense (direct purchase)
    response = client.post(f'/materials/requests/{mat_request.id}/create-expense/',
                          {'total_amount': '500.00'})
    test_passed = response.status_code in [200, 302]
    mat_request.refresh_from_db()
    print_test("POST /materials/requests/<id>/create-expense/",
               test_passed and mat_request.status == 'fulfilled',
               f"Status: {mat_request.status}")
    
    # Cleanup
    mat_request.delete()

def test_inventory_endpoints():
    """Test Activity 2: Inventory endpoints"""
    print("\n=== Testing Inventory Endpoints (Activity 2) ===")
    
    client = Client()
    user = User.objects.filter(is_staff=True).first()
    if not user:
        print_test("Inventory", False, "No admin users found")
        return
    
    client.force_login(user)
    
    # Test 1: Low stock alert page
    response = client.get('/inventory/low-stock/')
    print_test("GET /inventory/low-stock/",
               response.status_code == 200,
               f"Status: {response.status_code}")

def test_notifications():
    """Test that notifications are being created"""
    print("\n=== Testing Notifications System ===")
    
    from core.models import Notification
    
    # Count recent notifications
    recent_count = Notification.objects.filter(
        created_at__gte=django.utils.timezone.now() - timedelta(minutes=5)
    ).count()
    
    print_test("Notifications created", recent_count > 0,
               f"Found {recent_count} recent notifications")

def run_all_tests():
    """Run all endpoint tests"""
    print("=" * 60)
    print("KIBRAY - Activity 1 & 2 Endpoint Test Suite")
    print("=" * 60)
    
    try:
        test_task_time_tracking()
        test_daily_plan_endpoints()
        test_material_request_workflow()
        test_inventory_endpoints()
        test_notifications()
        
        print("\n" + "=" * 60)
        print("Test Suite Complete")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    run_all_tests()
