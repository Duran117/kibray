from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import EmailMultiAlternatives
from django.core.management.base import BaseCommand
from django.template.loader import render_to_string
from django.utils import timezone

User = get_user_model()


class Command(BaseCommand):
    help = "Send daily notification digests to users with unread notifications"

    def add_arguments(self, parser):
        parser.add_argument(
            "--since-hours", type=int, default=24, help="Window of hours to include in the digest (default: 24)"
        )
        parser.add_argument("--dry-run", action="store_true", help="Only print summary, do not send emails")

    def handle(self, *args, **options):
        from core.models import Notification

        since_hours = options["since_hours"]
        dry_run = options["dry_run"]
        now = timezone.now()
        since = now - timedelta(hours=since_hours)

        # Early exit if email not configured
        if not getattr(settings, "EMAIL_HOST", None):
            self.stdout.write(self.style.WARNING("EMAIL_HOST not configured; skipping send."))
            dry_run = True

        # Find users with unread notifications in window
        qs = Notification.objects.filter(is_read=False, created_at__gte=since).select_related("user")
        by_user = {}
        for n in qs:
            by_user.setdefault(n.user_id, {"user": n.user, "items": []})["items"].append(n)

        total_sent = 0
        for uid, bundle in by_user.items():
            user = bundle["user"]
            items = bundle["items"]
            if not getattr(user, "email", None):
                continue

            context = {
                "user": user,
                "items": items[:25],  # cap list in email
                "count": len(items),
                "since": since,
                "now": now,
                "app_name": getattr(settings, "APP_NAME", "Kibray"),
                "site_url": getattr(settings, "SITE_URL", ""),
            }
            context["remaining"] = max(0, context["count"] - len(context["items"]))
            subject = f"[{context['app_name']}] Resumen de notificaciones ({context['count']})"
            text_body = render_to_string("core/emails/notification_digest.txt", context)
            html_body = render_to_string("core/emails/notification_digest.html", context)

            if dry_run:
                self.stdout.write(self.style.NOTICE(f"[DRY] Would send {context['count']} to {user.email}"))
                continue

            msg = EmailMultiAlternatives(subject, text_body, to=[user.email])
            msg.attach_alternative(html_body, "text/html")
            try:
                msg.send()
                total_sent += 1
            except Exception as ex:
                self.stdout.write(self.style.ERROR(f"Failed to send to {user.email}: {ex}"))

        self.stdout.write(self.style.SUCCESS(f"Digest run complete. Emails sent: {total_sent}"))
