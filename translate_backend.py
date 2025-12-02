#!/usr/bin/env python3
import re

filepath = '/Users/jesus/Documents/kibray/locale/es/LC_MESSAGES/django.po'

translations = {
    "entity_type and action required": "tipo de entidad y acción requeridos",
    "entity_type and entity_id required": "tipo de entidad e ID de entidad requeridos",
    "Admin access required": "Se requiere acceso de administrador",
    "status required": "estado requerido",
    "Touch-up requires photo evidence before completion": "El retoque requiere evidencia fotográfica antes de completar",
    "Touch-up requires a photo before completion": "El retoque requiere una foto antes de completar",
    "dependency_id required": "dependency_id requerido",
    "Dependency task not found": "Tarea de dependencia no encontrada",
    "Task not in Completada state": "La tarea no está en estado Completada",
    "Dependencies incomplete": "Dependencias incompletas",
    "Already tracking or touch-up": "Ya está en seguimiento o retoque",
    "Not tracking": "No está en seguimiento",
    "image file required": "archivo de imagen requerido",
    "assigned_to is required": "assigned_to es requerido",
    "User not found": "Usuario no encontrado",
    "Invalid cost value": "Valor de costo inválido",
    "Staff permission required": "Se requiere permiso de personal",
    "Cannot approve resolved damage": "No se puede aprobar daño resuelto",
    "Damage already resolved": "Daño ya resuelto",
    "Change Order already created": "Orden de cambio ya creada",
    "updates must be an object": "las actualizaciones deben ser un objeto",
    "Invalid or missing OTP for 2FA-enabled account": "OTP inválido o faltante para cuenta con 2FA habilitado",
    "2FA validation failed": "Validación 2FA falló",
    "Employee does not exist": "El empleado no existe",
    "This feature is only available for Admin/PM users.": "Esta funcionalidad solo está disponible para usuarios Admin/PM.",
    "Ritual completed successfully!": "¡Ritual completado exitosamente!",
    "Invalid step index": "Índice de paso inválido",
    "Amount must be greater than zero.": "El monto debe ser mayor que cero.",
    "Date cannot be in the future.": "La fecha no puede estar en el futuro.",
    "Task cannot depend on itself": "La tarea no puede depender de sí misma",
    "A change order with this reference code already exists for this project": "Ya existe una orden de cambio con este código de referencia para este proyecto",
    "End date must be after start date": "La fecha de fin debe ser posterior a la fecha de inicio",
    "Selected organization is not active": "La organización seleccionada no está activa",
    "Due date cannot be in the past": "La fecha de vencimiento no puede estar en el pasado",
}

with open(filepath, 'r', encoding='utf-8') as f:
    lines = f.readlines()

result = []
i = 0
translated_count = 0

while i < len(lines):
    line = lines[i]
    result.append(line)
    
    if line.startswith('msgid "') and not line.startswith('msgid ""'):
        msgid_text = line[7:-2]
        
        if i + 1 < len(lines) and lines[i + 1].strip() == 'msgstr ""':
            if msgid_text in translations:
                result.append(f'msgstr "{translations[msgid_text]}"\n')
                translated_count += 1
                i += 2
                continue
    
    i += 1

with open(filepath, 'w', encoding='utf-8') as f:
    f.writelines(result)

print(f"Translated {translated_count} strings")
