"""Task views — CRUD, wizard, command center, time tracking."""
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
def agregar_tarea(request, project_id):
    """
    Permite a clientes (y staff) agregar touch-ups usando el modelo TouchUp V2.
    - Cliente crea → se auto-asigna al primer admin activo.
    - Staff crea → puede asignar directamente a un empleado.
    - Se envían notificaciones a admins y PMs.
    """
    from core.models import ClientProjectAccess, TouchUp, TouchUpPhoto

    project = get_object_or_404(Project, id=project_id)

    # Verificar acceso
    profile = getattr(request.user, "profile", None)
    has_access = ClientProjectAccess.objects.filter(user=request.user, project=project).exists()
    if profile and profile.role == "client":
        if not (has_access or project.client == request.user.username):
            messages.error(request, _("You don't have access to this project."))
            return redirect("dashboard_client")
    elif not request.user.is_staff and not has_access:
        messages.error(request, _("Access denied."))
        return redirect("dashboard")

    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        description = request.POST.get("description", "").strip()

        if not title:
            messages.error(request, _("Title is required."))
            return redirect("client_project_view", project_id=project_id)

        # Floor plan location (optional)
        floor_plan_id = request.POST.get("floor_plan_id") or None
        pin_x = request.POST.get("pin_x") or None
        pin_y = request.POST.get("pin_y") or None

        floor_plan_obj = None
        if floor_plan_id:
            from core.models import FloorPlan
            floor_plan_obj = FloorPlan.objects.filter(
                id=floor_plan_id, project=project
            ).first()

        # Create TouchUp V2 (not legacy Task)
        touchup_kwargs = dict(
            project=project,
            title=title,
            description=description,
            status="open",
            priority=request.POST.get("priority", "medium") or "medium",
            created_by=request.user,
        )
        if floor_plan_obj and pin_x and pin_y:
            from decimal import Decimal, InvalidOperation
            try:
                px = Decimal(pin_x)
                py = Decimal(pin_y)
                if 0 <= px <= 1 and 0 <= py <= 1:
                    touchup_kwargs["floor_plan"] = floor_plan_obj
                    touchup_kwargs["pin_x"] = px
                    touchup_kwargs["pin_y"] = py
            except (InvalidOperation, ValueError):
                pass  # Skip invalid pin data, create without location

        touchup = TouchUp.objects.create(**touchup_kwargs)

        # Handle photo uploads (single legacy field + multiple)
        photos = request.FILES.getlist("photos") or []
        single_image = request.FILES.get("image")
        if single_image:
            photos.insert(0, single_image)

        for photo_file in photos:
            TouchUpPhoto.objects.create(
                touchup=touchup,
                image=photo_file,
                phase="before",
                uploaded_by=request.user,
            )

        # Auto-assign to first active admin (superuser or staff with admin role)
        admin_user = User.objects.filter(
            is_active=True, is_superuser=True
        ).first()
        if not admin_user:
            admin_user = User.objects.filter(
                is_active=True, is_staff=True, profile__role="admin"
            ).first()

        # Notify admins and PMs
        admins_and_pms = User.objects.filter(
            is_active=True
        ).filter(
            Q(is_superuser=True) | Q(profile__role__in=["admin", "project_manager"])
        ).distinct()

        creator_name = request.user.get_full_name() or request.user.username
        for u in admins_and_pms:
            if u != request.user:
                Notification.objects.create(
                    user=u,
                    notification_type="task_created",
                    title=_("New Touch-Up: %(title)s") % {"title": title[:60]},
                    message=_("%(creator)s created a touch-up in %(project)s") % {
                        "creator": creator_name,
                        "project": project.name,
                    },
                    related_object_type="TouchUp",
                    related_object_id=touchup.id,
                    link_url=f"/projects/{project.id}/touchups-v2/{touchup.id}/",
                )

        messages.success(
            request,
            _("Touch-up '%(title)s' created successfully. The team has been notified.") % {"title": title},
        )
        return redirect("client_project_view", project_id=project_id)



@login_required
def task_list_view(request, project_id: int):
    from datetime import timedelta

    project = get_object_or_404(Project, pk=project_id)
    
    # SECURITY: Check project access
    has_access, redirect_url = _check_user_project_access(request.user, project)
    if not has_access:
        messages.error(request, _("Access denied."))
        return redirect(redirect_url or "dashboard")
    
    tasks = (
        Task.objects.filter(project=project)
        .select_related("assigned_to")
        .prefetch_related("dependencies")
        if Task
        else []
    )

    # Apply filters from query parameters
    status_filter = request.GET.get("status")
    priority_filter = request.GET.get("priority")
    assigned_filter = request.GET.get("assigned_to")
    overdue_filter = request.GET.get("overdue")

    if status_filter:
        tasks = tasks.filter(status=status_filter)

    if priority_filter:
        tasks = tasks.filter(priority=priority_filter)

    if assigned_filter:
        tasks = tasks.filter(assigned_to_id=assigned_filter)

    today = date.today()
    if overdue_filter == "yes":
        # Tasks overdue (due_date < today and not completed)
        tasks = tasks.filter(due_date__lt=today).exclude(status="Completed")
    elif overdue_filter == "today":
        # Tasks due today
        tasks = tasks.filter(due_date=today)
    elif overdue_filter == "week":
        # Tasks due this week
        week_end = today + timedelta(days=7)
        tasks = tasks.filter(due_date__lte=week_end, due_date__gte=today)

    tasks = tasks.order_by("-id")

    # Get employees for filter dropdown (only actual employees, not clients)
    employees = Employee.objects.filter(is_active=True).order_by("first_name", "last_name")

    can_create = request.user.is_staff
    form = None
    try:
        from core.forms import TaskForm as TaskFormModel
    except Exception:
        task_form_cls = None
    else:
        task_form_cls = TaskFormModel
    if can_create and task_form_cls:
        if request.method == "POST":
            form = task_form_cls(request.POST, request.FILES)
            if form.is_valid():
                inst = form.save(commit=False)
                inst.created_by = request.user
                inst.project = project
                inst.save()
                form.save_m2m()  # Save dependencies
                messages.success(request, "Tarea creada.")
                return redirect("task_list", project_id=project.id)
        else:
            form = task_form_cls(initial={"project": project})

    return render(
        request,
        "core/task_list.html",
        {
            "project": project,
            "tasks": tasks,
            "form": form,
            "can_create": can_create,
            "employees": employees,
            "today": today,
        },
    )



@login_required
def task_detail(request, task_id: int):
    """Detalle de una tarea.

    Permisos:
    - Staff: puede ver cualquier tarea.
    - Empleado: solo tareas asignadas a su Employee.
    """
    from datetime import date

    task = get_object_or_404(Task, pk=task_id)
    employee = Employee.objects.filter(user=request.user).first()

    if not request.user.is_staff and (not employee or task.assigned_to_id != employee.id):
        messages.error(request, gettext("Sin permiso para ver esta tarea."))
        return redirect("task_list_all")

    return render(request, "core/task_detail.html", {
        "task": task,
        "employee": employee,
        "today": date.today(),
    })



@login_required
def task_edit_view(request, task_id: int):
    task = get_object_or_404(Task, pk=task_id)
    if not request.user.is_staff:
        messages.error(request, "Solo staff puede editar tareas.")
        return redirect("task_detail", task_id=task.id)
    from core.forms import TaskForm

    if request.method == "POST":
        form = TaskForm(request.POST, request.FILES, instance=task)
        if form.is_valid():
            form.save()
            messages.success(request, "Tarea actualizada.")
            # Redirect to command center with project filter
            return redirect(f"/tasks/command-center/?project={task.project_id}")
    else:
        form = TaskForm(instance=task)
    return render(request, "core/task_form.html", {"form": form, "task": task, "edit": True})



@login_required
def task_delete_view(request, task_id: int):
    task = get_object_or_404(Task, pk=task_id)
    if not request.user.is_staff:
        messages.error(request, "Solo staff puede eliminar tareas.")
        return redirect("task_detail", task_id=task.id)
    if request.method == "POST":
        project_id = task.project_id
        task.delete()
        messages.success(request, "Tarea eliminada.")
        # Redirect to command center with project filter
        return redirect(f"/tasks/command-center/?project={project_id}")
    return render(request, "core/task_confirm_delete.html", {"task": task})



@login_required
def task_list_all(request):
    """DEPRECATED: Redirect to Task Command Center."""
    return redirect("task_command_center")



@login_required
def task_create_wizard(request):
    """
    Task Creation Wizard - Standalone page for creating tasks.
    
    Opens task_form.html with project selection enabled.
    Staff-only view.
    """
    if not request.user.is_staff:
        messages.error(request, gettext("You don't have permission to create tasks"))
        return redirect("task_command_center")
    
    from core.forms import TaskForm
    
    # Get active projects
    projects = Project.objects.filter(is_archived=False).order_by("name")
    
    # Handle pre-selected project from query param
    project_id = request.GET.get("project")
    initial_project = None
    if project_id:
        try:
            initial_project = Project.objects.get(id=project_id, is_archived=False)
        except Project.DoesNotExist:
            pass
    
    if request.method == "POST":
        form = TaskForm(request.POST, request.FILES)
        if form.is_valid():
            task = form.save(commit=False)
            task.created_by = request.user
            task.save()
            form.save_m2m()  # Save dependencies
            
            messages.success(request, gettext("Task created successfully"))
            
            # Redirect back to command center or project task list
            if task.project:
                return redirect(f"/tasks/command-center/?project={task.project.id}")
            return redirect("task_command_center")
        else:
            messages.error(request, gettext("Please correct the errors below"))
    else:
        initial = {}
        if initial_project:
            initial["project"] = initial_project
        form = TaskForm(initial=initial)
    
    return render(
        request,
        "core/task_form.html",
        {
            "form": form,
            "projects": projects,
            "edit": False,
            "title": gettext("Create New Task"),
        },
    )



@login_required
def task_command_center(request):
    """
    Task Command Center - Centro de control unificado de tareas.
    
    Features:
    - Selector de proyecto con filtrado
    - Estadísticas en tiempo real
    - Filtros avanzados (estado, prioridad, asignado, búsqueda)
    - Creación de tareas via modal
    - Acciones bulk (asignar, cambiar estado/prioridad)
    - Vista detallada de tareas con pines/touchups integrados
    
    Permisos:
    - Staff/Admin: Ve todas las tareas, puede crear/editar/asignar
    - Empleado: Solo ve sus tareas asignadas, puede actualizar estado
    """
    from django.db.models import Count, Q
    from core.notifications import notify_task_created
    
    is_staff = request.user.is_staff or request.user.is_superuser
    today = timezone.localdate()
    
    # Get current employee if exists
    current_employee = Employee.objects.filter(user=request.user).first()
    current_employee_id = current_employee.id if current_employee else None
    
    # Handle POST - Create Task
    if request.method == "POST" and request.POST.get("action") == "create":
        project_id = request.POST.get("project")
        title = request.POST.get("title", "").strip()
        
        if not project_id or not title:
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse({"error": gettext("Project and title are required")}, status=400)
            messages.error(request, gettext("Project and title are required"))
            return redirect("task_command_center")
        
        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse({"error": gettext("Project not found")}, status=404)
            messages.error(request, gettext("Project not found"))
            return redirect("task_command_center")
        
        # Create task
        task = Task.objects.create(
            project=project,
            title=title,
            description=request.POST.get("description", ""),
            priority=request.POST.get("priority", "medium"),
            due_date=request.POST.get("due_date") or None,
            is_touchup=request.POST.get("is_touchup") == "true",
            created_by=request.user,
            status="Pending",
        )
        
        # Handle image upload
        if request.FILES.get("image"):
            task.image = request.FILES["image"]
            task.save()
        
        # Assign employee if provided (staff only)
        if is_staff and request.POST.get("assigned_to"):
            try:
                emp = Employee.objects.get(id=request.POST.get("assigned_to"))
                task.assigned_to = emp
                task.save()
                # Send notification
                notify_task_created(task, request.user)
            except Employee.DoesNotExist:
                pass
        
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"success": True, "task_id": task.id})
        
        messages.success(request, gettext("Task created successfully"))
        return redirect("task_command_center")
    
    # Get projects for selector
    if is_staff:
        projects = Project.objects.filter(is_archived=False).order_by("name")
    else:
        # Employees see projects where they have assignments or tasks
        projects = Project.objects.filter(
            Q(tasks__assigned_to=current_employee) |
            Q(resource_assignments__employee=current_employee)
        ).distinct().filter(is_archived=False).order_by("name")
    
    # Selected project filter
    selected_project_id = request.GET.get("project")
    selected_project = None
    if selected_project_id:
        try:
            selected_project = Project.objects.get(id=selected_project_id)
        except Project.DoesNotExist:
            pass
    
    # Base queryset
    tasks_qs = Task.objects.select_related("project", "assigned_to").prefetch_related("dependencies")
    
    # Apply permissions filter
    if is_staff:
        # Staff sees all tasks
        if selected_project:
            tasks_qs = tasks_qs.filter(project=selected_project)
    else:
        # Employees see only their assigned tasks
        tasks_qs = tasks_qs.filter(assigned_to=current_employee)
        if selected_project:
            tasks_qs = tasks_qs.filter(project=selected_project)
    
    tasks = tasks_qs.order_by("-created_at")
    
    # Calculate statistics
    stats = {
        "total": tasks.count(),
        "pending": tasks.filter(status="Pending").count(),
        "in_progress": tasks.filter(status="In Progress").count(),
        "completed": tasks.filter(status="Completed").count(),
        "overdue": tasks.filter(due_date__lt=today).exclude(status__in=["Completed", "Cancelled"]).count(),
        "unassigned": tasks.filter(assigned_to__isnull=True).count() if is_staff else 0,
        "touchups": tasks.filter(is_touchup=True).count(),
        "my_tasks": tasks.filter(assigned_to=current_employee).count() if current_employee else 0,
    }
    
    # Get employees for assignment dropdown (staff only)
    employees = Employee.objects.filter(is_active=True).order_by("first_name") if is_staff else []
    
    return render(
        request,
        "core/task_command_center.html",
        {
            "tasks": tasks,
            "projects": projects,
            "selected_project": selected_project,
            "stats": stats,
            "employees": employees,
            "is_staff": is_staff,
            "today": today,
            "current_employee_id": current_employee_id,
        },
    )



# ===========================
# ACTIVITY 1: NEW TIME TRACKING ENDPOINTS (Q11.13)
# ===========================


@login_required
def task_start_tracking(request, task_id):
    """AJAX endpoint to start time tracking on a task."""
    if request.method != "POST":
        return JsonResponse({"error": gettext("POST required")}, status=405)

    task = get_object_or_404(Task, id=task_id)
    employee = Employee.objects.filter(user=request.user).first()

    # Check permission
    if not (request.user.is_staff or (employee and task.assigned_to == employee)):
        return JsonResponse({"error": gettext("Sin permiso")}, status=403)

    # Check if task can start (dependencies)
    if not task.can_start():
        incomplete_deps = task.dependencies.filter(status__in=["pending", "in_progress"])
        dep_names = ", ".join([d.title for d in incomplete_deps])
        return JsonResponse(
            {
                "error": gettext("No se puede iniciar. Dependencias incompletas: %(deps)s")
                % {"deps": dep_names}
            },
            status=400,
        )

    # Start tracking
    if task.start_tracking():
        return JsonResponse(
            {
                "success": True,
                "started_at": task.started_at.isoformat() if task.started_at else None,
                "message": "Seguimiento de tiempo iniciado",
            }
        )
    else:
        return JsonResponse({"error": gettext("Ya hay un seguimiento activo")}, status=400)



@login_required
def task_stop_tracking(request, task_id):
    """AJAX endpoint to stop time tracking on a task."""
    if request.method != "POST":
        return JsonResponse({"error": gettext("POST required")}, status=405)

    task = get_object_or_404(Task, id=task_id)
    employee = Employee.objects.filter(user=request.user).first()

    # Check permission
    if not (request.user.is_staff or (employee and task.assigned_to == employee)):
        return JsonResponse({"error": gettext("Sin permiso")}, status=403)

    # Stop tracking
    elapsed = task.stop_tracking()
    if elapsed is not None:
        return JsonResponse(
            {
                "success": True,
                "elapsed_seconds": elapsed,
                "total_hours": task.get_time_tracked_hours(),
                "message": f"Seguimiento detenido. {elapsed} segundos agregados.",
            }
        )
    else:
        return JsonResponse({"error": gettext("No hay seguimiento activo")}, status=400)


