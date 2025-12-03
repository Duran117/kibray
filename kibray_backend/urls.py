from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.contrib.auth.views import LogoutView
from django.urls import include, path
from django.views.generic import RedirectView
from django.views.i18n import JavaScriptCatalog
from django.views.i18n import set_language as dj_set_language
from rest_framework.routers import DefaultRouter

from core import views
from core import views_financial as fin_views
from core import views_notifications as notif_views
from core.api.views import tasks_gantt_alias
from reports.api.views import ProjectCostSummaryView
from signatures.api.views import SignatureViewSet

signatures_router = DefaultRouter()
signatures_router.register(r"signatures", SignatureViewSet, basename="signature")

urlpatterns = [
    # Home
    path("", views.root_redirect, name="home"),
    # Auth
    path("login/", auth_views.LoginView.as_view(template_name="core/login.html"), name="login"),
    path("logout/", LogoutView.as_view(next_page="login"), name="logout"),
    
    # Phase 4 React Navigation App (SPA routes)
    path("files/", views.navigation_app_view, name="navigation_files"),
    path("users/", views.navigation_app_view, name="navigation_users"),
    path("calendar/", views.navigation_app_view, name="navigation_calendar"),
    path("chat/", views.navigation_app_view, name="navigation_chat"),
    path("reports/", views.navigation_app_view, name="navigation_reports"),
    path("notifications/", views.navigation_app_view, name="navigation_notifications"),
    path("search/", views.navigation_app_view, name="navigation_search"),
    
    # Admin
    path("admin/", admin.site.urls),
    # Dashboard(s)
    path("dashboard/", views.dashboard_view, name="dashboard"),
    path("dashboard/admin/", views.dashboard_admin, name="dashboard_admin"),
    path("dashboard/bi/", views.executive_bi_dashboard, name="dashboard_bi"),
    path("schedule/master/", views.master_schedule_center, name="master_schedule_center"),
    path("focus/", views.focus_wizard, name="focus_wizard"),
    path("planner/", lambda req: __import__('core.views_planner', fromlist=['strategic_ritual_wizard']).strategic_ritual_wizard(req), name="strategic_planner"),
    path("dashboard/employee/", views.dashboard_employee, name="dashboard_employee"),
    path("dashboard/pm/", views.dashboard_pm, name="dashboard_pm"),
    path("dashboard/pm/select/<str:action>/", views.pm_select_project, name="pm_select_project"),
    path("dashboard/client/", views.dashboard_client, name="dashboard_client"),
    path("dashboard/designer/", views.dashboard_designer, name="dashboard_designer"),
    path("dashboard/superintendent/", views.dashboard_superintendent, name="dashboard_superintendent"),
    path("dashboard/analytics/", views.analytics_dashboard, name="analytics_dashboard"),
    # Demo/Testing
    path("demo/js-i18n/", views.js_i18n_demo, name="js_i18n_demo"),
    # Project list & CRUD
    path("projects/", views.project_list, name="project_list"),
    path("projects/create/", views.project_create, name="project_create"),
    path("projects/<int:project_id>/edit/", views.project_edit, name="project_edit"),
    path("projects/<int:project_id>/delete/", views.project_delete, name="project_delete"),
    path("projects/<int:project_id>/toggle-status/", views.project_status_toggle, name="project_status_toggle"),
    # Project overview + acciones
    path("projects/<int:project_id>/overview/", views.project_overview, name="project_overview"),
    path("projects/<int:project_id>/profit/", views.project_profit_dashboard, name="project_profit_dashboard"),
    path("projects/<int:project_id>/materials/request/", views.materials_request_view, name="materials_request"),
    path("projects/<int:project_id>/pickup/", views.pickup_view, name="pickup_view"),
    path("projects/<int:project_id>/inventory/", views.inventory_view, name="inventory_view"),
    path("projects/<int:project_id>/inventory/move/", views.inventory_move_view, name="inventory_move"),
    path("projects/<int:project_id>/inventory/history/", views.inventory_history_view, name="inventory_history"),
    path("projects/<int:project_id>/tasks/", views.task_list_view, name="task_list"),
    path("tasks/<int:task_id>/edit/", views.task_edit_view, name="task_edit"),
    path("tasks/<int:task_id>/delete/", views.task_delete_view, name="task_delete"),
    path("projects/<int:project_id>/schedule/", views.project_schedule_view, name="project_schedule"),
    # Schedule Generator (Hierarchical)
    path("projects/<int:project_id>/schedule/generator/", views.schedule_generator_view, name="schedule_generator"),
    path("schedule/category/<int:category_id>/edit/", views.schedule_category_edit, name="schedule_category_edit"),
    path(
        "schedule/category/<int:category_id>/delete/", views.schedule_category_delete, name="schedule_category_delete"
    ),
    path("schedule/item/<int:item_id>/edit/", views.schedule_item_edit, name="schedule_item_edit"),
    path("schedule/item/<int:item_id>/delete/", views.schedule_item_delete, name="schedule_item_delete"),
    # Calendar Integration
    path("projects/<int:project_id>/schedule/export.ics", views.project_schedule_ics, name="project_schedule_ics"),
    path(
        "projects/<int:project_id>/schedule/google-calendar/",
        views.project_schedule_google_calendar,
        name="project_schedule_google_calendar",
    ),
    # React Gantt Chart
    path("projects/<int:project_id>/schedule/gantt/", views.schedule_gantt_react_view, name="schedule_gantt_react"),
    # Site photos
    path("projects/<int:project_id>/photos/", views.site_photo_list, name="site_photo_list"),
    path("projects/<int:project_id>/photos/new/", views.site_photo_create, name="site_photo_create"),
    # Color Samples
    path("projects/<int:project_id>/colors/", views.color_sample_list, name="color_sample_list"),
    path("projects/<int:project_id>/colors/new/", views.color_sample_create, name="color_sample_create"),
    path("colors/sample/<int:sample_id>/", views.color_sample_detail, name="color_sample_detail"),
    path("colors/sample/<int:sample_id>/edit/", views.color_sample_edit, name="color_sample_edit"),
    path("colors/sample/<int:sample_id>/delete/", views.color_sample_delete, name="color_sample_delete"),
    path("colors/sample/<int:sample_id>/review/", views.color_sample_review, name="color_sample_review"),
    path(
        "colors/sample/<int:sample_id>/quick-action/", views.color_sample_quick_action, name="color_sample_quick_action"
    ),
    # Floor Plans
    path("projects/<int:project_id>/plans/", views.floor_plan_list, name="floor_plan_list"),
    path("projects/<int:project_id>/plans/new/", views.floor_plan_create, name="floor_plan_create"),
    path("plans/<int:plan_id>/", views.floor_plan_detail, name="floor_plan_detail"),
    path("plans/<int:plan_id>/edit/", views.floor_plan_edit, name="floor_plan_edit"),
    path("plans/<int:plan_id>/delete/", views.floor_plan_delete, name="floor_plan_delete"),
    path("plans/<int:plan_id>/add-pin/", views.floor_plan_add_pin, name="floor_plan_add_pin"),
    path("pins/<int:pin_id>/detail.json", views.pin_detail_ajax, name="pin_detail_ajax"),
    # Touch-up board
    path("projects/<int:project_id>/touchups/", views.touchup_board, name="touchup_board"),
    path("projects/<int:project_id>/touchups-react/", views.touchup_board_react, name="touchup_board_react"),
    path("touchups/quick-update/<int:task_id>/", views.touchup_quick_update, name="touchup_quick_update"),
    # Color Approvals React
    path("color-approvals/", views.color_approvals_react, name="color_approvals_react"),
    path(
        "projects/<int:project_id>/color-approvals/", views.color_approvals_react, name="color_approvals_react_project"
    ),
    # PM Assignments React
    path("pm-assignments/", views.pm_assignments_react, name="pm_assignments_react"),
    # Damage reports
    path("projects/<int:project_id>/damages/", views.damage_report_list, name="damage_report_list"),
    path("damages/<int:report_id>/", views.damage_report_detail, name="damage_report_detail"),
    path("damages/<int:report_id>/edit/", views.damage_report_edit, name="damage_report_edit"),
    path("damages/<int:report_id>/delete/", views.damage_report_delete, name="damage_report_delete"),
    path("damages/<int:report_id>/add-photos/", views.damage_report_add_photos, name="damage_report_add_photos"),
    path(
        "damages/<int:report_id>/update-status/", views.damage_report_update_status, name="damage_report_update_status"
    ),
    # Design chat (legacy simple); new channel-based chat below
    path("projects/<int:project_id>/design-chat/", views.design_chat, name="design_chat"),
    # Channel-based project chat
    path("projects/<int:project_id>/chat/", views.project_chat_index, name="project_chat_index"),
    path("projects/<int:project_id>/chat/<int:channel_id>/", views.project_chat_room, name="project_chat_room"),
    # PDF resumen de proyecto
    path("project/<int:project_id>/pdf/", views.project_pdf_view, name="project_pdf"),
    # Crear entidades simples
    path("schedule/add/", views.schedule_create_view, name="schedule_create"),
    path("expense/add/", views.expense_create_view, name="expense_create"),
    path("income/add/", views.income_create_view, name="income_create"),
    path("timeentry/add/", views.timeentry_create_view, name="timeentry_create"),
    path("timeentry/<int:entry_id>/edit/", views.timeentry_edit_view, name="timeentry_edit"),
    path("timeentry/<int:entry_id>/delete/", views.timeentry_delete_view, name="timeentry_delete"),
    # Income/Expense lists & CRUD
    path("incomes/", views.income_list, name="income_list"),
    path("incomes/<int:income_id>/edit/", views.income_edit_view, name="income_edit"),
    path("incomes/<int:income_id>/delete/", views.income_delete_view, name="income_delete"),
    path("expenses/", views.expense_list, name="expense_list"),
    path("expenses/<int:expense_id>/edit/", views.expense_edit_view, name="expense_edit"),
    path("expenses/<int:expense_id>/delete/", views.expense_delete_view, name="expense_delete"),
    # Vista cliente
    path("proyecto/<int:project_id>/", views.client_project_view, name="client_project_view"),
    path("proyecto/<int:project_id>/agregar_tarea/", views.agregar_tarea, name="agregar_tarea"),  # type: ignore[arg-type]
    path("proyecto/<int:project_id>/agregar_comentario/", views.agregar_comentario, name="agregar_comentario"),
    # Change Orders
    path("changeorder/<int:changeorder_id>/", views.changeorder_detail_view, name="changeorder_detail"),
    path("changeorder/<int:changeorder_id>/billing-history/", views.changeorder_billing_history_view, name="changeorder_billing_history"),
    path("changeorder/<int:changeorder_id>/sign/", views.changeorder_customer_signature_view, name="changeorder_customer_signature"),
    path("changeorder/<int:changeorder_id>/sign/<str:token>/", views.changeorder_customer_signature_view, name="changeorder_customer_signature_token"),
    path("changeorder/add/", views.changeorder_create_view, name="changeorder_create"),
    path("changeorder/<int:co_id>/edit/", views.changeorder_edit_view, name="changeorder_edit"),
    path("changeorder/<int:co_id>/delete/", views.changeorder_delete_view, name="changeorder_delete"),
    path("changeorders/board/", views.changeorder_board_view, name="changeorder_board"),
    path("changeorders/unassigned-time/", views.unassigned_timeentries_view, name="unassigned_timeentries"),
    # Deprecated legacy photo annotation endpoints removed (use /api/v1/changeorder-photo/<id>/...)
    path("changeorder/photo-editor/", views.photo_editor_standalone_view, name="photo_editor_standalone"),
    # Client Requests
    path("projects/<int:project_id>/client-requests/new/", views.client_request_create, name="client_request_create"),
    path("projects/<int:project_id>/client-requests/", views.client_requests_list, name="client_requests_list"),
    path("client-requests/", views.client_requests_list, name="client_requests_list_all"),
    path(
        "client-requests/<int:request_id>/convert/", views.client_request_convert_to_co, name="client_request_convert"
    ),
    # Payroll
    # Nuevo sistema de nómina
    path("payroll/week/", views.payroll_weekly_review, name="payroll_weekly_review"),
    path("payroll/summary/", views.payroll_summary_view, name="payroll_summary"),
    path("payroll/record/<int:record_id>/pay/", views.payroll_record_payment, name="payroll_record_payment"),
    path("payroll/history/", views.payroll_payment_history, name="payroll_payment_history"),
    path(
        "payroll/history/employee/<int:employee_id>/",
        views.payroll_payment_history,
        name="payroll_payment_history_employee",
    ),
    # Invoices
    path("invoices/", views.invoice_list, name="invoice_list"),
    # path("invoices/new/", views.invoice_create_view, name="invoice_create"),  # DEPRECATED: Use invoice_builder instead
    path("invoices/builder/<int:project_id>/", views.invoice_builder_view, name="invoice_builder"),
    path("invoices/payments/", views.invoice_payment_dashboard, name="invoice_payment_dashboard"),
    path("invoices/<int:invoice_id>/pay/", views.record_invoice_payment, name="record_invoice_payment"),
    path("invoices/<int:invoice_id>/mark-sent/", views.invoice_mark_sent, name="invoice_mark_sent"),
    path("invoices/<int:invoice_id>/mark-approved/", views.invoice_mark_approved, name="invoice_mark_approved"),
    path("invoices/<int:pk>/", views.invoice_detail, name="invoice_detail"),
    # path("invoices/<int:pk>/edit/", views.invoice_edit, name="invoice_edit"),  # DEPRECATED: Edit from invoice_detail if needed
    path("invoices/<int:pk>/pdf/", views.invoice_pdf, name="invoice_pdf"),
    path("ajax/changeorders/", views.changeorders_ajax, name="changeorders_ajax"),
    path("ajax/changeorder_lines/", views.changeorder_lines_ajax, name="changeorder_lines_ajax"),
    # Change Order API endpoints
    path(
        "api/changeorders/<int:co_id>/update-status/", views.changeorder_update_status, name="changeorder_update_status"
    ),
    path(
        "api/changeorders/<int:co_id>/send-to-client/",
        views.changeorder_send_to_client,
        name="changeorder_send_to_client",
    ),
    path("api/projects/<int:project_id>/approved-colors/", views.get_approved_colors, name="get_approved_colors"),
    # Cost codes / presupuesto
    path("cost-codes/", views.costcode_list_view, name="costcode_list"),
    path("projects/<int:project_id>/budget/", views.budget_lines_view, name="budget_lines"),
    path("budget-line/<int:line_id>/plan/", views.budget_line_plan_view, name="budget_line_plan"),
    # Estimates
    path("projects/<int:project_id>/estimates/new/", views.estimate_create_view, name="estimate_create"),
    path("estimates/<int:estimate_id>/", views.estimate_detail_view, name="estimate_detail"),
    path("estimates/<int:estimate_id>/send-email/", views.estimate_send_email, name="estimate_send_email"),
    # Project Activation
    path("projects/<int:project_id>/activate/", views.project_activation_view, name="project_activation"),
    # Daily log / RFIs / Issues / Risks
    path("projects/<int:project_id>/daily-log/", views.daily_log_view, name="daily_log"),
    path("projects/<int:project_id>/daily-log/create/", views.daily_log_create, name="daily_log_create"),
    path("daily-log/<int:log_id>/", views.daily_log_detail, name="daily_log_detail"),
    path("projects/<int:project_id>/rfis/", views.rfi_list_view, name="rfi_list"),
    path("rfis/<int:rfi_id>/answer/", views.rfi_answer_view, name="rfi_answer"),
    path("rfis/<int:rfi_id>/edit/", views.rfi_edit_view, name="rfi_edit"),
    path("rfis/<int:rfi_id>/delete/", views.rfi_delete_view, name="rfi_delete"),
    path("projects/<int:project_id>/issues/", views.issue_list_view, name="issue_list"),
    path("issues/<int:issue_id>/edit/", views.issue_edit_view, name="issue_edit"),
    path("issues/<int:issue_id>/delete/", views.issue_delete_view, name="issue_delete"),
    path("projects/<int:project_id>/risks/", views.risk_list_view, name="risk_list"),
    path("risks/<int:risk_id>/edit/", views.risk_edit_view, name="risk_edit"),
    path("risks/<int:risk_id>/delete/", views.risk_delete_view, name="risk_delete"),
    # File Organization
    path("projects/<int:project_id>/files/", views.project_files_view, name="project_files"),
    path("projects/<int:project_id>/files/category/create/", views.file_category_create, name="file_category_create"),
    path("projects/<int:project_id>/files/<int:category_id>/upload/", views.file_upload, name="file_upload"),
    path("files/<int:file_id>/delete/", views.file_delete, name="file_delete"),
    path("files/<int:file_id>/download/", views.file_download, name="file_download"),
    path("files/<int:file_id>/edit/", views.file_edit_metadata, name="file_edit_metadata"),
    # Touch-up Pins (deprecated flow) - gated via settings.TOUCHUP_PIN_ENABLED
    # These routes are disabled by default to consolidate on Task(is_touchup=True)
    # Set TOUCHUP_PIN_ENABLED=True to re-enable the legacy TouchUpPin UI.
    # Note: Data model remains for compatibility and potential future migration.
    *(
        [
            path("projects/<int:project_id>/touchup-plans/", views.touchup_plans_list, name="touchup_plans_list"),
            path("plans/<int:plan_id>/touchups/", views.touchup_plan_detail, name="touchup_plan_detail"),
            path("plans/<int:plan_id>/touchups/create/", views.touchup_create, name="touchup_create"),
            path("touchups/<int:touchup_id>/", views.touchup_detail_ajax, name="touchup_detail_ajax"),
            path("touchups/<int:touchup_id>/update/", views.touchup_update, name="touchup_update"),
            path("touchups/<int:touchup_id>/complete/", views.touchup_complete, name="touchup_complete"),
            path("touchups/<int:touchup_id>/delete/", views.touchup_delete, name="touchup_delete"),
            path("touchups/<int:touchup_id>/approve/", views.touchup_approve, name="touchup_approve"),
            path("touchups/<int:touchup_id>/reject/", views.touchup_reject, name="touchup_reject"),
        ]
        if getattr(settings, "TOUCHUP_PIN_ENABLED", False)
        else [
            # Stub route: redirect to Task-based touch-up board when legacy UI disabled
            path("projects/<int:project_id>/touchup-plans/", views.touchup_board, name="touchup_plans_list"),
        ]
    ),
    # Info Pins (Regular floor plan pins)
    path("pins/<int:pin_id>/info/", views.pin_info_ajax, name="pin_info_ajax"),
    path("pins/<int:pin_id>/update/", views.pin_update, name="pin_update"),
    path("pins/<int:pin_id>/add-photo/", views.pin_add_photo, name="pin_add_photo"),
    path("pins/attachments/<int:attachment_id>/delete/", views.pin_delete_photo, name="pin_delete_photo"),
    # Earned Value + export
    path("projects/<int:project_id>/earned-value/", views.project_ev_view, name="project_ev"),
    path("projects/<int:project_id>/earned-value/series/", views.project_ev_series, name="project_ev_series"),
    path("projects/<int:project_id>/earned-value/csv/", views.project_ev_csv, name="project_ev_csv"),
    path("projects/<int:project_id>/progress/upload/", views.upload_project_progress, name="upload_project_progress"),
    path(
        "projects/<int:project_id>/progress/sample.csv", views.download_progress_sample, name="download_progress_sample"
    ),
    path("projects/<int:project_id>/progress/export.csv", views.project_progress_csv, name="project_progress_csv"),
    path("projects/<int:project_id>/progress/<int:pk>/delete/", views.delete_progress, name="delete_progress"),
    path("projects/<int:project_id>/progress/<int:pk>/edit/", views.edit_progress, name="edit_progress"),
    path(
        "projects/<int:project_id>/progress/",
        RedirectView.as_view(pattern_name="project_ev", permanent=False),
        name="project_progress",
    ),
    # Legacy redirect
    path(
        "project/<int:project_id>/earned-value/",
        RedirectView.as_view(pattern_name="project_ev", permanent=True),
        name="project_ev_legacy",
    ),
    # Inventario
    path("projects/<int:project_id>/inventory/", views.inventory_view, name="inventory_view"),
    path("projects/<int:project_id>/inventory/move/", views.inventory_move_view, name="inventory_move"),
    path("projects/<int:project_id>/inventory/history/", views.inventory_history_view, name="inventory_history"),
    # Materials
    path(
        "materials/request/<int:request_id>/receive-ticket/",
        views.materials_receive_ticket_view,
        name="materials_receive_ticket",
    ),
    path(
        "projects/<int:project_id>/materials/direct-purchase/",
        views.materials_direct_purchase_view,
        name="materials_direct_purchase",
    ),
    path("materials/requests/", views.materials_requests_list_view, name="materials_requests_list_all"),
    path(
        "projects/<int:project_id>/materials/requests/",
        views.materials_requests_list_view,
        name="materials_requests_list",
    ),
    path("materials/requests/<int:request_id>/", views.materials_request_detail_view, name="materials_request_detail"),
    path(
        "materials/requests/<int:request_id>/mark-ordered/",
        views.materials_mark_ordered_view,
        name="materials_mark_ordered",
    ),
    # ACTIVITY 2: Material Request Workflow (Q14.4, Q14.10, Q14.6)
    path(
        "materials/requests/<int:request_id>/submit/", views.materials_request_submit, name="materials_request_submit"
    ),
    path(
        "materials/requests/<int:request_id>/approve/",
        views.materials_request_approve,
        name="materials_request_approve",
    ),
    path(
        "materials/requests/<int:request_id>/reject/", views.materials_request_reject, name="materials_request_reject"
    ),
    path(
        "materials/requests/<int:request_id>/receive-partial/",
        views.materials_receive_partial,
        name="materials_receive_partial",
    ),
    path(
        "materials/requests/<int:request_id>/create-expense/",
        views.materials_create_expense,
        name="materials_create_expense",
    ),
    # ACTIVITY 2: Inventory Management (Q15.5, Q15.11)
    path("inventory/low-stock/", views.inventory_low_stock_alert, name="inventory_low_stock"),
    path("inventory/adjust/<int:item_id>/<int:location_id>/", views.inventory_adjust, name="inventory_adjust"),
    # Daily Planning System
    path("planning/", views.daily_planning_dashboard, name="daily_planning_dashboard"),
    path("planning/project/<int:project_id>/create/", views.daily_plan_create, name="daily_plan_create"),
    path("planning/<int:plan_id>/edit/", views.daily_plan_edit, name="daily_plan_edit"),
    path(
        "planning/activity/<int:activity_id>/delete/",
        views.daily_plan_delete_activity,
        name="daily_plan_delete_activity",
    ),
    path("planning/activity/<int:activity_id>/complete/", views.activity_complete, name="activity_complete"),
    path("planning/employee/morning/", views.employee_morning_dashboard, name="employee_morning_dashboard"),
    path("planning/sop/library/", views.sop_library, name="sop_library"),
    path("planning/sop/create/", views.sop_create_wizard, name="sop_create"),  # NEW: Wizard version
    path("planning/sop/create/classic/", views.sop_create_edit, name="sop_create_classic"),  # OLD: Classic form
    path("planning/sop/<int:template_id>/edit/", views.sop_create_wizard, name="sop_edit"),  # NEW: Wizard for editing
    path("planning/sop/<int:template_id>/edit/classic/", views.sop_create_edit, name="sop_edit_classic"),  # OLD
    # Minutas / Project Timeline
    path("projects/<int:project_id>/minutes/", views.project_minutes_list, name="project_minutes_list"),
    path("projects/<int:project_id>/minutes/new/", views.project_minute_create, name="project_minute_create"),
    path("minutes/<int:minute_id>/", views.project_minute_detail, name="project_minute_detail"),
    # Notifications
    path("notifications/", notif_views.notifications_list, name="notifications_list"),
    path(
        "notifications/<int:notification_id>/mark-read/",
        notif_views.notification_mark_read,
        name="notification_mark_read",
    ),
    path("notifications/mark-all-read/", notif_views.notifications_mark_all_read, name="notifications_mark_all_read"),
    # NUEVAS FUNCIONALIDADES FINANCIERAS 2025
    path("financial/dashboard/", fin_views.financial_dashboard, name="financial_dashboard"),
    path("financial/aging-report/", fin_views.invoice_aging_report, name="invoice_aging_report"),
    path("financial/productivity/", fin_views.productivity_dashboard, name="productivity_dashboard"),
    path("financial/export/", fin_views.export_financial_data, name="export_financial_data"),
    path("financial/performance/", fin_views.employee_performance_review, name="employee_performance_list"),
    path(
        "financial/performance/<int:employee_id>/",
        fin_views.employee_performance_review,
        name="employee_performance_review",
    ),
    # Task detail & my tasks (added to fix broken dashboard links)
    path("tasks/<int:task_id>/", views.task_detail, name="task_detail"),
    path("tasks/my/", views.task_list_all, name="task_list_all"),
    # ACTIVITY 1: Task time tracking (Q11.13)
    path("tasks/<int:task_id>/start-tracking/", views.task_start_tracking, name="task_start_tracking"),
    path("tasks/<int:task_id>/stop-tracking/", views.task_stop_tracking, name="task_stop_tracking"),
    # ACTIVITY 1: Daily plan enhancements (Q12.2, Q12.5, Q12.8)
    path("planning/<int:plan_id>/fetch-weather/", views.daily_plan_fetch_weather, name="daily_plan_fetch_weather"),
    path(
        "planning/<int:plan_id>/convert-activities/",
        views.daily_plan_convert_activities,
        name="daily_plan_convert_activities",
    ),
    path("planning/<int:plan_id>/productivity/", views.daily_plan_productivity, name="daily_plan_productivity"),
    # ===== GESTIÓN DE CLIENTES =====
    path("clients/", views.client_list, name="client_list"),
    path("clients/create/", views.client_create, name="client_create"),
    path("clients/<int:user_id>/", views.client_detail, name="client_detail"),
    path("clients/<int:user_id>/edit/", views.client_edit, name="client_edit"),
    path("clients/<int:user_id>/delete/", views.client_delete, name="client_delete"),
    path("clients/<int:user_id>/reset-password/", views.client_reset_password, name="client_reset_password"),
    path("clients/<int:user_id>/assign-project/", views.client_assign_project, name="client_assign_project"),
    # ===== ADMINISTRACIÓN AVANZADA =====
    # Dashboard principal admin
    path("admin-panel/", include("core.urls_admin")),
    # Explicit Gantt mapping BEFORE including API to ensure resolution
    path("api/v1/tasks/gantt/", tasks_gantt_alias, name="api-tasks-gantt"),
    # REST API v1 (mobile, integrations)
    path("api/v1/", include("core.api.urls")),
    path("api/v1/", include(signatures_router.urls)),
    path(
        "api/v1/reports/project-cost-summary/<int:project_id>/",
        ProjectCostSummaryView.as_view(),
        name="project-cost-summary",
    ),
    # Language switchers
    # Django standard i18n endpoint (expects POST with 'language' and optional 'next')
    path("i18n/setlang/", dj_set_language, name="set_language"),
    # JavaScript translation catalog
    path("jsi18n/", JavaScriptCatalog.as_view(), name="javascript-catalog"),
    # Legacy simple session-based (kept for compatibility)
    path("lang/<str:code>/", views.set_language_view, name="set_language_code"),
    # Public proposal approval (no login required)
    path("proposals/<str:token>/", views.proposal_public_view, name="proposal_public"),
]

# Media/Static en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
