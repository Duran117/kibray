from rest_framework import viewsets, status
import json
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.request import Request
from rest_framework import filters
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth import get_user_model
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.db.models import Sum, Q, F, DecimalField
from django.db.models.functions import Coalesce
from decimal import Decimal
from django.core.files.base import ContentFile
import base64, re
from core.models import (
    Notification, ChatChannel, ChatMessage, Task, DamageReport,
    FloorPlan, PlanPin, ColorSample, Project, ScheduleCategory, ScheduleItem,
    ChangeOrderPhoto, Income, Expense, CostCode, BudgetLine
)
from .serializers import (
    NotificationSerializer, ChatChannelSerializer, ChatMessageSerializer,
    TaskSerializer, DamageReportSerializer, FloorPlanSerializer,
    PlanPinSerializer, ColorSampleSerializer, ProjectListSerializer,
    ScheduleCategorySerializer, ScheduleItemSerializer,
    ProjectSerializer, IncomeSerializer, ExpenseSerializer,
    CostCodeSerializer, BudgetLineSerializer, ProjectBudgetSummarySerializer
)
from .filters import IncomeFilter, ExpenseFilter, ProjectFilter
from .pagination import StandardResultsSetPagination

User = get_user_model()

# Notifications
class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user).order_by('-created_at')
    
    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return Response({'status': 'ok'})
    
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        notif = self.get_object()
        notif.is_read = True
        notif.save()
        return Response({'status': 'ok'})
    
    @action(detail=False, methods=['get'])
    def count_unread(self, request):
        count = Notification.objects.filter(user=request.user, is_read=False).count()
        return Response({'unread_count': count})

# Chat
class ChatChannelViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ChatChannelSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # Channels where user is participant
        return ChatChannel.objects.filter(participants=self.request.user).order_by('-created_at')

class ChatMessageViewSet(viewsets.ModelViewSet):
    serializer_class = ChatMessageSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    def get_queryset(self):
        channel_id = self.request.query_params.get('channel')
        qs = ChatMessage.objects.select_related('user', 'channel').order_by('-created_at')
        if channel_id:
            qs = qs.filter(channel_id=channel_id)
        return qs
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

# Touch-ups / Tasks
class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        qs = Task.objects.select_related('project', 'assigned_to').order_by('-created_at')
        touchup_only = self.request.query_params.get('touchup')
        if touchup_only == 'true':
            qs = qs.filter(is_touchup=True)
        assigned_to_me = self.request.query_params.get('assigned_to_me')
        if assigned_to_me == 'true':
            qs = qs.filter(assigned_to=self.request.user)
        return qs
    
    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        task = self.get_object()
        new_status = request.data.get('status')
        if new_status:
            task.status = new_status
            task.save()
            return Response({'status': 'updated'})
        return Response({'error': 'status required'}, status=status.HTTP_400_BAD_REQUEST)

# Damage Reports
class DamageReportViewSet(viewsets.ModelViewSet):
    serializer_class = DamageReportSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    def get_queryset(self):
        return DamageReport.objects.select_related('project', 'reported_by').order_by('-created_at')
    
    def perform_create(self, serializer):
        serializer.save(reported_by=self.request.user)

# Floor Plans & Pins
class FloorPlanViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = FloorPlanSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return FloorPlan.objects.prefetch_related('pins').select_related('project').order_by('-created_at')

class PlanPinViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = PlanPinSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        plan_id = self.request.query_params.get('plan')
        qs = PlanPin.objects.select_related('plan', 'color_sample', 'linked_task').order_by('-created_at')
        if plan_id:
            qs = qs.filter(plan_id=plan_id)
        return qs

# Color Samples
class ColorSampleViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ColorSampleSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return ColorSample.objects.select_related('project').order_by('-created_at')

# Projects
class ProjectViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ProjectListSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Project.objects.all().order_by('-created_at')

# Schedule Categories
class ScheduleCategoryViewSet(viewsets.ModelViewSet):
    serializer_class = ScheduleCategorySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        project_id = self.request.query_params.get('project')
        qs = ScheduleCategory.objects.select_related('project', 'parent')
        if project_id:
            qs = qs.filter(project_id=project_id)
        return qs.order_by('order')

# Schedule Items
class ScheduleItemViewSet(viewsets.ModelViewSet):
    serializer_class = ScheduleItemSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        project_id = self.request.query_params.get('project')
        qs = ScheduleItem.objects.select_related('project', 'category', 'cost_code').prefetch_related('dependencies')
        if project_id:
            qs = qs.filter(project_id=project_id)
        return qs.order_by('order')
    
    @action(detail=False, methods=['post'])
    def bulk_update(self, request):
        """Bulk update schedule items (e.g., after drag-and-drop)"""
        updates = request.data.get('updates', [])
        if not updates:
            return Response({'error': 'No updates provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        updated_items = []
        for update_data in updates:
            item_id = update_data.pop('id', None)
            if not item_id:
                continue
            
            try:
                item = ScheduleItem.objects.get(id=item_id)
                for field, value in update_data.items():
                    if hasattr(item, field):
                        setattr(item, field, value)
                item.save()
                updated_items.append(item)
            except ScheduleItem.DoesNotExist:
                continue
        
        serializer = self.get_serializer(updated_items, many=True)
        return Response(serializer.data)


# ===== GLOBAL SEARCH API =====
from django.db.models import Q
from core.models import ChangeOrder, Invoice, TimeEntry

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def global_search(request):
    """
    Universal search across all major entities.
    GET /api/search/?q=query
    
    Returns results from:
    - Projects (name, address, client)
    - Change Orders (number, description, project)
    - Invoices (number, project, client)
    - Employees (name, position, phone)
    - Tasks (title, description, project)
    """
    query = request.GET.get('q', '').strip()
    
    if not query or len(query) < 2:
        return Response({
            'query': query,
            'results': {
                'projects': [],
                'change_orders': [],
                'invoices': [],
                'employees': [],
                'tasks': []
            },
            'total_count': 0
        })
    
    # Search Projects
    projects = Project.objects.filter(
        Q(name__icontains=query) |
        Q(address__icontains=query) |
        Q(client__company_name__icontains=query) |
        Q(client__first_name__icontains=query) |
        Q(client__last_name__icontains=query)
    ).select_related('client')[:10]
    
    project_results = [{
        'id': p.id,
        'type': 'project',
        'title': p.name,
        'subtitle': f"{p.client.get_full_name() if p.client else 'No Client'} • {p.address}",
        'url': f'/projects/{p.id}/',
        'icon': 'bi-building',
        'badge': p.status.upper() if hasattr(p, 'status') else None
    } for p in projects]
    
    # Search Change Orders
    change_orders = ChangeOrder.objects.filter(
        Q(co_number__icontains=query) |
        Q(description__icontains=query) |
        Q(project__name__icontains=query)
    ).select_related('project')[:10]
    
    co_results = [{
        'id': co.id,
        'type': 'change_order',
        'title': f"CO-{co.co_number}",
        'subtitle': f"{co.project.name} • ${co.amount:,.2f}",
        'url': f'/change-orders/{co.id}/',
        'icon': 'bi-file-earmark-diff',
        'badge': co.status.upper()
    } for co in change_orders]
    
    # Search Invoices
    invoices = Invoice.objects.filter(
        Q(invoice_number__icontains=query) |
        Q(project__name__icontains=query) |
        Q(project__client__company_name__icontains=query)
    ).select_related('project', 'project__client')[:10]
    
    invoice_results = [{
        'id': inv.id,
        'type': 'invoice',
        'title': f"Invoice #{inv.invoice_number}",
        'subtitle': f"{inv.project.name if inv.project else 'No Project'} • ${inv.total_amount:,.2f}",
        'url': f'/invoices/{inv.id}/',
        'icon': 'bi-receipt',
        'badge': inv.status.upper()
    } for inv in invoices]
    
    # Search Employees
    employees = User.objects.filter(
        Q(first_name__icontains=query) |
        Q(last_name__icontains=query) |
        Q(email__icontains=query) |
        Q(phone__icontains=query) |
        Q(profile__position__icontains=query)
    ).select_related('profile')[:10]
    
    employee_results = [{
        'id': emp.id,
        'type': 'employee',
        'title': emp.get_full_name(),
        'subtitle': f"{emp.profile.position if hasattr(emp, 'profile') and emp.profile else 'No Position'} • {emp.email}",
        'url': f'/employees/{emp.id}/',
        'icon': 'bi-person-circle',
        'badge': None
    } for emp in employees]
    
    # Search Tasks
    tasks = Task.objects.filter(
        Q(title__icontains=query) |
        Q(description__icontains=query) |
        Q(project__name__icontains=query)
    ).select_related('project', 'assigned_to')[:10]
    
    task_results = [{
        'id': task.id,
        'type': 'task',
        'title': task.title,
        'subtitle': f"{task.project.name if task.project else 'No Project'} • {task.assigned_to.get_full_name() if task.assigned_to else 'Unassigned'}",
        'url': f'/tasks/{task.id}/',
        'icon': 'bi-check-square',
        'badge': task.status.upper() if hasattr(task, 'status') else None
    } for task in tasks]
    
    total_count = (
        len(project_results) +
        len(co_results) +
        len(invoice_results) +
        len(employee_results) +
        len(task_results)
    )
    
    return Response({
        'query': query,
        'results': {
            'projects': project_results,
            'change_orders': co_results,
            'invoices': invoice_results,
            'employees': employee_results,
            'tasks': task_results
        },
        'total_count': total_count
    })

# ChangeOrder Photo Annotations
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def save_changeorder_photo_annotations(request, photo_id):
    """Save annotations (drawings) to a ChangeOrderPhoto"""
    try:
        photo = get_object_or_404(ChangeOrderPhoto, id=photo_id)
        raw = request.data
        # DRF when receiving a JSON array sets request.data to a list, not dict.
        if isinstance(raw, list):
            annotations = raw
        elif isinstance(raw, dict):
            # Accept either {'annotations': [...]} or full dict representing annotations
            inner = raw.get('annotations')
            if inner is not None:
                annotations = inner
            else:
                annotations = raw
        elif isinstance(raw, str):
            # Could be a JSON string representing list/dict
            try:
                parsed = json.loads(raw)
                annotations = parsed if isinstance(parsed, (list, dict)) else raw
            except Exception:
                annotations = raw
        else:
            annotations = []

        # Normalize if annotations is still a string containing JSON
        if isinstance(annotations, str):
            try:
                parsed = json.loads(annotations)
                if isinstance(parsed, (list, dict)):
                    annotations = parsed
            except Exception:
                pass

        # Persist as single JSON string
        if isinstance(annotations, (list, dict)):
            photo.annotations = json.dumps(annotations)
        else:
            photo.annotations = annotations
        photo.save()

        return JsonResponse({
            'success': True,
            'message': 'Annotations saved',
            'photo_id': photo.id,
            'annotation_count': len(annotations) if isinstance(annotations, list) else 1
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def delete_changeorder_photo(request, photo_id):
    """Delete a ChangeOrderPhoto"""
    try:
        photo = get_object_or_404(ChangeOrderPhoto, id=photo_id)
        photo.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Photo deleted successfully'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_changeorder_photo_image(request, photo_id):
    """Replace the stored image with an annotated version (base64 Data URL).

    Expected JSON body:
    {
      "image_data": "data:image/png;base64,iVBORw0KGgo...",
      "keep_original": true  # optional, defaults true
    }
    Returns updated image URL with cache-busting query param.
    """
    try:
        photo = get_object_or_404(ChangeOrderPhoto, id=photo_id)
        image_data = request.data.get('image_data') or request.POST.get('image_data')
        if not image_data:
            return JsonResponse({'success': False, 'error': 'image_data required'}, status=400)
        match = re.match(r'^data:image/(png|jpeg|jpg);base64,(.+)$', image_data)
        if not match:
            return JsonResponse({'success': False, 'error': 'Invalid data URL'}, status=400)
        ext = match.group(1)
        b64 = match.group(2)
        try:
            content = base64.b64decode(b64)
        except Exception:
            return JsonResponse({'success': False, 'error': 'Base64 decode failed'}, status=400)
        # Use model helper to replace & preserve original
        photo.replace_with_annotated(content, extension=('jpg' if ext=='jpeg' else ext))
        # Bust cache with updated_at timestamp
        cache_bust = int(photo.updated_at.timestamp()) if photo.updated_at else '0'
        return JsonResponse({
            'success': True,
            'photo_id': photo.id,
            'image_url': f"{photo.image.url}?v={cache_bust}",
            'updated_at': photo.updated_at.isoformat()
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


# =============================================================================
# FINANCIAL API VIEWSETS
# =============================================================================

class ProjectViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Project CRUD operations with financial data.
    
    Filters:
    - name: Search by project name (case-insensitive)
    - client: Search by client name (case-insensitive)
    - start_date_after: Projects starting after this date
    - start_date_before: Projects starting before this date
    - is_active: Show only active projects (end_date is null or in future)
    
    Ordering:
    - name, client, start_date, end_date, created_at, total_income, total_expenses
    """
    queryset = Project.objects.all().order_by('-created_at')
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ProjectFilter
    search_fields = ['name', 'client', 'address']
    ordering_fields = ['name', 'client', 'start_date', 'end_date', 'created_at', 'total_income', 'total_expenses']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ProjectListSerializer
        return ProjectSerializer
    
    @action(detail=True, methods=['get'])
    def financial_summary(self, request, pk=None):
        """Get financial summary for a project"""
        project = self.get_object()
        
        # Aggregate income and expenses
        income_total = project.incomes.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        expense_total = project.expenses.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        # Expense breakdown by category
        expense_by_category = project.expenses.values('category').annotate(
            total=Sum('amount')
        ).order_by('-total')
        
        # Income by payment method
        income_by_method = project.incomes.values('payment_method').annotate(
            total=Sum('amount')
        ).order_by('-total')
        
        summary = {
            'project_id': project.id,
            'project_name': project.name,
            'total_income': income_total,
            'total_expenses': expense_total,
            'profit': income_total - expense_total,
            'budget_total': project.budget_total,
            'budget_remaining': project.budget_total - expense_total,
            'percent_spent': round((expense_total / project.budget_total * 100) if project.budget_total > 0 else 0, 2),
            'is_over_budget': expense_total > project.budget_total,
            'expense_by_category': list(expense_by_category),
            'income_by_method': list(income_by_method),
        }
        
        return Response(summary)
    
    @action(detail=False, methods=['get'])
    def budget_overview(self, request):
        """Get budget overview for all projects"""
        projects = self.get_queryset()
        
        summaries = []
        for project in projects:
            expense_total = project.expenses.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
            percent_spent = round((expense_total / project.budget_total * 100) if project.budget_total > 0 else 0, 2)
            
            summaries.append({
                'project_id': project.id,
                'project_name': project.name,
                'budget_total': project.budget_total,
                'budget_labor': project.budget_labor,
                'budget_materials': project.budget_materials,
                'budget_other': project.budget_other,
                'total_expenses': expense_total,
                'budget_remaining': project.budget_total - expense_total,
                'percent_spent': percent_spent,
                'is_over_budget': expense_total > project.budget_total,
            })
        
        serializer = ProjectBudgetSummarySerializer(summaries, many=True)
        return Response(serializer.data)


class IncomeViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Income CRUD operations.
    
    Filters:
    - project: Filter by project ID
    - date_after: Income received after this date
    - date_before: Income received before this date
    - payment_method: Filter by payment method
    - amount_min: Minimum amount
    - amount_max: Maximum amount
    
    Ordering:
    - date, amount, payment_method, created_at
    """
    queryset = Income.objects.select_related('project').all().order_by('-date')
    serializer_class = IncomeSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = IncomeFilter
    search_fields = ['project_name', 'description', 'notes']
    ordering_fields = ['date', 'amount', 'payment_method']
    
    def perform_create(self, serializer):
        """Update project total_income when creating income"""
        income = serializer.save()
        project = income.project
        project.total_income = project.incomes.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        project.save(update_fields=['total_income'])
    
    def perform_update(self, serializer):
        """Update project total_income when updating income"""
        income = serializer.save()
        project = income.project
        project.total_income = project.incomes.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        project.save(update_fields=['total_income'])
    
    def perform_destroy(self, instance):
        """Update project total_income when deleting income"""
        project = instance.project
        instance.delete()
        project.total_income = project.incomes.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        project.save(update_fields=['total_income'])
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get income summary"""
        queryset = self.filter_queryset(self.get_queryset())
        
        total = queryset.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        by_method = queryset.values('payment_method').annotate(
            total=Sum('amount')
        ).order_by('-total')
        by_project = queryset.values('project__name').annotate(
            total=Sum('amount')
        ).order_by('-total')[:10]
        
        return Response({
            'total_income': total,
            'income_by_method': list(by_method),
            'income_by_project': list(by_project),
            'count': queryset.count()
        })


class ExpenseViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Expense CRUD operations.
    
    Filters:
    - project: Filter by project ID
    - category: Filter by expense category
    - cost_code: Filter by cost code ID
    - date_after: Expenses after this date
    - date_before: Expenses before this date
    - amount_min: Minimum amount
    - amount_max: Maximum amount
    
    Ordering:
    - date, amount, category, created_at
    """
    queryset = Expense.objects.select_related('project', 'cost_code', 'change_order').all().order_by('-date')
    serializer_class = ExpenseSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    parser_classes = [MultiPartParser, FormParser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ExpenseFilter
    search_fields = ['project_name', 'description']
    ordering_fields = ['date', 'amount', 'category']
    
    def perform_create(self, serializer):
        """Update project total_expenses when creating expense"""
        expense = serializer.save()
        project = expense.project
        project.total_expenses = project.expenses.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        project.save(update_fields=['total_expenses'])
    
    def perform_update(self, serializer):
        """Update project total_expenses when updating expense"""
        expense = serializer.save()
        project = expense.project
        project.total_expenses = project.expenses.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        project.save(update_fields=['total_expenses'])
    
    def perform_destroy(self, instance):
        """Update project total_expenses when deleting expense"""
        project = instance.project
        instance.delete()
        project.total_expenses = project.expenses.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        project.save(update_fields=['total_expenses'])
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get expense summary"""
        queryset = self.filter_queryset(self.get_queryset())
        
        total = queryset.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        by_category = queryset.values('category').annotate(
            total=Sum('amount')
        ).order_by('-total')
        by_project = queryset.values('project__name').annotate(
            total=Sum('amount')
        ).order_by('-total')[:10]
        by_cost_code = queryset.filter(cost_code__isnull=False).values(
            'cost_code__code', 'cost_code__name'
        ).annotate(
            total=Sum('amount')
        ).order_by('-total')[:10]
        
        return Response({
            'total_expenses': total,
            'expense_by_category': list(by_category),
            'expense_by_project': list(by_project),
            'expense_by_cost_code': list(by_cost_code),
            'count': queryset.count()
        })


class CostCodeViewSet(viewsets.ModelViewSet):
    """
    ViewSet for CostCode CRUD operations.
    
    Filters:
    - active: Show only active cost codes
    - category: Filter by category (labor, material, equipment)
    
    Ordering:
    - code, name, category
    """
    queryset = CostCode.objects.all().order_by('code')
    serializer_class = CostCodeSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['code', 'name', 'category']
    ordering_fields = ['code', 'name', 'category']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        active_only = self.request.query_params.get('active')
        if active_only == 'true':
            queryset = queryset.filter(active=True)
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category=category)
        return queryset


class BudgetLineViewSet(viewsets.ModelViewSet):
    """
    ViewSet for BudgetLine CRUD operations.
    
    Filters:
    - project: Filter by project ID
    - cost_code: Filter by cost code ID
    - allowance: Filter by allowance (true/false)
    
    Ordering:
    - cost_code__code, baseline_amount, revised_amount
    """
    queryset = BudgetLine.objects.select_related('project', 'cost_code').all()
    serializer_class = BudgetLineSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    ordering_fields = ['cost_code__code', 'baseline_amount', 'revised_amount']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        project_id = self.request.query_params.get('project')
        if project_id:
            queryset = queryset.filter(project_id=project_id)
        cost_code_id = self.request.query_params.get('cost_code')
        if cost_code_id:
            queryset = queryset.filter(cost_code_id=cost_code_id)
        allowance = self.request.query_params.get('allowance')
        if allowance == 'true':
            queryset = queryset.filter(allowance=True)
        elif allowance == 'false':
            queryset = queryset.filter(allowance=False)
        return queryset.order_by('cost_code__code')
    
    @action(detail=False, methods=['get'])
    def project_summary(self, request):
        """Get budget summary for a project"""
        project_id = request.query_params.get('project')
        if not project_id:
            return Response({'error': 'project parameter required'}, status=400)
        
        queryset = self.get_queryset().filter(project_id=project_id)
        
        total_baseline = queryset.aggregate(total=Sum('baseline_amount'))['total'] or Decimal('0.00')
        total_revised = queryset.aggregate(total=Sum('revised_amount'))['total'] or Decimal('0.00')
        
        by_cost_code = queryset.values(
            'cost_code__code', 'cost_code__name', 'cost_code__category'
        ).annotate(
            baseline=Sum('baseline_amount'),
            revised=Sum('revised_amount')
        ).order_by('cost_code__code')
        
        return Response({
            'project_id': project_id,
            'total_baseline': total_baseline,
            'total_revised': total_revised,
            'variance': total_revised - total_baseline,
            'by_cost_code': list(by_cost_code),
            'line_count': queryset.count()
        })
