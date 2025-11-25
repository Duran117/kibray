from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.request import Request
from django.contrib.auth import get_user_model
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from core.models import (
    Notification, ChatChannel, ChatMessage, Task, DamageReport,
    FloorPlan, PlanPin, ColorSample, Project, ScheduleCategory, ScheduleItem,
    ChangeOrderPhoto
)
from .serializers import (
    NotificationSerializer, ChatChannelSerializer, ChatMessageSerializer,
    TaskSerializer, DamageReportSerializer, FloorPlanSerializer,
    PlanPinSerializer, ColorSampleSerializer, ProjectListSerializer,
    ScheduleCategorySerializer, ScheduleItemSerializer
)

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
        annotations = request.data.get('annotations', [])
        
        # Store annotations as JSON
        photo.annotations = annotations
        photo.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Annotations saved successfully'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)

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
