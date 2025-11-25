from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('core', '0078_tasktemplate_enhancements'),
    ]

    operations = [
        migrations.CreateModel(
            name='TwoFactorProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('secret', models.CharField(blank=True, help_text='Base32 secret (no padding)', max_length=64)),
                ('enabled', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('last_verified_at', models.DateTimeField(blank=True, null=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='twofa', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Two-Factor Profile',
                'verbose_name_plural': 'Two-Factor Profiles',
            },
        ),
        migrations.AddIndex(
            model_name='twofactorprofile',
            index=models.Index(fields=['enabled'], name='core_twofac_enabled_idx'),
        ),
    ]
