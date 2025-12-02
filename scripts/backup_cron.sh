#!/bin/bash
# Automated Database Backup Script
# Add to crontab: 0 2 * * * /path/to/backup_cron.sh

set -e

# Configuration
PROJECT_DIR="/Users/jesus/Documents/kibray"
VENV_DIR="$PROJECT_DIR/.venv"
LOG_FILE="$PROJECT_DIR/logs/backup.log"

# Activate virtual environment
source "$VENV_DIR/bin/activate"

# Change to project directory
cd "$PROJECT_DIR"

# Run backup with S3 upload
echo "[$(date)] Starting database backup..." >> "$LOG_FILE"
python manage.py backup_database --upload-s3 >> "$LOG_FILE" 2>&1

if [ $? -eq 0 ]; then
    echo "[$(date)] ✅ Backup completed successfully" >> "$LOG_FILE"
else
    echo "[$(date)] ❌ Backup failed" >> "$LOG_FILE"
    exit 1
fi
