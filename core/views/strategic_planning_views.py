from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils.translation import gettext_lazy as _

from core.models import (
    StrategicPlanningSession,
    StrategicItem,
    StrategicTask
)
from core.serializers.strategic_planning_serializers import (
    StrategicPlanningSessionSerializer,
    StrategicPlanningSessionDetailSerializer,
    StrategicItemSerializer,
    StrategicTaskSerializer
)
from core.services.strategic_planning_service import StrategicPlanningService

class StrategicPlanningSessionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Strategic Planning Sessions.
    """
    permission_classes = [permissions.IsAuthenticated]
    queryset = StrategicPlanningSession.objects.all()
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return StrategicPlanningSessionDetailSerializer
        return StrategicPlanningSessionSerializer

    def perform_create(self, serializer):
        # Use service to create session with auto-generated days
        # We override perform_create to use the service logic
        # Note: DRF's serializer.save() calls model.save(), but we want service.create_session
        pass 

    def create(self, request, *args, **kwargs):
        """Custom create using Service"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            session = StrategicPlanningService.create_session(
                user=request.user,
                project=serializer.validated_data['project'],
                start_date=serializer.validated_data['date_range_start'],
                end_date=serializer.validated_data['date_range_end'],
                notes=serializer.validated_data.get('notes', '')
            )
            
            # Return the created session using the detail serializer
            response_serializer = StrategicPlanningSessionDetailSerializer(session)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """Update session status"""
        session = self.get_object()
        new_status = request.data.get('status')
        if not new_status:
             return Response({'error': 'Status is required'}, status=status.HTTP_400_BAD_REQUEST)
             
        try:
            StrategicPlanningService.update_status(session, new_status, request.user)
            return Response({'status': new_status})
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve the session"""
        session = self.get_object()
        try:
            StrategicPlanningService.update_status(session, 'APPROVED', request.user)
            return Response({'status': 'approved'})
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def export(self, request, pk=None):
        """Export to Daily Plan"""
        session = self.get_object()
        try:
            count = StrategicPlanningService.export_to_daily_plan(session.id, request.user)
            return Response({
                'status': 'exported',
                'activities_created': count
            })
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def calculate_totals(self, request, pk=None):
        """Recalculate totals"""
        try:
            totals = StrategicPlanningService.calculate_session_totals(pk)
            return Response(totals)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def validate(self, request, pk=None):
        """Validate dependencies"""
        try:
            errors = StrategicPlanningService.validate_dependencies(pk)
            return Response({
                'is_valid': len(errors) == 0,
                'errors': errors
            })
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class StrategicItemViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Strategic Items directly.
    """
    permission_classes = [permissions.IsAuthenticated]
    queryset = StrategicItem.objects.all()
    serializer_class = StrategicItemSerializer

    def perform_create(self, serializer):
        # Use service if complex logic needed, or standard save for simple cases
        # For now standard save is fine, but we might want to use service for ordering
        super().perform_create(serializer)
        # Trigger recalculation?
        
    @action(detail=True, methods=['post'])
    def add_task(self, request, pk=None):
        """Add a task to this item"""
        item = self.get_object()
        description = request.data.get('description')
        hours = request.data.get('estimated_hours', 0)
        
        if not description:
            return Response({'error': 'Description required'}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            task = StrategicPlanningService.add_task_to_item(item.id, description, hours)
            return Response(StrategicTaskSerializer(task).data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class StrategicTaskViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Strategic Tasks.
    """
    permission_classes = [permissions.IsAuthenticated]
    queryset = StrategicTask.objects.all()
    serializer_class = StrategicTaskSerializer
