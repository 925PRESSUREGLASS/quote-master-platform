# Quote Master Pro - Production Deployment Guide

## Prerequisites

### System Requirements
- **Server**: 4+ CPU cores, 8GB+ RAM, 50GB+ storage
- **OS**: Ubuntu 20.04+ or CentOS 8+
- **Docker**: Version 20.10+
- **Docker Compose**: Version 2.0+
- **Domain**: SSL-ready domain name

### Required Services
- **PostgreSQL**: Production database
- **Redis**: Caching and session storage
- **Nginx**: Reverse proxy and SSL termination
- **Let's Encrypt**: SSL certificates

## Step 1: Server Setup

### 1.1 Install Docker and Docker Compose
```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### 1.2 Configure Firewall
```bash
# Ubuntu UFW
sudo ufw allow 22      # SSH
sudo ufw allow 80      # HTTP
sudo ufw allow 443     # HTTPS
sudo ufw enable

# CentOS/RHEL
sudo firewall-cmd --permanent --add-service=ssh
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

### 1.3 Create Application Directory
```bash
sudo mkdir -p /opt/quote-master-pro
sudo chown $USER:$USER /opt/quote-master-pro
cd /opt/quote-master-pro
```

## Step 2: Code Deployment

### 2.1 Clone Repository
```bash
git clone https://github.com/your-org/quote-master-pro.git .
```

### 2.2 Configure Environment Variables
```bash
# Copy and customize environment file
cp env.example .env

# Edit with your production values
nano .env
```

**Critical Environment Variables:**
```bash
# Database
DB_USER=quote_master
DB_PASSWORD=your_secure_db_password_here
DB_NAME=quote_master_pro

# Redis
REDIS_PASSWORD=your_secure_redis_password_here

# Security
SECRET_KEY=your_64_character_secret_key_here
ACCESS_TOKEN_EXPIRE_MINUTES=30

# AI Services
OPENAI_API_KEY=your_openai_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here

# Domain
DOMAIN=your-domain.com
CORS_ORIGINS=https://your-domain.com,https://www.your-domain.com

# SSL
SSL_EMAIL=admin@your-domain.com

# Monitoring
GRAFANA_USER=admin
GRAFANA_PASSWORD=your_secure_grafana_password_here
```

## Step 3: SSL Certificate Setup

### 3.1 Install Certbot
```bash
# Ubuntu
sudo apt update
sudo apt install certbot python3-certbot-nginx

# CentOS
sudo yum install certbot python3-certbot-nginx
```

### 3.2 Obtain SSL Certificate
```bash
sudo certbot certonly --standalone -d your-domain.com -d www.your-domain.com
```

### 3.3 Configure SSL Renewal
```bash
# Test renewal
sudo certbot renew --dry-run

# Add to cron
echo "0 12 * * * /usr/bin/certbot renew --quiet" | sudo crontab -
```

## Step 4: Production Deployment

### 4.1 Build and Deploy
```bash
# Make deployment script executable
chmod +x deploy.sh

# Run production deployment
./deploy.sh
```

### 4.2 Verify Deployment
```bash
# Check container status
docker-compose -f docker-compose.prod.yml ps

# Check logs
docker-compose -f docker-compose.prod.yml logs -f

# Test health endpoints
curl https://your-domain.com/health
curl https://your-domain.com/api/health
```

## Step 5: Monitoring Setup

### 5.1 Start Monitoring Stack
```bash
# Start with monitoring profile
docker-compose -f docker-compose.prod.yml --profile monitoring up -d
```

### 5.2 Configure Grafana
1. Access: `https://your-domain.com:3000`
2. Login: admin / your_grafana_password
3. Add Prometheus data source: `http://prometheus:9090`
4. Import dashboards from `monitoring/grafana/dashboards/`

### 5.3 Set Up Alerts
```bash
# Configure email alerts in Grafana
# Set up Slack/Discord webhooks if needed
# Configure Prometheus alerting rules
```

## Step 6: Backup Configuration

### 6.1 Database Backup
```bash
# Create backup script
cat > /opt/quote-master-pro/backup-db.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/opt/backups/quote-master-pro"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

docker-compose -f docker-compose.prod.yml exec -T postgres pg_dump \
  -U quote_master quote_master_pro | gzip > $BACKUP_DIR/db_backup_$DATE.sql.gz

# Keep only last 7 days
find $BACKUP_DIR -name "db_backup_*.sql.gz" -mtime +7 -delete
EOF

chmod +x /opt/quote-master-pro/backup-db.sh

# Add to cron (daily at 2 AM)
echo "0 2 * * * /opt/quote-master-pro/backup-db.sh" | crontab -
```

### 6.2 Application Backup
```bash
# Backup application data and config
cat > /opt/quote-master-pro/backup-app.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/opt/backups/quote-master-pro"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup environment and configs
tar -czf $BACKUP_DIR/app_config_$DATE.tar.gz \
  .env docker-compose.prod.yml nginx/ monitoring/

# Keep only last 30 days
find $BACKUP_DIR -name "app_config_*.tar.gz" -mtime +30 -delete
EOF

chmod +x /opt/quote-master-pro/backup-app.sh
```

## Step 7: Security Hardening

### 7.1 Network Security
```bash
# Create custom Docker network with restricted access
docker network create --driver bridge --subnet=172.20.0.0/16 quote-master-secure

# Update docker-compose.prod.yml to use custom network
```

### 7.2 Container Security
```bash
# Run containers as non-root user
# Implement resource limits
# Use security scanning
docker scan quote-master-backend:latest
```

### 7.3 System Security
```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Configure fail2ban
sudo apt install fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban

# Disable root SSH
sudo sed -i 's/PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config
sudo systemctl restart ssh
```

## Step 8: Performance Optimization

### 8.1 System Tuning
```bash
# Optimize system parameters
echo 'vm.swappiness=10' | sudo tee -a /etc/sysctl.conf
echo 'net.core.rmem_max=16777216' | sudo tee -a /etc/sysctl.conf
echo 'net.core.wmem_max=16777216' | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
```

### 8.2 Database Optimization
```bash
# PostgreSQL tuning in docker-compose.prod.yml
# Increase shared_buffers, work_mem, maintenance_work_mem
# Enable query optimization
```

### 8.3 Nginx Optimization
```bash
# Configure Nginx for high performance
# Enable gzip compression
# Set up proper caching headers
# Implement rate limiting
```

## Step 9: Maintenance Procedures

### 9.1 Regular Updates
```bash
# Weekly update script
cat > /opt/quote-master-pro/update.sh << 'EOF'
#!/bin/bash
cd /opt/quote-master-pro

# Backup before update
./backup-db.sh
./backup-app.sh

# Pull latest changes
git pull origin main

# Rebuild and redeploy
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d --build

# Health check
sleep 30
curl -f https://your-domain.com/health || echo "Health check failed!"
EOF

chmod +x /opt/quote-master-pro/update.sh
```

### 9.2 Log Management
```bash
# Configure log rotation
sudo tee /etc/logrotate.d/quote-master-pro << 'EOF'
/opt/quote-master-pro/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    copytruncate
}
EOF
```

### 9.3 Performance Monitoring
```bash
# Weekly performance report
cat > /opt/quote-master-pro/performance-report.sh << 'EOF'
#!/bin/bash
cd /opt/quote-master-pro

# Run performance benchmark
python scripts/performance_benchmark.py --url https://your-domain.com

# Email results to admin
# mail -s "Quote Master Pro Performance Report" admin@your-domain.com < benchmark_results.json
EOF

chmod +x /opt/quote-master-pro/performance-report.sh
```

## Step 10: Troubleshooting

### 10.1 Common Issues

**Container Won't Start:**
```bash
docker-compose -f docker-compose.prod.yml logs [service_name]
docker system prune -a
```

**Database Connection Issues:**
```bash
docker-compose -f docker-compose.prod.yml exec postgres psql -U quote_master -d quote_master_pro
```

**SSL Certificate Issues:**
```bash
sudo certbot renew
sudo systemctl restart nginx
```

**Performance Issues:**
```bash
# Check resource usage
docker stats
htop

# Check database performance
docker-compose -f docker-compose.prod.yml exec postgres pg_stat_activity
```

### 10.2 Emergency Procedures

**System Recovery:**
```bash
# Stop all services
docker-compose -f docker-compose.prod.yml down

# Restore from backup
# [Restore procedures based on backup type]

# Restart services
./deploy.sh
```

## Step 11: Production Checklist

### Pre-Launch Verification
- [ ] SSL certificates installed and valid
- [ ] Environment variables configured securely
- [ ] Database migrations completed
- [ ] All services healthy and responding
- [ ] Monitoring dashboards accessible
- [ ] Backup procedures tested
- [ ] Performance benchmarks within targets
- [ ] Security scan completed
- [ ] Load testing passed
- [ ] Documentation updated

### Post-Launch Monitoring
- [ ] Monitor error rates and response times
- [ ] Verify backup procedures running
- [ ] Check resource usage trends
- [ ] Monitor SSL certificate expiration
- [ ] Review security logs
- [ ] Update dependencies regularly

## Support and Maintenance

### 24/7 Monitoring
- **Uptime Monitoring**: UptimeRobot, Pingdom
- **Application Monitoring**: Grafana dashboards
- **Log Monitoring**: ELK stack or similar
- **Error Tracking**: Sentry integration

### Emergency Contacts
- **System Administrator**: [Your contact info]
- **Database Administrator**: [DBA contact info]
- **Development Team**: [Dev team contact]
- **Hosting Provider**: [Provider support info]

## Performance Targets

### Service Level Objectives (SLOs)
- **Uptime**: 99.9% (8.77 hours downtime/year)
- **Response Time**: 95% of requests under 500ms
- **Error Rate**: Less than 0.1%
- **Database Query Time**: 95% under 100ms

### Scaling Triggers
- **CPU Usage**: Scale up when >80% for 5 minutes
- **Memory Usage**: Scale up when >85% for 5 minutes
- **Response Time**: Scale up when >1s for 95th percentile
- **Connection Pool**: Scale up when >80% utilization

---

**Deployment Complete! 🚀**

Your Quote Master Pro application is now ready for production use with enterprise-grade reliability, security, and performance.
