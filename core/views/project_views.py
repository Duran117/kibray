"""Project views — CRUD, overview, client portal, financials."""
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

# Module split: re-exports from per-domain modules
from core.views.project_crud_views import *  # noqa: F401, F403
from core.views.project_overview_views import *  # noqa: F401, F403
from core.views.project_client_portal_views import *  # noqa: F401, F403
from core.views.project_finance_views import *  # noqa: F401, F403
