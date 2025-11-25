#!/usr/bin/env python3
"""
Auto-traductor inteligente para archivos .po
Detecta si el texto ya está en español y lo preserva
"""

import re
import sys

# Palabras clave en español para detectar si ya está traducido
SPANISH_KEYWORDS = {
    'el', 'la', 'los', 'las', 'un', 'una', 'de', 'del', 'para', 'con', 'sin',
    'que', 'si', 'no', 'más', 'muy', 'también', 'aquí', 'ahí', 'donde',
    'cuando', 'cómo', 'ción', 'dad', 'ión', 'ñ', 'á', 'é', 'í', 'ó', 'ú',
    'año', 'día', 'mes', 'usuario', 'proyecto', 'fecha', 'nombre', 'descripción'
}

# Diccionario robusto de traducciones
TRANSLATIONS = {
    # Django default messages
    "This field is required.": "Este campo es obligatorio.",
    
    # Common UI  
    "Amount": "Monto",
    "Title": "Título",
    "Description": "Descripción",
    "Date": "Fecha",
    "Time": "Hora",
    "Status": "Estado",
    "Priority": "Prioridad",
    "Notes": "Notas",
    "Save": "Guardar",
    "Cancel": "Cancelar",
    "Delete": "Eliminar",
    "Edit": "Editar",
    "Create": "Crear",
    "Back": "Volver",
    "Close": "Cerrar",
    "Submit": "Enviar",
    
    # Status
    "Not started": "No iniciado",
    "In Progress": "En progreso",
    "Completed": "Completado",
    "Blocked": "Bloqueado",
    "Low": "Baja",
    "Medium": "Media",
    "High": "Alta",
    "Urgent": "Urgente",
    
    # Payment methods
    "Transfer": "Transferencia",
    "Check": "Cheque",
    "Cash": "Efectivo",
    "Other": "Otro",
    "Payment method": "Método de pago",
    "Invoice or receipt": "Factura o comprobante",
    
    # Categories
    "Food": "Comida",
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
    if any(char in text_lower for char in ['ñ', 'á', 'é', 'í', 'ó', 'ú', '¿', '¡']):
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
    
    with open(po_file_path, 'r', encoding='utf-8') as f:
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
    with open(po_file_path, 'w', encoding='utf-8') as f:
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
