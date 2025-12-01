"""
Project-related viewsets for the Kibray API
"""
from django.db.models import Q, Count, Sum
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.api.serializer_classes import (
    ProjectListSerializer,
    ProjectDetailSerializer,
    ProjectCreateUpdateSerializer,
    ProjectStatsSerializer,
)
from core.api.filter_classes import ProjectFilter
from core.api.permission_classes import IsProjectMember
from core.models import Project


class ProjectViewSet(viewsets.ModelViewSet):
    """
    ViewSet for projects with full CRUD operations
    """
    queryset = Project.objects.select_related(
        'billing_organization', 'project_lead'
    ).prefetch_related('observers')
    permission_classes = [IsAuthenticated]
    filterset_class = ProjectFilter
    search_fields = ['name', 'address', 'description', 'client']
    ordering_fields = ['name', 'start_date', 'end_date', 'created_at']
    ordering = ['name']
    
    def get_queryset(self):
        """Filter queryset based on user permissions"""
        queryset = super().get_queryset()
        user = self.request.user
        
        # Superusers see all projects
        if user.is_superuser or user.is_staff:
            return queryset
        
        # Filter to projects where user is lead or observer
        # Note: This uses ClientContact, which may have a link to User
        return queryset.filter(
            Q(project_lead__user=user) | Q(observers__user=user)
        ).distinct()
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ProjectListSerializer
        elif self.action == 'retrieve':
            return ProjectDetailSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return ProjectCreateUpdateSerializer
        return ProjectDetailSerializer
    
    def get_permissions(self):
        """Add project-specific permissions for certain actions"""
        if self.action in ['retrieve', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsProjectMember()]
        return super().get_permissions()
    
    @action(detail=False, methods=['get'])
    def assigned_projects(self, request):
        """Get projects where user is assigned"""
        user = request.user
        queryset = Project.objects.filter(
            Q(project_lead__user=user) | Q(observers__user=user)
        ).distinct()
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = ProjectListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = ProjectListSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        """Get detailed statistics for a project"""
        project = self.get_object()
        
        # Calculate statistics
        tasks = project.tasks.all()
        total_tasks = tasks.count()
        completed_tasks = tasks.filter(status='Completada').count()
        in_progress_tasks = tasks.filter(status='En Progreso').count()
        
        # Budget calculations
        total_budget = float(project.budget_total or 0)
        spent_budget = float(project.total_expenses or 0)
        budget_variance = total_budget - spent_budget
        
        data = {
            'project_id': project.id,
            'project_name': project.name,
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'in_progress_tasks': in_progress_tasks,
            'total_budget': total_budget,
            'spent_budget': spent_budget,
            'budget_variance': budget_variance,
        }
        
        serializer = ProjectStatsSerializer(data)
        return Response(serializer.data)
    
    def perform_create(self, serializer):
        """Set created_by on project creation"""
        # Note: Current Project model doesn't have created_by field
        # This is for future compatibility
        serializer.save()
