#!/usr/bin/env python3
"""Check Jesus Duran entries for Feb 6, 2026"""
import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "kibray_backend.settings")
django.setup()

from datetime import date
from decimal import Decimal
from core.models import TimeEntry, Employee

# Find Jesus Duran
emp = Employee.objects.filter(first_name__icontains="Jesus").first()
if not emp:
    print("Employee not found")
    exit()

print(f"\n👤 {emp.first_name} {emp.last_name}")

# Get entries for Feb 6
target_date = date(2026, 2, 6)
entries = TimeEntry.objects.filter(
    employee=emp,
    date=target_date
).order_by('start_time')

print(f"\n📅 Entries for {target_date}:")
print(f"{'='*80}")

total = Decimal("0")
base = Decimal("0")
co = Decimal("0")

for i, e in enumerate(entries, 1):
    hours = e.hours_worked or Decimal("0")
    total += hours
    
    end_str = e.end_time.strftime('%H:%M') if e.end_time else 'OPEN'
    start_str = e.start_time.strftime('%H:%M') if e.start_time else 'NULL!'
    proj = e.project.name if e.project else 'NO PROJECT!'
    
    if e.change_order_id:
        co += hours
        co_str = f"CO#{e.change_order_id}"
    else:
        base += hours
        co_str = "BASE"
    
    # Check for issues
    issues = []
    if not e.start_time:
        issues.append("⚠️ NO START_TIME!")
    if e.end_time and (e.hours_worked is None or e.hours_worked == 0):
        issues.append("⚠️ hours_worked=0 but has end_time!")
    if e.end_time and e.start_time:
        # Calculate expected
        s = e.start_time.hour * 60 + e.start_time.minute
        en = e.end_time.hour * 60 + e.end_time.minute
        if en < s:
            en += 24 * 60
        expected = Decimal(en - s) / Decimal(60)
        if abs(hours - expected) > Decimal("0.6"):  # More than 30min diff (lunch)
            issues.append(f"⚠️ Expected ~{expected:.1f}h")
    
    issue_str = " ".join(issues) if issues else ""
    
    print(f"{i}. {start_str} - {end_str} | {hours}h | {proj[:20]} | {co_str} {issue_str}")
    if e.notes:
        print(f"   Notes: {e.notes[:60]}")

print(f"{'='*80}")
print(f"TOTAL: {total}h | BASE: {base}h | CO: {co}h")
print(f"{'='*80}")
