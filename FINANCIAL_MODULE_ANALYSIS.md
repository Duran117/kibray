# ANÁLISIS Y REESTRUCTURACIÓN DEL MÓDULO FINANCIERO
## Sistema Kibray - Análisis Completo

### 📊 ESTADO ACTUAL DEL SISTEMA

#### Modelos Existentes:
1. **Invoice** (Factura)
   - Campos: invoice_number, date_issued, due_date, total_amount, is_paid, pdf, notes
   - Relaciones: project, change_orders (M2M), income (1-to-1)
   - ✅ Tiene auto-generación de número de factura
   - ✅ Crea Income automático al marcarse como pagada
   - ❌ NO tiene seguimiento de estados (enviado, aprobado, pagado)
   - ❌ NO tiene fechas de envío, aprobación, pago
   - ❌ Validación de presupuesto muy básica

2. **InvoiceLine** (Línea de Factura)
   - Campos: description, amount
   - Relaciones: invoice, time_entry, expense
   - ✅ Puede vincular gastos y time entries
   - ❌ NO tiene cantidad, unidad, precio unitario

3. **ChangeOrder** (Orden de Cambio)
   - Campos: description, date_created, status, notes, amount
   - Estados: pending, approved, sent, billed, paid
   - ✅ Tiene seguimiento de estados
   - ✅ Puede vincularse a gastos, time entries, invoices
   - ❌ NO tiene fecha de aprobación, cliente que aprobó
   - ❌ NO tiene adjuntos firmados

4. **Expense** (Gasto)
   - Campos: amount, date, category, description, receipt, invoice
   - Relaciones: project, change_order, cost_code
   - ✅ Tiene adjuntos (receipt, invoice)
   - ❌ NO tiene proveedor, método de pago, referencia
   - ❌ NO diferencia entre pagado/pendiente

5. **Income** (Ingreso)
   - Campos: amount, date, payment_method, category, description, invoice
   - Relaciones: project
   - ✅ Tiene método de pago
   - ❌ NO tiene referencia de pago (check #, transfer ID)
   - ❌ NO vincula claramente con Invoice cuando es pago parcial

#### Vistas y Flujos Actuales:
- `invoice_create`: Crea factura + líneas + vincula COs
- `invoice_edit`: Edita factura existente
- `invoice_list`: Lista facturas (básico)
- `invoice_detail`: Detalle de factura
- `invoice_pdf`: Genera PDF (NECESITA MEJORA ESTÉTICA)
- `changeorder_create`, `changeorder_detail`, `changeorder_board`
- `expense_create_view`, `income_create_view`

#### Templates Actuales:
- `invoice_list.html`: Tabla simple
- `invoice_detail.html`: Vista básica
- `invoice_form.html`: Formulario con JS para COs
- `changeorder_detail.html`, `changeorder_board.html`

---

### 🎯 PROBLEMAS IDENTIFICADOS

#### Críticos:
1. **Invoice NO tiene estados de seguimiento**
   - No se puede marcar como "Enviada", "Aprobada por cliente", "En proceso de pago"
   - No hay timestamps de cada transición

2. **PDF generado NO es profesional**
   - Layout básico sin estética
   - No tiene logo, colores corporativos, formato profesional
   - No muestra desglose claro

3. **NO hay flujo de pagos parciales**
   - Un Invoice solo puede estar "pagado" o "no pagado"
   - No se registran múltiples pagos contra una factura

4. **Expense NO diferencia pagado vs pendiente**
   - No hay campo para marcar si ya se pagó
   - No hay vinculación con pagos realizados

5. **Income NO referencia correctamente pagos**
   - Cuando se marca Invoice como pagada, crea Income genérico
   - No hay forma de registrar pago parcial o múltiples pagos

#### Moderados:
6. **ChangeOrder falta información de aprobación**
   - No guarda quién aprobó (cliente)
   - No tiene fecha de aprobación
   - No permite adjuntar documento firmado

7. **InvoiceLine muy simple**
   - No tiene qty, unit, unit_price (solo amount total)
   - Dificulta transparencia con cliente

8. **Análisis financiero inexistente**
   - No hay dashboard con métricas
   - No hay gráficos de flujo de caja
   - No hay reportes de cuentas por cobrar/pagar

---

### ✅ PLAN DE REESTRUCTURACIÓN

#### FASE 1: Mejorar modelo Invoice y seguimiento de estados
**Cambios en Invoice:**
```python
class Invoice(models.Model):
    # ... campos existentes ...
    
    # NUEVOS CAMPOS DE SEGUIMIENTO
    STATUS_CHOICES = [
        ('DRAFT', 'Draft - Not Sent'),
        ('SENT', 'Sent to Client'),
        ('APPROVED', 'Approved by Client'),
        ('PARTIALLY_PAID', 'Partially Paid'),
        ('PAID', 'Fully Paid'),
        ('OVERDUE', 'Overdue'),
        ('CANCELLED', 'Cancelled'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    
    sent_date = models.DateTimeField(null=True, blank=True)
    sent_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='sent_invoices')
    
    approved_date = models.DateTimeField(null=True, blank=True)
    approved_by_client = models.CharField(max_length=200, blank=True)  # nombre del cliente que aprobó
    
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    balance_due = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Métodos
    def update_status(self):
        # Auto-calcula estado basado en amount_paid
        if self.amount_paid == 0:
            if self.sent_date and timezone.now() > self.due_date:
                self.status = 'OVERDUE'
            elif self.sent_date:
                self.status = 'SENT'
        elif self.amount_paid >= self.total_amount:
            self.status = 'PAID'
        else:
            self.status = 'PARTIALLY_PAID'
```

**Nuevo modelo: InvoicePayment**
```python
class InvoicePayment(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateField()
    payment_method = models.CharField(max_length=50, choices=Income.PAYMENT_METHOD_CHOICES)
    reference = models.CharField(max_length=100, blank=True)  # check #, transfer ID, etc.
    notes = models.TextField(blank=True)
    income = models.OneToOneField(Income, on_delete=models.SET_NULL, null=True, blank=True)
    recorded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    recorded_at = models.DateTimeField(auto_now_add=True)
```

#### FASE 2: Mejorar modelo Expense (Cuentas por Pagar)
```python
class Expense(models.Model):
    # ... campos existentes ...
    
    # NUEVOS CAMPOS
    vendor = models.CharField(max_length=200, blank=True)  # proveedor
    payment_status = models.CharField(max_length=20, choices=[
        ('PENDING', 'Pending Payment'),
        ('PAID', 'Paid'),
        ('PARTIAL', 'Partially Paid'),
    ], default='PENDING')
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_date = models.DateField(null=True, blank=True)
    payment_method = models.CharField(max_length=50, blank=True)
    payment_reference = models.CharField(max_length=100, blank=True)
```

#### FASE 3: Mejorar ChangeOrder
```python
class ChangeOrder(models.Model):
    # ... campos existentes ...
    
    # NUEVOS CAMPOS
    approved_by_client = models.CharField(max_length=200, blank=True)
    client_approval_date = models.DateField(null=True, blank=True)
    signed_document = models.FileField(upload_to='changeorders/signed/', blank=True, null=True)
```

#### FASE 4: PDF Profesional
- Usar WeasyPrint o ReportLab para mejor diseño
- Template HTML elegante con CSS
- Logo de empresa
- Colores corporativos
- Formato profesional: encabezado, tabla clara, totales destacados, términos de pago
- Footer con información de contacto

#### FASE 5: Dashboard Financiero Interactivo
**Métricas clave:**
- Total facturado vs cobrado (este mes, trimestre, año)
- Cuentas por cobrar (aging: 0-30, 31-60, 61-90, 90+ días)
- Cuentas por pagar pendientes
- Flujo de caja proyectado
- Gráfico de ingresos vs gastos (mensual)
- Top 5 clientes por ingresos
- Top 5 categorías de gastos
- Proyectos con mejor margen

**Vistas interactivas:**
- Filtros por fecha, proyecto, cliente
- Drill-down en cada métrica
- Exportar a Excel/PDF
- Alertas de facturas vencidas

#### FASE 6: Vistas mejoradas
- `invoice_dashboard`: Dashboard principal con KPIs
- `invoice_send`: Acción para marcar como enviada + email opcional
- `invoice_record_payment`: Registrar pago (parcial o total)
- `accounts_receivable`: Reporte de cuentas por cobrar
- `accounts_payable`: Reporte de cuentas por pagar
- `expense_pay`: Marcar gasto como pagado
- `financial_report`: Reporte completo P&L, balance

---

### 📋 ORDEN DE IMPLEMENTACIÓN

**Prioridad 1 (Inmediato):**
1. ✅ Agregar campos de seguimiento a Invoice (status, dates)
2. ✅ Crear modelo InvoicePayment
3. ✅ Mejorar PDF de factura (diseño profesional)
4. ✅ Vista para registrar pagos
5. ✅ Vista para marcar factura como enviada

**Prioridad 2 (Corto plazo):**
6. ✅ Mejorar modelo Expense (payment tracking)
7. ✅ Dashboard financiero básico (KPIs principales)
8. ✅ Reporte de cuentas por cobrar
9. ✅ Mejorar ChangeOrder (aprobaciones)

**Prioridad 3 (Mediano plazo):**
10. ✅ Dashboard interactivo avanzado con gráficos
11. ✅ Reporte de cuentas por pagar
12. ✅ Alertas automáticas (facturas vencidas)
13. ✅ Exportar reportes a Excel

---

### 🚀 SIGUIENTE ACCIÓN

Comenzar con Prioridad 1, ítem 1-5:
1. Migración para agregar campos a Invoice
2. Crear modelo InvoicePayment
3. Rediseñar template PDF completamente
4. Crear vistas de seguimiento
5. Actualizar forms y templates

¿Proceder con la implementación?
