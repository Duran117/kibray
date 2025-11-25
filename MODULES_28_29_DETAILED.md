# MÓDULOS 28-29 - FUNCIONES COMPLEMENTARIAS Y CRUD OPERATIONS

## 📝 **MÓDULO 28: CRUD OPERATIONS & FORMS** (12/12 COMPLETO)

### 📌 FUNCIÓN 28.1 - Crear Schedule (CRUD Básico)

**Vista:** `schedule_create_view` (línea 476)

**Propósito:** Formulario simple para crear eventos de cronograma (legacy - reemplazado por Schedule system nuevo).

**Permisos:** Solo admin/PM

**Flujo:**
```
Admin/PM → Formulario Schedule → Guardar → Redirect dashboard
```

**Implementación:**
```python
@login_required
def schedule_create_view(request):
    profile = request.user.profile
    if profile.role not in ["admin", "superuser", "project_manager"]:
        return redirect('dashboard')

    if request.method == "POST":
        form = ScheduleForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('dashboard')
    else:
        form = ScheduleForm()
    
    return render(request, "core/schedule_form.html", {"form": form})
```

**Nota:** Esta función es parte del sistema legacy de Schedule. El nuevo sistema usa `ScheduleCategory` y `ScheduleItem` con el Gantt interactivo.

---

### 📌 FUNCIÓN 28.2 - Crear Expense (CRUD Básico)

**Vista:** `expense_create_view` (línea 492)

**Propósito:** Formulario para registrar gastos del proyecto.

**Permisos:** Solo admin/PM

**Campos del formulario:**
- Project (selector)
- Amount (decimal)
- Description (text)
- Category (selector: Materials, Labor, Equipment, etc.)
- Date (date picker)
- Receipt (file upload - opcional)

**Flujo:**
```
PM selecciona proyecto → Ingresa amount + category → Sube recibo → Save
                                ↓
                        Expense registrado en DB
                                ↓
                        Afecta AC (Actual Cost) en EV
```

---

### 📌 FUNCIÓN 28.3 - Crear Income (CRUD Básico)

**Vista:** `income_create_view` (línea 508)

**Propósito:** Registrar ingresos recibidos (pagos de clientes).

**Campos:**
- Project
- Amount
- Description
- Payment method (Check, Transfer, Cash, Credit Card)
- Date received
- Receipt/proof (file upload)

**Diferencia vs Invoice Payment:**
- **Income**: Ingreso genérico (puede ser adelanto, pago final sin invoice, etc.)
- **InvoicePayment**: Pago específico vinculado a una factura

**Uso común:**
```
- Depósitos iniciales antes de crear invoice
- Pagos en efectivo pequeños
- Ingresos misceláneos del proyecto
```

---

### 📌 FUNCIÓN 28.4 - Crear TimeEntry (CRUD Básico)

**Vista:** `timeentry_create_view` (línea 524)

**Propósito:** Registro manual de horas trabajadas (alternativa a clock in/out).

**Campos:**
- Date (date picker)
- Project (selector)
- Hours worked (decimal)
- Description/notes
- Cost code (opcional)
- Change order (opcional)

**Auto-asignación:**
```python
entry = form.save(commit=False)
entry.employee = request.user.employee  # Auto-asigna al usuario actual
entry.save()
```

**Uso:**
- Empleados que olvidaron hacer clock in/out
- Correcciones de tiempo
- Trabajo remoto/offline

**Botón "Save and Add Another":**
```html
<button type="submit" name="save_and_add_another">
    Save and Add Another
</button>
```
Permite registrar múltiples días rápidamente.

---

### 📌 FUNCIÓN 28.5-28.8 - Task CRUD Operations

**28.5: task_list_view** (línea 3375)
- Lista de tareas del proyecto
- Formulario inline para crear nueva task
- Solo staff puede crear

**28.6: task_detail** (línea 3399)
- Detalle de tarea individual
- Muestra: título, descripción, status, asignado, proyecto
- Enlaces a editar/eliminar

**28.7: task_edit_view** (línea 3405)
- Editar tarea existente
- Solo staff
- Formulario pre-llenado con datos actuales

**28.8: task_delete_view** (línea 3422)
- Confirmación antes de eliminar
- Solo staff
- Redirect a task_list del proyecto

**UI Mockup - Task List:**
```
┌────────────────────────────────────────────────────────┐
│ 📋 Tasks - Project Alpha                               │
├────────────────────────────────────────────────────────┤
│ ┌────────────────────────────────────────────────────┐ │
│ │ ✅ Paint living room - DONE                        │ │
│ │    Assigned: Juan P. | Due: 2025-04-20             │ │
│ │    [View] [Edit] [Delete]                          │ │
│ ├────────────────────────────────────────────────────┤ │
│ │ 🔵 Install trim - IN PROGRESS                      │ │
│ │    Assigned: Mike J. | Due: 2025-04-25             │ │
│ │    [View] [Edit] [Delete]                          │ │
│ ├────────────────────────────────────────────────────┤ │
│ │ ⚪ Exterior touch-ups - PENDING                    │ │
│ │    Unassigned | Due: 2025-04-30                    │ │
│ │    [View] [Edit] [Delete]                          │ │
│ └────────────────────────────────────────────────────┘ │
│                                                        │
│ ➕ Create New Task                                     │
│ ┌────────────────────────────────────────────────────┐ │
│ │ Title: [___________________________________]       │ │
│ │ Description: [______________________________]      │ │
│ │ Assign to: [Select employee ▼]                    │ │
│ │ Due date: [2025-05-01]                             │ │
│ │ [Create Task]                                      │ │
│ └────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────┘
```

---

### 📌 FUNCIÓN 28.9 - task_list_all

**Vista:** `task_list_all` (línea 3435)

**Propósito:** Ver todas las tareas asignadas al usuario actual (vista personal del empleado).

**Filtrado:**
```python
tasks = Task.objects.filter(
    assigned_to=request.user
).select_related("project").order_by("-id")
```

**Diferencia con task_list_view:**
- `task_list_view`: Todas las tareas de UN proyecto específico
- `task_list_all`: Mis tareas de TODOS los proyectos

**Uso:** Employee dashboard → "My Tasks" → Ve tareas de múltiples proyectos

---

### 📌 FUNCIÓN 28.10-28.12 - Schedule CRUD (ScheduleCategory & ScheduleItem)

**28.10: schedule_category_edit** (línea 4632)
```python
def schedule_category_edit(request, category_id):
    """Editar categoría del cronograma (ej: cambiar nombre de 'Prep' a 'Preparation')"""
    category = get_object_or_404(ScheduleCategory, pk=category_id)
    # ... form logic
```

**28.11: schedule_category_delete** (línea 4657)
```python
def schedule_category_delete(request, category_id):
    """Eliminar categoría completa (y sus items asociados)"""
    category = get_object_or_404(ScheduleCategory, pk=category_id)
    category.delete()  # Cascade delete items
```

**28.12: schedule_item_edit** (línea 4678)
```python
def schedule_item_edit(request, item_id):
    """Editar item del cronograma (fechas, progreso, dependencias)"""
    item = get_object_or_404(ScheduleItem, pk=item_id)
    # ... form logic
```

**28.13: schedule_item_delete** (línea 4703)
```python
def schedule_item_delete(request, item_id):
    """Eliminar item del cronograma"""
    item = get_object_or_404(ScheduleItem, pk=item_id)
    item.delete()
```

**Uso común:**
- PM ajusta cronograma después de auto-generación desde estimate
- Agrega subcategorías detalladas
- Cambia fechas cuando hay retrasos/adelantos
- Elimina items obsoletos

---

## 🏗️ **MÓDULO 29: PROJECT MANAGEMENT VIEWS** (13/13 COMPLETO)

### 📌 FUNCIÓN 29.1 - Lista de Proyectos

**Vista:** `project_list` (línea 2591)

**Propósito:** Vista simple de todos los proyectos del sistema.

**Implementación:**
```python
@login_required
def project_list(request):
    projects = Project.objects.all().order_by('id')
    return render(request, 'core/project_list.html', {'projects': projects})
```

**UI Mockup:**
```
┌──────────────────────────────────────────────────────────┐
│ 🏗️  All Projects                            [+ New]      │
├──────────────────────────────────────────────────────────┤
│ ID │ Name              │ Client     │ Status  │ Progress │
├────┼───────────────────┼────────────┼─────────┼──────────┤
│ 1  │ Alpha Residence   │ John Doe   │ Active  │ 28%      │
│ 2  │ Beta Commercial   │ ABC Corp   │ Active  │ 65%      │
│ 3  │ Gamma Touch-up    │ Jane Smith │ Closed  │ 100%     │
│ 4  │ Delta Remodel     │ Mike Jones │ Active  │ 15%      │
└──────────────────────────────────────────────────────────┘
```

**Acciones por fila:**
- Click → Ir a project_overview
- Links: View Details, Budget, Schedule, Invoice Builder

---

### 📌 FUNCIÓN 29.2 - Project Overview (Vista 360°)

**Vista:** `project_overview` (línea 3133)

**Propósito:** Dashboard completo del proyecto con todas las métricas en una sola página.

**Secciones incluidas:**
```
1. Project Summary (client, location, dates, status)
2. Financial Metrics (budget, spent, revenue, profit)
3. Earned Value (PV, EV, AC, SPI, CPI)
4. Team & Labor (PM, employees, hours logged)
5. Tasks & Quality (tasks, touch-ups, damage reports)
6. Materials & Inventory (requests, stock alerts)
7. Upcoming Milestones (schedule items próximos)
8. Design & Color (samples, floor plans, design chat)
9. Quick Actions (buttons para crear CO, Invoice, Meeting)
```

**Permisos:** Solo staff/PM

**Uso:** Vista ejecutiva para tomar decisiones rápidas sin navegar múltiples páginas.

---

### 📌 FUNCIÓN 29.3 - Client Project View

**Vista:** `client_project_view` (línea 758)

**Propósito:** Vista del proyecto específicamente diseñada para clientes (sin datos internos).

**Qué ve el cliente:**
```
✅ Project info (name, location, description)
✅ Schedule timeline (ScheduleItems visuales)
✅ Progress photos (SitePhoto gallery)
✅ Invoices SENT (no DRAFT)
✅ Payments made (history)
✅ Change Orders approved/pending
✅ Color Samples submitted
✅ Chat with team
✅ Request forms (materials, issues)

❌ NO ve: Labor costs, payroll, internal notes
❌ NO ve: Profit margins, EV metrics
❌ NO ve: Employee time entries
```

**UI enfoque:**
- Visual-first (fotos grandes, progress bars)
- Comunicación fácil (chat button prominente)
- Self-service (submit color samples, requests)

---

### 📌 FUNCIÓN 29.4 - Pickup View

**Vista:** `pickup_view` (línea 3371)

**Propósito:** Vista para coordinación de recogida de materiales.

**Uso:** PM genera lista de materiales listos para pickup por empleados.

**Implementación:**
```python
@login_required
def pickup_view(request, project_id: int):
    """Lista de materiales pendientes de pickup para el proyecto"""
    project = get_object_or_404(Project, pk=project_id)
    # ... mostrar MaterialRequests con status='ordered' o 'ready_for_pickup'
```

**UI Mockup:**
```
┌────────────────────────────────────────────────┐
│ 📦 Pickup List - Project Alpha                 │
├────────────────────────────────────────────────┤
│ Ready for Pickup:                              │
│ ☑ Premium White Paint (10 gal)                │
│    Location: Home Depot #4521                  │
│    Order #: HD-8975412                         │
│    [Mark as Picked Up]                         │
│                                                │
│ ☑ Masking Tape (12 rolls)                     │
│    Location: Sherwin Williams                  │
│    Order #: SW-65432                           │
│    [Mark as Picked Up]                         │
└────────────────────────────────────────────────┘
```

---

### 📌 FUNCIÓN 29.5 - Budget Line Plan View

**Vista:** `budget_line_plan_view` (línea 2582)

**Propósito:** Planificar fechas de una línea presupuestal específica.

**Campos editables:**
- planned_start (date)
- planned_finish (date)
- baseline_amount (decimal)

**Flujo:**
```
PM crea BudgetLine → Define fechas planeadas → Se usa para calcular PV
                             ↓
                    line_planned_percent() usa estas fechas
                             ↓
                    EV calculation preciso por fecha
```

**Importancia:** Sin fechas planeadas, EV asume 100% desde día 1 (incorrecto).

---

### 📌 FUNCIÓN 29.6-29.9 - Progress Management

**29.6: upload_project_progress** (línea 2682)
```python
def upload_project_progress(request, project_id):
    """
    Upload bulk progress via CSV file.
    PM puede actualizar progreso de múltiples líneas offline.
    """
    # Parse CSV con columnas: budget_line_id, date, percent_complete, notes
    # Crear BudgetProgress para cada fila
```

**Flujo de bulk update:**
```
1. PM descarga template CSV (download_progress_sample)
2. PM llena progreso en Excel offline
3. PM sube CSV (upload_project_progress)
4. Sistema crea BudgetProgress records
5. Dashboard EV actualiza automáticamente
```

**29.7: delete_progress** (línea 2777)
```python
def delete_progress(request, project_id, pk):
    """Eliminar punto de progreso incorrecto"""
    prog = get_object_or_404(BudgetProgress, pk=pk)
    prog.delete()
```

**29.8: edit_progress** (línea 2789)
```python
def edit_progress(request, project_id, pk):
    """Editar progreso existente (corregir % o fecha)"""
    prog = get_object_or_404(BudgetProgress, pk=pk)
    form = BudgetProgressEditForm(request.POST or None, instance=prog)
    # ...
```

**29.9: project_ev_series** (línea 2524)
```python
def project_ev_series(request, project_id):
    """
    JSON endpoint para gráficos de tendencia EV.
    Retorna series de datos para Chart.js o similar.
    """
    # Calcula EV para cada día en un rango
    # Retorna: {dates: [], pv: [], ev: [], ac: []}
```

**Uso de project_ev_series:**
```javascript
// Frontend - Chart.js
fetch(`/project/${projectId}/ev/series/?days=45`)
  .then(res => res.json())
  .then(data => {
    new Chart(ctx, {
      type: 'line',
      data: {
        labels: data.dates,
        datasets: [
          {label: 'PV', data: data.pv, borderColor: 'blue'},
          {label: 'EV', data: data.ev, borderColor: 'green'},
          {label: 'AC', data: data.ac, borderColor: 'red'}
        ]
      }
    });
  });
```

---

### 📌 FUNCIÓN 29.10 - Daily Log View

**Vista:** `daily_log_view` (línea 2320)

**Propósito:** Registro diario de actividades del proyecto (bitácora).

**Uso:**
- PM registra eventos importantes
- Problemas encontrados
- Decisiones tomadas
- Visitas de inspectores
- Condiciones climáticas

**Campos:**
```python
class DailyLog(models.Model):
    project = ForeignKey(Project)
    date = DateField()
    weather = CharField(max_length=50)  # Sunny, Rainy, etc.
    crew_count = IntegerField()
    hours_worked = DecimalField()
    work_performed = TextField()
    issues = TextField(blank=True)
    notes = TextField(blank=True)
    created_by = ForeignKey(User)
```

**UI Mockup:**
```
┌────────────────────────────────────────────────────────┐
│ 📝 Daily Log - Project Alpha                           │
├────────────────────────────────────────────────────────┤
│ April 15, 2025                                         │
│ Weather: Sunny, 72°F                                   │
│ Crew: 4 employees, 32 hours total                     │
│                                                        │
│ Work Performed:                                        │
│ - Completed exterior prep on north wall               │
│ - Started first coat on east side                     │
│ - Installed masking on windows                        │
│                                                        │
│ Issues:                                                │
│ - Found rot on 2 window frames (photos attached)      │
│ - Need additional primer for damaged areas            │
│                                                        │
│ Notes:                                                 │
│ - Client approved color sample #3                     │
│ - Scheduled delivery of materials for 4/17            │
│                                                        │
│ Logged by: Mike Johnson (PM) at 5:45 PM               │
├────────────────────────────────────────────────────────┤
│ [Add New Log Entry]                                    │
└────────────────────────────────────────────────────────┘
```

**Diferencia vs DailyPlan:**
- **DailyPlan**: Planificación prospectiva (qué SE HARÁ)
- **DailyLog**: Registro retrospectivo (qué SE HIZO)

---

### 📌 FUNCIÓN 29.11 - Project Chat Index

**Vista:** `project_chat_index` (línea 1390)

**Propósito:** Página índice de canales de chat del proyecto.

**Funcionalidad:**
```python
def project_chat_index(request, project_id):
    """
    Muestra lista de canales disponibles:
    - General
    - Design Discussion
    - Direct with Client
    - etc.
    """
    project = get_object_or_404(Project, pk=project_id)
    channels = ChatChannel.objects.filter(project=project)
    return render(request, 'core/chat_index.html', {
        'project': project,
        'channels': channels
    })
```

**UI:**
```
┌────────────────────────────────────────────┐
│ 💬 Project Chat - Alpha Residence          │
├────────────────────────────────────────────┤
│ Channels:                                  │
│                                            │
│ 📢 General                    (12 unread)  │
│    Last: "Materials arrived" - 2h ago      │
│                                            │
│ 🎨 Design Discussion          (3 unread)   │
│    Last: "Color approved!" - 5h ago        │
│                                            │
│ 👤 Direct with John (Client)  (0 unread)   │
│    Last: "Thanks for update" - 1d ago      │
│                                            │
│ [+ Create New Channel]                     │
└────────────────────────────────────────────┘
```

Click en canal → `project_chat_room(project_id, channel_id)`

---

### 📌 FUNCIÓN 29.12 - Schedule Generator View

**Vista:** `schedule_generator_view` (línea 4470)

**Propósito:** Interfaz para auto-generar cronograma desde estimate.

**Flujo:**
```
PM → Project sin schedule → Click "Generate Schedule"
                    ↓
      Selector de estimate (si hay múltiples)
                    ↓
      Confirmación de generación
                    ↓
      Llamada a _generate_schedule_from_estimate()
                    ↓
      ScheduleCategories + Items creados
                    ↓
      Redirect a Gantt view para edición
```

**UI Mockup:**
```
┌────────────────────────────────────────────────┐
│ ⚡ Auto-Generate Schedule                      │
├────────────────────────────────────────────────┤
│ Project: Alpha Residence                       │
│                                                │
│ Select Estimate:                               │
│ (●) Estimate #2025-042 (approved)              │
│     5 categories, $40,000 total                │
│                                                │
│ ⚠️  This will create:                          │
│ • 5 schedule categories                        │
│ • 5 initial schedule items (placeholders)     │
│ • You can then add detailed subtasks           │
│                                                │
│ [Generate Schedule] [Cancel]                   │
└────────────────────────────────────────────────┘
```

**Después de generación:**
```
Success: Schedule created with 5 categories!
Next steps:
1. Review categories in Gantt view
2. Add detailed tasks per category
3. Set dependencies and dates
4. Assign resources
```

---

### 📌 FUNCIÓN 29.13 - Google Calendar Instructions

**Vista:** `project_schedule_google_calendar` (línea 4743)

**Propósito:** Página de instrucciones para suscribirse al calendario del proyecto.

**Contenido:**
```
1. Muestra URL de suscripción iCal
2. Instrucciones paso a paso por calendario:
   - Google Calendar: "Add calendar by URL"
   - Apple Calendar: "File → New Calendar Subscription"
   - Outlook: "Add calendar → From internet"
3. Botón para descargar .ics file directamente
```

**Template context:**
```python
context = {
    'project': project,
    'subscription_url': 'https://kibray.app/projects/5/schedule.ics',
    'ics_url': reverse('project_schedule_ics', kwargs={'project_id': project.id}),
}
```

**UI Mockup:**
```
┌──────────────────────────────────────────────────────┐
│ 📅 Subscribe to Project Schedule                     │
├──────────────────────────────────────────────────────┤
│ Project: Alpha Residence                             │
│                                                      │
│ Keep your calendar synced with project updates!     │
│                                                      │
│ Subscription URL:                                    │
│ ┌──────────────────────────────────────────────────┐│
│ │https://kibray.app/projects/5/schedule.ics  [Copy]││
│ └──────────────────────────────────────────────────┘│
│                                                      │
│ 📖 Instructions:                                     │
│                                                      │
│ ▼ Google Calendar                                    │
│   1. Open Google Calendar                            │
│   2. Click "+" next to "Other calendars"            │
│   3. Select "From URL"                               │
│   4. Paste the URL above                             │
│   5. Click "Add calendar"                            │
│                                                      │
│ ▼ Apple Calendar (macOS/iOS)                         │
│   1. Open Calendar app                               │
│   2. File → New Calendar Subscription                │
│   3. Paste the URL above                             │
│   4. Click "Subscribe"                               │
│                                                      │
│ ▼ Outlook                                            │
│   1. Open Outlook Calendar                           │
│   2. Add calendar → From internet                    │
│   3. Paste the URL above                             │
│   4. Click "OK"                                      │
│                                                      │
│ Or download the .ics file directly:                  │
│ [📥 Download Calendar File]                          │
│                                                      │
│ ✨ Updates automatically when schedule changes!      │
└──────────────────────────────────────────────────────┘
```

---

## 📊 **RESUMEN MÓDULOS 28-29**

**Módulo 28 - CRUD Operations (12 funciones):**
- 4 Create views: Schedule, Expense, Income, TimeEntry
- 4 Task CRUD: List, Detail, Edit, Delete
- 1 Task list all (personal)
- 4 Schedule CRUD: Category edit/delete, Item edit/delete

**Módulo 29 - Project Management Views (13 funciones):**
- 1 Project list (all projects)
- 1 Project overview (360° dashboard)
- 1 Client project view (cliente-specific)
- 1 Pickup view (material coordination)
- 1 Budget line plan (fechas)
- 4 Progress management (upload, delete, edit, series)
- 1 Daily log (bitácora)
- 1 Chat index (channels list)
- 1 Schedule generator (from estimate)
- 1 Google Calendar instructions

**Total: 25 funciones adicionales documentadas**

**GRAN TOTAL SISTEMA: 207 + 25 = 232 funciones (93% del sistema estimado de 250)**
