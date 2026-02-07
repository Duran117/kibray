# Generated migration to fix Color Sample folder location and document visibility

from django.db import migrations


def fix_colorsample_files(apps, schema_editor):
    """
    Fix two issues:
    1. Move ColorSample PDFs from 'Signed Change Orders' to 'Signed Color Samples'
    2. Make all signed documents (COs and Color Samples) public for client access
    """
    ProjectFile = apps.get_model('core', 'ProjectFile')
    FileCategory = apps.get_model('core', 'FileCategory')
    
    # 1. Move ColorSample PDFs to correct folder
    # Find files that start with "ColorSample_" but are in cos_signed category
    colorsample_files = ProjectFile.objects.filter(
        name__startswith='ColorSample_',
        category__category_type='cos_signed'
    )
    
    for pf in colorsample_files:
        # Get or create the correct category for this project
        correct_category = FileCategory.objects.filter(
            project=pf.project,
            category_type='colorsamples_signed',
            parent=None
        ).first()
        
        if not correct_category:
            # Create the category if it doesn't exist
            max_order = FileCategory.objects.filter(project=pf.project, parent=None).count()
            correct_category = FileCategory.objects.create(
                project=pf.project,
                name='Signed Color Samples',
                category_type='colorsamples_signed',
                icon='bi-palette',
                color='purple',
                order=max_order + 1,
            )
        
        # Move the file to the correct category
        pf.category = correct_category
        pf.save(update_fields=['category'])
    
    # 2. Make all signed documents public
    # Change Orders
    co_files = ProjectFile.objects.filter(
        name__startswith='ChangeOrder_',
        is_public=False
    )
    co_files.update(is_public=True)
    
    # Also match the pattern: CO_{id}_*
    co_files_alt = ProjectFile.objects.filter(
        name__startswith='CO_',
        is_public=False
    )
    co_files_alt.update(is_public=True)
    
    # Color Samples
    cs_files = ProjectFile.objects.filter(
        name__startswith='ColorSample_',
        is_public=False
    )
    cs_files.update(is_public=True)
    
    # Also files in signed categories should be public
    signed_categories = FileCategory.objects.filter(
        category_type__in=['cos_signed', 'colorsamples_signed']
    )
    
    for category in signed_categories:
        category.files.filter(is_public=False).update(is_public=True)


def reverse_fix(apps, schema_editor):
    """Reverse: move ColorSample files back and make private (not recommended)"""
    # This is a data fix, we won't reverse making docs public
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0171_rename_cos_firmados_folders'),
    ]

    operations = [
        migrations.RunPython(fix_colorsample_files, reverse_fix),
    ]
