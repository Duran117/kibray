"""Touch-up V2 views — extracted from legacy_views.py in Phase 8."""
from core.views._helpers import *  # noqa: F401, F403
from core.views._helpers import (
    _check_user_project_access,
    _is_pm_or_admin,
    _is_staffish,
    logger,
)
from django.utils.translation import gettext_lazy as _  # noqa: F811


# TOUCH-UP V2 VIEWS
# ========================================================================================


@login_required
def touchup_list(request, project_id):
    """List all touch-ups for a project with filters."""
    from django.core.paginator import Paginator

    from core.models import TouchUp

    project = get_object_or_404(Project, id=project_id)

    has_access, redirect_url = _check_user_project_access(request.user, project)
    if not has_access:
        messages.error(request, _("You don't have access to this project."))
        return redirect(redirect_url)

    is_pm_admin = _is_pm_or_admin(request.user)

    # Employees can see touch-ups assigned to them; PM/Admin see all
    if is_pm_admin:
        qs = (
            TouchUp.objects.filter(project=project)
            .select_related("assigned_to", "created_by", "closed_by", "color_sample")
            .prefetch_related("photos")
        )
    else:
        # Employee — must have an Employee profile
        try:
            emp = Employee.objects.get(user=request.user)
        except Employee.DoesNotExist:
            messages.error(request, _("You don't have access to this project."))
            return redirect("dashboard")
        qs = (
            TouchUp.objects.filter(project=project, assigned_to=emp)
            .select_related("assigned_to", "created_by", "closed_by", "color_sample")
            .prefetch_related("photos")
        )

    # Filters
    status = request.GET.get("status", "")
    if status:
        qs = qs.filter(status=status)
    elif "status" not in request.GET:
        # Default: hide closed touch-ups unless explicitly requested
        qs = qs.exclude(status="closed")

    priority = request.GET.get("priority", "")
    if priority:
        qs = qs.filter(priority=priority)

    assigned = request.GET.get("assigned", "")
    if assigned == "unassigned":
        qs = qs.filter(assigned_to__isnull=True)
    elif assigned:
        qs = qs.filter(assigned_to_id=assigned)

    search = request.GET.get("q", "").strip()
    if search:
        from django.db.models import Q

        qs = qs.filter(Q(title__icontains=search) | Q(description__icontains=search))

    # Source filter (portal vs staff)
    source = request.GET.get("source", "")
    if source == "portal":
        qs = qs.exclude(resident_name="").exclude(resident_name__isnull=True)
    elif source == "staff":
        from django.db.models import Q as SourceQ
        qs = qs.filter(SourceQ(resident_name="") | SourceQ(resident_name__isnull=True))

    # Sort
    sort = request.GET.get("sort", "-created_at")
    valid_sorts = [
        "created_at", "-created_at", "priority", "-priority",
        "status", "-status", "due_date", "-due_date",
    ]
    if sort in valid_sorts:
        qs = qs.order_by(sort)

    # Stats
    from django.db.models import Count, Q as DQ

    stats = TouchUp.objects.filter(project=project).aggregate(
        total=Count("id"),
        open=Count("id", filter=DQ(status="open")),
        in_progress=Count("id", filter=DQ(status="in_progress")),
        review=Count("id", filter=DQ(status="review")),
        closed=Count("id", filter=DQ(status="closed")),
        portal=Count("id", filter=~DQ(resident_name="") & DQ(resident_name__isnull=False)),
    )

    # Employees for filter dropdown
    employees = Employee.objects.filter(is_active=True).order_by("first_name", "last_name")

    paginator = Paginator(qs, 20)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(
        request,
        "core/touchup_v2_list.html",
        {
            "project": project,
            "page_obj": page_obj,
            "stats": stats,
            "employees": employees,
            "filter_status": status,
            "filter_priority": priority,
            "filter_assigned": assigned,
            "filter_search": search,
            "filter_source": source,
            "sort_by": sort,
            "status_choices": TouchUp.STATUS_CHOICES,
            "priority_choices": TouchUp.PRIORITY_CHOICES,
            "is_pm_admin": is_pm_admin,
        },
    )


@login_required
def touchup_v2_create(request, project_id):
    """Create a new touch-up."""
    from core.models import TouchUp, TouchUpPhoto

    project = get_object_or_404(Project, id=project_id)

    if not _is_pm_or_admin(request.user):
        messages.error(request, _("Only PMs and Admins can create touch-ups."))
        return redirect("touchup_list", project_id=project.id)

    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        if not title:
            messages.error(request, _("Title is required."))
            return redirect("touchup_v2_create", project_id=project.id)

        assigned_to_id = request.POST.get("assigned_to") or None
        assigned_to = None
        if assigned_to_id:
            assigned_to = Employee.objects.filter(id=assigned_to_id).first()

        color_sample_id = request.POST.get("color_sample") or None

        touchup = TouchUp.objects.create(
            project=project,
            title=title,
            description=request.POST.get("description", "").strip(),
            goal=request.POST.get("goal", "").strip(),
            notes=request.POST.get("notes", "").strip(),
            color_name=request.POST.get("color_name", "").strip(),
            color_code=request.POST.get("color_code", "").strip(),
            color_brand=request.POST.get("color_brand", "").strip(),
            color_hex=request.POST.get("color_hex", "").strip(),
            sheen=request.POST.get("sheen", "").strip(),
            color_sample_id=color_sample_id if color_sample_id else None,
            priority=request.POST.get("priority", "medium"),
            due_date=request.POST.get("due_date") or None,
            assigned_to=assigned_to,
            created_by=request.user,
        )

        # Handle floor plan pin location (optional)
        floor_plan_id = request.POST.get("floor_plan_id")
        pin_x = request.POST.get("pin_x")
        pin_y = request.POST.get("pin_y")
        if floor_plan_id and pin_x and pin_y:
            try:
                from core.models import FloorPlan
                from decimal import Decimal
                fp = FloorPlan.objects.get(id=floor_plan_id, project=project)
                touchup.floor_plan = fp
                touchup.pin_x = Decimal(pin_x)
                touchup.pin_y = Decimal(pin_y)
                touchup.save(update_fields=["floor_plan", "pin_x", "pin_y"])
            except (FloorPlan.DoesNotExist, Exception):
                pass

        # Handle multiple initial photos
        photos = request.FILES.getlist("photos")
        for photo in photos:
            TouchUpPhoto.objects.create(
                touchup=touchup,
                image=photo,
                phase="before",
                uploaded_by=request.user,
            )

        # Notify assigned employee
        if assigned_to and assigned_to.user:
            Notification.objects.create(
                user=assigned_to.user,
                project=project,
                notification_type="touchup",
                title=_("New Touch-Up: %(title)s") % {"title": title[:60]},
                message=_("You've been assigned a touch-up in %(project)s") % {"project": project.name},
                related_object_type="TouchUp",
                related_object_id=touchup.id,
                link_url=f"/projects/{project.id}/touchups-v2/{touchup.id}/",
            )

        messages.success(request, _("Touch-up \"%(title)s\" created successfully.") % {"title": touchup.title[:40]})

        # "Create & add another" → go back to create form; otherwise → list
        if request.POST.get("action") == "create_another":
            return redirect("touchup_v2_create", project_id=project.id)
        return redirect("touchup_list", project_id=project.id)

    # GET — render create form
    employees = Employee.objects.filter(is_active=True).order_by("first_name", "last_name")
    color_samples = project.color_samples.filter(status__in=["approved", "review"]).order_by("name")

    # Floor plans for optional pin location
    from core.models import FloorPlan
    floor_plans = FloorPlan.objects.filter(project=project, is_current=True).order_by("level")
    import json
    floor_plans_data = [
        {
            "id": fp.id,
            "name": fp.name,
            "level": fp.level,
            "level_identifier": fp.level_identifier or "",
            "image_url": fp.image.url if fp.image else "",
        }
        for fp in floor_plans
    ]

    return render(
        request,
        "core/touchup_v2_create.html",
        {
            "project": project,
            "employees": employees,
            "color_samples": color_samples,
            "priority_choices": TouchUp.PRIORITY_CHOICES,
            "floor_plans": floor_plans,
            "floor_plans_json": json.dumps(floor_plans_data),
        },
    )


@login_required
def touchup_v2_detail(request, project_id, touchup_id):
    """Detail view for a single touch-up with full info, photos, and updates."""
    from core.models import TouchUp

    project = get_object_or_404(Project, id=project_id)
    touchup = get_object_or_404(
        TouchUp.objects.select_related(
            "assigned_to", "created_by", "closed_by", "color_sample", "project", "floor_plan"
        ).prefetch_related("photos", "updates__author"),
        pk=touchup_id,
        project=project,
    )

    has_access, redirect_url = _check_user_project_access(request.user, project)
    if not has_access:
        # Allow if the touch-up is assigned to this user's employee profile
        try:
            emp = Employee.objects.get(user=request.user)
            if touchup.assigned_to != emp:
                messages.error(request, _("You don't have access to this project."))
                return redirect(redirect_url)
        except Employee.DoesNotExist:
            messages.error(request, _("You don't have access to this project."))
            return redirect(redirect_url)

    is_pm_admin = _is_pm_or_admin(request.user)
    can_edit = is_pm_admin

    # Employees can update their own touchup status (open→in_progress→review)
    is_assigned_employee = False
    if not is_pm_admin:
        try:
            emp = Employee.objects.get(user=request.user)
            is_assigned_employee = touchup.assigned_to == emp
        except Employee.DoesNotExist:
            pass

    before_photos = touchup.photos.filter(phase="before")
    progress_photos = touchup.photos.filter(phase="progress")
    after_photos = touchup.photos.filter(phase="after")
    employees = Employee.objects.filter(is_active=True).order_by("first_name", "last_name")

    # Floor plans for location display & editing
    from core.models import FloorPlan
    floor_plans = FloorPlan.objects.filter(project=project, is_current=True).order_by("level")
    import json
    floor_plans_data = [
        {
            "id": fp.id,
            "name": fp.name,
            "level": fp.level,
            "level_identifier": fp.level_identifier or "",
            "image_url": fp.image.url if fp.image else "",
        }
        for fp in floor_plans
    ]

    return render(
        request,
        "core/touchup_v2_detail.html",
        {
            "project": project,
            "touchup": touchup,
            "can_edit": can_edit,
            "is_assigned_employee": is_assigned_employee,
            "is_pm_admin": is_pm_admin,
            "before_photos": before_photos,
            "progress_photos": progress_photos,
            "after_photos": after_photos,
            "employees": employees,
            "status_choices": TouchUp.STATUS_CHOICES,
            "floor_plans": floor_plans,
            "floor_plans_json": json.dumps(floor_plans_data),
        },
    )


@login_required
def touchup_v2_update(request, project_id, touchup_id):
    """Update touch-up fields. PM/Admin can update everything.
    Assigned employees can only update status (open→in_progress, in_progress→review)."""
    from core.models import TouchUp, TouchUpUpdate

    project = get_object_or_404(Project, id=project_id)
    touchup = get_object_or_404(TouchUp, pk=touchup_id, project=project)

    is_pm_admin = _is_pm_or_admin(request.user)

    # Check if user is the assigned employee
    is_assigned_employee = False
    if not is_pm_admin:
        try:
            emp = Employee.objects.get(user=request.user)
            is_assigned_employee = touchup.assigned_to == emp
        except Employee.DoesNotExist:
            pass

    if not is_pm_admin and not is_assigned_employee:
        messages.error(request, _("You don't have permission to update this touch-up."))
        return redirect("touchup_v2_detail", project_id=project.id, touchup_id=touchup.id)

    if request.method != "POST":
        return redirect("touchup_v2_detail", project_id=project.id, touchup_id=touchup.id)

    old_status = touchup.status

    if is_pm_admin:
        # PM/Admin: full field update
        for field in ["title", "description", "goal", "notes", "color_name",
                       "color_code", "color_brand", "color_hex", "sheen"]:
            value = request.POST.get(field)
            if value is not None:
                setattr(touchup, field, value.strip())

        new_status = request.POST.get("status")
        if new_status and new_status in dict(TouchUp.STATUS_CHOICES):
            touchup.status = new_status

        priority = request.POST.get("priority")
        if priority and priority in dict(TouchUp.PRIORITY_CHOICES):
            touchup.priority = priority

        assigned_to_id = request.POST.get("assigned_to")
        if assigned_to_id == "":
            touchup.assigned_to = None
        elif assigned_to_id:
            touchup.assigned_to = Employee.objects.filter(id=assigned_to_id).first()

        due_date = request.POST.get("due_date")
        if due_date == "":
            touchup.due_date = None
        elif due_date:
            touchup.due_date = due_date

        color_sample_id = request.POST.get("color_sample")
        if color_sample_id == "":
            touchup.color_sample = None
        elif color_sample_id:
            touchup.color_sample_id = color_sample_id
    else:
        # Assigned employee: only status transitions allowed
        EMPLOYEE_TRANSITIONS = {
            "open": "in_progress",
            "in_progress": "review",
        }
        new_status = request.POST.get("status")
        allowed_next = EMPLOYEE_TRANSITIONS.get(touchup.status)
        if new_status and new_status == allowed_next:
            touchup.status = new_status
        elif new_status:
            messages.error(request, _("You can only move this touch-up to '%(next)s'.") % {
                "next": dict(TouchUp.STATUS_CHOICES).get(allowed_next, "")
            })
            return redirect("touchup_v2_detail", project_id=project.id, touchup_id=touchup.id)

    # Handle floor plan pin location (PM/Admin only)
    if is_pm_admin:
        floor_plan_id = request.POST.get("floor_plan_id")
        pin_x = request.POST.get("pin_x")
        pin_y = request.POST.get("pin_y")
        if floor_plan_id is not None:  # Field was in the form
            if floor_plan_id and pin_x and pin_y:
                try:
                    from core.models import FloorPlan
                    from decimal import Decimal
                    fp = FloorPlan.objects.get(id=floor_plan_id, project=project)
                    touchup.floor_plan = fp
                    touchup.pin_x = Decimal(pin_x)
                    touchup.pin_y = Decimal(pin_y)
                except (FloorPlan.DoesNotExist, Exception):
                    pass
            elif floor_plan_id and not pin_x:
                # Floor plan selected but pin cleared
                touchup.floor_plan = None
                touchup.pin_x = None
                touchup.pin_y = None

    touchup.save()

    # Create status change update if status changed
    if old_status != touchup.status:
        TouchUpUpdate.objects.create(
            touchup=touchup,
            author=request.user,
            comment=_("Status changed from %(old)s to %(new)s") % {
                "old": dict(TouchUp.STATUS_CHOICES).get(old_status, old_status),
                "new": touchup.get_status_display(),
            },
            old_status=old_status,
            new_status=touchup.status,
        )

        # Notify the creator about status changes (started, completed, etc.)
        if touchup.created_by and touchup.created_by != request.user:
            status_messages = {
                "in_progress": _("Work has started on your touch-up: %(title)s"),
                "review": _("Your touch-up is now under review: %(title)s"),
                "closed": _("Your touch-up has been completed: %(title)s"),
            }
            msg_template = status_messages.get(touchup.status)
            if msg_template:
                Notification.objects.create(
                    user=touchup.created_by,
                    project=project,
                    notification_type="touchup",
                    title=msg_template % {"title": touchup.title[:60]},
                    message=_("%(user)s updated the status to %(status)s") % {
                        "user": request.user.get_full_name() or request.user.username,
                        "status": touchup.get_status_display(),
                    },
                    related_object_type="TouchUp",
                    related_object_id=touchup.id,
                    link_url=f"/projects/{project.id}/touchups-v2/{touchup.id}/",
                )

    messages.success(request, _("Touch-up updated."))
    return redirect("touchup_v2_detail", project_id=project.id, touchup_id=touchup.id)


@login_required
def touchup_v2_add_update(request, project_id, touchup_id):
    """Add a follow-up comment/photo to a touch-up."""
    from core.models import TouchUp, TouchUpUpdate

    project = get_object_or_404(Project, id=project_id)
    touchup = get_object_or_404(TouchUp, pk=touchup_id, project=project)

    if request.method != "POST":
        return redirect("touchup_v2_detail", project_id=project.id, touchup_id=touchup.id)

    comment = request.POST.get("comment", "").strip()
    if not comment:
        messages.error(request, _("Comment cannot be empty."))
        return redirect("touchup_v2_detail", project_id=project.id, touchup_id=touchup.id)

    photo = request.FILES.get("photo")

    TouchUpUpdate.objects.create(
        touchup=touchup,
        author=request.user,
        comment=comment,
        photo=photo,
    )

    # Notify the touchup creator if commenter is different
    if request.user != touchup.created_by and touchup.created_by:
        Notification.objects.create(
            user=touchup.created_by,
            project=project,
            notification_type="touchup",
            title=_("Update on: %(title)s") % {"title": touchup.title[:60]},
            message=f"{request.user.get_full_name() or request.user.username}: {comment[:100]}",
            related_object_type="TouchUp",
            related_object_id=touchup.id,
            link_url=f"/projects/{project.id}/touchups-v2/{touchup.id}/",
        )

    messages.success(request, _("Follow-up added."))
    return redirect("touchup_v2_detail", project_id=project.id, touchup_id=touchup.id)


@login_required
def touchup_v2_add_photo(request, project_id, touchup_id):
    """Add photos to a touch-up (any phase)."""
    from core.models import TouchUp, TouchUpPhoto

    project = get_object_or_404(Project, id=project_id)
    touchup = get_object_or_404(TouchUp, pk=touchup_id, project=project)

    if request.method != "POST":
        return redirect("touchup_v2_detail", project_id=project.id, touchup_id=touchup.id)

    phase = request.POST.get("phase", "before")
    if phase not in dict(TouchUpPhoto.PHASE_CHOICES):
        phase = "before"

    photos = request.FILES.getlist("photos")
    if not photos:
        messages.error(request, _("Please select at least one photo."))
        return redirect("touchup_v2_detail", project_id=project.id, touchup_id=touchup.id)

    for photo_file in photos:
        TouchUpPhoto.objects.create(
            touchup=touchup,
            image=photo_file,
            phase=phase,
            caption=request.POST.get("caption", "").strip(),
            uploaded_by=request.user,
        )

    messages.success(request, _("Photos uploaded."))
    return redirect("touchup_v2_detail", project_id=project.id, touchup_id=touchup.id)


@login_required
def touchup_v2_close(request, project_id, touchup_id):
    """Close a touch-up with closing notes and required after photos."""
    from core.models import TouchUp, TouchUpPhoto, TouchUpUpdate

    project = get_object_or_404(Project, id=project_id)
    touchup = get_object_or_404(TouchUp, pk=touchup_id, project=project)

    if not _is_pm_or_admin(request.user):
        messages.error(request, _("Only PMs and Admins can close touch-ups."))
        return redirect("touchup_v2_detail", project_id=project.id, touchup_id=touchup.id)

    if request.method != "POST":
        return redirect("touchup_v2_detail", project_id=project.id, touchup_id=touchup.id)

    closing_notes = request.POST.get("closing_notes", "").strip()
    photos = request.FILES.getlist("photos")

    # Require at least one after photo
    existing_after = touchup.photos.filter(phase="after").count()
    if not photos and existing_after == 0:
        messages.error(request, _("At least one 'after' photo is required to close a touch-up."))
        return redirect("touchup_v2_detail", project_id=project.id, touchup_id=touchup.id)

    # Save after photos
    for photo_file in photos:
        TouchUpPhoto.objects.create(
            touchup=touchup,
            image=photo_file,
            phase="after",
            uploaded_by=request.user,
        )

    old_status = touchup.status
    touchup.close(request.user, notes=closing_notes)

    # Record update
    TouchUpUpdate.objects.create(
        touchup=touchup,
        author=request.user,
        comment=_("Touch-up closed.") + (f" {closing_notes}" if closing_notes else ""),
        old_status=old_status,
        new_status="closed",
    )

    # Notify the creator that their touch-up was completed
    if touchup.created_by and touchup.created_by != request.user:
        Notification.objects.create(
            user=touchup.created_by,
            project=project,
            notification_type="touchup",
            title=_("Your touch-up has been completed: %(title)s") % {"title": touchup.title[:60]},
            message=_("%(user)s closed this touch-up in %(project)s") % {
                "user": request.user.get_full_name() or request.user.username,
                "project": project.name,
            },
            related_object_type="TouchUp",
            related_object_id=touchup.id,
            link_url=f"/projects/{project.id}/touchups-v2/{touchup.id}/",
        )

    messages.success(request, _("Touch-up closed successfully."))
    return redirect("touchup_list", project_id=project.id)


@login_required
def touchup_v2_reopen(request, project_id, touchup_id):
    """Reopen a closed touch-up."""
    from core.models import TouchUp, TouchUpUpdate

    project = get_object_or_404(Project, id=project_id)
    touchup = get_object_or_404(TouchUp, pk=touchup_id, project=project)

    if not _is_pm_or_admin(request.user):
        messages.error(request, _("Only PMs and Admins can reopen touch-ups."))
        return redirect("touchup_v2_detail", project_id=project.id, touchup_id=touchup.id)

    if request.method == "POST" and touchup.status == "closed":
        reason = request.POST.get("reason", "").strip()
        touchup.status = "open"
        touchup.closed_by = None
        touchup.closed_at = None
        touchup.closing_notes = ""
        touchup.save()

        TouchUpUpdate.objects.create(
            touchup=touchup,
            author=request.user,
            comment=_("Reopened.") + (f" {reason}" if reason else ""),
            old_status="closed",
            new_status="open",
        )

        messages.success(request, _("Touch-up reopened."))

    return redirect("touchup_v2_detail", project_id=project.id, touchup_id=touchup.id)


@login_required
def touchup_v2_delete(request, project_id, touchup_id):
    """Delete a touch-up. PM/Admin only."""
    from core.models import TouchUp

    project = get_object_or_404(Project, id=project_id)
    touchup = get_object_or_404(TouchUp, pk=touchup_id, project=project)

    if not _is_pm_or_admin(request.user):
        messages.error(request, _("Only PMs and Admins can delete touch-ups."))
        return redirect("touchup_v2_detail", project_id=project.id, touchup_id=touchup.id)

    if request.method == "POST":
        touchup.delete()
        messages.success(request, _("Touch-up deleted."))
        return redirect("touchup_list", project_id=project.id)

    return redirect("touchup_v2_detail", project_id=project.id, touchup_id=touchup.id)


@login_required
def touchup_v2_save_annotation(request, project_id, touchup_id, photo_id):
    """Save canvas annotation data for a photo (AJAX)."""
    import json

    from core.models import TouchUpPhoto

    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)

    photo = get_object_or_404(TouchUpPhoto, pk=photo_id, touchup_id=touchup_id)

    try:
        data = json.loads(request.body)
        photo.annotations = data.get("annotations", {})
        photo.save(update_fields=["annotations"])
        return JsonResponse({"success": True})
    except (json.JSONDecodeError, Exception) as e:
        logger.error(f"Error saving photo annotations: {e}")
        return JsonResponse({"error": "Invalid request data"}, status=400)
