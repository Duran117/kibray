"""
Management command to seed the database with realistic test data using Faker
"""
from datetime import timedelta
from decimal import Decimal
import random

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone
from faker import Faker

from core.models import (
    ChangeOrder,
    ClientContact,
    ClientOrganization,
    Employee,
    Profile,
    Project,
    Task,
)


class Command(BaseCommand):
    help = 'Seed database with realistic test data for development'

    def handle(self, *args, **options):
        fake = Faker()

        self.stdout.write('Starting database seed...')

        # Create Client Organizations
        orgs = []
        self.stdout.write('Creating client organizations...')
        for i in range(5):
            org = ClientOrganization.objects.create(
                name=fake.company(),
                billing_address=fake.address(),
                billing_city=fake.city(),
                billing_state=fake.state(),
                billing_zip=fake.zipcode(),
                billing_email=fake.company_email(),
                billing_phone=fake.phone_number(),
                website=fake.url(),
                is_active=fake.boolean(chance_of_getting_true=90)
            )
            orgs.append(org)

        self.stdout.write(self.style.SUCCESS(f'Created {len(orgs)} organizations'))

        # Create Users
        users = []
        self.stdout.write('Creating users...')
        for i in range(15):
            username = fake.user_name()
            try:
                user = User.objects.create_user(
                    username=username,
                    email=fake.email(),
                    first_name=fake.first_name(),
                    last_name=fake.last_name(),
                    password='testpass123'
                )
                users.append(user)
            except:
                # Skip if username already exists
                continue

        self.stdout.write(self.style.SUCCESS(f'Created {len(users)} users'))

        # Create Profiles
        self.stdout.write('Creating user profiles...')
        roles = ['admin', 'pm', 'employee', 'client', 'designer']
        for user in users:
            if not hasattr(user, 'profile'):
                Profile.objects.create(
                    user=user,
                    role=random.choice(roles),
                    phone_number=fake.phone_number()[:20]
                )

        # Create Client Contacts
        contacts = []
        self.stdout.write('Creating client contacts...')
        for org in orgs:
            for i in range(random.randint(1, 3)):
                # Pick a user that doesn't already have a ClientContact
                available_users = [u for u in users if not hasattr(u, 'client_contact')]
                if not available_users:
                    break
                contact_user = random.choice(available_users)
                contact = ClientContact.objects.create(
                    user=contact_user,
                    organization=org,
                    role=random.choice(['project_lead', 'observer', 'project_manager']),
                    phone_direct=fake.phone_number()[:20],
                    phone_mobile=fake.phone_number()[:20],
                    can_approve_change_orders=fake.boolean(chance_of_getting_true=70),
                    can_view_financials=fake.boolean(chance_of_getting_true=80)
                )
                contacts.append(contact)

        self.stdout.write(self.style.SUCCESS(f'Created {len(contacts)} client contacts'))

        # Create Projects
        projects = []
        self.stdout.write('Creating projects...')
        for i in range(10):
            start_date = fake.date_between(start_date='-1y', end_date='today')
            end_date = start_date + timedelta(days=random.randint(30, 365))

            project = Project.objects.create(
                name=fake.sentence(nb_words=3)[:-1],
                project_code=f"PRJ-{2024}-{i+1:04d}",
                client=fake.company(),
                address=fake.address(),
                start_date=start_date,
                end_date=end_date,
                description=fake.text(max_nb_chars=200),
                billing_organization=random.choice(orgs),
                project_lead=random.choice(contacts) if contacts else None,
                budget_total=Decimal(str(random.randint(50000, 500000))),
                budget_labor=Decimal(str(random.randint(20000, 200000))),
                budget_materials=Decimal(str(random.randint(10000, 150000))),
                budget_other=Decimal(str(random.randint(5000, 50000))),
                total_income=Decimal(str(random.randint(0, 300000))),
                total_expenses=Decimal(str(random.randint(0, 250000))),
            )

            # Add observers
            if len(contacts) > 3:
                observers = random.sample(contacts, k=random.randint(1, 3))
                project.observers.set(observers)

            projects.append(project)

        self.stdout.write(self.style.SUCCESS(f'Created {len(projects)} projects'))

        # Create Employees
        employees = []
        self.stdout.write('Creating employees...')
        for i in range(min(10, len(users))):
            try:
                employee = Employee.objects.create(
                    user=users[i],
                    name=f"{users[i].first_name} {users[i].last_name}",
                    hourly_rate=Decimal(str(random.randint(15, 50))),
                    is_active=True
                )
                employees.append(employee)
            except:
                # Skip if employee already exists
                continue

        self.stdout.write(self.style.SUCCESS(f'Created {len(employees)} employees'))

        # Create Tasks
        tasks = []
        self.stdout.write('Creating tasks...')
        statuses = ['Pendiente', 'En Progreso', 'Completada', 'Cancelada']
        priorities = ['low', 'medium', 'high', 'urgent']

        for i in range(50):
            project = random.choice(projects)
            due_date = fake.date_between(start_date='today', end_date='+30d')
            status = random.choice(statuses)

            task = Task.objects.create(
                project=project,
                title=fake.sentence(nb_words=5)[:-1],
                description=fake.text(max_nb_chars=200),
                status=status,
                priority=random.choice(priorities),
                due_date=due_date,
                created_by=random.choice(users),
                assigned_to=random.choice(employees) if employees and random.random() > 0.3 else None,
            )

            if status == 'Completada':
                task.completed_at = timezone.now() - timedelta(days=random.randint(1, 30))
                task.save()

            tasks.append(task)

        self.stdout.write(self.style.SUCCESS(f'Created {len(tasks)} tasks'))

        # Create Change Orders
        change_orders = []
        self.stdout.write('Creating change orders...')
        co_statuses = ['draft', 'pending', 'approved', 'sent', 'billed', 'paid']

        for i in range(20):
            project = random.choice(projects)
            amount = Decimal(str(random.randint(500, 50000)))
            status = random.choice(co_statuses)

            co = ChangeOrder.objects.create(
                project=project,
                description=fake.text(max_nb_chars=150),
                amount=amount,
                status=status,
                reference_code=f"CO-{2024}-{random.randint(1000, 9999)}",
                notes=fake.text(max_nb_chars=100) if random.random() > 0.5 else '',
            )
            change_orders.append(co)

        self.stdout.write(self.style.SUCCESS(f'Created {len(change_orders)} change orders'))

        # Summary
        self.stdout.write(self.style.SUCCESS('\n=== Seed Data Summary ==='))
        self.stdout.write(self.style.SUCCESS(f'Organizations: {len(orgs)}'))
        self.stdout.write(self.style.SUCCESS(f'Users: {len(users)}'))
        self.stdout.write(self.style.SUCCESS(f'Client Contacts: {len(contacts)}'))
        self.stdout.write(self.style.SUCCESS(f'Projects: {len(projects)}'))
        self.stdout.write(self.style.SUCCESS(f'Employees: {len(employees)}'))
        self.stdout.write(self.style.SUCCESS(f'Tasks: {len(tasks)}'))
        self.stdout.write(self.style.SUCCESS(f'Change Orders: {len(change_orders)}'))
        self.stdout.write(self.style.SUCCESS('\nDatabase seeding completed successfully!'))
        self.stdout.write(self.style.WARNING('\nDefault user password: testpass123'))
