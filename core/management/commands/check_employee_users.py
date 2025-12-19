"""
Management command para verificar y vincular usuarios con Employees.
Uso: python manage.py check_employee_users [--fix]
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import Employee


class Command(BaseCommand):
    help = 'Verifica que todos los usuarios tengan Employee vinculado y viceversa'

    def add_arguments(self, parser):
        parser.add_argument(
            '--fix',
            action='store_true',
            help='Intentar vincular automáticamente usuarios con employees por email/nombre',
        )

    def handle(self, *args, **options):
        fix = options['fix']
        
        self.stdout.write(self.style.SUCCESS('=== VERIFICACIÓN USUARIO ↔ EMPLOYEE ===\n'))
        
        # 1. Usuarios sin Employee
        users_without_employee = []
        for user in User.objects.all():
            if not Employee.objects.filter(user=user).exists():
                users_without_employee.append(user)
        
        self.stdout.write(f'📊 Usuarios sin Employee: {len(users_without_employee)}')
        for user in users_without_employee[:10]:
            self.stdout.write(f'   - {user.username} ({user.email})')
        
        # 2. Employees sin User
        employees_without_user = Employee.objects.filter(user__isnull=True)
        self.stdout.write(f'\n📊 Employees sin User: {employees_without_user.count()}')
        for emp in employees_without_user[:10]:
            self.stdout.write(f'   - {emp.id}: {emp.first_name} {emp.last_name} ({emp.email})')
        
        # 3. Vincular automáticamente si --fix
        if fix:
            self.stdout.write(self.style.WARNING('\n🔧 Intentando vincular automáticamente...\n'))
            fixed = 0
            
            for emp in employees_without_user:
                # Intentar por email
                if emp.email:
                    user = User.objects.filter(email=emp.email).first()
                    if user and not hasattr(user, 'employee_profile'):
                        emp.user = user
                        emp.save()
                        self.stdout.write(self.style.SUCCESS(f'   ✅ Vinculado: {emp.first_name} {emp.last_name} → {user.username}'))
                        fixed += 1
                        continue
                
                # Intentar por username similar
                username_base = f"{emp.first_name.lower()}.{emp.last_name.lower()}"
                user = User.objects.filter(username__icontains=username_base).first()
                if user and not hasattr(user, 'employee_profile'):
                    emp.user = user
                    emp.save()
                    self.stdout.write(self.style.SUCCESS(f'   ✅ Vinculado: {emp.first_name} {emp.last_name} → {user.username}'))
                    fixed += 1
            
            self.stdout.write(self.style.SUCCESS(f'\n✅ Total vinculados: {fixed}'))
        else:
            self.stdout.write(self.style.WARNING('\n💡 Usa --fix para intentar vincular automáticamente'))
        
        # 4. Mostrar usuarios que pueden hacer clock-in
        self.stdout.write(self.style.SUCCESS('\n=== USUARIOS QUE PUEDEN HACER CLOCK-IN ==='))
        valid_employees = Employee.objects.filter(user__isnull=False, is_active=True)
        self.stdout.write(f'Total: {valid_employees.count()}\n')
        for emp in valid_employees:
            self.stdout.write(f'✅ {emp.user.username} → Employee: {emp.first_name} {emp.last_name} (ID: {emp.id})')
