#!/usr/bin/env python3
"""Generate inventory.json for repo files (skip .git, venvs, node_modules)."""
import os
import json

root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
items = []
for dirpath, dirnames, filenames in os.walk(root):
    # skip .git and virtualenv and node_modules
    parts = set(dirpath.split(os.sep))
    if '.git' in parts or '.venv' in parts or 'venv' in parts or 'node_modules' in parts:
        continue
    for f in filenames:
        path = os.path.join(dirpath, f)
        try:
            size = os.path.getsize(path)
        except OSError:
            size = 0
        items.append({'path': os.path.relpath(path, root), 'size': size})

out = {'generated_by': 'assistant', 'root': root, 'file_count': len(items), 'files': sorted(items, key=lambda x: x['path'])}
with open(os.path.join(root, 'inventory.json'), 'w') as fh:
    json.dump(out, fh, indent=2, ensure_ascii=False)

print('inventory.json written with', len(items), 'files')
