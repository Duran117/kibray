"""Idempotent command to promote existing users to the 'partner' (socio) role.

Profit-share Phase 1.5. Designed to be run in PRODUCTION to flag the real
partners by username or email WITHOUT hardcoding names anywhere in the code.

Usage:
    python manage.py promote_partners --user jluis --user jmanuel
    python manage.py promote_partners --email jose.luis@... --email jose.manuel@...
    python manage.py promote_partners --user jluis --dry-run

Guarantees:
  - Idempotent: re-running is a no-op for users already 'partner'.
  - Read-only with --dry-run: prints the plan, changes nothing.
  - Never creates users: only promotes existing ones (refuses unknown).
  - Only touches Profile.role; does NOT alter payroll/Employee here (that is
    handled explicitly in Phase 6 so this command stays safe and reversible).
"""
from __future__ import annotations

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import Q

from core.access import ROLE_PARTNER
from core.models import Profile

User = get_user_model()


class Command(BaseCommand):
    help = "Promote existing users to the 'partner' (socio) role by username or email."

    def add_arguments(self, parser):
        parser.add_argument(
            "--user", action="append", default=[], dest="usernames",
            help="Username to promote (repeatable).",
        )
        parser.add_argument(
            "--email", action="append", default=[], dest="emails",
            help="Email to promote (repeatable).",
        )
        parser.add_argument(
            "--dry-run", action="store_true",
            help="Show what would change without writing anything.",
        )

    def handle(self, *args, **options):
        usernames = [u.strip() for u in options["usernames"] if u.strip()]
        emails = [e.strip() for e in options["emails"] if e.strip()]
        dry_run = options["dry_run"]

        if not usernames and not emails:
            raise CommandError(
                "Provide at least one --user <username> or --email <email>."
            )

        # Resolve each selector individually so we can report misses precisely.
        resolved: dict[int, User] = {}
        missing: list[str] = []

        for uname in usernames:
            u = User.objects.filter(username__iexact=uname).first()
            if u:
                resolved[u.pk] = u
            else:
                missing.append(f"username={uname!r}")

        for email in emails:
            u = User.objects.filter(email__iexact=email).first()
            if u:
                resolved[u.pk] = u
            else:
                missing.append(f"email={email!r}")

        if missing:
            self.stdout.write(self.style.WARNING(
                "⚠️  No matching user for: " + ", ".join(missing)
            ))

        if not resolved:
            raise CommandError("No existing users matched. Nothing to do.")

        self.stdout.write(self.style.MIGRATE_HEADING(
            f"\nPromote to '{ROLE_PARTNER}' — {len(resolved)} user(s) matched"
            + (" [DRY-RUN]" if dry_run else "")
        ))

        to_change: list[tuple[User, str]] = []
        already: list[User] = []

        for u in resolved.values():
            profile, _ = Profile.objects.get_or_create(
                user=u, defaults={"role": ROLE_PARTNER}
            )
            current = profile.role
            if current == ROLE_PARTNER:
                already.append(u)
            else:
                to_change.append((u, current))

        for u in already:
            self.stdout.write(f"  ✓ {u.username} <{u.email}> already '{ROLE_PARTNER}' (no change)")

        for u, current in to_change:
            self.stdout.write(
                f"  → {u.username} <{u.email}>  {current!r} → {ROLE_PARTNER!r}"
            )

        if dry_run:
            self.stdout.write(self.style.NOTICE(
                f"\nDRY-RUN: would change {len(to_change)}, "
                f"{len(already)} already correct. No writes performed."
            ))
            return

        if not to_change:
            self.stdout.write(self.style.SUCCESS(
                f"\nNothing to update — all {len(already)} already '{ROLE_PARTNER}'."
            ))
            return

        with transaction.atomic():
            for u, _current in to_change:
                profile = u.profile
                profile.role = ROLE_PARTNER
                profile.save(update_fields=["role"])

        self.stdout.write(self.style.SUCCESS(
            f"\n✅ Promoted {len(to_change)} user(s) to '{ROLE_PARTNER}'. "
            f"{len(already)} were already set."
        ))
