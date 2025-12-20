from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.generic import TemplateView

from core.models import Employee, StrategicPlanningSession


class StrategicPlanningDashboardView(LoginRequiredMixin, TemplateView):
    template_name = "core/strategic_planning_dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Fetch sessions for the current user or all if admin/manager
        # For now, let's just fetch all sessions ordered by date_range_start
        sessions = StrategicPlanningSession.objects.all().order_by('-date_range_start')

        context['sessions'] = sessions
        context['now'] = timezone.now()
        return context

class StrategicPlanningDetailView(LoginRequiredMixin, TemplateView):
    template_name = "core/strategic_planning_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        session_id = kwargs.get('pk')

        # Fetch session with full hierarchy pre-fetched for performance
        session = get_object_or_404(
            StrategicPlanningSession.objects.prefetch_related(
                'days',
                'days__items',
                'days__items__tasks',
                'days__items__tasks__subtasks',
                'days__items__material_requirements',
                'days__items__successors',
                'days__items__predecessors'
            ).select_related('project', 'user'),
            pk=session_id
        )

        context['session'] = session
        # Pass active employees for assignment dropdowns
        context['employees'] = Employee.objects.filter(is_active=True).order_by('first_name')

        # Prepare data for Gantt View
        import json
        gantt_items = []
        day_map = {} # Map date string to day ID

        for day in session.days.all():
            day_map[day.target_date.isoformat()] = day.id
            for item in day.items.all():
                gantt_items.append({
                    'id': item.id,
                    'title': item.title,
                    'start_date': day.target_date.isoformat(),
                    'duration': item.duration_days,
                    'day_id': day.id,
                    'priority': item.priority,
                    'assigned_to': [e.id for e in item.assigned_to.all()]
                })
        context['gantt_items_json'] = json.dumps(gantt_items)
        context['day_map_json'] = json.dumps(day_map)

        return context
