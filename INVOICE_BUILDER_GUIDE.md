# 🎉 INVOICE BUILDER - GUÍA DE USO RÁPIDO

## ¿Qué Acabamos de Crear?

Un sistema inteligente que te ahorra **30-45 minutos** por factura al automatizar la recopilación de:
- ✅ Estimados aprobados (contrato base)
- ✅ Change Orders aprobados (trabajos extras)
- ✅ Tiempo & Materiales (horas registradas por empleados)

## 🚀 Cómo Usar el Invoice Builder

### Paso 1: Ir al Proyecto
```
Desde tu dashboard → Selecciona un proyecto
O navega a: /projects/<id>/invoice-builder/
```

URL directa: `http://localhost:8000/invoices/builder/<project_id>/`

### Paso 2: Revisar lo que el Sistema Pre-seleccionó

El sistema automáticamente muestra:

#### 📋 Contrato Base (Estimado)
- Último estimado aprobado
- Con markup aplicado (material + labor + overhead + profit)
- **Pre-seleccionado** ✓

#### 🔧 Change Orders
- Solo COs en estado `approved` o `sent`
- Que NO hayan sido facturados antes
- **Todos pre-seleccionados** ✓

#### ⏱️ Tiempo & Materiales (General)
- TimeEntries sin ChangeOrder asignado
- Muestra horas totales
- **Factura a $50/hora** (tu rate)
- **Pre-seleccionado** ✓

#### ⏱️ Tiempo & Materiales (en COs)
- TimeEntries que SÍ tienen ChangeOrder asignado
- Agrupados por CO
- **Factura a $50/hora adicional**
- **Pre-seleccionados** ✓

### Paso 3: Ajustar (si es necesario)
- Desmarca casillas para EXCLUIR items
- Por ejemplo: si aún no quieres facturar un CO específico

### Paso 4: Generar Factura
1. Revisa el **Resumen** (columna derecha)
2. Ajusta fecha de vencimiento (default: Net 30 días)
3. Click "✅ Generar Factura"

### Resultado
- ✅ Factura creada en estado **BORRADOR**
- ✅ Líneas generadas automáticamente
- ✅ Total calculado
- ✅ Change Orders marcados como `billed`
- ✅ Listo para enviar al cliente

---

## 💰 Sistema de Tracking de Pagos

### Modelos Nuevos

#### 1. Invoice (Mejorado)
```python
status = 'DRAFT' | 'SENT' | 'PARTIAL' | 'PAID' | 'OVERDUE'
amount_paid = Decimal  # Total pagado hasta ahora
sent_date = DateTime   # Cuándo se envió
paid_date = DateTime   # Cuándo se pagó completa
```

**Propiedades:**
- `balance_due` → Cuánto falta por pagar
- `payment_progress` → % pagado

#### 2. InvoicePayment (Nuevo)
```python
invoice = FK(Invoice)
amount = Decimal
payment_date = Date
payment_method = 'CHECK' | 'CASH' | 'TRANSFER' | 'CARD'
reference = CharField  # Check #, Transfer ID
```

**Auto-actualiza:**
- `invoice.amount_paid` += payment.amount
- `invoice.status` → 'PARTIAL' o 'PAID'
- Crea `Income` automáticamente

---

## 📊 Cómo Ver Todo Esto

### En Django Admin
```
/admin/core/invoice/
```
Ahora verás:
- Columnas: invoice_number, project, **status**, total_amount, **amount_paid**, **balance_due**
- Inline: **InvoicePayment** (tabla de pagos dentro de cada factura)

### Próximo: Record Payment View
Crearemos botón en invoice_detail: "💵 Registrar Pago"

---

## 🎯 Lo Que Esto Resuelve

### ANTES (Tu Pain Point)
1. Crear factura
2. ❓ "¿Qué COs aprobé?"
3. ❓ "¿Cuánto tiempo trabajaron en extras?" → **LLAMAR A EMPLEADOS**
4. ⏱️ 30-45 minutos copiando datos manualmente
5. ❌ Riesgo de olvidar cobrar COs

### AHORA
1. Click "Invoice Builder"
2. Todo pre-poblado automáticamente
3. Click "Generar"
4. ✅ 2 minutos total

### Tiempo Ahorrado
- **30-45 min/factura** × 10 facturas/mes = **5-7.5 horas/mes**
- **60-90 horas/año** de papeleo eliminado

---

## 🔥 SIGUIENTES PASOS (En Orden de Prioridad)

### 1. Record Payment View (15 min)
Botón para registrar pagos parciales:
```
Invoice Detail → [💵 Registrar Pago]
→ Form: amount, date, method, reference
→ Actualiza invoice.amount_paid
→ Crea Income automático
```

### 2. Project Profit Dashboard (30 min)
Vista que muestra:
- 📈 Budgeted Revenue (Estimate + COs)
- 💰 Actual Costs (TimeEntries + Expenses)
- 📊 **Profit Margin** en tiempo real
- ⚠️ Alertas si margen < 10%

### 3. Professional Invoice PDF (45 min)
- Logo de empresa
- Layout profesional
- WeasyPrint para calidad impresión

### 4. Material Markup Calculator (30 min)
Analiza tus proyectos históricos y recomienda:
- Material markup: 15-25%
- Overhead allocation: 10-15%
- Para alcanzar tu target profit: 25-35%

---

## 💡 TIPS PRO

### Para Empleados
Cuando registren tiempo en **extras/cambios**:
1. Seleccionar TimeEntry normal
2. **Asignar el ChangeOrder** en el dropdown
3. Agregar nota: "Pintado extra de puerta"

Así TÚ nunca tienes que llamarlos!

### Para Ti
- Usa Invoice Builder **semanalmente** o **por milestone**
- Envía facturas regularmente = mejor cash flow
- Revisa dashboard de profit **durante** proyecto, no al final

---

## 🐛 Si Algo No Funciona

### Error: "No hay estimado aprobado"
→ Ve a proyecto → Estimates → Marca uno como `approved=True`

### Error: "No se encuentran COs"
→ COs deben estar en estado `approved` o `sent`

### TimeEntries no aparecen
→ Verifica que:
  - `project` esté correcto
  - No estén ya linkeados a otra factura (InvoiceLine.time_entry)

---

## 📞 Para Configurar en Producción

### 1. Ajustar T&M Rate
En `invoice_builder_view` línea ~625:
```python
TM_HOURLY_RATE = Decimal('50.00')  # Cambiar aquí
```

### 2. Default Payment Terms
En `invoice_builder_view` línea ~688:
```python
due_date = timezone.now().date() + timedelta(days=30)  # Net 30
# Cambiar a: timedelta(days=15) para Net 15
```

### 3. Markup por Proyecto (Avanzado)
Agregar campos a Project:
```python
class Project:
    tm_hourly_rate = DecimalField(default=50)
    material_markup_pct = DecimalField(default=15)
```

---

## 🎯 Métricas de Éxito

Track estas métricas para validar el sistema:

1. **Tiempo por Factura**
   - Antes: 30-45 min
   - Meta: < 5 min

2. **Facturas Olvidadas**
   - Antes: 1-2 COs/mes sin cobrar
   - Meta: 0

3. **Cash Flow**
   - Facturar más rápido = cobrar más rápido
   - Meta: Reducir AR aging 30→60 días a 0→30 días

4. **Margen Real**
   - Antes: Descubres al final del proyecto
   - Ahora: Sabes en tiempo real

---

## 🚀 ESTO ES SOLO EL COMIENZO

Este sistema te libera de:
- ❌ Llamar empleados por tiempo en COs
- ❌ Papeleo de facturas
- ❌ Olvidar cobrar extras

Próximo: Dashboard que te muestra si estás **ganando dinero** DURANTE el proyecto, no después.

**Tu meta:** Empresa que funcione sin ti → Delegable

Este es el primer paso. 🎉
