# Arquitectura Cliente Multi-Proyecto - Implementación Completa

## 📐 Estructura Jerárquica Implementada

### Nivel 1: Dashboard General del Cliente
**Ruta:** `/dashboard/client/` (nombre: `dashboard_client`)  
**Vista:** `dashboard_client`  
**Template:** `core/templates/core/dashboard_client.html`

**Propósito:**
- Pantalla de entrada para todos los clientes
- Muestra TODOS los proyectos del cliente
- Vista tipo "portafolio" con cards visuales por proyecto
- Métricas generales: progreso, invoices, fotos recientes

**Casos de Uso:**
1. **New West (Compañía con múltiples PMs)**
   - PM Zach ve solo "Proyecto A" (filtrado por `project.client == username`)
   - PM Jon ve solo "Proyecto B" (filtrado por `project.client == username`)
   - Cada PM tiene su propio usuario con `project.client` apuntando a su username

2. **Ivan Stanley (Dueño con 3 proyectos)**
   - Ve los 3 proyectos en un dashboard
   - Puede seleccionar cualquiera para ver detalles

**Contenido por Proyecto:**
- Card con header gradient (progreso visual)
- 6 fotos recientes en galería
- Próximo evento en schedule
- 5 facturas recientes con balance
- 5 solicitudes del cliente más recientes
- Botones de acción:
  - "Ver Detalles" → `client_project_view` (dashboard completo del proyecto)
  - "Galería" → `site_photo_list`
  - "Minutas" → `project_minutes_list`
  - "Solicitudes" → `client_requests_list`

---

### Nivel 2: Dashboard Individual del Proyecto
**Ruta:** `/proyecto/<int:project_id>/` (nombre: `client_project_view`)  
**Vista:** `client_project_view`  
**Template:** `core/templates/core/client_project_view.html`

**Propósito:**
- Dashboard COMPLETO de UN proyecto específico
- **Es como una página separada con todas las funciones necesarias**
- El cliente gestiona todo lo relacionado a ESE proyecto aquí
- Breadcrumbs: Mis Proyectos > Nombre del Proyecto

**Control de Acceso:**
```python
# Verificar que project.client == request.user.username
# O que el usuario sea staff (PM/Admin puede ver)
```

**Secciones Implementadas:**

#### A) Header con Progreso
- Nombre del proyecto con gradient background
- Dirección completa
- Fechas (inicio - fin)
- Porcentaje de progreso con barra visual

#### B) Notificaciones Pendientes
- Alert amarillo si hay solicitudes sin responder
- Link directo a la sección de solicitudes

#### C) Métricas Financieras (3 cards)
1. Total Facturado
2. Total Pagado
3. Balance Pendiente

#### D) **Solicitudes / Touch-ups** ⭐ NUEVO
- Lista de tareas pendientes con:
  - Título y descripción
  - Fecha de creación
  - Estado (Pendiente, En Progreso, Completada)
  - Empleado asignado (si aplica)
  - Foto adjunta (si existe)
- Lista de tareas completadas recientes
- Botón "Nueva Solicitud" → Modal para crear

**Flujo de Touch-ups:**
1. Cliente toma foto del área con problemas
2. Cliente crea tarea con título, descripción, y foto
3. Sistema guarda `Task` con `created_by=cliente`, `status='Pendiente'`, `image=foto`
4. PM recibe notificación (TODO: implementar)
5. PM asigna tarea a empleado: `task.assigned_to = employee`
6. Empleado completa trabajo: `task.status = 'Completada'`, `task.completed_at = now()`
7. Cliente recibe notificación (TODO: implementar)

#### E) Minutas del Proyecto
- Timeline visual de las 10 minutas más recientes
- Solo muestra minutas con `visible_to_client=True`
- Iconos según tipo de evento
- Link a vista completa de minutas

#### F) Próximos Eventos (Schedule)
- 5 próximos eventos programados
- Fecha, hora, título, descripción
- Icono de reloj para cada evento

#### G) Fotos Recientes
- Grid 4x3 de las 12 fotos más recientes
- Thumbnails con hover effect
- Link a galería completa

#### H) Facturas
- Tabla completa con todas las facturas
- Columnas: Número, Fecha, Monto, Pagado, Balance, Estado
- Badges de colores según estado de pago
- Botón "Ver" para cada factura

#### I) Comentarios
- Lista de todos los comentarios con avatares
- Imágenes adjuntas (si existen)
- Relacionados con tareas específicas (si aplica)
- Botón "Nuevo Comentario" → Modal

**Modales Implementados:**

1. **Modal: Nueva Tarea/Touch-up**
   ```html
   <form method="post" action="{% url 'agregar_tarea' project.id %}" enctype="multipart/form-data">
     - Campo: Título (requerido)
     - Campo: Descripción (opcional)
     - Campo: Foto (opcional, accept="image/*")
     - Tip: Menciona usar tape azul como referencia
   </form>
   ```

2. **Modal: Nuevo Comentario**
   ```html
   <form method="post" action="{% url 'agregar_comentario' project.id %}" enctype="multipart/form-data">
     - Campo: Texto (requerido)
     - Campo: Imagen (opcional)
   </form>
   ```

---

## 🔐 Sistema de Permisos Implementado

### Verificación en `client_project_view`:
```python
profile = getattr(request.user, 'profile', None)
if profile and profile.role == 'client':
    # Cliente debe ser el dueño del proyecto
    if project.client != request.user.username:
        messages.error(request, "No tienes acceso a este proyecto.")
        return redirect('dashboard_client')
elif not request.user.is_staff:
    # Si no es cliente ni staff, denegar
    messages.error(request, "Acceso denegado.")
    return redirect('dashboard')
# Staff (PM/Admin) siempre puede ver
```

### Verificación en `agregar_tarea` y `agregar_comentario`:
```python
# Mismo sistema de permisos
# Cliente solo puede crear tareas en SUS proyectos
# Staff puede crear en cualquier proyecto
```

---

## 📊 Modelos Actualizados

### Task Model (Mejorado)
```python
class Task(models.Model):
    project = ForeignKey(Project, related_name='tasks')
    title = CharField(max_length=200)
    description = TextField(blank=True)
    status = CharField(choices=[...])  # Pendiente, En Progreso, Completada, Cancelada
    created_by = ForeignKey(User, related_name='created_tasks')  # ⭐ NUEVO
    assigned_to = ForeignKey(Employee, related_name='assigned_tasks')  # ⭐ NUEVO
    created_at = DateTimeField(auto_now_add=True)  # ⭐ NUEVO
    completed_at = DateTimeField(null=True, blank=True)  # ⭐ NUEVO
    image = ImageField(upload_to="tasks/", blank=True, null=True)  # ⭐ NUEVO
```

### Comment Model (Mejorado)
```python
class Comment(models.Model):
    project = ForeignKey(Project, related_name='comments')
    user = ForeignKey(User)
    text = TextField(blank=True)  # Ahora opcional si hay imagen
    image = ImageField(upload_to="comments/", blank=True, null=True)
    created_at = DateTimeField(auto_now_add=True)
    task = ForeignKey(Task, related_name='comments')  # ⭐ NUEVO - Relacionar con tarea
```

**Migración:** `core/migrations/0042_*.py` - APLICADA ✅

---

## 🎯 Floating Action Button (FAB) Actualizado

### Cambio Implementado:
```django
{% if user.is_authenticated and user.is_staff and project %}
<!-- FAB solo visible cuando hay contexto de proyecto -->
<div class="fab-container">
  <a href="{% url 'project_minute_create' project.id %}">Nueva Minuta</a>
  <a href="{% url 'changeorder_create' %}">Nuevo CO</a>
  <a href="{% url 'materials_request' project.id %}">Solicitar Materiales</a>
</div>
{% endif %}
```

**Vistas con FAB disponible:**
- `project_overview` ✅ (ya tiene `project` en contexto)
- `client_project_view` ✅ (ya tiene `project` en contexto)
- `project_ev` ✅
- `project_profit_dashboard` ✅
- Cualquier vista que pase `project` al template

**Vistas SIN FAB:**
- `dashboard_admin` (no hay proyecto específico)
- `dashboard_pm` (no hay proyecto específico)
- `dashboard_client` (múltiples proyectos)
- `project_list` (listado, no detalle)

---

## 🔄 Flujos de Trabajo Implementados

### Flujo 1: Cliente New West - PM Zach (Solo Proyecto A)

1. **Login** → Usuario: `zach@newwest.com`
2. **Profile:** `role='client'`, Usuario vinculado a proyectos donde `project.client='zach@newwest.com'`
3. **Dashboard Cliente:** Ve solo "Proyecto A"
4. **Click "Ver Detalles"** → `client_project_view(project_id=A)`
5. **Ve Touch-up necesario** → Click "Nueva Solicitud"
6. **Modal abre:**
   - Título: "Pared principal con rayones"
   - Descripción: "Área marcada con tape azul"
   - Foto: [Sube imagen]
7. **Submit** → `agregar_tarea(project_id=A)`
8. **Task creada:**
   ```python
   Task(
       project=Proyecto_A,
       title="Pared principal con rayones",
       description="Área marcada con tape azul",
       status="Pendiente",
       created_by=zach_user,
       image=photo.jpg
   )
   ```
9. **Zach ve:** Tarea aparece en sección "Pendientes" con badge amarillo
10. **PM recibe notificación** (TODO)
11. **PM asigna:** `task.assigned_to = empleado_juan`
12. **Zach ve:** "Asignado a: Juan"
13. **Juan completa trabajo:** `task.status = 'Completada'`
14. **Zach ve:** Tarea movida a "Completadas Recientes" con badge verde

### Flujo 2: Cliente Ivan Stanley (3 Proyectos)

1. **Login** → Usuario: `ivan@stanleyhomes.com`
2. **Dashboard Cliente:** Ve 3 cards:
   - Proyecto Mountain View (70% progreso)
   - Proyecto Lakeside (45% progreso)
   - Proyecto Downtown (90% progreso)
3. **Click "Ver Detalles" en Mountain View** → `client_project_view(project_id=MV)`
4. **Ve dashboard completo de Mountain View:**
   - Solicitudes pendientes
   - Minutas del proyecto
   - Fotos recientes
   - Facturas
   - Comentarios
5. **Navega a Lakeside:**
   - Click breadcrumb "Mis Proyectos"
   - Ve los 3 proyectos nuevamente
   - Click "Ver Detalles" en Lakeside
6. **Dashboard de Lakeside** con su información específica

---

## 🧩 Integración con Sistemas Existentes

### 1. Sistema de Minutas
- `ProjectMinute` con `visible_to_client=True` aparece en timeline
- Cliente puede ver decisiones, cambios, milestones
- No puede crear minutas (solo PM/Admin)

### 2. Sistema de Facturas
- `Invoice` relacionadas con el proyecto
- Cliente ve estado de pago en tiempo real
- Puede descargar PDF desde `invoice_detail`

### 3. Sistema de Fotos
- `SitePhoto` del proyecto
- Cliente ve galería completa
- Puede navegar a `site_photo_list` para ver todas

### 4. Sistema de Schedule
- `Schedule` próximos eventos
- Cliente sabe cuándo esperar al equipo
- Puede ver calendario completo

### 5. Sistema de Change Orders (Indirecto)
- Cliente NO ve COs directamente en su dashboard
- Pero puede crear `ClientRequest` que PM convierte en CO
- Link a `client_requests_list` disponible

---

## 📱 Responsive Design

Todos los templates usan Bootstrap 5 con:
- Grid system `col-lg-6` para desktop, stack en mobile
- Cards con `shadow-sm` para profundidad visual
- Modales centrados con `modal-dialog`
- Botones adaptivos con `btn-sm` para mobile
- Imágenes con `img-fluid` y `object-fit: cover`

---

## ✅ Checklist de Funcionalidades

### Dashboard Cliente (Vista General) ✅
- [x] Lista todos los proyectos del cliente
- [x] Filtro por `project.client == username`
- [x] Cards con progreso visual (gradient header)
- [x] 6 fotos recientes por proyecto
- [x] Próximo evento en schedule
- [x] 5 facturas recientes con balance
- [x] 5 solicitudes más recientes
- [x] Botones de acción (Ver Detalles, Galería, Minutas, Solicitudes)

### Client Project View (Dashboard Individual) ✅
- [x] Breadcrumbs (Mis Proyectos > Proyecto)
- [x] Header con progreso y fechas
- [x] Notificaciones de solicitudes pendientes
- [x] Métricas financieras (3 cards)
- [x] Sección de solicitudes/touch-ups con modal
- [x] Timeline de minutas (solo visible_to_client)
- [x] Próximos eventos del schedule
- [x] Galería de fotos recientes
- [x] Tabla completa de facturas
- [x] Lista de comentarios con modal
- [x] Control de acceso por permisos

### Sistema de Touch-ups ✅
- [x] Modelo Task mejorado con campos nuevos
- [x] Cliente puede crear tareas con foto
- [x] PM puede asignar a empleado
- [x] Estado tracking (Pendiente → En Progreso → Completada)
- [x] Imagen directamente en Task (no solo en comentarios)
- [x] Relación task-comment para contexto

### Permisos y Seguridad ✅
- [x] Cliente solo ve SUS proyectos
- [x] Cliente solo crea tareas en SUS proyectos
- [x] Staff (PM/Admin) puede ver todos los proyectos
- [x] Validación en vistas con mensajes de error
- [x] Redirects apropiados según rol

### FAB (Floating Action Button) ✅
- [x] Solo visible con contexto de proyecto
- [x] Solo visible para staff
- [x] Rutas corregidas con project_id
- [x] Animaciones suaves (hover/focus)

---

## 🚀 Pendientes / Mejoras Futuras

### Alta Prioridad
1. **Sistema de Notificaciones**
   - [ ] Notificar PM cuando cliente crea tarea
   - [ ] Notificar cliente cuando tarea se completa
   - [ ] Badge de notificaciones en navigation
   - [ ] Emails automáticos

2. **Markup de Imágenes (Touch-ups Avanzado)**
   - [ ] Permitir dibujar/marcar en fotos
   - [ ] Flechas, círculos, texto en imágenes
   - [ ] Canvas HTML5 o librería como Fabric.js
   - [ ] Guardar imagen con markup

### Media Prioridad
3. **Dashboard Analytics**
   - [ ] Gráfico de progreso histórico
   - [ ] Timeline de pagos
   - [ ] Estadísticas de touch-ups (cuántos, tiempo promedio)

4. **Mobile App**
   - [ ] PWA para clientes
   - [ ] Capacidad de tomar fotos directamente
   - [ ] Push notifications

### Baja Prioridad
5. **Mejoras UX**
   - [ ] Filtros en tabla de facturas
   - [ ] Búsqueda en comentarios
   - [ ] Export PDF del dashboard completo
   - [ ] Dark mode

---

## 📝 Notas de Implementación

### Nombres de Rutas Estandarizados:
- `materials_request` (singular) - Crear nueva solicitud
- `materials_requests_list` (plural) - Listar todas
- `materials_request_detail` (singular) - Ver detalle
- **Consistente con convención REST**

### Templates Eliminados/Obsoletos:
- ❌ `core/templates/core/dashboard.html` - Reemplazado por redirects inteligentes
- ⚠️ Versión anterior de `client_project_view.html` - Reemplazada completamente

### Migraciones Aplicadas:
- `0042_alter_comment_options_alter_task_options_and_more.py` ✅
  - Task: added created_by, assigned_to, created_at, completed_at, image
  - Comment: added task relation, text now optional

---

## 🎯 Conclusión

La arquitectura implementada soporta completamente:

✅ **Múltiples compañías con múltiples PMs**
- Cada PM ve solo SUS proyectos (filtrado por username)
- Separación completa entre clientes

✅ **Un cliente con múltiples proyectos**
- Dashboard general muestra todos
- Dashboard individual por proyecto con funcionalidad completa

✅ **Sistema de touch-ups funcional**
- Cliente crea con foto
- PM asigna
- Tracking de estado

✅ **Jerarquía clara y sin confusión**
- Nivel 1: Vista general (portafolio)
- Nivel 2: Dashboard completo del proyecto (página funcional separada)

✅ **Navegación intuitiva**
- Breadcrumbs en todos lados
- Botones claros de acción
- Diseño moderno y responsive

**Sistema listo para producción.** 🚀

---

**Generado:** 2025-11-08  
**Python Check:** ✅ 0 errors  
**Migrations:** ✅ Applied (0042)  
**Status:** 🟢 Production Ready
