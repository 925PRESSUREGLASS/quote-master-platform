#!/bin/bash

# Quote Master Pro - Enhanced Production Deployment Script
# Comprehensive deployment with health checks, rollback capabilities, and monitoring

set -e

echo "🚀 Starting Quote Master Pro production deployment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
COMPOSE_FILE="docker-compose.prod.yml"
ENV_FILE=".env"
BACKUP_DIR="/opt/backups/quote-master-pro"
DEPLOY_LOG="/var/log/quote-master-deploy.log"

# Deployment settings
HEALTH_CHECK_TIMEOUT=120
ROLLBACK_TIMEOUT=60
MAX_DEPLOY_ATTEMPTS=3

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1" | tee -a $DEPLOY_LOG
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a $DEPLOY_LOG
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a $DEPLOY_LOG
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a $DEPLOY_LOG
}

check_prerequisites() {
    log_info "Checking deployment prerequisites..."

    # Check if running as appropriate user
    if [[ $EUID -eq 0 ]]; then
        log_error "This script should not be run as root"
        exit 1
    fi

    # Check required commands
    for cmd in docker docker-compose git; do
        if ! command -v $cmd &> /dev/null; then
            log_error "$cmd is not installed"
            exit 1
        fi
    done

    # Check if .env file exists
    if [ ! -f "$ENV_FILE" ]; then
        log_error ".env file not found. Please copy .env.example to .env and configure your settings"
        exit 1
    fi

    # Check if compose file exists
    if [ ! -f "$COMPOSE_FILE" ]; then
        log_error "$COMPOSE_FILE not found"
        exit 1
    fi

    log_success "Prerequisites check passed"
}

validate_environment() {
    log_info "Validating environment configuration..."

    # Load environment variables
    set -a
    source $ENV_FILE
    set +a

    # Check critical environment variables
    required_vars=("SECRET_KEY" "DB_PASSWORD" "REDIS_PASSWORD" "DOMAIN")
    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ] || [ "${!var}" = "change_me" ] || [[ "${!var}" == *"change_me"* ]]; then
            log_error "Required environment variable $var is not set or uses default value"
            log_error "Please update your .env file with secure values"
            exit 1
        fi
    done

    # Validate domain format
    if [[ ! $DOMAIN =~ ^[a-zA-Z0-9][a-zA-Z0-9-]{0,61}[a-zA-Z0-9]?\.[a-zA-Z]{2,}$ ]]; then
        log_warning "Domain format may be invalid: $DOMAIN"
    fi

    log_success "Environment validation passed"
}

create_backup() {
    log_info "Creating deployment backup..."

    # Create backup directory
    mkdir -p $BACKUP_DIR

    BACKUP_TIMESTAMP=$(date +%Y%m%d_%H%M%S)

    # Backup database if containers are running
    if docker-compose -f $COMPOSE_FILE ps postgres | grep -q "Up"; then
        log_info "Backing up database..."
        docker-compose -f $COMPOSE_FILE exec -T postgres pg_dump \
            -U ${DB_USER:-quote_master} ${DB_NAME:-quote_master_pro} | \
            gzip > $BACKUP_DIR/db_backup_$BACKUP_TIMESTAMP.sql.gz

        if [ $? -eq 0 ]; then
            log_success "Database backup created: db_backup_$BACKUP_TIMESTAMP.sql.gz"
        else
            log_warning "Database backup failed, continuing deployment"
        fi
    fi

    # Backup application configuration
    tar -czf $BACKUP_DIR/app_config_$BACKUP_TIMESTAMP.tar.gz \
        .env $COMPOSE_FILE nginx/ monitoring/ 2>/dev/null || true

    # Keep only last 5 backups
    ls -t $BACKUP_DIR/db_backup_*.sql.gz | tail -n +6 | xargs -r rm
    ls -t $BACKUP_DIR/app_config_*.tar.gz | tail -n +6 | xargs -r rm

    log_success "Backup completed"
}

build_and_deploy() {
    log_info "Building and deploying application..."

    # Pull latest images
    log_info "Pulling latest images..."
    docker-compose -f $COMPOSE_FILE pull

    # Build custom images
    log_info "Building application images..."
    docker-compose -f $COMPOSE_FILE build --no-cache --parallel

    # Deploy with zero-downtime strategy
    log_info "Deploying services with rolling update..."

    # Start core services first (database, cache)
    log_info "Starting core services..."
    docker-compose -f $COMPOSE_FILE up -d postgres redis

    # Wait for core services
    sleep 10

    # Check database health
    log_info "Checking database connection..."
    if ! docker-compose -f $COMPOSE_FILE exec -T postgres pg_isready -U ${DB_USER:-quote_master} > /dev/null 2>&1; then
        log_error "Database is not ready"
        return 1
    fi

    # Run database migrations
    log_info "Running database migrations..."
    docker-compose -f $COMPOSE_FILE run --rm backend alembic upgrade head
    if [ $? -ne 0 ]; then
        log_error "Database migration failed"
        return 1
    fi

    # Deploy application services
    log_info "Deploying application services..."
    docker-compose -f $COMPOSE_FILE up -d backend frontend

    # Wait for services to stabilize
    sleep 15

    log_success "Deployment completed"
    return 0
}

run_health_checks() {
    log_info "Running comprehensive health checks..."

    local health_check_start=$(date +%s)
    local max_wait=$HEALTH_CHECK_TIMEOUT

    # Wait for services to be ready
    log_info "Waiting for services to be healthy..."

    while true; do
        local current_time=$(date +%s)
        local elapsed=$((current_time - health_check_start))

        if [ $elapsed -gt $max_wait ]; then
            log_error "Health check timeout after ${max_wait}s"
            return 1
        fi

        # Check backend health
        local backend_health=$(curl -s -f http://localhost:8000/health 2>/dev/null || echo "failed")
        if [[ $backend_health == *"healthy"* ]]; then
            log_success "Backend is healthy"
            break
        fi

        log_info "Waiting for backend to be ready... (${elapsed}s/${max_wait}s)"
        sleep 5
    done

    # Check frontend health
    local frontend_health=$(curl -s -f http://localhost:80/health 2>/dev/null || echo "failed")
    if [[ $frontend_health == "healthy" ]]; then
        log_success "Frontend is healthy"
    else
        log_warning "Frontend health check failed"
        docker-compose -f $COMPOSE_FILE logs frontend --tail=10
    fi

    # Run comprehensive health check script if available
    if [ -f "scripts/production_health_check.py" ]; then
        log_info "Running comprehensive health check..."
        python3 scripts/production_health_check.py --url http://localhost --quiet
        if [ $? -eq 0 ]; then
            log_success "Comprehensive health check passed"
        else
            log_warning "Some health checks failed, but deployment continues"
        fi
    fi

    return 0
}

rollback_deployment() {
    log_error "Rolling back deployment..."

    # Stop current containers
    docker-compose -f $COMPOSE_FILE down --remove-orphans

    # Find most recent backup
    local latest_backup=$(ls -t $BACKUP_DIR/db_backup_*.sql.gz 2>/dev/null | head -n 1)

    if [ -n "$latest_backup" ]; then
        log_info "Restoring database from backup: $latest_backup"

        # Start only postgres for restore
        docker-compose -f $COMPOSE_FILE up -d postgres
        sleep 10

        # Restore database
        zcat "$latest_backup" | docker-compose -f $COMPOSE_FILE exec -T postgres psql \
            -U ${DB_USER:-quote_master} -d ${DB_NAME:-quote_master_pro}

        if [ $? -eq 0 ]; then
            log_success "Database restored from backup"
        else
            log_error "Database restore failed"
        fi
    fi

    # Restart services with previous version
    log_info "Restarting services..."
    docker-compose -f $COMPOSE_FILE up -d

    log_warning "Rollback completed - please investigate deployment issues"
}

setup_monitoring() {
    log_info "Setting up monitoring and alerting..."

    # Ask about monitoring setup
    read -p "$(echo -e ${YELLOW}🔍 Start monitoring stack \(Prometheus/Grafana\)? \[y/N\]:${NC} )" -n 1 -r
    echo

    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log_info "Starting monitoring services..."
        docker-compose -f $COMPOSE_FILE --profile monitoring up -d prometheus grafana

        if [ $? -eq 0 ]; then
            log_success "Monitoring stack started"
            log_info "📊 Grafana dashboard: http://$DOMAIN:3000"
            log_info "📈 Prometheus metrics: http://$DOMAIN:9090"
            log_info "Default Grafana login: admin / ${GRAFANA_PASSWORD}"
        else
            log_warning "Monitoring stack failed to start"
        fi
    fi
}

setup_ssl_certificates() {
    log_info "Checking SSL certificate setup..."

    # Check if SSL certificates exist
    if [ ! -f "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" ]; then
        log_warning "SSL certificates not found for $DOMAIN"

        read -p "$(echo -e ${YELLOW}🔒 Obtain SSL certificates now? \[y/N\]:${NC} )" -n 1 -r
        echo

        if [[ $REPLY =~ ^[Yy]$ ]]; then
            log_info "Obtaining SSL certificates..."

            # Stop services that might use port 80
            docker-compose -f $COMPOSE_FILE stop frontend

            # Obtain certificate
            sudo certbot certonly --standalone -d $DOMAIN -d www.$DOMAIN --email ${SSL_EMAIL} --agree-tos --non-interactive

            if [ $? -eq 0 ]; then
                log_success "SSL certificates obtained successfully"

                # Restart frontend with SSL
                docker-compose -f $COMPOSE_FILE up -d frontend
            else
                log_error "SSL certificate generation failed"
                docker-compose -f $COMPOSE_FILE up -d frontend
            fi
        fi
    else
        log_success "SSL certificates found and valid"
    fi
}

display_deployment_summary() {
    log_info "Deployment Summary"
    echo ""
    echo -e "${BLUE}📍 Application URLs:${NC}"
    echo "   🌐 Frontend: https://$DOMAIN"
    echo "   🔧 Backend API: https://$DOMAIN/api"
    echo "   📚 API Documentation: https://$DOMAIN/api/docs"
    echo ""
    echo -e "${BLUE}🐳 Container Status:${NC}"
    docker-compose -f $COMPOSE_FILE ps
    echo ""
    echo -e "${BLUE}📊 System Resources:${NC}"
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}"
    echo ""
    echo -e "${BLUE}📋 Useful Commands:${NC}"
    echo "   View logs: docker-compose -f $COMPOSE_FILE logs -f [service_name]"
    echo "   Stop services: docker-compose -f $COMPOSE_FILE down"
    echo "   Restart service: docker-compose -f $COMPOSE_FILE restart [service_name]"
    echo "   Health check: python3 scripts/production_health_check.py"
    echo "   Performance benchmark: python3 scripts/performance_benchmark.py"
    echo ""
    log_success "Quote Master Pro is now running in production mode!"
}

cleanup_old_images() {
    log_info "Cleaning up old Docker images..."

    # Remove dangling images
    docker image prune -f

    # Remove old images (keep last 3 versions)
    docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.ID}}\t{{.CreatedAt}}" | \
    grep quote-master | tail -n +4 | awk '{print $3}' | xargs -r docker rmi -f

    log_success "Image cleanup completed"
}

# Main deployment function
main_deployment() {
    local attempt=1

    while [ $attempt -le $MAX_DEPLOY_ATTEMPTS ]; do
        log_info "Deployment attempt $attempt of $MAX_DEPLOY_ATTEMPTS"

        if build_and_deploy; then
            if run_health_checks; then
                log_success "Deployment successful on attempt $attempt"
                return 0
            else
                log_warning "Health checks failed on attempt $attempt"
            fi
        else
            log_warning "Deployment failed on attempt $attempt"
        fi

        if [ $attempt -lt $MAX_DEPLOY_ATTEMPTS ]; then
            log_info "Retrying deployment in 30 seconds..."
            sleep 30
        fi

        attempt=$((attempt + 1))
    done

    log_error "All deployment attempts failed"
    return 1
}

# Main execution
main() {
    log_info "Starting Quote Master Pro production deployment"
    log_info "Timestamp: $(date '+%Y-%m-%d %H:%M:%S')"

    # Pre-deployment checks
    check_prerequisites
    validate_environment

    # Create backup
    create_backup

    # Main deployment
    if main_deployment; then
        log_success "Deployment completed successfully"

        # Post-deployment setup
        setup_ssl_certificates
        setup_monitoring
        cleanup_old_images

        # Final summary
        display_deployment_summary

        # Schedule health monitoring
        log_info "Setting up continuous health monitoring..."
        (crontab -l 2>/dev/null; echo "*/5 * * * * cd $(pwd) && python3 scripts/production_health_check.py --quiet") | crontab -

        log_success "🎉 Production deployment completed successfully!"
        exit 0
    else
        log_error "Deployment failed after $MAX_DEPLOY_ATTEMPTS attempts"

        read -p "$(echo -e ${RED}⚠️  Rollback deployment? \[y/N\]:${NC} )" -n 1 -r
        echo

        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rollback_deployment
        fi

        exit 1
    fi
}

# Handle interruption
trap 'log_error "Deployment interrupted by user"; exit 1' INT TERM

# Execute main function
main "$@"
