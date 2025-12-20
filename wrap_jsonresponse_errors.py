#!/usr/bin/env python3
"""
Wrap JsonResponse "error" strings with gettext()
"""
import re

# Read file
with open('/Users/jesus/Documents/kibray/core/views.py', encoding='utf-8') as f:
    content = f.read()

# Pattern for simple error messages without f-strings
# JsonResponse({"error": "text"}, ...)
pattern = r'JsonResponse\(\{"error": "([^"]+)"\}'
replacement = r'JsonResponse({"error": gettext("\1")}'

content = re.sub(pattern, replacement, content)

# Now handle f-string errors - these need manual conversion
# For now, let's handle a few common ones
fstring_replacements = [
    ('{"error": f"No se puede iniciar. Dependencias incompletas: {dep_names}"}',
     '{"error": gettext("No se puede iniciar. Dependencias incompletas: %(deps)s") % {"deps": dep_names}}'),
]

for old, new in fstring_replacements:
    content = content.replace(old, new)

# Write back
with open('/Users/jesus/Documents/kibray/core/views.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Wrapped JsonResponse error messages")
