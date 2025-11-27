# Reports App

Minimal isolated app for server-side report generation and rendering.

## Model
- `ReportTemplate`: Configures report metadata (name, slug, JSON config).

## Services
- `render_project_cost_summary(project)`: Returns CSV-formatted cost summary (income, expense, profit).

## API
Base path: `/api/v1/reports/`
- `GET /project-cost-summary/{project_id}/` returns CSV report (requires auth)

## Extending
1. Add new render functions in `services.py` (e.g., `render_labor_breakdown`, `render_gantt_export`)
2. Optionally store templates in `ReportTemplate` model with JSON config for dynamic parameters
3. Wire new endpoints in `kibray_backend/urls.py`

## Tests
See `tests/test_reports_api.py`.
