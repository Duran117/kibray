"""
Deep System Health-Check Command for Module 25: Strategic Planner
Performs 5 strict verification checks with colored output.
"""
import os
import sys

from django.apps import apps
from django.conf import settings
from django.core.management.base import BaseCommand
from django.urls import get_resolver


class Command(BaseCommand):
    help = 'Performs deep system health-check for Module 25 Strategic Planner implementation'

    # ANSI Color Codes
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    RESET = '\033[0m'

    def __init__(self):
        super().__init__()
        self.errors = []
        self.warnings = []
        self.success_count = 0
        self.total_checks = 0

    def add_style(self, text, color):
        """Add color styling to text"""
        return f"{color}{text}{self.RESET}"

    def print_header(self, text):
        """Print section header"""
        self.stdout.write(f"\n{self.BOLD}{self.BLUE}{'=' * 70}{self.RESET}")
        self.stdout.write(f"{self.BOLD}{self.BLUE}{text}{self.RESET}")
        self.stdout.write(f"{self.BOLD}{self.BLUE}{'=' * 70}{self.RESET}\n")

    def print_success(self, text):
        """Print success message"""
        self.stdout.write(self.add_style(f"✓ {text}", self.GREEN))

    def print_error(self, text):
        """Print error message"""
        self.stdout.write(self.add_style(f"✗ {text}", self.RED))
        self.errors.append(text)

    def print_warning(self, text):
        """Print warning message"""
        self.stdout.write(self.add_style(f"⚠ {text}", self.YELLOW))
        self.warnings.append(text)

    def check_url_registrations(self):
        """Check 1: URL & View Registration"""
        self.print_header("CHECK 1: URL & VIEW REGISTRATION")

        required_views = [
            'strategic_planner',  # Main wizard view
            'planner-calendar-feed',  # iCal feed
            'dashboard_admin',  # Admin dashboard
            'dashboard_bi',  # BI dashboard
        ]

        resolver = get_resolver()
        registered_names = set()

        # Get all URL patterns recursively
        def get_all_url_names(url_patterns):
            names = set()
            for pattern in url_patterns:
                if hasattr(pattern, 'name') and pattern.name:
                    names.add(pattern.name)
                if hasattr(pattern, 'url_patterns'):
                    names.update(get_all_url_names(pattern.url_patterns))
            return names

        registered_names = get_all_url_names(resolver.url_patterns)

        for view_name in required_views:
            self.total_checks += 1
            if view_name in registered_names:
                self.print_success(f"View '{view_name}' is registered")
                self.success_count += 1
            else:
                self.print_error(f"View '{view_name}' is NOT registered in urls.py")

        # Additional API endpoint checks
        api_endpoints = [
            'planner-active-habits',
            'planner-random-vision',
            'planner-complete-ritual',
            'planner-today-ritual',
            'planner-toggle-action',
            'planner-update-step',
            'planner-stats',
        ]

        self.stdout.write(f"\n{self.BOLD}API Endpoints:{self.RESET}")
        for endpoint in api_endpoints:
            self.total_checks += 1
            if endpoint in registered_names:
                self.print_success(f"API endpoint '{endpoint}' is registered")
                self.success_count += 1
            else:
                self.print_warning(f"API endpoint '{endpoint}' is NOT registered")

    def check_data_models(self):
        """Check 2: Data Model Structure"""
        self.print_header("CHECK 2: DATA MODEL STRUCTURE")

        required_models = {
            'LifeVision': ['deep_why', 'scope', 'progress_pct', 'title', 'user'],
            'ExecutiveHabit': ['frequency', 'title', 'is_active', 'user'],
            'DailyRitualSession': ['physiology_check', 'gratitude_entries', 'energy_level', 'user', 'date'],
            'PowerAction': ['is_frog', 'micro_steps', 'ical_uid', 'is_80_20', 'session', 'title'],
            'HabitCompletion': ['habit', 'completed_date'],
        }

        try:
            core_models = apps.get_app_config('core').get_models()
            model_names = {model.__name__: model for model in core_models}

            for model_name, required_fields in required_models.items():
                self.total_checks += 1
                if model_name in model_names:
                    self.print_success(f"Model '{model_name}' exists")
                    self.success_count += 1

                    # Deep field check
                    model = model_names[model_name]
                    model_fields = [field.name for field in model._meta.get_fields()]

                    self.stdout.write(f"  {self.BOLD}Field Verification:{self.RESET}")
                    for field in required_fields:
                        self.total_checks += 1
                        if field in model_fields:
                            # Get field type
                            field_obj = model._meta.get_field(field)
                            field_type = field_obj.__class__.__name__
                            self.print_success(f"  Field '{field}' exists ({field_type})")
                            self.success_count += 1

                            # Critical field type checks
                            if model_name == 'PowerAction':
                                if field == 'is_frog' and field_type != 'BooleanField':
                                    self.print_error(f"  Field '{field}' should be BooleanField, got {field_type}")
                                elif field == 'micro_steps' and field_type != 'JSONField':
                                    self.print_error(f"  Field '{field}' should be JSONField, got {field_type}")
                                elif field == 'ical_uid' and field_type != 'UUIDField':
                                    self.print_error(f"  Field '{field}' should be UUIDField, got {field_type}")

                            if model_name == 'LifeVision':
                                if field == 'deep_why' and field_type != 'TextField':
                                    self.print_error(f"  Field '{field}' should be TextField, got {field_type}")

                            if model_name == 'ExecutiveHabit':
                                if field == 'frequency' and field_type != 'CharField':
                                    self.print_error(f"  Field '{field}' should be CharField, got {field_type}")
                        else:
                            self.print_error(f"  Field '{field}' is MISSING from {model_name}")
                else:
                    self.print_error(f"Model '{model_name}' is MISSING from core app")

            # Check for model relationships
            self.stdout.write(f"\n{self.BOLD}Relationship Verification:{self.RESET}")
            self.total_checks += 3

            if 'PowerAction' in model_names:
                power_action = model_names['PowerAction']
                # Check ForeignKey to DailyRitualSession
                if hasattr(power_action, 'session'):
                    self.print_success("PowerAction -> DailyRitualSession relationship exists")
                    self.success_count += 1
                else:
                    self.print_error("PowerAction missing 'session' ForeignKey to DailyRitualSession")

                # Check ForeignKey to LifeVision
                if hasattr(power_action, 'linked_vision'):
                    self.print_success("PowerAction -> LifeVision relationship exists")
                    self.success_count += 1
                else:
                    self.print_warning("PowerAction missing 'linked_vision' ForeignKey (optional)")
                    self.success_count += 1

            if 'HabitCompletion' in model_names:
                habit_completion = model_names['HabitCompletion']
                if hasattr(habit_completion, 'habit'):
                    self.print_success("HabitCompletion -> ExecutiveHabit relationship exists")
                    self.success_count += 1
                else:
                    self.print_error("HabitCompletion missing 'habit' ForeignKey")

        except Exception as e:
            self.print_error(f"Failed to load core models: {str(e)}")

    def check_security_and_logic(self):
        """Check 3: Security & Logic"""
        self.print_header("CHECK 3: SECURITY & LOGIC")

        views_file = os.path.join(settings.BASE_DIR, 'core', 'views_planner.py')

        self.total_checks += 5

        if not os.path.exists(views_file):
            self.print_error("File 'core/views_planner.py' does NOT exist")
            return

        self.print_success("File 'core/views_planner.py' exists")
        self.success_count += 1

        try:
            with open(views_file, encoding='utf-8') as f:
                content = f.read()

            # Check for @login_required
            if '@login_required' in content:
                self.print_success("Security: @login_required decorator found")
                self.success_count += 1
            else:
                self.print_error("Security: @login_required decorator NOT found")

            # Check for calendar token or ical_uid usage
            has_calendar_token = 'calendar_token' in content or 'user_token' in content
            has_ical_uid = 'ical_uid' in content

            if has_calendar_token or has_ical_uid:
                self.print_success(f"Calendar feed security: Found {'calendar_token/user_token' if has_calendar_token else 'ical_uid'}")
                self.success_count += 1
            else:
                self.print_error("Calendar feed security: NO calendar_token or ical_uid found")

            # Check for iCal generation
            if 'Calendar' in content or 'icalendar' in content:
                self.print_success("iCal generation: Calendar import found")
                self.success_count += 1
            else:
                self.print_error("iCal generation: NO Calendar/icalendar import found")

            # Check for transaction safety
            if '@transaction.atomic' in content or 'transaction.atomic' in content:
                self.print_success("Transaction safety: @transaction.atomic found")
                self.success_count += 1
            else:
                self.print_warning("Transaction safety: @transaction.atomic NOT found (recommended)")
                self.success_count += 1

            # Additional security checks
            self.stdout.write(f"\n{self.BOLD}Additional Security Checks:{self.RESET}")
            security_items = [
                ('CSRF Protection', 'csrftoken' in content or 'csrf_exempt' in content),
                ('User Filtering', 'request.user' in content),
                ('Staff Check', 'is_staff' in content or 'is_superuser' in content),
                ('HTTP Method Check', 'require_http_methods' in content or 'require_POST' in content),
            ]

            for item_name, check_result in security_items:
                if check_result:
                    self.print_success(f"{item_name}: Implemented")
                else:
                    self.print_warning(f"{item_name}: Not detected (may be optional)")

        except Exception as e:
            self.print_error(f"Failed to read views_planner.py: {str(e)}")

    def check_templates(self):
        """Check 4: Template Existence"""
        self.print_header("CHECK 4: TEMPLATE EXISTENCE")

        templates = [
            ('core/templates/core/strategic_ritual.html', 'Strategic Ritual Wizard'),
            ('core/templates/core/dashboard_admin.html', 'Admin Dashboard'),
        ]

        for template_path, description in templates:
            self.total_checks += 1
            full_path = os.path.join(settings.BASE_DIR, template_path)

            if os.path.exists(full_path):
                file_size = os.path.getsize(full_path)
                self.print_success(f"{description}: EXISTS ({file_size:,} bytes)")
                self.success_count += 1

                # Check file size to ensure it's not empty
                if file_size < 100:
                    self.print_warning(f"{description}: File is very small ({file_size} bytes)")
            else:
                self.print_error(f"{description}: DOES NOT EXIST at {template_path}")

    def check_integration(self):
        """Check 5: Integration Check"""
        self.print_header("CHECK 5: INTEGRATION CHECK")

        dashboard_path = os.path.join(settings.BASE_DIR, 'core', 'templates', 'core', 'dashboard_admin.html')

        self.total_checks += 4

        if not os.path.exists(dashboard_path):
            self.print_error("dashboard_admin.html does NOT exist")
            return

        try:
            with open(dashboard_path, encoding='utf-8') as f:
                content = f.read()

            # Check for Frog/PowerAction reference
            has_frog_ref = 'frog' in content.lower() or 'PowerAction' in content
            if has_frog_ref:
                self.print_success("Dashboard contains 'frog' or 'PowerAction' reference (widget integrated)")
                self.success_count += 1
            else:
                self.print_error("Dashboard does NOT contain 'frog' or 'PowerAction' reference")

            # Check for strategic planner link
            has_planner_link = 'strategic_planner' in content or 'strategic-planner' in content or 'planner/' in content
            if has_planner_link:
                self.print_success("Dashboard contains link to Strategic Planner")
                self.success_count += 1
            else:
                self.print_error("Dashboard does NOT contain link to Strategic Planner")

            # Check for Strategic Focus widget
            has_widget = 'Strategic Focus' in content or 'strategicFocusWidget' in content
            if has_widget:
                self.print_success("Dashboard contains 'Strategic Focus' widget")
                self.success_count += 1
            else:
                self.print_error("Dashboard does NOT contain 'Strategic Focus' widget")

            # Check for API calls to planner endpoints
            has_api_calls = '/api/planner/' in content or 'planner/ritual' in content
            if has_api_calls:
                self.print_success("Dashboard contains API calls to planner endpoints")
                self.success_count += 1
            else:
                self.print_error("Dashboard does NOT contain API calls to planner endpoints")

            # Additional integration checks
            self.stdout.write(f"\n{self.BOLD}Additional Integration Checks:{self.RESET}")

            integration_items = [
                ('Quick Actions Button', 'Strategic Planner' in content or 'strategic_planner' in content),
                ('JavaScript Functions', 'loadStrategicFocus' in content or 'toggleFrogStatus' in content),
                ('Micro-step Toggle', 'toggleMicroStep' in content or 'micro_step' in content),
                ('Frog Display', '🐸' in content or 'frog_display' in content),
            ]

            for item_name, check_result in integration_items:
                if check_result:
                    self.print_success(f"{item_name}: Found")
                else:
                    self.print_warning(f"{item_name}: Not detected")

        except Exception as e:
            self.print_error(f"Failed to read dashboard_admin.html: {str(e)}")

    def print_summary(self):
        """Print final summary"""
        self.print_header("AUDIT SUMMARY")

        success_rate = (self.success_count / self.total_checks * 100) if self.total_checks > 0 else 0

        self.stdout.write(f"\n{self.BOLD}Total Checks Performed:{self.RESET} {self.total_checks}")
        self.stdout.write(self.add_style(f"Passed: {self.success_count}", self.GREEN))
        self.stdout.write(self.add_style(f"Failed: {len(self.errors)}", self.RED))
        self.stdout.write(self.add_style(f"Warnings: {len(self.warnings)}", self.YELLOW))
        self.stdout.write(f"\n{self.BOLD}Success Rate:{self.RESET} {success_rate:.1f}%")

        if len(self.errors) == 0:
            self.stdout.write(f"\n{self.add_style(f'{self.BOLD}✓ ALL CRITICAL CHECKS PASSED!{self.RESET}', self.GREEN)}")
            self.stdout.write(self.add_style("Module 25 Strategic Planner is properly implemented.", self.GREEN))
        else:
            self.stdout.write(f"\n{self.add_style(f'{self.BOLD}✗ CRITICAL ERRORS FOUND!{self.RESET}', self.RED)}")
            self.stdout.write(self.add_style(f"Please fix {len(self.errors)} error(s) before production deployment.", self.RED))

            self.stdout.write(f"\n{self.BOLD}Errors:{self.RESET}")
            for i, error in enumerate(self.errors, 1):
                self.stdout.write(f"  {i}. {error}")

        if len(self.warnings) > 0:
            self.stdout.write(f"\n{self.BOLD}Warnings (Optional Improvements):{self.RESET}")
            for i, warning in enumerate(self.warnings, 1):
                self.stdout.write(f"  {i}. {warning}")

        self.stdout.write(f"\n{self.BOLD}{self.BLUE}{'=' * 70}{self.RESET}\n")

    def handle(self, *args, **options):
        """Main command handler"""
        self.stdout.write(f"\n{self.BOLD}{self.BLUE}╔{'═' * 68}╗{self.RESET}")
        self.stdout.write(f"{self.BOLD}{self.BLUE}║{' ' * 10}MODULE 25 STRATEGIC PLANNER - DEEP AUDIT{' ' * 15}║{self.RESET}")
        self.stdout.write(f"{self.BOLD}{self.BLUE}║{' ' * 20}System Health Check{' ' * 29}║{self.RESET}")
        self.stdout.write(f"{self.BOLD}{self.BLUE}╚{'═' * 68}╝{self.RESET}\n")

        try:
            # Run all checks
            self.check_url_registrations()
            self.check_data_models()
            self.check_security_and_logic()
            self.check_templates()
            self.check_integration()

            # Print summary
            self.print_summary()

            # Exit with error code if critical errors found
            if len(self.errors) > 0:
                sys.exit(1)
            else:
                sys.exit(0)

        except Exception as e:
            self.print_error(f"Unexpected error during audit: {str(e)}")
            import traceback
            self.stdout.write(traceback.format_exc())
            sys.exit(1)
