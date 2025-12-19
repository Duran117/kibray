#!/usr/bin/env python
"""
Script de diagnóstico rápido para el usuario cesar123
Ejecutar en Railway: railway run python diagnose_cesar123.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kibray.settings')
django.setup()

from django.contrib.auth.models import User
from django.utils import timezone
from core.models import Employee, Project, ResourceAssignment, TimeEntry

print("=" * 80)
print("DIAGNÓSTICO: Usuario cesar123")
print("=" * 80)

# 1. Verificar usuario existe
try:
    user = User.objects.get(username='cesar123')
    print(f"✅ Usuario encontrado: {user.username} (ID: {user.id})")
    print(f"   - Email: {user.email}")
    print(f"   - Staff: {user.is_staff}")
    print(f"   - Activo: {user.is_active}")
except User.DoesNotExist:
    print("❌ Usuario 'cesar123' NO EXISTE en la base de datos")
    exit(1)

# 2. Verificar vinculación Employee
try:
    employee = Employee.objects.get(user=user)
    print(f"✅ Empleado vinculado: {employee.first_name} {employee.last_name} (ID: {employee.id})")
    print(f"   - Email: {employee.email}")
    print(f"   - Teléfono: {employee.phone}")
    print(f"   - Activo: {employee.is_active}")
except Employee.DoesNotExist:
    print("❌ El usuario NO tiene un Employee vinculado")
    print("   Solución: Crear Employee en admin y vincularlo a este User")
    exit(1)

# 3. Verificar asignaciones hoy
today = timezone.localdate()
print(f"\n📅 Fecha de hoy: {today}")

assignments_today = ResourceAssignment.objects.filter(
    employee=employee,
    date=today
).select_related('project')

print(f"\n📋 Asignaciones para HOY ({today}):")
if assignments_today.exists():
    for assignment in assignments_today:
        print(f"   ✅ Proyecto: {assignment.project.name} (ID: {assignment.project.id})")
        print(f"      - Turno: {assignment.shift}")
        print(f"      - Rol: {assignment.role}")
else:
    print("   ❌ NO tiene asignaciones para hoy")
    print("   Solución: Crear ResourceAssignment en admin para este empleado y hoy")

# 4. Verificar proyectos disponibles (según lógica del view)
print(f"\n🎯 Proyectos disponibles para clock-in:")
if user.is_staff:
    available_projects = Project.objects.all()
    print(f"   Staff/Admin: TODOS los proyectos ({available_projects.count()})")
elif assignments_today.exists():
    my_projects = Project.objects.filter(
        resource_assignments__in=assignments_today
    ).distinct()
    print(f"   Empleado con asignaciones: {my_projects.count()} proyectos")
    for proj in my_projects:
        print(f"      ✅ {proj.name} (ID: {proj.id})")
else:
    print(f"   ❌ Empleado SIN asignaciones: 0 proyectos")
    print(f"   Clock-in NO permitido (flujo de excepción)")

# 5. Verificar TimeEntry abierto
print(f"\n⏰ Estado de TimeEntry:")
open_entry = TimeEntry.objects.filter(
    employee=employee,
    end_time__isnull=True
).order_by('-date', '-start_time').first()

if open_entry:
    print(f"   ⚠️  Tiene entrada ABIERTA:")
    print(f"      - Proyecto: {open_entry.project.name}")
    print(f"      - Fecha: {open_entry.date}")
    print(f"      - Inicio: {open_entry.start_time}")
    print(f"   Debe hacer clock-out primero")
else:
    print(f"   ✅ No tiene entradas abiertas - puede hacer clock-in")

# 6. Historial reciente
print(f"\n📊 Últimas 5 entradas:")
recent_entries = TimeEntry.objects.filter(employee=employee).order_by('-date', '-start_time')[:5]
if recent_entries.exists():
    for entry in recent_entries:
        status = "ABIERTO" if entry.end_time is None else f"Cerrado ({entry.hours_worked}h)"
        print(f"   - {entry.date} | {entry.project.name} | {entry.start_time} | {status}")
else:
    print(f"   (No hay entradas previas)")

print("\n" + "=" * 80)
print("FIN DEL DIAGNÓSTICO")
print("=" * 80)
