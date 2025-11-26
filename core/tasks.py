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
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


@shared_task(name='core.tasks.check_inventory_shortages')
def check_inventory_shortages():
    """
    Check for low inventory levels and send alerts.
    Runs daily at 8 AM.
    
    Scans all active items with thresholds, aggregates quantities
    across all locations, and creates notifications for items below threshold.
    """
    from core.models import InventoryItem, ProjectInventory, Notification
    from django.contrib.auth import get_user_model
    from django.db.models import Sum, Q
    
    User = get_user_model()
    today = timezone.now().date()
    
    # Get active items with thresholds
    items = InventoryItem.objects.filter(
        active=True,
        no_threshold=False
    ).filter(
        Q(low_stock_threshold__isnull=False) | Q(default_threshold__isnull=False)
    )
    
    low_stock_items = []
    
    for item in items:
        threshold = item.get_effective_threshold()
        if not threshold:
            continue
        
        # Get total quantity across all locations
        total_qty = ProjectInventory.objects.filter(item=item).aggregate(
            total=Sum('quantity')
        )['total'] or Decimal("0")
        
        if total_qty < threshold:
            shortage = threshold - total_qty
            low_stock_items.append({
                'item': item,
                'current_qty': total_qty,
                'threshold': threshold,
                'shortage': shortage
            })
    
    # Send notifications to admins and managers
    if low_stock_items:
        recipients = User.objects.filter(Q(is_staff=True) | Q(is_superuser=True))
        
        # Create summary notification
        item_list = ', '.join([
            f"{item_data['item'].name} ({item_data['current_qty']}/{item_data['threshold']})"
            for item_data in low_stock_items[:5]  # First 5 items
        ])
        
        if len(low_stock_items) > 5:
            item_list += f" ... and {len(low_stock_items) - 5} more"
        
        for user in recipients:
            Notification.objects.create(
                user=user,
                notification_type='task_alert',
                title=f'Low Inventory Alert: {len(low_stock_items)} items',
                message=f'Items below threshold: {item_list}',
                link_url='/inventory/',
                related_object_type='inventory',
                related_object_id=None
            )
    
    logger.info(f"Inventory check: {len(low_stock_items)} items below threshold")
    
    return {
        'date': str(today),
        'low_stock_count': len(low_stock_items),
        'items_checked': items.count()
    }


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


@shared_task(name='core.tasks.update_daily_weather_snapshots')
def update_daily_weather_snapshots():
    """
    Fetch and persist weather data for all active projects.
    Runs daily at 5 AM (before daily plan updates).
    
    Creates WeatherSnapshot records for today's date for each project.
    Uses project address (if available) or name as location identifier.
    """
    from core.models import Project, WeatherSnapshot
    from django.db.models import Q
    
    today = timezone.now().date()
    
    # Filter active projects (no end_date or end_date in future)
    active_projects = Project.objects.filter(
        Q(end_date__isnull=True) | Q(end_date__gte=today)
    )
    
    snapshots_created = 0
    snapshots_updated = 0
    
    for project in active_projects:
        # Use address or project name as location key
        location_key = project.address if project.address else project.name
        
        # Fetch weather data (placeholder: replace with real API in production)
        # For now, simulate basic data
        import random
        conditions = ['Clear', 'Partly Cloudy', 'Cloudy', 'Light Rain', 'Overcast']
        
        weather_data = {
            'temperature_max': round(random.uniform(15, 32), 1),
            'temperature_min': round(random.uniform(8, 20), 1),
            'conditions_text': random.choice(conditions),
            'precipitation_mm': round(random.uniform(0, 5), 1) if random.random() < 0.3 else 0,
            'wind_kph': round(random.uniform(5, 25), 1),
            'humidity_percent': random.randint(40, 85),
        }
        
        # Check if snapshot already exists for today
        snapshot, created = WeatherSnapshot.objects.update_or_create(
            project=project,
            date=today,
            source='open-meteo',
            defaults={
                'temperature_max': weather_data['temperature_max'],
                'temperature_min': weather_data['temperature_min'],
                'conditions_text': weather_data['conditions_text'],
                'precipitation_mm': weather_data['precipitation_mm'],
                'wind_kph': weather_data['wind_kph'],
                'humidity_percent': weather_data['humidity_percent'],
                'raw_json': weather_data,
                'provider_url': 'https://open-meteo.com/en/docs',
            }
        )
        
        if created:
            snapshots_created += 1
        else:
            snapshots_updated += 1
    
    logger.info(f"Weather snapshots: {snapshots_created} created, {snapshots_updated} updated")
    return {
        'date': str(today),
        'created': snapshots_created,
        'updated': snapshots_updated,
        'total_projects': active_projects.count()
    }


@shared_task(name='core.tasks.alert_high_priority_touchups')
def alert_high_priority_touchups():
    """
    Alert project managers about high-priority open touch-ups.
    Runs daily at 9 AM.
    
    Scans all projects for touch-up tasks with priority=high/urgent
    that are still pending or in progress. Sends notifications if
    count exceeds threshold (default: 3).
    """
    from core.models import Project, Task, Notification
    from django.contrib.auth import get_user_model
    from django.db.models import Q, Count
    
    User = get_user_model()
    THRESHOLD = 3  # Alert if 3+ high-priority touchups
    
    today = timezone.now().date()
    
    # Get active projects
    active_projects = Project.objects.filter(
        Q(end_date__isnull=True) | Q(end_date__gte=today)
    )
    
    alerts_sent = 0
    
    for project in active_projects:
        # Count high-priority open touch-ups
        high_priority_touchups = project.tasks.filter(
            is_touchup=True,
            priority__in=['high', 'urgent'],
            status__in=['Pendiente', 'En Progreso']
        )
        
        touchup_count = high_priority_touchups.count()
        
        if touchup_count >= THRESHOLD:
            # Get project managers and admins
            recipients = []
            
            # Find users with PM role who have access to this project
            try:
                from core.models import ClientProjectAccess
                pm_accesses = ClientProjectAccess.objects.filter(
                    project=project,
                    role='external_pm'
                ).select_related('user')
                recipients.extend([access.user for access in pm_accesses])
            except Exception:
                pass
            
            # Add admin users
            admins = User.objects.filter(Q(is_staff=True) | Q(is_superuser=True))
            recipients.extend(admins)
            
            # Remove duplicates
            recipients = list(set(recipients))
            
            # Create notifications
            for user in recipients:
                Notification.objects.create(
                    user=user,
                    notification_type='task_alert',
                    title=f'High-Priority Touch-ups Alert: {project.name}',
                    message=f'{touchup_count} high-priority touch-up tasks require attention.',
                    link_url=f'/projects/{project.id}/touchups/',
                    related_object_type='project',
                    related_object_id=project.id
                )
            
            alerts_sent += len(recipients)
            logger.info(f"Sent {len(recipients)} alerts for {touchup_count} touchups in project {project.id}")
    
    return {
        'date': str(today),
        'alerts_sent': alerts_sent,
        'threshold': THRESHOLD
    }


@shared_task(name='core.tasks.update_daily_weather_snapshots_legacy')
def update_daily_weather_snapshots_legacy():
    """Daily task to snapshot weather for active projects (Module 30 skeleton)."""
    from core.models import Project, Notification
    from core.services.weather_service import get_weather_service
    svc = get_weather_service()
    now = timezone.now()
    projects = Project.objects.filter(is_active=True) if hasattr(Project, 'is_active') else Project.objects.all()
    count = 0
    for project in projects:
        # Placeholder: using project.name as location key
        data = svc.get_weather(project.name)
        # For now, just notify admins with snapshot (will later persist to model)
        Notification.objects.create(
            user=None,
            notification_type='weather_snapshot',
            title=f'Weather Snapshot {project.name}',
            message=f"{data.condition} {data.temperature_c}°C",
            related_object_type='project',
            related_object_id=project.id
        )
        count += 1
    logger.info(f"Weather snapshots generated for {count} projects at {now}")
    return {'snapshots': count, 'timestamp': str(now)}


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


@shared_task(name='core.tasks.update_daily_plans_weather')
def update_daily_plans_weather():
    """
    Update weather data for upcoming daily plans.
    Runs daily at 5 AM.
    
    Fetches weather for:
    - Today's plans without recent weather data
    - Tomorrow's plans without weather data
    
    Uses WeatherService with cache, rate limiting, and circuit breaker.
    """
    from core.models import DailyPlan, Project
    from core.services.weather import weather_service
    
    now = timezone.now()
    today = now.date()
    tomorrow = today + timedelta(days=1)
    
    # Target plans: today and tomorrow, not in SKIPPED/CANCELLED
    target_plans = DailyPlan.objects.filter(
        plan_date__in=[today, tomorrow],
        status__in=['DRAFT', 'PUBLISHED', 'IN_PROGRESS']
    ).select_related('project')
    
    updated = 0
    skipped_no_address = 0
    skipped_stale = 0
    errors = 0
    
    for plan in target_plans:
        # Skip if no project address (can't geocode)
        if not plan.project.address:
            skipped_no_address += 1
            continue
        
        # Check if weather data is recent (< 2 hours old)
        if plan.weather_fetched_at:
            age = (now - plan.weather_fetched_at).total_seconds() / 3600
            if age < 2:  # Skip if fetched within last 2 hours
                skipped_stale += 1
                continue
        
        # Attempt weather fetch
        try:
            plan.fetch_weather()
            updated += 1
            logger.info(f"Updated weather for DailyPlan {plan.id} ({plan.project.name}, {plan.plan_date})")
        except Exception as e:
            errors += 1
            logger.error(f"Failed to fetch weather for DailyPlan {plan.id}: {e}")
    
    result = {
        'updated': updated,
        'skipped_no_address': skipped_no_address,
        'skipped_recent': skipped_stale,
        'errors': errors,
        'timestamp': str(now)
    }
    
    logger.info(f"Weather update complete: {result}")
    return result


@shared_task(name='core.tasks.fetch_weather_for_plan')
def fetch_weather_for_plan(plan_id):
    """
    Fetch weather data for a specific DailyPlan (async task).
    Called automatically when plan is created/updated.
    
    Args:
        plan_id: DailyPlan primary key
    
    Returns:
        dict with status and weather data summary
    """
    from core.models import DailyPlan
    
    try:
        plan = DailyPlan.objects.get(id=plan_id)
    except DailyPlan.DoesNotExist:
        logger.error(f"DailyPlan {plan_id} not found for weather fetch")
        return {'status': 'not_found', 'plan_id': plan_id}
    
    if not plan.project.address:
        logger.warning(f"DailyPlan {plan_id} has no project address, skipping weather fetch")
        return {'status': 'no_address', 'plan_id': plan_id}
    
    try:
        weather_data = plan.fetch_weather()
        if weather_data:
            logger.info(f"Weather fetched successfully for DailyPlan {plan_id}")
            return {
                'status': 'success',
                'plan_id': plan_id,
                'temperature': weather_data.get('temperature'),
                'condition': weather_data.get('condition')
            }
        else:
            logger.warning(f"Weather fetch returned no data for DailyPlan {plan_id}")
            return {'status': 'no_data', 'plan_id': plan_id}
    except Exception as e:
        logger.error(f"Error fetching weather for DailyPlan {plan_id}: {e}")
        return {'status': 'error', 'plan_id': plan_id, 'error': str(e)}


