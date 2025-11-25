"""
Vistas administrativas para gestión completa del sistema
Replica funcionalidad de Django Admin con interfaz Kibray
"""
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.contrib.admin.models import LogEntry
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q, Count, Sum
from decimal import Decimal
from django.core.paginator import Paginator
from django.utils.translation import gettext as _
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from functools import wraps

from core.models import (
    Project, Expense, Income, TimeEntry, Schedule, 
    Task, ChangeOrder, FloorPlan, DamageReport, Profile
)


def admin_required(view_func):
    """Decorador para verificar que el usuario es admin o superuser"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not (request.user.is_staff or request.user.is_superuser):
            messages.error(request, _("No tienes permisos para acceder a esta sección."))
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return login_required(wrapper)


# ============================================================
# GESTIÓN DE USUARIOS
# ============================================================

@admin_required
def admin_users_list(request):
    """Lista de todos los usuarios con filtros y búsqueda"""
    search = request.GET.get('search', '')
    role = request.GET.get('role', '')
    status = request.GET.get('status', '')
    
    users = User.objects.select_related('profile').order_by('-date_joined')
    
    # Filtros
    if search:
        users = users.filter(
            Q(username__icontains=search) |
            Q(email__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search)
        )
    
    if role:
        if role == 'superuser':
            users = users.filter(is_superuser=True)
        elif role == 'staff':
            users = users.filter(is_staff=True, is_superuser=False)
        elif role == 'client':
            users = users.filter(profile__role='client')
        elif role == 'employee':
            users = users.filter(profile__role='employee')
        elif role == 'contractor':
            users = users.filter(profile__role='contractor')
    
    if status == 'active':
        users = users.filter(is_active=True)
    elif status == 'inactive':
        users = users.filter(is_active=False)
    
    # Paginación
    paginator = Paginator(users, 25)
    page = request.GET.get('page', 1)
    users_page = paginator.get_page(page)
    
    context = {
        'users': users_page,
        'search': search,
        'role': role,
        'status': status,
        'total_users': users.count(),
        'active_users': users.filter(is_active=True).count(),
        'staff_users': users.filter(is_staff=True).count(),
    }
    return render(request, 'core/admin/users_list.html', context)


@admin_required
def admin_user_detail(request, user_id):
    """Detalle y edición de usuario"""
    user = get_object_or_404(User.objects.select_related('profile'), pk=user_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'update_info':
            user.first_name = request.POST.get('first_name', '')
            user.last_name = request.POST.get('last_name', '')
            user.email = request.POST.get('email', '')
            user.is_active = request.POST.get('is_active') == 'on'
            user.is_staff = request.POST.get('is_staff') == 'on'
            user.is_superuser = request.POST.get('is_superuser') == 'on'
            user.save()
            
            # Actualizar perfil
            if hasattr(user, 'profile'):
                user.profile.phone = request.POST.get('phone', '')
                user.profile.role = request.POST.get('role', 'employee')
                user.profile.save()
            
            messages.success(request, _("Usuario actualizado correctamente."))
            return redirect('admin_user_detail', user_id=user.id)
        
        elif action == 'change_password':
            new_password = request.POST.get('new_password')
            if new_password:
                user.set_password(new_password)
                user.save()
                messages.success(request, _("Contraseña cambiada correctamente."))
                return redirect('admin_user_detail', user_id=user.id)
        
        elif action == 'toggle_active':
            user.is_active = not user.is_active
            user.save()
            status = _("activado") if user.is_active else _("desactivado")
            messages.success(request, _("Usuario {status}.").format(status=status))
            return redirect('admin_user_detail', user_id=user.id)
    
    # Obtener proyectos del usuario (simplificado - Project no tiene assigned_to)
    projects = []
    
    # Obtener grupos del usuario
    user_groups = user.groups.all()
    
    # Obtener actividad reciente
    recent_activity = LogEntry.objects.filter(user=user).order_by('-action_time')[:20]
    
    context = {
        'user_obj': user,
        'projects': projects,
        'user_groups': user_groups,
        'recent_activity': recent_activity,
    }
    return render(request, 'core/admin/user_detail.html', context)


@admin_required
def admin_user_create(request):
    """Crear nuevo usuario"""
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        role = request.POST.get('role', 'employee')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, _("Ya existe un usuario con ese nombre."))
        elif not password:
            messages.error(request, _("Debes proporcionar una contraseña."))
        else:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                is_active=True
            )
            
            # Crear perfil
            Profile.objects.create(
                user=user,
                phone=request.POST.get('phone', ''),
                role=role
            )
            
            messages.success(request, _("Usuario creado correctamente."))
            return redirect('admin_user_detail', user_id=user.id)
    
    return render(request, 'core/admin/user_form.html')


@admin_required
@require_POST
def admin_user_delete(request, user_id):
    """Eliminar usuario"""
    user = get_object_or_404(User, pk=user_id)
    
    if user.id == request.user.id:
        messages.error(request, _("No puedes eliminarte a ti mismo."))
    elif user.is_superuser and not request.user.is_superuser:
        messages.error(request, _("No puedes eliminar un superusuario."))
    else:
        username = user.username
        user.delete()
        messages.success(request, _("Usuario '{username}' eliminado.").format(username=username))
    
    return redirect('admin_users_list')


# ============================================================
# GESTIÓN DE GRUPOS Y PERMISOS
# ============================================================

@admin_required
def admin_groups_list(request):
    """Lista de grupos"""
    groups = Group.objects.annotate(
        user_count=Count('user')
    ).order_by('name')
    
    context = {
        'groups': groups,
    }
    return render(request, 'core/admin/groups_list.html', context)


@admin_required
def admin_group_detail(request, group_id):
    """Detalle de grupo con gestión de permisos"""
    group = get_object_or_404(Group, pk=group_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'update_permissions':
            permission_ids = request.POST.getlist('permissions')
            group.permissions.set(permission_ids)
            messages.success(request, _("Permisos actualizados."))
            return redirect('admin_group_detail', group_id=group.id)
        
        elif action == 'update_name':
            group.name = request.POST.get('name')
            group.save()
            messages.success(request, _("Grupo actualizado."))
            return redirect('admin_group_detail', group_id=group.id)
    
    # Obtener todos los permisos organizados por content type
    all_permissions = Permission.objects.select_related('content_type').order_by(
        'content_type__app_label', 'content_type__model', 'codename'
    )
    
    group_permission_ids = set(group.permissions.values_list('id', flat=True))
    
    # Organizar permisos por modelo
    permissions_by_model = {}
    for perm in all_permissions:
        model_name = perm.content_type.model
        if model_name not in permissions_by_model:
            permissions_by_model[model_name] = {
                'label': perm.content_type.name,
                'permissions': []
            }
        permissions_by_model[model_name]['permissions'].append({
            'id': perm.id,
            'name': perm.name,
            'codename': perm.codename,
            'has_permission': perm.id in group_permission_ids
        })
    
    context = {
        'group': group,
        'permissions_by_model': permissions_by_model,
        'users': group.user_set.all(),
    }
    return render(request, 'core/admin/group_detail.html', context)


@admin_required
def admin_group_create(request):
    """Crear nuevo grupo"""
    if request.method == 'POST':
        name = request.POST.get('name')
        
        if Group.objects.filter(name=name).exists():
            messages.error(request, _("Ya existe un grupo con ese nombre."))
        else:
            group = Group.objects.create(name=name)
            messages.success(request, _("Grupo creado correctamente."))
            return redirect('admin_group_detail', group_id=group.id)
    
    return render(request, 'core/admin/group_form.html')


# ============================================================
# GESTIÓN DE MODELOS CORE
# ============================================================

@admin_required
def admin_model_list(request, model_name):
    """Vista genérica para listar cualquier modelo"""
    models_config = {
        'projects': {
            'model': Project,
            'fields': ['name', 'client', 'status', 'start_date', 'budget_total'],
            'title': _('Proyectos'),
        },
        'expenses': {
            'model': Expense,
            'fields': ['description', 'amount', 'date', 'project', 'category'],
            'title': _('Gastos'),
        },
        'income': {
            'model': Income,
            'fields': ['description', 'amount', 'date', 'project', 'category'],
            'title': _('Ingresos'),
        },
        'timeentries': {
            'model': TimeEntry,
            'fields': ['user', 'project', 'date', 'hours_worked', 'change_order'],
            'title': _('Entradas de Tiempo'),
        },
        'schedules': {
            'model': Schedule,
            'fields': ['project', 'task_name', 'assigned_to', 'start_date', 'end_date', 'status'],
            'title': _('Cronograma'),
        },
        'tasks': {
            'model': Task,
            'fields': ['title', 'project', 'assigned_to', 'due_date', 'status', 'priority'],
            'title': _('Tareas'),
        },
        'changeorders': {
            'model': ChangeOrder,
            'fields': ['project', 'title', 'status', 'amount', 'created_at'],
            'title': _('Change Orders'),
        },
        'floorplans': {
            'model': FloorPlan,
            'fields': ['project', 'title', 'floor_number', 'created_at'],
            'title': _('Floor Plans'),
        },
    }
    
    # Redirigir 'clients' a la vista especializada de clientes
    if model_name == 'clients':
        return redirect('client_list')
    
    if model_name not in models_config:
        messages.error(request, _("Modelo no encontrado."))
        return redirect('dashboard_admin')
    
    config = models_config[model_name]
    Model = config['model']
    
    # Búsqueda y filtros
    search = request.GET.get('search', '')
    objects = Model.objects.all()
    
    if search:
        # Búsqueda básica en campos de texto
        q_objects = Q()
        for field in config['fields']:
            if '__' not in field:  # Solo campos directos
                q_objects |= Q(**{f'{field}__icontains': search})
        objects = objects.filter(q_objects)
    
    objects = objects.order_by('-id')
    
    # Paginación
    paginator = Paginator(objects, 25)
    page = request.GET.get('page', 1)
    objects_page = paginator.get_page(page)
    
    context = {
        'model_name': model_name,
        'title': config['title'],
        'objects': objects_page,
        'fields': config['fields'],
        'search': search,
        'total_count': objects.count(),
    }
    return render(request, 'core/admin/model_list.html', context)


# ============================================================
# LOGS Y AUDITORÍA
# ============================================================

@admin_required
def admin_activity_logs(request):
    """Ver logs de actividad del sistema"""
    logs = LogEntry.objects.select_related(
        'user', 'content_type'
    ).order_by('-action_time')
    
    # Filtros
    user_id = request.GET.get('user')
    action = request.GET.get('action')
    
    if user_id:
        logs = logs.filter(user_id=user_id)
    
    if action:
        logs = logs.filter(action_flag=action)
    
    # Paginación
    paginator = Paginator(logs, 50)
    page = request.GET.get('page', 1)
    logs_page = paginator.get_page(page)
    
    context = {
        'logs': logs_page,
        'users': User.objects.filter(is_active=True).order_by('username'),
    }
    return render(request, 'core/admin/activity_logs.html', context)


# ============================================================
# DASHBOARD ADMINISTRATIVO PRINCIPAL
# ============================================================

@admin_required
def admin_dashboard_main(request):
    """Dashboard principal con acceso a todas las funciones administrativas"""
    context = {
        'total_users': User.objects.count(),
        'active_users': User.objects.filter(is_active=True).count(),
        'total_projects': Project.objects.count(),
        'active_projects': Project.objects.filter(end_date__isnull=True).count(),  # Proyectos sin fecha de fin = activos
        'total_clients': Profile.objects.filter(role='client').count(),
        'total_changeorders': ChangeOrder.objects.count(),
        'recent_users': User.objects.order_by('-date_joined')[:5],
        'recent_activity': LogEntry.objects.select_related('user', 'content_type').order_by('-action_time')[:10],
    }
    return render(request, 'core/admin/dashboard_main.html', context)


# ============================================================
# GESTIÓN DE PROYECTOS (CRUD COMPLETO)
# ============================================================

@admin_required
def admin_project_edit(request, project_id):
    """Editar un proyecto existente"""
    project = get_object_or_404(Project, id=project_id)
    
    if request.method == 'POST':
        # Actualizar campos del proyecto
        project.name = request.POST.get('name', '').strip()
        project.client = request.POST.get('client', '').strip()
        project.address = request.POST.get('address', '').strip()
        project.start_date = request.POST.get('start_date')
        project.end_date = request.POST.get('end_date') or None
        project.description = request.POST.get('description', '').strip()
        project.paint_colors = request.POST.get('paint_colors', '').strip()
        project.paint_codes = request.POST.get('paint_codes', '').strip()
        project.stains_or_finishes = request.POST.get('stains_or_finishes', '').strip()
        project.number_of_rooms_or_areas = request.POST.get('number_of_rooms_or_areas') or None
        project.number_of_paint_defects = request.POST.get('number_of_paint_defects') or None
        project.reflection_notes = request.POST.get('reflection_notes', '').strip()
        project.budget_total = request.POST.get('budget_total', 0)
        project.budget_labor = request.POST.get('budget_labor', 0)
        project.budget_materials = request.POST.get('budget_materials', 0)
        project.budget_other = request.POST.get('budget_other', 0)
        
        # Validaciones
        if not project.name:
            messages.error(request, _("El nombre del proyecto es obligatorio."))
        elif not project.start_date:
            messages.error(request, _("La fecha de inicio es obligatoria."))
        else:
            try:
                project.full_clean()
                project.save()
                messages.success(request, _(f"Proyecto '{project.name}' actualizado correctamente."))
                return redirect('admin_model_list', model_name='projects')
            except Exception as e:
                messages.error(request, _(f"Error al guardar el proyecto: {str(e)}"))
    
    context = {
        'project': project,
        'title': _('Editar Proyecto'),
        'action': 'edit',
    }
    return render(request, 'core/admin/project_form.html', context)


@admin_required
def admin_project_create(request):
    """Crear un nuevo proyecto"""
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        client = request.POST.get('client', '').strip()
        address = request.POST.get('address', '').strip()
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date') or None
        description = request.POST.get('description', '').strip()
        paint_colors = request.POST.get('paint_colors', '').strip()
        paint_codes = request.POST.get('paint_codes', '').strip()
        stains_or_finishes = request.POST.get('stains_or_finishes', '').strip()
        number_of_rooms_or_areas = request.POST.get('number_of_rooms_or_areas') or None
        number_of_paint_defects = request.POST.get('number_of_paint_defects') or None
        reflection_notes = request.POST.get('reflection_notes', '').strip()
        budget_total = request.POST.get('budget_total', 0)
        budget_labor = request.POST.get('budget_labor', 0)
        budget_materials = request.POST.get('budget_materials', 0)
        budget_other = request.POST.get('budget_other', 0)
        
        # Validaciones
        if not name:
            messages.error(request, _("El nombre del proyecto es obligatorio."))
        elif not start_date:
            messages.error(request, _("La fecha de inicio es obligatoria."))
        else:
            try:
                project = Project(
                    name=name,
                    client=client,
                    address=address,
                    start_date=start_date,
                    end_date=end_date,
                    description=description,
                    paint_colors=paint_colors,
                    paint_codes=paint_codes,
                    stains_or_finishes=stains_or_finishes,
                    number_of_rooms_or_areas=number_of_rooms_or_areas,
                    number_of_paint_defects=number_of_paint_defects,
                    reflection_notes=reflection_notes,
                    budget_total=budget_total,
                    budget_labor=budget_labor,
                    budget_materials=budget_materials,
                    budget_other=budget_other,
                )
                project.full_clean()
                project.save()
                messages.success(request, _(f"Proyecto '{project.name}' creado correctamente."))
                return redirect('admin_model_list', model_name='projects')
            except Exception as e:
                messages.error(request, _(f"Error al crear el proyecto: {str(e)}"))
    
    context = {
        'title': _('Crear Nuevo Proyecto'),
        'action': 'create',
    }
    return render(request, 'core/admin/project_form.html', context)


@admin_required
@require_POST
def admin_project_delete(request, project_id):
    """Eliminar un proyecto con verificación de dependencias.

    Reglas:
    - Si el proyecto tiene objetos relacionados (ingresos, gastos, timeentries, tareas, changeorders, planos, schedules)
      se requiere confirmación explícita (campo hidden 'confirm' en el POST).
    - Sin confirmación se muestra error y NO se elimina.
    - Con confirmación se elimina en cascada.
    """
    project = get_object_or_404(Project, id=project_id)
    project_name = project.name

    # Contar dependencias relevantes
    related_counts = {
        'ingresos': project.incomes.count(),
        'gastos': project.expenses.count(),
        'timeentries': getattr(project, 'timeentry_set', []).count() if hasattr(project, 'timeentry_set') else 0,
        'tareas': getattr(project, 'tasks', []).count() if hasattr(project, 'tasks') else 0,
        'changeorders': getattr(project, 'changeorder_set', []).count() if hasattr(project, 'changeorder_set') else 0,
        'planos': getattr(project, 'floorplans', []).count() if hasattr(project, 'floorplans') else 0,
        'schedules': getattr(project, 'schedule_set', []).count() if hasattr(project, 'schedule_set') else 0,
    }

    total_related = sum(related_counts.values())
    confirm = request.POST.get('confirm') == 'true'

    if total_related > 0 and not confirm:
        # Construir mensaje descriptivo
        detalles = ", ".join([f"{k}: {v}" for k, v in related_counts.items() if v])
        messages.error(
            request,
            _(f"El proyecto '{project_name}' tiene datos relacionados ({detalles}). Debes confirmar la eliminación."))
        return redirect('admin_model_list', model_name='projects')

    try:
        project.delete()
        messages.success(request, _(f"Proyecto '{project_name}' eliminado correctamente."))
    except Exception as e:
        messages.error(request, _(f"Error al eliminar el proyecto: {str(e)}"))

    return redirect('admin_model_list', model_name='projects')


# ============================================================
# GESTIÓN DE GASTOS (Expense) - Edición
# ============================================================

@admin_required
def admin_expense_edit(request, expense_id):
    """Editar un gasto existente"""
    expense = get_object_or_404(Expense, id=expense_id)
    projects = Project.objects.order_by('name')

    if request.method == 'POST':
        # Captura de campos
        expense.project_id = request.POST.get('project') or expense.project_id
        expense.project_name = request.POST.get('project_name', '').strip() or expense.project_name
        expense.amount = request.POST.get('amount', expense.amount)
        expense.date = request.POST.get('date', expense.date)
        expense.category = request.POST.get('category', expense.category)
        expense.description = request.POST.get('description', '').strip()
        # change_order y cost_code opcionales
        expense.change_order_id = request.POST.get('change_order') or expense.change_order_id
        expense.cost_code_id = request.POST.get('cost_code') or expense.cost_code_id

        # Validaciones mínimas
        errors = []
        if not expense.project_id:
            errors.append(_("El proyecto es obligatorio."))
        if not expense.project_name:
            errors.append(_("El nombre del proyecto/factura es obligatorio."))
        if not expense.amount or str(expense.amount).strip() == '' or float(expense.amount) < 0:
            errors.append(_("El monto debe ser positivo."))
        if not expense.date:
            errors.append(_("La fecha es obligatoria."))
        if not expense.category:
            errors.append(_("La categoría es obligatoria."))

        if errors:
            for e in errors:
                messages.error(request, e)
        else:
            try:
                expense.save()
                # Recalcular total_expenses del proyecto
                project = expense.project
                total = project.expenses.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
                # Normalizar a 2 decimales para cumplir con max_digits/decimal_places del modelo
                try:
                    project.total_expenses = (total if isinstance(total, Decimal) else Decimal(str(total))).quantize(Decimal('0.01'))
                except Exception:
                    project.total_expenses = Decimal('0.00')
                project.save(update_fields=['total_expenses'])
                messages.success(request, _(f"Gasto actualizado correctamente: ${expense.amount}"))
                return redirect('admin_model_list', model_name='expenses')
            except Exception as e:
                messages.error(request, _(f"Error al guardar el gasto: {str(e)}"))

    context = {
        'title': _('Editar Gasto'),
        'expense': expense,
        'projects': projects,
        'category_choices': Expense._meta.get_field('category').choices,
        'action': 'edit',
    }
    return render(request, 'core/admin/expense_form.html', context)


@admin_required
def admin_expense_create(request):
    """Crear un nuevo gasto"""
    projects = Project.objects.order_by('name')

    if request.method == 'POST':
        project_id = request.POST.get('project')
        project_name = request.POST.get('project_name', '').strip()
        amount = request.POST.get('amount')
        date = request.POST.get('date')
        category = request.POST.get('category')
        description = request.POST.get('description', '').strip()

        errors = []
        if not project_id:
            errors.append(_("El proyecto es obligatorio."))
        if not project_name:
            errors.append(_("El nombre del proyecto/factura es obligatorio."))
        try:
            amt_decimal = Decimal(str(amount))
            if amt_decimal < 0:
                errors.append(_("El monto debe ser positivo."))
        except Exception:
            errors.append(_("Monto inválido."))
            errors.append(_("El monto debe ser positivo."))
        if not date:
            errors.append(_("La fecha es obligatoria."))
        if not category:
            errors.append(_("La categoría es obligatoria."))

        if errors:
            for e in errors:
                messages.error(request, e)
        else:
            try:
                expense = Expense(
                    project_id=project_id,
                    project_name=project_name,
                    amount=amt_decimal,
                    date=date,
                    category=category,
                    description=description,
                )
                expense.save()
                # Recalcular total_expenses
                project = expense.project
                total = project.expenses.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
                # Normalizar a 2 decimales
                try:
                    project.total_expenses = (total if isinstance(total, Decimal) else Decimal(str(total))).quantize(Decimal('0.01'))
                except Exception:
                    project.total_expenses = Decimal('0.00')
                project.save(update_fields=['total_expenses'])
                messages.success(request, _(f"Gasto creado correctamente: ${expense.amount}"))
                return redirect('admin_model_list', model_name='expenses')
            except Exception as e:
                messages.error(request, _(f"Error al crear el gasto: {str(e)}"))

    context = {
        'title': _('Crear Gasto'),
        'projects': projects,
        'category_choices': Expense._meta.get_field('category').choices,
        'action': 'create',
    }
    return render(request, 'core/admin/expense_form.html', context)


@admin_required
@require_POST
def admin_expense_delete(request, expense_id):
    """Eliminar gasto y recalcular totales"""
    expense = get_object_or_404(Expense, id=expense_id)
    project = expense.project
    try:
        expense.delete()
        total = project.expenses.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        try:
            project.total_expenses = (total if isinstance(total, Decimal) else Decimal(str(total))).quantize(Decimal('0.01'))
        except Exception:
            project.total_expenses = Decimal('0.00')
        project.save(update_fields=['total_expenses'])
        messages.success(request, _("Gasto eliminado"))
    except Exception as e:
        messages.error(request, _(f"Error al eliminar el gasto: {str(e)}"))
    return redirect('admin_model_list', model_name='expenses')


# ============================================================
# GESTIÓN DE INGRESOS (Income)
# ============================================================

@admin_required
def admin_income_edit(request, income_id):
    """Editar un ingreso existente"""
    income = get_object_or_404(Income, id=income_id)
    projects = Project.objects.order_by('name')
    payment_choices = Income._meta.get_field('payment_method').choices

    if request.method == 'POST':
        income.project_id = request.POST.get('project') or income.project_id
        income.project_name = request.POST.get('project_name', '').strip() or income.project_name
        amount_in = request.POST.get('amount', income.amount)
        income.date = request.POST.get('date', income.date)
        income.payment_method = request.POST.get('payment_method', income.payment_method)
        income.category = request.POST.get('category', income.category)
        income.description = request.POST.get('description', '').strip()

        errors = []
        if not income.project_id:
            errors.append(_("El proyecto es obligatorio."))
        if not income.project_name:
            errors.append(_("El nombre del proyecto/factura es obligatorio."))
        try:
            amt_dec = Decimal(str(amount_in))
            if amt_dec < 0:
                errors.append(_("El monto debe ser positivo."))
            else:
                income.amount = amt_dec
        except Exception:
            errors.append(_("Monto inválido."))
        if not income.date:
            errors.append(_("La fecha es obligatoria."))
        if not income.payment_method:
            errors.append(_("El método de pago es obligatorio."))
        else:
            valid_codes = {c for c,_ in payment_choices}
            if income.payment_method not in valid_codes:
                errors.append(_("Método de pago inválido."))

        if errors:
            for e in errors:
                messages.error(request, e)
        else:
            try:
                income.save()
                project = income.project
                total = project.incomes.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
                try:
                    project.total_income = (total if isinstance(total, Decimal) else Decimal(str(total))).quantize(Decimal('0.01'))
                except Exception:
                    project.total_income = Decimal('0.00')
                project.save(update_fields=['total_income'])
                messages.success(request, _(f"Ingreso actualizado correctamente: ${income.amount}"))
                return redirect('admin_model_list', model_name='income')
            except Exception as e:
                messages.error(request, _(f"Error al guardar el ingreso: {str(e)}"))

    context = {
        'title': _("Editar Ingreso"),
        'income': income,
        'projects': projects,
        'payment_choices': payment_choices,
        'action': 'edit',
    }
    return render(request, 'core/admin/income_form.html', context)


@admin_required
def admin_income_create(request):
    """Crear un nuevo ingreso"""
    projects = Project.objects.order_by('name')
    payment_choices = Income._meta.get_field('payment_method').choices

    if request.method == 'POST':
        project_id = request.POST.get('project')
        project_name = request.POST.get('project_name', '').strip()
        amount = request.POST.get('amount')
        date = request.POST.get('date')
        payment_method = request.POST.get('payment_method')
        category = request.POST.get('category', '').strip() or None
        description = request.POST.get('description', '').strip()

        errors = []
        if not project_id:
            errors.append(_("El proyecto es obligatorio."))
        if not project_name:
            errors.append(_("El nombre del proyecto/factura es obligatorio."))
        try:
            amt_decimal = Decimal(str(amount))
            if amt_decimal < 0:
                errors.append(_("El monto debe ser positivo."))
        except Exception:
            errors.append(_("Monto inválido."))
        if not date:
            errors.append(_("La fecha es obligatoria."))
        if not payment_method:
            errors.append(_("El método de pago es obligatorio."))
        else:
            valid_codes = {c for c,_ in payment_choices}
            if payment_method not in valid_codes:
                errors.append(_("Método de pago inválido."))

        if errors:
            for e in errors:
                messages.error(request, e)
        else:
            try:
                income = Income(
                    project_id=project_id,
                    project_name=project_name,
                    amount=amt_decimal,
                    date=date,
                    payment_method=payment_method,
                    category=category,
                    description=description,
                )
                income.save()
                project = income.project
                total = project.incomes.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
                try:
                    project.total_income = (total if isinstance(total, Decimal) else Decimal(str(total))).quantize(Decimal('0.01'))
                except Exception:
                    project.total_income = Decimal('0.00')
                project.save(update_fields=['total_income'])
                messages.success(request, _(f"Ingreso creado correctamente: ${income.amount}"))
                return redirect('admin_model_list', model_name='income')
            except Exception as e:
                messages.error(request, _(f"Error al crear el ingreso: {str(e)}"))

    context = {
        'title': _("Crear Ingreso"),
        'projects': projects,
        'payment_choices': payment_choices,
        'action': 'create',
    }
    return render(request, 'core/admin/income_form.html', context)


@admin_required
@require_POST
def admin_income_delete(request, income_id):
    """Eliminar ingreso y recalcular totales"""
    income = get_object_or_404(Income, id=income_id)
    project = income.project
    try:
        income.delete()
        total = project.incomes.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        try:
            project.total_income = (total if isinstance(total, Decimal) else Decimal(str(total))).quantize(Decimal('0.01'))
        except Exception:
            project.total_income = Decimal('0.00')
        project.save(update_fields=['total_income'])
        messages.success(request, _("Ingreso eliminado"))
    except Exception as e:
        messages.error(request, _(f"Error al eliminar el ingreso: {str(e)}"))
    return redirect('admin_model_list', model_name='income')
