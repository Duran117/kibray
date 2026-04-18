"""Project financial views — financials hub, budget, cost codes, estimates, invoices."""
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
def project_financials_hub(request, project_id):
    """
    Hub financiero principal del proyecto.
    Muestra resumen de budget, spent, remaining y breakdown por cost code.
    
    Para PM (no admin): muestra Working Budget (-30%) 
    Para Admin/Superuser: muestra Budget real completo
    """
    if not _is_staffish(request.user):
        return redirect("dashboard")
    project = get_object_or_404(Project, pk=project_id)
    
    # Determinar si es PM (no admin)
    profile = getattr(request.user, 'profile', None)
    is_pm = profile and profile.role == 'pm' if profile else False
    
    # Calcular totales
    budget_lines = project.budget_lines.select_related('cost_code').all()
    
    # Total budget = suma de revised_amount de todas las líneas
    total_budget = sum(line.revised_amount or line.baseline_amount for line in budget_lines)
    
    # Working budget para PM = total - 30%
    working_budget = total_budget * Decimal('0.70') if total_budget else Decimal('0')
    
    # Calculate actual spent from expenses linked to project
    from django.db.models import Sum as DJSum
    total_spent = project.expenses.aggregate(total=DJSum('amount'))['total'] or Decimal('0')
    
    # Also include labor cost from time entries
    time_labor_cost = Decimal('0')
    for te in TimeEntry.objects.filter(project=project).select_related('employee'):
        rate = te.employee.hourly_rate if te.employee and te.employee.hourly_rate else Decimal('0')
        time_labor_cost += (te.hours_worked or Decimal('0')) * rate
    total_spent += time_labor_cost
    
    # Remaining
    if is_pm and not request.user.is_superuser:
        remaining = working_budget - total_spent
        display_budget = working_budget
    else:
        remaining = total_budget - total_spent
        display_budget = total_budget
    
    # Porcentajes
    spent_percentage = int((total_spent / display_budget * 100) if display_budget else 0)
    margin_percentage = 30 if is_pm else (int((remaining / total_budget * 100)) if total_budget else 0)
    
    # Preparar datos de líneas para display
    # Pre-compute expense totals per cost_code for per-line breakdown
    from core.models import Expense
    expense_by_costcode = {}
    for exp in Expense.objects.filter(project=project).values('cost_code_id').annotate(total=DJSum('amount')):
        if exp['cost_code_id']:
            expense_by_costcode[exp['cost_code_id']] = exp['total'] or Decimal('0')
    
    lines_data = []
    for line in budget_lines:
        line_budget = line.revised_amount or line.baseline_amount
        # Para PM mostrar budget reducido
        if is_pm and not request.user.is_superuser:
            line_display_budget = line_budget * Decimal('0.70')
        else:
            line_display_budget = line_budget
        
        line_spent = expense_by_costcode.get(line.cost_code_id, Decimal('0'))
        line_remaining = line_display_budget - line_spent
        line_spent_pct = (line_spent / line_display_budget * 100) if line_display_budget else 0
        line_remaining_pct = 100 - float(line_spent_pct)
        
        lines_data.append({
            'cost_code': line.cost_code,
            'description': line.description,
            'display_budget': line_display_budget,
            'spent': line_spent,
            'remaining': line_remaining,
            'spent_pct': line_spent_pct,
            'remaining_pct': line_remaining_pct,
        })
    
    context = {
        'project': project,
        'is_pm': is_pm,
        'total_budget': total_budget,
        'working_budget': working_budget,
        'total_spent': total_spent,
        'remaining': remaining,
        'spent_percentage': spent_percentage,
        'margin_percentage': margin_percentage,
        'budget_lines': lines_data,
        'active_tab': 'overview',
    }
    
    return render(request, 'core/project_financials_hub.html', context)




@login_required
def project_budget_detail(request, project_id):
    """
    Vista de detalle del budget con capacidad de agregar/editar/eliminar líneas.
    Solo staff/admin puede editar.
    """
    if not _is_staffish(request.user):
        return redirect("dashboard")
    project = get_object_or_404(Project, pk=project_id)
    
    # Verificar permisos de edición
    can_edit = request.user.is_staff or request.user.is_superuser
    
    if request.method == 'POST' and can_edit:
        action = request.POST.get('action', 'add')
        
        # DELETE action
        if action == 'delete':
            line_id = request.POST.get('line_id')
            if line_id:
                try:
                    line = BudgetLine.objects.get(pk=line_id, project=project)
                    line.delete()
                    messages.success(request, _('Budget line deleted successfully.'))
                except BudgetLine.DoesNotExist:
                    messages.error(request, _('Budget line not found.'))
            return redirect('project_budget_detail', project_id=project.id)
        
        # EDIT action
        elif action == 'edit':
            line_id = request.POST.get('line_id')
            if line_id:
                try:
                    line = BudgetLine.objects.get(pk=line_id, project=project)
                    line.description = request.POST.get('description', line.description)
                    line.qty = Decimal(str(request.POST.get('qty', line.qty) or 0))
                    line.unit = request.POST.get('unit', line.unit)
                    line.unit_cost = Decimal(str(request.POST.get('unit_cost', line.unit_cost) or 0))
                    # Allow editing revised_amount directly
                    revised = request.POST.get('revised_amount')
                    if revised:
                        line.revised_amount = Decimal(str(revised))
                    line.save()
                    messages.success(request, _('Budget line updated successfully.'))
                except (BudgetLine.DoesNotExist, InvalidOperation) as e:
                    messages.error(request, _('Error updating budget line.'))
            return redirect('project_budget_detail', project_id=project.id)
        
        # ADD action (default)
        else:
            cost_code_id = request.POST.get('cost_code')
            description = request.POST.get('description', '')
            qty = request.POST.get('qty', 0)
            unit = request.POST.get('unit', '')
            unit_cost = request.POST.get('unit_cost', 0)
            
            if cost_code_id:
                try:
                    cost_code = CostCode.objects.get(pk=cost_code_id)
                    BudgetLine.objects.create(
                        project=project,
                        cost_code=cost_code,
                        description=description,
                        qty=Decimal(str(qty)) if qty else Decimal('0'),
                        unit=unit,
                        unit_cost=Decimal(str(unit_cost)) if unit_cost else Decimal('0'),
                    )
                    messages.success(request, _('Budget line added successfully.'))
                except (CostCode.DoesNotExist, InvalidOperation) as e:
                    messages.error(request, _('Error adding budget line.'))
            
            return redirect('project_budget_detail', project_id=project.id)
    
    budget_lines = project.budget_lines.select_related('cost_code').order_by('cost_code__code')
    cost_codes = CostCode.objects.filter(active=True).order_by('code')
    
    # Calcular totales
    total_baseline = sum(line.baseline_amount for line in budget_lines)
    total_revised = sum(line.revised_amount for line in budget_lines)
    variance = total_revised - total_baseline
    
    context = {
        'project': project,
        'budget_lines': budget_lines,
        'cost_codes': cost_codes,
        'can_edit': can_edit,
        'total_baseline': total_baseline,
        'total_revised': total_revised,
        'variance': variance,
        'active_tab': 'budget',
    }
    
    return render(request, 'core/project_budget_detail.html', context)




@login_required  
def project_cost_codes(request, project_id):
    """
    Gestión de Cost Codes - códigos para categorizar costos.
    Solo admin puede crear/editar.
    """
    if not _is_staffish(request.user):
        return redirect("dashboard")
    project = get_object_or_404(Project, pk=project_id)
    
    can_edit = request.user.is_staff or request.user.is_superuser
    
    if request.method == 'POST' and can_edit:
        action = request.POST.get('action', 'create')
        
        if action == 'create':
            code = request.POST.get('code', '').strip().upper()
            name = request.POST.get('name', '').strip()
            category = request.POST.get('category', '').strip()
            
            if code and name:
                try:
                    CostCode.objects.create(
                        code=code,
                        name=name,
                        category=category,
                        active=True,
                    )
                    messages.success(request, _('Cost code created successfully.'))
                except IntegrityError:
                    messages.error(request, _('A cost code with that code already exists.'))
            else:
                messages.error(request, _('Code and name are required.'))
        
        elif action == 'update':
            costcode_id = request.POST.get('costcode_id')
            if costcode_id:
                try:
                    costcode = CostCode.objects.get(pk=costcode_id)
                    costcode.code = request.POST.get('code', '').strip().upper()
                    costcode.name = request.POST.get('name', '').strip()
                    costcode.category = request.POST.get('category', '').strip()
                    costcode.active = request.POST.get('active') == 'on'
                    costcode.save()
                    messages.success(request, _('Cost code updated successfully.'))
                except CostCode.DoesNotExist:
                    messages.error(request, _('Cost code not found.'))
        
        elif action == 'delete':
            costcode_id = request.POST.get('costcode_id')
            if costcode_id:
                try:
                    costcode = CostCode.objects.get(pk=costcode_id)
                    costcode.delete()
                    messages.success(request, _('Cost code deleted.'))
                except CostCode.DoesNotExist:
                    messages.error(request, _('Cost code not found.'))
        
        return redirect('project_cost_codes', project_id=project.id)
    
    cost_codes = CostCode.objects.all().order_by('category', 'code')
    
    # Default categories for construction
    default_categories = [
        'Appliances',
        'Cabinets',
        'Cleanup',
        'Concrete',
        'Countertops',
        'Demolition',
        'Drywall',
        'Electrical',
        'Equipment',
        'Exterior',
        'Exterior Painting',
        'Flooring',
        'Framing',
        'HVAC',
        'Interior',
        'Interior Painting',
        'Labor',
        'Landscaping',
        'Material',
        'Plumbing',
        'Roofing',
        'Subcontractor',
        'Windows & Doors',
        'Other',
    ]
    
    # Get existing categories, normalize to title case
    existing_raw = CostCode.objects.exclude(category__isnull=True).exclude(category='').values_list('category', flat=True).distinct()
    existing_normalized = set()
    for cat in existing_raw:
        # Normalize: "interior painting" -> "Interior Painting"
        normalized = cat.strip().title()
        existing_normalized.add(normalized)
    
    # Merge and deduplicate
    all_categories = sorted(set(default_categories) | existing_normalized)
    
    # Agrupar por categoría (normalizado)
    codes_by_category = defaultdict(list)
    for cc in cost_codes:
        cat = (cc.category or '').strip().title() or _('Uncategorized')
        codes_by_category[cat].append(cc)
    
    context = {
        'project': project,
        'cost_codes': cost_codes,
        'codes_by_category': dict(codes_by_category),
        'can_edit': can_edit,
        'active_tab': 'costcodes',
        'categories': all_categories,
    }
    
    return render(request, 'core/project_cost_codes.html', context)




@login_required
def project_estimates(request, project_id):
    """
    Lista de estimados del proyecto.
    Solo visible para staff/admin.
    """
    # SECURITY: Only staff/superusers can view estimates (financial data)
    if not (request.user.is_staff or request.user.is_superuser):
        return HttpResponseForbidden(_('Access denied'))
    
    project = get_object_or_404(Project, pk=project_id)
    
    estimates = project.estimates.all().order_by('-version')
    
    # Calcular totales para cada estimado
    estimates_data = []
    for est in estimates:
        lines = est.lines.select_related('cost_code')
        direct_cost = sum(line.direct_cost() for line in lines)
        
        # Calcular precio propuesto con markups
        material_markup = direct_cost * (est.markup_material / 100)
        labor_markup = direct_cost * (est.markup_labor / 100)
        overhead = direct_cost * (est.overhead_pct / 100)
        profit = direct_cost * (est.target_profit_pct / 100)
        proposed_price = direct_cost + material_markup + labor_markup + overhead + profit
        
        estimates_data.append({
            'estimate': est,
            'direct_cost': direct_cost,
            'proposed_price': proposed_price,
            'lines_count': lines.count(),
        })
    
    context = {
        'project': project,
        'estimates': estimates_data,
        'can_create': request.user.is_staff or request.user.is_superuser,
        'active_tab': 'estimates',
    }
    
    return render(request, 'core/project_estimates_list.html', context)




@login_required
def project_invoices(request, project_id):
    """
    Lista de facturas del proyecto.
    Solo visible para staff/admin.
    """
    if not (request.user.is_staff or request.user.is_superuser):
        return HttpResponseForbidden(_('Access denied'))
    
    project = get_object_or_404(Project, pk=project_id)
    
    invoices = project.invoices.all().order_by('-created_at')
    
    context = {
        'project': project,
        'invoices': invoices,
        'active_tab': 'invoices',
    }
    
    return render(request, 'core/project_invoices_list.html', context)


