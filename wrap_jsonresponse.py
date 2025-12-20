#!/usr/bin/env python3
"""
Wrap JsonResponse "message" strings with gettext()
"""

# Read file
with open('/Users/jesus/Documents/kibray/core/views.py', encoding='utf-8') as f:
    content = f.read()

# Simple string replacements for JsonResponse messages
replacements = [
    ('{"success": True, "message": "Archivo actualizado"}',
     '{"success": True, "message": gettext("Archivo actualizado")}'),

    ('"touchup_id": touchup.id, "message": "Touch-up creado exitosamente"}',
     '"touchup_id": touchup.id, "message": gettext("Touch-up creado exitosamente")}'),

    ('{"success": True, "message": "Touch-up actualizado"}',
     '{"success": True, "message": gettext("Touch-up actualizado")}'),

    ('{"success": True, "message": "Touch-up completado exitosamente"}',
     '{"success": True, "message": gettext("Touch-up completado exitosamente")}'),

    ('{"success": True, "message": "Touch-up aprobado exitosamente"}',
     '{"success": True, "message": gettext("Touch-up aprobado exitosamente")}'),

    ('{"success": True, "message": "Touch-up rechazado, el empleado debe corregirlo"}',
     '{"success": True, "message": gettext("Touch-up rechazado, el empleado debe corregirlo")}'),

    ('{"success": True, "message": "Pin actualizado"}',
     '{"success": True, "message": gettext("Pin actualizado")}'),

    ('{"success": True, "message": "Foto eliminada"}',
     '{"success": True, "message": gettext("Foto eliminada")}'),
]

for old, new in replacements:
    content = content.replace(old, new)

# Write back
with open('/Users/jesus/Documents/kibray/core/views.py', 'w', encoding='utf-8') as f:
    f.write(content)

print(f"Wrapped {len(replacements)} JsonResponse messages")
