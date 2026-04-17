"""Legacy monolithic views module.

Shared helpers, constants, and common imports live in core.views._helpers.
This module re-imports them for backward compatibility.
"""
# Re-export everything from _helpers so existing code keeps working
from core.views._helpers import *  # noqa: F401, F403
from core.views._helpers import (  # explicit imports for linters
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
# _ is excluded from wildcard imports (underscore prefix), import explicitly
from django.utils.translation import gettext_lazy as _  # noqa: F811


