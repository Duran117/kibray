"""
Full-Spectrum Forensic Audit Command
Comprehensive 5-Layer Deep Scan for Django Application
"""
from django.core.management.base import BaseCommand
from django.apps import apps
from django.conf import settings
from django.db import connection
from django.db.models import Q, Count, F
from datetime import datetime, timedelta
import os
import re
import ast
import difflib
from pathlib import Path
from collections import defaultdict
import sys


class Command(BaseCommand):
    help = 'Performs full-spectrum forensic audit of entire Django application'

    # ANSI Color Codes
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    RESET = '\033[0m'

    def __init__(self):
        super().__init__()
        self.report = []
        self.issues = {
            'critical': [],
            'high': [],
            'medium': [],
            'low': [],
            'info': []
        }
        self.stats = {
            'files_scanned': 0,
            'py_files': 0,
            'html_files': 0,
            'js_files': 0,
            'models_checked': 0,
            'dead_code_found': 0,
            'todos_found': 0
        }

    def add_issue(self, severity, category, message, file_path=None, line_num=None):
        """Add an issue to the report"""
        issue = {
            'severity': severity,
            'category': category,
            'message': message,
            'file': file_path,
            'line': line_num,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        self.issues[severity].append(issue)

    def write_section_header(self, title, level=1):
        """Write a section header to the report"""
        if level == 1:
            self.report.append(f"\n{'=' * 80}\n")
            self.report.append(f"# {title}\n")
            self.report.append(f"{'=' * 80}\n\n")
        elif level == 2:
            self.report.append(f"\n## {title}\n")
            self.report.append(f"{'-' * 60}\n\n")
        else:
            self.report.append(f"\n### {title}\n\n")

    def scan_python_files(self):
        """LAYER 1: Python Logic & Hygiene"""
        self.stdout.write(f"\n{self.BOLD}{self.BLUE}LAYER 1: PYTHON LOGIC & HYGIENE{self.RESET}")
        self.write_section_header("LAYER 1: PYTHON LOGIC & HYGIENE", 1)

        base_dir = Path(settings.BASE_DIR)
        py_files = list(base_dir.rglob('*.py'))
        
        # Exclude migrations, __pycache__, venv
        py_files = [
            f for f in py_files 
            if 'migrations' not in str(f) 
            and '__pycache__' not in str(f)
            and '.venv' not in str(f)
            and 'venv' not in str(f)
        ]
        
        self.stats['py_files'] = len(py_files)
        self.stdout.write(f"Scanning {len(py_files)} Python files...")

        defined_functions = {}  # {function_name: [file_paths]}
        defined_classes = {}  # {class_name: [file_paths]}
        all_code_content = []  # For similarity check
        
        for py_file in py_files:
            self.stats['files_scanned'] += 1
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    all_code_content.append((str(py_file), content))
                
                # Check for print statements (should use logging)
                print_matches = re.finditer(r'^\s*print\s*\(', content, re.MULTILINE)
                for match in print_matches:
                    line_num = content[:match.start()].count('\n') + 1
                    self.add_issue(
                        'low',
                        'Code Hygiene',
                        f"Found print() statement (use logging instead)",
                        str(py_file.relative_to(base_dir)),
                        line_num
                    )
                
                # Check for pdb.set_trace()
                if 'pdb.set_trace()' in content or 'breakpoint()' in content:
                    line_num = content.find('pdb.set_trace()')
                    if line_num == -1:
                        line_num = content.find('breakpoint()')
                    line_num = content[:line_num].count('\n') + 1 if line_num != -1 else 0
                    self.add_issue(
                        'high',
                        'Debug Code',
                        "Found debug breakpoint (pdb.set_trace() or breakpoint())",
                        str(py_file.relative_to(base_dir)),
                        line_num
                    )
                
                # Parse AST to find defined functions and classes
                try:
                    tree = ast.parse(content)
                    for node in ast.walk(tree):
                        if isinstance(node, ast.FunctionDef):
                            if node.name not in defined_functions:
                                defined_functions[node.name] = []
                            defined_functions[node.name].append(str(py_file.relative_to(base_dir)))
                        elif isinstance(node, ast.ClassDef):
                            if node.name not in defined_classes:
                                defined_classes[node.name] = []
                            defined_classes[node.name].append(str(py_file.relative_to(base_dir)))
                except SyntaxError:
                    self.add_issue(
                        'high',
                        'Syntax Error',
                        "File contains syntax errors",
                        str(py_file.relative_to(base_dir)),
                        None
                    )
                    
            except Exception as e:
                self.add_issue(
                    'medium',
                    'File Read Error',
                    f"Could not read file: {str(e)}",
                    str(py_file.relative_to(base_dir)),
                    None
                )
        
        # Check for duplicate function/class names
        self.report.append("### Duplicate Definitions\n\n")
        for func_name, files in defined_functions.items():
            if len(files) > 1:
                self.add_issue(
                    'medium',
                    'Code Redundancy',
                    f"Function '{func_name}' defined in multiple files: {', '.join(files)}",
                    None,
                    None
                )
                self.report.append(f"- **Function**: `{func_name}` in {len(files)} files\n")
        
        for class_name, files in defined_classes.items():
            if len(files) > 1 and class_name != 'Meta':  # Meta is common in models
                self.add_issue(
                    'medium',
                    'Code Redundancy',
                    f"Class '{class_name}' defined in multiple files: {', '.join(files)}",
                    None,
                    None
                )
                self.report.append(f"- **Class**: `{class_name}` in {len(files)} files\n")
        
        # Module 25 Specific Checks
        self.report.append("\n### Module 25 Specific Checks\n\n")
        try:
            PowerAction = apps.get_model('core', 'PowerAction')
            self.report.append("✓ **PowerAction model exists**\n")
            
            # Check for specific fields
            fields = [f.name for f in PowerAction._meta.get_fields()]
            if 'is_frog' in fields:
                self.report.append("✓ **PowerAction.is_frog field exists**\n")
            else:
                self.add_issue(
                    'critical',
                    'Module 25',
                    "PowerAction model missing 'is_frog' field",
                    None,
                    None
                )
                self.report.append("✗ **PowerAction.is_frog field MISSING**\n")
            
            if 'micro_steps' in fields:
                self.report.append("✓ **PowerAction.micro_steps field exists**\n")
            else:
                self.add_issue(
                    'critical',
                    'Module 25',
                    "PowerAction model missing 'micro_steps' field",
                    None,
                    None
                )
                self.report.append("✗ **PowerAction.micro_steps field MISSING**\n")
                
        except LookupError:
            self.add_issue(
                'critical',
                'Module 25',
                "PowerAction model does not exist",
                None,
                None
            )
            self.report.append("✗ **PowerAction model DOES NOT EXIST**\n")

    def scan_templates(self):
        """LAYER 2: Template Integrity"""
        self.stdout.write(f"\n{self.BOLD}{self.CYAN}LAYER 2: TEMPLATE INTEGRITY{self.RESET}")
        self.write_section_header("LAYER 2: TEMPLATE INTEGRITY", 1)

        base_dir = Path(settings.BASE_DIR)
        html_files = list(base_dir.rglob('*.html'))
        
        self.stats['html_files'] = len(html_files)
        self.stdout.write(f"Scanning {len(html_files)} HTML templates...")

        for html_file in html_files:
            self.stats['files_scanned'] += 1
            try:
                with open(html_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                rel_path = str(html_file.relative_to(base_dir))
                
                # Check for placeholder variables
                placeholder_patterns = [
                    r'{{\s*(todo|test|placeholder|example|dummy|xxx)\s*}}',
                    r'{{\s*variable\s*}}',
                    r'{{\s*value\s*}}'
                ]
                for pattern in placeholder_patterns:
                    matches = re.finditer(pattern, content, re.IGNORECASE)
                    for match in matches:
                        line_num = content[:match.start()].count('\n') + 1
                        self.add_issue(
                            'medium',
                            'Template Quality',
                            f"Placeholder variable detected: {match.group()}",
                            rel_path,
                            line_num
                        )
                
                # Check for dead links
                dead_link_patterns = [
                    (r'href\s*=\s*["\']#["\']', 'Empty href="#"'),
                    (r'src\s*=\s*["\']["\']', 'Empty src=""'),
                    (r'action\s*=\s*["\']["\']', 'Empty action=""')
                ]
                for pattern, description in dead_link_patterns:
                    matches = re.finditer(pattern, content, re.IGNORECASE)
                    for match in matches:
                        line_num = content[:match.start()].count('\n') + 1
                        self.add_issue(
                            'low',
                            'Dead Links',
                            description,
                            rel_path,
                            line_num
                        )
                
                # Check for hardcoded URLs
                hardcoded_url_pattern = r'(href|src|action)\s*=\s*["\']/([\w/\-]+)["\']'
                matches = re.finditer(hardcoded_url_pattern, content)
                for match in matches:
                    # Ignore static files and media
                    url = match.group(2)
                    if not any(x in url for x in ['static', 'media', 'admin']):
                        line_num = content[:match.start()].count('\n') + 1
                        self.add_issue(
                            'medium',
                            'Hardcoded URLs',
                            f"Hardcoded URL '/{url}' (use {{% url %}} tag)",
                            rel_path,
                            line_num
                        )
                
                # Module 25 UI Check - Dashboard admin
                if 'dashboard_admin.html' in str(html_file):
                    self.report.append("\n### Module 25 Dashboard Widget Check\n\n")
                    if '🐸' in content or 'frog' in content.lower():
                        self.report.append("✓ **Dashboard contains Frog widget reference**\n")
                    else:
                        self.add_issue(
                            'high',
                            'Module 25 UI',
                            "dashboard_admin.html missing Frog (🐸) widget",
                            rel_path,
                            None
                        )
                        self.report.append("✗ **Dashboard missing Frog widget**\n")
                    
                    if 'strategicFocusWidget' in content or 'Strategic Focus' in content:
                        self.report.append("✓ **Dashboard contains Strategic Focus widget**\n")
                    else:
                        self.add_issue(
                            'high',
                            'Module 25 UI',
                            "dashboard_admin.html missing Strategic Focus widget",
                            rel_path,
                            None
                        )
                        self.report.append("✗ **Dashboard missing Strategic Focus widget**\n")
                        
            except Exception as e:
                self.add_issue(
                    'medium',
                    'File Read Error',
                    f"Could not read template: {str(e)}",
                    str(html_file.relative_to(base_dir)),
                    None
                )

    def scan_database(self):
        """LAYER 3: Database Health"""
        self.stdout.write(f"\n{self.BOLD}{self.MAGENTA}LAYER 3: DATABASE HEALTH{self.RESET}")
        self.write_section_header("LAYER 3: DATABASE HEALTH", 1)

        all_models = apps.get_models()
        self.stats['models_checked'] = len(all_models)
        
        self.stdout.write(f"Scanning {len(all_models)} models...")

        # Sanity Check: Test data
        self.report.append("### Test Data Detection\n\n")
        test_patterns = ['test', 'asdf', 'temp', 'xxx', 'dummy', 'placeholder']
        
        for model in all_models:
            try:
                # Get text fields
                text_fields = [
                    f for f in model._meta.get_fields() 
                    if f.get_internal_type() in ['CharField', 'TextField']
                ]
                
                for field in text_fields:
                    if not field.is_relation:
                        for pattern in test_patterns:
                            try:
                                filter_kwargs = {f"{field.name}__icontains": pattern}
                                count = model.objects.filter(**filter_kwargs).count()
                                if count > 0:
                                    self.add_issue(
                                        'low',
                                        'Test Data',
                                        f"{model.__name__}.{field.name} contains '{pattern}' ({count} records)",
                                        None,
                                        None
                                    )
                                    self.report.append(f"- **{model.__name__}.{field.name}**: {count} records with '{pattern}'\n")
                            except Exception:
                                pass  # Skip if filtering fails
                                
            except Exception as e:
                pass  # Skip models that can't be queried
        
        # Logic Check: Negative numbers in price/quantity fields
        self.report.append("\n### Negative Values Check\n\n")
        
        for model in all_models:
            model_name = model.__name__
            try:
                # Check for price/quantity/amount fields
                numeric_fields = [
                    f for f in model._meta.get_fields()
                    if f.get_internal_type() in ['DecimalField', 'FloatField', 'IntegerField']
                    and any(keyword in f.name.lower() for keyword in ['price', 'quantity', 'amount', 'cost', 'budget'])
                ]
                
                for field in numeric_fields:
                    try:
                        filter_kwargs = {f"{field.name}__lt": 0}
                        count = model.objects.filter(**filter_kwargs).count()
                        if count > 0:
                            self.add_issue(
                                'medium',
                                'Data Integrity',
                                f"{model_name}.{field.name} has {count} negative values",
                                None,
                                None
                            )
                            self.report.append(f"- **{model_name}.{field.name}**: {count} negative values\n")
                    except Exception:
                        pass
                        
            except Exception:
                pass
        
        # Orphans Check: Active Projects without Clients
        self.report.append("\n### Orphaned Records Check\n\n")
        
        try:
            Project = apps.get_model('core', 'Project')
            # Check for projects without clients
            orphaned_projects = Project.objects.filter(client__isnull=True).count()
            if orphaned_projects > 0:
                self.add_issue(
                    'high',
                    'Data Integrity',
                    f"{orphaned_projects} Projects exist without Clients",
                    None,
                    None
                )
                self.report.append(f"- **Orphaned Projects**: {orphaned_projects} projects without clients\n")
            else:
                self.report.append("✓ No orphaned projects found\n")
        except LookupError:
            self.report.append("⚠ Project model not found\n")

    def scan_business_rules(self):
        """LAYER 4: Business Rules"""
        self.stdout.write(f"\n{self.BOLD}{self.YELLOW}LAYER 4: BUSINESS RULES{self.RESET}")
        self.write_section_header("LAYER 4: BUSINESS RULES", 1)

        # Productivity Module Rules
        self.report.append("### Module 25 Business Rules\n\n")
        
        try:
            PowerAction = apps.get_model('core', 'PowerAction')
            
            # Rule 1: Frogs must be scheduled
            unscheduled_frogs = PowerAction.objects.filter(
                is_frog=True,
                scheduled_start__isnull=True
            ).count()
            
            if unscheduled_frogs > 0:
                self.add_issue(
                    'critical',
                    'Business Rule Violation',
                    f"{unscheduled_frogs} PowerActions marked as Frog have no scheduled_start",
                    None,
                    None
                )
                self.report.append(f"✗ **{unscheduled_frogs} Frogs without schedule** (CRITICAL)\n")
            else:
                self.report.append("✓ All Frogs are properly scheduled\n")
            
            # Rule 2: Check for multiple Frogs per session
            from django.db.models import Count
            sessions_with_multiple_frogs = PowerAction.objects.filter(
                is_frog=True
            ).values('session').annotate(
                frog_count=Count('id')
            ).filter(frog_count__gt=1).count()
            
            if sessions_with_multiple_frogs > 0:
                self.add_issue(
                    'critical',
                    'Business Rule Violation',
                    f"{sessions_with_multiple_frogs} sessions have multiple Frogs (only 1 allowed)",
                    None,
                    None
                )
                self.report.append(f"✗ **{sessions_with_multiple_frogs} sessions with multiple Frogs** (CRITICAL)\n")
            else:
                self.report.append("✓ No sessions with multiple Frogs\n")
                
        except LookupError:
            self.report.append("⚠ PowerAction model not found\n")
        
        try:
            LifeVision = apps.get_model('core', 'LifeVision')
            
            # Rule 3: Life Visions must have deep_why
            visions_without_why = LifeVision.objects.filter(
                Q(deep_why__isnull=True) | Q(deep_why='') | Q(deep_why__icontains='test')
            ).count()
            
            if visions_without_why > 0:
                self.add_issue(
                    'critical',
                    'Business Rule Violation',
                    f"{visions_without_why} LifeVision goals exist without meaningful deep_why",
                    None,
                    None
                )
                self.report.append(f"✗ **{visions_without_why} Visions without deep_why** (CRITICAL)\n")
            else:
                self.report.append("✓ All Life Visions have deep_why\n")
                
        except LookupError:
            self.report.append("⚠ LifeVision model not found\n")
        
        # Habits Check
        self.report.append("\n### Habit Tracking Rules\n\n")
        
        try:
            ExecutiveHabit = apps.get_model('core', 'ExecutiveHabit')
            DailyRitualSession = apps.get_model('core', 'DailyRitualSession')
            
            # Check for habits without recent activity
            thirty_days_ago = datetime.now().date() - timedelta(days=30)
            total_habits = ExecutiveHabit.objects.filter(is_active=True).count()
            
            # Get recent ritual sessions
            recent_sessions = DailyRitualSession.objects.filter(
                date__gte=thirty_days_ago
            ).count()
            
            if total_habits > 0 and recent_sessions == 0:
                self.add_issue(
                    'medium',
                    'Habit Tracking',
                    f"{total_habits} active habits exist but no DailyRitualSessions in last 30 days",
                    None,
                    None
                )
                self.report.append(f"⚠ **{total_habits} habits with no recent activity**\n")
            else:
                self.report.append(f"✓ {total_habits} active habits, {recent_sessions} recent sessions\n")
                
        except LookupError:
            self.report.append("⚠ Habit models not found\n")

    def scan_todos(self):
        """LAYER 5: TODO Scanner"""
        self.stdout.write(f"\n{self.BOLD}{self.GREEN}LAYER 5: TODO SCANNER{self.RESET}")
        self.write_section_header("LAYER 5: PROJECT TODO SCANNER", 1)

        base_dir = Path(settings.BASE_DIR)
        
        # Scan all source files
        extensions = ['*.py', '*.html', '*.js', '*.css', '*.jsx', '*.tsx', '*.vue']
        all_files = []
        for ext in extensions:
            all_files.extend(base_dir.rglob(ext))
        
        # Exclude certain directories
        all_files = [
            f for f in all_files
            if not any(x in str(f) for x in ['.venv', 'venv', 'node_modules', '__pycache__', 'migrations'])
        ]
        
        self.stdout.write(f"Scanning {len(all_files)} files for TODOs...")
        
        todo_patterns = [
            (r'#\s*(TODO|FIXME|REVISAR|PENDING|BORRAR|HACK|XXX|BUG)[\s:](.*)', 'Python/Shell'),
            (r'//\s*(TODO|FIXME|REVISAR|PENDING|BORRAR|HACK|XXX|BUG)[\s:](.*)', 'JavaScript'),
            (r'{#\s*(TODO|FIXME|REVISAR|PENDING|BORRAR|HACK|XXX|BUG)[\s:](.*?)#}', 'Django Template'),
            (r'<!--\s*(TODO|FIXME|REVISAR|PENDING|BORRAR|HACK|XXX|BUG)[\s:](.*?)-->', 'HTML Comment'),
            (r'/\*\s*(TODO|FIXME|REVISAR|PENDING|BORRAR|HACK|XXX|BUG)[\s:](.*?)\*/', 'Block Comment')
        ]
        
        todos_by_type = defaultdict(list)
        
        for file_path in all_files:
            self.stats['files_scanned'] += 1
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    lines = content.split('\n')
                
                rel_path = str(file_path.relative_to(base_dir))
                
                for line_num, line in enumerate(lines, 1):
                    for pattern, comment_type in todo_patterns:
                        matches = re.finditer(pattern, line, re.IGNORECASE)
                        for match in matches:
                            todo_type = match.group(1).upper()
                            todo_text = match.group(2).strip()
                            
                            self.stats['todos_found'] += 1
                            
                            todos_by_type[todo_type].append({
                                'file': rel_path,
                                'line': line_num,
                                'text': todo_text,
                                'type': comment_type
                            })
                            
                            severity = 'low'
                            if todo_type in ['FIXME', 'BUG', 'BORRAR']:
                                severity = 'medium'
                            elif todo_type == 'HACK':
                                severity = 'high'
                            
                            self.add_issue(
                                severity,
                                'TODO/FIXME',
                                f"[{todo_type}] {todo_text}",
                                rel_path,
                                line_num
                            )
                            
            except Exception as e:
                pass  # Skip files that can't be read
        
        # Write TODO summary
        self.report.append(f"**Total TODOs Found**: {self.stats['todos_found']}\n\n")
        
        for todo_type in sorted(todos_by_type.keys()):
            todos = todos_by_type[todo_type]
            self.report.append(f"### {todo_type} ({len(todos)} items)\n\n")
            
            for todo in todos[:50]:  # Limit to first 50 per type
                self.report.append(f"- **{todo['file']}:{todo['line']}** - {todo['text']}\n")
            
            if len(todos) > 50:
                self.report.append(f"\n... and {len(todos) - 50} more\n")
            
            self.report.append("\n")

    def generate_summary(self):
        """Generate final summary"""
        self.write_section_header("EXECUTIVE SUMMARY", 1)
        
        self.report.append(f"**Audit Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        self.report.append(f"**Project**: Kibray Construction Management System\n")
        self.report.append(f"**Branch**: chore/security/upgrade-django-requests\n\n")
        
        self.report.append("### Scan Statistics\n\n")
        for key, value in self.stats.items():
            self.report.append(f"- **{key.replace('_', ' ').title()}**: {value:,}\n")
        
        self.report.append("\n### Issues by Severity\n\n")
        total_issues = sum(len(issues) for issues in self.issues.values())
        self.report.append(f"**Total Issues Found**: {total_issues}\n\n")
        
        for severity in ['critical', 'high', 'medium', 'low', 'info']:
            count = len(self.issues[severity])
            icon = '🔴' if severity == 'critical' else '🟠' if severity == 'high' else '🟡' if severity == 'medium' else '🟢'
            self.report.append(f"- {icon} **{severity.upper()}**: {count}\n")
        
        self.report.append("\n### Top Issues by Category\n\n")
        
        category_counts = defaultdict(int)
        for severity_issues in self.issues.values():
            for issue in severity_issues:
                category_counts[issue['category']] += 1
        
        for category, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
            self.report.append(f"- **{category}**: {count}\n")
        
        self.report.append("\n### Detailed Issues\n\n")
        
        for severity in ['critical', 'high', 'medium', 'low']:
            if len(self.issues[severity]) > 0:
                self.report.append(f"\n#### {severity.upper()} Priority Issues\n\n")
                
                for issue in self.issues[severity][:100]:  # Limit to 100 per severity
                    location = ""
                    if issue['file']:
                        location = f"**{issue['file']}"
                        if issue['line']:
                            location += f":{issue['line']}"
                        location += "**"
                    
                    self.report.append(f"- [{issue['category']}] {issue['message']}")
                    if location:
                        self.report.append(f" - {location}")
                    self.report.append("\n")
                
                if len(self.issues[severity]) > 100:
                    self.report.append(f"\n... and {len(self.issues[severity]) - 100} more {severity} issues\n")

    def handle(self, *args, **options):
        """Main command handler"""
        self.stdout.write(f"\n{self.BOLD}{self.BLUE}{'=' * 80}{self.RESET}")
        self.stdout.write(f"{self.BOLD}{self.BLUE}FULL-SPECTRUM FORENSIC AUDIT{self.RESET}")
        self.stdout.write(f"{self.BOLD}{self.BLUE}Kibray Construction Management System{self.RESET}")
        self.stdout.write(f"{self.BOLD}{self.BLUE}{'=' * 80}{self.RESET}\n")
        
        start_time = datetime.now()
        
        try:
            # Run all layers
            self.scan_python_files()
            self.scan_templates()
            self.scan_database()
            self.scan_business_rules()
            self.scan_todos()
            
            # Generate summary
            self.generate_summary()
            
            # Write report to file
            report_path = os.path.join(settings.BASE_DIR, 'FULL_AUDIT_REPORT.md')
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(''.join(self.report))
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # Print summary to console
            self.stdout.write(f"\n{self.BOLD}{'=' * 80}{self.RESET}")
            self.stdout.write(f"{self.BOLD}AUDIT COMPLETE{self.RESET}")
            self.stdout.write(f"{self.BOLD}{'=' * 80}{self.RESET}\n")
            
            self.stdout.write(f"\n{self.BOLD}Duration:{self.RESET} {duration:.2f} seconds")
            self.stdout.write(f"{self.BOLD}Files Scanned:{self.RESET} {self.stats['files_scanned']:,}")
            
            total_issues = sum(len(issues) for issues in self.issues.values())
            self.stdout.write(f"{self.BOLD}Total Issues:{self.RESET} {total_issues:,}\n")
            
            # Color-coded severity counts
            self.stdout.write(f"{self.RED}Critical: {len(self.issues['critical'])}{self.RESET}")
            self.stdout.write(f"{self.YELLOW}High: {len(self.issues['high'])}{self.RESET}")
            self.stdout.write(f"{self.CYAN}Medium: {len(self.issues['medium'])}{self.RESET}")
            self.stdout.write(f"{self.GREEN}Low: {len(self.issues['low'])}{self.RESET}\n")
            
            self.stdout.write(f"\n{self.BOLD}Report saved to:{self.RESET} {report_path}\n")
            
            # Exit code based on critical issues
            if len(self.issues['critical']) > 0:
                self.stdout.write(f"\n{self.RED}{self.BOLD}⚠ CRITICAL ISSUES FOUND - IMMEDIATE ACTION REQUIRED{self.RESET}\n")
                sys.exit(1)
            else:
                self.stdout.write(f"\n{self.GREEN}{self.BOLD}✓ No critical issues found{self.RESET}\n")
                sys.exit(0)
                
        except Exception as e:
            self.stdout.write(f"\n{self.RED}AUDIT FAILED: {str(e)}{self.RESET}\n")
            import traceback
            self.stdout.write(traceback.format_exc())
            sys.exit(1)
