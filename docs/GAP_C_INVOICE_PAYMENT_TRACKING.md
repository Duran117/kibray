# Gap C: Invoice Payment Tracking & Accounts Receivable - Implementation Complete

## Overview
Gap C enhances the invoicing system with comprehensive payment tracking, status workflow management, partial payments support, and accounts receivable monitoring. This enables accurate cash flow tracking and automated income record creation.

**Status**: ✅ COMPLETE (Backend + API Layer)  
**Migration**: `0037_invoice_amount_paid_invoice_approved_date_and_more.py` - Applied successfully  
**Test Coverage**: 5 passing tests (1 backend + 4 API)

---

## Business Problem Solved

### Before Gap C:
- ❌ Invoices were binary: "paid" or "not paid" (no partial payment tracking)
- ❌ No status workflow (draft → sent → approved → paid)
- ❌ Multiple payments on same invoice not tracked individually  
- ❌ No timestamp tracking for when invoice was sent, viewed, approved, or paid
- ❌ Manual tracking of who sent the invoice
- ❌ No automatic aging reports (overdue detection)
- ❌ Income records created manually or only on full payment

### After Gap C:
- ✅ Full payment tracking with partial payments support
- ✅ 8-state status workflow with automatic transitions
- ✅ Individual payment records linked to income
- ✅ Complete audit trail (sent_date, sent_by, approved_date, paid_date, viewed_date)
- ✅ Automatic overdue detection
- ✅ Real-time balance_due calculation
- ✅ Automatic Income creation on each payment
- ✅ Payment progress percentage tracking

---

## Data Model Changes

### Enhanced Invoice Model

#### New Fields:

**Status Tracking:**
- `status`: CharField with 8 choices (see below)
- `sent_date`: DateTimeField - When invoice was sent to client
- `sent_by`: ForeignKey to User - Who sent the invoice
- `viewed_date`: DateTimeField - When client viewed invoice (future: client portal)
- `approved_date`: DateTimeField - When client approved invoice
- `paid_date`: DateTimeField - When invoice was fully paid

**Payment Tracking:**
- `amount_paid`: DecimalField - Total amount paid so far (default=0)
- `balance_due`: Property - Calculated as `total_amount - amount_paid` (never negative)
- `payment_progress`: Property - Percentage paid `(amount_paid / total_amount) * 100`
- `fully_paid`: Property - Boolean, true when `amount_paid >= total_amount`

**Legacy Compatibility:**
- `is_paid`: BooleanField - DEPRECATED, kept for old reports, synced from `fully_paid`

#### Status Workflow:

```python
STATUS_CHOICES = [
    ("DRAFT", "Borrador"),              # Initial state, not sent
    ("SENT", "Enviada"),                # Sent to client
    ("VIEWED", "Vista por Cliente"),    # Client opened invoice (future)
    ("APPROVED", "Aprobada"),           # Client approved invoice
    ("PARTIAL", "Pago Parcial"),        # Partially paid (0 < amount_paid < total_amount)
    ("PAID", "Pagada Completa"),        # Fully paid (amount_paid >= total_amount)
    ("OVERDUE", "Vencida"),             # Past due_date with balance > 0
    ("CANCELLED", "Cancelada"),         # Cancelled invoice
]
```

#### New Methods:

**`Invoice._sync_payment_flags()`**
- Internal method to sync `is_paid` legacy field with `fully_paid` property
- Sets `paid_date` timestamp when transitioning to paid
- Updates `status` to PAID or PARTIAL based on `amount_paid`

**`Invoice.update_status()`**
- Auto-updates status based on payment amount and dates
- Checks for overdue condition (past `due_date` with `balance > 0`)
- Returns new status
- Called automatically after save and after InvoicePayment creation

**`Invoice.save()` Override:**
- Auto-generates unique `invoice_number` using project code or client initials
- Calls `_sync_payment_flags()` before saving
- Creates Income record when transitioning from unpaid to fully paid (legacy behavior)

### New Model: InvoicePayment

Tracks individual payments against invoices, enabling partial payments and payment history.

**Fields:**
- `invoice`: ForeignKey → Invoice (related_name='payments')
- `amount`: DecimalField - Payment amount
- `payment_date`: DateField - When payment was received
- `payment_method`: CharField - CHECK/CASH/TRANSFER/CARD/OTHER
- `reference`: CharField - Check #, Transfer ID, confirmation code, etc.
- `notes`: TextField - Additional payment notes
- `recorded_by`: ForeignKey → User - Who recorded the payment
- `recorded_at`: DateTimeField (auto_now_add=True)
- `income`: OneToOneField → Income - Auto-created income record

**Automatic Behaviors:**

On `InvoicePayment.save()`:
1. **Updates Invoice.amount_paid**: Adds payment amount to running total
2. **Calls Invoice.update_status()**: Triggers status transition (SENT → PARTIAL → PAID)
3. **Creates Income record**: Automatically generates Income with:
   - `project`: Same as invoice
   - `amount`: Payment amount
   - `date`: Payment date
   - `payment_method`: From payment
   - `category`: "PAYMENT"
   - `description`: "Pago de $X para factura INV-XXX. Ref: XXX"
4. **Links Income**: Sets `self.income` to created record

**Meta Options:**
- `ordering`: ['-payment_date', '-recorded_at']
- `verbose_name`: "Invoice Payment"

---

## Payment Workflow

### Typical Invoice Lifecycle:

```
1. CREATE INVOICE (status=DRAFT)
   └─> Invoice.objects.create(project=..., total_amount=1000)
   
2. SEND TO CLIENT (status=SENT)
   └─> POST /api/v1/invoices/{id}/mark_sent/
   └─> Sets: sent_date, sent_by, status=SENT
   
3. CLIENT APPROVES (status=APPROVED)
   └─> POST /api/v1/invoices/{id}/mark_approved/
   └─> Sets: approved_date, status=APPROVED
   
4. RECORD PARTIAL PAYMENT (status=PARTIAL)
   └─> POST /api/v1/invoices/{id}/record_payment/
       {amount: 400, payment_date: "2025-12-01", method: "CHECK", reference: "CHK-1001"}
   └─> Creates InvoicePayment(amount=400)
   └─> Updates Invoice.amount_paid = 400
   └─> Status → PARTIAL (400 < 1000)
   └─> Creates Income(amount=400)
   └─> Balance due = 600
   
5. RECORD FINAL PAYMENT (status=PAID)
   └─> POST /api/v1/invoices/{id}/record_payment/
       {amount: 600, payment_date: "2025-12-15", method: "TRANSFER"}
   └─> Creates InvoicePayment(amount=600)
   └─> Updates Invoice.amount_paid = 1000
   └─> Status → PAID (1000 >= 1000)
   └─> Sets paid_date timestamp
   └─> Creates Income(amount=600)
   └─> Balance due = 0
```

### Overdue Detection:

Automatic overdue status if:
- `due_date < today`
- `balance_due > 0`
- `status NOT IN [DRAFT, CANCELLED, PAID]`

Called by `Invoice.update_status()` which runs:
- After `Invoice.save()`
- After `InvoicePayment.save()`

---

## API Endpoints

### Invoice Endpoints

#### 1. Create Invoice
**Endpoint:** `POST /api/v1/invoices/`  
**Permission:** IsAuthenticated

**Request:**
```json
{
  "project": 1,
  "due_date": "2025-12-15",
  "notes": "Primera factura",
  "lines": [
    {"description": "Avance general", "amount": "1200.00"},
    {"description": "Change Order CO-004", "amount": "300.50"}
  ]
}
```

**Response (201 Created):**
```json
{
  "id": 1,
  "invoice_number": "ACME-0001-001",
  "status": "DRAFT",
  "total_amount": "1500.50",
  "amount_paid": "0.00",
  "balance_due": "1500.50",
  "payment_progress": 0.0,
  "project": 1,
  "date_issued": "2025-11-28",
  "due_date": "2025-12-15",
  "sent_date": null,
  "approved_date": null,
  "paid_date": null,
  "lines": [
    {
      "id": 1,
      "description": "Avance general",
      "amount": "1200.00"
    },
    {
      "id": 2,
      "description": "Change Order CO-004",
      "amount": "300.50"
    }
  ]
}
```

#### 2. Mark Invoice as Sent
**Endpoint:** `POST /api/v1/invoices/{id}/mark_sent/`  
**Permission:** IsAuthenticated  
**Description:** Marks invoice as sent to client

**Request:** (empty body)

**Response (200 OK):**
```json
{
  "id": 1,
  "status": "SENT",
  "sent_date": "2025-11-28T14:30:00Z",
  "sent_by": 1,
  "message": "Invoice marked as sent"
}
```

#### 3. Mark Invoice as Approved
**Endpoint:** `POST /api/v1/invoices/{id}/mark_approved/`  
**Permission:** IsAuthenticated  
**Description:** Marks invoice as approved by client

**Request (optional):**
```json
{
  "approved_by_client": "John Smith - ACME Corp"
}
```

**Response (200 OK):**
```json
{
  "id": 1,
  "status": "APPROVED",
  "approved_date": "2025-12-01T10:15:00Z",
  "message": "Invoice marked as approved"
}
```

#### 4. Record Payment
**Endpoint:** `POST /api/v1/invoices/{id}/record_payment/`  
**Permission:** IsAuthenticated  
**Description:** Records a payment (partial or full) against invoice

**Request:**
```json
{
  "amount": "400.00",
  "payment_date": "2025-12-01",
  "payment_method": "CHECK",
  "reference": "CHK-1001",
  "notes": "Check received from client"
}
```

**Response (201 Created):**
```json
{
  "id": 1,
  "invoice": 1,
  "amount": "400.00",
  "payment_date": "2025-12-01",
  "payment_method": "CHECK",
  "reference": "CHK-1001",
  "notes": "Check received from client",
  "recorded_by": 1,
  "recorded_at": "2025-12-01T16:30:00Z",
  "income": 15,
  "invoice_status": "PARTIAL",
  "invoice_amount_paid": "400.00",
  "invoice_balance_due": "1100.50"
}
```

#### 5. Get Payment History
**Endpoint:** `GET /api/v1/invoices/{id}/payment_history/`  
**Permission:** IsAuthenticated  
**Description:** Retrieves all payments for an invoice

**Response (200 OK):**
```json
{
  "invoice_id": 1,
  "invoice_number": "ACME-0001-001",
  "total_amount": "1500.50",
  "amount_paid": "900.00",
  "balance_due": "600.50",
  "payments": [
    {
      "id": 2,
      "amount": "500.00",
      "payment_date": "2025-12-05",
      "payment_method": "TRANSFER",
      "reference": "TRX-2002",
      "recorded_by": "admin",
      "recorded_at": "2025-12-05T09:00:00Z"
    },
    {
      "id": 1,
      "amount": "400.00",
      "payment_date": "2025-12-01",
      "payment_method": "CHECK",
      "reference": "CHK-1001",
      "recorded_by": "admin",
      "recorded_at": "2025-12-01T16:30:00Z"
    }
  ]
}
```

#### 6. Filter Invoices
**Endpoint:** `GET /api/v1/invoices/?status=OVERDUE&project=5`  
**Permission:** IsAuthenticated  
**Description:** List invoices with filters

**Query Parameters:**
- `status`: Filter by status (DRAFT/SENT/APPROVED/PARTIAL/PAID/OVERDUE/CANCELLED)
- `project`: Filter by project ID
- `is_paid`: Filter by payment status (true/false) - legacy
- `ordering`: Sort by field (e.g., `-due_date`, `amount_paid`)

**Response (200 OK):**
```json
[
  {
    "id": 3,
    "invoice_number": "ACME-0001-003",
    "status": "OVERDUE",
    "total_amount": "2500.00",
    "amount_paid": "0.00",
    "balance_due": "2500.00",
    "due_date": "2025-11-15",
    "days_overdue": 13,
    "project": {
      "id": 5,
      "name": "Villa Moderna"
    }
  }
]
```

---

## Usage Examples

### Example 1: Create Invoice and Track Payments

```python
from core.models import Invoice, InvoicePayment, Project
from decimal import Decimal
from datetime import date

# Create invoice
project = Project.objects.get(id=1)
invoice = Invoice.objects.create(
    project=project,
    total_amount=Decimal("1500.00"),
    due_date=date(2025, 12, 31),
    notes="Factura por avance de obra"
)

# Invoice starts as DRAFT
assert invoice.status == "DRAFT"
assert invoice.amount_paid == Decimal("0")
assert invoice.balance_due == Decimal("1500.00")

# Mark as sent
invoice.status = "SENT"
invoice.sent_date = timezone.now()
invoice.sent_by = request.user
invoice.save()

# Record partial payment
payment1 = InvoicePayment.objects.create(
    invoice=invoice,
    amount=Decimal("600.00"),
    payment_date=date(2025, 12, 10),
    payment_method="CHECK",
    reference="CHK-5001",
    recorded_by=request.user
)

# Check updated invoice
invoice.refresh_from_db()
assert invoice.status == "PARTIAL"
assert invoice.amount_paid == Decimal("600.00")
assert invoice.balance_due == Decimal("900.00")
assert invoice.payment_progress == 40.0

# Verify Income created
assert payment1.income is not None
assert payment1.income.amount == Decimal("600.00")

# Record final payment
payment2 = InvoicePayment.objects.create(
    invoice=invoice,
    amount=Decimal("900.00"),
    payment_date=date(2025, 12, 20),
    payment_method="TRANSFER",
    reference="TRX-9876",
    recorded_by=request.user
)

# Check fully paid
invoice.refresh_from_db()
assert invoice.status == "PAID"
assert invoice.fully_paid is True
assert invoice.amount_paid == Decimal("1500.00")
assert invoice.balance_due == Decimal("0")
assert invoice.paid_date is not None
```

### Example 2: Overdue Detection

```python
from django.utils import timezone
from datetime import timedelta

# Create overdue invoice
invoice = Invoice.objects.create(
    project=project,
    total_amount=Decimal("1000.00"),
    due_date=timezone.now().date() - timedelta(days=15),  # 15 days ago
    status="SENT"
)

# Manually trigger status update
invoice.update_status()

# Check overdue
assert invoice.status == "OVERDUE"

# Pay invoice - status should change from OVERDUE to PAID
payment = InvoicePayment.objects.create(
    invoice=invoice,
    amount=Decimal("1000.00"),
    payment_date=timezone.now().date(),
    payment_method="CASH",
    recorded_by=user
)

invoice.refresh_from_db()
assert invoice.status == "PAID"
assert invoice.balance_due == Decimal("0")
```

### Example 3: Overpayment Handling

```python
# Create invoice for $500
invoice = Invoice.objects.create(
    project=project,
    total_amount=Decimal("500.00")
)

# Client pays $600 (overpayment)
payment = InvoicePayment.objects.create(
    invoice=invoice,
    amount=Decimal("600.00"),
    payment_date=date.today(),
    payment_method="TRANSFER",
    recorded_by=user
)

invoice.refresh_from_db()
assert invoice.amount_paid == Decimal("600.00")
assert invoice.balance_due == Decimal("0")  # Never negative
assert invoice.payment_progress == 120.0  # Can exceed 100%
assert invoice.status == "PAID"
```

### Example 4: Query Overdue Invoices (Accounts Receivable Aging)

```python
from datetime import date, timedelta

# Get all overdue invoices
overdue = Invoice.objects.filter(
    status="OVERDUE",
    balance_due__gt=0
).order_by('due_date')

# Aging report: 0-30, 31-60, 61-90, 90+ days
today = date.today()
aging = {
    '0-30': [],
    '31-60': [],
    '61-90': [],
    '90+': []
}

for invoice in overdue:
    days = (today - invoice.due_date).days
    if days <= 30:
        aging['0-30'].append(invoice)
    elif days <= 60:
        aging['31-60'].append(invoice)
    elif days <= 90:
        aging['61-90'].append(invoice)
    else:
        aging['90+'].append(invoice)

# Calculate totals
totals = {
    category: sum(inv.balance_due for inv in invoices)
    for category, invoices in aging.items()
}
```

---

## Test Coverage

### Backend Test (`tests/test_invoice_payment_unification.py`) - 1/1 PASSING ✅

**`test_invoice_payment_unification`**
- Creates invoice with `total_amount=$500`
- Verifies initial state: `amount_paid=0`, `is_paid=False`, `fully_paid=False`
- Sets `amount_paid=$200`: verifies `status=PARTIAL`, `balance_due=$300`
- Sets `amount_paid=$500`: verifies `status=PAID`, `fully_paid=True`, `balance_due=$0`
- Tests overpayment: sets `amount_paid=$600`, verifies `balance_due=$0` (not negative)

### API Tests (`tests/test_module6_invoices_api.py`) - 4/4 PASSING ✅

1. **`test_create_invoice_with_lines_and_totals`**
   - POST `/api/v1/invoices/` with project and 2 lines
   - Verifies `status=DRAFT`, `total_amount=$1500.50`
   - Verifies `invoice_number` auto-generated
   - GET invoice detail includes lines

2. **`test_mark_sent_and_approved`**
   - Creates invoice
   - POST `/api/v1/invoices/{id}/mark_sent/`: verifies `status=SENT`, `sent_date` set
   - POST `/api/v1/invoices/{id}/mark_approved/`: verifies `status=APPROVED`, `approved_date` set

3. **`test_record_payment_partial_and_paid`**
   - Creates invoice for $800
   - POST payment $300 (CHECK): verifies `status=PARTIAL`, `amount_paid=$300`
   - POST payment $500 (TRANSFER): verifies `status=PAID`, `amount_paid=$800`

4. **`test_filter_invoices_by_project_and_status`**
   - Creates 2 invoices with different statuses
   - GET `/api/v1/invoices/?project={id}`: verifies filtering by project
   - GET `/api/v1/invoices/?status=SENT`: verifies filtering by status

---

## Properties & Computed Fields

### Invoice Properties

**`balance_due`**
- Calculated as `total_amount - amount_paid`
- Never negative (returns 0 if overpaid)
- Used in status updates and UI

**`payment_progress`**
- Percentage: `(amount_paid / total_amount) * 100`
- Can exceed 100% if overpaid
- Used for progress bars and dashboards

**`fully_paid`**
- Boolean: `amount_paid >= total_amount`
- Replaces legacy `is_paid` field
- Used in status logic

**`days_overdue`** (Future Enhancement)
```python
@property
def days_overdue(self):
    if self.due_date and self.balance_due > 0:
        return max(0, (timezone.now().date() - self.due_date).days)
    return 0
```

---

## Legacy Compatibility

### Deprecated Fields

**`Invoice.is_paid`** (BooleanField)
- **Status:** DEPRECATED
- **Reason:** Replaced by `fully_paid` property and `amount_paid` tracking
- **Behavior:** Auto-synced from `fully_paid` via `_sync_payment_flags()`
- **Migration Plan:** 
  - ⚠️ Keep until all reports updated to use `amount_paid` and `status`
  - Will be removed in future migration (post-2026)
  - Documentation updated to discourage use

**`Invoice.income`** (OneToOneField)
- **Status:** Legacy behavior maintained
- **Original:** Created only when `is_paid` became True
- **Current:** Created on first payment via InvoicePayment
- **Future:** May be deprecated as InvoicePayment.income provides better granularity

---

## Migration Details

**File:** `core/migrations/0037_invoice_amount_paid_invoice_approved_date_and_more.py`  
**Status:** ✅ Applied  
**Date:** November 8, 2025

**Operations:**
1. AddField: Invoice.amount_paid (default=0)
2. AddField: Invoice.approved_date (null=True)
3. AddField: Invoice.paid_date (null=True)
4. AddField: Invoice.sent_by (FK to User)
5. AddField: Invoice.sent_date (null=True)
6. AddField: Invoice.status (default='DRAFT')
7. AddField: Invoice.viewed_date (null=True)
8. CreateModel: InvoicePayment (with all fields)

**Backward Compatibility:**
- All new fields nullable or have defaults
- Legacy `is_paid` field maintained
- Existing invoices start with `status=DRAFT`, `amount_paid=0`
- No data migration needed (manual status updates post-migration)

---

## Future Enhancements (Gap D+)

### 1. Client Portal Invoice Viewing
- Track `viewed_date` when client opens invoice link
- Transition SENT → VIEWED automatically
- Email notifications with secure invoice links

### 2. Automated Dunning (Overdue Reminders)
- Scheduled task to send overdue reminders
- Escalation levels: 7 days, 14 days, 30 days overdue
- Email templates with payment links

### 3. Bulk Payment Import
- Upload CSV/Excel of payments
- Auto-match by invoice_number
- Batch reconciliation

### 4. Payment Plans
- Allow installment payments with schedule
- Auto-generate payment reminders
- Track payment plan compliance

### 5. Accounts Receivable Dashboard
- Aging report widget (0-30, 31-60, 61-90, 90+)
- Total AR amount
- Average days to payment
- Payment trend charts
- Client payment history

### 6. Credit Memo Support
- Negative InvoicePayment for refunds
- Adjust Invoice.amount_paid downward
- Link to original payment

### 7. Late Payment Penalties
- Auto-calculate interest on overdue balance
- Add penalty as separate invoice line
- Configure penalty percentage in settings

---

## Security Considerations

1. **Payment Recording Permissions**
   - Only authenticated users can record payments
   - Consider role-based permission: `can_record_payment`
   - Audit trail via `recorded_by` field

2. **Payment Deletion**
   - No delete method on InvoicePayment (by design)
   - Prevents data manipulation
   - Use credit memos for corrections

3. **Income Record Integrity**
   - OneToOne link prevents duplicate incomes per payment
   - Auto-creation ensures accounting consistency
   - Manual income editing should be restricted

4. **Status Transitions**
   - Only allow valid transitions (DRAFT → SENT → APPROVED → PARTIAL → PAID)
   - Consider state machine validation
   - Log all status changes

---

## Troubleshooting

### Issue: Invoice status not updating after payment

**Solution:**
```python
# Manually trigger status update
invoice.update_status()
```

### Issue: InvoicePayment not creating Income

**Solution:** Income is auto-created on `save()`. If missing:
```python
from core.models import Income

# Manually create income
income = Income.objects.create(
    project=payment.invoice.project,
    amount=payment.amount,
    date=payment.payment_date,
    payment_method=payment.payment_method,
    category="PAYMENT",
    description=f"Pago factura {payment.invoice.invoice_number}"
)
payment.income = income
payment.save(update_fields=['income'])
```

### Issue: balance_due showing negative

**Solution:** `balance_due` property prevents negatives. If seeing negative, check:
```python
# Check raw values
print(invoice.total_amount, invoice.amount_paid)

# Recalculate
print(invoice.balance_due)  # Property handles max(0, ...)
```

---

## API Rate Limiting & Best Practices

1. **Batch Payment Recording**
   - For multiple payments, record one at a time
   - Each creates Income and updates Invoice
   - Consider background task for bulk imports

2. **Concurrent Payment Recording**
   - InvoicePayment.save() uses `amount_paid += amount`
   - Potential race condition if simultaneous payments
   - Use database transactions or locks for bulk operations

3. **Status Query Performance**
   - Index on `status` field (already included in migration)
   - Use `select_related('project')` for list views
   - Cache overdue queries with 1-hour expiry

---

## Gap C Completion Checklist

- [x] Invoice status workflow with 8 states
- [x] Invoice payment tracking fields (amount_paid, sent_date, etc.)
- [x] InvoicePayment model for individual payments
- [x] Automatic Invoice.amount_paid updates on payment
- [x] Automatic Income creation per payment
- [x] Invoice.update_status() method with overdue detection
- [x] Legacy field sync (_sync_payment_flags)
- [x] Migration 0037 created and applied
- [x] Backend test (1/1 passing)
- [x] API tests (4/4 passing)
- [x] API endpoints: mark_sent, mark_approved, record_payment
- [x] Balance due and payment progress properties
- [x] Documentation (this file)

**Status:** ✅ **GAP C COMPLETE**

---

## Support

For questions or issues related to Gap C implementation:
- Review this documentation
- Check test cases in `tests/test_invoice_payment_unification.py` and `tests/test_module6_invoices_api.py`
- Examine model code in `core/models.py` (Invoice and InvoicePayment)
- Inspect migration `core/migrations/0037_invoice_amount_paid_invoice_approved_date_and_more.py`
- Check API views in `core/api/views.py` (InvoiceViewSet)

---

**Gap C Implementation Complete - November 28, 2025**
