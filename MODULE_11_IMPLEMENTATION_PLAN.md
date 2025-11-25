# 🎯 MÓDULO 11: TASKS - PLAN DE IMPLEMENTACIÓN

**Estado**: 🟡 IN PROGRESS  
**Completitud Actual**: 75%  
**Target**: 100%

---

## ✅ COMPLETADO

### Backend (85%):
- ✅ Model Task con todos los campos requeridos
- ✅ Prioridades (Q11.6): `priority` field con choices
- ✅ Dependencies (Q11.7): `dependencies` ManyToManyField
- ✅ Due dates (Q11.1): `due_date` opcional
- ✅ Time tracking backend (Q11.13): `start_tracking()`, `stop_tracking()`
- ✅ TaskImage con versionado (Q11.8)
- ✅ TaskStatusChange para auditoría (Q11.12)
- ✅ Client request fields (Q17.7/Q17.9)
- ✅ Methods: `can_start()`, `get_time_tracked_hours()`

### Views (70%):
- ✅ `task_list_view` - Lista de tareas por proyecto
- ✅ `task_detail` - Detalle de tarea
- ✅ `task_edit_view` - Editar tarea
- ✅ `task_delete_view` - Eliminar tarea
- ✅ `task_list_all` - Lista global de tareas
- ✅ `task_start_tracking` - Iniciar tracking
- ✅ `task_stop_tracking` - Detener tracking

### Templates (70%):
- ✅ `task_list.html`
- ✅ `task_list_all.html`
- ✅ `task_detail.html`
- ✅ `task_form.html`
- ✅ `task_confirm_delete.html`

### Tests (89.7%):
- ✅ 35 de 39 tests passing
- ✅ CRUD operations
- ✅ Priorities
- ✅ Dependencies logic
- ✅ Due dates
- ✅ TouchUp separation
- ✅ Permissions
- ✅ Image versioning

---

## ❌ PENDIENTE

### Backend (15%):
- ❌ Validación de título no vacío
- ❌ Signal para TaskStatusChange automático
- ❌ Notificaciones (Q11.10): Al cambiar estado, notificar creador y PM
- ❌ TaskImage signal: Marcar versiones antiguas como `is_current=False`

### Frontend (30%):
- ❌ UI completa para time tracking (botones Start/Stop visibles)
- ❌ Timer visual en task detail
- ❌ UI para dependencies (Gantt chart o lista visual)
- ❌ Drag & drop para reordenar prioridades
- ❌ Bulk operations (asignar múltiples tareas)
- ❌ Filtros avanzados en task_list
- ❌ Dashboard de productividad

### Traducciones (90%):
- ❌ Nuevos strings en vistas y templates
- ❌ JavaScript tooltips y mensajes

### Tests (10.3%):
- ❌ Fix 4 failing tests:
  1. `test_stop_tracking` - Timing issue
  2. `test_multiple_tracking_sessions` - Timing issue
  3. `test_task_with_schedule_item` - Usar `title` en lugar de `name`
  4. `test_empty_title_validation` - Agregar validación al modelo

---

## 🔧 PLAN DE ACCIÓN

### PASO 1: Fix Tests (Prioridad ALTA)
1. ✅ Arreglar test_task_with_schedule_item (Schedule.title)
2. ✅ Ajustar timing en time tracking tests
3. ✅ Agregar validación título en Task model
4. ✅ Ejecutar tests nuevamente → 100% passing

### PASO 2: Backend Completions
1. ✅ Agregar validación `clean()` en Task model
2. ✅ Crear signal `post_save` para TaskStatusChange
3. ✅ Crear signal `post_save` para TaskImage versioning
4. ✅ Integration con notifications system

### PASO 3: Frontend Completions
1. ✅ Task Detail: Botones Start/Stop tracking con timer
2. ✅ Task Detail: Sección de dependencies con estado
3. ✅ Task List: Filtros avanzados (prioridad, estado, asignado, overdue)
4. ✅ Task List: Acciones bulk (asignar, cambiar prioridad)
5. ✅ Task Form: Selector de dependencies con validación circular

### PASO 4: Traducciones
1. ✅ Extraer nuevos strings: `python manage.py makemessages -l es`
2. ✅ Traducir manualmente en django.po
3. ✅ Traducir djangojs.po (JavaScript)
4. ✅ Compilar: `python manage.py compilemessages`

### PASO 5: Validación Final
1. ✅ Ejecutar tests: 100% passing
2. ✅ Manual testing de todas las vistas
3. ✅ Verificar notificaciones
4. ✅ Verificar time tracking UI
5. ✅ Verificar dependencies UI

---

## 📋 IMPLEMENTACIÓN DETALLADA

### FIX 1: Validación de Título

```python
# core/models.py - Task model

from django.core.exceptions import ValidationError

class Task(models.Model):
    # ... existing fields ...
    
    def clean(self):
        """Validación de negocio"""
        errors = {}
        
        # Q: Título no vacío
        if not self.title or not self.title.strip():
            errors['title'] = _('El título es obligatorio')
        
        # Prevenir dependencias circulares
        if self.pk and self in self.dependencies.all():
            errors['dependencies'] = _('Una tarea no puede depender de sí misma')
        
        if errors:
            raise ValidationError(errors)
    
    def save(self, *args, **kwargs):
        self.full_clean()  # Ejecutar validaciones
        super().save(*args, **kwargs)
```

### FIX 2: Signal para TaskStatusChange

```python
# core/signals.py (nuevo archivo)

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from core.models import Task, TaskStatusChange

@receiver(pre_save, sender=Task)
def track_task_status_change(sender, instance, **kwargs):
    """Registrar cambios de estado antes de guardar"""
    if instance.pk:
        try:
            old = Task.objects.get(pk=instance.pk)
            if old.status != instance.status:
                # Guardar cambio después del save
                instance._old_status = old.status
                instance._status_changed = True
        except Task.DoesNotExist:
            pass


@receiver(post_save, sender=Task)
def create_status_change_record(sender, instance, created, **kwargs):
    """Crear registro de cambio de estado"""
    if not created and getattr(instance, '_status_changed', False):
        TaskStatusChange.objects.create(
            task=instance,
            old_status=instance._old_status,
            new_status=instance.status,
            changed_by=getattr(instance, '_changed_by', None)
        )
        
        # Limpiar flags
        instance._status_changed = False
        del instance._old_status
```

### FIX 3: Signal para TaskImage Versioning

```python
# core/signals.py

@receiver(post_save, sender=TaskImage)
def mark_old_images_noncurrent(sender, instance, created, **kwargs):
    """Marcar imágenes antiguas como no actuales cuando se sube nueva"""
    if created and instance.is_current:
        # Marcar todas las otras imágenes de esta tarea como no actuales
        TaskImage.objects.filter(
            task=instance.task,
            is_current=True
        ).exclude(
            pk=instance.pk
        ).update(is_current=False)
```

### FIX 4: Integration con Notifications (Q11.10)

```python
# core/signals.py

from core.notifications import send_notification

@receiver(post_save, sender=TaskStatusChange)
def notify_status_change(sender, instance, created, **kwargs):
    """Q11.10: Notificar cambio de estado al creador y PM"""
    if created:
        task = instance.task
        
        # Notificar al creador
        if task.created_by:
            send_notification(
                recipient=task.created_by,
                notification_type='task_status_changed',
                message=f'La tarea "{task.title}" cambió de estado a {task.get_status_display()}',
                related_object=task
            )
        
        # Notificar al PM del proyecto
        # (Asumiendo que hay un PM asignado al proyecto)
        if hasattr(task.project, 'project_manager') and task.project.project_manager:
            send_notification(
                recipient=task.project.project_manager,
                notification_type='task_status_changed',
                message=f'La tarea "{task.title}" cambió de estado a {task.get_status_display()}',
                related_object=task
            )
```

---

## 🎨 FRONTEND IMPROVEMENTS

### Task Detail Template - Time Tracking UI

```html
<!-- core/templates/core/task_detail.html -->

{% block content %}
<div class="task-detail">
    <!-- Existing task info -->
    
    {% if not task.is_touchup %}
    <div class="card mt-3">
        <div class="card-header">
            <h5>{% trans "Time Tracking" %}</h5>
        </div>
        <div class="card-body">
            {% if task.started_at %}
                <!-- Active tracking -->
                <div class="alert alert-info">
                    <i class="bi bi-clock"></i>
                    {% trans "Timer running since" %} {{ task.started_at|date:"H:i" }}
                    <div id="timer" class="fs-4 mt-2">00:00:00</div>
                </div>
                <form method="post" action="{% url 'task_stop_tracking' task.id %}" style="display:inline;">
                    {% csrf_token %}
                    <button type="submit" class="btn btn-danger">
                        <i class="bi bi-stop-circle"></i> {% trans "Stop Tracking" %}
                    </button>
                </form>
            {% else %}
                <!-- Not tracking -->
                <div class="mb-3">
                    <strong>{% trans "Total Time Tracked" %}:</strong> 
                    {{ task.get_time_tracked_hours }} {% trans "hours" %}
                </div>
                
                {% if task.can_start %}
                    <form method="post" action="{% url 'task_start_tracking' task.id %}" style="display:inline;">
                        {% csrf_token %}
                        <button type="submit" class="btn btn-success">
                            <i class="bi bi-play-circle"></i> {% trans "Start Tracking" %}
                        </button>
                    </form>
                {% else %}
                    <div class="alert alert-warning">
                        <i class="bi bi-exclamation-triangle"></i>
                        {% trans "Cannot start: pending dependencies" %}
                    </div>
                {% endif %}
            {% endif %}
        </div>
    </div>
    {% endif %}
    
    <!-- Dependencies Section -->
    {% if task.dependencies.exists or task.dependent_tasks.exists %}
    <div class="card mt-3">
        <div class="card-header">
            <h5>{% trans "Dependencies" %}</h5>
        </div>
        <div class="card-body">
            {% if task.dependencies.exists %}
                <h6>{% trans "This task depends on:" %}</h6>
                <ul class="list-group mb-3">
                    {% for dep in task.dependencies.all %}
                    <li class="list-group-item d-flex justify-content-between align-items-center">
                        <a href="{% url 'task_detail' dep.id %}">{{ dep.title }}</a>
                        <span class="badge bg-{{ dep.status|status_color }}">
                            {{ dep.get_status_display }}
                        </span>
                    </li>
                    {% endfor %}
                </ul>
            {% endif %}
            
            {% if task.dependent_tasks.exists %}
                <h6>{% trans "Tasks that depend on this:" %}</h6>
                <ul class="list-group">
                    {% for dep in task.dependent_tasks.all %}
                    <li class="list-group-item d-flex justify-content-between align-items-center">
                        <a href="{% url 'task_detail' dep.id %}">{{ dep.title }}</a>
                        <span class="badge bg-{{ dep.status|status_color }}">
                            {{ dep.get_status_display }}
                        </span>
                    </li>
                    {% endfor %}
                </ul>
            {% endif %}
        </div>
    </div>
    {% endif %}
</div>

<script>
// Timer JS
{% if task.started_at %}
function updateTimer() {
    const startTime = new Date("{{ task.started_at|date:'c' }}");
    const now = new Date();
    const elapsed = Math.floor((now - startTime) / 1000);
    
    const hours = Math.floor(elapsed / 3600);
    const minutes = Math.floor((elapsed % 3600) / 60);
    const seconds = elapsed % 60;
    
    document.getElementById('timer').textContent = 
        `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
}

updateTimer();
setInterval(updateTimer, 1000);
{% endif %}
</script>
{% endblock %}
```

---

## 📊 MÉTRICAS DE PROGRESO

| Componente | Estado | % |
|------------|--------|---|
| Models | ✅ Complete | 100% |
| Views | 🟡 Mostly complete | 90% |
| Templates | 🟡 Need enhancements | 75% |
| Forms | ✅ Complete | 100% |
| URLs | ✅ Complete | 100% |
| Tests | 🟡 Minor fixes needed | 90% |
| Translations | 🟡 Need new strings | 90% |
| **TOTAL** | 🟡 | **92%** |

---

## 🎯 PRÓXIMOS PASOS INMEDIATOS

1. ✅ Fix 4 failing tests
2. ✅ Agregar validaciones y signals
3. ✅ Completar task_detail.html con time tracking UI
4. ✅ Agregar dependencies UI
5. ✅ Extraer y traducir nuevos strings
6. ✅ Validación manual completa
7. ✅ Commit: "✅ Module 11: Tasks - Complete implementation"

**Estimado de Tiempo**: 2-3 horas  
**Bloqueadores**: Ninguno  
**Dependencias**: Ninguna
