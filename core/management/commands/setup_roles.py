"""
Management command para configurar roles y permisos del sistema Kibray
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from core.models import (
    Project, Estimate, Invoice, Employee, Expense, Income,
    Task, Schedule, ChangeOrder, MaterialRequest, DailyLog,
    PayrollRecord, TimeEntry
)


class Command(BaseCommand):
    help = 'Configura grupos y permisos para el sistema Kibray (ERP de Construcción)'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('🔧 Iniciando configuración de roles...'))
        
        # Crear/actualizar los 5 roles principales
        self.setup_general_manager()
        self.setup_project_manager()
        self.setup_superintendent()
        self.setup_employee()
        self.setup_client()
        
        self.stdout.write(self.style.SUCCESS('\n✅ Roles configurados exitosamente'))

    def setup_general_manager(self):
        """
        General Manager: CRUD total en Project, Estimate, Invoice, Employee, Financials
        Puede ver costos reales
        """
        group, created = Group.objects.get_or_create(name='General Manager')
        group.permissions.clear()
        
        models = [Project, Estimate, Invoice, Employee, Expense, Income, 
                  PayrollRecord, TimeEntry, ChangeOrder, Task, Schedule, MaterialRequest]
        
        permissions = []
        for model in models:
            ct = ContentType.objects.get_for_model(model)
            # CRUD completo
            permissions.extend(Permission.objects.filter(
                content_type=ct,
                codename__in=[
                    f'add_{model._meta.model_name}',
                    f'change_{model._meta.model_name}',
                    f'delete_{model._meta.model_name}',
                    f'view_{model._meta.model_name}',
                ]
            ))
        
        group.permissions.set(permissions)
        self.stdout.write(self.style.SUCCESS(f'  ✅ General Manager configurado ({len(permissions)} permisos)'))

    def setup_project_manager(self):
        """
        Project Manager: CRUD en Project, Task, Schedule, ChangeOrder, MaterialRequest
        NO puede borrar usuarios ni cambiar configuraciones globales. Ve costos.
        """
        group, created = Group.objects.get_or_create(name='Project Manager')
        group.permissions.clear()
        
        # Modelos con CRUD completo
        full_crud_models = [Project, Task, Schedule, ChangeOrder, MaterialRequest, TimeEntry]
        
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
        
        # Modelos con solo view (pueden ver finanzas pero no modificar)
        view_only_models = [Invoice, Expense, Income, PayrollRecord]
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
            codename__in=[
                'add_employee',
                'change_employee',
                'view_employee',
            ]
        ))
        
        group.permissions.set(permissions)
        self.stdout.write(self.style.SUCCESS(f'  ✅ Project Manager configurado ({len(permissions)} permisos)'))

    def setup_superintendent(self):
        """
        Superintendent: View Project, View Schedule, Add/Change DailyLog, Add/Change Task, Add MaterialRequest
        BLOQUEO TOTAL: NO ver costos, hourly_rate, invoice, add_changeorder
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
        
        # Solo Add en MaterialRequest (puede pedirlos, no ver todos los detalles)
        ct = ContentType.objects.get_for_model(MaterialRequest)
        permissions.extend(Permission.objects.filter(
            content_type=ct,
            codename__in=['add_materialrequest', 'view_materialrequest']
        ))
        
        # EXPLÍCITAMENTE: NO dar permisos de:
        # - view_invoice, add_changeorder, view_expense, view_income, view_payrollrecord
        # - view_employee (para no ver hourly_rate)
        
        group.permissions.set(permissions)
        self.stdout.write(self.style.SUCCESS(f'  ✅ Superintendent configurado ({len(permissions)} permisos) - BLOQUEO FINANCIERO'))

    def setup_employee(self):
        """
        Employee: View Task, Change Task (status), View Own TimeEntry
        BLOQUEO: Cero acceso financiero
        """
        group, created = Group.objects.get_or_create(name='Employee')
        group.permissions.clear()
        
        permissions = []
        
        # Task: ver y cambiar status
        ct = ContentType.objects.get_for_model(Task)
        permissions.extend(Permission.objects.filter(
            content_type=ct,
            codename__in=[
                'view_task',
                'change_task',  # Para actualizar status
            ]
        ))
        
        # TimeEntry: solo ver (filtrado por usuario en las vistas)
        ct = ContentType.objects.get_for_model(TimeEntry)
        permissions.extend(Permission.objects.filter(
            content_type=ct,
            codename='view_timeentry'
        ))
        
        group.permissions.set(permissions)
        self.stdout.write(self.style.SUCCESS(f'  ✅ Employee configurado ({len(permissions)} permisos) - ACCESO MÍNIMO'))

    def setup_client(self):
        """
        Client: View Project, View Schedule, View Invoice, View ChangeOrder
        Financial Firewall: NO acceso a PayrollRecord, Expense (interno), campos de costo real
        """
        group, created = Group.objects.get_or_create(name='Client')
        group.permissions.clear()
        
        permissions = []
        
        # Solo VIEW en estos modelos
        for model in [Project, Schedule, Invoice, ChangeOrder]:
            ct = ContentType.objects.get_for_model(model)
            permissions.extend(Permission.objects.filter(
                content_type=ct,
                codename=f'view_{model._meta.model_name}'
            ))
        
        # EXPLÍCITAMENTE: NO dar permisos de:
        # - PayrollRecord, Expense, Income, Employee, TimeEntry
        # - Los views deben filtrar campos sensibles (hourly_rate, cost_rate, etc.)
        
        group.permissions.set(permissions)
        self.stdout.write(self.style.SUCCESS(f'  ✅ Client configurado ({len(permissions)} permisos) - FIREWALL FINANCIERO'))
