"""
Script de diagnóstico para el problema de clock-in del empleado.
Verifica la lógica de asignación de proyectos disponibles.
"""
from datetime import timedelta
import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "kibray_backend.settings")
django.setup()

from django.contrib.auth import get_user_model
from django.utils import timezone

from core.models import Employee, Project, ResourceAssignment, TimeEntry

User = get_user_model()

def diagnose_employee_clock_in(username):
    """Diagnosticar el problema de clock-in para un empleado específico."""

    print(f"\n{'='*80}")
    print(f"DIAGNÓSTICO DE CLOCK-IN PARA USUARIO: {username}")
    print(f"{'='*80}\n")

    # 1. Verificar que el usuario existe
    try:
        user = User.objects.get(username=username)
        print(f"✅ Usuario encontrado: {user.username} (ID: {user.id})")
        print(f"   - Staff: {user.is_staff}")
        print(f"   - Superuser: {user.is_superuser}")
    except User.DoesNotExist:
        print(f"❌ Usuario '{username}' NO encontrado")
        return

    # 2. Verificar empleado vinculado
    try:
        employee = Employee.objects.get(user=user)
        print(f"\n✅ Empleado vinculado: {employee.first_name} {employee.last_name} (ID: {employee.id})")
    except Employee.DoesNotExist:
        print("\n❌ NO hay empleado vinculado a este usuario")
        return

    # 3. Variables de fecha
    today = timezone.localdate()
    recent_cutoff = today - timedelta(days=30)

    print(f"\n📅 Fecha de hoy: {today}")
    print(f"📅 Fecha de corte (últimos 30 días): {recent_cutoff}")

    # 4. Verificar asignaciones para HOY
    assignments_today = ResourceAssignment.objects.filter(
        employee=employee,
        date=today
    ).select_related("project")

    print(f"\n🔍 ASIGNACIONES PARA HOY ({today}):")
    if assignments_today.exists():
        print(f"   ✅ Encontradas {assignments_today.count()} asignación(es):")
        for i, assignment in enumerate(assignments_today, 1):
            print(f"      {i}. {assignment.project.name} (ID: {assignment.project.id})")
            print(f"         - Turno: {assignment.shift}")
            print(f"         - Fecha: {assignment.date}")
    else:
        print("   ⚠️  NO hay asignaciones específicas para hoy")

    # 5. Proyectos desde asignaciones de hoy
    projects_from_assignments = Project.objects.filter(
        resource_assignments__in=assignments_today
    ).distinct()

    print("\n🔍 PROYECTOS DESDE ASIGNACIONES DE HOY:")
    if projects_from_assignments.exists():
        print(f"   ✅ {projects_from_assignments.count()} proyecto(s):")
        for proj in projects_from_assignments:
            print(f"      - {proj.name} (ID: {proj.id})")
    else:
        print("   ⚠️  NO hay proyectos desde asignaciones de hoy")

    # 6. Trabajo reciente (últimos 30 días)
    projects_from_recent_work = Project.objects.filter(
        timeentry__employee=employee,
        timeentry__date__gte=recent_cutoff,
        is_archived=False
    ).distinct()

    print("\n🔍 PROYECTOS CON TRABAJO RECIENTE (últimos 30 días):")
    if projects_from_recent_work.exists():
        print(f"   ✅ {projects_from_recent_work.count()} proyecto(s):")
        for proj in projects_from_recent_work:
            last_entry = TimeEntry.objects.filter(
                employee=employee,
                project=proj
            ).order_by('-date').first()
            print(f"      - {proj.name} (ID: {proj.id})")
            if last_entry:
                print(f"        Último trabajo: {last_entry.date}")
    else:
        print("   ⚠️  NO hay proyectos con trabajo reciente")

    # 7. Proyectos activos (sin fecha de fin)
    active_projects = Project.objects.filter(
        end_date__isnull=True,
        is_archived=False
    ).distinct()

    print("\n🔍 PROYECTOS ACTIVOS (sin fecha de fin, no archivados):")
    print(f"   ℹ️  {active_projects.count()} proyecto(s) activos en total:")
    for proj in active_projects[:5]:  # Mostrar solo los primeros 5
        print(f"      - {proj.name} (ID: {proj.id})")
    if active_projects.count() > 5:
        print(f"      ... y {active_projects.count() - 5} más")

    # 8. Combinar todas las fuentes
    my_projects_combined = (
        projects_from_assignments |
        projects_from_recent_work |
        active_projects
    ).distinct()

    print("\n🎯 PROYECTOS DISPONIBLES PARA CLOCK-IN (combinados):")
    print(f"   ✅ {my_projects_combined.count()} proyecto(s) totales:")
    for proj in my_projects_combined[:10]:  # Mostrar solo los primeros 10
        sources = []
        if proj in projects_from_assignments:
            sources.append("asignación hoy")
        if proj in projects_from_recent_work:
            sources.append("trabajo reciente")
        if proj in active_projects:
            sources.append("activo")
        print(f"      - {proj.name} (ID: {proj.id}) [{', '.join(sources)}]")
    if my_projects_combined.count() > 10:
        print(f"      ... y {my_projects_combined.count() - 10} más")

    # 9. Determinar el modo de clock-in
    has_assignments_today = assignments_today.exists()
    has_any_valid_projects = my_projects_combined.exists()

    print("\n🚦 DECISIÓN DE POLÍTICA:")
    if user.is_staff:
        print("   🔓 Modo: OVERRIDE_ADMIN (usuario es staff)")
        print("   → Puede hacer clock-in en CUALQUIER proyecto")
    elif has_assignments_today:
        print("   ✅ Modo: ASSIGNED_TODAY")
        print(f"   → Puede hacer clock-in en proyectos asignados para hoy ({projects_from_assignments.count()})")
    elif has_any_valid_projects:
        print("   ℹ️  Modo: RECENT_OR_ACTIVE")
        print(f"   → Puede hacer clock-in en proyectos con trabajo reciente o activos ({my_projects_combined.count()})")
    else:
        print("   ⚠️  Modo: FALLBACK_ACTIVE")
        print(f"   → Puede hacer clock-in en proyectos activos como fallback ({active_projects.count()})")

    # 10. Verificar TimeEntry abierto
    open_entry = TimeEntry.objects.filter(
        employee=employee,
        end_time__isnull=True
    ).order_by("-date", "-start_time").first()

    print("\n⏰ ESTADO ACTUAL:")
    if open_entry:
        print("   🟢 Ya tiene un TimeEntry abierto:")
        print(f"      - Proyecto: {open_entry.project.name}")
        print(f"      - Inicio: {open_entry.start_time}")
        print(f"      - Fecha: {open_entry.date}")
    else:
        print("   ⚪ NO tiene TimeEntry abierto (puede hacer clock-in)")

    print(f"\n{'='*80}")
    print("DIAGNÓSTICO COMPLETO")
    print(f"{'='*80}\n")

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Uso: python diagnose_employee_clockin.py <username>")
        print("\nEjemplo: python diagnose_employee_clockin.py john.doe")
        sys.exit(1)

    username = sys.argv[1]
    diagnose_employee_clock_in(username)
