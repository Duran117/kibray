# Generated manually for Activity 5
# Module 16: Payroll enhancements
# Modules 23-27: Dashboards, Reports, Automation basics

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
from decimal import Decimal


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('core', '0069_activity4_client_colors_blueprints'),
    ]

    operations = [
        # ============================================
        # MODULE 16: PAYROLL ENHANCEMENTS
        # ============================================
        
        # Q16.5: Overtime calculation support
        migrations.AddField(
            model_name='payrollrecord',
            name='regular_hours',
            field=models.DecimalField(
                max_digits=6,
                decimal_places=2,
                default=Decimal("0"),
                help_text='Regular hours (up to 40/week)'
            ),
        ),
        migrations.AddField(
            model_name='payrollrecord',
            name='overtime_hours',
            field=models.DecimalField(
                max_digits=6,
                decimal_places=2,
                default=Decimal("0"),
                help_text='Overtime hours (over 40/week)'
            ),
        ),
        migrations.AddField(
            model_name='payrollrecord',
            name='overtime_rate',
            field=models.DecimalField(
                max_digits=8,
                decimal_places=2,
                null=True,
                blank=True,
                help_text='Overtime rate (typically 1.5x regular)'
            ),
        ),
        
        # Q16.5: Bonuses and deductions
        migrations.AddField(
            model_name='payrollrecord',
            name='bonus',
            field=models.DecimalField(
                max_digits=10,
                decimal_places=2,
                default=Decimal("0"),
                help_text='Bonus amount'
            ),
        ),
        migrations.AddField(
            model_name='payrollrecord',
            name='deductions',
            field=models.DecimalField(
                max_digits=10,
                decimal_places=2,
                default=Decimal("0"),
                help_text='Total deductions'
            ),
        ),
        migrations.AddField(
            model_name='payrollrecord',
            name='deduction_notes',
            field=models.TextField(
                blank=True,
                help_text='Details of deductions'
            ),
        ),
        
        # Q16.8: Tax calculation (future use)
        migrations.AddField(
            model_name='payrollrecord',
            name='gross_pay',
            field=models.DecimalField(
                max_digits=10,
                decimal_places=2,
                default=Decimal("0"),
                help_text='Gross pay before deductions'
            ),
        ),
        migrations.AddField(
            model_name='payrollrecord',
            name='tax_withheld',
            field=models.DecimalField(
                max_digits=10,
                decimal_places=2,
                default=Decimal("0"),
                help_text='Q16.8: Tax withholding (future use)'
            ),
        ),
        migrations.AddField(
            model_name='payrollrecord',
            name='net_pay',
            field=models.DecimalField(
                max_digits=10,
                decimal_places=2,
                default=Decimal("0"),
                help_text='Net pay after deductions and taxes'
            ),
        ),
        
        # Q16.10: Manual adjustment audit trail
        migrations.AddField(
            model_name='payrollrecord',
            name='manually_adjusted',
            field=models.BooleanField(
                default=False,
                help_text='Q16.10: True if admin made manual adjustments'
            ),
        ),
        migrations.AddField(
            model_name='payrollrecord',
            name='adjusted_by',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='payroll_adjustments',
                to=settings.AUTH_USER_MODEL,
                help_text='Q16.10: Admin who made adjustments'
            ),
        ),
        migrations.AddField(
            model_name='payrollrecord',
            name='adjusted_at',
            field=models.DateTimeField(
                blank=True,
                null=True,
                help_text='Q16.10: When adjustment was made'
            ),
        ),
        migrations.AddField(
            model_name='payrollrecord',
            name='adjustment_reason',
            field=models.TextField(
                blank=True,
                help_text='Q16.10: Why adjustment was made'
            ),
        ),
        
        # Q16.15: Missing days detection
        migrations.AddField(
            model_name='payrollrecord',
            name='missing_days',
            field=models.JSONField(
                default=list,
                blank=True,
                help_text='Q16.15: List of dates with no time entries'
            ),
        ),
        
        # Q16.16: Project breakdown for multi-project tracking
        migrations.AddField(
            model_name='payrollrecord',
            name='project_hours',
            field=models.JSONField(
                default=dict,
                blank=True,
                help_text='Q16.16: Hours breakdown by project {project_id: hours}'
            ),
        ),
        
        # Q16.6: Enhanced status workflow
        migrations.AlterField(
            model_name='payrollperiod',
            name='status',
            field=models.CharField(
                max_length=20,
                choices=[
                    ('draft', 'Draft'),
                    ('under_review', 'Under Review'),
                    ('approved', 'Approved'),
                    ('paid', 'Paid'),
                ],
                default='draft',
                help_text='Q16.6: Payroll period status'
            ),
        ),
        
        # Q16.9: Validation tracking
        migrations.AddField(
            model_name='payrollperiod',
            name='validation_errors',
            field=models.JSONField(
                default=list,
                blank=True,
                help_text='Q16.9: List of validation errors (missing check-ins, etc.)'
            ),
        ),
        migrations.AddField(
            model_name='payrollperiod',
            name='approved_by',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='approved_payroll_periods',
                to=settings.AUTH_USER_MODEL,
                help_text='Admin who approved this period'
            ),
        ),
        migrations.AddField(
            model_name='payrollperiod',
            name='approved_at',
            field=models.DateTimeField(
                blank=True,
                null=True,
                help_text='When period was approved'
            ),
        ),
        
        # Q16.13: Link payroll to expenses
        migrations.AddField(
            model_name='payrollrecord',
            name='expense',
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='payroll_record',
                to='core.expense',
                help_text='Q16.13: Linked expense record for labor cost'
            ),
        ),
        
        # Q16.11: Multiple rate types support
        migrations.AddField(
            model_name='employee',
            name='overtime_multiplier',
            field=models.DecimalField(
                max_digits=3,
                decimal_places=2,
                default=Decimal("1.50"),
                help_text='Q16.11: Overtime rate multiplier (typically 1.5)'
            ),
        ),
        migrations.AddField(
            model_name='employee',
            name='has_custom_overtime',
            field=models.BooleanField(
                default=False,
                help_text='Q16.11: True if employee has custom overtime rate'
            ),
        ),
        
        # ============================================
        # INDEXES FOR PERFORMANCE
        # ============================================
        
        migrations.AddIndex(
            model_name='payrollrecord',
            index=models.Index(fields=['week_start', 'week_end', 'employee'], name='payroll_week_emp_idx'),
        ),
        migrations.AddIndex(
            model_name='payrollrecord',
            index=models.Index(fields=['reviewed', 'manually_adjusted'], name='payroll_review_adjust_idx'),
        ),
        migrations.AddIndex(
            model_name='payrollperiod',
            index=models.Index(fields=['status', 'week_start'], name='payroll_period_status_week_idx'),
        ),
    ]
