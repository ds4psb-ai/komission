#!/bin/bash
# Restore PostgreSQL from backup
# Usage: ./restore_db.sh [backup_file.sql.gz]

set -e

BACKUP_DIR="/Users/ted/komission/backups"

if [ -z "$1" ]; then
    echo "📋 Available backups:"
    ls -lht "${BACKUP_DIR}"/komission_pg_*.sql.gz 2>/dev/null || echo "  No backups found"
    echo ""
    echo "Usage: $0 <backup_file.sql.gz>"
    echo "Example: $0 ${BACKUP_DIR}/komission_pg_20260103_120000.sql.gz"
    exit 1
fi

BACKUP_FILE="$1"

if [ ! -f "${BACKUP_FILE}" ]; then
    echo "❌ Backup file not found: ${BACKUP_FILE}"
    exit 1
fi

echo "⚠️  WARNING: This will DROP and recreate the database!"
echo "📦 Restore from: ${BACKUP_FILE}"
read -p "Continue? (y/N): " confirm

if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
    echo "Cancelled."
    exit 0
fi

echo "🔄 Restoring database..."

# Decompress to temp file
TEMP_SQL="/tmp/komission_restore_$$.sql"
gunzip -c "${BACKUP_FILE}" > "${TEMP_SQL}"

# Drop and recreate database
docker exec -i komission-postgres-1 psql -U kmeme_user -d postgres -c "DROP DATABASE IF EXISTS kmeme_db;"
docker exec -i komission-postgres-1 psql -U kmeme_user -d postgres -c "CREATE DATABASE kmeme_db;"

# Restore
cat "${TEMP_SQL}" | docker exec -i komission-postgres-1 psql -U kmeme_user -d kmeme_db

# Cleanup
rm -f "${TEMP_SQL}"

echo "✅ Database restored successfully!"
echo ""
echo "🔄 Restart backend to reconnect:"
echo "   pkill -f 'uvicorn app.main' && cd /Users/ted/komission/backend && source venv/bin/activate && uvicorn app.main:app --reload"
