"""Touchup board & plans (legacy) — CRUD, pins."""
from core.views._helpers import *  # noqa: F401, F403
from core.views._helpers import (
    _generate_basic_pdf_from_html,
    _check_user_project_access,
    _is_admin_user,
    _is_pm_or_admin,
    _is_staffish,
    _require_admin_or_redirect,
    _require_roles,
    _parse_date,
    _ensure_inventory_item,
    staff_required,
    logger,
    pisa,
    ROLES_ADMIN,
    ROLES_PM,
    ROLES_STAFF,
    ROLES_FIELD,
    ROLES_ALL_INTERNAL,
    ROLES_CLIENT_SIDE,
    ROLES_PROJECT_ACCESS,
)
from django.utils.translation import gettext_lazy as _  # noqa: F811


@login_required
def touchup_board(request, project_id):
    """Vista dedicada para gestionar touch-ups del proyecto (Q11.2 con mejoras)."""
    from django.core.paginator import Paginator

    project = get_object_or_404(Project, id=project_id)
    
    # SECURITY: Check project access
    has_access, redirect_url = _check_user_project_access(request.user, project)
    if not has_access:
        messages.error(request, _("You don't have access to this project."))
        return redirect(redirect_url)
    
    qs = (
        project.tasks.filter(is_touchup=True)
        .select_related("assigned_to", "created_by")
        .order_by("-created_at")
    )

    # Filters
    status = request.GET.get("status")
    if status:
        qs = qs.filter(status=status)

    # ACTIVITY 1: Priority filter (Q11.6)
    priority = request.GET.get("priority")
    if priority:
        qs = qs.filter(priority=priority)

    assigned = request.GET.get("assigned")
    if assigned == "unassigned":
        qs = qs.filter(assigned_to__isnull=True)
    elif assigned:
        qs = qs.filter(assigned_to__id=assigned)

    date_from = request.GET.get("date_from")
    if date_from:
        qs = qs.filter(created_at__date__gte=date_from)

    date_to = request.GET.get("date_to")
    if date_to:
        qs = qs.filter(created_at__date__lte=date_to)

    # ACTIVITY 1: Filter by due date (Q11.1 - overdue tasks)
    show_overdue = request.GET.get("overdue")
    if show_overdue:
        from django.utils import timezone

        qs = qs.filter(due_date__lt=timezone.now().date(), status__in=["pending", "in_progress"])

    # Sorting (updated with new fields)
    sort_by = request.GET.get("sort", "-created_at")
    valid_sorts = [
        "created_at",
        "-created_at",
        "status",
        "-status",
        "assigned_to",
        "-assigned_to",
        "priority",
        "-priority",  # Q11.6
        "due_date",
        "-due_date",  # Q11.1
    ]
    if sort_by in valid_sorts:
        qs = qs.order_by(sort_by)

    # Pagination
    paginator = Paginator(qs, 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # Get available employees for filter dropdown
    employees = Employee.objects.filter(is_active=True).order_by("first_name", "last_name")

    # ACTIVITY 1: Priority choices for filter dropdown
    from core.models import Task

    priority_choices = Task.PRIORITY_CHOICES

    return render(
        request,
        "core/touchup_board.html",
        {
            "project": project,
            "page_obj": page_obj,
            "filter_status": status,
            "filter_priority": priority,
            "filter_assigned": assigned,
            "filter_date_from": date_from,
            "filter_date_to": date_to,
            "show_overdue": show_overdue,
            "sort_by": sort_by,
            "employees": employees,
            "priority_choices": priority_choices,
        },
    )



@login_required
def touchup_quick_update(request, task_id):
    """AJAX endpoint for quick status/assignment updates on touch-up board."""
    if request.method != "POST":
        return JsonResponse({"error": gettext("POST required")}, status=405)

    task = get_object_or_404(Task, id=task_id, is_touchup=True)

    # Check permission: staff, assigned employee, or project client
    employee = Employee.objects.filter(user=request.user).first()
    is_assigned = employee and task.assigned_to == employee
    if not (request.user.is_staff or is_assigned or task.project.client == request.user.username):
        return JsonResponse({"error": gettext("Sin permiso")}, status=403)

    action = request.POST.get("action")

    if action == "status":
        new_status = request.POST.get("status")
        if new_status in dict(Task.STATUS_CHOICES):
            task.status = new_status
            if new_status == "Completed":
                task.completed_at = timezone.now()
            task.save()
            return JsonResponse({"success": True, "status": task.get_status_display()})

    elif action == "assign":
        employee_id = request.POST.get("employee_id")
        if employee_id:
            employee = get_object_or_404(User, id=employee_id)
            task.assigned_to = employee
            task.save()
            return JsonResponse({"success": True, "assigned_to": employee.username})
        else:
            task.assigned_to = None
            task.save()
            return JsonResponse({"success": True, "assigned_to": "Sin asignar"})

    return JsonResponse({"error": gettext("Acción inválida")}, status=400)



@login_required
def touchup_plans_list(request, project_id):
    """List all floor plans with active touch-ups"""
    from core.models import FloorPlan

    project = get_object_or_404(Project, id=project_id)
    profile = getattr(request.user, "profile", None)

    # Permission check: PM, Admin, Client, Designer, Owner
    if not request.user.is_staff and (
        not profile
        or profile.role
        not in ["project_manager", "admin", "superuser", "client", "designer", "owner"]
    ):
        messages.error(request, "No tienes permiso para gestionar touch-ups")
        return redirect("project_overview", project_id)

    # Get plans with active touch-ups
    plans = FloorPlan.objects.filter(project=project).prefetch_related("touchup_pins")

    # Annotate with active touchup count
    from django.db.models import Count, Q

    plans = plans.annotate(
        active_touchups=Count(
            "touchup_pins", filter=Q(touchup_pins__status__in=["pending", "in_progress"])
        )
    )

    context = {"project": project, "plans": plans, "page_title": "Planos Touch-up"}
    return render(request, "core/touchup_plans_list.html", context)



@login_required
def touchup_plan_detail(request, plan_id):
    """View a single floor plan with its touch-ups"""
    from core.models import FloorPlan, TouchUpPin

    plan = get_object_or_404(FloorPlan, id=plan_id)
    project = plan.project
    profile = getattr(request.user, "profile", None)

    # Permission check
    allowed_roles = [
        "project_manager",
        "admin",
        "superuser",
        "employee",
        "painter",
        "client",
        "designer",
        "owner",
    ]
    if not request.user.is_staff and (not profile or profile.role not in allowed_roles):
        messages.error(request, "No tienes permiso para ver touch-ups")
        return redirect("project_overview", project.id)

    # Get touchups - filter by assigned user if employee
    touchups = TouchUpPin.objects.filter(plan=plan)
    if profile and profile.role in ["employee", "painter"] and not request.user.is_staff:
        touchups = touchups.filter(assigned_to=request.user)

    touchups = touchups.select_related("assigned_to", "created_by", "approved_color", "closed_by")

    # Can create: authorized roles
    can_create = request.user.is_staff or (
        profile and profile.role in ROLES_PROJECT_ACCESS
    )

    context = {
        "project": project,
        "plan": plan,
        "touchups": touchups,
        "can_create": can_create,
        "page_title": f"Touch-ups - {plan.name}",
    }
    return render(request, "core/touchup_plan_detail.html", context)



@login_required
def touchup_create(request, plan_id):
    """Create a new touch-up pin"""
    from core.forms import TouchUpPinForm
    from core.models import FloorPlan

    plan = get_object_or_404(FloorPlan, id=plan_id)
    project = plan.project
    profile = getattr(request.user, "profile", None)

    # Permission check: PM, Admin, Client, Designer, Owner
    if not request.user.is_staff and (
        not profile
        or profile.role
        not in ["project_manager", "admin", "superuser", "client", "designer", "owner"]
    ):
        return JsonResponse({"error": gettext("No autorizado")}, status=403)

    if request.method == "POST":
        form = TouchUpPinForm(request.POST, project=project)
        if form.is_valid():
            touchup = form.save(commit=False)
            touchup.created_by = request.user
            touchup.save()

            messages.success(request, f'Touch-up "{touchup.task_name}" creado')
            return JsonResponse(
                {
                    "success": True,
                    "touchup_id": touchup.id,
                    "message": gettext("Touch-up creado exitosamente"),
                }
            )
        else:
            return JsonResponse({"error": "Formulario inválido", "errors": form.errors}, status=400)

    # GET - return form
    form = TouchUpPinForm(initial={"plan": plan}, project=project)
    return render(
        request, "core/touchup_create_form.html", {"form": form, "plan": plan, "project": project}
    )



@login_required
def touchup_detail_ajax(request, touchup_id):
    """Get touch-up details via AJAX"""
    from core.models import TouchUpPin

    touchup = get_object_or_404(TouchUpPin, id=touchup_id)
    profile = getattr(request.user, "profile", None)

    # Permission check
    can_view = (
        request.user.is_staff
        or (profile and profile.role in ROLES_STAFF)
        or touchup.assigned_to == request.user
    )

    if not can_view:
        return JsonResponse({"error": gettext("No autorizado")}, status=403)

    # Check if user can approve (PM/Admin)
    can_approve = request.user.is_staff or (
        profile and profile.role in ROLES_STAFF
    )

    data = {
        "id": touchup.id,
        "task_name": touchup.task_name,
        "description": touchup.description,
        "status": touchup.status,
        "status_display": touchup.get_status_display(),
        "created_at": touchup.created_at.isoformat(),
        "created_by": str(touchup.created_by) if touchup.created_by else None,
        "assigned_to": str(touchup.assigned_to) if touchup.assigned_to else "Sin asignar",
        "approved_color": touchup.approved_color.name if touchup.approved_color else None,
        "custom_color_name": touchup.custom_color_name,
        "sheen": touchup.sheen,
        "details": touchup.details,
        "can_edit": touchup.can_edit(request.user),
        "can_close": touchup.can_close(request.user),
        "can_approve": can_approve,
        "approval_status": touchup.approval_status,
        "approval_status_display": touchup.get_approval_status_display(),
        "rejection_reason": touchup.rejection_reason,
        "reviewed_by": str(touchup.reviewed_by) if touchup.reviewed_by else None,
        "reviewed_at": touchup.reviewed_at.isoformat() if touchup.reviewed_at else None,
        "completion_photos": [
            {
                "id": photo.id,
                "url": photo.image.url,
                "notes": photo.notes,
                "uploaded_at": photo.uploaded_at.isoformat(),
            }
            for photo in touchup.completion_photos.all()
        ],
    }

    return JsonResponse(data)



@login_required
def touchup_update(request, touchup_id):
    """Update a touch-up (PM/Admin only)"""
    from core.forms import TouchUpPinForm
    from core.models import TouchUpPin

    touchup = get_object_or_404(TouchUpPin, id=touchup_id)

    # Permission check
    if not touchup.can_edit(request.user):
        return JsonResponse({"error": gettext("No autorizado")}, status=403)

    if request.method == "POST":
        form = TouchUpPinForm(request.POST, instance=touchup, project=touchup.plan.project)
        if form.is_valid():
            form.save()
            messages.success(request, "Touch-up actualizado")
            return JsonResponse({"success": True, "message": gettext("Touch-up actualizado")})
        else:
            return JsonResponse({"error": "Formulario inválido", "errors": form.errors}, status=400)

    return JsonResponse({"error": gettext("Método no permitido")}, status=405)



@login_required
def touchup_complete(request, touchup_id):
    """Mark touch-up as completed with photos (Assigned employee or PM)"""
    import json

    from core.models import TouchUpCompletionPhoto, TouchUpPin

    touchup = get_object_or_404(TouchUpPin, id=touchup_id)

    # Permission check
    if not touchup.can_close(request.user):
        return JsonResponse(
            {"error": gettext("No autorizado para cerrar este touch-up")}, status=403
        )

    if request.method == "POST":
        notes = request.POST.get("notes", "")
        photos = request.FILES.getlist("photos")

        if not photos:
            return JsonResponse({"error": gettext("Debes subir al menos una foto")}, status=400)

        # Save completion photos with annotations
        for idx, photo in enumerate(photos):
            # Get annotations for this photo if provided
            annotations_key = f"annotations_{idx}"
            annotations_data = request.POST.get(annotations_key, "{}")

            # Parse annotations JSON
            try:
                annotations = json.loads(annotations_data) if annotations_data else {}
            except json.JSONDecodeError:
                annotations = {}

            TouchUpCompletionPhoto.objects.create(
                touchup=touchup,
                image=photo,
                notes=notes,
                annotations=annotations,
                uploaded_by=request.user,
            )

        # Mark as completed
        touchup.close_touchup(request.user)

        messages.success(request, f'Touch-up "{touchup.task_name}" completado')
        return JsonResponse(
            {"success": True, "message": gettext("Touch-up completado exitosamente")}
        )

    return JsonResponse({"error": gettext("Método no permitido")}, status=405)



@login_required
def touchup_delete(request, touchup_id):
    """Delete a touch-up (PM/Admin only)"""
    from core.models import TouchUpPin

    touchup = get_object_or_404(TouchUpPin, id=touchup_id)

    # Permission check
    if not touchup.can_edit(request.user):
        return JsonResponse({"error": gettext("No autorizado")}, status=403)

    if request.method == "POST":
        plan_id = touchup.plan.id
        task_name = touchup.task_name
        touchup.delete()

        messages.success(request, f'Touch-up "{task_name}" eliminado')
        return JsonResponse({"success": True, "redirect": f"/plans/{plan_id}/touchups/"})

    return JsonResponse({"error": gettext("Método no permitido")}, status=405)



@login_required
def touchup_approve(request, touchup_id):
    """Approve a completed touch-up (PM/Admin only)"""
    from django.utils import timezone

    from core.models import TouchUpPin

    touchup = get_object_or_404(TouchUpPin, id=touchup_id)

    # Permission check - only PM/Admin can approve
    if not touchup.can_edit(request.user):
        return JsonResponse({"error": gettext("No autorizado para aprobar")}, status=403)

    if request.method == "POST":
        touchup.approval_status = "approved"
        touchup.reviewed_by = request.user
        touchup.reviewed_at = timezone.now()
        touchup.save()

        messages.success(request, f'Touch-up "{touchup.task_name}" aprobado')
        return JsonResponse({"success": True, "message": gettext("Touch-up aprobado exitosamente")})

    return JsonResponse({"error": gettext("Método no permitido")}, status=405)



@login_required
def touchup_reject(request, touchup_id):
    """Reject a completed touch-up with reason (PM/Admin only)"""
    from django.utils import timezone

    from core.models import TouchUpPin

    touchup = get_object_or_404(TouchUpPin, id=touchup_id)

    # Permission check - only PM/Admin can reject
    if not touchup.can_edit(request.user):
        return JsonResponse({"error": gettext("No autorizado para rechazar")}, status=403)

    if request.method == "POST":
        reason = request.POST.get("reason", "")
        if not reason:
            return JsonResponse(
                {"error": gettext("Debes proporcionar un motivo de rechazo")}, status=400
            )

        touchup.approval_status = "rejected"
        touchup.rejection_reason = reason
        touchup.reviewed_by = request.user
        touchup.reviewed_at = timezone.now()
        touchup.status = "in_progress"  # Reabrir para que el empleado lo corrija
        touchup.save()

        messages.warning(request, f'Touch-up "{touchup.task_name}" rechazado')
        return JsonResponse(
            {"success": True, "message": gettext("Touch-up rechazado, el empleado debe corregirlo")}
        )

    return JsonResponse({"error": gettext("Método no permitido")}, status=405)



# ========================================================================================
# INFO PIN VIEWS (Different from Touch-up Pins)
# ========================================================================================


@login_required
def pin_info_ajax(request, pin_id):
    """Get info pin details via AJAX"""

    from core.models import PlanPin


    try:
        pin = get_object_or_404(PlanPin, id=pin_id)
        profile = getattr(request.user, "profile", None)

        # Anyone can view info pins
        can_edit = request.user.is_staff or (
            profile
            and profile.role
            in ["project_manager", "admin", "superuser", "client", "designer", "owner"]
        )

        data = {
            "id": pin.id,
            "title": pin.title or "",
            "description": pin.description or "",
            "pin_type": pin.pin_type,
            "pin_type_display": pin.get_pin_type_display(),
            "pin_color": pin.pin_color,
            "can_edit": can_edit,
            "color_sample": None,
            "linked_task": None,
            "attachments": [],
        }

        # Add color sample if exists
        try:
            if pin.color_sample:
                cs = pin.color_sample
                data["color_sample"] = {
                    "id": cs.id,
                    "name": cs.name or "",
                    "code": cs.code or "",
                    "brand": cs.brand or "",
                    "finish": cs.finish or "",
                    "gloss": cs.gloss or "",
                    "status": cs.status or "",
                    "status_display": cs.get_status_display(),
                    "notes": cs.notes or "",
                    "room_location": cs.room_location or "",
                    "sample_number": cs.sample_number or "",
                    "sample_image": cs.sample_image.url if cs.sample_image else None,
                    "reference_photo": cs.reference_photo.url if cs.reference_photo else None,
                }
        except Exception as e:
            logger.error(f"Error loading color sample for pin {pin_id}: {e}")

        # Add linked task if exists
        try:
            if pin.linked_task:
                data["linked_task"] = {
                    "id": pin.linked_task.id,
                    "title": pin.linked_task.title or "",
                    "status": pin.linked_task.status or "",
                }
        except Exception as e:
            logger.error(f"Error loading linked task for pin {pin_id}: {e}")

        # Add attachments (photos)
        try:
            data["attachments"] = [
                {
                    "id": att.id,
                    "image_url": att.image.url if att.image else "",
                    "has_annotations": bool(att.annotations),
                    "created_at": att.created_at.isoformat() if att.created_at else "",
                }
                for att in pin.attachments.all()
            ]
        except Exception as e:
            logger.error(f"Error loading attachments for pin {pin_id}: {e}")

        return JsonResponse(data)

    except Exception as e:
        logger.error(f"Error in pin_info_ajax for pin {pin_id}: {str(e)}", exc_info=True)
        return JsonResponse({"error": "Error loading pin information"}, status=500)



@login_required
def pin_update(request, pin_id):
    """Update info pin details"""
    from core.models import PlanPin

    pin = get_object_or_404(PlanPin, id=pin_id)
    profile = getattr(request.user, "profile", None)

    # Permission check
    can_edit = request.user.is_staff or (
        profile
        and profile.role in ROLES_PROJECT_ACCESS
    )

    if not can_edit:
        return JsonResponse({"error": gettext("No autorizado")}, status=403)

    if request.method == "POST":
        pin.title = request.POST.get("title", pin.title)
        pin.description = request.POST.get("description", pin.description)
        pin.pin_type = request.POST.get("pin_type", pin.pin_type)

        # Update color sample if provided
        color_sample_id = request.POST.get("color_sample_id")
        if color_sample_id:
            from core.models import ColorSample

            with contextlib.suppress(ColorSample.DoesNotExist):
                pin.color_sample = ColorSample.objects.get(id=color_sample_id)

        pin.save()

        messages.success(request, "Pin actualizado exitosamente")
        return JsonResponse({"success": True, "message": gettext("Pin actualizado")})

    return JsonResponse({"error": gettext("Método no permitido")}, status=405)



@login_required
def pin_add_photo(request, pin_id):
    """Add photo attachment to info pin"""
    import json

    from core.models import PlanPin, PlanPinAttachment

    pin = get_object_or_404(PlanPin, id=pin_id)
    profile = getattr(request.user, "profile", None)

    # Permission check
    can_edit = request.user.is_staff or (
        profile
        and profile.role in ROLES_PROJECT_ACCESS
    )

    if not can_edit:
        return JsonResponse({"error": gettext("No autorizado")}, status=403)

    if request.method == "POST":
        photos = request.FILES.getlist("photos")

        if not photos:
            return JsonResponse({"error": gettext("No se enviaron fotos")}, status=400)

        created_attachments = []
        for idx, photo in enumerate(photos):
            # Get annotations for this photo if provided
            annotations_key = f"annotations_{idx}"
            annotations_data = request.POST.get(annotations_key, "{}")

            # Parse annotations JSON
            try:
                annotations = json.loads(annotations_data) if annotations_data else {}
            except json.JSONDecodeError:
                annotations = {}

            attachment = PlanPinAttachment.objects.create(
                pin=pin, image=photo, annotations=annotations
            )
            created_attachments.append({"id": attachment.id, "url": attachment.image.url})

        messages.success(
            request, _("%(count)s foto(s) agregada(s) al pin") % {"count": len(photos)}
        )
        return JsonResponse(
            {
                "success": True,
                "message": "Fotos agregadas exitosamente",
                "attachments": created_attachments,
            }
        )

    return JsonResponse({"error": gettext("Método no permitido")}, status=405)



@login_required
def pin_delete_photo(request, attachment_id):
    """Delete photo attachment from info pin"""
    from core.models import PlanPinAttachment

    attachment = get_object_or_404(PlanPinAttachment, id=attachment_id)
    profile = getattr(request.user, "profile", None)

    # Permission check
    can_edit = request.user.is_staff or (
        profile
        and profile.role in ROLES_PROJECT_ACCESS
    )

    if not can_edit:
        return JsonResponse({"error": gettext("No autorizado")}, status=403)

    if request.method == "POST":
        # Delete file from storage
        if attachment.image:
            attachment.image.delete()

        attachment.delete()

        return JsonResponse({"success": True, "message": gettext("Foto eliminada")})

    return JsonResponse({"error": gettext("Método no permitido")}, status=405)


# --- TOUCHUP BOARD REACT ---
@login_required
def touchup_board_react(request, project_id):
    """
    TouchUp Board React view - serves React-based kanban board for touchups.
    """
    project = get_object_or_404(Project, id=project_id)

    return render(
        request,
        "core/touchup_board_react.html",
        {
            "project_id": project_id,
            "project": project,
        },
    )


