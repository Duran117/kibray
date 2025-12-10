from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

from .dashboard_extra import ClientDashboardView, ProjectDashboardView
from . import sop_api
from . import schedule_api

# Health check endpoints
from core.views_health import (
    health_check,
    health_check_detailed,
    readiness_check,
    liveness_check,
)

# Import Phase 5 viewsets from viewset_classes (new architecture)
from .viewset_classes import (
    ProjectViewSet as ProjectViewSetNew,
    TaskViewSet as TaskViewSetNew,
    UserViewSet as UserViewSetNew,
    ChangeOrderViewSet as ChangeOrderViewSetNew,
    AnalyticsViewSet as AnalyticsViewSetNew,
)

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
    ColorSampleViewSet,
    ColorApprovalViewSet,
    ColorApprovalAnalyticsDashboardView,
    CostCodeViewSet,
    DailyLogPlanningViewSet,
    DailyPlanViewSet,
    DamageReportViewSet,
    ExpenseViewSet,
    FinancialDashboardView,
    FloorPlanViewSet,
    IncomeViewSet,
    InventoryItemViewSet,
    InventoryLocationViewSet,
    InventoryMovementViewSet,
    FieldMaterialsViewSet,
    InventoryValuationReportView,
    InvoiceAgingReportAPIView,
    InvoiceDashboardView,
    InvoiceTrendsView,
    InvoiceViewSet,
    LoginAttemptViewSet,
    MaterialCatalogViewSet,
    DailyLogSanitizedViewSet,
    MaterialRequestViewSet,
    MaterialsDashboardView,
    MaterialsUsageAnalyticsView,
    NotificationViewSet,
    PMPerformanceDashboardView,
    ProjectFileViewSet,  # ⭐ Phase 4 File Manager
    ProjectHealthDashboardView,
    ProjectManagerAssignmentViewSet,
    PushSubscriptionViewSet,  # ⭐ PWA Push Notifications
    PayrollDashboardView,
    PayrollPaymentViewSet,
    PayrollPeriodViewSet,
    PayrollRecordViewSet,
    PermissionMatrixViewSet,
    PlannedActivityViewSet,
    PlanPinViewSet,
    ProjectInventoryViewSet,
    ProjectViewSet,
    ScheduleCategoryViewSet,
    ScheduleItemViewSet,
    SitePhotoViewSet,
    TaskDependencyViewSet,
    TaskGanttView,
    TouchupAnalyticsDashboardView,
    TaskTemplateViewSet,
    TaskViewSet,
    TimeEntryViewSet,
    TwoFactorTokenObtainPairView,
    TwoFactorViewSet,
    WeatherSnapshotViewSet,
    delete_changeorder_photo,
    global_search,
    save_changeorder_photo_annotations,
    update_changeorder_photo_image,
)

# Strategic Future Planning (Phase A3 - Dec 2025)
from core.views.strategic_planning_views import (
    StrategicPlanningSessionViewSet,
    StrategicItemViewSet,
    StrategicTaskViewSet,
    StrategicSubtaskViewSet,
    StrategicMaterialViewSet
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
router.register(r"project-manager-assignments", ProjectManagerAssignmentViewSet, basename="project-manager-assignment")

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
router.register(r"ai-suggestions", AISuggestionViewSet, basename="ai-suggestion")  # AI Enhancement (Dec 2025)
router.register(r"time-entries", TimeEntryViewSet, basename="time-entry")

# Module 14: Materials & Inventory
router.register(r"material-requests", MaterialRequestViewSet, basename="material-request")
router.register(r"material-catalog", MaterialCatalogViewSet, basename="material-catalog")
router.register(r"client-requests", ClientRequestViewSet, basename="client-request")
router.register(r"client-request-attachments", ClientRequestAttachmentViewSet, basename="client-request-attachment")
router.register(r"site-photos", SitePhotoViewSet, basename="site-photo")
router.register(r"inventory/items", InventoryItemViewSet, basename="inventory-item")
router.register(r"inventory/locations", InventoryLocationViewSet, basename="inventory-location")
router.register(r"inventory/stocks", ProjectInventoryViewSet, basename="project-inventory")
router.register(r"inventory/movements", InventoryMovementViewSet, basename="inventory-movement")
router.register(r"field-materials", FieldMaterialsViewSet, basename="field-materials")

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
from .focus_api import DailyFocusSessionViewSet, FocusTaskViewSet
from .bulk_views import BulkTaskUpdateAPIView
router.register(r"focus/sessions", DailyFocusSessionViewSet, basename="focus-session")
router.register(r"focus/tasks", FocusTaskViewSet, basename="focus-task")

# Strategic Future Planning (Phase A3 - Dec 2025)
router.register(r"strategic/sessions", StrategicPlanningSessionViewSet, basename="strategic-session")
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
        "changeorder-photo/<int:photo_id>/annotated-image/", update_changeorder_photo_image, name="update_photo_image"
    ),
    # API routes
    path("tasks/bulk-update/", BulkTaskUpdateAPIView.as_view(), name="tasks-bulk-update"),
    # Include router URLs
    path("", include(router.urls)),
    # Ensure gantt endpoint resolves under router and direct mapping
    path("tasks/gantt/", TaskGanttView.as_view(), name="tasks-gantt"),
    path("tasks/gantt/", TaskViewSet.as_view({"get": "gantt"}), name="tasks-gantt-router"),
    # Dashboards
    path("dashboards/invoices/", InvoiceDashboardView.as_view(), name="dashboard-invoices"),
    path("dashboards/invoices/trends/", InvoiceTrendsView.as_view(), name="dashboard-invoice-trends"),
    path("dashboards/materials/", MaterialsDashboardView.as_view(), name="dashboard-materials"),
    path("dashboards/materials/usage/", MaterialsUsageAnalyticsView.as_view(), name="dashboard-materials-usage"),
    path("dashboards/financial/", FinancialDashboardView.as_view(), name="financial-dashboard"),
    
    # SOP Express API
    path("sop/generate/", sop_api.generate_sop_with_ai, name="sop-generate-ai"),
    path("sop/save/", sop_api.save_sop, name="sop-save"),

    # Master Schedule API
    path("schedule/master/", schedule_api.get_master_schedule_data, name="api-schedule-master"),

    # Include router URLs
    path("", include(router.urls)),
]


