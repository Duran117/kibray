from datetime import date
import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "kibray_backend.settings")
django.setup()

from django.contrib.auth.models import User

from core.models import Employee, Project


def setup_data():
    print("Setting up test data...")

    # Ensure Admin
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser('admin', 'admin@example.com', 'Kibray2025!Admin')
        print("Created admin user")

    # Ensure Project
    project, created = Project.objects.get_or_create(
        name="Test Project Full",
        defaults={
            'start_date': date.today(),
            'project_code': 'TP-FULL'
        }
    )
    if created:
        print(f"Created project: {project.name}")

    # Ensure Employees
    employees = [
        {'first_name': 'John', 'last_name': 'Doe', 'email': 'john@example.com'},
        {'first_name': 'Jane', 'last_name': 'Smith', 'email': 'jane@example.com'},
        {'first_name': 'Bob', 'last_name': 'Builder', 'email': 'bob@example.com'},
    ]

    for emp_data in employees:
        user, _ = User.objects.get_or_create(username=emp_data['email'], defaults={'email': emp_data['email']})
        emp, created = Employee.objects.get_or_create(
            social_security_number=f"SSN-{emp_data['first_name']}",
            defaults={
                'user': user,
                'first_name': emp_data['first_name'],
                'last_name': emp_data['last_name'],
                'hourly_rate': 25.00,
                'email': emp_data['email']
            }
        )
        if created:
            print(f"Created employee: {emp.first_name} {emp.last_name}")

    print("Data setup complete.")

if __name__ == "__main__":
    setup_data()
