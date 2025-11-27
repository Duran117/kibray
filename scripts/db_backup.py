"""Simple SQLite backup script.
Creates a timestamped copy of db.sqlite3 into backups/ directory.
Usage:
    python scripts/db_backup.py
"""

from __future__ import annotations

import datetime as dt
import pathlib
import shutil
import sys

BASE_DIR = pathlib.Path(__file__).resolve().parent.parent
DB_FILE = BASE_DIR / "db.sqlite3"
BACKUP_DIR = BASE_DIR / "backups"


def backup_sqlite(db_path: pathlib.Path, dest_dir: pathlib.Path) -> pathlib.Path:
    if not db_path.exists():
        raise FileNotFoundError(f"Database file not found: {db_path}")
    dest_dir.mkdir(exist_ok=True)
    timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = dest_dir / f"db_backup_{timestamp}.sqlite3"
    shutil.copy2(db_path, backup_path)
    return backup_path


if __name__ == "__main__":
    try:
        path = backup_sqlite(DB_FILE, BACKUP_DIR)
        print(f"Backup created: {path}")
    except Exception as e:
        print(f"Backup failed: {e}", file=sys.stderr)
        sys.exit(1)
