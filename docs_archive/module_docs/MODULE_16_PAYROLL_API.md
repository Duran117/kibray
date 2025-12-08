# Module 16: Payroll API

New REST API for weekly payroll review, approval, and payments.

## Models exposed
- PayrollPeriod: Weekly period (week_start, week_end, status)
- PayrollRecord: Per-employee weekly record (hours, rates, gross/net/total)
- PayrollPayment: Partial/full payments recorded per record

## Routes
- GET/POST /api/v1/payroll/periods/
- GET/PATCH/DELETE /api/v1/payroll/periods/{id}/
- POST /api/v1/payroll/periods/{id}/validate/
- POST /api/v1/payroll/periods/{id}/approve/ (body: {"skip_validation": true|false})
- POST /api/v1/payroll/periods/{id}/generate_expenses/

- GET/POST /api/v1/payroll/records/
- GET/PATCH/DELETE /api/v1/payroll/records/{id}/
- POST /api/v1/payroll/records/{id}/manual_adjust/ (body: { reason, updates: { field: value, ... } })
- POST /api/v1/payroll/records/{id}/create_expense/

- GET/POST /api/v1/payroll/payments/
- GET/PATCH/DELETE /api/v1/payroll/payments/{id}/

## Filters
- Periods: status, week_start, week_end
- Records: period, employee, week_start, week_end, reviewed
- Payments: payroll_record, payment_date, payment_method

## Behaviors
- Approving a period runs validations (missing days, zero hours) unless skip_validation=true.
- manual_adjust records who adjusted, when, and holds a free-text reason.
- create_expense links an Expense for labor cost (requires at least one Project in the system; uses the first as fallback).
- Payments set recorded_by automatically; a warning is returned if overpayment is detected.

## Testing status
- End-to-end tests cover period creation/approval (skipping validation), record creation/adjustment, partial payment, balances, and expense linkage.
