"""
Management command to silence excessive print() statements in production code.

Usage:
    python manage.py silence_prints
    python manage.py silence_prints --dry-run
    python manage.py silence_prints --restore

Author: Senior Python Code Cleaner
Date: November 29, 2025
"""

from pathlib import Path
import re
import shutil

from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Silence excessive print() statements in core/ to clean up production logs"

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview changes without modifying files',
        )
        parser.add_argument(
            '--restore',
            action='store_true',
            help='Restore files from .bak backups',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed output of each silenced print',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        restore = options['restore']
        verbose = options['verbose']

        # Base directory: core/
        base_dir = Path(settings.BASE_DIR) / 'core'

        if not base_dir.exists():
            self.stdout.write(self.style.ERROR(f"❌ Directory not found: {base_dir}"))
            return

        if restore:
            self.restore_backups(base_dir, verbose)
            return

        # Patterns to exclude
        exclude_patterns = [
            'migrations/',
            'management/commands/',
            '__pycache__/',
            '.pyc',
            'tests/',
            'test_',
            '_BACKUP_',
            '.bak',
            '_clean.py',
        ]

        # Target files to scan (patterns to match)
        target_patterns = [
            'views',
            'models',
            'utils',
            'tasks',
            'forms',
            'serializers',
            'services',
            'api',
            'notifications',
            'context_processors',
            'security_decorators',
        ]

        total_silenced = 0
        files_modified = 0
        modified_files_list = []

        # Scan all Python files in core/
        for py_file in base_dir.rglob('*.py'):
            # Skip excluded paths
            if any(excluded in str(py_file) for excluded in exclude_patterns):
                continue

            # Check if file matches target patterns
            # Match if filename or directory contains any of the patterns
            relative_path = py_file.relative_to(base_dir)
            file_name = py_file.stem  # filename without extension

            is_target = any(
                pattern in file_name.lower() or pattern in str(relative_path).lower()
                for pattern in target_patterns
            )

            if not is_target:
                continue

            # Process the file
            silenced_count = self.silence_prints_in_file(
                py_file, dry_run, verbose
            )

            if silenced_count > 0:
                total_silenced += silenced_count
                files_modified += 1
                modified_files_list.append((py_file, silenced_count))

        # Summary
        self.stdout.write("\n" + "=" * 70)
        if dry_run:
            self.stdout.write(self.style.WARNING("🔍 DRY RUN MODE - No files were modified"))
        else:
            self.stdout.write(self.style.SUCCESS(f"🤫 Silenced {total_silenced} print statements across {files_modified} files."))

        if modified_files_list:
            self.stdout.write("\n📝 Modified files:")
            for file_path, count in modified_files_list:
                rel_path = file_path.relative_to(settings.BASE_DIR)
                self.stdout.write(f"   • {rel_path}: {count} prints silenced")

        if not dry_run and files_modified > 0:
            self.stdout.write("\n💾 Backups created with .bak extension")
            self.stdout.write("   To restore: python manage.py silence_prints --restore")

        self.stdout.write("=" * 70 + "\n")

    def silence_prints_in_file(self, file_path: Path, dry_run: bool, verbose: bool) -> int:
        """
        Silence print statements in a single file.
        
        Returns:
            Number of print statements silenced
        """
        try:
            with open(file_path, encoding='utf-8') as f:
                original_content = f.read()
                lines = original_content.split('\n')
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Error reading {file_path}: {e}")
            )
            return 0

        modified_lines = []
        silenced_count = 0

        # Regex pattern to match print statements
        # Matches: print(...) with any indentation
        # Does NOT match: # print(...) or """ print(...) """
        print_pattern = re.compile(
            r'^(\s*)print\(',  # Indentation + print(
            re.MULTILINE
        )

        for line_num, line in enumerate(lines, 1):
            # Check if line contains a print statement
            match = print_pattern.match(line)

            if match:
                # Additional checks to avoid false positives
                stripped = line.strip()

                # Skip if already commented
                if stripped.startswith('#'):
                    modified_lines.append(line)
                    continue

                # Skip if inside a string (basic check)
                if stripped.startswith(('"""', "'''", '"', "'")):
                    modified_lines.append(line)
                    continue

                # Silence the print statement
                indent = match.group(1)
                silenced_line = f"{indent}# [SILENCED] {stripped}"
                modified_lines.append(silenced_line)
                silenced_count += 1

                if verbose:
                    rel_path = file_path.relative_to(Path(settings.BASE_DIR))
                    self.stdout.write(
                        f"   Line {line_num} in {rel_path}: {stripped[:60]}..."
                    )
            else:
                modified_lines.append(line)

        # If no changes, skip file
        if silenced_count == 0:
            return 0

        # Create backup and write changes (if not dry run)
        if not dry_run:
            # Create backup
            backup_path = Path(str(file_path) + '.bak')
            try:
                shutil.copy2(file_path, backup_path)
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"❌ Error creating backup for {file_path}: {e}")
                )
                return 0

            # Write modified content
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(modified_lines))
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"❌ Error writing to {file_path}: {e}")
                )
                # Restore from backup if write fails
                try:
                    shutil.copy2(backup_path, file_path)
                except Exception:
                    pass
                return 0

        return silenced_count

    def restore_backups(self, base_dir: Path, verbose: bool):
        """
        Restore all files from their .bak backups.
        """
        self.stdout.write(self.style.WARNING("🔄 Restoring files from backups..."))

        restored_count = 0

        for backup_file in base_dir.rglob('*.py.bak'):
            original_file = Path(str(backup_file)[:-4])  # Remove .bak extension

            if original_file.exists():
                try:
                    shutil.copy2(backup_file, original_file)
                    restored_count += 1

                    if verbose:
                        rel_path = original_file.relative_to(settings.BASE_DIR)
                        self.stdout.write(f"   ✅ Restored: {rel_path}")

                    # Optionally remove backup after restoration
                    # backup_file.unlink()

                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f"❌ Error restoring {original_file}: {e}")
                    )

        if restored_count > 0:
            self.stdout.write(
                self.style.SUCCESS(f"\n✅ Restored {restored_count} files from backups")
            )
        else:
            self.stdout.write(
                self.style.WARNING("⚠️  No backup files found to restore")
            )
