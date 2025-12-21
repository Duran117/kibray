"""
Analytics-related serializers for the Kibray API
"""

from rest_framework import serializers


class KPISerializer(serializers.Serializer):
    """Serializer for KPI metrics"""

    total_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_projects = serializers.IntegerField()
    active_projects = serializers.IntegerField()
    completed_projects = serializers.IntegerField()
    total_tasks = serializers.IntegerField()
    completed_tasks = serializers.IntegerField()
    pending_changeorders = serializers.IntegerField()
    total_team_members = serializers.IntegerField()
    avg_project_completion = serializers.DecimalField(max_digits=5, decimal_places=2)


class ChartDatasetSerializer(serializers.Serializer):
    """Serializer for chart dataset"""

    label = serializers.CharField()
    data = serializers.ListField(child=serializers.FloatField())
    border_color = serializers.CharField(required=False, source="borderColor")
    background_color = serializers.CharField(required=False, source="backgroundColor")


class ChartDataSerializer(serializers.Serializer):
    """Serializer for chart data"""

    labels = serializers.ListField(child=serializers.CharField())
    datasets = ChartDatasetSerializer(many=True)


class AnalyticsResponseSerializer(serializers.Serializer):
    """Complete analytics response"""

    kpis = KPISerializer()
    budget_chart = ChartDataSerializer(source="budgetChart")
    project_progress = ChartDataSerializer(source="projectProgress")
    task_distribution = ChartDataSerializer(source="taskDistribution")
    monthly_trends = ChartDataSerializer(source="monthlyTrends")
    time_range = serializers.CharField(source="timeRange")
    generated_at = serializers.DateTimeField(source="generatedAt")


class ProjectAnalyticsSerializer(serializers.Serializer):
    """Analytics for a single project"""

    project_id = serializers.IntegerField()
    project_name = serializers.CharField()
    total_budget = serializers.DecimalField(max_digits=12, decimal_places=2)
    spent_budget = serializers.DecimalField(max_digits=12, decimal_places=2)
    budget_variance = serializers.DecimalField(max_digits=12, decimal_places=2)
    tasks_summary = serializers.DictField()
    changeorders_summary = serializers.DictField()
    timeline_data = serializers.DictField()
    team_utilization = serializers.DictField()
