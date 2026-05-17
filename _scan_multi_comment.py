import re, pathlib
for p in pathlib.Path('core/templates').rglob('*.html'):
    src = p.read_text(encoding='utf-8', errors='ignore')
    for m in re.finditer(r'\{#(.*?)#\}', src, re.DOTALL):
        if '\n' in m.group(1):
            line = src[:m.start()].count('\n') + 1
            n = len(m.group(1).splitlines())
            print(f'{p}:{line}: multi-line ({n} lines)')
