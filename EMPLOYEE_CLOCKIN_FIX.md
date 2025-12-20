# Fix: Employee Clock-In Issue

## Problema Identificado

El dashboard de empleado no permitía hacer clock-in incluso cuando el usuario tenía:
- Empleado asignado ✅
- Proyecto asignado ✅

La razón era que la lógica **solo** verificaba `ResourceAssignment` con `date=today`, y si no había una asignación específica para el día actual, bloqueaba completamente el clock-in.

## Solución Implementada

### 1. Lógica Mejorada de Proyectos Disponibles

La nueva lógica considera **múltiples fuentes** de proyectos válidos (en orden de prioridad):

#### a) Proyectos Asignados Hoy (ResourceAssignment)
```python
assignments_today = ResourceAssignment.objects.filter(employee=employee, date=today)
projects_from_assignments = Project.objects.filter(resource_assignments__in=assignments_today)
```
**Prioridad:** ALTA

#### b) Proyectos con Trabajo Reciente (últimos 30 días)
```python
recent_cutoff = today - timedelta(days=30)
projects_from_recent_work = Project.objects.filter(
    time_entries__employee=employee,
    time_entries__date__gte=recent_cutoff,
    is_archived=False
)
```
**Prioridad:** MEDIA

#### c) Proyectos Activos (sin fecha de fin)
```python
active_projects = Project.objects.filter(
    end_date__isnull=True,
    is_archived=False
).exclude(status__in=['completed', 'cancelled'])
```
**Prioridad:** BAJA (fallback)

### 2. Política de Clock-In por Modo

La lógica ahora determina diferentes **modos de clock-in**:

| Modo | Condición | Proyectos Disponibles | UI Badge |
|------|-----------|----------------------|----------|
| `override_admin` | Usuario es staff | TODOS los proyectos | 🟣 Morado |
| `assigned_today` | Tiene ResourceAssignment hoy | Solo proyectos asignados hoy | 🟢 Verde |
| `recent_or_active` | Sin asignación hoy, pero trabajó recientemente | Proyectos recientes + activos | 🔵 Azul |
| `fallback_active` | Sin trabajo reciente | Solo proyectos activos | 🟡 Amarillo |

### 3. Validación Backend Mejorada

```python
# Antes: verificación estricta solo con asignaciones de hoy
if selected_project not in my_projects_today:
    messages.error(request, "❌ No estás asignado...")
    return redirect("dashboard_employee")

# Ahora: verificación flexible con lista combinada
if selected_project in available_projects:
    # ✅ Permitir clock-in
    pass
else:
    # ❌ Denegar clock-in
    messages.error(request, "❌ No tienes permiso...")
    return redirect("dashboard_employee")
```

### 4. UI Mejorada con Feedback Claro

El template ahora muestra **diferentes alertas según el modo**:

#### Modo: `assigned_today` (Asignación específica hoy)
```
✅ Tienes asignaciones de proyecto para hoy
Puedes hacer clock-in en 2 proyectos asignados.
```

#### Modo: `recent_or_active` (Sin asignación hoy)
```
ℹ️ Sin asignación específica para hoy
Puedes hacer clock-in en 5 proyectos basados en tu trabajo reciente.
Próximas asignaciones: Dec 20 · Proyecto A, Dec 21 · Proyecto B
```

#### Modo: `fallback_active` (Sin trabajo reciente)
```
⚠️ No se encontró trabajo reciente
Puedes hacer clock-in en 8 proyectos activos. Si es incorrecto, contacta a tu supervisor.
```

#### Modo: Sin proyectos disponibles
```
❌ No hay proyectos disponibles
No puedes hacer clock-in sin una asignación de proyecto.
Contacta a tu supervisor para que te asigne.
```

## Archivos Modificados

### Backend
- `core/views.py` - Función `dashboard_employee()`:
  - Nueva lógica de combinación de proyectos
  - Validación backend mejorada
  - Contexto enriquecido con `clock_in_mode`

### Frontend
- `core/templates/core/dashboard_employee_clean.html`:
  - Alertas condicionales por modo
  - Mensajes traducidos con i18n
  - Feedback visual mejorado (colores, iconos)

## Testing

Para probar con un usuario específico, ejecutar:

```bash
python3 diagnose_employee_clockin.py <username>
```

Este script diagnóstico mostrará:
- ✅ Asignaciones de hoy
- 📊 Proyectos desde asignaciones
- 🕐 Proyectos con trabajo reciente
- 🟢 Proyectos activos
- 🎯 Proyectos combinados disponibles
- 🚦 Modo de clock-in aplicable
- ⏰ Estado actual (TimeEntry abierto o no)

## Ejemplo de Salida del Diagnóstico

```
================================================================================
DIAGNÓSTICO DE CLOCK-IN PARA USUARIO: john.doe
================================================================================

✅ Usuario encontrado: john.doe (ID: 15)
   - Staff: False
   - Superuser: False

✅ Empleado vinculado: John Doe (ID: 8)

📅 Fecha de hoy: 2025-12-19
📅 Fecha de corte (últimos 30 días): 2025-11-19

🔍 ASIGNACIONES PARA HOY (2025-12-19):
   ⚠️  NO hay asignaciones específicas para hoy

🔍 PROYECTOS DESDE ASIGNACIONES DE HOY:
   ⚠️  NO hay proyectos desde asignaciones de hoy

🔍 PROYECTOS CON TRABAJO RECIENTE (últimos 30 días):
   ✅ 3 proyecto(s):
      - Residencia Martinez (ID: 45)
        Último trabajo: 2025-12-15
      - Oficina Downtown (ID: 52)
        Último trabajo: 2025-12-10
      - Casa Rodriguez (ID: 38)
        Último trabajo: 2025-11-28

🔍 PROYECTOS ACTIVOS (sin fecha de fin, no archivados):
   ℹ️  12 proyecto(s) activos en total:
      - Residencia Martinez (ID: 45)
      - Oficina Downtown (ID: 52)
      ... y 10 más

🎯 PROYECTOS DISPONIBLES PARA CLOCK-IN (combinados):
   ✅ 12 proyecto(s) totales:
      - Residencia Martinez (ID: 45) [trabajo reciente, activo]
      - Oficina Downtown (ID: 52) [trabajo reciente, activo]
      - Casa Rodriguez (ID: 38) [trabajo reciente, activo]
      ... y 9 más

🚦 DECISIÓN DE POLÍTICA:
   ℹ️  Modo: RECENT_OR_ACTIVE
   → Puede hacer clock-in en proyectos con trabajo reciente o activos (12)

⏰ ESTADO ACTUAL:
   ⚪ NO tiene TimeEntry abierto (puede hacer clock-in)

================================================================================
DIAGNÓSTICO COMPLETO
================================================================================
```

## Beneficios

1. **Flexibilidad:** Empleados pueden trabajar sin necesidad de ResourceAssignment diario
2. **Continuidad:** Empleados pueden seguir en proyectos donde ya trabajaron
3. **Seguridad:** Validación backend sigue protegiendo contra accesos no autorizados
4. **Transparencia:** UI clara muestra por qué ciertos proyectos están disponibles
5. **Diagnóstico:** Script de debug facilita troubleshooting

## Compatibilidad

- ✅ Mantiene funcionalidad de ResourceAssignment cuando existe
- ✅ Modo admin (`override_admin`) sigue funcionando
- ✅ Validación backend no comprometida
- ✅ Templates legacy y clean ambos actualizados

## Próximos Pasos Sugeridos

1. Crear ResourceAssignments para empleados regulares (mejora planificación)
2. Añadir notificación proactiva cuando faltan asignaciones
3. Dashboard PM: resaltar empleados sin asignaciones para el día
4. Reportes: tiempo trabajado sin asignación formal
