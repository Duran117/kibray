#!/usr/bin/env python3
"""Find templates with most inline CSS for refactor priority."""
import os, re

results = []
template_dir = 'core/templates/core'
for f in sorted(os.listdir(template_dir)):
    if not f.endswith('.html'):
        continue
    path = os.path.join(template_dir, f)
    with open(path) as fh:
        content = fh.read()
    # Count CSS chars inside <style> blocks
    style_blocks = re.findall(r'<style[^>]*>(.*?)</style>', content, re.DOTALL)
    css_chars = sum(len(s) for s in style_blocks)
    css_lines = sum(s.count('\n') for s in style_blocks)
    total_lines = content.count('\n')
    if css_lines > 30:
        results.append((css_lines, total_lines, f))

results.sort(reverse=True)
print(f"{'CSS':>5}  {'TOTAL':>5}  FILE")
for css, total, name in results[:30]:
    print(f"{css:>5}  {total:>5}  {name}")
