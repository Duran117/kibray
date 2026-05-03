#!/usr/bin/env python
"""Bulk-wrap hardcoded strings in `messages.X(request, "...")` calls with `_()`.

Targets `core/views/*.py`. Idempotent: skips strings already wrapped in `_(`,
`gettext(`, `gettext_lazy(`, or `ngettext(`. Also ensures
`from django.utils.translation import gettext_lazy as _` is present.

Why: LANGUAGE_CODE='es' makes raw Spanish leak into UI for EN users.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TARGET_DIR = ROOT / "core" / "views"

# messages.<level>(request, "literal" [, ...])  — single OR double quoted, no f"" or already-wrapped
MSG_RE = re.compile(
    r"""(messages\.(?:success|error|warning|info|debug)\(\s*request\s*,\s*)
        (?!_\(|gettext|ngettext|f["'])
        (?P<q>["'])(?P<text>(?:\\.|(?!(?P=q)).)*?)(?P=q)
    """,
    re.VERBOSE,
)

IMPORT_LINE = "from django.utils.translation import gettext_lazy as _\n"

changed_files: list[tuple[Path, int]] = []

for py in sorted(TARGET_DIR.glob("*.py")):
    if py.name.startswith("__"):
        continue
    src = py.read_text(encoding="utf-8")

    new_src, n = MSG_RE.subn(
        lambda m: f'{m.group(1)}_({m.group("q")}{m.group("text")}{m.group("q")})',
        src,
    )
    if n == 0:
        continue

    # Ensure import present
    if "gettext_lazy as _" not in new_src and "from django.utils.translation import gettext as _" not in new_src:
        # Insert after the last `from django` import or top of file imports
        lines = new_src.splitlines(keepends=True)
        insert_at = 0
        for i, line in enumerate(lines):
            if line.startswith(("import ", "from ")):
                insert_at = i + 1
        lines.insert(insert_at, IMPORT_LINE)
        new_src = "".join(lines)

    py.write_text(new_src, encoding="utf-8")
    changed_files.append((py, n))

print(f"Wrapped {sum(n for _, n in changed_files)} strings in {len(changed_files)} files:")
for p, n in changed_files:
    print(f"  {p.relative_to(ROOT)}: {n}")
