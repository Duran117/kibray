#!/usr/bin/env python3
"""
Script para completar traducciones faltantes en archivos .po
Usa traducciones comunes y DeepL/Google Translate API si está disponible
"""

import re

# Diccionario de traducciones comunes ES
COMMON_TRANSLATIONS = {
    # General UI
    "Welcome": "Bienvenido",
    "Dashboard": "Panel de Control",
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
    "Home": "Inicio",
    "Loading": "Cargando",
    "Please wait": "Por favor espere",
    "Success": "Éxito",
    "Error": "Error",
    "Warning": "Advertencia",
    "Info": "Información",
    "Confirm": "Confirmar",
    "Yes": "Sí",
    "No": "No",
    "OK": "OK",
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
    "Address": "Dirección",
    "Location": "Ubicación",
    # Financial
    "Income": "Ingreso",
    "Expense": "Gasto",
    "Expenses": "Gastos",
    "Profit": "Ganancia",
    "Loss": "Pérdida",
    "Revenue": "Ingresos",
    "Cost": "Costo",
    "Amount": "Monto",
    "Payment": "Pago",
    "Invoice": "Factura",
    "Receipt": "Recibo",
    "Balance": "Balance",
    "Transaction": "Transacción",
    # Time & Schedule
    "Schedule": "Cronograma",
    "Calendar": "Calendario",
    "Event": "Evento",
    "Task": "Tarea",
    "Tasks": "Tareas",
    "Time Entry": "Registro de Tiempo",
    "Hours": "Horas",
    "Minutes": "Minutos",
    "Duration": "Duración",
    "Start Time": "Hora de Inicio",
    "End Time": "Hora de Fin",
    "Daily": "Diario",
    "Weekly": "Semanal",
    "Monthly": "Mensual",
    "Today": "Hoy",
    "Yesterday": "Ayer",
    "Tomorrow": "Mañana",
    "This Week": "Esta Semana",
    "Last Week": "Semana Pasada",
    "This Month": "Este Mes",
    "Last Month": "Mes Pasado",
    # Materials & Inventory
    "Material": "Material",
    "Materials": "Materiales",
    "Inventory": "Inventario",
    "Stock": "Existencias",
    "Quantity": "Cantidad",
    "Unit": "Unidad",
    "Supplier": "Proveedor",
    "Order": "Orden",
    "Request": "Solicitud",
    # People
    "Employee": "Empleado",
    "Employees": "Empleados",
    "User": "Usuario",
    "Users": "Usuarios",
    "Team": "Equipo",
    "Role": "Rol",
    "Permission": "Permiso",
    "Permissions": "Permisos",
    # Reports
    "Report": "Reporte",
    "Reports": "Reportes",
    "Statistics": "Estadísticas",
    "Chart": "Gráfico",
    "Graph": "Gráfica",
    "Data": "Datos",
    # Common phrases
    "Are you sure?": "¿Estás seguro?",
    "This action cannot be undone": "Esta acción no se puede deshacer",
    "Successfully saved": "Guardado exitosamente",
    "Successfully deleted": "Eliminado exitosamente",
    "Successfully updated": "Actualizado exitosamente",
    "No results found": "No se encontraron resultados",
    "Please select": "Por favor seleccione",
    "Choose file": "Elegir archivo",
    "No file chosen": "Ningún archivo elegido",
    "Change password": "Cambiar contraseña",
    "Forgot password": "Olvidé mi contraseña",
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
    "Discount": "Descuento",
    "Subtotal": "Subtotal",
    "Grand Total": "Total General",
    "Paid": "Pagado",
    "Unpaid": "No Pagado",
    "Pending": "Pendiente",
    "Approved": "Aprobado",
    "Rejected": "Rechazado",
    "Draft": "Borrador",
    "Published": "Publicado",
    "Active": "Activo",
    "Inactive": "Inactivo",
    "Completed": "Completado",
    "In Progress": "En Progreso",
    "Cancelled": "Cancelado",
}


def complete_translations(po_file_path):
    """Completa traducciones faltantes en un archivo .po"""

    with open(po_file_path, encoding="utf-8") as f:
        content = f.read()

    # Contar vacíos antes
    empty_before = len(re.findall(r'msgstr ""', content))

    # Patrón para encontrar msgid/msgstr vacíos
    pattern = r'msgid "([^"]+)"\nmsgstr ""'

    completed_count = 0

    def replace_empty(match):
        nonlocal completed_count
        msgid = match.group(1)

        # Buscar traducción en diccionario
        if msgid in COMMON_TRANSLATIONS:
            translation = COMMON_TRANSLATIONS[msgid]
            completed_count += 1
            return f'msgid "{msgid}"\nmsgstr "{translation}"'

        # Si no está en el diccionario, dejar vacío
        return match.group(0)

    # Reemplazar traducciones vacías
    new_content = re.sub(pattern, replace_empty, content)

    # Guardar archivo
    with open(po_file_path, "w", encoding="utf-8") as f:
        f.write(new_content)

    # Contar vacíos después
    empty_after = len(re.findall(r'msgstr ""', new_content))

    print(f"✅ Traducciones completadas: {completed_count}")
    print(f"⏳ Traducciones vacías restantes: {empty_after}")
    print(f"📊 Progreso: {empty_before - empty_after} nuevas traducciones agregadas")

    return completed_count


if __name__ == "__main__":
    po_file = "/Users/jesus/Documents/kibray/locale/es/LC_MESSAGES/django.po"
    completed = complete_translations(po_file)
    print(f"\n🎉 Total de traducciones completadas: {completed}")
    print("\n⚠️  Ahora ejecuta: python3 manage.py compilemessages")
