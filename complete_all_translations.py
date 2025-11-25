#!/usr/bin/env python3
"""
Completa TODAS las traducciones faltantes al 100%
"""

import re
import sys

# Diccionario MASIVO de traducciones
TRANSLATIONS = {
    # Django defaults
    "This field is required.": "Este campo es obligatorio.",
    "Enter a valid email address.": "Introduce una dirección de correo válida.",
    "Enter a valid URL.": "Introduce una URL válida.",
    "Enter a valid date.": "Introduce una fecha válida.",
    "Enter a valid time.": "Introduce una hora válida.",
    "Enter a whole number.": "Introduce un número entero.",
    "Ensure this value is less than or equal to %(limit_value)s.": "Asegúrate de que este valor sea menor o igual a %(limit_value)s.",
    "Ensure this value is greater than or equal to %(limit_value)s.": "Asegúrate de que este valor sea mayor o igual a %(limit_value)s.",
    
    # Common UI
    "Welcome": "Bienvenido",
    "Dashboard": "Panel de Control",
    "Home": "Inicio",
    "Login": "Iniciar Sesión",
    "Logout": "Cerrar Sesión",
    "Save": "Guardar",
    "Cancel": "Cancelar",
    "Delete": "Eliminar",
    "Edit": "Editar",
    "Create": "Crear",
    "Update": "Actualizar",
    "View": "Ver",
    "Back": "Volver",
    "Next": "Siguiente",
    "Previous": "Anterior",
    "Search": "Buscar",
    "Filter": "Filtrar",
    "Export": "Exportar",
    "Import": "Importar",
    "Print": "Imprimir",
    "Download": "Descargar",
    "Upload": "Subir",
    "Submit": "Enviar",
    "Close": "Cerrar",
    "Open": "Abrir",
    "Add": "Agregar",
    "Remove": "Quitar",
    "Select": "Seleccionar",
    "Actions": "Acciones",
    "Options": "Opciones",
    "Settings": "Configuración",
    "Profile": "Perfil",
    "Help": "Ayuda",
    "About": "Acerca de",
    "Contact": "Contacto",
    "Loading": "Cargando",
    "Please wait": "Por favor espere",
    "Success": "Éxito",
    "Error": "Error",
    "Warning": "Advertencia",
    "Info": "Información",
    "Confirm": "Confirmar",
    "Yes": "Sí",
    "No": "No",
    "OK": "Aceptar",
    "Details": "Detalles",
    "Summary": "Resumen",
    "Total": "Total",
    "Status": "Estado",
    "Date": "Fecha",
    "Time": "Hora",
    "Name": "Nombre",
    "Description": "Descripción",
    "Notes": "Notas",
    "Comments": "Comentarios",
    "Required": "Requerido",
    "Optional": "Opcional",
    "All": "Todos",
    "None": "Ninguno",
    "Show": "Mostrar",
    "Hide": "Ocultar",
    "More": "Más",
    "Less": "Menos",
    
    # Projects
    "Project": "Proyecto",
    "Projects": "Proyectos",
    "Project Name": "Nombre del Proyecto",
    "Project Overview": "Resumen del Proyecto",
    "Project List": "Lista de Proyectos",
    "Create Project": "Crear Proyecto",
    "Edit Project": "Editar Proyecto",
    "Delete Project": "Eliminar Proyecto",
    "Active Projects": "Proyectos Activos",
    "Completed Projects": "Proyectos Completados",
    "Project Manager": "Gerente de Proyecto",
    "Start Date": "Fecha de Inicio",
    "End Date": "Fecha de Fin",
    "Budget": "Presupuesto",
    "Client": "Cliente",
    "Clients": "Clientes",
    "Address": "Dirección",
    "Location": "Ubicación",
    "Progress": "Progreso",
    
    # Financial
    "Income": "Ingreso",
    "Incomes": "Ingresos",
    "Expense": "Gasto",
    "Expenses": "Gastos",
    "Profit": "Ganancia",
    "Loss": "Pérdida",
    "Revenue": "Ingresos",
    "Cost": "Costo",
    "Costs": "Costos",
    "Amount": "Monto",
    "Payment": "Pago",
    "Payments": "Pagos",
    "Invoice": "Factura",
    "Invoices": "Facturas",
    "Receipt": "Recibo",
    "Balance": "Balance",
    "Transaction": "Transacción",
    "Transactions": "Transacciones",
    
    # Time & Schedule
    "Schedule": "Cronograma",
    "Schedules": "Cronogramas",
    "Calendar": "Calendario",
    "Event": "Evento",
    "Events": "Eventos",
    "Task": "Tarea",
    "Tasks": "Tareas",
    "Time Entry": "Registro de Tiempo",
    "Time Entries": "Registros de Tiempo",
    "Hours": "Horas",
    "Minutes": "Minutos",
    "Duration": "Duración",
    "Start Time": "Hora de Inicio",
    "End Time": "Hora de Fin",
    "Daily": "Diario",
    "Weekly": "Semanal",
    "Monthly": "Mensual",
    "Yearly": "Anual",
    "Today": "Hoy",
    "Yesterday": "Ayer",
    "Tomorrow": "Mañana",
    "This Week": "Esta Semana",
    "Last Week": "Semana Pasada",
    "Next Week": "Próxima Semana",
    "This Month": "Este Mes",
    "Last Month": "Mes Pasado",
    "Next Month": "Próximo Mes",
    
    # Materials & Inventory
    "Material": "Material",
    "Materials": "Materiales",
    "Inventory": "Inventario",
    "Stock": "Existencias",
    "Quantity": "Cantidad",
    "Unit": "Unidad",
    "Units": "Unidades",
    "Supplier": "Proveedor",
    "Suppliers": "Proveedores",
    "Order": "Orden",
    "Orders": "Órdenes",
    "Request": "Solicitud",
    "Requests": "Solicitudes",
    
    # People
    "Employee": "Empleado",
    "Employees": "Empleados",
    "User": "Usuario",
    "Users": "Usuarios",
    "Team": "Equipo",
    "Teams": "Equipos",
    "Role": "Rol",
    "Roles": "Roles",
    "Permission": "Permiso",
    "Permissions": "Permisos",
    "Group": "Grupo",
    "Groups": "Grupos",
    
    # Reports
    "Report": "Reporte",
    "Reports": "Reportes",
    "Statistics": "Estadísticas",
    "Chart": "Gráfico",
    "Charts": "Gráficos",
    "Graph": "Gráfica",
    "Data": "Datos",
    "Analytics": "Análisis",
    
    # Status
    "Not started": "No iniciado",
    "In Progress": "En Progreso",
    "In progress": "En progreso",
    "Completed": "Completado",
    "Complete": "Completo",
    "Blocked": "Bloqueado",
    "Cancelled": "Cancelado",
    "Pending": "Pendiente",
    "Approved": "Aprobado",
    "Rejected": "Rechazado",
    "Draft": "Borrador",
    "Published": "Publicado",
    "Active": "Activo",
    "Inactive": "Inactivo",
    
    # Priority
    "Low": "Baja",
    "Medium": "Media",
    "High": "Alta",
    "Urgent": "Urgente",
    "Critical": "Crítico",
    
    # Payment
    "Transfer": "Transferencia",
    "Check": "Cheque",
    "Cash": "Efectivo",
    "Credit Card": "Tarjeta de Crédito",
    "Debit Card": "Tarjeta de Débito",
    "Other": "Otro",
    "Payment method": "Método de pago",
    "Invoice or receipt": "Factura o comprobante",
    "Paid": "Pagado",
    "Unpaid": "No Pagado",
    
    # Categories
    "Food": "Comida",
    "Insurance": "Seguro",
    "Storage": "Almacenamiento",
    "Warehouse": "Almacén",
    "Office": "Oficina",
    "Transport": "Transporte",
    "Transportation": "Transporte",
    "Tools": "Herramientas",
    "Equipment": "Equipo",
    "Maintenance": "Mantenimiento",
    "Utilities": "Servicios",
    
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
    "Touch-up": "Retoques",
    "Inspection": "Inspección",
    "Final inspection": "Inspección final",
    
    # Admin panel
    "Admin Panel": "Panel Administrativo",
    "Advanced Admin Panel": "Panel Administrativo Avanzado",
    "Admin Dashboard": "Panel de Administración",
    "What can you do here?": "¿Qué puedes hacer aquí?",
    "User Management": "Gestión de Usuarios",
    "Data Management": "Gestión de Datos",
    "Audit and Logs": "Auditoría y Logs",
    "Quick Access": "Acceso Rápido",
    "Quick Actions": "Acciones Rápidas",
    "Total Users": "Total Usuarios",
    "Change Orders": "Órdenes de Cambio",
    "Change Order": "Orden de Cambio",
    "Floor Plans": "Planos",
    "Floor Plan": "Plano",
    "Create new client": "Crear nuevo cliente",
    "Create internal user": "Crear usuario interno",
    "Manage groups": "Gestionar grupos",
    "No recent users": "No hay usuarios recientes",
    "View complete logs": "Ver logs completos",
    "No recent activity": "No hay actividad reciente",
    "Recent activity": "Actividad reciente",
    "Django Admin": "Administración Django",
    
    # Forms
    "Register a new expense": "Registrar un nuevo gasto",
    "Register expense": "Registrar gasto",
    "Modify expense data": "Modificar datos del gasto",
    "Invoice/Project Name": "Nombre Factura/Proyecto",
    "Income date": "Fecha de ingreso",
    "Project name or invoice": "Nombre del proyecto o factura",
    "Project name is required.": "El nombre del proyecto es obligatorio.",
    "Start date is required.": "La fecha de inicio es obligatoria.",
    "End date is required.": "La fecha de fin es obligatoria.",
    "Amount is required.": "El monto es obligatorio.",
    "Enter a valid amount.": "Introduce un monto válido.",
    
    # Budget
    "Total budget allocated to project": "Presupuesto total asignado al proyecto",
    "Budget for labor": "Presupuesto para mano de obra",
    "Budget for materials": "Presupuesto para materiales",
    "Budget for other expenses": "Presupuesto para otros gastos",
    "Budget for other expenses (insurance, storage, etc.)": "Presupuesto para otros gastos (seguros, almacenamiento, etc.)",
    
    # Tasks & Damage
    "No associated floor plan": "Sin plano asociado",
    "No associated pin": "Sin pin asociado",
    "No linked touch-up": "Sin touch-up vinculado",
    "No linked CO": "Sin CO vinculado",
    "Reported damage type": "Tipo de daño reportado",
    "Damage type": "Tipo de daño",
    "Damage urgency level": "Nivel de urgencia del daño",
    "Urgency level": "Nivel de urgencia",
    "Estimated repair cost": "Costo estimado de reparación",
    "Estimated repair cost (optional)": "Costo estimado de reparación (opcional)",
    "Floor plan where damage is located": "Plano donde se encuentra el daño",
    "Floor plan where damage is located (optional)": "Plano donde se encuentra el daño (opcional)",
    "Specific pin if applicable": "Pin específico si aplica",
    "Specific pin if applicable (optional)": "Pin específico si aplica (opcional)",
    "Related touch-up": "Touch-up relacionado",
    "Related touch-up (optional)": "Touch-up relacionado (opcional)",
    "Related Change Order": "Change Order relacionado",
    "Related Change Order (optional)": "Change Order relacionado (opcional)",
    "Optional deadline": "Fecha límite opcional",
    "Deadline": "Fecha límite",
    "Task priority": "Prioridad de la tarea",
    "User who created the task": "Usuario que creó la tarea",
    "User who created the task (client or staff)": "Usuario que creó la tarea (cliente o staff)",
    "Created by": "Creado por",
    "Assigned to": "Asignado a",
    
    # Daily planning - Placeholders
    "Achievements of the day...": "Logros del día...",
    "General notes...": "Notas generales...",
    "Safety incidents...": "Incidentes de seguridad...",
    "Delays or issues...": "Retrasos o problemas...",
    "Plan for tomorrow...": "Plan para mañana...",
    "Main calendar activity": "Actividad principal del calendario",
    "Main calendar activity (e.g.: Cover and Prepare)": "Actividad principal del calendario (ej: Cubrir y Preparar)",
    "Progress percentage of this activity": "Porcentaje de progreso de esta actividad",
    "Select tasks that were completed or progressed today": "Selecciona las tareas que se completaron o avanzaron hoy",
    "Mark to be visible to client and owner": "Marcar para que sea visible para cliente y owner",
    "Visible to client": "Visible para el cliente",
    "Ex: Crack in main bathroom wall": "Ej: Grieta en pared del baño principal",
    "Describe damage in as much detail as possible...": "Describe el daño con el mayor detalle posible...",
    "Ex: Kitchen - North Wall": "Ej: Cocina - Pared Norte",
    
    # Paint codes
    "Example: SW 7008 Alabaster, SW 6258 Tricorn Black": "Ejemplo: SW 7008 Alabaster, SW 6258 Tricorn Black",
    "Paint codes if different from common colors": "Códigos de pintura si son diferentes de los colores comunes",
    "Paint codes": "Códigos de pintura",
    "Example: Milesi Butternut 072 - 2 coats": "Ejemplo: Milesi Butternut 072 - 2 coats",
    "Number of spots or imperfections detected": "Número de manchas o imperfecciones detectadas",
    "Notes about learnings, mistakes, or improvements for future projects": "Notas sobre aprendizajes, errores o mejoras para próximos proyectos",
    "Lessons learned": "Lecciones aprendidas",
    
    # Percentage
    "If you can't complete 100%, indicate the percentage achieved": "Si no puedes completar 100%, indica el porcentaje alcanzado",
    "Percentage": "Porcentaje",
    "Complete": "Completar",
    
    # CRUD operations
    "Create, edit and delete users, groups and permissions": "Crear, editar y eliminar usuarios, grupos y permisos",
    "Full CRUD management of projects, expenses, income, time entries": "Gestión CRUD completa de proyectos, gastos, ingresos, registros de tiempo",
    "View audit logs and system activity": "Ver logs de auditoría y actividad del sistema",
    "Configure master data and system parameters": "Configurar datos maestros y parámetros del sistema",
    "For daily operations (approvals, metrics, alerts), use the": "Para operaciones diarias (aprobaciones, métricas, alertas), usa el",
    "Manage users, roles, permissions and system groups.": "Administra usuarios, roles, permisos y grupos del sistema.",
    "Access and manage all system models.": "Accede y administra todos los modelos del sistema.",
    "Monitor system activity and changes made.": "Monitorea la actividad del sistema y cambios realizados.",
    
    # Time units
    "ago": "hace",
    "day": "día",
    "days": "días",
    "hour": "hora",
    "hours": "horas",
    "minute": "minuto",
    "minutes": "minutos",
    "second": "segundo",
    "seconds": "segundos",
    "week": "semana",
    "weeks": "semanas",
    "month": "mes",
    "months": "meses",
    "year": "año",
    "years": "años",
    
    # Common phrases
    "Are you sure?": "¿Estás seguro?",
    "Are you sure you want to delete this?": "¿Estás seguro de que quieres eliminar esto?",
    "This action cannot be undone": "Esta acción no se puede deshacer",
    "This action cannot be undone.": "Esta acción no se puede deshacer.",
    "Successfully saved": "Guardado exitosamente",
    "Successfully deleted": "Eliminado exitosamente",
    "Successfully updated": "Actualizado exitosamente",
    "Successfully created": "Creado exitosamente",
    "No results found": "No se encontraron resultados",
    "No records found": "No se encontraron registros",
    "Please select": "Por favor seleccione",
    "Please select an option": "Por favor seleccione una opción",
    "Choose file": "Elegir archivo",
    "No file chosen": "Ningún archivo elegido",
    "Change password": "Cambiar contraseña",
    "Forgot password": "Olvidé mi contraseña",
    "Forgot password?": "¿Olvidaste tu contraseña?",
    "Remember me": "Recordarme",
    "Sign in": "Ingresar",
    "Sign out": "Salir",
    "Sign up": "Registrarse",
    "Username": "Nombre de usuario",
    "Password": "Contraseña",
    "Email": "Correo electrónico",
    "Phone": "Teléfono",
    "Company": "Empresa",
    "Price": "Precio",
    "Tax": "Impuesto",
    "Taxes": "Impuestos",
    "Discount": "Descuento",
    "Subtotal": "Subtotal",
    "Grand Total": "Total General",
    
    # Notifications
    "Notification": "Notificación",
    "Notifications": "Notificaciones",
    "Mark as read": "Marcar como leído",
    "Mark all as read": "Marcar todo como leído",
    "Clear all": "Limpiar todo",
    "No notifications": "No hay notificaciones",
    "You have no new notifications": "No tienes notificaciones nuevas",
    
    # Errors
    "An error occurred": "Ocurrió un error",
    "Page not found": "Página no encontrada",
    "Access denied": "Acceso denegado",
    "You don't have permission to access this page": "No tienes permiso para acceder a esta página",
    "Invalid credentials": "Credenciales inválidas",
    "Invalid username or password": "Nombre de usuario o contraseña inválidos",
    
    # Actions
    "Register": "Registrar",
    "Register Hours": "Registrar Horas",
    "Add Expense": "Agregar Gasto",
    "Add Income": "Agregar Ingreso",
    "View Details": "Ver Detalles",
    "View All": "Ver Todo",
    "Show All": "Mostrar Todo",
    "Show More": "Mostrar Más",
    "Show Less": "Mostrar Menos",
    "Load More": "Cargar Más",
    "Refresh": "Actualizar",
    "Reset": "Restablecer",
    "Clear": "Limpiar",
    "Apply": "Aplicar",
    "Send": "Enviar",
    "Reply": "Responder",
    "Forward": "Reenviar",
    "Share": "Compartir",
    "Copy": "Copiar",
    "Paste": "Pegar",
    "Cut": "Cortar",
    "Undo": "Deshacer",
    "Redo": "Rehacer",
    
    # Filters
    "All types": "Todos los tipos",
    "All statuses": "Todos los estados",
    "All projects": "Todos los proyectos",
    "All users": "Todos los usuarios",
    "Filter by": "Filtrar por",
    "Sort by": "Ordenar por",
    "Order by": "Ordenar por",
    "Ascending": "Ascendente",
    "Descending": "Descendente",
    "From": "Desde",
    "To": "Hasta",
    "Between": "Entre",
    
    # Pagination
    "Previous": "Anterior",
    "Next": "Siguiente",
    "First": "Primera",
    "Last": "Última",
    "Page": "Página",
    "of": "de",
    "Showing": "Mostrando",
    "to": "a",
    "entries": "entradas",
    "results": "resultados",
    
    # File upload
    "Upload file": "Subir archivo",
    "Upload image": "Subir imagen",
    "Upload document": "Subir documento",
    "Choose files": "Elegir archivos",
    "Drop files here": "Arrastra archivos aquí",
    "Drag and drop": "Arrastra y suelta",
    "Browse": "Examinar",
    "Maximum file size": "Tamaño máximo de archivo",
    "Allowed file types": "Tipos de archivo permitidos",
    
    # Misc
    "Language": "Idioma",
    "Theme": "Tema",
    "Light": "Claro",
    "Dark": "Oscuro",
    "Auto": "Automático",
    "Version": "Versión",
    "Last updated": "Última actualización",
    "Created": "Creado",
    "Modified": "Modificado",
    "By": "Por",
    "Owner": "Propietario",
    "Type": "Tipo",
    "Category": "Categoría",
    "Categories": "Categorías",
    "Tag": "Etiqueta",
    "Tags": "Etiquetas",
    "Title": "Título",
    "Subject": "Asunto",
    "Message": "Mensaje",
    "Content": "Contenido",
    "Attachment": "Adjunto",
    "Attachments": "Adjuntos",
    "Link": "Enlace",
    "Links": "Enlaces",
    "File": "Archivo",
    "Files": "Archivos",
    "Folder": "Carpeta",
    "Folders": "Carpetas",
    "Image": "Imagen",
    "Images": "Imágenes",
    "Document": "Documento",
    "Documents": "Documentos",
    "Video": "Video",
    "Videos": "Videos",
    "Audio": "Audio",
    "Archive": "Archivo",
    "Archives": "Archivos",
}

# Palabras clave en español para detectar si ya está traducido
SPANISH_KEYWORDS = {
    'el', 'la', 'los', 'las', 'un', 'una', 'de', 'del', 'para', 'con', 'sin',
    'que', 'si', 'no', 'más', 'muy', 'también', 'aquí', 'ahí', 'donde',
    'cuando', 'cómo', 'ción', 'dad', 'ión', 'ñ', 'á', 'é', 'í', 'ó', 'ú',
    'año', 'día', 'mes', 'usuario', 'proyecto', 'fecha', 'nombre', 'descripción',
    'crear', 'editar', 'eliminar', 'guardar', 'cancelar', 'todos', 'ninguno',
    'ejemplo', 'opcional', 'requerido', 'selecciona', 'introduce', 'escribe'
}

def is_already_spanish(text):
    """Detecta si el texto ya está en español"""
    if not text or len(text) < 2:
        return False
        
    text_lower = text.lower()
    
    # Si tiene caracteres especiales del español
    if any(char in text_lower for char in ['ñ', 'á', 'é', 'í', 'ó', 'ú', '¿', '¡']):
        return True
    
    # Si contiene palabras clave en español
    words = set(re.findall(r'\w+', text_lower))
    if len(words & SPANISH_KEYWORDS) >= 1:
        return True
    
    return False

def translate_text(text):
    """Traduce un texto al español"""
    # Si ya está en español, dejarlo tal cual
    if is_already_spanish(text):
        return text
    
    # Buscar traducción exacta
    if text in TRANSLATIONS:
        return TRANSLATIONS[text]
    
    # Buscar case-insensitive
    for key, value in TRANSLATIONS.items():
        if key.lower() == text.lower():
            return value
    
    # Si contiene variables de Django, intentar traducir la parte fija
    if '%(' in text or '{' in text:
        for key, value in TRANSLATIONS.items():
            if key in text:
                return text.replace(key, value)
    
    # Intentar traducciones comunes de palabras sueltas
    simple_translations = {
        'view': 'ver',
        'list': 'lista',
        'all': 'todos',
        'new': 'nuevo',
        'old': 'antiguo',
        'recent': 'reciente',
        'last': 'último',
        'first': 'primero',
        'total': 'total',
        'count': 'contador',
        'number': 'número',
        'id': 'id',
        'code': 'código',
        'reference': 'referencia',
        'value': 'valor',
        'label': 'etiqueta',
        'display': 'mostrar',
        'main': 'principal',
        'general': 'general',
        'default': 'predeterminado',
        'custom': 'personalizado',
    }
    
    lower_text = text.lower()
    for eng, esp in simple_translations.items():
        if eng in lower_text:
            return text.replace(eng, esp).replace(eng.capitalize(), esp.capitalize())
    
    return ""

def process_po_file(po_file_path):
    """Procesa un archivo .po y completa todas las traducciones"""
    
    with open(po_file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    new_lines = []
    completed = 0
    already_spanish = 0
    still_empty = 0
    i = 0
    
    print("🔄 Procesando traducciones...")
    
    while i < len(lines):
        line = lines[i]
        new_lines.append(line)
        
        # Buscar msgid seguido de msgstr vacío
        if line.startswith('msgid "') and not line.strip() == 'msgid ""':
            # Extraer texto entre comillas (manejo de multilinea)
            msgid_lines = [line[7:-2]]  # Quitar 'msgid "' y '"\n'
            j = i + 1
            
            # Leer líneas adicionales del msgid si son multilinea
            while j < len(lines) and lines[j].startswith('"') and not lines[j].startswith('msgstr'):
                msgid_lines.append(lines[j][1:-2])  # Quitar comillas
                j += 1
            
            msgid = ''.join(msgid_lines)
            
            # Verificar si la siguiente línea es msgstr ""
            if j < len(lines) and lines[j].strip() == 'msgstr ""':
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
                        new_lines.append(lines[j])
                        still_empty += 1
                
                i = j + 1
                continue
        
        i += 1
    
    # Guardar archivo
    with open(po_file_path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    
    print(f"\n✅ Traducciones del inglés: {completed}")
    print(f"🔄 Textos ya en español: {already_spanish}")
    print(f"⏳ Aún vacías: {still_empty}")
    print(f"📊 Total procesado: {completed + already_spanish}")
    
    total_attempted = completed + already_spanish + still_empty
    if total_attempted > 0:
        success_rate = ((completed + already_spanish) / total_attempted) * 100
        print(f"🎯 Tasa de éxito: {success_rate:.1f}%")
    
    return completed + already_spanish

if __name__ == "__main__":
    po_file = "/Users/jesus/Documents/kibray/locale/es/LC_MESSAGES/django.po"
    total = process_po_file(po_file)
    print(f"\n🎉 Total: {total} traducciones completadas")
    print("\n⚠️  Ahora ejecuta:")
    print("   python3 manage.py compilemessages")
    print("   python3 manage.py runserver")
