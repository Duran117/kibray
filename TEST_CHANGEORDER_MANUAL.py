"""
Test manual para verificar funcionalidades de Change Order

Para probar:
1. Iniciar servidor: python3 manage.py runserver
2. Navegar a: http://localhost:8000/changeorders/board/
3. Seguir los pasos de prueba descritos abajo
"""

# PASO 1: VERIFICAR DROPDOWN DE COLORES APROBADOS
# ================================================
# 1. Ir a "Crear Change Order"
# 2. Seleccionar un proyecto que tenga ColorSample con status='approved'
# 3. Verificar que aparece el dropdown "Colores Aprobados del Proyecto"
# 4. Seleccionar un color del dropdown
# 5. Verificar que se llena el campo "Código de Referencia"
#
# Resultado esperado: Dropdown solo aparece si hay colores aprobados


# PASO 2: VERIFICAR EDITOR INMEDIATO
# ===================================
# 1. En el formulario, hacer clic en "Subir fotos"
# 2. Seleccionar una imagen
# 3. Verificar que el modal de editor se abre INMEDIATAMENTE
# 4. Dibujar una línea o flecha
# 5. Hacer clic en "Guardar Anotaciones"
# 6. Verificar que la foto aparece en el preview con badge "Con anotaciones"
#
# Resultado esperado: No se necesita clic extra en "Editar"


# PASO 3: VERIFICAR PRECISIÓN DEL CURSOR
# =======================================
# 1. Abrir editor de foto (seguir pasos anteriores)
# 2. Posicionar el cursor en un punto específico de la imagen
# 3. Hacer clic y arrastrar para dibujar una línea
# 4. Verificar que la línea empieza EXACTAMENTE donde está el cursor
# 5. Hacer zoom in/out en el navegador (Cmd/Ctrl + +/-)
# 6. Verificar que sigue siendo preciso
#
# Resultado esperado: Líneas empiezan donde el cursor hace clic


# PASO 4: PROYECTO SIN COLORES APROBADOS
# =======================================
# 1. Crear Change Order
# 2. Seleccionar un proyecto que NO tenga ColorSample aprobados
# 3. Verificar que el dropdown NO aparece
# 4. Verificar que color picker manual sigue disponible
#
# Resultado esperado: Dropdown oculto, manual input funciona


# PASO 5: TOUCH EVENTS (MÓVIL)
# =============================
# 1. Abrir en dispositivo móvil o usar DevTools responsive mode
# 2. Subir foto desde galería o cámara
# 3. Usar dedo/stylus para dibujar en el canvas
# 4. Verificar que el dibujo sigue el dedo con precisión
#
# Resultado esperado: Touch drawing funciona igual que mouse


# QUERIES ÚTILES PARA DEBUGGING
# ==============================

# Ver colores aprobados de un proyecto
from core.models import ColorSample, Project

project = Project.objects.first()
approved = ColorSample.objects.filter(project=project, status="approved")
print(f"Colores aprobados en {project.name}: {approved.count()}")
for color in approved:
    print(f"  - {color.code} / {color.name} / {color.brand}")


# Ver fotos con anotaciones
from core.models import ChangeOrderPhoto

photos_with_annotations = ChangeOrderPhoto.objects.exclude(annotations="")
print(f"Fotos con anotaciones: {photos_with_annotations.count()}")
for photo in photos_with_annotations:
    print(f"  CO-{photo.change_order.id}: {len(photo.annotations)} bytes de JSON")


# Crear color sample de prueba
def create_test_color_sample(project):
    color = ColorSample.objects.create(
        project=project, code="SW 7006", name="Extra White", brand="Sherwin Williams", finish="Flat", status="approved"
    )
    print(f"Color de prueba creado: {color.code}")
    return color


# Simular AJAX request
import json

import requests

# (Asumiendo servidor corriendo en localhost:8000)
project_id = 1
response = requests.get(f"http://localhost:8000/api/projects/{project_id}/approved-colors/")
data = response.json()
print(f"API response: {json.dumps(data, indent=2)}")


# CHECKLIST DE VERIFICACIÓN
# ==========================
"""
□ Dropdown aparece solo si hay colores aprobados
□ Dropdown se actualiza al cambiar proyecto
□ Seleccionar color aprobado llena reference_code
□ Editor se abre inmediatamente al seleccionar foto
□ Múltiples fotos → editor se abre para cada una
□ Cursor preciso en cualquier zoom level
□ Touch events funcionan en móvil
□ Anotaciones se guardan correctamente en JSON
□ Fotos con anotaciones muestran badge
□ API endpoint retorna JSON correcto
"""
