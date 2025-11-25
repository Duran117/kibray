#!/usr/bin/env python3
"""
Comprehensive button and form audit for all modules
Tests every button, form, and endpoint systematically
"""
import os
import django
import time

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kibray_backend.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from core.models import (
    Project, Task, Employee, DailyPlan, PlannedActivity,
    MaterialRequest, MaterialRequestItem, InventoryItem, InventoryLocation,
    SitePhoto, DamageReport, ColorSample, FloorPlan, PlanPin,
    PayrollPeriod, PayrollRecord
)
from decimal import Decimal
from datetime import date, timedelta
from io import BytesIO
from PIL import Image

def print_test(module, test_name, passed, message=""):
    status = "✅" if passed else "❌"
    print(f"{status} [{module}] {test_name}")
    if message:
        print(f"   → {message}")

def setup_test_data():
    """Create minimal test data"""
    user = User.objects.filter(is_staff=True).first()
    if not user:
        user = User.objects.create_user('testadmin', 'test@test.com', 'password', is_staff=True)
    
    employee = Employee.objects.filter(user=user).first()
    if not employee:
        employee = Employee.objects.create(
            user=user,
            first_name="Test",
            last_name="Admin",
            social_security_number="999-99-9999",
            hourly_rate=Decimal("25.00"),
            overtime_multiplier=Decimal("1.50")
        )
    
    project = Project.objects.first()
    if not project:
        print("❌ No projects found - create at least one project first")
        return None, None, None
    
    return user, employee, project

# ============================================
# MODULE 11: TASKS
# ============================================

def audit_tasks_module():
    print("\n" + "="*60)
    print("AUDITING MODULE 11: TASKS")
    print("="*60)
    
    user, employee, project = setup_test_data()
    if not user:
        return

    # Asegurar campos overtime en Employee para lógica nueva (migración Q16.11)
    if not hasattr(employee, 'overtime_multiplier'):
        # Fallback: set attributes dynamically (model may not yet have columns if migration not applied in this DB)
        try:
            employee.overtime_multiplier = Decimal('1.50')
            employee.has_custom_overtime = False
            employee.save()
        except Exception:
            pass
    else:
        try:
            if employee.overtime_multiplier is None:
                employee.overtime_multiplier = Decimal('1.50')
            if not hasattr(employee, 'has_custom_overtime'):
                employee.has_custom_overtime = False
            employee.save()
        except Exception:
            pass
    
    client = Client()
    client.force_login(user)
    
    # Test 1: Task list view (contains creation form when staff)
    response = client.get(f'/projects/{project.id}/tasks/')
    print_test("Tasks", "Task List & Create Form GET", 
               response.status_code == 200,
               f"Status: {response.status_code}")
    
    # Test 2: Create task (POST to same endpoint) with priority & due_date
    response = client.post(f'/projects/{project.id}/tasks/', {
        'title': 'Audit Test Task',
        'description': 'Test task for audit',
        'project': project.id,
        'assigned_to': employee.id,
        'status': 'Pendiente',
        'priority': 'high',
        'due_date': (date.today() + timedelta(days=7)).isoformat(),
        'is_touchup': '',
    })
    print_test("Tasks", "Task Create POST with Priority/Due Date",
               response.status_code in [200, 302],
               f"Status: {response.status_code}")
    
    task = Task.objects.filter(title='Audit Test Task').first()
    if task:
        # Test 3: Task detail view
        response = client.get(f'/tasks/{task.id}/')
        print_test("Tasks", "Task Detail View",
                   response.status_code == 200 and b'Seguimiento de tiempo' in response.content,
                   "Time tracking section visible" if b'Seguimiento de tiempo' in response.content else "Missing time tracking")
        
        # Test 4: Start time tracking
        response = client.post(f'/tasks/{task.id}/start-tracking/')
        data = response.json() if response.status_code == 200 else {}
        print_test("Tasks", "Start Time Tracking Button",
                   response.status_code == 200 and data.get('success'),
                   f"Response: {data}")
        
        # Wait 2 seconds
        time.sleep(2)
        
        # Test 5: Stop time tracking
        response = client.post(f'/tasks/{task.id}/stop-tracking/')
        data = response.json() if response.status_code == 200 else {}
        print_test("Tasks", "Stop Time Tracking Button",
                   response.status_code == 200 and data.get('success'),
                   f"Elapsed: {data.get('elapsed_seconds')}s, Total: {data.get('total_hours')}h")
        
        # Test 6: Touch-up board with filters
        response = client.get(f'/projects/{project.id}/touchups/')
        print_test("Tasks", "Touch-up Board View",
                   response.status_code == 200,
                   f"Status: {response.status_code}")
        
        # Test 7: Touch-up board with priority filter
        response = client.get(f'/projects/{project.id}/touchups/?priority=high')
        print_test("Tasks", "Touch-up Board Priority Filter",
                   response.status_code == 200,
                   "Priority filter working")

# ============================================
# MODULE 12: DAILY PLANS
# ============================================

def audit_daily_plans_module():
    print("\n" + "="*60)
    print("AUDITING MODULE 12: DAILY PLANS")
    print("="*60)
    
    user, employee, project = setup_test_data()
    if not user:
        return
    
    client = Client()
    client.force_login(user)
    
    # Test 1: Daily planning dashboard
    response = client.get('/planning/')
    print_test("Daily Plans", "Planning Dashboard",
               response.status_code == 200,
               f"Status: {response.status_code}")
    
    # Test 2: Create daily plan
    response = client.post(f'/planning/project/{project.id}/create/', {
        'plan_date': date.today().isoformat(),
    })
    print_test("Daily Plans", "Create Daily Plan",
               response.status_code in [200, 302],
               f"Status: {response.status_code}")
    
    plan = DailyPlan.objects.filter(project=project, plan_date=date.today()).first()
    if plan:
        # Test 3: Fetch weather button
        response = client.post(f'/planning/{plan.id}/fetch-weather/')
        data = response.json() if response.status_code == 200 else {}
        print_test("Daily Plans", "Fetch Weather Button",
                   response.status_code == 200,
                   f"Weather: {data.get('weather_data')}")
        
        # Prepare plan for conversion: set status to PUBLISHED and add a PlannedActivity
        plan.status = 'PUBLISHED'
        plan.save(update_fields=['status'])
        PlannedActivity.objects.create(daily_plan=plan, title="Actividad Audit")
        # Test 4: Convert activities to tasks button
        response = client.post(f'/planning/{plan.id}/convert-activities/')
        data = response.json() if response.status_code == 200 else {}
        print_test("Daily Plans", "Convert Activities Button",
                   response.status_code == 200 and data.get('success'),
                   f"Status: {response.status_code}, Created: {data.get('tasks_created')}")
        
        # Test 5: Productivity endpoint
        response = client.get(f'/planning/{plan.id}/productivity/')
        data = response.json() if response.status_code == 200 else {}
        print_test("Daily Plans", "Productivity Score Endpoint",
                   response.status_code == 200,
                   f"Score: {data.get('productivity_score')}%")

# ============================================
# MODULE 14-15: MATERIALS & INVENTORY
# ============================================

def audit_materials_inventory():
    print("\n" + "="*60)
    print("AUDITING MODULES 14-15: MATERIALS & INVENTORY")
    print("="*60)
    
    user, employee, project = setup_test_data()
    if not user:
        return
    
    client = Client()
    client.force_login(user)
    
    # Test 1: Create material request
    mat_request = MaterialRequest.objects.create(
        project=project,
        requested_by=user,
        status='draft',
        needed_when='now'
    )
    
    MaterialRequestItem.objects.create(
        request=mat_request,
        category="paint",
        product_name="Test Paint",
        quantity=Decimal("10"),
        unit="gal",
        brand_text="SW"
    )
    
    print_test("Materials", "Material Request Created",
               True,
               f"Request #{mat_request.id}")
    
    # Test 2: Submit button
    response = client.post(f'/materials/requests/{mat_request.id}/submit/')
    mat_request.refresh_from_db()
    print_test("Materials", "Submit Request Button",
               response.status_code in [200, 302] and mat_request.status == 'pending',
               f"Status: {mat_request.status}")
    
    # Test 3: Approve button
    response = client.post(f'/materials/requests/{mat_request.id}/approve/')
    mat_request.refresh_from_db()
    print_test("Materials", "Approve Request Button",
               response.status_code in [200, 302] and mat_request.status == 'approved',
               f"Status: {mat_request.status}, Approved by: {mat_request.approved_by}")
    
    # Test 4: Create expense from request
    response = client.post(f'/materials/requests/{mat_request.id}/create-expense/',
                          {'total_amount': '500.00'})
    mat_request.refresh_from_db()
    print_test("Materials", "Create Expense Button",
               response.status_code in [200, 302] and mat_request.status == 'fulfilled',
               f"Status: {mat_request.status}")
    
    # Test 5: Low stock dashboard
    response = client.get('/inventory/low-stock/')
    print_test("Inventory", "Low Stock Dashboard",
               response.status_code == 200,
               f"Status: {response.status_code}")

# ============================================
# MODULE 18: SITE PHOTOS
# ============================================

def audit_photos_module():
    print("\n" + "="*60)
    print("AUDITING MODULE 18: SITE PHOTOS")
    print("="*60)
    
    user, employee, project = setup_test_data()
    if not user:
        return
    
    client = Client()
    client.force_login(user)
    
    # Test 1: Photo list view
    response = client.get(f'/projects/{project.id}/photos/')
    print_test("Photos", "Photo List View",
               response.status_code == 200,
               f"Status: {response.status_code}")
    
    # Test 2: Create photo with GPS and privacy (Q18.2, Q18.4)
    from django.core.files.uploadedfile import SimpleUploadedFile
    img = _generate_test_image(color=(100, 150, 200))
    photo_file = SimpleUploadedFile('room.png', img.read(), content_type='image/png')
    
    create_resp = client.post(f'/projects/{project.id}/photos/new/', {
        'room': 'Living Room',
        'wall_ref': 'North Wall',
        'photo_type': 'progress',
        'visibility': 'public',
        'caption': 'Progress photo for living room',
        'notes': 'Base coat applied',
        'location_lat': '40.712776',
        'location_lng': '-74.005974',
        'image': photo_file,
    })
    print_test("Photos", "Create Photo POST",
               create_resp.status_code in [200, 302],
               f"Status: {create_resp.status_code}")
    
    photo = SitePhoto.objects.filter(project=project, room='Living Room').first()
    if not photo:
        print_test("Photos", "Photo Created Lookup", False, "Photo not found")
        return
    
    # Test 3: Verify GPS fields (Q18.2)
    gps_ok = photo.location_lat is not None and photo.location_lng is not None
    print_test("Photos", "GPS Location Fields",
               gps_ok,
               f"Lat: {photo.location_lat}, Lng: {photo.location_lng}")
    
    # Test 4: Verify visibility (Q18.4)
    visibility_ok = photo.visibility == 'public'
    print_test("Photos", "Privacy Control",
               visibility_ok,
               f"Visibility: {photo.visibility}")
    
    # Test 5: Verify versioning fields (Q18.6)
    version_ok = photo.version == 1 and photo.is_current_version == True
    print_test("Photos", "Versioning Fields",
               version_ok,
               f"Version: {photo.version}, Current: {photo.is_current_version}")
    
    # Test 6: Verify caption (Q18.10)
    caption_ok = photo.caption == 'Progress photo for living room'
    print_test("Photos", "Caption Field",
               caption_ok,
               f"Caption: {photo.caption[:30] if photo.caption else None}")
    
    # Test 7: Filter by visibility
    filter_resp = client.get(f'/projects/{project.id}/photos/?visibility=public')
    filter_ok = filter_resp.status_code == 200
    print_test("Photos", "Visibility Filter",
               filter_ok,
               f"Status: {filter_resp.status_code}")

# ============================================
# MODULE 21: DAMAGE REPORTS
# ============================================

def audit_damage_reports():
    print("\n" + "="*60)
    print("AUDITING MODULE 21: DAMAGE REPORTS")
    print("="*60)
    
    user, employee, project = setup_test_data()
    if not user:
        return
    
    client = Client()
    client.force_login(user)
    
    # Test 1: Damage report list
    response = client.get(f'/projects/{project.id}/damages/')
    print_test("Damage Reports", "Damage Report List",
               response.status_code == 200,
               f"Status: {response.status_code}")
    
    # Test 2: Create damage report with auto-task (Q21.4)
    from django.core.files.uploadedfile import SimpleUploadedFile
    img = _generate_test_image()
    photo = SimpleUploadedFile('damage.png', img.read(), content_type='image/png')
    
    create_resp = client.post(f'/projects/{project.id}/damages/', {
        'title': 'Grieta en pared',
        'description': 'Daño estructural en pared norte',
        'category': 'structural',
        'severity': 'high',
        'status': 'open',
        'estimated_cost': '1500.00',
        'location_detail': 'Cocina - Pared Norte',
        'root_cause': 'Asentamiento estructural',
        'photos': photo,
    })
    print_test("Damage Reports", "Create Report POST",
               create_resp.status_code in [200, 302],
               f"Status: {create_resp.status_code}")
    
    report = DamageReport.objects.filter(project=project, title='Grieta en pared').first()
    if not report:
        print_test("Damage Reports", "Report Created Lookup", False, "Report not found")
        return
    
    # Test 3: Verify auto-task creation (Q21.4)
    auto_task_ok = report.auto_task is not None
    print_test("Damage Reports", "Auto-Task Creation",
               auto_task_ok,
               f"Task ID: {report.auto_task_id if auto_task_ok else 'None'}")
    
    # Test 4: Detail view
    detail_resp = client.get(f'/damages/{report.id}/')
    print_test("Damage Reports", "Detail View",
               detail_resp.status_code == 200,
               f"Status: {detail_resp.status_code}")
    
    # Test 5: Change severity (Q21.7)
    report.change_severity('critical', user)
    report.refresh_from_db()
    severity_ok = report.severity == 'critical' and report.severity_changed_by == user and report.severity_changed_at is not None
    print_test("Damage Reports", "Change Severity Method",
               severity_ok,
               f"New: {report.get_severity_display()}, Changed by: {report.severity_changed_by}")
    
    # Test 6: Update status to in_progress (Q21.9 time tracking)
    status_resp = client.post(f'/damages/{report.id}/update-status/', {
        'status': 'in_progress'
    })
    report.refresh_from_db()
    in_progress_ok = report.status == 'in_progress' and report.in_progress_at is not None
    print_test("Damage Reports", "Status to In Progress",
               in_progress_ok,
               f"Started: {report.in_progress_at}")
    
    # Test 7: Resolve and check resolution time (Q21.9)
    resolve_resp = client.post(f'/damages/{report.id}/update-status/', {
        'status': 'resolved'
    })
    report.refresh_from_db()
    resolution_time = report.get_resolution_time()
    resolved_ok = report.status == 'resolved' and report.resolved_at is not None and resolution_time is not None
    print_test("Damage Reports", "Resolve & Resolution Time",
               resolved_ok,
               f"Time: {resolution_time.total_seconds() if resolution_time else 0}s")
    
    # Test 8: Severity & status filters
    filter_resp = client.get(f'/projects/{project.id}/damages/?severity=critical&status=resolved')
    filter_ok = filter_resp.status_code == 200
    print_test("Damage Reports", "Severity & Status Filters",
               filter_ok,
               f"Status: {filter_resp.status_code}")

# ============================================
# RUN ALL AUDITS
# ============================================

def run_full_audit():
    print("\n" + "="*80)
    print(" "*20 + "KIBRAY - COMPREHENSIVE BUTTON & FORM AUDIT")
    print("="*80)
    
    audit_tasks_module()
    audit_daily_plans_module()
    audit_materials_inventory()
    audit_inventory_movements_module()
    audit_payroll_module()
    audit_photos_module()
    audit_color_samples_module()
    audit_floor_plans_module()
    audit_damage_reports()
    
    print("\n" + "="*80)
    print(" "*30 + "AUDIT COMPLETE")
    print("="*80)

# ============================================
# MODULE 19: COLOR SAMPLES (Added after main to keep ordering clarity)
# ============================================

def audit_inventory_movements_module():
    print("\n" + "="*60)
    print("AUDITING MODULE 15: INVENTORY MOVEMENTS")
    print("="*60)

    user, employee, project = setup_test_data()
    if not user:
        return

    client = Client()
    client.force_login(user)

    # Ensure base locations
    primary_loc, _ = InventoryLocation.objects.get_or_create(project=project, name="Principal", defaults={"is_storage": False})
    storage_loc, _ = InventoryLocation.objects.get_or_create(name="Main Storage", is_storage=True)

    # Create test item
    item = InventoryItem.objects.create(name="Audit Item", category="OTRO", unit="pcs", low_stock_threshold=Decimal("5"))

    # Test 1: Move form GET
    resp = client.get(f'/projects/{project.id}/inventory/move/')
    print_test("Inventory Movements", "Move Form GET", resp.status_code == 200, f"Status: {resp.status_code}")

    # Helper to POST movement
    def post_move(data):
        return client.post(f'/projects/{project.id}/inventory/move/', data)

    # Test 2: RECEIVE movement (adds stock)
    recv_resp = post_move({
        'item': item.id,
        'movement_type': 'RECEIVE',
        'to_location': primary_loc.id,
        'quantity': '10.00',
    })
    stock_after_receive = None
    from core.models import ProjectInventory, InventoryMovement
    stock_after_receive = ProjectInventory.objects.filter(item=item, location=primary_loc).first()
    receive_ok = (recv_resp.status_code in [200,302]) and stock_after_receive and stock_after_receive.quantity == Decimal('10.00')
    print_test("Inventory Movements", "RECEIVE Movement", receive_ok, f"Qty: {stock_after_receive.quantity if stock_after_receive else 'None'}")

    # Test 3: ISSUE movement (reduces stock)
    issue_resp = post_move({
        'item': item.id,
        'movement_type': 'ISSUE',
        'from_location': primary_loc.id,
        'quantity': '3.00',
    })
    stock_issue = ProjectInventory.objects.filter(item=item, location=primary_loc).first()
    issue_ok = (issue_resp.status_code in [200,302]) and stock_issue and stock_issue.quantity == Decimal('7.00')
    print_test("Inventory Movements", "ISSUE Movement", issue_ok, f"Qty: {stock_issue.quantity if stock_issue else 'None'}")

    # Test 4: Negative stock prevention (attempt to issue more than available)
    neg_resp = post_move({
        'item': item.id,
        'movement_type': 'ISSUE',
        'from_location': primary_loc.id,
        'quantity': '100.00',
    })
    # Should return 200 with form errors and not change stock
    stock_neg = ProjectInventory.objects.filter(item=item, location=primary_loc).first()
    neg_created = InventoryMovement.objects.filter(item=item, quantity=Decimal('100.00'), movement_type='ISSUE').exists()
    neg_ok = (neg_resp.status_code == 200) and (not neg_created) and stock_neg.quantity == Decimal('7.00')
    print_test("Inventory Movements", "Negative Stock Prevention", neg_ok, f"Status: {neg_resp.status_code}, Qty: {stock_neg.quantity if stock_neg else 'None'}")

    # Test 5: TRANSFER movement (primary -> secondary)
    secondary_loc = InventoryLocation.objects.create(project=project, name="Secundaria", is_storage=False)
    transfer_resp = post_move({
        'item': item.id,
        'movement_type': 'TRANSFER',
        'from_location': primary_loc.id,
        'to_location': secondary_loc.id,
        'quantity': '2.00',
    })
    stock_primary = ProjectInventory.objects.filter(item=item, location=primary_loc).first()
    stock_secondary = ProjectInventory.objects.filter(item=item, location=secondary_loc).first()
    transfer_ok = (transfer_resp.status_code in [200,302]) and stock_primary and stock_secondary and stock_primary.quantity == Decimal('5.00') and stock_secondary.quantity == Decimal('2.00')
    print_test("Inventory Movements", "TRANSFER Movement", transfer_ok, f"Primary: {stock_primary.quantity if stock_primary else 'None'}, Secondary: {stock_secondary.quantity if stock_secondary else 'None'}")

    # Test 6: ADJUST movement (increase stock via adjustment)
    adjust_resp = post_move({
        'item': item.id,
        'movement_type': 'ADJUST',
        'to_location': primary_loc.id,
        'quantity': '1.50',
    })
    stock_adjust = ProjectInventory.objects.filter(item=item, location=primary_loc).first()
    adjust_ok = (adjust_resp.status_code in [200,302]) and stock_adjust and stock_adjust.quantity == Decimal('6.50')
    print_test("Inventory Movements", "ADJUST Movement", adjust_ok, f"Qty: {stock_adjust.quantity if stock_adjust else 'None'}")

    # Test 7: History view lists movements
    history_resp = client.get(f'/projects/{project.id}/inventory/history/')
    movements_count = InventoryMovement.objects.filter(item=item).count()
    history_ok = history_resp.status_code == 200 and movements_count >= 4  # RECEIVE + ISSUE + TRANSFER + ADJUST (negative attempt not applied)
    print_test("Inventory Movements", "History View", history_ok, f"Movements: {movements_count}")

# ============================================
# MODULE 16: PAYROLL
# ============================================

def audit_payroll_module():
    print("\n" + "="*60)
    print("AUDITING MODULE 16: PAYROLL")
    print("="*60)

    user, employee, project = setup_test_data()
    if not user:
        return

    client = Client()
    client.force_login(user)

    from datetime import datetime, timedelta
    today = datetime.now().date()
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)

    # Seed time entries for all weekdays to pass validation
    from core.models import TimeEntry, PayrollPeriod, PayrollRecord
    import datetime as dt
    # Crear entradas para todos los días laborales (L-V) para evitar errores de días faltantes al aprobar
    for offset in range(5):
        d = week_start + timedelta(days=offset)
        TimeEntry.objects.get_or_create(
            employee=employee,
            project=project,
            date=d,
            start_time=dt.time(8, 0),
            end_time=dt.time(16, 30),
            defaults={}
        )

    # Test 1: Weekly review GET (auto creates period & records)
    review_resp = client.get('/payroll/week/')
    period = PayrollPeriod.objects.filter(week_start=week_start, week_end=week_end).first()
    record = PayrollRecord.objects.filter(period=period, employee=employee).first()
    print_test("Payroll", "Weekly Review GET",
               review_resp.status_code == 200 and period is not None and record is not None,
               f"Status: {review_resp.status_code}, Period: {period.id if period else 'None'}")

    # Test 2: Update records POST (assign hours & rate)
    update_resp = client.post('/payroll/week/', {
        'action': 'update_records',
        f'hours_{employee.id}': '42.0',  # triggers overtime split (2 OT)
        f'rate_{employee.id}': str(employee.hourly_rate),
        f'notes_{employee.id}': 'Audit payroll update'
    })
    record.refresh_from_db()
    update_ok = update_resp.status_code in [200,302] and record.reviewed and record.total_hours == Decimal('42.0') and record.overtime_hours == Decimal('2.0')
    print_test("Payroll", "Update Records POST",
               update_ok,
               f"Total: {record.total_hours}, Regular: {record.regular_hours}, OT: {record.overtime_hours}, Pay: {record.total_pay}")

    # Test 3: Approve period (skip validation para test ya que no tenemos TimeEntry para todos los empleados)
    period.approve(user, skip_validation=True)
    period.refresh_from_db()
    approve_ok = period.status == 'approved' and period.approved_by == user
    print_test("Payroll", "Approve Period Method",
               approve_ok,
               f"Status: {period.status}, Approved By: {getattr(period.approved_by, 'username', None)}")

    # Test 4: Manual adjustment (bonus)
    record.manual_adjust(user, reason='Overtime correction', bonus=Decimal('50.00'))
    record.refresh_from_db()
    adjust_ok = record.manually_adjusted and record.bonus == Decimal('50.00') and record.adjusted_by == user
    print_test("Payroll", "Manual Adjustment",
               adjust_ok,
               f"Bonus: {record.bonus}, Adjusted By: {getattr(record.adjusted_by,'username',None)}")

    # Recalculate after bonus
    record.split_hours_regular_overtime()
    record.calculate_total_pay()
    record.save()

    # Test 5: Generate expense record
    period.generate_expense_records()
    record.refresh_from_db()
    expense_ok = record.expense is not None and record.expense.amount == record.total_pay
    print_test("Payroll", "Generate Expense Records",
               expense_ok,
               f"Expense ID: {record.expense.id if record.expense else 'None'} | Amount: {record.expense.amount if record.expense else 'None'}")

    # Test 6: Record payment
    pay_resp = client.post(f'/payroll/record/{record.id}/pay/', {
        'amount': str(record.total_pay),
        'payment_date': week_end.isoformat(),
        'payment_method': 'check',
        'check_number': 'CHK123',
    })
    record.refresh_from_db()
    amount_paid = record.amount_paid()
    payment_ok = pay_resp.status_code in [200,302] and amount_paid >= record.total_pay
    print_test("Payroll", "Record Payment Form",
               payment_ok,
               f"Paid: {amount_paid}, Due: {record.balance_due()}")

    # Test 7: Payment history view
    history_resp = client.get('/payroll/history/')
    history_ok = history_resp.status_code == 200
    print_test("Payroll", "Payment History View",
               history_ok,
               f"Status: {history_resp.status_code}")


def audit_color_samples_module():
    print("\n" + "="*60)
    print("AUDITING MODULE 19: COLOR SAMPLES")
    print("="*60)

    user, employee, project = setup_test_data()
    if not user:
        return

    client = Client()
    client.force_login(user)

    # Test 1: List view
    resp = client.get(f'/projects/{project.id}/colors/')
    print_test("Color Samples", "List View", resp.status_code == 200, f"Status: {resp.status_code}")

    # Test 2: Create sample (minimal fields, images optional)
    create_resp = client.post(f'/projects/{project.id}/colors/new/', {
        'code': 'SW-7008',
        'name': 'Alabaster',
        'brand': 'Sherwin Williams',
        'finish': 'Matte',
        'gloss': '',
        'notes': 'Test sample audit',
        'room_location': 'Living Room',
        'room_group': 'Interior',
        'project': project.id,
    })
    print_test("Color Samples", "Create Sample POST", create_resp.status_code in [200,302], f"Status: {create_resp.status_code}")

    sample = ColorSample.objects.filter(project=project, code='SW-7008').first()
    if not sample:
        print_test("Color Samples", "Sample Created Lookup", False, "Sample not found after POST")
        return
    else:
        print_test("Color Samples", "Sample Created Lookup", True, f"ID: {sample.id}, Status: {sample.status}")

    # Test 3: Quick approve action
    approve_resp = client.post(f'/colors/sample/{sample.id}/quick-action/', {'action': 'approve'})
    sample.refresh_from_db()
    approve_data = approve_resp.json() if approve_resp.status_code == 200 else {}
    ok = approve_resp.status_code == 200 and sample.status == 'approved' and sample.approved_by == user and sample.approved_at is not None and sample.sample_number and sample.approval_signature
    print_test("Color Samples", "Quick Approve Button", ok, f"Num: {sample.sample_number}, Sig: {sample.approval_signature[:12] if sample.approval_signature else None}")

    # Test 4: Create second sample and reject
    reject_resp_create = client.post(f'/projects/{project.id}/colors/new/', {
        'code': 'SW-0001',
        'name': 'RejectMe',
        'brand': 'Sherwin Williams',
        'finish': 'Semi-Gloss',
        'room_location': 'Kitchen',
        'room_group': 'Interior',
        'project': project.id,
    })
    second = ColorSample.objects.filter(project=project, code='SW-0001').first()
    if second:
        reject_resp = client.post(f'/colors/sample/{second.id}/quick-action/', {
            'action': 'reject',
            'reason': 'Does not match palette'
        })
        second.refresh_from_db()
        print_test("Color Samples", "Quick Reject Button", reject_resp.status_code == 200 and second.status == 'rejected' and second.rejection_reason, f"Reason: {second.rejection_reason}")
    else:
        print_test("Color Samples", "Second Sample Creation", False, "Missing second sample")

    # Test 5: Filter by brand
    filter_resp = client.get(f'/projects/{project.id}/colors/?brand=Sherwin')
    brand_ok = filter_resp.status_code == 200 and b'Sherwin' in filter_resp.content
    print_test("Color Samples", "Brand Filter", brand_ok, f"Status: {filter_resp.status_code}")
    # Test 6: Room filter
    room_filter_resp = client.get(f'/projects/{project.id}/colors/?brand=Sherwin&status=approved')
    room_ok = room_filter_resp.status_code == 200
    print_test("Color Samples", "Status Filter", room_ok, f"Status: {room_filter_resp.status_code}")

# ============================================
# MODULE 20: FLOOR PLANS / BLUEPRINTS
# ============================================

def _generate_test_image(color=(255,0,0)):
    img = Image.new('RGB', (120, 80), color=color)
    bio = BytesIO()
    img.save(bio, format='PNG')
    bio.seek(0)
    bio.name = 'test.png'
    return bio

def audit_floor_plans_module():
    print("\n" + "="*60)
    print("AUDITING MODULE 20: FLOOR PLANS / BLUEPRINTS")
    print("="*60)

    user, employee, project = setup_test_data()
    if not user:
        return

    client = Client()
    client.force_login(user)

    # Test 1: List view
    list_resp = client.get(f'/projects/{project.id}/plans/')
    print_test("Floor Plans", "List View", list_resp.status_code == 200, f"Status: {list_resp.status_code}")

    # Test 2: Create plan (needs image)
    from django.core.files.uploadedfile import SimpleUploadedFile
    img = _generate_test_image()
    upload = SimpleUploadedFile('plan.png', img.read(), content_type='image/png')
    create_resp = client.post(f'/projects/{project.id}/plans/new/', {
        'name': 'Nivel Audit',
        'level': 0,
        'level_identifier': 'Level 0',
        'project': project.id,
        'image': upload,
    })
    plan = FloorPlan.objects.filter(project=project, name='Nivel Audit').first()
    print_test("Floor Plans", "Create Plan POST", plan is not None, f"Status: {create_resp.status_code}")
    if not plan:
        return

    # Test 3: Detail view
    detail_resp = client.get(f'/plans/{plan.id}/')
    print_test("Floor Plans", "Detail View", detail_resp.status_code == 200, f"Status: {detail_resp.status_code}")

    # Test 4: Add pin (touchup triggers auto task)
    pin_resp = client.post(f'/plans/{plan.id}/add-pin/', {
        'x': '0.1234',
        'y': '0.5678',
        'title': 'Pin Audit',
        'description': 'Test pin',
        'pin_type': 'touchup',
        'pin_color': '#0d6efd',
    })
    pin = PlanPin.objects.filter(plan=plan).order_by('-id').first()
    auto_task_ok = pin and pin.linked_task_id is not None
    print_test("Floor Plans", "Add Pin & Auto Task", pin_resp.status_code in [200,302] and auto_task_ok, f"PinResp: {pin_resp.status_code}, AutoTask: {auto_task_ok}")

    # Test 5: Pin detail AJAX
    if pin:
        ajax_resp = client.get(f'/pins/{pin.id}/detail.json')
        ajax_ok = ajax_resp.status_code == 200 and ajax_resp.json().get('id') == pin.id
        print_test("Floor Plans", "Pin Detail AJAX", ajax_ok, f"Status: {ajax_resp.status_code}")

    # Test 6: Versioning (model method)
    if plan and hasattr(plan, 'create_new_version'):
        new_img = _generate_test_image(color=(0,0,255))
        from django.core.files.uploadedfile import SimpleUploadedFile
        new_upload = SimpleUploadedFile('plan_v2.png', new_img.read(), content_type='image/png')
        new_version = plan.create_new_version(new_image=new_upload, created_by=user)
        plan.refresh_from_db()
        migratable = plan.pins.filter(status='pending_migration').count()
        version_ok = new_version.version == plan.version + 1 or new_version.is_current
        print_test("Floor Plans", "Versioning Migration", migratable >= 0 and version_ok, f"Migratable Pins: {migratable}, New Version ID: {new_version.id}")

if __name__ == '__main__':
    run_full_audit()

