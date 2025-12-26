"""
Management command para limpiar asignaciones antiguas (> 30 días).
Reduce costos de almacenamiento sin afectar funcionalidad.

Uso:
    python manage.py cleanup_old_assignments          # Dry-run (solo muestra)
    python manage.py cleanup_old_assignments --execute  # Elimina realmente
    python manage.py cleanup_old_assignments --days=60  # Personalizar días
"""
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from core.models import ResourceAssignment


class Command(BaseCommand):
    help = "Elimina asignaciones de empleados anteriores a X días (default: 30)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            type=int,
            default=30,
            help="Eliminar asignaciones anteriores a este número de días (default: 30)",
        )
        parser.add_argument(
            "--execute",
            action="store_true",
            help="Ejecutar la eliminación. Sin esto, solo muestra qué se eliminaría (dry-run).",
        )

    def handle(self, *args, **options):
        days = options["days"]
        execute = options["execute"]
        
        cutoff_date = timezone.localdate() - timedelta(days=days)
        
        # Encontrar asignaciones a eliminar
        old_assignments = ResourceAssignment.objects.filter(date__lt=cutoff_date)
        count = old_assignments.count()
        
        self.stdout.write(self.style.WARNING(f"\n{'='*60}"))
        self.stdout.write(self.style.WARNING("CLEANUP: Asignaciones Antiguas"))
        self.stdout.write(self.style.WARNING(f"{'='*60}\n"))
        
        self.stdout.write(f"📅 Fecha de corte: {cutoff_date} ({days} días atrás)")
        self.stdout.write(f"📊 Asignaciones encontradas: {count}")
        
        if count == 0:
            self.stdout.write(self.style.SUCCESS("\n✅ No hay asignaciones antiguas para eliminar."))
            return
        
        # Mostrar resumen por proyecto
        from django.db.models import Count
        by_project = old_assignments.values("project__name").annotate(
            total=Count("id")
        ).order_by("-total")[:10]
        
        self.stdout.write("\n📁 Top proyectos afectados:")
        for item in by_project:
            self.stdout.write(f"   • {item['project__name']}: {item['total']} asignaciones")
        
        # Rango de fechas
        oldest = old_assignments.order_by("date").first()
        newest = old_assignments.order_by("-date").first()
        if oldest and newest:
            self.stdout.write(f"\n📆 Rango: {oldest.date} → {newest.date}")
        
        if execute:
            self.stdout.write(self.style.WARNING(f"\n⚠️  Eliminando {count} asignaciones..."))
            deleted, _ = old_assignments.delete()
            self.stdout.write(self.style.SUCCESS(f"✅ {deleted} asignaciones eliminadas exitosamente."))
        else:
            self.stdout.write(self.style.NOTICE(
                f"\n🔍 DRY-RUN: Se eliminarían {count} asignaciones."
            ))
            self.stdout.write(self.style.NOTICE(
                "   Ejecuta con --execute para eliminar realmente."
            ))
        
        self.stdout.write("")
