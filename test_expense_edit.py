#!/usr/bin/env python
"""Prueba de edición de gastos (Expense)"""

import os
from datetime import date
from decimal import Decimal

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "kibray_backend.settings")
django.setup()

from django.contrib.auth.models import User
from django.test import Client, override_settings

from core.models import Expense, Project


@override_settings(ALLOWED_HOSTS=["testserver", "127.0.0.1", "localhost"])
def test_expense_edit_flow():
    print("=" * 60)
    print("PRUEBA #4: Edición de Gasto")
    print("=" * 60)
    # Usuario admin
    if not User.objects.filter(username="admin_test").exists():
        User.objects.create_superuser("admin_test", "admin@test.local", "pass1234")
    client = Client()
    assert client.login(username="admin_test", password="pass1234"), "Login admin falló"

    # Asegurar proyecto base
    project, _ = Project.objects.get_or_create(name="Proyecto Gastos", start_date=date.today())

    # Crear gasto inicial
    expense = Expense.objects.create(
        project=project,
        amount=Decimal("120.50"),
        project_name="Compra Material",
        date=date.today(),
        category="MATERIALES",
    )
    eid = expense.id
    print(f"✓ Gasto inicial creado ID={eid} monto={expense.amount}")

    # Simular edición vía vista
    resp = client.post(
        f"/admin-panel/expenses/{eid}/edit/",
        data={
            "project": project.id,
            "project_name": "Compra Material Editada",
            "amount": "200.75",
            "date": date.today().strftime("%Y-%m-%d"),
            "category": "MATERIALES",
            "description": "Actualización de prueba",
        },
    )
    assert resp.status_code in (302, 303), f"Respuesta inesperada {resp.status_code}"

    expense.refresh_from_db()
    assert str(expense.amount) == "200.75", "Monto no actualizado"
    assert expense.project_name == "Compra Material Editada", "Nombre no actualizado"
    print("✓ Edición persistida correctamente")

    # Validación negativa (monto negativo)
    resp_bad = client.post(
        f"/admin-panel/expenses/{eid}/edit/",
        data={
            "project": project.id,
            "project_name": "Compra Material Editada",
            "amount": "-10",
            "date": date.today().strftime("%Y-%m-%d"),
            "category": "MATERIALES",
        },
    )
    # La vista debe devolver 200 porque renderiza con mensajes de error
    assert resp_bad.status_code == 200, "Debe quedarse en la misma página con errores"
    expense.refresh_from_db()
    assert str(expense.amount) == "200.75", "Monto cambió pese a error"
    print("✓ Validación de monto negativo funcionando")

    print("\n✅ PRUEBA DE EDICIÓN DE GASTO COMPLETADA")


if __name__ == "__main__":
    test_expense_edit_flow()
