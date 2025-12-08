# REESTRUCTURACIÓN FINANCIERA - CONTRATISTA DE PINTURA
**Fecha:** 7 de Noviembre, 2025  
**Negocio:** Contratista de pintura (precio fijo SF², tiempo & materiales, extras)  
**Objetivo:** Sistema que capture TODO el dinero ganado/gastado + mantenga margen saludable

---

## 🎯 TU FLUJO DE DINERO REAL (Como Contratista)

### Cómo Trabajas Hoy:
1. **Cliente solicita trabajo** → Creas **Estimate** (presupuesto)
   - Calculas: Labor + Materiales + Markup + Overhead + Target Profit
   - Cliente aprueba → Creas **Proposal** → Cliente acepta
   
2. **Durante el trabajo** pasan cosas:
   - 🔨 **Trabajas más horas**: TimeEntry registra horas extras
   - 🎨 **Cliente pide extras**: "Pinta también esta puerta" → ChangeOrder
   - 💰 **Compras materiales**: Expense registra gastos
   - 📸 **Documentas progreso**: DailyLog, fotos de sitio
   
3. **Es hora de cobrar**:
   - ❓ **PROBLEMA HOY**: Tienes que crear Invoice manualmente copiando datos
   - ❓ No sabes cuánto has gastado vs cuánto presupuestaste
   - ❓ Cliente paga parcialmente → No tienes forma de rastrear

4. **Proyecto termina**:
   - ❓ **PREGUNTA CRÍTICA**: ¿Gané dinero? ¿Cuánto fue mi margen real?
   - ❓ ¿Estimé bien? ¿Dónde me pasé de presupuesto?

---

## 🚨 PROBLEMAS CRÍTICOS IDENTIFICADOS

### 1. ESTIMADO → FACTURA: SIN PUENTE
**Qué pasa hoy:**
- Tienes Estimate aprobado con breakdown detallado (labor, materials, markup)
- Tienes ChangeOrders aprobados con montos adicionales
- Pero crear Invoice es empezar de CERO: copiar/pegar manualmente

**Qué necesitas:**
```
[Estimate v2 APROBADO]  ──┐
[ChangeOrder #5 BILLED]  ──┼──► [BOTÓN: "Create Invoice from..."]  ──► [Invoice pre-poblada]
[TimeEntry últimos 30d]  ──┘
```

**Impacto:** 
- ⏱️ Pierdes 30-45 min por factura haciendo data entry
- ❌ Riesgo de olvidar cobrar ChangeOrders aprobados
- 📉 Facturas retrasadas = cash flow retrasado

---

### 2. MARGEN REAL: INVISIBLE HASTA EL FINAL
**Qué pasa hoy:**
- Estimate dice: "Target profit: 15%"
- Durante proyecto: gastas en materiales (Expense), pagas labor (TimeEntry)
- ❓ Pero NO SABES si aún vas a ganar 15% hasta que termines

**Qué necesitas:**
- **Dashboard de margen en tiempo real:**
  ```
  PROYECTO: Casa Johnson
  ┌─────────────────────────────────────────┐
  │ PRESUPUESTO (Estimate + COs)            │
  │   Labor:      $5,000  (100 hrs @ $50)   │
  │   Materials:  $3,000                    │
  │   Markup:     $1,200  (15%)             │
  │   Total:      $9,200                    │
  ├─────────────────────────────────────────┤
  │ REAL (Actual Costs)                     │
  │   Labor:      $5,500  (110 hrs @ $50) ⚠️│
  │   Materials:  $3,200  ⚠️                 │
  │   Total:      $8,700                    │
  ├─────────────────────────────────────────┤
  │ MARGEN: $500 (5.4%) ❌ ALERTA: -9.6%    │
  └─────────────────────────────────────────┘
  ```

**Impacto:**
- 🔴 Descubres que perdiste dinero DESPUÉS de terminar
- 📉 No puedes ajustar durante el trabajo
- 💸 Proyectos no rentables destruyen tu negocio

---

### 3. PAGOS PARCIALES: NO RASTREADOS
**Qué pasa hoy:**
- Facturas $10,000
- Cliente paga $3,000 inicial
- Luego $4,000 más
- Luego final $3,000
- Tu sistema solo sabe: `is_paid = True/False` ❌

**Qué necesitas:**
```
INVOICE #1234 - $10,000
├─ Pago 1: $3,000  (15-Oct-2025, Check #5501)
├─ Pago 2: $4,000  (30-Oct-2025, Transfer #TX889)
├─ Pago 3: $3,000  (10-Nov-2025, Check #5523) ✅
└─ TOTAL PAGADO: $10,000 / $10,000 (100%)
```

**Impacto:**
- 📊 No sabes cuánto REALMENTE tienes por cobrar (AR aging)
- 💰 Cash flow planning imposible
- 📞 Confusión con cliente sobre pagos

---

### 4. GASTOS: SIN TRACKING DE PROVEEDOR/PAGO
**Qué pasa hoy:**
- Compras pintura en Sherwin-Williams: $450
- Creas Expense con monto
- ❓ Pero no guardas: vendor, método de pago, si ya pagaste

**Qué necesitas:**
```
EXPENSE #789
├─ Vendor: Sherwin-Williams
├─ Amount: $450.00
├─ Status: PAID ✅
├─ Payment Date: 2025-11-01
├─ Payment Method: Company Credit Card
└─ Payment Reference: Card ending 4532
```

**Impacto:**
- 📉 No sabes cuánto debes (AP aging)
- 🏦 Reconciliación bancaria difícil
- 💳 No rastreas gastos por vendor para negociar descuentos

---

### 5. PDF FACTURA: NO PROFESIONAL
**Qué pasa hoy:**
- PDF básico generado con ReportLab
- Sin logo, sin branding
- Layout poco profesional

**Qué necesitas:**
```
┌───────────────────────────────────────────┐
│  [TU LOGO]              INVOICE #1234     │
│  Kibray Painting LLC     Date: Nov 7, 2025│
│  (555) 123-4567                           │
├───────────────────────────────────────────┤
│  BILL TO:                                 │
│  Casa Johnson                             │
│  123 Main St, Seattle WA                  │
├───────────────────────────────────────────┤
│  DESCRIPTION          QTY    RATE   AMOUNT│
│  Interior Painting    500SF  $2.50  $1,250│
│  Exterior Touch-up    100SF  $3.00    $300│
│  Change Order #5              ...     $450│
│                                       ─────│
│  SUBTOTAL:                          $2,000│
│  TAX (10%):                           $200│
│  TOTAL:                             $2,200│
├───────────────────────────────────────────┤
│  Payment Terms: Net 30                    │
│  Thank you for your business!             │
└───────────────────────────────────────────┘
```

**Impacto:**
- 😬 Clientes ven factura poco profesional
- 📄 Dificulta cobro (no inspira confianza)
- 🏆 No refleja tu calidad de trabajo

---

### 6. CHANGE ORDERS: NO FLUYEN A FACTURA
**Qué pasa hoy:**
- ChangeOrder status: `pending → approved → sent → billed → paid`
- Pero cuando creas Invoice, no hay lista de "COs listos para facturar"
- Tienes que recordar/buscar cuáles están en estado `sent` o `approved`

**Qué necesitas:**
```
CREAR FACTURA - Casa Johnson
┌───────────────────────────────────────────┐
│ ✅ INCLUIR EN FACTURA:                    │
├───────────────────────────────────────────┤
│ □ Estimate v2 (Base Contract)   $8,000   │
│ □ Change Order #5 [approved]      $450   │
│ □ Change Order #7 [sent]          $320   │
│ □ Time & Materials (Oct 1-31)     $890   │
├───────────────────────────────────────────┤
│ [Generate Invoice] → Total: $9,660        │
└───────────────────────────────────────────┘
```

**Impacto:**
- ❌ Olvidas cobrar COs aprobados
- 💸 Pierdes dinero que ya trabajaste
- ⏱️ Tiempo extra rastreando qué falta facturar

---

## 💡 SOLUCIÓN PROPUESTA (3 FASES)

### 🚀 FASE 1: INVOICE INTELIGENTE (Prioritario - 1 semana)

#### 1.1 Modelo InvoicePayment (Pagos Parciales)
```python
class InvoicePayment(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateField()
    payment_method = models.CharField(max_length=50, choices=PAYMENT_METHOD_CHOICES)
    reference = models.CharField(max_length=100, blank=True)  # Check #, Transfer ID
    notes = models.TextField(blank=True)
    recorded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    recorded_at = models.DateTimeField(auto_now_add=True)
    
    # Link opcional a Income si quieres auto-crear Income por pago
    income = models.OneToOneField('Income', on_delete=models.SET_NULL, null=True, blank=True)
```

#### 1.2 Campos Adicionales en Invoice
```python
class Invoice(models.Model):
    # ... campos existentes ...
    
    # Status tracking
    STATUS_CHOICES = [
        ('DRAFT', 'Borrador'),
        ('SENT', 'Enviada'),
        ('VIEWED', 'Vista por Cliente'),
        ('APPROVED', 'Aprobada'),
        ('PARTIAL', 'Pago Parcial'),
        ('PAID', 'Pagada Completa'),
        ('OVERDUE', 'Vencida'),
        ('CANCELLED', 'Cancelada'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    
    # Timestamps
    sent_date = models.DateTimeField(null=True, blank=True)
    viewed_date = models.DateTimeField(null=True, blank=True)
    approved_date = models.DateTimeField(null=True, blank=True)
    paid_date = models.DateTimeField(null=True, blank=True)
    
    # Sent by
    sent_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='invoices_sent')
    
    # Payment tracking
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    @property
    def balance_due(self):
        return self.total_amount - self.amount_paid
    
    @property
    def payment_progress(self):
        if self.total_amount == 0:
            return 0
        return (self.amount_paid / self.total_amount) * 100
    
    def update_status(self):
        """Auto-update status based on payments and dates"""
        if self.balance_due <= 0:
            self.status = 'PAID'
            if not self.paid_date:
                self.paid_date = timezone.now()
        elif self.amount_paid > 0:
            self.status = 'PARTIAL'
        elif self.due_date and timezone.now().date() > self.due_date and self.balance_due > 0:
            self.status = 'OVERDUE'
        # ... etc
        self.save()
```

#### 1.3 Vista: Invoice Builder (Smart Creation)
```python
@login_required
@staff_required
def invoice_builder_view(request, project_id):
    """
    Smart invoice creation:
    - Pre-load approved Estimate
    - Show available ChangeOrders (approved/sent, not yet billed)
    - Show unbilled TimeEntries
    - Show unbilled Expenses (markupable)
    - Generate InvoiceLines automatically
    """
    project = get_object_or_404(Project, pk=project_id)
    
    # Get data sources
    latest_estimate = project.estimates.filter(approved=True).order_by('-version').first()
    unbilled_cos = project.changeorders.filter(status__in=['approved', 'sent']).exclude(invoices__isnull=False)
    unbilled_time = TimeEntry.objects.filter(project=project, invoiceline__isnull=True)
    unbilled_expenses = Expense.objects.filter(project=project, invoiceline__isnull=True, category='MATERIALES')
    
    if request.method == 'POST':
        # User selects what to include
        include_estimate = request.POST.get('include_estimate') == 'on'
        selected_co_ids = request.POST.getlist('change_orders')
        include_time = request.POST.get('include_time') == 'on'
        include_expenses = request.POST.get('include_expenses') == 'on'
        
        # Create Invoice
        invoice = Invoice.objects.create(
            project=project,
            date_issued=timezone.now().date(),
            due_date=timezone.now().date() + timedelta(days=30),
            status='DRAFT',
        )
        
        # Add lines
        if include_estimate and latest_estimate:
            # Calculate total from EstimateLines
            direct_cost = sum(line.direct_cost() for line in latest_estimate.lines.all())
            markup = direct_cost * (latest_estimate.markup_material + latest_estimate.markup_labor) / 100
            overhead = direct_cost * latest_estimate.overhead_pct / 100
            profit = direct_cost * latest_estimate.target_profit_pct / 100
            total = direct_cost + markup + overhead + profit
            
            InvoiceLine.objects.create(
                invoice=invoice,
                description=f"Contrato Base - Estimate v{latest_estimate.version}",
                amount=total,
            )
        
        # Add ChangeOrders
        for co_id in selected_co_ids:
            co = ChangeOrder.objects.get(pk=co_id)
            InvoiceLine.objects.create(
                invoice=invoice,
                description=f"Change Order #{co.id}: {co.description[:100]}",
                amount=co.amount,
            )
            co.status = 'billed'
            co.save()
            invoice.change_orders.add(co)
        
        # Add Time & Materials (with markup)
        if include_time:
            time_total = sum(te.labor_cost for te in unbilled_time)
            if time_total > 0:
                markup_pct = latest_estimate.markup_labor if latest_estimate else 20
                marked_up = time_total * (1 + markup_pct / 100)
                InvoiceLine.objects.create(
                    invoice=invoice,
                    description="Time & Materials (Labor)",
                    amount=marked_up,
                )
                # Link time entries
                for te in unbilled_time:
                    line = InvoiceLine.objects.create(
                        invoice=invoice,
                        description=f"  - {te.employee.name}: {te.hours_worked}hrs",
                        amount=0,  # Already in total above
                        time_entry=te,
                    )
        
        # Calculate total
        invoice.total_amount = sum(line.amount for line in invoice.lines.all())
        invoice.save()
        
        messages.success(request, f"Invoice #{invoice.invoice_number} created!")
        return redirect('invoice_detail', invoice_id=invoice.id)
    
    context = {
        'project': project,
        'estimate': latest_estimate,
        'unbilled_cos': unbilled_cos,
        'unbilled_time': unbilled_time,
        'unbilled_expenses': unbilled_expenses,
    }
    return render(request, 'core/invoice_builder.html', context)
```

#### 1.4 Vista: Record Payment
```python
@login_required
@staff_required
def invoice_record_payment_view(request, invoice_id):
    invoice = get_object_or_404(Invoice, pk=invoice_id)
    
    if request.method == 'POST':
        amount = Decimal(request.POST.get('amount', 0))
        payment_date = request.POST.get('payment_date')
        payment_method = request.POST.get('payment_method')
        reference = request.POST.get('reference', '')
        notes = request.POST.get('notes', '')
        
        # Create payment record
        payment = InvoicePayment.objects.create(
            invoice=invoice,
            amount=amount,
            payment_date=payment_date,
            payment_method=payment_method,
            reference=reference,
            notes=notes,
            recorded_by=request.user,
        )
        
        # Update invoice
        invoice.amount_paid += amount
        invoice.update_status()
        
        # Auto-create Income (optional)
        Income.objects.create(
            project=invoice.project,
            amount=amount,
            date=payment_date,
            payment_method=payment_method,
            category='PAYMENT',
            description=f"Payment for Invoice #{invoice.invoice_number}",
            invoice=invoice,
        )
        
        messages.success(request, f"Payment of ${amount} recorded!")
        return redirect('invoice_detail', invoice_id=invoice.id)
    
    return render(request, 'core/invoice_record_payment.html', {'invoice': invoice})
```

---

### 📊 FASE 2: DASHBOARD FINANCIERO (2 semanas)

#### 2.1 Vista: Project Profit Dashboard
```python
@login_required
@staff_required
def project_profit_dashboard(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    
    # BUDGETED (from Estimate + ChangeOrders)
    latest_estimate = project.estimates.filter(approved=True).order_by('-version').first()
    if latest_estimate:
        budgeted_revenue = sum(line.direct_cost() for line in latest_estimate.lines.all())
        budgeted_revenue *= (1 + latest_estimate.markup_material/100 + latest_estimate.markup_labor/100)
        budgeted_revenue += budgeted_revenue * latest_estimate.overhead_pct / 100
        budgeted_revenue += budgeted_revenue * latest_estimate.target_profit_pct / 100
    else:
        budgeted_revenue = 0
    
    # Add approved ChangeOrders
    approved_cos = project.changeorders.filter(status__in=['approved', 'sent', 'billed'])
    budgeted_revenue += sum(co.amount for co in approved_cos)
    
    # ACTUAL COSTS
    labor_cost = sum(te.labor_cost for te in project.timeentries.all())
    material_cost = sum(
        e.amount for e in project.expenses.filter(category='MATERIALES')
    )
    other_cost = sum(
        e.amount for e in project.expenses.exclude(category='MATERIALES')
    )
    total_cost = labor_cost + material_cost + other_cost
    
    # BILLED (from Invoices)
    total_billed = sum(inv.total_amount for inv in project.invoices.all())
    total_collected = sum(inv.amount_paid for inv in project.invoices.all())
    
    # PROFIT METRICS
    estimated_profit = budgeted_revenue - total_cost
    estimated_margin = (estimated_profit / budgeted_revenue * 100) if budgeted_revenue > 0 else 0
    
    actual_profit = total_collected - total_cost
    actual_margin = (actual_profit / total_collected * 100) if total_collected > 0 else 0
    
    # VARIANCE
    revenue_variance = budgeted_revenue - total_billed
    cost_variance = total_cost  # Over budget if positive
    
    # ALERTS
    alerts = []
    if actual_margin < 10:
        alerts.append({'level': 'danger', 'message': f'Margen muy bajo: {actual_margin:.1f}%'})
    if labor_cost > budgeted_revenue * 0.6:
        alerts.append({'level': 'warning', 'message': 'Labor cost > 60% de revenue'})
    if revenue_variance > 0:
        alerts.append({'level': 'info', 'message': f'${revenue_variance:.0f} aún sin facturar'})
    
    context = {
        'project': project,
        'budgeted_revenue': budgeted_revenue,
        'labor_cost': labor_cost,
        'material_cost': material_cost,
        'other_cost': other_cost,
        'total_cost': total_cost,
        'total_billed': total_billed,
        'total_collected': total_collected,
        'estimated_profit': estimated_profit,
        'estimated_margin': estimated_margin,
        'actual_profit': actual_profit,
        'actual_margin': actual_margin,
        'alerts': alerts,
    }
    return render(request, 'core/project_profit_dashboard.html', context)
```

#### 2.2 Template: Dashboard con Charts
```html
<!-- project_profit_dashboard.html -->
<div class="row">
  <div class="col-md-4">
    <div class="card">
      <div class="card-body">
        <h5>Revenue</h5>
        <p class="display-6">${{ budgeted_revenue|floatformat:0 }}</p>
        <small>Budgeted</small>
      </div>
    </div>
  </div>
  <div class="col-md-4">
    <div class="card">
      <div class="card-body">
        <h5>Costs</h5>
        <p class="display-6">${{ total_cost|floatformat:0 }}</p>
        <small>Labor: ${{ labor_cost|floatformat:0 }} | Materials: ${{ material_cost|floatformat:0 }}</small>
      </div>
    </div>
  </div>
  <div class="col-md-4">
    <div class="card {% if actual_margin < 10 %}bg-danger text-white{% endif %}">
      <div class="card-body">
        <h5>Profit Margin</h5>
        <p class="display-6">{{ actual_margin|floatformat:1 }}%</p>
        <small>Target: {{ estimate.target_profit_pct }}%</small>
      </div>
    </div>
  </div>
</div>

<!-- Cost Breakdown Chart (Chart.js) -->
<canvas id="costChart"></canvas>
<script>
const ctx = document.getElementById('costChart').getContext('2d');
new Chart(ctx, {
    type: 'doughnut',
    data: {
        labels: ['Labor', 'Materials', 'Other'],
        datasets: [{
            data: [{{ labor_cost }}, {{ material_cost }}, {{ other_cost }}],
            backgroundColor: ['#FF6384', '#36A2EB', '#FFCE56']
        }]
    }
});
</script>

<!-- Alerts -->
{% for alert in alerts %}
<div class="alert alert-{{ alert.level }}">{{ alert.message }}</div>
{% endfor %}
```

---

### 🎨 FASE 3: PDF PROFESIONAL (1 semana)

#### 3.1 Template HTML con WeasyPrint
```html
<!-- invoice_pdf_template.html -->
<!DOCTYPE html>
<html>
<head>
<style>
@page {
    size: letter;
    margin: 1in;
}
body {
    font-family: 'Helvetica', sans-serif;
    color: #333;
}
.header {
    display: flex;
    justify-content: space-between;
    margin-bottom: 30px;
}
.logo {
    width: 150px;
}
.invoice-info {
    text-align: right;
}
.invoice-number {
    font-size: 24px;
    font-weight: bold;
    color: #2c3e50;
}
table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 20px;
}
th {
    background-color: #3498db;
    color: white;
    padding: 10px;
    text-align: left;
}
td {
    padding: 10px;
    border-bottom: 1px solid #ddd;
}
.total-row {
    font-weight: bold;
    font-size: 18px;
    background-color: #ecf0f1;
}
.footer {
    margin-top: 50px;
    border-top: 2px solid #3498db;
    padding-top: 20px;
    text-align: center;
    color: #7f8c8d;
}
</style>
</head>
<body>
<div class="header">
    <div class="company">
        <img src="{{ logo_url }}" class="logo" alt="Logo">
        <h2>Kibray Painting LLC</h2>
        <p>123 Main St, Seattle WA 98101</p>
        <p>Phone: (555) 123-4567</p>
        <p>License #: WA-123456</p>
    </div>
    <div class="invoice-info">
        <p class="invoice-number">INVOICE #{{ invoice.invoice_number }}</p>
        <p>Date: {{ invoice.date_issued|date:"M d, Y" }}</p>
        <p>Due Date: {{ invoice.due_date|date:"M d, Y" }}</p>
    </div>
</div>

<div class="bill-to">
    <h3>BILL TO:</h3>
    <p><strong>{{ invoice.project.name }}</strong></p>
    <p>{{ invoice.project.address }}</p>
</div>

<table>
    <thead>
        <tr>
            <th>DESCRIPTION</th>
            <th style="text-align: right;">AMOUNT</th>
        </tr>
    </thead>
    <tbody>
        {% for line in invoice.lines.all %}
        <tr>
            <td>{{ line.description }}</td>
            <td style="text-align: right;">${{ line.amount|floatformat:2 }}</td>
        </tr>
        {% endfor %}
    </tbody>
    <tfoot>
        <tr>
            <td style="text-align: right;"><strong>SUBTOTAL:</strong></td>
            <td style="text-align: right;">${{ invoice.total_amount|floatformat:2 }}</td>
        </tr>
        <tr>
            <td style="text-align: right;"><strong>TAX ({{ tax_rate }}%):</strong></td>
            <td style="text-align: right;">${{ tax_amount|floatformat:2 }}</td>
        </tr>
        <tr class="total-row">
            <td style="text-align: right;">TOTAL DUE:</td>
            <td style="text-align: right;">${{ total_with_tax|floatformat:2 }}</td>
        </tr>
    </tfoot>
</table>

<div class="payment-info" style="margin-top: 30px;">
    <h4>PAYMENT INFORMATION:</h4>
    <p>Please make checks payable to: <strong>Kibray Painting LLC</strong></p>
    <p>Or pay online: <a href="{{ payment_link }}">{{ payment_link }}</a></p>
</div>

<div class="footer">
    <p>Thank you for your business!</p>
    <p>Questions? Email: billing@kibraypaint.com</p>
</div>
</body>
</html>
```

#### 3.2 Vista PDF Mejorada
```python
from weasyprint import HTML
from django.template.loader import render_to_string

@login_required
def invoice_pdf_view(request, invoice_id):
    invoice = get_object_or_404(Invoice, pk=invoice_id)
    
    # Calculate tax (optional)
    tax_rate = 10.0  # 10% sales tax (adjust per state)
    tax_amount = invoice.total_amount * (tax_rate / 100)
    total_with_tax = invoice.total_amount + tax_amount
    
    # Render HTML template
    html_string = render_to_string('core/invoice_pdf_template.html', {
        'invoice': invoice,
        'logo_url': request.build_absolute_uri(settings.STATIC_URL + 'logo.png'),
        'tax_rate': tax_rate,
        'tax_amount': tax_amount,
        'total_with_tax': total_with_tax,
        'payment_link': request.build_absolute_uri(f'/pay/{invoice.id}/'),
    })
    
    # Generate PDF
    html = HTML(string=html_string, base_url=request.build_absolute_uri('/'))
    pdf = html.write_pdf()
    
    # Return as download
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Invoice_{invoice.invoice_number}.pdf"'
    return response
```

---

## 🔥 FEATURES AVANZADOS (Fase 4+)

### 1. Cash Flow Forecast
```python
def cash_flow_forecast(months=3):
    """
    Predice flujo de efectivo próximos 3 meses basado en:
    - Invoices pendientes de cobro (expected payment dates)
    - Expenses recurrentes (vendor bills)
    - Payroll schedule
    """
    forecast = []
    for month in range(1, months+1):
        target_date = timezone.now().date() + timedelta(days=30*month)
        
        expected_income = Invoice.objects.filter(
            status__in=['SENT', 'PARTIAL'],
            due_date__lte=target_date
        ).aggregate(total=Sum('balance_due'))['total'] or 0
        
        expected_expenses = Expense.objects.filter(
            payment_status='PENDING',
            # Assuming recurring expenses
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        forecast.append({
            'month': target_date.strftime('%B %Y'),
            'income': expected_income,
            'expenses': expected_expenses,
            'net': expected_income - expected_expenses,
        })
    
    return forecast
```

### 2. Vendor Management (para Expenses)
```python
class Vendor(models.Model):
    name = models.CharField(max_length=200)
    contact_name = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    payment_terms = models.CharField(max_length=50, default='Net 30')
    account_number = models.CharField(max_length=50, blank=True)  # Your account # with them
    notes = models.TextField(blank=True)
    
    @property
    def total_spent(self):
        return self.expenses.aggregate(total=Sum('amount'))['total'] or 0
    
    @property
    def outstanding_balance(self):
        return self.expenses.filter(payment_status='PENDING').aggregate(total=Sum('amount'))['total'] or 0
```

### 3. Expense Payment Tracking
```python
class Expense(models.Model):
    # ... existing fields ...
    
    # NEW FIELDS
    vendor = models.ForeignKey(Vendor, on_delete=models.SET_NULL, null=True, blank=True, related_name='expenses')
    
    PAYMENT_STATUS_CHOICES = [
        ('PENDING', 'Pendiente'),
        ('PAID', 'Pagado'),
        ('PARTIAL', 'Pago Parcial'),
    ]
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='PENDING')
    
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_date = models.DateField(null=True, blank=True)
    payment_method = models.CharField(max_length=50, blank=True)
    payment_reference = models.CharField(max_length=100, blank=True)  # Check #, etc
    
    @property
    def balance_due(self):
        return self.amount - self.amount_paid
```

### 4. Aging Reports (AR & AP)
```python
@login_required
@staff_required
def accounts_receivable_aging(request):
    """
    Report de facturas por cobrar agrupadas por antigüedad:
    - Current (0-30 days)
    - 31-60 days
    - 61-90 days
    - 90+ days (CRITICAL)
    """
    today = timezone.now().date()
    
    invoices = Invoice.objects.filter(status__in=['SENT', 'PARTIAL', 'OVERDUE'])
    
    aging_buckets = {
        'current': [],      # 0-30 days
        '31_60': [],
        '61_90': [],
        'over_90': [],
    }
    
    for inv in invoices:
        days_old = (today - inv.date_issued).days
        if days_old <= 30:
            aging_buckets['current'].append(inv)
        elif days_old <= 60:
            aging_buckets['31_60'].append(inv)
        elif days_old <= 90:
            aging_buckets['61_90'].append(inv)
        else:
            aging_buckets['over_90'].append(inv)
    
    totals = {
        bucket: sum(inv.balance_due for inv in invoices)
        for bucket, invoices in aging_buckets.items()
    }
    
    return render(request, 'core/ar_aging.html', {
        'aging_buckets': aging_buckets,
        'totals': totals,
    })
```

---

## 📋 IMPLEMENTATION ROADMAP

### WEEK 1: Invoice Improvements
- [ ] Crear modelo `InvoicePayment`
- [ ] Agregar campos de status/timestamps a `Invoice`
- [ ] Migración de datos (set default status)
- [ ] Vista `invoice_record_payment`
- [ ] Template para registrar pagos
- [ ] Actualizar `invoice_detail` para mostrar pagos

### WEEK 2: Invoice Builder
- [ ] Vista `invoice_builder` (smart creation)
- [ ] Template con checkboxes para Estimate/COs/Time
- [ ] Lógica de auto-cálculo de markup en T&M
- [ ] Botón "Mark as Sent" en invoice detail
- [ ] Email notification cuando invoice enviada (opcional)

### WEEK 3: Project Profit Dashboard
- [ ] Vista `project_profit_dashboard`
- [ ] Template con cards de metrics
- [ ] Integrar Chart.js para gráficos
- [ ] Alerts automáticos (low margin, over budget)
- [ ] Link en project detail page

### WEEK 4: Professional PDF
- [ ] Instalar WeasyPrint (`pip install weasyprint`)
- [ ] Crear `invoice_pdf_template.html` con branding
- [ ] Subir logo a static files
- [ ] Actualizar `invoice_pdf_view` para usar WeasyPrint
- [ ] Agregar tax calculation (configurable por estado)
- [ ] Botón "Download PDF" en invoice detail

### WEEK 5-6: Vendor & Expense Tracking
- [ ] Crear modelo `Vendor`
- [ ] Agregar campos payment tracking a `Expense`
- [ ] Vista `vendor_list` y `vendor_detail`
- [ ] Vista `expense_record_payment`
- [ ] Template accounts payable dashboard

### WEEK 7-8: Aging Reports & Analytics
- [ ] Vista `accounts_receivable_aging`
- [ ] Vista `accounts_payable_aging`
- [ ] Template con tables por aging bucket
- [ ] Vista `cash_flow_forecast`
- [ ] Template con chart de proyección 3 meses

---

## 🎯 KPIs A RASTREAR

### Por Proyecto:
1. **Gross Profit Margin** = (Revenue - Costs) / Revenue
   - Target: 15-25% (típico para painting contractors)
   - Alert si < 10%

2. **Labor Efficiency** = Actual Hours / Budgeted Hours
   - Target: ≤ 100%
   - Alert si > 110%

3. **Material Waste** = Actual Material Cost / Budgeted Material Cost
   - Target: ≤ 105%
   - Alert si > 110%

4. **Change Order Ratio** = CO Revenue / Base Contract Revenue
   - Insight: Si > 20%, significa mucho cambio de scope

5. **Invoice Collection Time** = Days from invoice sent → paid
   - Target: < 30 days
   - Alert si > 45 days

### Por Negocio (Global):
1. **Monthly Revenue** (rolling 12 months)
2. **Outstanding AR** (cuentas por cobrar)
3. **Outstanding AP** (cuentas por pagar)
4. **Cash Position** = Bank Balance + AR - AP
5. **Win Rate** = Estimates accepted / Estimates sent

---

## 💬 PRÓXIMOS PASOS - DECISIONES NECESARIAS

### 1. Pricing Strategy (para markup):
**Pregunta:** ¿Cómo calculas markup hoy en T&M?
- Opción A: Fixed % (e.g., 20% on labor, 15% on materials)
- Opción B: Variable por cliente/proyecto
- Opción C: Cost-plus con overhead allocation

**Recomendación:** Fixed % configurable por proyecto

---

### 2. Tax Handling:
**Pregunta:** ¿Cobras sales tax en facturas?
- Si SÍ: ¿Qué rate? (varía por estado/ciudad)
- ¿Algunos clientes están tax-exempt?

**Recomendación:** Campo `tax_rate` en Project (default 10%, editable)

---

### 3. Payment Terms:
**Pregunta:** ¿Qué términos usas?
- Net 30 (pago en 30 días)
- Net 15
- Progress payments (30% upfront, 40% midpoint, 30% completion)
- Due on receipt

**Recomendación:** Campo `payment_terms` en Invoice con templates comunes

---

### 4. Retainage (Retención):
**Pregunta:** ¿Clientes retienen % hasta final? (común en construcción)
- Example: Retain 10% until punch list complete

**Recomendación:** Campo `retainage_pct` en Invoice, auto-calcular retainage amount

---

### 5. Deposits/Upfront Payments:
**Pregunta:** ¿Pides depósito antes de empezar?
- Example: 30% upfront, rest on completion

**Recomendación:** Invoice con type='DEPOSIT', luego PROGRESS, luego FINAL

---

## 🚀 EMPECEMOS - PRIORIDAD 1

Basado en tu necesidad urgente, sugiero empezar con:

### Sprint 1 (Esta semana):
1. ✅ **InvoicePayment model** - para rastrear pagos parciales
2. ✅ **Invoice status fields** - DRAFT/SENT/PAID/etc
3. ✅ **Record payment view** - botón simple "Add Payment"
4. ✅ **Update invoice_detail template** - mostrar payments table

**Output:** Podrás ver exactamente cuánto has cobrado de cada factura

### Sprint 2 (Próxima semana):
1. ✅ **Invoice Builder view** - crear factura desde Estimate + COs
2. ✅ **Smart InvoiceLine generation** - auto-populate desde data sources
3. ✅ **Professional PDF template** (básico con WeasyPrint)

**Output:** Crear facturas tomará 2 minutos en vez de 30

### Sprint 3 (Semana 3):
1. ✅ **Project Profit Dashboard** - ver margen real time
2. ✅ **Alerts for low margin** - email si profit < 10%
3. ✅ **Cost breakdown charts** - visualizar dónde va el dinero

**Output:** Sabrás si estás ganando dinero ANTES de terminar proyecto

---

## 📞 PREGUNTAS PARA TI

Antes de empezar a codificar, necesito que me respondas:

1. **¿Cuál es tu mayor pain point hoy?**
   - A) Crear facturas toma mucho tiempo
   - B) No sé si estoy ganando dinero
   - C) Clientes no pagan a tiempo
   - D) No sé cuánto debo a vendors

2. **¿Cómo cobras mayormente?**
   - A) Precio fijo por SF² (cuánto markup usas?)
   - B) Tiempo & Material (qué rate cobras? hourly rate + markup?)
   - C) Lump sum por proyecto completo
   - D) Mix de los anteriores

3. **¿Tienes estructura de pricing clara?**
   - Labor rate: $__/hour
   - Material markup: ___%
   - Overhead: ___% 
   - Target profit: ___%

4. **¿Qué te gustaría ver en un dashboard?**
   - Revenue este mes vs último mes
   - Profit margin por proyecto
   - Top 5 clientes por revenue
   - Cuentas por cobrar aging
   - Otros?

---

**RESPONDE ESTAS PREGUNTAS Y EMPEZAMOS A CODIFICAR HOY MISMO** 🎯
