"""
Push Notifications Helper for Kibray
Uses OneSignal REST API for web push notifications
"""

import logging

from django.conf import settings
import requests

logger = logging.getLogger(__name__)


class PushNotificationService:
    """Service for sending push notifications via OneSignal"""

    BASE_URL = "https://onesignal.com/api/v1/notifications"

    @staticmethod
    def send_notification(user_ids, heading, content, url=None, data=None):
        """
        Send push notification to specific users

        Args:
            user_ids (list): List of OneSignal player IDs or Django user IDs
            heading (str): Notification heading/title
            content (str): Notification body text
            url (str): URL to open when notification clicked
            data (dict): Custom data to attach to notification

        Returns:
            dict: Response from OneSignal API
        """
        if not hasattr(settings, "ONESIGNAL_APP_ID") or not settings.ONESIGNAL_APP_ID:
            logger.warning("OneSignal not configured. Skipping push notification.")
            return None

        if not hasattr(settings, "ONESIGNAL_REST_API_KEY") or not settings.ONESIGNAL_REST_API_KEY:
            logger.warning("OneSignal REST API Key not configured. Skipping push notification.")
            return None

        payload = {
            "app_id": settings.ONESIGNAL_APP_ID,
            "include_external_user_ids": [str(uid) for uid in user_ids],
            "headings": {"en": heading},
            "contents": {"en": content},
            "web_url": url,
            "data": data or {},
        }

        headers = {
            "Content-Type": "application/json; charset=utf-8",
            "Authorization": f"Basic {settings.ONESIGNAL_REST_API_KEY}",
        }

        try:
            response = requests.post(
                PushNotificationService.BASE_URL, json=payload, headers=headers, timeout=10
            )
            response.raise_for_status()
            logger.info(f"Push notification sent to {len(user_ids)} users: {heading}")
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send push notification: {e}")
            return None

    @staticmethod
    def send_to_all(heading, content, url=None, segments=None):
        """
        Send notification to all subscribers or specific segments

        Args:
            heading (str): Notification heading
            content (str): Notification content
            url (str): URL to open
            segments (list): OneSignal segments (e.g., ['Active Users', 'Subscribed Users'])
        """
        if not hasattr(settings, "ONESIGNAL_APP_ID"):
            return None

        payload = {
            "app_id": settings.ONESIGNAL_APP_ID,
            "included_segments": segments or ["Subscribed Users"],
            "headings": {"en": heading},
            "contents": {"en": content},
            "web_url": url,
        }

        headers = {
            "Content-Type": "application/json; charset=utf-8",
            "Authorization": f"Basic {settings.ONESIGNAL_REST_API_KEY}",
        }

        try:
            response = requests.post(
                PushNotificationService.BASE_URL, json=payload, headers=headers, timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send broadcast notification: {e}")
            return None


# ===== NOTIFICATION TRIGGERS =====


def notify_invoice_approved(invoice):
    """Notify PM when invoice is approved"""
    from django.urls import reverse

    if invoice.project and invoice.project.pm:
        url = reverse("invoice_detail", args=[invoice.id])
        PushNotificationService.send_notification(
            user_ids=[invoice.project.pm.id],
            heading="💰 Factura Aprobada",
            content=f"Factura #{invoice.number} para {invoice.project.name} aprobada",
            url=url,
            data={"type": "invoice", "invoice_id": invoice.id},
        )


def notify_changeorder_created(change_order):
    """Notify admin when change order is created"""
    from django.contrib.auth import get_user_model
    from django.urls import reverse

    user_model = get_user_model()
    admins = user_model.objects.filter(is_staff=True, is_active=True)

    if admins.exists():
        url = reverse("changeorder_detail", args=[change_order.id])
        admin_ids = [admin.pk for admin in admins]
        PushNotificationService.send_notification(
            user_ids=admin_ids,
            heading="📝 Nueva Orden de Cambio",
            content=f"CO #{change_order.co_number} - {change_order.project.name}: ${change_order.amount}",
            url=url,
            data={"type": "changeorder", "co_id": change_order.id},
        )


def notify_changeorder_approved(change_order):
    """Notify requester when their change order is approved"""
    from django.urls import reverse

    if change_order.created_by:
        url = reverse("changeorder_detail", args=[change_order.id])
        PushNotificationService.send_notification(
            user_ids=[change_order.created_by.id],
            heading="✅ Orden de Cambio Aprobada",
            content=f"Tu CO #{change_order.co_number} ha sido aprobada por ${change_order.amount}",
            url=url,
            data={"type": "changeorder", "co_id": change_order.id},
        )


def notify_material_request(material_request):
    """Notify inventory manager when material is requested"""
    from django.contrib.auth import get_user_model
    from django.urls import reverse

    user_model = get_user_model()
    # Assuming you have a group or role for inventory managers
    managers = user_model.objects.filter(groups__name="Inventory Manager", is_active=True)

    if managers.exists():
        url = reverse("materials_request_list", args=[material_request.project.id])
        manager_ids = [m.pk for m in managers]
        PushNotificationService.send_notification(
            user_ids=manager_ids,
            heading="📦 Solicitud de Material",
            content=f"{material_request.product_name} - {material_request.quantity} {material_request.unit}",
            url=url,
            data={"type": "material_request", "request_id": material_request.id},
        )


def notify_material_received(material_request):
    """Notify requester when material is received"""
    from django.urls import reverse

    if material_request.requested_by:
        url = reverse("project_overview", args=[material_request.project.id])
        PushNotificationService.send_notification(
            user_ids=[material_request.requested_by.id],
            heading="✅ Material Recibido",
            content=f"{material_request.product_name} ha llegado al proyecto",
            url=url,
            data={"type": "material", "request_id": material_request.id},
        )


def notify_task_assigned(task):
    """Notify employee when task/touchup is assigned to them"""
    from django.urls import reverse

    if task.assigned_to:
        url = reverse("task_detail", args=[task.id])
        PushNotificationService.send_notification(
            user_ids=[task.assigned_to.id],
            heading="🎯 Nueva Tarea Asignada",
            content=f"{task.title} - {task.project.name if hasattr(task, 'project') else 'Sin proyecto'}",
            url=url,
            data={"type": "task", "task_id": task.id},
        )


def notify_touchup_completed(task):
    """Notify PM when touchup is completed"""
    from django.urls import reverse

    if hasattr(task, "project") and task.project and task.project.pm:
        url = reverse("task_detail", args=[task.id])
        PushNotificationService.send_notification(
            user_ids=[task.project.pm.id],
            heading="✅ Touch-up Completado",
            content=f"{task.title} completado por {task.assigned_to.username if task.assigned_to else 'Sin asignar'}",
            url=url,
            data={"type": "touchup", "task_id": task.id},
        )


def notify_project_budget_alert(project):
    """Notify PM and admin when project exceeds budget"""
    from django.contrib.auth import get_user_model
    from django.urls import reverse

    user_model = get_user_model()
    users_to_notify = []

    if project.pm:
        users_to_notify.append(project.pm.pk)

    admins = user_model.objects.filter(is_staff=True, is_active=True)
    users_to_notify.extend([admin.pk for admin in admins])

    if users_to_notify:
        url = reverse("project_overview", args=[project.id])
        PushNotificationService.send_notification(
            user_ids=users_to_notify,
            heading="⚠️ Alerta de Presupuesto",
            content=f"{project.name} ha excedido el presupuesto aprobado",
            url=url,
            data={"type": "budget_alert", "project_id": project.id},
        )


def notify_daily_plan_created(daily_plan):
    """Notify team when daily plan is created"""
    from django.urls import reverse

    # Get all employees assigned to this project
    if daily_plan.project:
        # Assuming TimeEntry or similar model tracks project employees
        from core.models import TimeEntry

        employees = (
            TimeEntry.objects.filter(project=daily_plan.project)
            .values_list("employee_id", flat=True)
            .distinct()
        )

        if employees:
            url = reverse("daily_planning_dashboard")
            PushNotificationService.send_notification(
                user_ids=list(employees),
                heading="📋 Plan Diario Actualizado",
                content=f"Nuevo plan para {daily_plan.project.name} - {daily_plan.date.strftime('%d/%m/%Y')}",
                url=url,
                data={"type": "daily_plan", "plan_id": daily_plan.id},
            )


def notify_payroll_ready(employee, payroll_entry):
    """Notify employee when payroll is ready"""
    from django.urls import reverse

    url = reverse("dashboard")
    PushNotificationService.send_notification(
        user_ids=[employee.id],
        heading="💵 Nómina Disponible",
        content=f"Tu pago de ${payroll_entry.amount} está listo para procesar",
        url=url,
        data={"type": "payroll", "entry_id": payroll_entry.id},
    )
