"""
Helper functions for creating notifications.
Call these from views or signals when events occur.
"""

from django.contrib.auth.models import User
from django.urls import reverse

from core.models import Notification


def notify_task_created(task, creator):
    """Notify PMs when a client creates a touch-up task."""
    pms = User.objects.filter(profile__role="project_manager", is_active=True)
    link = reverse("client_project_view", args=[task.project.id])
    for pm in pms:
        Notification.objects.create(
            user=pm,
            notification_type="task_created",
            title=f"Nueva tarea: {task.title}",
            message=f"{creator.username} creó una tarea en {task.project.name}",
            related_object_type="task",
            related_object_id=task.id,
            link_url=link,
        )


def notify_task_assigned(task, assigned_to):
    """Notify employee when assigned to a task."""
    if not assigned_to or not assigned_to.user:
        return
    link = reverse("client_project_view", args=[task.project.id])
    Notification.objects.create(
        user=assigned_to.user,
        notification_type="task_assigned",
        title=f"Tarea asignada: {task.title}",
        message=f'Has sido asignado a "{task.title}" en {task.project.name}',
        related_object_type="task",
        related_object_id=task.id,
        link_url=link,
    )


def notify_task_completed(task, completer):
    """Notify client/PM when task is completed."""
    from core.models import ClientProjectAccess

    link = reverse("client_project_view", args=[task.project.id])
    # Notify client
    client_users = ClientProjectAccess.objects.filter(
        project=task.project, role="client"
    ).values_list("user", flat=True)
    for uid in client_users:
        try:
            u = User.objects.get(id=uid)
            Notification.objects.create(
                user=u,
                notification_type="task_completed",
                title=f"Tarea completada: {task.title}",
                message=f'{completer.username} completó "{task.title}"',
                related_object_type="task",
                related_object_id=task.id,
                link_url=link,
            )
        except User.DoesNotExist:
            pass


def notify_color_review(color_sample, reviewer):
    """Notify PM/client when color sample status changes."""
    link = reverse("color_sample_detail", args=[color_sample.id])
    # Notify PMs
    pms = User.objects.filter(profile__role="project_manager", is_active=True)
    for pm in pms:
        Notification.objects.create(
            user=pm,
            notification_type="color_review",
            title=f"Color under review: {color_sample.name or color_sample.code}",
            message=f"{reviewer.username} changed status to {color_sample.get_status_display()}",
            related_object_type="color_sample",
            related_object_id=color_sample.id,
            link_url=link,
        )


def notify_color_approved(color_sample, approver):
    """Notify stakeholders when color is approved."""
    from core.models import ClientProjectAccess

    link = reverse("color_sample_detail", args=[color_sample.id])
    # Notify client
    client_users = ClientProjectAccess.objects.filter(
        project=color_sample.project, role="client"
    ).values_list("user", flat=True)
    for uid in client_users:
        try:
            u = User.objects.get(id=uid)
            Notification.objects.create(
                user=u,
                notification_type="color_approved",
                title=f"Color approved: {color_sample.name or color_sample.code}",
                message=f"{approver.username} approved the color for {color_sample.project.name}",
                related_object_type="color_sample",
                related_object_id=color_sample.id,
                link_url=link,
            )
        except User.DoesNotExist:
            pass


def notify_damage_reported(damage_report, reporter):
    """Notify PM when damage is reported."""
    link = reverse("damage_report_detail", args=[damage_report.id])
    pms = User.objects.filter(profile__role="project_manager", is_active=True)
    staff = User.objects.filter(is_staff=True, is_active=True)
    for u in set(list(pms) | set(staff)):
        Notification.objects.create(
            user=u,
            notification_type="damage_reported",
            title=f"Damage reported: {damage_report.title}",
            message=f"{reporter.username} reported a damage ({damage_report.get_severity_display()}) in {damage_report.project.name}",
            related_object_type="damage_report",
            related_object_id=damage_report.id,
            link_url=link,
        )


def notify_chat_message(channel, sender, message_text):
    """Notify channel participants of new chat message (optional, can be noisy)."""
    # Only notify if message is important or @mentions (implement mention detection if needed)
    # For now, skip to avoid spam; but structure is here if needed
    pass
