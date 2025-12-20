
"""
Management command para simular escenarios de la arquitectura final Kibray
Genera datos realistas para testing - Villa Moderna
"""
from datetime import date, time, timedelta
from decimal import Decimal

from django.contrib.auth.models import Group, User
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from core.models import (
    ChangeOrder,
    DailyLog,
    Employee,
    Estimate,
    Expense,
    FloorPlan,
    InventoryItem,
    InventoryLocation,
    Invoice,
    InvoiceLine,
    PlanPin,
    Project,
    ProjectInventory,
    Schedule,
    Task,
)


class Command(BaseCommand):
    help = 'Simula escenario completo "Villa Moderna" para Arquitectura Final'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('\n🎬 SIMULACIÓN KIBRAY - VILLA MODERNA (Arquitectura Final)\n'))

        with transaction.atomic():
            # Setup users and roles
            users = self._setup_users()

            # Create complete scenario
            self._simulate_villa_moderna(users)

        self.stdout.write(self.style.SUCCESS('\n✅ SIMULACIÓN COMPLETADA\n'))
        self._print_credentials(users)

    def _setup_users(self):
        """Crea usuarios con roles configurados"""
        users = {}

        # Admin
        users['admin'], _ = User.objects.get_or_create(
            username='admin_kibray',
            defaults={
                'email': 'admin@kibray.com',
                'is_staff': True,
                'is_superuser': True,
                'first_name': 'Carlos',
                'last_name': 'Administrador'
            }
        )
        users['admin'].set_password('admin123')
        users['admin'].save()

        # PM Full
        users['pm'], _ = User.objects.get_or_create(
            username='pm_full',
            defaults={
                'email': 'pm@kibray.com',
                'is_staff': True,
                'first_name': 'María',
                'last_name': 'Manager'
            }
        )
        users['pm'].set_password('pm123')
        users['pm'].save()

        pm_group, _ = Group.objects.get_or_create(name='Project Manager')
        users['pm'].groups.add(pm_group)

        # PM Trainee
        users['trainee'], _ = User.objects.get_or_create(
            username='pm_trainee',
            defaults={
                'email': 'trainee@kibray.com',
                'is_staff': True,
                'first_name': 'Juan',
                'last_name': 'Aprendiz'
            }
        )
        users['trainee'].set_password('trainee123')
        users['trainee'].save()

        trainee_group, _ = Group.objects.get_or_create(name='Project Manager (Trainee)')
        users['trainee'].groups.add(trainee_group)

        # Designer
        users['designer'], _ = User.objects.get_or_create(
            username='designer',
            defaults={
                'email': 'designer@kibray.com',
                'is_staff': True,
                'first_name': 'Ana',
                'last_name': 'Diseñadora'
            }
        )
        users['designer'].set_password('designer123')
        users['designer'].save()

        designer_group, _ = Group.objects.get_or_create(name='Designer')
        users['designer'].groups.add(designer_group)

        # Superintendent
        users['super'], _ = User.objects.get_or_create(
            username='superintendent',
            defaults={
                'email': 'super@kibray.com',
                'is_staff': True,
                'first_name': 'Pedro',
                'last_name': 'Supervisor'
            }
        )
        users['super'].set_password('super123')
        users['super'].save()

        super_group, _ = Group.objects.get_or_create(name='Superintendent')
        users['super'].groups.add(super_group)

        # Employee for reimbursement
        users['employee'], _ = Employee.objects.get_or_create(
            first_name='José',
            last_name='Pintor',
            defaults={
                'position': 'Painter',
                'hourly_rate': Decimal('25.00'),
                'is_active': True
            }
        )

        # Client
        users['client'], _ = User.objects.get_or_create(
            username='cliente_villa',
            defaults={
                'email': 'cliente@example.com',
                'first_name': 'Roberto',
                'last_name': 'Villa'
            }
        )
        users['client'].set_password('client123')
        users['client'].save()

        client_group, _ = Group.objects.get_or_create(name='Client')
        users['client'].groups.add(client_group)

        self.stdout.write('  ✅ 7 usuarios creados (Admin, PM, PM Trainee, Designer, Superintendent, Employee, Client)')
        return users

    def _simulate_villa_moderna(self, users):
        """
        Escenario completo: Villa Moderna
        - Proyecto $50,000 con 15% markup
        - Invoice deposit $5,000 (pagada)
        - Change Order $500 (aprobado)
        - Expense reembolsable $15 (pendiente)
        - Inventario con herramientas
        - Planos con pines
        - Daily Plan con tareas
        """
        self.stdout.write(self.style.WARNING('\n🏡 ESCENARIO: VILLA MODERNA\n'))

        # 1. Crear proyecto
        project, created = Project.objects.get_or_create(
            name='Villa Moderna - Familia Villa',
            defaults={
                'client': 'Roberto Villa',
                'address': 'Av. Principal 456, Zona Residencial',
                'start_date': date.today() - timedelta(days=10),
                'end_date': date.today() + timedelta(days=50),
                'budget_total': Decimal('50000.00'),
                'budget_labor': Decimal('30000.00'),
                'budget_materials': Decimal('17000.00'),
                'budget_other': Decimal('3000.00'),
                'default_co_labor_rate': Decimal('50.00'),
                'material_markup_percent': Decimal('15.00'),
            }
        )

        if created:
            self.stdout.write(f'  📋 Proyecto: {project.name}')
            self.stdout.write(f'     Presupuesto: ${project.budget_total:,.2f}')
            self.stdout.write(f'     Labor Rate: ${project.default_co_labor_rate}/hr')
            self.stdout.write(f'     Material Markup: {project.material_markup_percent}%')

        # 2. Crear estimate
        estimate, _ = Estimate.objects.get_or_create(
            project=project,
            version=1,
            defaults={
                'approved': True,
                'markup_material': Decimal('15.00'),
                'markup_labor': Decimal('10.00'),
                'overhead_pct': Decimal('10.00'),
                'target_profit_pct': Decimal('15.00'),
                'notes': 'Renovación completa de villa de 3 pisos'
            }
        )

        self.stdout.write(f'  📄 Estimate: {estimate.code} (Aprobado)')

        # 3. Invoice deposit (pagada)
        invoice_deposit, inv_created = Invoice.objects.get_or_create(
            project=project,
            invoice_type='deposit',
            defaults={
                'total_amount': Decimal('5000.00'),
                'date_issued': date.today() - timedelta(days=7),
                'due_date': date.today() - timedelta(days=5),
                'status': 'PAID',
                'amount_paid': Decimal('5000.00'),
                'paid_date': timezone.now() - timedelta(days=5),
                'notes': 'Anticipo 10% del contrato ($50,000)'
            }
        )

        if inv_created:
            InvoiceLine.objects.create(
                invoice=invoice_deposit,
                description=f'Anticipo 10% - Contrato {estimate.code}',
                amount=Decimal('5000.00')
            )

        self.stdout.write(f'  💰 Invoice Deposit: #{invoice_deposit.invoice_number} - ${invoice_deposit.total_amount:,.2f} (PAGADA)')

        # 4. Change Order (aprobado)
        co, _ = ChangeOrder.objects.get_or_create(
            project=project,
            description='Pintura adicional de pérgola y área de jardín',
            defaults={
                'amount': Decimal('500.00'),
                'status': 'approved',
                'notes': 'Cliente solicitó incluir pérgola nueva no contemplada en estimado original',
                'labor_rate_override': Decimal('50.00')
            }
        )

        self.stdout.write(f'  📝 Change Order: CO-{co.id} - ${co.amount:,.2f} (APROBADO)')

        # 5. Calcular saldo restante
        remaining = project.calculate_remaining_balance()

        self.stdout.write('\n  📊 RESUMEN FINANCIERO:')
        self.stdout.write(f'     Presupuesto Original:  ${project.budget_total:,.2f}')
        self.stdout.write(f'     + Change Orders:       ${co.amount:,.2f}')
        self.stdout.write(f'     = Total Actualizado:   ${project.budget_total + co.amount:,.2f}')
        self.stdout.write(f'     - Facturado (Deposit): ${invoice_deposit.total_amount:,.2f}')
        self.stdout.write(self.style.SUCCESS(f'     = SALDO RESTANTE:      ${remaining:,.2f}'))

        # 6. Gasto reembolsable
        employee = users['employee']

        expense, _ = Expense.objects.get_or_create(
            project=project,
            amount=Decimal('15.00'),
            category='HERRAMIENTAS',
            defaults={
                'description': 'Brocha profesional 3" Purdy (compra de emergencia)',
                'date': date.today() - timedelta(days=2),
                'paid_by_employee': employee,
                'reimbursement_status': 'pending',
                'project_name': project.name
            }
        )

        self.stdout.write('\n  💳 Gasto Reembolsable:')
        self.stdout.write(f'     Empleado: {employee.first_name} {employee.last_name}')
        self.stdout.write(f'     Monto: ${expense.amount}')
        self.stdout.write(f'     Estado: {expense.get_reimbursement_status_display()}')
        self.stdout.write(f'     Descripción: {expense.description}')

        # 7. Setup inventario
        self._setup_inventory(project)

        # 8. Setup visual (planos y pines)
        self._setup_visual_data(project, users)

        # 9. Setup planner (schedule y tareas)
        self._setup_planner_data(project, users)

    def _setup_inventory(self, project):
        """Setup inventario con herramientas y materiales"""
        self.stdout.write('\n  📦 INVENTARIO:')

        # Create project location
        project_location, _ = InventoryLocation.objects.get_or_create(
            name='Sitio Villa Moderna',
            project=project,
            defaults={
                'is_storage': False
            }
        )

        # Create inventory items
        items_data = [
            ('Rodillo profesional 9"', 'HERRAMIENTA', 'unit', 8),
            ('Escalera aluminio 20 pies', 'ESCALERA', 'unit', 2),
            ('Pintura blanca Sherwin Williams Pro', 'PINTURA', 'gallon', 15),
            ('Brocha angular 2.5"', 'HERRAMIENTA', 'unit', 12),
            ('Lija grano 120', 'MATERIAL', 'sheet', 50),
            ('Masking tape 2"', 'MATERIAL', 'roll', 20),
            ('Cinta de papel', 'MATERIAL', 'roll', 15),
        ]

        for name, category, unit, qty in items_data:
            item, _ = InventoryItem.objects.get_or_create(
                name=name,
                defaults={
                    'category': category,
                    'unit': unit,
                    'low_stock_threshold': Decimal('2')
                }
            )

            ProjectInventory.objects.get_or_create(
                item=item,
                location=project_location,
                defaults={'quantity': Decimal(str(qty))}
            )

        self.stdout.write(f'     Ubicación: {project_location.name}')
        self.stdout.write(f'     Items: {len(items_data)} tipos de herramientas/materiales')
        self.stdout.write('     ✅ Listos para "Transferir a Bodega"')

    def _setup_visual_data(self, project, users):
        """Setup planos y pines para visualización"""
        self.stdout.write('\n  🎨 DATOS VISUALES (Planos & Pines):')

        # Create floor plans
        floor_plan_1, _ = FloorPlan.objects.get_or_create(
            project=project,
            level=0,
            defaults={
                'name': 'Planta Baja - Villa Moderna',
                'image': None
            }
        )

        floor_plan_2, _ = FloorPlan.objects.get_or_create(
            project=project,
            level=1,
            defaults={
                'name': 'Primer Piso - Villa Moderna',
                'image': None
            }
        )

        # Create pins on floor plan 1
        pins_data = [
            (Decimal('0.25'), Decimal('0.30'), 'task', 'Preparación de pared sala', 'Lijar y limpiar superficie antes de pintar'),
            (Decimal('0.40'), Decimal('0.50'), 'touchup', 'Touch-up esquina cocina', 'Pequeña imperfección detectada'),
            (Decimal('0.60'), Decimal('0.40'), 'info', 'Punto eléctrico', 'Evitar pintar sobre switch - cliente lo reemplazará'),
            (Decimal('0.75'), Decimal('0.65'), 'leftover', 'Pintura sobrante', 'Galón de pintura blanca guardado en closet'),
        ]

        for x, y, pin_type, title, desc in pins_data:
            PlanPin.objects.get_or_create(
                plan=floor_plan_1,
                x=x,
                y=y,
                defaults={
                    'pin_type': pin_type,
                    'title': title,
                    'description': desc,
                    'created_by': users['pm'],
                    'owner_role': 'project_manager',
                    'is_visible': True
                }
            )

        self.stdout.write(f'     Plano 1: {floor_plan_1.name} ({len(pins_data)} pines)')
        self.stdout.write(f'     Plano 2: {floor_plan_2.name}')
        self.stdout.write('     Pin tipos: task, touchup, info, leftover')

    def _setup_planner_data(self, project, users):
        """Setup schedule y tareas con features del planner"""
        self.stdout.write('\n  📅 PLANNER (Schedule & Tareas):')

        # Create main schedule
        from datetime import datetime
        schedule, _ = Schedule.objects.get_or_create(
            project=project,
            title='Schedule Principal - Villa Moderna',
            defaults={
                'description': 'Cronograma completo de renovación villa 3 pisos',
                'start_datetime': timezone.make_aware(datetime.combine(project.start_date, time(8, 0))),
                'end_datetime': timezone.make_aware(datetime.combine(project.end_date or project.start_date + timedelta(days=50), time(17, 0))),
                'stage': 'Preparation',
                'completion_percentage': 30
            }
        )

        # Create tasks with planner features
        employee = users['employee']

        task1, _ = Task.objects.get_or_create(
            project=project,
            title='Preparar paredes planta baja',
            defaults={
                'description': 'Lijar, limpiar y aplicar primer en todas las paredes de planta baja',
                'status': 'En Progreso',
                'priority': 'high',
                'assigned_to': employee,
                'schedule_weight': 80,
                'is_subtask': False,
                'is_client_responsibility': False,
                'progress_percent': 60,
                'due_date': project.start_date + timedelta(days=5),
                'checklist': [
                    {'item': 'Proteger pisos y muebles', 'checked': True},
                    {'item': 'Lijar superficies', 'checked': True},
                    {'item': 'Limpiar polvo', 'checked': True},
                    {'item': 'Aplicar primer', 'checked': False},
                ]
            }
        )

        task2, _ = Task.objects.get_or_create(
            project=project,
            title='Pintar sala y comedor',
            defaults={
                'description': 'Aplicar 2 manos de pintura blanca en sala y comedor',
                'status': 'Pendiente',
                'priority': 'high',
                'assigned_to': employee,
                'schedule_weight': 90,
                'is_subtask': False,
                'progress_percent': 0,
                'due_date': project.start_date + timedelta(days=15),
                'checklist': [
                    {'item': 'Primera mano de pintura', 'checked': False},
                    {'item': 'Dejar secar 4 horas', 'checked': False},
                    {'item': 'Segunda mano', 'checked': False},
                    {'item': 'Touch-ups finales', 'checked': False},
                ]
            }
        )

        task3, _ = Task.objects.get_or_create(
            project=project,
            title='Aprobar colores cocina',
            defaults={
                'description': 'Cliente debe aprobar muestras de color para cocina',
                'status': 'Pendiente',
                'priority': 'urgent',
                'schedule_weight': 100,
                'is_subtask': False,
                'is_client_responsibility': True,
                'progress_percent': 0,
                'due_date': project.start_date + timedelta(days=12),
            }
        )

        # Create daily log entry
        daily_log, _ = DailyLog.objects.get_or_create(
            project=project,
            date=date.today(),
            defaults={
                'weather': 'Soleado, 22°C',
                'crew_count': 2,
                'progress_notes': 'Equipo trabajó en preparación de paredes planta baja. Avance del 60%.',
                'accomplishments': '- Lijado completo sala y comedor\n- Limpieza de superficies\n- Primer aplicado en sala',
                'delays': 'Cliente no ha aprobado colores para cocina. Esperando respuesta.',
                'next_day_plan': 'Completar primer en comedor. Comenzar pintura sala si hay aprobación.',
                'schedule_item': schedule,
                'schedule_progress_percent': Decimal('30'),
                'is_published': True,
                'created_by': users['pm']
            }
        )

        self.stdout.write(f'     Schedule: {schedule.title}')
        self.stdout.write(f'     Tareas: {Task.objects.filter(project=project).count()}')
        self.stdout.write(f'     Daily Log: {daily_log.date.strftime("%d/%m/%Y")}')
        self.stdout.write('     ✅ Checklist funcional, schedule_weight, client_responsibility')

    def _print_credentials(self, users):
        """Imprime credenciales de acceso para auditoría visual"""
        self.stdout.write(self.style.SUCCESS('\n' + '='*80))
        self.stdout.write(self.style.SUCCESS('🔑 CREDENCIALES DE ACCESO - AUDITORÍA VISUAL'))
        self.stdout.write(self.style.SUCCESS('='*80 + '\n'))

        credentials = [
            ('👔 Admin (Full Access)', 'admin_kibray', 'admin123', 'Acceso total + costos reales'),
            ('🎯 PM Full (Can send emails)', 'pm_full', 'pm123', 'CRUD proyectos + envío emails'),
            ('📚 PM Trainee (No emails)', 'pm_trainee', 'trainee123', 'CRUD proyectos SIN envío emails'),
            ('🎨 Designer (Interfaz Zen)', 'designer', 'designer123', 'ColorSample, FloorPlan, Chat'),
            ('🏗️  Superintendent (Operativo)', 'superintendent', 'super123', 'Tareas, Daily Log (sin finanzas)'),
            ('👷 Client (Vista externa)', 'cliente_villa', 'client123', 'Solo lectura de su proyecto'),
        ]

        for role, username, password, description in credentials:
            self.stdout.write(f'  {role}:')
            self.stdout.write(f'    Username: {username}')
            self.stdout.write(f'    Password: {password}')
            self.stdout.write(f'    Acceso: {description}\n')

        self.stdout.write(self.style.SUCCESS('='*80))
        self.stdout.write(self.style.WARNING('\n⚠️  ESCENARIO LISTO PARA PRUEBAS:\n'))
        self.stdout.write('  ✅ Finanzas: $5,000 deposit pagado, $500 CO, $45,500 saldo restante')
        self.stdout.write('  ✅ Reembolso: $15 pendiente para empleado José Pintor')
        self.stdout.write('  ✅ Inventario: Herramientas listas para "Transferir a Bodega"')
        self.stdout.write('  ✅ Visual: Planos con pines (task, touchup, info, leftover)')
        self.stdout.write('  ✅ Planner: Schedule jerárquico con tareas, checklist, progress')
        self.stdout.write('  ✅ Roles: 6 perfiles con permisos granulares configurados')
        self.stdout.write('\n')
