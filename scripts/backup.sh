#!/bin/bash

# Quote Master Pro - Backup Script

set -e

# Configuration
BACKUP_DIR="${BACKUP_DIR:-./backups}"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-7}"

# Database configuration
DB_CONTAINER="${DB_CONTAINER:-quote-master-db}"
DB_NAME="${POSTGRES_DB:-quote_master}"
DB_USER="${POSTGRES_USER:-postgres}"

echo "📦 Starting backup process..."

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Database backup
echo "🗄️  Backing up database..."
docker exec "$DB_CONTAINER" pg_dump -U "$DB_USER" -d "$DB_NAME" | gzip > "$BACKUP_DIR/database_$TIMESTAMP.sql.gz"

# Uploads backup
echo "📁 Backing up uploads..."
if [ -d "./uploads" ]; then
    tar -czf "$BACKUP_DIR/uploads_$TIMESTAMP.tar.gz" -C . uploads/
else
    echo "⚠️  Uploads directory not found, skipping..."
fi

# Configuration backup
echo "⚙️  Backing up configuration..."
tar -czf "$BACKUP_DIR/config_$TIMESTAMP.tar.gz" \
    --exclude='.env*' \
    --exclude='*.log' \
    --exclude='node_modules' \
    --exclude='.git' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    .env.example docker-compose*.yml Dockerfile* nginx/ monitoring/ scripts/ 2>/dev/null || true

# Docker volumes backup
echo "📦 Backing up Docker volumes..."
docker run --rm \
    -v quote-master-pro_postgres_data:/source:ro \
    -v "$PWD/$BACKUP_DIR":/backup \
    alpine tar -czf "/backup/postgres_volume_$TIMESTAMP.tar.gz" -C /source .

docker run --rm \
    -v quote-master-pro_redis_data:/source:ro \
    -v "$PWD/$BACKUP_DIR":/backup \
    alpine tar -czf "/backup/redis_volume_$TIMESTAMP.tar.gz" -C /source .

# Clean old backups
echo "🧹 Cleaning old backups (older than $BACKUP_RETENTION_DAYS days)..."
find "$BACKUP_DIR" -name "*.gz" -mtime +$BACKUP_RETENTION_DAYS -delete 2>/dev/null || true

# Create backup manifest
echo "📋 Creating backup manifest..."
cat > "$BACKUP_DIR/manifest_$TIMESTAMP.txt" << EOF
Quote Master Pro Backup Manifest
Created: $(date)
Timestamp: $TIMESTAMP

Files included:
- database_$TIMESTAMP.sql.gz (PostgreSQL database dump)
- uploads_$TIMESTAMP.tar.gz (User uploaded files)
- config_$TIMESTAMP.tar.gz (Configuration files)
- postgres_volume_$TIMESTAMP.tar.gz (PostgreSQL data volume)
- redis_volume_$TIMESTAMP.tar.gz (Redis data volume)

Restore instructions:
1. Stop all services: docker-compose down
2. Restore database: gunzip -c database_$TIMESTAMP.sql.gz | docker exec -i quote-master-db psql -U $DB_USER -d $DB_NAME
3. Restore uploads: tar -xzf uploads_$TIMESTAMP.tar.gz
4. Restore volumes: Use docker volume commands to restore data
5. Start services: docker-compose up -d
EOF

echo "✅ Backup completed successfully!"
echo "📁 Backup location: $BACKUP_DIR"
echo "📋 Manifest: $BACKUP_DIR/manifest_$TIMESTAMP.txt"

# List current backups
echo ""
echo "📦 Current backups:"
ls -lh "$BACKUP_DIR" | grep "$TIMESTAMP" || echo "No backups found for this session"