# 🏦 ANÁLISIS PROFUNDO DEL SISTEMA FINANCIERO — Kibray

> **Fecha:** Junio 2025  
> **Alcance:** Todos los modelos, vistas, servicios, API y templates financieros  
> **Objetivo:** Identificar código basura, bugs, redundancias y oportunidades de optimización  

---

## 📋 RESUMEN EJECUTIVO

| Categoría | Hallazgos |
|-----------|-----------|
| 🔴 **Bugs Críticos** | 3 |
| 🟠 **Código Muerto / Basura** | 5 modelos + 1 servicio |
| 🟡 **Redundancias** | 4 campos redundantes |
| 🔵 **Inconsistencias** | 3 patrones inconsistentes |
| 🟢 **Fortalezas** | Sistema de invoicing sólido, payroll robusto |
| ⚪ **Mejoras Propuestas** | 12 acciones concretas |

---

## 🏗️ ARQUITECTURA ACTUAL — Mapa Visual

```
┌─────────────────────────────────────────────────────────────┐
│                    SISTEMA FINANCIERO                        │
├──────────────┬──────────────┬───────────────┬───────────────┤
│   INGRESOS   │   GASTOS     │  FACTURACIÓN  │   NÓMINA      │
│              │              │               │               │
│ • Income     │ • Expense    │ • Invoice     │ • PayrollPrd  │
│              │ • ExpenseOCR │ • InvoiceLine │ • PayrollRec  │
│              │   (MUERTO)   │ • InvPayment  │ • PayrollPay  │
│              │              │ • InvLineEst  │               │
│              │              │ • InvAutomat  │               │
│              │              │   (MUERTO)    │               │
├──────────────┴──────────────┼───────────────┼───────────────┤
│       PRESUPUESTO           │  ESTIMADOS    │ CHANGE ORDERS │
│                             │               │               │
│ • CostCode                  │ • Estimate    │ • ChangeOrder │
│ • BudgetLine                │ • EstimateLn  │ • CO Photo    │
│ • BudgetProgress            │ • Proposal    │               │
│                             │ • Contract    │               │
├─────────────────────────────┴───────────────┴───────────────┤
│                    SERVICIOS / ANALYTICS                     │
│                                                             │
│ • FinancialAnalyticsService (financial_service.py)          │
│ • ChangeOrderService (financial_service.py)                 │
│ • compute_project_ev (earned_value.py) — REFS DEAD MODEL    │
├─────────────────────────────────────────────────────────────┤
│                    VISTAS / TEMPLATES                        │
│                                                             │
│ • views_financial.py (5 views: dashboard, aging, produc-    │
│   tivity, export, employee_performance)                     │
│ • legacy_views.py (~25 financial views)                     │
│ • API ViewSets: Invoice, Income, Expense, Payroll×3,        │
│   CostCode, BudgetLine, ChangeOrder + Dashboard views       │
└─────────────────────────────────────────────────────────────┘
```

**Total de modelos financieros:** 17  
**Templates financieros:** 26 archivos  
**Views financieras:** ~30 funciones  
**API ViewSets:** 9 endpoints  

---

## 🔴 BUGS CRÍTICOS (Requieren fix inmediato)

### BUG-1: Status Case Mismatch — `views_financial.py` vs `Invoice` model
**Severidad:** 🔴 CRÍTICO — Las queries NO DEVUELVEN DATOS

```python
# MODELO (core/models/__init__.py:2930)
STATUS_CHOICES = [
    ("DRAFT", "Draft"),       # ← MAYÚSCULAS
    ("SENT", "Sent"),
    ("PAID", "Paid Complete"),
    ...
]

# VISTA (core/views_financial.py:54) — ¡USA MINÚSCULAS!
Invoice.objects.filter(status="paid")                     # ❌ Devuelve 0 resultados
Invoice.objects.filter(status__in=["sent", "viewed"...])  # ❌ Devuelve 0 resultados

# MISMA VISTA (línea 238) — ¡USA MAYÚSCULAS!  
Invoice.objects.filter(status__in=["SENT", "VIEWED"...])  # ✅ Correcto
```

**Impacto:** El dashboard financiero ejecutivo muestra $0 en revenue, $0 en AR, 0 facturas vencidas. **Toda la data financiera del dashboard está rota.**

**Fix:** Cambiar todas las queries de `views_financial.py` a usar MAYÚSCULAS (`"PAID"`, `"SENT"`, etc.)

---

### BUG-2: `expense_set` vs `expenses` — Wrong Related Name
**Severidad:** 🔴 CRÍTICO — AttributeError en producción

```python
# MODELO (core/models/__init__.py:378)
project = models.ForeignKey(Project, related_name="expenses", ...)  # related_name="expenses"

# VISTA (core/views_financial.py:159)
total_expenses = project.expense_set.aggregate(...)  # ❌ expense_set NO existe, es "expenses"
```

**Impacto:** El alert de "proyectos sobre presupuesto" en el financial dashboard crashea con `AttributeError`.

**Fix:** Cambiar `project.expense_set` → `project.expenses`

---

### BUG-3: `earned_value.py` referencia `PayrollEntry` eliminado
**Severidad:** 🟠 ALTO — Silenciosamente falla

```python
# core/services/earned_value.py:52-58
try:
    from core.models import PayrollEntry    # ❌ Modelo eliminado en migración 0038
    pe_qs = PayrollEntry.objects.filter(...)
except Exception:
    pass  # Silenciosamente ignora — AC (Actual Cost) está INCOMPLETO
```

**Impacto:** El cálculo de Earned Value (EVM) no incluye costos de nómina → CPI y AC son incorrectos. El `try/except` oculta el error.

**Fix:** Reemplazar con `PayrollRecord` (modelo actual).

---

## 🟠 CÓDIGO MUERTO / BASURA (5 modelos + 1 servicio)

### DEAD-1: `ExpenseOCRData` — Modelo fantasma (línea 8106)
- **0 referencias** en views, API, o templates
- Solo existe en admin.py (registro de admin)
- Requiere `pytesseract + OpenCV` — **nunca instalados**
- **Veredicto:** 🗑️ ELIMINAR — No hay UI, no hay servicio, no hay tests

### DEAD-2: `InvoiceAutomation` — Modelo fantasma (línea 8159)
- **0 referencias** en views, API, o templates  
- Tiene campos de Stripe (`stripe_payment_intent_id`) — **nunca configurado**
- Recurring invoices, late fees, email reminders — **nada implementado**
- **Veredicto:** 🗑️ ELIMINAR — Es aspiracional, no funcional

### DEAD-3: `InventoryBarcode` — Modelo fantasma (línea 8223)
- **0 referencias** en views, API, o templates
- Requiere `python-barcode + pyzbar` — **nunca instalados**
- **Veredicto:** 🗑️ ELIMINAR — No es financiero realmente, y no funciona

### DEAD-4: `Proposal` modelo — Bajo uso
- Tiene `client_view_token` y `accepted` fields
- **Sin vistas dedicadas** para que el cliente acepte
- Duplica funcionalidad con el modelo `Contract` (que SÍ tiene flujo completo)
- **Veredicto:** ⚠️ EVALUAR — ¿Se usa? Si no, consolidar en Contract

### DEAD-5: `PayrollEntry` + `Payroll` — Eliminados pero referenciados
- Comentario en código: `# DEPRECATED: Payroll y PayrollEntry eliminados` (línea 2094)
- **PERO** `earned_value.py` aún los importa (BUG-3)
- Migración `0038` los eliminó correctamente de la DB
- **Veredicto:** ✅ Ya eliminados de DB, solo limpiar referencia en `earned_value.py`

### DEAD-6: `FinancialAnalyticsService.get_inventory_risk_items()`
- Consulta `ProjectInventory` — un modelo de inventario, NO financiero
- **No se usa en ninguna vista financiera**
- Está en `financial_service.py` pero es de inventario
- **Veredicto:** 🔄 MOVER a un servicio de inventario o eliminar

---

## 🟡 REDUNDANCIAS

### RED-1: Campo `project_name` en `Income` y `Expense`
```python
# Income (línea 345)
project_name = models.CharField(max_length=255, verbose_name="Nombre del proyecto o factura")

# Expense (línea 387)  
project_name = models.CharField(max_length=200, blank=True)
```
- **Ya tienen `project` ForeignKey** → `income.project.name` resuelve lo mismo
- Se usa como "label" al auto-crear Income desde Invoice: `project_name=f"Factura {number}"`
- **Veredicto:** Renombrar a `label` o `source_description` para claridad. No es nombre del proyecto.

### RED-2: `is_paid` en `Invoice` (deprecated pero activo)
```python
is_paid = models.BooleanField(
    default=False,
    help_text="DEPRECATED: usar amount_paid y total_amount; se eliminará tras migración"
)
```
- El modelo ya tiene `fully_paid` property y `_sync_payment_flags()` que lo mantiene sincronizado
- **Veredicto:** Planificar migración para eliminar `is_paid` y usar solo `amount_paid >= total_amount`

### RED-3: Doble creación de `Income` al pagar Invoice
```python
# Invoice.save() — Crea Income cuando invoice completa pago (línea 3070)
Income.objects.create(..., amount=self.total_amount, ...)

# InvoicePayment.save() — TAMBIÉN crea Income por cada pago (línea 3166)
Income.objects.create(..., amount=self.amount, ...)
```
- **Si pagas con 1 solo pago completo:** se crean 2 Income records (duplicado)
- El Invoice.save() crea Income por `total_amount`, InvoicePayment crea Income por `self.amount`
- **Veredicto:** 🔴 ELIMINAR la creación de Income en `Invoice.save()`. Solo `InvoicePayment` debe crear Income.

### RED-4: Test Compatibility Aliases en `ChangeOrder`
```python
# ChangeOrder.__init__ (línea ~2120)
def __init__(self, *args, **kwargs):
    # Map old test field names → real field names
    if "billing_hourly_rate" in kwargs: ...
    if "material_markup_pct" in kwargs: ...
```
- Override de `__init__` para compatibilidad de tests
- Properties `billing_hourly_rate`, `material_markup_pct`, `title` como aliases
- **Veredicto:** 🔄 Actualizar tests para usar nombres reales, eliminar aliases

---

## 🔵 INCONSISTENCIAS

### INCON-1: Choices en español vs inglés — Sin patrón
| Modelo | Choices |
|--------|---------|
| `Income.payment_method` | `EFECTIVO`, `TRANSFERENCIA`, `CHEQUE` ← **Español** |
| `Expense.category` | `MATERIALES`, `COMIDA`, `SEGURO` ← **Español** |
| `Invoice.STATUS_CHOICES` | `DRAFT`, `SENT`, `PAID` ← **Inglés MAYÚSCULAS** |
| `InvoicePayment.PAYMENT_METHOD` | `CHECK`, `CASH`, `TRANSFER` ← **Inglés MAYÚSCULAS** |
| `PayrollPeriod.STATUS_CHOICES` | `draft`, `under_review`, `approved` ← **Inglés minúsculas** |
| `ChangeOrder.STATUS_CHOICES` | `draft`, `pending`, `approved` ← **Inglés minúsculas** |

**Impacto:** Confusión para desarrolladores, queries frágiles (BUG-1 es consecuencia directa).

**Recomendación:** Estandarizar TODO en inglés MAYÚSCULAS con display names en español via `gettext`.

### INCON-2: Flujo Income — Fuentes múltiples sin coherencia
```
Income se crea desde:
1. Manual (vista income_create_view)
2. Auto desde Invoice.save() cuando se paga completa
3. Auto desde InvoicePayment.save() por cada pago parcial
4. No hay reconciliación entre fuentes
```
**Problema:** No hay forma de distinguir Income manual vs auto-generado. No hay campo `source` o `auto_generated`.

### INCON-3: `PayrollRecord.create_expense_record()` usa `Project.objects.first()`
```python
# core/models/__init__.py (dentro de PayrollRecord)
project = Project.objects.first()  # ← PELIGROSO: asigna al primer proyecto random
```
**Impacto:** Gastos de nómina podrían asignarse al proyecto incorrecto.

---

## 🟢 FORTALEZAS DEL SISTEMA

### ✅ Lo que funciona bien:
1. **Invoice pipeline completo:** DRAFT → SENT → VIEWED → APPROVED → PARTIAL → PAID con tracking de fechas
2. **InvoicePayment con pagos parciales:** Permite múltiples pagos, auto-actualiza status
3. **Progressive billing (InvoiceLineEstimate):** Facturación por porcentaje de estimate lines, validación de 100%
4. **PayrollPeriod workflow:** draft → under_review → approved → paid con validación y aprobación
5. **Estimate → Contract → Invoice pipeline:** Cadena completa de estimate aprobado a contrato firmado
6. **ChangeOrder con T&M y Fixed pricing:** Dos modelos de pricing con cálculos correctos
7. **BudgetLine + BudgetProgress + CostCode:** Sistema de presupuesto con tracking de avance
8. **Earned Value Management (EVM):** SPI y CPI para análisis de proyecto (necesita fix de PayrollEntry)
9. **FinancialAnalyticsService:** Cash flow projection, project margins, company KPIs (necesita fix de case)
10. **Contract model con firma digital:** Client signature, contractor countersign, revision tracking

---

## 📊 INVENTARIO COMPLETO DE COMPONENTES

### Modelos (17 total)
| # | Modelo | Línea | Estado | Acción |
|---|--------|-------|--------|--------|
| 1 | `Income` | 343 | ⚠️ Redundancias | Fix `project_name` |
| 2 | `Expense` | 377 | ⚠️ Redundancias | Fix `project_name` |
| 3 | `ChangeOrder` | 2100 | ⚠️ Test aliases | Limpiar aliases |
| 4 | `ChangeOrderPhoto` | 2249 | ✅ Sólido | — |
| 5 | `PayrollPeriod` | 2302 | ✅ Sólido | — |
| 6 | `PayrollRecord` | 2423 | ⚠️ Pesado (25+ fields) | Fix `Project.objects.first()` |
| 7 | `PayrollPayment` | 2654 | ✅ Sólido | — |
| 8 | `Invoice` | 2918 | ⚠️ Doble Income | Fix doble creación |
| 9 | `InvoiceLine` | 3106 | ✅ Sólido | — |
| 10 | `InvoicePayment` | 3120 | ✅ Sólido | — |
| 11 | `InvoiceLineEstimate` | 3188 | ✅ Sólido | — |
| 12 | `CostCode` | 3251 | ✅ Sólido | — |
| 13 | `BudgetLine` | 3261 | ✅ Sólido | — |
| 14 | `Estimate` | 3307 | ✅ Sólido | — |
| 15 | `EstimateLine` | 3375 | ✅ Sólido | — |
| 16 | `Proposal` | ~3420 | ❓ Bajo uso | Evaluar vs Contract |
| 17 | `Contract` | ~3440 | ✅ Completo | — |

### Modelos MUERTOS (eliminar)
| # | Modelo | Línea | Razón |
|---|--------|-------|-------|
| 18 | `ExpenseOCRData` | 8106 | 0 refs en views/API, deps no instaladas |
| 19 | `InvoiceAutomation` | 8159 | 0 refs en views/API, Stripe no config |
| 20 | `InventoryBarcode` | 8223 | 0 refs en views/API, deps no instaladas |
| 21 | `BudgetProgress` | 4036 | ⚠️ Usado por EVM, OK mantener |

### Templates (26 archivos)
| Área | Templates | Estado |
|------|-----------|--------|
| Invoice | `invoice_builder`, `invoice_list`, `invoice_detail`, `invoice_pdf`, `invoice_aging_report`, `invoice_payment_dashboard`, `project_invoices_list` | ✅ Completo |
| Payroll | `payroll_weekly_review`, `payroll_payment_form`, `payroll_payment_history`, `my_payroll` | ✅ Completo |
| Expense | `expense_list`, `expense_form`, `expense_confirm_delete` | ✅ Básico |
| Income | `income_list`, `income_form`, `income_confirm_delete` | ✅ Básico |
| Budget | `budget_lines`, `budget_wizard`, `budget_line_plan`, `project_budget_detail` | ✅ Completo |
| Estimate | `estimate_form`, `estimate_detail`, `estimate_pdf`, `project_estimates_list` | ✅ Completo |
| Financial | `financial_dashboard`, `project_financials_hub`, `project_profit_dashboard`, `client_financials` | ⚠️ Dashboard con bugs |

### API ViewSets (9 endpoints)
| ViewSet | Archivo | Estado |
|---------|---------|--------|
| `InvoiceViewSet` | api/views.py:498 | ✅ |
| `IncomeViewSet` | api/views.py:2666 | ✅ |
| `ExpenseViewSet` | api/views.py:2741 | ✅ |
| `PayrollPeriodViewSet` | api/views.py:1307 | ✅ |
| `PayrollRecordViewSet` | api/views.py:1427 | ✅ |
| `PayrollPaymentViewSet` | api/views.py:1466 | ✅ |
| `CostCodeViewSet` | api/views.py:2827 | ✅ |
| `BudgetLineViewSet` | api/views.py:2857 | ✅ |
| `ChangeOrderViewSet` | viewset_classes/ | ✅ |
| `InvoiceDashboardView` | api/views.py:5071 | ✅ |
| `InvoiceTrendsView` | api/views.py:5105 | ✅ |

---

## 🎯 PLAN DE ACCIÓN PRIORIZADO

### Fase 1: 🔴 Fixes Críticos (Inmediato) — ✅ COMPLETADO `2ed1e2ce`
| # | Acción | Archivos | Estado |
|---|--------|----------|--------|
| 1 | ✅ Fix status case mismatch en `views_financial.py` | `core/views_financial.py` | DONE |
| 2 | ✅ Fix `expense_set` → `expenses` | `core/views_financial.py` | DONE |
| 3 | ✅ Fix `PayrollEntry` → `PayrollRecord` en `earned_value.py` | `core/services/earned_value.py` | DONE |
| 4 | ✅ Fix doble creación de Income en `Invoice.save()` | `core/models/__init__.py` | DONE |
| 5 | ✅ Fix `Project.objects.first()` con smart lookup | `core/models/__init__.py` | DONE |

### Fase 2: 🟠 Limpieza de Código Muerto — ✅ COMPLETADO `2ed1e2ce`
| # | Acción | Archivos | Estado |
|---|--------|----------|--------|
| 6 | ✅ Eliminar `ExpenseOCRData` + admin | `models/__init__.py`, `admin.py` | DONE |
| 7 | ✅ Eliminar `InvoiceAutomation` + admin | `models/__init__.py`, `admin.py` | DONE |
| 8 | ✅ Eliminar `InventoryBarcode` + admin | `models/__init__.py`, `admin.py` | DONE |
| 9 | ✅ Migración `0174` generada | `core/migrations/0174_*.py` | DONE |

### Fase 3: 🟡 Estandarización — ✅ COMPLETADO `a754c223`
| # | Acción | Archivos | Estado |
|---|--------|----------|--------|
| 10 | ⏸️ DEFERRED — Estandarizar choices a UPPER_ENGLISH | Riesgo: data migration en producción | DEFERRED |
| 11 | ⏸️ DEFERRED — Renombrar `project_name` → `source_label` | Riesgo: ~30+ refs en models/forms/templates | DEFERRED |
| 12 | ✅ Agregar campo `source` a Income + migration 0175 | `models/__init__.py` | DONE |
| 12b | ✅ InvoicePayment auto-set `source="INVOICE_PAYMENT"` | `models/__init__.py` | DONE |
| 12c | ✅ ChangeOrder: Removed `__init__` kwargs alias mapping | `models/__init__.py` | DONE |
| 12d | ✅ ChangeOrder: Removed property setters, kept read-only | `models/__init__.py` | DONE |
| 12e | ✅ tasks.py: `material_markup_pct` → `material_markup_percent` | `core/tasks.py` | DONE |
| 12f | ✅ PayrollPeriod N+1 → aggregate queries | `models/__init__.py` | DONE |

### Fase 4: 🔵 Mejoras Futuras (Post-estabilización) — ✅ COMPLETADO `10d44722`
| # | Acción | Descripción | Estado |
|---|--------|-------------|--------|
| 13 | ✅ Eliminar `is_paid` deprecated de Invoice | Removido campo + migration 0176 | DONE |
| 14 | ~~Limpiar test aliases de ChangeOrder~~ | ✅ Hecho en Fase 3 (12c/12d) | DONE |
| 15 | ✅ Evaluar Proposal vs Contract | Son modelos distintos (correcto) — no consolidar | EVALUATED |
| 16 | ~~Agregar `auto_generated` flag a Income~~ | ✅ Reemplazado por `source` field (12) | DONE |
| 17 | ~~Optimizar N+1 queries en PayrollPeriod~~ | ✅ Hecho en Fase 3 (12f) | DONE |

---

## 📐 MODELO IDEAL vs MODELO ACTUAL

```
FLUJO IDEAL:
                                                          
  Estimate ──approve──→ Contract ──sign──→ Project Active  
      │                     │                     │        
      └──→ BudgetLines      └──→ PaymentSchedule  │        
                │                                  │        
                ▼                                  ▼        
  CostCodes ──→ Budget Tracking     Invoice Builder        
                │                        │                 
                ▼                        ▼                 
  BudgetProgress          InvoiceLine ←── EstimateLine     
        │                      │                           
        ▼                      ▼                           
  EVM (SPI/CPI)          InvoicePayment ──→ Income (auto)  
                               │                           
                               ▼                           
                          Status Pipeline                  
                    DRAFT→SENT→VIEWED→PARTIAL→PAID         
                                                           
  Payroll System:    ChangeOrder System:                   
  Period→Record→Pay  CO(Fixed/T&M)→Sign→Bill→Invoice       
        │                   │                              
        ▼                   ▼                              
     Expense (auto)     Expense (linked)                   

EL SISTEMA ACTUAL YA TIENE ESTE FLUJO.
Los problemas son de CALIDAD (bugs, código muerto)
no de ARQUITECTURA (que es sólida).
```

---

## 💡 CONCLUSIÓN

**El modelo de datos es CORRECTO y ROBUSTO.** La arquitectura financiera está bien diseñada con:
- Pipeline completo Estimate → Contract → Invoice → Payment
- Sistema de nómina con períodos, registros y pagos
- Change Orders con pricing dual (Fixed/T&M)
- Presupuesto con CostCodes, BudgetLines y EVM

**Los problemas eran de EJECUCIÓN, no de DISEÑO:**
1. ✅ **3 bugs críticos** — Corregidos (case mismatch, wrong related_name, dead model ref)
2. ✅ **3 modelos fantasma** — Eliminados (OCR, Automation, Barcode) + migration 0174
3. ✅ **Income sin trazabilidad** — Agregado campo `source` + migration 0175
4. ✅ **Duplicación lógica** — Eliminada doble Income creation en Invoice.save()
5. ✅ **ChangeOrder código muerto** — __init__ override + property setters eliminados
6. ✅ **N+1 queries** — PayrollPeriod optimizado con aggregate queries
7. ⏸️ **Inconsistencias de naming** — DEFERRED (Spanish choices, project_name field) por riesgo en producción

**Commits:**
- `2ed1e2ce` — Phase 1+2: 5 critical fixes + 3 dead models removed
- `a754c223` — Phase 3: Income.source, ChangeOrder cleanup, N+1 optimization
- `10d44722` — Phase 4: Remove deprecated Invoice.is_paid + migration 0176

**✅ Auditoría financiera completa. Todas las fases ejecutadas.**

---

*Reporte generado por análisis profundo de: `core/models/__init__.py` (10,161 líneas), `core/services/financial_service.py`, `core/services/earned_value.py`, `core/views_financial.py`, `core/views/legacy_views.py`, `core/api/views.py`, `kibray_backend/urls.py`, y 26 templates.*
