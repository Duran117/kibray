#!/usr/bin/env python3
"""
Wrap remaining API error messages with gettext
"""
import re

filepath = '/Users/jesus/Documents/kibray/core/api/views.py'

# Read the file
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Remaining simple string patterns
patterns = [
    ('{"error": "Invalid cost value"}', '{"error": gettext("Invalid cost value")}'),
    ('{"error": "Staff permission required"}', '{"error": gettext("Staff permission required")}'),
    ('{"error": "Cannot approve resolved damage"}', '{"error": gettext("Cannot approve resolved damage")}'),
    ('{"error": "Damage already resolved"}', '{"error": gettext("Damage already resolved")}'),
    ('{"error": "Change Order already created"}', '{"error": gettext("Change Order already created")}'),
    ('{"error": "updates must be an object"}', '{"error": gettext("updates must be an object")}'),
]

for old, new in patterns:
    content = content.replace(old, new)

# Write back
with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print("Wrapped remaining API error messages")
