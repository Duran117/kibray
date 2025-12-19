"""Seed de datos demo para el Gantt v2 (fases/items/tareas/dependencias).

Ejecutar con:
  source .venv/bin/activate && python scripts/seed_gantt_v2_demo.py
"""
from __future__ import annotations

import os
import sys
from datetime import date, timedelta
from pathlib import Path

import django

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "kibray_backend.settings")
django.setup()

from core.models import Project, ScheduleDependencyV2, ScheduleItemV2, SchedulePhaseV2, ScheduleTaskV2  # noqa: E402


def main() -> None:
    project = Project.objects.first()
    if not project:
        print("⚠️  No hay proyectos en la base. Crea uno primero (Project).")
        return

    print(f"Usando proyecto {project.id}: {project.name}")

    phase_defs = [
        ("Planificación", "#22d3ee", 0),
        ("Ejecución", "#a855f7", 1),
        ("Cierre", "#f97316", 2),
    ]

    phases = {}
    for name, color, order in phase_defs:
        phase, _ = SchedulePhaseV2.objects.get_or_create(
            project=project, name=name, defaults={"color": color, "order": order}
        )
        phases[name] = phase
    print(f"Fases: {', '.join(phases.keys())}")

    today = date.today()
    items_def = [
        ("Kickoff inicial", "Planificación", -2, 0, 100, "done", "#22d3ee", False),
        ("Plan maestro", "Planificación", -1, 3, 40, "in_progress", "#06b6d4", False),
        ("Obra gruesa", "Ejecución", 1, 10, 20, "in_progress", "#a855f7", False),
        ("Entrega de materiales", "Ejecución", 4, 4, 0, "planned", "#14b8a6", True),
        ("Acabados", "Ejecución", 11, 18, 0, "planned", "#f59e0b", False),
        ("Hito: entrega parcial", "Cierre", 19, 19, 0, "planned", "#f97316", True),
    ]

    items: dict[str, ScheduleItemV2] = {}
    for idx, (name, phase_name, start_off, end_off, progress, status, color, is_ms) in enumerate(items_def):
        phase = phases[phase_name]
        start = today + timedelta(days=start_off)
        end = today + timedelta(days=end_off)
        item, created = ScheduleItemV2.objects.get_or_create(
            project=project,
            phase=phase,
            name=name,
            defaults={
                "start_date": start,
                "end_date": end,
                "progress": progress,
                "status": status,
                "color": color,
                "is_milestone": is_ms,
                "order": idx,
            },
        )
        if not created:
            item.start_date = start
            item.end_date = end
            item.progress = progress
            item.status = status
            item.color = color
            item.is_milestone = is_ms
            item.order = idx
            item.save()
        items[name] = item
        print(f"{ '✓ nuevo' if created else '↺ actualizado' }: {name} ({start} → {end})")

    task_map = {
        "Plan maestro": [
            ("Definir alcance", "in_progress", today + timedelta(days=1)),
            ("Costeo preliminar", "pending", today + timedelta(days=2)),
        ],
        "Obra gruesa": [
            ("Demolición", "pending", None),
            ("Estructura", "pending", None),
        ],
        "Acabados": [
            ("Pintura", "pending", today + timedelta(days=12)),
            ("Iluminación", "pending", today + timedelta(days=14)),
        ],
    }

    for item_name, tasks in task_map.items():
        item = items.get(item_name)
        if not item:
            continue
        for order, (title, status, due) in enumerate(tasks):
            task, _ = ScheduleTaskV2.objects.get_or_create(
                item=item,
                title=title,
                defaults={"status": status, "due_date": due, "order": order},
            )
            task.status = status
            task.due_date = due
            task.order = order
            task.save()

    deps = [
        ("Plan maestro", "Obra gruesa"),
        ("Obra gruesa", "Acabados"),
    ]

    for source_name, target_name in deps:
        source = items.get(source_name)
        target = items.get(target_name)
        if not source or not target:
            continue
        dep, _ = ScheduleDependencyV2.objects.get_or_create(
            source_item=source, target_item=target, defaults={"dependency_type": "FS"}
        )
        dep.dependency_type = "FS"
        dep.save()

    print(f"Items totales en proyecto: {ScheduleItemV2.objects.filter(project=project).count()}")
    print(f"Tareas totales en proyecto: {ScheduleTaskV2.objects.filter(item__project=project).count()}")
    print("✅ Seed Gantt v2 completo")


if __name__ == "__main__":
    main()
