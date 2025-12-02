#!/usr/bin/env python
"""
Script to create Django superuser
Run with: railway run python create_admin.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kibray_backend.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

username = 'admin'
email = 'admin@kibray.com'
password = 'Kibray2025!Admin'

if User.objects.filter(username=username).exists():
    print(f'⚠️  User "{username}" already exists')
    user = User.objects.get(username=username)
    print(f'   Email: {user.email}')
    print(f'   Is superuser: {user.is_superuser}')
    print(f'   Is staff: {user.is_staff}')
else:
    user = User.objects.create_superuser(username, email, password)
    print(f'✅ Superuser created successfully!')
    print(f'   Username: {username}')
    print(f'   Email: {email}')
    print(f'   Password: {password}')
    print(f'   Is superuser: {user.is_superuser}')
    print(f'   Is staff: {user.is_staff}')
