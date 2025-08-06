from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from datetime import datetime, timedelta
from django.core.exceptions import ValidationError
from django import forms  # <-- Importa forms aquí

# ---------------------
# Modelo de Empleado
# ---------------------
class Employee(models.Model):
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True)  # <-- AGREGA ESTA LÍNEA
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    social_security_number = models.CharField(max_length=20, unique=True)
    hourly_rate = models.DecimalField(max_digits=7, decimal_places=2)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    is_active = models.BooleanField(default=True)
    hire_date = models.DateField(null=True, blank=True)
    position = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    document = models.FileField(upload_to='employees/documents/', blank=True, null=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

# ---------------------
# Modelo de Proyecto
# ---------------------
class Project(models.Model):
    name = models.CharField(max_length=100)
    client = models.CharField(max_length=100, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    paint_colors = models.TextField(blank=True, help_text="Ejemplo: SW 7008 Alabaster, SW 6258 Tricorn Black")
    paint_codes = models.TextField(blank=True, help_text="Códigos de pintura si son diferentes de los colores comunes")
    stains_or_finishes = models.TextField(blank=True, help_text="Ejemplo: Milesi Butternut 072 - 2 coats")
    number_of_rooms_or_areas = models.IntegerField(blank=True, null=True)
    number_of_paint_defects = models.IntegerField(blank=True, null=True, help_text="Número de manchas o imperfecciones detectadas")
    total_income = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_expenses = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    reflection_notes = models.TextField(blank=True, help_text="Notas sobre aprendizajes, errores o mejoras para próximos proyectos")
    created_at = models.DateTimeField(auto_now_add=True)
    # Presupuesto
    budget_total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Presupuesto total asignado al proyecto")
    budget_labor = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Presupuesto para mano de obra")
    budget_materials = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Presupuesto para materiales")
    budget_other = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Presupuesto para otros gastos (seguros, almacenamiento, etc.)")

    def profit(self):
        return round(self.total_income - self.total_expenses, 2)

    @property
    def budget_remaining(self):
        return round(self.budget_total - self.total_expenses, 2)

    def __str__(self):
        return self.name

# ---------------------
# Modelo de Ingreso
# ---------------------
class Income(models.Model):
    project = models.ForeignKey(Project, related_name="incomes", on_delete=models.CASCADE)
    project_name = models.CharField(max_length=255, verbose_name="Nombre del proyecto o factura")
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Cantidad recibida")
    date = models.DateField(verbose_name="Fecha de ingreso")
    payment_method = models.CharField(
        max_length=50,
        choices=[
            ("EFECTIVO", "Efectivo"),
            ("TRANSFERENCIA", "Transferencia"),
            ("CHEQUE", "Cheque"),
            ("ZELLE", "Zelle"),
            ("OTRO", "Otro")
        ],
        verbose_name="Método de pago"
    )
    category = models.CharField(max_length=100, blank=True, null=True, verbose_name="Categoría (opcional)")
    description = models.TextField(blank=True, null=True, verbose_name="Descripción (opcional)")
    invoice = models.FileField(upload_to="incomes/", blank=True, null=True, verbose_name="Factura o comprobante")
    notes = models.TextField(blank=True, null=True, verbose_name="Notas (opcional)")

    def __str__(self):
        return f"{self.project_name} - ${self.amount}"

# ---------------------
# Modelo de Gasto
# ---------------------
class Expense(models.Model):
    project = models.ForeignKey(Project, related_name="expenses", on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    project_name = models.CharField(max_length=255)
    date = models.DateField()
    category = models.CharField(
        max_length=50,
        choices=[
            ("MATERIALES", "Materiales"),
            ("COMIDA", "Comida"),
            ("SEGURO", "Seguro"),
            ("ALMACÉN", "Storage"),
            ("MANO_OBRA", "Mano de obra"),
            ("OFICINA", "Oficina"),
            ("OTRO", "Otro"),
        ]
    )
    description = models.TextField(blank=True, null=True)
    receipt = models.FileField(upload_to="expenses/receipts/", blank=True, null=True)
    invoice = models.FileField(upload_to="expenses/invoices/", blank=True, null=True)
    change_order = models.ForeignKey('ChangeOrder', on_delete=models.SET_NULL, null=True, blank=True, related_name='expenses')

    def __str__(self):
        return f"{self.project_name} - {self.category} - ${self.amount}"

# ---------------------
# Modelo de Registro de Horas
# ---------------------
class TimeEntry(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, blank=True, null=True)
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    hours_worked = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    change_order = models.ForeignKey(
        'ChangeOrder',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='time_entries'
    )
    notes = models.TextField(blank=True, null=True)

    @property
    def labor_cost(self):
        if self.hours_worked is not None and self.employee and self.employee.hourly_rate is not None:
            return round(self.hours_worked * self.employee.hourly_rate, 2)
        return 0

    def save(self, *args, **kwargs):
        if self.start_time and self.end_time:
            start_minutes = self.start_time.hour * 60 + self.start_time.minute
            end_minutes = self.end_time.hour * 60 + self.end_time.minute
            diff = end_minutes - start_minutes
            hours = diff / 60
            if end_minutes > (12 * 60 + 30):
                hours -= 0.5
            if hours < 0:
                hours += 24
            self.hours_worked = round(hours, 2)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.employee.first_name} | {self.date} | {self.project.name if self.project else 'No Project'}"

    class Meta:
        ordering = ['-date']

# ---------------------
# Modelo de Cronograma
# ---------------------
class Schedule(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    is_personal = models.BooleanField(default=False)
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    is_complete = models.BooleanField(default=False)
    completion_percentage = models.IntegerField(default=0)
    stage = models.CharField(max_length=100, choices=[
        ("Site cleaning", "Site cleaning"),
        ("Preparation", "Preparation"),
        ("Covering", "Covering"),
        ("Staining", "Staining"),
        ("Sealer", "Sealer"),
        ("Lacquer", "Lacquer"),
        ("Caulking", "Caulking"),
        ("Painting", "Painting"),
        ("Plastic removal", "Plastic removal"),
        ("Cleaning", "Cleaning"),
        ("Touch up", "Touch up"),
    ], blank=True)
    delay_reason = models.TextField(blank=True)
    advance_reason = models.TextField(blank=True)
    photo = models.ImageField(upload_to='schedule_photos/', blank=True, null=True)

    def __str__(self):
        return f"{self.project.name} - {self.title}"

    class Meta:
        ordering = ['start_datetime']

# ---------------------
# Modelo de Tarea
# ---------------------
class Task(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=50, default="Pendiente")

    def __str__(self):
        return f"{self.title} - {self.status}"

# ---------------------
# Modelo de Comentario
# ---------------------
class Comment(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    text = models.TextField()
    image = models.ImageField(upload_to="comments/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.user.username} on {self.project.name}"

# ---------------------
# Modelo de Perfil de Usuario
# ---------------------
ROLE_CHOICES = [
    ('employee', 'Employee'),
    ('project_manager', 'Project Manager'),
    ('client', 'Client'),
]

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)

    def __str__(self):
        return f"{self.user.username} - {self.role}"

# Crear perfil automáticamente al crear usuario
@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance, role='employee')
    else:
        if hasattr(instance, 'profile'):
            instance.profile.save()

# ---------------------
# Modelo de Nómina y Detalle de Nómina
# ---------------------
class Payroll(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    week_start = models.DateField()
    week_end = models.DateField()
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    is_paid = models.BooleanField(default=False)
    payment_reference = models.CharField(max_length=100, blank=True, help_text="Cheque o referencia de pago")

    def __str__(self):
        return f"{self.project.name} - {self.week_start} to {self.week_end}"

def get_last_hourly_rate(employee, before_date):
    last_record = PayrollRecord.objects.filter(
        employee=employee,
        week_end__lt=before_date
    ).order_by('-week_end').first()
    if last_record:
        return last_record.hourly_rate
    return employee.hourly_rate

class PayrollEntry(models.Model):
    payroll = models.ForeignKey(Payroll, related_name="entries", on_delete=models.CASCADE)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    hours_worked = models.DecimalField(max_digits=5, decimal_places=2)
    hourly_rate = models.DecimalField(max_digits=7, decimal_places=2)
    total_pay = models.DecimalField(max_digits=10, decimal_places=2)
    notes = models.TextField(blank=True)
    payment_reference = models.CharField(max_length=100, blank=True, help_text="Cheque o referencia de pago individual")

    def save(self, *args, **kwargs):
        if not self.hourly_rate:
            self.hourly_rate = get_last_hourly_rate(self.employee, self.payroll.week_start)
        self.total_pay = round(self.hours_worked * self.hourly_rate, 2)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.employee} - {self.hours_worked} hrs"

# ---------------------
# Modelo de Orden de Cambio
# ---------------------
class ChangeOrder(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='change_orders')
    description = models.TextField()
    date_created = models.DateField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pendiente'),
        ('approved', 'Aprobado'),
        ('sent', 'Enviado'),
        ('billed', 'Facturado'),
        ('paid', 'Pagado'),
    ], default='pending')
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"Change Order for {self.project.name} - {self.description[:30]}"

# ---------------------
# Modelo de Registro de Nómina
# ---------------------
class PayrollRecord(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    week_start = models.DateField()
    week_end = models.DateField()
    total_hours = models.DecimalField(max_digits=6, decimal_places=2)
    hourly_rate = models.DecimalField(max_digits=8, decimal_places=2)
    total_pay = models.DecimalField(max_digits=10, decimal_places=2)
    paid = models.BooleanField(default=False)
    pay_date = models.DateField(null=True, blank=True)
    check_number = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return f"{self.employee} | {self.week_start} - {self.week_end}"

# Puedes poner esto en core/models.py o en un archivo utils.py

def get_week_hours(employee, week_start, week_end):
    return TimeEntry.objects.filter(
        employee=employee,
        date__range=(week_start, week_end),
        change_order__isnull=True
    )

def calcular_total_horas(employee, week_start, week_end):
    horas = get_week_hours(employee, week_start, week_end)
    return sum([h.hours_worked or 0 for h in horas])

# Ejemplo de función para crear un registro de nómina semanal
def crear_o_actualizar_payroll_record(employee, week_start, week_end):
    total_hours = calcular_total_horas(employee, week_start, week_end)
    last_rate = get_last_hourly_rate(employee, week_start)
    total_pay = round(total_hours * last_rate, 2)
    record, created = PayrollRecord.objects.update_or_create(
        employee=employee,
        week_start=week_start,
        week_end=week_end,
        defaults={
            'total_hours': total_hours,
            'hourly_rate': last_rate,
            'total_pay': total_pay,
        }
    )
    return record

# ---------------------
# Modelo de Factura
# ---------------------
class Invoice(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='invoices')
    change_orders = models.ManyToManyField('ChangeOrder', blank=True, related_name='invoices')
    invoice_number = models.CharField(max_length=20, unique=True, editable=False)
    date_issued = models.DateField(auto_now_add=True)
    due_date = models.DateField(null=True, blank=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    is_paid = models.BooleanField(default=False)
    pdf = models.FileField(upload_to='invoices/', blank=True, null=True)
    notes = models.TextField(blank=True)
    # Relación a Income (se crea cuando se marca como pagado)
    income = models.OneToOneField('Income', on_delete=models.SET_NULL, null=True, blank=True, related_name='invoice_link')

    def save(self, *args, **kwargs):
        creating = self._state.adding
        was_paid = False
        if not creating:
            old = Invoice.objects.get(pk=self.pk)
            was_paid = old.is_paid

        # Generar número de factura si no existe
        if not self.invoice_number:
            initials = ''.join([w[0].upper() for w in self.project.client.split()[:2]])
            count = Invoice.objects.filter(project__client__icontains=self.project.client[:2]).count() + 1
            self.invoice_number = f"KP{initials}{count:03d}"

        super().save(*args, **kwargs)

        # Si se marcó como pagado y no había sido pagado antes, crea Income
        if self.is_paid and (creating or not was_paid) and not self.income:
            income = Income.objects.create(
                project=self.project,
                project_name=f"Factura {self.invoice_number}",
                amount=self.total_amount,
                date=self.date_issued,
                payment_method="OTRO",  # Puedes ajustar esto según tu lógica
                description=f"Ingreso por factura {self.invoice_number}",
            )
            self.income = income
            super().save(update_fields=['income'])

    def clean(self):
        # Calcula el monto máximo permitido
        project_budget = self.project.budget_total or 0
        change_orders_total = sum([co.amount for co in self.change_orders.all()])
        max_allowed = project_budget + change_orders_total

        if self.total_amount > max_allowed:
            raise ValidationError(
                f"El monto total de la factura (${self.total_amount}) excede el máximo permitido (${max_allowed})."
            )

    def __str__(self):
        return f"{self.invoice_number} - {self.project.name}"

# ---------------------
# Modelo de Línea de Factura
# ---------------------
class InvoiceLine(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='lines')
    description = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    # Opcional: relación a TimeEntry o Expense para trazabilidad
    time_entry = models.ForeignKey('TimeEntry', on_delete=models.SET_NULL, null=True, blank=True)
    expense = models.ForeignKey('Expense', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.description} - ${self.amount}"

# ---------------------
# Formulario para Registro de Horas
# ---------------------
class TimeEntryForm(forms.ModelForm):
    class Meta:
        model = TimeEntry
        fields = [
            'employee',
            'project',
            'date',
            'start_time',
            'end_time',
            'hours_worked',
            'change_order',  # incluye este si lo necesitas
            # agrega aquí todos los campos que quieres mostrar en el formulario
        ]

