# Touch-Up Board (Module 28) - Arquitectura Propuesta

## Objetivo
Centralizar, visualizar y cerrar pendientes de retoque (paint touch-ups, punch items menores) con flujo propio separable de tareas generales, evitando sobrecargar el backlog de `Task`.

## Alternativas de Modelo
1. Reutilizar `Task` con flag `is_touchup` (ya existe).
   - Pros: Sin migraciones complejas, reutiliza señales y auditoría.
   - Contras: Mezcla métricas de productividad, tablero principal se llena.
2. Modelo dedicado `TouchUp`.
   - Campos sugeridos:
     - `project` FK
     - `title` (short)
     - `description` (detalles opcionales)
     - `status` (choices: `Pendiente`, `En Progreso`, `Listo Foto`, `Rechazado`, `Cerrado`)
     - `reported_by` (user/profile)
     - `assigned_to` (employee opcional)
     - `required_photo` (bool default True)
     - `closed_at` datetime
     - `room_location` (string / future relation)
     - `priority` (Baja/Media/Alta)
     - `image_current` (FK a última foto) + `images` M2M / related
   - Pros: Aislamiento semántico, métricas específicas, flujo distinto.
   - Contras: Duplica cierta lógica (fotos, status changes, notificaciones).

Recomendación: FASE 1 usar `Task(is_touchup=True)` + vista Kanban separada. FASE 2 migrar a modelo dedicado si la complejidad/reglas se expanden.

## Workflow
- `Pendiente` → creado.
- `En Progreso` → alguien lo toma.
- `Listo Foto` → marcado como listo con foto obligatoria recién subida.
- Validación automática: si pasa a `Listo Foto` sin nueva imagen -> error.
- `Cerrado` → aprobado por rol `project_manager` o `quality_inspector`.
- `Rechazado` → PM rechaza foto (vuelve a `En Progreso`).

## Señales / Lógica
- Pre-save: si status cambia a `Listo Foto` verificar existencia imagen subida < 10m.
- Post-save: notificar creador + PM en cierre o rechazo.
- Imagen versioning ya gestionado por `TaskImage` (reutilizable).

## Kanban Board
Columnas: Pendiente | En Progreso | Listo Foto | Rechazado | Cerrado

Filtros: Proyecto, Prioridad, Habitacion (room_location), Fecha creación.

Acciones rápidas:
- Botón "Tomar" (cambia a En Progreso).
- Subir foto (arrastrar) + auto-cambio a Listo Foto.
- Aprobación (PM) → Cerrado.
- Rechazo (PM) → Rechazado con comentario.

## Métricas
- Tiempo promedio Pendiente → Cerrado.
- % Rechazados por semana.
- TouchUps abiertos por prioridad.
- Mapa calor de habitaciones (futuro).

## Próximos Pasos
1. Agregar vistas filtradas para `Task(is_touchup=True)`.
2. Añadir validación mínima foto en transición a `Completada` si `is_touchup`.
3. Definir roles que pueden cerrar (config simple en settings o tabla).
4. Recolectar feedback usuarios antes de crear modelo dedicado.

