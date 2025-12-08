# Module 14: Materials & Inventory API

This module introduces a complete materials request workflow and inventory management API.

## Endpoints

- Material Requests
  - GET/POST/PUT/PATCH/DELETE /api/v1/material-requests/
  - Actions:
    - POST /api/v1/material-requests/{id}/submit/ → draft → pending
    - POST /api/v1/material-requests/{id}/approve/ → pending → approved (staff only)
    - POST /api/v1/material-requests/{id}/mark_ordered/ → approved/pending → ordered
    - POST /api/v1/material-requests/{id}/receive/ {"items": [{"id": <item_id>, "received_quantity": <qty>}, ...]}
      - Creates inventory movements (RECEIVE) to the project location
      - Updates request status: partially_received or fulfilled
    - POST /api/v1/material-requests/{id}/direct_purchase_expense/ {"total_amount": 123.45}
      - Creates Expense, receives all items, marks request fulfilled

- Material Catalog
  - /api/v1/material-catalog/ (project-scoped or global by setting project=null)

- Inventory
  - Items: /api/v1/inventory/items/ (unique SKU enforced)
  - Locations: /api/v1/inventory/locations/
  - Stocks (read-only): /api/v1/inventory/stocks/
  - Movements: /api/v1/inventory/movements/ (auto-applied on create; prevents negative issues)

## Serializers

- InventoryItemSerializer, InventoryLocationSerializer, ProjectInventorySerializer (read-only quantity), InventoryMovementSerializer (applies on create).
- MaterialRequestSerializer with nested MaterialRequestItemSerializer, supporting create/update with items.
- MaterialCatalogSerializer.

## Notes & Constraints

- Negative inventory is blocked by validations on movement.apply().
- Costs: InventoryItem.average_cost auto-updates on RECEIVE with unit_cost if valuation_method is AVG.
- Default project location is created lazily when receiving materials.
- Notifications are emitted by model methods (e.g., partial/complete receipt), reused from existing Notification system.

## Tests

Added tests under tests/test_module14_materials_api.py:
- SKU uniqueness via API
- Material Request full flow: submit → approve → order → partial + full receive
- Direct purchase expense integration (creates Expense and inventory)
- Catalog CRUD smoke and filtering
- Negative inventory prevention on ISSUE

## How to run (optional)

- Run full suite: pytest -q
- Run only Module 14 tests: pytest -q tests/test_module14_materials_api.py

