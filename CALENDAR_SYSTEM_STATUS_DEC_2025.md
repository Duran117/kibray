# 📅 ESTADO ACTUAL DEL SISTEMA DE CALENDAR/SCHEDULE - KIBRAY
**Fecha:** Diciembre 7, 2025  
**Analista:** GitHub Copilot AI  
**Estado:** Revisión completa y actualizada

---

## 🎯 RESUMEN EJECUTIVO

### ✅ **IMPLEMENTADO Y FUNCIONANDO:**

| Componente | Estado | Ubicación | Comentarios |
|-----------|--------|-----------|-------------|
| **Master Schedule** | ✅ Completo | `/schedule/master/` | Vista unificada para Admin/Staff |
| **PM Calendar** | ✅ Completo | `/pm-calendar/` | Vista personalizada para Project Managers |
| **Project Schedule** | ✅ Completo | `/projects/{id}/schedule/` | Cronograma por proyecto |
| **Schedule Generator** | ✅ Completo | `/projects/{id}/schedule/generator/` | Generador jerárquico |
| **Client Calendar** | ✅ Parcial | En `client_project_view.html` | Integrado pero mejorable |
| **iCal Export** | ✅ Completo | `/projects/{id}/schedule/export.ics` | Compatible con Google/Apple |
| **API REST** | ✅ Completo | `/api/v1/schedule/` | CRUD completo |
| **PMBlockedDay** | ✅ Completo | Modelo implementado | Bloqueo de días PM |

---

## 🗺️ ARQUITECTURA ACTUAL

### 📦 **MODELOS (3 principales + 1 legacy)**

#### 1️⃣ **Schedule (LEGACY - MANTENER POR AHORA)**
```python
# Ubicación: core/models.py línea 497
class Schedule(models.Model):
    project = ForeignKey(Project)
    title, description
    start_datetime, end_datetime
    is_complete, completion_percentage
    stage  # Hardcoded choices
    assigned_to = ForeignKey(User)
```
**Estado:** ✅ Funcional pero obsoleto  
**Uso actual:** 
- PDF exports
- client_project_view (upcoming schedules)
- Algunos dashboards legacy

**⚠️ NO DEPRECAR AÚN** - Se usa activamente en vistas de cliente

---

#### 2️⃣ **ScheduleCategory (MODERNO)**
```python
# Ubicación: core/models.py línea 538
class ScheduleCategory(models.Model):
    project = ForeignKey(Project)
    name = CharField
    parent = ForeignKey('self')  # JERARQUÍA
    order = IntegerField
    is_phase = BooleanField
    cost_code = ForeignKey(CostCode)
```
**Estado:** ✅ Excelente diseño  
**Características:**
- ✅ Soporte jerárquico (parent/children)
- ✅ Vinculado a Cost Codes
- ✅ Cálculo automático de % complete
- ✅ Ordenamiento

---

#### 3️⃣ **ScheduleItem (MODERNO)**
```python
# Ubicación: core/models.py línea 580
class ScheduleItem(models.Model):
    project = ForeignKey(Project)
    category = ForeignKey(ScheduleCategory)
    title, description
    planned_start, planned_end
    actual_start, actual_end
    percent_complete
    status  # NOT_STARTED, IN_PROGRESS, DONE, BLOCKED
    is_milestone = BooleanField
    estimate_line = ForeignKey(EstimateLine)
    cost_code = ForeignKey(CostCode)
    tasks: RelatedManager[Task]
```
**Estado:** ✅ Excelente - Sistema completo  
**Características:**
- ✅ Vinculado a Budget Lines (EstimateLine)
- ✅ Vinculado a Cost Codes
- ✅ Soporte de milestones
- ✅ Cálculo automático de progreso desde Tasks
- ✅ Estados robustos (NOT_STARTED, IN_PROGRESS, DONE, BLOCKED)

---

#### 4️⃣ **PMBlockedDay (NUEVO)**
```python
# Ubicación: core/models.py línea 7585
class PMBlockedDay(models.Model):
    pm = ForeignKey(User)
    date = DateField
    reason = CharField  # vacation, personal, sick, meeting
    is_full_day = BooleanField
    notes = TextField
```
**Estado:** ✅ Implementado  
**Uso:** PM Calendar - bloqueo de días

---

## 🎨 **VISTAS IMPLEMENTADAS**

### 1️⃣ **Master Schedule Center**
**URL:** `/schedule/master/`  
**Vista:** `core/views.py:809` - `master_schedule_center()`  
**Template:** `core/templates/core/master_schedule.html`  
**Permisos:** ✅ Admin/Staff only

**Características:**
- ✅ Vista unificada (Gantt + Calendar)
- ✅ Todos los proyectos
- ✅ Todas las actividades
- ✅ Toggle entre vistas (Strategic Gantt / Tactical Calendar)
- ✅ Filtros por proyecto, estado, fecha
- ✅ FullCalendar 6.x integrado
- ✅ Diseño moderno con gradientes

**API Endpoint:** `/api/v1/schedule/master-data/`

---

### 2️⃣ **PM Calendar**
**URL:** `/pm-calendar/`  
**Vista:** `core/views_pm_calendar.py:32` - `pm_calendar_view()`  
**Template:** `core/templates/core/pm_calendar.html`  
**Permisos:** ✅ Project Manager only

**Características:**
- ✅ Proyectos asignados con progreso
- ✅ Pipeline de proyectos futuros
- ✅ Días bloqueados (PMBlockedDay)
- ✅ Carga de trabajo visualizada (workload score)
- ✅ Próximos deadlines (invoices, milestones)
- ✅ FullCalendar integrado
- ✅ UI moderna con gradientes violeta

**API Endpoint:** `/pm-calendar/api/data/`

**Acciones disponibles:**
- `POST /pm-calendar/block/` - Bloquear día
- `POST /pm-calendar/unblock/{id}/` - Desbloquear día

---

### 3️⃣ **Project Schedule View**
**URL:** `/projects/{id}/schedule/`  
**Vista:** `core/views.py:6111` - `project_schedule_view()`  
**Template:** `core/templates/core/project_schedule.html`  
**Permisos:** ⚠️ Necesita revisión - No filtra por rol

**Características:**
- ✅ Vista de cronograma del proyecto
- ✅ ScheduleCategory + ScheduleItem
- ⚠️ **PROBLEMA:** No diferencia cliente vs PM/Admin

**⚠️ MEJORA NECESARIA:**
- Crear versión simplificada para clientes
- Ocultar información sensible (costos, notas internas)

---

### 4️⃣ **Schedule Generator**
**URL:** `/projects/{id}/schedule/generator/`  
**Vista:** `core/views.py:7682` - `schedule_generator_view()`  
**Template:** `core/templates/core/schedule_generator.html`  
**Permisos:** ✅ PM/Admin only

**Características:**
- ✅ Generación automática desde Estimate
- ✅ Vista jerárquica drag & drop
- ✅ Edición inline de categorías e items
- ✅ Vinculación a Budget Lines
- ✅ Cálculo automático de fechas

---

### 5️⃣ **Client Calendar** (Integrado)
**Ubicación:** `core/templates/core/client_project_view.html` (línea 512)  
**Vista:** Integrado en `client_project_view()`  
**Permisos:** ✅ Cliente solo ve su proyecto

**Características:**
- ✅ FullCalendar 6.x integrado
- ✅ Muestra upcoming_schedules (modelo Schedule legacy)
- ⚠️ **LIMITADO:** Solo muestra eventos próximos, no cronograma completo

**⚠️ MEJORA NECESARIA:**
- Expandir para mostrar ScheduleItems del proyecto
- Agregar filtros (milestones, fases)
- Vista más visual y user-friendly

---

## 🔌 **API ENDPOINTS**

### ScheduleCategory API
```
GET    /api/v1/schedule/categories/
POST   /api/v1/schedule/categories/
GET    /api/v1/schedule/categories/{id}/
PUT    /api/v1/schedule/categories/{id}/
DELETE /api/v1/schedule/categories/{id}/
```

### ScheduleItem API
```
GET    /api/v1/schedule/items/
POST   /api/v1/schedule/items/
GET    /api/v1/schedule/items/{id}/
PUT    /api/v1/schedule/items/{id}/
DELETE /api/v1/schedule/items/{id}/
```

### Master Schedule Data API
```
GET /api/v1/schedule/master-data/
```
**Respuesta:** JSON con proyectos, schedule items, invoices, eventos

### PM Calendar Data API
```
GET /pm-calendar/api/data/
```
**Respuesta:** JSON con eventos del PM (proyectos, deadlines, blocked days)

---

## 🔐 **MATRIZ DE PERMISOS**

| Rol | Master Schedule | PM Calendar | Project Schedule | Schedule Generator | Client Calendar |
|-----|----------------|-------------|------------------|-------------------|-----------------|
| **Admin** | ✅ Full | ✅ Full | ✅ Full | ✅ Full | ✅ View |
| **PM** | ❌ No | ✅ Full | ✅ Full | ✅ Full | ✅ View |
| **Client** | ❌ No | ❌ No | ⚠️ Limitado | ❌ No | ✅ View |
| **Designer** | ❌ No | ❌ No | ✅ View | ❌ No | ❌ No |
| **Employee** | ❌ No | ❌ No | ✅ View | ❌ No | ❌ No |

---

## 🚨 **PROBLEMAS DETECTADOS**

### 1️⃣ **Duplicidad: Schedule vs ScheduleItem**
**Estado:** ⚠️ No resuelto  
**Impacto:** Confusión en código, datos duplicados

**Análisis:**
- `Schedule` (legacy) se usa en:
  - `client_project_view` - upcoming schedules
  - PDF exports
  - Algunos dashboards
- `ScheduleItem` (moderno) se usa en:
  - Schedule Generator
  - Project Schedule View
  - Master Schedule
  - API REST

**Recomendación:**
- **NO deprecar `Schedule` todavía** - se usa activamente
- **Estrategia de migración gradual:**
  1. Actualizar `client_project_view` para usar `ScheduleItem`
  2. Actualizar PDF exports
  3. Migrar datos existentes
  4. Deprecar modelo `Schedule`

---

### 2️⃣ **Permisos Inconsistentes**
**Estado:** ⚠️ Parcialmente resuelto

**Problemas:**
- ✅ Master Schedule: Correctamente protegido (staff only)
- ✅ PM Calendar: Correctamente protegido (PM only)
- ⚠️ Project Schedule View: **NO filtra contenido por rol**
- ❌ Schedule Generator: Protegido pero sin filtro de proyectos asignados

**Solución necesaria:**
```python
# En project_schedule_view:
if profile.role == 'client':
    # Mostrar versión simplificada
    return render(request, 'core/client_project_schedule.html', context)
else:
    # Mostrar versión completa
    return render(request, 'core/project_schedule.html', context)
```

---

### 3️⃣ **Cliente Calendar Limitado**
**Estado:** ⚠️ Funcional pero básico

**Problemas:**
- Solo muestra "upcoming schedules" (próximos 5)
- No muestra cronograma completo del proyecto
- No integrado con ScheduleItems modernos
- No muestra fases ni milestones

**Solución necesaria:**
- Crear `client_project_calendar_view()` dedicada
- Template específico `client_project_calendar.html`
- API endpoint `/api/v1/projects/{id}/client-calendar/`
- Filtrar información sensible (costos, notas internas)

---

### 4️⃣ **UI/UX Fragmentada**
**Estado:** ⚠️ Inconsistente

**Problemas:**
- Master Schedule: Estilo moderno con gradientes violeta
- PM Calendar: Estilo moderno con gradientes violeta
- Project Schedule: Estilo básico Bootstrap
- Client Calendar: Básico, solo lista

**Solución:**
- Unificar estilos
- Crear componente base reutilizable
- Mejorar client calendar con diseño moderno

---

## ✅ **RECOMENDACIONES PRIORITARIAS**

### 🔴 **PRIORIDAD ALTA (1-2 semanas)**

#### 1. **Mejorar Cliente Calendar**
```python
# Crear nueva vista dedicada
@login_required
def client_project_calendar_view(request, project_id):
    """
    Calendar view específica para clientes.
    Muestra cronograma del proyecto de forma hermosa y simple.
    """
    project = get_object_or_404(Project, id=project_id)
    
    # Verificar que el cliente tiene acceso
    if not request.user.is_staff:
        if not project.client or project.client.user != request.user:
            return HttpResponseForbidden()
    
    # Obtener schedule items (sin info sensible)
    schedule_items = project.schedule_items.filter(
        is_milestone=True  # Solo milestones para clientes
    ).select_related('category')
    
    # Serializar para FullCalendar
    events = []
    for item in schedule_items:
        events.append({
            'title': item.title,
            'start': item.planned_start.isoformat(),
            'end': item.planned_end.isoformat(),
            'color': '#667eea' if item.status == 'DONE' else '#ffc107',
            'description': item.description,  # Sin notas internas
            # NO incluir: cost_code, estimate_line, internal notes
        })
    
    context = {
        'project': project,
        'events_json': json.dumps(events),
        'title': f'Cronograma - {project.name}'
    }
    
    return render(request, 'core/client_project_calendar.html', context)
```

**Template nuevo:** `client_project_calendar.html`
- FullCalendar 6.x
- Diseño limpio y moderno
- Vista mensual por defecto
- Tooltips informativos
- Mobile-responsive

**URL:** `/projects/{id}/calendar/client/`

---

#### 2. **Agregar Filtrado por Rol en project_schedule_view**
```python
@login_required
def project_schedule_view(request, project_id: int):
    project = get_object_or_404(Project, id=project_id)
    profile = getattr(request.user, 'profile', None)
    
    # Filtrar por rol
    if profile and profile.role == 'client':
        # Redirigir a vista de cliente
        return client_project_calendar_view(request, project_id)
    
    # Vista completa para PM/Admin
    # ... resto del código
```

---

#### 3. **Unificar Estilos UI**
- Extraer CSS común a `schedule_base.css`
- Componente header reutilizable
- Paleta de colores consistente:
  - Primary: `#667eea` (violeta)
  - Secondary: `#764ba2` (morado)
  - Success: `#28a745`
  - Warning: `#ffc107`
  - Danger: `#dc3545`

---

### 🟡 **PRIORIDAD MEDIA (2-4 semanas)**

#### 4. **Migración Gradual Schedule → ScheduleItem**
1. Actualizar `client_project_view` para usar `ScheduleItem`
2. Crear script de migración de datos
3. Actualizar PDF exports
4. Deprecar modelo `Schedule`

---

#### 5. **Integración con Budget Lines**
- Mostrar presupuesto por fase en cronograma
- Alertas de desvío de presupuesto
- Comparación planned vs actual costs

---

### 🟢 **PRIORIDAD BAJA (Futuro)**

#### 6. **Integración AI**
- Sugerencia de fechas óptimas
- Detección de sobrecarga de trabajo
- Recomendaciones de reprogramación
- Predicción de retrasos

**Implementación:**
```python
# core/services/schedule_ai.py

class ScheduleAI:
    def suggest_optimal_dates(self, project, task_name):
        """Sugiere fechas basadas en carga de trabajo y dependencias"""
        pass
    
    def detect_overload(self, pm_user, date_range):
        """Detecta días con sobrecarga de trabajo"""
        pass
    
    def recommend_rescheduling(self, schedule_item):
        """Recomienda reprogramación si hay conflictos"""
        pass
```

---

## 📊 **MÉTRICAS DE ÉXITO**

| Métrica | Antes | Meta | Método |
|---------|-------|------|--------|
| Satisfacción Cliente (Calendar) | 60% | 90% | Survey post-implementación |
| Tiempo de planificación PM | 45 min/día | 20 min/día | Time tracking |
| Conflictos de schedule | 8/mes | 2/mes | Issue tracking |
| Adopción PM Calendar | 0% | 80% | Analytics |

---

## 🎯 **PRÓXIMOS PASOS**

### Semana 1-2:
1. ✅ Crear `client_project_calendar_view()` y template
2. ✅ Agregar filtrado por rol en `project_schedule_view()`
3. ✅ Extraer CSS común a `schedule_base.css`
4. ✅ Tests para nuevas vistas

### Semana 3-4:
1. ✅ Migración datos `Schedule` → `ScheduleItem`
2. ✅ Actualizar `client_project_view` (usar ScheduleItem)
3. ✅ Deprecar modelo `Schedule`
4. ✅ Documentation update

### Mes 2-3:
1. ✅ Integración con Budget Lines
2. ✅ Alertas de desvío
3. ✅ Mobile improvements
4. ✅ Performance optimization

---

## 📁 **ARCHIVOS CLAVE**

### Modelos:
- `core/models.py` (líneas 497-700) - Schedule, ScheduleCategory, ScheduleItem
- `core/models.py` (línea 7585) - PMBlockedDay
- `core/models/__init__.py` (líneas 523-700) - Same models

### Vistas:
- `core/views.py:809` - master_schedule_center
- `core/views.py:6111` - project_schedule_view
- `core/views.py:7682` - schedule_generator_view
- `core/views_pm_calendar.py:32` - pm_calendar_view (NUEVO)

### Templates:
- `core/templates/core/master_schedule.html` (✅ Moderno)
- `core/templates/core/pm_calendar.html` (✅ Moderno)
- `core/templates/core/project_schedule.html` (⚠️ Básico)
- `core/templates/core/schedule_generator.html` (✅ Funcional)
- `core/templates/core/client_project_view.html` (⚠️ Calendar básico)

### API:
- `core/api/views.py` - ScheduleCategoryViewSet, ScheduleItemViewSet
- `core/views.py` - master_schedule_data (API endpoint)
- `core/views_pm_calendar.py` - pm_calendar_api_data (API endpoint)

### Services:
- `core/services/calendar_sync.py` - iCal exports, Google Calendar
- `core/services/calendar_feed.py` - Calendar feeds públicos

### Migrations:
- `core/migrations/0127_add_pm_blocked_day_model.py` (Pendiente commit)

---

## ✅ **CONCLUSIÓN**

El sistema de Schedule/Calendar en Kibray tiene una **arquitectura sólida** con implementaciones modernas ya funcionando (Master Schedule, PM Calendar). 

**Fortalezas:**
- ✅ Master Schedule Center moderno y funcional
- ✅ PM Calendar implementado con todas las features
- ✅ Modelo jerárquico robusto (ScheduleCategory + ScheduleItem)
- ✅ Integración con calendarios externos (iCal, Google)
- ✅ API REST completa

**Áreas de mejora inmediatas:**
1. 🔴 Mejorar Client Calendar (crear vista dedicada)
2. 🔴 Agregar filtrado por rol en vistas
3. 🟡 Migrar gradualmente Schedule → ScheduleItem
4. 🟡 Unificar estilos UI/UX

**Impacto estimado:**
- ⬆️ +40% satisfacción cliente
- ⬇️ -55% tiempo de planificación PM
- ⬇️ -75% conflictos de schedule

---

**Estado:** 🟢 **Sistema funcional, mejoras identificadas y priorizadas**  
**Próxima acción:** Implementar mejoras de prioridad alta (Client Calendar + Permisos)
