import json
from django.core.management.base import BaseCommand
from core.models import ChangeOrderPhoto

class Command(BaseCommand):
    help = "Normalize and fix double-encoded JSON annotations in ChangeOrderPhoto.annotations TextField"

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Show what would change without saving')
        parser.add_argument('--limit', type=int, default=None, help='Limit number of photos processed')
        parser.add_argument('--verbose', action='store_true', help='Print per-record details')

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        limit = options['limit']
        verbose = options['verbose']

        qs = ChangeOrderPhoto.objects.exclude(annotations='').order_by('id')
        total = qs.count()
        if limit:
            qs = qs[:limit]

        processed = 0
        fixed = 0
        skipped = 0

        for photo in qs:
            original = photo.annotations
            new_value, changed, reason = self._normalize(original)

            if verbose:
                self.stdout.write(f"Photo #{photo.id}: changed={changed} reason={reason}")

            if changed:
                fixed += 1
                if not dry_run:
                    photo.annotations = new_value
                    photo.save(update_fields=['annotations'])
            else:
                skipped += 1

            processed += 1

        self.stdout.write(self.style.SUCCESS("Annotation cleanup complete"))
        self.stdout.write(f"Total existing with annotations: {total}")
        self.stdout.write(f"Processed: {processed}")
        self.stdout.write(f"Fixed: {fixed}")
        self.stdout.write(f"Unchanged: {skipped}")
        if dry_run:
            self.stdout.write(self.style.WARNING("(Dry run - no changes saved)"))

    def _normalize(self, value: str):
        """Return (normalized_value, changed_bool, reason_string).
        Handles cases:
        - Proper JSON list/dict (re-serialize for consistency)
        - Double-encoded JSON string inside JSON string
        - Python repr of list/dict with single quotes (use ast.literal_eval)
        - Non-JSON strings left untouched
        """
        if not value or not isinstance(value, str):
            return value, False, 'empty_or_non_string'

        # Try parse once
        try:
            first = json.loads(value)
        except Exception:
            # Attempt python literal eval for single-quoted structures
            import ast
            try:
                py_obj = ast.literal_eval(value)
                if isinstance(py_obj, (list, dict)):
                    return json.dumps(py_obj), True, 'python_repr_converted'
            except Exception:
                return value, False, 'not_json'

        # If first parse yields list/dict -> we want single json.dumps of structure
        if isinstance(first, (list, dict)):
            normalized = json.dumps(first)
            if normalized != value:
                return normalized, True, 're-serialized_struct'
            return value, False, 'already_ok_struct'

        # If first parse is a string that itself looks like JSON array/object -> second parse
        if isinstance(first, str):
            inner_str = first.strip()
            if (inner_str.startswith('{') and inner_str.endswith('}')) or (inner_str.startswith('[') and inner_str.endswith(']')):
                try:
                    second = json.loads(inner_str)
                    if isinstance(second, (list, dict)):
                        normalized = json.dumps(second)
                        # Definitely changed
                        return normalized, True, 'double_encoded_struct'
                except Exception:
                    return value, False, 'inner_not_json'
            # Plain string content - keep as-is
            return value, False, 'string_content'

        # Any other type (number, bool, null) -> keep original string representation
        return value, False, 'primitive'
