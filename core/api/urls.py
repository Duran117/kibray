from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from .dashboard_extra import ClientDashboardView, ProjectDashboardView
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
    MeetingMinuteViewSet,
    DailyLogSanitizedViewSet,
    MaterialRequestViewSet,
    MaterialsDashboardView,
    MaterialsUsageAnalyticsView,
    NotificationViewSet,
    PMPerformanceDashboardView,
    ProjectHealthDashboardView,
    ProjectManagerAssignmentViewSet,
    PayrollDashboardView,
    PayrollPaymentViewSet,
    PayrollPeriodViewSet,
    PayrollRecordViewSet,
    PermissionMatrixViewSet,
    TaxProfileViewSet,
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
router.register(r"meeting-minutes", MeetingMinuteViewSet, basename="meeting-minute")
router.register(r"daily-logs-sanitized", DailyLogSanitizedViewSet, basename="daily-log-sanitized")

# Tasks & Reports
router.register(r"tasks", TaskViewSet, basename="task")
router.register(r"damage-reports", DamageReportViewSet, basename="damage-report")
router.register(r"task-dependencies", TaskDependencyViewSet, basename="task-dependency")

# Floor Plans & Colors
router.register(r"floor-plans", FloorPlanViewSet, basename="floor-plan")
router.register(r"plan-pins", PlanPinViewSet, basename="plan-pin")
router.register(r"color-samples", ColorSampleViewSet, basename="color-sample")
router.register(r"color-approvals", ColorApprovalViewSet, basename="color-approval")

# Projects
router.register(r"projects", ProjectViewSet, basename="project")
router.register(r"project-manager-assignments", ProjectManagerAssignmentViewSet, basename="project-manager-assignment")

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
router.register(r"payroll/tax-profiles", TaxProfileViewSet, basename="tax-profile")  # Gap B

# Security: 2FA
router.register(r"2fa", TwoFactorViewSet, basename="twofactor")

# Module 21: Business Intelligence Analytics
router.register(r"bi", BIAnalyticsViewSet, basename="bi-analytics")

urlpatterns = [
    # JWT Auth
    path("auth/login/", TwoFactorTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("auth/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
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
]
