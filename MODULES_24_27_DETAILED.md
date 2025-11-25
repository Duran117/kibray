# MÓDULOS 24-27 - DOCUMENTACIÓN DETALLADA

## 📦 **MÓDULO 24: USER MANAGEMENT & SETTINGS** (4/4 COMPLETO)

### 📌 FUNCIÓN 24.1 - Cambio de Idioma (i18n)

**Vista:** `set_language_view` (línea 3112)

**Propósito:** Cambiar idioma del entorno visual completo (iconos, etiquetas, UI) entre inglés/español.

**Alcance del cambio:**
```
✅ Interfaz completa (labels, buttons, headers)
✅ Mensajes del sistema
✅ Notificaciones
✅ Dashboards
❌ NO afecta: Reportes PDF (siguen en español)
❌ NO afecta: Datos ingresados por usuarios
```

**Flujo:**
```
Usuario selecciona idioma → Actualiza sesión → Activa traducción
                                  ↓
                          Persiste en Profile.language
                                  ↓
                          Redirect a página anterior
```

**Implementación:**
```python
def set_language_view(request, code: str):
    code = (code or '').lower()
    if code not in ("en", "es"):
        code = "en"
    
    # 1. Actualizar sesión
    request.session["lang"] = code
    translation.activate(code)
    
    # 2. Persistir en usuario
    if request.user.is_authenticated:
        prof = request.user.profile
        prof.language = code
        prof.save(update_fields=["language"])
    
    # 3. Redirect
    next_url = request.META.get("HTTP_REFERER") or reverse("dashboard")
    return redirect(next_url)
```

**Idiomas soportados:**
- `en`: English (para clientes que hablan inglés)
- `es`: Español (para equipo interno)

**UI Mockup:**
```
┌─────────────────────────────────────┐
│ ⚙️  User Settings                   │
├─────────────────────────────────────┤
│ Language / Idioma:                  │
│                                     │
│  ( ) 🇺🇸 English                    │
│  (●) 🇲🇽 Español                    │
│                                     │
│ [Guardar Cambios]                   │
└─────────────────────────────────────┘
```

---

### 📌 FUNCIÓN 24.2 - Profile & Roles

**Modelo:** `Profile` (models.py línea 410)

**Campos:**
```python
class Profile(models.Model):
    user = OneToOneField(User)
    role = CharField(choices=ROLE_CHOICES)  # 6 roles
    language = CharField(choices=[('en','English'), ('es','Español')])
```

**Roles del Sistema:**
```
1. admin - Acceso total, dashboards financieros
2. project_manager - Gestión de proyectos, nómina, COs
3. employee - Registro de tiempo, tareas asignadas
4. client - Vista de proyecto, chat, invoices
5. designer - Color samples, floor plans, design chat
6. superintendent - Quality control, damage reports, touch-ups
```

**Auto-creación:**
```python
@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(
            user=instance,
            role='employee',  # Default
            language='en'
        )
```

**Uso en vistas:**
```python
profile = request.user.profile
role = profile.role

if role in ["admin", "superuser", "project_manager"]:
    # Acceso permitido
    pass
```

---

### 📌 FUNCIÓN 24.3 - ClientProjectAccess (Acceso Granular)

**Modelo:** `ClientProjectAccess` (models.py línea 434)

**Propósito:** Controlar qué proyectos ve cada cliente y qué puede hacer.

**Campos:**
```python
class ClientProjectAccess(models.Model):
    user = ForeignKey(User)
    project = ForeignKey(Project)
    role = CharField(choices=[
        ('client', 'Client'),
        ('external_pm', 'External PM'),
        ('viewer', 'Viewer')
    ])
    can_comment = BooleanField(default=True)
    can_create_tasks = BooleanField(default=True)
    granted_at = DateTimeField(auto_now_add=True)
```

**Qué puede ver un cliente en su proyecto:**
```
✅ Invoices enviados (SENT, VIEWED, APPROVED)
✅ Payments realizados
✅ Change Orders aprobados/pendientes
✅ Schedule completo (ScheduleCategory, ScheduleItem)
✅ Información del proyecto (descripción, ubicación, fechas)
✅ Color Samples (propuestos, aprobados, rechazados)
✅ Actividades/Tareas asignadas
✅ Problemas reportados (Issues)
✅ Chat directo con admin
✅ Chat grupal con designer, owner, admin
✅ Fotos del proyecto (SitePhoto)
✅ Floor plans con pins

❌ NO ve: Datos internos de nómina
❌ NO ve: Costos de labor
❌ NO ve: Reportes financieros internos
❌ NO ve: Earned Value Management (solo para admin/PM)
```

**Permisos configurables:**
```python
# Cliente solo lectura
access = ClientProjectAccess.objects.create(
    user=client_user,
    project=project,
    role='viewer',
    can_comment=False,      # Solo ver, no comentar
    can_create_tasks=False  # No puede crear tareas
)

# Cliente full access
access = ClientProjectAccess.objects.create(
    user=client_user,
    project=project,
    role='client',
    can_comment=True,       # Puede comentar
    can_create_tasks=True   # Puede crear solicitudes
)

# PM externo
access = ClientProjectAccess.objects.create(
    user=external_pm,
    project=project,
    role='external_pm',
    can_comment=True,
    can_create_tasks=True
)
```

**UI Mockup (Admin asignando acceso):**
```
┌──────────────────────────────────────────────┐
│ 🔐 Manage Client Access - Project Alpha      │
├──────────────────────────────────────────────┤
│ Client: john.doe@email.com                   │
│                                              │
│ Role:                                        │
│ (●) Client - Full project visibility         │
│ ( ) External PM - Can manage activities      │
│ ( ) Viewer - Read-only access               │
│                                              │
│ Permissions:                                 │
│ ☑ Can comment on project                    │
│ ☑ Can create tasks/requests                 │
│                                              │
│ [Grant Access] [Cancel]                      │
└──────────────────────────────────────────────┘
```

---

### 📌 FUNCIÓN 24.4 - Root Redirect & Dashboard Routing

**Vista:** `root_redirect` (línea 2383)

**Propósito:** Redirigir automáticamente según rol del usuario.

**Lógica:**
```python
def root_redirect(request):
    # Según rol definido en Profile
    profile = getattr(request.user, 'profile', None)
    role = getattr(profile, "role", "employee")
    
    if role == "admin":
        return redirect('dashboard_admin')
    elif role == "project_manager":
        return redirect('dashboard_pm')
    elif role == "employee":
        return redirect('dashboard_employee')
    elif role == "client":
        return redirect('dashboard_client')
    elif role == "designer":
        return redirect('dashboard_designer')
    elif role == "superintendent":
        return redirect('dashboard_superintendent')
    else:
        return redirect('dashboard')
```

---

## 📊 **MÓDULO 25: EXPORT & REPORTING** (7/7 COMPLETO)

### 📌 FUNCIÓN 25.1 - PDF Reporte de Proyecto

**Vista:** `project_pdf_view` (línea 438)
**Template:** `core/templates/core/project_pdf.html`

**Propósito:** Generar PDF ejecutivo con métricas del proyecto para análisis interno.

**Uso:** Solo admin/PM (reportes internos para medir rendimiento del equipo y empresa)

**Generación PDF:**
```python
from xhtml2pdf import pisa

template = get_template("core/project_pdf.html")
html = template.render(context)
result = BytesIO()
pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)

if not pdf.err:
    return HttpResponse(result.getvalue(), content_type="application/pdf")
```

---

### 📌 FUNCIÓN 25.2 - PDF Factura (Invoice)

**Vista:** `invoice_pdf` (línea 2015)
**Template:** `core/templates/core/invoice_pdf.html`

**Propósito:** Generar factura profesional con logo de Kibray para descarga.

**Incluye:**
- Logo de Kibray (customizable)
- Información de la empresa
- Detalles del cliente
- InvoiceLines (descripción + monto)
- Total calculado
- Payment terms

**Descarga:**
```html
<a href="{% url 'invoice_pdf' pk=invoice.pk %}" target="_blank">
    📥 Descargar PDF
</a>
```

---

### 📌 FUNCIÓN 25.3 - Exportación iCal (Calendar Sync)

**Servicio:** `core/services/calendar_sync.py`
**Endpoint:** `project_schedule_ics` (línea 4724)

**Propósito:** Suscripción al cronograma del proyecto desde cualquier calendario (Google, Outlook, Apple).

**Función:** `generate_ical_for_project`

**Características:**
- Incluye TODOS los schedule items (no solo el primero)
- Auto-actualización cuando se edita el schedule
- Colores por estado (green=DONE, blue=IN_PROGRESS, red=BLOCKED)
- Categorías y metadata
- Compatible con todos los clientes de calendario

**Actualización automática:**
```
PM edita ScheduleItem en Gantt → API bulk_update → DB update
                                        ↓
                     Cliente con calendar suscrito recibe update automático
                     (próximo refresh del calendario, usualmente cada 30 min)
```

---

### 📌 FUNCIÓN 25.4 - Exportación CSV (Earned Value)

**Vista:** `project_ev_csv` (línea 2550)

**Propósito:** Exportar datos de EV para análisis en Excel o con AI.

**Columnas:**
```
Date,Baseline_Total,PV,EV,AC,SPI,CPI,Percent_Complete
```

**Uso para análisis con AI:**
```
1. Descargar CSV
2. Importar a Excel/Sheets
3. Conectar con ChatGPT/Claude: "Analiza tendencia y predice finalización"
4. Generar gráficos de tendencia
```

---

### 📌 FUNCIÓN 25.5 - CSV Template para Progreso

**Vista:** `download_progress_sample` (línea 2604)

**Propósito:** Template CSV que PM llena offline y sube con `upload_project_progress`.

**Template:**
```csv
BudgetLine_ID,Date,Percent_Complete,Notes
1,2025-04-15,25.5,"Preparación completada"
2,2025-04-15,10.0,"Iniciando pintura exterior"
```

---

### 📌 FUNCIÓN 25.6 - Exportación CSV (Progreso)

**Vista:** `project_progress_csv` (línea 2817)

**Columnas:**
```
BudgetLine,Code,Description,Baseline,Date,Percent,Notes
```

---

### 📌 FUNCIÓN 25.7 - Vista Gantt React

**Vista:** `schedule_gantt_react_view` (línea 4762)

**Características:**
```
✅ Drag-and-drop para reordenar items
✅ Extender barras para cambiar duración
✅ Mover barras para cambiar fechas
✅ Crear dependencias visuales
✅ Editar in-line
✅ Zoom (día, semana, mes)
✅ Colores por estado
✅ Milestones como diamantes
```

**Integración con calendario:**
- Drag item en Gantt → API bulk_update
- ScheduleItem.planned_start/end actualizados
- iCal subscription regenerada automáticamente

---

## ⚙️ **MÓDULO 26: UTILITIES & ADVANCED FEATURES** (5/5 COMPLETO)

### 📌 FUNCIÓN 26.1 - Earned Value Management

**Servicio:** `core/services/earned_value.py`

**Cálculo en tiempo real:**
```
✅ Se calcula cada día después del clock out
✅ Día de trabajo cerrado → PayrollEntry/TimeEntry completos
✅ Dashboard actualiza inmediatamente
```

**Función 1: `line_planned_percent`**
```python
def line_planned_percent(line, as_of: date) -> Decimal:
    """Interpolación lineal de progreso planeado"""
    if as_of <= line.planned_start:
        return Decimal('0')
    if as_of >= line.planned_finish:
        return Decimal('1')
    
    total_days = (line.planned_finish - line.planned_start).days
    done_days = (as_of - line.planned_start).days
    return Decimal(done_days) / Decimal(total_days)
```

**Función 2: `compute_project_ev`**
```python
def compute_project_ev(project, as_of=None):
    """
    PV: Planned Value (cuánto deberíamos haber gastado)
    EV: Earned Value (cuánto trabajo completamos)
    AC: Actual Cost (cuánto gastamos realmente)
    SPI: Schedule Performance Index (EV/PV)
    CPI: Cost Performance Index (EV/AC)
    """
    # ... cálculos detallados
    
    return {
        'PV': PV,
        'EV': EV,
        'AC': AC,
        'SPI': SPI,  # > 1.0 = adelante | < 1.0 = atrasado
        'CPI': CPI,  # > 1.0 = bajo presupuesto | < 1.0 = sobre presupuesto
        'percent_complete_cost': percent_complete
    }
```

---

### 📌 FUNCIÓN 26.2 - Schedule Generator

**Vista:** `_generate_schedule_from_estimate` (línea 4569)

**Propósito:** Auto-crear cronograma desde estimate aprobado.

**Proceso:**
```
Estimate categorías → ScheduleCategory → ScheduleItem placeholder
                              ↓
                      PM agrega subcategorías/tareas
```

**Ejemplo:**
```
Estimate: "Interior Painting" ($15,000)
    ↓
Schedule Category: "Interior Painting"
    ↓
PM agrega 10 subcategorías:
  - Master Bedroom
  - Guest Bedroom 1
  - Guest Bedroom 2
  - Living Room
  - Kitchen
  - Bathrooms
  - etc.
```

---

### 📌 FUNCIÓN 26.3-26.5 - Helper Utilities

**Helpers:**
1. `_is_staffish`: Verifica si usuario es staff/PM
2. `staff_required` decorator: Restricción de acceso
3. `_ensure_inventory_item`: Auto-crear items sin duplicados
4. `_parse_date`: Parser robusto de fechas
5. `_ensure_default_channels`: Auto-crear canales de chat

---

## 🎯 **MÓDULO 27: REST API** (8/8 COMPLETO)

### API Endpoints Disponibles

**27.1 Notifications API:**
- GET `/api/notifications/` - Lista notificaciones
- POST `/api/notifications/mark_all_read/`
- POST `/api/notifications/{id}/mark_read/`
- GET `/api/notifications/count_unread/`

**27.2 Chat API:**
- GET `/api/chat/channels/` - Canales del usuario
- GET `/api/chat/messages/?channel={id}`
- POST `/api/chat/messages/` - Enviar mensaje

**27.3 Tasks API:**
- GET `/api/tasks/?touchup=true` - Filtrar touch-ups
- GET `/api/tasks/?assigned_to_me=true`
- POST `/api/tasks/{id}/update_status/`

**27.4 Quality Control API:**
- GET `/api/damage-reports/`
- POST `/api/damage-reports/`

**27.5 Floor Plans API:**
- GET `/api/floor-plans/` - Con pins prefetch
- GET `/api/pins/?plan={id}`

**27.6 Color Samples API:**
- GET `/api/color-samples/`

**27.7 Projects API:**
- GET `/api/projects/`

**27.8 Schedule API:**
- GET `/api/schedule/categories/?project={id}`
- GET `/api/schedule/items/?project={id}`
- POST `/api/schedule/items/bulk_update/` - Drag-and-drop en Gantt

**Uso:**
- Frontend React/Vue
- Mobile app futura
- Integraciones externas

---

**TOTAL MÓDULOS 24-27: 24 funciones documentadas**

**GRAN TOTAL DOCUMENTACIÓN: 183 + 24 = 207 funciones (83% del sistema)**
