"""
Django management command to create initial superuser
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import os


class Command(BaseCommand):
    help = 'Creates a superuser if it does not exist'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            default='admin',
            help='Username for the superuser'
        )
        parser.add_argument(
            '--email',
            type=str,
            default='admin@kibray.com',
            help='Email for the superuser'
        )
        parser.add_argument(
            '--password',
            type=str,
            default=None,
            help='Password for the superuser (if not provided, will use env var DJANGO_SUPERUSER_PASSWORD)'
        )
        parser.add_argument(
            '--noinput',
            '--no-input',
            action='store_true',
            help='Do not prompt for any input'
        )

    def handle(self, *args, **options):
        User = get_user_model()
        username = options['username']
        email = options['email']
        password = options['password'] or os.getenv('DJANGO_SUPERUSER_PASSWORD', 'Kibray2025!Admin')

        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.WARNING(f'⚠️  User "{username}" already exists'))
            user = User.objects.get(username=username)
            self.stdout.write(f'   Email: {user.email}')
            self.stdout.write(f'   Is superuser: {user.is_superuser}')
            self.stdout.write(f'   Is staff: {user.is_staff}')
        else:
            user = User.objects.create_superuser(username, email, password)
            self.stdout.write(self.style.SUCCESS(f'✅ Superuser created successfully!'))
            self.stdout.write(f'   Username: {username}')
            self.stdout.write(f'   Email: {email}')
            self.stdout.write(f'   Password: [HIDDEN]')
            self.stdout.write(f'   Is superuser: {user.is_superuser}')
            self.stdout.write(f'   Is staff: {user.is_staff}')
