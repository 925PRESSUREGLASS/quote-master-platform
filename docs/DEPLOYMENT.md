# Quote Master Pro - Deployment Guide

## 📋 Table of Contents

- [🚀 Quick Deployment](#-quick-deployment)
- [🐳 Docker Deployment](#-docker-deployment)
- [☁️ Cloud Deployment](#️-cloud-deployment)
- [🔧 Environment Configuration](#-environment-configuration)
- [📊 Monitoring Setup](#-monitoring-setup)
- [🔄 CI/CD Pipeline](#-cicd-pipeline)
- [🔐 Security Configuration](#-security-configuration)
- [📈 Scaling Strategy](#-scaling-strategy)
- [🆘 Troubleshooting](#-troubleshooting)

---

## 🚀 Quick Deployment

### **Prerequisites**

- Docker 20.10+
- Docker Compose 2.0+
- 2GB+ RAM available
- Valid AI service API keys (OpenAI, Anthropic)

### **One-Command Deployment**

```bash
# Clone repository
git clone https://github.com/925PRESSUREGLASS/quote-master-platform.git
cd quote-master-platform

# Quick production deployment
make deploy-quick

# Or manual steps:
cp .env.example .env
# Edit .env with your API keys
docker-compose -f docker-compose.prod.yml up -d
```

### **Verify Deployment**

```bash
# Check service health
curl http://localhost:8000/health

# Check monitoring
open http://localhost:3001  # Grafana (admin/admin)

# Check API documentation
open http://localhost:8000/docs
```

---

## 🐳 Docker Deployment

### **Development Environment**

```bash
# Start development stack
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

**Services Started:**
- **API**: FastAPI server (port 8000)
- **Database**: PostgreSQL (port 5432)
- **Cache**: Redis (port 6379)
- **Frontend**: React dev server (port 3000)

### **Production Environment**

```bash
# Build production images
docker-compose -f docker-compose.prod.yml build

# Start production stack
docker-compose -f docker-compose.prod.yml up -d

# Include monitoring
docker-compose -f docker-compose.prod.yml -f docker-compose.monitoring.yml up -d
```

**Production Services:**
- **API**: Production FastAPI (port 8000)
- **Database**: PostgreSQL with persistent volumes
- **Cache**: Redis cluster
- **Frontend**: Nginx serving built React app
- **Monitoring**: Prometheus, Grafana, Jaeger

### **Docker Compose Files**

#### **docker-compose.yml** (Development)
```yaml
version: '3.8'
services:
  api:
    build:
      context: .
      dockerfile: Dockerfile.dev
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=development
      - DATABASE_URL=postgresql://postgres:password@db:5432/quote_master_pro
      - REDIS_URL=redis://redis:6379/0
    volumes:
      - .:/app
    depends_on:
      - db
      - redis

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.dev
    ports:
      - "3000:3000"
    volumes:
      - ./frontend:/app
      - /app/node_modules

  db:
    image: postgres:15
    environment:
      POSTGRES_DB: quote_master_pro
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

#### **docker-compose.prod.yml** (Production)
```yaml
version: '3.8'
services:
  api:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=production
      - DATABASE_URL=postgresql://postgres:${DB_PASSWORD}@db:5432/quote_master_pro
      - REDIS_URL=redis://redis:6379/0
    env_file:
      - .env.production
    depends_on:
      - db
      - redis
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "80:80"
      - "443:443"
    depends_on:
      - api
    restart: unless-stopped

  db:
    image: postgres:15
    environment:
      POSTGRES_DB: quote_master_pro
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./scripts/init-db.sql:/docker-entrypoint-initdb.d/init-db.sql
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
```

### **Dockerfile** (Production)
```dockerfile
# Multi-stage build for production
FROM python:3.11-slim as builder

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt requirements/
RUN pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY src/ ./src/
COPY alembic/ ./alembic/
COPY alembic.ini ./
COPY scripts/ ./scripts/

# Create non-root user
RUN useradd --create-home --shell /bin/bash app
USER app

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start application
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## ☁️ Cloud Deployment

### **AWS Deployment**

#### **ECS with Fargate**
```bash
# Build and push images to ECR
aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin 123456789012.dkr.ecr.us-west-2.amazonaws.com

docker build -t quote-master-api .
docker tag quote-master-api:latest 123456789012.dkr.ecr.us-west-2.amazonaws.com/quote-master-api:latest
docker push 123456789012.dkr.ecr.us-west-2.amazonaws.com/quote-master-api:latest

# Deploy with ECS CLI or CloudFormation
ecs-cli up --cluster quote-master-cluster
ecs-cli compose --project-name quote-master service up
```

#### **Terraform Configuration**
```hcl
# infrastructure/terraform/main.tf
provider "aws" {
  region = var.aws_region
}

module "vpc" {
  source = "terraform-aws-modules/vpc/aws"
  name = "quote-master-vpc"

  cidr = "10.0.0.0/16"
  azs = ["us-west-2a", "us-west-2b"]
  public_subnets = ["10.0.1.0/24", "10.0.2.0/24"]
  private_subnets = ["10.0.11.0/24", "10.0.12.0/24"]

  enable_nat_gateway = true
  enable_vpn_gateway = false
}

module "ecs" {
  source = "terraform-aws-modules/ecs/aws"

  cluster_name = "quote-master-cluster"
  capacity_providers = ["FARGATE", "FARGATE_SPOT"]
}

module "rds" {
  source = "terraform-aws-modules/rds/aws"

  identifier = "quote-master-db"
  engine = "postgres"
  engine_version = "15.4"
  instance_class = "db.t3.micro"
  allocated_storage = 20

  name = "quote_master_pro"
  username = var.db_username
  password = var.db_password

  vpc_security_group_ids = [module.security_group.security_group_id]
  subnet_ids = module.vpc.database_subnets
}
```

### **Google Cloud Platform (GCP)**

#### **Cloud Run Deployment**
```bash
# Build and push to Container Registry
gcloud builds submit --tag gcr.io/PROJECT_ID/quote-master-api

# Deploy to Cloud Run
gcloud run deploy quote-master-api \
  --image gcr.io/PROJECT_ID/quote-master-api \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars ENVIRONMENT=production
```

#### **Kubernetes Engine**
```yaml
# kubernetes/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: quote-master-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: quote-master-api
  template:
    metadata:
      labels:
        app: quote-master-api
    spec:
      containers:
      - name: api
        image: gcr.io/PROJECT_ID/quote-master-api:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: quote-master-secrets
              key: database-url
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: quote-master-secrets
              key: openai-api-key
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
```

### **Microsoft Azure**

#### **Container Instances**
```bash
# Create resource group
az group create --name quote-master-rg --location eastus

# Deploy container instance
az container create \
  --resource-group quote-master-rg \
  --name quote-master-api \
  --image your-registry.azurecr.io/quote-master-api:latest \
  --dns-name-label quote-master-api \
  --ports 8000 \
  --environment-variables ENVIRONMENT=production
```

---

## 🔧 Environment Configuration

### **Environment Variables**

#### **.env.production**
```bash
# Application
APP_NAME="Quote Master Pro"
ENVIRONMENT=production
SECRET_KEY=your-super-secret-key-change-in-production
DEBUG=False

# Database
DATABASE_URL=postgresql://user:password@db-host:5432/quote_master_pro
DB_PASSWORD=secure-database-password

# Redis
REDIS_URL=redis://redis-host:6379/0
REDIS_PASSWORD=secure-redis-password

# AI Services
OPENAI_API_KEY=sk-your-real-openai-key
ANTHROPIC_API_KEY=sk-ant-your-real-anthropic-key
AZURE_OPENAI_API_KEY=your-azure-key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/

# Security
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
BCRYPT_ROUNDS=12

# Email
EMAIL_HOST=smtp.sendgrid.net
EMAIL_PORT=587
EMAIL_USER=apikey
EMAIL_PASSWORD=your-sendgrid-api-key
EMAIL_FROM="Quote Master Pro <noreply@quotemasterpro.com>"

# Monitoring
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id
NEW_RELIC_LICENSE_KEY=your-new-relic-key

# External Services
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_S3_BUCKET=quote-master-files

# Rate Limiting
RATE_LIMIT_REQUESTS=1000
RATE_LIMIT_WINDOW=3600
```

### **Secrets Management**

#### **Using Docker Secrets**
```bash
# Create secrets
echo "your-db-password" | docker secret create db_password -
echo "your-openai-key" | docker secret create openai_key -

# Reference in compose file
version: '3.8'
services:
  api:
    image: quote-master-api
    secrets:
      - db_password
      - openai_key
    environment:
      - DATABASE_PASSWORD_FILE=/run/secrets/db_password
      - OPENAI_API_KEY_FILE=/run/secrets/openai_key

secrets:
  db_password:
    external: true
  openai_key:
    external: true
```

#### **Using Kubernetes Secrets**
```bash
# Create secret from command line
kubectl create secret generic quote-master-secrets \
  --from-literal=database-url="postgresql://..." \
  --from-literal=openai-api-key="sk-..."

# Or from file
kubectl create secret generic quote-master-secrets \
  --from-env-file=.env.production
```

---

## 📊 Monitoring Setup

### **Prometheus Configuration**

```yaml
# monitoring/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "alerts.yml"

scrape_configs:
  - job_name: 'quote-master-api'
    static_configs:
      - targets: ['api:8000']
    metrics_path: '/metrics'
    scrape_interval: 10s

  - job_name: 'postgres-exporter'
    static_configs:
      - targets: ['postgres-exporter:9187']

  - job_name: 'redis-exporter'
    static_configs:
      - targets: ['redis-exporter:9121']

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093
```

### **Grafana Dashboard Setup**

```bash
# Start monitoring stack
docker-compose -f docker-compose.monitoring.yml up -d

# Access Grafana
open http://localhost:3001
# Login: admin/admin (change on first login)

# Import dashboards
# - Use dashboard ID 1860 for Node Exporter
# - Import custom dashboards from monitoring/grafana/dashboards/
```

### **Alert Rules**

```yaml
# monitoring/prometheus/alerts.yml
groups:
  - name: quote_master_alerts
    rules:
      - alert: APIHighErrorRate
        expr: rate(http_requests_total{status=~"5.*"}[5m]) > 0.1
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "High API error rate"
          description: "Error rate is {{ $value }} requests per second"

      - alert: DatabaseConnectionFailure
        expr: up{job="postgres-exporter"} == 0
        for: 30s
        labels:
          severity: critical
        annotations:
          summary: "Database connection lost"

      - alert: AIServiceHighLatency
        expr: ai_request_duration_seconds{quantile="0.95"} > 10
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "AI service high latency"
          description: "95th percentile latency is {{ $value }}s"
```

---

## 🔄 CI/CD Pipeline

### **GitHub Actions Workflow**

```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements/dev.txt

      - name: Run tests
        run: |
          make test

      - name: Run security scan
        run: |
          bandit -r src/
          safety check

  build:
    needs: test
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Log in to Container Registry
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}

      - name: Build and push Docker image
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}

  deploy:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'

    steps:
      - name: Deploy to production
        uses: appleboy/ssh-action@v1.0.0
        with:
          host: ${{ secrets.PRODUCTION_HOST }}
          username: ${{ secrets.PRODUCTION_USER }}
          key: ${{ secrets.PRODUCTION_SSH_KEY }}
          script: |
            cd /opt/quote-master
            docker-compose pull
            docker-compose up -d
            docker system prune -f
```

### **Deployment Scripts**

#### **scripts/deploy.sh**
```bash
#!/bin/bash
set -e

echo "🚀 Starting deployment..."

# Pull latest changes
git pull origin main

# Build new images
docker-compose -f docker-compose.prod.yml build

# Run database migrations
docker-compose -f docker-compose.prod.yml run --rm api alembic upgrade head

# Deploy with zero downtime
docker-compose -f docker-compose.prod.yml up -d --no-deps --scale api=2 api
sleep 30
docker-compose -f docker-compose.prod.yml up -d --no-deps --scale api=1 api

# Cleanup old images
docker system prune -f

echo "✅ Deployment completed!"
```

### **Blue-Green Deployment**

```bash
#!/bin/bash
# scripts/blue-green-deploy.sh

CURRENT_ENV=$(docker-compose -f docker-compose.prod.yml ps -q api | head -1)
NEW_ENV="blue"

if [[ $CURRENT_ENV == *"blue"* ]]; then
  NEW_ENV="green"
fi

echo "Deploying to $NEW_ENV environment..."

# Start new environment
docker-compose -f docker-compose.$NEW_ENV.yml up -d

# Health check
for i in {1..30}; do
  if curl -f http://localhost:8001/health; then
    echo "Health check passed"
    break
  fi
  sleep 10
done

# Switch traffic
echo "Switching traffic to $NEW_ENV..."
# Update load balancer configuration

# Stop old environment
OLD_ENV=$([[ $NEW_ENV == "blue" ]] && echo "green" || echo "blue")
docker-compose -f docker-compose.$OLD_ENV.yml down

echo "Deployment completed!"
```

---

## 🔐 Security Configuration

### **SSL/TLS Configuration**

#### **Nginx SSL Configuration**
```nginx
# nginx/ssl.conf
server {
    listen 443 ssl http2;
    server_name api.quotemasterpro.com;

    ssl_certificate /etc/letsencrypt/live/quotemasterpro.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/quotemasterpro.com/privkey.pem;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    ssl_prefer_server_ciphers off;
    ssl_dhparam /etc/nginx/dhparam.pem;

    location / {
        proxy_pass http://api:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

#### **Let's Encrypt Setup**
```bash
# Install Certbot
curl -L https://dl.eff.org/certbot-auto -o certbot-auto
chmod +x certbot-auto

# Get certificate
./certbot-auto certonly --webroot \
  -w /var/www/html \
  -d quotemasterpro.com \
  -d api.quotemasterpro.com

# Auto-renewal
echo "0 12 * * * /path/to/certbot-auto renew --quiet" | crontab -
```

### **Firewall Configuration**

```bash
# UFW Firewall setup
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable

# Allow specific IPs for admin access
ufw allow from 192.168.1.100 to any port 22
```

### **Security Headers**

```python
# src/api/middleware/security.py
from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)

        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        return response
```

---

## 📈 Scaling Strategy

### **Horizontal Scaling**

#### **Docker Swarm**
```bash
# Initialize swarm
docker swarm init

# Create service
docker service create \
  --name quote-master-api \
  --replicas 3 \
  --publish 8000:8000 \
  quote-master-api:latest

# Scale service
docker service scale quote-master-api=5
```

#### **Kubernetes Horizontal Pod Autoscaler**
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: quote-master-api-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: quote-master-api
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### **Database Scaling**

#### **Read Replicas**
```yaml
# docker-compose.prod.yml
services:
  db-primary:
    image: postgres:15
    environment:
      POSTGRES_REPLICATION_MODE: master
      POSTGRES_REPLICATION_USER: replicator
      POSTGRES_REPLICATION_PASSWORD: replica_password

  db-replica:
    image: postgres:15
    environment:
      POSTGRES_REPLICATION_MODE: slave
      POSTGRES_REPLICATION_USER: replicator
      POSTGRES_REPLICATION_PASSWORD: replica_password
      POSTGRES_MASTER_HOST: db-primary
```

### **Load Balancing**

#### **HAProxy Configuration**
```
# haproxy.cfg
global
    daemon
    maxconn 4096

defaults
    mode http
    timeout connect 5000ms
    timeout client 50000ms
    timeout server 50000ms

frontend quote_master_frontend
    bind *:80
    default_backend quote_master_backend

backend quote_master_backend
    balance roundrobin
    option httpchk GET /health
    server api1 api1:8000 check
    server api2 api2:8000 check
    server api3 api3:8000 check
```

---

## 🆘 Troubleshooting

### **Common Issues**

#### **Database Connection Issues**
```bash
# Check database connectivity
docker-compose exec api python -c "
from src.core.database import check_db_health
print('DB Health:', check_db_health())
"

# Check database logs
docker-compose logs db

# Reset database
docker-compose down
docker volume rm quote-master-platform_postgres_data
docker-compose up -d
```

#### **AI Service Failures**
```bash
# Check AI service status
curl http://localhost:8000/api/v1/quotes/ai-service/health

# Reset circuit breakers
curl -X POST http://localhost:8000/api/v1/quotes/ai-service/circuit-breaker/reset/openai

# Check logs
docker-compose logs api | grep -i "ai_service"
```

#### **Memory Issues**
```bash
# Check memory usage
docker stats

# Increase memory limits
# Edit docker-compose.yml:
services:
  api:
    deploy:
      resources:
        limits:
          memory: 2G
```

### **Performance Issues**

```bash
# Profile API endpoints
docker-compose exec api python -m cProfile -s tottime -o profile.stats src/api/main.py

# Check database performance
docker-compose exec db psql -U postgres -d quote_master_pro -c "
SELECT query, mean_time, calls
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;
"
```

### **Monitoring Alerts**

```bash
# Check Prometheus targets
curl http://localhost:9090/api/v1/targets

# Test alert rules
curl -X POST http://localhost:9093/api/v1/alerts

# View Grafana logs
docker-compose logs grafana
```

### **Backup and Recovery**

```bash
# Database backup
docker-compose exec db pg_dump -U postgres quote_master_pro > backup.sql

# Database restore
docker-compose exec -T db psql -U postgres quote_master_pro < backup.sql

# Full system backup
docker-compose down
tar -czf quote-master-backup-$(date +%Y%m%d).tar.gz \
  --exclude=node_modules \
  --exclude=.git \
  .
```

---

This comprehensive deployment guide covers all aspects of deploying Quote Master Pro from development to production, including security, monitoring, scaling, and troubleshooting. Choose the deployment method that best fits your infrastructure and requirements.
