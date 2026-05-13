"""Diagnose & test the configured Django email backend.

Usage:
    # Just print the config & detect common misconfigurations
    python manage.py test_email_config

    # Also send a real test email
    python manage.py test_email_config --to you@example.com

    # On Railway:
    railway run python manage.py test_email_config --to you@example.com
"""
from __future__ import annotations

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Diagnose the active email backend and optionally send a test."

    def add_arguments(self, parser):
        parser.add_argument(
            "--to",
            help="Recipient email address. If omitted, only diagnostics run.",
        )

    def handle(self, *args, to: str | None = None, **opts):
        out = self.stdout
        err = self.stderr

        backend = getattr(settings, "EMAIL_BACKEND", "<unset>")
        host = getattr(settings, "EMAIL_HOST", None)
        port = getattr(settings, "EMAIL_PORT", None)
        use_tls = getattr(settings, "EMAIL_USE_TLS", None)
        user = getattr(settings, "EMAIL_HOST_USER", None)
        pwd_set = bool(getattr(settings, "EMAIL_HOST_PASSWORD", None))
        from_addr = getattr(
            settings, "DEFAULT_FROM_EMAIL", "<unset>",
        )

        out.write("─── Active email configuration ────────────────────")
        out.write(f"EMAIL_BACKEND       : {backend}")
        out.write(f"EMAIL_HOST          : {host or '∅ (unset)'}")
        out.write(f"EMAIL_PORT          : {port}")
        out.write(f"EMAIL_USE_TLS       : {use_tls}")
        out.write(f"EMAIL_HOST_USER     : {user or '∅ (unset)'}")
        out.write(f"EMAIL_HOST_PASSWORD : {'★ set' if pwd_set else '∅ (unset)'}")
        out.write(f"DEFAULT_FROM_EMAIL  : {from_addr}")
        out.write("")

        # ── Diagnose common misconfigurations ──────────────────────
        is_console = backend.endswith("console.EmailBackend")
        is_smtp = backend.endswith("smtp.EmailBackend")

        if is_console:
            self.stdout.write(self.style.WARNING(
                "⚠️  Console backend active — emails print to stdout, "
                "they do NOT reach an inbox. This is the correct dev "
                "default. To send real emails set:\n"
                "    EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend"
            ))
        elif is_smtp and not host:
            err.write(self.style.ERROR(
                "❌  SMTP backend is active but EMAIL_HOST is empty.\n"
                "    Required env vars (e.g. SendGrid):\n"
                "      EMAIL_HOST=smtp.sendgrid.net\n"
                "      EMAIL_HOST_USER=apikey\n"
                "      EMAIL_HOST_PASSWORD=<SENDGRID_API_KEY>\n"
                "      EMAIL_PORT=587\n"
                "      EMAIL_USE_TLS=True\n"
                "      DEFAULT_FROM_EMAIL=noreply@kibraypainting.us"
            ))
        elif is_smtp and not pwd_set:
            err.write(self.style.ERROR(
                "❌  SMTP backend active and EMAIL_HOST is set, but "
                "EMAIL_HOST_PASSWORD is empty. The auth handshake "
                "will fail."
            ))
        elif is_smtp:
            out.write(self.style.SUCCESS(
                "✅ SMTP looks fully configured."
            ))

        if not to:
            out.write("")
            out.write(
                "Pass --to <address> to actually attempt sending."
            )
            return

        # ── Actually send ──────────────────────────────────────────
        out.write("")
        out.write(f"📨  Attempting to send test email to {to}…")
        try:
            msg = EmailMultiAlternatives(
                subject="Kibray — email config test",
                body=(
                    "If you can read this, the SMTP path works.\n"
                    f"Backend : {backend}\n"
                    f"Host    : {host or '<unset>'}\n"
                    f"From    : {from_addr}\n"
                ),
                from_email=from_addr,
                to=[to],
            )
            sent = msg.send(fail_silently=False)
        except Exception as e:
            err.write(self.style.ERROR(
                f"❌  send() raised {type(e).__name__}: {e}"
            ))
            return

        if sent:
            out.write(self.style.SUCCESS(
                f"✅ send() returned {sent} — check the inbox."
            ))
        else:
            err.write(self.style.ERROR(
                "❌  send() returned 0 — backend silently dropped the "
                "message."
            ))
