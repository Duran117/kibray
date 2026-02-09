#!/usr/bin/env python3
"""
Diagnostic script for payroll issues
Run this in production to analyze time entries

Usage:
    python3 diagnose_payroll_issue.py [employee_name] [date]
    
Examples:
    python3 diagnose_payroll_issue.py "Jesus Duran" 2025-02-06
    python3 diagnose_payroll_issue.py "Jesus" today
    python3 diagnose_payroll_issue.py --week "Jesus"
"""
import os
import sys
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "kibray_backend.settings")
django.setup()

from datetime import date, datetime, timedelta
from decimal import Decimal
from core.models import TimeEntry, Employee, PayrollRecord

def find_employee(name_query):
    """Find employee by name (partial match)"""
    return Employee.objects.filter(
        first_name__icontains=name_query
    ).first() or Employee.objects.filter(
        last_name__icontains=name_query
    ).first()

def parse_date(date_str):
    """Parse date string or 'today'"""
    if date_str.lower() == 'today':
        return date.today()
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return None

def analyze_entries(employee, target_date=None, week=False):
    """Analyze time entries for employee"""
    print(f"\n{'='*80}")
    print(f"👤 EMPLOYEE: {employee.first_name} {employee.last_name} (ID: {employee.id})")
    print(f"{'='*80}")
    
    # Determine date range
    if week:
        # Get last 7 days
        start_date = date.today() - timedelta(days=7)
        end_date = date.today()
        print(f"📅 DATE RANGE: {start_date} to {end_date}")
        entries = TimeEntry.objects.filter(
            employee=employee,
            date__gte=start_date,
            date__lte=end_date
        ).order_by('date', 'start_time')
    elif target_date:
        print(f"📅 DATE: {target_date}")
        entries = TimeEntry.objects.filter(
            employee=employee,
            date=target_date
        ).order_by('start_time')
    else:
        # Last 10 entries
        print(f"📅 LAST 10 ENTRIES")
        entries = TimeEntry.objects.filter(
            employee=employee
        ).order_by('-date', '-start_time')[:10]
    
    if not entries.exists():
        print("❌ No entries found!")
        return
    
    print(f"\n{'='*80}")
    print(f"{'#':<4} {'Date':<12} {'Start':<7} {'End':<7} {'Hours':<8} {'Project':<20} {'CO':<15} {'Issues'}")
    print(f"{'='*80}")
    
    total = Decimal("0")
    base = Decimal("0")
    co_hours = Decimal("0")
    issues_count = 0
    
    current_date = None
    day_total = Decimal("0")
    
    for i, e in enumerate(entries, 1):
        hours = e.hours_worked or Decimal("0")
        
        # Group by date
        if current_date and e.date != current_date:
            print(f"{'--':<4} {'Day Total':<12} {'':<7} {'':<7} {day_total:<8}")
            day_total = Decimal("0")
        
        current_date = e.date
        day_total += hours
        total += hours
        
        end_str = e.end_time.strftime('%H:%M') if e.end_time else 'OPEN'
        start_str = e.start_time.strftime('%H:%M') if e.start_time else 'NULL!'
        proj = (e.project.name[:18] + '..') if e.project and len(e.project.name) > 20 else (e.project.name if e.project else 'NO PROJECT!')
        
        if e.change_order_id:
            co_hours += hours
            co_str = f"CO#{e.change_order_id}"
            if e.change_order:
                co_str = e.change_order.title[:13] + '..' if len(e.change_order.title) > 15 else e.change_order.title
        else:
            base += hours
            co_str = "BASE"
        
        # Check for issues
        issues = []
        if not e.start_time:
            issues.append("NO_START")
        if e.end_time and (e.hours_worked is None or e.hours_worked == 0):
            issues.append("HOURS=0!")
        if e.end_time and e.start_time:
            # Calculate expected hours
            s = e.start_time.hour * 60 + e.start_time.minute
            en = e.end_time.hour * 60 + e.end_time.minute
            if en < s:
                en += 24 * 60
            expected = Decimal(en - s) / Decimal(60)
            if expected >= Decimal("5.0"):
                # Account for lunch deduction
                expected -= Decimal("0.5")
            if abs(hours - expected) > Decimal("0.1"):
                issues.append(f"CALC_DIFF")
        
        if issues:
            issues_count += 1
        
        issue_str = ", ".join(issues) if issues else "✓"
        
        print(f"{i:<4} {str(e.date):<12} {start_str:<7} {end_str:<7} {str(hours):<8} {proj:<20} {co_str:<15} {issue_str}")
        
        if e.notes:
            print(f"     📝 {e.notes[:70]}")
    
    # Print last day total
    if current_date:
        print(f"{'--':<4} {'Day Total':<12} {'':<7} {'':<7} {day_total:<8}")
    
    print(f"{'='*80}")
    print(f"\n📊 SUMMARY:")
    print(f"   Total Entries: {entries.count()}")
    print(f"   Total Hours: {total}")
    print(f"   🏠 BASE Hours: {base}")
    print(f"   📋 CO Hours: {co_hours}")
    print(f"   ⚠️  Issues Found: {issues_count}")
    
    # Check payroll records
    if target_date:
        payroll = PayrollRecord.objects.filter(
            employee=employee,
            period_start__lte=target_date,
            period_end__gte=target_date
        ).first()
        if payroll:
            print(f"\n💰 PAYROLL RECORD (Period: {payroll.period_start} to {payroll.period_end}):")
            print(f"   Status: {payroll.status}")
            print(f"   Total Hours: {payroll.total_hours}")
        else:
            print(f"\n💰 No payroll record found for this date")
    
    print(f"{'='*80}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 diagnose_payroll_issue.py [employee_name] [date|today|--week]")
        print("\nExamples:")
        print("  python3 diagnose_payroll_issue.py 'Jesus' today")
        print("  python3 diagnose_payroll_issue.py 'Jesus' 2025-02-06")
        print("  python3 diagnose_payroll_issue.py 'Jesus' --week")
        sys.exit(1)
    
    emp_name = sys.argv[1]
    emp = find_employee(emp_name)
    
    if not emp:
        print(f"❌ Employee '{emp_name}' not found!")
        # List available employees
        print("\nAvailable employees:")
        for e in Employee.objects.all()[:10]:
            print(f"  - {e.first_name} {e.last_name}")
        sys.exit(1)
    
    # Parse date argument
    target_date = None
    week = False
    
    if len(sys.argv) > 2:
        if sys.argv[2] == '--week':
            week = True
        else:
            target_date = parse_date(sys.argv[2])
            if not target_date:
                print(f"❌ Invalid date format: {sys.argv[2]}")
                print("Use: YYYY-MM-DD or 'today'")
                sys.exit(1)
    
    analyze_entries(emp, target_date, week)
