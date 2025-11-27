#!/usr/bin/env python3
"""
Script FINAL para completar el 100% de traducciones
Si msgid ya está en español, lo copia a msgstr
"""

import re

# Traducciones adicionales específicas
SPECIFIC_TRANSLATIONS = {
    "Monto": "Monto",
    "ej: Soleado, 75°F": "ej: Soleado, 75°F",
    "Retrasos o problemas...": "Retrasos o problemas...",
    "Ej: Cocina - Pared Norte": "Ej: Cocina - Pared Norte",
    "Transferencia": "Transferencia",
    "Cheque": "Cheque",
    "Otro": "Otro",
    "Factura o comprobante": "Factura o comprobante",
    "Seguro": "Seguro",
    "Oficina": "Oficina",
    "Bloqueado": "Bloqueado",
    "Baja": "Baja",
    "Media": "Media",
    "Alta": "Alta",
    "Urgente": "Urgente",
    "If you can't complete 100%, indicate the percentage achieved": "Si no puedes completar 100%, indica el porcentaje alcanzado",
    "Panel Administrativo": "Panel Administrativo",
    "Panel Administrativo Avanzado": "Panel Administrativo Avanzado",
    "Gestionar grupos": "Gestionar grupos",
    "Gastos": "Gastos",
    "Tiempo": "Tiempo",
    "Ver logs completos": "Ver logs completos",
    "Cronograma": "Cronograma",
    "Tareas": "Tareas",
    "Grupo": "Grupo",
    "usuarios": "usuarios",
    "permisos": "permisos",
    "Usuarios": "Usuarios",
    "Ej: Administradores, Empleados, Clientes...": "Ej: Administradores, Empleados, Clientes...",
    "Acceso completo al sistema": "Acceso completo al sistema",
    "Siguiente paso": "Siguiente paso",
    "Nuevo Grupo": "Nuevo Grupo",
    "Usuarios en este grupo": "Usuarios en este grupo",
    "Permisos asignados": "Permisos asignados",
    "Usuarios:": "Usuarios:",
    "Administradores": "Administradores",
    "Empleados": "Empleados",
    "Acceso a proyectos, tareas, time entries y touch-ups": "Acceso a proyectos, tareas, time entries y touch-ups",
    "Ver sus proyectos, facturas y documentos": "Ver sus proyectos, facturas y documentos",
    "Buscar": "Buscar",
    "Acciones": "Acciones",
    "Anterior": "Anterior",
    "Siguiente": "Siguiente",
    "Comienza creando tu primer registro": "Comienza creando tu primer registro",
    "Cliente": "Cliente",
    "Tintes o Acabados": "Tintes o Acabados",
    "Presupuesto": "Presupuesto",
    "Presupuesto Materiales": "Presupuesto Materiales",
    "Presupuesto Otros": "Presupuesto Otros",
    "Rol": "Rol",
}


def has_spanish_chars(text):
    """Detecta caracteres típicos del español"""
    spanish_chars = ["ñ", "Ñ", "á", "é", "í", "ó", "ú", "Á", "É", "Í", "Ó", "Ú", "¿", "¡"]
    return any(char in text for char in spanish_chars)


def is_likely_spanish(text):
    """Determina si un texto probablemente ya está en español"""
    if not text or len(text) < 2:
        return False

    # Si tiene caracteres especiales del español
    if has_spanish_chars(text):
        return True

    # Palabras comunes en español
    spanish_words = [
        "el",
        "la",
        "los",
        "las",
        "un",
        "una",
        "de",
        "del",
        "al",
        "para",
        "con",
        "sin",
        "por",
        "que",
        "si",
        "no",
        "más",
        "muy",
        "también",
        "aquí",
        "ahí",
        "donde",
        "cuando",
        "cómo",
        "este",
        "esta",
        "estos",
        "estas",
        "ese",
        "esa",
        "esos",
        "esas",
        "año",
        "día",
        "mes",
        "usuario",
        "usuarios",
        "proyecto",
        "proyectos",
        "fecha",
        "nombre",
        "descripción",
        "crear",
        "editar",
        "eliminar",
        "guardar",
        "cancelar",
        "todos",
        "todas",
        "ninguno",
        "ninguna",
        "ejemplo",
        "opcional",
        "requerido",
        "selecciona",
        "introduce",
        "escribe",
        "grupo",
        "grupos",
        "permiso",
        "permisos",
        "acceso",
        "sistema",
        "panel",
        "administrativo",
        "siguiente",
        "anterior",
        "nuevo",
        "nueva",
        "buscar",
        "filtrar",
        "exportar",
        "gastos",
        "ingresos",
        "tiempo",
        "cronograma",
        "tareas",
        "cliente",
        "clientes",
        "empleado",
        "empleados",
        "administrador",
        "administradores",
        "presupuesto",
        "materiales",
        "otros",
        "monto",
        "cheque",
        "transferencia",
        "factura",
        "comprobante",
        "seguro",
        "oficina",
        "bloqueado",
        "baja",
        "media",
        "alta",
        "urgente",
        "ver",
        "gestionar",
        "asignados",
        "completo",
        "registro",
        "rol",
        "tintes",
        "acabados",
        "comienza",
        "creando",
        "primer",
        "paso",
        "retrasos",
        "problemas",
        "cocina",
        "pared",
        "norte",
        "sur",
        "este",
        "oeste",
    ]

    text_lower = text.lower()
    words_in_text = re.findall(r"\b\w+\b", text_lower)

    # Si tiene al menos una palabra en español
    for word in words_in_text:
        if word in spanish_words:
            return True

    # Terminaciones típicas del español
    if any(text_lower.endswith(suffix) for suffix in ["ción", "sión", "dad", "tad", "dor", "dora", "mente"]):
        return True

    return False


def process_po_file_final(po_file_path):
    """Procesamiento final: si msgid está en español, copiarlo a msgstr"""

    with open(po_file_path, encoding="utf-8") as f:
        lines = f.readlines()

    new_lines = []
    auto_copied = 0
    from_dict = 0
    still_empty = 0
    i = 0

    print("🔄 Procesando traducciones finales...")

    while i < len(lines):
        line = lines[i]
        new_lines.append(line)

        # Buscar msgid seguido de msgstr vacío
        if line.startswith('msgid "') and not line.strip() == 'msgid ""':
            msgid = line[7:-2]  # Extraer texto entre comillas

            # Verificar si la siguiente línea es msgstr ""
            if i + 1 < len(lines) and lines[i + 1].strip() == 'msgstr ""':
                # Primero verificar el diccionario
                if msgid in SPECIFIC_TRANSLATIONS:
                    new_lines.append(f'msgstr "{SPECIFIC_TRANSLATIONS[msgid]}"\n')
                    from_dict += 1
                # Si ya está en español, copiarlo
                elif is_likely_spanish(msgid):
                    new_lines.append(f'msgstr "{msgid}"\n')
                    auto_copied += 1
                else:
                    # Intentar traducción básica de palabras comunes
                    translation = get_basic_translation(msgid)
                    if translation:
                        new_lines.append(f'msgstr "{translation}"\n')
                        from_dict += 1
                    else:
                        new_lines.append(lines[i + 1])
                        still_empty += 1

                i += 2
                continue

        i += 1

    # Guardar archivo
    with open(po_file_path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

    print(f"\n✅ Auto-copiadas (ya en español): {auto_copied}")
    print(f"✅ Traducidas del diccionario: {from_dict}")
    print(f"⏳ Aún vacías: {still_empty}")
    print(f"📊 Total completado: {auto_copied + from_dict}")

    return auto_copied + from_dict


def get_basic_translation(text):
    """Traducciones básicas de palabras comunes en inglés"""
    basic = {
        "View": "Ver",
        "List": "Lista",
        "All": "Todos",
        "New": "Nuevo",
        "Recent": "Reciente",
        "Last": "Último",
        "First": "Primero",
        "Total": "Total",
        "Count": "Contador",
        "Number": "Número",
        "Code": "Código",
        "Reference": "Referencia",
        "Value": "Valor",
        "Label": "Etiqueta",
        "Display": "Mostrar",
        "Main": "Principal",
        "General": "General",
        "Default": "Predeterminado",
        "Custom": "Personalizado",
        "Search": "Buscar",
        "Filter": "Filtrar",
        "Sort": "Ordenar",
        "Group": "Grupo",
        "Role": "Rol",
        "Permission": "Permiso",
        "User": "Usuario",
        "Admin": "Administrador",
        "Staff": "Personal",
        "Client": "Cliente",
        "Project": "Proyecto",
        "Task": "Tarea",
        "Time": "Tiempo",
        "Date": "Fecha",
        "Hour": "Hora",
        "Day": "Día",
        "Week": "Semana",
        "Month": "Mes",
        "Year": "Año",
        "Budget": "Presupuesto",
        "Cost": "Costo",
        "Price": "Precio",
        "Amount": "Monto",
        "Total": "Total",
        "Subtotal": "Subtotal",
        "Tax": "Impuesto",
        "Discount": "Descuento",
        "Payment": "Pago",
        "Invoice": "Factura",
        "Receipt": "Recibo",
        "Expense": "Gasto",
        "Income": "Ingreso",
        "Material": "Material",
        "Supplier": "Proveedor",
        "Order": "Orden",
        "Status": "Estado",
        "Priority": "Prioridad",
        "Category": "Categoría",
        "Type": "Tipo",
        "Name": "Nombre",
        "Description": "Descripción",
        "Notes": "Notas",
        "Comments": "Comentarios",
        "Actions": "Acciones",
        "Options": "Opciones",
        "Settings": "Configuración",
        "Help": "Ayuda",
        "Save": "Guardar",
        "Cancel": "Cancelar",
        "Delete": "Eliminar",
        "Edit": "Editar",
        "Create": "Crear",
        "Update": "Actualizar",
        "Add": "Agregar",
        "Remove": "Quitar",
        "Back": "Volver",
        "Next": "Siguiente",
        "Previous": "Anterior",
        "Close": "Cerrar",
        "Submit": "Enviar",
    }

    return basic.get(text, "")


if __name__ == "__main__":
    po_file = "/Users/jesus/Documents/kibray/locale/es/LC_MESSAGES/django.po"
    total = process_po_file_final(po_file)
    print(f"\n🎉 Total: {total} traducciones completadas en esta pasada")
    print("\n⚠️  Ejecuta:")
    print("   python3 manage.py compilemessages")
