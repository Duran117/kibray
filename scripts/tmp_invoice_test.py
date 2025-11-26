import os, sys, pathlib
PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
	sys.path.insert(0, str(PROJECT_ROOT))
os.environ.setdefault('DJANGO_SETTINGS_MODULE','kibray_backend.settings')
import django
django.setup()
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.utils import timezone
from core.models import Project, Invoice
User = get_user_model()

user = User.objects.create_user(username='invtester2', password='x')
project = Project.objects.create(name='PayProj2', client='ClientY', start_date=timezone.now().date())

invoice = Invoice.objects.create(project=project, total_amount=Decimal('500.00'), status='SENT')
print('Initial', invoice.status, invoice.amount_paid, invoice.is_paid, invoice.fully_paid, invoice.balance_due, round(invoice.payment_progress,2))

invoice.amount_paid = Decimal('200.00')
invoice.save()
invoice.refresh_from_db()
print('Partial', invoice.status, invoice.amount_paid, invoice.is_paid, invoice.fully_paid, invoice.balance_due, round(invoice.payment_progress,2))

invoice.amount_paid = Decimal('500.00')
invoice.save()
invoice.refresh_from_db()
print('Full', invoice.status, invoice.amount_paid, invoice.is_paid, invoice.fully_paid, invoice.balance_due, round(invoice.payment_progress,2))

invoice.amount_paid = Decimal('600.00')
invoice.save()
invoice.refresh_from_db()
print('Overpay', invoice.status, invoice.amount_paid, invoice.is_paid, invoice.fully_paid, invoice.balance_due, round(invoice.payment_progress,2))
