"""
Tests para validar la lógica de financial snapshots en TimeEntry
y cálculos de tarifas en Project/ChangeOrder
"""
import pytest
from decimal import Decimal
from datetime import time
from django.test import TestCase
from django.contrib.auth.models import User
from core.models import Project, ChangeOrder, TimeEntry, Employee


class FinancialSnapshotTestCase(TestCase):
    """
    Tests críticos para garantizar que los cambios en tarifas NO afectan
    retroactivamente a TimeEntries existentes (accuracy histórica)
    """
    
    def setUp(self):
        """Configurar datos de prueba"""
        # Usuario admin
        self.admin = User.objects.create_user(
            username='admin',
            password='admin123',
            is_staff=True
        )
        
        # Proyecto con tarifa default
        self.project = Project.objects.create(
            name='Proyecto Test Financial',
            client='Cliente Test',
            start_date='2024-01-01',
            default_co_labor_rate=Decimal('50.00'),
            budget_labor=Decimal('10000.00'),
            budget_materials=Decimal('5000.00'),
            budget_other=Decimal('1000.00')
        )
        
        # Empleado con tarifa de costo
        self.employee = Employee.objects.create(
            user=self.admin,
            first_name='Juan',
            last_name='Pérez',
            social_security_number='123-45-6789',
            position='Superintendent',
            hourly_rate=Decimal('30.00')
        )
        
        # Change Order con tarifa override
        self.co = ChangeOrder.objects.create(
            project=self.project,
            description='Change Order de prueba',
            reference_code='CO Test',
            labor_rate_override=Decimal('75.00'),
            material_markup_percent=Decimal('20.00')
        )
    
    def test_timeentry_snapshots_on_creation(self):
        """
        TEST 1: Verificar que al crear TimeEntry se capturan los snapshots correctamente
        """
        # Crear TimeEntry con Change Order
        entry = TimeEntry.objects.create(
            employee=self.employee,
            project=self.project,
            change_order=self.co,
            date='2024-01-15',
            start_time=time(8, 0),
            end_time=time(16, 0),
            hours_worked=Decimal('8.00'),
            notes='Trabajo de prueba'
        )
        
        # Validar que se capturaron los snapshots
        self.assertIsNotNone(entry.cost_rate_snapshot, 
                            "cost_rate_snapshot debe capturarse en creación")
        self.assertIsNotNone(entry.billable_rate_snapshot,
                            "billable_rate_snapshot debe capturarse en creación")
        
        # Validar valores exactos
        self.assertEqual(entry.cost_rate_snapshot, Decimal('30.00'),
                        "cost_rate_snapshot debe ser igual a employee.hourly_rate")
        self.assertEqual(entry.billable_rate_snapshot, Decimal('75.00'),
                        "billable_rate_snapshot debe usar CO override (75.00)")
    
    def test_timeentry_uses_project_default_without_co(self):
        """
        TEST 2: Verificar que sin CO, se usa la tarifa default del proyecto
        """
        entry = TimeEntry.objects.create(
            employee=self.employee,
            project=self.project,
            date='2024-01-16',
            start_time=time(9, 0),
            end_time=time(13, 0),
            hours_worked=Decimal('4.00'),
            notes='Trabajo sin CO'
        )
        
        self.assertEqual(entry.billable_rate_snapshot, Decimal('50.00'),
                        "Sin CO, debe usar project.default_co_labor_rate (50.00)")
    
    def test_timeentry_snapshots_are_immutable(self):
        """
        TEST 3 (CRÍTICO): Cambiar tarifas NO debe afectar TimeEntries existentes
        """
        # Crear TimeEntry inicial
        entry = TimeEntry.objects.create(
            employee=self.employee,
            project=self.project,
            change_order=self.co,
            date='2024-01-15',
            start_time=time(8, 0),
            end_time=time(16, 0),
            hours_worked=Decimal('8.00'),
            notes='Trabajo inicial'
        )
        
        # Guardar valores originales
        original_cost = entry.cost_rate_snapshot
        original_billable = entry.billable_rate_snapshot
        
        # CAMBIAR tarifas del empleado y CO
        self.employee.hourly_rate = Decimal('45.00')  # 30 -> 45
        self.employee.save()
        
        self.co.labor_rate_override = Decimal('100.00')  # 75 -> 100
        self.co.save()
        
        self.project.default_co_labor_rate = Decimal('65.00')  # 50 -> 65
        self.project.save()
        
        # Recargar entry desde DB
        entry.refresh_from_db()
        
        # VALIDAR: Los snapshots NO deben cambiar
        self.assertEqual(entry.cost_rate_snapshot, original_cost,
                        "cost_rate_snapshot NO debe cambiar después de modificar employee.hourly_rate")
        self.assertEqual(entry.billable_rate_snapshot, original_billable,
                        "billable_rate_snapshot NO debe cambiar después de modificar CO/Project rates")
        
        # Verificar valores exactos
        self.assertEqual(entry.cost_rate_snapshot, Decimal('30.00'),
                        "Debe mantener tarifa original de 30.00")
        self.assertEqual(entry.billable_rate_snapshot, Decimal('75.00'),
                        "Debe mantener tarifa original de 75.00")
    
    def test_new_timeentry_uses_new_rates(self):
        """
        TEST 4: Nuevos TimeEntries deben usar las tarifas actualizadas
        """
        # Cambiar tarifas
        self.employee.hourly_rate = Decimal('35.00')
        self.employee.save()
        
        self.co.labor_rate_override = Decimal('80.00')
        self.co.save()
        
        # Crear NUEVO TimeEntry
        new_entry = TimeEntry.objects.create(
            employee=self.employee,
            project=self.project,
            change_order=self.co,
            date='2024-01-20',
            start_time=time(8, 0),
            end_time=time(14, 0),
            hours_worked=Decimal('6.00'),
            notes='Trabajo nuevo'
        )
        
        # Validar que usa las tarifas NUEVAS
        self.assertEqual(new_entry.cost_rate_snapshot, Decimal('35.00'),
                        "Nuevo entry debe usar nueva tarifa del empleado (35.00)")
        self.assertEqual(new_entry.billable_rate_snapshot, Decimal('80.00'),
                        "Nuevo entry debe usar nueva tarifa del CO (80.00)")
    
    def test_changeorder_get_effective_labor_rate(self):
        """
        TEST 5: Validar método get_effective_labor_rate() de ChangeOrder
        """
        # CO con override
        co_with_override = ChangeOrder.objects.create(
            project=self.project,
            reference_code='CO con override',
            labor_rate_override=Decimal('90.00')
        )
        self.assertEqual(co_with_override.get_effective_labor_rate(), Decimal('90.00'),
                        "Debe retornar el override cuando existe")
        
        # CO sin override
        co_without_override = ChangeOrder.objects.create(
            project=self.project,
            reference_code='CO sin override'
        )
        self.assertEqual(co_without_override.get_effective_labor_rate(), Decimal('50.00'),
                        "Debe retornar project.default_co_labor_rate cuando no hay override")
    
    def test_timeentry_snapshots_not_editable(self):
        """
        TEST 6: Verificar que los snapshots tienen editable=False
        """
        from core.models import TimeEntry
        
        cost_field = TimeEntry._meta.get_field('cost_rate_snapshot')
        billable_field = TimeEntry._meta.get_field('billable_rate_snapshot')
        
        self.assertFalse(cost_field.editable,
                        "cost_rate_snapshot debe tener editable=False")
        self.assertFalse(billable_field.editable,
                        "billable_rate_snapshot debe tener editable=False")
    
    def test_timeentry_snapshots_with_zero_rates(self):
        """
        TEST 7: Validar comportamiento cuando employee no tiene hourly_rate
        """
        # Crear un nuevo usuario para este empleado
        user_no_rate = User.objects.create_user(username='emp_no_rate', password='pass')
        
        # Empleado sin tarifa
        emp_no_rate = Employee.objects.create(
            user=user_no_rate,
            first_name='Sin',
            last_name='Tarifa',
            social_security_number='999-99-9999',
            position='Employee',
            hourly_rate=Decimal('0.00')
        )
        
        entry = TimeEntry.objects.create(
            employee=emp_no_rate,
            project=self.project,
            date='2024-01-17',
            start_time=time(8, 0),
            end_time=time(13, 0),
            hours_worked=Decimal('5.00')
        )
        
        # Debe usar 0.00 cuando hourly_rate es None
        self.assertEqual(entry.cost_rate_snapshot, Decimal('0.00'),
                        "Sin hourly_rate, debe usar 0.00")
    
    def test_timeentry_without_project_or_co(self):
        """
        TEST 8: Validar comportamiento cuando no hay proyecto ni CO
        """
        entry = TimeEntry.objects.create(
            employee=self.employee,
            date='2024-01-18',
            start_time=time(10, 0),
            end_time=time(13, 0),
            hours_worked=Decimal('3.00'),
            notes='Sin proyecto ni CO'
        )
        
        # Debe tener snapshots pero con valores default
        self.assertIsNotNone(entry.cost_rate_snapshot)
        self.assertEqual(entry.cost_rate_snapshot, Decimal('30.00'),
                        "Debe capturar employee.hourly_rate aunque no haya proyecto")
        self.assertEqual(entry.billable_rate_snapshot, Decimal('0.00'),
                        "Sin proyecto ni CO, billable debe ser 0.00")
    
    def test_project_default_co_labor_rate_default_value(self):
        """
        TEST 9: Verificar que Project.default_co_labor_rate tiene default correcto
        """
        project = Project.objects.create(
            name='Proyecto sin tarifa',
            client='Cliente',
            start_date='2024-01-01',
            budget_labor=Decimal('1000.00')
        )
        
        self.assertEqual(project.default_co_labor_rate, Decimal('50.00'),
                        "default_co_labor_rate debe tener default de 50.00")
    
    def test_changeorder_material_markup_default(self):
        """
        TEST 10: Verificar que ChangeOrder.material_markup_percent tiene default
        """
        co = ChangeOrder.objects.create(
            project=self.project,
            reference_code='CO sin markup especificado'
        )
        
        self.assertEqual(co.material_markup_percent, Decimal('15.00'),
                        "material_markup_percent debe tener default de 15.00")


class FinancialCalculationsTestCase(TestCase):
    """
    Tests para validar cálculos financieros derivados de los snapshots
    """
    
    def setUp(self):
        self.admin = User.objects.create_user(username='admin2', password='pass')
        self.project = Project.objects.create(
            name='Proyecto Cálculos',
            client='Cliente',
            start_date='2024-01-01',
            default_co_labor_rate=Decimal('60.00'),
            budget_labor=Decimal('20000.00')
        )
        self.employee = Employee.objects.create(
            user=self.admin,
            first_name='Test',
            last_name='User',
            social_security_number='222-22-2222',
            hourly_rate=Decimal('25.00')
        )
    
    def test_cost_vs_billable_calculation(self):
        """
        TEST 11: Validar que cost y billable se calculan correctamente
        NOTA: TimeEntry resta 0.5h de almuerzo en turnos de 8-18 (>5h cruzando 12:30)
        """
        entry = TimeEntry.objects.create(
            employee=self.employee,
            project=self.project,
            date='2024-02-01',
            start_time=time(8, 0),
            end_time=time(18, 0)
            # hours_worked se calculará automáticamente: 10h - 0.5h = 9.5h
        )
        
        # El save() calculó 9.5 horas (10 - 0.5 almuerzo)
        expected_cost = Decimal('9.50') * Decimal('25.00')  # 237.50
        expected_billable = Decimal('9.50') * Decimal('60.00')  # 570.00
        
        # Calcular usando snapshots
        actual_cost = entry.hours_worked * entry.cost_rate_snapshot
        actual_billable = entry.hours_worked * entry.billable_rate_snapshot
        
        self.assertEqual(actual_cost, expected_cost,
                        "Costo debe ser hours * cost_rate_snapshot")
        self.assertEqual(actual_billable, expected_billable,
                        "Billable debe ser hours * billable_rate_snapshot")
    
    def test_profit_margin_calculation(self):
        """
        TEST 12: Validar cálculo de margen de ganancia
        NOTA: TimeEntry resta 0.5h de almuerzo en turnos de 8-16 (>5h cruzando 12:30)
        """
        entry = TimeEntry.objects.create(
            employee=self.employee,
            project=self.project,
            date='2024-02-02',
            start_time=time(8, 0),
            end_time=time(16, 0)
            # hours_worked se calculará: 8h - 0.5h = 7.5h
        )
        
        cost = entry.hours_worked * entry.cost_rate_snapshot  # 7.5 * 25 = 187.50
        billable = entry.hours_worked * entry.billable_rate_snapshot  # 7.5 * 60 = 450
        profit = billable - cost  # 262.50
        margin = (profit / billable) * 100 if billable > 0 else 0  # 58.33%
        
        self.assertEqual(cost, Decimal('187.50'))
        self.assertEqual(billable, Decimal('450.00'))
        self.assertEqual(profit, Decimal('262.50'))
        self.assertAlmostEqual(float(margin), 58.33, places=2,
                              msg="Margen debe ser ~58.33%")


@pytest.mark.django_db
class TestFinancialSnapshotsPytest:
    """
    Tests adicionales usando pytest para mayor flexibilidad
    """
    
    def test_bulk_timeentry_creation_preserves_snapshots(self):
        """
        TEST 13: Crear múltiples TimeEntries y validar que todos tienen snapshots
        """
        admin = User.objects.create_user(username='admin3', password='pass')
        project = Project.objects.create(
            name='Proyecto Bulk',
            client='Cliente',
            start_date='2024-01-01',
            default_co_labor_rate=Decimal('55.00'),
            budget_labor=Decimal('5000.00')
        )
        employee = Employee.objects.create(
            user=admin,
            first_name='Bulk',
            last_name='Test',
            social_security_number='333-33-3333',
            hourly_rate=Decimal('28.00')
        )
        
        # Crear 5 TimeEntries
        entries = []
        for i in range(5):
            entry = TimeEntry.objects.create(
                employee=employee,
                project=project,
                date=f'2024-02-{i+10:02d}',
                start_time=time(8, 0),
                end_time=time(16, 0),
                hours_worked=Decimal('8.00'),
                notes=f'Día {i+1}'
            )
            entries.append(entry)
        
        # Validar que TODOS tienen snapshots
        for entry in entries:
            assert entry.cost_rate_snapshot == Decimal('28.00'), \
                f"Entry {entry.id} debe tener cost_rate_snapshot de 28.00"
            assert entry.billable_rate_snapshot == Decimal('55.00'), \
                f"Entry {entry.id} debe tener billable_rate_snapshot de 55.00"
        
        # Cambiar tarifa del empleado
        employee.hourly_rate = Decimal('32.00')
        employee.save()
        
        # Validar que los entries antiguos NO cambiaron
        for entry in entries:
            entry.refresh_from_db()
            assert entry.cost_rate_snapshot == Decimal('28.00'), \
                "Snapshots antiguos NO deben cambiar"
