# MÓDULO 11: Tasks - Implementación Completa

## 📋 Resumen Ejecutivo

El Módulo 11 extiende el sistema de tareas con funcionalidades avanzadas:
- ✅ Priorización (Alta/Media/Baja/Urgente)
- ✅ Dependencias entre tareas (prerequisitos)
- ✅ Fechas límite opcionales
- ✅ Versionado de imágenes
- ✅ Histórico de cambios de estado
- ✅ Time tracking integrado
- ✅ Reapertura de tareas completadas

## 🏗️ Arquitectura

### Modelos Principales

#### Task (core/models.py)
```python
class Task:
    # Campos base
    title: str
    description: str
    status: str  # Pendiente, En Progreso, Completada, Cancelada
    priority: str  # low, medium, high, urgent
    due_date: DateField  # opcional
    
    # Relaciones
    project: ForeignKey(Project)
    assigned_to: ForeignKey(Employee)
    created_by: ForeignKey(User)
    dependencies: ManyToManyField('self')  # Tareas prerequisito
    
    # Time tracking
    started_at: DateTimeField
    time_tracked_seconds: int
    
    # Propiedades computadas
    @property
    def total_hours -> float
    @property
    def reopen_events_count -> int
    
    # Métodos principales
    def can_start() -> bool
    def start_tracking() -> bool
    def stop_tracking() -> int
    def reopen(user, notes) -> bool
    def add_image(file, user, caption) -> TaskImage
```

#### TaskImage (Versionado)
```python
class TaskImage:
    task: ForeignKey(Task)
    image: ImageField
    caption: str
    uploaded_by: ForeignKey(User)
    version: int  # Auto-incrementa
    is_current: bool  # Solo una imagen es_current=True
    uploaded_at: DateTimeField
```

#### TaskStatusChange (Auditoría)
```python
class TaskStatusChange:
    task: ForeignKey(Task)
    old_status: str
    new_status: str
    changed_by: ForeignKey(User)
    changed_at: DateTimeField
    notes: str
```

#### TimeEntry (Integración)
```python
class TimeEntry:
    # Nuevo campo añadido (migración 0077)
    task: ForeignKey(Task)  # Vincular horas registradas a tarea
```

---

## 🔌 API Endpoints

Base URL: `/api/v1/tasks/`

### 1. Gestión de Dependencias

#### Agregar Dependencia
```http
POST /api/v1/tasks/{task_id}/add_dependency/
Content-Type: application/json

{
  "dependency_id": 42
}
```

**Respuesta:**
```json
{
  "status": "ok",
  "dependencies": [42, 15, 8]
}
```

**Errores:**
- 400: Dependencia circular detectada
- 400: La tarea no puede depender de sí misma
- 404: Tarea dependencia no encontrada

#### Remover Dependencia
```http
POST /api/v1/tasks/{task_id}/remove_dependency/
Content-Type: application/json

{
  "dependency_id": 42
}
```

---

### 2. Reapertura de Tareas

```http
POST /api/v1/tasks/{task_id}/reopen/
Content-Type: application/json

{
  "notes": "Cliente solicitó correcciones adicionales"
}
```

**Respuesta:**
```json
{
  "status": "ok",
  "new_status": "En Progreso",
  "reopen_events_count": 2
}
```

**Requisitos:**
- La tarea debe estar en estado `Completada`
- Se registra automáticamente en `TaskStatusChange`
- Limpia `completed_at`
- Notifica a PMs y asignado

---

### 3. Time Tracking

#### Iniciar Tracking
```http
POST /api/v1/tasks/{task_id}/start_tracking/
```

**Respuesta:**
```json
{
  "status": "ok",
  "started_at": "2025-11-25T14:30:00Z"
}
```

**Requisitos:**
- Dependencias deben estar completadas (`can_start()`)
- No aplica para touch-ups (`is_touchup=False`)
- Cambia estado a `En Progreso`

#### Detener Tracking
```http
POST /api/v1/tasks/{task_id}/stop_tracking/
```

**Respuesta:**
```json
{
  "status": "ok",
  "elapsed_seconds": 3600,
  "time_tracked_seconds": 7200,
  "time_tracked_hours": 2.0
}
```

---

### 4. Resumen de Horas

```http
GET /api/v1/tasks/{task_id}/hours_summary/
```

**Respuesta:**
```json
{
  "task_id": 123,
  "title": "Pintar habitación principal",
  "time_tracked_hours": 2.5,
  "time_entries_hours": 8.0,
  "total_hours": 10.5
}
```

**Cálculo:**
- `time_tracked_hours`: Horas internas (start/stop tracking)
- `time_entries_hours`: Suma de `TimeEntry` vinculados
- `total_hours`: Suma total combinada

---

### 5. Subir Imagen Versionada

```http
POST /api/v1/tasks/{task_id}/add_image/
Content-Type: multipart/form-data

image: [archivo]
caption: "Avance día 3 - Primer coat aplicado"
```

**Respuesta:**
```json
{
  "status": "ok",
  "image_id": 456,
  "version": 2
}
```

**Versionado Automático:**
- Primera imagen → version=1
- Segunda imagen → version=2, marca anterior como `is_current=False`
- Mantiene histórico completo

---

## 📊 Serializer Extendido

`TaskSerializer` incluye ahora:

```json
{
  "id": 123,
  "title": "Pintar habitación",
  "description": "...",
  "project": 5,
  "project_name": "Casa Johnson",
  "assigned_to": 10,
  "assigned_to_name": "Juan Pérez",
  "status": "En Progreso",
  "priority": "high",
  "due_date": "2025-11-30",
  "is_touchup": false,
  "created_at": "2025-11-20T10:00:00Z",
  "started_at": "2025-11-25T08:30:00Z",
  "time_tracked_seconds": 9000,
  "time_tracked_hours": 2.5,
  "total_hours": 10.5,
  "dependencies_ids": [42, 15],
  "reopen_events_count": 1
}
```

---

## 🧪 Tests

Ubicación: `tests/test_module11_tasks_api.py`

### Suite Completa (5 tests)

```python
class TestModule11TaskAPI:
    def test_add_and_remove_dependency()
    def test_reopen_creates_status_change()
    def test_start_and_stop_tracking()
    def test_hours_summary()
    def test_add_image_versioning()
```

**Ejecutar:**
```bash
python -m pytest tests/test_module11_tasks_api.py -v
```

**Resultado:**
```
✅ 5 passed in 7.70s
```

---

## 🔄 Migraciones

### 0077_timeentry_task.py
```python
# Añade campo task a TimeEntry
operations = [
    migrations.AddField(
        model_name='timeentry',
        name='task',
        field=models.ForeignKey(
            blank=True, null=True,
            on_delete=django.db.models.deletion.SET_NULL,
            related_name='time_entries',
            to='core.task'
        ),
    ),
]
```

**Aplicar:**
```bash
python manage.py migrate
```

---

## 🚀 Casos de Uso

### Caso 1: Crear tarea con dependencias
```python
# Crear tareas
prep = Task.objects.create(project=proj, title="Preparar superficie")
paint = Task.objects.create(project=proj, title="Aplicar pintura")

# Establecer dependencia (pintar depende de preparar)
paint.dependencies.add(prep)

# Validar antes de empezar
if paint.can_start():
    paint.start_tracking()
else:
    print("Dependencias incompletas")
```

### Caso 2: Tracking de tiempo completo
```python
# Iniciar trabajo
task.start_tracking()

# ... trabajo en progreso ...

# Detener y obtener resumen
task.stop_tracking()
summary = task.total_hours  # incluye TimeEntry + tracking interno
```

### Caso 3: Reabrir tarea con historial
```python
completed_task = Task.objects.get(id=123)
completed_task.reopen(user=pm_user, notes="Encontrado defecto")

# Verificar historial
changes = completed_task.status_changes.all()
# [Pendiente→En Progreso, En Progreso→Completada, Completada→En Progreso]
```

### Caso 4: Subir múltiples versiones de imagen
```python
# Primera foto (before)
v1 = task.add_image(before_photo, user, "Antes de comenzar")
# v1.version = 1, v1.is_current = True

# Segunda foto (after)
v2 = task.add_image(after_photo, user, "Trabajo terminado")
# v2.version = 2, v2.is_current = True
# v1.is_current = False (automático)

# Consultar histórico
all_versions = task.images.all().order_by('version')
current = task.images.filter(is_current=True).first()
```

---

## 🔐 Validaciones

### Dependencias Circulares
```python
# BLOQUEADO: A → B → A
taskA.dependencies.add(taskB)
taskB.dependencies.add(taskA)  # ValidationError
```

### Auto-dependencia
```python
# BLOQUEADO: A → A
task.dependencies.add(task)  # ValidationError
```

### Reopen sin completar
```python
# BLOQUEADO: solo Completada puede reabrirse
pending_task.reopen()  # Returns False
```

---

## 📈 Métricas y Propiedades

### total_hours
Suma de:
1. `time_tracked_seconds / 3600` (tracking interno)
2. Suma de `hours_worked` de TimeEntry vinculados

### reopen_events_count
Cuenta de veces que la tarea cambió de `Completada` a otro estado.

### can_start()
Verifica que todas las tareas en `dependencies` tengan `status='Completada'`.

---

## 🎯 Próximos Pasos (Fase 2 continuación)

1. ✅ **Módulo 11 COMPLETO**
2. ⏳ **Módulo 29**: Pre-Task Library (fuzzy search ampliado)
3. ⏳ **Módulo 12**: Daily Plans (integración con templates)
4. ⏳ **Módulo 30**: Weather Integration (auto-population)
5. ⏳ **Módulo 28**: Touch-Up Board (kanban separado)

---

## 📝 Notas Técnicas

### Índices de BD
```python
indexes = [
    models.Index(fields=['project', 'status']),
    models.Index(fields=['assigned_to', 'status']),
    models.Index(fields=['is_touchup']),
    models.Index(fields=['due_date']),
    models.Index(fields=['priority', 'status']),
]
```

### Signals
- `TaskStatusChange` se registra automáticamente al cambiar estado
- Notificaciones se envían a asignados y PMs
- `_current_user` se guarda temporalmente para auditoría

### Performance
- `select_related('project', 'assigned_to')` en queries
- `prefetch_related('dependencies', 'images')` para relaciones múltiples
- Cache de `total_hours` recomendado para reportes

---

**Fecha de Implementación:** 25 de Noviembre, 2025  
**Versión Django:** 4.2.26  
**Tests:** 5/5 PASAN ✅  
**Migración:** 0077 aplicada ✅
