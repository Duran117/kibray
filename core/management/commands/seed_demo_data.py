from datetime import date, datetime, time, timedelta
from decimal import Decimal
import random
import uuid

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction

from core.models import (
    BudgetLine,
    ChangeOrder,
    ChatChannel,
    ChatMessage,
    CostCode,
    DailyLog,
    Employee,
    Estimate,
    EstimateLine,
    Expense,
    Income,
    InventoryItem,
    InventoryLocation,
    Invoice,
    InvoiceLine,
    Issue,
    PayrollPayment,
    PayrollPeriod,
    Project,
    ProjectInventory,
    Proposal,
    Schedule,
    Task,
    TimeEntry,
)


class Command(BaseCommand):
    help = "Populate the database with demo users, projects and related records so you can explore the app."

    def handle(self, *args, **options):
        with transaction.atomic():
            self.stdout.write(self.style.MIGRATE_HEADING("Creating demo data..."))
            users = self._ensure_users()
            costcodes = self._ensure_cost_codes()
            projects = self._ensure_projects(users)
            self._ensure_budget_and_estimates(projects, costcodes)
            self._ensure_tasks_schedules_and_logs(projects, users)
            self._ensure_financials(projects, users)
            self._ensure_time_and_payroll(users, projects)
            self._ensure_inventory(projects)
            self._ensure_chat(projects, users)
        self.stdout.write(self.style.SUCCESS("Demo data ready. You can log in with admin/admin123 or pm/pm123."))

    # --- Helpers ---
    def _ensure_users(self):
        users = {}

        # Admin (may already exist via createsu)
        admin, _ = User.objects.get_or_create(username="admin", defaults={"email": "admin@example.com"})
        if not admin.has_usable_password():
            admin.set_password("admin123")
            admin.is_staff = True
            admin.is_superuser = True
            admin.save()
        users["admin"] = admin

        # Project Manager
        pm, created = User.objects.get_or_create(username="pm", defaults={"email": "pm@example.com"})
        if created:
            pm.set_password("pm123")
            pm.is_staff = True
            pm.save()
        # Set role if profile exists
        if hasattr(pm, "profile"):
            pm.profile.role = "project_manager"
            pm.profile.language = "es"
            pm.profile.save()
        users["pm"] = pm

        # Employees
        for i in range(1, 4):
            u, created = User.objects.get_or_create(username=f"emp{i}", defaults={"email": f"emp{i}@example.com"})
            if created:
                u.set_password("emp123")
                u.save()
            if hasattr(u, "profile"):
                u.profile.role = "employee"
                u.profile.language = "es"
                u.profile.save()
            emp, _ = Employee.objects.get_or_create(
                user=u,
                defaults={
                    "first_name": f"Empleado{i}",
                    "last_name": "Demo",
                    "social_security_number": f"000-00-000{i}",
                    "hourly_rate": Decimal("20.00") + i,
                    "phone": "555-0100",
                    "email": f"emp{i}@example.com",
                    "is_active": True,
                },
            )
            users[f"emp{i}"] = u

        # Client user (viewer)
        client, created = User.objects.get_or_create(username="cliente", defaults={"email": "cliente@example.com"})
        if created:
            client.set_password("cliente123")
            client.save()
        if hasattr(client, "profile"):
            client.profile.role = "client"
            client.profile.language = "es"
            client.profile.save()
        users["client"] = client

        return users

    def _ensure_cost_codes(self):
        # Minimal useful set
        base = [
            ("LAB001", "General Labor", "labor"),
            ("LAB002", "Prep & Masking", "labor"),
            ("MAT001", "Paint - Interior", "material"),
            ("MAT002", "Primer & Caulk", "material"),
            ("EQP001", "Equipment Rental", "equipment"),
        ]
        objs = []
        for code, name, cat in base:
            obj, _ = CostCode.objects.get_or_create(code=code, defaults={"name": name, "category": cat})
            objs.append(obj)
        return {o.code: o for o in objs}

    def _ensure_projects(self, users):
        today = date.today()
        p1, _ = Project.objects.get_or_create(
            name="Casa Moderno – Interior",
            defaults={
                "client": "Acme Homes",
                "address": "123 Main St",
                "start_date": today - timedelta(days=20),
                "end_date": today + timedelta(days=40),
                "description": "Pintura interior y acabados",
                "budget_total": Decimal("25000.00"),
                "budget_labor": Decimal("12000.00"),
                "budget_materials": Decimal("8000.00"),
                "budget_other": Decimal("5000.00"),
            },
        )
        p2, _ = Project.objects.get_or_create(
            name="Oficinas Centro – Remodel",
            defaults={
                "client": "North West LLC",
                "address": "45 Business Ave",
                "start_date": today - timedelta(days=5),
                "end_date": today + timedelta(days=60),
                "description": "Remodelación y pintura de oficinas",
                "budget_total": Decimal("40000.00"),
                "budget_labor": Decimal("20000.00"),
                "budget_materials": Decimal("15000.00"),
                "budget_other": Decimal("5000.00"),
            },
        )
        return [p1, p2]

    def _ensure_budget_and_estimates(self, projects, costcodes):
        # Budget lines
        for p in projects:
            BudgetLine.objects.get_or_create(
                project=p,
                cost_code=costcodes["LAB001"],
                defaults={
                    "description": "Mano de obra general",
                    "qty": Decimal("200"),
                    "unit": "hr",
                    "unit_cost": Decimal("20.00"),
                    "planned_start": p.start_date,
                    "planned_finish": p.start_date + timedelta(days=30),
                },
            )
            BudgetLine.objects.get_or_create(
                project=p,
                cost_code=costcodes["MAT001"],
                defaults={
                    "description": "Pinturas y materiales",
                    "qty": Decimal("100"),
                    "unit": "gal",
                    "unit_cost": Decimal("35.00"),
                    "planned_start": p.start_date,
                    "planned_finish": p.start_date + timedelta(days=20),
                },
            )

            # Estimate + lines
            est, _ = Estimate.objects.get_or_create(
                project=p,
                version=1,
                defaults={
                    "approved": (p == projects[0]),
                    "markup_material": Decimal("10.0"),
                    "markup_labor": Decimal("5.0"),
                    "overhead_pct": Decimal("8.0"),
                    "target_profit_pct": Decimal("15.0"),
                },
            )
            EstimateLine.objects.get_or_create(
                estimate=est,
                cost_code=costcodes["LAB002"],
                defaults={
                    "description": "Preparación y enmascarado",
                    "qty": Decimal("100"),
                    "unit": "hr",
                    "labor_unit_cost": Decimal("22.00"),
                },
            )
            EstimateLine.objects.get_or_create(
                estimate=est,
                cost_code=costcodes["MAT002"],
                defaults={
                    "description": "Primer y selladores",
                    "qty": Decimal("30"),
                    "unit": "gal",
                    "material_unit_cost": Decimal("28.00"),
                },
            )

            # Proposal
            Proposal.objects.get_or_create(
                estimate=est,
                defaults={
                    "client_view_token": str(uuid.uuid4()),
                    "accepted": est.approved,
                    "accepted_at": datetime.now() if est.approved else None,
                },
            )

    def _ensure_tasks_schedules_and_logs(self, projects, users):
        today = datetime.now()
        for p in projects:
            # Schedule items
            Schedule.objects.get_or_create(
                project=p,
                title="Site cleaning",
                defaults={
                    "description": "Limpieza inicial del sitio",
                    "start_datetime": today - timedelta(days=2),
                    "end_datetime": today - timedelta(days=1),
                    "is_personal": False,
                    "assigned_to": users["pm"],
                    "stage": "Site cleaning",
                    "completion_percentage": 100,
                    "is_complete": True,
                },
            )
            Schedule.objects.get_or_create(
                project=p,
                title="Preparation",
                defaults={
                    "description": "Enmascarado y preparación",
                    "start_datetime": today,
                    "end_datetime": today + timedelta(days=2),
                    "is_personal": False,
                    "assigned_to": users["pm"],
                    "stage": "Preparation",
                    "completion_percentage": 30,
                },
            )

            # Tasks
            for idx, title in enumerate(["Mask windows", "Sand trims", "Prime walls", "Paint ceilings"], start=1):
                Task.objects.get_or_create(
                    project=p,
                    title=title,
                    defaults={
                        "description": f"Tarea {idx} para {p.name}",
                        "status": random.choice(["Pendiente", "En Progreso", "Completada"]),
                        "created_by": users["pm"],
                        "assigned_to_id": getattr(
                            Employee.objects.filter(user__username__startswith="emp").order_by("id").first(), "id", None
                        ),
                    },
                )

            # Daily logs & Issues
            DailyLog.objects.get_or_create(
                project=p,
                date=date.today(),
                defaults={
                    "weather": "Soleado",
                    "crew_count": 3,
                    "progress_notes": "Progreso estable",
                    "created_by": users["pm"],
                },
            )
            Issue.objects.get_or_create(
                project=p,
                title="Small drywall patch",
                defaults={
                    "description": "Reparación menor antes de pintar",
                    "severity": "low",
                    "status": "in_progress",
                },
            )

    def _ensure_financials(self, projects, users):
        # Change Orders / Invoices / Expenses / Incomes
        for p in projects:
            co, _ = ChangeOrder.objects.get_or_create(
                project=p,
                description="Extra rooms painting",
                defaults={"amount": Decimal("1200.00"), "status": "approved"},
            )

            inv, _ = Invoice.objects.get_or_create(
                project=p,
                invoice_number=None,  # allow auto-number
                defaults={
                    "total_amount": Decimal("5000.00"),
                    "due_date": date.today() + timedelta(days=15),
                    "status": "SENT",
                },
            )
            InvoiceLine.objects.get_or_create(
                invoice=inv,
                description="Mobilization and prep",
                defaults={"amount": Decimal("1500.00")},
            )
            InvoiceLine.objects.get_or_create(
                invoice=inv,
                description="Materials",
                defaults={"amount": Decimal("800.00")},
            )

            # Register partial payment
            if inv.amount_paid == 0:
                from core.models import InvoicePayment

                InvoicePayment.objects.create(
                    invoice=inv,
                    amount=Decimal("1000.00"),
                    payment_date=date.today(),
                    payment_method="CHECK",
                    recorded_by=users["pm"],
                    reference="CHK-101",
                )

            # Expense sample
            Expense.objects.get_or_create(
                project=p,
                project_name=p.name,
                amount=Decimal("320.50"),
                date=date.today() - timedelta(days=1),
                category="MATERIALES",
                defaults={
                    "description": "Compra pintura y masking",
                    "change_order": co,
                },
            )

            # Income sample (if not tied to invoices)
            Income.objects.get_or_create(
                project=p,
                project_name=f"Down payment {p.name}",
                amount=Decimal("2000.00"),
                date=date.today() - timedelta(days=2),
                payment_method="TRANSFERENCIA",
            )

    def _ensure_time_and_payroll(self, users, projects):
        # Create a payroll week and time entries for employees
        monday = date.today() - timedelta(days=date.today().weekday())
        sunday = monday + timedelta(days=6)
        period, _ = PayrollPeriod.objects.get_or_create(
            week_start=monday,
            week_end=sunday,
            defaults={"created_by": users["pm"], "status": "draft"},
        )

        emps = list(Employee.objects.all()[:3])
        for emp in emps:
            for p in projects:
                # 2 entries per employee per project
                for d in range(2):
                    entry_date = monday + timedelta(days=d)
                    start_t = time(8, 0)
                    end_t = time(16, 30)
                    TimeEntry.objects.get_or_create(
                        employee=emp,
                        project=p,
                        date=entry_date,
                        start_time=start_t,
                        end_time=end_t,
                        defaults={"notes": "Trabajo de pintura"},
                    )

            # Create PayrollRecord by helper (compute hours and pay)
            from core.models import crear_o_actualizar_payroll_record

            rec = crear_o_actualizar_payroll_record(emp, monday, sunday)
            rec.period = period
            rec.save()

            # Optional partial payment
            PayrollPayment.objects.get_or_create(
                payroll_record=rec,
                amount=Decimal("150.00"),
                payment_date=monday + timedelta(days=1),
                defaults={"payment_method": "check", "check_number": "1001", "recorded_by": users["pm"]},
            )

    def _ensure_inventory(self, projects):
        # Storage and on-project locations
        storage, _ = InventoryLocation.objects.get_or_create(name="Central Storage", is_storage=True)
        loc_proj, _ = InventoryLocation.objects.get_or_create(name="Site Storage", project=projects[0])

        paint, _ = InventoryItem.objects.get_or_create(
            name="Paint - Interior White", category="PINTURA", default_threshold=Decimal("5")
        )
        tape, _ = InventoryItem.objects.get_or_create(
            name="Tape 2in 3M", category="MATERIAL", default_threshold=Decimal("10")
        )

        ProjectInventory.objects.get_or_create(item=paint, location=storage, defaults={"quantity": Decimal("20")})
        ProjectInventory.objects.get_or_create(item=tape, location=storage, defaults={"quantity": Decimal("50")})
        ProjectInventory.objects.get_or_create(item=paint, location=loc_proj, defaults={"quantity": Decimal("8")})

    def _ensure_chat(self, projects, users):
        for p in projects:
            ch, _ = ChatChannel.objects.get_or_create(
                project=p,
                name="General",
                defaults={"channel_type": "group", "created_by": users["pm"], "is_default": True},
            )
            ChatMessage.objects.get_or_create(
                channel=ch,
                user=users["pm"],
                message=f"Bienvenidos al proyecto {p.name}!",
            )
