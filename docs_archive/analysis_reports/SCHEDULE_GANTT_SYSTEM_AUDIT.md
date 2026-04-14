# 🔍 AUDITORÍA COMPLETA: Sistema de Schedule / Calendar / Gantt

**Fecha:** Enero 2025  
**Objetivo:** Análisis exhaustivo del sistema de cronogramas en 3 capas (Cliente, PM/Admin en Proyecto, Admin Master Schedule), identificar problemas, proponer arquitectura unificada.  
**Regla:** SOLO análisis y plan — NO se escribe código hasta aprobar el plan.

---

## 📋 TABLA DE CONTENIDOS

1. [Estado Actual — Inventario Completo](#1-estado-actual)
2. [Análisis por Capa (3 Tiers)](#2-análisis-por-capa)
3. [Problemas Críticos Identificados](#3-problemas-críticos)
4. [Mapa de Conexiones y Dependencias](#4-mapa-de-conexiones)
5. [Arquitectura Propuesta](#5-arquitectura-propuesta)
6. [Plan de Trabajo por Fases](#6-plan-de-trabajo)
7. [Matriz de Riesgos](#7-matriz-de-riesgos)
8. [Checklist de Validación](#8-checklist-de-validación)

---

## 1. ESTADO ACTUAL — Inventario Completo {#1-estado-actual}

### 1.1 Modelos de Datos

#### V1 (Legacy) — `core/models/__init__.py`
| Modelo | Línea | Estado | Quién lo usa |
|--------|-------|--------|-------------|
| `ScheduleCategory` | 745 | ⚠️ LEGACY | FK en `Task.schedule_item`, `DailyLog.schedule_item`, `strategic_future_planning.DailyPlanDay` |
| `ScheduleItem` | 798 | ⚠️ LEGACY | `schedule_item_edit_view`, `schedule_item_delete_view` en legacy_views.py |

**Hallazgo:** V1 ya NO se usa en schedule_generator (migrado a V2). Los únicos consumidores reales son:
- `Task.schedule_item` → FK a `ScheduleItem` V1 (línea 1330)
- `DailyLog.schedule_item` → FK a `ScheduleItem` V1 (línea 3787)
- `DailyPlanDay.schedule_item` → FK a `ScheduleItem` V1 (strategic_future_planning.py:207)
- Vistas CRUD antiguas de edit/delete en legacy_views.py (líneas 12331, 12360)

#### V2 (Moderno) — `core/models/__init__.py`
| Modelo | Línea | Relaciones | Campos Clave |
|--------|-------|------------|-------------|
| `SchedulePhaseV2` | 878 | `project` FK → Project | `name`, `color`, `order`, `weight_percent`, `start_date`, `end_date`, `calculated_progress` (property) |
| `ScheduleItemV2` | 937 | `project` FK, `phase` FK → PhaseV2 | `name`, `start_date`, `end_date`, `status`, `progress`, `weight_percent`, `is_milestone`, `assigned_to`, `order`, `calculated_progress` (property) |
| `ScheduleTaskV2` | 1042 | `item` FK → ItemV2 | `title`, `status`, `assigned_to`, `weight_percent`, `due_date`, `completed_at` |
| `TaskChecklistItem` | ~1080 | `task` FK → TaskV2 | `description`, `is_completed`, `order`, `sop_reference` |
| `ScheduleDependencyV2` | 1118 | `source_item`, `target_item` FK → ItemV2 | `dependency_type` (FS/SS/FF/SF) |

**Jerarquía V2:**
```
Project
  └── SchedulePhaseV2 (stages/fases) — weight_percent
        └── ScheduleItemV2 (items/barras) — weight_percent, status, progress
              └── ScheduleTaskV2 (tasks/tareas) — weight_percent, is_completed
                    └── TaskChecklistItem (checklist)
```

**Progreso Ponderado:**
- `PhaseV2.calculated_progress` = promedio ponderado de sus items
- `ItemV2.calculated_progress` = promedio ponderado de sus tasks (o `progress` manual si no hay tasks)
- Cada nivel tiene `weight_percent` para distribuir importancia

---

### 1.2 APIs (`core/api/schedule_api.py`)

| Endpoint | Método | Línea | Respuesta | Usado por |
|----------|--------|-------|-----------|-----------|
| `/api/v1/schedule/master/` | GET | 38 | `{projects[], schedule_items[], events[], metadata}` | `master_schedule.html` (custom JS) |
| `/api/v1/gantt/v2/projects/<id>/` | GET | 345 | `{project, phases[{items[{tasks[]}]}], dependencies[], metadata}` | React Gantt (mode=project) |
| `/api/v1/gantt/v2/phases/` | POST | 460 | Crea `SchedulePhaseV2` | React Gantt CRUD |
| `/api/v1/gantt/v2/phases/<id>/` | PATCH/DELETE | 470 | Edita/borra phase | React Gantt CRUD |
| `/api/v1/gantt/v2/items/` | POST | 490 | Crea `ScheduleItemV2` | React Gantt CRUD |
| `/api/v1/gantt/v2/items/<id>/` | PATCH/DELETE | 500 | Edita/borra item | React Gantt CRUD |
| `/api/v1/gantt/v2/tasks/` | POST | 520 | Crea `ScheduleTaskV2` | React Gantt CRUD |
| `/api/v1/gantt/v2/tasks/<id>/` | PATCH/DELETE | 530 | Edita/borra task | React Gantt CRUD |
| `/api/v1/gantt/v2/dependencies/` | POST | 540 | Crea dependencia | React Gantt CRUD |
| `/api/v1/gantt/v2/dependencies/<id>/` | DELETE | 550 | Borra dependencia | React Gantt CRUD |
| `/projects/<id>/calendar/client/api/` | GET | views_client_calendar.py:101 | `[{title, start, end, ...}]` (FullCalendar format) | `client_project_calendar.html` |
| `/pm-calendar/api/data/` | GET | views_pm_calendar.py | PM calendar events | `pm_calendar.html` |

**🚨 Problema de formato:** El API master (`/schedule/master/`) devuelve `{projects, schedule_items, events}` — formato COMPLETAMENTE diferente al del Gantt V2 (`{project, phases[items[]], dependencies}`). El React Gantt espera el formato V2.

---

### 1.3 Vistas (Views)

| Vista | Archivo | URL | Template | Permisos |
|-------|---------|-----|----------|----------|
| `master_schedule_center` | legacy_views.py:1259 | `/master-schedule/` | `master_schedule.html` | staff only |
| `schedule_gantt_react_view` | legacy_views.py:12421 | `/projects/<id>/schedule/gantt/` | `schedule_gantt_react.html` | staff + PM |
| `schedule_generator_view` | legacy_views.py:12093 | `/projects/<id>/schedule/generator/` | `schedule_generator.html` | staff + PM |
| `project_schedule_view` | legacy_views.py:9599 | `/projects/<id>/schedule/` | `project_schedule.html` | staff + PM |
| `client_project_calendar_view` | views_client_calendar.py:18 | `/projects/<id>/calendar/client/` | `client_project_calendar.html` | client auth |
| `pm_calendar_view` | views_pm_calendar.py:32 | `/pm-calendar/` | `pm_calendar.html` | staff |

---

### 1.4 Templates y su Tecnología

| Template | Líneas | Tecnología | Qué hace |
|----------|--------|------------|---------|
| `master_schedule.html` | 1006 | **Custom JS Gantt** + FullCalendar 6.1.10 CDN | Barras por proyecto (no por item), toggle calendar, fetch `/api/v1/schedule/master/`. Monday.com inspired. |
| `schedule_gantt_react.html` | 96 | **React Gantt** (IIFE bundle) | Monta `window.KibrayGantt.mount()` con mode='project'. ✅ FUNCIONA CORRECTAMENTE |
| `client_project_calendar.html` | 884 | **FullCalendar CDN** + Timeline list custom | Calendario mes/semana + lista Timeline. Dark theme. SIN Gantt. |
| `pm_calendar.html` | 470 | **FullCalendar CDN** | Calendario con blocked days, deadlines, milestones. SIN Gantt. |
| `schedule_generator.html` | ~400 | **CSS bars** custom | Generador con barras CSS, V2 models |
| `project_schedule.html` | ~150 | **HTML table** | Tabla simple, V1 model |

---

### 1.5 React Gantt (`frontend/gantt/`)

| Archivo | Qué hace |
|---------|---------|
| `types/gantt.ts` | Define `GanttMode = 'project' \| 'master' \| 'pm' \| 'strategic'`, todas las interfaces |
| `api/ganttApi.ts` | API client — `fetchGanttData()` switch por mode, CRUD completo para items/phases/tasks/deps |
| `api/adapters.ts` | `transformV2Response()` — transforma `{phases[items[]]}` → `{categories[], items[]}` |
| `hooks/useGanttData.ts` | Hook React — fetch + CRUD + optimistic updates |
| `main-django.tsx` | Entry point IIFE — `window.KibrayGantt.mount(elementId, config)` |
| `components/KibrayGanttInteractive.tsx` | Componente principal — drag&drop, resize, sidebar, dependency lines |
| `components/GanttBar.tsx` / `GanttBarInteractive.tsx` | Barras interactivas con resize handles |
| `components/GanttStageBar.tsx` | Barras de fase/stage (span automático) |
| `components/CalendarView.tsx` | Vista de calendario alternativa dentro del React Gantt |
| `components/SlideOverPanel.tsx` | Panel lateral para editar items |
| `components/CreateItemModal.tsx` | Modal para crear items |

**Modos del React Gantt y su estado:**
| Mode | URL que fetch | ¿Template lo usa? | ¿API compatible? |
|------|--------------|-------------------|-----------------|
| `project` | `/gantt/v2/projects/<id>/` | ✅ `schedule_gantt_react.html` | ✅ Perfecto |
| `master` | `/schedule/master/` | ❌ NADIE lo usa | ❌ **Formato incompatible** — API devuelve `{projects, schedule_items, events}`, Gantt espera `{categories, items, dependencies}` |
| `pm` | `/pm-calendar/api/data/` | ❌ NADIE lo usa | ❌ **Formato incompatible** — devuelve FullCalendar events |
| `strategic` | `/strategic-planner/summary/` | ❌ NADIE lo usa | ❓ No verificado |

---

## 2. ANÁLISIS POR CAPA (3 Tiers) {#2-análisis-por-capa}

### 🟢 TIER 1: Gantt de Proyecto (PM/Admin dentro de un proyecto)
**Estado: ✅ FUNCIONA CORRECTAMENTE**

- **URL:** `/projects/<id>/schedule/gantt/`
- **Template:** `schedule_gantt_react.html`
- **Tecnología:** React Gantt (`KibrayGanttApp`) en mode='project'
- **API:** `/api/v1/gantt/v2/projects/<id>/` → formato `{project, phases[items[tasks[]]], dependencies}`
- **Adapter:** `transformV2Response()` transforma a formato interno
- **CRUD:** ✅ Create/Edit/Delete phases, items, tasks, dependencies
- **Drag & Drop:** ✅ Mover y resize barras
- **Dependencias:** ✅ FS/SS/FF/SF con líneas SVG
- **Progreso Ponderado:** ✅ weight_percent en cada nivel
- **Vista Calendar:** ✅ Toggle Gantt ↔ Calendar integrado

**Veredicto:** Este tier es el modelo a seguir. El único componente que funciona al 100%.

---

### 🔴 TIER 2: Calendar del Cliente (vista del proyecto para el cliente)
**Estado: ❌ NO TIENE GANTT — solo FullCalendar**

- **URL:** `/projects/<id>/calendar/client/`
- **Template:** `client_project_calendar.html` (884 líneas)
- **Tecnología:** FullCalendar 6.1.10 (CDN) + HTML Timeline list custom
- **API:** `/projects/<id>/calendar/client/api/` → formato FullCalendar `[{title, start, end, color}]`
- **Datos:** Lee de `ScheduleItemV2` (correcto), pero los formatea como dots en calendario
- **Vistas disponibles:** Month, Week, Timeline list
- **NO tiene:** Barras Gantt, dependencias, drag&drop, progress bars

**Lo que el cliente ve actualmente:**
1. Un calendario con puntos de colores por milestone/item
2. Una lista timeline con items agrupados (sin barras)
3. Puede clicar para ver detalle (modal AJAX)
4. Theme dark personalizado

**Lo que debería ver (según el usuario):**
- Barras Gantt del proyecto (read-only)
- Phases con sus items y progreso
- Milestones marcados
- Sin capacidad de editar

---

### 🔴 TIER 3: Master Schedule (Admin — todos los proyectos)
**Estado: ❌ GANTT CUSTOM DESCONECTADO — sin bidireccionalidad**

- **URL:** `/master-schedule/`
- **Template:** `master_schedule.html` (1006 líneas)
- **Tecnología:** JavaScript custom Gantt + FullCalendar 6.1.10 (CDN)
- **API:** `/api/v1/schedule/master/` → formato `{projects[], schedule_items[], events[], metadata}`
- **Vista Gantt:** Renderiza barras por **PROYECTO** (no por item), muestra progress bar dentro de cada barra
- **Vista Calendar:** FullCalendar con invoices, COs, tasks, milestones, meetings
- **NO tiene:** CRUD de items, drag&drop, resize, dependencias, drill-down a items dentro de cada proyecto

**Lo que el admin ve actualmente:**
1. Una barra horizontal por cada proyecto activo (no archivado)
2. Progress % dentro de cada barra (calculado desde V2 o fallback tasks)
3. Click en barra → navega a `/projects/<id>/overview/`
4. Toggle a Calendar → FullCalendar con eventos tácticos (invoices, COs, etc.)
5. Filtros: tipo de evento, texto, rango de fechas (solo calendar)
6. Tooltip con PM, client, progress%

**Lo que debería hacer (según el usuario):**
- Mostrar barras por proyecto Y poder expandir para ver items/phases dentro
- **Bidireccionalidad:** Crear/editar items en master → se reflejan en proyecto individual
- **Bidireccionalidad:** Editar items en proyecto → se reflejan en master view
- Personal items del admin (que no pertenecen a ningún proyecto)

---

## 3. PROBLEMAS CRÍTICOS IDENTIFICADOS {#3-problemas-críticos}

### 🔴 P1: TRES IMPLEMENTACIONES GANTT DIFERENTES
| Implementación | Usado en | Tecnología | Mantenibilidad |
|---------------|---------|-----------|---------------|
| React Gantt | Project Gantt | React/TS, IIFE bundle | ✅ Buena |
| Custom JS Gantt | Master Schedule | Vanilla JS en template | ❌ Mala — 1006 líneas en HTML |
| CSS Bars | Schedule Generator | CSS puro en template | ❌ Mala — duplicación |

**Impacto:** Triplicación de lógica de renderizado, bugs se arreglan en un lugar pero no en otros, inconsistencia visual.

### 🔴 P2: API MASTER SCHEDULE INCOMPATIBLE CON REACT GANTT
El React Gantt en `ganttApi.ts` llama a `/schedule/master/` cuando mode='master', pero:
- **API devuelve:** `{projects: [{id, name, start_date, end_date, progress_pct, color}], schedule_items: [...], events: [...]}`
- **React Gantt espera:** `{categories: [...], items: [...], dependencies: [...], permissions: {...}}`
- **El adapter** `transformV2Response()` espera `{phases: [{items: [...]}]}` — completamente diferente

**Resultado:** Si alguien monta el React Gantt en mode='master', crashearía porque el adapter no puede transformar el formato.

### 🔴 P3: CALENDARIO CLIENTE SIN GANTT
- El cliente ve dots en un calendario — no barras de progreso
- El componente React Gantt ya existe y soporta `canEdit=false` (read-only)
- Solo falta montar el React Gantt en el template del cliente
- Pero hay que decidir: ¿el cliente ve phases+items, o solo items, o solo milestones?

### 🟡 P4: NO HAY BIDIRECCIONALIDAD EN MASTER SCHEDULE
- La "bidireccionalidad" realmente es un non-issue a nivel de datos, porque:
  - Master schedule lee de los MISMOS modelos V2 que el proyecto individual
  - Si alguien edita un `ScheduleItemV2` en el project Gantt, el master schedule lo ve automáticamente al refrescar
- **El problema real es:** El master schedule NO tiene capacidad de CREAR/EDITAR items (es solo lectura con barras por proyecto)
- **Solución natural:** Si montamos el React Gantt en mode='master' con CRUD, la "bidireccionalidad" es automática porque ambos usan los mismos modelos V2

### 🟡 P5: V1 MODELS SIGUEN EXISTIENDO
- `ScheduleCategory` y `ScheduleItem` (V1) todavía existen
- Tienen FKs desde `Task`, `DailyLog`, `DailyPlanDay`
- No se pueden borrar sin migrar esos FKs a V2
- Pero ya no se crean nuevos V1 items (schedule_generator ya usa V2)

### 🟡 P6: DUPLICACIÓN DE VISTAS DE SCHEDULE POR PROYECTO
Hay 3 vistas diferentes para schedule dentro de un proyecto:
1. `/projects/<id>/schedule/` → `project_schedule.html` (tabla HTML, V1)
2. `/projects/<id>/schedule/generator/` → `schedule_generator.html` (CSS bars, V2)
3. `/projects/<id>/schedule/gantt/` → `schedule_gantt_react.html` (React Gantt, V2) ✅

Solo la 3ra es la correcta. Las otras dos confunden al usuario.

### 🟢 P7: PM CALENDAR ES FUNCIONAL PERO LIMITADO
- `pm_calendar.html` usa FullCalendar para mostrar eventos del PM
- Funciona, pero no tiene vista Gantt
- El React Gantt tiene mode='pm' definido pero sin uso
- Mejora futura, no urgente

---

## 4. MAPA DE CONEXIONES Y DEPENDENCIAS {#4-mapa-de-conexiones}

```
┌──────────────────────────────────────────────────────────────────────┐
│                        CAPA DE DATOS (V2)                            │
│                                                                      │
│  Project ──→ SchedulePhaseV2 ──→ ScheduleItemV2 ──→ ScheduleTaskV2  │
│                  (stages)           (items/bars)       (tasks)        │
│                                       │                              │
│                                       └──→ ScheduleDependencyV2      │
│                                                                      │
│  FUENTE ÚNICA DE VERDAD — Todos los tiers leen de aquí              │
└──────────────────────────────────────────────────────────────────────┘
            │                    │                      │
            ▼                    ▼                      ▼
┌─────────────────┐  ┌──────────────────┐  ┌──────────────────────┐
│ TIER 3: MASTER  │  │ TIER 1: PROJECT  │  │ TIER 2: CLIENT       │
│ /master-schedule│  │ /schedule/gantt/ │  │ /calendar/client/    │
│                 │  │                  │  │                      │
│ VE: Todos los   │  │ VE: Un proyecto  │  │ VE: Un proyecto      │
│ proyectos       │  │ en detalle       │  │ (read-only)          │
│                 │  │                  │  │                      │
│ HOY: Custom JS  │  │ HOY: React Gantt │  │ HOY: FullCalendar    │
│ → proyecto bars │  │ → phases/items ✅│  │ → dots, no Gantt ❌  │
│                 │  │                  │  │                      │
│ IDEAL: React    │  │ IDEAL: (ya está) │  │ IDEAL: React Gantt   │
│ Gantt master    │  │                  │  │ read-only             │
│ → expandible    │  │                  │  │                      │
└─────────────────┘  └──────────────────┘  └──────────────────────┘
```

### Flujo de Datos Actual vs Ideal

**Actual:**
```
Master API (/schedule/master/) ──→ Custom JS Gantt (formato propio)
Project API (/gantt/v2/projects/<id>/) ──→ React Gantt (formato V2)
Client API (/calendar/client/api/) ──→ FullCalendar (formato FC events)
```

**Ideal (propuesto):**
```
Master API v2 (nuevo) ──→ React Gantt mode='master' (formato V2 adaptado)
Project API (/gantt/v2/projects/<id>/) ──→ React Gantt mode='project' (ya funciona)
Project API (/gantt/v2/projects/<id>/) ──→ React Gantt mode='project' canEdit=false (CLIENTE)
```

**La clave:** El calendario del cliente NO necesita un API diferente. Puede usar el MISMO API del proyecto Gantt V2, solo que el frontend se monta en read-only (`canEdit=false`).

---

## 5. ARQUITECTURA PROPUESTA {#5-arquitectura-propuesta}

### 5.1 Principio Central: UN SOLO GANTT, TRES MODOS

El React Gantt (`KibrayGanttApp`) ya soporta `mode: GanttMode` y `canEdit: boolean`. La propuesta es:

| Tier | Mode | canEdit | API Endpoint | Qué muestra |
|------|------|---------|-------------|-------------|
| Project (PM/Admin) | `'project'` | `true` | `/gantt/v2/projects/<id>/` (existente) | Phases → Items → Tasks, CRUD completo |
| Client | `'project'` | `false` | `/gantt/v2/projects/<id>/` (existente, con filtro) | Phases → Items (solo milestones + items visibles), read-only |
| Master | `'master'` | `true` | `/gantt/v2/master/` (**NUEVO**) | Proyectos como stages → Items agrupados, CRUD multi-proyecto |

### 5.2 Cambios en Backend

#### A) Nuevo API: `/api/v1/gantt/v2/master/` 
**Objetivo:** Devolver datos de TODOS los proyectos en formato V2 que el React Gantt entiende.

**Formato de respuesta (adaptado a lo que `transformV2Response` espera):**
```json
{
  "projects": [...],
  "phases": [
    {
      "id": "project_1",          // Cada PROYECTO es una "phase" en master
      "name": "Riverside Renovation",
      "color": "#3b82f6",
      "order": 0,
      "project": 1,
      "weight_percent": 0,
      "calculated_progress": 45,
      "start_date": "2025-01-01",
      "end_date": "2025-06-30",
      "items": [                   // Los ScheduleItemV2 del proyecto
        {
          "id": 123,
          "name": "Foundation",
          "start_date": "2025-01-01",
          "end_date": "2025-02-15",
          "status": "done",
          "progress": 100,
          "phase": "project_1",
          "project": 1,
          ...
        }
      ]
    }
  ],
  "dependencies": [...],
  "metadata": {...},
  "permissions": {
    "can_view": true,
    "can_create": true,   // Admin puede crear items en cualquier proyecto
    "can_edit": true,
    "can_delete": true
  }
}
```

**Lógica:** Mapear Project → Phase (category), ScheduleItemV2 → Item. Las phases reales dentro de cada proyecto se aplanan o se convierten en sub-items agrupados.

**Alternativa más simple:** Mantener la jerarquía Project → Phase → Item, usando un "super-phase" por proyecto que agrupa las phases reales. Esto requiere un adapter en el frontend.

#### B) Filtro de visibilidad para clientes
Agregar un campo `is_client_visible` a `ScheduleItemV2` (default `True`), o usar un query param `?client_view=true` en el API existente que filtre items sensibles.

#### C) Deprecar API master viejo
Una vez que el nuevo API master V2 funcione, la vista `/api/v1/schedule/master/` se puede deprecar. No borrar inmediatamente, pero marcar como deprecated.

### 5.3 Cambios en Frontend (React Gantt)

#### A) Adapter para Master Mode
En `adapters.ts`, crear `transformMasterResponse()` que convierta la respuesta del nuevo API master a formato interno:
- Cada proyecto → `GanttCategory`
- Items de cada proyecto → `GanttItem[]`
- Dependencies cross-project → `GanttDependency[]`

#### B) Modo Read-Only mejorado
Cuando `canEdit=false`:
- Ocultar botones de create/edit/delete
- Deshabilitar drag & drop
- Deshabilitar resize
- Ocultar link para crear dependencies
- Sidebar: solo "View" mode, nunca "Edit"
- Esto ya debería funcionar parcialmente por el prop `canEdit`, verificar completitud

#### C) Comportamiento por Mode en `main-django.tsx`
Actualizar `loadData()` para usar el adapter correcto según el mode:
```
mode === 'project' → transformV2Response (ya existe)
mode === 'master'  → transformMasterResponse (nuevo)
```

### 5.4 Cambios en Templates

#### A) `client_project_calendar.html` → Reemplazar con React Gantt
**Opción 1 (Recomendada):** Crear nuevo template `client_project_gantt.html` que monte el React Gantt:
```html
<div id="gantt-app-root" style="height: 80vh;"></div>
<script>
  window.KibrayGantt.mount('gantt-app-root', {
    mode: 'project',
    projectId: {{ project.id }},
    canEdit: false,
    csrfToken: '{{ csrf_token }}',
    projectName: '{{ project.name }}',
  });
</script>
```

**Opción 2:** Mantener `client_project_calendar.html` como opción de "Calendar View" y agregar un toggle que muestre el React Gantt (similar a como master_schedule.html hace toggle Gantt/Calendar).

**Decisión pendiente del usuario:** ¿El cliente ve el mismo Gantt del PM (read-only) o una vista simplificada?

#### B) `master_schedule.html` → Reemplazar con React Gantt
Crear nuevo template `master_schedule_v2.html` que monte React Gantt en mode='master':
```html
<div id="gantt-app-root" style="height: calc(100vh - 64px);"></div>
<script>
  window.KibrayGantt.mount('gantt-app-root', {
    mode: 'master',
    canEdit: true,
    csrfToken: '{{ csrf_token }}',
  });
</script>
```

#### C) Eliminar templates obsoletos
- `project_schedule.html` (tabla V1) → Redirect a `/schedule/gantt/`
- `schedule_generator.html` → Evaluar si aún necesario (genera desde estimado, podría integrarse en React Gantt)

### 5.5 Sobre la "Bidireccionalidad"

**Hallazgo clave:** La bidireccionalidad ya es inherente al sistema porque todos los tiers leen/escriben en los MISMOS modelos V2.

- Admin edita item en Master Schedule → Escribe en `ScheduleItemV2` → PM ve cambio al abrir Project Gantt
- PM edita item en Project Gantt → Escribe en `ScheduleItemV2` → Admin ve cambio al abrir Master Schedule
- NO se necesita sincronización, webhooks, ni eventos — es la misma tabla SQL

**Lo único que falta es:** Que el Master Schedule use los mismos modelos V2 a través de React Gantt (en lugar del JS custom que solo lee pero no escribe).

---

## 6. PLAN DE TRABAJO POR FASES {#6-plan-de-trabajo}

### FASE 0: Preparación (sin cambios visibles)
**Duración estimada:** 1 sesión  
**Riesgo:** Bajo

- [ ] **0.1** Verificar que el React Gantt build (`gantt-app.iife.js`) está actualizado
- [ ] **0.2** Verificar que `canEdit=false` en React Gantt realmente deshabilita TODA interacción
- [ ] **0.3** Documentar el formato exacto de respuesta de `/gantt/v2/projects/<id>/`
- [ ] **0.4** Escribir tests para los APIs existentes (si no hay)
- [ ] **0.5** Backup del master_schedule.html y client_project_calendar.html actuales

---

### FASE 1: Cliente ve Gantt (Tier 2 — impacto más visible, menor riesgo)
**Duración estimada:** 1-2 sesiones  
**Riesgo:** Bajo (no rompe nada existente, solo agrega funcionalidad)

- [ ] **1.1** Crear vista `client_project_gantt_view` que monte React Gantt con `canEdit=false`
- [ ] **1.2** Crear template `client_project_gantt.html` mínimo (similar a `schedule_gantt_react.html`)
- [ ] **1.3** Decidir si el cliente ve TODOS los items o solo `is_milestone=True` + items con status relevante
- [ ] **1.4** Agregar URL `/projects/<id>/schedule/client/` que renderice el nuevo template
- [ ] **1.5** En el portal del cliente, cambiar el link "Calendar" para incluir toggle Gantt/Calendar
- [ ] **1.6** Opcionalmente agregar campo `is_client_visible` a `ScheduleItemV2` (migration + admin + default True)
- [ ] **1.7** Filtrar en el API o en el frontend los items no visibles para el cliente
- [ ] **1.8** Probar con un proyecto real: el cliente debe ver barras read-only
- [ ] **1.9** Verificar que el client NO puede acceder al API de escritura (permisos)

**Entregable:** El cliente ve un Gantt read-only con las barras del proyecto.

---

### FASE 2: Master Schedule V2 (Tier 3 — más complejo)
**Duración estimada:** 2-3 sesiones  
**Riesgo:** Medio

#### Sub-fase 2A: Nuevo API Master V2
- [ ] **2A.1** Crear endpoint `/api/v1/gantt/v2/master/` que devuelva formato V2
- [ ] **2A.2** Decidir la jerarquía: ¿Proyecto=Category, Phase=Sub-item? ¿O Proyecto=Category con items directos?
- [ ] **2A.3** Manejar que un item en master pertenece a un proyecto específico (para CRUD)
- [ ] **2A.4** Incluir dependencies cross-project (si las hay) o intra-project
- [ ] **2A.5** Agregar parámetros de filtrado: `?status=active&pm=<id>&date_start=&date_end=`
- [ ] **2A.6** Incluir `permissions` en la respuesta (admin=full CRUD, PM=solo sus proyectos)
- [ ] **2A.7** Tests del nuevo endpoint

#### Sub-fase 2B: Adapter Frontend para Master
- [ ] **2B.1** Crear `transformMasterResponse()` en `adapters.ts`
- [ ] **2B.2** Actualizar `main-django.tsx` → `loadData()` para usar el adapter correcto por mode
- [ ] **2B.3** Manejar que CRUD en master necesita saber `project_id` de cada item
- [ ] **2B.4** Opcional: expandir/colapsar proyectos (ya tienen `is_collapsed` en Category)
- [ ] **2B.5** Rebuild del IIFE bundle

#### Sub-fase 2C: Template Master V2
- [ ] **2C.1** Crear template `master_schedule_v2.html` que monte React Gantt en mode='master'
- [ ] **2C.2** Mantener el toggle Gantt/Calendar (el Calendar view del React Gantt ya existe)
- [ ] **2C.3** Para eventos tácticos (invoices, COs) del calendar, decidir: ¿moverlos al CalendarView del React Gantt, o mantener FullCalendar separado?
- [ ] **2C.4** Actualizar vista `master_schedule_center` para renderizar el nuevo template
- [ ] **2C.5** Guardar el template viejo como `master_schedule_legacy.html` (no borrar)
- [ ] **2C.6** Probar con datos reales: múltiples proyectos, expandir, crear item, verificar que aparece en project Gantt individual

**Entregable:** Master Schedule usa React Gantt, muestra todos los proyectos con drill-down a items, CRUD funcional, cambios se reflejan automáticamente en project Gantt.

---

### FASE 3: Limpieza y consolidación
**Duración estimada:** 1-2 sesiones  
**Riesgo:** Bajo-Medio

- [ ] **3.1** Redirect `/projects/<id>/schedule/` → `/projects/<id>/schedule/gantt/` (deprecar tabla V1)
- [ ] **3.2** Evaluar si `schedule_generator.html` debe integrarse en el React Gantt como "Generate from Estimate" button
- [ ] **3.3** Deprecar el API viejo `/api/v1/schedule/master/` (mantener pero marcar deprecated)
- [ ] **3.4** Evaluar migración de FKs V1: `Task.schedule_item` → apuntar a V2 o crear campo paralelo
- [ ] **3.5** Consolidar CSS/JS: remover FullCalendar CDN de templates que ya no lo necesitan
- [ ] **3.6** Actualizar navegación/menú para que los links apunten a las vistas correctas
- [ ] **3.7** Actualizar documentación

---

### FASE 4: Mejoras futuras (nice-to-have)
**Duración estimada:** Variable  
**Riesgo:** Bajo

- [ ] **4.1** PM Calendar con React Gantt mode='pm' (personal items + assigned tasks)
- [ ] **4.2** Real-time updates via WebSocket (cuando un PM edita, el master se actualiza en vivo)
- [ ] **4.3** Export to PDF del Gantt (para reportes a clientes)
- [ ] **4.4** Critical path analysis en React Gantt
- [ ] **4.5** Baseline comparison (planned vs actual)
- [ ] **4.6** Resource leveling / workload balance
- [ ] **4.7** Notificaciones cuando un item cambia de status o se atrasa

---

## 7. MATRIZ DE RIESGOS {#7-matriz-de-riesgos}

| # | Riesgo | Probabilidad | Impacto | Mitigación |
|---|--------|-------------|---------|-----------|
| R1 | React Gantt build rompe al agregar adapter | Baja | Alto | Build + test antes de deploy. Mantener IIFE anterior como backup. |
| R2 | Performance en Master con muchos proyectos (~50+ proyectos × ~20 items = 1000+ barras) | Media | Medio | Virtualización de filas, lazy load por proyecto expandido, paginación en API |
| R3 | Cliente accede a API de escritura | Baja | Alto | Permisos en backend: `@permission_classes` verificar rol, no solo `IsAuthenticated` |
| R4 | CRUD en master crea items en proyecto equivocado | Media | Alto | `project_id` OBLIGATORIO en cada create/update desde master. Validar en backend. |
| R5 | Migración V1→V2 rompe Tasks/DailyLogs existentes | Media | Alto | NO borrar V1 models en Fase 1-2. Solo deprecar. Migrar FKs en Fase 3 con script. |
| R6 | Template viejo de master_schedule se rompe al cambiar | Baja | Bajo | Guardar como `_legacy.html`. Switch gradual. |
| R7 | CalendarView del React Gantt no muestra invoices/COs | Alta | Medio | Decidir en Fase 2C.3: ¿enriquecer CalendarView o mantener FullCalendar para eventos tácticos? |
| R8 | El adapter master no maneja correctamente items sin phase | Media | Medio | En el API master, asignar items sin phase a un "Uncategorized" pseudo-phase |

---

## 8. CHECKLIST DE VALIDACIÓN {#8-checklist-de-validación}

### Antes de empezar cada fase, verificar:
- [ ] ¿Los tests existentes pasan? (`python manage.py test`)
- [ ] ¿El React Gantt build compila sin errores? (`cd frontend/gantt && npm run build`)
- [ ] ¿Hay backup del estado actual? (git commit)

### Después de cada fase, verificar:
- [ ] **Tier 1 (Project Gantt):** ¿Sigue funcionando exactamente igual? No debe romperse NADA.
- [ ] **Tier 2 (Client):** ¿El cliente ve barras read-only? ¿No puede editar?
- [ ] **Tier 3 (Master):** ¿Muestra todos los proyectos? ¿CRUD funciona? ¿Cambios se reflejan en proyecto?
- [ ] **Permisos:** ¿Cada rol ve solo lo que le corresponde?
- [ ] **Mobile:** ¿El React Gantt es responsive? (ya tiene sidebar responsive)
- [ ] **Performance:** ¿El master schedule carga en <3 segundos con datos reales?

---

## RESUMEN EJECUTIVO

### Lo que funciona ✅
- **React Gantt de proyecto** — CRUD completo, drag&drop, dependencias, progreso ponderado
- **Modelos V2** — jerarquía completa Phase→Item→Task→Checklist
- **APIs V2** — CRUD completo para todos los modelos

### Lo que falta ❌
1. **Cliente NO ve Gantt** → montar React Gantt read-only (Fase 1, ~1 sesión)
2. **Master Schedule desconectado** → nuevo API + React Gantt mode=master (Fase 2, ~2-3 sesiones)
3. **3 implementaciones Gantt duplicadas** → unificar todo en React Gantt (Fases 1-3)

### La "bidireccionalidad" es gratis 🎁
No requiere sync ni webhooks. Todos los tiers leen/escriben en los mismos modelos V2. Solo falta que el Master Schedule use React Gantt con CRUD en lugar de JS custom read-only.

### Orden recomendado
```
Fase 0 (prep) → Fase 1 (client gantt) → Fase 2 (master v2) → Fase 3 (limpieza)
```

**Total estimado: 4-6 sesiones de trabajo**

---

> ⚠️ **ESTE DOCUMENTO ES SOLO ANÁLISIS Y PLAN.** No se debe escribir código hasta que el usuario revise y apruebe este plan. Cualquier duda o cambio de dirección debe discutirse antes de implementar.
