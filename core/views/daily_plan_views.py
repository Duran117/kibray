"""Daily planning, SOP & activity views — extracted from legacy_views.py in Phase 8."""
from core.views._helpers import *  # noqa: F401, F403
from core.views._helpers import (
    _check_user_project_access,
    _is_admin_user,
    _is_staffish,
    _require_admin_or_redirect,
    logger,
)
from django.utils.translation import gettext_lazy as _  # noqa: F811



@login_required
def daily_plan_fetch_weather(request, plan_id):
    """AJAX endpoint to fetch weather for a daily plan (Q12.8)."""
    if request.method != "POST":
        return JsonResponse({"error": gettext("POST required")}, status=405)

    if not _is_staffish(request.user):
        return JsonResponse({"error": gettext("Sin permiso")}, status=403)

    plan = get_object_or_404(DailyPlan, id=plan_id)

    # Fetch weather (calls API)
    success = plan.fetch_weather()

    if success:
        return JsonResponse(
            {
                "success": True,
                "weather_data": plan.weather_data,
                "fetched_at": plan.weather_fetched_at.isoformat()
                if plan.weather_fetched_at
                else None,
            }
        )
    else:
        return JsonResponse(
            {"error": gettext("No se pudo obtener el clima. Verifique la ubicación del proyecto.")},
            status=400,
        )


@login_required
def daily_plan_convert_activities(request, plan_id):
    """Convert planned activities to tasks (Q12.2)."""
    if request.method != "POST":
        return JsonResponse({"error": gettext("POST required")}, status=405)

    if not _is_staffish(request.user):
        return JsonResponse({"error": gettext("Sin permiso")}, status=403)

    plan = get_object_or_404(DailyPlan, id=plan_id)

    # Can only convert if status is PUBLISHED
    if plan.status != "PUBLISHED":
        return JsonResponse(
            {"error": gettext("Solo se pueden convertir planes en estado PUBLISHED")}, status=400
        )

    # Convert activities to tasks
    created_tasks = plan.convert_activities_to_tasks()

    # Update plan status
    plan.status = "IN_PROGRESS"
    plan.save()

    return JsonResponse(
        {
            "success": True,
            "tasks_created": len(created_tasks),
            "task_ids": [t.id for t in created_tasks],
            "message": f"{len(created_tasks)} tareas creadas exitosamente",
        }
    )


@login_required
def daily_plan_productivity(request, plan_id):
    """Get productivity score for a daily plan (Q12.5)."""
    plan = get_object_or_404(DailyPlan, id=plan_id)

    score = plan.calculate_productivity_score()

    return JsonResponse(
        {
            "plan_id": plan.id,
            "plan_date": plan.plan_date.isoformat(),
            "estimated_hours": float(plan.estimated_hours_total or 0),
            "actual_hours": float(plan.actual_hours_worked or 0),
            "productivity_score": score,
            "status": plan.status,
        }
    )





@login_required
def daily_plan_list(request):
    """List daily plans with optional status filter (Module 12.7)."""
    if not _is_staffish(request.user):
        return HttpResponseForbidden("Access denied")
    status = request.GET.get("status")
    qs = DailyPlan.objects.select_related("project", "created_by").order_by("-plan_date")
    if status and status in ["DRAFT", "PUBLISHED", "IN_PROGRESS", "COMPLETED", "SKIPPED"]:
        qs = qs.filter(status=status)
    return render(
        request,
        "core/daily_plan_list.html",
        {
            "plans": qs[:200],  # safety cap
            "filter_status": status,
        },
    )


@login_required
def daily_plan_detail(request, plan_id):
    """Detail view for a daily plan with productivity and weather (Module 12.7)."""
    plan = get_object_or_404(DailyPlan.objects.select_related("project", "created_by"), pk=plan_id)

    # Allow staff OR any employee assigned to activities in this plan
    if not _is_staffish(request.user):
        is_assigned = plan.activities.filter(
            assigned_employees__user=request.user
        ).exists()
        if not is_assigned:
            return HttpResponseForbidden("Access denied")

    activities = (
        plan.activities.select_related("activity_template", "schedule_item")
        .prefetch_related(
            "assigned_employees",
            "sub_activities__assigned_employees",
            "comments__author",
        )
        .filter(parent__isnull=True)  # Only top-level activities
        .order_by("order")
    )
    productivity = plan.calculate_productivity_score()

    # Get all active employees for assignment modal
    employees = Employee.objects.filter(is_active=True).order_by("first_name", "last_name")

    return render(
        request,
        "core/daily_plan_detail.html",
        {
            "plan": plan,
            "activities": activities,
            "employees": employees,
            "productivity_score": productivity,
            "weather": plan.weather_data,
            "can_convert": plan.status == "PUBLISHED",
            "can_start": plan.status == "PUBLISHED",
            "can_complete": plan.status == "IN_PROGRESS",
        },
    )


@login_required
def daily_plan_delete(request, plan_id):
    """Delete a daily plan (staff/PM only). Shows confirm page."""
    if not _is_staffish(request.user):
        return HttpResponseForbidden("Access denied")

    plan = get_object_or_404(DailyPlan.objects.select_related("project"), pk=plan_id)

    if request.method == "POST":
        project_name = plan.project.name
        plan_date = plan.plan_date
        plan.delete()
        messages.success(
            request,
            _("Daily plan for %(date)s in %(project)s deleted")
            % {"date": plan_date, "project": project_name},
        )
        return redirect("daily_planning_dashboard")

    return render(request, "core/daily_plan_confirm_delete.html", {"plan": plan})


@login_required
def daily_planning_dashboard(request):
    """
    Visual Planning Workspace – Calendar + Timeline + Team Assignments
    Redesigned Dec 2025: node-based timeline with branches, team panel,
    voice/text input, material prep, weather integration.
    """
    if not _is_staffish(request.user):
        return HttpResponseForbidden("Access denied")

    today = timezone.now().date()

    # ── Handle create plan form submission (kept from legacy) ──────────
    if request.method == "POST" and request.POST.get("create_plan"):
        project_id = request.POST.get("project")
        plan_date_str = request.POST.get("plan_date")

        if project_id and plan_date_str:
            project = get_object_or_404(Project, pk=project_id)
            plan_date = datetime.strptime(plan_date_str, "%Y-%m-%d").date()

            existing = DailyPlan.objects.filter(project=project, plan_date=plan_date).first()
            if existing:
                messages.warning(
                    request, _("Plan already exists for %(date)s") % {"date": plan_date}
                )
                return redirect("daily_plan_detail", plan_id=existing.id)

            completion_deadline = timezone.make_aware(
                datetime.combine(
                    plan_date - timedelta(days=1), datetime.min.time().replace(hour=17)
                )
            )

            plan = DailyPlan.objects.create(
                project=project,
                plan_date=plan_date,
                created_by=request.user,
                completion_deadline=completion_deadline,
                status="DRAFT",
            )

            messages.success(request, _("Daily plan created for %(date)s") % {"date": plan_date})
            return redirect("daily_plan_detail", plan_id=plan.id)

    # ── Gather data for the workspace (±30 days window) ────────────────
    window_start = today - timedelta(days=30)
    window_end = today + timedelta(days=30)

    plans_qs = (
        DailyPlan.objects.filter(plan_date__range=[window_start, window_end])
        .select_related("project", "created_by")
        .prefetch_related(
            "activities",
            "activities__assigned_employees",
        )
        .order_by("plan_date", "project__name")
    )

    # Build JSON-friendly plans list
    plans_json_list = []
    plan_dates_set = set()

    for plan in plans_qs:
        plan_dates_set.add(plan.plan_date.isoformat())

        activities_list = []
        for act in plan.activities.all():
            activities_list.append({
                "id": act.id,
                "title": act.title,
                "description": act.description or "",
                "order": act.order,
                "parent_id": act.parent_id,
                "start_time": act.start_time.strftime("%H:%M") if act.start_time else None,
                "end_time": act.end_time.strftime("%H:%M") if act.end_time else None,
                "estimated_hours": float(act.estimated_hours) if act.estimated_hours else None,
                "actual_hours": float(act.actual_hours) if act.actual_hours else None,
                "status": act.status,
                "progress_percentage": act.progress_percentage,
                "materials_needed": act.materials_needed or [],
                "materials_checked": act.materials_checked,
                "material_shortage": act.material_shortage,
                "assigned_employee_ids": list(
                    act.assigned_employees.values_list("id", flat=True)
                ),
                "is_group_activity": act.is_group_activity,
            })

        # Weather data (already JSON)
        weather = plan.weather_data if plan.weather_data else None

        # Project color – fall back to a deterministic colour based on project id
        project_colors = [
            "#6366f1", "#8b5cf6", "#ec4899", "#f97316", "#14b8a6",
            "#3b82f6", "#22c55e", "#eab308", "#f43f5e", "#06b6d4",
        ]
        proj_color = project_colors[plan.project_id % len(project_colors)]

        plans_json_list.append({
            "id": plan.id,
            "plan_date": plan.plan_date.isoformat(),
            "project_id": plan.project_id,
            "project_name": plan.project.name,
            "project_color": proj_color,
            "status": plan.status,
            "created_by": plan.created_by.get_full_name() or plan.created_by.username,
            "weather_data": weather,
            "admin_approved": plan.admin_approved,
            "activities": activities_list,
        })

    # Employees for avatar display
    employees = list(
        Employee.objects.filter(is_active=True).values("id", "first_name", "last_name")
    )

    # Active projects for create modal
    active_projects = Project.objects.filter(
        Q(end_date__gte=today) | Q(end_date__isnull=True)
    ).order_by("name")

    context = {
        "today": today,
        "projects": active_projects,
        "plans_json": json.dumps(plans_json_list, default=str),
        "plan_dates_json": json.dumps(sorted(plan_dates_set)),
        "employees_json": json.dumps(employees, default=str),
        "plans_by_date": plans_json_list,
    }

    return render(request, "core/daily_plan_workspace.html", context)


@login_required
def daily_plan_create(request, project_id):
    """
    Create a new daily plan for a project with smart suggestions from schedule.

    GET: Shows form with suggested schedule items for the target date
    POST: Creates plan and optionally imports activities from schedule items
    """
    if not _is_staffish(request.user):
        return HttpResponseForbidden("Access denied")

    project = get_object_or_404(Project, pk=project_id)

    if request.method == "POST":
        plan_date_str = request.POST.get("plan_date")
        plan_date = None
        if plan_date_str:
            try:
                plan_date = datetime.strptime(plan_date_str, "%Y-%m-%d").date()
            except ValueError:
                # Invalid date format: re-render form with error instead of raising exception
                messages.error(request, _("Invalid date format"))
                from core.services.planning_service import get_suggested_items_for_date

                target_date = timezone.now().date() + timedelta(days=1)
                suggested_items = get_suggested_items_for_date(project, target_date)
                return render(
                    request,
                    "core/daily_plan_create.html",
                    {
                        "project": project,
                        "min_date": timezone.now().date(),
                        "target_date": target_date,
                        "suggested_items": suggested_items,
                        "has_suggestions": len(suggested_items) > 0,
                        "invalid_date": True,
                    },
                )

        if not plan_date:
            messages.error(request, _("Plan date is required"))
            return redirect("daily_planning_dashboard")

        # Check if plan already exists
        existing = DailyPlan.objects.filter(project=project, plan_date=plan_date).first()
        if existing:
            messages.warning(request, _("Plan already exists for %(date)s") % {"date": plan_date})
            return redirect("daily_plan_edit", plan_id=existing.id)

        # Set completion deadline (5pm day before)
        completion_deadline = timezone.make_aware(
            datetime.combine(plan_date - timedelta(days=1), datetime.min.time().replace(hour=17))
        )

        # Create plan
        plan = DailyPlan.objects.create(
            project=project,
            plan_date=plan_date,
            created_by=request.user,
            completion_deadline=completion_deadline,
            status="DRAFT",
        )

        # Import selected schedule items as activities
        selected_items = request.POST.getlist("import_items")  # List of schedule_item IDs
        if selected_items:
            from core.models import PlannedActivity

            for idx, item_id in enumerate(selected_items):
                try:
                    schedule_item = ScheduleItemV2.objects.get(id=int(item_id), project=project)
                    PlannedActivity.objects.create(
                        daily_plan=plan,
                        title=schedule_item.name,
                        description=schedule_item.description,
                        order=idx,
                        status="PENDING",
                        progress_percentage=0,
                    )
                except ScheduleItemV2.DoesNotExist:
                    continue

            messages.success(
                request,
                f"Daily plan created with {len(selected_items)} imported activities for {plan_date}",
            )
        else:
            messages.success(request, _("Daily plan created for %(date)s") % {"date": plan_date})

        return redirect("daily_plan_edit", plan_id=plan.id)

    # GET request - show form with suggestions
    from core.services.planning_service import get_suggested_items_for_date

    # Get target date from query param, default to tomorrow
    date_param = request.GET.get("date")
    if date_param:
        try:
            target_date = datetime.strptime(date_param, "%Y-%m-%d").date()
        except ValueError:
            target_date = timezone.now().date() + timedelta(days=1)
    else:
        target_date = timezone.now().date() + timedelta(days=1)

    # Get suggested items for target date
    suggested_items = get_suggested_items_for_date(project, target_date)

    return render(
        request,
        "core/daily_plan_create.html",
        {
            "project": project,
            "min_date": timezone.now().date(),
            "target_date": target_date,
            "suggested_items": suggested_items,
            "has_suggestions": len(suggested_items) > 0,
        },
    )


@login_required
def daily_plan_edit(request, plan_id):
    """Edit a daily plan and its activities using forms and inline formset (Modules 12.5-12.7)."""
    if not _is_staffish(request.user):
        return HttpResponseForbidden("Access denied")

    from django.utils.translation import gettext as _

    from core.forms import DailyPlanForm, make_planned_activity_formset

    plan = get_object_or_404(DailyPlan.objects.select_related("project"), pk=plan_id)

    # Instantiate forms
    if request.method == "POST":
        action = request.POST.get("action")

        if action == "add_activity":
            try:
                from core.models import ActivityTemplate, PlannedActivity, ScheduleItem

                # Extract data
                template_id = request.POST.get("activity_template")
                schedule_id = request.POST.get("schedule_item")
                title = request.POST.get("title")
                description = request.POST.get("description", "")
                hours = request.POST.get("estimated_hours")
                employee_ids = request.POST.getlist("assigned_employees")

                # Resolve relations
                template = ActivityTemplate.objects.get(pk=template_id) if template_id else None
                schedule = ScheduleItem.objects.get(pk=schedule_id) if schedule_id else None

                # Default title from template if not provided
                if not title and template:
                    title = template.name
                elif not title:
                    title = "New Activity"

                # Create activity
                activity = PlannedActivity.objects.create(
                    daily_plan=plan,
                    title=title,
                    description=description,
                    activity_template=template,
                    schedule_item=schedule,
                    estimated_hours=hours if hours else None,
                    order=plan.activities.count() + 1,
                )

                # Assign employees
                if employee_ids:
                    activity.assigned_employees.set(employee_ids)

                messages.success(request, _("Activity added successfully"))
                return redirect("daily_plan_edit", plan_id=plan.id)

            except Exception as e:
                messages.error(request, f"Error adding activity: {str(e)}")
                return redirect("daily_plan_edit", plan_id=plan.id)

        elif action == "edit_activity":
            try:
                from core.models import ActivityTemplate, PlannedActivity, ScheduleItem

                activity_id = request.POST.get("activity_id")
                activity = PlannedActivity.objects.get(pk=activity_id, daily_plan=plan)

                # Update fields
                title = request.POST.get("title", "").strip()
                if title:
                    activity.title = title
                activity.description = request.POST.get("description", "")

                hours = request.POST.get("estimated_hours")
                activity.estimated_hours = hours if hours else None

                # Status
                new_status = request.POST.get("status", "")
                if new_status in dict(PlannedActivity.STATUS_CHOICES):
                    activity.status = new_status

                # Progress
                progress = request.POST.get("progress_percentage", "")
                if progress:
                    activity.progress_percentage = min(100, max(0, int(progress)))

                # Template & schedule (optional)
                template_id = request.POST.get("activity_template")
                activity.activity_template = (
                    ActivityTemplate.objects.get(pk=template_id) if template_id else None
                )

                schedule_id = request.POST.get("schedule_item")
                activity.schedule_item = (
                    ScheduleItem.objects.get(pk=schedule_id) if schedule_id else None
                )

                # Start/end times
                start_time = request.POST.get("start_time", "")
                end_time = request.POST.get("end_time", "")
                activity.start_time = start_time if start_time else None
                activity.end_time = end_time if end_time else None

                activity.save()

                # Assign employees (M2M)
                employee_ids = request.POST.getlist("assigned_employees")
                activity.assigned_employees.set(employee_ids)

                messages.success(request, _("Activity updated successfully"))
                return redirect("daily_plan_edit", plan_id=plan.id)

            except PlannedActivity.DoesNotExist:
                messages.error(request, _("Activity not found"))
                return redirect("daily_plan_edit", plan_id=plan.id)
            except Exception as e:
                messages.error(request, f"Error updating activity: {str(e)}")
                return redirect("daily_plan_edit", plan_id=plan.id)

        elif action == "submit":
            if plan.activities.exists():
                plan.status = "PUBLISHED"
                plan.save(update_fields=["status"])

                # Notify each assigned employee
                notified_users = set()
                for activity in plan.activities.prefetch_related("assigned_employees__user"):
                    for emp in activity.assigned_employees.all():
                        if emp.user and emp.user_id not in notified_users:
                            notified_users.add(emp.user_id)
                            Notification.objects.create(
                                user=emp.user,
                                project=plan.project,
                                notification_type="daily_plan",
                                title=_("New Daily Plan: %(project)s") % {"project": plan.project.name},
                                message=_("A plan for %(date)s has been published. Check your assigned activities.") % {"date": plan.plan_date.strftime("%b %d")},
                                related_object_type="DailyPlan",
                                related_object_id=plan.id,
                                link_url=f"/planning/{plan.id}/",
                            )

                messages.success(request, _("Plan submitted successfully. %(count)s employees notified.") % {"count": len(notified_users)})
            else:
                messages.error(request, _("Cannot submit empty plan"))
            return redirect("daily_plan_edit", plan_id=plan.id)

        elif action == "copy_yesterday_team":
            # ✅ Copy team assignments from yesterday's plan
            from datetime import timedelta

            yesterday_date = plan.plan_date - timedelta(days=1)

            try:
                yesterday_plan = DailyPlan.objects.filter(
                    project=plan.project, plan_date=yesterday_date
                ).first()

                if not yesterday_plan:
                    messages.warning(
                        request, _(f"No plan found for {yesterday_date.strftime('%Y-%m-%d')}")
                    )
                    return redirect("daily_plan_edit", plan_id=plan.id)

                # Get yesterday's activities with employees
                yesterday_activities = yesterday_plan.activities.prefetch_related(
                    "assigned_employees"
                ).all()

                if not yesterday_activities:
                    messages.warning(request, _("Yesterday's plan has no activities"))
                    return redirect("daily_plan_edit", plan_id=plan.id)

                # Collect all unique employees from yesterday
                all_employees = set()
                for activity in yesterday_activities:
                    all_employees.update(activity.assigned_employees.all())

                if not all_employees:
                    messages.warning(request, _("Yesterday's plan has no employees assigned"))
                    return redirect("daily_plan_edit", plan_id=plan.id)

                # Apply to all today's activities
                count = 0
                for activity in plan.activities.all():
                    activity.assigned_employees.set(all_employees)
                    count += 1

                employee_names = ", ".join([f"{e.first_name}" for e in all_employees])
                messages.success(
                    request,
                    _(
                        f"✅ Copied {len(all_employees)} employees ({employee_names}) to {count} activities"
                    ),
                )
                return redirect("daily_plan_edit", plan_id=plan.id)

            except Exception as e:
                messages.error(request, f"❌ Error copying team: {str(e)}")
                return redirect("daily_plan_edit", plan_id=plan.id)

        elif action == "check_materials":
            # Mock material check for now or call method on activities
            count = 0
            for activity in plan.activities.all():
                if hasattr(activity, "check_materials"):
                    activity.check_materials()
                    count += 1
            messages.success(request, _(f"Checked materials for {count} activities"))
            return redirect("daily_plan_edit", plan_id=plan.id)

        # Fallback to standard form processing if no specific action
        form = DailyPlanForm(request.POST, instance=plan)
        formset = make_planned_activity_formset(plan, data=request.POST, files=request.FILES)
        if form.is_valid() and formset.is_valid():
            form.save()  # Handles weather fetch + estimated hours recalculation
            formset.save()
            messages.success(request, _("Plan actualizado"))
            # Workflow quick actions via hidden field 'transition'
            transition = request.POST.get("transition")
            if transition:
                # Attempt state transition
                try:
                    desired = transition
                    current = plan.status
                    allowed = {
                        "DRAFT": ["PUBLISHED", "SKIPPED"],
                        "PUBLISHED": ["IN_PROGRESS", "SKIPPED"],
                        "IN_PROGRESS": ["COMPLETED"],
                    }
                    if desired != current and desired in allowed.get(current, []):
                        plan.status = desired
                        plan.save(update_fields=["status"])
                        messages.success(request, _("Transición de estado exitosa"))
                    else:
                        messages.warning(request, _("Transición inválida"))
                except Exception:
                    messages.error(request, _("Error aplicando transición de estado"))
            return redirect("daily_plan_edit", plan_id=plan.id)
        else:
            messages.error(request, _("Revisa errores en el formulario"))
    else:
        form = DailyPlanForm(instance=plan)
        formset = make_planned_activity_formset(plan)

    # For display contexts
    productivity = plan.calculate_productivity_score()
    activities = plan.activities.prefetch_related("assigned_employees").order_by("order")

    # Data for Add Activity modal dropdowns
    from core.models import ActivityTemplate, ScheduleItem

    available_templates = ActivityTemplate.objects.filter(
        is_active=True, is_latest_version=True
    ).order_by("category", "name")
    schedule_items = ScheduleItem.objects.filter(
        project=plan.project
    ).order_by("order")

    # Only show explicitly created Employee records (no auto-creation)
    # Employees must be created via Django Admin or management commands
    employees = Employee.objects.filter(is_active=True).order_by("first_name", "last_name")

    context = {
        "plan": plan,
        "form": form,
        "formset": formset,
        "activities": activities,
        "productivity_score": productivity,
        "can_convert": plan.status == "PUBLISHED",
        "can_start": plan.status == "PUBLISHED",
        "can_complete": plan.status == "IN_PROGRESS",
        "available_templates": available_templates,
        "schedule_items": schedule_items,
        "employees": employees,
    }
    return render(request, "core/daily_plan_edit.html", context)


@login_required
def daily_plan_delete_activity(request, activity_id):
    """
    Delete a planned activity
    """
    if not _is_staffish(request.user):
        return HttpResponseForbidden("Access denied")

    activity = get_object_or_404(PlannedActivity, pk=activity_id)
    plan_id = activity.daily_plan.id

    if request.method == "POST":
        activity.delete()
        messages.success(request, _("Activity deleted"))

    return redirect("daily_plan_edit", plan_id=plan_id)


@login_required
def activity_add_comment(request, activity_id):
    """Add a comment to a planned activity. Any logged-in user can comment."""
    from django.utils.translation import gettext as _

    from core.models import ActivityComment

    activity = get_object_or_404(
        PlannedActivity.objects.select_related("daily_plan__project"), pk=activity_id
    )

    if request.method == "POST":
        content = request.POST.get("content", "").strip()
        if not content:
            messages.error(request, _("Comment cannot be empty"))
            return redirect("daily_plan_detail", plan_id=activity.daily_plan_id)

        photo = request.FILES.get("photo")

        ActivityComment.objects.create(
            activity=activity,
            author=request.user,
            content=content,
            photo=photo,
        )

        # Notify the plan creator if commenter is not the creator
        plan = activity.daily_plan
        if request.user != plan.created_by and plan.created_by:
            Notification.objects.create(
                user=plan.created_by,
                project=plan.project,
                notification_type="daily_plan",
                title=_("New comment on: %(activity)s") % {"activity": activity.title[:50]},
                message=f"{request.user.get_full_name() or request.user.username}: {content[:100]}",
                related_object_type="DailyPlan",
                related_object_id=plan.id,
                link_url=f"/planning/{plan.id}/",
            )

        messages.success(request, _("Comment added"))
        return redirect("daily_plan_detail", plan_id=activity.daily_plan_id)

    return redirect("daily_plan_detail", plan_id=activity.daily_plan_id)


@login_required
def employee_morning_dashboard(request):
    """
    Dashboard for employees to see their daily plan
    Shows today's assigned activities with all details
    """
    try:
        employee = request.user.employee
    except Exception:
        messages.error(request, _("You are not registered as an employee"))
        return redirect("dashboard")

    today = timezone.now().date()

    # Get today's activities assigned to this employee
    todays_activities = (
        PlannedActivity.objects.filter(
            daily_plan__plan_date=today,
            assigned_employees=employee,
            status__in=["PENDING", "IN_PROGRESS"],
        )
        .select_related("daily_plan__project", "activity_template")
        .prefetch_related("assigned_employees")
        .order_by("order")
    )

    context = {
        "employee": employee,
        "today": today,
        "activities": todays_activities,
    }

    return render(request, "core/employee_morning_dashboard.html", context)


@login_required
def activity_complete(request, activity_id):
    """
    Mark an activity as complete with photos
    """
    activity = get_object_or_404(PlannedActivity, pk=activity_id)

    try:
        employee = request.user.employee
    except Exception:
        messages.error(request, _("You are not registered as an employee"))
        return redirect("dashboard")

    # Check if employee is assigned
    if not activity.assigned_employees.filter(id=employee.id).exists():
        return HttpResponseForbidden("You are not assigned to this activity")

    if request.method == "POST":
        progress = int(request.POST.get("progress", 100))
        notes = request.POST.get("notes", "")

        # Handle photo uploads (simplified - you'll need proper file handling)
        photos = []
        uploaded_files = request.FILES.getlist("photos")
        # Basic file persistence into MEDIA_ROOT/activity_completions/<activity_id>/
        import os

        from django.conf import settings

        activity_dir = os.path.join(settings.MEDIA_ROOT, "activity_completions", str(activity.id))
        os.makedirs(activity_dir, exist_ok=True)
        for f in uploaded_files:
            safe_name = f.name.replace(" ", "_")
            dest_path = os.path.join(activity_dir, safe_name)
            with open(dest_path, "wb+") as dest:
                for chunk in f.chunks():
                    dest.write(chunk)
            # Store relative media URL path for later display
            rel_path = os.path.join("activity_completions", str(activity.id), safe_name).replace(
                "\\", "/"
            )
            photos.append(rel_path)

        # Create completion record
        ActivityCompletion.objects.create(
            planned_activity=activity,
            completed_by=employee,
            progress_percentage=progress,
            employee_notes=notes,
            completion_photos=photos,
        )

        # Update activity status
        activity.status = "COMPLETED"
        activity.progress_percentage = progress
        activity.save()

        # If all activities for a Schedule item are complete, update Schedule
        if activity.schedule_item:
            related_activities = PlannedActivity.objects.filter(
                schedule_item=activity.schedule_item
            )
            if all(a.status == "COMPLETED" for a in related_activities):
                activity.schedule_item.progress = 100
                activity.schedule_item.save()

        messages.success(
            request, _("Activity '%(title)s' marked as complete!") % {"title": activity.title}
        )
        return redirect("employee_morning_dashboard")

    # GET request - show completion form
    context = {
        "activity": activity,
        "employee": employee,
    }

    return render(request, "core/activity_complete.html", context)


@login_required
def sop_library(request):
    """
    Browse and search Activity Templates (SOPs) - Q13.3 enhanced search
    """
    if not _is_staffish(request.user):
        return HttpResponseForbidden("Access denied")

    category = request.GET.get("category", "")
    search = request.GET.get("search", "")
    duration_min = request.GET.get("duration_min", "")
    duration_max = request.GET.get("duration_max", "")

    templates = ActivityTemplate.objects.filter(is_active=True)

    if category:
        templates = templates.filter(category=category)

    # ACTIVITY 1: Enhanced keyword search (Q13.3)
    if search:
        templates = templates.filter(
            Q(name__icontains=search)
            | Q(description__icontains=search)
            | Q(tips__icontains=search)
            | Q(materials_needed__icontains=search)
            | Q(special_requirements__icontains=search)
        )

    # ACTIVITY 1: Duration filter (Q13.3)
    if duration_min:
        with contextlib.suppress(ValueError):
            templates = templates.filter(estimated_duration__gte=float(duration_min))

    if duration_max:
        with contextlib.suppress(ValueError):
            templates = templates.filter(estimated_duration__lte=float(duration_max))

    templates = templates.order_by("category", "name")

    context = {
        "templates": templates,
        "categories": ActivityTemplate.CATEGORY_CHOICES,
        "selected_category": category,
        "search_query": search,
        "duration_min": duration_min,
        "duration_max": duration_max,
    }

    return render(request, "core/sop_library.html", context)


@login_required
def sop_create_edit(request, template_id=None):
    """
    Create or edit an Activity Template (SOP)
    """
    if not _is_staffish(request.user):
        return HttpResponseForbidden("Access denied")

    instance = None
    if template_id:
        instance = get_object_or_404(ActivityTemplate, pk=template_id)

    if request.method == "POST":
        form = ActivityTemplateForm(request.POST, request.FILES, instance=instance)
        if form.is_valid():
            sop = form.save(commit=False)
            if not instance:
                sop.created_by = request.user
            sop.save()
            form.save_m2m()

            # Handle file uploads for reference files
            uploaded_files = request.FILES.getlist("reference_files")
            if uploaded_files:
                from core.models import SOPReferenceFile

                for f in uploaded_files:
                    SOPReferenceFile.objects.create(sop=sop, file=f)

            messages.success(request, _("SOP saved successfully!"))
            return redirect("sop_library")
    else:
        form = ActivityTemplateForm(instance=instance)

    context = {
        "form": form,
        "editing": bool(instance),
        "sop": instance,
    }
    return render(request, "core/sop_creator.html", context)


@login_required
def sop_create_wizard(request, template_id=None):
    """
    Wizard-style SOP creator with step-by-step guidance (NEW IMPROVED VERSION)
    """
    if not _is_staffish(request.user):
        return HttpResponseForbidden("Access denied")

    instance = None
    if template_id:
        instance = get_object_or_404(ActivityTemplate, pk=template_id)

    if request.method == "POST":
        # Process form data
        name = request.POST.get("name")
        category = request.POST.get("category")
        description = request.POST.get("description", "")
        tips = request.POST.get("tips", "")
        common_errors = request.POST.get("common_errors", "")
        video_url = request.POST.get("video_url", "")
        is_active = request.POST.get("is_active") == "on"

        # Parse JSON fields
        import json

        steps = json.loads(request.POST.get("steps", "[]"))
        materials_list = json.loads(request.POST.get("materials_list", "[]"))
        tools_list = json.loads(request.POST.get("tools_list", "[]"))

        # Calculate time estimate
        time_hours = float(request.POST.get("time_hours", 0))
        time_minutes = float(request.POST.get("time_minutes", 0))
        time_estimate = time_hours + (time_minutes / 60.0)

        # Create or update SOP
        if instance:
            sop = instance
            sop.name = name
            sop.category = category
            sop.description = description
            sop.tips = tips
            sop.common_errors = common_errors
            sop.video_url = video_url
            sop.is_active = is_active
            sop.steps = steps
            sop.materials_list = materials_list
            sop.tools_list = tools_list
            sop.time_estimate = time_estimate if time_estimate > 0 else None
            sop.save()
        else:
            sop = ActivityTemplate.objects.create(
                name=name,
                category=category,
                description=description,
                tips=tips,
                common_errors=common_errors,
                video_url=video_url,
                is_active=is_active,
                steps=steps,
                materials_list=materials_list,
                tools_list=tools_list,
                time_estimate=time_estimate if time_estimate > 0 else None,
                created_by=request.user,
            )

        # Handle file uploads
        uploaded_files = request.FILES.getlist("reference_files")
        if uploaded_files:
            from core.models import SOPReferenceFile

            for f in uploaded_files:
                SOPReferenceFile.objects.create(sop=sop, file=f)

        messages.success(request, _("✨ SOP creado exitosamente!"))
        return redirect("sop_library")

    # GET request - show wizard
    form = ActivityTemplateForm(instance=instance)
    context = {
        "form": form,
        "editing": bool(instance),
        "sop": instance,
    }
    return render(request, "core/sop_creator_wizard.html", context)


# ===========================
# MINUTAS / PROJECT TIMELINE
# ===========================





@login_required
def daily_plan_timeline(request, plan_id):
    """Timeline view for a daily plan (Module 12.8)."""
    if not _is_staffish(request.user):
        return HttpResponseForbidden("Access denied")

    from core.api.serializers import PlannedActivitySerializer

    plan = get_object_or_404(DailyPlan.objects.select_related("project", "created_by"), pk=plan_id)

    # Fetch surrounding plans (e.g., +/- 15 days) for context
    # Allow overriding the center date via query param to navigate
    focus_date_str = request.GET.get("focus_date")
    if focus_date_str:
        try:
            focus_date = datetime.strptime(focus_date_str, "%Y-%m-%d").date()
        except ValueError:
            focus_date = plan.plan_date
    else:
        focus_date = plan.plan_date

    start_date = focus_date - timedelta(days=15)
    end_date = focus_date + timedelta(days=15)

    related_plans = DailyPlan.objects.filter(
        project=plan.project, plan_date__range=[start_date, end_date]
    ).prefetch_related("activities")

    all_activities = []
    for p in related_plans:
        p_activities = p.activities.all().order_by("start_time", "order")
        # We need to inject the plan_date into the activity data for the frontend
        serialized = PlannedActivitySerializer(p_activities, many=True).data
        for item in serialized:
            item["plan_date"] = p.plan_date.isoformat()
        all_activities.extend(serialized)

    # Fetch employees for assignment dropdown
    from core.models import Employee

    employees = Employee.objects.filter(is_active=True).values("id", "first_name", "last_name")
    employees_json = json.dumps(list(employees), default=str)

    activities_json = json.dumps(all_activities, default=str)

    # Pass date range info
    timeline_config = {
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "focus_date": focus_date.isoformat(),
    }

    return render(
        request,
        "core/daily_plan_timeline.html",
        {
            "plan": plan,
            "activities_json": activities_json,
            "employees_json": employees_json,
            "timeline_config": json.dumps(timeline_config),
        },
    )


# =============================================================================
# FINANCIAL SYSTEM - Reorganized Views
# =============================================================================

