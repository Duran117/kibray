import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kibray_backend.settings')
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()
try:
    u = User.objects.get(username='admin')
    u.set_password('Kibray2025!Admin')
    u.save()
    print("Password updated successfully.")
except User.DoesNotExist:
    print("User 'admin' not found.")
