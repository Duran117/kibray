"""Phase 9 Commit M migrator — move callers off two legacy shims.

Migrates ``_check_user_project_access`` → ``check_project_access`` and
``_require_admin_or_redirect`` → ``require_admin_or_redirect`` across
``core/views/`` source files.

Steps per file:
  1. Remove those two names from any explicit
     ``from core.views._helpers import (...)`` block (preserve the rest).
  2. If at least one of the migrated names was actually used, insert
     a single ``from core.access import ...`` line right after the
     ``_helpers import *`` line (or after the explicit ``_helpers`` block).
  3. Rewrite call sites: bare-name occurrences swap to the canonical name.

Idempotent: re-running is a no-op once migration is complete.
"""
from __future__ import annotations

import os
import re

RENAMES = {
    "_check_user_project_access": "check_project_access",
    "_require_admin_or_redirect": "require_admin_or_redirect",
}


def find_explicit_block(src: str):
    m = re.search(
        r"^from\s+core\.views\._helpers\s+import\s*\(",
        src, re.MULTILINE,
    )
    if not m:
        return None
    i = m.end() - 1
    depth = 0
    while i < len(src):
        if src[i] == "(":
            depth += 1
        elif src[i] == ")":
            depth -= 1
            if depth == 0:
                end = i + 1
                if end < len(src) and src[end] == "\n":
                    end += 1
                return m.start(), end
        i += 1
    return None


def parse_items(block_text: str):
    inner = re.search(r"\(([^()]*)\)", block_text, re.DOTALL).group(1)
    raw = [s.strip().rstrip(",").strip()
           for s in inner.replace("\n", ",").split(",")]
    return [s for s in raw if s and not s.startswith("#")]


def rebuild_block(items):
    if not items:
        return ""
    inner = "\n    " + ",\n    ".join(items) + ",\n"
    return f"from core.views._helpers import ({inner})\n"


def migrate(path: str) -> tuple[int, int]:
    src = open(path).read()
    if not any(re.search(rf"\b{old}\b", src) for old in RENAMES):
        return 0, 0

    # ── 1. Update the explicit import block (drop migrated names).
    block = find_explicit_block(src)
    used_canonicals = set()
    if block is not None:
        start, end = block
        block_text = src[start:end]
        items = parse_items(block_text)
        kept = []
        for name in items:
            if name in RENAMES:
                used_canonicals.add(RENAMES[name])
            else:
                kept.append(name)
        if kept != items:
            src = src[:start] + rebuild_block(kept) + src[end:]

    # ── 2. Rewrite bare call sites (the import line is already gone,
    #      so this is safe — won't double-rename).
    rewrites = 0
    for old, new in RENAMES.items():
        pattern = rf"\b{old}\b"
        new_src, n = re.subn(pattern, new, src)
        if n:
            used_canonicals.add(new)
            rewrites += n
            src = new_src

    # ── 3. Add a clean canonical import (after the wildcard line if any,
    #      else at the top after the docstring).
    if used_canonicals and "from core.access import" not in src:
        names = ", ".join(sorted(used_canonicals))
        new_import = f"from core.access import {names}\n"
        wildcard_line = re.search(
            r"^from core\.views\._helpers import \*.*$\n",
            src, re.MULTILINE,
        )
        if wildcard_line:
            ins = wildcard_line.end()
            src = src[:ins] + new_import + src[ins:]
        else:
            # Insert after the module docstring / first import line.
            m = re.search(r"^(from|import)\s", src, re.MULTILINE)
            ins = m.start() if m else 0
            src = src[:ins] + new_import + src[ins:]
    elif used_canonicals:
        # An import line already exists — extend it if any canonical name missing.
        m = re.search(
            r"^from core\.access import (.+)$", src, re.MULTILINE,
        )
        if m:
            existing = {s.strip() for s in m.group(1).split(",")}
            existing.update(used_canonicals)
            new_line = f"from core.access import {', '.join(sorted(existing))}"
            src = src[: m.start()] + new_line + src[m.end():]

    open(path, "w").write(src)
    return rewrites, len(used_canonicals)


def main():
    total_calls = 0
    files = 0
    for root, _, fs in os.walk("core/views"):
        for fn in fs:
            if not fn.endswith(".py") or fn == "_helpers.py":
                continue
            path = os.path.join(root, fn)
            n, k = migrate(path)
            if n or k:
                files += 1
                total_calls += n
                print(f"{path}: {n} call rewrite(s)")
    print(f"\nFiles touched: {files}   total call rewrites: {total_calls}")


if __name__ == "__main__":
    main()
