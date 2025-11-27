from django.shortcuts import get_object_or_404
from rest_framework import permissions, views
from rest_framework.response import Response

from core.models import Project
from reports.services import render_project_cost_summary


class ProjectCostSummaryView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, project_id: int):
        project = get_object_or_404(Project, pk=project_id)
        result = render_project_cost_summary(project)
        return Response(result.body.decode("utf-8"), content_type=result.content_type)
