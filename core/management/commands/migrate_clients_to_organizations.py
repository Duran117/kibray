"""
Management command para migrar clientes existentes al sistema de organizaciones.

Este comando:
1. Identifica clientes sin ClientContact
2. Opcionalmente los asigna a una organización existente o nueva
3. Crea los registros ClientContact necesarios

Uso:
    python manage.py migrate_clients_to_organizations --list
    python manage.py migrate_clients_to_organizations --assign-org=1 --clients=5,6,7
    python manage.py migrate_clients_to_organizations --create-individual-orgs
    python manage.py migrate_clients_to_organizations --cleanup-test-users
"""

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.db import transaction

User = get_user_model()


class Command(BaseCommand):
    help = "Migra clientes existentes al sistema de organizaciones (ClientContact)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--list",
            action="store_true",
            help="Lista clientes sin ClientContact (sin hacer cambios)",
        )
        parser.add_argument(
            "--assign-org",
            type=int,
            help="ID de la organización a la que asignar clientes",
        )
        parser.add_argument(
            "--clients",
            type=str,
            help="IDs de clientes a migrar (separados por coma). Si no se especifica, migra todos.",
        )
        parser.add_argument(
            "--role",
            type=str,
            default="project_lead",
            choices=["project_lead", "observer", "accounting", "executive", "owner"],
            help="Rol a asignar (default: project_lead)",
        )
        parser.add_argument(
            "--create-individual-orgs",
            action="store_true",
            help="Crear una organización individual para cada cliente sin org",
        )
        parser.add_argument(
            "--cleanup-test-users",
            action="store_true",
            help="Eliminar usuarios de prueba (emails que contienen test, tmp, o vacíos)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Mostrar qué se haría sin hacer cambios",
        )

    def handle(self, *args, **options):
        from core.models import ClientContact, ClientOrganization, Profile

        # Obtener clientes sin ClientContact
        clients_without_contact = User.objects.filter(
            profile__role="client"
        ).exclude(
            id__in=ClientContact.objects.values_list("user_id", flat=True)
        ).order_by("email")

        # Opción: Listar
        if options["list"]:
            self.stdout.write(self.style.WARNING(
                f"\n=== Clientes sin ClientContact: {clients_without_contact.count()} ==="
            ))
            for client in clients_without_contact:
                name = client.get_full_name() or "(sin nombre)"
                email = client.email or "(sin email)"
                self.stdout.write(f"  ID {client.id}: {email} - {name}")
            
            self.stdout.write(self.style.WARNING("\n=== Organizaciones disponibles ==="))
            for org in ClientOrganization.objects.filter(is_active=True):
                contacts_count = org.contacts.count()
                self.stdout.write(f"  ID {org.id}: {org.name} ({contacts_count} contactos)")
            return

        # Opción: Limpiar usuarios de prueba
        if options["cleanup_test_users"]:
            test_patterns = ["test", "tmp", "example.com"]
            test_clients = clients_without_contact.filter(
                email__icontains="test"
            ) | clients_without_contact.filter(
                email__icontains="tmp"
            ) | clients_without_contact.filter(
                email__icontains="example.com"
            ) | clients_without_contact.filter(
                email=""
            ) | clients_without_contact.filter(
                email__isnull=True
            )
            
            self.stdout.write(self.style.WARNING(
                f"\n=== Usuarios de prueba a eliminar: {test_clients.count()} ==="
            ))
            for client in test_clients:
                self.stdout.write(f"  - {client.email or '(vacío)'} (ID: {client.id})")
            
            if options["dry_run"]:
                self.stdout.write(self.style.NOTICE("\n[DRY RUN] No se realizaron cambios"))
                return
            
            confirm = input("\n¿Eliminar estos usuarios? (yes/no): ")
            if confirm.lower() == "yes":
                with transaction.atomic():
                    count = test_clients.count()
                    for client in test_clients:
                        # Eliminar profile primero
                        Profile.objects.filter(user=client).delete()
                        client.delete()
                    self.stdout.write(self.style.SUCCESS(f"✅ Eliminados {count} usuarios de prueba"))
            else:
                self.stdout.write(self.style.NOTICE("Operación cancelada"))
            return

        # Opción: Asignar a organización específica
        if options["assign_org"]:
            try:
                org = ClientOrganization.objects.get(id=options["assign_org"])
            except ClientOrganization.DoesNotExist:
                raise CommandError(f"Organización con ID {options['assign_org']} no existe")
            
            # Filtrar clientes específicos si se proporcionaron
            if options["clients"]:
                client_ids = [int(x.strip()) for x in options["clients"].split(",")]
                clients_to_migrate = clients_without_contact.filter(id__in=client_ids)
            else:
                clients_to_migrate = clients_without_contact
            
            self.stdout.write(self.style.WARNING(
                f"\n=== Asignando {clients_to_migrate.count()} clientes a: {org.name} ==="
            ))
            
            for client in clients_to_migrate:
                self.stdout.write(f"  - {client.email} -> {org.name} (rol: {options['role']})")
            
            if options["dry_run"]:
                self.stdout.write(self.style.NOTICE("\n[DRY RUN] No se realizaron cambios"))
                return
            
            confirm = input("\n¿Continuar? (yes/no): ")
            if confirm.lower() == "yes":
                with transaction.atomic():
                    role = options["role"]
                    for client in clients_to_migrate:
                        ClientContact.objects.create(
                            user=client,
                            organization=org,
                            role=role,
                            can_approve_change_orders=(role in ["project_lead", "accounting", "owner"]),
                            can_view_financials=(role in ["project_lead", "accounting", "owner", "executive"]),
                            can_create_tasks=(role == "project_lead"),
                            can_approve_colors=(role in ["project_lead", "owner"]),
                            receive_daily_reports=(role == "project_lead"),
                            receive_invoice_notifications=(role in ["project_lead", "accounting", "owner"]),
                        )
                    self.stdout.write(self.style.SUCCESS(
                        f"✅ Migrados {clients_to_migrate.count()} clientes a {org.name}"
                    ))
            else:
                self.stdout.write(self.style.NOTICE("Operación cancelada"))
            return

        # Opción: Crear organizaciones individuales
        if options["create_individual_orgs"]:
            # Solo para clientes con nombre y email válido
            valid_clients = clients_without_contact.exclude(
                email__icontains="test"
            ).exclude(
                email__icontains="tmp"
            ).exclude(
                email__icontains="example.com"
            ).exclude(
                email=""
            ).exclude(
                first_name=""
            )
            
            self.stdout.write(self.style.WARNING(
                f"\n=== Creando organizaciones individuales para {valid_clients.count()} clientes ==="
            ))
            
            for client in valid_clients:
                org_name = f"{client.get_full_name()} (Individual)"
                self.stdout.write(f"  - {client.email} -> Nueva org: {org_name}")
            
            if options["dry_run"]:
                self.stdout.write(self.style.NOTICE("\n[DRY RUN] No se realizaron cambios"))
                return
            
            confirm = input("\n¿Continuar? (yes/no): ")
            if confirm.lower() == "yes":
                with transaction.atomic():
                    created = 0
                    for client in valid_clients:
                        org_name = f"{client.get_full_name()} (Individual)"
                        org = ClientOrganization.objects.create(
                            name=org_name,
                            organization_type="individual",
                            billing_email=client.email,
                        )
                        ClientContact.objects.create(
                            user=client,
                            organization=org,
                            role="owner",
                            can_approve_change_orders=True,
                            can_view_financials=True,
                            can_create_tasks=True,
                            can_approve_colors=True,
                            receive_daily_reports=True,
                            receive_invoice_notifications=True,
                        )
                        created += 1
                    self.stdout.write(self.style.SUCCESS(
                        f"✅ Creadas {created} organizaciones individuales"
                    ))
            else:
                self.stdout.write(self.style.NOTICE("Operación cancelada"))
            return

        # Si no se especificó ninguna opción
        self.stdout.write(self.style.NOTICE(
            "\nUso: python manage.py migrate_clients_to_organizations [--list|--assign-org=ID|--create-individual-orgs|--cleanup-test-users]"
        ))
        self.stdout.write("Ejecute con --list para ver clientes sin migrar")
