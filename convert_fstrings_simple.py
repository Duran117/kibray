#!/usr/bin/env python3
"""
Simple f-string to % format converter for messages
"""

# Read file
with open('/Users/jesus/Documents/kibray/core/views.py', encoding='utf-8') as f:
    lines = f.readlines()

# Define simple replacements (line contains -> replace with)
replacements = {
    'messages.success(request, f"Tarea \'{title}\' creada exitosamente. El PM será notificado.")':
        'messages.success(request, _("Tarea \'%(title)s\' creada exitosamente. El PM será notificado.") % {"title": title})',

    'messages.success(request, f"Reporte creado con {len(photos)} foto(s)")':
        'messages.success(request, _("Reporte creado con %(count)s foto(s)") % {"count": len(photos)})',

    'messages.success(request, f"{username} invitado.")':
        'messages.success(request, _("%(username)s invitado.") % {"username": username})',

    'messages.success(request, f"{updated} registros asignados al CO #{co.id}.")':
        'messages.success(request, _("%(count)s registros asignados al CO #%(co_id)s.") % {"count": updated, "co_id": co.id})',

    'messages.success(request, f"CO #{co.id} creado y {updated} registros asignados.")':
        'messages.success(request, _("CO #%(co_id)s creado y %(count)s registros asignados.") % {"co_id": co.id, "count": updated})',

    'messages.error(request, f"Error: {e}")':
        'messages.error(request, _("Error: %(error)s") % {"error": e})',

    'messages.success(request, f"✅ Factura {invoice.invoice_number} marcada como ENVIADA.")':
        'messages.success(request, _("✅ Factura %(invoice_number)s marcada como ENVIADA.") % {"invoice_number": invoice.invoice_number})',

    'messages.warning(request, f"La factura ya tiene status: {invoice.get_status_display()}")':
        'messages.warning(request, _("La factura ya tiene status: %(status)s") % {"status": invoice.get_status_display()})',

    'messages.success(request, f"✅ Factura {invoice.invoice_number} marcada como APROBADA.")':
        'messages.success(request, _("✅ Factura %(invoice_number)s marcada como APROBADA.") % {"invoice_number": invoice.invoice_number})',

    'messages.error(request, f"Error enviando correo: {e}")':
        'messages.error(request, _("Error enviando correo: %(error)s") % {"error": e})',

    'messages.success(request, f"Daily Log creado para {dl.date}")':
        'messages.success(request, _("Daily Log creado para %(date)s") % {"date": dl.date})',

    'messages.error(request, f"Error de validación: {str(e)}")':
        'messages.error(request, _("Error de validación: %(error)s") % {"error": str(e)})',

    'messages.error(request, f"Error al activar proyecto: {str(e)}")':
        'messages.error(request, _("Error al activar proyecto: %(error)s") % {"error": str(e)})',

    'messages.success(request, f"{len(photos)} foto(s) agregada(s)")':
        'messages.success(request, _("%(count)s foto(s) agregada(s)") % {"count": len(photos)})',
}

# Process lines
new_lines = []
for line in lines:
    new_line = line
    for old, new in replacements.items():
        if old in line:
            new_line = line.replace(old, new)
            break
    new_lines.append(new_line)

# Write back
with open('/Users/jesus/Documents/kibray/core/views.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print(f"Processed {len(replacements)} f-string patterns")
