#!/usr/bin/env python
"""Rename throwaway `_` variables to `__` in files where we added a
`gettext_lazy as _` import, so the i18n alias isn't shadowed by tuple-unpack.

Patterns rewritten (only in files listed in MODIFIED):
- `, _ =`              ->  `, __ =`
- `_, `   (tuple LHS)  ->  `__, `   (only when on LHS of `=`)
- `for _ in `          ->  `for __ in `
- `for _, `            ->  `for __, `
- `, _ in `            ->  `, __ in `
- standalone `_ = expr` line  ->  `__ = expr`
"""
from __future__ import annotations
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

MODIFIED = [
    "core/views/_helpers.py",
    "core/views/changeorder_views.py",
    "core/views/chat_views.py",
    "core/views/client_mgmt_views.py",
    "core/views/color_floor_views.py",
    "core/views/contract_views.py",
    "core/views/daily_log_views.py",
    "core/views/daily_plan_views.py",
    "core/views/damage_report_views.py",
    "core/views/dashboard_admin_views.py",
    "core/views/dashboard_client_views.py",
    "core/views/dashboard_employee_views.py",
    "core/views/dashboard_pm_views.py",
    "core/views/expense_income_views.py",
    "core/views/file_views.py",
    "core/views/financial_views.py",
    "core/views/materials_views.py",
    "core/views/meeting_minutes_views.py",
    "core/views/payroll_views.py",
    "core/views/project_client_portal_views.py",
    "core/views/project_crud_views.py",
    "core/views/project_overview_views.py",
    "core/views/project_progress_views.py",
    "core/views/rfi_issue_risk_views.py",
    "core/views/schedule_views.py",
    "core/views/task_views.py",
    "core/views/touchup_legacy_views.py",
]

PATTERNS = [
    # `, _ =`  -> `, __ =`   (right-hand of LHS tuple unpacking)
    (re.compile(r",\s*_\s*="), ", __ ="),
    # `_, X =` at start of LHS unpacking -> `__, X =`
    (re.compile(r"(^|\n)(\s*)_,\s"), r"\1\2__, "),
    # `for _ in` / `for _, ` -> __ variants
    (re.compile(r"\bfor\s+_\s+in\b"), "for __ in"),
    (re.compile(r"\bfor\s+_\s*,"), "for __,"),
    (re.compile(r",\s*_\s+in\b"), ", __ in"),
    # `_ = expr` standalone line
    (re.compile(r"(^|\n)(\s+)_\s*=\s"), r"\1\2__ = "),
]

total = 0
for rel in MODIFIED:
    p = ROOT / rel
    if not p.exists():
        continue
    src = p.read_text(encoding="utf-8")
    new = src
    for pat, repl in PATTERNS:
        new = pat.sub(repl, new)
    if new != src:
        diff = sum(1 for a, b in zip(src.split("\n"), new.split("\n")) if a != b)
        p.write_text(new, encoding="utf-8")
        print(f"  {rel}: {diff} line(s) updated")
        total += diff

print(f"Total lines updated: {total}")
