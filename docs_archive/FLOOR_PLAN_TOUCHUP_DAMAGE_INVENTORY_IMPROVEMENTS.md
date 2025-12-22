# 🎯 MEJORAS REQUERIDAS - PLANOS 2D, TOUCH-UPS, DAÑOS E INVENTARIO

**Fecha**: Diciembre 12, 2025  
**Estado**: Plan de Implementación

---

## 📋 RESUMEN DE TAREAS

### 1️⃣ **SISTEMA DE PLANOS 2D - Boards Diferenciados**

**Problema Actual:**
- Solo existe UN board para marcar planos 2D con información general
- No hay vista filtrada específica para Touch-ups/Detalles

**Solución Requerida:**
- ✅ Mantener board actual (información general) - YA EXISTE
- ➕ CREAR: Board de Touch-ups/Detalles (solo muestra pines de tipo touch-up)

---

### 2️⃣ **DAÑOS - Integración con Planos 2D**

**Problema Actual:**
- Los daños NO tienen opción de marcar ubicación en planos 2D
- No hay conexión entre DamageReport y FloorPlan/PlanPin

**Solución Requerida:**
- Agregar campo de ubicación (floor_plan + coordinates) en DamageReport
- Crear vista de planos 2D específica para marcar daños
- Permitir ver daños en el visualizador de planos

---

### 3️⃣ **INVENTARIO - Interfaz Wizard Moderna**

**Problema Actual:**
- Los botones de inventario NO tienen estilo wizard
- UI anticuada vs resto del sistema

**Solución Requerida:**
- Rediseñar interfaz de inventario con estilo wizard moderno
- Paso a paso: Selección → Detalles → Confirmación
- Consistente con Strategic Planner y otros wizards

---

## 🔧 PLAN DE IMPLEMENTACIÓN

### FASE 1: Floor Plan Touch-up Board (2-3 horas)

#### Archivos a Modificar:
1. **URL Pattern** (`kibray_backend/urls.py`)
   ```python
   path("plans/<int:plan_id>/touchups/", views.floor_plan_touchup_view, name="floor_plan_touchup_view"),
   ```

2. **Vista** (`core/views/legacy_views.py`)
   ```python
   @login_required
   def floor_plan_touchup_view(request, plan_id):
       """
       Vista especializada de plano 2D mostrando SOLO touch-ups
       """
       plan = get_object_or_404(FloorPlan, pk=plan_id)
       # Filtrar solo pines de tipo 'touchup'
       touchup_pins = plan.pins.filter(pin_type='touchup')
       
       return render(request, 'core/floor_plan_touchup_view.html', {
           'plan': plan,
           'pins': touchup_pins,
           'mode': 'touchup'  # Para filtrado de UI
       })
   ```

3. **Template** (`core/templates/core/floor_plan_touchup_view.html`)
   - Copiar base de `floor_plan_detail.html`
   - Modificar para mostrar SOLO pines tipo 'touchup'
   - Agregar filtros visuales (color específico, iconos)
   - Agregar header: "Touch-ups / Detalles"

4. **Navegación** - Agregar botón en:
   - `project_overview.html` - Sección de planos
   - `floor_plan_list.html` - Cada plano
   - `touchup_board.html` - Link a planos con touch-ups

---

### FASE 2: Daños + Planos 2D (3-4 horas)

#### Cambios en Modelo:
```python
# core/models.py - DamageReport
class DamageReport(models.Model):
    # ... campos existentes ...
    
    # NUEVO: Ubicación en plano 2D
    floor_plan = models.ForeignKey(
        'FloorPlan', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='damage_reports'
    )
    floor_plan_x = models.FloatField(null=True, blank=True)
    floor_plan_y = models.FloatField(null=True, blank=True)
```

#### Migración:
```bash
python manage.py makemigrations
python manage.py migrate
```

#### Archivos a Crear/Modificar:

1. **Vista de Selección** (`damage_report_form.html`)
   - Agregar opción: "Marcar ubicación en plano"
   - Botón que abre modal de selección de plano

2. **Modal de Planos** (JavaScript en template)
   - Lista de planos disponibles del proyecto
   - Al seleccionar → Abrir plano en modo "marcar daño"

3. **Vista de Marcado** (`floor_plan_mark_damage.html`)
   - Copia de `floor_plan_detail.html` pero modo "damage"
   - Click en plano guarda coordenadas
   - Redirige a formulario de daño con data

4. **Visualización de Daños en Planos**
   - Modificar `floor_plan_detail.html`
   - Mostrar pines de daños con ícono específico
   - Color rojo/warning para diferencia

---

### FASE 3: Inventario Wizard (2-3 horas)

#### Templates a Crear:

1. **inventory_wizard.html** - Template principal
   ```html
   {% extends "core/base_modern.html" %}
   <!-- Estilo similar a strategic_planning_detail.html -->
   
   <div class="wizard-container">
       <!-- Step 1: Seleccionar Acción -->
       <div class="wizard-step" id="step-1">
           <div class="step-cards">
               <div class="step-card" onclick="selectAction('add')">
                   <i class="bi bi-plus-circle"></i>
                   <h3>Agregar Inventario</h3>
               </div>
               <div class="step-card" onclick="selectAction('move')">
                   <i class="bi bi-arrow-left-right"></i>
                   <h3>Mover Inventario</h3>
               </div>
               <div class="step-card" onclick="selectAction('adjust')">
                   <i class="bi bi-tools"></i>
                   <h3>Ajustar Stock</h3>
               </div>
           </div>
       </div>
       
       <!-- Step 2: Detalles -->
       <!-- Step 3: Confirmación -->
   </div>
   ```

2. **Estilos CSS** - Copiar de strategic_planning_detail.html
   - `.wizard-container`
   - `.wizard-step`
   - `.step-card` con efectos hover
   - Transiciones entre pasos

3. **JavaScript**
   - Navegación entre pasos
   - Validación de formularios
   - Animaciones de transición

#### Archivos a Modificar:

1. **URLs** (`kibray_backend/urls.py`)
   ```python
   # Reemplazar rutas viejas con wizard
   path("inventory/wizard/", views.inventory_wizard, name="inventory_wizard"),
   ```

2. **Vista** (`core/views/legacy_views.py`)
   ```python
   @login_required
   @staff_required
   def inventory_wizard(request, project_id=None):
       """
       Wizard moderno para gestión de inventario
       """
       # Lógica del wizard por pasos
       pass
   ```

3. **Navegación**
   - Dashboard Admin → Botón "Inventario" → Wizard
   - Dashboard PM → Botón "Inventario" → Wizard

---

## 📊 ESTRUCTURA DE ARCHIVOS

```
kibray/
├── core/
│   ├── models.py                              # Modificar DamageReport
│   ├── views/
│   │   └── legacy_views.py                   # Agregar nuevas vistas
│   ├── templates/core/
│   │   ├── floor_plan_touchup_view.html      # NUEVO
│   │   ├── floor_plan_mark_damage.html       # NUEVO
│   │   ├── inventory_wizard.html             # NUEVO
│   │   ├── floor_plan_detail.html            # MODIFICAR
│   │   └── damage_report_form.html           # MODIFICAR
│   └── migrations/
│       └── 00XX_add_floor_plan_to_damage.py  # NUEVO
└── kibray_backend/
    └── urls.py                               # MODIFICAR
```

---

## ✅ CHECKLIST DE VALIDACIÓN

### Floor Plan Touch-up Board:
- [ ] URL `/plans/<id>/touchups/` funciona
- [ ] Solo muestra pines de tipo 'touchup'
- [ ] Navegación desde project_overview
- [ ] Navegación desde touchup_board
- [ ] Responsive en móvil

### Daños + Planos 2D:
- [ ] Migración aplicada correctamente
- [ ] Formulario de daño tiene opción "marcar en plano"
- [ ] Modal de selección de plano funciona
- [ ] Vista de marcado guarda coordenadas
- [ ] Daños se visualizan en floor_plan_detail
- [ ] Ícono diferente para daños vs touch-ups

### Inventario Wizard:
- [ ] Wizard tiene 3 pasos claros
- [ ] Transiciones suaves entre pasos
- [ ] Botones con estilo moderno (igual a Strategic Planner)
- [ ] Validación en cada paso
- [ ] Responsive en móvil
- [ ] Navegación desde dashboards funciona

---

## 🚀 ORDEN DE IMPLEMENTACIÓN RECOMENDADO

1. **PRIMERO**: Floor Plan Touch-up Board (más fácil, sin cambios de BD)
2. **SEGUNDO**: Daños + Planos 2D (requiere migración)
3. **TERCERO**: Inventario Wizard (mejora UX pero no crítico)

---

## 📝 NOTAS TÉCNICAS

### PlanPin Types Actuales:
```python
PIN_TYPE_CHOICES = [
    ('info', 'Información General'),
    ('touchup', 'Touch-up/Detalle'),
    ('damage', 'Daño'),
    ('color', 'Muestra de Color'),
    ('task', 'Tarea'),
]
```

### Floor Plan Permissions:
- Admin/PM: Puede crear y editar todos los pines
- Designer: Puede editar pines y comentarios
- Client: Solo vista

### Inventory Actions:
- Add (Agregar nuevo item)
- Move (Mover entre ubicaciones)
- Adjust (Ajuste de stock)
- Low Stock Alerts (Alertas)

---

**Implementador**: Listo para comenzar con Fase 1
**Siguiente Paso**: Implementar Floor Plan Touch-up Board
