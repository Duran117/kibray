#!/usr/bin/env python
"""
Script para poblar la base de datos con datos de prueba para analytics.
Esto permitirá probar las APIs de ColorApproval y PMPerformance.
"""

from datetime import datetime, timedelta
import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "kibray_backend.settings")
django.setup()

from django.contrib.auth.models import User

from core.models import ColorApproval, Project, ProjectManagerAssignment


def seed_data():
    print("🌱 Iniciando seed de datos para analytics...")

    # Obtener o crear usuarios
    admin = User.objects.filter(is_superuser=True).first()
    if not admin:
        admin = User.objects.create_superuser("admin", "admin@kibray.com", "admin123")
        print(f"✅ Usuario admin creado: {admin.username}")
    else:
        print(f"✅ Usuario admin encontrado: {admin.username}")

    # Crear PM users si no existen
    pm1, _ = User.objects.get_or_create(
        username="pm_juan", defaults={"email": "juan@kibray.com", "first_name": "Juan", "last_name": "Pérez"}
    )
    pm2, _ = User.objects.get_or_create(
        username="pm_maria", defaults={"email": "maria@kibray.com", "first_name": "María", "last_name": "González"}
    )
    print(f"✅ PMs creados/encontrados: {pm1.username}, {pm2.username}")

    # Obtener proyectos existentes
    projects = Project.objects.all()[:3]
    if not projects:
        print("⚠️  No hay proyectos en la base de datos. Crea proyectos primero.")
        return

    print(f"✅ Proyectos encontrados: {len(projects)}")

    # Crear ColorApprovals para testing
    color_approvals_data = [
        {
            "project": projects[0],
            "status": "PENDING",
            "color_name": "Blanco Polar",
            "color_code": "WP-001",
            "brand": "Sherwin Williams",
            "location": "Sala principal",
            "requested_by": admin,
        },
        {
            "project": projects[0],
            "status": "APPROVED",
            "color_name": "Gris Urbano",
            "color_code": "GU-045",
            "brand": "Sherwin Williams",
            "location": "Habitación 1",
            "requested_by": admin,
            "approved_by": admin,
            "signed_at": datetime.now() - timedelta(days=2),
        },
        {
            "project": projects[0],
            "status": "REJECTED",
            "color_name": "Azul Marino",
            "color_code": "AM-120",
            "brand": "Benjamin Moore",
            "location": "Cocina",
            "requested_by": admin,
            "notes": "Cliente prefiere un tono más claro",
        },
    ]

    if len(projects) > 1:
        color_approvals_data.extend(
            [
                {
                    "project": projects[1],
                    "status": "PENDING",
                    "color_name": "Beige Natural",
                    "color_code": "BN-033",
                    "brand": "Behr",
                    "location": "Exterior fachada",
                    "requested_by": admin,
                },
                {
                    "project": projects[1],
                    "status": "APPROVED",
                    "color_name": "Verde Olivo",
                    "color_code": "VO-088",
                    "brand": "Benjamin Moore",
                    "location": "Sala de estar",
                    "requested_by": admin,
                    "approved_by": admin,
                    "signed_at": datetime.now() - timedelta(days=5),
                },
            ]
        )

    # Crear las ColorApprovals
    created_count = 0
    for data in color_approvals_data:
        # Verificar si ya existe
        exists = ColorApproval.objects.filter(project=data["project"], color_name=data["color_name"]).exists()

        if not exists:
            ColorApproval.objects.create(**data)
            created_count += 1

    print(f"✅ ColorApprovals creados: {created_count}/{len(color_approvals_data)}")

    # Crear PM Assignments
    assignments_data = [
        {"project": projects[0], "pm": pm1},
        {"project": projects[1] if len(projects) > 1 else projects[0], "pm": pm2},
    ]

    if len(projects) > 2:
        assignments_data.append({"project": projects[2], "pm": pm1})

    assigned_count = 0
    for data in assignments_data:
        obj, created = ProjectManagerAssignment.objects.get_or_create(**data)
        if created:
            assigned_count += 1

    print(f"✅ PM Assignments creados: {assigned_count}/{len(assignments_data)}")

    # Resumen
    print("\n📊 Resumen de datos creados:")
    print(f"   - ColorApprovals total: {ColorApproval.objects.count()}")
    print(f"     • Pending: {ColorApproval.objects.filter(status='PENDING').count()}")
    print(f"     • Approved: {ColorApproval.objects.filter(status='APPROVED').count()}")
    print(f"     • Rejected: {ColorApproval.objects.filter(status='REJECTED').count()}")
    print(f"   - PM Assignments: {ProjectManagerAssignment.objects.count()}")
    print(f"   - Projects: {Project.objects.count()}")
    print(f"   - PMs: {User.objects.filter(username__startswith='pm_').count()}")
    print("\n✅ Seed completado exitosamente!")


if __name__ == "__main__":
    seed_data()
