# Generated manually for Activity 4
# Modules: Client Portal (17), Color Samples (19), Blueprints (20)

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('core', '0068_activity3_schedules_photos_damages'),
    ]

    operations = [
        # ============================================
        # MODULE 19: COLOR SAMPLES ENHANCEMENTS
        # ============================================
        
        # Q19.3: Grouping by room/location
        migrations.AddField(
            model_name='colorsample',
            name='room_location',
            field=models.CharField(
                max_length=200,
                blank=True,
                help_text='Room or location (e.g., "Kitchen", "Master Bedroom")'
            ),
        ),
        migrations.AddField(
            model_name='colorsample',
            name='room_group',
            field=models.CharField(
                max_length=100,
                blank=True,
                help_text='Group multiple samples by room'
            ),
        ),
        
        # Q19.4: Sequential numbering with client prefix
        migrations.AddField(
            model_name='colorsample',
            name='sample_number',
            field=models.CharField(
                max_length=50,
                blank=True,
                null=True,
                help_text='Unique sample number (e.g., KPISM10001)'
            ),
        ),
        
        # Q19.5: Track who rejected and when
        migrations.AddField(
            model_name='colorsample',
            name='rejected_by',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='color_samples_rejected',
                to=settings.AUTH_USER_MODEL,
                help_text='User who rejected the sample'
            ),
        ),
        migrations.AddField(
            model_name='colorsample',
            name='rejected_at',
            field=models.DateTimeField(
                blank=True,
                null=True,
                help_text='When the sample was rejected'
            ),
        ),
        migrations.AddField(
            model_name='colorsample',
            name='rejection_reason',
            field=models.TextField(
                blank=True,
                help_text='Q19.12: Required reason for rejection'
            ),
        ),
        
        # Q19.6: Audit trail for status changes
        migrations.AddField(
            model_name='colorsample',
            name='status_changed_by',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='color_sample_status_changes',
                to=settings.AUTH_USER_MODEL,
                help_text='Last user who changed status'
            ),
        ),
        migrations.AddField(
            model_name='colorsample',
            name='status_changed_at',
            field=models.DateTimeField(
                blank=True,
                null=True,
                help_text='When status was last changed'
            ),
        ),
        
        # Q19.13: Digital signature for legal purposes
        migrations.AddField(
            model_name='colorsample',
            name='approval_signature',
            field=models.TextField(
                blank=True,
                help_text='Cryptographic signature hash for approval'
            ),
        ),
        migrations.AddField(
            model_name='colorsample',
            name='approval_ip',
            field=models.GenericIPAddressField(
                blank=True,
                null=True,
                help_text='IP address of approver for legal purposes'
            ),
        ),
        
        # Q19.7: Link to tasks
        migrations.AddField(
            model_name='colorsample',
            name='linked_tasks',
            field=models.ManyToManyField(
                blank=True,
                related_name='color_samples',
                to='core.task',
                help_text='Tasks that use this color'
            ),
        ),
        
        # Q19.8: Multiple photos support (will use separate model)
        # Already supported via sample_image + reference_photo
        # Can add ColorSamplePhoto model if needed
        
        # ============================================
        # MODULE 20: BLUEPRINTS/FLOOR PLANS ENHANCEMENTS
        # ============================================
        
        # Q20.1: Versioning for floor plans
        migrations.AddField(
            model_name='floorplan',
            name='version',
            field=models.IntegerField(
                default=1,
                help_text='Version number when plan is replaced'
            ),
        ),
        migrations.AddField(
            model_name='floorplan',
            name='is_current',
            field=models.BooleanField(
                default=True,
                help_text='True if this is the current active version'
            ),
        ),
        migrations.AddField(
            model_name='floorplan',
            name='replaced_by',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='replaces',
                to='core.floorplan',
                help_text='Newer version that replaces this plan'
            ),
        ),
        
        # Q20.2: Pin status for migration tracking
        migrations.AddField(
            model_name='planpin',
            name='status',
            field=models.CharField(
                max_length=20,
                choices=[
                    ('active', 'Active'),
                    ('pending_migration', 'Pending Migration'),
                    ('migrated', 'Migrated'),
                    ('archived', 'Archived'),
                ],
                default='active',
                help_text='Pin status for version migration'
            ),
        ),
        migrations.AddField(
            model_name='planpin',
            name='migrated_to',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='migrated_from',
                to='core.planpin',
                help_text='New pin in updated plan version'
            ),
        ),
        
        # Q20.9: PDF export tracking
        migrations.AddField(
            model_name='floorplan',
            name='last_pdf_export',
            field=models.DateTimeField(
                blank=True,
                null=True,
                help_text='Last time plan with pins was exported to PDF'
            ),
        ),
        
        # Q20.10: Client commenting on pins
        migrations.AddField(
            model_name='planpin',
            name='client_comments',
            field=models.JSONField(
                default=list,
                blank=True,
                help_text='Array of client comments with timestamps'
            ),
        ),
        
        # ============================================
        # MODULE 17: CLIENT PORTAL (Basic structure)
        # ============================================
        
        # Q17.2: Client request system (will use existing models)
        # Client can create MaterialRequest, ChangeOrder, Tasks with is_client_request=True
        migrations.AddField(
            model_name='task',
            name='is_client_request',
            field=models.BooleanField(
                default=False,
                help_text='Q17.7: Task created by client as request'
            ),
        ),
        migrations.AddField(
            model_name='task',
            name='client_cancelled',
            field=models.BooleanField(
                default=False,
                help_text='Q17.9: Client cancelled their own request'
            ),
        ),
        migrations.AddField(
            model_name='task',
            name='cancellation_reason',
            field=models.TextField(
                blank=True,
                help_text='Q17.9: Why client cancelled request'
            ),
        ),
        
        # ============================================
        # INDEXES FOR PERFORMANCE
        # ============================================
        
        migrations.AddIndex(
            model_name='colorsample',
            index=models.Index(fields=['project', 'room_group', 'status'], name='colorsample_proj_room_status_idx'),
        ),
        migrations.AddIndex(
            model_name='colorsample',
            index=models.Index(fields=['sample_number'], name='colorsample_number_idx'),
        ),
        migrations.AddIndex(
            model_name='floorplan',
            index=models.Index(fields=['project', 'is_current'], name='floorplan_proj_current_idx'),
        ),
        migrations.AddIndex(
            model_name='planpin',
            index=models.Index(fields=['plan', 'status', 'pin_type'], name='planpin_plan_status_type_idx'),
        ),
    ]
