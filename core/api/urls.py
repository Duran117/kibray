from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

from .dashboard_extra import ClientDashboardView, ProjectDashboardView

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

# Module 21: Business Intelligence Analytics
router.register(r"bi", BIAnalyticsViewSet, basename="bi-analytics")

# Phase 5: Navigation Analytics
router.register(r"nav-analytics", AnalyticsViewSetNew, basename="nav-analytics")

# Module 25: Executive Focus Workflow (Productivity)
# from .focus_api import DailyFocusSessionViewSet, FocusTaskViewSet, focus_stats
from .bulk_views import BulkTaskUpdateAPIView
# router.register(r"focus/sessions", DailyFocusSessionViewSet, basename="focus-session")
# router.register(r"focus/tasks", FocusTaskViewSet, basename="focus-task")

urlpatterns = [
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
    path("", include(router.urls)),
    # Ensure gantt endpoint resolves under router and direct mapping
    path("tasks/gantt/", TaskGanttView.as_view(), name="tasks-gantt"),
    path("tasks/gantt/", TaskViewSet.as_view({"get": "gantt"}), name="tasks-gantt-router"),
    # Dashboards
    path("dashboards/invoices/", InvoiceDashboardView.as_view(), name="dashboard-invoices"),
    path("dashboards/invoices/trends/", InvoiceTrendsView.as_view(), name="dashboard-invoice-trends"),
    path("dashboards/materials/", MaterialsDashboardView.as_view(), name="dashboard-materials"),
    path("dashboards/materials/usage/", MaterialsUsageAnalyticsView.as_view(), name="dashboard-materials-usage"),
    path("dashboards/financial/", FinancialDashboardView.as_view(), name="dashboard-financial"),
    path("dashboards/payroll/", PayrollDashboardView.as_view(), name="dashboard-payroll"),
    path("dashboards/admin/", AdminDashboardView.as_view(), name="dashboard-admin"),
    path("dashboards/projects/<int:project_id>/", ProjectDashboardView.as_view(), name="dashboard-project"),
    path("dashboards/client/", ClientDashboardView.as_view(), name="dashboard-client"),
    # Analytics Dashboards (NEW)
    path(
        "analytics/projects/<int:project_id>/health/",
        ProjectHealthDashboardView.as_view(),
        name="analytics-project-health",
    ),
    path("analytics/touchups/", TouchupAnalyticsDashboardView.as_view(), name="analytics-touchups"),
    path("analytics/color-approvals/", ColorApprovalAnalyticsDashboardView.as_view(), name="analytics-color-approvals"),
    path("analytics/pm-performance/", PMPerformanceDashboardView.as_view(), name="analytics-pm-performance"),
    # Gap D: Inventory Valuation
    path("inventory/valuation-report/", InventoryValuationReportView.as_view(), name="inventory-valuation-report"),
    # Gap E: Advanced Financial Reporting
    path("financial/aging-report/", InvoiceAgingReportAPIView.as_view(), name="financial-aging-report"),
    path("financial/cash-flow-projection/", CashFlowProjectionAPIView.as_view(), name="financial-cash-flow"),
    path("financial/budget-variance/", BudgetVarianceAnalysisAPIView.as_view(), name="financial-budget-variance"),
    # Gap F: Client Portal
    path("client/invoices/", ClientInvoiceListAPIView.as_view(), name="client-invoices"),
    path("client/invoices/<int:invoice_id>/approve/", ClientInvoiceApprovalAPIView.as_view(), name="client-invoice-approve"),
    # Master Schedule Center
    path("schedule/master/", lambda req: __import__('core.api.schedule_api', fromlist=['get_master_schedule_data']).get_master_schedule_data(req), name="master-schedule-data"),
    # Focus Workflow Stats & Calendar
    # path("focus/stats/", focus_stats, name="focus-stats"),
    # iCal Calendar Feeds
    path("calendar/feed/<int:user_token>.ics", lambda req, user_token: __import__('core.api.calendar_feed', fromlist=['generate_focus_calendar_feed']).generate_focus_calendar_feed(req, user_token), name="focus-calendar-feed"),
    path("calendar/master/<int:user_token>.ics", lambda req, user_token: __import__('core.api.calendar_feed', fromlist=['generate_master_calendar_feed']).generate_master_calendar_feed(req, user_token), name="master-calendar-feed"),
    # Strategic Planner (Module 25 Part B)
    path("planner/habits/active/", lambda req: __import__('core.views_planner', fromlist=['get_active_habits']).get_active_habits(req), name="planner-active-habits"),
    path("planner/visions/random/", lambda req: __import__('core.views_planner', fromlist=['get_random_vision']).get_random_vision(req), name="planner-random-vision"),
    path("planner/ritual/complete/", lambda req: __import__('core.views_planner', fromlist=['complete_ritual']).complete_ritual(req), name="planner-complete-ritual"),
    path("planner/ritual/today/", lambda req: __import__('core.views_planner', fromlist=['today_ritual_summary']).today_ritual_summary(req), name="planner-today-ritual"),
    path("planner/action/<int:action_id>/toggle/", lambda req, action_id: __import__('core.views_planner', fromlist=['toggle_power_action_status']).toggle_power_action_status(req, action_id), name="planner-toggle-action"),
    path("planner/action/<int:action_id>/step/<int:step_index>/", lambda req, action_id, step_index: __import__('core.views_planner', fromlist=['update_micro_step']).update_micro_step(req, action_id, step_index), name="planner-update-step"),
    path("planner/stats/", lambda req: __import__('core.views_planner', fromlist=['planner_stats']).planner_stats(req), name="planner-stats"),
    path("planner/feed/<str:user_token>.ics", lambda req, user_token: __import__('core.views_planner', fromlist=['planner_calendar_feed']).planner_calendar_feed(req, user_token), name="planner-calendar-feed"),
    # Bulk Task Operations
    path("tasks/bulk-update/", BulkTaskUpdateAPIView.as_view(), name="tasks-bulk-update"),
    # Push Notifications (Phase 6 - Improvement #16)
    path("notifications/preferences/", lambda req: __import__('core.api.views', fromlist=['PushNotificationPreferencesView']).PushNotificationPreferencesView.as_view()(req), name="notification-preferences"),
]

# Add device token routes to router
from .views import DeviceTokenViewSet
router.register(r"notifications/devices", DeviceTokenViewSet, basename="device-token")


