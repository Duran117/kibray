#!/usr/bin/env python3
"""
Convert remaining f-strings batch 2
"""

# Read file
with open('/Users/jesus/Documents/kibray/core/views.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Additional replacements
replacements = {
    'messages.success(request, f"✓ Entrada registrada a las {now.strftime(\'%H:%M\')}.")':
        'messages.success(request, _("✓ Entrada registrada a las %(time)s.") % {"time": now.strftime(\'%H:%M\')})',
    
    'messages.error(request, f"Acción no soportada: {action}")':
        'messages.error(request, _("Acción no soportada: %(action)s") % {"action": action})',
    
    'messages.success(request, f"Ticket procesado. {len(items_data)} ítem(s) recibido(s).")':
        'messages.success(request, _("Ticket procesado. %(count)s ítem(s) recibido(s).") % {"count": len(items_data)})',
    
    'messages.success(request, f"Compra directa registrada. {len(items_data)} ítem(s) agregado(s) al inventario.")':
        'messages.success(request, _("Compra directa registrada. %(count)s ítem(s) agregado(s) al inventario.") % {"count": len(items_data)})',
    
    'messages.success(request, f"Solicitud #{mat_request.id} marcada como ordenada.")':
        'messages.success(request, _("Solicitud #%(id)s marcada como ordenada.") % {"id": mat_request.id})',
    
    'messages.success(request, f"Solicitud #{mat_request.id} aprobada")':
        'messages.success(request, _("Solicitud #%(id)s aprobada") % {"id": mat_request.id})',
    
    'messages.success(request, f"Solicitud #{mat_request.id} rechazada")':
        'messages.success(request, _("Solicitud #%(id)s rechazada") % {"id": mat_request.id})',
    
    'messages.success(request, f"Gasto #{expense.id} creado por ${total_amount}")':
        'messages.success(request, _("Gasto #%(id)s creado por $%(amount)s") % {"id": expense.id, "amount": total_amount})',
    
    'messages.error(request, f"Error al crear gasto: {str(e)}")':
        'messages.error(request, _("Error al crear gasto: %(error)s") % {"error": str(e)})',
    
    'messages.success(request, f"Inventario ajustado: {quantity} {item.unit}")':
        'messages.success(request, _("Inventario ajustado: %(quantity)s %(unit)s") % {"quantity": quantity, "unit": item.unit})',
    
    'messages.error(request, f"Cantidad inválida: {str(e)}")':
        'messages.error(request, _("Cantidad inválida: %(error)s") % {"error": str(e)})',
    
    'messages.error(request, f"Error: {str(e)}")':
        'messages.error(request, _("Error: %(error)s") % {"error": str(e)})',
    
    'messages.warning(request, f"Plan already exists for {plan_date}")':
        'messages.warning(request, _("Plan already exists for %(date)s") % {"date": plan_date})',
    
    'messages.success(request, f"Daily plan created for {plan_date}")':
        'messages.success(request, _("Daily plan created for %(date)s") % {"date": plan_date})',
    
    'messages.success(request, f"Activity \'{activity.title}\' marked as complete!")':
        'messages.success(request, _("Activity \'%(title)s\' marked as complete!") % {"title": activity.title})',
    
    'messages.success(request, f"Progreso recalculado: {item.percent_complete}%")':
        'messages.success(request, _("Progreso recalculado: %(percent)s%%") % {"percent": item.percent_complete})',
    
    'messages.error(request, f"Error al generar cronograma: {str(e)}")':
        'messages.error(request, _("Error al generar cronograma: %(error)s") % {"error": str(e)})',
    
    'messages.success(request, f"{len(photos)} foto(s) agregada(s) al pin")':
        'messages.success(request, _("%(count)s foto(s) agregada(s) al pin") % {"count": len(photos)})',
    
    'messages.success(request, f"Cliente {client.get_full_name()} desactivado exitosamente.")':
        'messages.success(request, _("Cliente %(name)s desactivado exitosamente.") % {"name": client.get_full_name()})',
    
    'messages.success(request, f"Cliente {client_name} eliminado permanentemente.")':
        'messages.success(request, _("Cliente %(name)s eliminado permanentemente.") % {"name": client_name})',
    
    'messages.success(request, f"Contraseña actualizada y email enviado a {client.email}")':
        'messages.success(request, _("Contraseña actualizada y email enviado a %(email)s") % {"email": client.email})',
    
    'messages.warning(request, f"Contraseña actualizada pero hubo un error al enviar el email: {str(e)}")':
        'messages.warning(request, _("Contraseña actualizada pero hubo un error al enviar el email: %(error)s") % {"error": str(e)})',
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

print(f"Processed {len(replacements)} additional f-string patterns")
