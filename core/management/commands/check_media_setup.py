"""
Django management command to check and fix media file configuration
Usage: python manage.py check_media_setup
"""
from django.core.management.base import BaseCommand
from django.conf import settings
import os

class Command(BaseCommand):
    help = 'Check and fix media file configuration for Railway deployment'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('='*60))
        self.stdout.write(self.style.SUCCESS('🔧 MEDIA SETUP CHECK AND FIX'))
        self.stdout.write(self.style.SUCCESS('='*60))
        
        # Check MEDIA_ROOT
        self.stdout.write(f'\n📁 MEDIA_ROOT: {settings.MEDIA_ROOT}')
        
        if not os.path.exists(settings.MEDIA_ROOT):
            self.stdout.write(self.style.WARNING(f'   ⚠️  Directory does not exist, creating...'))
            try:
                os.makedirs(settings.MEDIA_ROOT, exist_ok=True)
                self.stdout.write(self.style.SUCCESS(f'   ✅ Created: {settings.MEDIA_ROOT}'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'   ❌ Failed to create: {e}'))
                return
        else:
            self.stdout.write(self.style.SUCCESS(f'   ✅ Exists'))
        
        # Check if writable
        if os.access(settings.MEDIA_ROOT, os.W_OK):
            self.stdout.write(self.style.SUCCESS(f'   ✅ Writable'))
        else:
            self.stdout.write(self.style.ERROR(f'   ❌ Not writable!'))
            return
        
        # Create subdirectories
        subdirs = ['floor_plans', 'color_samples', 'daily_plans', 'photos', 'signatures']
        self.stdout.write(f'\n📂 Creating subdirectories...')
        for subdir in subdirs:
            path = os.path.join(settings.MEDIA_ROOT, subdir)
            try:
                os.makedirs(path, exist_ok=True)
                self.stdout.write(self.style.SUCCESS(f'   ✅ {subdir}/'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'   ❌ {subdir}/: {e}'))
        
        # Check existing files
        self.stdout.write(f'\n📊 Checking existing files...')
        for subdir in subdirs:
            path = os.path.join(settings.MEDIA_ROOT, subdir)
            if os.path.exists(path):
                files = os.listdir(path)
                self.stdout.write(f'   {subdir}/: {len(files)} files')
                
                # Check for corrupted files (very small)
                if files:
                    corrupted = 0
                    for f in files[:10]:  # Check first 10
                        fpath = os.path.join(path, f)
                        if os.path.isfile(fpath):
                            size = os.path.getsize(fpath)
                            if size < 1000:
                                corrupted += 1
                    if corrupted > 0:
                        self.stdout.write(self.style.WARNING(f'      ⚠️  {corrupted} files are very small (< 1KB), may be corrupted'))
        
        # Summary
        self.stdout.write(self.style.SUCCESS('\n' + '='*60))
        self.stdout.write(self.style.SUCCESS('✅ MEDIA SETUP COMPLETE'))
        self.stdout.write(self.style.SUCCESS('='*60))
        self.stdout.write(f'\n💡 Configuration:')
        self.stdout.write(f'   MEDIA_URL: {settings.MEDIA_URL}')
        self.stdout.write(f'   MEDIA_ROOT: {settings.MEDIA_ROOT}')
        self.stdout.write(f'   USE_S3: {getattr(settings, "USE_S3", "Not set")}')
        self.stdout.write(f'\n📝 Next steps:')
        self.stdout.write(f'   1. Upload new floor plan images')
        self.stdout.write(f'   2. Old images (< 1KB) are corrupted and need to be replaced')
        self.stdout.write(f'   3. New uploads will be saved to: {settings.MEDIA_ROOT}')
