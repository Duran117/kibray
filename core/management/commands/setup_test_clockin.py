"""
Management command para preparar prueba de clock-in.
Uso: python manage.py setup_test_clockin <username>
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from core.models import Employee, Project, ResourceAssignment


class Command(BaseCommand):
    help = 'Prepara un usuario para pruebas de clock-in (verifica Employee y crea asignación HOY)'

    def add_arguments(self, parser):
        parser.add_argument(
            'username',
            type=str,
            help='Username del usuario a preparar'
        )

    def handle(self, *args, **options):
        username = options['username']
        today = timezone.localdate()
        
        self.stdout.write(self.style.SUCCESS(f'\n=== PREPARANDO PRUEBA DE CLOCK-IN PARA: {username} ===\n'))
        
        # 1. Verificar usuario
        try:
            user = User.objects.get(username=username)
            self.stdout.write(self.style.SUCCESS(f'✅ Usuario encontrado: {user.username} (ID: {user.id})'))
            self.stdout.write(f'   Email: {user.email}')
            self.stdout.write(f'   Is staff: {user.is_staff}')
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'❌ Usuario "{username}" no existe'))
            self.stdout.write('\nUsuarios disponibles:')
            for u in User.objects.all()[:10]:
                self.stdout.write(f'   - {u.username}')
            return
        
        # 2. Verificar Employee vinculado
        try:
            employee = user.employee_profile
            self.stdout.write(self.style.SUCCESS(f'✅ Employee vinculado: {employee.first_name} {employee.last_name} (ID: {employee.id})'))
        except Exception:
            self.stdout.write(self.style.ERROR(f'❌ Usuario NO tiene Employee vinculado'))
            self.stdout.write('\n¿Crear Employee para este usuario? (y/n): ', ending='')
            
            # Listar employees sin user
            employees_sin_user = Employee.objects.filter(user__isnull=True)
            if employees_sin_user.exists():
                self.stdout.write(self.style.WARNING('\nEmployees sin usuario vinculado:'))
                for emp in employees_sin_user[:5]:
                    self.stdout.write(f'   {emp.id}: {emp.first_name} {emp.last_name} ({emp.email})')
                self.stdout.write('\nPuedes vincular manualmente: emp.user = user; emp.save()')
            return
        
        # 3. Verificar proyectos disponibles
        projects = Project.objects.all()
        self.stdout.write(f'\n📊 Proyectos en el sistema: {projects.count()}')
        if not projects.exists():
            self.stdout.write(self.style.ERROR('❌ No hay proyectos. Crea al menos uno.'))
            return
        
        for proj in projects[:5]:
            self.stdout.write(f'   - {proj.id}: {proj.name}')
        
        # 4. Verificar asignaciones HOY
        assignments_today = ResourceAssignment.objects.filter(
            employee=employee,
            date=today
        )
        
        self.stdout.write(f'\n📅 Asignaciones para HOY ({today}): {assignments_today.count()}')
        
        if assignments_today.exists():
            self.stdout.write(self.style.SUCCESS('✅ Ya tiene asignaciones hoy:'))
            for assign in assignments_today:
                self.stdout.write(f'   - {assign.project.name} ({assign.get_shift_display()})')
        else:
            self.stdout.write(self.style.WARNING('⚠️  NO tiene asignaciones para hoy'))
            
            # Crear asignación automática
            first_project = projects.first()
            self.stdout.write(f'\n🔧 Creando asignación de prueba...')
            self.stdout.write(f'   Proyecto: {first_project.name}')
            self.stdout.write(f'   Fecha: {today}')
            self.stdout.write(f'   Turno: Día completo')
            
            assignment = ResourceAssignment.objects.create(
                employee=employee,
                project=first_project,
                date=today,
                shift='FULL_DAY',
                notes='Asignación de prueba para clock-in'
            )
            
            self.stdout.write(self.style.SUCCESS(f'✅ Asignación creada (ID: {assignment.id})'))
        
        # 5. Verificar TimeEntry abierto
        from core.models import TimeEntry
        open_entries = TimeEntry.objects.filter(
            employee=employee,
            end_time__isnull=True
        )
        
        if open_entries.exists():
            self.stdout.write(self.style.WARNING(f'\n⚠️  Tiene {open_entries.count()} entrada(s) abierta(s):'))
            for entry in open_entries:
                self.stdout.write(f'   - Proyecto: {entry.project.name}, Inicio: {entry.start_time}')
                self.stdout.write('   Debes hacer Clock Out primero')
        else:
            self.stdout.write(self.style.SUCCESS('\n✅ No hay entradas abiertas'))
        
        # 6. Resumen final
        self.stdout.write(self.style.SUCCESS('\n' + '='*60))
        self.stdout.write(self.style.SUCCESS('RESUMEN: Usuario listo para clock-in'))
        self.stdout.write(self.style.SUCCESS('='*60))
        self.stdout.write(f'Usuario: {user.username}')
        self.stdout.write(f'Employee: {employee.first_name} {employee.last_name}')
        self.stdout.write(f'Asignaciones hoy: {ResourceAssignment.objects.filter(employee=employee, date=today).count()}')
        self.stdout.write(f'Proyectos disponibles: {projects.count()}')
        self.stdout.write(f'\n✅ Ahora puedes hacer login y probar clock-in en: /dashboard/employee/')
