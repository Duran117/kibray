from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('core', '0083_clientrequest_attachments'),
    ]

    operations = [
        migrations.AddField(
            model_name='chatmessage',
            name='attachment',
            field=models.FileField(upload_to='project_chat/', null=True, blank=True),
        ),
    ]
