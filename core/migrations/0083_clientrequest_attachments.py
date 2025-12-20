from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0082_clientrequest_request_type'),
    ]

    operations = [
        migrations.CreateModel(
            name='ClientRequestAttachment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(upload_to='client_requests/')),
                ('filename', models.CharField(max_length=255)),
                ('content_type', models.CharField(blank=True, max_length=100)),
                ('size_bytes', models.IntegerField(default=0)),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
                ('uploaded_by', models.ForeignKey(blank=True, null=True, on_delete=models.SET_NULL, to='auth.user')),
                ('request', models.ForeignKey(on_delete=models.CASCADE, related_name='attachments', to='core.clientrequest')),
            ],
            options={'ordering': ['-uploaded_at']},
        ),
    ]
