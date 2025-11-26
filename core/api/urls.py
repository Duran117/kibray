from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from .views import TwoFactorTokenObtainPairView, TwoFactorViewSet
from .views import (
    NotificationViewSet, ChatChannelViewSet, ChatMessageViewSet,
    TaskViewSet, DamageReportViewSet, FloorPlanViewSet, PlanPinViewSet,
    ColorSampleViewSet, ProjectViewSet, ScheduleCategoryViewSet, ScheduleItemViewSet,
    IncomeViewSet, ExpenseViewSet, CostCodeViewSet, BudgetLineViewSet,
    DailyLogPlanningViewSet, TaskTemplateViewSet, WeatherSnapshotViewSet,
    DailyPlanViewSet, PlannedActivityViewSet, TimeEntryViewSet,
    MaterialRequestViewSet, MaterialCatalogViewSet,
    ClientRequestViewSet,
    ClientRequestAttachmentViewSet,
    SitePhotoViewSet,
    InventoryItemViewSet, InventoryLocationViewSet, ProjectInventoryViewSet, InventoryMovementViewSet,
    InvoiceViewSet,
    PayrollPeriodViewSet, PayrollRecordViewSet, PayrollPaymentViewSet,
    PermissionMatrixViewSet, AuditLogViewSet, LoginAttemptViewSet,
    global_search, save_changeorder_photo_annotations, delete_changeorder_photo,
    update_changeorder_photo_image,
    InvoiceDashboardView, MaterialsDashboardView, FinancialDashboardView, PayrollDashboardView,
    InvoiceTrendsView, MaterialsUsageAnalyticsView, AdminDashboardView
)
from .dashboard_extra import ProjectDashboardView, ClientDashboardView

router = DefaultRouter()
# Notifications & Chat
router.register(r'notifications', NotificationViewSet, basename='notification')
# Security & Audit (Phase 9)
router.register(r'permissions', PermissionMatrixViewSet, basename='permission-matrix')
router.register(r'audit-logs', AuditLogViewSet, basename='audit-log')
router.register(r'login-attempts', LoginAttemptViewSet, basename='login-attempt')

router.register(r'chat/channels', ChatChannelViewSet, basename='chat-channel')
router.register(r'chat/messages', ChatMessageViewSet, basename='chat-message')

# Tasks & Reports
router.register(r'tasks', TaskViewSet, basename='task')
router.register(r'damage-reports', DamageReportViewSet, basename='damage-report')

# Floor Plans & Colors
router.register(r'floor-plans', FloorPlanViewSet, basename='floor-plan')
router.register(r'plan-pins', PlanPinViewSet, basename='plan-pin')
router.register(r'color-samples', ColorSampleViewSet, basename='color-sample')

# Projects
router.register(r'projects', ProjectViewSet, basename='project')

# Schedule
router.register(r'schedule/categories', ScheduleCategoryViewSet, basename='schedule-category')
router.register(r'schedule/items', ScheduleItemViewSet, basename='schedule-item')

# Financial (NEW)
router.register(r'incomes', IncomeViewSet, basename='income')
router.register(r'expenses', ExpenseViewSet, basename='expense')
router.register(r'cost-codes', CostCodeViewSet, basename='cost-code')
router.register(r'budget-lines', BudgetLineViewSet, basename='budget-line')
router.register(r'invoices', InvoiceViewSet, basename='invoice')

# Phase 1: Planning & Weather (NEW)
router.register(r'daily-logs', DailyLogPlanningViewSet, basename='daily-log')
router.register(r'task-templates', TaskTemplateViewSet, basename='task-template')
router.register(r'weather-snapshots', WeatherSnapshotViewSet, basename='weather-snapshot')
router.register(r'daily-plans', DailyPlanViewSet, basename='daily-plan')
router.register(r'planned-activities', PlannedActivityViewSet, basename='planned-activity')
router.register(r'time-entries', TimeEntryViewSet, basename='time-entry')

# Module 14: Materials & Inventory
router.register(r'material-requests', MaterialRequestViewSet, basename='material-request')
router.register(r'material-catalog', MaterialCatalogViewSet, basename='material-catalog')
router.register(r'client-requests', ClientRequestViewSet, basename='client-request')
router.register(r'client-request-attachments', ClientRequestAttachmentViewSet, basename='client-request-attachment')
router.register(r'site-photos', SitePhotoViewSet, basename='site-photo')
router.register(r'inventory/items', InventoryItemViewSet, basename='inventory-item')
router.register(r'inventory/locations', InventoryLocationViewSet, basename='inventory-location')
router.register(r'inventory/stocks', ProjectInventoryViewSet, basename='project-inventory')
router.register(r'inventory/movements', InventoryMovementViewSet, basename='inventory-movement')

# Module 16: Payroll
router.register(r'payroll/periods', PayrollPeriodViewSet, basename='payroll-period')
router.register(r'payroll/records', PayrollRecordViewSet, basename='payroll-record')
router.register(r'payroll/payments', PayrollPaymentViewSet, basename='payroll-payment')

# Security: 2FA
router.register(r'2fa', TwoFactorViewSet, basename='twofactor')

urlpatterns = [
    # JWT Auth
    path('auth/login/', TwoFactorTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    # Global Search
    path('search/', global_search, name='global_search'),
    # ChangeOrder Photos
    path('changeorder-photo/<int:photo_id>/annotations/', save_changeorder_photo_annotations, name='save_photo_annotations'),
    path('changeorder-photo/<int:photo_id>/delete/', delete_changeorder_photo, name='delete_photo'),
    path('changeorder-photo/<int:photo_id>/annotated-image/', update_changeorder_photo_image, name='update_photo_image'),
    # API routes
    path('', include(router.urls)),
    # Dashboards
    path('dashboards/invoices/', InvoiceDashboardView.as_view(), name='dashboard-invoices'),
    path('dashboards/invoices/trends/', InvoiceTrendsView.as_view(), name='dashboard-invoice-trends'),
    path('dashboards/materials/', MaterialsDashboardView.as_view(), name='dashboard-materials'),
    path('dashboards/materials/usage/', MaterialsUsageAnalyticsView.as_view(), name='dashboard-materials-usage'),
    path('dashboards/financial/', FinancialDashboardView.as_view(), name='dashboard-financial'),
    path('dashboards/payroll/', PayrollDashboardView.as_view(), name='dashboard-payroll'),
    path('dashboards/admin/', AdminDashboardView.as_view(), name='dashboard-admin'),
    path('dashboards/projects/<int:project_id>/', ProjectDashboardView.as_view(), name='dashboard-project'),
    path('dashboards/client/', ClientDashboardView.as_view(), name='dashboard-client'),
]
