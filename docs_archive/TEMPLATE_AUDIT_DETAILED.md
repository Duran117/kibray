# Template Audit Detailed Report

Generated: Auto

## Summary
- Total templates: 215
- Templates with issues: 17
- Potentially unused: 2

## Issues Found

### client_list.html
  ⚠️ Suspicious href: '?page=1{% if search_query %}&search={{ search_query }}{% endif %}{% if status_filter %}&status={{ status_filter }}{% endif %}'
  ⚠️ Suspicious href: '?page={{ page_obj.previous_page_number }}{% if search_query %}&search={{ search_query }}{% endif %}{% if status_filter %}&status={{ status_filter }}{% endif %}'
  ⚠️ Suspicious href: '?page={{ page_obj.next_page_number }}{% if search_query %}&search={{ search_query }}{% endif %}{% if status_filter %}&status={{ status_filter }}{% endif %}'
  ⚠️ Suspicious href: '?page={{ page_obj.paginator.num_pages }}{% if search_query %}&search={{ search_query }}{% endif %}{% if status_filter %}&status={{ status_filter }}{% endif %}'

### damage_report_list.html
  ⚠️ Suspicious href: '?'
  ⚠️ Suspicious href: '?status=open'
  ⚠️ Suspicious href: '?status=in_progress'
  ⚠️ Suspicious href: '?status=resolved'
  ⚠️ Suspicious href: '?severity=low'
  ⚠️ Suspicious href: '?severity=medium'
  ⚠️ Suspicious href: '?severity=high'
  ⚠️ Suspicious href: '?severity=critical'

### dashboard_pm_clean.html
  ⚠️ Suspicious href: '?filter=problems'
  ⚠️ Suspicious href: '?filter=approvals'
  ⚠️ Suspicious href: '?'

### documents_workspace.html
  ⚠️ Suspicious href: '?tag={{ tag.id }}{% if selected_category_id %}&category={{ selected_category_id }}{% endif %}'

### employee_performance_list.html
  ⚠️ Suspicious href: '?year={{ y }}'

### materials_requests_list.html
  ⚠️ Suspicious href: '?status='
  ⚠️ Suspicious href: '?status=draft'
  ⚠️ Suspicious href: '?status=submitted'
  ⚠️ Suspicious href: '?status=approved'

### materials_requests_list_modern.html
  ⚠️ Suspicious href: '?status='
  ⚠️ Suspicious href: '?status=pending'
  ⚠️ Suspicious href: '?status=submitted'
  ⚠️ Suspicious href: '?status=approved'
  ⚠️ Suspicious href: '?status=ordered'

### notifications_list.html
  ⚠️ Suspicious href: '?'
  ⚠️ Suspicious href: '?read=false'
  ⚠️ Suspicious href: '?read=true'
  ⚠️ Suspicious href: '?page={{ notifications.previous_page_number }}{% if filter_read %}&read={{ filter_read }}{% endif %}'
  ⚠️ Suspicious href: '?page={{ notifications.next_page_number }}{% if filter_read %}&read={{ filter_read }}{% endif %}'

### organization_list.html
  ⚠️ Suspicious href: '?page={{ page_obj.previous_page_number }}&search={{ search_query }}&status={{ status_filter }}'
  ⚠️ Suspicious href: '?page={{ page_obj.next_page_number }}&search={{ search_query }}&status={{ status_filter }}'

### payroll_weekly_review.html
  ⚠️ Suspicious href: '?week_start={{ prev_week|date:'
  ⚠️ Suspicious href: '?week_start={{ next_week|date:'

### project_ev.html
  ⚠️ Suspicious href: '?as_of={{ as_of|date:'
  ⚠️ Suspicious href: '?as_of={{ as_of|date:'

### site_photo_list.html
  ⚠️ Suspicious href: '?type='
  ⚠️ Suspicious href: '?type=before'
  ⚠️ Suspicious href: '?type=progress'
  ⚠️ Suspicious href: '?type=after'
  ⚠️ Suspicious href: '?type=defect'
  ⚠️ Suspicious href: '?type=reference'

### timeentry_assignment_hub.html
  ⚠️ Suspicious href: '?filter=all'
  ⚠️ Suspicious href: '?filter=unassigned'
  ⚠️ Suspicious href: '?filter=no_project'
  ⚠️ Suspicious href: '?filter=no_budget_line'

### touchup_board_clean.html
  ⚠️ Suspicious href: '?page=1'
  ⚠️ Suspicious href: '?page={{ page_obj.previous_page_number }}'
  ⚠️ Suspicious href: '?page={{ page_obj.next_page_number }}'
  ⚠️ Suspicious href: '?page={{ page_obj.paginator.num_pages }}'

### unassigned_hours_hub.html
  ⚠️ Suspicious href: '?week={{ prev_week }}&employee={{ employee_filter }}'
  ⚠️ Suspicious href: '?week={{ next_week }}&employee={{ employee_filter }}'
  ⚠️ Suspicious href: '?week={{ week_start|date:'
  ⚠️ Suspicious href: '?week={{ week_start|date:'

### unassigned_timeentries.html
  ⚠️ Suspicious href: '?'
  ⚠️ Suspicious href: '?show_all=1'
  ⚠️ Suspicious href: '?page={{ page_obj.previous_page_number }}'
  ⚠️ Suspicious href: '?page={{ page_obj.next_page_number }}'

### wizards/user_list.html
  ⚠️ Suspicious href: '?page={{ users.previous_page_number }}'
  ⚠️ Suspicious href: '?page={{ users.next_page_number }}'

## Potentially Unused Templates

- components/button.html
- login.html
