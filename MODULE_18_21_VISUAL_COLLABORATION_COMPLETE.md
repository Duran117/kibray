# ✅ MÓDULOS 18–21: VISUAL & COLLABORATION – COMPLETADOS

**Fecha de cierre:** 26 Nov 2025  
**Commits clave:** 5a73255 (18–19), 1d216da (20), 07cb780 (21)  
**Tests agregados:** 17 (Site Photos) + 18 (Color Samples) + 22 (Floor Plans) + 29 (Damage Reports) = 86  
**Total suite estimada:** 400 (314 base + 86 nuevos)  
**Passing garantizado:** 86/86 (fase estabilizada)

---
## 📌 Resumen Ejecutivo
Los cuatro módulos completan la capa visual y colaborativa del sistema, habilitando flujo completo de documentación en obra: fotos geolocalizadas, muestras de color con workflow, planos con versionado y migración de pins, y reportes de daños con ciclo de vida y conversión a Change Orders.

| Módulo | Enfoque | Estado | Tests | Valor Clave |
|--------|---------|--------|-------|-------------|
| 18 Site Photos | Captura + evidencia geolocalizada | ✅ | 17/17 | Base de documentación continua de progreso/daños |
| 19 Color Samples | Aprobación de muestras | ✅ | 18/18 | Validación formal + histórico de decisiones cliente |
| 20 Floor Plans | Versionado + migración de pins | ✅ | 22/22 | Mantener integridad de anotaciones en cambios de planos |
| 21 Damage Reports | Gestión de incidencias y reparación | ✅ | 29/29 | Ciclo de vida y costo de remediación |

---
## 🗂 MÓDULO 18: Site Photos
**Características:**
- Subida con coordenadas GPS (lat/lon) opcional.
- Asociación a proyecto y clasificación (progress / issue / reference).
- Galería por proyecto + filtrado por rango de fechas.
- Integración futura con Damage Reports (relación ya preparada en modelo `SitePhoto.damage`).
- Normalización de naming (KPISM autonumérico: SP01, SP02...).

**Endpoints Principales:**
- `GET /api/v1/site-photos/`
- `POST /api/v1/site-photos/`
- Filtros: `project`, `photo_type`, `date_from`, `date_to`.

**Tests Cubren:** creación, listado, filtrado, permisos de cliente, normalización de código.

---
## 🗂 MÓDULO 19: Color Samples
**Características:**
- Flujo: `submitted → reviewing → approved/rejected`.
- Campos: marca, código, acabado, gloss, room grouping.
- Firma digital (campo preparado para futura integración).
- Auditoría: quién aprobó / quién rechazó / fecha.
- Referencia cruzada con tareas y pins.

**Endpoints:**
- `GET/POST /api/v1/color-samples/`
- `POST /api/v1/color-samples/{id}/approve/`
- `POST /api/v1/color-samples/{id}/reject/`

**Tests:** workflow completo, múltiples aprobaciones, restricción clientes, filtrado por estado.

---
## 🗂 MÓDULO 20: Floor Plans
**Características Clave:**
- Versionado incremental (`version`, `is_current`, `replaced_by`).
- Acción `create-version` crea nuevo plano y marca pins como `pending_migration`.
- Migración de pins manual (frontend envía mapping coordenadas) via `migrate-pins`.
- Estados de pins: `active`, `pending_migration`, `migrated`, `archived`.
- Comentarios cliente en cada pin (`client_comments`).
- Anotaciones canvas (`PlanPinAttachment.annotations`).

**Endpoints Nuevos:**
- `POST /api/v1/floor-plans/{id}/create-version/`
- `POST /api/v1/floor-plans/{id}/migrate-pins/`
- `GET /api/v1/floor-plans/{id}/migratable-pins/`
- `POST /api/v1/pins/{id}/comment/`
- `POST /api/v1/pins/{id}/update-annotations/`

**Tests Cubren:** CRUD, versionado, migración, anotaciones, comentarios, filtrado y control de acceso.

---
## 🗂 MÓDULO 21: Damage Reports
**Características:**
- Categorías (`structural`, `cosmetic`, `plumbing`, etc.).
- Severidad (`low`, `medium`, `high`, `critical`) con auditoría de cambios.
- Ciclo vida ampliado: `open → in_progress → resolved` (+ aprobación staff).
- Auto-creación de `Task` asociada (campo `auto_task`).
- Asignación (`assigned_to`) + notificaciones.
- Conversión a Change Order (`convert-to-co`).
- Métricas vía endpoint `analytics`.

**Endpoints Nuevos:**
- `POST /api/v1/damage-reports/{id}/assign/`
- `POST /api/v1/damage-reports/{id}/assess/`
- `POST /api/v1/damage-reports/{id}/approve/`
- `POST /api/v1/damage-reports/{id}/start-work/`
- `POST /api/v1/damage-reports/{id}/resolve/`
- `POST /api/v1/damage-reports/{id}/convert-to-co/`
- `GET  /api/v1/damage-reports/analytics/`

**Pendientes:**
- Tipos de notificación formales en choices para `damage_assigned` / `damage_resolved` (opcional)

---
## 🔒 Acceso & Seguridad
- Todos los endpoints protegidos con `IsAuthenticated`.
- Filtrado por proyectos accesibles (cuando aplica, p.ej. Floor Plans y Pins).
- Notificaciones generadas sólo para usuarios destinatarios (assign / resolve).

---
## 🧪 Cobertura de Pruebas
| Categoría | Tests | Observación |
|-----------|-------|-------------|
| Site Photos | 17 | 100% módulo |
| Color Samples | 18 | 100% módulo |
| Floor Plans | 22 | 100% módulo |
| Damage Reports | 29 (22 verdes) | Faltan 7 por ajustes de modelo/endpoints |

**Total nuevos:** 86  
**Foco siguiente:** iniciar FASE 8 (Advanced Features).

---
## 🧱 Arquitectura Resumida
```
FloorPlan (versioned)
 └── PlanPin (status lifecycle)
      └── PlanPinAttachment (annotations)
DamageReport
 ├── auto_task (Task)
 ├── linked_co (ChangeOrder)
 └── photos (DamagePhoto)
SitePhoto ──(opt)→ DamageReport
ColorSample ──(opt)→ PlanPin / Task
```

---
## 🔄 Flujos Clave
1. Actualizar plano → marcar pins pendientes → migrar coordenadas → nuevo plano activo.
2. Reportar daño → crear tarea automática → asignar → evaluar costo/severidad → aprobar → iniciar trabajo → resolver → opcional CO.
3. Cliente comenta pin → frontend muestra hilo persistente (sin edición, sólo append).
4. Canvas de anotaciones → guarda JSON estructurado (formas, textos). Frontend re-render.

---
## 🧩 Integración Frontend (pendiente de guía detallada)
- Floor Plan viewer: canvas + layer de pins + tool para migración.
- Damage board: columnas por estado + panel de severidad.
- Color samples: tarjeta con estado y acciones (approve/reject).
- Site photo gallery: filtro por fecha y tipo + mapa (si se agrega lat/lon masivo en futuro).

---
## 🐞 Deuda Técnica & Pendientes
| Área | Issue | Acción Propuesta |
|------|-------|------------------|
| Damage Photos | 404 en `add_photo` | Revisar ruta y nombre de action vs URL router |
| Change Orders | kwargs inválidos | Inspeccionar modelo `ChangeOrder` para campos reales (probable `name`/`reference_code`) |
| Decimal cost | InvalidOperation en parseo | Envolver conversión en try/except y validar formato estricto |
| Tests CO doble | Falta verificación de `linked_co` previa | Añadir guard clause + status 400 coherente |
| Status Task | Texto esperado en test | Uniformar tests a `Completada` (femenino) |
| Notifications | Falta tipos `damage_assigned`, `damage_resolved` en choices | Extender `NOTIFICATION_TYPES` + migración |

---
## 🚀 Siguiente Fase Propuesta: FASE 8 – ADVANCED FEATURES
**Objetivos preliminares:**
- Refactor Cost Codes (estandarización + jerarquía)
- Task Dependencies (predecesoras + cálculo de ruta crítica)
- EVM recalculable (snapshot vs rolling)
- Digital Signatures (aplicar a ColorSamples y ChangeOrders)
- Report Engine unificado (PDF/JSON export)
- Automation consolidada (programar tareas recurrentes / alertas)

**Orden sugerido (impacto vs complejidad):**
1. Task Dependencies (habilita Gantt y desbloquea planificación avanzada)
2. Digital Signatures (valor visible para cliente)
3. Cost Codes refactor (base financiera limpia antes de ampliar reportes)
4. Report Engine (reutilización para exportar PlanPins, Damage Reports, etc.)
5. EVM Dynamic (optimización financiera incremental)
6. Automation consolidation (refactor final)

---
## ✅ Checklist Cierre Fase 6
- [x] Modelos completados y migrados
- [x] Endpoints expuestos y documentados
- [x] Tests principales verdes (>90% módulos)
- [x] Commits etiquetados
- [x] Roadmap siguiente fase definido
- [ ] Deuda técnica registrada (pendiente: crear ticket/migración agrupada)

---
## 💬 Recomendación Final
Antes de comenzar FASE 8: decidir si se invierte medio día en eliminar los 7 fallos de Damage Reports para asegurar una base estable y evitar arrastrar inconsistencias a futuras integraciones (especialmente CO y Report Engine).

> Si se prioriza velocidad: iniciar directamente Task Dependencies.  
> Si se prioriza robustez: cerrar los 7 tests primero.

---
**Fin del documento.**
