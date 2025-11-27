"""
Management command to create a comprehensive demo project with realistic data
"""

import random
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from core.models import Employee, Expense, Income, Profile, Project, TimeEntry

User = get_user_model()


class Command(BaseCommand):
    help = "Creates a demo construction project with realistic data"

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("🏗️  Creando proyecto de demostración..."))

        # 1. Crear usuarios y empleados
        self.stdout.write("👥 Creando usuarios y empleados...")
        pm, superintendent, employees = self.create_team()

        # 2. Crear cliente
        self.stdout.write("👤 Creando cliente...")
        client = self.create_client()

        # 3. Crear proyecto
        self.stdout.write("🏠 Creando proyecto...")
        project = self.create_project(client)

        # 4. Crear entradas de tiempo
        self.stdout.write("⏱️  Creando registros de tiempo...")
        time_entries = self.create_time_entries(project, employees)

        # 5. Crear gastos
        self.stdout.write("💳 Creando gastos...")
        expenses = self.create_expenses(project)

        # 6. Crear ingresos
        self.stdout.write("💵 Creando ingresos...")
        incomes = self.create_incomes(project)

        # Resumen
        self.stdout.write(self.style.SUCCESS("\n" + "=" * 70))
        self.stdout.write(self.style.SUCCESS("✅ ¡PROYECTO DE DEMOSTRACIÓN CREADO EXITOSAMENTE!"))
        self.stdout.write(self.style.SUCCESS("=" * 70))
        self.stdout.write(f"\n📋 Proyecto: {project.name}")
        self.stdout.write(f"🏷️  Cliente: {project.client}")
        self.stdout.write(f"💰 Presupuesto: ${project.budget_total:,.2f}")
        self.stdout.write(f"📅 Inicio: {project.start_date}")
        self.stdout.write(f"📅 Fin: {project.end_date}")
        self.stdout.write("\n👥 Equipo creado:")
        self.stdout.write(f"   - PM: {pm.first_name} {pm.last_name}")
        self.stdout.write(f"   - Superintendent: {superintendent.first_name} {superintendent.last_name}")
        self.stdout.write(f"   - Empleados: {len(employees)}")
        self.stdout.write("\n📊 Datos creados:")
        self.stdout.write(f"   - Entradas de tiempo: {len(time_entries)}")
        self.stdout.write(f"   - Gastos: {len(expenses)}")
        self.stdout.write(f"   - Ingresos: {len(incomes)}")
        self.stdout.write(f"   - Total Ingresos: ${sum(i.amount for i in incomes):,.2f}")
        self.stdout.write(f"   - Total Gastos: ${sum(e.amount for e in expenses):,.2f}")
        self.stdout.write(f"   - Ganancia: ${sum(i.amount for i in incomes) - sum(e.amount for e in expenses):,.2f}")

        self.stdout.write(self.style.SUCCESS("\n🎯 Credenciales para acceder:"))
        self.stdout.write("   Username: carlos.martinez | Password: demo123 (Project Manager)")
        self.stdout.write("   Username: miguel.torres | Password: demo123 (Superintendent)")
        self.stdout.write("   Username: juan.garcia | Password: demo123 (Carpintero)")
        self.stdout.write(self.style.SUCCESS("\n🚀 ¡Listo para simular todas las funcionalidades!"))

    def create_team(self):
        """Crea el equipo de trabajo"""

        # Project Manager
        pm_user, _ = User.objects.get_or_create(
            username="carlos.martinez",
            defaults={
                "email": "carlos.martinez@kibray.com",
                "first_name": "Carlos",
                "last_name": "Martínez",
                "is_staff": True,
            },
        )
        pm_user.set_password("demo123")
        pm_user.save()

        Profile.objects.get_or_create(user=pm_user, defaults={"role": "project_manager"})

        pm_employee, _ = Employee.objects.get_or_create(
            user=pm_user,
            defaults={
                "first_name": "Carlos",
                "last_name": "Martínez",
                "social_security_number": "PM-001",
                "position": "Project Manager",
                "hourly_rate": Decimal("45.00"),
                "email": "carlos.martinez@kibray.com",
                "phone": "555-0101",
                "is_active": True,
                "hire_date": timezone.now().date() - timedelta(days=730),
            },
        )

        # Superintendent
        super_user, _ = User.objects.get_or_create(
            username="miguel.torres",
            defaults={
                "email": "miguel.torres@kibray.com",
                "first_name": "Miguel",
                "last_name": "Torres",
                "is_staff": True,
            },
        )
        super_user.set_password("demo123")
        super_user.save()

        Profile.objects.get_or_create(user=super_user, defaults={"role": "superintendent"})

        super_employee, _ = Employee.objects.get_or_create(
            user=super_user,
            defaults={
                "first_name": "Miguel",
                "last_name": "Torres",
                "social_security_number": "SUP-001",
                "position": "Superintendent",
                "hourly_rate": Decimal("40.00"),
                "email": "miguel.torres@kibray.com",
                "phone": "555-0102",
                "is_active": True,
                "hire_date": timezone.now().date() - timedelta(days=600),
            },
        )

        # Empleados
        employees_data = [
            ("juan.garcia", "Juan", "García", "Carpintero", "28.00", "EMP-001", "555-0201"),
            ("pedro.lopez", "Pedro", "López", "Electricista", "32.00", "EMP-002", "555-0202"),
            ("luis.hernandez", "Luis", "Hernández", "Plomero", "30.00", "EMP-003", "555-0203"),
            ("jose.rodriguez", "José", "Rodríguez", "Pintor", "25.00", "EMP-004", "555-0204"),
            ("alberto.sanchez", "Alberto", "Sánchez", "Albañil", "27.00", "EMP-005", "555-0205"),
            ("ricardo.ramirez", "Ricardo", "Ramírez", "Ayudante General", "20.00", "EMP-006", "555-0206"),
        ]

        employees = []
        for username, first, last, position, rate, ssn, phone in employees_data:
            user, _ = User.objects.get_or_create(
                username=username, defaults={"email": f"{username}@kibray.com", "first_name": first, "last_name": last}
            )
            user.set_password("demo123")
            user.save()

            Profile.objects.get_or_create(user=user, defaults={"role": "employee"})

            emp, _ = Employee.objects.get_or_create(
                user=user,
                defaults={
                    "first_name": first,
                    "last_name": last,
                    "social_security_number": ssn,
                    "position": position,
                    "hourly_rate": Decimal(rate),
                    "email": f"{username}@kibray.com",
                    "phone": phone,
                    "is_active": True,
                    "hire_date": timezone.now().date() - timedelta(days=random.randint(180, 500)),
                },
            )
            employees.append(emp)

        return pm_employee, super_employee, employees

    def create_client(self):
        """Crea usuario cliente"""
        client_user, _ = User.objects.get_or_create(
            username="roberto.mendez",
            defaults={"email": "roberto.mendez@example.com", "first_name": "Roberto", "last_name": "Méndez"},
        )
        client_user.set_password("demo123")
        client_user.save()

        Profile.objects.get_or_create(user=client_user, defaults={"role": "client"})

        return client_user

    def create_project(self, client):
        """Crea el proyecto de construcción"""
        start_date = timezone.now().date() - timedelta(days=45)
        end_date = start_date + timedelta(days=180)

        project, created = Project.objects.get_or_create(
            name="Villa Moderna - Residencia Ejecutiva",
            defaults={
                "client": f"{client.first_name} {client.last_name}",
                "start_date": start_date,
                "end_date": end_date,
                "address": "Av. Las Palmas 2450, Col. Jardines del Valle",
                "description": "Residencia ejecutiva de lujo con acabados premium. "
                "Incluye 4 recámaras, 3.5 baños, cocina gourmet, "
                "sala de estar, comedor, estudio, terraza y jardín.",
                "budget_total": Decimal("485000.00"),
                "budget_labor": Decimal("145000.00"),
                "budget_materials": Decimal("285000.00"),
                "budget_other": Decimal("55000.00"),
                "paint_colors": "SW 7008 Alabaster (interiores), SW 7069 Iron Ore (fachada)",
                "stains_or_finishes": "Milesi Butternut 072 - 2 capas (carpintería)",
                "number_of_rooms_or_areas": 12,
            },
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f"   ✓ Proyecto creado: {project.name}"))
        else:
            self.stdout.write(self.style.WARNING(f"   ! Proyecto ya existía: {project.name}"))

        return project

    def create_time_entries(self, project, employees):
        """Crea entradas de tiempo realistas"""
        time_entries = []

        # Crear entradas para los últimos 30 días
        for days_ago in range(30, 0, -1):
            entry_date = timezone.now().date() - timedelta(days=days_ago)

            # Solo días laborables (lunes a sábado)
            if entry_date.weekday() == 6:  # Domingo
                continue

            # Cada empleado trabaja el 80% de los días
            for employee in employees:
                if random.random() < 0.8:
                    # Horarios típicos: 7:00 AM a 3:00 PM (8h) o 7:00 AM a 4:00 PM (8.5h con almuerzo)
                    start_hour = random.choice([7, 7, 8])
                    work_hours = random.choice([8, 9, 10])
                    end_hour = start_hour + work_hours

                    from datetime import time

                    start_time = time(start_hour, 0)
                    end_time = time(end_hour, 0)

                    entry, _ = TimeEntry.objects.get_or_create(
                        employee=employee,
                        project=project,
                        date=entry_date,
                        defaults={
                            "start_time": start_time,
                            "end_time": end_time,
                            "notes": f"Trabajo en {project.name}",
                        },
                    )
                    time_entries.append(entry)

        return time_entries

    def create_expenses(self, project):
        """Crea gastos del proyecto"""
        expenses_data = [
            ("Renta de maquinaria pesada", 8500, "OTRO", -30),
            ("Combustible y lubricantes", 2340, "OTRO", -28),
            ("Herramientas y equipo menor", 1850, "OTRO", -25),
            ("Servicios (agua, luz, internet)", 3200, "OFICINA", -20),
            ("Transporte de materiales", 4500, "OTRO", -18),
            ("Comida para trabajadores", 1200, "COMIDA", -15),
            ("Renta de andamios y cimbra", 5600, "OTRO", -12),
            ("Pruebas de laboratorio", 3800, "OTRO", -10),
            ("Permisos y licencias municipales", 2500, "OTRO", -8),
            ("Limpieza de obra", 850, "OTRO", -5),
            ("Seguridad (vigilancia nocturna)", 4200, "SEGURO", -22),
            ("Seguros de obra", 6500, "SEGURO", -35),
            ("Materiales: cemento y agregados", 24500, "MATERIALES", -32),
            ("Materiales: block y ladrillo", 18300, "MATERIALES", -29),
            ("Materiales: acero de refuerzo", 32100, "MATERIALES", -27),
            ("Materiales: instalación eléctrica", 15800, "MATERIALES", -24),
            ("Materiales: plomería", 12600, "MATERIALES", -21),
            ("Materiales: pintura y acabados", 19400, "MATERIALES", -16),
            ("Materiales: pisos y azulejos", 28900, "MATERIALES", -14),
            ("Materiales: puertas y ventanas", 35200, "MATERIALES", -11),
        ]

        expenses = []
        for desc, amount, category, days_ago in expenses_data:
            exp, _ = Expense.objects.get_or_create(
                project=project,
                amount=Decimal(str(amount)),
                date=timezone.now().date() - timedelta(days=abs(days_ago)),
                project_name=project.name,
                defaults={"description": desc, "category": category},
            )
            expenses.append(exp)

        return expenses

    def create_incomes(self, project):
        """Crea ingresos del proyecto"""
        incomes_data = [
            ("Anticipo 30% del proyecto", 145500, -40, "TRANSFERENCIA"),
            ("Primer avance 20%", 97000, -25, "TRANSFERENCIA"),
            ("Segundo avance 20%", 97000, -12, "CHEQUE"),
        ]

        incomes = []
        for desc, amount, days_ago, method in incomes_data:
            inc, _ = Income.objects.get_or_create(
                project=project,
                project_name=project.name,
                amount=Decimal(str(amount)),
                date=timezone.now().date() - timedelta(days=abs(days_ago)),
                defaults={"description": desc, "payment_method": method},
            )
            incomes.append(inc)

        return incomes
