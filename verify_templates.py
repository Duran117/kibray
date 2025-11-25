#!/usr/bin/env python3
"""
Script de Verificación Automática - Change Order Photo Editor
Verifica que todos los componentes estén correctamente conectados
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kibray_backend.settings')
django.setup()

from django.urls import reverse, resolve
from django.test import RequestFactory
from core import views
from core.models import ChangeOrderPhoto, ChangeOrder
import json

print("=" * 70)
print("VERIFICACIÓN AUTOMÁTICA - CHANGE ORDER PHOTO EDITOR")
print("=" * 70)
print()

# Test 1: Verificar rutas
print("📍 TEST 1: Verificando rutas...")
routes = [
    ('changeorder_create', '/changeorder/create/'),
    ('changeorder_edit', '/changeorder/1/edit/'),
    ('photo_editor_standalone', '/changeorder/photo-editor/'),
    ('changeorder_board', '/changeorders/board/'),
]

all_routes_ok = True
for name, expected_path in routes:
    try:
        url = reverse(name) if name != 'changeorder_edit' else reverse('changeorder_edit', args=[1])
        resolved = resolve(url)
        print(f"  ✅ {name}: {url}")
    except Exception as e:
        print(f"  ❌ {name}: ERROR - {e}")
        all_routes_ok = False

print()

# Test 2: Verificar templates existen
print("📄 TEST 2: Verificando existencia de templates...")
templates = [
    'core/templates/core/changeorder_form_standalone.html',
    'core/templates/core/changeorder_form_modern.html',
    'core/templates/core/photo_editor_standalone.html',
    'core/templates/core/changeorder_board.html',
    'core/templates/core/changeorder_detail_standalone.html',
    'core/templates/core/changeorder_confirm_delete.html',
]

all_templates_ok = True
for template_path in templates:
    if os.path.exists(template_path):
        size = os.path.getsize(template_path)
        print(f"  ✅ {template_path.split('/')[-1]}: {size:,} bytes")
    else:
        print(f"  ❌ {template_path}: NO EXISTE")
        all_templates_ok = False

print()

# Test 3: Verificar vistas tienen las funciones correctas
print("🔧 TEST 3: Verificando vistas...")
views_to_check = [
    'changeorder_create_view',
    'changeorder_edit_view',
    'photo_editor_standalone_view',
    'save_photo_annotations',
    'delete_changeorder_photo',
]

all_views_ok = True
for view_name in views_to_check:
    if hasattr(views, view_name):
        view_func = getattr(views, view_name)
        print(f"  ✅ {view_name}: Existe")
    else:
        print(f"  ❌ {view_name}: NO EXISTE")
        all_views_ok = False

print()

# Test 4: Verificar modelo ChangeOrderPhoto
print("🗄️  TEST 4: Verificando modelo ChangeOrderPhoto...")
try:
    photo_count = ChangeOrderPhoto.objects.count()
    print(f"  ✅ Modelo ChangeOrderPhoto: {photo_count} fotos en DB")
    
    # Verificar que el campo annotations existe
    if hasattr(ChangeOrderPhoto, 'annotations'):
        print(f"  ✅ Campo 'annotations': Existe")
    else:
        print(f"  ❌ Campo 'annotations': NO EXISTE")
        
    # Verificar una foto si existe
    if photo_count > 0:
        photo = ChangeOrderPhoto.objects.first()
        print(f"  ℹ️  Ejemplo foto ID {photo.id}:")
        print(f"     - annotations type: {type(photo.annotations)}")
        print(f"     - annotations length: {len(photo.annotations) if photo.annotations else 0}")
        
        # Verificar si es JSON válido
        if photo.annotations:
            try:
                parsed = json.loads(photo.annotations)
                print(f"     ✅ JSON válido: {len(parsed)} anotaciones")
            except json.JSONDecodeError as e:
                print(f"     ❌ JSON inválido: {e}")
except Exception as e:
    print(f"  ❌ Error verificando modelo: {e}")

print()

# Test 5: Verificar JavaScript en template
print("📜 TEST 5: Verificando JavaScript en templates...")
standalone_template = 'core/templates/core/changeorder_form_standalone.html'
if os.path.exists(standalone_template):
    with open(standalone_template, 'r') as f:
        content = f.read()
        
    # Verificar funciones críticas
    critical_functions = [
        'openPhotoEditorNewTab',
        'openPhotoEditorInNewTab',
        'deletePhoto',
        'saveAnnotations',
    ]
    
    all_functions_ok = True
    for func_name in critical_functions:
        if f'function {func_name}' in content:
            print(f"  ✅ {func_name}: Definida")
        else:
            print(f"  ❌ {func_name}: NO ENCONTRADA")
            all_functions_ok = False
    
    # Verificar balance de braces en script
    script_start = content.find('<script>')
    script_end = content.find('</script>')
    if script_start != -1 and script_end != -1:
        script_content = content[script_start+8:script_end]
        open_braces = script_content.count('{')
        close_braces = script_content.count('}')
        
        if open_braces == close_braces:
            print(f"  ✅ Balance de braces: {open_braces} open, {close_braces} close")
        else:
            print(f"  ❌ Balance de braces: {open_braces} open, {close_braces} close (DESBALANCEADO)")
            all_functions_ok = False
else:
    print(f"  ❌ Template standalone no existe")
    all_functions_ok = False

print()

# Test 6: Verificar editor standalone
print("🎨 TEST 6: Verificando editor standalone...")
editor_template = 'core/templates/core/photo_editor_standalone.html'
if os.path.exists(editor_template):
    with open(editor_template, 'r') as f:
        content = f.read()
        
    # Verificar funciones críticas del editor
    editor_functions = [
        'initializeEditor',
        'startDrawing',
        'draw',
        'stopDrawing',
        'redrawCanvas',
        'redrawAnnotations',
        'saveAnnotations',
    ]
    
    all_editor_ok = True
    for func_name in editor_functions:
        if f'function {func_name}' in content:
            print(f"  ✅ {func_name}: Definida")
        else:
            print(f"  ❌ {func_name}: NO ENCONTRADA")
            all_editor_ok = False
    
    # Verificar que use scaling para cursor
    if 'scaleX' in content and 'scaleY' in content:
        print(f"  ✅ Cursor scaling: Implementado")
    else:
        print(f"  ❌ Cursor scaling: NO IMPLEMENTADO")
        all_editor_ok = False
else:
    print(f"  ❌ Editor template no existe")
    all_editor_ok = False

print()

# Resumen final
print("=" * 70)
print("RESUMEN FINAL")
print("=" * 70)

all_ok = all([
    all_routes_ok,
    all_templates_ok,
    all_views_ok,
    all_functions_ok if 'all_functions_ok' in locals() else False,
    all_editor_ok if 'all_editor_ok' in locals() else False,
])

if all_ok:
    print("✅ TODOS LOS TESTS PASARON")
    print("El sistema está listo para uso en producción.")
    sys.exit(0)
else:
    print("❌ ALGUNOS TESTS FALLARON")
    print("Revisa los errores arriba y corrígelos antes de continuar.")
    sys.exit(1)
