"""
Management command to deactivate or delete Employee records that
are NOT real field workers/painters (e.g., admins, PMs, owners who 
were auto-created by the daily_plan_edit bug).

These users should exist as Users with Profile roles, but NOT as Employee
records (which are for payroll, time tracking, and field assignment).

Usage:
  # List all employees and flag suspicious ones:
  python manage.py deactivate_non_workers

  # Deactivate specific employees by employee_key:
  python manage.py deactivate_non_workers --deactivate EMP-007 EMP-008 EMP-009

  # Delete specific employees (only if they have NO payroll/time data):
  python manage.py deactivate_non_workers --delete EMP-007 EMP-008 EMP-009

  # Delete all employees with hourly_rate=0 and PENDING SSN:
  python manage.py deactivate_non_workers --delete-ghosts
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
    help = "List, deactivate, or delete Employee records that are not real workers"

    def add_arguments(self, parser):
        parser.add_argument(
            "--deactivate",
            nargs="+",
            metavar="EMP_KEY",
            help="Deactivate specific employees by employee_key (e.g., EMP-007 EMP-008)",
        )
        parser.add_argument(
            "--delete",
            nargs="+",
            metavar="EMP_KEY",
            help="Delete specific employees by employee_key (only if no payroll/time data)",
        )
        parser.add_argument(
            "--delete-ghosts",
            action="store_true",
            help="Delete all employees with hourly_rate=0 and SSN starting with PENDING",
        )

    def _employee_data_summary(self, emp):
        """Returns dict with data counts for an employee."""
        time_count = TimeEntry.objects.filter(employee=emp).count()
        payroll_count = PayrollRecord.objects.filter(employee=emp).count()
        assignment_count = ResourceAssignment.objects.filter(employee=emp).count()
        return {
            "time_entries": time_count,
            "payroll": payroll_count,
            "assignments": assignment_count,
            "total": time_count + payroll_count + assignment_count,
        }

    def _display_employee(self, emp, data=None):
        """Display one employee row."""
        if data is None:
            data = self._employee_data_summary(emp)

        username = emp.user.username if emp.user else "NO_USER"
        prof = Profile.objects.filter(user=emp.user).first() if emp.user else None
        role = prof.role if prof else "NO_PROFILE"
        ssn = emp.social_security_number or ""
        is_ghost = emp.hourly_rate == 0 or "PENDING" in ssn

        flag = "👻 GHOST" if is_ghost else "✅ OK"
        data_flag = f"📦 DATA({data['total']})" if data["total"] > 0 else "🗑️  EMPTY"

        self.stdout.write(
            f"  {flag} | {emp.employee_key:>10} | {emp.first_name:<12} {emp.last_name:<12} "
            f"| rate=${emp.hourly_rate:<8} | active={emp.is_active} "
            f"| user={username:<20} | role={role:<15} | {data_flag}"
        )

    def handle(self, *args, **options):
        deactivate_keys = options.get("deactivate")
        delete_keys = options.get("delete")
        delete_ghosts = options.get("delete_ghosts")

        # ===== LIST ALL EMPLOYEES =====
        self.stdout.write("=" * 100)
        self.stdout.write("EMPLOYEE RECORDS AUDIT")
        self.stdout.write("=" * 100)

        all_employees = Employee.objects.select_related("user").order_by("id")
        self.stdout.write(f"Total employees: {all_employees.count()}\n")

        for emp in all_employees:
            self._display_employee(emp)

        self.stdout.write("")

        # ===== DEACTIVATE =====
        if deactivate_keys:
            self.stdout.write(f"\nDeactivating: {', '.join(deactivate_keys)}")
            for key in deactivate_keys:
                try:
                    emp = Employee.objects.get(employee_key=key)
                    emp.is_active = False
                    emp.save(update_fields=["is_active"])
                    self.stdout.write(self.style.SUCCESS(
                        f"  ✅ Deactivated {key} ({emp.first_name} {emp.last_name})"
                    ))
                except Employee.DoesNotExist:
                    self.stdout.write(self.style.ERROR(f"  ❌ {key} not found"))
            return

        # ===== DELETE SPECIFIC =====
        if delete_keys:
            self.stdout.write(f"\nDeleting: {', '.join(delete_keys)}")
            for key in delete_keys:
                try:
                    emp = Employee.objects.get(employee_key=key)
                    data = self._employee_data_summary(emp)
                    if data["total"] > 0:
                        self.stdout.write(self.style.WARNING(
                            f"  ⚠️  SKIPPED {key} ({emp.first_name} {emp.last_name}) "
                            f"- has {data['total']} linked records "
                            f"(time={data['time_entries']}, payroll={data['payroll']}, "
                            f"assignments={data['assignments']}). Deactivating instead."
                        ))
                        emp.is_active = False
                        emp.save(update_fields=["is_active"])
                    else:
                        emp.delete()
                        self.stdout.write(self.style.SUCCESS(
                            f"  🗑️  Deleted {key} ({emp.first_name} {emp.last_name})"
                        ))
                except Employee.DoesNotExist:
                    self.stdout.write(self.style.ERROR(f"  ❌ {key} not found"))
            return

        # ===== DELETE ALL GHOSTS =====
        if delete_ghosts:
            from django.db.models import Q
            ghosts = Employee.objects.filter(
                Q(hourly_rate=0) | Q(social_security_number__startswith="PENDING")
            )
            self.stdout.write(f"\nFound {ghosts.count()} ghost employees (rate=0 or PENDING SSN)")
            deleted = 0
            skipped = 0
            for emp in ghosts:
                data = self._employee_data_summary(emp)
                if data["total"] > 0:
                    self.stdout.write(self.style.WARNING(
                        f"  ⚠️  SKIPPED {emp.employee_key} ({emp.first_name} {emp.last_name}) "
                        f"- has {data['total']} linked records. Deactivating instead."
                    ))
                    emp.is_active = False
                    emp.save(update_fields=["is_active"])
                    skipped += 1
                else:
                    self.stdout.write(self.style.SUCCESS(
                        f"  🗑️  Deleted {emp.employee_key} ({emp.first_name} {emp.last_name})"
                    ))
                    emp.delete()
                    deleted += 1

            self.stdout.write(self.style.SUCCESS(
                f"\nDone: {deleted} deleted, {skipped} deactivated (had data)"
            ))
            return

        # ===== DRY RUN MESSAGE =====
        self.stdout.write(
            self.style.NOTICE(
                "\nDRY RUN - No changes made. Use:\n"
                "  --deactivate EMP-007 EMP-008  → set is_active=False\n"
                "  --delete EMP-007 EMP-008      → delete if no data\n"
                "  --delete-ghosts               → delete all rate=0 / PENDING SSN\n"
            )
        )
