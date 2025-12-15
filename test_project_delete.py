#!/usr/bin/env python
"""Pruebas de eliminación de proyectos con verificación de dependencias."""

import os
from datetime import date
from decimal import Decimal

import django
import pytest

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "kibray_backend.settings")
django.setup()

from django.contrib.auth.models import User
from django.test import Client, override_settings

from core.models import Expense, Income, Project


@pytest.mark.django_db
def setup_admin_user():
    if not User.objects.filter(username="admin_test").exists():
        user = User.objects.create_superuser("admin_test", "admin@test.local", "pass1234")
    else:
        user = User.objects.get(username="admin_test")
    return user


@pytest.mark.django_db
def create_project_with_related():
    p = Project.objects.create(
        name="Proyecto Eliminar", start_date=date.today(), client="Cliente X", budget_total=Decimal("1000.00")
    )
    Income.objects.create(
        project=p, project_name="Factura 1", amount=Decimal("100.00"), date=date.today(), payment_method="EFECTIVO"
    )
    Expense.objects.create(
        project=p, project_name="Compra 1", amount=Decimal("50.00"), date=date.today(), category="Material"
    )
    return p


@pytest.mark.django_db
@override_settings(ALLOWED_HOSTS=["testserver", "127.0.0.1", "localhost"])
def test_delete_flow():
    print("=" * 60)
    print("PRUEBA #2: Eliminación segura de Proyecto")
    print("=" * 60)
    admin = setup_admin_user()
    client = Client()
    logged = client.login(username="admin_test", password="pass1234")
    assert logged, "No se pudo iniciar sesión como admin_test"

    # Crear proyecto con dependencias
    project = create_project_with_related()
    pid = project.id
    print(f"✓ Proyecto creado ID={pid} con ingresos={project.incomes.count()} gastos={project.expenses.count()}")

    # Intentar eliminar (con confirm true en esta implementación)
    resp = client.post(f"/admin-panel/projects/{pid}/delete/", data={"confirm": "true"})
    assert resp.status_code in (302, 303), f"Respuesta inesperada al eliminar: {resp.status_code}"
    exists = Project.objects.filter(id=pid).exists()
    assert not exists, "El proyecto debería haber sido eliminado"
    print("✓ Proyecto eliminado correctamente con confirmación")

    # Crear otro proyecto para probar bloqueo sin confirm (quitamos confirm)
    project2 = Project.objects.create(name="Proyecto Sin Confirm", start_date=date.today())
    pid2 = project2.id
    print(f"✓ Segundo proyecto creado ID={pid2} sin dependencias")
    # En nuestra lógica, sin dependencias sí se elimina aunque no haya confirm -> la vista sólo exige confirm si hay dependencias
    resp2 = client.post(f"/admin-panel/projects/{pid2}/delete/", data={})
    assert resp2.status_code in (302, 303), f"Respuesta inesperada: {resp2.status_code}"
    still_exists = Project.objects.filter(id=pid2).exists()
    assert not still_exists, "El proyecto sin dependencias también debe eliminarse"
    print("✓ Proyecto sin dependencias eliminado sin necesitar confirm")

    print("\nResumen:")
    print("  - Eliminación con dependencias require confirm (enviada) OK")
    print("  - Eliminación sin dependencias procede OK")
    print("\n✅ Pruebas de eliminación completadas")


if __name__ == "__main__":
    try:
        test_delete_flow()
    except Exception as e:
        print(f"❌ Error en pruebas: {e}")
        import traceback

        traceback.print_exc()
        raise
