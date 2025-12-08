# FASE 1 – Auditoría y Preparación

Fecha: 2025-11-25

## Resumen Ejecutivo
Se revisaron los modelos núcleo (Task, DailyLog→DailyPlan, Inventory, Payroll, ColorSample, FloorPlan/Pin, DamageReport, Schedule) y se implementaron mejoras estructurales iniciales para habilitar las fases siguientes: extensión de DailyLog como plan diario, señales de auditoría y versionado de imágenes, método de reapertura de tareas y modelo de caché meteorológico (`WeatherSnapshot`).

## Objetivos Cumplidos
- Inventario de relaciones y dependencias críticas (Task ↔ Schedule ↔ DailyLog, Inventory, Payroll).
- Extensión de `DailyLog` a plan operativo (campos: planned_templates, planned_tasks, is_complete, incomplete_reason, auto_weather + métodos instantiate/evaluate).
- Señales para Task: auditoría de cambios de estado, `completed_at` automático, recálculo de progreso en Schedule.
- Versionado automático `TaskImage` vía señal post_save.
- Método `Task.reopen()` para revertir estados terminados y registrar cambio.
- Modelo `WeatherSnapshot` agregado (caché diario por proyecto y fecha).
- Migración aplicada sin errores (0074 + nueva para WeatherSnapshot pendiente de generar).
- Backup de base de datos creado.

## Hallazgos Clave
1. Prioridades de Task inconsistentes (mezcla de idiomas y valores). Requiere normalización interna.
2. Duplicidad conceptual: `DailyLog` vs posible `DailyPlan` separado. Se decidió extender en vez de duplicar modelo (minimiza migraciones y debt).
3. Auditoría de estado de Task era manual y dispersa; ahora centralizada en señales.
4. Versionado de imágenes se hacía a mano; ahora automatizado.
5. Falta de fuente meteorológica: se introduce caché `WeatherSnapshot` para soporte de clima y análisis de productividad.
6. Posible legacy en Invoice (campos como `is_paid` vs `status`) y cost codes con potencial desalineación de indexing.

## Riesgos y Mitigaciones
| Riesgo | Impacto | Mitigación |
|--------|---------|------------|
| Inconsistencia prioridad | Filtrado/reportes erróneos | Normalizar enumeración + i18n mapping |
| Ausencia clima real | Incompletitud DailyPlan y métricas | Servicio Open-Meteo + caché WeatherSnapshot |
| Falta de auditoría histórica completa | Difícil reconstruir línea temporal | Señales ya registran `TaskStatusChange`; validar integridad periódicamente |
| Plantillas duplicadas instanciadas | Tareas redundantes | Lógica idempotente en `instantiate_planned_templates` |
| Crecimiento no controlado de snapshots | Espacio y rendimiento | TTL refresco (6h) + limpieza programada futura |

## Recomendaciones Inmediatas (Fase 2)
1. Implementar servicio clima (`core/services/weather.py`) con fetch + caching.
2. Añadir endpoints API para: obtener clima del día, instanciar plantillas, marcar plan como evaluado/completo.
3. Normalizar prioridades: agregar choices internos (low, medium, high, urgent) y migrar valores existentes.
4. Tests unitarios mínimos: `Task.reopen()`, `DailyLog.instantiate_planned_templates()`, `DailyLog.evaluate_completion()`, `WeatherSnapshot` fetch.
5. Agregar tarea de limpieza (cron / Celery beat) futura para snapshots antiguos (>30 días).

## Plan de Datos (WeatherSnapshot)
- Unicidad: (project, date, source).
- TTL: refrescar si `is_stale()` > 6h.
- Campos para analítica: temperatura, precipitación, humedad, viento.

## Próximos Pasos Concretos
1. Generar migración para `WeatherSnapshot`.
2. Crear servicio clima y funciones `get_or_fetch_weather(project, date)`.
3. Exponer serializer y endpoint `/api/projects/{id}/daily/{date}/weather/`.
4. Normalización prioridad Task (migración + mapping).
5. Escribir pruebas.

## Métricas Iniciales a Capturar en Fase 2
- Tiempo promedio de cierre de tareas planificadas vs no planificadas.
- Correlación clima (precipitación, temperatura extrema) con % de tareas planificadas completadas.
- Frecuencia de reopen sobre total de completadas.

## Pendientes Catalogados
- Legacy: Invoice status vs is_paid; cost code indexing; prioridades mixtas.
- Touch-Up board formal (kanban) aún no separado; dependerá de normalizar estados.
- Firma digital y EVM dinámico pospuestos a fases avanzadas.

---
Documento generado automáticamente (FASE 1). Ajustar manualmente si se requiere mayor detalle narrativo.
