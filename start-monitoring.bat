@echo off
REM Start OpenTelemetry Monitoring Stack (Windows version)
REM This script starts the OTLP Collector, Jaeger, Prometheus, Grafana, and Redis

echo 🚀 Starting Quote Master Pro Monitoring Stack...

REM Check if Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker is not running. Please start Docker first.
    exit /b 1
)

echo 📦 Starting monitoring services...

REM Start the monitoring stack
docker-compose -f docker-compose.monitoring.yml up -d

REM Wait for services to start
echo ⏳ Waiting for services to initialize...
timeout /t 10 /nobreak >nul

echo 🎯 Monitoring Stack Status:
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

REM Check service status
for %%s in (quote-master-otel-collector quote-master-jaeger quote-master-prometheus quote-master-grafana quote-master-redis) do (
    docker ps --filter "name=%%s" --filter "status=running" | findstr /C:"%%s" >nul
    if !errorlevel! equ 0 (
        echo ✅ %%s: Running
    ) else (
        echo ❌ %%s: Not running
    )
)

echo.
echo 🌐 Service URLs:
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo 📊 Grafana Dashboard:    http://localhost:3001 (admin/admin123)
echo 🔍 Jaeger Tracing UI:    http://localhost:16686
echo 📈 Prometheus:           http://localhost:9090
echo 🔧 OTLP Collector:       http://localhost:55680 (zpages)
echo 🗄️  Redis:                localhost:6379
echo.
echo 📡 OTLP Endpoints:
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo gRPC: localhost:4317
echo HTTP: localhost:4318
echo.

echo ✨ To enable tracing in your app, set:
echo set USE_OTLP_COLLECTOR=true
echo set OTLP_ENDPOINT=http://localhost:4317
echo.

echo 🏁 Monitoring stack is ready!
echo Start your Quote Master Pro API and traces will appear in Jaeger.

pause
