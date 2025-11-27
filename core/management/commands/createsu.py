from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Crea un superusuario automáticamente si no existe"

    def handle(self, *args, **options):
        User = get_user_model()
        if not User.objects.filter(username="admin").exists():
            User.objects.create_superuser("admin", "admin@example.com", "admin123")
            self.stdout.write(self.style.SUCCESS("Superusuario creado: admin/admin123"))
        else:
            self.stdout.write(self.style.WARNING("El superusuario ya existe"))
