"""
Management command to find and clean up Employee records
that were incorrectly created for client users.

Bug: daily_plan_edit used Employee.objects.get_or_create for ALL active Users,
including clients. This created ghost Employee records for client users.

Usage:
  # Diagnose only (safe, no changes):
  python manage.py cleanup_ghost_employees

  # Actually delete ghost employees (only if they have NO data):
  python manage.py cleanup_ghost_employees --fix

  # Force delete even if they have data (DANGEROUS):
  python manage.py cleanup_ghost_employees --fix --force
"""

from django.core.management.base import BaseCommand

from core.models import (
    Employee,
    PayrollRecord,
    Profile,
    ResourceAssignment,
    TimeEntry,
)


class Command(BaseCommand):
    help = "Find and optionally remove Employee records created for client users (ghost employees)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--fix",
            action="store_true",
            help="Actually delete ghost employees that have no associated data.",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Delete ghost employees even if they have associated data (DANGEROUS).",
        )

    def handle(self, *args, **options):
        do_fix = options["fix"]
        force = options["force"]

        # Find client user IDs
        client_user_ids = list(
            Profile.objects.filter(role="client").values_list("user_id", flat=True)
        )

        if not client_user_ids:
            self.stdout.write(self.style.SUCCESS("No client profiles found. Nothing to do."))
            return

        # Find ghost employees (Employee records linked to client users)
        ghosts = Employee.objects.filter(user_id__in=client_user_ids)

        self.stdout.write("=" * 60)
        self.stdout.write("GHOST EMPLOYEE DIAGNOSTIC")
        self.stdout.write("=" * 60)
        self.stdout.write(f"Client profiles found: {len(client_user_ids)}")
        self.stdout.write(f"Ghost Employee records: {ghosts.count()}")
        self.stdout.write("")

        if not ghosts.exists():
            self.stdout.write(
                self.style.SUCCESS(
                    "✅ No ghost employees found. Database is clean!"
                )
            )
            return

        safe_to_delete = []
        has_data = []

        for emp in ghosts:
            time_count = TimeEntry.objects.filter(employee=emp).count()
            payroll_count = PayrollRecord.objects.filter(employee=emp).count()
            assignment_count = ResourceAssignment.objects.filter(employee=emp).count()

            total_data = time_count + payroll_count + assignment_count
            username = emp.user.username if emp.user else "N/A"

            if total_data == 0:
                safe_to_delete.append(emp)
                self.stdout.write(
                    self.style.SUCCESS(
                        f"  ✅ SAFE | Employee #{emp.id} [{emp.employee_key}] "
                        f"{emp.first_name} {emp.last_name} (user: {username}) "
                        f"- No data attached"
                    )
                )
            else:
                has_data.append(emp)
                self.stdout.write(
                    self.style.WARNING(
                        f"  ⚠️  DATA | Employee #{emp.id} [{emp.employee_key}] "
                        f"{emp.first_name} {emp.last_name} (user: {username}) "
                        f"- TimeEntries: {time_count}, Payroll: {payroll_count}, "
                        f"Assignments: {assignment_count}"
                    )
                )

        self.stdout.write("")
        self.stdout.write(f"Safe to delete: {len(safe_to_delete)}")
        self.stdout.write(f"Have data (risky): {len(has_data)}")
        self.stdout.write("")

        if not do_fix:
            self.stdout.write(
                self.style.NOTICE(
                    "DRY RUN - No changes made. Use --fix to delete safe ghost employees."
                )
            )
            return

        # Delete safe ghosts
        if safe_to_delete:
            ids = [e.id for e in safe_to_delete]
            count = Employee.objects.filter(id__in=ids).delete()
            self.stdout.write(
                self.style.SUCCESS(f"🗑️  Deleted {count[0]} safe ghost employees.")
            )

        # Handle ghosts with data
        if has_data and force:
            self.stdout.write(
                self.style.WARNING("⚠️  --force flag: Deleting ghosts WITH data...")
            )
            ids = [e.id for e in has_data]
            count = Employee.objects.filter(id__in=ids).delete()
            self.stdout.write(
                self.style.WARNING(
                    f"🗑️  Force-deleted {count[0]} ghost employees "
                    f"(cascade deleted related records)."
                )
            )
        elif has_data:
            self.stdout.write(
                self.style.WARNING(
                    f"⚠️  {len(has_data)} ghost employees with data were NOT deleted. "
                    f"Review manually or use --force (DANGEROUS: deletes their "
                    f"time entries, payroll records, and assignments too)."
                )
            )

        self.stdout.write(self.style.SUCCESS("\nDone."))
