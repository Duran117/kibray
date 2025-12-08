# API de Finanzas - Documentación

**Fecha**: 15 de Noviembre, 2025  
**Versión**: 1.0  
**Base URL**: `http://localhost:8000/api/v1/`

---

## 📋 Resumen

Se han implementado los endpoints RESTful para el módulo financiero del sistema Kibray, incluyendo:

- **Projects** - Gestión de proyectos con datos financieros
- **Incomes** - Registro de ingresos
- **Expenses** - Registro de gastos
- **Cost Codes** - Códigos de costo para categorización
- **Budget Lines** - Líneas presupuestarias detalladas

Todos los endpoints soportan:
- ✅ Filtrado avanzado
- ✅ Búsqueda de texto
- ✅ Ordenamiento
- ✅ Paginación
- ✅ Autenticación JWT

---

## 🔐 Autenticación

Todos los endpoints requieren autenticación JWT.

### Obtener Token
```http
POST /api/v1/auth/login/
Content-Type: application/json

{
  "username": "tu_usuario",
  "password": "tu_contraseña"
}
```

**Respuesta**:
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

### Usar Token
```http
GET /api/v1/projects/
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

---

## 📁 Endpoints de Proyectos

### 1. Listar Proyectos
```http
GET /api/v1/projects/
```

**Query Parameters**:
- `name` - Buscar por nombre (case-insensitive)
- `client` - Buscar por cliente (case-insensitive)
- `start_date__gte` - Proyectos que inician después de esta fecha
- `start_date__lte` - Proyectos que inician antes de esta fecha
- `is_active` - Solo proyectos activos (true/false)
- `ordering` - Ordenar por: `name`, `client`, `start_date`, `end_date`, `created_at`, `total_income`, `total_expenses`
- `search` - Búsqueda en nombre, cliente, dirección
- `page` - Número de página
- `page_size` - Tamaño de página (default: 10)

**Ejemplo**:
```http
GET /api/v1/projects/?is_active=true&ordering=-total_income&page=1
```

**Respuesta**:
```json
{
  "count": 25,
  "next": "http://localhost:8000/api/v1/projects/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "name": "Casa Residencial Smith",
      "client": "John Smith",
      "address": "123 Main St",
      "start_date": "2025-01-15",
      "end_date": null,
      "created_at": "2025-01-10T10:30:00Z"
    }
  ]
}
```

### 2. Obtener Proyecto (Detallado)
```http
GET /api/v1/projects/{id}/
```

**Respuesta**:
```json
{
  "id": 1,
  "name": "Casa Residencial Smith",
  "client": "John Smith",
  "address": "123 Main St",
  "start_date": "2025-01-15",
  "end_date": null,
  "description": "Pintura interior y exterior",
  "paint_colors": "SW 7008 Alabaster, SW 6258 Tricorn Black",
  "paint_codes": "",
  "stains_or_finishes": "Milesi Butternut 072 - 2 coats",
  "number_of_rooms_or_areas": 8,
  "number_of_paint_defects": 5,
  "total_income": "25000.00",
  "total_expenses": "18500.00",
  "profit": "6500.00",
  "budget_total": "22000.00",
  "budget_labor": "12000.00",
  "budget_materials": "8000.00",
  "budget_other": "2000.00",
  "budget_remaining": "3500.00",
  "reflection_notes": "Completado a tiempo",
  "created_at": "2025-01-10T10:30:00Z",
  "income_count": 3,
  "expense_count": 12
}
```

### 3. Crear Proyecto
```http
POST /api/v1/projects/
Content-Type: application/json

{
  "name": "Casa Nueva",
  "client": "Jane Doe",
  "address": "456 Oak Ave",
  "start_date": "2025-02-01",
  "budget_total": "30000.00",
  "budget_labor": "15000.00",
  "budget_materials": "12000.00",
  "budget_other": "3000.00"
}
```

### 4. Actualizar Proyecto
```http
PUT /api/v1/projects/{id}/
PATCH /api/v1/projects/{id}/
Content-Type: application/json

{
  "end_date": "2025-03-15",
  "reflection_notes": "Proyecto completado exitosamente"
}
```

### 5. Eliminar Proyecto
```http
DELETE /api/v1/projects/{id}/
```

### 6. Resumen Financiero del Proyecto
```http
GET /api/v1/projects/{id}/financial_summary/
```

**Respuesta**:
```json
{
  "project_id": 1,
  "project_name": "Casa Residencial Smith",
  "total_income": "25000.00",
  "total_expenses": "18500.00",
  "profit": "6500.00",
  "budget_total": "22000.00",
  "budget_remaining": "3500.00",
  "percent_spent": 84.09,
  "is_over_budget": false,
  "expense_by_category": [
    {"category": "MATERIALES", "total": "8500.00"},
    {"category": "MANO_OBRA", "total": "7000.00"},
    {"category": "COMIDA", "total": "2000.00"},
    {"category": "OTRO", "total": "1000.00"}
  ],
  "income_by_method": [
    {"payment_method": "TRANSFERENCIA", "total": "15000.00"},
    {"payment_method": "CHEQUE", "total": "10000.00"}
  ]
}
```

### 7. Vista General de Presupuestos
```http
GET /api/v1/projects/budget_overview/
```

**Respuesta**:
```json
[
  {
    "project_id": 1,
    "project_name": "Casa Residencial Smith",
    "budget_total": "22000.00",
    "budget_labor": "12000.00",
    "budget_materials": "8000.00",
    "budget_other": "2000.00",
    "total_expenses": "18500.00",
    "budget_remaining": "3500.00",
    "percent_spent": 84.09,
    "is_over_budget": false
  }
]
```

---

## 💰 Endpoints de Ingresos

### 1. Listar Ingresos
```http
GET /api/v1/incomes/
```

**Query Parameters**:
- `project` - Filtrar por ID de proyecto
- `date__gte` - Ingresos después de esta fecha
- `date__lte` - Ingresos antes de esta fecha
- `payment_method` - Filtrar por método de pago
- `amount__gte` - Monto mínimo
- `amount__lte` - Monto máximo
- `ordering` - Ordenar por: `date`, `amount`, `payment_method`
- `search` - Buscar en project_name, description, notes

**Ejemplo**:
```http
GET /api/v1/incomes/?project=1&date__gte=2025-01-01&ordering=-amount
```

**Respuesta**:
```json
{
  "count": 3,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "project": 1,
      "project_name": "Casa Residencial Smith",
      "project_client": "John Smith",
      "project_name": "Pago inicial",
      "amount": "10000.00",
      "date": "2025-01-20",
      "payment_method": "TRANSFERENCIA",
      "category": "Inicial",
      "description": "Primer pago del proyecto",
      "invoice": null,
      "notes": ""
    }
  ]
}
```

### 2. Crear Ingreso
```http
POST /api/v1/incomes/
Content-Type: application/json

{
  "project": 1,
  "project_name": "Pago final",
  "amount": "5000.00",
  "date": "2025-02-15",
  "payment_method": "CHEQUE",
  "description": "Pago final del proyecto"
}
```

**Validaciones**:
- `amount` debe ser mayor que 0
- `date` no puede ser en el futuro

### 3. Actualizar Ingreso
```http
PUT /api/v1/incomes/{id}/
PATCH /api/v1/incomes/{id}/
```

### 4. Eliminar Ingreso
```http
DELETE /api/v1/incomes/{id}/
```

**Nota**: Al crear, actualizar o eliminar un ingreso, se actualiza automáticamente el `total_income` del proyecto.

### 5. Resumen de Ingresos
```http
GET /api/v1/incomes/summary/
```

**Respuesta**:
```json
{
  "total_income": "25000.00",
  "income_by_method": [
    {"payment_method": "TRANSFERENCIA", "total": "15000.00"},
    {"payment_method": "CHEQUE", "total": "10000.00"}
  ],
  "income_by_project": [
    {"project__name": "Casa Residencial Smith", "total": "25000.00"}
  ],
  "count": 3
}
```

---

## 💸 Endpoints de Gastos

### 1. Listar Gastos
```http
GET /api/v1/expenses/
```

**Query Parameters**:
- `project` - Filtrar por ID de proyecto
- `category` - Filtrar por categoría
- `cost_code` - Filtrar por ID de código de costo
- `date__gte` - Gastos después de esta fecha
- `date__lte` - Gastos antes de esta fecha
- `amount__gte` - Monto mínimo
- `amount__lte` - Monto máximo
- `ordering` - Ordenar por: `date`, `amount`, `category`
- `search` - Buscar en project_name, description

**Ejemplo**:
```http
GET /api/v1/expenses/?project=1&category=MATERIALES&ordering=-date
```

**Respuesta**:
```json
{
  "count": 12,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "project": 1,
      "project_name": "Casa Residencial Smith",
      "amount": "1500.00",
      "project_name": "Pintura premium",
      "date": "2025-01-18",
      "category": "MATERIALES",
      "description": "Compra de pintura SW",
      "receipt": "/media/expenses/receipts/receipt_001.pdf",
      "invoice": null,
      "change_order": null,
      "change_order_number": null,
      "cost_code": 5,
      "cost_code_name": "Material - Paint"
    }
  ]
}
```

### 2. Crear Gasto
```http
POST /api/v1/expenses/
Content-Type: multipart/form-data

project: 1
project_name: Compra de materiales
amount: 1200.00
date: 2025-01-25
category: MATERIALES
description: Brochas y rodillos
receipt: [archivo]
```

**Validaciones**:
- `amount` debe ser mayor que 0
- `date` no puede ser en el futuro

### 3. Actualizar Gasto
```http
PUT /api/v1/expenses/{id}/
PATCH /api/v1/expenses/{id}/
```

### 4. Eliminar Gasto
```http
DELETE /api/v1/expenses/{id}/
```

**Nota**: Al crear, actualizar o eliminar un gasto, se actualiza automáticamente el `total_expenses` del proyecto.

### 5. Resumen de Gastos
```http
GET /api/v1/expenses/summary/
```

**Respuesta**:
```json
{
  "total_expenses": "18500.00",
  "expense_by_category": [
    {"category": "MATERIALES", "total": "8500.00"},
    {"category": "MANO_OBRA", "total": "7000.00"},
    {"category": "COMIDA", "total": "2000.00"},
    {"category": "OTRO", "total": "1000.00"}
  ],
  "expense_by_project": [
    {"project__name": "Casa Residencial Smith", "total": "18500.00"}
  ],
  "expense_by_cost_code": [
    {"cost_code__code": "01-PAINT", "cost_code__name": "Material - Paint", "total": "8500.00"}
  ],
  "count": 12
}
```

---

## 🏷️ Endpoints de Códigos de Costo

### 1. Listar Códigos de Costo
```http
GET /api/v1/cost-codes/
```

**Query Parameters**:
- `active` - Solo códigos activos (true/false)
- `category` - Filtrar por categoría (labor, material, equipment)
- `search` - Buscar en code, name, category
- `ordering` - Ordenar por: `code`, `name`, `category`

**Ejemplo**:
```http
GET /api/v1/cost-codes/?active=true&category=material&ordering=code
```

**Respuesta**:
```json
[
  {
    "id": 1,
    "code": "01-PAINT",
    "name": "Material - Paint",
    "category": "material",
    "active": true,
    "expense_count": 5,
    "total_expenses": "8500.00"
  }
]
```

### 2. Crear Código de Costo
```http
POST /api/v1/cost-codes/
Content-Type: application/json

{
  "code": "02-TOOLS",
  "name": "Tools & Equipment",
  "category": "equipment",
  "active": true
}
```

### 3. Actualizar Código de Costo
```http
PUT /api/v1/cost-codes/{id}/
PATCH /api/v1/cost-codes/{id}/
```

### 4. Eliminar Código de Costo
```http
DELETE /api/v1/cost-codes/{id}/
```

---

## 📊 Endpoints de Líneas Presupuestarias

### 1. Listar Líneas Presupuestarias
```http
GET /api/v1/budget-lines/
```

**Query Parameters**:
- `project` - Filtrar por ID de proyecto
- `cost_code` - Filtrar por ID de código de costo
- `allowance` - Filtrar por allowance (true/false)
- `ordering` - Ordenar por: `cost_code__code`, `baseline_amount`, `revised_amount`

**Ejemplo**:
```http
GET /api/v1/budget-lines/?project=1&ordering=cost_code__code
```

**Respuesta**:
```json
[
  {
    "id": 1,
    "project": 1,
    "project_name": "Casa Residencial Smith",
    "cost_code": 1,
    "cost_code_name": "Material - Paint",
    "description": "Pintura interior y exterior",
    "qty": "500.00",
    "unit": "sqft",
    "unit_cost": "15.00",
    "allowance": false,
    "baseline_amount": "7500.00",
    "revised_amount": "7500.00",
    "total_amount": "7500.00",
    "planned_start": "2025-01-15",
    "planned_finish": "2025-02-15",
    "weight_override": null
  }
]
```

### 2. Crear Línea Presupuestaria
```http
POST /api/v1/budget-lines/
Content-Type: application/json

{
  "project": 1,
  "cost_code": 2,
  "description": "Mano de obra pintura",
  "qty": "40.00",
  "unit": "hours",
  "unit_cost": "35.00",
  "planned_start": "2025-01-20",
  "planned_finish": "2025-02-10"
}
```

**Nota**: El campo `baseline_amount` se calcula automáticamente como `qty * unit_cost`.

### 3. Actualizar Línea Presupuestaria
```http
PUT /api/v1/budget-lines/{id}/
PATCH /api/v1/budget-lines/{id}/

{
  "revised_amount": "1600.00"
}
```

### 4. Eliminar Línea Presupuestaria
```http
DELETE /api/v1/budget-lines/{id}/
```

### 5. Resumen Presupuestario del Proyecto
```http
GET /api/v1/budget-lines/project_summary/?project=1
```

**Respuesta**:
```json
{
  "project_id": 1,
  "total_baseline": "20000.00",
  "total_revised": "21500.00",
  "variance": "1500.00",
  "by_cost_code": [
    {
      "cost_code__code": "01-PAINT",
      "cost_code__name": "Material - Paint",
      "cost_code__category": "material",
      "baseline": "7500.00",
      "revised": "7500.00"
    },
    {
      "cost_code__code": "02-LABOR",
      "cost_code__name": "Labor - Painting",
      "cost_code__category": "labor",
      "baseline": "12500.00",
      "revised": "14000.00"
    }
  ],
  "line_count": 8
}
```

---

## 📈 Casos de Uso Comunes

### Dashboard Financiero
```javascript
// Obtener resumen de todos los proyectos activos
const projects = await fetch('/api/v1/projects/?is_active=true');

// Obtener detalles financieros de un proyecto específico
const financial = await fetch('/api/v1/projects/1/financial_summary/');

// Obtener ingresos del mes actual
const incomes = await fetch('/api/v1/incomes/?date__gte=2025-11-01&date__lte=2025-11-30');

// Obtener gastos del mes por categoría
const expenses = await fetch('/api/v1/expenses/summary/?date__gte=2025-11-01');
```

### Tracking de Presupuesto
```javascript
// Ver todos los proyectos con estado de presupuesto
const budgets = await fetch('/api/v1/projects/budget_overview/');

// Ver detalle presupuestario de un proyecto
const budgetLines = await fetch('/api/v1/budget-lines/?project=1');

// Resumen presupuestario con cost codes
const summary = await fetch('/api/v1/budget-lines/project_summary/?project=1');
```

### Reportes
```javascript
// Gastos por categoría (últimos 30 días)
const expenseReport = await fetch('/api/v1/expenses/summary/?date__gte=2025-10-15');

// Ingresos por método de pago
const incomeReport = await fetch('/api/v1/incomes/summary/');

// Proyectos sobre presupuesto
const overBudget = await fetch('/api/v1/projects/budget_overview/')
  .then(res => res.json())
  .then(data => data.filter(p => p.is_over_budget));
```

---

## 🔄 Códigos de Estado HTTP

- `200 OK` - Solicitud exitosa
- `201 Created` - Recurso creado exitosamente
- `204 No Content` - Eliminación exitosa
- `400 Bad Request` - Datos inválidos o faltantes
- `401 Unauthorized` - Token inválido o faltante
- `403 Forbidden` - Sin permisos
- `404 Not Found` - Recurso no encontrado
- `500 Internal Server Error` - Error del servidor

---

## 📝 Notas Importantes

1. **Paginación**: Por defecto, los listados retornan 10 items por página. Usa `page_size` para cambiar esto.

2. **Fechas**: Usar formato ISO 8601 (`YYYY-MM-DD`).

3. **Decimales**: Los montos se retornan como strings para evitar problemas de precisión.

4. **Actualización Automática**: Al crear/actualizar/eliminar ingresos o gastos, los totales del proyecto se actualizan automáticamente.

5. **Archivos**: Los endpoints de Expense soportan `multipart/form-data` para subir recibos e invoices.

6. **Búsqueda**: El parámetro `search` busca en múltiples campos usando búsqueda case-insensitive.

---

## 🧪 Testing con cURL

```bash
# Obtener token
curl -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# Listar proyectos
curl -X GET http://localhost:8000/api/v1/projects/ \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"

# Crear ingreso
curl -X POST http://localhost:8000/api/v1/incomes/ \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "project": 1,
    "project_name": "Pago inicial",
    "amount": "5000.00",
    "date": "2025-11-15",
    "payment_method": "TRANSFERENCIA"
  }'

# Crear gasto con archivo
curl -X POST http://localhost:8000/api/v1/expenses/ \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -F "project=1" \
  -F "project_name=Compra materiales" \
  -F "amount=1200.00" \
  -F "date=2025-11-15" \
  -F "category=MATERIALES" \
  -F "receipt=@receipt.pdf"
```

---

**Documentación generada**: 15 de Noviembre, 2025  
**Versión del API**: 1.0  
**Mantenido por**: GitHub Copilot
