from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from datetime import datetime

# ---------------------
# Modelo de Empleado
# ---------------------
class Employee(models.Model):
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
    notes = models.TextField(blank=True, null=True)
    touch_ups = models.BooleanField(default=False)
    change_order = models.ForeignKey('ChangeOrder', on_delete=models.SET_NULL, null=True, blank=True, related_name='time_entries')

    @property
    def labor_cost(self):
        return round(self.hours_worked * self.employee.hourly_rate, 2)

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

class PayrollEntry(models.Model):
    payroll = models.ForeignKey(Payroll, related_name="entries", on_delete=models.CASCADE)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    hours_worked = models.DecimalField(max_digits=5, decimal_places=2)
    hourly_rate = models.DecimalField(max_digits=7, decimal_places=2)
    total_pay = models.DecimalField(max_digits=10, decimal_places=2)
    notes = models.TextField(blank=True)
    payment_reference = models.CharField(max_length=100, blank=True, help_text="Cheque o referencia de pago individual")

    def save(self, *args, **kwargs):
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

