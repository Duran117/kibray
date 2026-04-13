"""
Custom permissions for Kibray API
"""

from .changeorder_permissions import (
    CanApproveChangeOrder,
    CanSubmitChangeOrder,
)
from .project_permissions import (
    CanManageProject,
    IsBillingOrganizationMember,
    IsProjectLeadOrReadOnly,
    IsProjectMember,
)
from .role_permissions import (
    DenyEmployeeAccess,
    IsStaffOrAdmin,
    IsStaffOrReadOnlyForEmployee,
)
from .task_permissions import (
    CanDeleteTask,
    CanUpdateTaskStatus,
    IsTaskAssigneeOrProjectMember,
)

__all__ = [
    "IsProjectMember",
    "IsProjectLeadOrReadOnly",
    "IsBillingOrganizationMember",
    "CanManageProject",
    "IsTaskAssigneeOrProjectMember",
    "CanUpdateTaskStatus",
    "CanDeleteTask",
    "CanApproveChangeOrder",
    "CanSubmitChangeOrder",
    "IsStaffOrAdmin",
    "IsStaffOrReadOnlyForEmployee",
    "DenyEmployeeAccess",
]
