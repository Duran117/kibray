#!/usr/bin/env python
"""
Script para vincular usuario cesar123 con Employee y crear asignación
Ejecutar: railway run python fix_cesar123.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kibray.settings')
django.setup()

from django.contrib.auth.models import User
from django.utils import timezone
from core.models import Employee, Project, ResourceAssignment

print("=" * 80)
print("FIX: Vinculación cesar123 → Employee y asignación a proyecto")
print("=" * 80)

# 1. Verificar usuario
try:
    user = User.objects.get(username='cesar123')
    print(f"✅ Usuario encontrado: {user.username} (ID: {user.id})")
except User.DoesNotExist:
    print("❌ Usuario 'cesar123' NO EXISTE")
    exit(1)

# 2. Buscar o crear Employee
employee = Employee.objects.filter(user=user).first()

if employee:
    print(f"✅ Ya tiene Employee vinculado: {employee.first_name} {employee.last_name} (ID: {employee.id})")
else:
    print("\n❌ NO tiene Employee vinculado")
    print("\nBuscando Employees sin User asignado...")
    
    # Buscar employees sin user
    unassigned_employees = Employee.objects.filter(user__isnull=True)
    
    if unassigned_employees.exists():
        print(f"\nEmployees disponibles ({unassigned_employees.count()}):")
        for i, emp in enumerate(unassigned_employees, 1):
            print(f"  {i}. {emp.first_name} {emp.last_name} - {emp.email}")
        
        print("\n¿Es cesar123 alguno de estos empleados?")
        print("Si SÍ: Vincúlalo manualmente en admin o con:")
        print(f"  employee = Employee.objects.get(id=X)")
        print(f"  employee.user = User.objects.get(username='cesar123')")
        print(f"  employee.save()")
    else:
        print("\nNo hay employees sin vincular. Creando nuevo Employee...")
        
        # Crear nuevo Employee
        employee = Employee.objects.create(
            user=user,
            first_name=user.first_name or "César",
            last_name=user.last_name or "Empleado",
            email=user.email or "cesar123@kibray.com",
            phone="",
            hire_date=timezone.now().date(),
            is_active=True,
            hourly_rate=25.00  # Rate por defecto
        )
        print(f"✅ Employee creado: {employee.first_name} {employee.last_name} (ID: {employee.id})")

# Si ahora tenemos employee vinculado, verificar/crear asignación
if employee:
    print("\n" + "=" * 80)
    print("ASIGNACIÓN A PROYECTO")
    print("=" * 80)
    
    # Verificar proyecto 308 Frisco
    try:
        project = Project.objects.get(id=308)
        print(f"✅ Proyecto encontrado: {project.name} (ID: {project.id})")
    except Project.DoesNotExist:
        print("❌ Proyecto ID 308 NO EXISTE")
        print("\nProyectos disponibles:")
        projects = Project.objects.all()[:10]
        for p in projects:
            print(f"  - {p.id}: {p.name}")
        exit(1)
    
    # Verificar asignación para hoy
    today = timezone.localdate()
    assignment = ResourceAssignment.objects.filter(
        employee=employee,
        project=project,
        date=today
    ).first()
    
    if assignment:
        print(f"✅ Ya tiene asignación para HOY ({today})")
        print(f"   - Turno: {assignment.shift}")
        print(f"   - Rol: {assignment.role}")
    else:
        print(f"\n❌ NO tiene asignación para HOY ({today})")
        print("Creando asignación...")
        
        assignment = ResourceAssignment.objects.create(
            employee=employee,
            project=project,
            date=today,
            shift="morning",  # Puede ser morning, afternoon, evening
            role="laborer"    # Puede ser laborer, supervisor, etc
        )
        print(f"✅ Asignación creada:")
        print(f"   - Empleado: {employee}")
        print(f"   - Proyecto: {project.name}")
        print(f"   - Fecha: {today}")
        print(f"   - Turno: {assignment.shift}")

print("\n" + "=" * 80)
print("✅ FIX COMPLETADO")
print("=" * 80)
print("\nAhora cesar123 debería poder hacer clock-in al proyecto 308 Frisco")
print("Recarga el dashboard y prueba de nuevo.")
