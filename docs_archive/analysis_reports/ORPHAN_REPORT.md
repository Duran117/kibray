# Codebase Quality Analysis Report

**Generated:** 2025-11-29 15:32:48
**Analyzer:** Code Quality Specialist v1.0

---

## Executive Summary

- **Files Analyzed:** 70
- **Unique Definitions:** 1063
- **Orphan Candidates:** 588
- **Duplicate Pairs:** 34

---

## 📦 Candidates for Deletion (Orphans)

*Functions/classes defined but never imported or used elsewhere.*

### `core/admin.py`

- **Class:** `class EmployeeAdmin` (Line 73)
- **Class:** `class IncomeAdmin` (Line 83)
- **Class:** `class ExpenseAdmin` (Line 93)
- **Class:** `class WarrantyTicketAdmin` (Line 102)
- **Class:** `class ProjectAdmin` (Line 111)
- **Class:** `class TimeEntryAdmin` (Line 131)
- **Class:** `class ScheduleAdmin` (Line 152)
- **Class:** `class ScheduleItemAdmin` (Line 167)
- **Class:** `class ProfileAdmin` (Line 176)
- **Class:** `class ClientProjectAccessAdmin` (Line 183)
- **Class:** `class InvoiceLineInline` (Line 191)
- **Class:** `class InvoicePaymentInline` (Line 196)
- **Class:** `class InvoiceAdmin` (Line 204)
- **Class:** `class InvoiceLineAdmin` (Line 218)
- **Class:** `class InvoicePaymentAdmin` (Line 224)
- **Class:** `class BudgetProgressInline` (Line 231)
- **Class:** `class BudgetLineAdmin` (Line 239)
- **Class:** `class BudgetProgressAdmin` (Line 258)
- **Class:** `class CostCodeAdmin` (Line 267)
- **Class:** `class MaterialRequestItemInline` (Line 273)
- **Class:** `class MaterialRequestAdmin` (Line 279)
- **Class:** `class MaterialCatalogAdmin` (Line 286)
- **Class:** `class SitePhotoAdmin` (Line 303)
- **Class:** `class ColorSampleAdmin` (Line 310)
- **Class:** `class ColorApprovalAdmin` (Line 318)
- **Class:** `class PlanPinAttachmentInline` (Line 376)
- **Class:** `class PlanPinInline` (Line 381)
- **Class:** `class FloorPlanAdmin` (Line 388)
- **Class:** `class ProjectManagerAssignmentAdmin` (Line 396)
- **Class:** `class PlanPinAdmin` (Line 404)
- **Class:** `class DamageReportAdmin` (Line 412)
- **Class:** `class DamagePhotoAdmin` (Line 419)
- **Class:** `class DesignChatMessageAdmin` (Line 425)
- **Class:** `class ChatMessageInline` (Line 432)
- **Class:** `class ChatChannelAdmin` (Line 440)
- **Class:** `class ChatMessageAdmin` (Line 449)
- **Class:** `class MeetingMinuteAdmin` (Line 457)
- **Class:** `class NotificationAdmin` (Line 485)
- **Class:** `class InventoryItemAdmin` (Line 493)
- **Class:** `class InventoryLocationAdmin` (Line 502)
- **Class:** `class ProjectInventoryAdmin` (Line 509)
- **Class:** `class InventoryMovementAdmin` (Line 521)
- **Class:** `class SOPReferenceFileInline` (Line 546)
- **Class:** `class ActivityTemplateAdmin` (Line 554)
- **Class:** `class SOPReferenceFileAdmin` (Line 576)
- **Class:** `class PlannedActivityInline` (Line 583)
- **Class:** `class DailyPlanAdmin` (Line 599)
- **Class:** `class PlannedActivityAdmin` (Line 638)
- **Class:** `class ActivityCompletionAdmin` (Line 665)
- **Class:** `class EVSnapshotAdmin` (Line 697)
- **Class:** `class QualityInspectionAdmin` (Line 715)
- **Class:** `class QualityDefectAdmin` (Line 742)
- **Class:** `class RecurringTaskAdmin` (Line 756)
- **Class:** `class GPSCheckInAdmin` (Line 779)
- **Class:** `class ExpenseOCRDataAdmin` (Line 809)
- **Class:** `class InvoiceAutomationAdmin` (Line 844)
- **Class:** `class InventoryBarcodeAdmin` (Line 890)
- **Class:** `class PunchListItemAdmin` (Line 915)
- **Class:** `class SubcontractorAdmin` (Line 935)
- **Class:** `class SubcontractorAssignmentAdmin` (Line 949)
- **Class:** `class EmployeePerformanceMetricAdmin` (Line 963)
- **Class:** `class EmployeeCertificationAdmin` (Line 992)
- **Class:** `class EmployeeSkillLevelAdmin` (Line 1013)
- **Class:** `class SOPCompletionAdmin` (Line 1026)
- **Class:** `class ChangeOrderAdmin` (Line 1040)
- **Class:** `class TaskTemplateAdmin` (Line 1064)
- **Class:** `class ProposalAdmin` (Line 1072)
- **Class:** `class ProposalEmailLogAdmin` (Line 1087)
- **Class:** `class FocusTaskInline` (Line 1121)
- **Class:** `class DailyFocusSessionAdmin` (Line 1133)
- **Class:** `class FocusTaskAdmin` (Line 1184)
- **Class:** `class LifeVisionAdmin` (Line 1282)
- **Class:** `class ExecutiveHabitAdmin` (Line 1312)
- **Class:** `class PowerActionInline` (Line 1320)
- **Class:** `class HabitCompletionInline` (Line 1331)
- **Class:** `class DailyRitualSessionAdmin` (Line 1339)
- **Class:** `class PowerActionAdmin` (Line 1401)
- **Class:** `class HabitCompletionAdmin` (Line 1496)
- **Function:** `employee_key_display(self, obj)` (Line 139)
- **Function:** `approve_selected(self, request, queryset)` (Line 347)
- **Function:** `reject_selected(self, request, queryset)` (Line 361)
- **Function:** `tasks_summary(self, obj)` (Line 463)
- **Function:** `item_sku_display(self, obj)` (Line 514)
- **Function:** `check_materials_action(self, request, queryset)` (Line 656)
- **Function:** `description_short(self, obj)` (Line 1048)
- **Function:** `response_add(self, request, obj, post_url_continue)` (Line 1054)
- **Function:** `response_change(self, request, obj)` (Line 1058)
- **Function:** `proposal_display(self, obj)` (Line 1095)
- **Function:** `success_display(self, obj)` (Line 1100)
- **Function:** `total_tasks_display(self, obj)` (Line 1161)
- **Function:** `completed_tasks_display(self, obj)` (Line 1165)
- **Function:** `is_completed_display(self, obj)` (Line 1379)
- **Function:** `total_actions_display(self, obj)` (Line 1384)
- **Function:** `high_impact_display(self, obj)` (Line 1388)

### `core/api/filters.py`

- **Class:** `class TimeEntryFilter` (Line 42)
- **Class:** `class TaskFilter` (Line 94)
- **Class:** `class ChangeOrderFilter` (Line 109)

### `core/api/focus_api.py`

- **Function:** `this_week(self, request)` (Line 67)
- **Function:** `complete_task(self, request, pk)` (Line 83)
- **Function:** `update_checklist(self, request, pk)` (Line 102)
- **Function:** `upcoming(self, request)` (Line 137)
- **Function:** `frog_history(self, request)` (Line 153)
- **Function:** `toggle_complete(self, request, pk)` (Line 168)
- **Function:** `update_time_block(self, request, pk)` (Line 178)

### `core/api/pagination.py`

- **Class:** `class LargeResultsSetPagination` (Line 39)
- **Class:** `class SmallResultsSetPagination` (Line 50)
- **Class:** `class MobileFriendlyPagination` (Line 61)

### `core/api/permissions.py`

- **Class:** `class IsOwner` (Line 17)
- **Class:** `class IsOwnerOrPM` (Line 31)
- **Class:** `class IsOwnerOrPMOrSuperintendent` (Line 45)
- **Class:** `class CanAccessProject` (Line 59)

### `core/api/serializers.py`

- **Class:** `class UserSerializer` (Line 37)
- **Class:** `class EmployeeSerializer` (Line 43)
- **Class:** `class InvoiceLineAPISerializer` (Line 971)
- **Class:** `class ChatMentionSerializer` (Line 1175)
- **Class:** `class EmployeeMiniSerializer` (Line 1468)
- **Class:** `class MaterialRequestItemSerializer` (Line 1684)
- **Class:** `class TwoFactorSetupSerializer` (Line 2069)
- **Function:** `validate_assigned_to_id(self, value)` (Line 1454)
- **Function:** `validate_status(self, value)` (Line 1782)
- **Function:** `validate_energy_level(self, value)` (Line 2210)
- **Function:** `validate_tasks(self, value)` (Line 2227)

### `core/api/views.py`

- **Function:** `mark_all_read(self, request)` (Line 131)
- **Function:** `count_unread(self, request)` (Line 143)
- **Function:** `my_permissions(self, request)` (Line 234)
- **Function:** `check_permission(self, request)` (Line 260)
- **Function:** `entity_history(self, request)` (Line 321)
- **Function:** `suspicious_activity(self, request)` (Line 380)
- **Function:** `mark_sent(self, request, pk)` (Line 452)
- **Function:** `mark_approved(self, request, pk)` (Line 465)
- **Function:** `record_payment(self, request, pk)` (Line 477)
- **Function:** `touchup_kanban(self, request)` (Line 537)
- **Function:** `quick_status(self, request, pk)` (Line 671)
- **Function:** `add_dependency(self, request, pk)` (Line 726)
- **Function:** `remove_dependency(self, request, pk)` (Line 746)
- **Function:** `time_summary(self, request, pk)` (Line 786)
- **Function:** `hours_summary(self, request, pk)` (Line 843)
- **Function:** `add_photo(self, request, pk)` (Line 984)
- **Function:** `add_photo_underscore(self, request, pk)` (Line 999)
- **Function:** `assess(self, request, pk)` (Line 1039)
- **Function:** `start_work(self, request, pk)` (Line 1103)
- **Function:** `convert_to_co(self, request, pk)` (Line 1157)
- **Function:** `analytics(self, request)` (Line 1201)
- **Function:** `generate_expenses(self, request, pk)` (Line 1250)
- **Function:** `lock(self, request, pk)` (Line 1256)
- **Function:** `recompute(self, request, pk)` (Line 1264)
- **Function:** `export(self, request, pk)` (Line 1276)
- **Function:** `create_expense(self, request, pk)` (Line 1352)
- **Function:** `audit(self, request, pk)` (Line 1358)
- **Function:** `enable(self, request)` (Line 1417)
- **Function:** `disable(self, request)` (Line 1436)
- **Function:** `create_version(self, request, pk)` (Line 1515)
- **Function:** `update_annotations(self, request, pk)` (Line 1880)
- **Function:** `request_changes(self, request, pk)` (Line 2040)
- **Function:** `bulk_update(self, request)` (Line 2140)
- **Function:** `financial_summary(self, request, pk)` (Line 2459)
- **Function:** `budget_overview(self, request)` (Line 2490)
- **Function:** `instantiate_templates(self, request, pk)` (Line 2772)
- **Function:** `bulk_import(self, request)` (Line 2902)
- **Function:** `toggle_favorite(self, request, pk)` (Line 2975)
- **Function:** `convert_activities(self, request, pk)` (Line 3032)
- **Function:** `add_activity(self, request, pk)` (Line 3045)
- **Function:** `recompute_actual_hours(self, request, pk)` (Line 3053)
- **Function:** `by_project_date(self, request)` (Line 3136)
- **Function:** `stop(self, request, pk)` (Line 3168)
- **Function:** `valuation_report(self, request, pk)` (Line 3224)
- **Function:** `calculate_cogs(self, request, pk)` (Line 3277)
- **Function:** `low_stock(self, request)` (Line 3340)
- **Function:** `submit(self, request, pk)` (Line 3415)
- **Function:** `direct_purchase_expense(self, request, pk)` (Line 3452)
- **Function:** `project_stock(self, request)` (Line 3479)
- **Function:** `report_usage(self, request)` (Line 3506)
- **Function:** `quick_request(self, request)` (Line 3588)
- **Function:** `add_participant(self, request, pk)` (Line 3761)
- **Function:** `remove_participant(self, request, pk)` (Line 3781)
- **Function:** `soft_delete(self, request, pk)` (Line 3888)
- **Function:** `my_mentions(self, request)` (Line 3910)
- **Function:** `destroy(self, request)` (Line 3992)
- **Function:** `gallery(self, request)` (Line 4124)
- **Function:** `company_kpis(self, request)` (Line 5270)
- **Function:** `cash_flow_projection(self, request)` (Line 5297)
- **Function:** `project_margins(self, request)` (Line 5348)
- **Function:** `gantt(self, request)` (Line 604)

### `core/apps.py`

- **Class:** `class CoreConfig` (Line 4)
- **Function:** `ready(self)` (Line 8)

### `core/audit.py`

- **Function:** `log_audit_action(user, action, entity_type, entity_id, entity_repr, old_values, new_values, request, notes, success, error_message)` (Line 27)
- **Function:** `log_user_login(sender, request, user)` (Line 91)
- **Function:** `log_user_logout(sender, request, user)` (Line 115)
- **Function:** `log_login_failure(sender, credentials, request)` (Line 130)
- **Function:** `capture_pre_save_state(sender, instance)` (Line 163)
- **Function:** `audit_project_changes(sender, instance, created)` (Line 174)
- **Function:** `audit_model_deletion(sender, instance)` (Line 218)
- **Class:** `class AuditLogMiddleware` (Line 244)
- **Function:** `__call__(self, request)` (Line 253)

### `core/context_processors.py`

- **Function:** `onesignal_config(request)` (Line 18)
- **Function:** `notification_badges(request)` (Line 26)

### `core/forms.py`

- **Class:** `class PayrollPaymentForm` (Line 121)
- **Class:** `class InvoiceLineForm` (Line 199)
- **Class:** `class DailyLogPhotoForm` (Line 319)
- **Class:** `class ChangeOrderPhotoForm` (Line 532)
- **Class:** `class ChangeOrderStatusForm` (Line 543)
- **Class:** `class PlannedActivityForm` (Line 1092)
- **Class:** `class TouchUpCompletionForm` (Line 1349)

### `core/management/commands/analyze_codebase.py`

- **Class:** `class CodeAnalyzer` (Line 37)
- **Function:** `is_django_standard_method(self, name)` (Line 82)
- **Function:** `should_skip_file(self, filepath)` (Line 97)
- **Function:** `extract_function_body(self, node)` (Line 123)
- **Function:** `scan_definitions(self, filepath)` (Line 147)
- **Function:** `scan_usages(self, filepath)` (Line 191)
- **Function:** `find_orphans(self)` (Line 224)
- **Function:** `calculate_similarity(self, code1, code2)` (Line 250)
- **Function:** `find_duplicates(self)` (Line 261)
- **Function:** `analyze(self)` (Line 295)
- **Function:** `generate_report(self, analyzer, base_dir)` (Line 356)

### `core/management/commands/create_demo_project.py`

- **Function:** `create_team(self)` (Line 75)
- **Function:** `create_client(self)` (Line 176)
- **Function:** `create_project(self, client)` (Line 189)
- **Function:** `create_time_entries(self, project, employees)` (Line 221)
- **Function:** `create_expenses(self, project)` (Line 260)
- **Function:** `create_incomes(self, project)` (Line 298)

### `core/management/commands/deep_audit.py`

- **Function:** `add_style(self, text, color)` (Line 31)
- **Function:** `print_success(self, text)` (Line 41)
- **Function:** `print_error(self, text)` (Line 45)
- **Function:** `print_warning(self, text)` (Line 50)
- **Function:** `check_url_registrations(self)` (Line 55)
- **Function:** `check_data_models(self)` (Line 109)
- **Function:** `check_security_and_logic(self)` (Line 198)
- **Function:** `check_integration(self)` (Line 291)

### `core/management/commands/fix_critical_data.py`

- **Function:** `fix_orphan_projects(self, dry_run)` (Line 100)
- **Function:** `purge_test_data(self, dry_run)` (Line 145)
- **Function:** `fix_code_breakpoint(self, dry_run)` (Line 218)

### `core/management/commands/forensic_audit.py`

- **Function:** `add_issue(self, severity, category, message, file_path, line_num)` (Line 53)
- **Function:** `write_section_header(self, title, level)` (Line 65)
- **Function:** `scan_python_files(self)` (Line 77)
- **Function:** `scan_templates(self)` (Line 230)
- **Function:** `scan_database(self)` (Line 337)
- **Function:** `scan_business_rules(self)` (Line 433)
- **Function:** `scan_todos(self)` (Line 539)
- **Function:** `generate_summary(self)` (Line 627)

### `core/management/commands/import_progress.py`

- **Function:** `to_decimal(val, default)` (Line 25)
- **Function:** `open_csv_source(path_or_url)` (Line 31)
- **Function:** `dict_reader_from_io(f)` (Line 41)

### `core/management/commands/setup_roles.py`

- **Function:** `setup_general_manager(self)` (Line 54)
- **Function:** `setup_project_manager(self)` (Line 88)
- **Function:** `setup_project_manager_trainee(self)` (Line 152)
- **Function:** `setup_designer(self)` (Line 212)
- **Function:** `setup_superintendent(self)` (Line 251)
- **Function:** `setup_employee(self)` (Line 302)
- **Function:** `setup_client(self)` (Line 331)

### `core/models.py`

- **Function:** `generate_project_code(year)` (Line 27)
- **Function:** `generate_employee_key()` (Line 62)
- **Function:** `generate_inventory_sku(category)` (Line 94)
- **Function:** `notify_pm_assignment(sender, instance, created)` (Line 314)
- **Function:** `create_or_update_user_profile(sender, instance, created)` (Line 1846)
- **Function:** `calcular_total_horas(employee, week_start, week_end)` (Line 2637)
- **Function:** `create_default_chat_channels(sender, instance, created)` (Line 5007)
- **Class:** `class PaintLeftover` (Line 7550)
- **Function:** `trigger_cold_storage_migration(self)` (Line 291)
- **Function:** `mark_reimbursed(self, method, reference, user)` (Line 628)
- **Function:** `approve_by_pm(self, approver)` (Line 1405)
- **Function:** `reject_by_pm(self, approver, reason)` (Line 1419)
- **Function:** `sign_document(self, signer, ip_address, signature_canvas_data, user_agent, geolocation)` (Line 2025)
- **Function:** `detect_missing_days(self)` (Line 2353)
- **Function:** `calculate_project_breakdown(self)` (Line 2373)
- **Function:** `calculate_net_payable(self)` (Line 2757)
- **Function:** `mark_for_admin_review(self, user)` (Line 2764)
- **Function:** `fully_paid(self)` (Line 2794)
- **Function:** `task_completion_summary(self)` (Line 3297)
- **Function:** `is_active_choice(self)` (Line 4333)
- **Function:** `can_annotate(self, user)` (Line 4336)
- **Function:** `generate_sample_number(self)` (Line 4478)
- **Function:** `add_client_comment(self, user, comment)` (Line 4729)
- **Function:** `update_average_cost(self, new_cost, quantity_purchased)` (Line 5457)
- **Function:** `check_reorder_point(self)` (Line 5556)
- **Function:** `bulk_transfer(cls, project, category_list, exclude_leftover)` (Line 5628)
- **Function:** `create_prep_template(cls, name, creator)` (Line 5982)
- **Function:** `create_paint_template(cls, name, creator)` (Line 6006)
- **Function:** `create_cleanup_template(cls, name, creator)` (Line 6030)
- **Function:** `auto_consume_materials(self, consumption_data, user)` (Line 6333)
- **Function:** `plannedactivity_set(self)` (Line 6387)
- **Function:** `overall_score(self)` (Line 7416)
- **Function:** `file_count(self)` (Line 7670)
- **Function:** `total_size(self)` (Line 7674)
- **Function:** `dfs(node)` (Line 1530)

### `core/notifications.py`

- **Function:** `notify_task_completed(task, completer)` (Line 44)
- **Function:** `notify_chat_message(channel, sender, message_text)` (Line 128)

### `core/notifications_push.py`

- **Class:** `class PushNotificationService` (Line 14)
- **Function:** `notify_invoice_approved(invoice)` (Line 104)
- **Function:** `notify_changeorder_created(change_order)` (Line 119)
- **Function:** `notify_changeorder_approved(change_order)` (Line 139)
- **Function:** `notify_material_request(material_request)` (Line 154)
- **Function:** `notify_material_received(material_request)` (Line 175)
- **Function:** `notify_touchup_completed(task)` (Line 205)
- **Function:** `notify_project_budget_alert(project)` (Line 220)
- **Function:** `notify_daily_plan_created(daily_plan)` (Line 245)
- **Function:** `notify_payroll_ready(employee, payroll_entry)` (Line 269)
- **Function:** `send_notification(user_ids, heading, content, url, data)` (Line 20)
- **Function:** `send_to_all(heading, content, url, segments)` (Line 66)

### `core/security_decorators.py`

- **Function:** `require_role()` (Line 18)
- **Function:** `ajax_login_required(view_func)` (Line 55)
- **Function:** `ajax_csrf_protect(view_func)` (Line 69)
- **Function:** `require_project_access(param_name)` (Line 87)
- **Function:** `rate_limit(key_prefix, max_requests, window_seconds)` (Line 146)
- **Function:** `sanitize_json_input(view_func)` (Line 194)
- **Function:** `require_post_with_csrf(view_func)` (Line 230)
- **Function:** `is_staffish(user)` (Line 247)
- **Function:** `sanitize_value(value)` (Line 210)

### `core/services/activation_service.py`

- **Function:** `validate_estimate(self)` (Line 46)
- **Function:** `create_schedule_from_estimate(self, start_date, items_to_schedule, selected_line_ids)` (Line 62)
- **Function:** `create_budget_from_estimate(self)` (Line 138)
- **Function:** `create_tasks_from_schedule(self, schedule_items, assigned_to)` (Line 171)
- **Function:** `create_deposit_invoice(self, deposit_percent, due_date)` (Line 217)

### `core/services/calendar_sync.py`

- **Function:** `generate_google_calendar_link(project)` (Line 81)

### `core/services/earned_value.py`

- **Function:** `line_planned_percent(line, as_of)` (Line 9)

### `core/services/financial_service.py`

- **Class:** `class CashFlowProjectionRow` (Line 74)
- **Function:** `net(self)` (Line 80)

### `core/services/payroll_tax.py`

- **Function:** `preview_tiered(profile, gross)` (Line 17)

### `core/services/planning_service.py`

- **Function:** `calculate_activity_priority(days_remaining, percent_complete, is_milestone)` (Line 96)

### `core/services/signature.py`

- **Class:** `class SignatureTokenPayload` (Line 22)
- **Function:** `generate_signature_token(changeorder_id, expires_in_days)` (Line 34)
- **Function:** `validate_signature_token(token, max_age_days)` (Line 44)
- **Function:** `to_dict(self)` (Line 30)

### `core/services/weather.py`

- **Class:** `class WeatherProvider` (Line 16)
- **Class:** `class MockWeatherProvider` (Line 42)
- **Class:** `class OpenWeatherMapProvider` (Line 59)
- **Function:** `__new__(cls)` (Line 140)
- **Function:** `set_provider(self, provider)` (Line 155)
- **Function:** `configure_for_production(cls)` (Line 267)
- **Function:** `configure_for_testing(cls)` (Line 278)

### `core/services/weather_service.py`

- **Class:** `class WeatherData` (Line 14)
- **Function:** `serialize(self, data)` (Line 45)

### `core/signals.py`

- **Function:** `task_capture_old_status(sender, instance)` (Line 20)
- **Function:** `task_post_save(sender, instance, created)` (Line 32)
- **Function:** `task_image_versioning(sender, instance, created)` (Line 54)
- **Function:** `track_task_changes(sender, instance)` (Line 97)
- **Function:** `create_task_status_change(sender, instance, created)` (Line 137)
- **Function:** `send_task_status_notification(task, old_status, new_status)` (Line 188)
- **Function:** `handle_task_image_versioning(sender, instance, created)` (Line 239)
- **Function:** `handle_user_logged_in(sender, request, user)` (Line 278)
- **Function:** `handle_user_logged_out(sender, request, user)` (Line 296)

### `core/signature_utils.py`

- **Function:** `bulk_verify_signatures(queryset)` (Line 117)
- **Function:** `export_signature_proof(entity, format)` (Line 172)

### `core/tasks.py`

- **Function:** `check_overdue_invoices()` (Line 93)
- **Function:** `alert_incomplete_daily_plans()` (Line 137)
- **Function:** `generate_weekly_payroll()` (Line 180)
- **Function:** `alert_high_priority_touchups()` (Line 410)
- **Function:** `update_daily_weather_snapshots_legacy()` (Line 483)
- **Function:** `send_pending_notifications()` (Line 570)
- **Function:** `update_invoice_statuses()` (Line 611)
- **Function:** `cleanup_old_notifications()` (Line 634)
- **Function:** `generate_daily_plan_reminders()` (Line 652)
- **Function:** `update_daily_plans_weather()` (Line 688)

### `core/templatetags/core_extras.py`

- **Function:** `mul(value, arg)` (Line 12)
- **Function:** `filter_by_status(queryset, status)` (Line 21)
- **Function:** `filter_by_id(queryset, obj_id)` (Line 31)
- **Function:** `abs_value(value)` (Line 40)
- **Function:** `sum_attr(queryset, attr_name)` (Line 49)
- **Function:** `getattribute(obj, attr_name)` (Line 72)

### `core/templatetags/currency_extras.py`

- **Function:** `currency_es(value, places)` (Line 8)

### `core/views.py`

- **Function:** `client_request_create(request, project_id)` (Line 113)
- **Function:** `client_requests_list(request, project_id)` (Line 130)
- **Function:** `client_request_convert_to_co(request, request_id)` (Line 143)
- **Function:** `dashboard_admin(request)` (Line 329)
- **Function:** `dashboard_client(request)` (Line 473)
- **Function:** `master_schedule_center(request)` (Line 614)
- **Function:** `focus_wizard(request)` (Line 630)
- **Function:** `dashboard_view(request)` (Line 648)
- **Function:** `project_pdf_view(request, project_id)` (Line 692)
- **Function:** `schedule_create_view(request)` (Line 731)
- **Function:** `expense_create_view(request)` (Line 748)
- **Function:** `income_create_view(request)` (Line 766)
- **Function:** `income_list(request)` (Line 784)
- **Function:** `income_edit_view(request, income_id)` (Line 799)
- **Function:** `income_delete_view(request, income_id)` (Line 820)
- **Function:** `expense_list(request)` (Line 837)
- **Function:** `expense_edit_view(request, expense_id)` (Line 852)
- **Function:** `expense_delete_view(request, expense_id)` (Line 873)
- **Function:** `timeentry_create_view(request)` (Line 890)
- **Function:** `timeentry_edit_view(request, entry_id)` (Line 911)
- **Function:** `timeentry_delete_view(request, entry_id)` (Line 938)
- **Function:** `payroll_weekly_review(request)` (Line 968)
- **Function:** `payroll_record_payment(request, record_id)` (Line 1116)
- **Function:** `payroll_payment_history(request, employee_id)` (Line 1164)
- **Function:** `client_project_view(request, project_id)` (Line 1202)
- **Function:** `color_sample_list(request, project_id)` (Line 1301)
- **Function:** `color_sample_create(request, project_id)` (Line 1327)
- **Function:** `color_sample_detail(request, sample_id)` (Line 1356)
- **Function:** `color_sample_review(request, sample_id)` (Line 1372)
- **Function:** `color_sample_quick_action(request, sample_id)` (Line 1419)
- **Function:** `color_sample_edit(request, sample_id)` (Line 1461)
- **Function:** `color_sample_delete(request, sample_id)` (Line 1493)
- **Function:** `floor_plan_list(request, project_id)` (Line 1521)
- **Function:** `floor_plan_create(request, project_id)` (Line 1555)
- **Function:** `floor_plan_detail(request, plan_id)` (Line 1583)
- **Function:** `floor_plan_edit(request, plan_id)` (Line 1636)
- **Function:** `floor_plan_delete(request, plan_id)` (Line 1665)
- **Function:** `pin_detail_ajax(request, pin_id)` (Line 1689)
- **Function:** `floor_plan_add_pin(request, plan_id)` (Line 1726)
- **Function:** `agregar_tarea(request, project_id)` (Line 1800)
- **Function:** `touchup_quick_update(request, task_id)` (Line 1940)
- **Function:** `damage_report_list(request, project_id)` (Line 1978)
- **Function:** `damage_report_detail(request, report_id)` (Line 2027)
- **Function:** `damage_report_edit(request, report_id)` (Line 2042)
- **Function:** `damage_report_delete(request, report_id)` (Line 2079)
- **Function:** `damage_report_add_photos(request, report_id)` (Line 2110)
- **Function:** `damage_report_update_status(request, report_id)` (Line 2140)
- **Function:** `design_chat(request, project_id)` (Line 2169)
- **Function:** `project_chat_index(request, project_id)` (Line 2222)
- **Function:** `project_chat_room(request, project_id, channel_id)` (Line 2229)
- **Function:** `agregar_comentario(request, project_id)` (Line 2277)
- **Function:** `changeorder_detail_view(request, changeorder_id)` (Line 2315)
- **Function:** `changeorder_billing_history_view(request, changeorder_id)` (Line 2331)
- **Function:** `changeorder_customer_signature_view(request, changeorder_id, token)` (Line 2391)
- **Function:** `changeorder_create_view(request)` (Line 2540)
- **Function:** `changeorder_edit_view(request, co_id)` (Line 2579)
- **Function:** `changeorder_delete_view(request, co_id)` (Line 2620)
- **Function:** `photo_editor_standalone_view(request)` (Line 2630)
- **Function:** `changeorder_board_view(request)` (Line 2650)
- **Function:** `unassigned_timeentries_view(request)` (Line 2679)
- **Function:** `payroll_summary_view(request)` (Line 2779)
- **Function:** `invoice_builder_view(request, project_id)` (Line 2887)
- **Function:** `invoice_create_view(request)` (Line 3191)
- **Function:** `invoice_list(request)` (Line 3234)
- **Function:** `invoice_detail(request, pk)` (Line 3241)
- **Function:** `invoice_pdf(request, pk)` (Line 3247)
- **Function:** `invoice_edit(request, pk)` (Line 3266)
- **Function:** `changeorders_ajax(request)` (Line 3283)
- **Function:** `changeorder_lines_ajax(request)` (Line 3291)
- **Function:** `invoice_payment_dashboard(request)` (Line 3299)
- **Function:** `record_invoice_payment(request, invoice_id)` (Line 3323)
- **Function:** `invoice_mark_sent(request, invoice_id)` (Line 3371)
- **Function:** `invoice_mark_approved(request, invoice_id)` (Line 3389)
- **Function:** `project_profit_dashboard(request, project_id)` (Line 3405)
- **Function:** `costcode_list_view(request)` (Line 3508)
- **Function:** `budget_lines_view(request, project_id)` (Line 3518)
- **Function:** `estimate_create_view(request, project_id)` (Line 3531)
- **Function:** `estimate_detail_view(request, estimate_id)` (Line 3554)
- **Function:** `estimate_send_email(request, estimate_id)` (Line 3576)
- **Function:** `daily_log_view(request, project_id)` (Line 3689)
- **Function:** `project_activation_view(request, project_id)` (Line 3755)
- **Function:** `daily_log_detail(request, log_id)` (Line 3877)
- **Function:** `daily_log_create(request, project_id)` (Line 3922)
- **Function:** `rfi_list_view(request, project_id)` (Line 3990)
- **Function:** `rfi_answer_view(request, rfi_id)` (Line 4005)
- **Function:** `rfi_edit_view(request, rfi_id)` (Line 4018)
- **Function:** `rfi_delete_view(request, rfi_id)` (Line 4039)
- **Function:** `issue_list_view(request, project_id)` (Line 4057)
- **Function:** `issue_edit_view(request, issue_id)` (Line 4070)
- **Function:** `issue_delete_view(request, issue_id)` (Line 4091)
- **Function:** `risk_list_view(request, project_id)` (Line 4109)
- **Function:** `risk_edit_view(request, risk_id)` (Line 4122)
- **Function:** `risk_delete_view(request, risk_id)` (Line 4143)
- **Function:** `root_redirect(request)` (Line 4161)
- **Function:** `project_ev_view(request, project_id)` (Line 4184)
- **Function:** `project_ev_series(request, project_id)` (Line 4306)
- **Function:** `project_ev_csv(request, project_id)` (Line 4333)
- **Function:** `budget_line_plan_view(request, line_id)` (Line 4368)
- **Function:** `project_list(request)` (Line 4378)
- **Function:** `download_progress_sample(request, project_id)` (Line 4393)
- **Function:** `staff_required(view_func)` (Line 4469)
- **Function:** `upload_project_progress(request, project_id)` (Line 4485)
- **Function:** `edit_progress(request, project_id, pk)` (Line 4596)
- **Function:** `project_progress_csv(request, project_id)` (Line 4625)
- **Function:** `dashboard_employee(request)` (Line 4673)
- **Function:** `dashboard_pm(request)` (Line 4788)
- **Function:** `pm_select_project(request, action)` (Line 4898)
- **Function:** `set_language_view(request, code)` (Line 4940)
- **Function:** `project_overview(request, project_id)` (Line 4961)
- **Function:** `materials_request_view(request, project_id)` (Line 5108)
- **Function:** `pickup_view(request, project_id)` (Line 5297)
- **Function:** `task_list_view(request, project_id)` (Line 5303)
- **Function:** `task_detail(request, task_id)` (Line 5383)
- **Function:** `task_edit_view(request, task_id)` (Line 5390)
- **Function:** `task_delete_view(request, task_id)` (Line 5409)
- **Function:** `task_list_all(request)` (Line 5423)
- **Function:** `task_start_tracking(request, task_id)` (Line 5435)
- **Function:** `task_stop_tracking(request, task_id)` (Line 5466)
- **Function:** `daily_plan_fetch_weather(request, plan_id)` (Line 5498)
- **Function:** `daily_plan_convert_activities(request, plan_id)` (Line 5524)
- **Function:** `daily_plan_productivity(request, plan_id)` (Line 5556)
- **Function:** `project_schedule_view(request, project_id)` (Line 5575)
- **Function:** `site_photo_list(request, project_id)` (Line 5591)
- **Function:** `site_photo_create(request, project_id)` (Line 5600)
- **Function:** `inventory_view(request, project_id)` (Line 5624)
- **Function:** `inventory_move_view(request, project_id)` (Line 5647)
- **Function:** `inventory_history_view(request, project_id)` (Line 5725)
- **Function:** `materials_receive_ticket_view(request, request_id)` (Line 5758)
- **Function:** `materials_direct_purchase_view(request, project_id)` (Line 5870)
- **Function:** `materials_requests_list_view(request, project_id)` (Line 5980)
- **Function:** `materials_mark_ordered_view(request, request_id)` (Line 6016)
- **Function:** `materials_request_detail_view(request, request_id)` (Line 6031)
- **Function:** `materials_request_submit(request, request_id)` (Line 6058)
- **Function:** `materials_request_approve(request, request_id)` (Line 6078)
- **Function:** `materials_request_reject(request, request_id)` (Line 6093)
- **Function:** `materials_receive_partial(request, request_id)` (Line 6109)
- **Function:** `materials_create_expense(request, request_id)` (Line 6154)
- **Function:** `inventory_low_stock_alert(request)` (Line 6176)
- **Function:** `inventory_adjust(request, item_id, location_id)` (Line 6208)
- **Function:** `daily_plan_list(request)` (Line 6252)
- **Function:** `daily_plan_detail(request, plan_id)` (Line 6271)
- **Function:** `daily_planning_dashboard(request)` (Line 6298)
- **Function:** `daily_plan_create(request, project_id)` (Line 6365)
- **Function:** `daily_plan_edit(request, plan_id)` (Line 6485)
- **Function:** `daily_plan_delete_activity(request, activity_id)` (Line 6549)
- **Function:** `employee_morning_dashboard(request)` (Line 6567)
- **Function:** `activity_complete(request, activity_id)` (Line 6600)
- **Function:** `sop_library(request)` (Line 6674)
- **Function:** `sop_create_edit(request, template_id)` (Line 6729)
- **Function:** `project_minutes_list(request, project_id)` (Line 6776)
- **Function:** `project_minute_create(request, project_id)` (Line 6804)
- **Function:** `project_minute_detail(request, minute_id)` (Line 6854)
- **Function:** `dashboard_designer(request)` (Line 6873)
- **Function:** `dashboard_superintendent(request)` (Line 6917)
- **Function:** `schedule_generator_view(request, project_id)` (Line 6975)
- **Function:** `schedule_category_edit(request, category_id)` (Line 7130)
- **Function:** `schedule_category_delete(request, category_id)` (Line 7159)
- **Function:** `schedule_item_edit(request, item_id)` (Line 7184)
- **Function:** `schedule_item_delete(request, item_id)` (Line 7213)
- **Function:** `project_schedule_ics(request, project_id)` (Line 7238)
- **Function:** `project_schedule_google_calendar(request, project_id)` (Line 7257)
- **Function:** `schedule_gantt_react_view(request, project_id)` (Line 7276)
- **Function:** `changeorder_update_status(request, co_id)` (Line 7306)
- **Function:** `changeorder_send_to_client(request, co_id)` (Line 7350)
- **Function:** `project_files_view(request, project_id)` (Line 7395)
- **Function:** `file_category_create(request, project_id)` (Line 7461)
- **Function:** `file_upload(request, project_id, category_id)` (Line 7482)
- **Function:** `file_delete(request, file_id)` (Line 7506)
- **Function:** `file_download(request, file_id)` (Line 7529)
- **Function:** `file_edit_metadata(request, file_id)` (Line 7550)
- **Function:** `touchup_plans_list(request, project_id)` (Line 7583)
- **Function:** `touchup_plan_detail(request, plan_id)` (Line 7612)
- **Function:** `touchup_create(request, plan_id)` (Line 7649)
- **Function:** `touchup_detail_ajax(request, touchup_id)` (Line 7682)
- **Function:** `touchup_update(request, touchup_id)` (Line 7733)
- **Function:** `touchup_complete(request, touchup_id)` (Line 7757)
- **Function:** `touchup_delete(request, touchup_id)` (Line 7802)
- **Function:** `touchup_approve(request, touchup_id)` (Line 7824)
- **Function:** `touchup_reject(request, touchup_id)` (Line 7849)
- **Function:** `pin_info_ajax(request, pin_id)` (Line 7885)
- **Function:** `pin_update(request, pin_id)` (Line 7943)
- **Function:** `pin_add_photo(request, pin_id)` (Line 7982)
- **Function:** `pin_delete_photo(request, attachment_id)` (Line 8029)
- **Function:** `client_list(request)` (Line 8063)
- **Function:** `client_create(request)` (Line 8110)
- **Function:** `client_detail(request, user_id)` (Line 8175)
- **Function:** `client_edit(request, user_id)` (Line 8217)
- **Function:** `client_delete(request, user_id)` (Line 8248)
- **Function:** `client_reset_password(request, user_id)` (Line 8318)
- **Function:** `client_assign_project(request, user_id)` (Line 8360)
- **Function:** `project_create(request)` (Line 8419)
- **Function:** `project_edit(request, project_id)` (Line 8437)
- **Function:** `project_delete(request, project_id)` (Line 8457)
- **Function:** `project_status_toggle(request, project_id)` (Line 8528)
- **Function:** `js_i18n_demo(request)` (Line 8552)
- **Function:** `analytics_dashboard(request)` (Line 8562)
- **Function:** `touchup_board_react(request, project_id)` (Line 8586)
- **Function:** `color_approvals_react(request, project_id)` (Line 8604)
- **Function:** `pm_assignments_react(request)` (Line 8624)
- **Function:** `proposal_public_view(request, token)` (Line 8632)

### `core/views_admin.py`

- **Function:** `admin_required(view_func)` (Line 22)
- **Function:** `admin_users_list(request)` (Line 41)
- **Function:** `admin_user_detail(request, user_id)` (Line 93)
- **Function:** `admin_user_create(request)` (Line 152)
- **Function:** `admin_user_delete(request, user_id)` (Line 187)
- **Function:** `admin_groups_list(request)` (Line 209)
- **Function:** `admin_group_detail(request, group_id)` (Line 220)
- **Function:** `admin_group_create(request)` (Line 270)
- **Function:** `admin_model_list(request, model_name)` (Line 291)
- **Function:** `admin_activity_logs(request)` (Line 383)
- **Function:** `admin_dashboard_main(request)` (Line 415)
- **Function:** `admin_project_edit(request, project_id)` (Line 438)
- **Function:** `admin_project_create(request)` (Line 484)
- **Function:** `admin_project_delete(request, project_id)` (Line 545)
- **Function:** `admin_expense_edit(request, expense_id)` (Line 595)
- **Function:** `admin_expense_create(request)` (Line 658)
- **Function:** `admin_expense_delete(request, expense_id)` (Line 728)
- **Function:** `admin_income_edit(request, income_id)` (Line 754)
- **Function:** `admin_income_create(request)` (Line 822)
- **Function:** `admin_income_delete(request, income_id)` (Line 896)
- **Function:** `wrapper(request)` (Line 26)

### `core/views_financial.py`

- **Function:** `financial_dashboard(request)` (Line 27)
- **Function:** `invoice_aging_report(request)` (Line 203)
- **Function:** `productivity_dashboard(request)` (Line 267)
- **Function:** `export_financial_data(request)` (Line 369)
- **Function:** `employee_performance_review(request, employee_id)` (Line 486)

### `core/views_notifications.py`

- **Function:** `notifications_list(request)` (Line 14)
- **Function:** `notification_mark_read(request, notification_id)` (Line 38)
- **Function:** `notifications_mark_all_read(request)` (Line 46)

**Total Orphans:** 588

---

## 🔄 Candidates for Merging (Duplicates)

*Function pairs with >85% code similarity.*

### Group: `admin_update`

- **Similarity:** 100.0%
  - **Location 1:** `core/consumers_fixed.py:476` - `admin_update()`
  - **Location 2:** `core/consumers.py:477` - `admin_update()`

### Group: `chat_message`

- **Similarity:** 100.0%
  - **Location 1:** `core/consumers_fixed.py:124` - `chat_message()`
  - **Location 2:** `core/consumers.py:125` - `chat_message()`

### Group: `checklist_completed`

- **Similarity:** 100.0%
  - **Location 1:** `core/models.py:8128` - `checklist_completed(self)`
  - **Location 2:** `core/models/focus_workflow.py:221` - `checklist_completed(self)`

### Group: `checklist_progress`

- **Similarity:** 100.0%
  - **Location 1:** `core/models.py:8119` - `checklist_progress(self)`
  - **Location 2:** `core/models/focus_workflow.py:212` - `checklist_progress(self)`

### Group: `checklist_total`

- **Similarity:** 100.0%
  - **Location 1:** `core/models.py:8135` - `checklist_total(self)`
  - **Location 2:** `core/models/focus_workflow.py:228` - `checklist_total(self)`

### Group: `completed_power_actions`

- **Similarity:** 100.0%
  - **Location 1:** `core/models.py:8356` - `completed_power_actions(self)`
  - **Location 2:** `core/models/strategic_planning.py:197` - `completed_power_actions(self)`

### Group: `completed_tasks`

- **Similarity:** 100.0%
  - **Location 1:** `core/models.py:7961` - `completed_tasks(self)`
  - **Location 2:** `core/models/focus_workflow.py:58` - `completed_tasks(self)`

### Group: `dashboard_update`

- **Similarity:** 100.0%
  - **Location 1:** `core/consumers_fixed.py:427` - `dashboard_update()`
  - **Location 2:** `core/consumers.py:428` - `dashboard_update()`

### Group: `direct_message`

- **Similarity:** 100.0%
  - **Location 1:** `core/consumers_fixed.py:271` - `direct_message()`
  - **Location 2:** `core/consumers.py:272` - `direct_message()`

### Group: `duration_minutes`

- **Similarity:** 100.0%
  - **Location 1:** `core/models.py:8111` - `duration_minutes(self)`
  - **Location 2:** `core/models/strategic_planning.py:373` - `duration_minutes(self)`

- **Similarity:** 100.0%
  - **Location 1:** `core/models.py:8111` - `duration_minutes(self)`
  - **Location 2:** `core/models/focus_workflow.py:204` - `duration_minutes(self)`

- **Similarity:** 100.0%
  - **Location 1:** `core/models.py:8534` - `duration_minutes(self)`
  - **Location 2:** `core/models/strategic_planning.py:373` - `duration_minutes(self)`

- **Similarity:** 100.0%
  - **Location 1:** `core/models.py:8534` - `duration_minutes(self)`
  - **Location 2:** `core/models/focus_workflow.py:204` - `duration_minutes(self)`

- **Similarity:** 100.0%
  - **Location 1:** `core/models/strategic_planning.py:373` - `duration_minutes(self)`
  - **Location 2:** `core/models/focus_workflow.py:204` - `duration_minutes(self)`

### Group: `frog_action`

- **Similarity:** 100.0%
  - **Location 1:** `core/models.py:8366` - `frog_action(self)`
  - **Location 2:** `core/models/strategic_planning.py:207` - `frog_action(self)`

### Group: `frog_task`

- **Similarity:** 100.0%
  - **Location 1:** `core/models.py:7971` - `frog_task(self)`
  - **Location 2:** `core/models/focus_workflow.py:68` - `frog_task(self)`

### Group: `high_impact_actions`

- **Similarity:** 100.0%
  - **Location 1:** `core/models.py:8361` - `high_impact_actions(self)`
  - **Location 2:** `core/models/strategic_planning.py:202` - `high_impact_actions(self)`

### Group: `high_impact_tasks`

- **Similarity:** 100.0%
  - **Location 1:** `core/models.py:7966` - `high_impact_tasks(self)`
  - **Location 2:** `core/models/focus_workflow.py:63` - `high_impact_tasks(self)`

### Group: `inspection_update`

- **Similarity:** 100.0%
  - **Location 1:** `core/consumers_fixed.py:535` - `inspection_update()`
  - **Location 2:** `core/consumers.py:536` - `inspection_update()`

### Group: `is_completed`

- **Similarity:** 100.0%
  - **Location 1:** `core/models.py:8346` - `is_completed(self)`
  - **Location 2:** `core/models/strategic_planning.py:187` - `is_completed(self)`

### Group: `mark_completed`

- **Similarity:** 100.0%
  - **Location 1:** `core/models.py:8370` - `mark_completed(self)`
  - **Location 2:** `core/models/strategic_planning.py:211` - `mark_completed(self)`

### Group: `mark_message_read`

- **Similarity:** 100.0%
  - **Location 1:** `core/consumers_fixed.py:216` - `mark_message_read(self, message_id, user)`
  - **Location 2:** `core/consumers.py:217` - `mark_message_read(self, message_id, user)`

### Group: `mark_notification_read`

- **Similarity:** 100.0%
  - **Location 1:** `core/consumers_fixed.py:391` - `mark_notification_read(self, notification_id)`
  - **Location 2:** `core/consumers.py:392` - `mark_notification_read(self, notification_id)`

### Group: `micro_steps_completed`

- **Similarity:** 100.0%
  - **Location 1:** `core/models.py:8551` - `micro_steps_completed(self)`
  - **Location 2:** `core/models/strategic_planning.py:390` - `micro_steps_completed(self)`

### Group: `micro_steps_progress`

- **Similarity:** 100.0%
  - **Location 1:** `core/models.py:8542` - `micro_steps_progress(self)`
  - **Location 2:** `core/models/strategic_planning.py:381` - `micro_steps_progress(self)`

### Group: `micro_steps_total`

- **Similarity:** 100.0%
  - **Location 1:** `core/models.py:8558` - `micro_steps_total(self)`
  - **Location 2:** `core/models/strategic_planning.py:397` - `micro_steps_total(self)`

### Group: `notification`

- **Similarity:** 100.0%
  - **Location 1:** `core/consumers_fixed.py:366` - `notification()`
  - **Location 2:** `core/consumers.py:367` - `notification()`

### Group: `plan_update`

- **Similarity:** 100.0%
  - **Location 1:** `core/consumers_fixed.py:505` - `plan_update()`
  - **Location 2:** `core/consumers.py:506` - `plan_update()`

### Group: `read_receipt`

- **Similarity:** 100.0%
  - **Location 1:** `core/consumers_fixed.py:183` - `read_receipt()`
  - **Location 2:** `core/consumers.py:184` - `read_receipt()`

### Group: `total_power_actions`

- **Similarity:** 100.0%
  - **Location 1:** `core/models.py:8351` - `total_power_actions(self)`
  - **Location 2:** `core/models/strategic_planning.py:192` - `total_power_actions(self)`

### Group: `total_tasks`

- **Similarity:** 100.0%
  - **Location 1:** `core/models.py:7956` - `total_tasks(self)`
  - **Location 2:** `core/models/focus_workflow.py:53` - `total_tasks(self)`

### Group: `typing_indicator`

- **Similarity:** 100.0%
  - **Location 1:** `core/consumers_fixed.py:140` - `typing_indicator()`
  - **Location 2:** `core/consumers.py:141` - `typing_indicator()`

### Group: `user_joined`

- **Similarity:** 100.0%
  - **Location 1:** `core/consumers_fixed.py:155` - `user_joined()`
  - **Location 2:** `core/consumers.py:156` - `user_joined()`

### Group: `user_left`

- **Similarity:** 100.0%
  - **Location 1:** `core/consumers_fixed.py:169` - `user_left()`
  - **Location 2:** `core/consumers.py:170` - `user_left()`

**Total Duplicate Pairs:** 34

---

## 💡 Recommendations

### Orphan Functions

**Action Plan:**
1. Review each orphan to confirm it's truly unused
2. Check if it's a utility function that should be used
3. If confirmed unused, create a cleanup PR
4. Consider if removal breaks any external integrations

### Duplicate Functions

**Action Plan:**
1. Compare implementations to identify the better version
2. Extract common logic to a shared utility module
3. Update all call sites to use the consolidated function
4. Remove redundant implementations
5. Add unit tests to prevent future duplication

---

*This report is generated automatically. Manual review is recommended before taking action.*
