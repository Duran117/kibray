# Generated manually for employee savings feature

from django.db import migrations, models
from django.conf import settings
from decimal import Decimal
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('core', '0157_colorsample_client_signature_fields'),
    ]

    operations = [
        # Add savings fields to PayrollPayment
        migrations.AddField(
            model_name='payrollpayment',
            name='amount_taken',
            field=models.DecimalField(
                decimal_places=2,
                default=Decimal('0'),
                help_text='Amount employee actually took (cash/check)',
                max_digits=10,
            ),
        ),
        migrations.AddField(
            model_name='payrollpayment',
            name='amount_saved',
            field=models.DecimalField(
                decimal_places=2,
                default=Decimal('0'),
                help_text='Amount employee saved/retained with company',
                max_digits=10,
            ),
        ),
        # Create EmployeeSavings model
        migrations.CreateModel(
            name='EmployeeSavings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.DecimalField(
                    decimal_places=2,
                    help_text='Amount saved or withdrawn',
                    max_digits=10,
                )),
                ('transaction_type', models.CharField(
                    choices=[
                        ('deposit', 'Depósito (Ahorro)'),
                        ('withdrawal', 'Retiro'),
                        ('adjustment', 'Ajuste Manual'),
                    ],
                    default='deposit',
                    max_length=20,
                )),
                ('date', models.DateField()),
                ('notes', models.TextField(blank=True)),
                ('recorded_at', models.DateTimeField(auto_now_add=True)),
                ('employee', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='savings_records',
                    to='core.employee',
                )),
                ('payroll_payment', models.ForeignKey(
                    blank=True,
                    help_text='Linked payroll payment (for automatic deposits)',
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='savings_record',
                    to='core.payrollpayment',
                )),
                ('recorded_by', models.ForeignKey(
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='employee_savings_recorded',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'verbose_name': 'Employee Savings',
                'verbose_name_plural': 'Employee Savings',
                'ordering': ['-date', '-recorded_at'],
            },
        ),
    ]
