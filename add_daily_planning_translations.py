#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para agregar traducciones españolas al archivo django.po
"""

import re

# Traducciones para Daily Planning System
translations = {
    "Daily Planning": "Planificación Diaria",
    "Daily Planning Dashboard": "Panel de Planificación Diaria",
    "Manage daily work plans for all projects": "Gestionar planes de trabajo diarios para todos los proyectos",
    "Overdue Plans!": "¡Planes Vencidos!",
    "The following plans are past their 5pm deadline:": "Los siguientes planes pasaron su plazo de 5pm:",
    "Complete Now": "Completar Ahora",
    "Create New Daily Plan": "Crear Nuevo Plan Diario",
    "Select Project": "Seleccionar Proyecto",
    "Choose Project": "Elegir Proyecto",
    "Plan Date": "Fecha del Plan",
    "Create Plan": "Crear Plan",
    "Today's Plans": "Planes de Hoy",
    "Status": "Estado",
    "Activities": "Actividades",
    "Created By": "Creado Por",
    "Actions": "Acciones",
    "activities": "actividades",
    "Edit": "Editar",
    "No plans for today yet.": "No hay planes para hoy todavía.",
    "Recent Plans": "Planes Recientes",
    "Date": "Fecha",
    "Project": "Proyecto",
    "Created": "Creado",
    "View/Edit": "Ver/Editar",
    "No plans created yet.": "No hay planes creados todavía.",
    "Quick Links": "Enlaces Rápidos",
    "SOP Library": "Biblioteca de SOPs",
    "Employee View": "Vista de Empleado",
    "Edit Daily Plan": "Editar Plan Diario",
    "Back to Planning Dashboard": "Volver al Panel de Planificación",
    "Project:": "Proyecto:",
    "Date:": "Fecha:",
    "Status:": "Estado:",
    "Draft": "Borrador",
    "Submitted": "Enviado",
    "Approved": "Aprobado",
    "Skipped": "Omitido",
    "This plan is overdue! Deadline was:": "¡Este plan está vencido! La fecha límite era:",
    "Add Activity": "Agregar Actividad",
    "Assigned:": "Asignados:",
    "No one assigned yet": "Nadie asignado todavía",
    "Materials:": "Materiales:",
    "Shortage!": "¡Escasez!",
    "complete": "completo",
    "Delete this activity?": "¿Eliminar esta actividad?",
    "No activities added yet. Click 'Add Activity' to start.": "No se han agregado actividades. Haz clic en 'Agregar Actividad' para empezar.",
    "Submit Plan": "Enviar Plan",
    "Add at least one activity before submitting": "Agrega al menos una actividad antes de enviar",
    "Back to Dashboard": "Volver al Panel",
    "Browse SOPs": "Explorar SOPs",
    "View Project": "Ver Proyecto",
    "Plan Info": "Información del Plan",
    "Created by:": "Creado por:",
    "Created:": "Creado:",
    "Deadline:": "Fecha límite:",
    "Approved by:": "Aprobado por:",
    "Approved:": "Aprobado:",
    "Activity Template (SOP)": "Plantilla de Actividad (SOP)",
    "(optional)": "(opcional)",
    "Select SOP template": "Seleccionar plantilla SOP",
    "Link to Schedule Item": "Vincular a Item de Calendario",
    "Not linked to schedule": "No vinculado al calendario",
    "Activity Title": "Título de Actividad",
    "Description": "Descripción",
    "Estimated Hours": "Horas Estimadas",
    "Assign Employees": "Asignar Empleados",
    "Hold Ctrl/Cmd to select multiple employees": "Mantén Ctrl/Cmd para seleccionar múltiples empleados",
    "Cancel": "Cancelar",
    "Good Morning": "Buenos Días",
    "Your work plan for": "Tu plan de trabajo para",
    "SOP": "SOP",
    "Steps to follow:": "Pasos a seguir:",
    "Tips:": "Consejos:",
    "Estimated time:": "Tiempo estimado:",
    "hours": "horas",
    "Team assigned": "Equipo asignado",
    "Materials needed": "Materiales necesarios",
    "Warning: Material shortage detected. Contact your supervisor.": "Advertencia: Escasez de materiales detectada. Contacta a tu supervisor.",
    "Progress": "Progreso",
    "Mark as Complete": "Marcar como Completo",
    "Activity completed!": "¡Actividad completada!",
    "No activities assigned for today": "No hay actividades asignadas para hoy",
    "Enjoy your day off or check with your supervisor!": "¡Disfruta tu día libre o consulta con tu supervisor!",
    "Complete Activity": "Completar Actividad",
    "Progress Percentage": "Porcentaje de Progreso",
    "Select the completion percentage for this activity": "Selecciona el porcentaje de completado para esta actividad",
    "Upload Photos": "Subir Fotos",
    "Upload photos showing the completed work. You can select multiple files.": "Sube fotos mostrando el trabajo completado. Puedes seleccionar múltiples archivos.",
    "Internal Notes": "Notas Internas",
    "Optional - Not shown to client": "Opcional - No se muestra al cliente",
    "Add any notes about this activity (in Spanish, for internal use only)": "Agrega notas sobre esta actividad (en español, solo para uso interno)",
    "These notes are for internal use only and will not be shown to the client": "Estas notas son solo para uso interno y no se mostrarán al cliente",
    "Checklist": "Lista de Verificación",
    "Verify that all steps have been completed before submitting": "Verifica que todos los pasos se hayan completado antes de enviar",
    "Important Information": "Información Importante",
    "Photos help document the quality of work for the client": "Las fotos ayudan a documentar la calidad del trabajo para el cliente",
    "Internal notes can include issues encountered, materials used, or time taken": "Las notas internas pueden incluir problemas encontrados, materiales usados o tiempo tomado",
    "If you can't complete 100%, indicate the percentage achieved": "Si no puedes completar el 100%, indica el porcentaje alcanzado",
    "Contact your supervisor if you encounter any problems": "Contacta a tu supervisor si encuentras algún problema",
    "Browse Standard Operating Procedures and Activity Templates": "Explorar Procedimientos Operativos Estándar y Plantillas de Actividad",
    "Category": "Categoría",
    "All Categories": "Todas las Categorías",
    "Search": "Buscar",
    "Search by name, description, or tips...": "Buscar por nombre, descripción o consejos...",
    "Show/Hide Steps": "Mostrar/Ocultar Pasos",
    "Steps": "Pasos",
    "Materials": "Materiales",
    "Show/Hide Materials": "Mostrar/Ocultar Materiales",
    "Tools": "Herramientas",
    "Show/Hide Tools": "Mostrar/Ocultar Herramientas",
    "Common Errors:": "Errores Comunes:",
    "Watch Video Tutorial": "Ver Tutorial en Video",
    "No SOPs found": "No se encontraron SOPs",
    "Try adjusting your search filters": "Intenta ajustar tus filtros de búsqueda",
    "No SOPs have been created yet. Contact your administrator to create activity templates.": "No se han creado SOPs todavía. Contacta a tu administrador para crear plantillas de actividades.",
    "My Daily Plan": "Mi Plan Diario",
}

# Leer archivo
with open('locale/es/LC_MESSAGES/django.po', 'r', encoding='utf-8') as f:
    content = f.read()

# Aplicar traducciones
for english, spanish in translations.items():
    # Escapar caracteres especiales para regex
    english_escaped = re.escape(english)
    
    # Buscar el patrón msgid "..." msgstr ""
    pattern = f'msgid "{english_escaped}"\\nmsgstr ""'
    replacement = f'msgid "{english}"\\nmsgstr "{spanish}"'
    
    content = re.sub(pattern, replacement, content)

# Guardar archivo
with open('locale/es/LC_MESSAGES/django.po', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Traducciones en español agregadas exitosamente!")
print(f"   Total de traducciones aplicadas: {len(translations)}")
