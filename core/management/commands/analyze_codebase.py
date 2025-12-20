"""
Django Management Command: Codebase Quality Analysis
====================================================

Purpose: Identify orphan (unused) and redundant (duplicate) functions in core/

Actions:
1. Scan for unused functions/classes (orphans)
2. Detect duplicate functions with >85% similarity
3. Generate ORPHAN_REPORT.md with actionable findings

Author: Senior Python Code Quality Specialist
Date: 2025-11-29
"""

import ast
from collections import defaultdict
from datetime import datetime
from difflib import SequenceMatcher
from pathlib import Path

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


class CodeAnalyzer:
    """Static analysis engine for Python code quality."""

    # Django standard methods that should never be flagged as orphans
    DJANGO_STANDARD_METHODS = {
        # HTTP methods
        'get', 'post', 'put', 'patch', 'delete', 'head', 'options', 'trace',
        # Model methods
        'save', 'clean', '__str__', '__repr__', '__init__',
        'get_absolute_url', 'get_queryset', 'get_context_data',
        # Form methods
        'clean_<field>', 'save_model', 'has_add_permission', 'has_change_permission',
        'has_delete_permission', 'has_module_permission',
        # Serializer methods
        'create', 'update', 'validate', 'to_representation', 'to_internal_value',
        # Admin methods
        'delete_model', 'save_formset', # Management command
        'handle', 'add_arguments',
        # Test methods
        'setUp', 'tearDown', 'setUpClass', 'tearDownClass',
        'setUpTestData', 'test_', # Signal handlers
        'pre_save', 'post_save', 'pre_delete', 'post_delete',
        # View methods
        'dispatch', 'get_success_url', 'form_valid', 'form_invalid',
        'get_form', 'get_form_kwargs', 'get_initial',
        # Middleware
        'process_request', 'process_view', 'process_template_response',
        'process_response', 'process_exception',
        # WebSocket consumers
        'connect', 'disconnect', 'receive',
        # Celery tasks
        'run', 'on_success', 'on_failure', 'on_retry',
    }

    def __init__(self, base_dir):
        self.base_dir = Path(base_dir)
        self.core_dir = self.base_dir / 'core'
        self.all_python_files = []
        self.definitions = defaultdict(list)  # function/class -> [(file, line, code)]
        self.usages = defaultdict(set)  # function/class -> set(files_using_it)
        self.orphans = []
        self.duplicates = []

    def is_django_standard_method(self, name):
        """Check if function name matches Django standard patterns."""
        if name in self.DJANGO_STANDARD_METHODS:
            return True
        # Check patterns
        if name.startswith('test_'):
            return True
        if name.startswith('clean_') and name != 'clean':
            return True
        if name.startswith('get_') or name.startswith('has_'):
            return True
        if name.startswith('save_') or name.startswith('delete_'):
            return True
        return False

    def should_skip_file(self, filepath):
        """Check if file should be excluded from analysis."""
        path_str = str(filepath)

        # Skip migrations
        if '/migrations/' in path_str:
            return True

        # Skip test files (analyzed separately)
        if '/tests/' in path_str or path_str.endswith('_test.py'):
            return True

        # Skip virtual environment
        if '/.venv/' in path_str or '/venv/' in path_str:
            return True

        # Skip __pycache__
        if '__pycache__' in path_str:
            return True

        # Skip staticfiles
        if '/staticfiles/' in path_str or '/static/' in path_str:
            return True

        return False

    def extract_function_body(self, node):
        """Extract clean function body as string."""
        try:
            # Get source segment if available
            body_lines = []
            for item in node.body:
                # Convert AST node back to approximate source
                if isinstance(item, ast.Expr) and isinstance(item.value, ast.Str):
                    # Docstring
                    continue
                body_lines.append(ast.unparse(item))
            return '\n'.join(body_lines)
        except:
            # Fallback: use AST dump
            return ast.dump(node)

    def get_function_signature(self, node):
        """Get function signature for comparison."""
        args = []
        if isinstance(node, ast.FunctionDef):
            for arg in node.args.args:
                args.append(arg.arg)
        return f"{node.name}({', '.join(args)})"

    def scan_definitions(self, filepath):
        """Scan file for function and class definitions."""
        try:
            with open(filepath, encoding='utf-8', errors='ignore') as f:
                content = f.read()

            tree = ast.parse(content, filename=str(filepath))

            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    name = node.name
                    line = node.lineno

                    # Skip Django standard methods
                    if self.is_django_standard_method(name):
                        continue

                    # Skip private methods (internal use)
                    if name.startswith('_') and not name.startswith('__'):
                        continue

                    # Extract body for similarity comparison
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        body = self.extract_function_body(node)
                        signature = self.get_function_signature(node)
                    else:
                        body = ''
                        signature = f"class {name}"

                    self.definitions[name].append({
                        'file': filepath,
                        'line': line,
                        'body': body,
                        'signature': signature,
                        'type': 'function' if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) else 'class'
                    })

        except SyntaxError:
            # Skip files with syntax errors
            pass
        except Exception:
            # Skip problematic files
            pass

    def scan_usages(self, filepath):
        """Scan file for function/class usage (imports and calls)."""
        try:
            with open(filepath, encoding='utf-8', errors='ignore') as f:
                content = f.read()

            tree = ast.parse(content, filename=str(filepath))

            # Track imports
            for node in ast.walk(tree):
                # Import statements
                if isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom):
                    for alias in node.names:
                        self.usages[alias.name].add(str(filepath))

                # Function calls
                elif isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        self.usages[node.func.id].add(str(filepath))
                    elif isinstance(node.func, ast.Attribute):
                        self.usages[node.func.attr].add(str(filepath))

                # Name references
                elif isinstance(node, ast.Name):
                    self.usages[node.id].add(str(filepath))

        except:
            pass

    def find_orphans(self):
        """Identify functions/classes that are defined but never used."""
        for name, defs in self.definitions.items():
            # Skip if only one definition (likely intentional)
            if len(defs) > 1:
                continue

            definition = defs[0]
            def_file = str(definition['file'])

            # Get all files that use this name
            usage_files = self.usages.get(name, set())

            # Remove self-reference (definition file)
            usage_files = {f for f in usage_files if f != def_file}

            # If no external usage, it's an orphan
            if not usage_files:
                self.orphans.append({
                    'name': name,
                    'file': definition['file'],
                    'line': definition['line'],
                    'type': definition['type'],
                    'signature': definition['signature']
                })

    def calculate_similarity(self, code1, code2):
        """Calculate similarity ratio between two code snippets."""
        if not code1 or not code2:
            return 0.0

        # Normalize whitespace
        code1 = ' '.join(code1.split())
        code2 = ' '.join(code2.split())

        return SequenceMatcher(None, code1, code2).ratio()

    def find_duplicates(self):
        """Identify duplicate functions with >85% similarity."""
        # Only compare functions with multiple definitions
        for name, defs in self.definitions.items():
            if len(defs) < 2:
                continue

            # Skip if all definitions are in the same file (legitimate overloading)
            files = {str(d['file']) for d in defs}
            if len(files) == 1:
                continue

            # Compare all pairs
            for i, def1 in enumerate(defs):
                for def2 in defs[i+1:]:
                    # Skip if same file
                    if def1['file'] == def2['file']:
                        continue

                    # Calculate similarity
                    similarity = self.calculate_similarity(def1['body'], def2['body'])

                    if similarity >= 0.85:
                        self.duplicates.append({
                            'name': name,
                            'file1': def1['file'],
                            'line1': def1['line'],
                            'signature1': def1['signature'],
                            'file2': def2['file'],
                            'line2': def2['line'],
                            'signature2': def2['signature'],
                            'similarity': similarity * 100
                        })

    def analyze(self):
        """Run complete analysis."""
        print(f"{CYAN}Scanning core/ directory...{RESET}")

        # Get all Python files
        self.all_python_files = list(self.core_dir.rglob('*.py'))
        self.all_python_files = [f for f in self.all_python_files if not self.should_skip_file(f)]

        print(f"{BLUE}Found {len(self.all_python_files)} Python files to analyze{RESET}\n")

        # Phase 1: Scan definitions
        print(f"{YELLOW}Phase 1: Scanning definitions...{RESET}")
        for filepath in self.all_python_files:
            self.scan_definitions(filepath)
        print(f"{GREEN}✓ Found {len(self.definitions)} unique names{RESET}\n")

        # Phase 2: Scan usages
        print(f"{YELLOW}Phase 2: Scanning usages...{RESET}")
        # Scan entire project (not just core/)
        all_project_files = list(self.base_dir.rglob('*.py'))
        all_project_files = [f for f in all_project_files if not self.should_skip_file(f)]

        for filepath in all_project_files:
            self.scan_usages(filepath)
        print(f"{GREEN}✓ Scanned {len(all_project_files)} files for usage{RESET}\n")

        # Phase 3: Find orphans
        print(f"{YELLOW}Phase 3: Identifying orphans...{RESET}")
        self.find_orphans()
        print(f"{GREEN}✓ Found {len(self.orphans)} orphan candidates{RESET}\n")

        # Phase 4: Find duplicates
        print(f"{YELLOW}Phase 4: Detecting duplicates...{RESET}")
        self.find_duplicates()
        print(f"{GREEN}✓ Found {len(self.duplicates)} duplicate pairs{RESET}\n")


class Command(BaseCommand):
    help = 'Analyze codebase for orphan and redundant functions'

    def handle(self, *args, **options):
        self.stdout.write(f"\n{CYAN}{'='*80}{RESET}")
        self.stdout.write(f"{BOLD}{CYAN}CODEBASE QUALITY ANALYSIS{RESET}")
        self.stdout.write(f"{CYAN}Code Hygiene & Redundancy Detection{RESET}")
        self.stdout.write(f"{CYAN}{'='*80}{RESET}\n")

        # Get base directory
        base_dir = Path(__file__).resolve().parent.parent.parent.parent

        # Initialize analyzer
        analyzer = CodeAnalyzer(base_dir)

        # Run analysis
        analyzer.analyze()

        # Generate report
        self.generate_report(analyzer, base_dir)

        # Summary
        self.print_summary(analyzer)

    def generate_report(self, analyzer, base_dir):
        """Generate ORPHAN_REPORT.md file."""
        report_path = base_dir / 'ORPHAN_REPORT.md'

        self.stdout.write(f"{YELLOW}Generating report...{RESET}")

        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("# Codebase Quality Analysis Report\n\n")
            f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("**Analyzer:** Code Quality Specialist v1.0\n\n")
            f.write("---\n\n")

            # Executive Summary
            f.write("## Executive Summary\n\n")
            f.write(f"- **Files Analyzed:** {len(analyzer.all_python_files)}\n")
            f.write(f"- **Unique Definitions:** {len(analyzer.definitions)}\n")
            f.write(f"- **Orphan Candidates:** {len(analyzer.orphans)}\n")
            f.write(f"- **Duplicate Pairs:** {len(analyzer.duplicates)}\n\n")

            # Orphans Section
            f.write("---\n\n")
            f.write("## 📦 Candidates for Deletion (Orphans)\n\n")
            f.write("*Functions/classes defined but never imported or used elsewhere.*\n\n")

            if analyzer.orphans:
                # Group by file
                orphans_by_file = defaultdict(list)
                for orphan in analyzer.orphans:
                    rel_path = orphan['file'].relative_to(base_dir)
                    orphans_by_file[rel_path].append(orphan)

                for filepath in sorted(orphans_by_file.keys()):
                    f.write(f"### `{filepath}`\n\n")
                    for orphan in orphans_by_file[filepath]:
                        f.write(f"- **{orphan['type'].title()}:** `{orphan['signature']}` (Line {orphan['line']})\n")
                    f.write("\n")

                f.write(f"**Total Orphans:** {len(analyzer.orphans)}\n\n")
            else:
                f.write("✅ **No orphan functions found!** All code appears to be in use.\n\n")

            # Duplicates Section
            f.write("---\n\n")
            f.write("## 🔄 Candidates for Merging (Duplicates)\n\n")
            f.write("*Function pairs with >85% code similarity.*\n\n")

            if analyzer.duplicates:
                # Group by name
                duplicates_by_name = defaultdict(list)
                for dup in analyzer.duplicates:
                    duplicates_by_name[dup['name']].append(dup)

                for name in sorted(duplicates_by_name.keys()):
                    f.write(f"### Group: `{name}`\n\n")
                    for dup in duplicates_by_name[name]:
                        file1_rel = dup['file1'].relative_to(base_dir)
                        file2_rel = dup['file2'].relative_to(base_dir)

                        f.write(f"- **Similarity:** {dup['similarity']:.1f}%\n")
                        f.write(f"  - **Location 1:** `{file1_rel}:{dup['line1']}` - `{dup['signature1']}`\n")
                        f.write(f"  - **Location 2:** `{file2_rel}:{dup['line2']}` - `{dup['signature2']}`\n")
                        f.write("\n")

                f.write(f"**Total Duplicate Pairs:** {len(analyzer.duplicates)}\n\n")
            else:
                f.write("✅ **No high-similarity duplicates found!** Code appears well-organized.\n\n")

            # Recommendations
            f.write("---\n\n")
            f.write("## 💡 Recommendations\n\n")

            if analyzer.orphans:
                f.write("### Orphan Functions\n\n")
                f.write("**Action Plan:**\n")
                f.write("1. Review each orphan to confirm it's truly unused\n")
                f.write("2. Check if it's a utility function that should be used\n")
                f.write("3. If confirmed unused, create a cleanup PR\n")
                f.write("4. Consider if removal breaks any external integrations\n\n")

            if analyzer.duplicates:
                f.write("### Duplicate Functions\n\n")
                f.write("**Action Plan:**\n")
                f.write("1. Compare implementations to identify the better version\n")
                f.write("2. Extract common logic to a shared utility module\n")
                f.write("3. Update all call sites to use the consolidated function\n")
                f.write("4. Remove redundant implementations\n")
                f.write("5. Add unit tests to prevent future duplication\n\n")

            if not analyzer.orphans and not analyzer.duplicates:
                f.write("✅ **Codebase is clean!** No immediate action required.\n\n")

            # Footer
            f.write("---\n\n")
            f.write("*This report is generated automatically. Manual review is recommended before taking action.*\n")

        self.stdout.write(f"{GREEN}✓ Report saved to: {report_path}{RESET}\n")

    def print_summary(self, analyzer):
        """Print execution summary."""
        self.stdout.write(f"\n{CYAN}{'='*80}{RESET}")
        self.stdout.write(f"{BOLD}{CYAN}ANALYSIS COMPLETE{RESET}\n")
        self.stdout.write(f"{CYAN}{'='*80}{RESET}\n")

        self.stdout.write(f"\n{BOLD}Scan Results:{RESET}")
        self.stdout.write(f"  • Python Files Scanned: {len(analyzer.all_python_files)}")
        self.stdout.write(f"  • Unique Definitions: {len(analyzer.definitions)}")
        self.stdout.write(f"  • Orphan Candidates: {len(analyzer.orphans)}")
        self.stdout.write(f"  • Duplicate Pairs: {len(analyzer.duplicates)}")

        if analyzer.orphans or analyzer.duplicates:
            self.stdout.write(f"\n{YELLOW}⚠️  Issues found. Review ORPHAN_REPORT.md for details.{RESET}")
        else:
            self.stdout.write(f"\n{GREEN}✅ Codebase is clean! No orphans or duplicates detected.{RESET}")

        self.stdout.write(f"\n{BOLD}{GREEN}✅ Analysis Complete. Check ORPHAN_REPORT.md to make decisions.{RESET}")
        self.stdout.write(f"\n{CYAN}{'='*80}{RESET}\n")
