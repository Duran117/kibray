#!/usr/bin/env python
"""
Script de preparación para remoción futura de Invoice.is_paid (R3).

Este script analiza el uso actual del campo is_paid en el código y la BD,
genera reporte de dependencias y sugiere acciones antes de eliminar el campo.

Ejecutar antes de crear la migración final que elimine is_paid.

Uso:
    python scripts/check_invoice_is_paid_usage.py
"""
import os
import pathlib
import sys

PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "kibray_backend.settings")
import django

django.setup()


from core.models import Invoice


def check_code_references():
    """Busca referencias a is_paid en el código fuente."""
    print("=" * 60)
    print("ANÁLISIS DE REFERENCIAS EN CÓDIGO")
    print("=" * 60)

    # Buscar en archivos Python (excluyendo migraciones y este script)
    code_refs = []
    for root, dirs, files in os.walk(PROJECT_ROOT):
        # Skip ciertos directorios
        dirs[:] = [d for d in dirs if d not in [".venv", "__pycache__", "migrations", ".git", "node_modules"]]
        for file in files:
            if file.endswith(".py"):
                filepath = pathlib.Path(root) / file
                if "migrations" in str(filepath) or "check_invoice_is_paid" in str(filepath):
                    continue
                try:
                    with open(filepath, encoding="utf-8") as f:
                        lines = f.readlines()
                        for i, line in enumerate(lines, 1):
                            if "is_paid" in line and "Invoice" in line:
                                code_refs.append((str(filepath.relative_to(PROJECT_ROOT)), i, line.strip()))
                except Exception:
                    continue

    if code_refs:
        print(f"\n⚠️  Encontradas {len(code_refs)} referencias a Invoice.is_paid:")
        for filepath, lineno, line in code_refs[:10]:  # Mostrar primeras 10
            print(f"  {filepath}:{lineno} -> {line[:80]}")
        if len(code_refs) > 10:
            print(f"  ... y {len(code_refs) - 10} más.")
    else:
        print("\n✅ No se encontraron referencias directas a is_paid en código (fuera de modelo).")

    return code_refs


def check_database_usage():
    """Analiza uso actual del campo is_paid en la BD."""
    print("\n" + "=" * 60)
    print("ANÁLISIS DE DATOS EN BASE DE DATOS")
    print("=" * 60)

    total = Invoice.objects.count()
    if total == 0:
        print("\n✅ No hay facturas en BD (ambiente vacío).")
        return

    # Contar discrepancias entre is_paid y fully_paid derivado
    discrepancias = 0
    for inv in Invoice.objects.all():
        legacy = inv.is_paid
        derived = inv.fully_paid
        if legacy != derived:
            discrepancias += 1

    print(f"\nTotal facturas: {total}")
    print(f"Discrepancias is_paid vs fully_paid: {discrepancias}")

    if discrepancias > 0:
        print(f"\n⚠️  {discrepancias} facturas tienen is_paid != fully_paid.")
        print("   Recomendación: ejecutar migración de sincronización antes de remover campo.")
        # Mostrar ejemplos
        for inv in Invoice.objects.all()[:5]:
            if inv.is_paid != inv.fully_paid:
                print(
                    f"   Invoice #{inv.id}: is_paid={inv.is_paid}, fully_paid={inv.fully_paid}, amount_paid={inv.amount_paid}, total={inv.total_amount}"
                )
    else:
        print("\n✅ Todos los valores is_paid están sincronizados con fully_paid.")

    return discrepancias


def check_constraints():
    """Verifica si hay constraints o índices usando is_paid."""
    print("\n" + "=" * 60)
    print("ANÁLISIS DE CONSTRAINTS E ÍNDICES")
    print("=" * 60)

    # Django no expone fácilmente índices custom via ORM; este check es informativo
    print("\n⚠️  Revisar manualmente:")
    print("   1. Índices personalizados en BD que incluyan is_paid")
    print("   2. Triggers o stored procedures que lean/escriban is_paid")
    print("   3. Reportes externos o integraciones consumiendo is_paid")
    print("\n   Comando sugerido (PostgreSQL):")
    print("   SELECT indexname FROM pg_indexes WHERE tablename='core_invoice' AND indexdef LIKE '%is_paid%';")


def generate_migration_plan():
    """Genera plan de migración sugerido."""
    print("\n" + "=" * 60)
    print("PLAN DE MIGRACIÓN SUGERIDO (R3)")
    print("=" * 60)

    print(
        """
Pasos para remover Invoice.is_paid:

1. Sincronización previa (si hay discrepancias):
   - Crear migración RunPython que recorra todas las facturas
   - Actualizar is_paid = (amount_paid >= total_amount) para cada Invoice
   - Ejecutar antes de remoción

2. Actualizar serializers y vistas:
   - Buscar todos los usos de 'is_paid' en serializers
   - Reemplazar por computed field 'fully_paid' o derivar en to_representation()
   - Actualizar tests que lean is_paid

3. Crear migración de remoción:
   - RemoveField('invoice', 'is_paid')
   - Añadir constraint opcional: CHECK (amount_paid <= total_amount * 1.25)
   
4. Actualizar documentación:
   - API_README.md: documentar que fully_paid reemplaza is_paid
   - Changelog: marcar como breaking change para clientes externos

5. Validación post-migración:
   - Ejecutar tests completos
   - Verificar dashboards y reportes siguen funcionando
   - Monitorear logs por 48h por errores relacionados

Archivo de migración sugerido (nombre): core/migrations/XXXX_remove_invoice_is_paid.py
"""
    )


def main():
    print("📋 Script de Preparación: Remoción de Invoice.is_paid")
    print("=" * 60)

    code_refs = check_code_references()
    discrepancias = check_database_usage()
    check_constraints()
    generate_migration_plan()

    print("\n" + "=" * 60)
    print("RESUMEN")
    print("=" * 60)

    issues = []
    if code_refs:
        issues.append(f"{len(code_refs)} referencias en código")
    if discrepancias and discrepancias > 0:
        issues.append(f"{discrepancias} discrepancias en BD")

    if issues:
        print(f"\n⚠️  Acción requerida: {', '.join(issues)}")
        print("   Ejecutar correcciones antes de proceder con remoción.")
    else:
        print("\n✅ Sistema listo para remoción de is_paid.")
        print("   Proceder con creación de migración según plan.")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
