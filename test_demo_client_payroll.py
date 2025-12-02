#!/usr/bin/env python3
"""
Test rápido para verificar que demo_client no puede acceder a payroll
"""

import os
import sys
import django

sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kibray_backend.settings')
django.setup()

from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory, force_authenticate
from core.api.views import PayrollPeriodViewSet

User = get_user_model()

def test_demo_client():
    """Test que demo_client NO puede acceder a Payroll"""
    
    factory = APIRequestFactory()
    
    try:
        # Obtener usuario demo_client
        user = User.objects.get(username='demo_client')
        profile = user.profile
        
        print(f"🔍 Testing demo_client access to Payroll")
        print(f"   Username: {user.username}")
        print(f"   Email: {user.email}")
        print(f"   Role: {profile.role}")
        print(f"   is_staff: {user.is_staff}")
        print(f"   is_superuser: {user.is_superuser}")
        print()
        
        # Test acceso a PayrollPeriodViewSet
        request = factory.get('/api/v1/payroll-periods/')
        force_authenticate(request, user=user)
        
        view = PayrollPeriodViewSet.as_view({'get': 'list'})
        response = view(request)
        
        if response.status_code == 403:
            print("✅ SUCCESS: demo_client DENIED access to Payroll (Status 403)")
            print("   This is correct - clients should not see payroll data")
        else:
            print(f"❌ FAILED: demo_client got access to Payroll (Status {response.status_code})")
            print("   This is a security issue - clients should NOT see payroll!")
            
    except User.DoesNotExist:
        print("⚠️  User 'demo_client' does not exist")
        print("   Run: python3 manage.py create_demo_client")

if __name__ == '__main__':
    test_demo_client()
