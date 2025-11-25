# core/signals.py
"""
Señales para Task, TaskImage, TaskStatusChange.
Implementa Q11.10 (notificaciones) y versionado automático de imágenes.
"""

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model

User = get_user_model()


# ============================================================================
# TASK STATUS CHANGE AUTO-TRACKING
# ============================================================================

@receiver(pre_save, sender='core.Task')
def track_task_status_change(sender, instance, **kwargs):
    """
    Crea TaskStatusChange cuando cambia el status de una tarea.
    Se ejecuta antes de guardar para capturar el valor anterior.
    """
    if not instance.pk:
        # Es una nueva tarea, no hay cambio de status
        return
    
    try:
        # Obtener el valor anterior del status
        from core.models import Task
        old_task = Task.objects.get(pk=instance.pk)
        
        if old_task.status != instance.status:
            # Guardar el cambio en el contexto de la instancia
            # para procesar en post_save
            instance._status_changed = True
            instance._old_status = old_task.status
    except Task.DoesNotExist:
        pass


@receiver(post_save, sender='core.Task')
def create_task_status_change(sender, instance, created, **kwargs):
    """
    Crea registro de TaskStatusChange después de guardar.
    Ejecuta notificaciones según Q11.10.
    """
    from core.models import TaskStatusChange
    
    # Solo procesar si hubo cambio de status (marcado en pre_save)
    if not hasattr(instance, '_status_changed'):
        return
    
    if not instance._status_changed:
        return
    
    # Verificar que _old_status existe
    if not hasattr(instance, '_old_status'):
        return
    
    # Crear registro de cambio
    TaskStatusChange.objects.create(
        task=instance,
        old_status=instance._old_status,
        new_status=instance.status,
        changed_by=getattr(instance, '_changed_by', None),  # Usuario que hizo el cambio
        notes=getattr(instance, '_change_notes', '')
    )
    
    # Guardar old_status para notificaciones antes de limpiar
    old_status_value = instance._old_status
    
    # Limpiar flags temporales
    delattr(instance, '_status_changed')
    delattr(instance, '_old_status')
    
    # ========================================
    # NOTIFICACIONES (Q11.10)
    # ========================================
    # Notificar al creador de la tarea + PM del proyecto
    send_task_status_notification(instance, old_status_value, instance.status)


def send_task_status_notification(task, old_status, new_status):
    """
    Envía notificaciones cuando cambia el status de una tarea.
    Q11.10: "Notificar al creador de la tarea y al PM del proyecto"
    """
    from core.models import Notification
    
    recipients = set()
    
    # 1. Creador de la tarea
    if task.created_by:
        recipients.add(task.created_by)
    
    # 2. Usuario asignado (si existe y tiene user vinculado)
    if task.assigned_to and hasattr(task.assigned_to, 'user') and task.assigned_to.user:
        recipients.add(task.assigned_to.user)
    
    # 3. PMs del proyecto (usuarios con perfil project_manager relacionados al proyecto)
    # Por ahora omitimos esta funcionalidad hasta tener la relación explícita
    # TODO: Agregar cuando se implemente Project.manager o Project.team_members
    
    # Crear notificación para cada destinatario
    for user in recipients:
        # No notificar al usuario que hizo el cambio
        changed_by = getattr(task, '_changed_by', None)
        if user == changed_by:
            continue
        
        # Determinar el tipo de notificación según el nuevo status
        if new_status == 'Completada':
            notif_type = 'task_completed'
        else:
            notif_type = 'task_assigned'  # Usar el tipo más cercano disponible
        
        Notification.objects.create(
            user=user,
            notification_type=notif_type,
            title=_('Cambio de Status: {}').format(task.title),
            message=_('La tarea "{}" cambió de {} a {}').format(
                task.title,
                old_status,
                new_status
            ),
            link_url=f'/task/{task.pk}/',
            related_object_type='Task',
            related_object_id=task.pk
        )


# ============================================================================
# TASK IMAGE VERSIONING
# ============================================================================

@receiver(post_save, sender='core.TaskImage')
def handle_task_image_versioning(sender, instance, created, **kwargs):
    """
    Maneja el versionado de imágenes de tareas.
    Cuando se sube una nueva imagen, marca las anteriores como is_current=False.
    """
    if not created:
        # Solo procesar imágenes nuevas
        return
    
    from core.models import TaskImage
    
    # Marcar todas las otras imágenes de esta tarea como no-current
    TaskImage.objects.filter(
        task=instance.task
    ).exclude(
        pk=instance.pk
    ).update(
        is_current=False
    )
    
    # Asegurar que la nueva imagen es current
    if not instance.is_current:
        instance.is_current = True
        instance.save(update_fields=['is_current'])


# ============================================================================
# TASK TIME TRACKING AUTO-STATUS
# ============================================================================

@receiver(pre_save, sender='core.Task')
def auto_status_on_time_tracking(sender, instance, **kwargs):
    """
    Cambia automáticamente el status a 'En Progreso' cuando se inicia time tracking.
    Q11.13: "Cuando se inicia el tracking, cambiar status a 'En Progreso'"
    """
    # Solo procesar si started_at cambió (se inició tracking)
    if not instance.pk:
        return
    
    try:
        from core.models import Task
        old_task = Task.objects.get(pk=instance.pk)
        
        # Si se acaba de iniciar tracking y no está en progreso
        if not old_task.started_at and instance.started_at:
            if instance.status != 'En Progreso':
                instance.status = 'En Progreso'
                instance._status_changed = True
                instance._old_status = old_task.status
    except Task.DoesNotExist:
        pass


# ============================================================================
# TASK DEPENDENCY VALIDATION
# ============================================================================

@receiver(pre_save, sender='core.Task')
def validate_task_dependencies(sender, instance, **kwargs):
    """
    Valida que no haya dependencias circulares.
    Ejecuta full_clean() que incluye Task.clean().
    """
    # Ya implementado en Task.clean() + Task.save()
    # Este signal es redundante pero se mantiene por claridad
    pass
