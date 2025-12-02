"""
Database Backup Management Command
Usage: python manage.py backup_database [--upload-s3]
"""
import os
import subprocess
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Creates a backup of the PostgreSQL database"

    def add_arguments(self, parser):
        parser.add_argument(
            "--upload-s3",
            action="store_true",
            help="Upload backup to S3 after creation",
        )
        parser.add_argument(
            "--keep-days",
            type=int,
            default=30,
            help="Number of days to keep backups (default: 30)",
        )

    def handle(self, *args, **options):
        upload_s3 = options["upload_s3"]
        keep_days = options["keep_days"]

        # Create backups directory
        backup_dir = os.path.join(settings.BASE_DIR, "backups")
        os.makedirs(backup_dir, exist_ok=True)

        # Generate backup filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = os.path.join(backup_dir, f"kibray_backup_{timestamp}.sql")

        self.stdout.write(f"📦 Creating database backup: {backup_file}")

        try:
            # Get database URL from environment
            database_url = os.getenv("DATABASE_URL")
            
            if not database_url:
                self.stdout.write(self.style.ERROR("❌ DATABASE_URL not found in environment"))
                return

            # Create backup using pg_dump
            result = subprocess.run(
                [
                    "pg_dump",
                    "--no-owner",
                    "--no-acl",
                    "--clean",
                    "--if-exists",
                    "-f",
                    backup_file,
                    database_url,
                ],
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                self.stdout.write(self.style.ERROR(f"❌ Backup failed: {result.stderr}"))
                return

            # Compress backup
            self.stdout.write("🗜️  Compressing backup...")
            subprocess.run(["gzip", backup_file], check=True)
            backup_file_gz = f"{backup_file}.gz"

            file_size = os.path.getsize(backup_file_gz) / (1024 * 1024)  # MB
            self.stdout.write(self.style.SUCCESS(f"✅ Backup created: {backup_file_gz} ({file_size:.2f} MB)"))

            # Upload to S3 if requested
            if upload_s3:
                self._upload_to_s3(backup_file_gz, timestamp)

            # Clean up old backups
            self._cleanup_old_backups(backup_dir, keep_days)

        except subprocess.CalledProcessError as e:
            self.stdout.write(self.style.ERROR(f"❌ Backup failed: {str(e)}"))
            logger.error(f"Database backup failed: {str(e)}")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Unexpected error: {str(e)}"))
            logger.error(f"Database backup error: {str(e)}")

    def _upload_to_s3(self, backup_file, timestamp):
        """Upload backup file to S3"""
        try:
            import boto3
            from botocore.exceptions import ClientError

            self.stdout.write("☁️  Uploading to S3...")

            s3_client = boto3.client(
                "s3",
                aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
                aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
                region_name=os.getenv("AWS_S3_REGION_NAME", "us-east-1"),
            )

            bucket_name = os.getenv("AWS_STORAGE_BUCKET_NAME")
            s3_key = f"backups/database/kibray_backup_{timestamp}.sql.gz"

            s3_client.upload_file(backup_file, bucket_name, s3_key)

            self.stdout.write(self.style.SUCCESS(f"✅ Uploaded to S3: s3://{bucket_name}/{s3_key}"))
            logger.info(f"Database backup uploaded to S3: {s3_key}")

        except ImportError:
            self.stdout.write(self.style.WARNING("⚠️  boto3 not installed, skipping S3 upload"))
        except ClientError as e:
            self.stdout.write(self.style.ERROR(f"❌ S3 upload failed: {str(e)}"))
            logger.error(f"S3 upload failed: {str(e)}")

    def _cleanup_old_backups(self, backup_dir, keep_days):
        """Delete backups older than keep_days"""
        cutoff_date = datetime.now() - timedelta(days=keep_days)
        deleted_count = 0

        self.stdout.write(f"🧹 Cleaning up backups older than {keep_days} days...")

        for filename in os.listdir(backup_dir):
            if filename.startswith("kibray_backup_") and filename.endswith(".sql.gz"):
                file_path = os.path.join(backup_dir, filename)
                file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))

                if file_mtime < cutoff_date:
                    os.remove(file_path)
                    deleted_count += 1
                    self.stdout.write(f"  🗑️  Deleted: {filename}")

        if deleted_count > 0:
            self.stdout.write(self.style.SUCCESS(f"✅ Cleaned up {deleted_count} old backup(s)"))
        else:
            self.stdout.write("ℹ️  No old backups to clean up")
