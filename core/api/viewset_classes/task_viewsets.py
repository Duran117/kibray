"""
Task-related viewsets for the Kibray API
"""
from django.db.models import Q
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.api.serializer_classes import (
    TaskListSerializer,
    TaskDetailSerializer,
    TaskCreateUpdateSerializer,
    TaskStatsSerializer,
)
from core.api.filter_classes import TaskFilter
from core.api.permission_classes import IsTaskAssigneeOrProjectMember
from core.models import Task


class TaskViewSet(viewsets.ModelViewSet):
    """
    ViewSet for tasks with full CRUD operations
    """
    queryset = Task.objects.select_related(
        'project', 'assigned_to', 'created_by'
    )
    permission_classes = [IsAuthenticated]
    filterset_class = TaskFilter
    search_fields = ['title', 'description']
    ordering_fields = ['due_date', 'priority', 'created_at', 'status']
    ordering = ['due_date']
    
    def get_queryset(self):
        """Filter queryset based on user permissions"""
        queryset = super().get_queryset()
        user = self.request.user
        
        # Superusers see all tasks
        if user.is_superuser or user.is_staff:
            return queryset
        
        # Filter to tasks assigned to user or in their projects
        return queryset.filter(
            Q(assigned_to__user=user) |
            Q(project__project_lead__user=user) |
            Q(project__observers__user=user)
        ).distinct()
    
    def get_serializer_class(self):
        if self.action == 'list':
            return TaskListSerializer
        elif self.action == 'retrieve':
            return TaskDetailSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return TaskCreateUpdateSerializer
        return TaskDetailSerializer
    
    def get_permissions(self):
        """Add task-specific permissions for certain actions"""
        if self.action in ['update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsTaskAssigneeOrProjectMember()]
        return super().get_permissions()
    
    @action(detail=False, methods=['get'])
    def my_tasks(self, request):
        """Get tasks assigned to current user"""
        user = request.user
        queryset = self.get_queryset().filter(assigned_to__user=user)
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = TaskListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = TaskListSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_status(self, request):
        """Get tasks filtered by status"""
        status_param = request.query_params.get('status')
        if not status_param:
            return Response(
                {'error': 'status parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        queryset = self.get_queryset().filter(status=status_param)
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = TaskListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = TaskListSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def overdue(self, request):
        """Get overdue tasks"""
        today = timezone.now().date()
        queryset = self.get_queryset().filter(
            due_date__lt=today
        ).exclude(status='Completada')
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = TaskListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = TaskListSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """Update task status"""
        task = self.get_object()
        new_status = request.data.get('status')
        
        if not new_status:
            return Response(
                {'error': 'status is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate status
        valid_statuses = ['Pendiente', 'En Progreso', 'Completada', 'Cancelada']
        if new_status not in valid_statuses:
            return Response(
                {'error': f'Invalid status. Must be one of: {", ".join(valid_statuses)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        task.status = new_status
        if new_status == 'Completada':
            task.completed_at = timezone.now()
        task.save()
        
        serializer = self.get_serializer(task)
        return Response(serializer.data)
    
    def perform_create(self, serializer):
        """Set created_by on task creation"""
        serializer.save(created_by=self.request.user)
