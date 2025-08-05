#!/bin/bash

# Quote Master Pro - Development Environment Setup

set -e

echo "🛠️  Setting up Quote Master Pro development environment..."

# Load environment variables
if [ -f .env.dev ]; then
    echo "📋 Loading development environment variables..."
    export $(grep -v '^#' .env.dev | xargs)
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

# Start development infrastructure
echo "🔧 Starting development infrastructure..."
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d db redis

# Wait for services
wait_for_service "PostgreSQL" localhost 5432
wait_for_service "Redis" localhost 6379

# Run database migrations
echo "🗄️  Running database migrations..."
docker-compose -f docker-compose.yml -f docker-compose.dev.yml run --rm api alembic upgrade head

# Start development services
echo "🚀 Starting development services..."
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# Start development tools (optional)
echo "🛠️  Starting development tools..."
docker-compose -f docker-compose.yml -f docker-compose.dev.yml --profile dev-tools up -d

# Wait for API
wait_for_service "API" localhost 8000

echo "✨ Development environment is ready!"
echo ""
echo "🌐 API: http://localhost:8000"
echo "📖 API Docs: http://localhost:8000/docs"
echo "🗄️  Adminer: http://localhost:8080"
echo "🔧 Redis Commander: http://localhost:8081"
echo ""
echo "📋 Development Service Status:"
docker-compose -f docker-compose.yml -f docker-compose.dev.yml ps

echo ""
echo "💡 Development Tips:"
echo "   - API auto-reloads on code changes"
echo "   - Use 'docker-compose logs -f api' to view API logs"
echo "   - Use 'docker-compose logs -f worker' to view worker logs"
echo "   - Frontend runs separately with 'npm run dev' in ./frontend/"