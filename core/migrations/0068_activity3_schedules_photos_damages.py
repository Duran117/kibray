# Generated manually for Activity 3
# Modules: Schedules (15), Photos (18), Damage Reports (21)

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('core', '0067_activity2_inventory_enhancements'),
    ]

    operations = [
        # ============================================
        # MODULE 18: SITE PHOTOS ENHANCEMENTS
        # ============================================

        # Q18.2: GPS location (store lat/long from project)
        migrations.AddField(
            model_name='sitephoto',
            name='location_lat',
            field=models.DecimalField(
                blank=True,
                decimal_places=6,
                max_digits=9,
                null=True,
                help_text='Latitude from project location'
            ),
        ),
        migrations.AddField(
            model_name='sitephoto',
            name='location_lng',
            field=models.DecimalField(
                blank=True,
                decimal_places=6,
                max_digits=9,
                null=True,
                help_text='Longitude from project location'
            ),
        ),

        # Q18.4: Privacy control
        migrations.AddField(
            model_name='sitephoto',
            name='visibility',
            field=models.CharField(
                max_length=20,
                choices=[
                    ('public', 'Public - Client visible'),
                    ('internal', 'Internal - Staff only'),
                ],
                default='public',
                help_text='Photo visibility control'
            ),
        ),

        # Q18.6: Versioning
        migrations.AddField(
            model_name='sitephoto',
            name='version',
            field=models.IntegerField(
                default=1,
                help_text='Version number if photo is replaced'
            ),
        ),
        migrations.AddField(
            model_name='sitephoto',
            name='is_current_version',
            field=models.BooleanField(
                default=True,
                help_text='True if this is the current version'
            ),
        ),
        migrations.AddField(
            model_name='sitephoto',
            name='replaced_by',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='replaces',
                to='core.sitephoto',
                help_text='Newer version that replaces this photo'
            ),
        ),

        # Q18.10: Enhanced categorization (already has photo_type, add caption)
        migrations.AddField(
            model_name='sitephoto',
            name='caption',
            field=models.CharField(
                max_length=255,
                blank=True,
                help_text='Photo caption/title for search'
            ),
        ),

        # Q18.12: Thumbnail (will be generated on save)
        migrations.AddField(
            model_name='sitephoto',
            name='thumbnail',
            field=models.ImageField(
                blank=True,
                null=True,
                upload_to='site_photos/thumbnails/',
                help_text='Auto-generated thumbnail'
            ),
        ),

        # ============================================
        # MODULE 21: DAMAGE REPORTS ENHANCEMENTS
        # ============================================

        # Q21.2: Assignee for damage resolution
        migrations.AddField(
            model_name='damagereport',
            name='assigned_to',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='assigned_damages',
                to=settings.AUTH_USER_MODEL,
                help_text='User responsible for resolving this damage'
            ),
        ),

        # Q21.4: Auto-created task reference
        migrations.AddField(
            model_name='damagereport',
            name='auto_task',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='damage_reports',
                to='core.task',
                help_text='Automatically created repair task'
            ),
        ),

        # Q21.9: Time tracking fields
        migrations.AddField(
            model_name='damagereport',
            name='in_progress_at',
            field=models.DateTimeField(
                blank=True,
                null=True,
                help_text='When work started on this damage'
            ),
        ),

        # Q21.7: Allow severity changes after creation (already mutable, add audit)
        migrations.AddField(
            model_name='damagereport',
            name='severity_changed_at',
            field=models.DateTimeField(
                blank=True,
                null=True,
                help_text='Last time severity was changed'
            ),
        ),
        migrations.AddField(
            model_name='damagereport',
            name='severity_changed_by',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='damage_severity_changes',
                to=settings.AUTH_USER_MODEL,
                help_text='Who changed the severity'
            ),
        ),

        # Q21.13: Grouping by location/cause
        migrations.AddField(
            model_name='damagereport',
            name='location_detail',
            field=models.CharField(
                max_length=200,
                blank=True,
                help_text='Specific location (e.g., "Kitchen - North Wall")'
            ),
        ),
        migrations.AddField(
            model_name='damagereport',
            name='root_cause',
            field=models.CharField(
                max_length=200,
                blank=True,
                help_text='Root cause for pattern analysis'
            ),
        ),

        # ============================================
        # INDEXES FOR PERFORMANCE
        # ============================================

        migrations.AddIndex(
            model_name='sitephoto',
            index=models.Index(fields=['project', 'photo_type', 'visibility'], name='sitephoto_proj_type_vis_idx'),
        ),
        migrations.AddIndex(
            model_name='sitephoto',
            index=models.Index(fields=['is_current_version', 'created_at'], name='sitephoto_ver_date_idx'),
        ),
        migrations.AddIndex(
            model_name='damagereport',
            index=models.Index(fields=['project', 'status', 'severity'], name='damage_proj_status_sev_idx'),
        ),
        migrations.AddIndex(
            model_name='damagereport',
            index=models.Index(fields=['assigned_to', 'status'], name='damage_assignee_status_idx'),
        ),
    ]
