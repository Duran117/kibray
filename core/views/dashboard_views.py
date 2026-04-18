"""Dashboard views — admin, client, employee, PM, designer, superintendent."""
from core.views._helpers import *  # noqa: F401, F403
from core.views._helpers import (
    _generate_basic_pdf_from_html,
    _check_user_project_access,
    _is_admin_user,
    _is_pm_or_admin,
    _is_staffish,
    _require_admin_or_redirect,
    _require_roles,
    _parse_date,
    _ensure_inventory_item,
    staff_required,
    logger,
    pisa,
    ROLES_ADMIN,
    ROLES_PM,
    ROLES_STAFF,
    ROLES_FIELD,
    ROLES_ALL_INTERNAL,
    ROLES_CLIENT_SIDE,
    ROLES_PROJECT_ACCESS,
)
from django.utils.translation import gettext_lazy as _  # noqa: F811

# Module split: this file now re-exports from per-role modules
from core.views.dashboard_admin_views import *  # noqa: F401, F403
from core.views.dashboard_client_views import *  # noqa: F401, F403
from core.views.dashboard_employee_views import *  # noqa: F401, F403
from core.views.dashboard_pm_views import *  # noqa: F401, F403
from core.views.dashboard_designer_views import *  # noqa: F401, F403
from core.views.dashboard_shared_views import *  # noqa: F401, F403
