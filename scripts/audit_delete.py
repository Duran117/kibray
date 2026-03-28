#!/usr/bin/env python3
"""
Delete Functionality Audit
Ensure all delete operations have proper confirmation
"""

import os
import re
from pathlib import Path

BASE_DIR = Path('/Users/jesus/Documents/kibray')
TEMPLATES_DIR = BASE_DIR / 'core' / 'templates' / 'core'

def check_delete_confirmations(template_path):
    """Check if delete operations have proper confirmation"""
    issues = []
    content = template_path.read_text()
    
    # Remove HTML/Django comments
    content_clean = re.sub(r'{#.*?#}', '', content, flags=re.DOTALL)
    content_clean = re.sub(r'<!--.*?-->', '', content_clean, flags=re.DOTALL)
    
    # Find delete-related forms and buttons
    # Pattern 1: Forms with "delete" in action
    delete_forms = re.findall(r'<form[^>]*action=["\'][^"\']*delete[^"\']*["\'][^>]*>(.*?)</form>', 
                              content_clean, re.IGNORECASE | re.DOTALL)
    
    for form in delete_forms:
        # Check for confirmation - onsubmit with confirm, or it's a dedicated confirm page
        if 'onsubmit' not in content_clean.lower():
            # Check if the form itself is in a confirmation dialog/modal
            if 'modal' not in content_clean.lower() and 'confirm' not in content_clean.lower():
                if 'confirm_delete' not in template_path.name:
                    issues.append("⚠️ Delete form without confirmation dialog")
    
    # Pattern 2: Direct delete links without confirmation
    # Find links with delete in href but no confirm
    delete_links = re.findall(r'<a[^>]*href=["\'][^"\']*delete[^"\']*["\'][^>]*>.*?</a>', 
                              content_clean, re.IGNORECASE | re.DOTALL)
    
    for link in delete_links:
        if 'confirm' not in link.lower() and 'modal' not in link.lower():
            if 'data-bs-toggle="modal"' not in link:
                issues.append(f"⚠️ Delete link without modal trigger: {link[:100]}...")
    
    # Pattern 3: Buttons with delete action
    delete_buttons = re.findall(r'<button[^>]*onclick=["\'][^"\']*delete[^"\']*["\'][^>]*>.*?</button>',
                                content_clean, re.IGNORECASE | re.DOTALL)
    
    for btn in delete_buttons:
        if 'confirm' not in btn.lower():
            issues.append(f"⚠️ Delete button without confirmation: {btn[:100]}...")
    
    return issues

def main():
    print("=" * 80)
    print("DELETE FUNCTIONALITY AUDIT")
    print("=" * 80)
    
    # Get templates with delete keyword
    delete_templates = []
    for root, dirs, files in os.walk(TEMPLATES_DIR):
        for f in files:
            if f.endswith('.html'):
                filepath = Path(root) / f
                content = filepath.read_text()
                if 'delete' in content.lower() or 'eliminar' in content.lower():
                    delete_templates.append(filepath)
    
    print(f"\nFound {len(delete_templates)} templates with delete functionality\n")
    
    # Templates that should have dedicated confirm pages
    expected_confirm_pages = {
        'project': 'project_delete_confirm.html',
        'client': 'client_delete_confirm.html',
        'task': 'task_confirm_delete.html',
        'changeorder': 'changeorder_confirm_delete.html',
        'expense': 'expense_confirm_delete.html',
        'income': 'income_confirm_delete.html',
        'rfi': 'rfi_confirm_delete.html',
        'risk': 'risk_confirm_delete.html',
        'issue': 'issue_confirm_delete.html',
        'site_photo': 'site_photo_confirm_delete.html',
        'floor_plan': 'floor_plan_confirm_delete.html',
        'color_sample': 'color_sample_confirm_delete.html',
        'daily_log': 'daily_log_confirm_delete.html',
        'daily_plan': 'daily_plan_confirm_delete.html',
        'damage_report': 'damage_report_confirm_delete.html',
        'organization': 'organization_delete_confirm.html',
        'timeentry': 'timeentry_confirm_delete.html',
        'schedule_item': 'schedule_item_confirm_delete.html',
        'schedule_category': 'schedule_category_confirm_delete.html',
    }
    
    # Check which confirm pages exist
    print("DELETE CONFIRMATION PAGES:")
    print("-" * 40)
    
    for entity, expected_file in sorted(expected_confirm_pages.items()):
        filepath = TEMPLATES_DIR / expected_file
        if filepath.exists():
            print(f"  ✅ {entity}: {expected_file}")
        else:
            print(f"  ❌ {entity}: MISSING {expected_file}")
    
    # Check for issues
    print("\n" + "=" * 80)
    print("ISSUES FOUND:")
    print("-" * 40)
    
    issues_found = []
    for template in sorted(delete_templates):
        rel_path = template.relative_to(TEMPLATES_DIR)
        issues = check_delete_confirmations(template)
        if issues:
            issues_found.append((str(rel_path), issues))
    
    if issues_found:
        for template, issues in issues_found:
            print(f"\n📄 {template}")
            for issue in issues:
                print(f"  {issue}")
    else:
        print("\n✅ All delete operations have proper confirmation!")
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("-" * 40)
    print(f"Templates with delete: {len(delete_templates)}")
    print(f"Templates with issues: {len(issues_found)}")
    confirm_pages = [f for f in os.listdir(TEMPLATES_DIR) if 'confirm_delete' in f or 'delete_confirm' in f]
    print(f"Confirmation pages: {len(confirm_pages)}")

if __name__ == '__main__':
    main()
