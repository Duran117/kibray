# 🔍 FASE 1: AUDITORÍA INICIAL (25 Nov 2025)

## Objetivo
Identificar dependencias críticas, campos legacy, riesgos de refactor y orden sugerido de intervención antes de continuar con nuevas fases.

---
## 1. Modelos Auditados
| Modelo | Rol | Dependencias clave | Observaciones |
|--------|-----|--------------------|---------------|
| `Task` | Núcleo de ejecución | FK `Project`, M2M histórico (TaskStatusChange), integración `TimeEntry` (via FK task), relaciones futuras con TouchUp/ColorSamples | Estados en español -> consistencia con otros módulos; status no normalizado con enums globales; priorización OK |
| `TimeEntry` | Tracking horas | FK `Employee`, FK `Project`, FK `Task`, FK `CostCode`, opcional `ChangeOrder` | Doble fuente de costos: labor_cost calculable; riesgo si se recalcula horas vs payroll snapshot |
| `MaterialRequest` | Flujo de aprovisionamiento | FK `Project`, FK `User (requested_by)`, items -> `MaterialRequestItem`, integra con Inventory/Expenses indirecto | Status incluye estado deprecated (`submitted`); conviene migrar a mapping interno y remover en nueva versión |
| `DailyPlan` | Planificación operativa | FK `Project`, FK `User (created_by)`, M2M `planned_templates`, `planned_tasks`, relación implícita con `WeatherSnapshot` futuro | `completion_deadline` naive datetimes (warnings en tests); falta automatización Celery para clima |
| `InventoryMovement` | Movimientos stock | FK `InventoryItem`, FK `InventoryLocation`, opcional `Task`, `Project`, `Expense` | Campo `note` marcado Legacy; distinguir razón vs note; considerar soft delete/audit trail extendido |
| `PayrollPeriod` / `PayrollRecord` / `PayrollPayment` | Nómina | `PayrollRecord` vincula empleado y periodo; `PayrollPayment` apunta a `PayrollRecord` | Comentarios DEPRECATED viejos (líneas 1024 etc.) todavía en codebase; limpiar para evitar confusión |
| `Invoice` | Facturación | FK `Project`, OneToOne `Income`, campos legacy `is_paid`, `amount_paid` coexistiendo | Doble representación de estado de pago; refactor: usar sólo `amount_paid` + derivar `is_paid` calculado |
| `ProjectInventory` | Estado stock por ubicación | FK `InventoryItem`, FK `InventoryLocation` | `threshold_override` + `default_threshold` (legacy) duplican lógica; consolidar en regla única |

---
## 2. Campos / Patrones Legacy Detectados
| Ubicación | Tipo | Descripción | Acción sugerida |
|-----------|------|-------------|----------------|
| `Invoice.is_paid` | Campo duplicado | Redundante con `amount_paid` y `status` | Marcar para remoción futura (migración) |
| `MaterialRequest.status='submitted'` | Estado deprecated | Mantener compat pero no generar nuevo uso | Añadir validación que no se asigne en nuevas creaciones |
| `InventoryItem.default_threshold` (3307) | Legacy | Umbral base vs override; falta política clara | Definir política: usar `item.default_threshold` + overrides por ubicación |
| `InventoryMovement.note` | Legacy | Sobreposición con `reason` | Deprecar `note`, migrar a `reason` en UI |
| Deprecated Payroll comentarios (línea 1024, forms) | Comentarios muertos | Confusión para nuevos devs | Eliminar tras confirmación negocio |
| Legacy templates seleccionables vía query param `?legacy=true` | Compatibilidad visual | Mantener hasta completar rediseño | Documentar fecha de sunset |
| DailyPlan naive datetime warnings (`completion_deadline`) | Riesgo TZ | Genera runtime warnings | Normalizar a timezone aware (usar `settings.TIME_ZONE`) |
| Weather service TODOs (`services/weather.py`) | Feature incompleta | Falta cache + API call real | Implementar en FASE 2 (pendiente) |

---
## 3. Dependencias Críticas
| Origen | Depende de | Tipo | Riesgo si cambia |
|--------|-----------|------|------------------|
| `TimeEntry` | `Task` | FK directo | Cambios de status/nombres en Task pueden afectar reporting de horas |
| `PayrollRecord` | `TimeEntry` (lógica externa) | Agregación | Cambiar estructura de TimeEntry rompe generación automática de nómina |
| `DailyPlan` | `TaskTemplate` / `Task` | M2M conversión | Cambios en TaskTemplate fields requieren migrar conversion logic |
| `MaterialRequest` | `InventoryMovement` (implícito en recepción) | Secuencia de procesos | Refactors en InventoryMovement deben asegurar continuidad recepción + expense link |
| `Invoice` | `Income` | OneToOne | Eliminación/migración de Invoice debe preservar link histórico de ingresos |
| `InventoryMovement` | `Expense` | FK opcional | Refactor de Expense categories puede requerir mapping nuevo |
| `ProjectInventory` | `InventoryItem` | Cálculos | Cambio en método de valuation o avg cost impacta dashboards |

---
## 4. Riesgos Potenciales
1. Doble semántica de estados (ej: Tasks estados en ES, algunos otros en EN) -> inconsistencia filtrado API.
2. Campos Legacy pueden causar divergencia si lógica de actualización no unificada (Invoice.is_paid vs status).
3. Falta timezone awareness en `DailyPlan.completion_deadline` puede romper lógica de validación en despliegues multi‑TZ.
4. Weather integración incompleta: paneles futuros pueden mostrar datos nulos/inconsistentes.
5. Estados deprecated (`submitted`) podrían seguir apareciendo en reportes si no se filtran.
6. Uso de `note` en InventoryMovement sin propósito claro; duplicidad semántica.

---
## 5. Recomendaciones de Refactor (Orden Sugerido)
| Prioridad | Acción | Justificación | Esfuerzo |
|-----------|--------|---------------|----------|
| 🔴 Alta | Unificar pago factura: derivar `is_paid` dinámico | Evita estados inconsistentes | Bajo (1 migración + serializer) |
| 🔴 Alta | Normalizar estados Task a set estándar (EN o ES) | Cohesión API y filtros | Medio (update choices + data migration) |
| 🟡 Media | Remover estado `submitted` en MaterialRequest (soft deprecate) | Reduce ruido | Bajo |
| 🟡 Media | Timezone aware para `completion_deadline` | Elimina warnings y errores futuros | Bajo |
| 🟡 Media | Documentar y programar sunset de templates legacy | Claridad roadmap | Bajo |
| 🟡 Media | Consolidar threshold lógica Inventory (override vs default) | Simplifica cálculos | Medio |
| 🟢 Baja | Remover comentarios DEPRECATED antiguos (Payroll) | Limpieza código | Bajo |
| 🟢 Baja | Deprecar `note` en InventoryMovement | Claridad datos | Bajo |
| 🟢 Baja | Implementar WeatherService real + cache | Completa FASE 2 | Medio |

---
## 6. Próximos Pasos de Auditoría (Acción Inmediata)
1. Crear migración planeada para Invoice (marcar `is_paid` como deprecated en comentario + preparar script de migración futura).
2. Añadir validación en creación MaterialRequest para bloquear uso de `submitted`.
3. Agregar helper para convertir `completion_deadline` a timezone aware al guardar.
4. Redactar SPEC corto para normalización de estados (Tasks + otros modelos multi-idioma).
5. Agendar implementación WeatherService (FASE 2) tras finalizar auditoría.

---
## 7. Backup
Se creó copia de seguridad: `db_backup_phase1_20251125.sqlite3`

---
## 8. Decisión Recomendada
Iniciar refactors rápidos (Alta prioridad) antes de arrancar FASE 2 Weather:
- Unificación pago factura
- Validación estado deprecated MaterialRequest
- TZ fix DailyPlan

Luego continuar con FASE 2 (Weather) para cerrar núcleo de planificación.

---
## 9. Checklist de Riesgo Post-Refactor
| Ítem | Validar tras cambio |
|------|---------------------|
| Facturas pagadas | Dashboard financial refleja correctamente pagos |
| Material requests | Ninguna nueva con estado deprecated |
| Daily plan warnings | No aparece warning naive datetime |
| Payroll generación | No se rompe al quitar legacy comentarios |
| Inventory valuation | Threshold logic no altera alerts |

---
_Reporte generado automáticamente (FASE 1)._ ✅
