from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from datetime import datetime, timedelta
from django.core.exceptions import ValidationError
from decimal import Decimal, ROUND_HALF_UP
from django.apps import apps
from django.utils import timezone
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from django.db.models.manager import RelatedManager

# ---------------------
# Modelo de Empleado
# ---------------------
class Employee(models.Model):
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True)
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
    total_income = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    total_expenses = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    reflection_notes = models.TextField(blank=True, help_text="Notas sobre aprendizajes, errores o mejoras para próximos proyectos")
    created_at = models.DateTimeField(auto_now_add=True)
    # Presupuesto
    budget_total = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"), help_text="Presupuesto total asignado al proyecto")
    budget_labor = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"), help_text="Presupuesto para mano de obra")
    budget_materials = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"), help_text="Presupuesto para materiales")
    budget_other = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"), help_text="Presupuesto para otros gastos (seguros, almacenamiento, etc.)")

    if TYPE_CHECKING:
        id: int
        estimates: 'RelatedManager[Estimate]'

    def profit(self):
        return round(self.total_income - self.total_expenses, 2)

    @property
    def budget_remaining(self):
        return round(self.budget_total - self.total_expenses, 2)

    def __str__(self):
        return self.name

    def earned_value_summary(self, as_of=None):
        from core.services.earned_value import compute_project_ev
        return compute_project_ev(self, as_of=as_of)

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
    cost_code = models.ForeignKey('CostCode', on_delete=models.SET_NULL, null=True, blank=True, related_name='expenses')

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
    end_time = models.TimeField(null=True, blank=True)  # <- permitir entrada abierta
    hours_worked = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    change_order = models.ForeignKey(
        'ChangeOrder',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='time_entries'
    )
    notes = models.TextField(blank=True, null=True)
    cost_code = models.ForeignKey('CostCode', on_delete=models.SET_NULL, null=True, blank=True, related_name='time_entries')

    @property
    def labor_cost(self):
        if self.hours_worked is not None and self.employee and self.employee.hourly_rate is not None:
            return (Decimal(self.hours_worked) * Decimal(self.employee.hourly_rate)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        return Decimal("0.00")

    def save(self, *args, **kwargs):
        if self.start_time and self.end_time:
            s = self.start_time.hour * 60 + self.start_time.minute
            e = self.end_time.hour * 60 + self.end_time.minute

            # Cruza medianoche
            if e < s:
                e += 24 * 60

            minutes = e - s
            hours = Decimal(minutes) / Decimal(60)

            # Almuerzo: solo si cruza 12:30 y el turno dura al menos 5 h
            LUNCH_MIN = 12 * 60 + 30
            if s < LUNCH_MIN <= e and hours >= Decimal("5.0"):
                hours -= Decimal("0.5")

            if hours < 0:
                hours = Decimal("0.00")

            self.hours_worked = hours.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
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
# Cronograma jerárquico (Categorías/Items)
# ---------------------
class ScheduleCategory(models.Model):
    """Categorías de cronograma por proyecto, con posibilidad de jerarquía."""
    if TYPE_CHECKING:
        items: "RelatedManager[ScheduleItem]"
        children: "RelatedManager[ScheduleCategory]"

    project = models.ForeignKey('Project', on_delete=models.CASCADE, related_name='schedule_categories')
    name = models.CharField(max_length=200)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    order = models.IntegerField(default=0)
    is_phase = models.BooleanField(default=False, help_text="Marcar si esta categoría representa una fase agregada del cronograma")
    cost_code = models.ForeignKey('CostCode', on_delete=models.SET_NULL, null=True, blank=True, related_name='schedule_categories')

    class Meta:
        ordering = ['project', 'parent__id', 'order', 'name']
        unique_together = ('project', 'name', 'parent')

    def __str__(self):
        return f"{self.project.name} · {self.name}"

    @property
    def percent_complete(self):
        """Promedio simple de los items directos o, si no hay, de subcategorías."""
        items = getattr(self, 'items', None)
        if items is not None:
            qs = self.items.all()
            if qs.exists():
                vals = [i.percent_complete or 0 for i in qs]
                return int(sum(vals) / len(vals)) if vals else 0
        # Si no hay items, promediar hijos
        kids = self.children.all()
        if kids.exists():
            vals = [c.percent_complete for c in kids]
            return int(sum(vals) / len(vals)) if vals else 0
        return 0


class ScheduleItem(models.Model):
    """Item planificable dentro de una categoría del cronograma."""
    STATUS_CHOICES = [
        ('NOT_STARTED', 'No iniciado'),
        ('IN_PROGRESS', 'En progreso'),
        ('BLOCKED', 'Bloqueado'),
        ('DONE', 'Completado'),
    ]

    project = models.ForeignKey('Project', on_delete=models.CASCADE, related_name='schedule_items')
    if TYPE_CHECKING:
        tasks: "RelatedManager[Task]"

    category = models.ForeignKey(ScheduleCategory, on_delete=models.CASCADE, related_name='items')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    order = models.IntegerField(default=0)

    planned_start = models.DateField(null=True, blank=True)
    planned_end = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='NOT_STARTED')
    percent_complete = models.IntegerField(default=0)
    is_milestone = models.BooleanField(default=False, help_text="Si es un hito se mostrará como diamante en el Gantt")

    # Vínculos contables/estimación (opcionales)
    budget_line = models.ForeignKey('BudgetLine', on_delete=models.SET_NULL, null=True, blank=True, related_name='schedule_items')
    estimate_line = models.ForeignKey('EstimateLine', on_delete=models.SET_NULL, null=True, blank=True, related_name='schedule_items')
    cost_code = models.ForeignKey('CostCode', on_delete=models.SET_NULL, null=True, blank=True, related_name='schedule_items')

    class Meta:
        ordering = ['project', 'category__id', 'order', 'id']

    def __str__(self):
        return f"{self.project.name} · {self.title}"

    def recalculate_progress(self, save=True):
        """Calcula % según tareas vinculadas (excluye canceladas)."""
        tasks_qs = getattr(self, 'tasks', None)
        if tasks_qs is None:
            return self.percent_complete
        qs = self.tasks.exclude(status='Cancelada')
        total = qs.count()
        if total == 0:
            pct = 0
        else:
            done = qs.filter(status='Completada').count()
            pct = int((done / total) * 100)
        self.percent_complete = max(0, min(100, pct))
        # Autoestado simple
        if self.percent_complete >= 100:
            self.status = 'DONE'
        elif qs.filter(status='En Progreso').exists():
            self.status = 'IN_PROGRESS'
        elif total > 0 and done == 0:
            self.status = 'NOT_STARTED'
        if save:
            self.save(update_fields=['percent_complete', 'status'])
        return self.percent_complete

# ---------------------
# Modelo de Tarea
# ---------------------
class Task(models.Model):
    """
    Tareas del proyecto, incluyendo touch-ups solicitados por clientes.
    El cliente puede crear tareas con fotos, el PM las asigna a empleados.
    """
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tasks')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    status = models.CharField(
        max_length=50, 
        default="Pendiente",
        choices=[
            ('Pendiente', 'Pendiente'),
            ('En Progreso', 'En Progreso'),
            ('Completada', 'Completada'),
            ('Cancelada', 'Cancelada'),
        ]
    )
    created_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='created_tasks',
        help_text="Usuario que creó la tarea (cliente o staff)"
    )
    assigned_to = models.ForeignKey(
        'Employee',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_tasks',
        help_text="Empleado asignado por el PM"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    is_touchup = models.BooleanField(default=False, help_text="Marcar si esta tarea es un touch-up")
    
    # Para touch-ups: permitir adjuntar imagen directamente a la tarea
    image = models.ImageField(upload_to="tasks/", blank=True, null=True, help_text="Foto del touch-up")
    # Enlace opcional a item del cronograma jerárquico
    schedule_item = models.ForeignKey('ScheduleItem', on_delete=models.SET_NULL, null=True, blank=True, related_name='tasks')

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Tarea"
        verbose_name_plural = "Tareas"

    def __str__(self):
        return f"{self.title} - {self.status}"

# ---------------------
# Modelo de Comentario
# ---------------------
class Comment(models.Model):
    """
    Comentarios en proyectos, pueden estar asociados a tareas específicas.
    Permiten adjuntar imágenes para comunicación visual.
    """
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    text = models.TextField(blank=True)
    image = models.ImageField(upload_to="comments/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Relacionar comentario con tarea si aplica
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='comments',
        help_text="Tarea relacionada si este comentario es sobre una tarea específica"
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Comentario"
        verbose_name_plural = "Comentarios"

    def __str__(self):
        username = self.user.username if self.user else "Unknown"
        return f"Comment by {username} on {self.project.name}"

# ---------------------
# Modelo de Perfil de Usuario
# ---------------------
ROLE_CHOICES = [
    ('employee', 'Employee'),
    ('project_manager', 'Project Manager'),
    ('client', 'Client'),
    ('designer', 'Designer'),
    ('superintendent', 'Superintendent'),
]

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    language = models.CharField(
        max_length=5,
        choices=[('en', 'English'), ('es', 'Español')],
        default='en',
        help_text="Preferred UI language"
    )

    def __str__(self):
        return f"{self.user.username} - {self.role}"

@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance, role='employee', language='en')
    else:
        if hasattr(instance, 'profile'):
            instance.profile.save()

# ---------------------
# Acceso granular de clientes a proyectos
# ---------------------
class ClientProjectAccess(models.Model):
    ROLE_CHOICES = [
        ('client', 'Client'),
        ('external_pm', 'External PM'),
        ('viewer', 'Viewer'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='project_accesses')
    project = models.ForeignKey('Project', on_delete=models.CASCADE, related_name='client_accesses')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='client')
    can_comment = models.BooleanField(default=True)
    can_create_tasks = models.BooleanField(default=True)
    granted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'project')
        verbose_name = 'Client Project Access'
        verbose_name_plural = 'Client Project Accesses'

    def __str__(self):
        return f"{self.user.username} → {self.project.name} ({self.role})"

# ---------------------
# Sistema de Nómina Mejorado
# ---------------------
# DEPRECATED: Payroll y PayrollEntry eliminados - usar PayrollPeriod y PayrollPayment

# ---------------------
# Modelo de Orden de Cambio
# ---------------------
class ChangeOrder(models.Model):
    if TYPE_CHECKING:
        id: int

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='change_orders')
    description = models.TextField()
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0"))
    date_created = models.DateField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pendiente'),
        ('approved', 'Aprobado'),
        ('sent', 'Enviado'),
        ('billed', 'Facturado'),
        ('paid', 'Pagado'),
    ], default='pending')
    notes = models.TextField(blank=True)
    color = models.CharField(max_length=7, blank=True, null=True, help_text="Color hex (ej: #FF5733)")
    reference_code = models.CharField(max_length=50, blank=True, null=True, help_text="Código de referencia o color")

    def __str__(self):
        return f"CO {self.id} | {self.project.name} | ${self.amount:.2f}"

class ChangeOrderPhoto(models.Model):
    """Fotos asociadas a un Change Order con anotaciones"""
    change_order = models.ForeignKey(ChangeOrder, on_delete=models.CASCADE, related_name='photos')
    image = models.ImageField(upload_to='changeorders/photos/')
    description = models.CharField(max_length=255, blank=True)
    annotations = models.TextField(blank=True, help_text="JSON con anotaciones dibujadas")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order', 'uploaded_at']

    def __str__(self):
        return f"Foto {self.id} - CO {self.change_order.id}"

# ---------------------
# Modelo de Registro de Nómina Semanal (mejorado)
# ---------------------
class PayrollPeriod(models.Model):
    """Período de nómina semanal para revisión y aprobación"""
    if TYPE_CHECKING:
        records: "RelatedManager[PayrollRecord]"

    week_start = models.DateField()
    week_end = models.DateField()
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=[
        ('draft', 'Borrador'),
        ('under_review', 'En Revisión'),
        ('approved', 'Aprobado'),
        ('paid', 'Pagado'),
    ], default='draft')
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-week_start']
        unique_together = ['week_start', 'week_end']

    def __str__(self):
        return f"Nómina {self.week_start} - {self.week_end}"

    def total_payroll(self):
        """Calcula el total de la nómina para todos los empleados"""
        return sum(record.total_pay for record in self.records.all())

    def total_paid(self):
        """Calcula cuánto se ha pagado de esta nómina"""
        return sum(payment.amount for record in self.records.all() for payment in record.payments.all())

    def balance_due(self):
        """Calcula cuánto falta por pagar"""
        return self.total_payroll() - self.total_paid()


class PayrollRecord(models.Model):
    """Registro individual de nómina por empleado por semana"""
    period = models.ForeignKey(PayrollPeriod, related_name='records', on_delete=models.CASCADE, null=True, blank=True)
    if TYPE_CHECKING:
        payments: "RelatedManager[PayrollPayment]"

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    week_start = models.DateField()
    week_end = models.DateField()
    
    # Campos calculados pero editables
    total_hours = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal("0"))
    hourly_rate = models.DecimalField(max_digits=8, decimal_places=2)
    adjusted_rate = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, 
                                        help_text="Tasa ajustada para esta semana (override)")
    total_pay = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0"))
    
    # Estado y notas
    reviewed = models.BooleanField(default=False)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['week_start', 'employee__last_name']

    def __str__(self):
        return f"{self.employee} | {self.week_start} - {self.week_end} | ${self.total_pay}"

    def effective_rate(self):
        """Retorna la tasa efectiva (ajustada o normal)"""
        return self.adjusted_rate if self.adjusted_rate else self.hourly_rate

    def calculate_total_pay(self):
        """Calcula el total a pagar"""
        return self.total_hours * self.effective_rate()

    def amount_paid(self):
        """Suma de todos los pagos hechos a este registro"""
        return sum(payment.amount for payment in self.payments.all())

    def balance_due(self):
        """Cantidad pendiente de pago"""
        return self.total_pay - self.amount_paid()


class PayrollPayment(models.Model):
    """Registro de pagos parciales o completos de nómina"""
    payroll_record = models.ForeignKey(PayrollRecord, related_name='payments', on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateField()
    payment_method = models.CharField(max_length=20, choices=[
        ('check', 'Cheque'),
        ('transfer', 'Transferencia'),
        ('cash', 'Efectivo'),
    ], default='check')
    check_number = models.CharField(max_length=50, blank=True)
    reference = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    recorded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-payment_date']

    def __str__(self):
        ref = f"#{self.check_number}" if self.check_number else self.reference
        return f"${self.amount} - {self.payroll_record.employee} - {ref}"


def get_week_hours(employee, week_start, week_end):
    """Obtiene las entradas de tiempo de un empleado para una semana"""
    return TimeEntry.objects.filter(
        employee=employee,
        date__range=(week_start, week_end)
    )

def calcular_total_horas(employee, week_start, week_end):
    horas = get_week_hours(employee, week_start, week_end)
    return sum([h.hours_worked or 0 for h in horas])

def crear_o_actualizar_payroll_record(employee, week_start, week_end):
    """Actualiza o crea un PayrollRecord usando la tarifa base del empleado.
    get_last_hourly_rate fue parte del sistema anterior; ahora usamos employee.hourly_rate directamente.
    """
    total_hours = calcular_total_horas(employee, week_start, week_end)
    base_rate = employee.hourly_rate
    total_pay = round(total_hours * base_rate, 2)
    record, created = PayrollRecord.objects.update_or_create(
        employee=employee,
        week_start=week_start,
        week_end=week_end,
        defaults={
            'total_hours': total_hours,
            'hourly_rate': base_rate,
            'total_pay': total_pay,
        }
    )
    return record

# ---------------------
# Modelo de Factura
# ---------------------
class Invoice(models.Model):
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
    
    if TYPE_CHECKING:
        project_id: int

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='invoices')
    invoice_number = models.CharField(max_length=40, unique=True, editable=False, help_text="Referencia amigable; si hay Estimate aprobado: usa su código + secuencia")
    date_issued = models.DateField(auto_now_add=True)
    due_date = models.DateField(null=True, blank=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0"))  # default=0 para primer save
    
    # Status tracking (NEW)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    sent_date = models.DateTimeField(null=True, blank=True)
    viewed_date = models.DateTimeField(null=True, blank=True)
    approved_date = models.DateTimeField(null=True, blank=True)
    paid_date = models.DateTimeField(null=True, blank=True)
    sent_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='invoices_sent')
    
    # Payment tracking (NEW)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0"))
    
    # Legacy fields (keep for backward compatibility)
    is_paid = models.BooleanField(default=False)
    pdf = models.FileField(upload_to='invoices/', blank=True, null=True)
    notes = models.TextField(blank=True)
    change_orders = models.ManyToManyField('ChangeOrder', blank=True, related_name='invoices')
    income = models.OneToOneField('Income', on_delete=models.SET_NULL, null=True, blank=True, related_name='invoice_link')
    
    @property
    def balance_due(self):
        """Remaining amount to be paid"""
        return self.total_amount - self.amount_paid
    
    @property
    def payment_progress(self):
        """Percentage paid"""
        if self.total_amount == 0:
            return 0
        return (self.amount_paid / self.total_amount) * 100
    
    def update_status(self):
        """Auto-update status based on payments and dates"""
        from django.utils import timezone
        
        if self.balance_due <= 0 and self.amount_paid > 0:
            self.status = 'PAID'
            if not self.paid_date:
                self.paid_date = timezone.now()
            self.is_paid = True  # Update legacy field
        elif self.amount_paid > 0:
            self.status = 'PARTIAL'
        elif self.due_date and timezone.now().date() > self.due_date and self.balance_due > 0:
            if self.status not in ['DRAFT', 'CANCELLED']:
                self.status = 'OVERDUE'
        
        self.save()

    def save(self, *args, **kwargs):
        creating = self._state.adding
        was_paid = False
        if not creating:
            old = Invoice.objects.get(pk=self.pk)
            was_paid = old.is_paid

        if not self.invoice_number:
            # Si existe una Estimate aprobada más reciente, usar su código como prefijo
            approved_estimate = getattr(self.project.estimates.filter(approved=True).order_by('-created_at').first(), 'code', None)
            if approved_estimate:
                seq = Invoice.objects.filter(project=self.project).count() + 1
                self.invoice_number = f"{approved_estimate}-INV{seq:02d}"
            else:
                client = (self.project.client or "").strip()
                initials = ''.join([w[0].upper() for w in client.split()[:2]]) or "KP"
                seq = Invoice.objects.filter(project=self.project).count() + 1
                self.invoice_number = f"{initials}-{self.project.id:04d}-{seq:03d}"

        super().save(*args, **kwargs)

        if self.is_paid and (creating or not was_paid) and not self.income:
            income = Income.objects.create(
                project=self.project,
                project_name=f"Factura {self.invoice_number}",
                amount=self.total_amount,
                date=self.date_issued,
                payment_method="OTRO",
                description=f"Ingreso por factura {self.invoice_number}",
            )
            self.income = income
            super().save(update_fields=['income'])

    def clean(self):
        if not self.pk or not self.project_id:
            return
        project_total = getattr(self.project, 'budget_total', 0) or 0
        existing = Invoice.objects.filter(project=self.project).exclude(pk=self.pk)\
                   .aggregate(total=models.Sum('total_amount'))['total'] or 0
        available = project_total - existing
        if self.total_amount and self.total_amount > available:
            raise ValidationError({'total_amount': f'El total excede el presupuesto disponible (${available:.2f}).'})

    def __str__(self):
        return f"{self.invoice_number} - {self.project.name}"

# ---------------------
# Modelo de Línea de Factura
# ---------------------
class InvoiceLine(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='lines')
    description = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    time_entry = models.ForeignKey('TimeEntry', on_delete=models.SET_NULL, null=True, blank=True)
    expense = models.ForeignKey('Expense', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.description} - ${self.amount}"

# ---------------------
# Modelo de Pago de Factura (NEW)
# ---------------------
class InvoicePayment(models.Model):
    """
    Tracks partial/full payments on invoices.
    Allows multiple payments per invoice for progress billing.
    """
    PAYMENT_METHOD_CHOICES = [
        ('CHECK', 'Cheque'),
        ('CASH', 'Efectivo'),
        ('TRANSFER', 'Transferencia'),
        ('CARD', 'Tarjeta'),
        ('OTHER', 'Otro'),
    ]
    
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateField()
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='CHECK')
    reference = models.CharField(max_length=100, blank=True, help_text="Check #, Transfer ID, etc.")
    notes = models.TextField(blank=True)
    recorded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    recorded_at = models.DateTimeField(auto_now_add=True)
    
    # Optional link to Income record
    income = models.OneToOneField('Income', on_delete=models.SET_NULL, null=True, blank=True, related_name='payment_link')
    
    class Meta:
        ordering = ['-payment_date', '-recorded_at']
        verbose_name = 'Invoice Payment'
        verbose_name_plural = 'Invoice Payments'
    
    def save(self, *args, **kwargs):
        creating = self._state.adding
        super().save(*args, **kwargs)
        
        # Update invoice amount_paid
        if creating:
            self.invoice.amount_paid += self.amount
            self.invoice.update_status()
            
            # Auto-create Income record
            if not self.income:
                income = Income.objects.create(
                    project=self.invoice.project,
                    project_name=f"Pago Factura {self.invoice.invoice_number}",
                    amount=self.amount,
                    date=self.payment_date,
                    payment_method=self.payment_method,
                    category='PAYMENT',
                    description=f"Pago de ${self.amount} para factura {self.invoice.invoice_number}. Ref: {self.reference}",
                )
                self.income = income
                super().save(update_fields=['income'])
    
    def __str__(self):
        return f"Payment ${self.amount} for {self.invoice.invoice_number} on {self.payment_date}"
# ---------------------
# Facturación Progresiva (Invoice Line Estimate Tracking)
# ---------------------
class InvoiceLineEstimate(models.Model):
    """
    Tracks progressive billing of estimate lines across multiple invoices.
    Ensures the sum of percentage_billed per estimate_line never exceeds 100%.
    """
    invoice_line = models.ForeignKey(InvoiceLine, on_delete=models.CASCADE, related_name='estimate_billings')
    estimate_line = models.ForeignKey('EstimateLine', on_delete=models.PROTECT, related_name='invoice_billings')
    percentage_billed = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        help_text="Percentage of this estimate line being billed (0.00-100.00)"
    )
    amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        help_text="Amount = estimate_line.total * (percentage_billed/100)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Invoice Line Estimate Billing'
        verbose_name_plural = 'Invoice Line Estimate Billings'
    
    def clean(self):
        """Validate that total percentage billed for estimate_line doesn't exceed 100%."""
        super().clean()
        
        if self.percentage_billed < 0 or self.percentage_billed > 100:
            raise ValidationError("El porcentaje debe estar entre 0 y 100")
        
        # Calculate total billed for this estimate line (excluding current instance if updating)
        existing_billings = InvoiceLineEstimate.objects.filter(
            estimate_line=self.estimate_line
        )
        if self.pk:
            existing_billings = existing_billings.exclude(pk=self.pk)
        
        total_billed = sum(b.percentage_billed for b in existing_billings)
        total_billed += self.percentage_billed
        
        if total_billed > 100:
            raise ValidationError(
                f"Total facturado ({total_billed}%) excede 100%. "
                f"Ya facturado: {total_billed - self.percentage_billed}%"
            )
    
    def save(self, *args, **kwargs):
        # Auto-calculate amount if not set
        if not self.amount and self.estimate_line:
            self.amount = self.estimate_line.total * (self.percentage_billed / 100)
        
        self.full_clean()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.estimate_line} - {self.percentage_billed}% (${self.amount})"


# --- Cost Structure ---
class CostCode(models.Model):
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=120)
    category = models.CharField(max_length=50, blank=True)  # labor, material, equipment
    active = models.BooleanField(default=True)
    def __str__(self): return f"{self.code} - {self.name}"

class BudgetLine(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='budget_lines')
    cost_code = models.ForeignKey(CostCode, on_delete=models.PROTECT, related_name='budget_lines')
    description = models.CharField(max_length=200, blank=True)
    qty = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))
    unit = models.CharField(max_length=20, blank=True)
    unit_cost = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))
    allowance = models.BooleanField(default=False)
    baseline_amount = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0"))
    revised_amount = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0"))
    planned_start = models.DateField(null=True, blank=True)
    planned_finish = models.DateField(null=True, blank=True)
    weight_override = models.DecimalField(
        max_digits=6, decimal_places=4, null=True, blank=True,
        help_text="Optional weight (0-1). If empty, weight is baseline/total."
    )

    def save(self,*a,**k):
        self.baseline_amount = (self.qty or 0) * (self.unit_cost or 0)
        if self.revised_amount == 0:
            self.revised_amount = self.baseline_amount
        self.full_clean(exclude=None)  # valida clean()
        super().save(*a,**k)
    def __str__(self): return f"{self.project.name} | {self.cost_code.code}"

    def clean(self):
        super().clean()
        # planned_finish >= planned_start
        if self.planned_start and self.planned_finish and self.planned_finish < self.planned_start:
            raise ValidationError("Planned finish must be on/after planned start.")
        # weight_override entre 0 y 1
        if self.weight_override is not None:
            if self.weight_override < 0 or self.weight_override > 1:
                raise ValidationError("Weight override must be between 0 and 1.")

# --- Estimating / Proposals ---
class Estimate(models.Model):
    if TYPE_CHECKING:
        project_id: int

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='estimates')
    version = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    approved = models.BooleanField(default=False)
    # Business-facing code: KP + client abbreviation + sequence starting at 1000
    code = models.CharField(max_length=40, unique=True, blank=True, help_text="KP + siglas del cliente + secuencia (desde 1000)")
    takeoff_link = models.URLField(blank=True, help_text="Link a Dropbox/Drive con el takeoff o soporte")
    markup_material = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0"))  # %
    markup_labor = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0"))
    overhead_pct = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0"))
    target_profit_pct = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0"))
    notes = models.TextField(blank=True)
    class Meta:
        unique_together = ('project','version')
        ordering = ['-version']
    def __str__(self): return f"Estimate v{self.version} - {self.project.name}"

    def _client_abbrev(self):
        """Derive 2-letter client abbreviation from Project.client.
        - If two or more words: first letters of first two words (e.g., 'North West' -> 'NW')
        - If single word: first two characters (e.g., 'Northwest' -> 'NO')
        - Fallback 'KP'
        """
        client = (self.project.client or '').strip()
        if not client:
            return 'KP'
        parts = [p for p in client.split() if p]
        if len(parts) >= 2:
            return (parts[0][0] + parts[1][0]).upper()
        first = parts[0] if parts else ''
        return first[:2].upper() if first else 'KP'

    def save(self, *args, **kwargs):
        # Auto-generate business code if missing
        if not self.code and self.project_id:
            base = f"KP{self._client_abbrev()}"
            # Find next sequence starting at 1000 per base
            existing = Estimate.objects.filter(code__startswith=base)
            max_seq = 999
            for e in existing.values_list('code', flat=True):
                # expects like KPNW1001, extract trailing digits
                tail = ''.join(ch for ch in e if ch.isdigit())
                try:
                    if tail:
                        num = int(tail)
                        if num > max_seq:
                            max_seq = num
                except Exception:
                    continue
            next_seq = max_seq + 1 if max_seq >= 1000 else 1000
            self.code = f"{base}{next_seq}"
        super().save(*args, **kwargs)

class EstimateLine(models.Model):
    estimate = models.ForeignKey(Estimate, on_delete=models.CASCADE, related_name='lines')
    cost_code = models.ForeignKey(CostCode, on_delete=models.PROTECT)
    description = models.CharField(max_length=200, blank=True)
    qty = models.DecimalField(max_digits=12, decimal_places=2)
    unit = models.CharField(max_length=20, blank=True)
    labor_unit_cost = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))
    material_unit_cost = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))
    other_unit_cost = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))
    def direct_cost(self):
        return (self.qty or 0) * (self.labor_unit_cost + self.material_unit_cost + self.other_unit_cost)
    def __str__(self): return f"{self.estimate} | {self.cost_code.code}"

class Proposal(models.Model):
    estimate = models.OneToOneField(Estimate, on_delete=models.CASCADE, related_name='proposal')
    issued_at = models.DateTimeField(auto_now_add=True)
    client_view_token = models.CharField(max_length=36, unique=True)
    accepted = models.BooleanField(default=False)
    accepted_at = models.DateTimeField(null=True, blank=True)
    client_comment = models.TextField(blank=True)
    def __str__(self): return f"Proposal {self.estimate.code} ({self.estimate.project.name})"

# --- Field Communication ---
class DailyLog(models.Model):
    """
    Daily Log - Reporte diario del PM sobre el progreso del proyecto.
    Muestra qué tareas se completaron hoy y el progreso general.
    Visible para PM, diseñadores, cliente, owner (NO empleados).
    """
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='daily_logs')
    date = models.DateField()
    weather = models.CharField(max_length=120, blank=True, help_text="Condiciones climáticas del día")
    crew_count = models.PositiveIntegerField(default=0, help_text="Número de personas trabajando")
    
    # Tareas completadas ese día (muchos a muchos)
    completed_tasks = models.ManyToManyField('Task', blank=True, related_name='daily_logs', 
                                            help_text="Tareas completadas o con progreso este día")
    
    # Notas y detalles
    progress_notes = models.TextField(blank=True, help_text="Notas generales de progreso")
    accomplishments = models.TextField(blank=True, help_text="Logros específicos del día")
    safety_incidents = models.TextField(blank=True, help_text="Incidentes de seguridad")
    delays = models.TextField(blank=True, help_text="Retrasos o problemas encontrados")
    next_day_plan = models.TextField(blank=True, help_text="Plan para el siguiente día")
    
    # Progreso del Schedule principal
    schedule_item = models.ForeignKey('Schedule', on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name='daily_logs',
                                     help_text="Actividad principal del schedule (ej: Cubrir y Preparar)")
    schedule_progress_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0,
                                                    help_text="Progreso de la actividad principal (%)")
    
    # Fotos del día
    photos = models.ManyToManyField('DailyLogPhoto', blank=True, related_name='logs')
    
    # Metadata
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_published = models.BooleanField(default=False, help_text="Visible para cliente/owner")
    
    class Meta:
        unique_together = ('project', 'date')
        ordering = ['-date']
        permissions = [
            ('view_dailylog_client', 'Can view daily log as client'),
        ]
    
    def __str__(self):
        return f"{self.project.name} - {self.date}"
    
    def task_completion_summary(self):
        """Resumen de tareas completadas vs total"""
        total_tasks = self.completed_tasks.count()
        fully_completed = self.completed_tasks.filter(status='completed').count()
        return {'total': total_tasks, 'completed': fully_completed}


class DailyLogPhoto(models.Model):
    """Fotos adjuntas a un Daily Log"""
    image = models.ImageField(upload_to='daily_logs/photos/')
    caption = models.CharField(max_length=255, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    def __str__(self):
        return f"Photo {self.id} - {self.caption[:30]}"

class RFI(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='rfis')
    number = models.PositiveIntegerField()
    question = models.TextField()
    answer = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=[('open','Open'),('answered','Answered'),('closed','Closed')], default='open')
    created_at = models.DateTimeField(auto_now_add=True)
    answered_at = models.DateTimeField(null=True, blank=True)
    class Meta:
        unique_together = ('project','number')
        ordering = ['-created_at']
    def __str__(self): return f"RFI #{self.number} - {self.project.name}"

class Issue(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='issues')
    title = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    severity = models.CharField(max_length=20, choices=[('low','Low'),('medium','Medium'),('high','High')], default='medium')
    status = models.CharField(max_length=20, choices=[('open','Open'),('in_progress','In Progress'),('resolved','Resolved')], default='open')
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    def __str__(self): return f"{self.project.name} | {self.title}"

class Risk(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='risks')
    title = models.CharField(max_length=150)
    probability = models.PositiveSmallIntegerField(help_text="1-100")
    impact = models.PositiveSmallIntegerField(help_text="1-100")
    mitigation = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=[('identified','Identified'),('mitigating','Mitigating'),('realized','Realized'),('closed','Closed')], default='identified')
    created_at = models.DateTimeField(auto_now_add=True)
    def score(self): return (self.probability or 0) * (self.impact or 0)
    def __str__(self): return f"{self.project.name} | {self.title}"

class BudgetProgress(models.Model):
    budget_line = models.ForeignKey(BudgetLine, on_delete=models.CASCADE, related_name='progress_points')
    date = models.DateField()
    qty_completed = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))
    percent_complete = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0"))  # 0–100
    note = models.CharField(max_length=200, blank=True)

    class Meta:
        # Se permite múltiples puntos en la misma fecha (para distintos registros de avance durante el día)
        ordering = ['-date']

    def save(self, *args, **kwargs):
        # Si no envían percent y existe qty en la línea, intenta derivarlo de qty_completed
        try:
            total_qty = getattr(self.budget_line, 'qty', None)
            if (not self.percent_complete or self.percent_complete == 0) and total_qty:
                if total_qty != 0:
                    self.percent_complete = min(100, (self.qty_completed / total_qty) * 100)
        except Exception:
            pass
        self.full_clean(exclude=None)  # valida clean()
        super().save(*args, **kwargs)

    def clean(self):
        super().clean()
        if self.percent_complete is not None:
            if self.percent_complete < 0 or self.percent_complete > 100:
                raise ValidationError("Percent complete must be between 0 and 100.")
        if self.qty_completed is not None and self.qty_completed < 0:
            raise ValidationError("Qty completed cannot be negative.")

    def __str__(self):
        return f"{self.budget_line} {self.date} {self.percent_complete}%"

# ---------------------
# Modelo de Solicitud de Material
# ---------------------
class MaterialRequest(models.Model):
    NEEDED_WHEN_CHOICES = [
        ("now", "Ahora (emergencia)"),
        ("tomorrow", "Mañana"),
        ("next_week", "Siguiente semana"),
        ("date", "Fecha específica"),
    ]
    STATUS_CHOICES = [
        ("pending", "Pendiente"),
        ("submitted", "Enviada"),
        ("ordered", "Ordenada"),
        ("fulfilled", "Entregada"),
        ("cancelled", "Cancelada"),
        ("purchased_lead", "Compra directa (líder)"),  # permite flujo de compra directa
    ]
    if TYPE_CHECKING:
        id: int
        get_status_display: Callable[[], str]

    project = models.ForeignKey("Project", on_delete=models.CASCADE, related_name="material_requests")
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    needed_when = models.CharField(max_length=20, choices=NEEDED_WHEN_CHOICES, default="now")
    needed_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"MR#{self.id} · {self.project} · {self.get_status_display()}"

# ---------------------
# Solicitudes de Cliente (extras que pueden convertirse en CO)
# ---------------------
class ClientRequest(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pendiente"),
        ("approved", "Aprobada"),
        ("converted", "Convertida a CO"),
        ("rejected", "Rechazada"),
    ]
    if TYPE_CHECKING:
        id: int
        get_status_display: Callable[[], str]

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="client_requests")
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    change_order = models.ForeignKey('ChangeOrder', on_delete=models.SET_NULL, null=True, blank=True, related_name='origin_requests')

    def __str__(self):
        return f"CR#{self.id} · {self.project.name} · {self.title} · {self.get_status_display()}"

class MaterialRequestItem(models.Model):
    if TYPE_CHECKING:
        get_unit_display: Callable[[], str]
        get_category_display: Callable[[], str]
    
    CATEGORY_CHOICES = [
        # Pinturas / acabados
        ("paint", "Pintura"),
        ("primer", "Primer"),
        ("stain", "Stain"),
        ("lacquer", "Laca/Clear"),
        ("thinner", "Thinner/Solvente"),
        # Consumibles de enmascarado/protección
        ("tape", "Tape"),
        ("plastic", "Plástico"),
        ("masking_paper", "Papel enmascarar"),
        ("floor_paper", "Papel para piso"),
        ("drop_cloth", "Tela/manta protección"),
        # Aplicación/herramientas
        ("brush", "Brocha"),
        ("roller_cover", "Rodillo (cover)"),
        ("roller_frame", "Rodillo (frame)"),
        ("tray", "Charola"),
        ("tray_liner", "Liner"),
        ("sandpaper", "Lija"),
        ("blades", "Cuchillas"),
        ("scraper", "Raspador"),
        ("mix", "Mezcladores/baldes"),
        # Selladores/adhesivos
        ("caulk", "Caulk/Sellador"),
        ("adhesive", "Adhesivo"),
        ("bonding", "Bonding agent"),
        # Seguridad/PPE
        ("respirator", "Respirador"),
        ("mask", "Mascarilla"),
        ("coverall", "Overol"),
        ("gloves", "Guantes"),
        ("rags", "Trapos"),
        # Otros
        ("colorant", "Colorante/Tinte"),
        ("other", "Otro"),
    ]
    BRAND_CHOICES = [
        ("sherwin_williams", "Sherwin‑Williams"),
        ("benjamin_moore", "Benjamin Moore"),
        ("3m", "3M"),
        ("wurth", "Würth"),
        ("milesi", "Milesi"),
        ("chemcraft", "Chemcraft"),
        ("purdy", "Purdy"),
        ("wooster", "Wooster"),
        ("titebond", "Titebond"),
        ("other", "Otra"),
    ]
    UNIT_CHOICES = [
        ("gal", "Galón"),
        ("liter", "Litro"),
        ("qt", "Quart"),
        ("pt", "Pint"),
        ("roll", "Rollo"),
        ("sheet", "Hoja"),
        ("box", "Caja"),
        ("tube", "Tubo"),
        ("pair", "Par"),
        ("pack", "Paquete"),
        ("sq_ft", "ft²"),
        ("sq_m", "m²"),
        ("unit", "Unidad"),
    ]

    request = models.ForeignKey(MaterialRequest, on_delete=models.CASCADE, related_name="items")
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    brand = models.CharField(max_length=30, choices=BRAND_CHOICES, default="sherwin_williams")
    product_name = models.CharField(max_length=200, blank=True)  # Emerald Interior, Hand-Masker, etc.
    color_name = models.CharField(max_length=200, blank=True)    # Snowbound
    color_code = models.CharField(max_length=100, blank=True)    # SW-xxxx
    finish = models.CharField(max_length=100, blank=True)        # Flat/Satin/Semi-Gloss
    gloss = models.CharField(max_length=100, blank=True)         # 20°/40° (si aplica)
    formula = models.TextField(blank=True)
    reference_image = models.FileField(upload_to="materials/requests/", null=True, blank=True)
    quantity = models.DecimalField(max_digits=8, decimal_places=2)
    unit = models.CharField(max_length=10, choices=UNIT_CHOICES, default="gal")
    comments = models.CharField(max_length=255, blank=True)

    inventory_item = models.ForeignKey("core.InventoryItem", null=True, blank=True, on_delete=models.SET_NULL)
    qty_requested = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0"))
    qty_ordered = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0"))
    qty_received = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0"))
    qty_consumed = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0"))
    qty_returned = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0"))
    item_status = models.CharField(max_length=20, choices=[
        ("pending", "Pending"),
        ("ordered", "Ordered"),
        ("received_partial", "Received Partial"),
        ("received", "Received"),
        ("consumed", "Consumed"),
        ("returned", "Returned"),
        ("canceled", "Canceled"),
    ], default="pending")
    item_notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.quantity} {self.get_unit_display()} · {self.product_name or self.get_category_display()}"

# ---------------------
# Modelo de Catálogo de Materiales
# ---------------------
class MaterialCatalog(models.Model):
    """Catálogo de materiales reutilizables (scoped por proyecto)."""
    project = models.ForeignKey("Project", on_delete=models.CASCADE, related_name="material_catalog", null=True, blank=True)
    category = models.CharField(max_length=20, choices=MaterialRequestItem.CATEGORY_CHOICES)
    brand_text = models.CharField(max_length=100)            # texto libre: “Sherwin‑Williams”, “3M”, etc.
    product_name = models.CharField(max_length=200, blank=True)
    color_name = models.CharField(max_length=200, blank=True)
    color_code = models.CharField(max_length=100, blank=True)
    finish = models.CharField(max_length=100, blank=True)
    gloss = models.CharField(max_length=100, blank=True)
    formula = models.TextField(blank=True)
    default_unit = models.CharField(max_length=50, blank=True)
    reference_image = models.FileField(upload_to="materials/catalog/", null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["project", "category", "brand_text", "product_name"])]
        verbose_name = "Catálogo de material"
        verbose_name_plural = "Catálogo de materiales"

    def __str__(self):
        base = f"{self.brand_text} · {self.product_name}".strip(" ·")
        extra = " ".join(x for x in [self.color_name, self.color_code, self.finish] if x)
        return f"{base} {extra}".strip()

class SitePhoto(models.Model):
    project = models.ForeignKey("core.Project", on_delete=models.CASCADE, related_name="site_photos")
    room = models.CharField(max_length=120, blank=True)
    wall_ref = models.CharField(max_length=120, blank=True, help_text="Pared o ubicación")
    image = models.ImageField(upload_to="site_photos/")

    # Reemplazo del FK inexistente a Color:
    # approved_color = models.ForeignKey("core.Color", null=True, blank=True, on_delete=models.SET_NULL, related_name="site_photos")
    approved_color_id = models.IntegerField(null=True, blank=True, db_index=True, help_text="ID de color aprobado (opcional)")

    color_text = models.CharField(max_length=120, blank=True)
    brand = models.CharField(max_length=120, blank=True)
    finish = models.CharField(max_length=120, blank=True)
    gloss = models.CharField(max_length=120, blank=True)
    special_finish = models.BooleanField(default=False)
    coats = models.PositiveSmallIntegerField(default=1)
    annotations = models.JSONField(default=dict, blank=True)
    notes = models.TextField(blank=True)
    
    # NUEVOS CAMPOS: Before/After comparison
    photo_type = models.CharField(
        max_length=20,
        choices=[
            ('before', 'Before'),
            ('progress', 'Progress'),
            ('after', 'After'),
            ('defect', 'Defect'),
            ('reference', 'Reference'),
        ],
        default='progress',
        help_text="Type of photo for better organization"
    )
    paired_with = models.ForeignKey(
        'self', 
        null=True, 
        blank=True,
        on_delete=models.SET_NULL,
        help_text="Link before/after photos together"
    )
    ai_defects_detected = models.JSONField(
        default=list,
        blank=True,
        help_text="AI-detected defects in this photo"
    )

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.project} · {self.room or 'Cuarto'} · {self.wall_ref or 'Pared'}"

    @property
    def approved_color(self):
        try:
            if self.approved_color_id:
                Color = apps.get_model("core", "Color")
                return Color.objects.filter(id=self.approved_color_id).first()
        except Exception:
            return None
        return None

# ---------------------
# Sistema de muestras / aprobación de colores
# ---------------------
class ColorSample(models.Model):
    STATUS_CHOICES = [
        ('proposed', 'Propuesto'),
        ('review', 'En Revisión'),
        ('approved', 'Aprobado'),
        ('rejected', 'Rechazado'),
        ('archived', 'Archivado'),
    ]
    project = models.ForeignKey('Project', on_delete=models.CASCADE, related_name='color_samples')
    code = models.CharField(max_length=60, blank=True, help_text='SW xxxx, Milesi xxx, etc.')
    name = models.CharField(max_length=120, blank=True)
    brand = models.CharField(max_length=120, blank=True)
    finish = models.CharField(max_length=120, blank=True)
    gloss = models.CharField(max_length=50, blank=True)
    version = models.PositiveIntegerField(default=1, help_text='Incrementa cuando se sube una variante')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='proposed')
    sample_image = models.ImageField(upload_to='color_samples/', null=True, blank=True)
    reference_photo = models.ImageField(upload_to='color_samples/ref/', null=True, blank=True)
    notes = models.TextField(blank=True)
    client_notes = models.TextField(blank=True)
    annotations = models.JSONField(default=dict, blank=True, help_text='Marcadores y comentarios sobre la imagen (JSON)')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='color_samples_created')
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='color_samples_approved')
    approved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    parent_sample = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='variants')

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['project', 'status']),
            models.Index(fields=['project', 'brand', 'code']),
        ]

    def __str__(self):
        base = self.name or self.code or 'Color Sample'
        return f"{base} (v{self.version}) - {self.project.name}"

    def save(self, *args, **kwargs):
        # Auto-increment version if derived from parent
        if self.parent_sample and self.version == 1:
            siblings = ColorSample.objects.filter(parent_sample=self.parent_sample)
            max_v = siblings.aggregate(m=models.Max('version'))['m'] or 1
            self.version = max_v + 1
        # Marcar approved_at si status aprobado y no existe timestamp
        from django.utils import timezone
        if self.status == 'approved' and not self.approved_at:
            self.approved_at = timezone.now()
        super().save(*args, **kwargs)

    def is_active_choice(self):
        return self.status in ['proposed', 'review']

    def can_annotate(self, user):
        # Regla simple: clientes y staff pueden anotar mientras esté en review/proposed
        if not user.is_authenticated:
            return False
        prof = getattr(user, 'profile', None)
        if prof and prof.role in ['client', 'project_manager', 'employee']:
            return self.is_active_choice()
        return user.is_staff and self.is_active_choice()

    def approve(self, user):
        from django.utils import timezone
        self.status = 'approved'
        self.approved_by = user
        self.approved_at = timezone.now()
        self.save(update_fields=['status', 'approved_by', 'approved_at'])

    def reject(self, user, note=None):
        self.status = 'rejected'
        if note:
            self.notes = (self.notes + '\nRechazado: ' + note).strip()
        self.save(update_fields=['status', 'notes'])

# ---------------------
# Planos 2D con pines interactivos
# ---------------------
class FloorPlan(models.Model):
    project = models.ForeignKey('Project', on_delete=models.CASCADE, related_name='floor_plans')
    name = models.CharField(max_length=120, help_text='Nivel o descripción: Planta Baja, Nivel 2, etc.')
    level = models.IntegerField(
        default=0,
        help_text='Nivel numérico: 0=Planta Baja, 1=Nivel 1, 2=Nivel 2, -1=Sótano, etc.'
    )
    level_identifier = models.CharField(
        max_length=50,
        blank=True,
        help_text='Identificador adicional: "Level 0", "Ground Floor", "Basement", etc.'
    )
    image = models.ImageField(upload_to='floor_plans/')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['level', 'name']
        indexes = [
            models.Index(fields=['project', 'level']),
        ]

    def __str__(self):
        level_display = f"Nivel {self.level}" if self.level >= 0 else f"Sótano {abs(self.level)}"
        return f"{self.project.name} · {level_display} · {self.name}"

class PlanPin(models.Model):
    PIN_TYPES = [
        ('note', 'Nota'),
        ('touchup', 'Touch-up'),
        ('color', 'Color'),
        ('alert', 'Alerta'),
        ('damage', 'Daño'),
    ]
    PIN_COLORS = [
        '#0d6efd', '#6610f2', '#6f42c1', '#d63384', '#dc3545',
        '#fd7e14', '#ffc107', '#198754', '#20c997', '#0dcaf0',
    ]
    plan = models.ForeignKey(FloorPlan, on_delete=models.CASCADE, related_name='pins')
    # Coordenadas normalizadas 0..1 relativas al ancho/alto de la imagen
    x = models.DecimalField(max_digits=6, decimal_places=4, help_text='0..1')
    y = models.DecimalField(max_digits=6, decimal_places=4, help_text='0..1')
    title = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    pin_type = models.CharField(max_length=20, choices=PIN_TYPES, default='note')
    color_sample = models.ForeignKey('ColorSample', null=True, blank=True, on_delete=models.SET_NULL, related_name='pins')
    linked_task = models.ForeignKey('Task', null=True, blank=True, on_delete=models.SET_NULL, related_name='pins')
    # Trayectoria multipunto (opcional): JSON array de {x,y,label}
    path_points = models.JSONField(default=list, blank=True, help_text='Lista de puntos conectados: [{x:0.1,y:0.2,label:"A"}]')
    is_multipoint = models.BooleanField(default=False, help_text='Pin con trayectoria multipunto')
    # Color personalizado para diferenciación visual
    pin_color = models.CharField(max_length=7, default='#0d6efd', help_text='Color hex para el pin')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Pin {self.pin_type} @({self.x},{self.y}) on {self.plan}"
    
    def save(self, *args, **kwargs):
        # Auto-asignar color rotativo si no se especificó
        if not self.pin_color or self.pin_color == '#0d6efd':
            existing_count = PlanPin.objects.filter(plan=self.plan).count()
            self.pin_color = self.PIN_COLORS[existing_count % len(self.PIN_COLORS)]
        super().save(*args, **kwargs)

class PlanPinAttachment(models.Model):
    if TYPE_CHECKING:
        pin_id: int
    
    pin = models.ForeignKey(PlanPin, on_delete=models.CASCADE, related_name='attachments')
    image = models.ImageField(upload_to='floor_plans/pins/', null=True, blank=True)
    annotations = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Attachment for Pin {self.pin_id}"

# ---------------------
# Reportes de daños
# ---------------------
class DamageReport(models.Model):
    if TYPE_CHECKING:
        get_severity_display: Callable[[], str]
        get_category_display: Callable[[], str]
    
    SEVERITY_CHOICES = [
        ('low','Bajo'),
        ('medium','Medio'),
        ('high','Alto'),
        ('critical','Crítico'),
    ]
    CATEGORY_CHOICES = [
        ('structural', 'Estructural'),
        ('cosmetic', 'Cosmético'),
        ('safety', 'Seguridad'),
        ('electrical', 'Eléctrico'),
        ('plumbing', 'Plomería'),
        ('hvac', 'HVAC'),
        ('other', 'Otro'),
    ]
    STATUS_CHOICES = [
        ('open','Abierto'),
        ('in_progress','En Progreso'),
        ('resolved','Resuelto'),
    ]
    project = models.ForeignKey('Project', on_delete=models.CASCADE, related_name='damage_reports')
    plan = models.ForeignKey(FloorPlan, on_delete=models.SET_NULL, null=True, blank=True, related_name='damage_reports')
    pin = models.OneToOneField(PlanPin, on_delete=models.SET_NULL, null=True, blank=True, related_name='damage_report')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='other', help_text="Categoría del daño")
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES, default='medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    estimated_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Costo estimado de reparación")
    linked_touchup = models.ForeignKey('TouchUpPin', on_delete=models.SET_NULL, null=True, blank=True, related_name='damage_reports', help_text="Touch-up vinculado si aplica")
    linked_co = models.ForeignKey('ChangeOrder', on_delete=models.SET_NULL, null=True, blank=True, related_name='damage_reports', help_text="Change Order vinculado si aplica")
    reported_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    reported_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True, help_text="Fecha de resolución")

    class Meta:
        ordering = ['-reported_at']

    def __str__(self):
        return f"Damage: {self.title} ({self.get_severity_display()})"

class DamagePhoto(models.Model):
    if TYPE_CHECKING:
        report_id: int
    
    report = models.ForeignKey(DamageReport, on_delete=models.CASCADE, related_name='photos')
    image = models.ImageField(upload_to='damage_reports/')
    notes = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Photo for {self.report_id}"

# ---------------------
# Chat de diseño colaborativo
# ---------------------
class DesignChatMessage(models.Model):
    if TYPE_CHECKING:
        project_id: int
    
    project = models.ForeignKey('Project', on_delete=models.CASCADE, related_name='design_messages')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    message = models.TextField()
    image = models.ImageField(upload_to='design_chat/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    pinned = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"DesignMsg {self.project_id} by {getattr(self.user,'username','?')}"

# ---------------------
# Chat de proyecto (canales)
# ---------------------
class ChatChannel(models.Model):
    CHANNEL_TYPES = [
        ('group', 'Grupo'),
        ('direct', 'Directo'),
    ]
    project = models.ForeignKey('Project', on_delete=models.CASCADE, related_name='chat_channels')
    name = models.CharField(max_length=120)
    channel_type = models.CharField(max_length=10, choices=CHANNEL_TYPES, default='group')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    participants = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='chat_channels', blank=True)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('project', 'name')
        ordering = ['name']

    def __str__(self):
        return f"[{self.project}] {self.name}"

class ChatMessage(models.Model):
    if TYPE_CHECKING:
        id: int
        channel_id: int
    
    channel = models.ForeignKey(ChatChannel, on_delete=models.CASCADE, related_name='messages')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    message = models.TextField(blank=True)
    image = models.ImageField(upload_to='project_chat/', null=True, blank=True)
    link_url = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"ChatMsg ch={self.channel_id} by {getattr(self.user,'username','?')}"

# ---------------------
# Sistema de notificaciones
# ---------------------
class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('task_created', 'Tarea creada'),
        ('task_assigned', 'Tarea asignada'),
        ('task_completed', 'Tarea completada'),
        ('color_review', 'Color en revisión'),
        ('color_approved', 'Color aprobado'),
        ('color_rejected', 'Color rechazado'),
        ('damage_reported', 'Daño reportado'),
        ('chat_message', 'Mensaje en chat'),
        ('comment_added', 'Comentario agregado'),
        ('estimate_approved', 'Estimación aprobada'),
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=30, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField(blank=True)
    # Relación genérica opcional (project, task, color_sample, etc.)
    related_object_type = models.CharField(max_length=50, blank=True)
    related_object_id = models.IntegerField(null=True, blank=True)
    link_url = models.CharField(max_length=255, blank=True, help_text='URL para redirigir al hacer clic')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.notification_type}] {self.title} → {self.user.username}"

    def mark_read(self):
        if not self.is_read:
            self.is_read = True
            self.save(update_fields=['is_read'])
class InventoryItem(models.Model):
    if TYPE_CHECKING:
        get_category_display: Callable[[], str]

    CATEGORY_CHOICES = [
        ("MATERIAL", "Material"),
        ("PINTURA", "Pintura"),
        ("ESCALERA", "Escaleras"),
        ("LIJADORA", "Lijadoras / Power"),
        ("SPRAY", "Sprayadoras / Tips"),
        ("HERRAMIENTA", "Herramientas"),
        ("OTRO", "Otro"),
    ]
    name = models.CharField(max_length=120)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    unit = models.CharField(max_length=20, default="pcs")
    is_equipment = models.BooleanField(default=False)  # reutilizable
    track_serial = models.BooleanField(default=False)
    default_threshold = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    active = models.BooleanField(default=True)
    no_threshold = models.BooleanField(default=False)  # <- debe existir

    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"


class InventoryLocation(models.Model):
    # project null => storage central
    name = models.CharField(max_length=120)
    project = models.ForeignKey("core.Project", null=True, blank=True, on_delete=models.CASCADE, related_name="inventory_locations")
    is_storage = models.BooleanField(default=False)

    def __str__(self):
        if self.project:
            return f"{self.project.name} / {self.name}"
        return f"Storage: {self.name}"


class ProjectInventory(models.Model):
    if TYPE_CHECKING:
        id: int
    
    item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE)
    location = models.ForeignKey(InventoryLocation, on_delete=models.CASCADE, related_name="stocks")
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0"))
    threshold_override = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)

    class Meta:
        unique_together = ("item", "location")

    def threshold(self):
        return self.threshold_override or self.item.default_threshold

    @property
    def is_below(self):
        th = self.threshold()
        return th is not None and self.quantity < th

    def __str__(self):
        return f"{self.location} · {self.item} = {self.quantity}"

class InventoryMovement(models.Model):
    TYPE_CHOICES = [
        ("RECEIVE", "Entrada compra"),
        ("ISSUE", "Salida a uso / consumo"),
        ("TRANSFER", "Traslado"),
        ("RETURN", "Regreso a storage"),
        ("ADJUST", "Ajuste manual"),
        ("CONSUME", "Consumo registrado"),
    ]
    item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE)
    from_location = models.ForeignKey(InventoryLocation, null=True, blank=True, related_name="moves_out", on_delete=models.SET_NULL)
    to_location = models.ForeignKey(InventoryLocation, null=True, blank=True, related_name="moves_in", on_delete=models.SET_NULL)
    movement_type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    note = models.CharField(max_length=255, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expense = models.ForeignKey("core.Expense", null=True, blank=True, on_delete=models.SET_NULL, related_name="inventory_movements")  # NUEVO

    def apply(self):
        # aplica efecto (idempotencia simple: NO volver a aplicar si ya se aplicó => se podría marcar un flag)
        if self.movement_type in ("RECEIVE", "RETURN"):
            if self.to_location:
                stock, _ = ProjectInventory.objects.get_or_create(item=self.item, location=self.to_location)
                stock.quantity += self.quantity
                stock.save()
        elif self.movement_type in ("ISSUE", "CONSUME"):
            if self.from_location:
                stock, _ = ProjectInventory.objects.get_or_create(item=self.item, location=self.from_location)
                stock.quantity -= self.quantity
                if stock.quantity < 0:
                    stock.quantity = Decimal("0")  # o lanzar error
                stock.save()
        elif self.movement_type == "TRANSFER":
            if self.from_location:
                s_from, _ = ProjectInventory.objects.get_or_create(item=self.item, location=self.from_location)
                s_from.quantity -= self.quantity
                if s_from.quantity < 0:
                    s_from.quantity = Decimal("0")
                s_from.save()
            if self.to_location:
                s_to, _ = ProjectInventory.objects.get_or_create(item=self.item, location=self.to_location)
                s_to.quantity += self.quantity
                s_to.save()
        elif self.movement_type == "ADJUST":
            # note describe razón; cantidad positiva suma (negativa restaría si lo permites)
            if self.to_location:
                stock, _ = ProjectInventory.objects.get_or_create(item=self.item, location=self.to_location)
                stock.quantity += self.quantity
                if stock.quantity < 0:
                    stock.quantity = Decimal("0")
                stock.save()

    def __str__(self):
        return f"{self.movement_type} {self.item} {self.quantity}"


# ===========================
# DAILY PLANNING SYSTEM MODELS
# ===========================

class ActivityTemplate(models.Model):
    """
    SOP (Standard Operating Procedure) - Template for common activities
    Used to standardize tasks and educate team
    """
    if TYPE_CHECKING:
        get_category_display: Callable[[], str]
    
    CATEGORY_CHOICES = [
        ('PREP', 'Preparation'),
        ('COVER', 'Covering'),
        ('SAND', 'Sanding'),
        ('STAIN', 'Staining'),
        ('SEAL', 'Sealing'),
        ('PAINT', 'Painting'),
        ('CAULK', 'Caulking'),
        ('CLEANUP', 'Cleanup'),
        ('OTHER', 'Other'),
    ]
    
    name = models.CharField(max_length=200, verbose_name="Activity Name")
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='OTHER')
    description = models.TextField(blank=True, help_text="Overall description of the activity")
    
    # SOP Details
    time_estimate = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Estimated hours to complete"
    )
    steps = models.JSONField(
        default=list,
        help_text="Checklist steps as JSON array. Example: ['Step 1', 'Step 2']"
    )
    materials_list = models.JSONField(
        default=list,
        help_text="Required materials as JSON array"
    )
    tools_list = models.JSONField(
        default=list,
        help_text="Required tools as JSON array"
    )
    tips = models.TextField(blank=True, help_text="Best practices and tips")
    common_errors = models.TextField(blank=True, help_text="Common mistakes to avoid")
    
    # Media
    reference_photos = models.JSONField(
        default=list,
        help_text="URLs or paths to reference photos"
    )
    video_url = models.URLField(blank=True, help_text="YouTube or training video URL")
    
    # NUEVOS CAMPOS: Gamification & Training
    difficulty_level = models.CharField(
        max_length=20,
        choices=[
            ('beginner', 'Beginner'),
            ('intermediate', 'Intermediate'),
            ('advanced', 'Advanced'),
        ],
        default='beginner',
        help_text="Skill level required"
    )
    completion_points = models.IntegerField(
        default=10,
        help_text="Points awarded for completing this SOP"
    )
    badge_awarded = models.CharField(
        max_length=50,
        blank=True,
        help_text="Badge name if special achievement"
    )
    required_tools = models.JSONField(
        default=list,
        help_text="Specific tools needed (for checklist)"
    )
    safety_warnings = models.TextField(
        blank=True,
        help_text="Important safety information"
    )
    
    # Metadata
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_templates')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True, help_text="Hide inactive templates")
    
    class Meta:
        ordering = ['category', 'name']
        verbose_name = "Activity Template (SOP)"
        verbose_name_plural = "Activity Templates (SOPs)"
    
    def __str__(self):
        return f"{self.get_category_display()} - {self.name}"


class DailyPlan(models.Model):
    """
    Daily planning document - must be created before 5pm for next working day
    Forces PMs to think ahead about activities, materials, and assignments
    """
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('SUBMITTED', 'Submitted'),
        ('APPROVED', 'Approved by Admin'),
        ('SKIPPED', 'No Planning Needed'),
    ]
    
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='daily_plans')
    plan_date = models.DateField(verbose_name="Date for this plan", help_text="The work day this plan is for")
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_plans')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    completion_deadline = models.DateTimeField(
        help_text="Deadline to submit plan (usually 5pm day before)"
    )
    
    # For skipped days
    no_planning_reason = models.TextField(
        blank=True,
        help_text="Reason why no planning is needed (e.g., no projects scheduled)"
    )
    admin_approved = models.BooleanField(default=False)
    approved_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='approved_plans'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-plan_date']
        unique_together = ['project', 'plan_date']
        indexes = [
            models.Index(fields=['plan_date', 'status']),
            models.Index(fields=['project', 'plan_date']),
        ]
        verbose_name = "Daily Plan"
        verbose_name_plural = "Daily Plans"
    
    def __str__(self):
        return f"Plan for {self.project.name} on {self.plan_date}"
    
    def is_overdue(self):
        """Check if plan should have been submitted by now"""
        from django.utils import timezone
        return timezone.now() > self.completion_deadline and self.status == 'DRAFT'


class PlannedActivity(models.Model):
    """
    Individual activity within a daily plan
    Can be linked to Schedule item or standalone
    """
    STATUS_CHOICES = [
        ('PENDING', 'Not Started'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('BLOCKED', 'Blocked'),
    ]
    
    if TYPE_CHECKING:
        id: int

    daily_plan = models.ForeignKey(DailyPlan, on_delete=models.CASCADE, related_name='activities')
    
    # Optional link to Schedule item
    schedule_item = models.ForeignKey(
        Schedule, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        help_text="Link to parent schedule item if this is a sub-task"
    )
    
    # Optional link to Activity Template (SOP)
    activity_template = models.ForeignKey(
        ActivityTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="SOP template for this activity"
    )
    
    # Activity details
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    order = models.IntegerField(default=0, help_text="Order in the daily plan")
    
    # Assignment
    assigned_employees = models.ManyToManyField(
        Employee,
        related_name='assigned_activities',
        help_text="Employees assigned to this activity"
    )
    is_group_activity = models.BooleanField(
        default=True,
        help_text="True if all employees work together, False if divided into sub-tasks"
    )
    
    # Planning details
    estimated_hours = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True
    )
    materials_needed = models.JSONField(
        default=list,
        help_text="List of materials needed with quantities"
    )
    materials_checked = models.BooleanField(
        default=False,
        help_text="True if material availability has been verified"
    )
    material_shortage = models.BooleanField(
        default=False,
        help_text="True if materials are insufficient"
    )
    
    # Progress
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    progress_percentage = models.IntegerField(
        default=0,
        help_text="0-100% completion"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['daily_plan', 'order']
        verbose_name = "Planned Activity"
        verbose_name_plural = "Planned Activities"
    
    def __str__(self):
        return f"{self.title} - {self.daily_plan.plan_date}"
    
    def check_materials(self):
        """
        Check if required materials are available in inventory
        Sets materials_checked and material_shortage flags
        
        IMPROVED: Added comprehensive error handling for malformed data
        """
        from decimal import Decimal, InvalidOperation
        from django.db.models import Q
        import logging
        
        logger = logging.getLogger(__name__)

        # Defensive: empty list => trivially OK
        if not self.materials_needed:
            self.materials_checked = True
            self.material_shortage = False
            self.save(update_fields=["materials_checked", "material_shortage"])
            return

        try:
            project = self.daily_plan.project
            shortages = []
            parsed_items = []  # (key, required_qty)

            # Expected simple syntax examples inside JSON list:
            #   "Paint:Sherwin-Williams:2gal"
            #   "Tape:3roll"
            #   "Lija grano 120:10unit"
            # If no quantity suffix, assume 1 unit. Quantity parsing: final token may contain number + unit.
            for raw in self.materials_needed:
                try:
                    if not isinstance(raw, str):
                        logger.warning(f"PlannedActivity {self.id}: Non-string material entry: {raw}")
                        continue
                    
                    if not raw.strip():
                        continue
                    
                    parts = [p.strip() for p in raw.split(":") if p.strip()]
                    required_qty = Decimal("1")
                    name_key = None
                    
                    if len(parts) == 1:
                        name_key = parts[0].lower()
                    else:
                        # Last part may contain quantity e.g. 2gal / 3roll / 5unit
                        *name_tokens, qty_token = parts
                        
                        # detect leading digits in qty_token with improved regex
                        import re
                        m = re.match(r"^(?P<num>\d+(?:\.\d+)?)(?P<unit>[a-zA-Z_]*)$", qty_token.strip())
                        
                        if m:
                            try:
                                required_qty = Decimal(m.group("num"))
                                unit_suffix = m.group("unit") or "unit"
                            except (InvalidOperation, ValueError) as e:
                                logger.warning(f"PlannedActivity {self.id}: Invalid quantity '{m.group('num')}' in '{raw}': {e}")
                                required_qty = Decimal("1")
                        else:
                            name_tokens.append(qty_token)  # treat as part of name
                            unit_suffix = "unit"
                        
                        name_key = ":".join(t.lower() for t in name_tokens)
                    
                    if name_key:
                        parsed_items.append((name_key, required_qty))
                        
                except Exception as e:
                    logger.error(f"PlannedActivity {self.id}: Error parsing material '{raw}': {e}")
                    continue

            # Build quick lookup for inventory by item name (case-insensitive contains)
            try:
                from .models import InventoryItem, ProjectInventory, InventoryLocation
            except ImportError:
                # Fallback if circular import
                InventoryItem = apps.get_model("core", "InventoryItem")
                ProjectInventory = apps.get_model("core", "ProjectInventory")
                InventoryLocation = apps.get_model("core", "InventoryLocation")

            # Prefer project-specific locations first; fallback to any storage location
            project_locations = InventoryLocation.objects.filter(Q(project=project) | Q(project__isnull=True))
            location_ids = list(project_locations.values_list("id", flat=True))
            stocks = ProjectInventory.objects.filter(location_id__in=location_ids).select_related("item", "location")

            # Aggregate available quantities per lowercase item name
            available_map = {}
            for s in stocks:
                try:
                    key = s.item.name.lower()  # type: ignore[attr-defined]
                    available_map[key] = available_map.get(key, Decimal("0")) + (s.quantity or Decimal("0"))  # type: ignore[attr-defined]
                except Exception as e:
                    logger.warning(f"PlannedActivity {self.id}: Error processing stock item {s.id}: {e}")  # type: ignore[attr-defined]
                    continue

            for key, required in parsed_items:
                try:
                    # Find closest match: direct key or contains logic
                    qty_available = None
                    if key in available_map:
                        qty_available = available_map[key]
                    else:
                        # fuzzy contains
                        matches = [k for k in available_map.keys() if key in k or k in key]
                        if matches:
                            qty_available = sum(available_map[m] for m in matches)
                    
                    if qty_available is None or qty_available < required:
                        shortages.append({
                            "material": key, 
                            "required": str(required), 
                            "available": str(qty_available or 0)
                        })
                except Exception as e:
                    logger.error(f"PlannedActivity {self.id}: Error checking availability for '{key}': {e}")
                    continue

            self.materials_checked = True
            self.material_shortage = bool(shortages)
            
            # Persist shortage details in description tail if shortage present (non‑destructive append)
            if shortages:
                import json
                try:
                    shortage_text = f"\n[MATERIAL SHORTAGE]\n" + json.dumps(shortages, ensure_ascii=False, indent=2)
                    if shortage_text not in (self.description or ""):
                        self.description = (self.description or "") + shortage_text
                except Exception as e:
                    logger.error(f"PlannedActivity {self.id}: Error serializing shortages: {e}")
            
            # Save changes
            if shortages:
                self.save(update_fields=["materials_checked", "material_shortage", "description"])
            else:
                self.save(update_fields=["materials_checked", "material_shortage"])
                    
        except Exception as e:
            # Catch-all to prevent complete failure
            logger.error(f"PlannedActivity {self.id}: Critical error in check_materials(): {e}", exc_info=True)
            self.materials_checked = False
            self.material_shortage = False
            self.save(update_fields=["materials_checked", "material_shortage"])


class ActivityCompletion(models.Model):
    """
    Record of completed activity with photos and employee notes
    Used for client reports and progress tracking
    """
    planned_activity = models.OneToOneField(
        PlannedActivity,
        on_delete=models.CASCADE,
        related_name='completion'
    )
    
    completed_by = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        null=True,
        related_name='completed_activities'
    )
    completion_datetime = models.DateTimeField(auto_now_add=True)
    
    # Photos (stored as JSON array of file paths/URLs)
    completion_photos = models.JSONField(
        default=list,
        help_text="Array of photo URLs/paths showing completed work"
    )
    
    # Notes (internal, Spanish)
    employee_notes = models.TextField(
        blank=True,
        help_text="Internal notes from employee (Spanish, not shown to client)"
    )
    
    # Progress indicator
    progress_percentage = models.IntegerField(
        default=100,
        help_text="Completion percentage at time of marking done"
    )
    
    # Verification
    verified_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_completions',
        help_text="PM or Admin who verified this completion"
    )
    verified_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-completion_datetime']
        verbose_name = "Activity Completion"
        verbose_name_plural = "Activity Completions"
    
    def __str__(self):
        return f"Completion: {self.planned_activity.title} by {self.completed_by}"


# ===========================
# SOP REFERENCE FILES
# ===========================

class SOPReferenceFile(models.Model):
    """
    Reference files (photos, PDFs, etc.) attached to Activity Templates (SOPs)
    """
    sop = models.ForeignKey(
        ActivityTemplate,
        on_delete=models.CASCADE,
        related_name='reference_files'
    )
    file = models.FileField(upload_to='sop_references/%Y/%m/%d/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = "SOP Reference File"
        verbose_name_plural = "SOP Reference Files"
    
    def filename(self):
        return self.file.name.split('/')[-1]
    
    def __str__(self):
        return f"{self.sop.name} - {self.filename()}"


# ===========================
# MINUTAS / PROJECT TIMELINE
# ===========================

class ProjectMinute(models.Model):
    """
    Timeline de decisiones, llamadas, aprobaciones y cambios del proyecto.
    Para Admin y Clientes mantener registro histórico de comunicaciones.
    """
    EVENT_TYPE_CHOICES = [
        ('decision', 'Decisión'),
        ('call', 'Llamada'),
        ('email', 'Correo'),
        ('meeting', 'Reunión'),
        ('approval', 'Aprobación'),
        ('change', 'Cambio/Modificación'),
        ('issue', 'Problema'),
        ('milestone', 'Hito'),
        ('note', 'Nota'),
    ]
    
    if TYPE_CHECKING:
        get_event_type_display: Callable[[], str]

    project = models.ForeignKey('Project', on_delete=models.CASCADE, related_name='minutes')
    event_type = models.CharField(max_length=20, choices=EVENT_TYPE_CHOICES, default='note')
    title = models.CharField(max_length=200, help_text="Resumen breve del evento")
    description = models.TextField(blank=True, help_text="Detalles completos")
    
    # Quién y cuándo
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='minutes_created')
    created_at = models.DateTimeField(auto_now_add=True)
    event_date = models.DateTimeField(help_text="Fecha/hora del evento real (puede ser diferente de created_at)")
    
    # Participantes (opcional)
    participants = models.TextField(blank=True, help_text="Nombres de participantes en llamada/reunión")
    
    # Archivos adjuntos
    attachment = models.FileField(upload_to='minutes/%Y/%m/', blank=True, null=True)
    
    # Visibilidad
    visible_to_client = models.BooleanField(default=True, help_text="¿El cliente puede ver esta minuta?")
    
    class Meta:
        ordering = ['-event_date']
        verbose_name = "Project Minute"
        verbose_name_plural = "Project Minutes"
    
    def __str__(self):
        return f"{self.project.name} - {self.get_event_type_display()} - {self.title}"


# ===========================
# EARNED VALUE SNAPSHOTS
# ===========================

class EVSnapshot(models.Model):
    """
    Daily snapshot of Earned Value metrics for trending and forecasting.
    Generated automatically by Celery task at 6 PM after employee clock out.
    """
    project = models.ForeignKey('Project', on_delete=models.CASCADE, related_name='ev_snapshots')
    date = models.DateField(help_text="Date of this snapshot")
    
    # Core EV metrics
    planned_value = models.DecimalField(max_digits=12, decimal_places=2, help_text="PV - Budgeted cost of work scheduled")
    earned_value = models.DecimalField(max_digits=12, decimal_places=2, help_text="EV - Budgeted cost of work performed")
    actual_cost = models.DecimalField(max_digits=12, decimal_places=2, help_text="AC - Actual cost of work performed")
    
    # Performance indices
    spi = models.DecimalField(max_digits=5, decimal_places=3, help_text="Schedule Performance Index (EV/PV)")
    cpi = models.DecimalField(max_digits=5, decimal_places=3, help_text="Cost Performance Index (EV/AC)")
    
    # Variances
    schedule_variance = models.DecimalField(max_digits=12, decimal_places=2, help_text="SV = EV - PV")
    cost_variance = models.DecimalField(max_digits=12, decimal_places=2, help_text="CV = EV - AC")
    
    # Forecasts
    estimate_at_completion = models.DecimalField(max_digits=12, decimal_places=2, help_text="EAC - Forecasted final cost")
    estimate_to_complete = models.DecimalField(max_digits=12, decimal_places=2, help_text="ETC - Remaining cost")
    variance_at_completion = models.DecimalField(max_digits=12, decimal_places=2, help_text="VAC = BAC - EAC")
    
    # Completion estimates
    percent_complete = models.DecimalField(max_digits=5, decimal_places=2, help_text="% of project complete")
    percent_spent = models.DecimalField(max_digits=5, decimal_places=2, help_text="% of budget spent")
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-date']
        unique_together = ['project', 'date']
        verbose_name = "EV Snapshot"
        verbose_name_plural = "EV Snapshots"
        indexes = [
            models.Index(fields=['project', '-date']),
        ]
    
    def __str__(self):
        return f"{self.project.name} - {self.date} (SPI:{self.spi}, CPI:{self.cpi})"


# ===========================
# QUALITY CONTROL
# ===========================

class QualityInspection(models.Model):
    """
    Quality control inspections with automated workflows and AI defect detection.
    """
    INSPECTION_TYPE_CHOICES = [
        ('initial', 'Initial Inspection'),
        ('progress', 'Progress Inspection'),
        ('final', 'Final Inspection'),
        ('warranty', 'Warranty Inspection'),
        ('defect_followup', 'Defect Follow-up'),
    ]
    
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('passed', 'Passed'),
        ('failed', 'Failed'),
        ('conditional', 'Conditional Pass'),
    ]
    
    if TYPE_CHECKING:
        get_inspection_type_display: Callable[[], str]

    project = models.ForeignKey('Project', on_delete=models.CASCADE, related_name='quality_inspections')
    inspection_type = models.CharField(max_length=20, choices=INSPECTION_TYPE_CHOICES)
    scheduled_date = models.DateField()
    completed_date = models.DateField(null=True, blank=True)
    
    inspector = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='inspections_performed')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    
    # AI-assisted scoring
    overall_score = models.IntegerField(null=True, blank=True, help_text="0-100 quality score")
    ai_defect_count = models.IntegerField(default=0, help_text="Defects detected by AI")
    manual_defect_count = models.IntegerField(default=0, help_text="Defects found manually")
    
    notes = models.TextField(blank=True)
    checklist_data = models.JSONField(default=dict, blank=True, help_text="Inspection checklist results")
    
    # Warranty tracking
    warranty_expiration = models.DateField(null=True, blank=True)
    warranty_notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-scheduled_date']
        verbose_name = "Quality Inspection"
        verbose_name_plural = "Quality Inspections"
    
    def __str__(self):
        return f"{self.project.name} - {self.get_inspection_type_display()} - {self.scheduled_date}"


class QualityDefect(models.Model):
    """
    Individual defects found during inspections with AI pattern detection.
    """
    SEVERITY_CHOICES = [
        ('minor', 'Minor'),
        ('moderate', 'Moderate'),
        ('major', 'Major'),
        ('critical', 'Critical'),
    ]
    
    if TYPE_CHECKING:
        get_severity_display: Callable[[], str]

    inspection = models.ForeignKey(QualityInspection, on_delete=models.CASCADE, related_name='defects')
    detected_by_ai = models.BooleanField(default=False)
    
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES)
    category = models.CharField(max_length=100, help_text="e.g., Paint finish, Trim alignment, etc.")
    description = models.TextField()
    location = models.CharField(max_length=200, help_text="Room/area where defect was found")
    
    # AI data
    ai_confidence = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text="AI confidence % (0-100)")
    ai_pattern_match = models.CharField(max_length=100, blank=True, help_text="Pattern matched by AI")
    
    # Resolution
    resolved = models.BooleanField(default=False)
    resolved_date = models.DateField(null=True, blank=True)
    resolved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='defects_resolved')
    resolution_notes = models.TextField(blank=True)
    
    # Photos
    photo = models.ImageField(upload_to='quality/defects/%Y/%m/', null=True, blank=True)
    resolution_photo = models.ImageField(upload_to='quality/resolutions/%Y/%m/', null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Quality Defect"
        verbose_name_plural = "Quality Defects"
    
    def __str__(self):
        return f"{self.inspection.project.name} - {self.category} ({self.get_severity_display()})"


# ===========================
# RECURRING TASKS
# ===========================

class RecurringTask(models.Model):
    """
    Template for tasks that repeat on a schedule.
    Auto-generates Task instances based on frequency.
    """
    if TYPE_CHECKING:
        get_frequency_display: Callable[[], str]

    FREQUENCY_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('biweekly', 'Bi-weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
    ]
    
    project = models.ForeignKey('Project', on_delete=models.CASCADE, related_name='recurring_tasks')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES)
    start_date = models.DateField(help_text="When to start generating tasks")
    end_date = models.DateField(null=True, blank=True, help_text="When to stop (null = no end)")
    
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='recurring_tasks_assigned')
    cost_code = models.ForeignKey('CostCode', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Template data
    checklist = models.JSONField(default=list, blank=True, help_text="Checklist items for auto-generated tasks")
    estimated_hours = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    active = models.BooleanField(default=True)
    last_generated = models.DateField(null=True, blank=True, help_text="Last date a task was generated")
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Recurring Task"
        verbose_name_plural = "Recurring Tasks"
    
    def __str__(self):
        return f"{self.project.name} - {self.title} ({self.get_frequency_display()})"


# ===========================
# EMPLOYEE GPS CHECK-IN/OUT
# ===========================

class GPSCheckIn(models.Model):
    """
    GPS-validated employee check-ins for time tracking accuracy.
    """
    employee = models.ForeignKey('Employee', on_delete=models.CASCADE, related_name='gps_checkins')
    project = models.ForeignKey('Project', on_delete=models.CASCADE, related_name='gps_checkins')
    time_entry = models.ForeignKey('TimeEntry', on_delete=models.SET_NULL, null=True, blank=True, related_name='gps_checkin')
    
    check_in_time = models.DateTimeField()
    check_in_latitude = models.DecimalField(max_digits=9, decimal_places=6)
    check_in_longitude = models.DecimalField(max_digits=9, decimal_places=6)
    check_in_accuracy = models.DecimalField(max_digits=5, decimal_places=2, help_text="GPS accuracy in meters")
    
    check_out_time = models.DateTimeField(null=True, blank=True)
    check_out_latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    check_out_longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    check_out_accuracy = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    # Validation
    within_geofence = models.BooleanField(default=True, help_text="Was check-in within project geofence?")
    distance_from_project = models.DecimalField(max_digits=8, decimal_places=2, help_text="Distance in meters")
    flagged_for_review = models.BooleanField(default=False)
    review_notes = models.TextField(blank=True)
    
    # Auto-break detection
    auto_break_detected = models.BooleanField(default=False)
    auto_break_minutes = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['-check_in_time']
        verbose_name = "GPS Check-In"
        verbose_name_plural = "GPS Check-Ins"
    
    def __str__(self):
        return f"{self.employee} - {self.project.name} - {self.check_in_time.date()}"


# ===========================
# OCR EXPENSE RECEIPTS
# ===========================

class ExpenseOCRData(models.Model):
    """
    OCR-extracted data from expense receipts using pytesseract + OpenCV.
    """
    expense = models.OneToOneField('Expense', on_delete=models.CASCADE, related_name='ocr_data')
    
    # Extracted fields
    vendor_name = models.CharField(max_length=200, blank=True)
    transaction_date = models.DateField(null=True, blank=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Line items
    line_items = models.JSONField(default=list, blank=True, help_text="Extracted line items from receipt")
    
    # OCR metadata
    ocr_confidence = models.DecimalField(max_digits=5, decimal_places=2, help_text="OCR confidence % (0-100)")
    raw_text = models.TextField(blank=True, help_text="Full raw OCR text")
    
    # Auto-categorization
    suggested_category = models.CharField(max_length=100, blank=True)
    suggested_cost_code = models.ForeignKey('CostCode', on_delete=models.SET_NULL, null=True, blank=True)
    ai_suggestion_confidence = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    # Review
    verified = models.BooleanField(default=False)
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    verification_notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Expense OCR Data"
        verbose_name_plural = "Expense OCR Data"
    
    def __str__(self):
        return f"OCR for {self.expense} - {self.vendor_name}"


# ===========================
# INVOICE AUTOMATION
# ===========================

class InvoiceAutomation(models.Model):
    """
    Automation settings for recurring invoices and email reminders.
    """
    invoice = models.OneToOneField('Invoice', on_delete=models.CASCADE, related_name='automation')
    
    # Recurring settings
    is_recurring = models.BooleanField(default=False)
    recurrence_frequency = models.CharField(
        max_length=20,
        choices=[
            ('weekly', 'Weekly'),
            ('biweekly', 'Bi-weekly'),
            ('monthly', 'Monthly'),
            ('quarterly', 'Quarterly'),
        ],
        blank=True
    )
    next_recurrence_date = models.DateField(null=True, blank=True)
    recurrence_end_date = models.DateField(null=True, blank=True, help_text="When to stop auto-generating")
    
    # Email automation
    auto_send_on_creation = models.BooleanField(default=False)
    auto_remind_before_due = models.IntegerField(default=3, help_text="Days before due date to send reminder")
    auto_remind_after_due = models.BooleanField(default=True, help_text="Send reminders for overdue invoices")
    reminder_frequency_days = models.IntegerField(default=7, help_text="How often to remind after due")
    
    # Late fees
    apply_late_fees = models.BooleanField(default=False)
    late_fee_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('1.5'), help_text="% per month")
    late_fee_grace_days = models.IntegerField(default=5, help_text="Days after due before applying fee")
    
    # Payment gateway
    stripe_payment_intent_id = models.CharField(max_length=200, blank=True)
    payment_link = models.URLField(blank=True, help_text="Direct payment link for client")
    
    last_reminder_sent = models.DateField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Invoice Automation"
        verbose_name_plural = "Invoice Automations"
    
    def __str__(self):
        return f"Automation for {self.invoice}"


# ===========================
# BARCODE INVENTORY
# ===========================

class InventoryBarcode(models.Model):
    """
    Barcode tracking for inventory items using python-barcode + pyzbar.
    """
    item = models.ForeignKey('InventoryItem', on_delete=models.CASCADE, related_name='barcodes')
    
    barcode_type = models.CharField(
        max_length=20,
        choices=[
            ('CODE128', 'Code 128'),
            ('CODE39', 'Code 39'),
            ('EAN13', 'EAN-13'),
            ('UPC', 'UPC'),
            ('QR', 'QR Code'),
        ],
        default='CODE128'
    )
    barcode_value = models.CharField(max_length=100, unique=True)
    barcode_image = models.ImageField(upload_to='inventory/barcodes/', blank=True)
    
    # Auto-reorder
    enable_auto_reorder = models.BooleanField(default=False)
    reorder_point = models.DecimalField(max_digits=10, decimal_places=2, help_text="Trigger reorder when stock below this")
    reorder_quantity = models.DecimalField(max_digits=10, decimal_places=2, help_text="How much to reorder")
    preferred_vendor = models.CharField(max_length=200, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Inventory Barcode"
        verbose_name_plural = "Inventory Barcodes"
    
    def __str__(self):
        return f"{self.item.name} - {self.barcode_value}"
    if TYPE_CHECKING:
        get_unit_display: Callable[[], str]
        get_category_display: Callable[[], str]


# ===========================
# NUEVAS FUNCIONALIDADES 2025
# ===========================

# ---------------------
# Punch List (Quality Control)
# ---------------------
class PunchListItem(models.Model):
    """
    Digital punch list for final quality control.
    Track defects/issues that need to be fixed before project completion.
    """
    project = models.ForeignKey('Project', on_delete=models.CASCADE, related_name='punchlist_items')
    location = models.CharField(max_length=200, help_text="e.g., 'Living Room - North Wall'")
    description = models.TextField()
    priority = models.CharField(
        max_length=20,
        choices=[
            ('critical', 'Critical'),
            ('high', 'High'),
            ('medium', 'Medium'),
            ('low', 'Low'),
        ],
        default='medium'
    )
    category = models.CharField(
        max_length=50,
        choices=[
            ('paint', 'Paint'),
            ('trim', 'Trim'),
            ('cleanup', 'Cleanup'),
            ('repair', 'Repair'),
            ('touch_up', 'Touch Up'),
            ('other', 'Other'),
        ],
        default='paint'
    )
    assigned_to = models.ForeignKey('Employee', on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_punchlist_items')
    photo = models.ImageField(upload_to='punchlist/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_punchlist_items')
    completed_at = models.DateTimeField(null=True, blank=True)
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_punchlist_items')
    verified_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ('open', 'Open'),
            ('in_progress', 'In Progress'),
            ('completed', 'Completed'),
            ('verified', 'Verified'),
        ],
        default='open'
    )
    notes = models.TextField(blank=True)
    
    class Meta:
        verbose_name = "Punch List Item"
        verbose_name_plural = "Punch List Items"
        ordering = ['-priority', 'created_at']
    
    def __str__(self):
        return f"{self.project.name} - {self.location}: {self.description[:50]}"


# ---------------------
# Subcontractor Management
# ---------------------
class Subcontractor(models.Model):
    """
    Manage subcontractors and their information.
    Track credentials, ratings, and compliance.
    """
    company_name = models.CharField(max_length=200)
    contact_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    address = models.TextField(blank=True)
    
    specialty = models.CharField(
        max_length=50,
        choices=[
            ('electrical', 'Electrical'),
            ('plumbing', 'Plumbing'),
            ('hvac', 'HVAC'),
            ('flooring', 'Flooring'),
            ('drywall', 'Drywall'),
            ('carpentry', 'Carpentry'),
            ('roofing', 'Roofing'),
            ('landscaping', 'Landscaping'),
            ('other', 'Other'),
        ]
    )
    
    if TYPE_CHECKING:
        get_specialty_display: Callable[[], str]
    
    hourly_rate = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=Decimal("5.0"), help_text="0-5 stars")
    
    # Compliance
    insurance_verified = models.BooleanField(default=False)
    insurance_expires = models.DateField(null=True, blank=True)
    w9_on_file = models.BooleanField(default=False)
    license_number = models.CharField(max_length=100, blank=True)
    
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Subcontractor"
        verbose_name_plural = "Subcontractors"
        ordering = ['company_name']
    
    def __str__(self):
        return f"{self.company_name} ({self.get_specialty_display()})"


class SubcontractorAssignment(models.Model):
    """
    Assign subcontractors to specific projects.
    Track scope, timeline, and payments.
    """
    project = models.ForeignKey('Project', on_delete=models.CASCADE, related_name='subcontractor_assignments')
    subcontractor = models.ForeignKey('Subcontractor', on_delete=models.CASCADE, related_name='assignments')
    
    scope_of_work = models.TextField()
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    
    contract_amount = models.DecimalField(max_digits=10, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('active', 'Active'),
            ('completed', 'Completed'),
            ('cancelled', 'Cancelled'),
        ],
        default='pending'
    )
    
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Subcontractor Assignment"
        verbose_name_plural = "Subcontractor Assignments"
    
    def __str__(self):
        return f"{self.subcontractor.company_name} - {self.project.name}"
    
    @property
    def balance_due(self):
        return self.contract_amount - self.amount_paid


# ---------------------
# Employee Performance Tracking (para bonos)
# ---------------------
class EmployeePerformanceMetric(models.Model):
    """
    Track employee performance metrics automatically.
    Used for annual bonus evaluation.
    """
    employee = models.ForeignKey('Employee', on_delete=models.CASCADE, related_name='performance_metrics')
    
    # Period
    year = models.IntegerField()
    month = models.IntegerField(null=True, blank=True, help_text="Leave blank for annual metrics")
    
    # Auto-calculated metrics
    total_hours_worked = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    billable_hours = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    productivity_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"), help_text="% billable hours")
    
    # Quality metrics
    defects_created = models.IntegerField(default=0, help_text="Touch-ups/rework assigned to this employee")
    tasks_completed = models.IntegerField(default=0)
    tasks_on_time = models.IntegerField(default=0)
    
    # Attendance
    days_worked = models.IntegerField(default=0)
    days_late = models.IntegerField(default=0)
    days_absent = models.IntegerField(default=0)
    
    # Manual ratings (PM/Admin inputs)
    quality_rating = models.IntegerField(null=True, blank=True, help_text="1-5 stars")
    attitude_rating = models.IntegerField(null=True, blank=True, help_text="1-5 stars")
    teamwork_rating = models.IntegerField(null=True, blank=True, help_text="1-5 stars")
    
    # Bonus
    bonus_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    bonus_notes = models.TextField(blank=True)
    bonus_paid = models.BooleanField(default=False)
    bonus_paid_date = models.DateField(null=True, blank=True)
    
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Employee Performance Metric"
        verbose_name_plural = "Employee Performance Metrics"
        unique_together = ['employee', 'year', 'month']
        ordering = ['-year', '-month']
    
    def __str__(self):
        period = f"{self.year}" if not self.month else f"{self.year}-{self.month:02d}"
        return f"{self.employee} - {period}"
    
    @property
    def overall_score(self):
        """Calculate overall performance score (0-100)"""
        scores = []
        
        # Productivity (30%)
        if self.productivity_rate:
            scores.append(float(self.productivity_rate) * 0.3)
        
        # Quality (25%)
        if self.quality_rating:
            scores.append((self.quality_rating / 5 * 100) * 0.25)
        
        # Attitude (25%)
        if self.attitude_rating:
            scores.append((self.attitude_rating / 5 * 100) * 0.25)
        
        # Attendance (20%)
        if self.days_worked > 0:
            attendance_score = ((self.days_worked - self.days_late - self.days_absent) / self.days_worked * 100) * 0.2
            scores.append(attendance_score)
        
        return sum(scores) if scores else 0


# ---------------------
# Employee Certifications & Skills
# ---------------------
class EmployeeCertification(models.Model):
    """
    Track employee certifications and skill levels.
    Supports internal training programs and gamification.
    """
    employee = models.ForeignKey('Employee', on_delete=models.CASCADE, related_name='certifications')
    certification_name = models.CharField(max_length=100)
    
    skill_category = models.CharField(
        max_length=50,
        choices=[
            ('painting', 'Painting'),
            ('drywall', 'Drywall'),
            ('carpentry', 'Carpentry'),
            ('safety', 'Safety'),
            ('equipment', 'Equipment Operation'),
            ('leadership', 'Leadership'),
            ('customer_service', 'Customer Service'),
        ]
    )
    
    date_earned = models.DateField(auto_now_add=True)
    expires_at = models.DateField(null=True, blank=True)
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    certificate_number = models.CharField(max_length=50, unique=True)
    
    notes = models.TextField(blank=True)
    
    class Meta:
        verbose_name = "Employee Certification"
        verbose_name_plural = "Employee Certifications"
        ordering = ['-date_earned']
    
    def __str__(self):
        return f"{self.employee} - {self.certification_name}"
    
    @property
    def is_expired(self):
        if not self.expires_at:
            return False
        return datetime.now().date() > self.expires_at


class EmployeeSkillLevel(models.Model):
    """
    Track employee skill progression.
    Supports gamification and training programs.
    """
    employee = models.ForeignKey('Employee', on_delete=models.CASCADE, related_name='skill_levels')
    skill = models.CharField(max_length=100)
    level = models.IntegerField(default=1, help_text="1-5 (Beginner to Expert)")
    
    assessments_passed = models.IntegerField(default=0)
    total_points = models.IntegerField(default=0)
    
    last_assessment_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Employee Skill Level"
        verbose_name_plural = "Employee Skill Levels"
        unique_together = ['employee', 'skill']
    
    def __str__(self):
        return f"{self.employee} - {self.skill} (Level {self.level})"


# ---------------------
# Enhanced SOP (with gamification)
# ---------------------
class SOPCompletion(models.Model):
    """
    Track SOP completions for gamification.
    Award points and badges.
    """
    employee = models.ForeignKey('Employee', on_delete=models.CASCADE, related_name='sop_completions')
    sop = models.ForeignKey('ActivityTemplate', on_delete=models.CASCADE, related_name='completions')
    
    completed_at = models.DateTimeField(auto_now_add=True)
    time_taken = models.DurationField(null=True, blank=True)
    
    score = models.IntegerField(null=True, blank=True, help_text="Quiz score if applicable")
    passed = models.BooleanField(default=True)
    
    points_awarded = models.IntegerField(default=10)
    badge_awarded = models.CharField(max_length=50, blank=True)
    
    notes = models.TextField(blank=True)
    
    class Meta:
        verbose_name = "SOP Completion"
        verbose_name_plural = "SOP Completions"
        unique_together = ['employee', 'sop']
    
    
    def __str__(self):
        return f"{self.employee} completed {self.sop.name}"


# ---------------------
# Paint Leftovers / Sobras de Pintura
# ---------------------
class PaintLeftover(models.Model):
    """
    Registro de sobras de pintura al final de proyecto.
    Permite rastrear cantidad restante y ubicación para reutilización.
    """
    project = models.ForeignKey(
        'Project',
        on_delete=models.CASCADE,
        related_name='paint_leftovers'
    )
    color_sample = models.ForeignKey(
        'ColorSample',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='leftovers'
    )
    brand = models.CharField(max_length=100, help_text="Marca de pintura (ej: Sherwin Williams)")
    color_name = models.CharField(max_length=200, help_text="Nombre del color (ej: SW 7008 Alabaster)")
    color_code = models.CharField(max_length=100, blank=True, help_text="Código del color")
    finish = models.CharField(
        max_length=50,
        choices=[
            ('flat', 'Flat'),
            ('matte', 'Matte'),
            ('eggshell', 'Eggshell'),
            ('satin', 'Satin'),
            ('semi_gloss', 'Semi-Gloss'),
            ('gloss', 'Gloss'),
        ],
        default='flat'
    )
    quantity_gallons = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        help_text="Cantidad en galones"
    )
    container_type = models.CharField(
        max_length=50,
        choices=[
            ('gallon', '1 Galón'),
            ('quart', 'Cuarto'),
            ('pint', 'Pinta'),
            ('other', 'Otro'),
        ],
        default='gallon'
    )
    num_containers = models.IntegerField(default=1, help_text="Número de contenedores")
    location = models.ForeignKey(
        'InventoryLocation',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Ubicación donde se almacena"
    )
    location_notes = models.CharField(max_length=255, blank=True, help_text="Notas de ubicación específica")
    condition = models.CharField(
        max_length=50,
        choices=[
            ('excellent', 'Excelente'),
            ('good', 'Buena'),
            ('fair', 'Regular'),
            ('poor', 'Mala - No usar'),
        ],
        default='good'
    )
    date_stored = models.DateField(auto_now_add=True)
    expiration_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='paint_leftovers_created'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-date_stored']
        verbose_name = "Paint Leftover"
        verbose_name_plural = "Paint Leftovers"
    
    def __str__(self):
        return f"{self.brand} - {self.color_name} ({self.quantity_gallons}gal)"
    
    def is_expired(self):
        if self.expiration_date:
            return timezone.now().date() > self.expiration_date
        return False


# ========================================================================================
# FILE ORGANIZATION SYSTEM
# ========================================================================================

class FileCategory(models.Model):
    """Categories for organizing project files"""
    if TYPE_CHECKING:
        id: int
        files: "RelatedManager[ProjectFile]"
    
    CATEGORY_TYPES = [
        ('daily_logs', 'Daily Logs Photos'),
        ('documents', 'Documents'),
        ('datasheets', 'Datasheets'),
        ('cos_signed', 'COs Firmados'),
        ('invoices', 'Invoices'),
        ('contracts', 'Contracts'),
        ('permits', 'Permits'),
        ('drawings', 'Drawings'),
        ('photos', 'Project Photos'),
        ('reports', 'Reports'),
        ('other', 'Other'),
    ]
    
    project = models.ForeignKey(
        'Project',
        on_delete=models.CASCADE,
        related_name='file_categories'
    )
    name = models.CharField(max_length=100)
    category_type = models.CharField(
        max_length=20,
        choices=CATEGORY_TYPES,
        default='other'
    )
    description = models.TextField(blank=True)
    icon = models.CharField(
        max_length=50,
        default='bi-folder',
        help_text='Bootstrap icon class (e.g., bi-folder, bi-file-earmark)'
    )
    color = models.CharField(
        max_length=20,
        default='primary',
        help_text='Bootstrap color (primary, success, danger, etc.)'
    )
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    class Meta:
        ordering = ['order', 'name']
        unique_together = ['project', 'name']
        verbose_name = "File Category"
        verbose_name_plural = "File Categories"
    
    def __str__(self):
        return f"{self.project.name} - {self.name}"
    
    def file_count(self):
        """Count files in this category"""
        return self.files.count()
    
    def total_size(self):
        """Calculate total size of files in bytes"""
        return sum(f.file.size for f in self.files.all() if f.file)


class ProjectFile(models.Model):
    """Files organized by categories within projects"""
    if TYPE_CHECKING:
        id: int
    
    FILE_TYPES = [
        ('pdf', 'PDF Document'),
        ('image', 'Image'),
        ('spreadsheet', 'Spreadsheet'),
        ('word', 'Word Document'),
        ('cad', 'CAD Drawing'),
        ('other', 'Other'),
    ]
    
    project = models.ForeignKey(
        'Project',
        on_delete=models.CASCADE,
        related_name='files'
    )
    category = models.ForeignKey(
        FileCategory,
        on_delete=models.CASCADE,
        related_name='files'
    )
    file = models.FileField(upload_to='project_files/%Y/%m/')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    file_type = models.CharField(
        max_length=20,
        choices=FILE_TYPES,
        default='other'
    )
    file_size = models.BigIntegerField(default=0, help_text='Size in bytes')
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='uploaded_files'
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Optional metadata
    tags = models.CharField(
        max_length=255,
        blank=True,
        help_text='Comma-separated tags'
    )
    is_public = models.BooleanField(
        default=False,
        help_text='Visible to clients'
    )
    version = models.CharField(
        max_length=20,
        blank=True,
        help_text='Document version (e.g., v1.0, Rev A)'
    )
    
    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = "Project File"
        verbose_name_plural = "Project Files"
    
    def __str__(self):
        return f"{self.name} ({self.category.name})"
    
    def save(self, *args, **kwargs):
        # Auto-set file size and detect file type
        if self.file:
            self.file_size = self.file.size
            
            # Auto-detect file type from extension
            ext = self.file.name.split('.')[-1].lower()
            type_map = {
                'pdf': 'pdf',
                'jpg': 'image', 'jpeg': 'image', 'png': 'image', 'gif': 'image',
                'xls': 'spreadsheet', 'xlsx': 'spreadsheet', 'csv': 'spreadsheet',
                'doc': 'word', 'docx': 'word',
                'dwg': 'cad', 'dxf': 'cad',
            }
            self.file_type = type_map.get(ext, 'other')
        
        super().save(*args, **kwargs)
    
    def get_icon(self):
        """Get Bootstrap icon based on file type"""
        icons = {
            'pdf': 'bi-file-pdf',
            'image': 'bi-file-image',
            'spreadsheet': 'bi-file-spreadsheet',
            'word': 'bi-file-word',
            'cad': 'bi-file-ruled',
            'other': 'bi-file-earmark',
        }
        return icons.get(self.file_type, 'bi-file-earmark')
    
    def get_size_display(self):
        """Human-readable file size"""
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"


# ========================================================================================
# TOUCH-UP SYSTEM (Separate from Info Pins)
# ========================================================================================

class TouchUpPin(models.Model):
    """
    Touch-up pins for paint/finishing work - separate workflow from info pins
    - PM/Admin creates and assigns to employee
    - Employee can only view and close with completion photo
    - Closed pins move to history and are removed from active view
    """
    if TYPE_CHECKING:
        id: int
        completion_photos: "RelatedManager[TouchUpCompletionPhoto]"
    
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('in_progress', 'En Progreso'),
        ('completed', 'Completado'),
        ('archived', 'Archivado'),
    ]
    
    APPROVAL_CHOICES = [
        ('pending_review', 'Pendiente de Revisión'),
        ('approved', 'Aprobado'),
        ('rejected', 'Rechazado'),
    ]
    
    # Location
    plan = models.ForeignKey(
        FloorPlan,
        on_delete=models.CASCADE,
        related_name='touchup_pins'
    )
    x = models.DecimalField(
        max_digits=6,
        decimal_places=4,
        help_text='Normalized X coordinate (0..1)'
    )
    y = models.DecimalField(
        max_digits=6,
        decimal_places=4,
        help_text='Normalized Y coordinate (0..1)'
    )
    
    # Task info
    task_name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Paint/Color details
    approved_color = models.ForeignKey(
        'ColorSample',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='touchup_pins'
    )
    custom_color_name = models.CharField(
        max_length=100,
        blank=True,
        help_text='If not using approved color'
    )
    sheen = models.CharField(
        max_length=50,
        blank=True,
        help_text='Brillo: Matte, Satin, Semi-gloss, Gloss'
    )
    details = models.TextField(
        blank=True,
        help_text='Additional details about the touch-up'
    )
    
    # Assignment
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_touchups'
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_touchups'
    )
    
    # Status tracking
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    approval_status = models.CharField(
        max_length=20,
        choices=APPROVAL_CHOICES,
        default='pending_review',
        help_text='Estado de aprobación de la completion'
    )
    rejection_reason = models.TextField(
        blank=True,
        help_text='Motivo del rechazo si aplica'
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_touchups',
        help_text='PM/Admin que revisó el completion'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    closed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='closed_touchups'
    )
    
    # Visual
    pin_color = models.CharField(
        max_length=7,
        default='#dc3545',
        help_text='Red for touch-ups by default'
    )
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'assigned_to']),
            models.Index(fields=['plan', 'status']),
        ]
    
    def __str__(self):
        return f"Touch-up: {self.task_name} ({self.get_status_display()})"
    
    def can_edit(self, user):
        """PM/Admin/Client/Designer/Owner can edit"""
        profile = getattr(user, 'profile', None)
        return user.is_staff or (profile and profile.role in [
            'project_manager', 'admin', 'superuser', 'client', 'designer', 'owner'
        ])
    
    def can_close(self, user):
        """Assigned employee or authorized users can close"""
        if self.can_edit(user):
            return True
        return self.assigned_to == user
    
    def close_touchup(self, user):
        """Mark as completed and archive"""
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.closed_by = user
        self.save()


class TouchUpCompletionPhoto(models.Model):
    """Photos uploaded when closing a touch-up"""
    if TYPE_CHECKING:
        id: int
        touchup_id: int
    
    touchup = models.ForeignKey(
        TouchUpPin,
        on_delete=models.CASCADE,
        related_name='completion_photos'
    )
    image = models.ImageField(upload_to='touchups/completion/')
    annotations = models.JSONField(
        default=dict,
        blank=True,
        help_text='Canvas annotations if photo was edited'
    )
    notes = models.CharField(max_length=255, blank=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Completion photo for touchup #{self.touchup_id}"


# ---------------------
# Enhanced SitePhoto (Before/After)
# ---------------------
# Extend existing SitePhoto with new fields - agregar migration
# NOTE: Esto requiere modificar el modelo SitePhoto existente
# Ver líneas ~450-480 en models.py








