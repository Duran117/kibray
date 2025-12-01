"""
Analytics-related viewsets for the Kibray API
"""
from datetime import timedelta
from decimal import Decimal

from django.db.models import Count, Sum, Avg, Q
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.api.serializer_classes import (
    AnalyticsResponseSerializer,
    ProjectAnalyticsSerializer,
)
from core.models import Project, Task, ChangeOrder, Employee


class AnalyticsViewSet(viewsets.ViewSet):
    """
    ViewSet for analytics and reporting
    """
    permission_classes = [IsAuthenticated]
    
    def list(self, request):
        """Get global analytics dashboard data"""
        # Extract time range parameter
        time_range = request.query_params.get('range', '30d')
        
        # Calculate date_from based on range
        date_from = timezone.now()
        if time_range == '7d':
            date_from = date_from - timedelta(days=7)
        elif time_range == '30d':
            date_from = date_from - timedelta(days=30)
        elif time_range == '90d':
            date_from = date_from - timedelta(days=90)
        elif time_range == '1y':
            date_from = date_from - timedelta(days=365)
        else:
            date_from = date_from - timedelta(days=30)  # default 30 days
        
        # Calculate KPIs
        total_projects = Project.objects.count()
        active_projects = Project.objects.filter(
            start_date__lte=timezone.now().date(),
            end_date__gte=timezone.now().date()
        ).count()
        completed_projects = Project.objects.filter(
            end_date__lt=timezone.now().date()
        ).count()
        
        total_tasks = Task.objects.count()
        completed_tasks = Task.objects.filter(status='Completada').count()
        
        pending_changeorders = ChangeOrder.objects.filter(status='pending').count()
        
        total_team_members = Employee.objects.filter(is_active=True).count()
        
        # Calculate average project completion
        if total_tasks > 0:
            avg_completion = (completed_tasks / total_tasks) * 100
        else:
            avg_completion = 0
        
        # Calculate total revenue
        total_revenue = Project.objects.aggregate(
            total=Sum('total_income')
        )['total'] or Decimal('0.00')
        
        kpis = {
            'total_revenue': float(total_revenue),
            'total_projects': total_projects,
            'active_projects': active_projects,
            'completed_projects': completed_projects,
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'pending_changeorders': pending_changeorders,
            'total_team_members': total_team_members,
            'avg_project_completion': round(avg_completion, 2),
        }
        
        # Budget Chart Data
        budget_data = Project.objects.filter(
            created_at__gte=date_from
        ).aggregate(
            budgeted=Sum('budget_total'),
            actual=Sum('total_expenses')
        )
        
        budget_chart = {
            'labels': ['Budgeted', 'Actual'],
            'datasets': [{
                'label': 'Budget Analysis',
                'data': [
                    float(budget_data['budgeted'] or 0),
                    float(budget_data['actual'] or 0)
                ],
                'backgroundColor': '#3b82f6',
                'borderColor': '#2563eb',
            }]
        }
        
        # Project Progress Chart
        project_statuses = {
            'Active': active_projects,
            'Completed': completed_projects,
            'Pending': total_projects - active_projects - completed_projects,
        }
        
        project_progress = {
            'labels': list(project_statuses.keys()),
            'datasets': [{
                'label': 'Projects by Status',
                'data': list(project_statuses.values()),
                'backgroundColor': ['#10b981', '#3b82f6', '#f59e0b'],
            }]
        }
        
        # Task Distribution Chart
        task_statuses = Task.objects.values('status').annotate(count=Count('id'))
        task_labels = [item['status'] for item in task_statuses]
        task_counts = [item['count'] for item in task_statuses]
        
        task_distribution = {
            'labels': task_labels if task_labels else ['No Data'],
            'datasets': [{
                'label': 'Tasks by Status',
                'data': task_counts if task_counts else [0],
                'backgroundColor': ['#ef4444', '#f59e0b', '#10b981', '#6b7280'],
            }]
        }
        
        # Monthly Trends Chart (last 6 months)
        monthly_labels = []
        monthly_tasks = []
        
        for i in range(5, -1, -1):
            month_date = timezone.now() - timedelta(days=30*i)
            month_label = month_date.strftime('%b %Y')
            monthly_labels.append(month_label)
            
            month_start = month_date.replace(day=1)
            if i > 0:
                next_month = (month_start + timedelta(days=32)).replace(day=1)
            else:
                next_month = timezone.now()
            
            tasks_completed = Task.objects.filter(
                completed_at__gte=month_start,
                completed_at__lt=next_month,
                status='Completada'
            ).count()
            monthly_tasks.append(tasks_completed)
        
        monthly_trends = {
            'labels': monthly_labels,
            'datasets': [{
                'label': 'Tasks Completed',
                'data': monthly_tasks,
                'borderColor': '#3b82f6',
                'backgroundColor': 'rgba(59, 130, 246, 0.1)',
            }]
        }
        
        # Construct response
        response_data = {
            'kpis': kpis,
            'budgetChart': budget_chart,
            'projectProgress': project_progress,
            'taskDistribution': task_distribution,
            'monthlyTrends': monthly_trends,
            'timeRange': time_range,
            'generatedAt': timezone.now(),
        }
        
        serializer = AnalyticsResponseSerializer(response_data)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def project_analytics(self, request):
        """Get detailed analytics for a specific project"""
        project_id = request.query_params.get('project_id')
        
        if not project_id:
            return Response(
                {'error': 'project_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            return Response(
                {'error': 'Project not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Calculate project statistics
        tasks = project.tasks.all()
        total_budget = float(project.budget_total or 0)
        spent_budget = float(project.total_expenses or 0)
        budget_variance = total_budget - spent_budget
        
        tasks_summary = {
            'total': tasks.count(),
            'completed': tasks.filter(status='Completada').count(),
            'in_progress': tasks.filter(status='En Progreso').count(),
            'pending': tasks.filter(status='Pendiente').count(),
        }
        
        changeorders_summary = {
            'total': project.change_orders.count(),
            'pending': project.change_orders.filter(status='pending').count(),
            'approved': project.change_orders.filter(status='approved').count(),
            'total_amount': float(project.change_orders.aggregate(
                total=Sum('amount')
            )['total'] or 0),
        }
        
        timeline_data = {
            'start_date': project.start_date.isoformat() if project.start_date else None,
            'end_date': project.end_date.isoformat() if project.end_date else None,
            'days_elapsed': (timezone.now().date() - project.start_date).days if project.start_date else 0,
        }
        
        team_utilization = {
            'assigned_tasks': tasks.filter(assigned_to__isnull=False).count(),
            'unassigned_tasks': tasks.filter(assigned_to__isnull=True).count(),
        }
        
        data = {
            'project_id': project.id,
            'project_name': project.name,
            'total_budget': total_budget,
            'spent_budget': spent_budget,
            'budget_variance': budget_variance,
            'tasks_summary': tasks_summary,
            'changeorders_summary': changeorders_summary,
            'timeline_data': timeline_data,
            'team_utilization': team_utilization,
        }
        
        serializer = ProjectAnalyticsSerializer(data)
        return Response(serializer.data)
