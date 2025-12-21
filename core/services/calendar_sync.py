"""
Servicio de sincronización con Google Calendar y exportación iCal.
"""

from datetime import timedelta

from django.urls import reverse
from icalendar import Calendar, Event


def generate_ical_for_project(project):
    """
    Genera un archivo iCal (.ics) con todos los items del cronograma del proyecto.
    Compatible con Google Calendar, Outlook, Apple Calendar, etc.
    """
    cal = Calendar()
    cal.add("prodid", "-//Kibray Project Schedule//kibray.app//")
    cal.add("version", "2.0")
    cal.add("calscale", "GREGORIAN")
    cal.add("method", "PUBLISH")
    cal.add("x-wr-calname", f"{project.name} - Cronograma")
    cal.add("x-wr-timezone", "America/New_York")
    cal.add("x-wr-caldesc", f"Cronograma del proyecto {project.name}")

    # Agregar todos los schedule items
    for item in project.schedule_items.all():
        if not item.planned_start or not item.planned_end:
            continue

        event = Event()
        event.add("uid", f"schedule-item-{item.id}@kibray.app")
        event.add("summary", item.title)

        # Si es milestone, evento de día completo en la fecha de inicio
        if item.is_milestone:
            event.add("dtstart", item.planned_start)
            event.add("dtend", item.planned_start + timedelta(days=1))
            event.add(
                "description",
                f"🏁 Hito: {item.description or item.title}\n\nEstado: {item.get_status_display()}\nProgreso: {item.percent_complete}%",
            )
        else:
            # Evento de rango de fechas
            event.add("dtstart", item.planned_start)
            event.add("dtend", item.planned_end + timedelta(days=1))

            description = f"{item.description or ''}\n\n"
            description += f"Categoría: {item.category.name}\n"
            description += f"Estado: {item.get_status_display()}\n"
            description += f"Progreso: {item.percent_complete}%\n"
            description += f"Proyecto: {project.name}"

            event.add("description", description)

        # Color según estado
        if item.status == "DONE":
            event.add("color", "green")
        elif item.status == "IN_PROGRESS":
            event.add("color", "blue")
        elif item.status == "BLOCKED":
            event.add("color", "red")
        else:
            event.add("color", "gray")

        event.add("status", "CONFIRMED")
        event.add("transp", "OPAQUE")
        event.add("sequence", 0)

        # Categoría
        event.add("categories", [item.category.name, project.name])

        # Metadata adicional
        if item.cost_code:
            event.add("x-cost-code", item.cost_code.code)

        cal.add_component(event)

    return cal.to_ical()


def generate_google_calendar_link(project):
    """
    Genera un enlace directo para añadir al Google Calendar.
    Usa el formato de URL de Google Calendar.
    """
    items = project.schedule_items.filter(
        planned_start__isnull=False, planned_end__isnull=False
    ).order_by("planned_start")

    if not items.exists():
        return None

    # Crear eventos múltiples no es posible con un solo link
    # Retornar el primero como ejemplo o usar ICS
    first_item = items.first()

    base_url = "https://calendar.google.com/calendar/render"
    params = {
        "action": "TEMPLATE",
        "text": f"{project.name} - {first_item.title}",
        "dates": f"{first_item.planned_start.strftime('%Y%m%d')}/{(first_item.planned_end + timedelta(days=1)).strftime('%Y%m%d')}",
        "details": f"{first_item.description or ''}\n\nEstado: {first_item.get_status_display()}\nProgreso: {first_item.percent_complete}%",
        "location": project.address or "",
    }

    from urllib.parse import urlencode

    return f"{base_url}?{urlencode(params)}"


def create_calendar_subscription_url(project, request):
    """
    Genera una URL de suscripción al calendario del proyecto.
    Esta URL puede ser agregada a cualquier cliente de calendario (Google, Outlook, Apple).
    """
    # Construir URL absoluta para el endpoint ICS
    ics_path = reverse("project_schedule_ics", kwargs={"project_id": project.id})
    return request.build_absolute_uri(ics_path)
