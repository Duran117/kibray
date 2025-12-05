from django.core.management.base import BaseCommand
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Create a superuser for production if it does not exist'

    def handle(self, *args, **options):
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser(
                username='admin',
                email='admin@kibraypainting.com',
                password='Kibray123!Secure'
            )
            self.stdout.write(self.style.SUCCESS('✅ Superuser created successfully!'))
            self.stdout.write('Username: admin')
            self.stdout.write('Email: admin@kibraypainting.com')
            self.stdout.write('Password: Kibray123!Secure')
        else:
            self.stdout.write(self.style.WARNING('⚠️  Superuser already exists'))
