"""
Database Restore Management Command
Usage: python manage.py restore_database --file=backup_file.sql.gz
"""
import logging
import os
import subprocess

from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Restores a PostgreSQL database from a backup file"

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            type=str,
            required=True,
            help="Path to the backup file (.sql or .sql.gz)",
        )
        parser.add_argument(
            "--confirm",
            action="store_true",
            help="Skip confirmation prompt (DANGEROUS)",
        )

    def handle(self, *args, **options):
        backup_file = options["file"]
        skip_confirmation = options["confirm"]

        if not os.path.exists(backup_file):
            self.stdout.write(self.style.ERROR(f"❌ Backup file not found: {backup_file}"))
            return

        # Safety confirmation
        if not skip_confirmation:
            self.stdout.write(self.style.WARNING("⚠️  WARNING: This will OVERWRITE your current database!"))
            confirmation = input("Type 'yes' to continue: ")
            if confirmation.lower() != "yes":
                self.stdout.write("❌ Restore cancelled")
                return

        self.stdout.write(f"📥 Restoring database from: {backup_file}")

        try:
            # Get database URL from environment
            database_url = os.getenv("DATABASE_URL")

            if not database_url:
                self.stdout.write(self.style.ERROR("❌ DATABASE_URL not found in environment"))
                return

            # Decompress if gzipped
            sql_file = backup_file
            if backup_file.endswith(".gz"):
                self.stdout.write("🗜️  Decompressing backup...")
                sql_file = backup_file[:-3]  # Remove .gz extension
                subprocess.run(["gunzip", "-k", "-f", backup_file], check=True)

            # Restore using psql
            self.stdout.write("🔄 Restoring database...")
            result = subprocess.run(
                ["psql", database_url, "-f", sql_file],
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                self.stdout.write(self.style.ERROR(f"❌ Restore failed: {result.stderr}"))
                return

            # Clean up decompressed file if it was created
            if backup_file.endswith(".gz") and os.path.exists(sql_file):
                os.remove(sql_file)

            self.stdout.write(self.style.SUCCESS("✅ Database restored successfully"))
            logger.info(f"Database restored from: {backup_file}")

        except subprocess.CalledProcessError as e:
            self.stdout.write(self.style.ERROR(f"❌ Restore failed: {str(e)}"))
            logger.error(f"Database restore failed: {str(e)}")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Unexpected error: {str(e)}"))
            logger.error(f"Database restore error: {str(e)}")
