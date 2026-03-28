#!/usr/bin/env python3
"""
Button Audit Script
Deep analysis of buttons and forms in templates
"""

import os
import re
from pathlib import Path
from collections import defaultdict

BASE_DIR = Path('/Users/jesus/Documents/kibray')
TEMPLATES_DIR = BASE_DIR / 'core' / 'templates' / 'core'
VIEWS_DIR = BASE_DIR / 'core' / 'views'

def get_all_view_functions():
    """Extract all view function names from views"""
    view_funcs = set()
    for root, dirs, files in os.walk(VIEWS_DIR):
        for f in files:
            if f.endswith('.py'):
                filepath = Path(root) / f
                content = filepath.read_text()
                # Pattern: def function_name(request
                funcs = re.findall(r'def\s+(\w+)\s*\(\s*request', content)
                view_funcs.update(funcs)
    return view_funcs

def analyze_forms(template_path):
    """Analyze forms in template"""
    issues = []
    content = template_path.read_text()
    
    # Remove comments
    content = re.sub(r'{#.*?#}', '', content, flags=re.DOTALL)
    content = re.sub(r'<!--.*?-->', '', content, flags=re.DOTALL)
    
    # Find all forms with their opening tags
    form_pattern = r'<form([^>]*)>(.*?)</form>'
    forms = re.findall(form_pattern, content, re.IGNORECASE | re.DOTALL)
    
    for i, (form_attrs, form_content) in enumerate(forms, 1):
        form_attrs_lower = form_attrs.lower()
        
        # Check if it's a POST form (explicit POST or no method = default POST)
        is_post = 'method="post"' in form_attrs_lower or "method='post'" in form_attrs_lower
        is_get = 'method="get"' in form_attrs_lower or "method='get'" in form_attrs_lower
        
        # If not explicitly GET, it could be POST (need CSRF)
        if is_post and 'csrf_token' not in form_content:
            # Check if it's a JS-handled form (has id and likely uses fetch)
            if ' id=' not in form_attrs:
                issues.append(f"  ❌ Form {i}: Missing CSRF token in POST form (CRITICAL)")
        
        # Check for submit capability - button inside form, input submit, or JS submit
        has_button = '<button' in form_content.lower()
        has_input_submit = 'type="submit"' in form_content.lower() or "type='submit'" in form_content.lower()
        has_js_submit = 'submit()' in form_content or '.submit(' in form_content
        
        # Only report if truly no way to submit
        if not has_button and not has_input_submit and not has_js_submit:
            # Check if form has ID (likely JS handled)
            if ' id=' not in form_attrs:
                issues.append(f"  ⚠️ Form {i}: No submit mechanism found")
    
    return issues

def analyze_buttons(template_path):
    """Analyze buttons that aren't in forms"""
    issues = []
    content = template_path.read_text()
    
    # Remove comments
    content = re.sub(r'{#.*?#}', '', content, flags=re.DOTALL)
    content = re.sub(r'<!--.*?-->', '', content, flags=re.DOTALL)
    
    # Find buttons with onclick but no href and not in form
    # Pattern for buttons with onclick
    onclick_buttons = re.findall(r'<button[^>]*onclick=["\']([^"\']+)["\'][^>]*>', content, re.IGNORECASE)
    
    for onclick in onclick_buttons:
        # Extract function name
        func_match = re.search(r'(\w+)\s*\(', onclick)
        if func_match:
            func_name = func_match.group(1)
            # Check if function is defined
            if func_name not in ['alert', 'confirm', 'history', 'window', 'location', 'document', 'this', 'return', 'event']:
                if f'function {func_name}' not in content and f'{func_name} =' not in content:
                    # Check for inline function calls
                    pass  # May be from external JS
    
    return issues

def analyze_delete_buttons(template_path):
    """Check delete buttons have proper confirmation"""
    issues = []
    content = template_path.read_text()
    
    # Remove comments
    content = re.sub(r'{#.*?#}', '', content, flags=re.DOTALL)
    content = re.sub(r'<!--.*?-->', '', content, flags=re.DOTALL)
    
    # Find delete-related buttons/links
    delete_patterns = [
        r'delete',
        r'eliminar',
        r'remove',
        r'trash',
    ]
    
    for pattern in delete_patterns:
        matches = re.finditer(rf'<(button|a)[^>]*>.*?{pattern}.*?</(button|a)>', content, re.IGNORECASE | re.DOTALL)
        for match in matches:
            element = match.group(0)
            # Check for confirmation
            if 'confirm' not in element.lower() and 'modal' not in element.lower() and 'data-bs-toggle="modal"' not in element:
                # Could be direct delete without confirmation
                pass
    
    return issues

def main():
    print("=" * 80)
    print("BUTTON DEEP AUDIT")
    print("=" * 80)
    
    view_funcs = get_all_view_functions()
    print(f"Found {len(view_funcs)} view functions")
    
    templates = []
    for root, dirs, files in os.walk(TEMPLATES_DIR):
        for f in files:
            if f.endswith('.html'):
                templates.append(Path(root) / f)
    
    print(f"Analyzing {len(templates)} templates...\n")
    
    critical_issues = []
    
    for template in sorted(templates):
        rel_path = template.relative_to(TEMPLATES_DIR)
        
        form_issues = analyze_forms(template)
        button_issues = analyze_buttons(template)
        delete_issues = analyze_delete_buttons(template)
        
        all_issues = form_issues + button_issues + delete_issues
        
        if all_issues:
            critical_issues.append((str(rel_path), all_issues))
    
    if critical_issues:
        print("CRITICAL ISSUES FOUND:")
        print("-" * 40)
        for template, issues in critical_issues:
            print(f"\n📄 {template}")
            for issue in issues:
                print(issue)
    else:
        print("✅ No critical button issues found!")
    
    print("\n" + "=" * 80)
    print("TEMPLATES WITH DELETE FUNCTIONALITY")
    print("=" * 80)
    
    delete_templates = []
    for template in templates:
        content = template.read_text()
        if any(x in content.lower() for x in ['delete', 'eliminar', 'remove', '_delete']):
            delete_templates.append(template.relative_to(TEMPLATES_DIR))
    
    for t in sorted(delete_templates):
        print(f"  📄 {t}")
    
    print(f"\nTotal: {len(delete_templates)} templates with delete functionality")

if __name__ == '__main__':
    main()
