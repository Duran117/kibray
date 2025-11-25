"""
Celery tasks for Kibray construction management system.
Handles automated background jobs and scheduled maintenance tasks.

Created during comprehensive automation implementation.
"""

from celery import shared_task
from django.utils import timezone
from django.db.models import Q, Sum
from django.core.mail import send_mail
from django.conf import settings
from datetime import timedelta, date
import logging

logger = logging.getLogger(__name__)


@shared_task(name='core.tasks.check_overdue_invoices')
def check_overdue_invoices():
    """
    Check for overdue invoices and update their status.
    Runs daily at 6 AM.
    
    Updates invoices with status SENT/VIEWED/APPROVED to OVERDUE
    if they're past their due date.
    """
    from core.models import Invoice
    
    today = timezone.now().date()
    
    # Find invoices that are past due date and not yet marked overdue
    overdue_invoices = Invoice.objects.filter(
        due_date__lt=today,
        status__in=['SENT', 'VIEWED', 'APPROVED', 'PARTIAL']
    )
    
    count = 0
    for invoice in overdue_invoices:
        # Calculate days overdue
        days_overdue = (today - invoice.due_date).days
        
        # Update status
        invoice.status = 'OVERDUE'
        invoice.save(update_fields=['status'])
        
        # Send notification to admin
        try:
            from core.notifications import notify_invoice_overdue
            notify_invoice_overdue(invoice, days_overdue)
        except Exception as e:
            logger.error(f"Failed to send overdue notification for invoice {invoice.id}: {e}")
        
        count += 1
    
    logger.info(f"Marked {count} invoices as OVERDUE")
    return {'updated': count, 'date': str(today)}


@shared_task(name='core.tasks.alert_incomplete_daily_plans')
def alert_incomplete_daily_plans():
    """
    Alert about daily plans not completed before deadline (5 PM day before).
    Runs at 5:15 PM daily.
    
    Finds DRAFT plans past their completion deadline and sends alerts.
    """
    from core.models import DailyPlan, Notification
    from django.contrib.auth import get_user_model
    
    User = get_user_model()
    now = timezone.now()
    
    # Find overdue draft plans
    overdue_plans = DailyPlan.objects.filter(
        status='DRAFT',
        completion_deadline__lt=now
    ).select_related('project', 'created_by')
    
    count = 0
    for plan in overdue_plans:
        # Notify creator and admins
        recipients = [plan.created_by] if plan.created_by else []
        admins = User.objects.filter(Q(is_staff=True) | Q(is_superuser=True))
        recipients.extend(admins)
        
        for user in set(recipients):
            Notification.objects.create(
                user=user,
                notification_type='alert',
                title=f'Daily Plan Overdue: {plan.project.name}',
                message=f'Daily plan for {plan.plan_date} was due at 5 PM yesterday and is still in DRAFT status.',
                related_url=f'/daily-plan/{plan.id}/edit/',
                priority='high'
            )
        
        count += 1
    
    logger.info(f"Sent alerts for {count} overdue daily plans")
    return {'alerted': count, 'time': str(now)}


@shared_task(name='core.tasks.generate_weekly_payroll')
def generate_weekly_payroll():
    """
    Generate PayrollPeriod records for the previous week.
    Runs on Monday at 7 AM.
    
    Creates payroll period for Mon-Sun of previous week,
    aggregates time entries, and creates PayrollRecord for each employee.
    """
    from core.models import PayrollPeriod, PayrollRecord, Employee, TimeEntry
    from django.contrib.auth import get_user_model
    
    User = get_user_model()
    today = date.today()
    
    # Calculate previous week (Mon-Sun)
    days_since_monday = today.weekday()
    last_monday = today - timedelta(days=days_since_monday + 7)
    last_sunday = last_monday + timedelta(days=6)
    
    # Check if period already exists
    existing = PayrollPeriod.objects.filter(
        week_start=last_monday,
        week_end=last_sunday
    ).first()
    
    if existing:
        logger.info(f"Payroll period for {last_monday} - {last_sunday} already exists")
        return {'status': 'exists', 'period_id': existing.id}
    
    # Get first admin user as creator
    creator = User.objects.filter(Q(is_superuser=True) | Q(is_staff=True)).first()
    
    # Create payroll period
    period = PayrollPeriod.objects.create(
        week_start=last_monday,
        week_end=last_sunday,
        status='pending',
        created_by=creator
    )
    
    # Create records for each active employee
    employees = Employee.objects.filter(is_active=True)
    records_created = 0
    
    for employee in employees:
        # Aggregate time entries
        time_entries = TimeEntry.objects.filter(
            employee=employee,
            date__range=(last_monday, last_sunday)
        )
        
        total_hours = sum(
            entry.hours_worked or 0 
            for entry in time_entries
        )
        
        # Create payroll record
        PayrollRecord.objects.create(
            period=period,
            employee=employee,
            week_start=last_monday,
            week_end=last_sunday,
            hourly_rate=employee.hourly_rate,
            total_hours=total_hours,
            total_pay=total_hours * employee.hourly_rate,
            reviewed=False
        )
        
        records_created += 1
    
    logger.info(f"Created payroll period {period.id} with {records_created} records")
    return {
        'period_id': period.id,
        'week': f"{last_monday} - {last_sunday}",
        'records': records_created
    }


@shared_task(name='core.tasks.check_inventory_shortages')
def check_inventory_shortages():
    """
    Check inventory levels and alert on shortages.
    Runs daily at 8 AM.
    
    Identifies items below threshold and sends notifications.
    """
    from core.models import ProjectInventory, Notification
    from django.contrib.auth import get_user_model
    
    User = get_user_model()
    
    # Get all project inventories with shortages
    shortages = []
    stocks = ProjectInventory.objects.select_related('item', 'location', 'location__project')
    
    for stock in stocks:
        if stock.is_below:  # Property that checks if below threshold
            shortages.append({
                'item': stock.item.name,
                'location': stock.location.name,
                'project': stock.location.project.name if stock.location.project else 'Storage',
                'current': float(stock.quantity),
                'threshold': float(stock.threshold or stock.item.default_threshold or 0)
            })
    
    if not shortages:
        logger.info("No inventory shortages detected")
        return {'shortages': 0}
    
    # Notify all PMs and admins
    recipients = User.objects.filter(
        Q(is_staff=True) | 
        Q(is_superuser=True) |
        Q(profile__role__in=['admin', 'project_manager'])
    )
    
    message = f"Low inventory detected for {len(shortages)} items:\n\n"
    for s in shortages[:10]:  # Limit to first 10
        message += f"• {s['item']} at {s['location']} ({s['project']}): {s['current']} (min: {s['threshold']})\n"
    
    if len(shortages) > 10:
        message += f"\n...and {len(shortages) - 10} more items"
    
    for user in recipients:
        Notification.objects.create(
            user=user,
            notification_type='alert',
            title='Inventory Shortage Alert',
            message=message,
            related_url='/inventory/',
            priority='medium'
        )
    
    logger.info(f"Sent inventory shortage alerts for {len(shortages)} items")
    return {'shortages': len(shortages), 'notified': recipients.count()}


@shared_task(name='core.tasks.send_pending_notifications')
def send_pending_notifications():
    """
    Send pending email notifications.
    Runs every hour.
    
    Finds unsent notifications and sends them via email.
    """
    from core.models import Notification
    
    # Get notifications marked for email but not yet sent
    pending = Notification.objects.filter(
        sent_via_email=False,
        created_at__gte=timezone.now() - timedelta(hours=24)  # Last 24h only
    ).select_related('user')[:100]  # Batch of 100
    
    sent_count = 0
    error_count = 0
    
    for notification in pending:
        try:
            send_mail(
                subject=notification.title,
                message=notification.message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[notification.user.email],
                fail_silently=False,
            )
            
            notification.sent_via_email = True
            notification.save(update_fields=['sent_via_email'])
            sent_count += 1
            
        except Exception as e:
            logger.error(f"Failed to send email notification {notification.id}: {e}")
            error_count += 1
    
    logger.info(f"Sent {sent_count} email notifications, {error_count} errors")
    return {'sent': sent_count, 'errors': error_count}


@shared_task(name='core.tasks.update_invoice_statuses')
def update_invoice_statuses():
    """
    Update invoice statuses based on due dates.
    Runs daily at 1 AM.
    """
    from core.models import Invoice
    
    today = timezone.now().date()
    updated = 0
    
    # Mark as OVERDUE if past due and still active
    invoices = Invoice.objects.filter(
        due_date__lt=today,
        status__in=['SENT', 'VIEWED', 'APPROVED', 'PARTIAL']
    )
    
    for invoice in invoices:
        invoice.status = 'OVERDUE'
        invoice.save(update_fields=['status'])
        updated += 1
    
    logger.info(f"Updated {updated} invoice statuses to OVERDUE")
    return {'updated': updated}


@shared_task(name='core.tasks.cleanup_old_notifications')
def cleanup_old_notifications():
    """
    Delete old read notifications to keep database clean.
    Runs weekly on Sunday at 2 AM.
    
    Deletes notifications older than 30 days that have been read.
    """
    from core.models import Notification
    
    cutoff = timezone.now() - timedelta(days=30)
    
    deleted_count, _ = Notification.objects.filter(
        is_read=True,
        created_at__lt=cutoff
    ).delete()
    
    logger.info(f"Deleted {deleted_count} old notifications")
    return {'deleted': deleted_count, 'cutoff': str(cutoff)}


@shared_task(name='core.tasks.generate_daily_plan_reminders')
def generate_daily_plan_reminders():
    """
    Send reminders for tomorrow's daily plans.
    Runs at 4 PM daily.
    """
    from core.models import DailyPlan, Notification
    
    tomorrow = timezone.now().date() + timedelta(days=1)
    
    # Get plans for tomorrow
    plans = DailyPlan.objects.filter(
        plan_date=tomorrow,
        status__in=['SUBMITTED', 'APPROVED']
    ).select_related('project').prefetch_related('assigned_employees')
    
    sent = 0
    for plan in plans:
        # Notify assigned employees
        for employee in plan.assigned_employees.all():
            if hasattr(employee, 'user') and employee.user:
                Notification.objects.create(
                    user=employee.user,
                    notification_type='reminder',
                    title=f'Tomorrow: {plan.project.name}',
                    message=f'You have {plan.activities.count()} activities scheduled for tomorrow at {plan.project.address}',
                    related_url=f'/employee/morning/',
                    priority='normal'
                )
                sent += 1
    
    logger.info(f"Sent {sent} daily plan reminders for {tomorrow}")
    return {'sent': sent, 'date': str(tomorrow)}
