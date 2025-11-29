"""
Master Schedule Center API
Provides unified data for Strategic Gantt (Projects timeline) and Tactical Calendar (Daily events).
"""
from datetime import timedelta
from decimal import Decimal
from django.db.models import Q, Sum, Count, F
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_master_schedule_data(request):
    """
    Get unified schedule data for Master Schedule Center.
    
    Returns:
        {
            "projects": [...],  # Strategic Gantt data
            "events": [...]     # Tactical Calendar events
        }
    """
    from core.models import (
        Project, ChangeOrder, Invoice
    )
    try:
        from core.models import Task
    except:
        Task = None
    try:
        from core.models import MeetingMinute
    except:
        MeetingMinute = None
    try:
        from core.models import ClientRequest
    except:
        ClientRequest = None
    try:
        from core.models import MaterialRequest
    except:
        MaterialRequest = None
    
    # === STRATEGIC GANTT: Projects Timeline ===
    projects_data = []
    active_projects = Project.objects.filter(
        is_archived=False
    ).prefetch_related(
        'tasks'
    ).order_by('start_date')
    
    # Color palette for projects (cycle through)
    colors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4', '#84cc16']
    
    for idx, project in enumerate(active_projects):
        # Calculate progress based on tasks completion
        total_tasks = project.tasks.count()
        completed_tasks = project.tasks.filter(status='Completada').count()
        progress_pct = int((completed_tasks / total_tasks * 100)) if total_tasks > 0 else 0
        
        # PM name - simplified (no manager_assignments relation)
        pm_name = "No PM assigned"
        
        # Client name
        client_name = project.client or "No Client"
        
        projects_data.append({
            'id': project.id,
            'name': project.name,
            'start_date': project.start_date.isoformat(),
            'end_date': project.end_date.isoformat() if project.end_date else (project.start_date + timedelta(days=90)).isoformat(),
            'progress_pct': progress_pct,
            'color': colors[idx % len(colors)],
            'pm_name': pm_name,
            'client_name': client_name,
            'url': f"/projects/{project.id}/overview/",
        })
    
    # === TACTICAL CALENDAR: Events ===
    events_data = []
    today = timezone.localdate()
    
    # Range: last 30 days to next 90 days
    start_range = today - timedelta(days=30)
    end_range = today + timedelta(days=90)
    
    # 1. INVOICES DUE (Red - Money)
    invoices = Invoice.objects.filter(
        due_date__gte=start_range,
        due_date__lte=end_range,
        status__in=['SENT', 'VIEWED', 'APPROVED', 'PARTIAL']
    ).select_related('project')
    
    for invoice in invoices:
        events_data.append({
            'title': f"💵 Invoice #{invoice.invoice_number} Due",
            'start': invoice.due_date.isoformat(),
            'end': invoice.due_date.isoformat(),
            'type': 'invoice',
            'color': '#dc2626',  # Red
            'url': f"/invoices/{invoice.id}/",
            'description': f"${invoice.total_amount} - {invoice.project.name if invoice.project else 'N/A'}",
        })
    
    # 2. CHANGE ORDER CREATION DATES (Orange - Work)
    change_orders = ChangeOrder.objects.filter(
        date_created__gte=start_range,
        date_created__lte=end_range,
        status__in=['pending', 'approved', 'sent', 'billed']
    ).select_related('project')
    
    for co in change_orders:
        events_data.append({
            'title': f"🔧 CO #{co.id}",
            'start': co.date_created.isoformat(),
            'end': co.date_created.isoformat(),
            'type': 'change_order',
            'color': '#f59e0b',  # Orange
            'url': f"/changeorder/{co.id}/",
            'description': f"{co.description[:60]}... - {co.project.name if co.project else 'N/A'}",
        })
    
    # 3-6. OTHER EVENTS (Tasks, Meetings, Client Requests, Material Requests)
    # TODO: Add support for additional event types when model fields are confirmed
    # Currently skipping to avoid field name mismatches
    
    # Sort events by start date
    events_data.sort(key=lambda x: x['start'])
    
    return Response({
        'projects': projects_data,
        'events': events_data,
        'metadata': {
            'total_projects': len(projects_data),
            'total_events': len(events_data),
            'date_range': {
                'start': start_range.isoformat(),
                'end': end_range.isoformat(),
            }
        }
    })
