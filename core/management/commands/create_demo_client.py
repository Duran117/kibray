"""
Management command to create a demo client user for testing
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from core.models import Profile, Project, ClientProjectAccess
from decimal import Decimal

User = get_user_model()


class Command(BaseCommand):
    help = 'Creates a demo client user with access to a test project'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('\n🔧 Creating Demo Client User...\n'))
        
        with transaction.atomic():
            # Create or get demo client user
            username = 'demo_client'
            email = 'client@demo.com'
            password = 'Demo123!'
            
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': email,
                    'first_name': 'Demo',
                    'last_name': 'Client',
                    'is_staff': False,
                    'is_active': True,
                }
            )
            
            if created:
                user.set_password(password)
                user.save()
                self.stdout.write(self.style.SUCCESS(f'  ✅ Created user: {username}'))
            else:
                self.stdout.write(self.style.WARNING(f'  ⚠️  User {username} already exists'))
            
            # Create or get profile with client role
            profile, prof_created = Profile.objects.get_or_create(
                user=user,
                defaults={
                    'role': 'client',
                    'display_name': 'Demo Client',
                    'full_name': 'Demo Client User',
                }
            )
            
            if prof_created:
                self.stdout.write(self.style.SUCCESS(f'  ✅ Created profile with role: client'))
            else:
                profile.role = 'client'
                profile.save()
                self.stdout.write(self.style.WARNING(f'  ⚠️  Updated existing profile to client role'))
            
            # Create or get a demo project
            from datetime import date, timedelta
            
            project, proj_created = Project.objects.get_or_create(
                name='Demo Client Project',
                defaults={
                    'address': '123 Demo Street, Demo City, DC 12345',
                    'client': username,
                    'start_date': date.today(),
                    'end_date': date.today() + timedelta(days=90),
                    'budget_labor': Decimal('50000.00'),
                    'budget_materials': Decimal('30000.00'),
                    'budget_total': Decimal('80000.00'),
                }
            )
            
            if proj_created:
                self.stdout.write(self.style.SUCCESS(f'  ✅ Created demo project: {project.name}'))
            else:
                self.stdout.write(self.style.WARNING(f'  ⚠️  Demo project already exists'))
            
            # Grant client access to the project
            access, acc_created = ClientProjectAccess.objects.get_or_create(
                project=project,
                user=user,
                defaults={
                    'role': 'client',
                    'can_comment': True,
                    'can_create_tasks': True,
                }
            )
            
            if acc_created:
                self.stdout.write(self.style.SUCCESS(f'  ✅ Granted client access to project'))
            else:
                self.stdout.write(self.style.WARNING(f'  ⚠️  Client access already exists'))
        
        self.stdout.write(self.style.SUCCESS('\n' + '='*60))
        self.stdout.write(self.style.SUCCESS('✅ Demo Client User Created Successfully!\n'))
        self.stdout.write(self.style.SUCCESS('Login Credentials:'))
        self.stdout.write(self.style.SUCCESS(f'  Username: {username}'))
        self.stdout.write(self.style.SUCCESS(f'  Password: {password}'))
        self.stdout.write(self.style.SUCCESS(f'  Email: {email}'))
        self.stdout.write(self.style.SUCCESS(f'  Role: Client'))
        self.stdout.write(self.style.SUCCESS(f'  Project: {project.name}'))
        self.stdout.write(self.style.SUCCESS('='*60 + '\n'))
