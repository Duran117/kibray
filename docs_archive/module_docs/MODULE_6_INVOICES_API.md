# Module 6: Invoices API

DRF-based API for creating and managing invoices with nested lines and payments.

## Models (existing)
- Invoice: `project, invoice_number, date_issued, due_date, status, total_amount`
- InvoiceLine: `invoice, description, quantity, unit_price, line_total`
- InvoicePayment: `invoice, amount, date, method, reference`

## Endpoints
Base path: `/api/v1/invoices/`

- GET `/` (list)
  - Filters (via `InvoiceFilter`): `project`, `status`, `date_issued_after/before`, `due_date_after/before`, `min_total`, `max_total`
  - Search: `invoice_number, project name/client`
  - Ordering: `-date_issued, -id` (default)
  - Response: list (unpaginated).

- POST `/` (create)
  - Body:
  ```json
  {
    "project": 1,
    "invoice_number": "INV-001",
    "date_issued": "2025-11-20",
    "due_date": "2025-12-05",
    "lines": [
      {"description": "Labor", "quantity": 10, "unit_price": 50},
      {"description": "Materials", "quantity": 1, "unit_price": 200}
    ]
  }
  ```
  - Computes `line_total`s and `total_amount` automatically.

- GET `/:id/` (detail)
- PATCH/PUT `/:id/` (update header or lines)
- DELETE `/:id/`

### Actions
- POST `/:id/mark_sent/`
  - Sets `status = SENT`, stores `sent_date` and `sent_by`.
- POST `/:id/mark_approved/`
  - Sets `status = APPROVED`, stores `approved_date`.
- POST `/:id/record_payment/`
  - Body:
  ```json
  { "amount": 300, "date": "2025-11-25", "method": "ach", "reference": "#123" }
  ```
  - Creates `InvoicePayment`, updates payment progress and `balance_due` (computed in serializer).

## Serializer outputs
- InvoiceSerializer
  - Includes nested `lines` and `payments`.
  - Computed fields: `payment_progress`, `balance_due`.

## Overdue Automation
- Task: `core.tasks.check_overdue_invoices`
  - Daily at 6 AM.
  - Marks invoices with `status in [SENT, VIEWED, APPROVED, PARTIAL]` and `due_date < today` as `OVERDUE`.

## Notes
- Pagination is disabled for the list endpoint to match current client/tests.
- Future: add webhooks or email delivery on mark_sent.
