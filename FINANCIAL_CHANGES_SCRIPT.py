"""
Script para aplicar cambios financieros a los modelos
Parte 1: Modificaciones a Project, ChangeOrder y TimeEntry
"""

# CAMBIOS A REALIZAR EN core/models.py:

# 1. En el modelo Project (después de budget_other, antes de if TYPE_CHECKING):
PROJECT_NEW_FIELD = """
    # Financial: Default labor rate for Change Orders
    default_co_labor_rate = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=Decimal("50.00"),
        help_text=_("Tarifa por hora por defecto para Change Orders en este proyecto")
    )
"""

# 2. En el modelo ChangeOrder (después del campo notes, antes de color):
CHANGEORDER_NEW_FIELDS = """
    # Financial: Labor rate and material markup
    labor_rate_override = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_("Tarifa por hora específica para este CO. Si está vacío, usa default_co_labor_rate del proyecto")
    )
    material_markup_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("15.00"),
        help_text=_("Porcentaje de markup en materiales (por defecto 15%)")
    )
"""

# 3. Método helper para ChangeOrder (antes de __str__):
CHANGEORDER_HELPER_METHOD = """
    def get_effective_labor_rate(self):
        \"\"\"Retorna la tarifa efectiva: override del CO o default del proyecto\"\"\"
        if self.labor_rate_override is not None:
            return self.labor_rate_override
        return self.project.default_co_labor_rate if self.project else Decimal("50.00")
"""

# 4. En el modelo TimeEntry (después de cost_code, antes de @property labor_cost):
TIMEENTRY_NEW_FIELDS = """
    # Financial Snapshots: Costos y tarifas al momento de la entrada
    cost_rate_snapshot = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        editable=False,
        null=True,
        blank=True,
        help_text=_("Costo del empleado (hourly_rate) al momento de esta entrada")
    )
    billable_rate_snapshot = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        editable=False,
        null=True,
        blank=True,
        help_text=_("Tarifa cobrada (según CO o proyecto) al momento de esta entrada")
    )
"""

# 5. Modificación al método save() de TimeEntry (reemplazar el método completo):
TIMEENTRY_SAVE_METHOD = '''
    def save(self, *args, **kwargs):
        # Calculate hours_worked
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
        
        # Financial Snapshots: Guardar tasas al momento de creación
        if self.pk is None:  # Solo en creación
            # Snapshot del costo del empleado
            if self.cost_rate_snapshot is None and self.employee:
                self.cost_rate_snapshot = self.employee.hourly_rate or Decimal("0.00")
            
            # Snapshot de la tarifa cobrable
            if self.billable_rate_snapshot is None:
                if self.change_order is not None:
                    # Usar tarifa del Change Order
                    self.billable_rate_snapshot = self.change_order.get_effective_labor_rate()
                elif self.project:
                    # Usar tarifa default del proyecto para trabajo regular
                    self.billable_rate_snapshot = self.project.default_co_labor_rate
                else:
                    # Sin proyecto ni CO, usar 0
                    self.billable_rate_snapshot = Decimal("0.00")
        
        super().save(*args, **kwargs)
'''

print("Archivo de cambios creado exitosamente")
print("\nRESUMEN DE CAMBIOS:")
print("=" * 70)
print("\n1. Project: Agregar campo default_co_labor_rate (Decimal, default=50.00)")
print("2. ChangeOrder: Agregar labor_rate_override y material_markup_percent")
print("3. ChangeOrder: Agregar método get_effective_labor_rate()")
print("4. TimeEntry: Agregar cost_rate_snapshot y billable_rate_snapshot")
print("5. TimeEntry: Modificar save() para capturar snapshots en creación")
print("\nSiguiente paso: Aplicar estos cambios a core/models.py")
