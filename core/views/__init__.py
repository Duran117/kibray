"""core.views package compatibility layer.

The project historically did `from core import views` and expected a very large
set of functions/classes (from the legacy monolithic `views.py`).

We keep that behavior using an explicit re-export, while still allowing targeted
imports of individual view modules.
"""

from ._helpers import *  # noqa: F403  (formerly re-exported via legacy_views shim)
from .touchup_v2_views import *  # noqa: F403
from .file_views import *  # noqa: F403
from .client_mgmt_views import *  # noqa: F403
from .payroll_views import *  # noqa: F403
from .color_floor_views import *  # noqa: F403
from .financial_views import *  # noqa: F403
from .materials_views import *  # noqa: F403
from .daily_plan_views import *  # noqa: F403
from .schedule_views import *  # noqa: F403
# dashboard_views shim → expand to its sub-modules
from .dashboard_admin_views import *  # noqa: F403
from .dashboard_client_views import *  # noqa: F403
from .dashboard_employee_views import *  # noqa: F403
from .dashboard_pm_views import *  # noqa: F403
from .dashboard_designer_views import *  # noqa: F403
from .dashboard_shared_views import *  # noqa: F403
from .changeorder_views import *  # noqa: F403
# project_views shim → expand to its sub-modules
from .project_crud_views import *  # noqa: F403
from .project_overview_views import *  # noqa: F403
from .project_client_portal_views import *  # noqa: F403
from .project_finance_views import *  # noqa: F403
from .project_progress_views import *  # noqa: F403
from .task_views import *  # noqa: F403
from .touchup_legacy_views import *  # noqa: F403
from .damage_report_views import *  # noqa: F403
from .chat_views import *  # noqa: F403
from .daily_log_views import *  # noqa: F403
from .rfi_issue_risk_views import *  # noqa: F403
from .site_photo_views import *  # noqa: F403
from .meeting_minutes_views import *  # noqa: F403
from .expense_income_views import *  # noqa: F403
from .contract_views import *  # noqa: F403
from .misc_views import *  # noqa: F403
from .strategic_planning_frontend import (
    StrategicPlanningDashboardView,
    StrategicPlanningDetailView,
)

__all__ = [
    "StrategicPlanningDashboardView",
    "StrategicPlanningDetailView",
]
