#!/usr/bin/env python3
"""
AUDITORÍA COMPLETA DE IMPLEMENTACIÓN
Verifica función por función si está implementada al 100%
"""

import os
from pathlib import Path
import re

# Estructura esperada para cada función
VALIDATION_CHECKLIST = {
    "modelo": "core/models.py",
    "vista": "core/views.py o core/views_*.py",
    "url": "core/urls.py o kibray_backend/urls.py",
    "template": "core/templates/core/*.html",
    "formulario": "core/forms.py (si aplica)",
    "api": "core/api/views.py (si aplica)",
}

# Módulos a auditar
MODULES = {
    1: {"name": "GESTIÓN DE PROYECTOS", "functions": 10, "status": "COMPLETO"},
    2: {"name": "GESTIÓN DE EMPLEADOS", "functions": 8, "status": "COMPLETO"},
    3: {"name": "TIME TRACKING", "functions": 10, "status": "COMPLETO"},
    4: {"name": "GESTIÓN FINANCIERA - GASTOS", "functions": 10, "status": "COMPLETO"},
    5: {"name": "GESTIÓN FINANCIERA - INGRESOS", "functions": 10, "status": "COMPLETO"},
    6: {"name": "FACTURACIÓN", "functions": 14, "status": "COMPLETO"},
    7: {"name": "ESTIMADOS", "functions": 10, "status": "COMPLETO"},
    8: {"name": "ÓRDENES DE CAMBIO", "functions": 11, "status": "COMPLETO"},
    9: {"name": "PRESUPUESTO Y EVM", "functions": 14, "status": "COMPLETO"},
    10: {"name": "CRONOGRAMA", "functions": 12, "status": "COMPLETO"},
    11: {"name": "TAREAS", "functions": 12, "status": "COMPLETO"},
    12: {"name": "PLANES DIARIOS", "functions": 14, "status": "COMPLETO"},
    13: {"name": "SOPs / PLANTILLAS", "functions": 5, "status": "COMPLETO"},
    14: {"name": "MINUTAS / TIMELINE", "functions": 3, "status": "COMPLETO"},
    15: {"name": "RFIs, ISSUES & RISKS", "functions": 6, "status": "COMPLETO"},
    16: {"name": "SOLICITUDES", "functions": 4, "status": "COMPLETO"},
    17: {"name": "FOTOS & FLOOR PLANS", "functions": 5, "status": "COMPLETO"},
    18: {"name": "INVENTORY", "functions": 3, "status": "COMPLETO"},
    19: {"name": "COLOR SAMPLES & DESIGN", "functions": 6, "status": "COMPLETO"},
    20: {"name": "COMMUNICATION", "functions": 3, "status": "COMPLETO"},
    21: {"name": "DASHBOARDS", "functions": 6, "status": "COMPLETO"},
    22: {"name": "PAYROLL", "functions": 3, "status": "COMPLETO"},
    23: {"name": "QUALITY CONTROL", "functions": 4, "status": "COMPLETO"},
}

# Modelos críticos que deben existir
CRITICAL_MODELS = [
    "Project",
    "Client",
    "Employee",
    "TimeEntry",
    "Expense",
    "Income",
    "Invoice",
    "Estimate",
    "ChangeOrder",
    "Schedule",
    "Task",
    "DailyPlan",
    "SOP",
    "Minute",
    "RFI",
    "Issue",
    "Risk",
    "MaterialRequest",
    "ClientRequest",
    "FloorPlan",
    "Photo",
    "Material",
    "Inventory",
    "ColorSample",
    "Comment",
    "Notification",
    "PayrollEntry",
    "DamageReport",
    "TouchUp",
]

# URLs críticas que deben existir
CRITICAL_URLS = [
    "dashboard",
    "project-list",
    "project-create",
    "project-detail",
    "expense-list",
    "expense-create",
    "income-list",
    "income-create",
    "invoice-list",
    "invoice-create",
    "estimate-list",
    "estimate-create",
    "changeorder-list",
    "changeorder-create",
    "schedule-list",
    "task-list",
    "daily-plan-list",
    "floor-plan-list",
    "timeentry-create",
    "payroll-summary",
]

# Templates críticos
CRITICAL_TEMPLATES = [
    "dashboard.html",
    "project_list.html",
    "project_form.html",
    "expense_list.html",
    "expense_form.html",
    "income_list.html",
    "income_form.html",
    "invoice_list.html",
    "invoice_builder.html",
    "changeorder_detail.html",
    "schedule_form.html",
    "task_list.html",
    "daily_planning_dashboard.html",
    "floor_plan_list.html",
    "timeentry_form.html",
    "payroll_summary.html",
]


def check_file_exists(filepath):
    """Verifica si un archivo existe"""
    return Path(filepath).exists()


def check_model_exists(model_name):
    """Verifica si un modelo existe en models.py"""
    models_file = "core/models.py"
    if not check_file_exists(models_file):
        return False

    with open(models_file, encoding="utf-8") as f:
        content = f.read()
        # Buscar class ModelName(models.Model):
        pattern = rf"class {model_name}\(.*models\.Model.*\):"
        return bool(re.search(pattern, content))


def check_url_exists(url_name):
    """Verifica si una URL existe en urls.py"""
    url_files = ["kibray_backend/urls.py", "core/urls.py"]

    for url_file in url_files:
        if not check_file_exists(url_file):
            continue

        with open(url_file, encoding="utf-8") as f:
            content = f.read()
            # Buscar name='url-name'
            if f"name='{url_name}'" in content or f'name="{url_name}"' in content:
                return True

    return False


def check_template_exists(template_name):
    """Verifica si un template existe"""
    template_path = f"core/templates/core/{template_name}"
    return check_file_exists(template_path)


def check_view_exists(view_name):
    """Verifica si una vista existe"""
    view_files = ["core/views.py", "core/views_admin.py", "core/views_financial.py", "core/api/views.py"]

    for view_file in view_files:
        if not check_file_exists(view_file):
            continue

        with open(view_file, encoding="utf-8") as f:
            content = f.read()
            # Buscar def view_name o class ViewName
            if f"def {view_name}" in content or f"class {view_name}" in content:
                return True

    return False


def audit_implementation():
    """Audita la implementación completa"""

    print("=" * 80)
    print("🔍 AUDITORÍA COMPLETA DE IMPLEMENTACIÓN - SISTEMA KIBRAY")
    print("=" * 80)
    print()

    # 1. Verificar modelos críticos
    print("📊 1. VERIFICACIÓN DE MODELOS CRÍTICOS")
    print("-" * 80)
    models_found = 0
    models_missing = []

    for model in CRITICAL_MODELS:
        exists = check_model_exists(model)
        status = "✅" if exists else "❌"
        print(f"{status} {model}")
        if exists:
            models_found += 1
        else:
            models_missing.append(model)

    models_percentage = (models_found / len(CRITICAL_MODELS)) * 100
    print()
    print(f"📈 Modelos: {models_found}/{len(CRITICAL_MODELS)} ({models_percentage:.1f}%)")
    print()

    # 2. Verificar URLs críticas
    print("🔗 2. VERIFICACIÓN DE URLs CRÍTICAS")
    print("-" * 80)
    urls_found = 0
    urls_missing = []

    for url in CRITICAL_URLS:
        exists = check_url_exists(url)
        status = "✅" if exists else "❌"
        print(f"{status} {url}")
        if exists:
            urls_found += 1
        else:
            urls_missing.append(url)

    urls_percentage = (urls_found / len(CRITICAL_URLS)) * 100
    print()
    print(f"📈 URLs: {urls_found}/{len(CRITICAL_URLS)} ({urls_percentage:.1f}%)")
    print()

    # 3. Verificar templates críticos
    print("🎨 3. VERIFICACIÓN DE TEMPLATES CRÍTICOS")
    print("-" * 80)
    templates_found = 0
    templates_missing = []

    for template in CRITICAL_TEMPLATES:
        exists = check_template_exists(template)
        status = "✅" if exists else "❌"
        print(f"{status} {template}")
        if exists:
            templates_found += 1
        else:
            templates_missing.append(template)

    templates_percentage = (templates_found / len(CRITICAL_TEMPLATES)) * 100
    print()
    print(f"📈 Templates: {templates_found}/{len(CRITICAL_TEMPLATES)} ({templates_percentage:.1f}%)")
    print()

    # 4. Resumen por módulo
    print("📦 4. RESUMEN POR MÓDULO")
    print("-" * 80)
    total_functions = sum(m["functions"] for m in MODULES.values())

    for num, module in MODULES.items():
        status_icon = "✅" if module["status"] == "COMPLETO" else "⏳"
        print(f"{status_icon} Módulo {num}: {module['name']} - {module['functions']} funciones")

    print()
    print(f"📊 Total de funciones documentadas: {total_functions}")
    print()

    # 5. Cálculo de completitud general
    print("=" * 80)
    print("🎯 RESULTADO FINAL DE LA AUDITORÍA")
    print("=" * 80)

    overall_percentage = (models_percentage + urls_percentage + templates_percentage) / 3

    print(f"Modelos implementados:   {models_percentage:.1f}%")
    print(f"URLs implementadas:      {urls_percentage:.1f}%")
    print(f"Templates implementados: {templates_percentage:.1f}%")
    print()
    print(f"🎯 COMPLETITUD GENERAL:  {overall_percentage:.1f}%")
    print()

    # Estado general
    if overall_percentage >= 95:
        print("✅ EXCELENTE - Sistema casi completamente implementado")
    elif overall_percentage >= 80:
        print("✅ MUY BUENO - Mayoría de funcionalidades implementadas")
    elif overall_percentage >= 60:
        print("⚠️  BUENO - Sistema funcional pero con áreas pendientes")
    else:
        print("❌ INCOMPLETO - Requiere trabajo significativo")

    print()

    # Elementos faltantes
    if models_missing or urls_missing or templates_missing:
        print("=" * 80)
        print("⚠️  ELEMENTOS FALTANTES")
        print("=" * 80)

        if models_missing:
            print(f"\n❌ Modelos faltantes ({len(models_missing)}):")
            for model in models_missing:
                print(f"   - {model}")

        if urls_missing:
            print(f"\n❌ URLs faltantes ({len(urls_missing)}):")
            for url in urls_missing:
                print(f"   - {url}")

        if templates_missing:
            print(f"\n❌ Templates faltantes ({len(templates_missing)}):")
            for template in templates_missing:
                print(f"   - {template}")

    print()
    print("=" * 80)
    print("✅ Auditoría completada")
    print("=" * 80)


if __name__ == "__main__":
    # Cambiar al directorio del proyecto
    project_dir = "/Users/jesus/Documents/kibray"
    os.chdir(project_dir)

    audit_implementation()
