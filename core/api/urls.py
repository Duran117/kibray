from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

# Strategic Future Planning (Phase A3 - Dec 2025)
from core.views.strategic_planning_views import (
    StrategicItemViewSet,
    StrategicMaterialViewSet,
    StrategicPlanningSessionViewSet,
    StrategicSubtaskViewSet,
    StrategicTaskViewSet,
)

# Health check endpoints
from core.views_health import (
    health_check,
    health_check_detailed,
    liveness_check,
    readiness_check,
)

from . import schedule_api, sop_api
from .bulk_views import BulkTaskUpdateAPIView, BulkTaskAssignAPIView, TaskDetailAPIView
from .dashboard_extra import ClientDashboardView, ProjectDashboardView
from .focus_api import DailyFocusSessionViewSet, FocusTaskViewSet
from .views import (
    AdminDashboardView,
    AISuggestionViewSet,  # AI Enhancement (Dec 2025)
    AuditLogViewSet,
    BIAnalyticsViewSet,
    BudgetLineViewSet,
    BudgetVarianceAnalysisAPIView,
    CashFlowProjectionAPIView,
    ChatChannelViewSet,
    ChatMessageViewSet,
    ClientInvoiceApprovalAPIView,
    ClientInvoiceListAPIView,
    ClientRequestAttachmentViewSet,
    ClientRequestViewSet,
    ColorApprovalAnalyticsDashboardView,
    ColorApprovalViewSet,
    ColorSampleViewSet,
    CostCodeViewSet,
    DailyLogPlanningViewSet,
    DailyLogSanitizedViewSet,
    DailyPlanViewSet,
    DamageReportViewSet,
    ExpenseViewSet,
    FieldMaterialsViewSet,
    FinancialDashboardView,
    FloorPlanViewSet,
    IncomeViewSet,
    InventoryItemViewSet,
    InventoryLocationViewSet,
    InventoryMovementViewSet,
    InventoryValuationReportView,
    InvoiceAgingReportAPIView,
    InvoiceDashboardView,
    InvoiceTrendsView,
    InvoiceViewSet,
    LoginAttemptViewSet,
    MaterialCatalogViewSet,
    MaterialRequestViewSet,
    MaterialsDashboardView,
    MaterialsUsageAnalyticsView,
    MeetingMinuteViewSet,
    NotificationViewSet,
    PayrollDashboardView,
    PayrollPaymentViewSet,
    PayrollPeriodViewSet,
    PayrollRecordViewSet,
    PermissionMatrixViewSet,
    PlannedActivityViewSet,
    PlanPinViewSet,
    PMPerformanceDashboardView,
    ProjectFileViewSet,  # ⭐ Phase 4 File Manager
    ProjectHealthDashboardView,
    ProjectInventoryViewSet,
    ProjectManagerAssignmentViewSet,
    PushSubscriptionViewSet,  # ⭐ PWA Push Notifications
    ScheduleCategoryViewSet,
    ScheduleItemViewSet,
    SitePhotoViewSet,
    TaskDependencyViewSet,
    TaskGanttView,
    TaskTemplateViewSet,
    TaskViewSet,
    TimeEntryViewSet,
    TouchupAnalyticsDashboardView,
    TwoFactorTokenObtainPairView,
    TwoFactorViewSet,
    WeatherSnapshotViewSet,
    delete_changeorder_photo,
    global_search,
    save_changeorder_photo_annotations,
    update_changeorder_photo_image,
)
from .viewset_classes import (
    AnalyticsViewSet as AnalyticsViewSetNew,
)
from .viewset_classes import (
    ChangeOrderViewSet as ChangeOrderViewSetNew,
)

# Import Phase 5 viewsets from viewset_classes (new architecture)
from .viewset_classes import (
    ProjectViewSet as ProjectViewSetNew,
)
from .viewset_classes import (
    TaskViewSet as TaskViewSetNew,
)
from .viewset_classes import (
    UserViewSet as UserViewSetNew,
)

router = DefaultRouter()
# Notifications & Chat
router.register(r"notifications", NotificationViewSet, basename="notification")
# Security & Audit (Phase 9)
router.register(r"permissions", PermissionMatrixViewSet, basename="permission-matrix")
router.register(r"audit-logs", AuditLogViewSet, basename="audit-log")
router.register(r"login-attempts", LoginAttemptViewSet, basename="login-attempt")

router.register(r"chat/channels", ChatChannelViewSet, basename="chat-channel")
router.register(r"chat/messages", ChatMessageViewSet, basename="chat-message")
router.register(r"daily-logs-sanitized", DailyLogSanitizedViewSet, basename="daily-log-sanitized")

# Tasks & Reports
router.register(r"tasks", TaskViewSetNew, basename="task")
router.register(r"damage-reports", DamageReportViewSet, basename="damage-report")
router.register(r"task-dependencies", TaskDependencyViewSet, basename="task-dependency")

# Floor Plans & Colors
router.register(r"floor-plans", FloorPlanViewSet, basename="floor-plan")
router.register(r"plan-pins", PlanPinViewSet, basename="plan-pin")
router.register(r"color-samples", ColorSampleViewSet, basename="color-sample")
router.register(r"color-approvals", ColorApprovalViewSet, basename="color-approval")

# Projects
router.register(r"projects", ProjectViewSetNew, basename="project")
router.register(
    r"project-manager-assignments",
    ProjectManagerAssignmentViewSet,
    basename="project-manager-assignment",
)

# Phase 4: File Manager
router.register(r"files", ProjectFileViewSet, basename="file")

# Phase 5: Users and Change Orders
router.register(r"users", UserViewSetNew, basename="user")
router.register(r"changeorders", ChangeOrderViewSetNew, basename="changeorder")

# Schedule
router.register(r"schedule/categories", ScheduleCategoryViewSet, basename="schedule-category")
router.register(r"schedule/items", ScheduleItemViewSet, basename="schedule-item")

# Financial (NEW)
router.register(r"incomes", IncomeViewSet, basename="income")
router.register(r"expenses", ExpenseViewSet, basename="expense")
router.register(r"cost-codes", CostCodeViewSet, basename="cost-code")
router.register(r"budget-lines", BudgetLineViewSet, basename="budget-line")
router.register(r"invoices", InvoiceViewSet, basename="invoice")

# Phase 1: Planning & Weather (NEW)
router.register(r"daily-logs", DailyLogPlanningViewSet, basename="daily-log")
router.register(r"task-templates", TaskTemplateViewSet, basename="task-template")
router.register(r"weather-snapshots", WeatherSnapshotViewSet, basename="weather-snapshot")
router.register(r"daily-plans", DailyPlanViewSet, basename="daily-plan")
router.register(r"planned-activities", PlannedActivityViewSet, basename="planned-activity")
router.register(
    r"ai-suggestions", AISuggestionViewSet, basename="ai-suggestion"
)  # AI Enhancement (Dec 2025)
router.register(r"time-entries", TimeEntryViewSet, basename="time-entry")

# Module 14: Materials & Inventory
router.register(r"material-requests", MaterialRequestViewSet, basename="material-request")
router.register(r"material-catalog", MaterialCatalogViewSet, basename="material-catalog")
router.register(r"client-requests", ClientRequestViewSet, basename="client-request")
router.register(
    r"client-request-attachments",
    ClientRequestAttachmentViewSet,
    basename="client-request-attachment",
)
router.register(r"site-photos", SitePhotoViewSet, basename="site-photo")
router.register(r"inventory/items", InventoryItemViewSet, basename="inventory-item")
router.register(r"inventory/locations", InventoryLocationViewSet, basename="inventory-location")
router.register(r"inventory/stocks", ProjectInventoryViewSet, basename="project-inventory")
router.register(r"inventory/movements", InventoryMovementViewSet, basename="inventory-movement")
router.register(r"field-materials", FieldMaterialsViewSet, basename="field-materials")
router.register(r"meeting-minutes", MeetingMinuteViewSet, basename="meeting-minute")

# Module 16: Payroll
router.register(r"payroll/periods", PayrollPeriodViewSet, basename="payroll-period")
router.register(r"payroll/records", PayrollRecordViewSet, basename="payroll-record")
router.register(r"payroll/payments", PayrollPaymentViewSet, basename="payroll-payment")

# Security: 2FA
router.register(r"2fa", TwoFactorViewSet, basename="twofactor")

# PWA: Push Notifications
router.register(r"push", PushSubscriptionViewSet, basename="push-subscription")

# Module 21: Business Intelligence Analytics
router.register(r"bi", BIAnalyticsViewSet, basename="bi-analytics")

# Phase 5: Navigation Analytics
router.register(r"nav-analytics", AnalyticsViewSetNew, basename="nav-analytics")

# Module 25: Executive Focus Workflow (Productivity)
router.register(r"focus/sessions", DailyFocusSessionViewSet, basename="focus-session")
router.register(r"focus/tasks", FocusTaskViewSet, basename="focus-task")

# Strategic Future Planning (Phase A3 - Dec 2025)
router.register(
    r"strategic/sessions", StrategicPlanningSessionViewSet, basename="strategic-session"
)
router.register(r"strategic/items", StrategicItemViewSet, basename="strategic-item")
router.register(r"strategic/tasks", StrategicTaskViewSet, basename="strategic-task")
router.register(r"strategic/subtasks", StrategicSubtaskViewSet, basename="strategic-subtask")
router.register(r"strategic/materials", StrategicMaterialViewSet, basename="strategic-material")

urlpatterns = [
    # Health Check Endpoints (Phase 7 - Step 45)
    path("health/", health_check, name="health-check"),
    path("health/detailed/", health_check_detailed, name="health-check-detailed"),
    path("readiness/", readiness_check, name="readiness-check"),
    path("liveness/", liveness_check, name="liveness-check"),
    # JWT Auth
    path("auth/login/", TwoFactorTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("auth/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    # API Documentation (Phase 5)
    path("schema/", SpectacularAPIView.as_view(), name="api-schema"),
    path("docs/", SpectacularSwaggerView.as_view(url_name="api-schema"), name="api-docs"),
    path("redoc/", SpectacularRedocView.as_view(url_name="api-schema"), name="api-redoc"),
    # Global Search
    path("search/", global_search, name="global_search"),
    # ChangeOrder Photos
    path(
        "changeorder-photo/<int:photo_id>/annotations/",
        save_changeorder_photo_annotations,
        name="save_photo_annotations",
    ),
    path("changeorder-photo/<int:photo_id>/delete/", delete_changeorder_photo, name="delete_photo"),
    path(
        "changeorder-photo/<int:photo_id>/annotated-image/",
        update_changeorder_photo_image,
        name="update_photo_image",
    ),
    # API routes - Task operations
    path("tasks/bulk-update/", BulkTaskUpdateAPIView.as_view(), name="tasks-bulk-update"),
    path("tasks/bulk-assign/", BulkTaskAssignAPIView.as_view(), name="tasks-bulk-assign"),
    path("tasks/<int:task_id>/detail/", TaskDetailAPIView.as_view(), name="task-detail-api"),
    # Include router URLs
    path("", include(router.urls)),
    # Ensure gantt endpoint resolves under router and direct mapping
    path("tasks/gantt/", TaskGanttView.as_view(), name="tasks-gantt"),
    path("tasks/gantt/", TaskViewSet.as_view({"get": "gantt"}), name="tasks-gantt-router"),
    # Dashboards (UI)
    path(
        "dashboards/projects/<int:project_id>/",
        ProjectDashboardView.as_view(),
        name="dashboard-project",
    ),
    path("dashboards/client/", ClientDashboardView.as_view(), name="dashboard-client"),
    path("dashboards/admin/", AdminDashboardView.as_view(), name="dashboard-admin"),
    path("dashboards/payroll/", PayrollDashboardView.as_view(), name="dashboard-payroll"),
    path("dashboards/invoices/", InvoiceDashboardView.as_view(), name="dashboard-invoices"),
    path(
        "dashboards/invoices/trends/", InvoiceTrendsView.as_view(), name="dashboard-invoice-trends"
    ),
    path("dashboards/materials/", MaterialsDashboardView.as_view(), name="dashboard-materials"),
    path(
        "dashboards/materials/usage/",
        MaterialsUsageAnalyticsView.as_view(),
        name="dashboard-materials-usage",
    ),
    path("dashboards/financial/", FinancialDashboardView.as_view(), name="financial-dashboard"),
    # Analytics API endpoints (used by tests)
    path(
        "analytics/project-health/<int:project_id>/",
        ProjectHealthDashboardView.as_view(),
        name="analytics-project-health",
    ),
    path("analytics/touchups/", TouchupAnalyticsDashboardView.as_view(), name="analytics-touchups"),
    path(
        "analytics/color-approvals/",
        ColorApprovalAnalyticsDashboardView.as_view(),
        name="analytics-color-approvals",
    ),
    path(
        "analytics/pm-performance/",
        PMPerformanceDashboardView.as_view(),
        name="analytics-pm-performance",
    ),
    # SOP Express API
    path("sop/generate/", sop_api.generate_sop_with_ai, name="sop-generate-ai"),
    path("sop/save/", sop_api.save_sop, name="sop-save"),
    # Gap D/E/F: Financial reporting & client portal
    path(
        "financial/aging-report/",
        InvoiceAgingReportAPIView.as_view(),
        name="financial-aging-report",
    ),
    path(
        "financial/cash-flow-projection/",
        CashFlowProjectionAPIView.as_view(),
        name="financial-cash-flow-projection",
    ),
    path(
        "financial/budget-variance/",
        BudgetVarianceAnalysisAPIView.as_view(),
        name="financial-budget-variance",
    ),
    path(
        "inventory/valuation-report/",
        InventoryValuationReportView.as_view(),
        name="inventory-valuation-report",
    ),
    path("client/invoices/", ClientInvoiceListAPIView.as_view(), name="client-invoice-list"),
    path(
        "client/invoices/<int:invoice_id>/approve/",
        ClientInvoiceApprovalAPIView.as_view(),
        name="client-invoice-approval",
    ),
    # Master Schedule API
    path("schedule/master/", schedule_api.get_master_schedule_data, name="api-schedule-master"),
    # Gantt v2 per project (React Modern Gantt feed)
    path(
        "gantt/v2/projects/<int:project_id>/",
        schedule_api.get_project_gantt_v2,
        name="api-gantt-v2-project",
    ),
    path("gantt/v2/phases/", schedule_api.create_schedule_phase_v2, name="api-gantt-v2-phase-create"),
    path(
        "gantt/v2/phases/<int:phase_id>/",
        schedule_api.update_schedule_phase_v2,
        name="api-gantt-v2-phase-update",
    ),
    path("gantt/v2/items/", schedule_api.create_schedule_item_v2, name="api-gantt-v2-item-create"),
    path(
        "gantt/v2/items/<int:item_id>/",
        schedule_api.update_schedule_item_v2,
        name="api-gantt-v2-item-update",
    ),
    path("gantt/v2/tasks/", schedule_api.create_schedule_task_v2, name="api-gantt-v2-task-create"),
    path(
        "gantt/v2/tasks/<int:task_id>/",
        schedule_api.update_schedule_task_v2,
        name="api-gantt-v2-task-update",
    ),
    path(
        "gantt/v2/dependencies/",
        schedule_api.create_schedule_dependency_v2,
        name="api-gantt-v2-dependency-create",
    ),
    path(
        "gantt/v2/dependencies/<int:dependency_id>/",
        schedule_api.delete_schedule_dependency_v2,
        name="api-gantt-v2-dependency-delete",
    ),
    # Include router URLs
    path("", include(router.urls)),
]
