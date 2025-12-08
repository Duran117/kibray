# LISTA DE CORRECCIONES PENDIENTES - KIBRAY

## ✅ COMPLETADAS

1. **models.Sum → Sum** - Corregido error en views.py líneas 1503, 2181, 2189, 2194, 2203, 2210
2. **Templates de tareas** - Corregido task_list.html y task_detail.html para mostrar empleado asignado correctamente
3. **Change Orders board** - Funcionando después de corregir Sum
4. **Profit dashboard** - Funcionando después de corregir Sum

## 🔴 ERRORES CRÍTICOS (Requieren atención inmediata)

### 3. Planos 2D - Error al abrir después de guardar
**Síntoma**: Usuario puede crear planos pero al intentar abrirlos da error
**Archivo**: core/views.py - floor_plan_detail (línea ~1017)
**Prioridad**: ALTA

### 4. Planning/Daily Plans - No carga
**Síntoma**: Planning no carga, no se pueden crear o ver daily logs
**Archivos**: core/views.py - daily_plan views
**Prioridad**: ALTA

### 5. Sobras de pintura - No permite registrar
**Síntoma**: No se pueden registrar paint leftovers
**Archivos**: Posiblemente falta vista o formulario
**Prioridad**: MEDIA

## 📋 FUNCIONALIDADES FALTANTES

### 6. Botón crear Invoice
**Descripción**: No hay botón visible en /invoices/ para crear nuevo invoice
**Solución**: Agregar botón en template de lista de invoices
**Prioridad**: ALTA

### 7. Panel de horas semanales para nómina
**Descripción**: Ver entrada/salida de cada empleado por semana antes de aprobar nómina
**Solución**: Crear nueva vista con resumen semanal de TimeEntry
**Archivos**: Nueva vista + template
**Prioridad**: MEDIA

### 8. Calendario en dashboard de proyecto
**Descripción**: Debe mostrar calendario limpio con línea de progreso del día actual
**Solución**: Implementar calendario con FullCalendar.js o similar
**Prioridad**: MEDIA

### 9. Visualización de colores
**Descripción**: No se pueden ver los colores guardados en sección de colores
**Solución**: Mejorar template color_samples para mostrar colores visualmente
**Prioridad**: BAJA

### 10. Fotos en damage reports
**Descripción**: Los damage reports funcionan pero no permiten agregar fotos
**Solución**: Agregar campo de imagen y actualizar formulario
**Prioridad**: MEDIA

### 11. Mantener en panel después de guardar
**Descripción**: Al guardar actividad en proyecto, redirige a dashboard principal (debería mantenerse en proyecto)
**Solución**: Cambiar redirect en vistas de proyecto
**Prioridad**: BAJA

### 12. Registro de archivos en proyecto
**Descripción**: No permite subir/registrar archivos en dashboard de proyecto
**Solución**: Crear modelo ProjectFile + vista + formulario
**Prioridad**: MEDIA

## 🚀 FUNCIONALIDADES AVANZADAS (Para fase 2)

### 13. Sistema touch-up con plano 2D
**Descripción**: Función para crear touch-ups usando plano 2D con pins interactivos
**Complejidad**: ALTA
**Estimado**: 8-12 horas
**Requiere**: JavaScript interactivo + backend API

### 14. Panel información proyecto con plano 2D
**Descripción**: Ver/editar info con plano 2D de fondo, agregar pins con fotos/instrucciones/punch list
**Complejidad**: ALTA
**Estimado**: 12-16 horas
**Requiere**: Canvas/SVG JavaScript + drag-drop + API REST

## 📊 RESUMEN

- ✅ Completadas: 4
- 🔴 Críticas: 3
- 📋 Faltantes: 9
- 🚀 Avanzadas: 2

**Total tareas**: 18

## 🎯 RECOMENDACIÓN DE PRIORIDAD

1. **Inmediato** (hoy):
   - Corregir error planos 2D
   - Agregar botón crear Invoice
   - Corregir Planning/Daily Plans

2. **Esta semana**:
   - Panel horas semanales nómina
   - Sobras de pintura
   - Fotos en damage reports
   - Registro de archivos

3. **Siguiente iteración**:
   - Calendario proyecto
   - Visualización colores
   - Mantener en panel
   - Sistema touch-up avanzado
   - Panel información proyecto

