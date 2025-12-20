#!/usr/bin/env python3
"""
Production Media Diagnostic Script
Run this in Railway to debug media file issues
"""
import os

# Try production settings first, fall back to development
try:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "kibray_backend.settings.production")
    import django
    django.setup()
except (ValueError, ImportError) as e:
    print(f"⚠️  Production settings failed: {e}")
    print("📝 Falling back to development settings...")
    os.environ["DJANGO_SETTINGS_MODULE"] = "kibray_backend.settings.development"
    import django
    django.setup()

import os.path

from django.conf import settings

from core.models import FloorPlan

print("=" * 60)
print("🔍 MEDIA CONFIGURATION DIAGNOSTIC")
print("=" * 60)

# Check settings
print("\n📋 SETTINGS:")
print(f"   DEBUG: {settings.DEBUG}")
print(f"   USE_S3: {getattr(settings, 'USE_S3', 'NOT SET')}")
print(f"   MEDIA_URL: {settings.MEDIA_URL}")
print(f"   MEDIA_ROOT: {settings.MEDIA_ROOT}")
print(f"   BASE_DIR: {settings.BASE_DIR}")

# Check if /data exists
print("\n📁 FILESYSTEM:")
print(f"   /data exists: {os.path.exists('/data')}")
if os.path.exists('/data'):
    print(f"   /data is writable: {os.access('/data', os.W_OK)}")
    print(f"   /data/media exists: {os.path.exists('/data/media')}")
    if os.path.exists('/data/media'):
        print(f"   /data/media is writable: {os.access('/data/media', os.W_OK)}")
        # List files in /data/media
        try:
            files = os.listdir('/data/media')
            print(f"   Files in /data/media: {len(files)}")
            if len(files) > 0:
                print(f"   First 5 files: {files[:5]}")
        except Exception as e:
            print(f"   Error listing /data/media: {e}")

# Check MEDIA_ROOT
print(f"\n   MEDIA_ROOT exists: {os.path.exists(settings.MEDIA_ROOT)}")
if os.path.exists(settings.MEDIA_ROOT):
    print(f"   MEDIA_ROOT is writable: {os.access(settings.MEDIA_ROOT, os.W_OK)}")
    # Check floor_plans subdirectory
    floor_plans_dir = os.path.join(settings.MEDIA_ROOT, 'floor_plans')
    print(f"   {floor_plans_dir} exists: {os.path.exists(floor_plans_dir)}")
    if os.path.exists(floor_plans_dir):
        try:
            files = os.listdir(floor_plans_dir)
            print(f"   Files in floor_plans/: {len(files)}")
            if len(files) > 0:
                print(f"   First 5 files: {files[:5]}")
                # Check file sizes
                for f in files[:3]:
                    fpath = os.path.join(floor_plans_dir, f)
                    size = os.path.getsize(fpath)
                    print(f"      {f}: {size} bytes")
        except Exception as e:
            print(f"   Error listing floor_plans/: {e}")

# Check database records
print("\n📊 DATABASE:")
floor_plans = FloorPlan.objects.all()
print(f"   Total floor plans: {floor_plans.count()}")

floor_plans_with_images = FloorPlan.objects.exclude(image='')
print(f"   Floor plans with images: {floor_plans_with_images.count()}")

# Check first few floor plans
print("\n🗺️  FLOOR PLAN SAMPLES:")
for plan in floor_plans[:5]:
    print(f"\n   Plan #{plan.id}: {plan.name}")
    print(f"      Project: {plan.project.name}")
    print(f"      Image field: {plan.image}")
    if plan.image:
        print(f"      Image URL: {plan.image.url}")
        print(f"      Image path: {plan.image.path if hasattr(plan.image, 'path') else 'N/A (using S3?)'}")
        if hasattr(plan.image, 'path'):
            if os.path.exists(plan.image.path):
                size = os.path.getsize(plan.image.path)
                print(f"      File exists: YES ({size} bytes)")
                if size < 1000:
                    print("      ⚠️  WARNING: File is very small, may be corrupted")
            else:
                print("      File exists: NO ❌")
                print(f"      Expected path: {plan.image.path}")
    else:
        print("      ⚠️  No image attached")

print("\n" + "=" * 60)
print("✅ DIAGNOSTIC COMPLETE")
print("=" * 60)

# Recommendations
print("\n💡 RECOMMENDATIONS:")
if not getattr(settings, 'USE_S3', False):
    if not os.path.exists('/data'):
        print("   ❌ /data directory doesn't exist")
        print("   → Create Railway Volume mounted at /data")
    elif not os.path.exists(settings.MEDIA_ROOT):
        print("   ❌ MEDIA_ROOT doesn't exist")
        print("   → Create directory: mkdir -p", settings.MEDIA_ROOT)
    elif not os.access(settings.MEDIA_ROOT, os.W_OK):
        print("   ❌ MEDIA_ROOT is not writable")
        print("   → Fix permissions: chmod 755", settings.MEDIA_ROOT)
    else:
        print("   ✅ Media configuration looks good")
        print("   → Try uploading a new floor plan image")
        print("   → Old images may have been lost during previous deploys")
else:
    print("   ℹ️  Using S3 for media storage")
    print("   → Check AWS credentials are set correctly")

print("\n📝 NEXT STEPS:")
print("   1. If /data doesn't exist, create Railway Volume")
print("   2. Re-upload floor plan images")
print("   3. Check browser console for JavaScript errors")
print("   4. Verify image URL is accessible: ", settings.MEDIA_URL)
