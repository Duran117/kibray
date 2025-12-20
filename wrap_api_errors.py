#!/usr/bin/env python3
"""
Wrap API error messages with gettext
"""

filepath = '/Users/jesus/Documents/kibray/core/api/views.py'

# Read the file
with open(filepath, encoding='utf-8') as f:
    content = f.read()

# Simple string patterns (no f-strings)
patterns = [
    ('{"error": "entity_type and action required"}', '{"error": gettext("entity_type and action required")}'),
    ('{"error": "entity_type and entity_id required"}', '{"error": gettext("entity_type and entity_id required")}'),
    ('{"error": "Admin access required"}', '{"error": gettext("Admin access required")}'),
    ('{"error": "status required"}', '{"error": gettext("status required")}'),
    ('{"error": "Touch-up requires photo evidence before completion"}', '{"error": gettext("Touch-up requires photo evidence before completion")}'),
    ('{"error": "Touch-up requires a photo before completion"}', '{"error": gettext("Touch-up requires a photo before completion")}'),
    ('{"error": "dependency_id required"}', '{"error": gettext("dependency_id required")}'),
    ('{"error": "Task cannot depend on itself"}', '{"error": gettext("Task cannot depend on itself")}'),
    ('{"error": "Dependency task not found"}', '{"error": gettext("Dependency task not found")}'),
    ('{"error": "Task not in Completada state"}', '{"error": gettext("Task not in Completada state")}'),
    ('{"error": "Dependencies incomplete"}', '{"error": gettext("Dependencies incomplete")}'),
    ('{"error": "Already tracking or touch-up"}', '{"error": gettext("Already tracking or touch-up")}'),
    ('{"error": "Not tracking"}', '{"error": gettext("Not tracking")}'),
    ('{"error": "image file required"}', '{"error": gettext("image file required")}'),
    ('{"error": "assigned_to is required"}', '{"error": gettext("assigned_to is required")}'),
    ('{"error": "User not found"}', '{"error": gettext("User not found")}'),
]

for old, new in patterns:
    content = content.replace(old, new)

# F-string patterns
content = content.replace(
    '{"error": f"Invalid status. Valid: {valid_statuses}"}',
    '{"error": gettext("Invalid status. Valid: %(statuses)s") % {"statuses": valid_statuses}}'
)

content = content.replace(
    '{"error": str(e)}',
    '{"error": gettext("%(error)s") % {"error": str(e)}}'
)

# Write back
with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print("Wrapped API error messages with gettext")
