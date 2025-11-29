# ✅ CHECKLIST DE VALIDACIÓN - ARQUITECTURA FINAL

**Fecha:** 28 de Noviembre, 2025  
**Tester:** _______________  
**Ambiente:** _______________  

---

## 🎯 OBJETIVO

Validar manualmente las funcionalidades críticas implementadas en la Arquitectura Final antes del deploy a producción.

**Prerequisitos:**
```bash
# 1. Ejecutar simulación
python manage.py simulate_company

# 2. Credenciales generadas:
# - admin_kibray / admin123
# - pm_full / pm123
# - pm_trainee / trainee123
# - designer / designer123
# - superintendent / super123
# - jose_pintor / employee123
# - cliente_villa / client123
```

---

## 📋 MÓDULO 1: FACTURACIÓN FLEXIBLE

### Test 1.1: Invoice Deposit (Anticipo)
**User:** pm_full  
**Steps:**
1. Login como `pm_full`
2. Ir a proyecto "Villa Moderna"
3. Ver invoices existentes
4. ✅ Verificar: Invoice #KPRV1000-INV01 existe
5. ✅ Verificar: `invoice_type = 'deposit'`
6. ✅ Verificar: `total_amount = $5,000.00`
7. ✅ Verificar: `status = 'PAGADA'`

**Resultado:** ☐ Pass | ☐ Fail  
**Notas:** _________________________________

---

### Test 1.2: Invoice con Retención
**User:** pm_full  
**Steps:**
1. Login como `pm_full`
2. Crear nueva invoice en "Villa Moderna"
3. Setear:
   - `invoice_type = 'final'`
   - `total_amount = $10,000`
   - `retention_amount = $500` (5%)
4. ✅ Verificar: `calculate_net_payable()` retorna `$9,500`

**Resultado:** ☐ Pass | ☐ Fail  
**Notas:** _________________________________

---

### Test 1.3: PM Trainee - Draft for Review
**User:** pm_trainee  
**Steps:**
1. Login como `pm_trainee`
2. Crear nueva invoice en "Villa Moderna"
3. Setear `total_amount = $2,000`
4. Guardar
5. ✅ Verificar: `is_draft_for_review = True` (auto)
6. ✅ Verificar: `status = 'DRAFT'` (auto)
7. ✅ Verificar: Notificación enviada a admin

**Resultado:** ☐ Pass | ☐ Fail  
**Notas:** _________________________________

---

## 💳 MÓDULO 2: REEMBOLSOS A EMPLEADOS

### Test 2.1: Crear Expense Reembolsable
**User:** pm_full  
**Steps:**
1. Login como `pm_full`
2. Ver expense existente (José Pintor, $15 brocha)
3. ✅ Verificar: `paid_by_employee = José Pintor`
4. ✅ Verificar: `reimbursement_status = 'pending'` (auto)
5. ✅ Verificar: `category = 'HERRAMIENTAS'`

**Resultado:** ☐ Pass | ☐ Fail  
**Notas:** _________________________________

---

### Test 2.2: Marcar como Reembolsado
**User:** admin_kibray  
**Steps:**
1. Login como `admin_kibray`
2. Abrir expense de José Pintor ($15)
3. Ejecutar: `mark_reimbursed(method='paid_direct', reference='CHK-1001')`
4. ✅ Verificar: `reimbursement_status = 'paid_direct'`
5. ✅ Verificar: `reimbursement_date = hoy`
6. ✅ Verificar: `reimbursement_reference = 'CHK-1001'`

**Resultado:** ☐ Pass | ☐ Fail  
**Notas:** _________________________________

---

## 📅 MÓDULO 3: PLANNER INTELIGENTE

### Test 3.1: Schedule Weight
**User:** pm_full  
**Steps:**
1. Login como `pm_full`
2. Ver tareas de "Villa Moderna"
3. ✅ Verificar: Tarea "Aprobar colores cocina" tiene `schedule_weight = 100`
4. ✅ Verificar: Tarea "Pintar sala" tiene `schedule_weight = 90`
5. ✅ Verificar: Tarea "Preparar paredes" tiene `schedule_weight = 80`
6. Ordenar por `schedule_weight DESC`
7. ✅ Verificar: Orden correcto (100 → 90 → 80)

**Resultado:** ☐ Pass | ☐ Fail  
**Notas:** _________________________________

---

### Test 3.2: Checklist Funcional
**User:** jose_pintor  
**Steps:**
1. Login como `jose_pintor`
2. Abrir tarea "Preparar paredes planta baja"
3. ✅ Verificar: Checklist tiene 4 items
4. ✅ Verificar: 3 items checked (proteger, lijar, limpiar)
5. ✅ Verificar: 1 item unchecked (aplicar primer)
6. Marcar "aplicar primer" como checked
7. Guardar
8. ✅ Verificar: Persiste cambio

**Resultado:** ☐ Pass | ☐ Fail  
**Notas:** _________________________________

---

### Test 3.3: Progress Percent
**User:** jose_pintor  
**Steps:**
1. Login como `jose_pintor`
2. Abrir tarea "Preparar paredes planta baja"
3. ✅ Verificar: `progress_percent = 60`
4. Actualizar a `progress_percent = 100`
5. Guardar
6. ✅ Verificar: Tarea guardada exitosamente

**Resultado:** ☐ Pass | ☐ Fail  
**Notas:** _________________________________

---

### Test 3.4: Client Responsibility Flag
**User:** cliente_villa  
**Steps:**
1. Login como `cliente_villa`
2. Ver tareas de "Villa Moderna"
3. ✅ Verificar: Tarea "Aprobar colores cocina" tiene badge "CLIENTE RESPONSABLE"
4. ✅ Verificar: `is_client_responsibility = True`
5. ✅ Verificar: No puede editar (solo vista)

**Resultado:** ☐ Pass | ☐ Fail  
**Notas:** _________________________________

---

## 🎨 MÓDULO 4: PIN CLEANUP AUTOMÁTICO

### Test 4.1: Pin Visibility Before Completion
**User:** pm_full  
**Steps:**
1. Login como `pm_full`
2. Abrir plano "Planta Baja - Villa Moderna"
3. ✅ Verificar: 4 pins visibles
4. Filtrar por tipo `task`
5. ✅ Verificar: 1 pin tipo `task` visible

**Resultado:** ☐ Pass | ☐ Fail  
**Notas:** _________________________________

---

### Test 4.2: Pin Cleanup on Task Completion
**User:** jose_pintor  
**Steps:**
1. Login como `jose_pintor`
2. Buscar tarea asociada a pin tipo `task`
3. Actualizar `progress_percent = 100`
4. Guardar
5. Refrescar plano
6. ✅ Verificar: Pin tipo `task` tiene `is_visible = False`
7. ✅ Verificar: Pin NO aparece en plano (oculto)

**Resultado:** ☐ Pass | ☐ Fail  
**Notas:** _________________________________

---

### Test 4.3: Info/Hazard Pins Remain Visible
**User:** pm_full  
**Steps:**
1. Login como `pm_full`
2. Completar TODAS las tareas del proyecto
3. Refrescar plano
4. ✅ Verificar: Pins tipo `info` siguen visibles
5. ✅ Verificar: Pins tipo `hazard` siguen visibles
6. ✅ Verificar: Pins tipo `task`/`touchup` ocultos

**Resultado:** ☐ Pass | ☐ Fail  
**Notas:** _________________________________

---

## 📦 MÓDULO 5: BULK TRANSFER CON LEFTOVER EXCLUSION

### Test 5.1: Inventario Pre-Transfer
**User:** pm_full  
**Steps:**
1. Login como `pm_full`
2. Ir a inventario "Villa Moderna"
3. ✅ Verificar: 7 items en "Sitio Villa Moderna"
4. ✅ Verificar: Categorías incluyen PINTURA, HERRAMIENTA
5. Anotar IDs de items

**Resultado:** ☐ Pass | ☐ Fail  
**Items:** _________________________________

---

### Test 5.2: Marcar Leftover en Plano
**User:** pm_full  
**Steps:**
1. Login como `pm_full`
2. Abrir plano "Planta Baja"
3. Buscar pin tipo `leftover`
4. ✅ Verificar: Pin apunta a item de inventario (ej: Pintura Blanca)
5. Anotar `inventory_item_id`

**Resultado:** ☐ Pass | ☐ Fail  
**Item marcado:** _________________________________

---

### Test 5.3: Ejecutar Bulk Transfer
**User:** admin_kibray  
**Steps:**
1. Login como `admin_kibray`
2. Ejecutar en Django shell:
```python
from core.models import ProjectInventory, Project
project = Project.objects.get(name__icontains='Villa Moderna')
result = ProjectInventory.bulk_transfer(
    project=project,
    category_list=['PINTURA', 'HERRAMIENTA'],
    exclude_leftover=True
)
print(result)
```
3. ✅ Verificar: `success = True`
4. ✅ Verificar: `total_transferred = 6` (no 7, porque 1 leftover excluido)
5. ✅ Verificar: Item marcado como `leftover` NO transferido

**Resultado:** ☐ Pass | ☐ Fail  
**Resultado dict:** _________________________________

---

## 🎨 MÓDULO 6: COLORSAMPLE → PROJECT INTEGRATION

### Test 6.1: Aprobar ColorSample
**User:** cliente_villa  
**Steps:**
1. Login como `cliente_villa`
2. Si no existe, crear ColorSample:
   - `name = 'Pure White'`
   - `code = 'SW7005'`
   - `brand = 'Sherwin-Williams'`
   - `room_location = 'Cocina'`
   - `finish = 'PINTURA'`
   - `gloss = 'MATE'`
3. Aprobar muestra
4. ✅ Verificar: `status = 'approved'`

**Resultado:** ☐ Pass | ☐ Fail  
**Notas:** _________________________________

---

### Test 6.2: Verificar Project.approved_finishes
**User:** pm_full  
**Steps:**
1. Login como `pm_full`
2. Abrir proyecto "Villa Moderna"
3. Ver campo `approved_finishes` (JSON)
4. ✅ Verificar estructura:
```json
{
  "Cocina": {
    "PINTURA_MATE": {
      "code": "SW7005",
      "name": "Pure White",
      "brand": "Sherwin-Williams",
      "sample_id": <id>,
      "approved_at": "<timestamp>"
    }
  }
}
```

**Resultado:** ☐ Pass | ☐ Fail  
**JSON:** _________________________________

---

## 🔐 MÓDULO 7: ROLES Y PERMISOS

### Test 7.1: General Manager - Full Access
**User:** admin_kibray  
**Steps:**
1. Login como `admin_kibray`
2. ✅ Verificar acceso a: Invoice, Expense, Income, PayrollRecord
3. ✅ Verificar: Puede crear, editar, borrar todos
4. ✅ Verificar: Tiene `can_send_external_emails` permission

**Resultado:** ☐ Pass | ☐ Fail  
**Notas:** _________________________________

---

### Test 7.2: PM Full - CRUD + Email
**User:** pm_full  
**Steps:**
1. Login como `pm_full`
2. ✅ Verificar: Puede crear/editar/borrar Invoice
3. ✅ Verificar: Puede crear/editar/borrar ChangeOrder
4. ✅ Verificar: Puede VIEW Expense/Income (no edit/delete)
5. ✅ Verificar: Tiene `can_send_external_emails` permission

**Resultado:** ☐ Pass | ☐ Fail  
**Notas:** _________________________________

---

### Test 7.3: PM Trainee - Sin Email
**User:** pm_trainee  
**Steps:**
1. Login como `pm_trainee`
2. ✅ Verificar: Puede crear/editar Invoice (NO delete)
3. ✅ Verificar: Invoices van a `is_draft_for_review=True`
4. ✅ Verificar: NO tiene `can_send_external_emails` permission
5. ✅ Verificar: NO puede borrar ChangeOrder

**Resultado:** ☐ Pass | ☐ Fail  
**Notas:** _________________________________

---

### Test 7.4: Designer - Interfaz Zen
**User:** designer  
**Steps:**
1. Login como `designer`
2. ✅ Verificar: Solo ve: ColorSample, FloorPlan, ChatChannel
3. ✅ Verificar: CRUD completo en esos 3 modelos
4. ✅ Verificar: VIEW Project, Task (no edit)
5. ✅ Verificar: NO ve: Invoice, Expense, Inventory, Schedule, DailyLog

**Resultado:** ☐ Pass | ☐ Fail  
**Notas:** _________________________________

---

### Test 7.5: Superintendent - Firewall Financiero
**User:** superintendent  
**Steps:**
1. Login como `superintendent`
2. ✅ Verificar: Puede ver/editar Task, DailyLog
3. ✅ Verificar: Puede ver Schedule, Project (no edit)
4. ✅ Verificar: NO ve: Invoice, Expense, Income, PayrollRecord

**Resultado:** ☐ Pass | ☐ Fail  
**Notas:** _________________________________

---

### Test 7.6: Employee - Acceso Mínimo
**User:** jose_pintor  
**Steps:**
1. Login como `jose_pintor`
2. ✅ Verificar: Solo ve Task (sus asignadas)
3. ✅ Verificar: Puede cambiar status de Task
4. ✅ Verificar: Puede ver TimeEntry (sus registros)
5. ✅ Verificar: NO ve: Project, Schedule, Invoice, etc.

**Resultado:** ☐ Pass | ☐ Fail  
**Notas:** _________________________________

---

### Test 7.7: Client - Vista Externa
**User:** cliente_villa  
**Steps:**
1. Login como `cliente_villa`
2. ✅ Verificar: Ve Project, Schedule, Invoice, ChangeOrder (solo SU proyecto)
3. ✅ Verificar: Ve Task, ColorSample, FloorPlan
4. ✅ Verificar: Puede agregar comentarios en ChatChannel
5. ✅ Verificar: NO ve: Expense, Income, PayrollRecord, Employee, TimeEntry

**Resultado:** ☐ Pass | ☐ Fail  
**Notas:** _________________________________

---

## 📊 MÓDULO 8: PROJECT - CAMPOS FINANCIEROS

### Test 8.1: Material Markup
**User:** pm_full  
**Steps:**
1. Login como `pm_full`
2. Ver proyecto "Villa Moderna"
3. ✅ Verificar: `material_markup_percent = 15.00`
4. Calcular: `get_material_markup_multiplier()`
5. ✅ Verificar: Retorna `Decimal('1.15')`

**Resultado:** ☐ Pass | ☐ Fail  
**Cálculo:** _________________________________

---

### Test 8.2: Remaining Balance
**User:** pm_full  
**Steps:**
1. Login como `pm_full`
2. Ver proyecto "Villa Moderna"
3. Ejecutar: `calculate_remaining_balance()`
4. ✅ Verificar: Retorna `$45,500.00`
   - Budget: $50,000
   - + CO: $500
   - - Invoice: $5,000
   - = $45,500

**Resultado:** ☐ Pass | ☐ Fail  
**Balance:** _________________________________

---

### Test 8.3: Archive for PM
**User:** admin_kibray  
**Steps:**
1. Login como `admin_kibray`
2. Abrir proyecto "Villa Moderna"
3. Setear `is_archived_for_pm = True`
4. Guardar
5. Login como `pm_full`
6. ✅ Verificar: "Villa Moderna" NO aparece en dashboard PM
7. Login como `admin_kibray`
8. ✅ Verificar: "Villa Moderna" SÍ aparece en dashboard Admin

**Resultado:** ☐ Pass | ☐ Fail  
**Notas:** _________________________________

---

## 📈 RESUMEN DE RESULTADOS

### Módulos Pasados

- ☐ Facturación Flexible (3 tests)
- ☐ Reembolsos a Empleados (2 tests)
- ☐ Planner Inteligente (4 tests)
- ☐ Pin Cleanup Automático (3 tests)
- ☐ Bulk Transfer (3 tests)
- ☐ ColorSample Integration (2 tests)
- ☐ Roles y Permisos (7 tests)
- ☐ Project Financials (3 tests)

### Total

**Tests Ejecutados:** ___ / 27  
**Tests Pasados:** ___ / 27  
**Tests Fallidos:** ___ / 27  

### Bloqueadores

| Issue # | Módulo | Descripción | Severidad |
|---------|--------|-------------|-----------|
| | | | |
| | | | |

---

## ✅ APROBACIÓN FINAL

**Tester:** _______________  
**Fecha:** _______________  
**Firma:** _______________

**Estado Final:** ☐ APROBADO PARA PRODUCCIÓN | ☐ REQUIERE CORRECCIONES

**Comentarios:**
_____________________________________________________________
_____________________________________________________________
_____________________________________________________________

---

*Checklist generado automáticamente. Versión 1.0*
