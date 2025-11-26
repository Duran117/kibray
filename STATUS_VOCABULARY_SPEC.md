# Status Vocabulary Normalization Spec

## Objective
Unificar los estados entre modelos clave eliminando duplicados, términos deprecados y mejorando consistencia semántica antes de migraciones mayores.

## Scope
Modelos incluidos en esta primera normalización:
- Invoice
- MaterialRequest
- DailyPlan (ya consistente tras introducción de nuevos estados)

## Principles
1. Estados deben reflejar exclusivamente *estado actual* (no acción pasada) y ser mutuamente excluyentes.
2. Preferir inglés consistente para API (`SENT`, `PENDING`) manteniendo traducción vía `get_status_display()` / i18n.
3. Evitar booleanos redundantes cuando puede derivarse del monto (ej: `fully_paid` en vez de `is_paid`).
4. Eliminar estados de transición obsoletos (`submitted`).

## Current vs Target Mapping

### Invoice
| Current | Target | Notes |
|---------|--------|-------|
| DRAFT | DRAFT | Sin cambio |
| SENT | SENT | Ok |
| VIEWED | VIEWED | Mantener para métricas engagement |
| APPROVED | APPROVED | Aprobación interna / cliente |
| PARTIAL | PARTIAL | Pago parcial, derivado de amount_paid < total_amount |
| PAID | PAID | Pago completo (derivado) |
| OVERDUE | OVERDUE | Solo si balance_due > 0 y fecha vencida |
| CANCELLED | CANCELLED | Mantener |

No cambios semánticos; migración futura: remover campo `is_paid`. Añadir constraint lógica en migración final: `CHECK (amount_paid <= total_amount * 1.25)` para limitar sobrepago extremo.

### MaterialRequest
| Current | Target | Notes |
|---------|--------|-------|
| draft | DRAFT | Normalizar mayúsculas opcional (evaluar impacto). Mantener por ahora. |
| pending | PENDING | Mapeo directo |
| approved | APPROVED | Ok |
| submitted | (remove) | Deprecated; bloqueado en código |
| ordered | ORDERED | Ok |
| partially_received | PARTIAL_RECEIVED | Normalizar snake -> upper + underscore |
| fulfilled | FULFILLED | Ok |
| cancelled | CANCELLED | Ok |
| purchased_lead | PURCHASED_DIRECT | Clarificar significado (compra directa por líder) |

#### Migration Strategy MaterialRequest
1. Introducir nuevo conjunto `NEW_STATUS_CHOICES` en código aceptando ambos (transitional) durante 1 release.
2. Data migration: actualizar filas:
   - `partially_received -> PARTIAL_RECEIVED`
   - `purchased_lead -> PURCHASED_DIRECT`
3. Añadir constraint: eliminar `submitted` del enum final.
4. Remover compat alias después de estabilización.

## DailyPlan
Estados ya consistentes: `DRAFT`, `PUBLISHED`, `IN_PROGRESS`, `COMPLETED`, `SKIPPED`. No acción requerida.

## API / Serializer Impact
- Añadir validación centralizada: rechazar valores legacy tras período de gracia.
- Documentar en `API_README.md` los nuevos valores y fecha de corte.

## Deprecation Timeline
| Phase | Acción |
|-------|--------|
| R0 (actual) | Bloqueo creación `submitted`, documentación spec |
| R1 | Introducir alias mapping y aceptar ambos valores MaterialRequest (except `submitted`) |
| R2 | Migración datos + warnings en logs si se detecta legacy |
| R3 | Remover legacy choices y `is_paid` campo en Invoice |

## Testing Plan
- Unit tests para: bloqueo estados deprecated, migración mapping correcta, derivación de pago Invoice.
- Snapshot tests para endpoints afectados validando nuevos valores.

## Risks & Mitigación
- Reportes externos consumiendo valores legacy: Proveer tabla de compat temporal en respuesta (`legacy_status` opcional) durante R1-R2.
- Scripts internos: Comunicación vía CHANGELOG y ejemplo de actualización.

## Next Steps
1. Implementar compat layer de estados MaterialRequest (R1).
2. Programar data migration (R2).
3. Preparar removal final `is_paid` (R3).
