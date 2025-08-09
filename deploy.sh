#!/bin/bash

# Quote Master Pro - Production Deployment Script
set -e

echo "🚀 Starting Quote Master Pro deployment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
COMPOSE_FILE="docker-compose.prod.yml"
ENV_FILE=".env"

# Check if .env file exists
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}❌ .env file not found!${NC}"
    echo -e "${YELLOW}📝 Please copy .env.example to .env and configure your settings${NC}"
    exit 1
fi

# Load environment variables
set -a
source $ENV_FILE
set +a

echo -e "${BLUE}📋 Deployment Configuration:${NC}"
echo "   Domain: ${DOMAIN:-localhost}"
echo "   Database: ${DB_NAME:-quote_master_pro}"
echo "   Environment: production"

# Check if required environment variables are set
required_vars=("SECRET_KEY" "DB_PASSWORD" "REDIS_PASSWORD")
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ] || [ "${!var}" = "change_me" ] || [[ "${!var}" == *"change_me"* ]]; then
        echo -e "${RED}❌ Required environment variable $var is not set or uses default value${NC}"
        echo -e "${YELLOW}📝 Please update your .env file with secure values${NC}"
        exit 1
    fi
done

# Create necessary directories
echo -e "${BLUE}📁 Creating directories...${NC}"
mkdir -p logs
mkdir -p data/postgres
mkdir -p data/redis
mkdir -p data/grafana

# Build and start services
echo -e "${BLUE}🔨 Building and starting services...${NC}"

# Stop existing containers
echo "   Stopping existing containers..."
docker-compose -f $COMPOSE_FILE down --remove-orphans

# Pull latest images
echo "   Pulling latest images..."
docker-compose -f $COMPOSE_FILE pull

# Build custom images
echo "   Building application images..."
docker-compose -f $COMPOSE_FILE build --no-cache

# Start core services first
echo "   Starting database and cache..."
docker-compose -f $COMPOSE_FILE up -d postgres redis

# Wait for services to be healthy
echo "   Waiting for services to be ready..."
sleep 10

# Check database health
echo "   Checking database connection..."
if ! docker-compose -f $COMPOSE_FILE exec -T postgres pg_isready -U $DB_USER > /dev/null 2>&1; then
    echo -e "${RED}❌ Database is not ready${NC}"
    exit 1
fi

# Run database migrations
echo "   Running database migrations..."
docker-compose -f $COMPOSE_FILE run --rm backend alembic upgrade head

# Start application services
echo "   Starting application services..."
docker-compose -f $COMPOSE_FILE up -d backend frontend

# Wait for application to be ready
echo "   Waiting for application to start..."
sleep 15

# Health checks
echo -e "${BLUE}🏥 Running health checks...${NC}"

# Check backend health
backend_health=$(curl -s -f http://localhost:8000/health 2>/dev/null || echo "failed")
if [[ $backend_health == *"healthy"* ]]; then
    echo -e "${GREEN}✅ Backend is healthy${NC}"
else
    echo -e "${RED}❌ Backend health check failed${NC}"
    docker-compose -f $COMPOSE_FILE logs backend --tail=20
    exit 1
fi

# Check frontend health
frontend_health=$(curl -s -f http://localhost:80/health 2>/dev/null || echo "failed")
if [[ $frontend_health == "healthy" ]]; then
    echo -e "${GREEN}✅ Frontend is healthy${NC}"
else
    echo -e "${RED}❌ Frontend health check failed${NC}"
    docker-compose -f $COMPOSE_FILE logs frontend --tail=20
    exit 1
fi

# Optional: Start monitoring stack
read -p "$(echo -e ${YELLOW}🔍 Start monitoring stack \(Prometheus/Grafana\)? \[y/N\]:${NC} )" -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "   Starting monitoring services..."
    docker-compose -f $COMPOSE_FILE --profile monitoring up -d prometheus grafana
    echo -e "${GREEN}📊 Grafana dashboard available at: http://localhost:3000${NC}"
    echo "   Default login: admin / ${GRAFANA_PASSWORD}"
fi

# Display deployment summary
echo -e "${GREEN}🎉 Deployment completed successfully!${NC}"
echo ""
echo -e "${BLUE}📍 Application URLs:${NC}"
echo "   🌐 Frontend: http://localhost (or http://${DOMAIN})"
echo "   🔧 Backend API: http://localhost/api (or http://${DOMAIN}/api)"
echo "   📚 API Documentation: http://localhost/api/docs"
echo ""
echo -e "${BLUE}🐳 Container Status:${NC}"
docker-compose -f $COMPOSE_FILE ps

echo ""
echo -e "${BLUE}📋 Useful Commands:${NC}"
echo "   View logs: docker-compose -f $COMPOSE_FILE logs -f [service_name]"
echo "   Stop services: docker-compose -f $COMPOSE_FILE down"
echo "   Restart service: docker-compose -f $COMPOSE_FILE restart [service_name]"
echo "   Database shell: docker-compose -f $COMPOSE_FILE exec postgres psql -U $DB_USER -d $DB_NAME"
echo ""
echo -e "${GREEN}✅ Quote Master Pro is now running in production mode!${NC}"
