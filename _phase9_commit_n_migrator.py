"""Phase 9 Commit N migrator — collapse `_is_staffish` and
`_is_pm_or_admin` callers in core/views/ onto the canonical
``core.access.is_admin_or_pm`` (narrow staff predicate that
explicitly excludes ROLE_OWNER).

Per file:
  1. Remove `_is_staffish` and `_is_pm_or_admin` from any explicit
     `from core.views._helpers import (...)` block (preserve other names).
  2. If at least one call site exists, insert
     `from core.access import is_admin_or_pm` after the wildcard
     `_helpers import *` line (or extend any existing top-level
     `from core.access import ...` line).
  3. Rewrite bare call sites: `_is_staffish(...)` and `_is_pm_or_admin(...)`
     -> `is_admin_or_pm(...)`.

Idempotent.
"""
from __future__ import annotations

import os
import re

OLD_NAMES = {"_is_staffish", "_is_pm_or_admin"}
NEW_NAME = "is_admin_or_pm"


def find_explicit_block(src: str):
    m = re.search(r"^from\s+core\.views\._helpers\s+import\s*\(",
                  src, re.MULTILINE)
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


def has_top_level_canonical(src: str) -> re.Match | None:
    """Return the FIRST top-level (column 0) ``from core.access import ...``
    line, or None. Indented imports inside functions don't count.
    """
    return re.search(r"^from core\.access import (.+)$", src, re.MULTILINE)


def migrate(path: str) -> int:
    src = open(path).read()
    if not any(re.search(rf"\b{old}\b", src) for old in OLD_NAMES):
        return 0

    # ── 1. Drop migrated names from the explicit import block.
    block = find_explicit_block(src)
    if block is not None:
        start, end = block
        block_text = src[start:end]
        items = parse_items(block_text)
        kept = [n for n in items if n not in OLD_NAMES]
        if kept != items:
            src = src[:start] + rebuild_block(kept) + src[end:]

    # ── 2. Rewrite bare call sites.
    rewrites = 0
    for old in OLD_NAMES:
        new_src, n = re.subn(rf"\b{old}\b", NEW_NAME, src)
        if n:
            rewrites += n
            src = new_src

    # ── 3. Ensure top-level canonical import exists & contains NEW_NAME.
    canon = has_top_level_canonical(src)
    if canon is None:
        # Insert after wildcard helpers line, else at module top.
        wildcard = re.search(
            r"^from core\.views\._helpers import \*.*$\n",
            src, re.MULTILINE,
        )
        if wildcard:
            ins = wildcard.end()
        else:
            m = re.search(r"^(from|import)\s", src, re.MULTILINE)
            ins = m.start() if m else 0
        src = src[:ins] + f"from core.access import {NEW_NAME}\n" + src[ins:]
    else:
        existing = {s.strip() for s in canon.group(1).split(",") if s.strip()}
        if NEW_NAME not in existing:
            existing.add(NEW_NAME)
            new_line = f"from core.access import {', '.join(sorted(existing))}"
            src = src[: canon.start()] + new_line + src[canon.end():]

    open(path, "w").write(src)
    return rewrites


def main():
    total = 0
    files_touched = 0
    for root, _, fs in os.walk("core/views"):
        for fn in fs:
            if not fn.endswith(".py") or fn == "_helpers.py":
                continue
            path = os.path.join(root, fn)
            n = migrate(path)
            if n:
                files_touched += 1
                total += n
                print(f"{path}: {n} call rewrite(s)")
    print(f"\nFiles touched: {files_touched}   total call rewrites: {total}")


if __name__ == "__main__":
    main()
