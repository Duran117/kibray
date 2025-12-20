"""
Management command: Import Technical Debt comments as PowerAction tasks.

Scans the repository for TODO/FIXME/PENDING/BUG comments across common file types
and converts each unique item into a PowerAction under the LifeVision goal
"System Perfection".

Usage:
    python manage.py import_technical_debt
    python manage.py import_technical_debt --dry-run

Author: Product Manager & Python Developer
Date: November 29, 2025
"""

from pathlib import Path
import re

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

# Import strategic planning models (available via core.models package)
from core.models import DailyRitualSession, LifeVision, PowerAction

COMMENT_PATTERNS = [
    r"TODO\s*:",
    r"FIXME\s*:",
    r"PENDING\s*:",
    r"BUG\s*:",
]

# File extensions to scan
EXTENSIONS = {".py", ".html", ".js", ".css"}


class Command(BaseCommand):
    help = (
        "Scan codebase comments (TODO/FIXME/PENDING/BUG) and import them as PowerActions "
        "under LifeVision 'System Perfection'."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Preview imports without creating database records",
        )
        parser.add_argument(
            "--root",
            type=str,
            default=str(Path(settings.BASE_DIR)),
            help="Root path to scan (defaults to project BASE_DIR)",
        )
        parser.add_argument(
            "--exclude",
            type=str,
            nargs="*",
            default=[
                ".venv/",
                "node_modules/",
                "__pycache__/",
                "core/migrations/",
                "core/management/commands/",  # skip CLI tools
                "frontend/dist/",
            ],
            help="Relative path substrings to exclude from scanning",
        )

    def handle(self, *args, **options):
        dry_run: bool = options["dry_run"]
        root_path = Path(options["root"]).resolve()
        exclude_list: list[str] = options["exclude"]

        if not root_path.exists():
            self.stdout.write(self.style.ERROR(f"❌ Root path not found: {root_path}"))
            return

        self.stdout.write(self.style.WARNING(f"🔎 Scanning: {root_path}"))
        self.stdout.write(self.style.WARNING(f"⛔ Excluding: {', '.join(exclude_list)}"))

        # Compile a single regex for performance (case-insensitive)
        pattern = re.compile(
            r"(" + "|".join(COMMENT_PATTERNS) + r")\s*(.*)$",
            re.IGNORECASE,
        )

        items: list[tuple[str, int, str, str]] = []  # (rel_path, line_no, tag, text)
        unique_titles: set[str] = set()  # dedup by title

        # Walk files
        for file_path in self.iter_files(root_path, exclude_list):
            rel_path = str(file_path.relative_to(root_path))
            try:
                with open(file_path, encoding="utf-8", errors="ignore") as f:
                    for i, line in enumerate(f, start=1):
                        # Skip long binary-like lines early
                        if "\x00" in line:
                            continue
                        m = pattern.search(line)
                        if m:
                            tag = m.group(1).upper().split(":")[0]  # TODO/FIXME/PENDING/BUG
                            text = m.group(2).strip()
                            if not text:
                                continue
                            title = self.normalize_title(text)
                            items.append((rel_path, i, tag, title))
                            unique_titles.add(title)
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Failed to read {rel_path}: {e}"))

        if not items:
            self.stdout.write(self.style.WARNING("ℹ️ No technical debt comments found."))
            return

        self.stdout.write(self.style.WARNING(f"🧾 Found {len(items)} tagged comments, {len(unique_titles)} unique titles."))

        # Get or create LifeVision "System Perfection"
        with transaction.atomic():
            life_vision, _lv_created = LifeVision.objects.get_or_create(
                title="System Perfection",
                defaults={
                    "user": self.get_default_user(),
                    "scope": "BUSINESS",
                    "deep_why": "Relentless pursuit of robustness, clarity, and maintainability.",
                },
            )

            # Ensure we have a DailyRitualSession for today to attach PowerActions
            default_user = life_vision.user or self.get_default_user()
            session, _sess_created = DailyRitualSession.objects.get_or_create(
                user=default_user,
                date=timezone.localdate(),
                defaults={
                    "physiology_check": False,
                    "gratitude_entries": [],
                    "daily_intention": "Technical debt triage",
                    "energy_level": 5,
                    "habits_checked": [],
                },
            )

        # Build existing titles set for deduplication
        existing_titles = set(
            PowerAction.objects.all().values_list("title", flat=True)
        )

        created_count = 0
        if dry_run:
            # Just report would-create items
            would_create = [t for t in unique_titles if t not in existing_titles]
            self.stdout.write(self.style.WARNING(f"🔍 DRY RUN: Would create {len(would_create)} new PowerActions."))
        else:
            for rel_path, line_no, tag, title in items:
                if title in existing_titles:
                    continue  # skip duplicates
                try:
                    pa = PowerAction.objects.create(
                        session=session,
                        title=title,
                        is_80_20=False,
                        is_frog=False,
                        status="DRAFT",
                        linked_vision=life_vision,
                        description=(
                            f"Imported from {rel_path}:{line_no}\n"
                            f"Tag: {tag}\n"
                            f"Context: Address technical debt item from code comment."
                        ),
                        micro_steps=[
                            {"text": "Investigate the root cause/context", "done": False},
                            {"text": f"Implement fix/refactor for: {title}", "done": False},
                            {"text": f"Validate in affected file: {rel_path}:{line_no}", "done": False},
                        ],
                    )
                    created_count += 1
                    existing_titles.add(title)  # avoid more duplicates within same run
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"❌ Failed to create PowerAction for '{title}': {e}"))

        self.stdout.write(
            self.style.SUCCESS(
                f"\n🚀 Successfully imported {created_count if not dry_run else 0} technical debt items as PowerActions under 'System Perfection'."
            )
        )

    def iter_files(self, root: Path, excludes: list[str]):
        """Yield files with allowed extensions, excluding paths containing any of the excludes."""
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            if path.suffix.lower() not in EXTENSIONS:
                continue
            rel_str = str(path.relative_to(root))
            if any(ex in rel_str for ex in excludes):
                continue
            yield path

    def normalize_title(self, text: str) -> str:
        """Normalize extracted comment text to a concise task title."""
        # Trim and collapse whitespace
        title = " ".join(text.split())
        # Remove trailing punctuation
        title = title.strip(" .;:")
        # Limit length to keep titles practical
        if len(title) > 200:
            title = title[:197] + "..."
        return title

    def get_default_user(self):
        """Pick a default user for LifeVision if none provided.
        Attempts to use the first superuser or staff; falls back to any user.
        """
        try:
            from django.contrib.auth import get_user_model

            User = get_user_model()
            user = User.objects.filter(is_superuser=True).first() or User.objects.filter(is_staff=True).first() or User.objects.first()
            return user
        except Exception:
            return None
