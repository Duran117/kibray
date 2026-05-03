"""Color sample, floor plan & pin views — extracted from legacy_views.py in Phase 8."""
from core.views._helpers import *  # noqa: F401, F403
from core.views._helpers import (
    _check_user_project_access,
    _is_admin_user,
    _is_staffish,
    _require_admin_or_redirect,
    logger,
)
from django.utils.translation import gettext_lazy as _  # noqa: F811


# --- COLOR SAMPLES ---
@login_required
def color_sample_list(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    
    # SECURITY: Check project access
    has_access, redirect_url = _check_user_project_access(request.user, project)
    if not has_access:
        messages.error(request, _("You don't have access to this project."))
        return redirect(redirect_url)
    
    samples = project.color_samples.select_related("created_by").all().order_by("-created_at")

    # Calculate status counts before filtering
    all_samples = project.color_samples.all()
    proposed_count = all_samples.filter(status="proposed").count()
    review_count = all_samples.filter(status="review").count()
    approved_count = all_samples.filter(status="approved").count()
    rejected_count = all_samples.filter(status="rejected").count()

    # Filters
    brand = request.GET.get("brand")
    if brand:
        samples = samples.filter(brand__icontains=brand)

    status = request.GET.get("status")
    if status:
        samples = samples.filter(status=status)

    return render(
        request,
        "core/color_sample_list.html",
        {
            "project": project,
            "samples": samples,
            "filter_brand": brand,
            "filter_status": status,
            "proposed_count": proposed_count,
            "review_count": review_count,
            "approved_count": approved_count,
            "rejected_count": rejected_count,
        },
    )


@login_required
def color_sample_create(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    
    # SECURITY: Check project access
    has_access, redirect_url = _check_user_project_access(request.user, project)
    if not has_access:
        messages.error(request, _("You don't have access to this project."))
        return redirect(redirect_url)

    if request.method == "POST":
        form = ColorSampleForm(request.POST, request.FILES)
        if form.is_valid():
            inst = form.save(commit=False)
            inst.project = project
            inst.created_by = request.user
            inst.save()
            messages.success(request, _("Color sample created."))
            return redirect("color_sample_list", project_id=project_id)
    else:
        form = ColorSampleForm(initial={"project": project})
    return render(
        request,
        "core/color_sample_form.html",
        {
            "form": form,
            "project": project,
        },
    )


@login_required
def color_sample_detail(request, sample_id):
    from core.models import ColorSample, ClientProjectAccess

    sample = get_object_or_404(ColorSample, id=sample_id)
    project = sample.project
    
    # SECURITY: Check project access for all users
    has_access, redirect_url = _check_user_project_access(request.user, project)
    if not has_access:
        messages.error(request, _("You don't have access to this project."))
        return redirect(redirect_url or "dashboard")
    
    # Additional check for clients: verify explicit project access
    profile = getattr(request.user, "profile", None)
    if profile and profile.role == "client":
        has_access = ClientProjectAccess.objects.filter(
            user=request.user, project=project
        ).exists() or project.client == request.user.username
        if not has_access:
            messages.error(request, _("You don't have access to this project."))
            return redirect("dashboard_client")
    
    return render(
        request,
        "core/color_sample_detail.html",
        {
            "sample": sample,
            "project": project,
        },
    )


@login_required
def color_sample_review(request, sample_id):
    from core.models import ColorSample

    sample = get_object_or_404(ColorSample, id=sample_id)
    project = sample.project
    profile = getattr(request.user, "profile", None)
    # Permissions: clients, PM and designers can leave notes and move to 'review'; only staff can approve/reject
    if not (
        request.user.is_staff
        or (profile and profile.role in ["client", "project_manager", "designer"])
    ):
        messages.error(request, _("Access denied."))
        return redirect("dashboard")

    if request.method == "POST":
        form = ColorSampleReviewForm(request.POST, instance=sample)
        if form.is_valid():
            old_status = sample.status
            inst = form.save(commit=False)
            # Validate status transition
            requested_status = inst.status
            if requested_status in ["approved", "rejected"] and not request.user.is_staff:
                messages.error(request, _("Only staff can approve or reject colors."))
            else:
                if requested_status == "approved" and not inst.approved_by:
                    inst.approved_by = request.user
                inst.save()
                # Notify changes
                from core.notifications import notify_color_approved, notify_color_review

                if requested_status == "approved":
                    notify_color_approved(inst, request.user)
                elif old_status != requested_status:
                    notify_color_review(inst, request.user)
                messages.success(
                    request,
                    f"Status updated to {inst.get_status_display()}"
                )
            return redirect("color_sample_detail", sample_id=sample.id)
    else:
        form = ColorSampleReviewForm(instance=sample)
    return render(
        request,
        "core/color_sample_review.html",
        {
            "form": form,
            "sample": sample,
            "project": project,
        },
    )


@login_required
def color_sample_quick_action(request, sample_id):
    """Quick approve/reject color sample (staff only, AJAX)."""
    if not request.user.is_staff:
        return JsonResponse({"error": "Permission denied"}, status=403)

    sample = get_object_or_404(ColorSample, id=sample_id)

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "approve":
            # Use model method to ensure signature and audit
            sample.approve(request.user, request.META.get("REMOTE_ADDR"))
            from core.notifications import notify_color_approved

            notify_color_approved(sample, request.user)
            return JsonResponse(
                {
                    "success": True,
                    "status": "approved",
                    "display": "Approved",
                    "sample_number": sample.sample_number,
                    "signature": sample.approval_signature,
                }
            )
        elif action == "reject":
            reason = request.POST.get("reason", "").strip()
            if not reason:
                return JsonResponse({"error": "Rejection reason required"}, status=400)
            sample.reject(request.user, reason)
            return JsonResponse(
                {
                    "success": True,
                    "status": "rejected",
                    "display": "Rejected",
                    "reason": sample.rejection_reason,
                }
            )

    return JsonResponse({"error": "Invalid action"}, status=400)


@login_required
def color_sample_client_feedback(request, sample_id):
    """Handle client feedback on color samples (request changes or add comment)."""
    from core.models import ColorSample
    from core.notifications import notify_color_review
    
    sample = get_object_or_404(ColorSample, id=sample_id)
    project = sample.project
    
    # Check access - client must have access to this project
    profile = getattr(request.user, "profile", None)
    if not profile:
        messages.error(request, _("Access denied."))
        return redirect("dashboard")
    
    # Allow clients, PMs, and staff
    if profile.role == "client":
        from core.models import ClientProjectAccess
        has_access = ClientProjectAccess.objects.filter(
            user=request.user, project=project
        ).exists() or project.client == request.user.username
        if not has_access:
            messages.error(request, _("You don't have access to this project."))
            return redirect("dashboard_client")
    elif profile.role not in ["project_manager", "designer"] and not request.user.is_staff:
        messages.error(request, _("Access denied."))
        return redirect("dashboard")
    
    if request.method == "POST":
        action = request.POST.get("action")
        feedback = request.POST.get("feedback", "").strip()
        
        if not feedback:
            messages.error(request, _("Please enter your feedback."))
            return redirect("color_sample_detail", sample_id=sample_id)
        
        if action == "request_changes":
            # Add feedback to client_notes and move to 'review' status
            existing_notes = sample.client_notes or ""
            timestamp = timezone.now().strftime("%Y-%m-%d %H:%M")
            new_note = f"[{timestamp}] Change requested by {request.user.get_full_name() or request.user.username}:\n{feedback}"
            sample.client_notes = f"{new_note}\n\n{existing_notes}".strip() if existing_notes else new_note
            sample.status = "review"
            sample.save()
            
            # Notify PM
            notify_color_review(sample, request.user)
            
            messages.success(request, _("Your feedback has been sent. The team will review your request."))
        
        elif action == "comment":
            # Just add comment to client_notes
            existing_notes = sample.client_notes or ""
            timestamp = timezone.now().strftime("%Y-%m-%d %H:%M")
            new_note = f"[{timestamp}] Comment from {request.user.get_full_name() or request.user.username}:\n{feedback}"
            sample.client_notes = f"{new_note}\n\n{existing_notes}".strip() if existing_notes else new_note
            sample.save()
            
            # Notify PM
            notify_color_review(sample, request.user)
            
            messages.success(request, _("Your comment has been added."))
        
        return redirect("color_sample_detail", sample_id=sample_id)
    
    return redirect("color_sample_detail", sample_id=sample_id)


@login_required
def color_sample_edit(request, sample_id):
    """Edit existing color sample"""
    sample = get_object_or_404(ColorSample, id=sample_id)
    project = sample.project
    profile = getattr(request.user, "profile", None)

    if not (request.user.is_staff or (profile and profile.role in ["client", "project_manager"])):
        messages.error(request, _("Access denied."))
        return redirect("color_sample_detail", sample_id=sample_id)

    if request.method == "POST":
        form = ColorSampleForm(request.POST, request.FILES, instance=sample)
        if form.is_valid():
            form.save()
            messages.success(request, _("Color sample updated."))
            return redirect("color_sample_detail", sample_id=sample_id)
    else:
        form = ColorSampleForm(instance=sample)

    return render(
        request,
        "core/color_sample_form.html",
        {
            "form": form,
            "project": project,
            "sample": sample,
            "is_edit": True,
        },
    )


@login_required
def color_sample_delete(request, sample_id):
    """Delete color sample"""
    sample = get_object_or_404(ColorSample, id=sample_id)
    project = sample.project
    profile = getattr(request.user, "profile", None)

    if not (request.user.is_staff or (profile and profile.role == "project_manager")):
        messages.error(request, _("Access denied."))
        return redirect("color_sample_detail", sample_id=sample_id)

    if request.method == "POST":
        project_id = sample.project.id
        sample.delete()
        messages.success(request, _("Color sample deleted."))
        return redirect("color_sample_list", project_id=project_id)

    return render(
        request,
        "core/color_sample_confirm_delete.html",
        {
            "sample": sample,
            "project": project,
        },
    )


# --- FLOOR PLANS ---
@login_required
def floor_plan_list(request, project_id):
    """List all floor plans for a project, grouped by level"""

    project = get_object_or_404(Project, id=project_id)
    
    # SECURITY: Check project access
    has_access, redirect_url = _check_user_project_access(request.user, project)
    if not has_access:
        messages.error(request, _("You don't have access to this project."))
        return redirect(redirect_url)
    
    plans = project.floor_plans.all().order_by("level", "name")

    # Group plans by level
    plans_by_level = defaultdict(list)
    for plan in plans:
        plans_by_level[plan.level].append(plan)

    # Sort levels
    sorted_levels = sorted(plans_by_level.keys(), reverse=True)  # Top to bottom

    # Check if user can edit pins (PM, Admin, Client, Designer, Owner)
    profile = getattr(request.user, "profile", None)
    can_edit_pins = request.user.is_staff or (
        profile
        and profile.role in ROLES_PROJECT_ACCESS
    )

    return render(
        request,
        "core/floor_plan_list.html",
        {
            "project": project,
            "plans": plans,
            "plans_by_level": dict(plans_by_level),
            "sorted_levels": sorted_levels,
            "can_edit_pins": can_edit_pins,
            "can_edit": can_edit_pins,
        },
    )


@login_required
def floor_plan_create(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    
    # SECURITY: Check project access
    has_access, redirect_url = _check_user_project_access(request.user, project)
    if not has_access:
        messages.error(request, _("You don't have access to this project."))
        return redirect(redirect_url)
    
    if request.method == "POST":
        form = FloorPlanForm(request.POST, request.FILES)
        if form.is_valid():
            inst = form.save(commit=False)
            inst.project = project
            inst.created_by = request.user
            inst.save()
            messages.success(request, _("Plano subido."))
            return redirect("floor_plan_list", project_id=project_id)
    else:
        form = FloorPlanForm()
    return render(
        request,
        "core/floor_plan_form.html",
        {
            "form": form,
            "project": project,
        },
    )


@login_required
def floor_plan_detail(request, plan_id):
    import json

    from core.models import FloorPlan

    plan = get_object_or_404(FloorPlan, id=plan_id)
    pins = plan.pins.select_related("color_sample", "linked_task").all()
    color_samples = plan.project.color_samples.filter(status__in=["approved", "review"]).order_by(
        "-created_at"
    )[:50]

    # Check if user can edit pins (PM, Admin, Client, Designer, Owner)
    profile = getattr(request.user, "profile", None)
    can_edit_pins = request.user.is_staff or (
        profile
        and profile.role in ROLES_PROJECT_ACCESS
    )

    # Check if user can delete pins/plan (only PM, Admin, Owner - NOT Designer)
    can_delete = request.user.is_staff or (
        profile and profile.role in (ROLES_STAFF | {"owner"})
    )

    # Serialize pins data for JavaScript
    pins_data = []
    for pin in pins:
        pins_data.append(
            {
                "id": pin.id,
                "x": float(pin.x),
                "y": float(pin.y),
                "title": pin.title,
                "description": pin.description or "",
                "pin_type": pin.pin_type,
                "pin_color": pin.pin_color,
                "path_points": pin.path_points or [],
            }
        )
    pins_json = json.dumps(pins_data)

    # Provide PlanPinForm so the page can render the pin editor fields
    from core.forms import PlanPinForm

    pin_form = PlanPinForm()

    return render(
        request,
        "core/floor_plan_detail.html",
        {
            "plan": plan,
            "pins": pins,
            "pins_json": pins_json,
            "color_samples": color_samples,
            "project": plan.project,
            "can_edit_pins": can_edit_pins,
            "can_delete": can_delete,
            "form": pin_form,
        },
    )


@login_required
def floor_plan_touchup_view(request, plan_id):
    """Display floor plan with touch-up and task pins (work items view)"""
    import json

    from core.models import FloorPlan

    plan = get_object_or_404(FloorPlan, id=plan_id)

    # Filter pins that are work items: touchup OR have a linked_task
    from django.db.models import Q
    all_work_pins = plan.pins.filter(
        Q(pin_type="touchup") | Q(linked_task__isnull=False)
    ).select_related("color_sample", "linked_task", "created_by").distinct()

    color_samples = plan.project.color_samples.filter(status__in=["approved", "review"]).order_by(
        "-created_at"
    )[:50]

    # Check if user can edit pins (PM, Admin, Client, Designer, Owner)
    profile = getattr(request.user, "profile", None)
    can_edit_pins = request.user.is_staff or (
        profile
        and profile.role in ROLES_PROJECT_ACCESS
    )

    # Check if user can delete pins/plan (only PM, Admin, Owner - NOT Designer)
    can_delete = request.user.is_staff or (
        profile and profile.role in (ROLES_STAFF | {"owner"})
    )

    # Serialize pins data for JavaScript
    pins_data = []
    for pin in all_work_pins:
        pins_data.append(
            {
                "id": pin.id,
                "x": float(pin.x),
                "y": float(pin.y),
                "title": pin.title,
                "description": pin.description or "",
                "pin_type": pin.pin_type,
                "pin_color": pin.pin_color,
                "path_points": pin.path_points or [],
            }
        )
    pins_json = json.dumps(pins_data)

    # Provide PlanPinForm so the page can render the pin editor fields
    from core.forms import PlanPinForm

    pin_form = PlanPinForm()

    # Get employees for task assignment
    employees = Employee.objects.filter(is_active=True).order_by("first_name", "last_name")

    # Get existing tasks for linking (unlinked tasks without a pin)
    from core.models import Task
    unlinked_tasks = Task.objects.filter(
        project=plan.project,
        plan_pin__isnull=True  # Only tasks without a pin location
    ).order_by("-created_at")[:50]

    # Separate touchup pins and task pins for the template
    touchup_pins = [p for p in all_work_pins if p.pin_type == "touchup"]
    task_pins = [p for p in all_work_pins if p.pin_type != "touchup" and p.linked_task]

    return render(
        request,
        "core/floor_plan_touchup_view.html",
        {
            "plan": plan,
            "pins": all_work_pins,
            "pins_json": pins_json,
            "touchup_pins": touchup_pins,
            "task_pins": task_pins,
            "color_samples": color_samples,
            "project": plan.project,
            "can_edit_pins": can_edit_pins,
            "can_delete": can_delete,
            "form": pin_form,
            "employees": employees,
            "unlinked_tasks": unlinked_tasks,
        },
    )


@login_required
def floor_plan_edit(request, plan_id):
    """Edit an existing floor plan (name, level, image)"""
    plan = get_object_or_404(FloorPlan, id=plan_id)
    project = plan.project
    profile = getattr(request.user, "profile", None)
    if not (request.user.is_staff or (profile and profile.role in ["project_manager"])):
        messages.error(request, _("Acceso denegado."))
        return redirect("floor_plan_detail", plan_id=plan.id)
    if request.method == "POST":
        form = FloorPlanForm(request.POST, request.FILES, instance=plan)
        if form.is_valid():
            form.save()
            messages.success(request, _("Plano actualizado."))
            return redirect("floor_plan_detail", plan_id=plan.id)
    else:
        form = FloorPlanForm(instance=plan)
    return render(
        request,
        "core/floor_plan_form.html",
        {
            "form": form,
            "project": project,
            "plan": plan,
            "is_edit": True,
        },
    )


@login_required
def floor_plan_delete(request, plan_id):
    """Delete a floor plan and its pins"""
    plan = get_object_or_404(FloorPlan, id=plan_id)
    project = plan.project
    profile = getattr(request.user, "profile", None)
    if not (request.user.is_staff or (profile and profile.role in ["project_manager"])):
        messages.error(request, _("Acceso denegado."))
        return redirect("floor_plan_detail", plan_id=plan.id)
    if request.method == "POST":
        project_id = project.id
        plan.delete()
        messages.success(request, _("Plano eliminado."))
        return redirect("floor_plan_list", project_id=project_id)
    return render(
        request,
        "core/floor_plan_confirm_delete.html",
        {
            "project": project,
            "plan": plan,
        },
    )


@login_required
def pin_detail_ajax(request, pin_id):
    """Return JSON details for a pin to show in a popover."""
    from core.models import PlanPin

    pin = get_object_or_404(
        PlanPin.objects.select_related("linked_task", "color_sample"), id=pin_id
    )
    data = {
        "id": pin.id,
        "title": getattr(pin, "title", f"Pin #{pin.id}"),
        "description": getattr(pin, "description", ""),
        "type": getattr(pin, "pin_type", ""),
        "color": getattr(pin, "pin_color", ""),
        "task": None,
        "color_sample": None,
        "links": {},
    }
    try:
        if pin.linked_task_id:
            data["task"] = {
                "id": pin.linked_task_id,
                "title": getattr(pin.linked_task, "title", ""),
                "status": getattr(pin.linked_task, "status", ""),
            }
            data["links"]["task"] = reverse("task_detail", args=[pin.linked_task_id])
        if pin.color_sample_id:
            data["color_sample"] = {
                "id": pin.color_sample_id,
                "name": getattr(pin.color_sample, "name", ""),
                "brand": getattr(pin.color_sample, "brand", ""),
                "status": getattr(pin.color_sample, "status", ""),
            }
            data["links"]["color_sample"] = reverse(
                "color_sample_detail", args=[pin.color_sample_id]
            )
    except Exception:
        pass
    return JsonResponse(data)


@login_required
def floor_plan_add_pin(request, plan_id):
    from core.models import DamageReport, FloorPlan, Task

    plan = get_object_or_404(FloorPlan, id=plan_id)
    if request.method == "POST":
        form = PlanPinForm(request.POST)
        try:
            x = Decimal(request.POST.get("x"))
            y = Decimal(request.POST.get("y"))
        except Exception:
            messages.error(request, _("Coordenadas inválidas."))
            return redirect("floor_plan_detail", plan_id=plan.id)

        # Capturar datos de trayectoria multipunto si existen
        is_multipoint = request.POST.get("is_multipoint") == "true"
        path_points_json = request.POST.get("path_points", "[]")
        try:
            path_points = json.loads(path_points_json) if is_multipoint else []
        except Exception:
            path_points = []

        if form.is_valid():
            pin = form.save(commit=False)
            pin.plan = plan
            pin.x = x
            pin.y = y
            pin.is_multipoint = is_multipoint
            pin.path_points = path_points
            pin.created_by = request.user
            pin.save()
            # Crear entidades asociadas según tipo
            if form.cleaned_data.get("create_task") and pin.pin_type in ["touchup", "color"]:
                task = Task.objects.create(
                    project=plan.project,
                    title=pin.title or "Touch-up plano",
                    description=pin.description,
                    status="Pending",
                    created_by=request.user,
                    is_touchup=True,
                )
                pin.linked_task = task
                pin.save(update_fields=["linked_task"])
            elif pin.pin_type == "damage":
                # Crear reporte de daño básico y asociarlo al pin
                dr = DamageReport.objects.create(
                    project=plan.project,
                    plan=plan,
                    pin=pin,
                    title=pin.title or "Damage reported",
                    description=pin.description,
                    severity="medium",
                    status="open",
                    reported_by=request.user,
                )
                # Notificar PM
                from core.notifications import notify_damage_reported

                notify_damage_reported(dr, request.user)
            messages.success(request, _("Pin agregado."))
            return redirect("floor_plan_detail", plan_id=plan.id)
    else:
        form = PlanPinForm()
    return render(
        request,
        "core/floor_plan_add_pin.html",
        {
            "form": form,
            "plan": plan,
            "project": plan.project,
        },
    )


