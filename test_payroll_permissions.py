#!/usr/bin/env python3
"""
Test script para verificar permisos de Payroll
Solo Admin y PM deben tener acceso
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kibray_backend.settings')
django.setup()

from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory, force_authenticate
from core.api.views import PayrollPeriodViewSet, PayrollRecordViewSet
from core.models import Profile

User = get_user_model()

def test_payroll_permissions():
    """Test que solo Admin y PM pueden acceder a Payroll"""
    
    factory = APIRequestFactory()
    
    # Crear usuarios de prueba con diferentes roles
    roles_to_test = [
        ('admin', True),
        ('superuser', True),
        ('project_manager', True),
        ('owner', True),
        ('client', False),
        ('employee', False),
        ('superintendent', False),
    ]
    
    print("🧪 Testing Payroll Permissions\n" + "="*50)
    
    for role, should_have_access in roles_to_test:
        # Crear usuario
        username = f'test_{role}'
        user, created = User.objects.get_or_create(
            username=username,
            defaults={'email': f'{username}@test.com'}
        )
        
        # Si es admin o superuser, activar is_staff
        if role in ['admin', 'superuser']:
            user.is_staff = True
            user.is_superuser = role == 'superuser'
            user.save()
        
        # Crear o actualizar profile
        profile, _ = Profile.objects.get_or_create(user=user)
        profile.role = role
        profile.save()
        
        # Test PayrollPeriodViewSet
        request = factory.get('/api/v1/payroll-periods/')
        force_authenticate(request, user=user)
        
        view = PayrollPeriodViewSet.as_view({'get': 'list'})
        response = view(request)
        
        # Verificar resultado
        has_access = response.status_code != 403
        status_icon = "✅" if has_access == should_have_access else "❌"
        access_text = "GRANTED" if has_access else "DENIED"
        expected_text = "SHOULD ACCESS" if should_have_access else "SHOULD DENY"
        
        print(f"{status_icon} Role: {role:20} | Access: {access_text:8} | Expected: {expected_text:15} | Status: {response.status_code}")
        
        if has_access != should_have_access:
            print(f"   ⚠️  FAILED: {role} {'should' if should_have_access else 'should NOT'} have access!")
    
    print("\n" + "="*50)
    print("✅ Test completed!")

if __name__ == '__main__':
    test_payroll_permissions()
