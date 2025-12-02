# =============================
# NOTIFICATIONS
# =============================

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext_lazy as _, gettext

from core.models import Notification


@login_required
def notifications_list(request):
    """Lista de notificaciones del usuario."""
    qs = request.user.notifications.all()
    filter_read = request.GET.get("read")
    if filter_read == "false":
        qs = qs.filter(is_read=False)
    elif filter_read == "true":
        qs = qs.filter(is_read=True)
    unread_count = request.user.notifications.filter(is_read=False).count()
    paginator = Paginator(qs, 20)
    page = request.GET.get("page", 1)
    notifications = paginator.get_page(page)
    return render(
        request,
        "core/notifications_list.html",
        {
            "notifications": notifications,
            "unread_count": unread_count,
            "filter_read": filter_read,
        },
    )


@login_required
def notification_mark_read(request, notification_id):
    """Marcar notificación como leída."""
    n = get_object_or_404(Notification, id=notification_id, user=request.user)
    n.mark_read()
    return redirect("notifications_list")


@login_required
def notifications_mark_all_read(request):
    """Marcar todas las notificaciones como leídas."""
    if request.method == "POST":
        request.user.notifications.filter(is_read=False).update(is_read=True)
        messages.success(request, _("Todas las notificaciones marcadas como leídas."))
    return redirect("notifications_list")
