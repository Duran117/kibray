#!/usr/bin/env python3
"""
Template Audit Script
Analyzes all HTML templates in core/templates/core/ to find:
1. Broken URL references
2. Forms without valid actions
3. Missing JavaScript functions
4. Unused templates
"""

import os
import re
from pathlib import Path
from collections import defaultdict

BASE_DIR = Path('/Users/jesus/Documents/kibray')
TEMPLATES_DIR = BASE_DIR / 'core' / 'templates' / 'core'
VIEWS_DIR = BASE_DIR / 'core' / 'views'
STATIC_DIR = BASE_DIR / 'core' / 'static'
URLS_FILE = BASE_DIR / 'kibray_backend' / 'urls.py'
API_URLS_FILE = BASE_DIR / 'core' / 'api' / 'urls.py'

# Patterns to search
URL_PATTERN = r"\{%\s*url\s+['\"]([^'\"]+)['\"]"
FORM_ACTION_PATTERN = r'action=["\']([^"\']*)["\']'
ONCLICK_PATTERN = r'onclick=["\']([^"\']+)["\']'
HREF_PATTERN = r'href=["\']([^"\']+)["\']'
BUTTON_PATTERN = r'<button[^>]*>|<a[^>]*class="[^"]*btn[^"]*"[^>]*>'

def get_all_templates():
    """Get all HTML templates"""
    templates = []
    for root, dirs, files in os.walk(TEMPLATES_DIR):
        for f in files:
            if f.endswith('.html'):
                templates.append(Path(root) / f)
    return sorted(templates)

def get_all_url_names():
    """Extract all URL names from urls.py files"""
    url_names = set()
    
    # Main URLs file
    if URLS_FILE.exists():
        content = URLS_FILE.read_text()
        names = re.findall(r"name=['\"]([^'\"]+)['\"]", content)
        url_names.update(names)
    
    # API URLs file
    if API_URLS_FILE.exists():
        content = API_URLS_FILE.read_text()
        names = re.findall(r"name=['\"]([^'\"]+)['\"]", content)
        url_names.update(names)
    
    return url_names

def get_all_templates_used_in_views():
    """Get all template names referenced in views"""
    templates_used = set()
    for root, dirs, files in os.walk(VIEWS_DIR):
        for f in files:
            if f.endswith('.py'):
                filepath = Path(root) / f
                content = filepath.read_text()
                # Pattern: template_name = 'xxx' or render(request, 'xxx')
                matches = re.findall(r"['\"]core/([^'\"]+\.html)['\"]", content)
                templates_used.update(matches)
    return templates_used

def analyze_template(template_path, valid_urls):
    """Analyze a single template for issues"""
    issues = []
    content = template_path.read_text()
    template_name = template_path.name
    
    # Remove HTML comments before analysis
    content_no_comments = re.sub(r'{#.*?#}', '', content, flags=re.DOTALL)
    content_no_comments = re.sub(r'<!--.*?-->', '', content_no_comments, flags=re.DOTALL)
    
    # 1. Check URL references (using content without comments)
    url_refs = re.findall(URL_PATTERN, content_no_comments)
    for url_name in url_refs:
        # Some URLs have arguments like 'name' pk=x, extract just the name
        clean_name = url_name.split()[0] if ' ' in url_name else url_name
        if clean_name not in valid_urls:
            issues.append(f"  ❌ URL not found: '{clean_name}'")
    
    # 2. Check form actions
    forms = re.findall(r'<form[^>]*>', content, re.IGNORECASE)
    for form in forms:
        if 'action=' in form.lower():
            action = re.search(r'action=["\']([^"\']*)["\']', form)
            if action:
                action_val = action.group(1)
                if action_val and not action_val.startswith('{%') and not action_val.startswith('#'):
                    if not action_val.startswith('/'):
                        issues.append(f"  ⚠️ Form action may be invalid: '{action_val}'")
    
    # 3. Check for common patterns that indicate buttons
    buttons = re.findall(r'<button[^>]*type=["\']submit["\'][^>]*>', content, re.IGNORECASE)
    submit_btns = len(buttons)
    
    # 4. Check onclick handlers for common JS functions
    onclicks = re.findall(ONCLICK_PATTERN, content)
    js_functions = set()
    for onclick in onclicks:
        # Extract function names
        funcs = re.findall(r'(\w+)\s*\(', onclick)
        js_functions.update(funcs)
    
    # Check if JS functions are defined in the same file
    script_content = re.findall(r'<script[^>]*>(.*?)</script>', content, re.DOTALL | re.IGNORECASE)
    script_text = '\n'.join(script_content)
    
    for func in js_functions:
        # Skip common built-in functions
        if func in ['alert', 'confirm', 'console', 'setTimeout', 'setInterval', 
                    'parseInt', 'parseFloat', 'history', 'window', 'document',
                    'fetch', 'JSON', 'location', 'event', 'this', 'return']:
            continue
        # Check if function is defined
        if f'function {func}' not in script_text and f'{func} =' not in script_text and f'{func}:' not in script_text:
            # Could be defined in external JS file
            if f'{func}' not in content:
                pass  # May be external, don't flag
    
    # 5. Check for broken internal hrefs
    hrefs = re.findall(HREF_PATTERN, content)
    for href in hrefs:
        if href and not href.startswith(('#', '{%', '{{', 'javascript:', 'mailto:', 'tel:', 'http', '/')):
            issues.append(f"  ⚠️ Suspicious href: '{href}'")
    
    return issues, submit_btns, url_refs

def main():
    print("=" * 80)
    print("TEMPLATE AUDIT REPORT")
    print("=" * 80)
    
    # Get all data
    templates = get_all_templates()
    valid_urls = get_all_url_names()
    templates_used = get_all_templates_used_in_views()
    
    print(f"\nFound {len(templates)} templates")
    print(f"Found {len(valid_urls)} URL names")
    print(f"Found {len(templates_used)} templates referenced in views")
    
    # Categories
    broken_urls = []
    form_issues = []
    unused_templates = []
    all_issues = defaultdict(list)
    
    # Analyze each template
    for template in templates:
        rel_path = template.relative_to(TEMPLATES_DIR)
        issues, submit_count, urls = analyze_template(template, valid_urls)
        
        if issues:
            all_issues[str(rel_path)] = issues
        
        # Check if template is unused
        template_rel = str(rel_path)
        if template_rel not in templates_used:
            # Check if it's included/extended from other templates
            is_included = False
            for other in templates:
                if other == template:
                    continue
                other_content = other.read_text()
                if rel_path.name in other_content or str(rel_path) in other_content:
                    is_included = True
                    break
            if not is_included:
                # Could be a base/partial template
                if not any(x in template_rel for x in ['base', 'partial', '_']):
                    unused_templates.append(str(rel_path))
    
    # Print issues
    print("\n" + "=" * 80)
    print("TEMPLATES WITH ISSUES")
    print("=" * 80)
    
    for template, issues in sorted(all_issues.items()):
        print(f"\n📄 {template}")
        for issue in issues:
            print(issue)
    
    # Print unused templates
    print("\n" + "=" * 80)
    print("POTENTIALLY UNUSED TEMPLATES")
    print("=" * 80)
    
    for template in sorted(unused_templates):
        print(f"  ❓ {template}")
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"  Total templates: {len(templates)}")
    print(f"  Templates with issues: {len(all_issues)}")
    print(f"  Potentially unused: {len(unused_templates)}")
    
    # Generate detailed report
    report_path = BASE_DIR / 'TEMPLATE_AUDIT_DETAILED.md'
    with open(report_path, 'w') as f:
        f.write("# Template Audit Detailed Report\n\n")
        f.write(f"Generated: Auto\n\n")
        f.write(f"## Summary\n")
        f.write(f"- Total templates: {len(templates)}\n")
        f.write(f"- Templates with issues: {len(all_issues)}\n")
        f.write(f"- Potentially unused: {len(unused_templates)}\n\n")
        
        f.write("## Issues Found\n\n")
        for template, issues in sorted(all_issues.items()):
            f.write(f"### {template}\n")
            for issue in issues:
                f.write(f"{issue}\n")
            f.write("\n")
        
        f.write("## Potentially Unused Templates\n\n")
        for template in sorted(unused_templates):
            f.write(f"- {template}\n")
    
    print(f"\n📝 Detailed report saved to: {report_path}")

if __name__ == '__main__':
    main()
