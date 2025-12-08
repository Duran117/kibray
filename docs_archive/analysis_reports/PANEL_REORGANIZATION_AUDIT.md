# 🔍 AUDITORÍA COMPLETA DE PANELES - SISTEMA KIBRAY

**Fecha**: 14 de Noviembre, 2025  
**Objetivo**: Revisar función por función cada panel, identificar qué falta, qué sobra, y reorganizar todo el sistema

---

## 📊 PANEL 1: PROJECT OVERVIEW (Vista Principal del Proyecto)

### **Ubicación Actual**: `/projects/<id>/` → `project_overview.html`

### ✅ **Funciones Existentes:**
1. **Header del Proyecto** - Información básica (nombre, dirección)
2. **Botones de Navegación**:
   - ✅ Minutas (Minutes)
   - ✅ Inventario
   - ✅ Archivos (project_files)
   - ✅ Profit Dashboard
   - ✅ EV (Earned Value)
   - ✅ Nuevo CO
   - ✅ Nueva Factura
   - ✅ Nueva Tarea
3. **Timeline del Proyecto** - Fechas inicio/fin, duración, progreso
4. **Métricas Financieras** - 4 cards: Ingresos, Gastos, Utilidad, Presupuesto Restante
5. **Widgets de Resumen**:
   - ✅ Colores (color samples)
   - ✅ Schedule Próximo
   - ✅ Tareas
   - ✅ Alertas/Daños (Issues)
   - ✅ Daily Logs
   - ✅ Archivos
   - ✅ Sobras de Material

### ❌ **FUNCIONES FALTANTES (CRÍTICAS):**

#### **Botones de Navegación que FALTAN en el Header:**
1. **❌ Floor Plans / Planos 2D** 
   - **Acción**: Agregar botón → `{% url 'floor_plan_list' project.id %}`
   - **Icono**: `<i class="bi bi-blueprint"></i>`
   - **Texto**: "Planos 2D"
   - **Color**: `btn-outline-info`

2. **❌ Touch-up System**
   - **Acción**: Agregar botón → `{% url 'touchup_plans_list' project.id %}`
   - **Icono**: `<i class="bi bi-brush"></i>`
   - **Texto**: "Touch-ups"
   - **Color**: `btn-outline-warning`

3. **❌ Damage Reports**
   - **Acción**: Agregar botón → `{% url 'damage_report_list' project.id %}`
   - **Icono**: `<i class="bi bi-exclamation-diamond"></i>`
   - **Texto**: "Reportes de Daño"
   - **Color**: `btn-outline-danger`

4. **❌ CO Board (Change Orders Board)**
   - **Acción**: Agregar botón → `{% url 'changeorder_board' %}`
   - **Icono**: `<i class="bi bi-kanban"></i>`
   - **Texto**: "CO Board"
   - **Color**: `btn-outline-success`

#### **Widgets que FALTAN:**
5. **❌ Widget de Floor Plans**
   - Mostrar últimos 3-5 planos con cantidad de pines
   - Botones: "Ver Todo" + "Crear Plano"

6. **❌ Widget de Touch-ups**
   - Mostrar últimos touch-ups pendientes/completados
   - Estadísticas: Total, Pendientes, En Proceso, Completados
   - Botones: "Ver Panel" + "Ver Mis Touch-ups"

7. **❌ Widget de Change Orders Summary**
   - Mostrar resumen por columna: Draft, Review, Approved, etc.
   - Total de COs activos
   - Botón: "Ver CO Board"

### 🔄 **REORGANIZACIÓN SUGERIDA:**

#### **Grupo 1: Navegación Principal (Top Buttons - Primera fila)**
```html
<div class="btn-group" role="group">
  <a href="floor_plans" class="btn btn-outline-info">
    <i class="bi bi-blueprint"></i> Planos 2D
  </a>
  <a href="touch-ups" class="btn btn-outline-warning">
    <i class="bi bi-brush"></i> Touch-ups
  </a>
  <a href="damages" class="btn btn-outline-danger">
    <i class="bi bi-exclamation-diamond"></i> Daños
  </a>
  <a href="co_board" class="btn btn-outline-success">
    <i class="bi bi-kanban"></i> CO Board
  </a>
  <a href="files" class="btn btn-outline-primary">
    <i class="bi bi-folder2-open"></i> Archivos
  </a>
  <a href="daily_logs" class="btn btn-outline-secondary">
    <i class="bi bi-journal-text"></i> Daily Logs
  </a>
</div>
```

#### **Grupo 2: Herramientas y Reportes (Segunda fila)**
```html
<div class="btn-group ms-2" role="group">
  <a href="minutas" class="btn btn-outline-secondary">
    <i class="bi bi-journal-text"></i> Minutas
  </a>
  <a href="inventario" class="btn btn-outline-warning">
    <i class="bi bi-box-seam"></i> Inventario
  </a>
  <a href="profit" class="btn btn-outline-info">
    <i class="bi bi-graph-up"></i> Profit
  </a>
  <a href="ev" class="btn btn-outline-primary">
    <i class="bi bi-speedometer2"></i> EV
  </a>
</div>
```

#### **Grupo 3: Acciones Rápidas (Tercera fila)**
```html
<div class="btn-group ms-2" role="group">
  <a href="nuevo_co" class="btn btn-warning">
    <i class="bi bi-file-earmark-plus"></i> Nuevo CO
  </a>
  <a href="nueva_factura" class="btn btn-success">
    <i class="bi bi-receipt"></i> Nueva Factura
  </a>
  <a href="nueva_tarea" class="btn btn-outline-primary">
    <i class="bi bi-check2-square"></i> Nueva Tarea
  </a>
</div>
```

#### **Widgets Layout (Orden Sugerido - 2 columnas):**
```
Row 1:
[Floor Plans Widget - 6 col] [Touch-ups Widget - 6 col]

Row 2:
[CO Summary Widget - 6 col] [Damage Reports Widget - 6 col]

Row 3:
[Daily Logs Widget - 6 col] [Schedule Próximo - 6 col]

Row 4:
[Tareas Widget - 6 col] [Colores Widget - 6 col]

Row 5:
[Archivos Widget - 6 col] [Alertas/Issues Widget - 6 col]

Row 6:
[Sobras de Material Widget - 12 col] (tabla completa)
```

---

## 📋 PANEL 2: DAILY LOGS

### **Ubicación**: `/projects/<id>/daily-logs/` → `daily_logs_list.html`

### ✅ **Funciones Existentes:**
1. Listado de Daily Logs con fecha, resumen
2. Botón "Crear Daily Log"
3. Filtros por fecha
4. Integración con Schedule Events

### ❌ **FUNCIONES FALTANTES:**
1. **❌ Exportar a PDF** - Generar reporte PDF del log
2. **❌ Notificaciones** - Notificar al PM cuando se crea un log
3. **❌ Adjuntar fotos** - Permitir subir fotos al daily log
4. **❌ Vista de calendario** - Ver logs en formato calendario mensual
5. **❌ Búsqueda/Filtros avanzados** - Buscar por palabra clave

### 🔄 **CAMBIOS SUGERIDOS:**
- Agregar botón "📸 Agregar Fotos" en cada log
- Agregar botón "📄 Exportar PDF" 
- Agregar vista de calendario switch (Lista | Calendario)
- Agregar barra de búsqueda en el header

---

## 📊 PANEL 3: CO BOARD (Change Orders)

### **Ubicación**: `/changeorders/board/` → `co_board.html`

### ✅ **Funciones Existentes:**
1. Vista Kanban con columnas: Draft, Review, Approved, In Progress, Completed, Rejected
2. Drag & Drop entre columnas
3. Tarjetas con información básica (título, monto, estado)
4. Botón "Crear CO"

### ❌ **FUNCIONES FALTANTES:**
1. **❌ Filtros por proyecto** - El board NO tiene filtro por proyecto (crítico)
2. **❌ Búsqueda** - Buscar CO por número, título, o descripción
3. **❌ Estadísticas del board** - Cantidad de COs por columna, totales de montos
4. **❌ Botón de exportar** - Exportar board a Excel/PDF
5. **❌ Quick view modal** - Ver detalles del CO sin salir del board
6. **❌ Archivar COs** - Función para archivar COs completados/rechazados

### 🔄 **CAMBIOS SUGERIDOS:**
- **CRÍTICO**: Agregar filtro por proyecto en el header del board
- Agregar "Stats Bar" arriba del board: Total COs, Total $, por columna
- Agregar botón "👁️ Quick View" en cada tarjeta para modal
- Agregar botón "📦 Archivar" para COs completados
- Mejorar responsive del board para móvil

---

## 🗺️ PANEL 4: FLOOR PLANS (Planos 2D)

### **Ubicación Lista**: `/projects/<id>/plans/` → `floor_plan_list.html`
### **Ubicación Detail**: `/plans/<id>/` → `floor_plan_detail.html`

### ✅ **Funciones Existentes:**
1. Lista de planos por nivel (-∞ a +∞)
2. Crear nuevo plano con nivel y nombre
3. Subir imagen del plano
4. Ver plano con pines (Info pins)
5. Agregar pines con click
6. Modal de info del pin
7. **NUEVO**: Sistema de Toggle Mode (View | Edit)
8. **NUEVO**: Modo multipunto para líneas A→B→C
9. Zoom in/out/reset
10. Vincular pin a color sample
11. Crear tarea desde pin

### ✅ **Funciones COMPLETAS (Recientemente):**
1. Info pins - CRUD completo con fotos
2. Photo Annotation System - 6 herramientas de dibujo
3. Permisos extendidos (Client, Designer, Owner)

### ❌ **FUNCIONES FALTANTES:**
1. **❌ Duplicar plano** - Copiar plano con todos sus pines
2. **❌ Imprimir plano** - Vista de impresión optimizada
3. **❌ Exportar plano con pines** - Exportar imagen con pines dibujados
4. **❌ Historial de cambios** - Ver quién agregó qué pines y cuándo
5. **❌ Búsqueda de pines** - Buscar pin por título/descripción
6. **❌ Filtros de pines** - Filtrar por tipo, estado, usuario
7. **❌ Overlay de cuadrícula** - Grid overlay para mediciones
8. **❌ Medición de distancias** - Herramienta de medición

### 🔄 **CAMBIOS SUGERIDOS:**
- Agregar botones en header de floor_plan_detail:
  - "🖨️ Imprimir"
  - "📥 Exportar con Pines"
  - "📋 Duplicar Plano"
- Agregar panel lateral de "Filtros":
  - Por tipo de pin (info, touchup, damage)
  - Por usuario creador
  - Por fecha
- Agregar "📊 Estadísticas" colapsable:
  - Total de pines
  - Por tipo
  - Por estado

---

## 🎨 PANEL 5: TOUCH-UP SYSTEM

### **Ubicación Lista**: `/projects/<id>/touchup-plans/` → `touchup_plans_list.html`
### **Ubicación Detail**: `/touchups/<plan_id>/` → `touchup_plan_detail.html`
### **Ubicación Employee**: `/touchups/my-touchups/` → `employee_touchup_list.html`

### ✅ **Funciones Existentes:**
1. Panel de gestión para PM/Admin
2. Vista de empleado para asignados
3. Crear touch-up pin en plano
4. Asignar a empleado
5. Completar con fotos
6. **NUEVO**: Photo Annotation en completion
7. Estado: Pendiente, En Proceso, Completado
8. Permisos extendidos (Client, Designer, Owner pueden crear/editar)

### ❌ **FUNCIONES FALTANTES:**
1. **❌ Historial de completions** - Ver todas las fotos de completion históricas
2. **❌ Aprobar/Rechazar completion** - PM puede aprobar o pedir re-trabajo
3. **❌ Comentarios en touch-up** - Thread de comentarios entre PM y empleado
4. **❌ Notificaciones push** - Notificar al empleado cuando se asigna
5. **❌ Prioridad** - Marcar touch-ups como Alta/Media/Baja prioridad
6. **❌ Tiempo estimado vs real** - Tracking de tiempo
7. **❌ Estadísticas de empleado** - Cuántos completados, promedio de tiempo
8. **❌ Exportar reporte** - PDF con todos los touch-ups del proyecto

### 🔄 **CAMBIOS SUGERIDOS:**
- Agregar campo "Prioridad" al modelo TouchUpPin
- Agregar botones en completion:
  - "✅ Aprobar" (PM/Admin)
  - "❌ Rechazar" (con motivo)
- Agregar sección de comentarios en touchup_plan_detail
- Agregar "📊 Estadísticas" en touchup_plans_list:
  - Total, Pendientes, En Proceso, Completados
  - Por empleado
  - Tiempo promedio
- Agregar botón "📄 Exportar Reporte"

---

## 🔴 PANEL 6: DAMAGE REPORTS (Reportes de Daño)

### **Ubicación**: `/projects/<id>/damages/` → `damage_report_list.html`
### **Ubicación Detail**: `/damages/<id>/` → `damage_report_detail.html`

### ✅ **Funciones Existentes:**
1. Crear reporte de daño con título, descripción
2. Subir múltiples fotos
3. **NUEVO**: Photo Annotation en creación
4. Estado: Reported, Under Review, In Progress, Resolved, Closed
5. Asignar responsable
6. Vincular a proyecto

### ❌ **FUNCIONES FALTANTES:**
1. **❌ Categoría de daño** - Structural, Cosmetic, Safety, etc.
2. **❌ Severidad** - Low, Medium, High, Critical
3. **❌ Costo estimado** - Campo para costo de reparación
4. **❌ Fecha de reporte vs resolución** - Tracking de tiempo
5. **❌ Vincular a touch-up** - Si el daño genera un touch-up
6. **❌ Vincular a CO** - Si el daño requiere un Change Order
7. **❌ Comentarios/Updates** - Thread de actualizaciones
8. **❌ Notificaciones** - Notificar cuando cambia estado
9. **❌ Exportar reporte** - PDF del damage report
10. **❌ Dashboard de estadísticas** - Ver todos los daños del proyecto

### 🔄 **CAMBIOS SUGERIDOS:**
- Agregar campos al modelo DamageReport:
  - `category` (choices)
  - `severity` (choices)
  - `estimated_cost` (decimal)
  - `linked_touchup` (FK)
  - `linked_co` (FK)
- Agregar sección de comentarios
- Agregar botón "🔗 Vincular a Touch-up"
- Agregar botón "🔗 Vincular a CO"
- Agregar "📊 Dashboard" en damage_report_list con métricas
- Agregar botón "📄 Exportar PDF"

---

## 📁 PANEL 7: FILE ORGANIZATION (Archivos)

### **Ubicación**: `/projects/<id>/files/` → `project_files_view.html`

### ✅ **Funciones Existentes:**
1. Sistema de 7 categorías:
   - Contracts
   - Invoices
   - Reports
   - Photos
   - Drawings
   - Permits
   - Other
2. Crear categoría custom
3. Subir archivos a categoría
4. Metadata (nombre, descripción, tags)
5. Download files
6. Delete files

### ❌ **FUNCIONES FALTANTES:**
1. **❌ Preview de archivos** - Ver PDF/imágenes sin descargar
2. **❌ Versiones de archivo** - Historial de versiones del mismo archivo
3. **❌ Búsqueda por tags** - Buscar archivos por etiquetas
4. **❌ Filtros avanzados** - Por fecha, tamaño, tipo, usuario
5. **❌ Compartir link** - Generar link temporal para compartir
6. **❌ Organizar por carpetas** - Subcarpetas dentro de categorías
7. **❌ Arrastrar y soltar** - Drag & drop para subir múltiples archivos
8. **❌ Zip download** - Descargar categoría completa como ZIP
9. **❌ Mover archivo** - Mover entre categorías
10. **❌ Editar metadata** - Editar nombre/descripción después de subir

### 🔄 **CAMBIOS SUGERIDOS:**
- Implementar vista previa (iframe para PDF, lightbox para imágenes)
- Agregar sistema de versiones:
  - Botón "📤 Subir Nueva Versión"
  - Ver historial de versiones
- Agregar barra de búsqueda con filtros
- Agregar drag & drop zone para uploads
- Agregar botón "📦 Descargar Todo" (ZIP)
- Agregar botón "✏️ Editar" en cada archivo
- Agregar botón "🔗 Compartir" con link temporal

---

## 📊 RESUMEN DE CAMBIOS PRIORITARIOS

### **🔴 CRÍTICO (Hacer Primero):**
1. **CO Board**: Agregar filtro por proyecto
2. **Project Overview**: Agregar botones faltantes (Floor Plans, Touch-ups, Damages, CO Board)
3. **Project Overview**: Agregar widgets faltantes (Floor Plans, Touch-ups, CO Summary)
4. **Damage Reports**: Agregar campos category, severity, estimated_cost

### **🟡 IMPORTANTE (Hacer Segundo):**
5. **Touch-ups**: Sistema de aprobación/rechazo de completions
6. **Floor Plans**: Exportar plano con pines dibujados
7. **File Organization**: Preview de archivos y drag & drop
8. **Daily Logs**: Agregar fotos y exportar PDF

### **🟢 MEJORA (Hacer Tercero):**
9. **Todos los panels**: Agregar búsqueda y filtros avanzados
10. **Todos los panels**: Agregar botones de exportar (PDF/Excel)
11. **Damage Reports**: Sistema de comentarios
12. **Touch-ups**: Estadísticas por empleado

---

## 📝 PLAN DE IMPLEMENTACIÓN

### **FASE 1: Project Overview (30 min)**
- Agregar botones faltantes en header
- Crear widgets de Floor Plans, Touch-ups, CO Summary
- Reorganizar layout de widgets

### **FASE 2: CO Board (20 min)**
- Agregar filtro por proyecto
- Agregar stats bar
- Mejorar responsive

### **FASE 3: Damage Reports Enhancement (45 min)**
- Agregar campos al modelo (migration)
- Actualizar formularios
- Agregar vinculación a Touch-ups/COs
- Agregar dashboard de estadísticas

### **FASE 4: Touch-up System Enhancement (45 min)**
- Agregar sistema de aprobación
- Agregar campo prioridad
- Agregar sección de comentarios
- Agregar estadísticas

### **FASE 5: File Organization Enhancement (60 min)**
- Implementar preview
- Agregar drag & drop
- Agregar edición de metadata
- Agregar ZIP download

### **FASE 6: Polish & UX (30 min)**
- Agregar búsqueda en todos los panels
- Mejorar mensajes de feedback
- Agregar loading states
- Testing completo

---

**Total Estimado**: 4-5 horas de implementación

