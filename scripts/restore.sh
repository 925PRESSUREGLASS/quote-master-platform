#!/bin/bash

# Quote Master Pro - Restore Script

set -e

# Configuration
BACKUP_DIR="${BACKUP_DIR:-./backups}"
DB_CONTAINER="${DB_CONTAINER:-quote-master-db}"
DB_NAME="${POSTGRES_DB:-quote_master}"
DB_USER="${POSTGRES_USER:-postgres}"

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS] TIMESTAMP"
    echo ""
    echo "Restore Quote Master Pro from backup"
    echo ""
    echo "Options:"
    echo "  -d, --database-only    Restore only database"
    echo "  -f, --files-only       Restore only files"
    echo "  -c, --config-only      Restore only configuration"
    echo "  -h, --help            Show this help message"
    echo ""
    echo "Example:"
    echo "  $0 20240115_143022"
    echo "  $0 --database-only 20240115_143022"
    echo ""
    echo "Available backups:"
    if [ -d "$BACKUP_DIR" ]; then
        ls -1 "$BACKUP_DIR" | grep -E "manifest_[0-9]{8}_[0-9]{6}\.txt" | sed 's/manifest_/  /' | sed 's/\.txt//'
    else
        echo "  No backup directory found"
    fi
}

# Parse command line arguments
RESTORE_DATABASE=true
RESTORE_FILES=true
RESTORE_CONFIG=true

while [[ $# -gt 0 ]]; do
    case $1 in
        -d|--database-only)
            RESTORE_DATABASE=true
            RESTORE_FILES=false
            RESTORE_CONFIG=false
            shift
            ;;
        -f|--files-only)
            RESTORE_DATABASE=false
            RESTORE_FILES=true
            RESTORE_CONFIG=false
            shift
            ;;
        -c|--config-only)
            RESTORE_DATABASE=false
            RESTORE_FILES=false
            RESTORE_CONFIG=true
            shift
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        -*)
            echo "Unknown option $1"
            show_usage
            exit 1
            ;;
        *)
            TIMESTAMP="$1"
            shift
            ;;
    esac
done

# Validate timestamp
if [ -z "$TIMESTAMP" ]; then
    echo "❌ Error: Timestamp is required"
    show_usage
    exit 1
fi

# Check if backup files exist
if [ ! -f "$BACKUP_DIR/manifest_$TIMESTAMP.txt" ]; then
    echo "❌ Error: Backup manifest not found for timestamp $TIMESTAMP"
    echo "Available backups:"
    ls -1 "$BACKUP_DIR" | grep -E "manifest_[0-9]{8}_[0-9]{6}\.txt" | sed 's/manifest_/  /' | sed 's/\.txt//' || echo "  No backups found"
    exit 1
fi

echo "🔄 Starting restore process for backup: $TIMESTAMP"
echo "📋 Reading backup manifest..."
cat "$BACKUP_DIR/manifest_$TIMESTAMP.txt"
echo ""

# Confirm restore
read -p "⚠️  This will overwrite current data. Continue? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Restore cancelled"
    exit 1
fi

# Stop services
echo "🛑 Stopping services..."
docker-compose down

# Database restore
if [ "$RESTORE_DATABASE" = true ]; then
    echo "🗄️  Restoring database..."
    
    if [ -f "$BACKUP_DIR/database_$TIMESTAMP.sql.gz" ]; then
        # Start only database service
        docker-compose up -d db
        
        # Wait for database to be ready
        echo "⏳ Waiting for database to be ready..."
        sleep 10
        
        # Drop and recreate database
        docker exec "$DB_CONTAINER" dropdb -U "$DB_USER" "$DB_NAME" --if-exists
        docker exec "$DB_CONTAINER" createdb -U "$DB_USER" "$DB_NAME"
        
        # Restore database
        gunzip -c "$BACKUP_DIR/database_$TIMESTAMP.sql.gz" | docker exec -i "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME"
        echo "✅ Database restored successfully"
    else
        echo "⚠️  Database backup file not found, skipping..."
    fi
fi

# Files restore
if [ "$RESTORE_FILES" = true ]; then
    echo "📁 Restoring files..."
    
    if [ -f "$BACKUP_DIR/uploads_$TIMESTAMP.tar.gz" ]; then
        # Backup current uploads if they exist
        if [ -d "./uploads" ]; then
            mv ./uploads "./uploads.backup.$(date +%s)"
        fi
        
        # Extract uploads
        tar -xzf "$BACKUP_DIR/uploads_$TIMESTAMP.tar.gz"
        echo "✅ Files restored successfully"
    else
        echo "⚠️  Files backup not found, skipping..."
    fi
fi

# Configuration restore
if [ "$RESTORE_CONFIG" = true ]; then
    echo "⚙️  Restoring configuration..."
    
    if [ -f "$BACKUP_DIR/config_$TIMESTAMP.tar.gz" ]; then
        # Backup current config
        tar -czf "./config.backup.$(date +%s).tar.gz" \
            docker-compose*.yml Dockerfile* nginx/ monitoring/ scripts/ 2>/dev/null || true
        
        # Extract configuration
        tar -xzf "$BACKUP_DIR/config_$TIMESTAMP.tar.gz"
        echo "✅ Configuration restored successfully"
    else
        echo "⚠️  Configuration backup not found, skipping..."
    fi
fi

# Docker volumes restore
echo "📦 Restoring Docker volumes..."

if [ -f "$BACKUP_DIR/postgres_volume_$TIMESTAMP.tar.gz" ]; then
    docker volume rm quote-master-pro_postgres_data 2>/dev/null || true
    docker volume create quote-master-pro_postgres_data
    docker run --rm \
        -v quote-master-pro_postgres_data:/target \
        -v "$PWD/$BACKUP_DIR":/backup \
        alpine tar -xzf "/backup/postgres_volume_$TIMESTAMP.tar.gz" -C /target
    echo "✅ PostgreSQL volume restored"
fi

if [ -f "$BACKUP_DIR/redis_volume_$TIMESTAMP.tar.gz" ]; then
    docker volume rm quote-master-pro_redis_data 2>/dev/null || true
    docker volume create quote-master-pro_redis_data
    docker run --rm \
        -v quote-master-pro_redis_data:/target \
        -v "$PWD/$BACKUP_DIR":/backup \
        alpine tar -xzf "/backup/redis_volume_$TIMESTAMP.tar.gz" -C /target
    echo "✅ Redis volume restored"
fi

# Start services
echo "🚀 Starting services..."
docker-compose up -d

echo "✅ Restore completed successfully!"
echo "🌐 Quote Master Pro should be available at: http://localhost:8000"

# Show service status
echo ""
echo "📋 Service Status:"
docker-compose ps