# Plan de implementación: Scheduler estilo Gantt

## Objetivo
Construir un scheduler con fases, items y tareas (tipo Gantt) similar a la referencia visual, primero en entorno local, luego integrarlo en la app.

## Alcance MVP (fase 1)
- Modelo de datos mínimo:
  - Project (existente)
  - SchedulePhase (proyecto, nombre, color, orden)
  - ScheduleItem (fase, nombre, start_date, end_date, assigned_to, color, status, order)
  - ScheduleTask (item, título, status, due_date opcional, order)
  - ScheduleDependency (source_item, target_item, tipo=FS)
- API read-only por proyecto (JSON jerárquico: fases → items → tareas, dependencias aparte).
- UI Gantt read-only (timeline con línea de hoy, zoom días/semana/mes).
- Filtros básicos (asignado, rango de fechas).

## Requisitos de UI/UX y librería
- Librería principal: **React Modern Gantt** (MIT) para la app interna en React. Si algún requisito no se cumple, fallback: **Frappe Gantt** (MIT) envuelta en un componente React.
- Requisitos funcionales clave: timeline multi-proyecto, jerarquía (fases → items → tareas), hitos/milestones, dependencias (links tipo FS), drag & drop para mover/redimensionar y actualizar progreso, callbacks/eventos para persistir cambios.
- Paleta y estilo: futurista, minimalista y limpia; colores vivos pero balanceados, con buen contraste. Ajustar palette centralizada en theme para iterar rápido.
- Calendario laboral: domingo es el único día off por defecto; si el proyecto lo exige, se podrá trabajar domingo (mostrar/permitir según bandera por proyecto/config).

## Iteraciones previstas
1) **Diseño y migraciones**: definir modelos y migraciones.
2) **API read-only**: endpoint que devuelve datos para un proyecto.
3) **UI Gantt read-only**: render de barras y línea de hoy.
4) **CRUD básico**: crear/editar/mover items y tareas.
5) **Dependencias**: alta/baja y visualización.
6) **Asignación y filtros**: dropdown de usuarios, filtro por asignado.
7) **Baselines (opcional)** y métricas de delta.

## Checklist de avance
- [x] Definir modelos y relaciones (SchedulePhaseV2, ScheduleItemV2, ScheduleTaskV2, ScheduleDependencyV2)
- [x] Crear migraciones (0141_gantt_v2_models)
- [x] Serializadores/endpoint read-only por proyecto (GET /api/gantt/v2/projects/<id>/)
- [x] UI Gantt read-only (timeline, línea de hoy)
- [x] CRUD Items/Tareas (POST/PATCH)
- [x] Dependencias (POST/DELETE)
- [x] Filtros (asignado, rango)
- [x] Pruebas básicas (unit/integration API)

Nota: se usaron modelos **V2** para evitar colisiones con el cronograma legado (ScheduleCategory/ScheduleItem).

## Decisiones pendientes
- Librería Gantt: **React Modern Gantt** (MIT). Fallback: Frappe Gantt (MIT) envuelta para React si falta alguna capacidad.
- Manejo de días laborables vs. fines de semana (MVP: todos los días). 
- Control de concurrencia: optimistic locking por `updated_at` en API (opcional).

## Suposiciones iniciales
- Usaremos fechas (date) sin TZ para el Gantt diario.
- Asignación a usuarios existentes (`auth_user`).
- Colores simples (palette predefinida).

## Riesgos
- Payload grande en proyectos con muchos items: considerar filtro por rango de fechas y paginación.
- Ciclos en dependencias: validar en backend.
- Integración con permisos: PM/Admin editan, empleados ven.
