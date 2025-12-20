from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0119_add_employee_key"),
    ]

    operations = [
        migrations.RunSQL(
            sql="ALTER TABLE core_employee ADD COLUMN employee_key varchar(20);",
            reverse_sql="-- no reverse",
        ),
    ]
