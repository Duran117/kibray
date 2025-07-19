from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User
from datetime import datetime, timedelta


# Modelo de Empleado
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


# Modelo de Ingresos
class Income(models.Model):
    project_name = models.CharField(max_length=255, verbose_name="Nombre del proyecto o factura")
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Cantidad recibida")
    date_received = models.DateField(verbose_name="Fecha de ingreso")
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
    notes = models.TextField(blank=True, null=True, verbose_name="Notas (opcional)")
    attachment = models.FileField(upload_to="incomes/", blank=True, null=True, verbose_name="Archivo adjunto (PDF o imagen)")

    def __str__(self):
        return f"{self.project_name} - ${self.amount}"


# Modelo de Gastos
class Expense(models.Model):
    CATEGORIES = [
        ("MATERIALES", "Materiales"),
        ("COMIDA", "Comida"),
        ("SEGURO", "Seguro"),
        ("ALMACÉN", "Storage"),
        ("MANO_OBRA", "Mano de obra"),
        ("OTRO", "Otro"),
    ]

    amount = models.DecimalField(max_digits=10, decimal_places=2)
    project_name = models.CharField(max_length=255)
    date = models.DateField()
    category = models.CharField(max_length=50, choices=CATEGORIES)
    description = models.TextField(blank=True, null=True)
    attachment = models.FileField(upload_to="expenses/", blank=True, null=True)

    def __str__(self):
        return f"{self.project_name} - {self.category} - ${self.amount}"


# Modelo de Proyectos
class Project(models.Model):
    name = models.CharField(max_length=100)
    client = models.CharField(max_length=100, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)

    description = models.TextField(blank=True, null=True)
    paint_colors = models.TextField(
        blank=True, help_text="Ejemplo: SW 7008 Alabaster, SW 6258 Tricorn Black"
    )
    paint_codes = models.TextField(
        blank=True, help_text="Códigos de pintura si son diferentes de los colores comunes"
    )
    stains_or_finishes = models.TextField(
        blank=True, help_text="Ejemplo: Milesi Butternut 072 - 2 coats"
    )
    number_of_rooms_or_areas = models.IntegerField(blank=True, null=True)
    number_of_paint_defects = models.IntegerField(
        blank=True, null=True, help_text="Número de manchas o imperfecciones detectadas"
    )

    total_income = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_expenses = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def profit(self):
        return self.total_income - self.total_expenses

    reflection_notes = models.TextField(
        blank=True,
        help_text="Notas sobre aprendizajes, errores o mejoras para próximos proyectos"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


# Modelo de Registro de Horas
class TimeEntry(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    notes = models.TextField(blank=True, null=True)

    @property
    def hours_worked(self):
        start = datetime.combine(self.date, self.start_time)
        end = datetime.combine(self.date, self.end_time)
        total_hours = (end - start).total_seconds() / 3600.0
        return max(total_hours - 0.5, 0)  # Se descuenta 30 min (media hora para almuerzo)

    @property
    def labor_cost(self):
        return round(self.hours_worked * self.employee.hourly_rate, 2)

    def __str__(self):
        return f"{self.employee.first_name} | {self.date} | {self.project.name}"


# Modelo de Cronograma
class Schedule(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    is_personal = models.BooleanField(default=False)  # Solo visible para el superusuario
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
