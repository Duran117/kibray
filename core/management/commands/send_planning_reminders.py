from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings
from django.core.mail import send_mail
from core.models import DailyPlan

class Command(BaseCommand):
    help = "Send reminder emails for Daily Plans still in DRAFT and past their submission deadline"

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Do not send emails, just list plans')

    def handle(self, *args, **options):
        now = timezone.now()
        # Plans whose deadline passed within last 24h and still DRAFT
        window_start = now - timezone.timedelta(hours=24)
        plans = DailyPlan.objects.filter(status='DRAFT', completion_deadline__lte=now, completion_deadline__gte=window_start)
        if not plans.exists():
            self.stdout.write(self.style.SUCCESS('No overdue draft plans to remind.'))
            return

        count = 0
        for plan in plans.select_related('project', 'created_by'):
            pm = plan.created_by
            if not pm or not pm.email:
                continue
            subject = f"Reminder: Submit Daily Plan for {plan.project.name} ({plan.plan_date})"
            body = (
                f"The daily plan for project '{plan.project.name}' for date {plan.plan_date} is still in DRAFT.\n"
                f"Deadline was: {plan.completion_deadline}. Please finalize and submit ASAP to avoid operational issues.\n\n"
                f"Login to submit." 
            )
            if options['dry_run']:
                self.stdout.write(f"[DRY] Would send reminder to {pm.email} for plan {plan.id}")
            else:
                try:
                    send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [pm.email], fail_silently=True)
                    count += 1
                except Exception as e:
                    self.stderr.write(f"Failed to send to {pm.email}: {e}")
        if options['dry_run']:
            self.stdout.write(self.style.WARNING(f"Dry run complete. {plans.count()} plans checked."))
        else:
            self.stdout.write(self.style.SUCCESS(f"Sent {count} reminder emails."))
