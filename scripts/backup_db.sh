#!/bin/bash
# Komission PostgreSQL Backup Script
# Runs daily via cron or manually
# Usage: ./backup_db.sh

set -e

BACKUP_DIR="/Users/ted/komission/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/komission_pg_${TIMESTAMP}.sql"
RETENTION_DAYS=7

# Create backup directory if not exists
mkdir -p "${BACKUP_DIR}"

echo "📦 Starting PostgreSQL backup..."

# Dump PostgreSQL database
docker exec komission-postgres-1 pg_dump -U kmeme_user kmeme_db > "${BACKUP_FILE}"

# Compress
gzip "${BACKUP_FILE}"
BACKUP_FILE="${BACKUP_FILE}.gz"

# Calculate size
SIZE=$(du -h "${BACKUP_FILE}" | cut -f1)
echo "✅ Backup created: ${BACKUP_FILE} (${SIZE})"

# Clean old backups (keep last 7 days)
echo "🧹 Cleaning backups older than ${RETENTION_DAYS} days..."
find "${BACKUP_DIR}" -name "komission_pg_*.sql.gz" -mtime +${RETENTION_DAYS} -delete

# List current backups
echo ""
echo "📋 Current backups:"
ls -lh "${BACKUP_DIR}"/komission_pg_*.sql.gz 2>/dev/null || echo "  (none)"

echo ""
echo "✨ Backup complete!"
