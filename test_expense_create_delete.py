#!/usr/bin/env python
"""Pruebas de creación y eliminación de gastos"""

import os
from datetime import date
from decimal import Decimal

import django
import pytest

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "kibray_backend.settings")
django.setup()

from django.contrib.auth.models import User
from django.db.models import Sum
from django.test import Client, override_settings

from core.models import Expense, Project


@pytest.mark.django_db
@override_settings(ALLOWED_HOSTS=["testserver", "127.0.0.1", "localhost"])
def test_expense_create_delete_flow():
    print("=" * 60)
    print("PRUEBA #5 y #6: Crear y Eliminar Gasto")
    print("=" * 60)
    # Usuario admin
    if not User.objects.filter(username="admin_test").exists():
        User.objects.create_superuser("admin_test", "admin@test.local", "pass1234")
    client = Client()
    assert client.login(username="admin_test", password="pass1234"), "Login admin falló"

    # Asegurar proyecto base
    project, _ = Project.objects.get_or_create(name="Proyecto Gastos CRUD", start_date=date.today())
    total_before = project.total_expenses
    print(f"Total de gastos antes: {total_before}")

    # Crear gasto vía vista
    resp_create = client.post(
        "/admin-panel/expenses/create/",
        data={
            "project": project.id,
            "project_name": "Compra Tornillos",
            "amount": "45.30",
            "date": date.today().strftime("%Y-%m-%d"),
            "category": "MATERIALES",
            "description": "Caja de tornillos acero",
        },
    )
    assert resp_create.status_code in (302, 303), f"Respuesta inesperada creación {resp_create.status_code}"
    project.refresh_from_db()
    total_after_create = project.total_expenses
    print(f"Total después de crear: {total_after_create}")
    assert total_after_create >= total_before + Decimal("45.30") - Decimal("0.01"), "Total no refleja nuevo gasto"

    expense = Expense.objects.filter(project=project, project_name="Compra Tornillos").first()
    assert expense, "Gasto creado no encontrado"
    eid = expense.id

    # Eliminar gasto vía vista
    resp_delete = client.post(f"/admin-panel/expenses/{eid}/delete/", data={})
    assert resp_delete.status_code in (302, 303), f"Respuesta inesperada eliminación {resp_delete.status_code}"
    project.refresh_from_db()
    total_after_delete = project.total_expenses
    print(f"Total después de eliminar: {total_after_delete}")
    sum_remaining = project.expenses.aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
    assert project.total_expenses == sum_remaining, "Total del proyecto no coincide con suma real de gastos restantes"

    print("\n✅ PRUEBAS DE CREACIÓN Y ELIMINACIÓN DE GASTO COMPLETADAS")


if __name__ == "__main__":
    test_expense_create_delete_flow()
