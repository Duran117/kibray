#!/usr/bin/env python3
"""
Script para recalcular hours_worked en todas las TimeEntries
que tienen start_time y end_time pero hours_worked incorrecto o NULL.

Uso: python3 fix_timeentry_hours.py [--dry-run] [--week YYYY-MM-DD]
"""
import os
import sys
import django
from decimal import Decimal, ROUND_HALF_UP

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "kibray_backend.settings")
django.setup()

from datetime import datetime, timedelta
from core.models import TimeEntry


def calculate_hours(start_time, end_time):
    """Calcular horas trabajadas (mismo algoritmo que el modelo)"""
    s = start_time.hour * 60 + start_time.minute
    e = end_time.hour * 60 + end_time.minute
    
    # Cruza medianoche
    if e < s:
        e += 24 * 60
    
    minutes = e - s
    hours = Decimal(minutes) / Decimal(60)
    
    # Almuerzo: solo si cruza 12:30 y el turno dura al menos 5h
    lunch_min = 12 * 60 + 30
    if s < lunch_min <= e and hours >= Decimal("5.0"):
        hours -= Decimal("0.5")
    
    if hours < 0:
        hours = Decimal("0.00")
    
    return hours.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def main():
    dry_run = "--dry-run" in sys.argv
    
    # Obtener semana específica si se proporciona
    week_start = None
    for i, arg in enumerate(sys.argv):
        if arg == "--week" and i + 1 < len(sys.argv):
            try:
                week_start = datetime.strptime(sys.argv[i + 1], "%Y-%m-%d").date()
            except ValueError:
                print(f"Error: Fecha inválida {sys.argv[i + 1]}")
                sys.exit(1)
    
    # Filtrar entradas
    entries = TimeEntry.objects.filter(
        start_time__isnull=False,
        end_time__isnull=False
    )
    
    if week_start:
        week_end = week_start + timedelta(days=6)
        entries = entries.filter(date__range=(week_start, week_end))
        print(f"\n📅 Analizando semana: {week_start} - {week_end}")
    else:
        print(f"\n📅 Analizando TODAS las entradas con start_time y end_time")
    
    entries = entries.select_related('employee', 'project').order_by(
        'employee__last_name', 'date', 'start_time'
    )
    
    print(f"📊 Total entradas a revisar: {entries.count()}")
    
    fixed_count = 0
    issues = []
    
    for entry in entries:
        expected_hours = calculate_hours(entry.start_time, entry.end_time)
        current_hours = entry.hours_worked or Decimal("0.00")
        
        # Verificar si hay discrepancia
        diff = abs(expected_hours - current_hours)
        
        if diff >= Decimal("0.01"):  # Diferencia de al menos 1 minuto
            emp_name = f"{entry.employee.first_name} {entry.employee.last_name}"
            co_info = f"CO:{entry.change_order_id}" if entry.change_order_id else "BASE"
            
            issues.append({
                'entry': entry,
                'current': current_hours,
                'expected': expected_hours,
                'diff': diff,
                'emp': emp_name,
                'co': co_info,
            })
            
            if not dry_run:
                entry.hours_worked = expected_hours
                entry.save(update_fields=['hours_worked'])
                fixed_count += 1
    
    # Mostrar resultados
    print(f"\n{'='*80}")
    print(f"{'DRY RUN - ' if dry_run else ''}RESULTADOS")
    print(f"{'='*80}\n")
    
    if issues:
        print(f"⚠️  Encontradas {len(issues)} entradas con discrepancias:\n")
        
        # Agrupar por empleado
        from collections import defaultdict
        by_emp = defaultdict(list)
        for issue in issues:
            by_emp[issue['emp']].append(issue)
        
        for emp, emp_issues in sorted(by_emp.items()):
            print(f"\n👤 {emp}:")
            total_diff = Decimal("0")
            for issue in emp_issues:
                e = issue['entry']
                print(f"   📅 {e.date} | {e.start_time.strftime('%H:%M')}-{e.end_time.strftime('%H:%M')} | "
                      f"Actual: {issue['current']}h → Esperado: {issue['expected']}h | "
                      f"Diff: +{issue['diff']}h | {issue['co']}")
                total_diff += issue['diff']
            print(f"   ─────────────────────────────")
            print(f"   Total horas faltantes: {total_diff}h")
        
        if dry_run:
            print(f"\n🔍 DRY RUN: No se hicieron cambios. Ejecuta sin --dry-run para corregir.")
        else:
            print(f"\n✅ Corregidas {fixed_count} entradas.")
    else:
        print("✅ Todas las entradas tienen hours_worked correcto.")
    
    print(f"\n{'='*80}\n")


if __name__ == "__main__":
    main()
