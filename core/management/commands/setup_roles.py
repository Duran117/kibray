"""
Management command para configurar roles y permisos del sistema Kibray
ARQUITECTURA FINAL: Incluye PM Trainee y Designer
"""
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand

from core.models import (
    ChangeOrder,
    ChatChannel,
    ColorSample,
    DailyLog,
    Employee,
    Estimate,
    Expense,
    FloorPlan,
    Income,
    Invoice,
    MaterialRequest,
    PayrollRecord,
    Project,
    Schedule,
    Task,
    TimeEntry,
)


class Command(BaseCommand):
    help = 'Configura grupos y permisos para Arquitectura Final Kibray (6 roles)'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('\n🔐 CONFIGURANDO ROLES Y PERMISOS - ARQUITECTURA FINAL\n'))

        # Create custom permission for email sending
        self._create_custom_permissions()

        # Setup roles
        self.setup_general_manager()
        self.setup_project_manager()
        self.setup_project_manager_trainee()  # NEW
        self.setup_designer()  # NEW
        self.setup_superintendent()
        self.setup_employee()
        self.setup_client()

        self.stdout.write(self.style.SUCCESS('\n✅ Roles configurados exitosamente\n'))

    def _create_custom_permissions(self):
        """Create custom permissions not tied to models"""
        from django.contrib.contenttypes.models import ContentType

        # Get or create a content type for custom permissions
        ct, _ = ContentType.objects.get_or_create(
            app_label='core',
            model='custompermission'  # Dummy model name
        )

        # Create custom permission for email sending
        Permission.objects.get_or_create(
            codename='can_send_external_emails',
            name='Can send external emails (invoices, estimates)',
            content_type=ct
        )

        self.stdout.write('  ✅ Custom permissions created')

    def setup_general_manager(self):
        """
        General Manager (Admin Operativo): Full access + Real Costs
        """
        group, created = Group.objects.get_or_create(name='General Manager')
        group.permissions.clear()

        models = [
            Project, Estimate, Invoice, Employee, Expense, Income,
            PayrollRecord, TimeEntry, ChangeOrder, Task, Schedule,
            MaterialRequest, DailyLog, ColorSample, FloorPlan, ChatChannel
        ]

        permissions = []
        for model in models:
            ct = ContentType.objects.get_for_model(model)
            permissions.extend(Permission.objects.filter(
                content_type=ct,
                codename__in=[
                    f'add_{model._meta.model_name}',
                    f'change_{model._meta.model_name}',
                    f'delete_{model._meta.model_name}',
                    f'view_{model._meta.model_name}',
                ]
            ))

        # Add custom permissions
        permissions.extend(Permission.objects.filter(
            codename__in=['can_send_external_emails']
        ))

        group.permissions.set(permissions)
        self.stdout.write(self.style.SUCCESS(f'  ✅ General Manager configurado ({len(permissions)} permisos)'))

    def setup_project_manager(self):
        """
        Project Manager (Full): CRUD en Project, Task, Schedule, ChangeOrder
        Puede enviar emails. Ve costos.
        """
        group, created = Group.objects.get_or_create(name='Project Manager')
        group.permissions.clear()

        # CRUD completo
        full_crud_models = [
            Project, Task, Schedule, ChangeOrder, MaterialRequest,
            TimeEntry, Invoice, Estimate, DailyLog
        ]

        permissions = []
        for model in full_crud_models:
            ct = ContentType.objects.get_for_model(model)
            permissions.extend(Permission.objects.filter(
                content_type=ct,
                codename__in=[
                    f'add_{model._meta.model_name}',
                    f'change_{model._meta.model_name}',
                    f'delete_{model._meta.model_name}',
                    f'view_{model._meta.model_name}',
                ]
            ))

        # Solo VIEW en finanzas
        view_only_models = [Expense, Income, PayrollRecord]
        for model in view_only_models:
            ct = ContentType.objects.get_for_model(model)
            permissions.extend(Permission.objects.filter(
                content_type=ct,
                codename=f'view_{model._meta.model_name}'
            ))

        # Employee: puede ver y cambiar, pero NO borrar
        ct = ContentType.objects.get_for_model(Employee)
        permissions.extend(Permission.objects.filter(
            content_type=ct,
            codename__in=['add_employee', 'change_employee', 'view_employee']
        ))

        # ColorSample y FloorPlan: Full access para revisar trabajos de diseño
        for model in [ColorSample, FloorPlan]:
            ct = ContentType.objects.get_for_model(model)
            permissions.extend(Permission.objects.filter(
                content_type=ct,
                codename__in=[
                    f'add_{model._meta.model_name}',
                    f'change_{model._meta.model_name}',
                    f'delete_{model._meta.model_name}',
                    f'view_{model._meta.model_name}',
                ]
            ))

        # CAN send external emails
        permissions.extend(Permission.objects.filter(
            codename='can_send_external_emails'
        ))

        group.permissions.set(permissions)
        self.stdout.write(self.style.SUCCESS(f'  ✅ Project Manager (Full) configurado ({len(permissions)} permisos)'))

    def setup_project_manager_trainee(self):
        """
        Project Manager (En Entrenamiento):
        - Puede CREAR Invoices y COs
        - PROHIBIDO: Enviar correos externos (must_review)
        - PROHIBIDO: Borrar usuarios
        - Invoices quedan en draft_for_review
        """
        group, created = Group.objects.get_or_create(name='Project Manager (Trainee)')
        group.permissions.clear()

        # CRUD en operaciones básicas
        crud_models = [Project, Task, Schedule, TimeEntry, DailyLog, MaterialRequest]

        permissions = []
        for model in crud_models:
            ct = ContentType.objects.get_for_model(model)
            permissions.extend(Permission.objects.filter(
                content_type=ct,
                codename__in=[
                    f'add_{model._meta.model_name}',
                    f'change_{model._meta.model_name}',
                    f'view_{model._meta.model_name}',
                ]
            ))

        # Invoices y COs: ADD y CHANGE (NO DELETE)
        for model in [Invoice, ChangeOrder, Estimate]:
            ct = ContentType.objects.get_for_model(model)
            permissions.extend(Permission.objects.filter(
                content_type=ct,
                codename__in=[
                    f'add_{model._meta.model_name}',
                    f'change_{model._meta.model_name}',
                    f'view_{model._meta.model_name}',
                ]
            ))

        # Solo VIEW en finanzas
        view_only_models = [Expense, Income, PayrollRecord, Employee]
        for model in view_only_models:
            ct = ContentType.objects.get_for_model(model)
            permissions.extend(Permission.objects.filter(
                content_type=ct,
                codename=f'view_{model._meta.model_name}'
            ))

        # ColorSample y FloorPlan: VIEW only
        for model in [ColorSample, FloorPlan]:
            ct = ContentType.objects.get_for_model(model)
            permissions.extend(Permission.objects.filter(
                content_type=ct,
                codename=f'view_{model._meta.model_name}'
            ))

        # EXPLICITLY NO send_external_emails permission

        group.permissions.set(permissions)
        self.stdout.write(self.style.WARNING(f'  ⚠️  PM Trainee configurado ({len(permissions)} permisos) - SIN envío de emails'))

    def setup_designer(self):
        """
        Designer: Interfaz "Zen" - Acceso visual y colaborativo
        - ColorSample: Full CRUD
        - FloorPlan: Full CRUD
        - ChatChannel: Full CRUD
        - Project: Solo VIEW (para contexto)
        - SIN acceso a finanzas o inventario denso
        """
        group, created = Group.objects.get_or_create(name='Designer')
        group.permissions.clear()

        permissions = []

        # Full CRUD en herramientas de diseño
        design_models = [ColorSample, FloorPlan, ChatChannel]
        for model in design_models:
            ct = ContentType.objects.get_for_model(model)
            permissions.extend(Permission.objects.filter(
                content_type=ct,
                codename__in=[
                    f'add_{model._meta.model_name}',
                    f'change_{model._meta.model_name}',
                    f'delete_{model._meta.model_name}',
                    f'view_{model._meta.model_name}',
                ]
            ))

        # Solo VIEW en Project (contexto) y Task (coordinar con equipo)
        for model in [Project, Task]:
            ct = ContentType.objects.get_for_model(model)
            permissions.extend(Permission.objects.filter(
                content_type=ct,
                codename=f'view_{model._meta.model_name}'
            ))

        group.permissions.set(permissions)
        self.stdout.write(self.style.SUCCESS(f'  ✅ Designer configurado ({len(permissions)} permisos) - Vista simplificada'))

    def setup_superintendent(self):
        """
        Superintendent: Operativo puro. Cero finanzas.
        VIEW: Project, Schedule
        ADD/CHANGE: DailyLog, Task
        ADD: MaterialRequest
        """
        group, created = Group.objects.get_or_create(name='Superintendent')
        group.permissions.clear()

        permissions = []

        # Solo VIEW en Project y Schedule
        for model in [Project, Schedule]:
            ct = ContentType.objects.get_for_model(model)
            permissions.extend(Permission.objects.filter(
                content_type=ct,
                codename=f'view_{model._meta.model_name}'
            ))

        # Add/Change en DailyLog y Task
        for model in [DailyLog, Task]:
            ct = ContentType.objects.get_for_model(model)
            permissions.extend(Permission.objects.filter(
                content_type=ct,
                codename__in=[
                    f'add_{model._meta.model_name}',
                    f'change_{model._meta.model_name}',
                    f'view_{model._meta.model_name}',
                ]
            ))

        # Solo Add en MaterialRequest
        ct = ContentType.objects.get_for_model(MaterialRequest)
        permissions.extend(Permission.objects.filter(
            content_type=ct,
            codename__in=['add_materialrequest', 'view_materialrequest']
        ))

        # VIEW FloorPlan para coordinar trabajo en campo
        ct = ContentType.objects.get_for_model(FloorPlan)
        permissions.extend(Permission.objects.filter(
            content_type=ct,
            codename='view_floorplan'
        ))

        # FIREWALL: NO permisos en Invoice, Expense, Income, PayrollRecord, Employee, ChangeOrder

        group.permissions.set(permissions)
        self.stdout.write(self.style.SUCCESS(f'  ✅ Superintendent configurado ({len(permissions)} permisos) - FIREWALL FINANCIERO'))

    def setup_employee(self):
        """
        Employee: Solo Tareas y Clock-In
        - VIEW/CHANGE: Task (solo status)
        - VIEW: TimeEntry (filtrado por usuario en vistas)
        - ACCESO MÍNIMO
        """
        group, created = Group.objects.get_or_create(name='Employee')
        group.permissions.clear()

        permissions = []

        # VIEW/CHANGE: Task (solo pueden actualizar status de sus tareas)
        ct = ContentType.objects.get_for_model(Task)
        permissions.extend(Permission.objects.filter(
            content_type=ct,
            codename__in=['view_task', 'change_task']
        ))

        # VIEW: TimeEntry (para revisar sus propios registros)
        ct = ContentType.objects.get_for_model(TimeEntry)
        permissions.extend(Permission.objects.filter(
            content_type=ct,
            codename='view_timeentry'
        ))

        group.permissions.set(permissions)
        self.stdout.write(self.style.SUCCESS(f'  ✅ Employee configurado ({len(permissions)} permisos) - Acceso mínimo'))

    def setup_client(self):
        """
        Client: Solo lectura de "Realidad Venta"
        - VIEW: Project, Schedule, Invoice, ChangeOrder, ColorSample, FloorPlan
        - FIREWALL COMPLETO: NO ve TimeEntry, PayrollRecord, Expense, Income, Employee
        """
        group, created = Group.objects.get_or_create(name='Client')
        group.permissions.clear()

        permissions = []

        # Solo VIEW en modelos relevantes para cliente
        view_models = [Project, Schedule, Invoice, ChangeOrder, ColorSample, FloorPlan, Task]
        for model in view_models:
            ct = ContentType.objects.get_for_model(model)
            permissions.extend(Permission.objects.filter(
                content_type=ct,
                codename=f'view_{model._meta.model_name}'
            ))

        # Puede agregar comentarios en ChatChannel
        ct = ContentType.objects.get_for_model(ChatChannel)
        permissions.extend(Permission.objects.filter(
            content_type=ct,
            codename__in=['view_chatchannel', 'add_chatchannel']
        ))

        group.permissions.set(permissions)
        self.stdout.write(self.style.SUCCESS(f'  ✅ Client configurado ({len(permissions)} permisos) - Vista externa'))
