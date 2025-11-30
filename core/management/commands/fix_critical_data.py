"""
Django Management Command: Fix Critical Data Integrity Issues
==============================================================

Purpose: Resolve HIGH Priority issues identified by forensic_audit.py

Actions:
1. Fix orphan Projects (assign to "Internal Operations" client)
2. Purge test/garbage data from key models
3. Remove debug breakpoints from forensic_audit.py

Author: Senior Django Database Administrator
Date: 2025-11-29
"""

import re
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Q
from django.apps import apps


# ANSI Color Codes for Terminal Output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
CYAN = '\033[96m'
MAGENTA = '\033[95m'
BOLD = '\033[1m'
RESET = '\033[0m'


class Command(BaseCommand):
    help = 'Fix critical data integrity issues found in forensic audit'

    def __init__(self):
        super().__init__()
        self.stats = {
            'orphan_projects_fixed': 0,
            'test_data_deleted': 0,
            'breakpoints_removed': 0,
        }

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be changed without making actual changes',
        )
        parser.add_argument(
            '--skip-orphans',
            action='store_true',
            help='Skip fixing orphan projects',
        )
        parser.add_argument(
            '--skip-test-data',
            action='store_true',
            help='Skip purging test data',
        )
        parser.add_argument(
            '--skip-breakpoints',
            action='store_true',
            help='Skip removing debug breakpoints',
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        
        self.stdout.write(f"\n{CYAN}{'='*80}{RESET}")
        self.stdout.write(f"{BOLD}{CYAN}DATABASE INTEGRITY FIX{RESET}")
        self.stdout.write(f"{CYAN}Critical Issues Resolution{RESET}")
        self.stdout.write(f"{CYAN}{'='*80}{RESET}\n")

        if dry_run:
            self.stdout.write(f"{YELLOW}🔍 DRY RUN MODE - No changes will be made{RESET}\n")

        # Action 1: Fix Orphan Projects
        if not options.get('skip_orphans'):
            self.fix_orphan_projects(dry_run)
        else:
            self.stdout.write(f"{YELLOW}⏭️  Skipped: Fix orphan projects{RESET}\n")

        # Action 2: Purge Test Data
        if not options.get('skip_test_data'):
            self.purge_test_data(dry_run)
        else:
            self.stdout.write(f"{YELLOW}⏭️  Skipped: Purge test data{RESET}\n")

        # Action 3: Fix Code Breakpoint
        if not options.get('skip_breakpoints'):
            self.fix_code_breakpoint(dry_run)
        else:
            self.stdout.write(f"{YELLOW}⏭️  Skipped: Remove debug breakpoints{RESET}\n")

        # Summary
        self.print_summary(dry_run)

    @transaction.atomic
    def fix_orphan_projects(self, dry_run=False):
        """Fix orphan Projects by assigning them to 'Internal Operations' client."""
        self.stdout.write(f"\n{BLUE}{'─'*80}{RESET}")
        self.stdout.write(f"{BOLD}ACTION 1: FIX ORPHAN PROJECTS{RESET}\n")
        self.stdout.write(f"{BLUE}{'─'*80}{RESET}\n")

        try:
            # Get Project model (client is a CharField, not ForeignKey)
            Project = apps.get_model('core', 'Project')

            # Find orphan projects (NULL or empty string)
            orphan_projects = Project.objects.filter(
                Q(client__isnull=True) | Q(client='') | Q(client__iexact='null')
            )
            orphan_count = orphan_projects.count()

            if orphan_count == 0:
                self.stdout.write(f"{GREEN}✅ No orphan projects found. Database is clean!{RESET}\n")
                return

            self.stdout.write(f"{YELLOW}📊 Found {orphan_count} orphan project(s) without a client{RESET}\n")

            # List orphan projects
            for project in orphan_projects[:5]:  # Show first 5
                client_value = project.client or '(empty)'
                self.stdout.write(f"   • Project #{project.pk}: {project.name or 'Unnamed'} [client: {client_value}]")
            if orphan_count > 5:
                self.stdout.write(f"   ... and {orphan_count - 5} more\n")

            if not dry_run:
                # Assign orphan projects to "Internal Operations"
                client_name = 'Internal Operations'
                updated = orphan_projects.update(client=client_name)
                self.stats['orphan_projects_fixed'] = updated

                self.stdout.write(f"{CYAN}🏢 Assigned orphan projects to: '{client_name}'{RESET}")
                self.stdout.write(f"\n{GREEN}✅ Fixed {updated} orphan project(s){RESET}\n")
            else:
                self.stdout.write(f"\n{YELLOW}[DRY RUN] Would assign {orphan_count} project(s) to 'Internal Operations'{RESET}\n")

        except Exception as e:
            self.stdout.write(f"{RED}❌ Error fixing orphan projects: {str(e)}{RESET}\n")
            raise

    @transaction.atomic
    def purge_test_data(self, dry_run=False):
        """Purge test/garbage data from key models."""
        self.stdout.write(f"\n{BLUE}{'─'*80}{RESET}")
        self.stdout.write(f"{BOLD}ACTION 2: PURGE TEST DATA{RESET}\n")
        self.stdout.write(f"{BLUE}{'─'*80}{RESET}\n")

        # Strict garbage keywords - must match exactly or with boundaries
        garbage_keywords = ['asdf', 'test data', 'dummy record', 'temp123', 'xxx', 'zzz']

        # Models to clean: (app_label, model_name, fields_to_check)
        models_to_clean = [
            ('core', 'Notification', ['title', 'message']),
            ('core', 'Task', ['title', 'description']),
            ('core', 'PowerAction', ['title', 'description']),
            ('core', 'MaterialRequestItem', ['product_name', 'description']),
        ]

        total_deleted = 0

        for app_label, model_name, fields in models_to_clean:
            try:
                Model = apps.get_model(app_label, model_name)
            except LookupError:
                self.stdout.write(f"{YELLOW}⚠️  Model {app_label}.{model_name} not found, skipping...{RESET}")
                continue

            # Build Q query for garbage detection
            q_filter = Q()
            for field in fields:
                # Check if field exists in model
                if not hasattr(Model, field):
                    continue
                
                for keyword in garbage_keywords:
                    # Case-insensitive exact match or with boundaries
                    # Use __icontains for substrings but we'll be strict with keywords
                    q_filter |= Q(**{f"{field}__iexact": keyword})
                    # Also match with spaces around to avoid "contest" matching "test"
                    q_filter |= Q(**{f"{field}__icontains": f" {keyword} "})
                    q_filter |= Q(**{f"{field}__istartswith": f"{keyword} "})
                    q_filter |= Q(**{f"{field}__iendswith": f" {keyword}"})

            # Find garbage records
            garbage_records = Model.objects.filter(q_filter)
            count = garbage_records.count()

            if count > 0:
                self.stdout.write(f"\n{YELLOW}📦 {model_name}: Found {count} garbage record(s){RESET}")
                
                # Show sample records (first 3)
                for record in garbage_records[:3]:
                    display_field = fields[0]
                    display_value = getattr(record, display_field, 'N/A')
                    self.stdout.write(f"   • #{record.pk}: {display_value[:60]}...")
                
                if count > 3:
                    self.stdout.write(f"   ... and {count - 3} more")

                if not dry_run:
                    deleted, _ = garbage_records.delete()
                    total_deleted += deleted
                    self.stdout.write(f"{GREEN}   ✓ Deleted {deleted} record(s){RESET}")
                else:
                    self.stdout.write(f"{YELLOW}   [DRY RUN] Would delete {count} record(s){RESET}")
            else:
                self.stdout.write(f"{GREEN}✅ {model_name}: No garbage data found{RESET}")

        if not dry_run:
            self.stats['test_data_deleted'] = total_deleted
            self.stdout.write(f"\n{GREEN}🗑️  Deleted {total_deleted} garbage record(s) total{RESET}\n")
        else:
            self.stdout.write(f"\n{YELLOW}[DRY RUN] Would delete multiple garbage records{RESET}\n")

    def fix_code_breakpoint(self, dry_run=False):
        """Remove debug breakpoints from forensic_audit.py."""
        self.stdout.write(f"\n{BLUE}{'─'*80}{RESET}")
        self.stdout.write(f"{BOLD}ACTION 3: FIX CODE BREAKPOINT{RESET}\n")
        self.stdout.write(f"{BLUE}{'─'*80}{RESET}\n")

        import os
        from pathlib import Path

        # Locate forensic_audit.py
        base_dir = Path(__file__).resolve().parent.parent.parent.parent
        audit_file = base_dir / 'core' / 'management' / 'commands' / 'forensic_audit.py'

        if not audit_file.exists():
            self.stdout.write(f"{RED}❌ File not found: {audit_file}{RESET}\n")
            return

        self.stdout.write(f"📁 Scanning: {audit_file.relative_to(base_dir)}\n")

        try:
            # Read file
            with open(audit_file, 'r', encoding='utf-8') as f:
                original_content = f.read()
                lines = original_content.split('\n')

            # Find actual breakpoint calls (not in strings or comments)
            breakpoint_lines = []
            cleaned_lines = []
            
            for line_num, line in enumerate(lines, start=1):
                # Skip if it's a comment line
                stripped = line.strip()
                if stripped.startswith('#'):
                    cleaned_lines.append(line)
                    continue
                
                # Check for actual breakpoint calls (not in strings)
                # Match: pdb.set_trace() or breakpoint() as standalone statements
                if re.search(r'^\s*(pdb\.set_trace\(\)|breakpoint\(\))\s*(?:#.*)?$', line):
                    breakpoint_lines.append((line_num, line.strip()))
                    self.stdout.write(f"{YELLOW}   Line {line_num}: {line.strip()}{RESET}")
                    # Skip this line (remove it)
                    continue
                else:
                    cleaned_lines.append(line)

            if not breakpoint_lines:
                self.stdout.write(f"{GREEN}✅ No debug breakpoints found. Code is clean!{RESET}\n")
                return

            self.stdout.write(f"\n{YELLOW}📊 Found {len(breakpoint_lines)} debug breakpoint(s){RESET}\n")

            if not dry_run:
                # Write cleaned content back
                cleaned_content = '\n'.join(cleaned_lines)
                with open(audit_file, 'w', encoding='utf-8') as f:
                    f.write(cleaned_content)

                self.stats['breakpoints_removed'] = len(breakpoint_lines)
                self.stdout.write(f"{GREEN}✅ Removed {len(breakpoint_lines)} debug breakpoint(s) from audit script{RESET}\n")
            else:
                self.stdout.write(f"{YELLOW}[DRY RUN] Would remove {len(breakpoint_lines)} breakpoint(s){RESET}\n")

        except Exception as e:
            self.stdout.write(f"{RED}❌ Error fixing code breakpoint: {str(e)}{RESET}\n")
            raise

    def print_summary(self, dry_run=False):
        """Print execution summary."""
        self.stdout.write(f"\n{CYAN}{'='*80}{RESET}")
        self.stdout.write(f"{BOLD}{CYAN}EXECUTION SUMMARY{RESET}\n")
        self.stdout.write(f"{CYAN}{'='*80}{RESET}\n")

        if dry_run:
            self.stdout.write(f"{YELLOW}Mode: DRY RUN (No changes made){RESET}\n")
        else:
            self.stdout.write(f"{GREEN}Mode: LIVE EXECUTION{RESET}\n")

        self.stdout.write(f"\n{BOLD}Results:{RESET}")
        self.stdout.write(f"  • Orphan Projects Fixed: {self.stats['orphan_projects_fixed']}")
        self.stdout.write(f"  • Test Data Deleted: {self.stats['test_data_deleted']}")
        self.stdout.write(f"  • Breakpoints Removed: {self.stats['breakpoints_removed']}")

        if not dry_run:
            total_actions = sum(self.stats.values())
            if total_actions > 0:
                self.stdout.write(f"\n{GREEN}✅ Successfully completed {total_actions} fix action(s)!{RESET}")
            else:
                self.stdout.write(f"\n{GREEN}✅ Database integrity check complete. No issues found!{RESET}")
        else:
            self.stdout.write(f"\n{YELLOW}ℹ️  Run without --dry-run to apply changes{RESET}")

        self.stdout.write(f"\n{CYAN}{'='*80}{RESET}\n")
