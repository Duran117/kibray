# Generated migration to rename folder names to English

from django.db import migrations


def rename_folders_to_english(apps, schema_editor):
    """Rename folder names from Spanish to English."""
    FileCategory = apps.get_model('core', 'FileCategory')
    
    # Rename 'COs Firmados' to 'Signed Change Orders'
    FileCategory.objects.filter(name='COs Firmados').update(name='Signed Change Orders')


def reverse_rename(apps, schema_editor):
    """Reverse: rename back to Spanish."""
    FileCategory = apps.get_model('core', 'FileCategory')
    FileCategory.objects.filter(name='Signed Change Orders').update(name='COs Firmados')


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0170_add_colorsamples_signed_category'),
    ]

    operations = [
        migrations.RunPython(rename_folders_to_english, reverse_rename),
    ]
