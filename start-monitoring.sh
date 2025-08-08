#!/bin/bash

# Start OpenTelemetry Monitoring Stack
# This script starts the OTLP Collector, Jaeger, Prometheus, Grafana, and Redis

echo "🚀 Starting Quote Master Pro Monitoring Stack..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

echo "📦 Starting monitoring services..."

# Start the monitoring stack
docker-compose -f docker-compose.monitoring.yml up -d

# Wait for services to start
echo "⏳ Waiting for services to initialize..."
sleep 10

echo "🎯 Monitoring Stack Status:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check service status
services=("quote-master-otel-collector" "quote-master-jaeger" "quote-master-prometheus" "quote-master-grafana" "quote-master-redis")

for service in "${services[@]}"; do
    if docker ps --filter "name=$service" --filter "status=running" | grep -q "$service"; then
        echo "✅ $service: Running"
    else
        echo "❌ $service: Not running"
    fi
done

echo ""
echo "🌐 Service URLs:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 Grafana Dashboard:    http://localhost:3001 (admin/admin123)"
echo "🔍 Jaeger Tracing UI:    http://localhost:16686"
echo "📈 Prometheus:           http://localhost:9090" 
echo "🔧 OTLP Collector:       http://localhost:55680 (zpages)"
echo "🗄️  Redis:                localhost:6379"
echo ""
echo "📡 OTLP Endpoints:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "gRPC: localhost:4317"
echo "HTTP: localhost:4318"
echo ""

echo "✨ To enable tracing in your app, set:"
echo "export USE_OTLP_COLLECTOR=true"
echo "export OTLP_ENDPOINT=http://localhost:4317"
echo ""

echo "🏁 Monitoring stack is ready!"
echo "Start your Quote Master Pro API and traces will appear in Jaeger."
