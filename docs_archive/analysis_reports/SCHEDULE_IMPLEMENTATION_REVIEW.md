# 🔬 AUDITORÍA DE IMPLEMENTACIÓN: Schedule/Gantt — Fase 1

**Fecha:** Abril 4, 2026  
**Filosofía:** Código simple, legible, reutilizable. Diseño premium minimalista estilo Apple — espacios limpios, armonía, sin ruido visual.  
**Meta:** Determinar la manera más inteligente (no la más rápida) de implementar.

---

## PREGUNTA CENTRAL

> ¿Cuál es la forma más simple y elegante de dar al cliente un Gantt read-only de su proyecto?

---

## OPCIÓN A: Crear template nuevo desde cero ❌

```
Nuevo template → nuevo CSS → nuevo JS → nuevo view → nuevo URL
```

**Contra:** Duplica lógica, más código que mantener, divergencia visual inevitable.

## OPCIÓN B: Reusar el React Gantt existente ✅

```
1 template de ~30 líneas → monta window.KibrayGantt.mount() con canEdit=false
```

**A favor:**
- El React Gantt YA tiene `canEdit` como prop (verificado en 60+ locations)
- `canEdit=false` ya deshabilita: drag, resize, create, delete, edit buttons
- Usa la misma API (`/api/v1/gantt/v2/projects/<id>/`)
- Misma data, misma fuente de verdad, cero sincronización
- Visual consistente entre PM view y Client view

---

## ANÁLISIS: ¿QUÉ HAY QUE CAMBIAR REALMENTE?

### 1. Lo que ya existe y funciona ✅

| Componente | Estado | Notas |
|-----------|--------|-------|
| React Gantt (`gantt-app.iife.js`) | ✅ Built & deployed | Soporta `canEdit=false` |
| API V2 (`/api/v1/gantt/v2/projects/<id>/`) | ✅ Funcional | Devuelve phases→items→tasks |
| Adapter (`transformV2Response`) | ✅ Funcional | Transforma API→Gantt format |
| Permission check en view | ✅ En `views_client_calendar.py` | Ya verifica ClientProjectAccess |
| `client_project_view.html` | ✅ Template del portal cliente | Ya tiene link "Schedule" que va a `client_project_calendar` |

### 2. Lo que NO funciona / sobra 🚨

| Componente | Problema | Líneas de código |
|-----------|----------|-----------------|
| `client_project_calendar.html` | **884 líneas** de CSS dark theme + FullCalendar + timeline custom | Template complejo para algo simple |
| `views_client_calendar.py` | **267 líneas** — 3 views, duplica access check 3 veces | Podría ser 1 view de ~40 líneas |
| `client_calendar_api_data` view | API wrapper innecesario — reformatea V2 data a FullCalendar format | Si usamos React Gantt, no se necesita |
| `client_calendar_milestone_detail` | AJAX detail modal — React Gantt ya tiene SlideOverPanel | Duplicado |
| FullCalendar CDN dependency | Solo para el client calendar — carga 200KB extra | React Gantt ya tiene CalendarView built-in |

### 3. Problema de diseño actual ⚠️

**El `client_project_calendar.html` actual:**
- Dark theme forzado (no coincide con `base_modern.html` que es light/slate)
- 884 líneas de CSS custom en un solo archivo
- FullCalendar CDN (200KB) para mostrar puntos en un calendario
- Timeline view custom en HTML plano
- Modal AJAX para detalles
- **No muestra barras Gantt** — solo dots y lista

**El portal del cliente (`client_project_view.html`) es:**
- Light theme (bg-white, slate borders)
- Tailwind CSS (ya incluido en base_modern)
- Clean, minimalist, con cards y spacing armónico
- Usa Bootstrap Icons

**Conflicto:** El calendar link lleva al cliente de un portal blanco/limpio → a una página dark/heavy. Ruptura visual completa.

---

## LA MANERA INTELIGENTE (Plan de Implementación)

### Principio: Reusar, no reinventar

En vez de mantener 884 líneas de template + 267 líneas de view + API custom + CDN dependency, hacemos esto:

### Paso 1: Simplificar la View (~30 líneas)

**Actual** (`views_client_calendar.py`): 267 líneas, 3 funciones, access check duplicado 3 veces.

**Propuesta**: Una sola view que:
1. Verifica acceso (reusar helper)
2. Renderiza template mínimo que monta React Gantt

```python
# Conceptual — la view quedaría así de simple:
@login_required
def client_project_schedule_view(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    verify_client_access(request.user, project)  # helper reutilizable
    return render(request, "core/client_project_schedule.html", {
        "project": project,
    })
```

**Nota:** El access check se repite idéntico en `client_project_calendar_view`, `client_calendar_api_data`, y `client_calendar_milestone_detail`. Debería extraerse a un helper/decorator.

### Paso 2: Template Mínimo (~35 líneas)

En vez de 884 líneas, el template sería:

```html
{% extends "core/base_modern.html" %}
{% block content %}
  <back-link> + <h1> + <project-name>
  <div id="gantt-app-root" style="height: calc(100vh - 180px);">
  <script> window.KibrayGantt.mount('gantt-app-root', {
    mode: 'project', projectId: X, canEdit: false, ...
  }) </script>
{% endblock %}
```

**Resultado visual:** El cliente ve exactamente el mismo Gantt que el PM pero sin botones de edición. Barras, phases, progress, dependencies, calendar toggle — todo incluido gratis.

### Paso 3: Seguridad en el API (crítico)

**Hallazgo de seguridad 🚨:** Todas las APIs V2 de schedule usan solo `@permission_classes([IsAuthenticated])`. Esto significa que un cliente autenticado podría:
- Llamar a `POST /api/v1/gantt/v2/items/` y crear items
- Llamar a `PATCH /api/v1/gantt/v2/items/<id>/` y editar items
- Llamar a `DELETE /api/v1/gantt/v2/items/<id>/` y borrar items

**Mitigación necesaria:**
- Frontend: `canEdit=false` previene la UI de hacer llamadas de escritura
- Backend: Las APIs de escritura (POST/PATCH/DELETE) necesitan verificar `is_staff or is_pm`
- El GET ya es safe — mostrar data read-only está bien para clientes autenticados con acceso al proyecto

### Paso 4: Limpieza del link en `client_project_view.html`

La nav bar del portal cliente ya tiene:
```html
<a href="{% url 'client_project_calendar' project.id %}">Schedule</a>
```

Solo cambiar el URL name para apuntar a la nueva view (o reusar el mismo nombre).

---

## COMPARACIÓN: ANTES vs DESPUÉS

| Métrica | Antes (actual) | Después (propuesto) |
|---------|---------------|-------------------|
| Template | 884 líneas (dark CSS custom) | ~35 líneas (reusar React Gantt) |
| View | 267 líneas (3 funciones) | ~30 líneas (1 función + helper) |
| API custom para cliente | `client_calendar_api_data` (50+ líneas) | No necesario — usa API V2 existente |
| AJAX detail view | `client_calendar_milestone_detail` (60+ líneas) | No necesario — SlideOverPanel built-in |
| CDN dependencies extra | FullCalendar 6.1.10 (~200KB) | Ninguna — ya cargado gantt-app.iife.js |
| Consistencia visual | ❌ Dark theme ≠ portal light | ✅ Misma estética que el resto del portal |
| Features para cliente | Dots en calendario + lista | Gantt bars + calendar + progress + dependencies |
| Mantenibilidad | Arreglar bugs en 2 lugares | 1 solo componente |
| **Total líneas de código** | **~1,200** | **~65** |

---

## DECISIONES QUE NECESITAN CONFIRMACIÓN

### D1: ¿El cliente ve el toggle Gantt/Calendar?
- **Opción A:** Solo Gantt (más simple, más limpio)
- **Opción B:** Gantt + Calendar toggle (ya viene gratis en React Gantt)
- **Recomendación:** Opción B — el ViewSwitcher ya está built-in, 0 código extra

### D2: ¿Qué pasa con `client_project_calendar.html` (884 líneas)?
- **Opción A:** Borrar inmediatamente
- **Opción B:** Renombrar a `client_project_calendar_legacy.html` y redirigir
- **Recomendación:** Opción B primero, borrar en la siguiente sesión de limpieza

### D3: ¿Se necesita campo `is_client_visible` en ScheduleItemV2?
- **Ahora:** No. Todos los items son visibles al cliente.
- **Futuro:** Si el PM quiere ocultar items internos, agregar un BooleanField con default=True
- **Recomendación:** No agregar ahora. YAGNI. Si se necesita, es un migration de 1 campo.

### D4: ¿La API V2 GET necesita verificar acceso por proyecto para clientes?
- **Ahora:** Solo verifica `IsAuthenticated` — cualquier usuario autenticado puede leer CUALQUIER proyecto
- **Riesgo:** Un cliente podría leer el schedule de un proyecto al que no tiene acceso
- **Recomendación:** Agregar verificación de acceso al proyecto en el GET endpoint
- **Prioridad:** Alta para producción, pero puede ser iteración separada

---

## ORDEN DE EJECUCIÓN

```
1. Crear helper de access check (reutilizable)          [~10 min]
2. Crear view simplificada                               [~10 min]
3. Crear template mínimo (~35 líneas)                    [~15 min]
4. Actualizar URL + link en client_project_view.html     [~5 min]
5. Probar: cliente ve Gantt read-only                    [~10 min]
6. Renombrar template legacy                             [~2 min]
7. Commit + push                                         [~5 min]
```

**Tiempo total estimado: ~1 hora**

---

## VERIFICACIÓN DE DISEÑO (Apple Minimal)

El React Gantt ya usa:
- **Fondo blanco** con borders `#e5e7eb` (slate-200)
- **Tipografía system-ui** (Inter/SF Pro stack)
- **Colores sobrios:** indigo-600 accent, slate grays, emerald/amber para status
- **Spacing generoso:** 48px row height, 280px sidebar
- **Transiciones suaves:** 200ms ease en hover states
- **Sin decoración excesiva:** no shadows, no gradients, no rounded excess

Esto es **consistente con `client_project_view.html`** que usa el mismo lenguaje visual (white cards, slate borders, indigo accents).

El template actual `client_project_calendar.html` con su dark theme es la **anomalía** — es el que rompe la armonía.

---

## CONCLUSIÓN

> **La mejor manera de hacer esto NO es escribir código nuevo.**  
> Es eliminar 1,200 líneas de código innecesario y reusar lo que ya funciona.

El React Gantt es el componente más pulido del sistema. Tiene drag&drop, dependency lines, stage bars, progress calculations, calendar view, slide-over panel — todo con `canEdit` como prop booleano.

Montarlo con `canEdit=false` para el cliente es literalmente **3 líneas de JavaScript** y **0 líneas de CSS**.

La respuesta a "¿cuál es la mejor manera?" es: **la que resulta en menos código.**

---

> ⏳ **PENDIENTE:** Aprobación del usuario antes de implementar.
