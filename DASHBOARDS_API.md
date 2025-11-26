# Dashboards API (Phase 7 Initial)

Base path prefix: `/api/v1/dashboards/`

## Admin Dashboard
GET `/api/v1/dashboards/admin/`

Company wide aggregates:
- projects: active, completed, total
- employees: active, total
- financial: income, expenses, net_profit, profit_margin, invoices (total_invoiced, total_paid, outstanding, overdue_count, collection_rate)
- inventory: total_items
- recent_activity: latest mixed project/task/invoice/log items (max 10)
- health_score: weighted (profit + collection)

## Project Dashboard
GET `/api/v1/dashboards/projects/{project_id}/`

Keys:
- project: id, name, client, budget_total, budget_remaining
- tasks: total, pending, in_progress, completed, touchups_open
- damage_reports: open, in_progress, resolved
- color_samples: proposed, review, approved, rejected
- photos: count
- schedule: avg_progress_percent (avg of schedule item percent_complete)
- labor: hours_logged, estimated_labor_cost (sum entry.labor_cost)
- financial: income, expenses, profit, profit_margin_percent
- weather: cached_days (WeatherSnapshot count)
- recent_activity: last tasks/damages/colors (up to 7 combined)

## Client Dashboard
GET `/api/v1/dashboards/client/`

Per project (client has access via `ClientProjectAccess`):
- id, name, budget_remaining, touchups_open, color_review (count status=review), damages_open
Totals block: projects_count, pending_color_reviews, pending_touchups.

## Notes
- Authentication: JWT required.
- All numeric currency fields are Decimal serialized as string by DRF.
- No caching yet (Redis planned for Automation phase).
- Extendable: Add EVM summary and risk indicators (future module).
