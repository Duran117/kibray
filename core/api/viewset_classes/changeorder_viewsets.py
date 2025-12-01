"""
ChangeOrder-related viewsets for the Kibray API
"""
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.api.serializer_classes import (
    ChangeOrderListSerializer,
    ChangeOrderDetailSerializer,
    ChangeOrderCreateUpdateSerializer,
    ChangeOrderApprovalSerializer,
)
from core.api.filter_classes import ChangeOrderFilter
from core.api.permission_classes import CanApproveChangeOrder
from core.models import ChangeOrder


class ChangeOrderViewSet(viewsets.ModelViewSet):
    """
    ViewSet for change orders with full CRUD operations
    """
    queryset = ChangeOrder.objects.select_related('project')
    permission_classes = [IsAuthenticated]
    filterset_class = ChangeOrderFilter
    search_fields = ['reference_code', 'description']
    ordering_fields = ['date_created', 'amount', 'status']
    ordering = ['-date_created']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ChangeOrderListSerializer
        elif self.action == 'retrieve':
            return ChangeOrderDetailSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return ChangeOrderCreateUpdateSerializer
        elif self.action in ['approve', 'reject']:
            return ChangeOrderApprovalSerializer
        return ChangeOrderDetailSerializer
    
    def get_permissions(self):
        """Add change-order-specific permissions for certain actions"""
        if self.action in ['approve', 'reject']:
            return [IsAuthenticated(), CanApproveChangeOrder()]
        return super().get_permissions()
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve a change order"""
        change_order = self.get_object()
        notes = request.data.get('notes', '')
        
        if change_order.status == 'approved':
            return Response(
                {'error': 'Change order is already approved'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        change_order.status = 'approved'
        if notes:
            change_order.notes = f"{change_order.notes}\n\nApproval notes: {notes}".strip()
        change_order.save()
        
        # TODO: Create notification/alert for project members
        
        serializer = self.get_serializer_class()(change_order)
        return Response({
            'message': 'Change order approved successfully',
            'change_order': serializer.data
        })
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject a change order"""
        change_order = self.get_object()
        notes = request.data.get('notes', '')
        
        if change_order.status == 'approved':
            return Response(
                {'error': 'Cannot reject an approved change order'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        change_order.status = 'draft'  # Set back to draft
        if notes:
            change_order.notes = f"{change_order.notes}\n\nRejection notes: {notes}".strip()
        change_order.save()
        
        # TODO: Create notification/alert for submitter
        
        serializer = self.get_serializer_class()(change_order)
        return Response({
            'message': 'Change order rejected',
            'change_order': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def pending_approvals(self, request):
        """Get pending change orders"""
        queryset = self.get_queryset().filter(status='pending')
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = ChangeOrderListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = ChangeOrderListSerializer(queryset, many=True)
        return Response(serializer.data)
    
    def perform_create(self, serializer):
        """Set submission date and generate reference code"""
        # Generate next reference code
        project = serializer.validated_data.get('project')
        if project:
            last_co = ChangeOrder.objects.filter(project=project).order_by('-id').first()
            if last_co and last_co.reference_code:
                # Extract number from last code
                try:
                    num = int(last_co.reference_code.split('-')[-1])
                    next_num = num + 1
                except:
                    next_num = 1
            else:
                next_num = 1
            
            reference_code = f"CO-{timezone.now().year}-{next_num:04d}"
            serializer.save(reference_code=reference_code)
        else:
            serializer.save()
