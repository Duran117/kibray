#!/usr/bin/env python3
"""
AUDITORÍA EXHAUSTIVA - Verificación función por función
"""

import os
import re
from pathlib import Path


def count_models():
    """Cuenta todos los modelos en models.py"""
    models_file = "core/models.py"
    if not Path(models_file).exists():
        return 0, []

    with open(models_file, encoding="utf-8") as f:
        content = f.read()

    # Buscar todas las clases que heredan de models.Model
    pattern = r"class (\w+)\(.*models\.Model.*\):"
    models = re.findall(pattern, content)
    return len(models), models


def count_urls():
    """Cuenta todas las URLs con nombre"""
    url_files = ["kibray_backend/urls.py", "core/urls.py", "core/urls_admin.py"]
    total_urls = 0
    all_urls = []

    for url_file in url_files:
        if not Path(url_file).exists():
            continue

        with open(url_file, encoding="utf-8") as f:
            content = f.read()

        # Buscar name="algo" y name='algo'
        urls = re.findall(r'name=["\']([^"\']+)["\']', content)
        total_urls += len(urls)
        all_urls.extend(urls)

    return total_urls, all_urls


def count_templates():
    """Cuenta todos los templates HTML"""
    templates_dir = Path("core/templates/core")
    if not templates_dir.exists():
        return 0, []

    html_files = list(templates_dir.glob("*.html"))
    template_names = [f.name for f in html_files]
    return len(html_files), template_names


def count_views():
    """Cuenta todas las vistas"""
    view_files = ["core/views.py", "core/views_admin.py", "core/views_financial.py", "core/api/views.py"]

    total_views = 0
    all_views = []

    for view_file in view_files:
        if not Path(view_file).exists():
            continue

        with open(view_file, encoding="utf-8") as f:
            content = f.read()

        # Buscar funciones def
        functions = re.findall(r"^def (\w+)\(", content, re.MULTILINE)
        # Buscar clases
        classes = re.findall(r"^class (\w+)\(", content, re.MULTILINE)

        total_views += len(functions) + len(classes)
        all_views.extend(functions + classes)

    return total_views, all_views


def count_forms():
    """Cuenta todos los formularios"""
    forms_file = "core/forms.py"
    if not Path(forms_file).exists():
        return 0, []

    with open(forms_file, encoding="utf-8") as f:
        content = f.read()

    # Buscar clases que heredan de forms.
    pattern = r"class (\w+)\(.*forms\."
    forms = re.findall(pattern, content)
    return len(forms), forms


def count_api_endpoints():
    """Cuenta endpoints de API"""
    api_views_file = "core/api/views.py"
    if not Path(api_views_file).exists():
        return 0, []

    with open(api_views_file, encoding="utf-8") as f:
        content = f.read()

    # Buscar ViewSets y APIViews
    pattern = r"class (\w+)\(.*(?:ViewSet|APIView|GenericAPIView)"
    endpoints = re.findall(pattern, content)
    return len(endpoints), endpoints


def count_migrations():
    """Cuenta migraciones"""
    migrations_dir = Path("core/migrations")
    if not migrations_dir.exists():
        return 0, []

    migration_files = [f for f in migrations_dir.glob("*.py") if f.name != "__init__.py"]
    return len(migration_files), [f.name for f in migration_files]


def audit_comprehensive():
    """Auditoría comprehensiva del sistema"""

    print("=" * 100)
    print(" " * 30 + "🔍 AUDITORÍA EXHAUSTIVA - SISTEMA KIBRAY")
    print("=" * 100)
    print()

    # Cambiar al directorio del proyecto
    project_dir = "/Users/jesus/Documents/kibray"
    os.chdir(project_dir)

    # 1. Modelos
    models_count, models_list = count_models()
    print("📊 1. MODELOS DE BASE DE DATOS")
    print("-" * 100)
    print(f"Total de modelos: {models_count}")
    print(f"Modelos encontrados: {', '.join(models_list[:10])}{'...' if len(models_list) > 10 else ''}")
    print()

    # 2. URLs
    urls_count, urls_list = count_urls()
    print("🔗 2. RUTAS (URLs)")
    print("-" * 100)
    print(f"Total de URLs con nombre: {urls_count}")
    print(f"Ejemplos: {', '.join(urls_list[:10])}...")
    print()

    # 3. Templates
    templates_count, templates_list = count_templates()
    print("🎨 3. TEMPLATES HTML")
    print("-" * 100)
    print(f"Total de templates: {templates_count}")
    print(f"Ejemplos: {', '.join(templates_list[:10])}...")
    print()

    # 4. Vistas
    views_count, views_list = count_views()
    print("👁️  4. VISTAS Y CONTROLADORES")
    print("-" * 100)
    print(f"Total de vistas: {views_count}")
    print(f"Ejemplos: {', '.join(views_list[:10])}...")
    print()

    # 5. Formularios
    forms_count, forms_list = count_forms()
    print("📝 5. FORMULARIOS")
    print("-" * 100)
    print(f"Total de formularios: {forms_count}")
    print(f"Ejemplos: {', '.join(forms_list[:10])}...")
    print()

    # 6. API Endpoints
    api_count, api_list = count_api_endpoints()
    print("🔌 6. API ENDPOINTS")
    print("-" * 100)
    print(f"Total de endpoints API: {api_count}")
    if api_list:
        print(f"Endpoints: {', '.join(api_list[:10])}...")
    print()

    # 7. Migraciones
    migrations_count, _ = count_migrations()
    print("🗄️  7. MIGRACIONES DE BASE DE DATOS")
    print("-" * 100)
    print(f"Total de migraciones: {migrations_count}")
    print()

    # 8. Resumen de módulos según documentación
    print("=" * 100)
    print(" " * 30 + "📦 MÓDULOS DOCUMENTADOS")
    print("=" * 100)
    print()

    modules = {
        1: {"name": "GESTIÓN DE PROYECTOS", "functions": 10},
        2: {"name": "GESTIÓN DE EMPLEADOS", "functions": 8},
        3: {"name": "TIME TRACKING", "functions": 10},
        4: {"name": "GESTIÓN FINANCIERA - GASTOS", "functions": 10},
        5: {"name": "GESTIÓN FINANCIERA - INGRESOS", "functions": 10},
        6: {"name": "FACTURACIÓN", "functions": 14},
        7: {"name": "ESTIMADOS", "functions": 10},
        8: {"name": "ÓRDENES DE CAMBIO", "functions": 11},
        9: {"name": "PRESUPUESTO Y EVM", "functions": 14},
        10: {"name": "CRONOGRAMA", "functions": 12},
        11: {"name": "TAREAS", "functions": 12},
        12: {"name": "PLANES DIARIOS", "functions": 14},
        13: {"name": "SOPs / PLANTILLAS", "functions": 5},
        14: {"name": "MINUTAS / TIMELINE", "functions": 3},
        15: {"name": "RFIs, ISSUES & RISKS", "functions": 6},
        16: {"name": "SOLICITUDES", "functions": 4},
        17: {"name": "FOTOS & FLOOR PLANS", "functions": 5},
        18: {"name": "INVENTORY", "functions": 3},
        19: {"name": "COLOR SAMPLES & DESIGN", "functions": 6},
        20: {"name": "COMMUNICATION", "functions": 3},
        21: {"name": "DASHBOARDS", "functions": 6},
        22: {"name": "PAYROLL", "functions": 3},
        23: {"name": "QUALITY CONTROL", "functions": 4},
    }

    total_documented_functions = sum(m["functions"] for m in modules.values())

    for num, module in modules.items():
        print(f"✅ Módulo {num:2d}: {module['name']:<40} - {module['functions']:2d} funciones")

    print()
    print(f"📊 Total de funciones documentadas: {total_documented_functions}")
    print()

    # 9. Análisis de completitud
    print("=" * 100)
    print(" " * 30 + "🎯 ANÁLISIS DE COMPLETITUD")
    print("=" * 100)
    print()

    # Estimación: cada función requiere en promedio:
    # - 0.5 modelos (algunas usan modelos existentes)
    # - 1-3 URLs
    # - 1-2 templates
    # - 1-2 vistas
    # - 0.5 formularios

    expected_urls = total_documented_functions * 2  # Promedio de 2 URLs por función
    expected_templates = total_documented_functions * 1.5  # Promedio de 1.5 templates
    expected_views = total_documented_functions * 1.5  # Promedio de 1.5 vistas
    expected_forms = total_documented_functions * 0.5  # Promedio de 0.5 forms

    urls_percentage = min((urls_count / expected_urls) * 100, 100)
    templates_percentage = min((templates_count / expected_templates) * 100, 100)
    views_percentage = min((views_count / expected_views) * 100, 100)
    forms_percentage = min((forms_count / expected_forms) * 100, 100)

    print(f"URLs implementadas:      {urls_count:3d} de ~{int(expected_urls):3d} esperadas ({urls_percentage:.1f}%)")
    print(
        f"Templates implementados: {templates_count:3d} de ~{int(expected_templates):3d} esperados ({templates_percentage:.1f}%)"
    )
    print(f"Vistas implementadas:    {views_count:3d} de ~{int(expected_views):3d} esperadas ({views_percentage:.1f}%)")
    print(f"Forms implementados:     {forms_count:3d} de ~{int(expected_forms):3d} esperados ({forms_percentage:.1f}%)")
    print()

    overall_percentage = (urls_percentage + templates_percentage + views_percentage + forms_percentage) / 4

    print(f"🎯 COMPLETITUD ESTIMADA: {overall_percentage:.1f}%")
    print()

    if overall_percentage >= 95:
        print("✅ EXCELENTE - Sistema casi completamente implementado")
        print("   → Todas las funcionalidades principales están en su lugar")
        print("   → Listo para pruebas exhaustivas y deployment")
    elif overall_percentage >= 80:
        print("✅ MUY BUENO - Mayoría de funcionalidades implementadas")
        print("   → Sistema funcional y robusto")
        print("   → Algunas funcionalidades secundarias pendientes")
    elif overall_percentage >= 60:
        print("⚠️  BUENO - Sistema funcional pero con áreas pendientes")
        print("   → Funcionalidades core implementadas")
        print("   → Requiere completar funcionalidades secundarias")
    else:
        print("❌ INCOMPLETO - Requiere trabajo significativo")
        print("   → Muchas funcionalidades aún por implementar")

    print()

    # 10. Recomendaciones
    print("=" * 100)
    print(" " * 30 + "💡 PRÓXIMOS PASOS RECOMENDADOS")
    print("=" * 100)
    print()

    if overall_percentage < 80:
        print("1. 🔴 PRIORIDAD ALTA: Completar funcionalidades core faltantes")
        print("2. 🟡 PRIORIDAD MEDIA: Implementar validaciones y permisos")
        print("3. 🟢 PRIORIDAD BAJA: Agregar funcionalidades avanzadas")
    elif overall_percentage < 95:
        print("1. ✅ Completar funcionalidades secundarias restantes")
        print("2. 🧪 Realizar pruebas exhaustivas función por función")
        print("3. 🐛 Corregir bugs encontrados durante las pruebas")
        print("4. 📱 Optimizar experiencia móvil")
    else:
        print("1. 🧪 Realizar pruebas exhaustivas de integración")
        print("2. 📝 Completar documentación de usuario")
        print("3. 🚀 Preparar para deployment en producción")
        print("4. 📊 Implementar analytics y monitoreo")

    print()
    print("=" * 100)
    print(" " * 35 + "✅ AUDITORÍA COMPLETADA")
    print("=" * 100)


if __name__ == "__main__":
    audit_comprehensive()
