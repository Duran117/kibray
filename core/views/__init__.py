"""core.views package compatibility layer.

The project historically did `from core import views` and expected a very large
set of functions/classes (from the legacy monolithic `views.py`).

We keep that behavior using an explicit re-export, while still allowing targeted
imports of individual view modules.
"""

from .legacy_views import *  # noqa: F403
from .strategic_planning_frontend import (
    StrategicPlanningDashboardView,
    StrategicPlanningDetailView,
)

__all__ = [
    "StrategicPlanningDashboardView",
    "StrategicPlanningDetailView",
]
