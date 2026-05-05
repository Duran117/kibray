"""
Phase 9 — Translate all remaining Spanish user-facing messages to English.

Strategy: scan every .py file for `messages.error/success/warning/info(...)`
calls whose source string is in Spanish (either bare "..." or _( "..." )).
Replace using a curated phrase-translation map. Source language stays English;
the existing locale .po files still translate EN→ES at runtime when LANG=es.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Spanish source string  →  English replacement
TRANSLATIONS: dict[str, str] = {
    # Permissions / access
    "No tienes permiso para acceder a esta función.":
        "You don't have permission to access this feature.",
    "No tienes permiso para acceder a Analytics.":
        "You don't have permission to access Analytics.",
    "No tienes permisos para esta acción.":
        "You don't have permission for this action.",
    "No tienes permisos para acceder a esta página.":
        "You don't have permission to access this page.",
    "No tienes permisos para activar proyectos":
        "You don't have permission to activate projects",
    "No tienes permisos para editar este presupuesto.":
        "You don't have permission to edit this budget.",
    "No tienes permisos para crear minutas.":
        "You don't have permission to create meeting minutes.",
    "No tienes permisos para ver esta minuta.":
        "You don't have permission to view these meeting minutes.",
    "No tienes permisos para editar minutas.":
        "You don't have permission to edit meeting minutes.",
    "No tienes permisos para eliminar minutas.":
        "You don't have permission to delete meeting minutes.",
    "No tienes permisos.":
        "You don't have permission.",
    "No tienes permisos para eliminar este comentario.":
        "You don't have permission to delete this comment.",
    "No tienes permiso para gestionar touch-ups":
        "You don't have permission to manage touch-ups",
    "No tienes permiso para ver touch-ups":
        "You don't have permission to view touch-ups",
    "No tienes permisos para agregar progreso.":
        "You don't have permission to add progress.",
    "No tienes permisos para importar progreso.":
        "You don't have permission to import progress.",
    "No tienes permisos para borrar progreso.":
        "You don't have permission to delete progress.",
    "No tienes permisos para exportar progreso.":
        "You don't have permission to export progress.",
    "No tienes permiso para ver Daily Logs":
        "You don't have permission to view Daily Logs",
    "No tienes permiso para enviar esta solicitud":
        "You don't have permission to submit this request",
    "No tienes acceso a este canal.":
        "You don't have access to this channel.",
    "No tienes acceso a este proyecto.":
        "You don't have access to this project.",
    # Role-restricted
    "Solo PM o admin pueden crear asignaciones.":
        "Only PM or admin can create assignments.",
    "Solo PM o admin pueden editar asignaciones.":
        "Only PM or admin can edit assignments.",
    "Solo PM o admin pueden eliminar asignaciones.":
        "Only PM or admin can delete assignments.",
    "Solo PM o admin pueden corregir horas.":
        "Only PM or admin can correct hours.",
    "Solo Admin puede asignar diseñadores.":
        "Only Admin can assign designers.",
    "Solo staff puede editar tareas.":
        "Only staff can edit tasks.",
    "Solo staff puede eliminar tareas.":
        "Only staff can delete tasks.",
    "Acceso solo para PM/Staff.":
        "Access restricted to PM/Staff.",
    "Acceso solo para Admin/Staff.":
        "Access restricted to Admin/Staff.",
    "Vista solo disponible para Project Managers":
        "View only available for Project Managers",
    # Validations
    "Debes seleccionar un cost code.":
        "You must select a cost code.",
    "Debes agregar texto o imagen.":
        "You must add text or an image.",
    "Debes especificar el monto total":
        "You must specify the total amount",
    "Título es requerido":
        "Title is required",
    "Título y fecha son requeridos.":
        "Title and date are required.",
    "Monto y fecha de pago son requeridos.":
        "Amount and payment date are required.",
    "Cantidad y razón son requeridos":
        "Quantity and reason are required",
    "Monto inválido":
        "Invalid amount",
    "El nombre del canal es requerido.":
        "Channel name is required.",
    "Selecciona al menos un ítem con cantidad > 0.":
        "Select at least one item with quantity greater than 0.",
    "Completa tienda y total o marca 'Sin gasto'.":
        "Complete store and total, or check 'No expense'.",
    "Para crear CO, selecciona filas de un solo proyecto.":
        "To create a CO, select rows from a single project.",
    "Selecciona entradas y un proyecto.":
        "Select entries and a project.",
    "Error al crear ítem. Verifica los campos.":
        "Failed to create item. Check the fields.",
    "No hay estimado aprobado para este proyecto":
        "No approved estimate for this project",
    "Este Daily Log no está disponible":
        "This Daily Log is not available",
    "La solicitud no está en estado borrador":
        "Request is not in draft status",
    # Success messages
    "Horas registradas correctamente.":
        "Hours recorded successfully.",
    "Horas registradas.":
        "Hours recorded.",
    "Ingreso actualizado.":
        "Income updated.",
    "Ingreso eliminado.":
        "Income deleted.",
    "Gasto actualizado.":
        "Expense updated.",
    "Gasto eliminado.":
        "Expense deleted.",
    "Registro de horas actualizado.":
        "Time entry updated.",
    "Registro de horas eliminado.":
        "Time entry deleted.",
    "Propuesta enviada correctamente al cliente.":
        "Proposal sent successfully to the client.",
    "RFI actualizado.":
        "RFI updated.",
    "RFI eliminado.":
        "RFI deleted.",
    "Issue actualizado.":
        "Issue updated.",
    "Issue eliminado.":
        "Issue deleted.",
    "Risk actualizado.":
        "Risk updated.",
    "Risk eliminado.":
        "Risk deleted.",
    "Reporte actualizado.":
        "Report updated.",
    "Reporte de daño eliminado.":
        "Damage report deleted.",
    "Plan actualizado":
        "Plan updated",
    "Transición de estado exitosa":
        "Status transition successful",
    "✨ SOP creado exitosamente!":
        "✨ SOP created successfully!",
    "Plano actualizado.":
        "Floor plan updated.",
    "Plano eliminado.":
        "Floor plan deleted.",
    "Comentario agregado exitosamente.":
        "Comment added successfully.",
    "Comentario eliminado.":
        "Comment deleted.",
    "Minuta creada exitosamente.":
        "Meeting minutes created successfully.",
    "Minuta actualizada exitosamente.":
        "Meeting minutes updated successfully.",
    "Minuta eliminada exitosamente.":
        "Meeting minutes deleted successfully.",
    "Touch-up actualizado":
        "Touch-up updated",
    "Pin actualizado exitosamente":
        "Pin updated successfully",
    "Progreso eliminado.":
        "Progress deleted.",
    "Progreso actualizado.":
        "Progress updated.",
    "Información del cliente actualizada exitosamente.":
        "Client information updated successfully.",
    "Daily Log creado para %(date)s":
        "Daily Log created for %(date)s",
    "Nómina actualizada correctamente.":
        "Payroll updated successfully.",
    "Solicitud enviada para aprobación":
        "Request submitted for approval",
    "Solicitud #%(id)s aprobada":
        "Request #%(id)s approved",
    "Solicitud #%(id)s rechazada":
        "Request #%(id)s rejected",
    # JsonResponse / ValidationError / HttpResponseForbidden
    "Permiso denegado": "Permission denied",
    "Sin permiso": "Permission denied",
    "Sin permisos": "Permission denied",
    "No tienes permiso": "You don't have permission",
    "No tienes acceso": "You don't have access",
    "No tienes acceso a este proyecto": "You don't have access to this project",
    "No tienes acceso a este archivo": "You don't have access to this file",
    "No tienes permiso para subir archivos": "You don't have permission to upload files",
    "No tienes permiso para descargar este archivo":
        "You don't have permission to download this file",
    "No tienes permiso para iniciar workflows":
        "You don't have permission to start workflows",
    "No tienes permisos para ver este cronograma.":
        "You don't have permission to view this schedule.",
    "Estado inválido": "Invalid status",
    "JSON inválido": "Invalid JSON",
    "Formulario inválido": "Invalid form",
    "Formato de correo electrónico inválido.":
        "Invalid email format.",
    "Percent complete inválido.": "Invalid percent complete.",
    "status inválido": "invalid status",
    "Tipo de dependencia inválido": "Invalid dependency type",
    "Debes seleccionar un proyecto para marcar entrada":
        "You must select a project to clock in",
    "Debes seleccionar un proyecto antes de marcar entrada":
        "You must select a project before clocking in",
    "El CO seleccionado no pertenece al proyecto elegido.":
        "The selected CO does not belong to the chosen project.",
    "La fase seleccionada no pertenece al proyecto elegido.":
        "The selected phase does not belong to the chosen project.",
    "Para crear tareas operativas, primero debes crear el cronograma":
        "You must create the schedule before adding operational tasks",
    "Debes subir al menos una foto":
        "You must upload at least one photo",
    "Touch-up aprobado exitosamente":
        "Touch-up approved successfully",
    # f-string day-unblock message — keep variable
    "Día {date_str} desbloqueado correctamente":
        "Day {date_str} unblocked successfully",
    # Round 3
    "Asignación actualizada.": "Assignment updated.",
    "Asignación eliminada.": "Assignment deleted.",
    "Acción no reconocida.": "Unknown action.",
    "✓ Línea actualizada.": "✓ Line updated.",
    "Línea no encontrada.": "Line not found.",
    "No se crearon líneas (ya existen en el presupuesto).":
        "No lines were created (they already exist in the budget).",
    "Todas las notificaciones marcadas como leídas.":
        "All notifications marked as read.",
    "Error de validación: %(error)s":
        "Validation error: %(error)s",
    "Coordenadas inválidas.": "Invalid coordinates.",
    "Error al crear categoría": "Failed to create category",
    "El comentario no puede estar vacío.":
        "Comment cannot be empty.",
    "Transición inválida": "Invalid transition",
    "Error aplicando transición de estado":
        "Error applying state transition",
    "Tu usuario no está vinculado a un empleado.":
        "Your user is not linked to an employee.",
    "El cliente no tenía acceso a ese proyecto.":
        "The client did not have access to that project.",
    "Agrega al menos un ítem con cantidad > 0.":
        "Add at least one item with quantity greater than 0.",
    "La solicitud no está pendiente de aprobación":
        "Request is not pending approval",
    "Cantidad inválida: %(error)s":
        "Invalid quantity: %(error)s",
    # f-string fragments — replace just the Spanish words/phrases
    "✓ Línea '": "✓ Line '",
    "' agregada al presupuesto.": "' added to budget.",
    "Error al agregar línea: ": "Failed to add line: ",
    "' eliminada.": "' deleted.",
    " líneas creadas desde template '": " lines created from template '",
    'Categoría "': 'Category "',
    '" creada': '" created',
    'Ítem "': 'Item "',
    '" creado.': '" created.',
    '" actualizado.': '" updated.',
    '" eliminado.': '" deleted.',
    'Organización "': 'Organization "',
    '" creada exitosamente.': '" created successfully.',
    '" actualizada exitosamente.': '" updated successfully.',
    '" desactivada exitosamente.': '" deactivated successfully.',
    '" eliminada permanentemente.': '" permanently deleted.',

    # ===== Round 4: forms.py labels / placeholders / help_text =====
    "Descripción del gasto...": "Expense description...",
    "Descripción de la foto...": "Photo description...",
    "Descripción de la foto": "Photo description",
    "Descripción": "Description",
    "Descripción (opcional)": "Description (optional)",
    "Descripción del proyecto": "Project description",
    "Descripción de esta categoría...": "Description of this category...",
    "Descripción opcional...": "Optional description...",
    "Descripción detallada del touch-up...": "Detailed description of the touch-up...",
    "Ej: Grieta en pared del baño principal":
        "E.g.: Crack in main bathroom wall",
    "Describe el daño con el mayor detalle posible...":
        "Describe the damage in as much detail as possible...",
    "Causa raíz (opcional)": "Root cause (optional)",
    "Tipo de daño reportado": "Type of damage reported",
    "Nivel de urgencia del daño": "Damage urgency level",
    "Costo estimado de reparación (opcional)":
        "Estimated repair cost (optional)",
    "Plano donde se encuentra el daño (opcional)":
        "Plan where the damage is located (optional)",
    "Pin específico si aplica (opcional)":
        "Specific pin if applicable (optional)",
    "Fecha límite opcional": "Optional deadline",
    "Porcentaje de contribución al item del Gantt":
        "Percent contribution to the Gantt item",
    "Título": "Title",
    "Material del catálogo": "Catalog material",
    "Categoría": "Category",
    "Producto / Línea": "Product / Line",
    "Código": "Code",
    "Fórmula (si aplica)": "Formula (if applicable)",
    "Cuándo se ocupa": "When needed",
    "Guardar este material en el catálogo del proyecto":
        "Save this material to the project catalog",
    "Elige una opción: agregar gasto o marcar sin gasto, no ambas.":
        "Choose one option: add expense or mark as no expense, not both.",
    "Ej: Planta Baja, Primer Piso, Ático...":
        "E.g.: Ground Floor, First Floor, Attic...",
    "Número del nivel: 0=Planta Baja, 1=Nivel 1, -1=Sótano 1, etc.":
        "Level number: 0=Ground Floor, 1=Level 1, -1=Basement 1, etc.",
    "Ej: Preparación": "E.g.: Preparation",
    "Horas reales del día (se puede llenar al finalizar).":
        "Actual hours for the day (can be filled out when finishing).",
    "Deadline debe ser antes del día planificado.":
        "Deadline must be before the planned day.",
    "Debes indicar motivo si el día se omite.":
        "You must provide a reason if the day is skipped.",
    "Una línea por material. Formato opcional cantidad al final (ej: Paint:Brand:2gal).":
        "One line per material. Optional quantity at the end (e.g.: Paint:Brand:2gal).",
    "Descripción de esta categoría...":
        "Description of this category...",
    "Notas sobre la finalización del trabajo (opcional)...":
        "Notes about the work completion (optional)...",
    "Notas de Finalización": "Completion Notes",
    "Fotos de Finalización": "Completion Photos",
    "Correo Electrónico": "Email",
    "Teléfono": "Phone",
    "Organización (Compañía)": "Organization (Company)",
    "Selecciona una organización existente o deja vacío para cliente individual":
        "Select an existing organization or leave empty for an individual client",
    "Selecciona una organización o deja vacío para cliente individual":
        "Select an organization or leave empty for an individual client",
    "-- Cliente Individual (Sin organización) --":
        "-- Individual Client (No organization) --",
    "Rol en la Organización": "Role in the Organization",
    "Cargo/Título": "Job Title",
    "El correo electrónico es obligatorio.": "Email is required.",
    "Ya existe un usuario con este correo electrónico.":
        "A user with this email already exists.",
    "No se permiten correos electrónicos desechables.":
        "Disposable email addresses are not allowed.",
    "Dirección completa": "Full address",
    "Dirección": "Address",
    "Nueva contraseña": "New password",
    "Nueva Contraseña": "New Password",
    "Confirmar contraseña": "Confirm password",
    "Confirmar Contraseña": "Confirm Password",
    "Las contraseñas no coinciden.": "Passwords do not match.",
    "Nombre de la compañía": "Company name",
    "Dirección de facturación": "Billing address",
    "Código postal": "ZIP code",
    "Nombre de la Compañía": "Company Name",
    "Dirección de Facturación": "Billing Address",
    "Código Postal": "ZIP Code",
    "Email de Facturación": "Billing Email",
    "Términos de Pago (días)": "Payment Terms (days)",
    "Organización Activa": "Active Organization",
    "El nombre de la compañía es obligatorio.":
        "Company name is required.",
    "Organización de Facturación": "Billing Organization",
    "Selecciona la empresa cliente para facturación":
        "Select the client company for billing",
    "-- Sin organización (cliente individual) --":
        "-- No organization (individual client) --",
    "Dirección completa del proyecto": "Full project address",
    "Códigos de pintura específicos": "Specific paint codes",
    "La fecha de finalización no puede ser anterior a la fecha de inicio.":
        "End date cannot be earlier than start date.",
    "Notas sobre aprendizajes, errores o mejoras para próximos proyectos":
        "Notes on learnings, mistakes or improvements for upcoming projects",
    "El mensaje no puede estar vacío.": "Message cannot be empty.",
    "Líneas del estimado a incluir en cronograma":
        "Estimate lines to include in the schedule",
    "Deja vacío para incluir todas las líneas":
        "Leave empty to include all lines",
    "Debes seleccionar al menos una acción (cronograma, presupuesto o anticipo)":
        "You must select at least one action (schedule, budget or deposit)",

    # ===== Round 4: notifications_push.py =====
    "💵 Nómina Disponible": "💵 Payroll Available",

    # ===== Round 4: api / sop_api.py =====
    "La descripción de la tarea es requerida":
        "Task description is required",
    "¡SOP creado exitosamente!": "SOP created successfully!",
    "Proyecto sin ubicación de inventario":
        "Project has no inventory location",
    "Cantidad inválida": "Invalid quantity",

    # ===== Round 4: views/financial_views.py =====
    "⚠️ No se puede cancelar una factura que ya está PAGADA.":
        "⚠️ Cannot cancel an invoice that is already PAID.",
    "La factura ya está cancelada.": "The invoice is already cancelled.",
    "Adjunto encontrarás la cotización detallada para tu revisión.\n\n":
        "Attached you will find the detailed quote for your review.\n\n",

    # ===== Round 4: views/contract_views.py =====
    "Propuesta no encontrada o enlace inválido.":
        "Proposal not found or invalid link.",

    # ===== Round 4: views/daily_plan_views.py =====
    "No se pudo obtener el clima. Verifique la ubicación del proyecto.":
        "Could not retrieve weather. Please verify the project location.",

    # ===== Round 4: views/file_views.py =====
    "El archivo no está disponible. Por favor contacte al administrador.":
        "The file is not available. Please contact the administrator.",

    # ===== Round 4: views/dashboard_designer_views.py =====
    "Acceso restringido a diseñadores": "Access restricted to designers",

    # ===== Round 4: views/materials_views.py =====
    "Solicitud registrada. El material quedó guardado en el catálogo del proyecto.":
        "Request submitted. Material has been saved in the project catalog.",
    "Ticket procesado. %(count)s ítem(s) recibido(s).":
        "Ticket processed. %(count)s item(s) received.",
    "Compra directa registrada. %(count)s ítem(s) agregado(s) al inventario.":
        "Direct purchase recorded. %(count)s item(s) added to inventory.",

    # ===== Round 4: views/client_mgmt_views.py =====
    "Contraseña actualizada y email enviado a %(email)s":
        "Password updated and email sent to %(email)s",
    "Contraseña actualizada pero hubo un error al enviar el email.":
        "Password updated but there was an error sending the email.",
    "Contraseña actualizada pero hubo un error al enviar el email: %(error)s":
        "Password updated but there was an error sending the email: %(error)s",

    # ===== Round 4: views/project_progress_views.py =====
    "El archivo es demasiado grande (máx. 2 MB).":
        "File is too large (max 2 MB).",

    # ===== Round 4: forms.py wider sweep =====
    "Transición inválida desde ": "Invalid transition from ",
}


def translate_file(path: Path) -> int:
    """Apply translations in-place. Returns number of substitutions made."""
    text = path.read_text(encoding="utf-8")
    original = text
    n = 0
    for es, en in TRANSLATIONS.items():
        # f-string fragments contain `{` or `"` already and need a raw replace
        if "{" in es or es.startswith('"') or es.endswith('"') or es.startswith("'"):
            if es in text:
                count = text.count(es)
                text = text.replace(es, en)
                n += count
            continue
        # Match the Spanish string inside any quote style: "...", '...'
        for q in ('"', "'"):
            needle = f"{q}{es}{q}"
            if needle in text:
                count = text.count(needle)
                text = text.replace(needle, f"{q}{en}{q}")
                n += count
    if text != original:
        path.write_text(text, encoding="utf-8")
    return n


def main() -> int:
    targets = [
        ROOT / "core",
        ROOT / "kibray_backend",
    ]
    total = 0
    files_changed = 0
    for base in targets:
        for p in base.rglob("*.py"):
            if "/migrations/" in str(p) or "/.venv/" in str(p):
                continue
            n = translate_file(p)
            if n:
                total += n
                files_changed += 1
                print(f"  {p.relative_to(ROOT)}: {n} replacements")
    print(f"\nTotal: {total} substitutions in {files_changed} files.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
