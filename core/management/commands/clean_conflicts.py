"""
Django Management Command: Clean File Conflicts
===============================================

Purpose: Safely resolve duplicate/conflicting files in core/ directory

Actions:
1. Analyze consumers.py group (backups, fixed versions)
2. Detect models.py vs models/ folder conflict
3. Interactive confirmation before deletion
4. Clear Python cache files after cleanup

Author: Senior Django Cleanup Specialist
Date: 2025-11-29
"""

from datetime import datetime
from pathlib import Path
import shutil

from django.core.management.base import BaseCommand

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
    help = 'Safely resolve duplicate/conflicting files in core/ directory'

    def __init__(self):
        super().__init__()
        self.base_dir = None
        self.core_dir = None
        self.files_to_delete = []
        self.stats = {
            'consumers_cleaned': 0,
            'models_conflict_resolved': False,
            'pyc_files_deleted': 0,
        }

    def add_arguments(self, parser):
        parser.add_argument(
            '--auto-yes',
            action='store_true',
            help='Automatically answer YES to all prompts (use with caution!)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without actually deleting files',
        )

    def handle(self, *args, **options):
        auto_yes = options.get('auto_yes', False)
        dry_run = options.get('dry_run', False)

        self.stdout.write(f"\n{CYAN}{'='*80}{RESET}")
        self.stdout.write(f"{BOLD}{CYAN}DJANGO CLEANUP SPECIALIST{RESET}")
        self.stdout.write(f"{CYAN}File Conflict Resolution{RESET}")
        self.stdout.write(f"{CYAN}{'='*80}{RESET}\n")

        if dry_run:
            self.stdout.write(f"{YELLOW}🔍 DRY RUN MODE - No files will be deleted{RESET}\n")

        if auto_yes:
            self.stdout.write(f"{YELLOW}⚠️  AUTO-YES MODE - All deletions will be confirmed automatically{RESET}\n")

        # Get directories
        self.base_dir = Path(__file__).resolve().parent.parent.parent.parent
        self.core_dir = self.base_dir / 'core'

        # Analysis Phase
        self.stdout.write(f"{BLUE}{'─'*80}{RESET}")
        self.stdout.write(f"{BOLD}PHASE 1: ANALYZING FILES{RESET}\n")
        self.stdout.write(f"{BLUE}{'─'*80}{RESET}\n")

        # Step 1: Analyze consumers.py group
        self.analyze_consumers_group(auto_yes, dry_run)

        # Step 2: Analyze models.py structure
        self.analyze_models_structure(auto_yes, dry_run)

        # Execution Phase
        if self.files_to_delete:
            self.stdout.write(f"\n{BLUE}{'─'*80}{RESET}")
            self.stdout.write(f"{BOLD}PHASE 2: CLEANUP EXECUTION{RESET}\n")
            self.stdout.write(f"{BLUE}{'─'*80}{RESET}\n")

            self.execute_cleanup(dry_run)
        else:
            self.stdout.write(f"\n{GREEN}✅ No conflicts found. Codebase is clean!{RESET}\n")

        # Clear cache
        self.stdout.write(f"\n{BLUE}{'─'*80}{RESET}")
        self.stdout.write(f"{BOLD}PHASE 3: CACHE CLEANUP{RESET}\n")
        self.stdout.write(f"{BLUE}{'─'*80}{RESET}\n")
        self.clear_python_cache(dry_run)

        # Summary
        self.print_summary(dry_run)

    def get_file_info(self, filepath):
        """Get file size and last modified date."""
        if not filepath.exists():
            return None

        stat = filepath.stat()
        size_kb = stat.st_size / 1024
        modified = datetime.fromtimestamp(stat.st_mtime)

        return {
            'path': filepath,
            'size_kb': size_kb,
            'modified': modified,
            'name': filepath.name
        }

    def analyze_consumers_group(self, auto_yes, dry_run):
        """Analyze consumers.py and its variants."""
        self.stdout.write(f"\n{YELLOW}Step 1: Analyzing consumers.py group...{RESET}\n")

        # Find all consumers*.py files
        consumers_files = list(self.core_dir.glob('consumers*.py'))

        if not consumers_files:
            self.stdout.write(f"{GREEN}✓ No consumers.py files found{RESET}\n")
            return

        if len(consumers_files) == 1:
            self.stdout.write(f"{GREEN}✓ Only one consumers.py file found (no duplicates){RESET}\n")
            return

        self.stdout.write(f"{RED}⚠️  Found {len(consumers_files)} consumer file(s):{RESET}\n\n")

        # Gather file info
        file_infos = []
        for f in sorted(consumers_files):
            info = self.get_file_info(f)
            if info:
                file_infos.append(info)

        # Display files with details
        main_file = None
        backup_files = []

        for idx, info in enumerate(file_infos, start=1):
            name = info['name']
            size = info['size_kb']
            modified = info['modified'].strftime('%Y-%m-%d %H:%M:%S')

            # Determine if this is the main file or backup
            is_main = name == 'consumers.py'
            is_backup = '.broken' in name or '_fixed' in name or '_backup' in name

            status = ""
            if is_main:
                status = f"{GREEN}KEEP (Main File){RESET}"
                main_file = info
            elif is_backup:
                status = f"{RED}BACKUP/DELETE?{RESET}"
                backup_files.append(info)
            else:
                status = f"{YELLOW}UNKNOWN{RESET}"

            self.stdout.write(f"  {idx}. {BOLD}{name}{RESET}")
            self.stdout.write(f"     Size: {size:.1f} KB")
            self.stdout.write(f"     Modified: {modified}")
            self.stdout.write(f"     Status: {status}\n")

        if not backup_files:
            self.stdout.write(f"\n{GREEN}✓ No backup files to clean{RESET}\n")
            return

        # Ask for confirmation
        self.stdout.write(f"\n{YELLOW}{'─'*60}{RESET}")
        self.stdout.write(f"{BOLD}Recommended Action:{RESET}")
        self.stdout.write(f"  • KEEP: {GREEN}consumers.py{RESET} (main file)")

        for backup in backup_files:
            self.stdout.write(f"  • DELETE: {RED}{backup['name']}{RESET} (backup/old version)")

        self.stdout.write(f"{YELLOW}{'─'*60}{RESET}\n")

        if auto_yes:
            self.stdout.write(f"{YELLOW}[AUTO-YES] Marking backup files for deletion...{RESET}\n")
            for backup in backup_files:
                self.files_to_delete.append(backup['path'])
                self.stats['consumers_cleaned'] += 1
        else:
            response = input(f"{BOLD}Delete backup files? (yes/no): {RESET}").strip().lower()
            if response in ['yes', 'y']:
                for backup in backup_files:
                    self.files_to_delete.append(backup['path'])
                    self.stats['consumers_cleaned'] += 1
                self.stdout.write(f"{GREEN}✓ Backup files marked for deletion{RESET}\n")
            else:
                self.stdout.write(f"{YELLOW}⏭️  Skipped - backup files will be kept{RESET}\n")

    def analyze_models_structure(self, auto_yes, dry_run):
        """Analyze models.py vs models/ folder conflict."""
        self.stdout.write(f"\n{YELLOW}Step 2: Analyzing models.py structure...{RESET}\n")

        models_file = self.core_dir / 'models.py'
        models_dir = self.core_dir / 'models'

        models_file_exists = models_file.exists()
        models_dir_exists = models_dir.exists() and models_dir.is_dir()

        # Check for conflict
        if models_file_exists and models_dir_exists:
            self.stdout.write(f"\n{RED}{'='*80}{RESET}")
            self.stdout.write(f"{BOLD}{RED}⚠️  CRITICAL CONFLICT DETECTED ⚠️{RESET}\n")
            self.stdout.write(f"{RED}{'='*80}{RESET}\n")

            self.stdout.write(f"{YELLOW}You have BOTH:{RESET}")
            self.stdout.write(f"  1. {BOLD}core/models.py{RESET} (file)")

            file_info = self.get_file_info(models_file)
            if file_info:
                self.stdout.write(f"     Size: {file_info['size_kb']:.1f} KB")
                self.stdout.write(f"     Modified: {file_info['modified'].strftime('%Y-%m-%d %H:%M:%S')}")

            self.stdout.write(f"\n  2. {BOLD}core/models/{RESET} (directory)")

            # List files in models/ directory
            model_files = list(models_dir.glob('*.py'))
            model_files = [f for f in model_files if f.name != '__init__.py']
            self.stdout.write(f"     Contains {len(model_files)} module(s):")
            for mf in sorted(model_files)[:5]:
                self.stdout.write(f"       • {mf.name}")
            if len(model_files) > 5:
                self.stdout.write(f"       • ... and {len(model_files) - 5} more")

            self.stdout.write(f"\n{RED}{'─'*80}{RESET}")
            self.stdout.write(f"{BOLD}{RED}Django cannot handle both simultaneously!{RESET}")
            self.stdout.write(f"{YELLOW}This causes import confusion and unpredictable behavior.{RESET}\n")
            self.stdout.write(f"{RED}{'─'*80}{RESET}\n")

            # Recommendations
            self.stdout.write(f"{BOLD}Recommended Solution:{RESET}")
            self.stdout.write(f"\n{GREEN}Option A: Keep Modular Structure (RECOMMENDED){RESET}")
            self.stdout.write("  • KEEP: core/models/ directory")
            self.stdout.write("  • DELETE: core/models.py")
            self.stdout.write("  • Why: Modular structure is better for large projects")
            self.stdout.write("  • Action: models.py should only contain imports from models/")

            self.stdout.write(f"\n{YELLOW}Option B: Keep Monolithic File{RESET}")
            self.stdout.write("  • KEEP: core/models.py")
            self.stdout.write("  • DELETE: core/models/ directory")
            self.stdout.write("  • Why: Simpler structure for small projects")
            self.stdout.write("  • Risk: May lose modular organization work\n")

            if auto_yes:
                self.stdout.write(f"\n{RED}❌ AUTO-YES disabled for this critical decision{RESET}")
                self.stdout.write(f"{YELLOW}Manual intervention required - cannot auto-delete models!{RESET}\n")
                return

            # Manual decision required
            self.stdout.write(f"\n{BOLD}{'─'*80}{RESET}")
            self.stdout.write(f"{BOLD}What do you want to do?{RESET}")
            self.stdout.write("  A) Keep core/models/ directory (delete models.py)")
            self.stdout.write("  B) Keep core/models.py file (delete models/ directory)")
            self.stdout.write("  C) Skip (manual resolution later)")
            self.stdout.write(f"{BOLD}{'─'*80}{RESET}\n")

            response = input(f"{BOLD}Choose option (A/B/C): {RESET}").strip().upper()

            if response == 'A':
                self.stdout.write(f"\n{GREEN}✓ You chose: Keep modular structure (models/ directory){RESET}")
                self.stdout.write(f"{YELLOW}Note: Ensure models.py only contains imports from models/{RESET}\n")

                confirm = input(f"{BOLD}{RED}Confirm deletion of models.py? (type 'DELETE' to confirm): {RESET}").strip()
                if confirm == 'DELETE':
                    self.files_to_delete.append(models_file)
                    self.stats['models_conflict_resolved'] = True
                    self.stdout.write(f"{GREEN}✓ models.py marked for deletion{RESET}\n")
                else:
                    self.stdout.write(f"{YELLOW}⏭️  Aborted - no changes made{RESET}\n")

            elif response == 'B':
                self.stdout.write(f"\n{YELLOW}⚠️  You chose: Keep monolithic file (models.py){RESET}")
                self.stdout.write(f"{RED}Warning: This will delete the modular structure!{RESET}\n")

                confirm = input(f"{BOLD}{RED}Confirm deletion of models/ directory? (type 'DELETE' to confirm): {RESET}").strip()
                if confirm == 'DELETE':
                    self.files_to_delete.append(models_dir)
                    self.stats['models_conflict_resolved'] = True
                    self.stdout.write(f"{GREEN}✓ models/ directory marked for deletion{RESET}\n")
                else:
                    self.stdout.write(f"{YELLOW}⏭️  Aborted - no changes made{RESET}\n")

            else:
                self.stdout.write(f"\n{YELLOW}⏭️  Skipped - you will need to resolve this manually{RESET}")
                self.stdout.write(f"{CYAN}Recommendation: Review your import statements before deciding{RESET}\n")

        elif models_file_exists and not models_dir_exists:
            self.stdout.write(f"{GREEN}✓ Using monolithic models.py structure (no conflicts){RESET}\n")

        elif not models_file_exists and models_dir_exists:
            self.stdout.write(f"{GREEN}✓ Using modular models/ directory structure (no conflicts){RESET}\n")

        else:
            self.stdout.write(f"{RED}❌ Neither models.py nor models/ directory found!{RESET}\n")

    def execute_cleanup(self, dry_run):
        """Execute the actual file deletions."""
        if not self.files_to_delete:
            return

        self.stdout.write(f"\n{YELLOW}Files to be deleted:{RESET}\n")
        for filepath in self.files_to_delete:
            rel_path = filepath.relative_to(self.base_dir)
            if filepath.is_dir():
                self.stdout.write(f"  🗂️  {RED}{rel_path}/{RESET} (directory)")
            else:
                self.stdout.write(f"  📄 {RED}{rel_path}{RESET}")

        if dry_run:
            self.stdout.write(f"\n{YELLOW}[DRY RUN] Files would be deleted (not actually deleting){RESET}\n")
            return

        self.stdout.write(f"\n{BOLD}Deleting files...{RESET}\n")

        for filepath in self.files_to_delete:
            try:
                if filepath.is_dir():
                    shutil.rmtree(filepath)
                    self.stdout.write(f"{GREEN}✓ Deleted directory: {filepath.name}/{RESET}")
                else:
                    filepath.unlink()
                    self.stdout.write(f"{GREEN}✓ Deleted file: {filepath.name}{RESET}")
            except Exception as e:
                self.stdout.write(f"{RED}✗ Failed to delete {filepath.name}: {str(e)}{RESET}")

    def clear_python_cache(self, dry_run):
        """Clear .pyc files and __pycache__ directories."""
        self.stdout.write(f"\n{YELLOW}Clearing Python cache files...{RESET}\n")

        pyc_count = 0
        pycache_count = 0

        # Find and delete .pyc files
        for pyc_file in self.base_dir.rglob('*.pyc'):
            pyc_count += 1
            if not dry_run:
                try:
                    pyc_file.unlink()
                except:
                    pass

        # Find and delete __pycache__ directories
        for pycache_dir in self.base_dir.rglob('__pycache__'):
            if pycache_dir.is_dir():
                pycache_count += 1
                if not dry_run:
                    try:
                        shutil.rmtree(pycache_dir)
                    except:
                        pass

        self.stats['pyc_files_deleted'] = pyc_count

        if dry_run:
            self.stdout.write(f"{YELLOW}[DRY RUN] Would delete:{RESET}")
            self.stdout.write(f"  • {pyc_count} .pyc files")
            self.stdout.write(f"  • {pycache_count} __pycache__ directories\n")
        else:
            self.stdout.write(f"{GREEN}✓ Deleted {pyc_count} .pyc files{RESET}")
            self.stdout.write(f"{GREEN}✓ Deleted {pycache_count} __pycache__ directories{RESET}\n")

    def print_summary(self, dry_run):
        """Print execution summary."""
        self.stdout.write(f"\n{CYAN}{'='*80}{RESET}")
        self.stdout.write(f"{BOLD}{CYAN}CLEANUP SUMMARY{RESET}\n")
        self.stdout.write(f"{CYAN}{'='*80}{RESET}\n")

        if dry_run:
            self.stdout.write(f"{YELLOW}Mode: DRY RUN (No changes made){RESET}\n")
        else:
            self.stdout.write(f"{GREEN}Mode: LIVE EXECUTION{RESET}\n")

        self.stdout.write(f"\n{BOLD}Actions Performed:{RESET}")
        self.stdout.write(f"  • Consumer Backups Cleaned: {self.stats['consumers_cleaned']}")

        if self.stats['models_conflict_resolved']:
            self.stdout.write(f"  • Models Conflict Resolved: {GREEN}Yes{RESET}")
        else:
            self.stdout.write(f"  • Models Conflict Resolved: {YELLOW}No (skipped or none){RESET}")

        self.stdout.write(f"  • Python Cache Cleared: {self.stats['pyc_files_deleted']} files")

        total_actions = self.stats['consumers_cleaned'] + (1 if self.stats['models_conflict_resolved'] else 0)

        if not dry_run and total_actions > 0:
            self.stdout.write(f"\n{GREEN}✅ Cleanup completed successfully!{RESET}")
            self.stdout.write(f"{CYAN}Recommendation: Run 'python manage.py check' to verify Django configuration{RESET}")
        elif dry_run:
            self.stdout.write(f"\n{YELLOW}ℹ️  Run without --dry-run to apply changes{RESET}")
        else:
            self.stdout.write(f"\n{GREEN}✅ No conflicts found. Codebase is clean!{RESET}")

        self.stdout.write(f"\n{CYAN}{'='*80}{RESET}\n")
