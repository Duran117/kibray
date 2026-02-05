"""Señales para tareas, imágenes y recalculo de progreso.

Responsabilidades:
 - Registrar cambios de estado (TaskStatusChange)
 - Establecer completed_at cuando estado pasa a Completada
 - Recalcular progreso de ScheduleItem al cambiar estado de una Task
 - Versionado de TaskImage: marcar anteriores como no actuales e incrementar versión
"""

import contextlib

from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.contrib.sessions.models import Session
from django.core.cache import cache
from django.db import models
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from core.models import Task, TaskImage, TaskStatusChange


# --- TASK STATUS CHANGE & PROGRESS ---
@receiver(pre_save, sender=Task)
def task_capture_old_status(sender, instance: Task, **kwargs):
    if instance.pk:
        try:
            old = Task.objects.get(pk=instance.pk)
            instance._old_status = old.status
        except Task.DoesNotExist:
            instance._old_status = None
    else:
        instance._old_status = None


@receiver(post_save, sender=Task)
def task_post_save(sender, instance: Task, created, **kwargs):
    getattr(instance, "_old_status", None)

    # Nota: La creación de TaskStatusChange se maneja en el receiver con dispatch_uid
    # create_task_status_change más abajo, para evitar duplicados. Aquí solo
    # mantenemos lógica de completed_at y recálculo de progreso.

    # Marcar fecha de completado
    if instance.status == "Completed" and instance.completed_at is None:
        # Evitar re-disparar señales y clobber de _old_status: usar update() directo
        Task.objects.filter(pk=instance.pk).update(completed_at=timezone.now())

    # Recalcular progreso del ScheduleItem si hay vínculo
    if instance.schedule_item:
        with contextlib.suppress(Exception):
            instance.schedule_item.recalculate_progress(save=True)


# --- TASK IMAGE VERSIONING ---
@receiver(post_save, sender=TaskImage)
def task_image_versioning(sender, instance: TaskImage, created, **kwargs):
    if not created:
        return
    # Obtener imágenes actuales previas
    previous = TaskImage.objects.filter(task=instance.task, is_current=True).exclude(pk=instance.pk)
    if previous.exists():
        # Incrementar versión basado en máximo anterior
        max_version = previous.aggregate(v=models.Max("version"))["v"] or 1
        instance.version = max_version + 1
        # Marcar anteriores como no actuales
        previous.update(is_current=False)
        instance.is_current = True
        instance.save(update_fields=["version", "is_current"])
    else:
        # Primera imagen de la tarea
        instance.version = 1
        instance.is_current = True
        instance.save(update_fields=["version", "is_current"])


# ============================================================================
# TASK STATUS CHANGE AUTO-TRACKING
# ============================================================================


@receiver(pre_save, sender="core.Task", dispatch_uid="track_task_changes_pre_save")
def track_task_changes(sender, instance, **kwargs):
    """
    Consolida todos los cambios pre-save para Task:
    1. Detecta cambios de status para crear TaskStatusChange
    2. Auto-status cuando se inicia time tracking
    3. Validación de dependencias
    """
    if not instance.pk:
        # Es una nueva tarea, no hay cambio de status ni tracking
        return

    try:
        # Obtener el valor anterior
        from core.models import Task

        old_task = Task.objects.get(pk=instance.pk)

        # ====================================
        # 1. TIME TRACKING AUTO-STATUS
        # ====================================
        # Si se acaba de iniciar tracking, cambiar status a 'In Progress'
        if not old_task.started_at and instance.started_at and instance.status != "In Progress":
            instance.status = "In Progress"

        # ====================================
        # 2. DETECT STATUS CHANGE
        # ====================================
        # Detectar si el status cambió (después de aplicar auto-status)
        if old_task.status != instance.status and (not getattr(instance, "_status_changed", False)):
            instance._status_changed = True
            instance._old_status = old_task.status

    except Task.DoesNotExist:
        pass


@receiver(post_save, sender="core.Task", dispatch_uid="create_task_status_change_post_save")
def create_task_status_change(sender, instance, created, **kwargs):
    """
    Crea registro de TaskStatusChange después de guardar.
    Ejecuta notificaciones según Q11.10.
    """

    # Solo procesar si hubo cambio de status (marcado en pre_save)
    if not hasattr(instance, "_status_changed"):
        return

    if not instance._status_changed:
        return

    # Verificar que _old_status existe
    if not hasattr(instance, "_old_status"):
        return

    # Prevenir ejecuciones duplicadas
    if hasattr(instance, "_status_change_processed"):
        return

    # Marcar como procesado
    instance._status_change_processed = True

    # Crear registro de cambio
    TaskStatusChange.objects.create(
        task=instance,
        old_status=instance._old_status,
        new_status=instance.status,
        changed_by=getattr(instance, "_changed_by", None),  # Usuario que hizo el cambio
        notes=getattr(instance, "_change_notes", ""),
    )

    # Guardar old_status para notificaciones antes de limpiar
    old_status_value = instance._old_status

    # Limpiar flags temporales
    if hasattr(instance, "_status_changed"):
        delattr(instance, "_status_changed")
    if hasattr(instance, "_old_status"):
        delattr(instance, "_old_status")
    if hasattr(instance, "_status_change_processed"):
        delattr(instance, "_status_change_processed")

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
    if task.assigned_to and hasattr(task.assigned_to, "user") and task.assigned_to.user:
        recipients.add(task.assigned_to.user)

    # 3. PMs del proyecto (usuarios con perfil project_manager relacionados al proyecto)
    # Q11.10: Agregar project managers del proyecto
    if task.project:
        # Obtener todos los PMs asignados al proyecto a través de ProjectManagerAssignment
        pm_assignments = task.project.pm_assignments.select_related("pm").all()
        for assignment in pm_assignments:
            if assignment.pm:
                recipients.add(assignment.pm)

    # Crear notificación para cada destinatario
    for user in recipients:
        # No notificar al usuario que hizo el cambio
        changed_by = getattr(task, "_changed_by", None)
        if user == changed_by:
            continue

        # Determinar el tipo de notificación según el nuevo status
        notif_type = "task_completed" if new_status == "Completed" else "task_assigned"

        Notification.objects.create(
            user=user,
            notification_type=notif_type,
            title=_("Status Change: {}").format(task.title),
            message=_('Task "{}" changed from {} to {}').format(task.title, old_status, new_status),
            link_url=f"/task/{task.pk}/",
            related_object_type="Task",
            related_object_id=task.pk,
        )


# ============================================================================
# TASK IMAGE VERSIONING
# ============================================================================


@receiver(post_save, sender="core.TaskImage", dispatch_uid="handle_task_image_versioning_post_save")
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
    TaskImage.objects.filter(task=instance.task).exclude(pk=instance.pk).update(is_current=False)

    # Asegurar que la nueva imagen es current
    if not instance.is_current:
        instance.is_current = True
        instance.save(update_fields=["is_current"])


# ======================================================
# SECURITY: Single active session per user
# ======================================================


def _active_session_cache_key(user_id: int) -> str:
    return f"active_session:{user_id}"


def _revoke_session(session_key: str) -> None:
    if not session_key:
        return
    # If session backend is not DB-backed, ignore
    with contextlib.suppress(Exception):
        Session.objects.filter(session_key=session_key).delete()


def handle_user_logged_in(sender, request, user, **kwargs):
    """Ensure user has only one active session: revoke any previous key."""
    try:
        new_key = getattr(request.session, "session_key", None)
        if not new_key:
            # Ensure the session is saved to get a key
            request.session.save()
            new_key = request.session.session_key
        cache_key = _active_session_cache_key(user.id)
        old_key = cache.get(cache_key)
        if old_key and old_key != new_key:
            _revoke_session(old_key)
        cache.set(cache_key, new_key, timeout=None)
    except Exception:
        # Non-fatal: if cache or session backend unavailable, skip
        pass


def handle_user_logged_out(sender, request, user, **kwargs):
    try:
        cache_key = _active_session_cache_key(user.id)
        cache.delete(cache_key)
    except Exception:
        pass


user_logged_in.connect(handle_user_logged_in)
user_logged_out.connect(handle_user_logged_out)
