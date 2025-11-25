from django.test import Client
from django.contrib.auth import get_user_model
from core.models import Project, DailyPlan, Employee
from datetime import date

User = get_user_model()

u = User.objects.create_user(username='x', password='x')
client = Client()
client.force_login(u)

p = Project.objects.create(name='P', start_date=date.today(), address='addr')
plan = DailyPlan.objects.create(project=p, plan_date=date.today(), completion_deadline=date.today())
em = Employee.objects.create(first_name='T', last_name='W', social_security_number='111-11-1111', hourly_rate='10.00')

payload = {
    'title': 'Prep',
    'description': 'desc',
    'order': 1,
    'assigned_employees': [em.id],
    'estimated_hours': 3.5
}
res = client.post(f'/api/v1/daily-plans/{plan.id}/add_activity/', payload, content_type='application/json')
print(res.status_code)
print(res.json())
