"""Phase 9 Commit L cleanup — strip unused legacy-helper imports.

For each file under ``core/views/`` (except ``_helpers.py``) this script:
  1. Parses the explicit ``from core.views._helpers import (...)`` block.
  2. Removes any listed name in UNUSED_PER_FILE that isn't actually called
     anywhere else in the file body.
  3. If the resulting list is empty, removes the entire import block.

Safe because every view file also does ``from core.views._helpers import *``
above the explicit block, so removing redundant names doesn't break runtime.
The explicit block exists for IDE introspection only — once a name isn't
used, keeping it just adds visual noise.
"""
from __future__ import annotations

import os
import re
import sys


HELPERS = [
    "_is_admin_user", "_is_staffish", "_is_pm_or_admin",
    "_check_user_project_access", "_require_admin_or_redirect",
    "_require_roles", "ROLES_ADMIN", "ROLES_PM", "ROLES_STAFF",
]


def find_explicit_import_block(src: str):
    """Return (start, end, body) of the first
    ``from core.views._helpers import (...)`` block, or None.
    """
    m = re.search(
        r"^from\s+core\.views\._helpers\s+import\s*\(",
        src,
        re.MULTILINE,
    )
    if not m:
        return None
    start = m.start()
    # Find matching close paren.
    i = m.end() - 1  # at '('
    depth = 0
    while i < len(src):
        if src[i] == "(":
            depth += 1
        elif src[i] == ")":
            depth -= 1
            if depth == 0:
                # Consume trailing newline if any.
                end = i + 1
                if end < len(src) and src[end] == "\n":
                    end += 1
                return start, end, src[m.start():end]
        i += 1
    return None


def is_truly_unused(src_minus_imports: str, name: str) -> bool:
    return not re.search(rf"\b{re.escape(name)}\b", src_minus_imports)


def clean_file(path: str) -> int:
    src = open(path).read()
    block = find_explicit_import_block(src)
    if block is None:
        return 0
    start, end, block_text = block

    # Body without the import block (so name detection ignores the import itself).
    body_only = src[:start] + src[end:]

    # Parse the comma-separated name list inside the parens.
    inner = re.search(r"\(([^()]*)\)", block_text, re.DOTALL).group(1)
    raw_items = [
        s.strip().rstrip(",").strip()
        for s in inner.replace("\n", ",").split(",")
    ]
    items = [s for s in raw_items if s and not s.startswith("#")]

    kept, removed = [], []
    for name in items:
        if name in HELPERS and is_truly_unused(body_only, name):
            removed.append(name)
        else:
            kept.append(name)

    if not removed:
        return 0

    if not kept:
        # Drop the entire explicit block.
        new_src = src[:start] + src[end:]
    else:
        # Rebuild with kept items, preserving formatting style.
        new_inner = "\n    " + ",\n    ".join(kept) + ",\n"
        new_block = f"from core.views._helpers import ({new_inner})\n"
        new_src = src[:start] + new_block + src[end:]

    open(path, "w").write(new_src)
    print(f"{path}: removed {len(removed)} unused import(s): {', '.join(removed)}")
    return len(removed)


def main():
    total = 0
    for root, _, files in os.walk("core/views"):
        for fn in files:
            if not fn.endswith(".py") or fn == "_helpers.py":
                continue
            total += clean_file(os.path.join(root, fn))
    print(f"\nTotal removed: {total}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
