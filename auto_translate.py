#!/usr/bin/env python3#!/usr/bin/env python3

""""""

Auto-translate empty Spanish strings in django.poAuto-traductor inteligente para archivos .po

"""Detecta si el texto ya está en español y lo preserva

import re"""



filepath = '/Users/jesus/Documents/kibray/locale/es/LC_MESSAGES/django.po'# Palabras clave en español para detectar si ya está traducido

SPANISH_KEYWORDS = {

# Translation dictionary for common backend messages    "el",

translations = {    "la",

    # API errors    "los",

    "entity_type and action required": "tipo de entidad y acción requeridos",    "las",

    "entity_type and entity_id required": "tipo de entidad e ID de entidad requeridos",    "un",

    "Admin access required": "Se requiere acceso de administrador",    "una",

    "status required": "estado requerido",    "de",

    "Invalid status. Valid: %(statuses)s": "Estado inválido. Válidos: %(statuses)s",    "del",

    "Touch-up requires photo evidence before completion": "El retoque requiere evidencia fotográfica antes de completar",    "para",

    "Touch-up requires a photo before completion": "El retoque requiere una foto antes de completar",    "con",

    "dependency_id required": "dependency_id requerido",    "sin",

    "Dependency task not found": "Tarea de dependencia no encontrada",    "que",

    "Task not in Completada state": "La tarea no está en estado Completada",    "si",

    "Dependencies incomplete": "Dependencias incompletas",    "no",

    "Already tracking or touch-up": "Ya está en seguimiento o retoque",    "más",

    "Not tracking": "No está en seguimiento",    "muy",

    "image file required": "archivo de imagen requerido",    "también",

    "assigned_to is required": "assigned_to es requerido",    "aquí",

    "User not found": "Usuario no encontrado",    "ahí",

    "Invalid cost value": "Valor de costo inválido",    "donde",

    "Staff permission required": "Se requiere permiso de personal",    "cuando",

    "Cannot approve resolved damage": "No se puede aprobar daño resuelto",    "cómo",

    "Damage already resolved": "Daño ya resuelto",    "ción",

    "Change Order already created": "Orden de cambio ya creada",    "dad",

    "updates must be an object": "las actualizaciones deben ser un objeto",    "ión",

    "Unsupported algorithm: %(alg)s": "Algoritmo no soportado: %(alg)s",    "ñ",

    "Invalid or missing OTP for 2FA-enabled account": "OTP inválido o faltante para cuenta con 2FA habilitado",    "á",

    "2FA validation failed": "Validación 2FA falló",    "é",

    "Employee does not exist": "El empleado no existe",    "í",

    "This feature is only available for Admin/PM users.": "Esta funcionalidad solo está disponible para usuarios Admin/PM.",    "ó",

    "Ritual completed successfully!": "¡Ritual completado exitosamente!",    "ú",

    "Invalid step index": "Índice de paso inválido",    "año",

        "día",

    # Validation errors    "mes",

    "Amount must be greater than zero.": "El monto debe ser mayor que cero.",    "usuario",

    "Date cannot be in the future.": "La fecha no puede estar en el futuro.",    "proyecto",

    "Task cannot depend on itself": "La tarea no puede depender de sí misma",    "fecha",

    "A change order with this reference code already exists for this project": "Ya existe una orden de cambio con este código de referencia para este proyecto",    "nombre",

    "End date must be after start date": "La fecha de fin debe ser posterior a la fecha de inicio",    "descripción",

    "Selected organization is not active": "La organización seleccionada no está activa",}

    "Due date cannot be in the past": "La fecha de vencimiento no puede estar en el pasado",

    # Diccionario robusto de traducciones

    # Common termsTRANSLATIONS = {

    ", ": ", ",    # Django default messages

}    "This field is required.": "Este campo es obligatorio.",

    # Common UI

# Read file    "Amount": "Monto",

with open(filepath, 'r', encoding='utf-8') as f:    "Title": "Título",

    content = f.read()    "Description": "Descripción",

    "Date": "Fecha",

# Split into entries    "Time": "Hora",

entries = re.split(r'\n(?=#:|msgid)', content)    "Status": "Estado",

    "Priority": "Prioridad",

translated_count = 0    "Notes": "Notas",

new_entries = []    "Save": "Guardar",

    "Cancel": "Cancelar",

for entry in entries:    "Delete": "Eliminar",

    # Check if this entry has an empty msgstr    "Edit": "Editar",

    if 'msgstr ""' in entry and 'msgid ""' not in entry:    "Create": "Crear",

        # Extract msgid    "Back": "Volver",

        msgid_match = re.search(r'msgid "([^"]*)"', entry)    "Close": "Cerrar",

        if msgid_match:    "Submit": "Enviar",

            msgid_text = msgid_match.group(1)    # Status

                "Not started": "No iniciado",

            # Check if we have a translation    "In Progress": "En progreso",

            if msgid_text in translations:    "Completed": "Completado",

                # Replace empty msgstr with translation    "Blocked": "Bloqueado",

                entry = entry.replace('msgstr ""', f'msgstr "{translations[msgid_text]}"')    "Low": "Baja",

                translated_count += 1    "Medium": "Media",

        "High": "Alta",

    new_entries.append(entry)    "Urgent": "Urgente",

    # Payment methods

# Join back    "Transfer": "Transferencia",

new_content = '\n'.join(new_entries)    "Check": "Cheque",

    "Cash": "Efectivo",

# Write back    "Other": "Otro",

with open(filepath, 'w', encoding='utf-8') as f:    "Payment method": "Método de pago",

    f.write(new_content)    "Invoice or receipt": "Factura o comprobante",

    # Categories

print(f"Auto-translated {translated_count} strings")    "Food": "Comida",

    "Insurance": "Seguro",
    "Storage": "Almacén / Storage",
    "Office": "Oficina",
    # Construction phases
    "Site cleaning": "Limpieza del sitio",
    "Preparation": "Preparación",
    "Covering": "Cobertura",
    "Sealer": "Sellador",
    "Lacquer": "Laca",
    "Caulking": "Calafateo",
    "Painting": "Pintura",
    "Plastic removal": "Remoción de plástico",
    "Touch up": "Retoques",
    # Admin panel
    "Admin Panel": "Panel Administrativo",
    "Advanced Admin Panel": "Panel Administrativo Avanzado",
    "What can you do here?": "¿Qué puedes hacer aquí?",
    "User Management": "Gestión de Usuarios",
    "Data Management": "Gestión de Datos",
    "Audit and Logs": "Auditoría y Logs",
    "Quick Access": "Accesos Rápidos",
    "Total Users": "Total Usuarios",
    "Change Orders": "Órdenes de Cambio",
    "Expenses": "Gastos",
    "Schedule": "Cronograma",
    "Tasks": "Tareas",
    "Floor Plans": "Planos",
    "Create new client": "Crear nuevo cliente",
    "Create internal user": "Crear usuario interno",
    "Manage groups": "Gestionar grupos",
    "No recent users": "No hay usuarios recientes",
    "View complete logs": "Ver logs completos",
    "No recent activity": "No hay actividad reciente",
    "Django Admin": "Django Admin",
    # Forms
    "Register a new expense": "Registrar un nuevo gasto",
    "Modify expense data": "Modificar datos del gasto",
    "Invoice/Project Name": "Nombre Factura/Proyecto",
    "Income date": "Fecha de ingreso",
    "Project name or invoice": "Nombre del proyecto o factura",
    "Project name is required.": "El nombre del proyecto es obligatorio.",
    "Start date is required.": "La fecha de inicio es obligatoria.",
    # Budget
    "Total budget allocated to project": "Presupuesto total asignado al proyecto",
    "Budget for other expenses (insurance, storage, etc.)": "Presupuesto para otros gastos (seguros, almacenamiento, etc.)",
    # Tasks & Damage
    "No associated floor plan": "Sin plano asociado",
    "No associated pin": "Sin pin asociado",
    "No linked touch-up": "Sin touch-up vinculado",
    "No linked CO": "Sin CO vinculado",
    "Reported damage type": "Tipo de daño reportado",
    "Damage urgency level": "Nivel de urgencia del daño",
    "Estimated repair cost (optional)": "Costo estimado de reparación (opcional)",
    "Floor plan where damage is located (optional)": "Plano donde se encuentra el daño (opcional)",
    "Specific pin if applicable (optional)": "Pin específico si aplica (opcional)",
    "Related touch-up (optional)": "Touch-up relacionado (opcional)",
    "Related Change Order (optional)": "Change Order relacionado (opcional)",
    "Optional deadline": "Fecha límite opcional",
    "Task priority": "Prioridad de la tarea",
    "User who created the task (client or staff)": "Usuario que creó la tarea (cliente o staff)",
    # Daily planning
    "Achievements of the day...": "Logros del día...",
    "General notes...": "Notas generales...",
    "Safety incidents...": "Incidentes de seguridad...",
    "Delays or issues...": "Retrasos o problemas...",
    "Plan for tomorrow...": "Plan para mañana...",
    "Main calendar activity (e.g.: Cover and Prepare)": "Actividad principal del calendario (ej: Cubrir y Preparar)",
    "Progress percentage of this activity": "Porcentaje de progreso de esta actividad",
    "Select tasks that were completed or progressed today": "Selecciona las tareas que se completaron o avanzaron hoy",
    "Mark to be visible to client and owner": "Marcar para que sea visible para cliente y owner",
    "Ex: Crack in main bathroom wall": "Ej: Grieta en pared del baño principal",
    "Describe damage in as much detail as possible...": "Describe el daño con el mayor detalle posible...",
    "Ex: Kitchen - North Wall": "Ej: Cocina - Pared Norte",
    # Paint codes
    "Example: SW 7008 Alabaster, SW 6258 Tricorn Black": "Ejemplo: SW 7008 Alabaster, SW 6258 Tricorn Black",
    "Paint codes if different from common colors": "Códigos de pintura si son diferentes de los colores comunes",
    "Example: Milesi Butternut 072 - 2 coats": "Ejemplo: Milesi Butternut 072 - 2 coats",
    "Number of spots or imperfections detected": "Número de manchas o imperfecciones detectadas",
    "Notes about learnings, mistakes, or improvements for future projects": "Notas sobre aprendizajes, errores o mejoras para próximos proyectos",
    # Percentage
    "If you can't complete 100%, indicate the percentage achieved": "Si no puedes completar 100%, indica el porcentaje alcanzado",
    # CRUD operations
    "Create, edit and delete users, groups and permissions": "Crear, editar y eliminar usuarios, grupos y permisos",
    "Full CRUD management of projects, expenses, income, time entries": "Gestión CRUD completa de proyectos, gastos, ingresos, time entries",
    "View audit logs and system activity": "Ver logs de auditoría y actividad del sistema",
    "Configure master data and system parameters": "Configurar datos maestros y parámetros del sistema",
    "For daily operations (approvals, metrics, alerts), use the": "Para operaciones diarias (aprobaciones, métricas, alertas), usa el",
    "Manage users, roles, permissions and system groups.": "Administra usuarios, roles, permisos y grupos del sistema.",
    "Access and manage all system models.": "Accede y administra todos los modelos del sistema.",
    "Monitor system activity and changes made.": "Monitorea la actividad del sistema y cambios realizados.",
    # Time units
    "ago": "hace",
}


def is_already_spanish(text):
    """Detecta si el texto ya está en español"""
    text_lower = text.lower()

    # Si tiene caracteres especiales del español
    if any(char in text_lower for char in ["ñ", "á", "é", "í", "ó", "ú", "¿", "¡"]):
        return True

    # Si contiene palabras clave en español
    words = set(text_lower.split())
    if len(words & SPANISH_KEYWORDS) >= 1:
        return True

    return False


def translate_text(text):
    """Traduce un texto al español"""

    # Si ya está en español, dejarlo tal cual
    if is_already_spanish(text):
        return text

    # Buscar en diccionario
    if text in TRANSLATIONS:
        return TRANSLATIONS[text]

    # Si no hay traducción, dejarlo vacío
    return ""


def process_po_file(po_file_path):
    """Procesa un archivo .po y completa traducciones"""

    with open(po_file_path, encoding="utf-8") as f:
        lines = f.readlines()

    new_lines = []
    completed = 0
    already_spanish = 0
    i = 0

    while i < len(lines):
        line = lines[i]
        new_lines.append(line)

        # Buscar msgid seguido de msgstr vacío
        if line.startswith('msgid "') and not line.strip() == 'msgid ""':
            msgid = line[7:-2]  # Extraer texto entre comillas

            # Verificar si la siguiente línea es msgstr ""
            if i + 1 < len(lines) and lines[i + 1].strip() == 'msgstr ""':
                # Decidir traducción
                if is_already_spanish(msgid):
                    # El msgid ya está en español, copiarlo al msgstr
                    new_lines.append(f'msgstr "{msgid}"\n')
                    already_spanish += 1
                else:
                    # Intentar traducir
                    translation = translate_text(msgid)
                    if translation:
                        new_lines.append(f'msgstr "{translation}"\n')
                        completed += 1
                    else:
                        new_lines.append(lines[i + 1])

                i += 2
                continue

        i += 1

    # Guardar archivo
    with open(po_file_path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

    print(f"✅ Traducciones completadas: {completed}")
    print(f"🔄 Textos ya en español preservados: {already_spanish}")
    print(f"📊 Total procesado: {completed + already_spanish}")

    return completed + already_spanish


if __name__ == "__main__":
    po_file = "/Users/jesus/Documents/kibray/locale/es/LC_MESSAGES/django.po"
    total = process_po_file(po_file)
    print(f"\n🎉 Total: {total} traducciones")
    print("\n⚠️  Ejecuta: python3 manage.py compilemessages")
