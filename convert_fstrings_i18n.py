#!/usr/bin/env python3
"""
Convert remaining f-strings in messages to gettext % formatting
"""
import re

# Read the file
with open('/Users/jesus/Documents/kibray/core/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

# List of f-string patterns to convert
conversions = [
    # Pattern: messages.xxx(request, f"Estado actualizado a {inst.get_status_display()}")
    (
        r'messages\.success\(request, f"Estado actualizado a \{inst\.get_status_display\(\)\}"\)',
        r'messages.success(request, _("Estado actualizado a %(status)s") % {"status": inst.get_status_display()})'
    ),
    # Pattern: messages.xxx(request, f"Tarea '{title}' creada exitosamente. El PM será notificado.")
    (
        r"messages\.success\(request, f\"Tarea '\{title\}' creada exitosamente\. El PM será notificado\.\"\\)",
        r'messages.success(request, _("Tarea \'%(title)s\' creada exitosamente. El PM será notificado.") % {"title": title})'
    ),
    # Pattern: messages.xxx(request, f"Reporte creado con {len(photos)} foto(s)")
    (
        r'messages\.success\(request, f"Reporte creado con \{len\(photos\)\} foto\(s\)"\)',
        r'messages.success(request, _("Reporte creado con %(count)s foto(s)") % {"count": len(photos)})'
    ),
    # Pattern: messages.xxx(request, f"{username} invitado.")
    (
        r'messages\.success\(request, f"\{username\} invitado\."\)',
        r'messages.success(request, _("%(username)s invitado.") % {"username": username})'
    ),
    # Pattern: messages.xxx(request, f"{updated} registros asignados al CO #{co.id}.")
    (
        r'messages\.success\(request, f"\{updated\} registros asignados al CO #\{co\.id\}\."\)',
        r'messages.success(request, _("%(count)s registros asignados al CO #%(co_id)s.") % {"count": updated, "co_id": co.id})'
    ),
    # Pattern: messages.xxx(request, f"CO #{co.id} creado y {updated} registros asignados.")
    (
        r'messages\.success\(request, f"CO #\{co\.id\} creado y \{updated\} registros asignados\."\)',
        r'messages.success(request, _("CO #%(co_id)s creado y %(count)s registros asignados.") % {"co_id": co.id, "count": updated})'
    ),
    # Pattern: messages.xxx(request, f"Error: {e}")
    (
        r'messages\.error\(request, f"Error: \{e\}"\)',
        r'messages.error(request, _("Error: %(error)s") % {"error": e})'
    ),
    # Pattern: messages.xxx(request, f"✅ Factura {invoice.invoice_number} marcada como ENVIADA.")
    (
        r'messages\.success\(request, f"✅ Factura \{invoice\.invoice_number\} marcada como ENVIADA\."\)',
        r'messages.success(request, _("✅ Factura %(invoice_number)s marcada como ENVIADA.") % {"invoice_number": invoice.invoice_number})'
    ),
    # Pattern: messages.xxx(request, f"La factura ya tiene status: {invoice.get_status_display()}")
    (
        r'messages\.warning\(request, f"La factura ya tiene status: \{invoice\.get_status_display\(\)\}"\)',
        r'messages.warning(request, _("La factura ya tiene status: %(status)s") % {"status": invoice.get_status_display()})'
    ),
    # Pattern: messages.xxx(request, f"✅ Factura {invoice.invoice_number} marcada como APROBADA.")
    (
        r'messages\.success\(request, f"✅ Factura \{invoice\.invoice_number\} marcada como APROBADA\."\)',
        r'messages.success(request, _("✅ Factura %(invoice_number)s marcada como APROBADA.") % {"invoice_number": invoice.invoice_number})'
    ),
    # Pattern: messages.xxx(request, f"Error enviando correo: {e}")
    (
        r'messages\.error\(request, f"Error enviando correo: \{e\}"\)',
        r'messages.error(request, _("Error enviando correo: %(error)s") % {"error": e})'
    ),
    # Pattern: messages.xxx(request, f"Daily Log creado para {dl.date}")
    (
        r'messages\.success\(request, f"Daily Log creado para \{dl\.date\}"\)',
        r'messages.success(request, _("Daily Log creado para %(date)s") % {"date": dl.date})'
    ),
    # Pattern: messages.xxx(request, f"Error de validación: {str(e)}")
    (
        r'messages\.error\(request, f"Error de validación: \{str\(e\)\}"\)',
        r'messages.error(request, _("Error de validación: %(error)s") % {"error": str(e)})'
    ),
    # Pattern: messages.xxx(request, f"Error al activar proyecto: {str(e)}")
    (
        r'messages\.error\(request, f"Error al activar proyecto: \{str\(e\)\}"\)',
        r'messages.error(request, _("Error al activar proyecto: %(error)s") % {"error": str(e)})'
    ),
    # Pattern: messages.xxx(request, f"{len(photos)} foto(s) agregada(s)")
    (
        r'messages\.success\(request, f"\{len\(photos\)\} foto\(s\) agregada\(s\)"\)',
        r'messages.success(request, _("%(count)s foto(s) agregada(s)") % {"count": len(photos)})'
    ),
]

for pattern, replacement in conversions:
    content = re.sub(pattern, replacement, content)

# Write back
with open('/Users/jesus/Documents/kibray/core/views.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("F-strings converted successfully!")
print("Total conversions:", len(conversions))
