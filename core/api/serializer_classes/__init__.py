"""
Serializers for Kibray API
"""
from .user_serializers import (
    UserListSerializer,
    UserDetailSerializer,
    UserCreateSerializer,
    UserUpdateSerializer,
    CurrentUserSerializer,
    UserMinimalSerializer,
    UserProfileSerializer,
)

from .project_serializers import (
    ProjectListSerializer,
    ProjectDetailSerializer,
    ProjectCreateUpdateSerializer,
    ProjectStatsSerializer,
    ClientOrganizationMinimalSerializer,
    ClientContactMinimalSerializer,
)

from .task_serializers import (
    TaskListSerializer,
    TaskDetailSerializer,
    TaskCreateUpdateSerializer,
    TaskStatsSerializer,
)

from .changeorder_serializers import (
    ChangeOrderListSerializer,
    ChangeOrderDetailSerializer,
    ChangeOrderCreateUpdateSerializer,
    ChangeOrderApprovalSerializer,
)

from .analytics_serializers import (
    AnalyticsResponseSerializer,
    ProjectAnalyticsSerializer,
    KPISerializer,
    ChartDataSerializer,
)
# Re-export budget summary serializer used by viewsets/tests
from core.api.serializers import ProjectBudgetSummarySerializer

__all__ = [
    # User serializers
    'UserListSerializer',
    'UserDetailSerializer',
    'UserCreateSerializer',
    'UserUpdateSerializer',
    'CurrentUserSerializer',
    'UserMinimalSerializer',
    'UserProfileSerializer',
    # Project serializers
    'ProjectListSerializer',
    'ProjectDetailSerializer',
    'ProjectCreateUpdateSerializer',
    'ProjectStatsSerializer',
    'ClientOrganizationMinimalSerializer',
    'ClientContactMinimalSerializer',
    # Task serializers
    'TaskListSerializer',
    'TaskDetailSerializer',
    'TaskCreateUpdateSerializer',
    'TaskStatsSerializer',
    # ChangeOrder serializers
    'ChangeOrderListSerializer',
    'ChangeOrderDetailSerializer',
    'ChangeOrderCreateUpdateSerializer',
    'ChangeOrderApprovalSerializer',
    # Analytics serializers
    'AnalyticsResponseSerializer',
    'ProjectAnalyticsSerializer',
    'KPISerializer',
    'ChartDataSerializer',
    'ProjectBudgetSummarySerializer',
]
