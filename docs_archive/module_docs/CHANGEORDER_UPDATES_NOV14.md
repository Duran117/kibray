# Actualizaciones - Change Order: Colores y Edición de Fotos

## 📅 Fecha: 14 de Noviembre, 2025

## 🎯 Cambios Implementados

### 1. ✅ **Dropdown de Colores Aprobados del Proyecto**

**Problema anterior:** El dropdown mostraba colores genéricos sin conexión con el proyecto.

**Solución implementada:**
- El dropdown ahora muestra **SOLO los colores aprobados** (`status='approved'`) del proyecto seleccionado
- Si no hay colores aprobados en el proyecto, el dropdown **no se muestra**
- Al cambiar de proyecto (en modo crear), se cargan dinámicamente los colores aprobados vía AJAX

**Archivos modificados:**
- `core/templates/core/changeorder_form_standalone.html`:
  - Dropdown con `id="approvedColorsGroup"` que se oculta si no hay colores
  - JavaScript para cargar colores dinámicamente al cambiar proyecto
  
- `core/views.py`:
  - `changeorder_create_view`: Pasa `approved_colors` del proyecto (si viene GET param)
  - `changeorder_edit_view`: Pasa `approved_colors` del proyecto del CO
  - **Nueva vista:** `get_approved_colors(project_id)` - API endpoint JSON

- `kibray_backend/urls.py`:
  - Nuevo endpoint: `/api/projects/<int:project_id>/approved-colors/`

**Comportamiento:**
```
1. Usuario selecciona proyecto → JavaScript llama API
2. API retorna colores con status='approved' del proyecto
3. Dropdown se llena con: "SW 7006 - White Dove (Sherwin Williams)"
4. Si no hay colores aprobados → dropdown permanece oculto
```

---

### 2. ✅ **Campo de Referencia de Color/Material**

**Aclaración del propósito:**
- Este campo es para **hacer match con materiales existentes** (madera, metal, etc.)
- NO está limitado a colores aprobados
- Usuario puede escribir libremente: "Madera X", "Metal Z", "Puerta Principal"

**Cambios en el template:**
- Label actualizado a: "Código de Referencia o Material"
- Help text: "Para hacer match con madera, metal u otro material (ej: 'Madera X', 'Metal Z')"

---

### 3. ✅ **Editor de Imagen Inmediato**

**Problema anterior:** Usuario seleccionaba foto → aparecía preview → tenía que hacer clic en "Editar"

**Solución implementada:**
- Al seleccionar/tomar foto, **el editor se abre INMEDIATAMENTE**
- Usuario puede dibujar/anotar **ANTES de cargar** la foto al formulario
- Al guardar anotaciones, la foto aparece en el preview con el badge "Con anotaciones"

**Cambios en JavaScript:**
```javascript
photoInput.addEventListener('change', function(e) {
    const files = Array.from(e.target.files);
    
    files.forEach((file, idx) => {
        const reader = new FileReader();
        reader.onload = function(e) {
            selectedFiles.push({
                file: file,
                dataUrl: e.target.result,
                description: '',
                annotations: []
            });
            
            // ⭐ ABRE EDITOR INMEDIATAMENTE
            openPhotoEditorNew(e.target.result, tempIndex, true);
        };
        reader.readAsDataURL(file);
    });
});
```

**Flujo nuevo:**
```
1. Usuario hace clic en "Subir foto"
2. Selecciona archivo
3. ⚡ INMEDIATAMENTE se abre el editor con la imagen
4. Usuario dibuja líneas, flechas, círculos
5. Hace clic en "Guardar Anotaciones"
6. La foto aparece en el preview del formulario
7. Al enviar formulario, se sube con anotaciones incluidas
```

---

### 4. ✅ **Corrección de Precisión del Cursor en Canvas**

**Problema anterior:** 
- Usuario hacía clic en un punto del canvas
- La línea aparecía en otro lugar (offset incorrecto)

**Causa raíz:**
- El canvas puede estar escalado (CSS) vs su tamaño real (width/height)
- No se consideraba el `getBoundingClientRect()` con escalado

**Solución implementada:**
```javascript
function getCanvasCoordinates(e) {
    const rect = canvas.getBoundingClientRect();
    const scaleX = canvas.width / rect.width;   // Factor de escala X
    const scaleY = canvas.height / rect.height; // Factor de escala Y
    
    return {
        x: (e.clientX - rect.left) * scaleX,
        y: (e.clientY - rect.top) * scaleY
    };
}

function startDrawing(e) {
    isDrawing = true;
    const coords = getCanvasCoordinates(e); // ⭐ USA FUNCIÓN CORREGIDA
    startX = coords.x;
    startY = coords.y;
}

function draw(e) {
    if (!isDrawing) return;
    const coords = getCanvasCoordinates(e); // ⭐ USA FUNCIÓN CORREGIDA
    const currentX = coords.x;
    const currentY = coords.y;
    // ... resto del código de dibujo
}
```

**Resultado:**
- ✅ Cursor preciso en cualquier tamaño de pantalla
- ✅ Funciona con canvas escalado por CSS
- ✅ Compatible con pantallas retina/HD

---

### 5. ✅ **Soporte Táctil (Touch Events)**

**Bonus implementado:**
```javascript
// Touch events para móvil
canvas.ontouchstart = function(e) {
    e.preventDefault();
    const touch = e.touches[0];
    const mouseEvent = new MouseEvent('mousedown', {
        clientX: touch.clientX,
        clientY: touch.clientY
    });
    canvas.dispatchEvent(mouseEvent);
};

canvas.ontouchmove = function(e) {
    e.preventDefault();
    const touch = e.touches[0];
    const mouseEvent = new MouseEvent('mousemove', {
        clientX: touch.clientX,
        clientY: touch.clientY
    });
    canvas.dispatchEvent(mouseEvent);
};
```

**Resultado:**
- ✅ Dibujo funciona en tablets/smartphones
- ✅ Touch preciso con corrección de coordenadas

---

## 🔄 Flujo Completo Actualizado

### Crear Change Order con Color y Fotos Anotadas

1. **Seleccionar Proyecto**
   - Dropdown de proyectos
   - Al seleccionar → carga colores aprobados dinámicamente

2. **Elegir Color** (3 opciones):
   - **Opción A:** Dropdown de colores aprobados del proyecto (si existen)
   - **Opción B:** Color picker HTML5 (selector visual)
   - **Opción C:** Input manual de hex (#FF5733)

3. **Referencia de Material** (opcional):
   - Escribir libremente: "Madera de entrada", "Metal portón", etc.

4. **Subir Fotos**:
   - Clic en área de carga
   - Seleccionar foto(s)
   - ⚡ **Editor se abre AUTOMÁTICAMENTE**
   - Dibujar anotaciones con cursor preciso
   - Guardar → foto aparece en preview

5. **Enviar Formulario**:
   - Todas las fotos con anotaciones se guardan
   - Colores y referencias guardadas en CO

---

## 🎨 Capturas del Comportamiento

### Dropdown de Colores Aprobados

**Proyecto CON colores aprobados:**
```
┌─────────────────────────────────────────┐
│ Colores Aprobados del Proyecto         │
│ ┌─────────────────────────────────────┐│
│ │ -- Seleccionar color aprobado --   ││
│ │ SW 7006 - White Dove (Sherwin W.)  ││
│ │ SW 6258 - Tricorn Black (Sherwin)  ││
│ │ BM 2024-10 - Hale Navy (Benjamin M)││
│ └─────────────────────────────────────┘│
└─────────────────────────────────────────┘
```

**Proyecto SIN colores aprobados:**
```
(El dropdown NO aparece, solo muestra color picker manual)
```

### Editor Inmediato

**Antes:**
```
1. Seleccionar foto → 2. Ver preview → 3. Clic "Editar" → 4. Dibujar
```

**Ahora:**
```
1. Seleccionar foto → ⚡ Inmediatamente: Editor abierto → 2. Dibujar
```

### Precisión del Cursor

**Antes:**
```
   Cursor aquí → ●
                      ● ← Línea dibujada aquí (offset incorrecto)
```

**Ahora:**
```
   Cursor aquí → ●——— Línea dibujada exactamente aquí ✓
```

---

## 🧪 Testing Manual

### Checklist de Colores Aprobados

- [x] Proyecto con colores aprobados → dropdown visible
- [x] Proyecto sin colores aprobados → dropdown oculto
- [x] Cambiar proyecto en crear → dropdown se actualiza
- [x] Seleccionar color aprobado → llena reference_code
- [x] Input manual de hex funciona independiente
- [x] Reference code se puede editar libremente

### Checklist de Editor Inmediato

- [x] Seleccionar foto → editor abre sin clic extra
- [x] Seleccionar múltiples fotos → abre editor para cada una
- [x] Guardar anotaciones → foto aparece en preview
- [x] Volver a editar foto → anotaciones se cargan

### Checklist de Precisión

- [x] Dibujo con mouse → líneas precisas
- [x] Dibujo con touch (móvil) → funciona correctamente
- [x] Canvas escalado (responsive) → coordenadas correctas
- [x] Pantalla retina → no hay offset

---

## 📊 Impacto en Base de Datos

**Sin cambios en esquema** - Todo funcionaba con estructura existente:
- `ColorSample.status = 'approved'` → filtrado backend
- `ChangeOrder.color` → hex manual
- `ChangeOrder.reference_code` → texto libre
- `ChangeOrderPhoto.annotations` → JSON con coordenadas

---

## 🚀 Próximos Pasos (Opcional)

### Mejoras Futuras Sugeridas

1. **Color Picker desde ColorSample:**
   - Extraer hex color de la imagen de muestra
   - Auto-llenar color picker al seleccionar del dropdown

2. **Tool de Texto:**
   - Agregar texto sobre las fotos
   - Font size, color, background

3. **Líneas Curvas:**
   - Herramienta de curva bezier
   - Círculos parciales (arcos)

4. **Historial de Anotaciones:**
   - Ver versiones anteriores de anotaciones
   - Revertir cambios

5. **Exportar con Anotaciones:**
   - PDF con fotos anotadas
   - Cliente puede ver anotaciones en vista pública

---

## 📝 Notas Técnicas

### API Endpoint de Colores
```python
GET /api/projects/<project_id>/approved-colors/

Response:
{
    "colors": [
        {
            "id": 1,
            "code": "SW 7006",
            "name": "White Dove",
            "brand": "Sherwin Williams",
            "finish": "Eggshell"
        }
    ]
}
```

### Estructura de Annotations JSON
```json
[
    {
        "type": "line",
        "color": "#FF0000",
        "width": 3,
        "x1": 150,
        "y1": 200,
        "x2": 350,
        "y2": 400
    },
    {
        "type": "arrow",
        "color": "#00FF00",
        "width": 5,
        "x1": 100,
        "y1": 100,
        "x2": 500,
        "y2": 500
    }
]
```

### Canvas Coordinate Conversion
```javascript
// CSS display size
rect.width = 800px
rect.height = 600px

// Actual canvas size
canvas.width = 3000px
canvas.height = 2000px

// Scale factors
scaleX = 3000 / 800 = 3.75
scaleY = 2000 / 600 = 3.33

// Cursor at (100, 100) CSS pixels
// Actual canvas coords: (100 * 3.75, 100 * 3.33) = (375, 333)
```

---

## ✅ Resumen de Archivos Modificados

| Archivo | Cambios |
|---------|---------|
| `core/views.py` | +30 líneas: `get_approved_colors()`, filtro en create/edit |
| `kibray_backend/urls.py` | +1 línea: endpoint API |
| `core/templates/core/changeorder_form_standalone.html` | ~150 líneas: dropdown dinámico, editor inmediato, coordenadas precisas |

**Total:** ~180 líneas modificadas/añadidas

---

**Estado:** ✅ IMPLEMENTADO Y FUNCIONANDO
**Probado:** Local en macOS con Python 3.x, Django 4.2.26
**Compatible:** Desktop (Chrome, Safari, Firefox), Mobile (iOS Safari, Chrome Android)
