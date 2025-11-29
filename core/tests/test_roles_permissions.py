"""
Tests para validar la configuración de roles y permisos del sistema
Valida que setup_roles.py configuró correctamente los 5 grupos
"""
import pytest
from django.test import TestCase
from django.contrib.auth.models import Group, Permission, User
from django.core.management import call_command


class RolesPermissionsTestCase(TestCase):
    """
    Tests para validar la seguridad del sistema basada en roles
    CRÍTICO: Estos tests aseguran que no haya violaciones de seguridad
    """
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Ejecutar setup_roles para configurar los grupos
        call_command('setup_roles')
    
    def test_all_groups_exist(self):
        """TEST 1: Verificar que los 5 grupos fueron creados"""
        groups = ['General Manager', 'Project Manager', 'Superintendent', 'Employee', 'Client']
        for group_name in groups:
            self.assertTrue(
                Group.objects.filter(name=group_name).exists(),
                f"Grupo '{group_name}' debe existir"
            )
    
    def test_general_manager_permissions_count(self):
        """TEST 2: General Manager debe tener 65 permisos (Arquitectura Final)"""
        gm = Group.objects.get(name='General Manager')
        self.assertEqual(gm.permissions.count(), 65,
                        "General Manager debe tener exactamente 65 permisos")
    
    def test_general_manager_has_financial_access(self):
        """TEST 3: General Manager debe tener acceso completo a financieros"""
        gm = Group.objects.get(name='General Manager')
        perms = list(gm.permissions.values_list('codename', flat=True))
        
        critical_perms = [
            'view_expense', 'add_expense', 'change_expense', 'delete_expense',
            'view_income', 'add_income', 'change_income', 'delete_income',
            'view_payrollrecord', 'add_payrollrecord', 'change_payrollrecord', 'delete_payrollrecord',
            'view_invoice', 'add_invoice', 'change_invoice', 'delete_invoice'
        ]
        
        for perm in critical_perms:
            self.assertIn(perm, perms,
                         f"General Manager debe tener permiso '{perm}'")
    
    def test_project_manager_permissions_count(self):
        """TEST 4: Project Manager debe tener 51 permisos (Arquitectura Final)"""
        pm = Group.objects.get(name='Project Manager')
        self.assertEqual(pm.permissions.count(), 51,
                        "Project Manager debe tener exactamente 51 permisos")
    
    def test_project_manager_cannot_delete_employees(self):
        """TEST 5: Project Manager NO puede borrar empleados"""
        pm = Group.objects.get(name='Project Manager')
        perms = list(pm.permissions.values_list('codename', flat=True))
        
        self.assertNotIn('delete_employee', perms,
                        "Project Manager NO debe poder borrar empleados")
    
    def test_project_manager_can_view_finances(self):
        """TEST 6: Project Manager (Full) tiene CRUD completo en finanzas (Arquitectura Final)"""
        pm = Group.objects.get(name='Project Manager')
        perms = list(pm.permissions.values_list('codename', flat=True))
        
        # PM Full tiene CRUD completo en Invoice y ChangeOrder
        self.assertIn('view_invoice', perms, "PM debe poder ver invoices")
        self.assertIn('add_invoice', perms, "PM debe poder agregar invoices")
        self.assertIn('change_invoice', perms, "PM debe poder modificar invoices")
        self.assertIn('delete_invoice', perms, "PM Full puede borrar invoices")
        
        # NO puede modificar expense ni income (solo VIEW)
        self.assertNotIn('delete_expense', perms, "PM NO debe poder borrar expenses")
        self.assertNotIn('delete_income', perms, "PM NO debe poder borrar income")
    
    def test_superintendent_permissions_count(self):
        """TEST 7: Superintendent debe tener 11 permisos (Arquitectura Final)"""
        super_group = Group.objects.get(name='Superintendent')
        self.assertEqual(super_group.permissions.count(), 11,
                        "Superintendent debe tener exactamente 11 permisos")
    
    def test_superintendent_financial_firewall(self):
        """TEST 8 (CRÍTICO): Superintendent NO debe ver datos financieros"""
        super_group = Group.objects.get(name='Superintendent')
        perms = list(super_group.permissions.values_list('codename', flat=True))
        
        financial_perms = [
            'view_invoice', 'view_expense', 'view_income', 
            'view_payrollrecord', 'view_employee',
            'add_changeorder', 'change_changeorder', 'delete_changeorder'
        ]
        
        for perm in financial_perms:
            self.assertNotIn(perm, perms,
                           f"Superintendent NO debe tener permiso '{perm}' (FIREWALL FINANCIERO)")
    
    def test_superintendent_can_manage_daily_operations(self):
        """TEST 9: Superintendent puede gestionar operaciones diarias"""
        super_group = Group.objects.get(name='Superintendent')
        perms = list(super_group.permissions.values_list('codename', flat=True))
        
        operational_perms = [
            'view_project', 'view_schedule',
            'add_dailylog', 'change_dailylog', 'view_dailylog',
            'add_task', 'change_task', 'view_task',
            'add_materialrequest', 'view_materialrequest'
        ]
        
        for perm in operational_perms:
            self.assertIn(perm, perms,
                         f"Superintendent debe tener permiso '{perm}'")
    
    def test_employee_permissions_count(self):
        """TEST 10: Employee debe tener solo 3 permisos"""
        emp = Group.objects.get(name='Employee')
        self.assertEqual(emp.permissions.count(), 3,
                        "Employee debe tener exactamente 3 permisos (ACCESO MÍNIMO)")
    
    def test_employee_minimal_access(self):
        """TEST 11 (CRÍTICO): Employee solo puede ver sus propias tareas"""
        emp = Group.objects.get(name='Employee')
        perms = list(emp.permissions.values_list('codename', flat=True))
        
        # Debe tener
        self.assertIn('view_task', perms, "Employee debe poder ver tasks")
        self.assertIn('change_task', perms, "Employee debe poder cambiar task status")
        self.assertIn('view_timeentry', perms, "Employee debe poder ver sus timeentries")
        
        # NO debe tener
        forbidden = [
            'view_project', 'view_invoice', 'view_expense',
            'view_payrollrecord', 'view_changeorder', 'view_employee'
        ]
        
        for perm in forbidden:
            self.assertNotIn(perm, perms,
                           f"Employee NO debe tener permiso '{perm}' (ACCESO MÍNIMO)")
    
    def test_client_permissions_count(self):
        """TEST 12: Client debe tener 9 permisos (Arquitectura Final)"""
        client = Group.objects.get(name='Client')
        self.assertEqual(client.permissions.count(), 9,
                        "Client debe tener exactamente 9 permisos")
    
    def test_client_view_only_external(self):
        """TEST 13: Client solo puede VER información externa (+ add_chatchannel)"""
        client = Group.objects.get(name='Client')
        perms = list(client.permissions.values_list('codename', flat=True))
        
        # Puede ver (solo VIEW) - Arquitectura Final
        allowed = [
            'view_project', 'view_schedule', 'view_invoice', 'view_changeorder',
            'view_task', 'view_colorsample', 'view_floorplan', 
            'view_chatchannel', 'add_chatchannel'  # ChatChannel permite agregar mensajes
        ]
        for perm in allowed:
            self.assertIn(perm, perms,
                         f"Client debe tener permiso '{perm}'")
        
        # NO puede modificar nada (excepto add_chatchannel para comunicarse)
        for perm in perms:
            self.assertTrue(perm.startswith('view_') or perm == 'add_chatchannel',
                          f"Client solo debe tener permisos 'view_*' o 'add_chatchannel', encontrado: '{perm}'")
    
    def test_client_financial_firewall(self):
        """TEST 14 (CRÍTICO): Client NO debe ver datos internos"""
        client = Group.objects.get(name='Client')
        perms = list(client.permissions.values_list('codename', flat=True))
        
        internal_perms = [
            'view_payrollrecord', 'view_expense', 'view_income',
            'view_employee', 'view_timeentry'
        ]
        
        for perm in internal_perms:
            self.assertNotIn(perm, perms,
                           f"Client NO debe tener permiso '{perm}' (FIREWALL COMPLETO)")
    
    def test_setup_roles_idempotency(self):
        """TEST 15: setup_roles puede ejecutarse múltiples veces sin cambios"""
        # Guardar estado actual
        initial_counts = {
            name: Group.objects.get(name=name).permissions.count()
            for name in ['General Manager', 'Project Manager', 'Superintendent', 'Employee', 'Client']
        }
        
        # Ejecutar setup_roles de nuevo
        call_command('setup_roles')
        
        # Verificar que los counts no cambiaron
        final_counts = {
            name: Group.objects.get(name=name).permissions.count()
            for name in ['General Manager', 'Project Manager', 'Superintendent', 'Employee', 'Client']
        }
        
        self.assertEqual(initial_counts, final_counts,
                        "setup_roles debe ser idempotente (sin cambios al ejecutar múltiples veces)")


class UserRoleAssignmentTestCase(TestCase):
    """
    Tests para validar asignación de roles a usuarios
    """
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        call_command('setup_roles')
    
    def test_assign_general_manager_to_user(self):
        """TEST 16: Asignar rol General Manager a usuario (Arquitectura Final)"""
        user = User.objects.create_user(username='gm_test', password='test123')
        gm_group = Group.objects.get(name='General Manager')
        user.groups.add(gm_group)
        
        self.assertIn(gm_group, user.groups.all(),
                     "Usuario debe estar en grupo General Manager")
        
        # Verificar que el usuario tiene los permisos del grupo
        user_perms = user.get_all_permissions()
        self.assertEqual(len(user_perms), 65,
                       "Usuario con rol GM debe tener 65 permisos del grupo")
        
        # Verificar algunos permisos críticos
        self.assertIn('core.view_expense', user_perms)
        self.assertIn('core.add_payrollrecord', user_perms)
        self.assertIn('core.can_send_external_emails', user_perms)
    
    def test_user_can_have_multiple_roles(self):
        """TEST 17: Usuario puede tener múltiples roles"""
        user = User.objects.create_user(username='multi_role', password='test123')
        pm_group = Group.objects.get(name='Project Manager')
        super_group = Group.objects.get(name='Superintendent')
        
        user.groups.add(pm_group, super_group)
        
        self.assertEqual(user.groups.count(), 2,
                        "Usuario debe estar en 2 grupos")
    
    def test_remove_role_from_user(self):
        """TEST 18: Remover rol de usuario"""
        user = User.objects.create_user(username='remove_role', password='test123')
        emp_group = Group.objects.get(name='Employee')
        user.groups.add(emp_group)
        
        self.assertIn(emp_group, user.groups.all())
        
        user.groups.remove(emp_group)
        
        self.assertNotIn(emp_group, user.groups.all(),
                        "Usuario no debe estar en grupo Employee después de remover")


@pytest.mark.django_db
class TestRolesPermissionsPytest:
    """
    Tests adicionales usando pytest
    """
    
    def test_group_permissions_are_persistent(self):
        """TEST 19: Permisos de grupos persisten en BD"""
        call_command('setup_roles')
        
        gm = Group.objects.get(name='General Manager')
        perm_count = gm.permissions.count()
        
        # Simular reinicio de aplicación (nueva query)
        gm_reloaded = Group.objects.get(name='General Manager')
        
        assert gm_reloaded.permissions.count() == perm_count, \
            "Permisos deben persistir después de recargar grupo"
    
    def test_permission_checking_performance(self):
        """TEST 20: Verificar que check de permisos es rápido"""
        import time
        
        call_command('setup_roles')
        user = User.objects.create_user(username='perf_test', password='test123')
        gm_group = Group.objects.get(name='General Manager')
        user.groups.add(gm_group)
        
        start = time.time()
        for _ in range(100):
            user.has_perm('core.view_expense')
        elapsed = time.time() - start
        
        assert elapsed < 1.0, \
            f"100 permission checks tomaron {elapsed:.3f}s (debe ser <1s)"
