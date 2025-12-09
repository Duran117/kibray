import os
import django
import re
from urllib.parse import urlparse, urljoin
from django.test import Client
from django.urls import reverse
from bs4 import BeautifulSoup

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "kibray_backend.settings")
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()

def run_audit():
    print("🚀 Starting Comprehensive Navigation Audit...")
    
    # 1. Setup User
    username = "audit_admin"
    password = "audit_password"
    email = "audit@example.com"
    
    user, created = User.objects.get_or_create(username=username, email=email)
    user.set_password(password)
    user.is_staff = True
    user.is_superuser = True
    user.save()
    
    client = Client()
    login_success = client.login(username=username, password=password)
    if not login_success:
        print("❌ Failed to login as superuser. Aborting.")
        return

    print("✅ Logged in as superuser.")

    # 2. Define Starting Points
    start_urls = [
        "/",
        "/dashboard/",
        "/dashboard/admin/",
        "/dashboard/pm/",
        "/dashboard/employee/",
        "/projects/",
        "/pm-calendar/",
        "/focus/",
        "/planner/",
    ]
    
    visited = set()
    to_visit = set(start_urls)
    errors = []
    warnings = []
    
    # Limit recursion to avoid infinite loops or external sites
    max_pages = 150
    count = 0

    while to_visit and count < max_pages:
        url = to_visit.pop()
        if url in visited:
            continue
            
        visited.add(url)
        count += 1
        
        # Skip static, media, or external links
        if url.startswith("/static/") or url.startswith("/media/") or url.startswith("http"):
            continue
            
        # Normalize URL
        if not url.startswith("/"):
            url = "/" + url

        try:
            print(f"Checking ({count}/{max_pages}): {url}")
            response = client.get(url, follow=True)
            
            if response.status_code >= 400:
                errors.append(f"❌ {response.status_code} at {url}")
                print(f"   -> ERROR: {response.status_code}")
                continue
                
            # Parse HTML for more links
            if 'text/html' in response.headers.get('Content-Type', ''):
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Find links
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    # Clean href
                    href = href.split('#')[0]
                    href = href.split('?')[0]
                    
                    if not href: continue
                    if href.startswith("javascript:"): continue
                    if href.startswith("mailto:"): continue
                    if href.startswith("tel:"): continue
                    
                    # Handle relative URLs
                    full_url = href
                    if not href.startswith("/") and not href.startswith("http"):
                        # Simple relative handling (could be improved)
                        full_url = urljoin(url, href)
                    
                    # Only add internal links
                    if full_url.startswith("/") and full_url not in visited:
                        to_visit.add(full_url)
                        
                # Find forms
                for form in soup.find_all('form', action=True):
                    action = form['action']
                    if action and action.startswith("/") and action not in visited:
                        to_visit.add(action)

        except Exception as e:
            errors.append(f"❌ Exception at {url}: {str(e)}")
            print(f"   -> EXCEPTION: {e}")

    print("\n" + "="*30)
    print("📊 AUDIT REPORT")
    print("="*30)
    
    if not errors:
        print("✅ No broken links found in scanned paths.")
    else:
        print(f"Found {len(errors)} errors:")
        for err in errors:
            print(err)
            
    print("="*30)

if __name__ == "__main__":
    run_audit()
