"""
Quick API Test Script - Verifies all endpoints are working
Run this after starting the development server: python manage.py runserver
"""

import requests

BASE_URL = "http://127.0.0.1:8000/api/v1"


def test_api():
    print("=" * 60)
    print("🧪 Kibray API v1 - Quick Test")
    print("=" * 60)

    # Test 1: Login endpoint (requires existing user)
    print("\n1️⃣ Testing Login Endpoint...")
    print(f"   POST {BASE_URL}/auth/login/")

    # Note: This will fail without a real user, but shows the endpoint is routed
    try:
        response = requests.post(f"{BASE_URL}/auth/login/", json={"username": "test", "password": "test"}, timeout=5)
        if response.status_code == 401:
            print("   ✅ Endpoint routed correctly (401 Unauthorized - expected without user)")
        else:
            print(f"   ⚠️  Status: {response.status_code}")
            print(f"   Response: {response.json()}")
    except requests.exceptions.ConnectionError:
        print("   ❌ Server not running! Start with: python manage.py runserver")
        return
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return

    # Test 2: List endpoints (should return 401 without token)
    endpoints = [
        ("Notifications", "/notifications/"),
        ("Chat Channels", "/chat-channels/"),
        ("Chat Messages", "/chat-messages/"),
        ("Tasks", "/tasks/"),
        ("Damage Reports", "/damage-reports/"),
        ("Floor Plans", "/floor-plans/"),
        ("Plan Pins", "/plan-pins/"),
        ("Color Samples", "/color-samples/"),
        ("Projects", "/projects/"),
    ]

    print("\n2️⃣ Testing Protected Endpoints (should return 401)...")
    for name, path in endpoints:
        try:
            response = requests.get(f"{BASE_URL}{path}", timeout=5)
            if response.status_code == 401:
                print(f"   ✅ {name:<20} - Properly protected")
            elif response.status_code == 200:
                print(f"   ⚠️  {name:<20} - Returned data (check auth config)")
            else:
                print(f"   ⚠️  {name:<20} - Status {response.status_code}")
        except Exception as e:
            print(f"   ❌ {name:<20} - Error: {e}")

    # Test 3: Create superuser and test full flow
    print("\n3️⃣ Full Flow Test (requires superuser)...")
    print("   To test login + authenticated requests:")
    print("   1. Create superuser: python manage.py createsuperuser")
    print("   2. Run: python manage.py shell")
    print("   3. Execute:")
    print(
        """
   from rest_framework_simplejwt.tokens import RefreshToken
   from django.contrib.auth.models import User
   user = User.objects.filter(is_superuser=True).first()
   refresh = RefreshToken.for_user(user)
   print(f"Access Token: {refresh.access_token}")
   """
    )
    print("   4. Use token in Authorization header: Bearer <token>")

    print("\n" + "=" * 60)
    print("✅ API Structure Test Complete!")
    print("=" * 60)
    print("\n📚 Next Steps:")
    print("   - Review API_README.md for full endpoint documentation")
    print("   - Review IOS_SETUP_GUIDE.md for mobile app setup")
    print("   - Test with Postman or curl using real credentials")
    print("\n")


if __name__ == "__main__":
    test_api()
