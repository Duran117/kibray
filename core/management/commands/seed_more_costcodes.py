from django.core.management.base import BaseCommand

from core.models import CostCode

DATA = [
    ("LAB003", "Detail Labor", "labor"),
    ("MAT003", "Caulking Materials", "material"),
    ("EQP002", "Lift Rental", "equipment"),
]


class Command(BaseCommand):
    help = "Seed extra cost codes."

    def handle(self, *args, **options):
        new = 0
        for code, name, cat in DATA:
            _, created = CostCode.objects.get_or_create(
                code=code, defaults={"name": name, "category": cat, "active": True}
            )
            if created:
                new += 1
        self.stdout.write(self.style.SUCCESS(f"Added: {new}"))
