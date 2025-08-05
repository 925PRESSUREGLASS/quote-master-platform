#!/bin/bash

# Quote Master Pro - Startup Script

set -e

echo "🚀 Starting Quote Master Pro..."

# Load environment variables
if [ -f .env ]; then
    echo "📋 Loading environment variables..."
    export $(grep -v '^#' .env | xargs)
fi

# Function to check if service is ready
wait_for_service() {
    local service=$1
    local host=$2
    local port=$3
    local timeout=${4:-60}
    
    echo "⏳ Waiting for $service to be ready..."
    
    for i in $(seq 1 $timeout); do
        if nc -z $host $port 2>/dev/null; then
            echo "✅ $service is ready!"
            return 0
        fi
        sleep 1
    done
    
    echo "❌ $service failed to start within $timeout seconds"
    return 1
}

# Start infrastructure services
echo "🔧 Starting infrastructure services..."
docker-compose up -d db redis

# Wait for database
wait_for_service "PostgreSQL" localhost 5432

# Wait for Redis
wait_for_service "Redis" localhost 6379

# Run database migrations
echo "🗄️  Running database migrations..."
docker-compose run --rm api alembic upgrade head

# Start application services
echo "🚀 Starting application services..."
docker-compose up -d

# Wait for API to be ready
wait_for_service "API" localhost 8000

echo "✨ Quote Master Pro is ready!"
echo "🌐 API: http://localhost:8000"
echo "📊 Grafana: http://localhost:3001 (admin/admin)"
echo "📈 Prometheus: http://localhost:9090"
echo "🗄️  Adminer: http://localhost:8080"

# Show service status
echo ""
echo "📋 Service Status:"
docker-compose ps