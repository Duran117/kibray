#!/usr/bin/env bash
set -euo pipefail

# Kibray production backup script for PostgreSQL
# Usage: ./scripts/backup_postgres.sh <DB_NAME> <DB_USER> <OUTPUT_DIR>
# Requires: pg_dump in PATH, proper network access to DB host
# Optional env vars: PGHOST, PGPORT, PGPASSWORD

if [ "$#" -lt 3 ]; then
  echo "Usage: $0 <DB_NAME> <DB_USER> <OUTPUT_DIR>"
  exit 1
fi

DB_NAME="$1"
DB_USER="$2"
OUTPUT_DIR="$3"
TIMESTAMP=$(date +"%Y%m%d-%H%M%S")
OUT_FILE="$OUTPUT_DIR/${DB_NAME}-${TIMESTAMP}.sql.gz"

mkdir -p "$OUTPUT_DIR"

# Safety: do not echo password; rely on env var PGPASSWORD or .pgpass
# Example: export PGPASSWORD="yourpassword"

echo "Backing up database '$DB_NAME' as user '$DB_USER' to '$OUT_FILE'"
pg_dump -U "$DB_USER" -F p "$DB_NAME" | gzip -9 > "$OUT_FILE"

# Optional: verify gzip integrity
gzip -t "$OUT_FILE"

echo "Backup completed: $OUT_FILE"
