from django.core.management.base import BaseCommand

from core.models import TimeEntry


class Command(BaseCommand):
    help = "Recalcula hours_worked de todas las TimeEntry usando la lógica actual del modelo."

    def handle(self, *args, **options):
        count = 0
        for t in TimeEntry.objects.all():
            t.save()
            count += 1
        self.stdout.write(self.style.SUCCESS(f"Recalculadas {count} entradas"))
