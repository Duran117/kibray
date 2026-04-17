"""core.views package compatibility layer.

The project historically did `from core import views` and expected a very large
set of functions/classes (from the legacy monolithic `views.py`).

We keep that behavior using an explicit re-export, while still allowing targeted
imports of individual view modules.
"""

from .legacy_views import *  # noqa: F403
from .touchup_v2_views import *  # noqa: F403
from .file_views import *  # noqa: F403
from .client_mgmt_views import *  # noqa: F403
from .payroll_views import *  # noqa: F403
from .color_floor_views import *  # noqa: F403
from .financial_views import *  # noqa: F403
from .materials_views import *  # noqa: F403
from .daily_plan_views import *  # noqa: F403
from .schedule_views import *  # noqa: F403
from .strategic_planning_frontend import (
    StrategicPlanningDashboardView,
    StrategicPlanningDetailView,
)

__all__ = [
    "StrategicPlanningDashboardView",
    "StrategicPlanningDetailView",
]
