#!/usr/bin/env python3
"""
Script para diagnosticar y ver el detalle de TimeEntries de un empleado.

Uso: python3 diagnose_timeentries.py <employee_name> [--date YYYY-MM-DD]

Ejemplo:
    python3 diagnose_timeentries.py "Jesus Duran" --date 2026-02-06
    python3 diagnose_timeentries.py "Jesus" --week 2026-02-02
"""
import os
import sys
import django
from decimal import Decimal

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "kibray_backend.settings")
django.setup()

from datetime import datetime, timedelta
from django.db.models import Q
from core.models import TimeEntry, Employee


def main():
    if len(sys.argv) < 2:
        print("Uso: python3 diagnose_timeentries.py <employee_name> [--date YYYY-MM-DD] [--week YYYY-MM-DD]")
        sys.exit(1)
    
    # Parse arguments
    emp_name = sys.argv[1]
    target_date = None
    week_start = None
    
    for i, arg in enumerate(sys.argv):
        if arg == "--date" and i + 1 < len(sys.argv):
            target_date = datetime.strptime(sys.argv[i + 1], "%Y-%m-%d").date()
        if arg == "--week" and i + 1 < len(sys.argv):
            week_start = datetime.strptime(sys.argv[i + 1], "%Y-%m-%d").date()
    
    # Buscar empleado
    employees = Employee.objects.filter(
        Q(first_name__icontains=emp_name) | 
        Q(last_name__icontains=emp_name)
    )
    
    if not employees.exists():
        print(f"❌ No se encontró empleado con nombre '{emp_name}'")
        sys.exit(1)
    
    if employees.count() > 1:
        print(f"⚠️  Múltiples empleados encontrados:")
        for e in employees:
            print(f"   - {e.first_name} {e.last_name} (ID: {e.id})")
        print(f"\nUsando el primero: {employees.first()}")
    
    employee = employees.first()
    print(f"\n👤 Empleado: {employee.first_name} {employee.last_name} (ID: {employee.id})")
    print(f"   Rate: ${employee.hourly_rate}/hr")
    
    # Filtrar entradas
    entries = TimeEntry.objects.filter(employee=employee)
    
    if target_date:
        entries = entries.filter(date=target_date)
        print(f"\n📅 Fecha: {target_date}")
    elif week_start:
        week_end = week_start + timedelta(days=6)
        entries = entries.filter(date__range=(week_start, week_end))
        print(f"\n📅 Semana: {week_start} - {week_end}")
    else:
        # Últimos 7 días
        today = datetime.now().date()
        entries = entries.filter(date__gte=today - timedelta(days=7))
        print(f"\n📅 Últimos 7 días")
    
    entries = entries.select_related('project').order_by('date', 'start_time')
    
    print(f"\n{'='*100}")
    print(f"DETALLE DE TIMEENTRIES ({entries.count()} entradas)")
    print(f"{'='*100}\n")
    
    # Agrupar por día
    from collections import defaultdict
    by_day = defaultdict(list)
    for e in entries:
        by_day[e.date].append(e)
    
    total_hours = Decimal("0")
    total_base = Decimal("0")
    total_co = Decimal("0")
    
    for day, day_entries in sorted(by_day.items()):
        day_total = Decimal("0")
        day_base = Decimal("0")
        day_co = Decimal("0")
        
        print(f"\n📆 {day.strftime('%A %Y-%m-%d')} ({len(day_entries)} entries)")
        print(f"   {'─'*90}")
        
        for i, e in enumerate(day_entries, 1):
            hours = e.hours_worked or Decimal("0")
            end_str = e.end_time.strftime('%H:%M') if e.end_time else '⏳OPEN'
            proj_name = e.project.name[:20] if e.project else 'N/A'
            
            # Determinar tipo
            if e.change_order_id:
                entry_type = f"📋 CO #{e.change_order_id}"
                day_co += hours
            else:
                entry_type = "🏠 BASE"
                day_base += hours
            
            day_total += hours
            
            # Calcular horas esperadas
            if e.start_time and e.end_time:
                s = e.start_time.hour * 60 + e.start_time.minute
                end = e.end_time.hour * 60 + e.end_time.minute
                if end < s:
                    end += 24 * 60
                expected = Decimal(end - s) / Decimal(60)
                if s < 12*60+30 <= end and expected >= 5:
                    expected -= Decimal("0.5")
                diff = abs(hours - expected)
                diff_str = f" ⚠️ Esperado: {expected:.2f}h" if diff > Decimal("0.05") else ""
            else:
                diff_str = ""
            
            print(f"   {i}. {e.start_time.strftime('%H:%M')}-{end_str} = {hours}h{diff_str}")
            print(f"      {entry_type} | {proj_name}")
            if e.notes:
                print(f"      📝 {e.notes[:50]}...")
        
        print(f"   {'─'*90}")
        print(f"   TOTAL DÍA: {day_total}h (🏠 {day_base}h BASE + 📋 {day_co}h CO)")
        
        total_hours += day_total
        total_base += day_base
        total_co += day_co
    
    print(f"\n{'='*100}")
    print(f"RESUMEN TOTAL")
    print(f"{'='*100}")
    print(f"   Total horas:  {total_hours}h")
    print(f"   Horas BASE:   {total_base}h (🏠)")
    print(f"   Horas CO:     {total_co}h (📋)")
    print(f"   Pay estimate: ${float(total_hours) * float(employee.hourly_rate):.2f}")
    print(f"{'='*100}\n")


if __name__ == "__main__":
    main()
