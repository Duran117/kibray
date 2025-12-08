# Inventory Management System Guide

## Overview

Kibray's inventory system provides **multi-location stock tracking** with **FIFO/LIFO/AVG cost valuation**, automated low-stock alerts, and comprehensive audit trails. Supports both consumable materials (paint, tape) and reusable equipment (ladders, sprayers).

## Architecture

### Core Models

```
InventoryItem          - Master catalog (SKU, category, valuation method, thresholds)
InventoryLocation      - Storage locations (central warehouse, project sites)
ProjectInventory       - Stock levels per item per location
InventoryMovement      - Transaction log (receipts, transfers, usage, adjustments)
```

### Valuation Methods

1. **FIFO (First In First Out)**: Uses oldest purchase costs first
2. **LIFO (Last In First Out)**: Uses newest purchase costs first
3. **AVG (Weighted Average)**: Recalculates average cost on each purchase

## Workflows

### 1. Purchase & Receive

```
Purchase Order → Receive to Warehouse → Update Stock
```

**API Flow**:
```bash
# Create receive movement
POST /api/v1/inventory/movements/
{
  "item": <item_id>,
  "to_location": <warehouse_id>,
  "movement_type": "RECEIVE",
  "quantity": 50.00,
  "unit_cost": 12.50,
  "reason": "PO-2025-001 received"
}

# Movement auto-applies:
# - Increases warehouse stock by 50
# - Updates item average_cost (if valuation_method=AVG)
# - Tracks unit_cost for FIFO/LIFO calculation
```

### 2. Transfer to Project Site

```
Warehouse → Project Site Storage
```

**API Flow** (Bulk Transfer):
```bash
POST /api/v1/inventory/movements/bulk_transfer/
{
  "from_location": <warehouse_id>,
  "to_location": <site_id>,
  "items": [
    {"item_id": 15, "quantity": 20.00},
    {"item_id": 22, "quantity": 10.00}
  ],
  "reason": "Initial site setup"
}

# Response:
{
  "success": 2,
  "errors": [],
  "movements": [
    {"id": 301, "item": "Paint Gallon", "quantity": "20.00"},
    {"id": 302, "item": "Roller", "quantity": "10.00"}
  ]
}
```

**Validation**: Transfer fails if source location has insufficient stock (prevents negative inventory).

### 3. Consumption (Usage on Tasks)

```
Project Site Storage → Consumed by Task
```

**API Flow**:
```bash
POST /api/v1/inventory/movements/
{
  "item": <item_id>,
  "from_location": <site_id>,
  "movement_type": "CONSUME",
  "quantity": 5.00,
  "related_task": <task_id>,
  "related_project": <project_id>,
  "reason": "Used on Task #45: Bedroom walls"
}

# Links consumption to task for cost tracking
# Reduces site stock by 5 units
```

### 4. Return to Warehouse

```
Project Site → Return Unused → Warehouse
```

**API Flow**:
```bash
POST /api/v1/inventory/movements/
{
  "item": <item_id>,
  "from_location": <site_id>,
  "to_location": <warehouse_id>,
  "movement_type": "RETURN",
  "quantity": 8.00,
  "reason": "Project complete, unused material"
}
```

### 5. Stock Adjustment (Physical Count)

```
Physical Count → Adjust Discrepancies
```

**API Flow**:
```bash
POST /api/v1/inventory/movements/stock_adjustment/
{
  "location": <warehouse_id>,
  "item": <item_id>,
  "new_quantity": 47.00,
  "reason": "Physical count correction - found damage"
}

# Response:
{
  "movement_id": 305,
  "previous_quantity": "50.00",
  "new_quantity": "47.00",
  "adjustment": "-3.00"
}
```

## Cost Calculation

### Average Cost (AVG)

Automatically recalculates on each `RECEIVE`:

```python
# Example: Current stock 100 @ $10 avg, receive 50 @ $15
weighted_avg = (100 * 10 + 50 * 15) / (100 + 50)
            = (1000 + 750) / 150
            = $11.67
```

### FIFO Cost

Used when issuing stock:

```
Purchase History:
- Batch 1: 50 @ $10 (oldest)
- Batch 2: 30 @ $12
- Batch 3: 20 @ $15 (newest)

Issue 60 units:
Cost = (50 * $10) + (10 * $12) = $500 + $120 = $620
Average per unit = $620 / 60 = $10.33
```

### LIFO Cost

```
Same purchases, issue 60 units:
Cost = (20 * $15) + (30 * $12) + (10 * $10) = $300 + $360 + $100 = $760
Average per unit = $760 / 60 = $12.67
```

**API**: Get calculated cost for any quantity:
```python
item = InventoryItem.objects.get(pk=15)
total_cost = item.get_cost_for_quantity(Decimal('60'))
# Returns total based on valuation_method (FIFO/LIFO/AVG)
```

## Multi-Location Tracking

### Locations Structure

```
Central Warehouse (is_storage=True, project=null)
├─ Raw Materials
├─ Equipment Pool
└─ Returns Holding

Project A Site (project=Project A)
├─ On-Site Storage
└─ Active Use

Project B Site (project=Project B)
└─ Trailer Storage
```

### Stock Queries

**Total Across All Locations**:
```python
item.total_quantity_all_locations()  # Aggregates ProjectInventory records
```

**Per Location**:
```python
ProjectInventory.objects.filter(item=item, location=warehouse)
```

**Active Projects Only**:
```bash
GET /api/v1/inventory/stocks/?location__project__end_date__gte=2025-11-26
```

## Low-Stock Alerts

### Threshold Configuration

**Per-Item Threshold** (preferred):
```python
item.low_stock_threshold = Decimal('20')  # Alert when < 20 units
```

**Global Default** (fallback):
```python
item.default_threshold = Decimal('10')
```

**Disable Alerts**:
```python
item.no_threshold = True  # For non-critical items
```

### Alert Mechanism

**Automated Daily Check** (Celery Task at 8 AM):
```python
# core/tasks.py: check_inventory_shortages()
# Aggregates stock across all locations
# Sends notifications to admins if below threshold
```

**Manual Check**:
```bash
GET /api/v1/inventory/movements/low_stock_report/
?category=PINTURA&location=5

# Response:
{
  "count": 3,
  "items": [
    {
      "item_id": 15,
      "item_name": "Paint Gallon - White",
      "sku": "PNT-WHT-001",
      "category": "Pintura",
      "current_quantity": "12.00",
      "threshold": "20.00",
      "shortage": "8.00",
      "valuation_method": "AVG",
      "average_cost": "15.50"
    }
  ]
}
```

## API Endpoints

### Items
- `GET /api/v1/inventory/items/` - List items (filter: category, active, is_equipment)
- `POST /api/v1/inventory/items/` - Create item (specify SKU, valuation_method, threshold)
- `PATCH /api/v1/inventory/items/<id>/` - Update item

### Locations
- `GET /api/v1/inventory/locations/` - List locations (filter: project, is_storage)
- `POST /api/v1/inventory/locations/` - Create location

### Stock Levels
- `GET /api/v1/inventory/stocks/` - Current stock per location (read-only)
  - Filter: `?item=<id>&location=<id>&location__project=<id>`

### Movements
- `GET /api/v1/inventory/movements/` - Transaction history
  - Filter: `?item=<id>&movement_type=TRANSFER&related_project=<id>`
- `POST /api/v1/inventory/movements/` - Single movement
- `POST /api/v1/inventory/movements/bulk_transfer/` - Multi-item transfer
- `POST /api/v1/inventory/movements/stock_adjustment/` - Adjust after physical count
- `GET /api/v1/inventory/movements/low_stock_report/` - Low stock summary

## Audit Trail

Every movement tracks:
- `created_by` - User who initiated movement
- `created_at` - Timestamp
- `reason` - Required explanation for adjustments
- `related_task` - Link to task if consumption
- `related_project` - Link to project
- `expense` - Link to purchase expense (if applicable)

**Query Movement History**:
```bash
# All movements for item in last 30 days
GET /api/v1/inventory/movements/
?item=15&created_at__gte=2025-10-27

# All movements for project
GET /api/v1/inventory/movements/
?related_project=5
```

## Equipment vs Consumables

### Consumables (track_serial=False)
- Aggregated quantities (e.g., "50 gallons paint")
- FIFO/LIFO/AVG valuation

### Equipment (is_equipment=True, track_serial=True)
- Individual serial numbers
- Reusable (transferred, not consumed)
- Transfer workflow:
  ```
  Warehouse → Project A → Project B → Warehouse
  ```

**Track Serial**:
```python
ladder = InventoryItem.objects.create(
    name='Extension Ladder 24ft',
    category='ESCALERA',
    is_equipment=True,
    track_serial=True
)

# Future: EquipmentSerial model for individual unit tracking
```

## Integration Points

### Link to Tasks
```python
movement.related_task = Task.objects.get(pk=45)
# Enables task-level material cost rollup
```

### Link to Expenses
```python
# When receiving purchase:
expense = Expense.objects.create(
    project=project,
    category='MATERIALES',
    amount=total_cost,
    ...
)
movement.expense = expense
# Connects inventory receipt to financial record
```

### Link to Material Requests
```python
# MaterialRequest.receive_materials() creates movements
# Automatically applies stock and updates request status
```

## Testing

Run inventory tests:
```bash
pytest tests/test_inventory_core.py -v

# Test coverage:
# - AVG cost calculation
# - FIFO/LIFO cost methods
# - Multi-location transfers
# - Negative inventory prevention
# - Stock adjustments
# - Low-stock detection
# - Valuation method accuracy
```

## Production Considerations

### Performance
- **Indexes**: Item name, SKU, category, location, movement_type, created_at
- **Caching**: Consider Redis cache for `total_quantity_all_locations()` (invalidate on movement)
- **Pagination**: Large movement history (1000s of records) → use cursor pagination

### Concurrency
- **Race condition**: Two simultaneous transfers from same location
  - Solution: Database row-level locking or optimistic concurrency (version field)
- **Double-apply prevention**: `applied=True` flag ensures idempotency

### Data Integrity
- **Negative prevention**: Enforced at `movement.apply()` level
- **Orphan stock**: Periodic audit task to reconcile `ProjectInventory` with movement sum
- **Cost accuracy**: FIFO/LIFO rely on `created_at` ordering; ensure server time sync

## Future Enhancements

### Phase 8+
- **Barcode scanning**: Mobile app integration (QR codes on bins)
- **Automated reordering**: Trigger PO when item hits reorder point
- **Batch/lot tracking**: Track paint batches for quality issues
- **Serial number management**: Individual asset tracking for equipment
- **Cost center allocation**: Allocate inventory costs to specific cost codes
- **Advanced analytics**: Material usage trends, cost variance analysis

### Redis Caching Example

```python
# Cache low-stock report (TTL: 1 hour)
from django.core.cache import cache

def get_low_stock_items():
    cache_key = 'inventory:low_stock'
    items = cache.get(cache_key)
    
    if items is None:
        items = # compute from DB
        cache.set(cache_key, items, 3600)
    
    return items

# Invalidate on movement
def on_movement_applied(movement):
    cache.delete('inventory:low_stock')
```

## Summary

✅ **Multi-location tracking**: Warehouse, project sites, transfers
✅ **Cost valuation**: FIFO, LIFO, Weighted Average
✅ **Automated alerts**: Daily low-stock notifications (Celery)
✅ **Negative prevention**: Enforced at transaction level
✅ **Audit trail**: Full history with user, reason, task linkage
✅ **Bulk operations**: Transfer multiple items in single API call
✅ **Flexible thresholds**: Per-item or global defaults
✅ **Equipment tracking**: Reusable assets with serial numbers (extensible)

Inventory system is production-ready with comprehensive tests, API docs, and integration hooks for financial/task modules.
