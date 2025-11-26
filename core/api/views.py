from rest_framework import viewsets, status
import json
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.request import Request
from rest_framework import filters
from rest_framework.views import APIView
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
    ChangeOrderPhoto, Income, Expense, CostCode, BudgetLine, DailyLog,
    TaskTemplate, WeatherSnapshot, Employee, DailyPlan, PlannedActivity, TimeEntry,
    MaterialRequest, MaterialRequestItem, MaterialCatalog,
    InventoryItem, InventoryLocation, ProjectInventory, InventoryMovement,
    PayrollPeriod, PayrollRecord, PayrollPayment, SitePhoto
)
from .serializers import (
    NotificationSerializer, ChatChannelSerializer, ChatMessageSerializer,
    TaskSerializer, DamageReportSerializer, FloorPlanSerializer,
    PlanPinSerializer, ColorSampleSerializer, ProjectListSerializer,
    ScheduleCategorySerializer, ScheduleItemSerializer,
    ProjectSerializer, IncomeSerializer, ExpenseSerializer,
    CostCodeSerializer, BudgetLineSerializer, ProjectBudgetSummarySerializer,
    DailyLogPlanningSerializer, TaskTemplateSerializer, WeatherSnapshotSerializer,
    InstantiatePlannedTemplatesSerializer, DailyPlanSerializer, PlannedActivitySerializer,
    TimeEntrySerializer,
    InventoryItemSerializer, InventoryLocationSerializer, ProjectInventorySerializer,
    InventoryMovementSerializer, MaterialRequestSerializer, MaterialRequestItemSerializer,
    MaterialCatalogSerializer,
    InvoiceSerializer, InvoiceLineAPISerializer, InvoicePaymentAPISerializer,
    PayrollPeriodSerializer, PayrollRecordSerializer, PayrollPaymentSerializer,
    TwoFactorSetupSerializer, TwoFactorEnableSerializer, TwoFactorDisableSerializer,
    TwoFactorTokenObtainPairSerializer, SitePhotoSerializer
)
from .filters import IncomeFilter, ExpenseFilter, ProjectFilter, InvoiceFilter
from .pagination import StandardResultsSetPagination
from rest_framework_simplejwt.views import TokenObtainPairView

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
    from rest_framework.parsers import JSONParser
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    
    def get_queryset(self):
        channel_id = self.request.query_params.get('channel')
        qs = ChatMessage.objects.select_related('user', 'channel').order_by('-created_at')
        if channel_id:
            qs = qs.filter(channel_id=channel_id)
        return qs
    
    def perform_create(self, serializer):
        # Save with user and detect mentions to notify
        msg = serializer.save(user=self.request.user)
        # @mentions notifications
        import re
        usernames = set(re.findall(r'@([A-Za-z0-9_\.\-]+)', msg.message or ''))
        if usernames:
            from django.contrib.auth import get_user_model
            from core.models import Notification
            User = get_user_model()
            for uname in usernames:
                try:
                    u = User.objects.get(username=uname)
                    Notification.objects.create(
                        user=u,
                        notification_type='chat_message',
                        title=f"Mention by {self.request.user.username}",
                        message=(msg.message or '')[:200],
                        related_object_type='chat_message',
                        related_object_id=msg.id,
                    )
                except User.DoesNotExist:
                    continue


# Invoices (Module 6) - DRF API
class InvoiceViewSet(viewsets.ModelViewSet):
    serializer_class = InvoiceSerializer
    permission_classes = [IsAuthenticated]
    # Module 6 tests expect an unpaginated list response for list endpoints
    pagination_class = None
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filterset_class = InvoiceFilter
    ordering = ['-date_issued', '-id']
    search_fields = ['invoice_number', 'project__name', 'project__client']

    def get_queryset(self):
        from core.models import Invoice
        return Invoice.objects.select_related('project').prefetch_related('lines', 'payments').order_by('-date_issued', '-id')

    def perform_create(self, serializer):
        serializer.save()

    @action(detail=True, methods=['post'])
    def mark_sent(self, request, pk=None):
        from django.utils import timezone
        invoice = self.get_object()
        if invoice.status == 'DRAFT':
            invoice.status = 'SENT'
            invoice.sent_date = timezone.now()
            invoice.sent_by = request.user if hasattr(invoice, 'sent_by') else None
            invoice.save(update_fields=['status', 'sent_date', 'sent_by'])
            return Response({'status': invoice.status, 'sent_date': invoice.sent_date})
        return Response({'detail': f'Invoice already {invoice.get_status_display()}.'}, status=400)

    @action(detail=True, methods=['post'])
    def mark_approved(self, request, pk=None):
        from django.utils import timezone
        invoice = self.get_object()
        if invoice.status in ['DRAFT', 'SENT', 'VIEWED']:
            invoice.status = 'APPROVED'
            invoice.approved_date = timezone.now()
            invoice.save(update_fields=['status', 'approved_date'])
            return Response({'status': invoice.status, 'approved_date': invoice.approved_date})
        return Response({'detail': f'Invoice status not eligible for approval: {invoice.status}'}, status=400)

    @action(detail=True, methods=['post'])
    def record_payment(self, request, pk=None):
        from core.models import InvoicePayment
        invoice = self.get_object()
        serializer = InvoicePaymentAPISerializer(data={
            **request.data,
            'invoice': invoice.id,
        })
        serializer.is_valid(raise_exception=True)
        payment = serializer.save(recorded_by=request.user)
        return Response(InvoicePaymentAPISerializer(payment).data, status=201)

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
            # Note: assigned_to is Employee; map current user to employee if exists
            from core.models import Employee
            emp = Employee.objects.filter(user=self.request.user).first()
            if emp:
                qs = qs.filter(assigned_to=emp)
            else:
                qs = qs.none()
        return qs
    
    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        task = self.get_object()
        new_status = request.data.get('status')
        if new_status:
            # Module 28: Prevent completing touch-up without photo evidence
            if task.is_touchup and str(new_status).lower() in ['completada', 'completed']:
                # Ensure at least one image exists
                if not task.images.exists():
                    return Response({'error': 'Touch-up requires a photo before completion'}, status=status.HTTP_400_BAD_REQUEST)
            task.status = new_status
            task.save()
            return Response({'status': 'updated'})
        return Response({'error': 'status required'}, status=status.HTTP_400_BAD_REQUEST)

    # ---- Module 11 custom actions ----
    @action(detail=True, methods=['post'])
    def add_dependency(self, request, pk=None):
        """Agregar una dependencia a la tarea (otra task debe completarse antes)."""
        task = self.get_object()
        dep_id = request.data.get('dependency_id')
        if not dep_id:
            return Response({'error': 'dependency_id required'}, status=400)
        if str(task.id) == str(dep_id):
            return Response({'error': 'Task cannot depend on itself'}, status=400)
        dependency = Task.objects.filter(pk=dep_id).first()
        if not dependency:
            return Response({'error': 'Dependency task not found'}, status=404)
        task.dependencies.add(dependency)
        try:
            task.full_clean()  # re-validar ciclos
        except Exception as e:
            task.dependencies.remove(dependency)
            return Response({'error': str(e)}, status=400)
        return Response({'status': 'ok', 'dependencies': list(task.dependencies.values_list('id', flat=True))})

    @action(detail=True, methods=['post'])
    def remove_dependency(self, request, pk=None):
        task = self.get_object()
        dep_id = request.data.get('dependency_id')
        if not dep_id:
            return Response({'error': 'dependency_id required'}, status=400)
        dependency = Task.objects.filter(pk=dep_id).first()
        if not dependency:
            return Response({'error': 'Dependency task not found'}, status=404)
        task.dependencies.remove(dependency)
        return Response({'status': 'ok', 'dependencies': list(task.dependencies.values_list('id', flat=True))})

    @action(detail=True, methods=['post'])
    def reopen(self, request, pk=None):
        """Reabrir una tarea Completada (cambia estado y registra histórico)."""
        task = self.get_object()
        notes = request.data.get('notes', '')
        success = task.reopen(user=request.user, notes=notes)
        if not success:
            return Response({'error': 'Task not in Completada state'}, status=400)
        return Response({'status': 'ok', 'new_status': task.status, 'reopen_events_count': task.reopen_events_count})

    @action(detail=True, methods=['post'])
    def start_tracking(self, request, pk=None):
        task = self.get_object()
        if not task.can_start():
            return Response({'error': 'Dependencies incomplete'}, status=400)
        started = task.start_tracking()
        if not started:
            return Response({'error': 'Already tracking or touch-up'}, status=400)
        return Response({'status': 'ok', 'started_at': task.started_at})

    @action(detail=True, methods=['post'])
    def stop_tracking(self, request, pk=None):
        task = self.get_object()
        elapsed = task.stop_tracking()
        if elapsed is None:
            return Response({'error': 'Not tracking'}, status=400)
        return Response({'status': 'ok', 'elapsed_seconds': elapsed, 'total_hours': task.total_hours})
    
    @action(detail=True, methods=['get'])
    def time_summary(self, request, pk=None):
        """
        Q11.13: Retorna resumen agregado de tiempo trabajado en la tarea.
        
        Incluye:
        - Tracking interno (time_tracked_seconds)
        - TimeEntry registros vinculados
        - Breakdown por empleado
        - Total combinado en horas
        """
        from core.models import TimeEntry
        from django.db.models import Sum, F
        from decimal import Decimal
        
        task = self.get_object()
        
        # Internal tracking (botón inicio/fin)
        internal_hours = task.get_time_tracked_hours()
        
        # TimeEntry aggregation
        time_entries = task.time_entries.select_related('employee', 'employee__user').all()
        
        # Breakdown por empleado
        employee_breakdown = time_entries.values(
            employee_id=F('employee__id'),
            employee_name=F('employee__user__first_name')
        ).annotate(
            hours=Sum('hours_worked')
        ).order_by('-hours')
        
        # Total TimeEntry hours
        time_entry_hours = sum(float(e['hours'] or 0) for e in employee_breakdown)
        
        # Total combinado
        total_hours = round(internal_hours + time_entry_hours, 2)
        
        return Response({
            'task_id': task.id,
            'task_title': task.title,
            'internal_tracking_hours': internal_hours,
            'time_entry_hours': round(time_entry_hours, 2),
            'total_hours': total_hours,
            'employee_breakdown': list(employee_breakdown),
            'is_tracking_active': task.started_at is not None,
            'reopen_count': task.reopen_events_count
        })
        return Response({'status': 'ok', 'elapsed_seconds': elapsed, 'time_tracked_seconds': task.time_tracked_seconds, 'time_tracked_hours': task.get_time_tracked_hours()})

    @action(detail=True, methods=['get'])
    def hours_summary(self, request, pk=None):
        task = self.get_object()
        return Response({
            'task_id': task.id,
            'title': task.title,
            'time_tracked_hours': task.get_time_tracked_hours(),
            'time_entries_hours': task.get_time_entries_hours(),
            'total_hours': task.total_hours
        })

    @action(detail=True, methods=['post'], parser_classes=[MultiPartParser, FormParser])
    def add_image(self, request, pk=None):
        task = self.get_object()
        img = request.FILES.get('image')
        if not img:
            return Response({'error': 'image file required'}, status=400)
        caption = request.data.get('caption', '')
        new_image = task.add_image(image_file=img, uploaded_by=request.user, caption=caption)
        return Response({'status': 'ok', 'image_id': new_image.id, 'version': new_image.version})

    @action(detail=False, methods=['get'])
    def touchup_board(self, request: Request):
        """Return a kanban-style board for touch-up tasks grouped by status.
        Filters:
          - project: Project ID
          - status: one or more status values
          - priority: one or more priority values
          - assigned_to: Employee ID
          - assigned_to_me: true|false (maps current user to Employee)
        Response:
          {
            columns: [
              {key: 'Pendiente', title: 'Pendiente', count: N, items: [...]},
              {key: 'En Progreso', title: 'En Progreso', count: M, items: [...]},
              {key: 'Completada', title: 'Completada', count: K, items: [...]}
            ],
            totals: { total: T, pending: N, in_progress: M, completed: K }
          }
        """
        qs = Task.objects.select_related('project', 'assigned_to').filter(is_touchup=True)
        project_id = request.query_params.get('project')
        if project_id:
            qs = qs.filter(project_id=project_id)
        # status filter (accept multiple via comma or repeated param)
        status_param = request.query_params.getlist('status') or (
            request.query_params.get('status', '').split(',') if request.query_params.get('status') else []
        )
        if status_param:
            qs = qs.filter(status__in=[s for s in status_param if s])
        # priority filter
        priority_param = request.query_params.getlist('priority') or (
            request.query_params.get('priority', '').split(',') if request.query_params.get('priority') else []
        )
        if priority_param:
            qs = qs.filter(priority__in=[p for p in priority_param if p])
        # assigned_to (Employee id)
        assigned_to = request.query_params.get('assigned_to')
        if assigned_to:
            qs = qs.filter(assigned_to_id=assigned_to)
        # assigned_to_me maps current user -> Employee
        assigned_to_me = request.query_params.get('assigned_to_me')
        if assigned_to_me == 'true':
            from core.models import Employee
            emp = Employee.objects.filter(user=request.user).first()
            if emp:
                qs = qs.filter(assigned_to=emp)
            else:
                qs = qs.none()

        # Group by status columns
        statuses = ['Pendiente', 'En Progreso', 'Completada']
        columns = []
        counts = {'pending': 0, 'in_progress': 0, 'completed': 0}
        for s in statuses:
            items_qs = qs.filter(status=s).order_by('-priority', '-created_at')
            items = self.get_serializer(items_qs, many=True).data
            count = len(items)
            if s == 'Pendiente':
                counts['pending'] = count
            elif s == 'En Progreso':
                counts['in_progress'] = count
            elif s == 'Completada':
                counts['completed'] = count
            columns.append({'key': s, 'title': s, 'count': count, 'items': items})

        totals = {'total': sum(counts.values()), **counts}
        return Response({'columns': columns, 'totals': totals})

# Damage Reports
class DamageReportViewSet(viewsets.ModelViewSet):
    serializer_class = DamageReportSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    def get_queryset(self):
        return DamageReport.objects.select_related('project', 'reported_by').order_by('-created_at')
    
    def perform_create(self, serializer):
        serializer.save(reported_by=self.request.user)

# ================================
# Module 16: Payroll API
# ================================

class PayrollPeriodViewSet(viewsets.ModelViewSet):
    serializer_class = PayrollPeriodSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'week_start', 'week_end']
    ordering_fields = ['week_start', 'week_end', 'created_at']

    def get_queryset(self):
        return PayrollPeriod.objects.select_related('created_by', 'approved_by').order_by('-week_start')

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'])
    def validate(self, request, pk=None):
        period = self.get_object()
        errors = period.validate_period()
        return Response({'errors': errors})

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        period = self.get_object()
        skip = request.data.get('skip_validation') in (True, 'true', '1', 1)
        try:
            period.approve(approved_by=request.user, skip_validation=bool(skip))
            return Response({'status': 'approved'})
        except Exception as e:
            return Response({'error': str(e)}, status=400)

    @action(detail=True, methods=['post'])
    def generate_expenses(self, request, pk=None):
        period = self.get_object()
        period.generate_expense_records()
        return Response({'status': 'ok'})


class PayrollRecordViewSet(viewsets.ModelViewSet):
    serializer_class = PayrollRecordSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['period', 'employee', 'week_start', 'week_end', 'reviewed']
    ordering_fields = ['week_start', 'employee__last_name']

    def get_queryset(self):
        return PayrollRecord.objects.select_related('employee', 'period', 'adjusted_by').order_by('-week_start')

    @action(detail=True, methods=['post'])
    def manual_adjust(self, request, pk=None):
        record = self.get_object()
        reason = request.data.get('reason', '')
        updates = request.data.get('updates', {})
        if not isinstance(updates, dict):
            return Response({'error': 'updates must be an object'}, status=400)
        record.manual_adjust(adjusted_by=request.user, reason=reason, **updates)
        return Response(self.get_serializer(record).data)

    @action(detail=True, methods=['post'])
    def create_expense(self, request, pk=None):
        record = self.get_object()
        exp = record.create_expense_record()
        return Response({'expense_id': exp.id})


class PayrollPaymentViewSet(viewsets.ModelViewSet):
    serializer_class = PayrollPaymentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['payroll_record', 'payment_date', 'payment_method']
    ordering_fields = ['payment_date', 'amount']

    def get_queryset(self):
        return PayrollPayment.objects.select_related('payroll_record', 'recorded_by').order_by('-payment_date')

    def perform_create(self, serializer):
        payment = serializer.save(recorded_by=self.request.user)
        # Optional: guard against overpayment
        try:
            if payment.payroll_record.amount_paid() > payment.payroll_record.total_pay:
                return Response({'warning': 'Overpayment detected'}, status=201)
        except Exception:
            pass


# ================================
# Security: 2FA TOTP API
# ================================
class TwoFactorViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['post'])
    def setup(self, request):
        from core.models import TwoFactorProfile
        prof = TwoFactorProfile.get_or_create_for_user(request.user)
        # Ensure secret exists
        uri = prof.provisioning_uri()
        return Response({'secret': prof.secret, 'otpauth_uri': uri})

    @action(detail=False, methods=['post'])
    def enable(self, request):
        from core.models import TwoFactorProfile
        serializer = TwoFactorEnableSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        otp = serializer.validated_data['otp']
        prof = TwoFactorProfile.get_or_create_for_user(request.user)
        if not prof.secret:
            prof.secret = TwoFactorProfile.generate_base32_secret()
        if prof.verify_otp(otp):
            prof.enabled = True
            from django.utils import timezone
            prof.last_verified_at = timezone.now()
            prof.save(update_fields=['enabled', 'secret', 'last_verified_at'])
            return Response({'status': 'enabled'})
        return Response({'error': 'Invalid OTP'}, status=400)

    @action(detail=False, methods=['post'])
    def disable(self, request):
        from core.models import TwoFactorProfile
        serializer = TwoFactorDisableSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        otp = serializer.validated_data['otp']
        prof = TwoFactorProfile.get_or_create_for_user(request.user)
        if not prof.enabled:
            return Response({'status': 'already_disabled'})
        if prof.verify_otp(otp):
            prof.enabled = False
            prof.save(update_fields=['enabled'])
            return Response({'status': 'disabled'})
        return Response({'error': 'Invalid OTP'}, status=400)


class TwoFactorTokenObtainPairView(TokenObtainPairView):
    serializer_class = TwoFactorTokenObtainPairSerializer

# Floor Plans & Pins
class FloorPlanViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = FloorPlanSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None
    
    def get_queryset(self):
        return FloorPlan.objects.prefetch_related('pins').select_related('project').order_by('-created_at')

class PlanPinViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = PlanPinSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None
    
    def get_queryset(self):
        plan_id = self.request.query_params.get('plan')
        pin_type = self.request.query_params.get('pin_type')
        qs = PlanPin.objects.select_related('plan', 'color_sample', 'linked_task').order_by('-created_at')
        if plan_id:
            qs = qs.filter(plan_id=plan_id)
        if pin_type:
            qs = qs.filter(pin_type=pin_type)
        return qs

    @action(detail=True, methods=['post'])
    def comment(self, request, pk=None):
        """Allow clients/staff to add a comment on a pin"""
        pin = self.get_object()
        comment = request.data.get('comment', '').strip()
        if not comment:
            return Response({'detail': 'comment is required'}, status=400)
        pin.add_client_comment(request.user, comment)
        return Response(PlanPinSerializer(pin, context={'request': request}).data)

# Color Samples
class ColorSampleViewSet(viewsets.ModelViewSet):
    serializer_class = ColorSampleSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return ColorSample.objects.select_related('project', 'approved_by', 'rejected_by').order_by('-created_at')

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        from .serializers import ColorSampleApproveSerializer
        sample = self.get_object()
        ser = ColorSampleApproveSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        ip = ser.validated_data.get('signature_ip') or request.META.get('REMOTE_ADDR')
        sample.approve(request.user, ip_address=ip)
        return Response(ColorSampleSerializer(sample, context={'request': request}).data)

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        from .serializers import ColorSampleRejectSerializer
        sample = self.get_object()
        ser = ColorSampleRejectSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        reason = ser.validated_data['reason']
        sample.reject(request.user, reason)
        return Response(ColorSampleSerializer(sample, context={'request': request}).data)

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


# ============================================================================
# PHASE 1: DailyLog Planning API
# ============================================================================

class DailyLogPlanningViewSet(viewsets.ModelViewSet):
    """ViewSet for DailyLog with planning capabilities"""
    queryset = DailyLog.objects.all().prefetch_related(
        'planned_templates', 'planned_tasks', 'project'
    )
    serializer_class = DailyLogPlanningSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['project', 'date', 'is_complete']
    ordering_fields = ['date', 'created_at']
    ordering = ['-date']
    
    @action(detail=True, methods=['post'])
    def instantiate_templates(self, request, pk=None):
        """Instantiate planned templates into tasks"""
        daily_log = self.get_object()
        serializer = InstantiatePlannedTemplatesSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        assigned_to_id = serializer.validated_data.get('assigned_to_id')
        assigned_to = None
        if assigned_to_id:
            assigned_to = get_object_or_404(Employee, pk=assigned_to_id)
        
        created_tasks = daily_log.instantiate_planned_templates(
            created_by=request.user,
            assigned_to=assigned_to
        )
        
        return Response({
            'status': 'ok',
            'created_count': len(created_tasks),
            'tasks': TaskSerializer(created_tasks, many=True).data
        })
    
    @action(detail=True, methods=['post'])
    def evaluate_completion(self, request, pk=None):
        """Evaluate if daily plan is complete"""
        daily_log = self.get_object()
        is_complete = daily_log.evaluate_completion()
        
        return Response({
            'status': 'ok',
            'is_complete': is_complete,
            'incomplete_reason': daily_log.incomplete_reason,
            'summary': {
                'total': daily_log.planned_tasks.count(),
                'completed': daily_log.planned_tasks.filter(status='Completada').count()
            }
        })
    
    @action(detail=True, methods=['get'])
    def weather(self, request, pk=None):
        """Get weather snapshot for this daily log date"""
        daily_log = self.get_object()
        
        # Try to get existing snapshot
        snapshot = WeatherSnapshot.objects.filter(
            project=daily_log.project,
            date=daily_log.date
        ).first()
        
        if snapshot:
            return Response(WeatherSnapshotSerializer(snapshot).data)
        else:
            return Response({
                'message': 'No weather data available for this date'
            }, status=status.HTTP_404_NOT_FOUND)


class TaskTemplateViewSet(viewsets.ModelViewSet):
    """ViewSet for TaskTemplate (Module 29)
    
    Features:
    - Fuzzy search with PostgreSQL trigram
    - Filter by category, tags, favorites, SOP
    - Sort by usage, recent use, creation
    - Bulk import CSV/JSON templates
    """
    queryset = TaskTemplate.objects.filter(is_active=True)
    serializer_class = TaskTemplateSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'is_favorite', 'created_by']
    search_fields = ['title', 'description', 'tags']
    ordering_fields = ['created_at', 'title', 'usage_count', 'last_used']
    ordering = ['-usage_count', '-created_at']
    
    def get_queryset(self):
        """Custom filtering for tags and SOP"""
        from django.db import connection
        import json
        qs = super().get_queryset()
        
        # Filter by tag (supports multiple via comma)
        # Uses JSONField contains for PostgreSQL, text search for SQLite
        tags = self.request.query_params.get('tags')
        if tags:
            tag_list = [t.strip() for t in tags.split(',')]
            
            if connection.vendor == 'postgresql':
                # PostgreSQL: use JSONField contains
                for tag in tag_list:
                    qs = qs.filter(tags__contains=[tag])
            else:
                # SQLite: filter by checking tags field as text
                for tag in tag_list:
                    # This will work for SQLite by checking JSON text representation
                    # Filter templates where tags field contains the tag string
                    qs = qs.extra(
                        where=["tags LIKE %s"],
                        params=[f'%"{tag}"%']
                    )
        
        # Filter by has_sop (boolean)
        has_sop = self.request.query_params.get('has_sop')
        if has_sop is not None:
            if has_sop.lower() in ('true', '1', 'yes'):
                qs = qs.exclude(sop_reference='').exclude(sop_reference__isnull=True)
            else:
                qs = qs.filter(Q(sop_reference='') | Q(sop_reference__isnull=True))
        
        return qs
        
        return qs
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=False, methods=['get'])
    def fuzzy_search(self, request):
        """Advanced fuzzy search using PostgreSQL trigram similarity
        
        Query params:
        - q: search query (min 2 chars)
        - limit: max results (default 20)
        """
        query = request.query_params.get('q', '').strip()
        limit = int(request.query_params.get('limit', 20))
        
        if not query or len(query) < 2:
            return Response(
                {'error': 'Query must be at least 2 characters'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        results = TaskTemplate.fuzzy_search(query, limit=limit)
        serializer = self.get_serializer(results, many=True)
        return Response({
            'count': len(results),
            'query': query,
            'results': serializer.data
        })
    
    @action(detail=False, methods=['post'])
    def bulk_import(self, request):
        """Bulk import templates from CSV or JSON
        
        Expected format (JSON array):
        [
            {
                "title": "Prepare walls",
                "description": "Sand and prime walls",
                "category": "preparation",
                "default_priority": "Medium",
                "estimated_hours": 4.0,
                "tags": ["sanding", "priming"],
                "checklist": ["Check surface", "Apply primer"],
                "sop_reference": "https://..."
            }
        ]
        
        CSV format:
        title,description,category,default_priority,estimated_hours,tags,checklist,sop_reference
        "Prepare walls","Sand...","preparation","Medium",4.0,"sanding,priming","Check,Prime","https://..."
        """
        import csv
        import io
        
        data_format = request.data.get('format', 'json')  # 'json' or 'csv'
        
        if data_format == 'json':
            templates_data = request.data.get('templates', [])
            if not isinstance(templates_data, list):
                return Response(
                    {'error': 'templates must be a list'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        elif data_format == 'csv':
            csv_file = request.FILES.get('file')
            if not csv_file:
                return Response(
                    {'error': 'file is required for CSV import'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Parse CSV
            decoded_file = csv_file.read().decode('utf-8')
            csv_reader = csv.DictReader(io.StringIO(decoded_file))
            templates_data = []
            for row in csv_reader:
                # Convert CSV strings to proper types
                template = {
                    'title': row.get('title', '').strip(),
                    'description': row.get('description', '').strip(),
                    'category': row.get('category', 'other').strip(),
                    'default_priority': row.get('default_priority', 'Medium').strip(),
                    'estimated_hours': float(row.get('estimated_hours', 0)) if row.get('estimated_hours') else None,
                    'tags': [t.strip() for t in row.get('tags', '').split(',') if t.strip()],
                    'checklist': [c.strip() for c in row.get('checklist', '').split(',') if c.strip()],
                    'sop_reference': row.get('sop_reference', '').strip(),
                }
                templates_data.append(template)
        else:
            return Response(
                {'error': 'format must be json or csv'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate and create
        created = []
        errors = []
        
        for idx, template_data in enumerate(templates_data):
            serializer = self.get_serializer(data=template_data)
            if serializer.is_valid():
                serializer.save(created_by=request.user)
                created.append(serializer.data)
            else:
                errors.append({
                    'index': idx,
                    'data': template_data,
                    'errors': serializer.errors
                })
        
        return Response({
            'created': len(created),
            'failed': len(errors),
            'created_templates': created,
            'errors': errors
        }, status=status.HTTP_201_CREATED if created else status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def toggle_favorite(self, request, pk=None):
        """Toggle is_favorite status"""
        template = self.get_object()
        template.is_favorite = not template.is_favorite
        template.save(update_fields=['is_favorite'])
        return Response({
            'id': template.id,
            'is_favorite': template.is_favorite
        })
    
    @action(detail=True, methods=['post'])
    def create_task(self, request, pk=None):
        """Create a task from this template (updates usage stats automatically)"""
        template = self.get_object()
        project_id = request.data.get('project_id')
        assigned_to_id = request.data.get('assigned_to_id')
        
        if not project_id:
            return Response(
                {'error': 'project_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        project = get_object_or_404(Project, pk=project_id)
        assigned_to = None
        if assigned_to_id:
            assigned_to = get_object_or_404(Employee, pk=assigned_to_id)
        
        task = template.create_task(
            project=project,
            created_by=request.user,
            assigned_to=assigned_to
        )
        
        return Response(
            TaskSerializer(task).data,
            status=status.HTTP_201_CREATED
        )


# ============================================================================
# PHASE 2: Daily Plans (Module 12)
# ============================================================================

class DailyPlanViewSet(viewsets.ModelViewSet):
    """ViewSet for DailyPlan (Module 12)"""
    queryset = DailyPlan.objects.all().select_related('project', 'created_by').prefetch_related('activities')
    serializer_class = DailyPlanSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['project', 'plan_date', 'status', 'admin_approved']
    search_fields = ['project__name', 'no_planning_reason']
    ordering_fields = ['plan_date', 'created_at', 'updated_at']
    ordering = ['-plan_date']

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'])
    def fetch_weather(self, request, pk=None):
        """Fetch and attach weather data to the plan"""
        plan = self.get_object()
        data = plan.fetch_weather()
        if data is None:
            return Response({'message': 'Weather not available'}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'weather': data, 'weather_fetched_at': plan.weather_fetched_at})

    @action(detail=True, methods=['post'])
    def convert_activities(self, request, pk=None):
        """Convert planned activities to real project tasks"""
        plan = self.get_object()
        tasks = plan.convert_activities_to_tasks(user=request.user)
        return Response({
            'created_count': len(tasks),
            'tasks': TaskSerializer(tasks, many=True).data
        })

    @action(detail=True, methods=['get'])
    def productivity(self, request, pk=None):
        plan = self.get_object()
        score = plan.calculate_productivity_score()
        return Response({'productivity_score': score})

    @action(detail=True, methods=['post'])
    def add_activity(self, request, pk=None):
        plan = self.get_object()
        serializer = PlannedActivitySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        activity = serializer.save(daily_plan=plan)
        return Response(PlannedActivitySerializer(activity).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def recompute_actual_hours(self, request, pk=None):
        """Sum hours from time entries linked to tasks converted from this plan's activities."""
        from django.db.models import Sum
        plan = self.get_object()
        task_ids = list(plan.activities.exclude(converted_task__isnull=True).values_list('converted_task_id', flat=True))
        total = TimeEntry.objects.filter(task_id__in=task_ids).aggregate(s=Sum('hours_worked'))['s'] or 0
        plan.actual_hours_worked = total
        plan.save(update_fields=['actual_hours_worked'])
        return Response({
            'actual_hours_worked': float(total) if total is not None else 0.0,
            'task_count': len(task_ids)
        })


class PlannedActivityViewSet(viewsets.ModelViewSet):
    """CRUD for PlannedActivity with material checks"""
    queryset = PlannedActivity.objects.all().select_related('daily_plan', 'schedule_item', 'activity_template').prefetch_related('assigned_employees')
    serializer_class = PlannedActivitySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['daily_plan', 'status']
    search_fields = ['title', 'description']
    ordering_fields = ['order', 'created_at', 'updated_at']
    ordering = ['order']

    @action(detail=True, methods=['post'])
    def check_materials(self, request, pk=None):
        activity = self.get_object()
        activity.check_materials()
        return Response({
            'materials_checked': activity.materials_checked,
            'material_shortage': activity.material_shortage,
            'description': activity.description
        })

    @action(detail=True, methods=['get'])
    def variance(self, request, pk=None):
        """Compute variance using estimated vs actual hours. If actual_hours is None, compute from converted_task time entries."""
        from django.db.models import Sum
        activity = self.get_object()
        actual = activity.actual_hours
        if actual is None and activity.converted_task_id:
            actual = TimeEntry.objects.filter(task_id=activity.converted_task_id).aggregate(s=Sum('hours_worked'))['s']
        if activity.estimated_hours and actual is not None:
            try:
                est = float(activity.estimated_hours)
                act = float(actual)
                variance_hours = round(est - act, 2)
                variance_pct = round(((variance_hours) / est) * 100, 1) if est else None
                return Response({
                    'variance_hours': variance_hours,
                    'variance_percentage': variance_pct,
                    'is_efficient': variance_hours > 0
                })
            except Exception:
                pass
        return Response({'detail': 'Insufficient data for variance'}, status=status.HTTP_400_BAD_REQUEST)


class WeatherSnapshotViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for WeatherSnapshot (Module 30)"""
    queryset = WeatherSnapshot.objects.all()
    serializer_class = WeatherSnapshotSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['project', 'date', 'source']
    ordering_fields = ['date', 'fetched_at']
    ordering = ['-date']
    
    @action(detail=False, methods=['get'])
    def by_project_date(self, request):
        """Get weather snapshot for specific project and date"""
        project_id = request.query_params.get('project_id')
        date = request.query_params.get('date')
        
        if not project_id or not date:
            return Response(
                {'error': 'project_id and date are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        snapshot = WeatherSnapshot.objects.filter(
            project_id=project_id,
            date=date
        ).first()
        
        if snapshot:
            return Response(WeatherSnapshotSerializer(snapshot).data)
        else:
            return Response(
                {'message': 'No weather data available'},
                status=status.HTTP_404_NOT_FOUND
            )


# ============================================================================
# Module 13: TimeEntry API
# ============================================================================

class TimeEntryViewSet(viewsets.ModelViewSet):
    queryset = TimeEntry.objects.all().select_related('employee', 'project', 'task')
    serializer_class = TimeEntrySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['employee', 'project', 'date']
    search_fields = ['notes', 'task__title', 'project__name', 'employee__first_name', 'employee__last_name']
    ordering_fields = ['date', 'start_time', 'end_time', 'hours_worked']
    ordering = ['-date', '-start_time']

    @action(detail=True, methods=['post'])
    def stop(self, request, pk=None):
        """Stop an open time entry by setting end_time; accepts optional end_time in payload (HH:MM[:SS])."""
        entry = self.get_object()
        end_time = request.data.get('end_time')
        from datetime import datetime
        from django.utils import timezone
        if end_time:
            try:
                fmt = '%H:%M:%S' if len(end_time.split(':')) == 3 else '%H:%M'
                entry.end_time = datetime.strptime(end_time, fmt).time()
            except Exception:
                return Response({'detail': 'Invalid end_time format'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            entry.end_time = timezone.localtime().time()
        entry.save()
        return Response(TimeEntrySerializer(entry).data)

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Aggregate total hours by grouping key (employee|project|task). Example: /time-entries/summary/?group=task&project=<id>"""
        from django.db.models import Sum
        group = request.query_params.get('group', 'employee')
        qs = self.filter_queryset(self.get_queryset())
        if group == 'project':
            data = qs.values('project').annotate(total_hours=Sum('hours_worked')).order_by('project')
        elif group == 'task':
            data = qs.values('task').annotate(total_hours=Sum('hours_worked')).order_by('task')
        else:
            data = qs.values('employee').annotate(total_hours=Sum('hours_worked')).order_by('employee')
        normalized = []
        for row in data:
            row = dict(row)
            if row.get('total_hours') is not None:
                row['total_hours'] = str(row['total_hours'])
            normalized.append(row)
        return Response(normalized)


# ============================================================================
# Module 14: Materials & Inventory API
# ============================================================================

class InventoryItemViewSet(viewsets.ModelViewSet):
    queryset = InventoryItem.objects.all().order_by('name')
    serializer_class = InventoryItemSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'active', 'is_equipment']
    search_fields = ['name', 'sku']
    ordering_fields = ['name', 'created_at']


class InventoryLocationViewSet(viewsets.ModelViewSet):
    queryset = InventoryLocation.objects.select_related('project').all().order_by('-is_storage', 'name')
    serializer_class = InventoryLocationSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['project', 'is_storage']
    search_fields = ['name', 'project__name']
    ordering_fields = ['name']


class ProjectInventoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ProjectInventory.objects.select_related('item', 'location', 'location__project').all()
    serializer_class = ProjectInventorySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['item', 'location', 'location__project']
    search_fields = ['item__name', 'location__name', 'location__project__name']
    ordering_fields = ['quantity']
    ordering = ['-quantity']


class InventoryMovementViewSet(viewsets.ModelViewSet):
    queryset = InventoryMovement.objects.select_related('item', 'from_location', 'to_location', 'related_task', 'related_project').all().order_by('-created_at')
    serializer_class = InventoryMovementSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['item', 'movement_type', 'related_project', 'from_location', 'to_location']
    search_fields = ['item__name', 'reason', 'note']
    ordering_fields = ['created_at', 'quantity']

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class MaterialCatalogViewSet(viewsets.ModelViewSet):
    queryset = MaterialCatalog.objects.select_related('project').all().order_by('-created_at')
    serializer_class = MaterialCatalogSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['project', 'category', 'is_active']
    search_fields = ['brand_text', 'product_name', 'color_name', 'color_code']
    ordering_fields = ['created_at', 'brand_text', 'product_name']

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class MaterialRequestViewSet(viewsets.ModelViewSet):
    queryset = MaterialRequest.objects.select_related('project', 'requested_by', 'approved_by').prefetch_related('items').all().order_by('-created_at')
    serializer_class = MaterialRequestSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['project', 'status', 'approved_by']
    search_fields = ['project__name', 'notes']
    ordering_fields = ['created_at', 'status']

    def perform_create(self, serializer):
        serializer.save(requested_by=self.request.user)

    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        mr = self.get_object()
        ok = mr.submit_for_approval(user=request.user)
        return Response({'status': mr.status, 'ok': ok})

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        mr = self.get_object()
        if not request.user.is_staff:
            return Response({'detail': 'Admin only'}, status=status.HTTP_403_FORBIDDEN)
        ok = mr.approve(admin_user=request.user)
        return Response({'status': mr.status, 'ok': ok})

    @action(detail=True, methods=['post'])
    def mark_ordered(self, request, pk=None):
        mr = self.get_object()
        ok = mr.mark_ordered(user=request.user)
        return Response({'status': mr.status, 'ok': ok})

    @action(detail=True, methods=['post'])
    def receive(self, request, pk=None):
        """Payload: {"items": [{"id": <item_id>, "received_quantity": <qty>}, ...]}"""
        mr = self.get_object()
        items = request.data.get('items', [])
        mapping = {}
        for it in items:
            try:
                iid = int(it.get('id'))
                qty = Decimal(str(it.get('received_quantity', 0)))
                if qty > 0:
                    mapping[iid] = qty
            except Exception:
                continue
        ok, msg = mr.receive_materials(mapping, user=request.user)
        return Response({'ok': ok, 'message': msg, 'status': mr.status})

    @action(detail=True, methods=['post'])
    def direct_purchase_expense(self, request, pk=None):
        """Create an expense for this request and receive all items directly.
        Payload: {"total_amount": 123.45}
        """
        mr = self.get_object()
        try:
            total = Decimal(str(request.data.get('total_amount')))
        except Exception:
            return Response({'detail': 'total_amount required'}, status=status.HTTP_400_BAD_REQUEST)
        expense = mr.create_direct_purchase_expense(total_amount=total, user=request.user)
        return Response({'expense_id': expense.id, 'status': mr.status})


class ClientRequestViewSet(viewsets.ModelViewSet):
    """Client Requests: Material, Change Order, Info"""
    from core.models import ClientRequest as Model
    from core.api.serializers import ClientRequestSerializer as Serializer

    queryset = Model.objects.select_related('project', 'created_by').all().order_by('-created_at')
    serializer_class = Serializer
    # Unpaginated for list endpoints to match tests pattern
    pagination_class = None
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['project', 'request_type', 'status']
    search_fields = ['title', 'description', 'project__name']
    ordering_fields = ['created_at', 'status']

    def perform_create(self, serializer):
        # Only staff or users with project access can create for that project
        project = serializer.validated_data.get('project')
        user = self.request.user
        if not user.is_staff:
            from core.models import ClientProjectAccess
            has_access = ClientProjectAccess.objects.filter(user=user, project=project).exists()
            if not has_access:
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied('No access to project')
        serializer.save(created_by=user)

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if user.is_staff:
            return qs
        # Restrict to projects the user has access to
        from core.models import ClientProjectAccess
        project_ids = ClientProjectAccess.objects.filter(user=user).values_list('project_id', flat=True)
        return qs.filter(project_id__in=list(project_ids))

    @action(detail=True, methods=['post'])
        
    def approve(self, request, pk=None):
        cr = self.get_object()
        if cr.status == 'pending':
            cr.status = 'approved'
            cr.save(update_fields=['status'])
        return Response({'status': cr.status})

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        cr = self.get_object()
        if cr.status in ['pending', 'approved']:
            cr.status = 'rejected'
            cr.save(update_fields=['status'])
        return Response({'status': cr.status})


class ClientRequestAttachmentViewSet(viewsets.ModelViewSet):
    from core.models import ClientRequestAttachment as Model
    from core.api.serializers import ClientRequestAttachmentSerializer as Serializer

    queryset = Model.objects.select_related('request', 'uploaded_by').all().order_by('-uploaded_at')
    serializer_class = Serializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['request']
    ordering_fields = ['uploaded_at', 'size_bytes']
    pagination_class = None

    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user)


class SitePhotoViewSet(viewsets.ModelViewSet):
    queryset = SitePhoto.objects.select_related('project', 'damage_report', 'created_by').all().order_by('-created_at')
    serializer_class = SitePhotoSerializer
    permission_classes = [IsAuthenticated]
    from rest_framework.parsers import JSONParser
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['project', 'damage_report', 'photo_type']
    search_fields = ['caption', 'notes', 'project__name']
    ordering_fields = ['created_at']
    pagination_class = None

    def get_queryset(self):
        qs = super().get_queryset()
        # Optional date range filter
        start = self.request.query_params.get('start')
        end = self.request.query_params.get('end')
        from django.utils.dateparse import parse_datetime, parse_date
        if start:
            dt = parse_datetime(start) or parse_date(start)
            if dt:
                qs = qs.filter(created_at__gte=dt)
        if end:
            dt = parse_datetime(end) or parse_date(end)
            if dt:
                qs = qs.filter(created_at__lte=dt)
        return qs

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


# ============================================================================
# FASE 7: Dashboards (basic API overviews)
# ============================================================================

class InvoiceDashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request):
        from core.models import Invoice
        from django.db.models import Sum, Count
        qs = Invoice.objects.all()
        total_invoices = qs.count()
        total_amount = qs.aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
        paid_amount = qs.filter(status='PAID').aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
        overdue_count = qs.filter(status='OVERDUE').count()
        outstanding = total_amount - paid_amount
        # Top clients by invoiced amount (by project.client)
        top_clients = list(
            qs.values('project__client').annotate(total=Sum('total_amount'), count=Count('id'))
            .order_by('-total')[:5]
        )
        return Response({
            'total_invoices': total_invoices,
            'total_amount': total_amount,
            'paid_amount': paid_amount,
            'outstanding_amount': outstanding,
            'overdue_count': overdue_count,
            'top_clients': top_clients,
        })


class InvoiceTrendsView(APIView):
    """Monthly invoice trends and aging report"""
    permission_classes = [IsAuthenticated]

    def get(self, request: Request):
        from core.models import Invoice
        from django.db.models import Sum, Count
        from django.utils import timezone
        from datetime import timedelta
        from dateutil.relativedelta import relativedelta

        # Monthly trends (last 6 months)
        today = timezone.now().date()
        monthly_trends = []
        for i in range(6):
            month_start = (today.replace(day=1) - relativedelta(months=i))
            month_end = (month_start + relativedelta(months=1) - timedelta(days=1))
            
            month_invoices = Invoice.objects.filter(date_issued__range=[month_start, month_end])
            total_invoiced = month_invoices.aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
            total_paid = month_invoices.filter(status='PAID').aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
            total_overdue = month_invoices.filter(status='OVERDUE').aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
            
            monthly_trends.append({
                'month': month_start.strftime('%Y-%m'),
                'month_label': month_start.strftime('%B %Y'),
                'total_invoiced': total_invoiced,
                'total_paid': total_paid,
                'total_overdue': total_overdue,
                'invoice_count': month_invoices.count(),
            })
        
        monthly_trends.reverse()  # Oldest first

        # Aging report (outstanding invoices by days overdue)
        outstanding = Invoice.objects.filter(status__in=['SENT', 'VIEWED', 'APPROVED', 'PARTIAL', 'OVERDUE'])
        aging_buckets = {
            '0-30': Decimal('0.00'),
            '31-60': Decimal('0.00'),
            '61-90': Decimal('0.00'),
            '90+': Decimal('0.00'),
        }
        
        for inv in outstanding:
            balance = inv.balance_due
            if balance <= 0:
                continue
            
            if inv.due_date:
                days_overdue = (today - inv.due_date).days
                if days_overdue <= 30:
                    aging_buckets['0-30'] += balance
                elif days_overdue <= 60:
                    aging_buckets['31-60'] += balance
                elif days_overdue <= 90:
                    aging_buckets['61-90'] += balance
                else:
                    aging_buckets['90+'] += balance
            else:
                # No due date, count as current
                aging_buckets['0-30'] += balance

        return Response({
            'monthly_trends': monthly_trends,
            'aging_report': aging_buckets,
        })



class MaterialsDashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request):
        from core.models import InventoryItem, ProjectInventory, InventoryMovement
        from django.db.models import Sum, Count
        # Totals
        total_items = InventoryItem.objects.filter(active=True).count()
        # Low stock items (any stock record below threshold)
        low_stock = ProjectInventory.objects.all()
        low_stock_count = sum(1 for s in low_stock if s.is_below)
        # Stock value using avg cost
        stocks = ProjectInventory.objects.select_related('item')
        total_stock_value = Decimal('0.00')
        for s in stocks:
            if s.item and s.item.average_cost is not None and s.quantity is not None:
                total_stock_value += (s.item.average_cost * s.quantity)
        # Recent movements
        recent_movements = InventoryMovement.objects.count()
        # Items by category
        by_category = list(
            InventoryItem.objects.values('category').annotate(count=Count('id')).order_by('-count')
        )
        return Response({
            'total_items': total_items,
            'low_stock_count': low_stock_count,
            'total_stock_value': total_stock_value,
            'recent_movements': recent_movements,
            'items_by_category': by_category,
        })


class MaterialsUsageAnalyticsView(APIView):
    """Materials usage analytics: top consumed, consumption by project, turnover, reorder suggestions"""
    permission_classes = [IsAuthenticated]

    def get(self, request: Request):
        from core.models import InventoryItem, InventoryMovement, ProjectInventory
        from django.db.models import Sum, Q, Count
        from django.utils import timezone
        from datetime import timedelta

        # Top consumed items (ISSUE and CONSUME movements)
        consumption_movements = InventoryMovement.objects.filter(
            movement_type__in=['ISSUE', 'CONSUME']
        )
        top_consumed = list(
            consumption_movements.values('item__name', 'item__id')
            .annotate(total_consumed=Sum('quantity'))
            .order_by('-total_consumed')[:10]
        )

        # Consumption breakdown by project
        project_consumption = list(
            consumption_movements.filter(related_project__isnull=False)
            .values('related_project__name', 'related_project__id')
            .annotate(total_consumed=Sum('quantity'), item_count=Count('item', distinct=True))
            .order_by('-total_consumed')[:10]
        )

        # Stock turnover calculation (consumption in last 30 days / average stock)
        thirty_days_ago = timezone.now() - timedelta(days=30)
        recent_consumption = consumption_movements.filter(created_at__gte=thirty_days_ago)
        
        turnover_items = []
        for item in InventoryItem.objects.filter(active=True):
            consumed = recent_consumption.filter(item=item).aggregate(total=Sum('quantity'))['total'] or Decimal('0')
            # Average stock across all locations
            avg_stock = ProjectInventory.objects.filter(item=item).aggregate(avg=Sum('quantity'))['avg'] or Decimal('0')
            
            if avg_stock > 0:
                turnover_rate = (consumed / avg_stock) if avg_stock != 0 else Decimal('0')
                turnover_items.append({
                    'item_id': item.id,
                    'item_name': item.name,
                    'consumed_30d': consumed,
                    'average_stock': avg_stock,
                    'turnover_rate': turnover_rate,
                })
        
        # Sort by turnover rate descending
        turnover_items.sort(key=lambda x: x['turnover_rate'], reverse=True)
        turnover_items = turnover_items[:15]  # Top 15

        # Reorder suggestions (items below threshold + high consumption rate)
        reorder_suggestions = []
        for stock in ProjectInventory.objects.select_related('item', 'location').all():
            if stock.is_below:
                # Calculate consumption rate (last 30 days)
                location_filter = Q(from_location=stock.location) | Q(to_location=stock.location)
                consumed = recent_consumption.filter(
                    location_filter,
                    item=stock.item
                ).aggregate(total=Sum('quantity'))['total'] or Decimal('0')
                
                consumption_rate = consumed / 30 if consumed > 0 else Decimal('0')
                # Days until depleted
                days_until_depleted = (stock.quantity / consumption_rate) if consumption_rate > 0 else None
                
                threshold = stock.threshold()
                reorder_suggestions.append({
                    'item_id': stock.item.id,
                    'item_name': stock.item.name,
                    'location_name': stock.location.name if stock.location else 'N/A',
                    'current_quantity': stock.quantity,
                    'threshold': threshold,
                    'consumption_rate_per_day': consumption_rate,
                    'days_until_depleted': days_until_depleted,
                    'suggested_order_qty': max(threshold * 2, consumed) if consumed > 0 else threshold * 2,
                })
        
        # Sort by urgency (days until depleted)
        reorder_suggestions.sort(key=lambda x: x['days_until_depleted'] if x['days_until_depleted'] else 9999)

        return Response({
            'top_consumed': top_consumed,
            'consumption_by_project': project_consumption,
            'stock_turnover': turnover_items,
            'reorder_suggestions': reorder_suggestions,
        })


class FinancialDashboardView(APIView):
    """Per-project financial summary with EV metrics and budget tracking"""
    permission_classes = [IsAuthenticated]

    def get(self, request: Request):
        from core.models import Project, Income, Expense
        from django.db.models import Sum, Q
        from datetime import datetime, date
        
        # Filters
        project_id = request.query_params.get('project')
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        
        qs = Project.objects.all()
        if project_id:
            qs = qs.filter(id=project_id)
        
        # Date filters for aggregates
        income_filter = Q()
        expense_filter = Q()
        if date_from:
            try:
                df = datetime.strptime(date_from, '%Y-%m-%d').date()
                income_filter &= Q(date__gte=df)
                expense_filter &= Q(date__gte=df)
            except Exception:
                pass
        if date_to:
            try:
                dt = datetime.strptime(date_to, '%Y-%m-%d').date()
                income_filter &= Q(date__lte=dt)
                expense_filter &= Q(date__lte=dt)
            except Exception:
                pass
        
        projects_data = []
        for proj in qs:
            income_total = proj.incomes.filter(income_filter).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
            expense_total = proj.expenses.filter(expense_filter).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
            profit = income_total - expense_total
            budget_used_pct = round((expense_total / proj.budget_total * 100) if proj.budget_total > 0 else 0, 2)
            
            # EV metrics (if available)
            ev_summary = None
            try:
                ev_summary = proj.earned_value_summary()
            except Exception:
                pass
            
            projects_data.append({
                'project_id': proj.id,
                'project_name': proj.name,
                'client': proj.client,
                'total_income': income_total,
                'total_expenses': expense_total,
                'profit': profit,
                'budget_total': proj.budget_total,
                'budget_used_percent': budget_used_pct,
                'is_over_budget': expense_total > proj.budget_total,
                'ev_metrics': ev_summary,
            })
        
        return Response({
            'projects': projects_data,
            'total_projects': len(projects_data),
        })


class PayrollDashboardView(APIView):
    """Weekly payroll overview: periods, totals, outstanding"""
    permission_classes = [IsAuthenticated]

    def get(self, request: Request):
        from core.models import PayrollPeriod, PayrollRecord, PayrollPayment, Employee
        from django.db.models import Sum, Count
        
        periods = PayrollPeriod.objects.all().order_by('-week_start')[:8]
        periods_data = []
        total_cost = Decimal('0.00')
        total_outstanding = Decimal('0.00')
        
        for period in periods:
            records = period.records.all()
            period_total = records.aggregate(total=Sum('total_pay'))['total'] or Decimal('0.00')
            # Payments are linked to PayrollRecord, not PayrollPeriod
            paid_total = PayrollPayment.objects.filter(payroll_record__period=period).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
            outstanding = period_total - paid_total
            
            periods_data.append({
                'period_id': period.id,
                'week_start': period.week_start.isoformat(),
                'week_end': period.week_end.isoformat(),
                'status': period.status,
                'employee_count': records.count(),
                'total_payroll': period_total,
                'paid': paid_total,
                'outstanding': outstanding,
            })
            
            total_cost += period_total
            total_outstanding += outstanding
        
        # Employee breakdown (top by hours)
        top_employees = list(
            PayrollRecord.objects.values('employee__first_name', 'employee__last_name')
            .annotate(total_hours=Sum('total_hours'), total_pay=Sum('total_pay'))
            .order_by('-total_hours')[:10]
        )
        
        return Response({
            'recent_periods': periods_data,
            'total_payroll_cost': total_cost,
            'total_outstanding': total_outstanding,
            'top_employees': top_employees,
        })


class AdminDashboardView(APIView):
    """Company-wide consolidated dashboard: projects, employees, financial health, recent activity"""
    permission_classes = [IsAuthenticated]

    def get(self, request: Request):
        from core.models import (
            Project, Employee, Invoice, Income, Expense,
            Task, TimeEntry, InventoryItem, PayrollPeriod, DailyLog
        )
        from django.db.models import Sum, Count, Q
        from django.utils import timezone
        from datetime import timedelta

        # Project summary
        active_projects = Project.objects.filter(end_date__isnull=True).count()
        total_projects = Project.objects.count()
        completed_projects = Project.objects.filter(end_date__isnull=False).count()

        # Employee summary
        active_employees = Employee.objects.filter(is_active=True).count()
        total_employees = Employee.objects.count()

        # Financial summary
        total_income = Income.objects.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        total_expenses = Expense.objects.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        net_profit = total_income - total_expenses
        profit_margin = (net_profit / total_income * 100) if total_income > 0 else Decimal('0.00')

        # Invoice summary
        total_invoiced = Invoice.objects.aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
        total_paid = Invoice.objects.filter(status='PAID').aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
        outstanding_invoices = total_invoiced - total_paid
        overdue_invoices = Invoice.objects.filter(status='OVERDUE').count()

        # Inventory summary
        total_inventory_items = InventoryItem.objects.filter(active=True).count()
        
        # Recent activity feed (last 10 items)
        thirty_days_ago = timezone.now() - timedelta(days=30)
        recent_activity = []

        # Recent projects
        for proj in Project.objects.order_by('-created_at')[:3]:
            recent_activity.append({
                'type': 'project',
                'date': proj.created_at.isoformat() if proj.created_at else None,
                'description': f"Project created: {proj.name}",
                'project_id': proj.id,
            })

        # Recent tasks
        for task in Task.objects.order_by('-created_at')[:3]:
            recent_activity.append({
                'type': 'task',
                'date': task.created_at.isoformat() if task.created_at else None,
                'description': f"Task: {task.title}",
                'project_id': task.project_id if hasattr(task, 'project_id') else None,
            })

        # Recent invoices
        for inv in Invoice.objects.order_by('-date_issued')[:3]:
            recent_activity.append({
                'type': 'invoice',
                'date': inv.date_issued.isoformat(),
                'description': f"Invoice {inv.invoice_number}: ${inv.total_amount}",
                'project_id': inv.project_id,
            })

        # Recent daily logs
        for log in DailyLog.objects.order_by('-date')[:3]:
            recent_activity.append({
                'type': 'daily_log',
                'date': log.date.isoformat(),
                'description': f"Daily log: {log.progress_notes[:50] if log.progress_notes else 'No notes'}",
                'project_id': log.project_id,
            })

        # Sort by date descending and limit to 10
        recent_activity.sort(key=lambda x: x['date'] if x['date'] else '', reverse=True)
        recent_activity = recent_activity[:10]

        # Financial health score (0-100)
        # Based on: profit margin, invoice collection rate, budget adherence
        collection_rate = (total_paid / total_invoiced * 100) if total_invoiced > 0 else Decimal('100')
        
        # Weighted health score
        health_score = Decimal('0')
        health_score += max(min(profit_margin, 50), 0)  # Max 50 points for profit margin (0-50%)
        health_score += collection_rate * Decimal('0.5')  # Max 50 points for collection (100% = 50 pts)
        health_score = min(health_score, Decimal('100'))

        return Response({
            'projects': {
                'active': active_projects,
                'completed': completed_projects,
                'total': total_projects,
            },
            'employees': {
                'active': active_employees,
                'total': total_employees,
            },
            'financial': {
                'total_income': total_income,
                'total_expenses': total_expenses,
                'net_profit': net_profit,
                'profit_margin': profit_margin,
                'total_invoiced': total_invoiced,
                'total_paid': total_paid,
                'outstanding': outstanding_invoices,
                'overdue_count': overdue_invoices,
                'collection_rate': collection_rate,
            },
            'inventory': {
                'total_items': total_inventory_items,
            },
            'recent_activity': recent_activity,
            'health_score': health_score,
        })






