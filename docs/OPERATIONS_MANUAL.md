# Operations Manual - API Observability Stack

This manual provides comprehensive operational guidance for deploying, maintaining, and troubleshooting the API HTTP Request Logging Management System in production environments.

## 📋 Table of Contents

1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Deployment Procedures](#deployment-procedures)
3. [Post-Deployment Validation](#post-deployment-validation)
4. [Monitoring and Alerting](#monitoring-and-alerting)
5. [Maintenance Tasks](#maintenance-tasks)
6. [Troubleshooting Guide](#troubleshooting-guide)
7. [Backup and Recovery](#backup-and-recovery)
8. [Performance Optimization](#performance-optimization)
9. [Security Operations](#security-operations)
10. [Capacity Planning](#capacity-planning)

---

## 🚀 Pre-Deployment Checklist

### Infrastructure Requirements
- [ ] **Hardware Resources**
  - [ ] Minimum 8 GB RAM available
  - [ ] Minimum 4 CPU cores
  - [ ] 50 GB free disk space
  - [ ] Network bandwidth: 1 Gbps
  
- [ ] **Software Prerequisites**
  - [ ] Docker Engine 20.10+
  - [ ] Docker Compose 2.0+
  - [ ] curl for health checks
  - [ ] Python 3.8+ for validation scripts

### Network Configuration
- [ ] **Port Availability**
  ```bash
  # Check if required ports are free
  for port in 80 3000 4317 4318 5601 8000 8428 9090 9200 16686; do
    if ss -tuln | grep ":$port " >/dev/null; then
      echo "Port $port is in use"
    else
      echo "Port $port is available"
    fi
  done
  ```

- [ ] **Firewall Rules** (if applicable)
  ```bash
  # Allow inbound traffic on required ports
  sudo ufw allow 80/tcp    # Frontend
  sudo ufw allow 3000/tcp  # Grafana
  sudo ufw allow 16686/tcp # Jaeger UI
  sudo ufw allow 9090/tcp  # Prometheus UI
  sudo ufw allow 5601/tcp  # Kibana UI
  ```

### Security Configuration
- [ ] **Environment Variables**
  ```bash
  # Create secure .env file
  cat > .env << 'EOF'
  GRAFANA_ADMIN_PASSWORD=your-secure-password-here
  ELASTICSEARCH_PASSWORD=your-elasticsearch-password
  OTEL_AUTH_TOKEN=your-collector-auth-token
  ENVIRONMENT=production
  EOF
  chmod 600 .env
  ```

- [ ] **SSL Certificates** (Production)
  - [ ] Valid SSL certificates for Grafana
  - [ ] Valid SSL certificates for external endpoints
  - [ ] Certificate expiration monitoring

---

## 🏗️ Deployment Procedures

### 1. Standard Deployment

#### Single Environment Deployment
```bash
# 1. Clone the repository
git clone <your-repository-url>
cd LOG_manage

# 2. Configure environment
cp .env.example .env
# Edit .env with your specific values

# 3. Start the stack
./start.sh start

# 4. Validate deployment
python3 validate-setup.py
```

#### Multi-Environment Deployment
```bash
# Development
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# Staging
docker-compose -f docker-compose.yml -f docker-compose.staging.yml up -d

# Production
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### 2. Kubernetes Deployment

#### Generate Kubernetes Manifests
```bash
# Convert Docker Compose to Kubernetes
kompose convert -f docker-compose.yml

# Apply to cluster
kubectl apply -f ./k8s-manifests/
```

#### Helm Chart Deployment
```bash
# Create Helm chart
helm create observability-stack

# Install chart
helm install observability ./observability-stack \
  --set environment=production \
  --set grafana.adminPassword=your-password
```

### 3. Cloud Platform Deployment

#### AWS Deployment
```bash
# Use AWS ECS with Docker Compose
docker context create ecs aws-observability
docker context use aws-observability
docker compose up
```

#### Azure Deployment
```bash
# Use Azure Container Instances
docker context create aci azure-observability
docker context use azure-observability
docker compose up
```

#### Google Cloud Deployment
```bash
# Use Google Cloud Run
gcloud run deploy observability-stack \
  --source . \
  --platform managed \
  --region us-central1
```

---

## ✅ Post-Deployment Validation

### 1. Automated Validation
```bash
# Run comprehensive validation
python3 validate-setup.py

# Expected output:
# ✅ Basic Connectivity
# ✅ Backend API
# ✅ Prometheus Metrics
# ✅ Jaeger Traces
# ✅ Elasticsearch Logs
# ✅ Grafana Datasources
# ✅ Frontend Tracing
# ✅ Trace Correlation
```

### 2. Manual Health Checks
```bash
# Check all services
./start.sh status

# Individual service checks
curl -f http://localhost/health              # Frontend
curl -f http://localhost:8000/health         # Backend
curl -f http://localhost:9090/-/ready        # Prometheus
curl -f http://localhost:16686/              # Jaeger
curl -f http://localhost:9200/_cluster/health # Elasticsearch
curl -f -u admin:admin http://localhost:3000/api/health # Grafana
```

### 3. End-to-End Testing
```bash
# Generate test traffic
for i in {1..10}; do
  curl -s http://localhost:8000/api/users >/dev/null
  curl -s http://localhost:8000/api/users/$((RANDOM % 5 + 1)) >/dev/null
  sleep 1
done

# Verify traces in Jaeger
curl -s "http://localhost:16686/api/traces?service=fastapi-backend&limit=5" | jq '.data | length'

# Verify metrics in Prometheus
curl -s "http://localhost:9090/api/v1/query?query=http_requests_total" | jq '.data.result | length'
```

---

## 📊 Monitoring and Alerting

### 1. Service Monitoring

#### System Metrics Dashboard
```bash
# Import system monitoring dashboard
curl -X POST \
  http://admin:admin@localhost:3000/api/dashboards/db \
  -H 'Content-Type: application/json' \
  -d @grafana/dashboards/system-metrics-dashboard.json
```

#### Key Metrics to Monitor
- **Request Rate**: `rate(http_requests_total[5m])`
- **Error Rate**: `rate(http_errors_total[5m]) / rate(http_requests_total[5m])`
- **Response Time**: `histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))`
- **Active Requests**: `http_requests_active`
- **System Resources**: CPU, Memory, Disk usage

### 2. Alerting Configuration

#### Prometheus Alert Rules
```yaml
# prometheus/alert_rules.yml
groups:
  - name: api_observability_alerts
    rules:
      - alert: HighErrorRate
        expr: rate(http_errors_total[5m]) / rate(http_requests_total[5m]) > 0.05
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value | humanizePercentage }} for the last 5 minutes"

      - alert: HighLatency
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 1
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High API latency detected"
          description: "95th percentile latency is {{ $value }}s"

      - alert: ServiceDown
        expr: up == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Service {{ $labels.instance }} is down"
          description: "Service has been down for more than 1 minute"

      - alert: ElasticsearchClusterRed
        expr: elasticsearch_cluster_health_status{color="red"} == 1
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Elasticsearch cluster status is red"

      - alert: HighMemoryUsage
        expr: (container_memory_usage_bytes / container_spec_memory_limit_bytes) * 100 > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High memory usage detected"
          description: "Memory usage is {{ $value }}%"
```

#### Grafana Alerting
```bash
# Configure notification channels
curl -X POST \
  http://admin:admin@localhost:3000/api/alert-notifications \
  -H 'Content-Type: application/json' \
  -d '{
    "name": "slack-alerts",
    "type": "slack",
    "settings": {
      "url": "your-slack-webhook-url",
      "channel": "#observability-alerts"
    }
  }'
```

### 3. Log Monitoring

#### Kibana Index Patterns
```bash
# Create index pattern for application logs
curl -X POST \
  http://localhost:5601/api/saved_objects/index-pattern/otel-logs-* \
  -H 'Content-Type: application/json' \
  -d '{
    "attributes": {
      "title": "otel-logs-*",
      "timeFieldName": "@timestamp"
    }
  }'
```

#### Log-based Alerts
```bash
# Example: Alert on high error log rate
# Use Elasticsearch Watcher or external log monitoring tools
```

---

## 🔧 Maintenance Tasks

### Daily Tasks

#### Health Checks
```bash
#!/bin/bash
# daily_health_check.sh

echo "=== Daily Health Check $(date) ==="

# Check service status
./start.sh status

# Check disk usage
df -h | grep -E "(elasticsearch|prometheus|grafana)" || echo "Storage check: OK"

# Check error rates
error_rate=$(curl -s "http://localhost:9090/api/v1/query?query=rate(http_errors_total[1h])" | jq -r '.data.result[0].value[1] // "0"')
echo "Error rate (last hour): $error_rate"

# Check memory usage
docker stats --no-stream --format "table {{.Container}}\t{{.MemUsage}}"

echo "=== Health Check Complete ==="
```

### Weekly Tasks

#### Data Cleanup
```bash
#!/bin/bash
# weekly_cleanup.sh

# Clean old Elasticsearch indices
curl -X DELETE "localhost:9200/otel-logs-$(date -d '30 days ago' +%Y.%m.%d)"

# Clean old Docker logs
docker system prune -f

# Vacuum Prometheus data (if using external storage)
# This is automatic for default Prometheus setup

# Backup Grafana dashboards
mkdir -p backups/grafana/$(date +%Y-%m-%d)
curl -s -u admin:admin "http://localhost:3000/api/search?type=dash-db" | \
  jq -r '.[].uri' | \
  while read uri; do
    curl -s -u admin:admin "http://localhost:3000/api/dashboards/$uri" > \
      "backups/grafana/$(date +%Y-%m-%d)/$(echo $uri | tr '/' '_').json"
  done
```

### Monthly Tasks

#### Performance Review
```bash
#!/bin/bash
# monthly_performance_review.sh

# Generate monthly report
echo "=== Monthly Performance Report $(date +%Y-%m) ==="

# Average response time
avg_response_time=$(curl -s "http://localhost:9090/api/v1/query?query=avg_over_time(http_request_duration_seconds[30d])" | jq -r '.data.result[0].value[1] // "N/A"')
echo "Average response time: ${avg_response_time}s"

# Total requests
total_requests=$(curl -s "http://localhost:9090/api/v1/query?query=increase(http_requests_total[30d])" | jq -r '.data.result[0].value[1] // "N/A"')
echo "Total requests: $total_requests"

# Error rate
error_rate=$(curl -s "http://localhost:9090/api/v1/query?query=rate(http_errors_total[30d])/rate(http_requests_total[30d])" | jq -r '.data.result[0].value[1] // "N/A"')
echo "Error rate: $error_rate"

# Storage usage
echo "Storage usage:"
docker exec elasticsearch curl -s "localhost:9200/_cat/indices?v&h=index,store.size"
docker exec prometheus du -sh /prometheus

echo "=== Report Complete ==="
```

#### Version Updates
```bash
# Check for updates
docker images | grep -E "(grafana|prometheus|jaegertracing|elasticsearch)"

# Update specific service
docker-compose pull grafana
docker-compose up -d grafana

# Validate after update
python3 validate-setup.py
```

---

## 🔍 Troubleshooting Guide

### Common Issues and Solutions

#### 1. Services Won't Start

**Symptom**: `docker-compose up` fails
```bash
# Diagnosis
docker-compose logs
docker-compose ps

# Common fixes
# Check port conflicts
ss -tuln | grep -E ":(80|3000|4317|4318|5601|8000|8428|9090|9200|16686)"

# Check disk space
df -h

# Check memory
free -h

# Restart with fresh state
docker-compose down -v
docker-compose up -d
```

#### 2. No Traces in Jaeger

**Symptom**: Jaeger UI shows no traces
```bash
# Diagnosis
# Check if collector is receiving traces
docker-compose logs otel-collector | grep -i trace

# Check if backend is sending traces
docker-compose logs fastapi-backend | grep -i trace

# Check collector configuration
curl http://localhost:8888/metrics | grep otelcol_receiver

# Solutions
# 1. Verify collector endpoints
curl -X POST http://localhost:4318/v1/traces \
  -H "Content-Type: application/json" \
  -d '{"resourceSpans": []}'

# 2. Check backend OTLP configuration
docker-compose exec fastapi-backend env | grep OTEL

# 3. Restart services in order
docker-compose restart jaeger otel-collector fastapi-backend
```

#### 3. Missing Metrics in Prometheus

**Symptom**: Prometheus shows no metrics from services
```bash
# Diagnosis
# Check Prometheus targets
curl http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | {job: .labels.job, health: .health}'

# Check if FastAPI is exposing metrics
curl http://localhost:8000/metrics

# Solutions
# 1. Verify Prometheus configuration
docker-compose exec prometheus cat /etc/prometheus/prometheus.yml

# 2. Check network connectivity
docker-compose exec prometheus wget -O- http://fastapi-backend:8000/metrics

# 3. Restart Prometheus
docker-compose restart prometheus
```

#### 4. Elasticsearch Cluster Red Status

**Symptom**: Elasticsearch cluster health is red
```bash
# Diagnosis
curl "http://localhost:9200/_cluster/health?pretty"
curl "http://localhost:9200/_cat/indices?v"

# Solutions
# 1. Check disk space
docker exec elasticsearch df -h

# 2. Check logs
docker-compose logs elasticsearch

# 3. Reset cluster (WARNING: DATA LOSS)
docker-compose down
docker volume rm $(docker volume ls -q | grep elasticsearch)
docker-compose up -d elasticsearch

# 4. Recovery (if possible)
curl -X PUT "localhost:9200/_all/_settings" \
  -H 'Content-Type: application/json' \
  -d '{"index.blocks.read_only_allow_delete": null}'
```

#### 5. Grafana Datasource Connection Issues

**Symptom**: Grafana can't connect to datasources
```bash
# Diagnosis
# Test datasource connectivity from Grafana container
docker-compose exec grafana wget -O- http://prometheus:9090/-/ready
docker-compose exec grafana wget -O- http://jaeger:16686/
docker-compose exec grafana curl http://elasticsearch:9200/_cluster/health

# Solutions
# 1. Check datasource configuration
curl -u admin:admin http://localhost:3000/api/datasources

# 2. Test and save datasources
curl -X POST -u admin:admin \
  http://localhost:3000/api/datasources/1/health

# 3. Recreate datasources
docker-compose restart grafana
```

### Performance Issues

#### High Memory Usage
```bash
# Check memory usage per service
docker stats --no-stream

# Adjust memory limits in docker-compose.yml
services:
  elasticsearch:
    environment:
      - "ES_JAVA_OPTS=-Xms1g -Xmx1g"  # Reduce if needed
```

#### High CPU Usage
```bash
# Identify CPU-intensive containers
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}"

# Reduce OpenTelemetry Collector load
# Edit otel/otel-collector-config.yml
processors:
  batch:
    timeout: 1s
    send_batch_size: 512  # Reduce batch size
```

#### Slow Query Performance
```bash
# Check Prometheus query performance
curl "http://localhost:9090/api/v1/status/tsdb" | jq '.data'

# Optimize Elasticsearch queries
curl "http://localhost:9200/_nodes/stats/indices/search"

# Check Grafana query performance
# Use Grafana query inspector
```

---

## 💾 Backup and Recovery

### 1. Data Backup Strategy

#### Automated Backup Script
```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/backups/$(date +%Y-%m-%d)"
mkdir -p "$BACKUP_DIR"

# Backup Grafana dashboards and configuration
echo "Backing up Grafana..."
docker exec grafana tar -czf - /var/lib/grafana > "$BACKUP_DIR/grafana.tar.gz"

# Backup Prometheus data
echo "Backing up Prometheus..."
docker exec prometheus tar -czf - /prometheus > "$BACKUP_DIR/prometheus.tar.gz"

# Backup Elasticsearch data
echo "Backing up Elasticsearch..."
docker exec elasticsearch curl -X PUT "localhost:9200/_snapshot/backup_repo/snapshot_$(date +%Y%m%d)" \
  -H 'Content-Type: application/json' \
  -d '{"indices": "*", "ignore_unavailable": true, "include_global_state": false}'

# Backup configuration files
echo "Backing up configuration..."
tar -czf "$BACKUP_DIR/configs.tar.gz" \
  docker-compose.yml \
  otel/ \
  prometheus/ \
  grafana/provisioning/

echo "Backup completed: $BACKUP_DIR"
```

#### Schedule Backups
```bash
# Add to crontab
crontab -e

# Daily backup at 2 AM
0 2 * * * /path/to/backup.sh

# Weekly full backup
0 3 * * 0 /path/to/full_backup.sh
```

### 2. Recovery Procedures

#### Full System Recovery
```bash
#!/bin/bash
# recovery.sh

BACKUP_DATE="2024-01-15"  # Specify backup date
BACKUP_DIR="/backups/$BACKUP_DATE"

# Stop services
docker-compose down -v

# Restore configuration
tar -xzf "$BACKUP_DIR/configs.tar.gz"

# Start infrastructure services
docker-compose up -d elasticsearch prometheus jaeger

# Wait for services to be ready
sleep 30

# Restore Elasticsearch data
docker exec elasticsearch curl -X POST "localhost:9200/_snapshot/backup_repo/snapshot_$(echo $BACKUP_DATE | tr -d '-')/_restore"

# Restore Prometheus data
docker run --rm -v prometheus-data:/prometheus -v "$BACKUP_DIR:/backup" \
  busybox tar -xzf /backup/prometheus.tar.gz -C /

# Restore Grafana data
docker run --rm -v grafana-data:/var/lib/grafana -v "$BACKUP_DIR:/backup" \
  busybox tar -xzf /backup/grafana.tar.gz -C /

# Start remaining services
docker-compose up -d

echo "Recovery completed"
```

---

## ⚡ Performance Optimization

### 1. Resource Optimization

#### Docker Resource Limits
```yaml
# docker-compose.yml optimizations
services:
  elasticsearch:
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '1.0'
        reservations:
          memory: 1G
          cpus: '0.5'
    environment:
      - "ES_JAVA_OPTS=-Xms1g -Xmx1g"

  prometheus:
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '0.5'
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.retention.time=30d'
      - '--storage.tsdb.retention.size=10GB'
```

#### OpenTelemetry Collector Optimization
```yaml
# otel/otel-collector-config.yml
processors:
  batch:
    timeout: 200ms
    send_batch_size: 1024
    send_batch_max_size: 2048

  memory_limiter:
    check_interval: 1s
    limit_mib: 512

  # Add sampling for high-volume environments
  probabilistic_sampler:
    sampling_percentage: 10.0  # Sample 10% of traces
```

### 2. Query Optimization

#### Prometheus Query Optimization
```bash
# Use recording rules for frequently used queries
# prometheus/recording_rules.yml
groups:
  - name: api_metrics
    interval: 30s
    rules:
      - record: api:request_rate_5m
        expr: rate(http_requests_total[5m])
      
      - record: api:error_rate_5m
        expr: rate(http_errors_total[5m]) / rate(http_requests_total[5m])
      
      - record: api:latency_p95_5m
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))
```

#### Elasticsearch Optimization
```bash
# Optimize Elasticsearch settings
curl -X PUT "localhost:9200/_cluster/settings" \
  -H 'Content-Type: application/json' \
  -d '{
    "persistent": {
      "indices.lifecycle.rollover.max_size": "1gb",
      "indices.lifecycle.rollover.max_age": "1d"
    }
  }'
```

### 3. Network Optimization

#### Container Network Configuration
```yaml
# docker-compose.yml
networks:
  observability:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
          gateway: 172.20.0.1
```

---

## 🔒 Security Operations

### 1. Access Control

#### Role-Based Access
```bash
# Grafana user management
curl -X POST -u admin:admin \
  http://localhost:3000/api/users \
  -H 'Content-Type: application/json' \
  -d '{
    "name": "Observer User",
    "email": "observer@company.com",
    "login": "observer",
    "password": "secure-password"
  }'

# Assign viewer role
curl -X PUT -u admin:admin \
  http://localhost:3000/api/orgs/1/users/2 \
  -H 'Content-Type: application/json' \
  -d '{"role": "Viewer"}'
```

### 2. SSL/TLS Configuration

#### Production SSL Setup
```yaml
# docker-compose.prod.yml
services:
  grafana:
    environment:
      - GF_SERVER_PROTOCOL=https
      - GF_SERVER_CERT_FILE=/etc/ssl/certs/grafana.crt
      - GF_SERVER_CERT_KEY=/etc/ssl/private/grafana.key
    volumes:
      - ./ssl:/etc/ssl
```

### 3. Security Monitoring

#### Security Alert Rules
```yaml
# prometheus/security_rules.yml
groups:
  - name: security_alerts
    rules:
      - alert: UnauthorizedAccess
        expr: rate(http_requests_total{code=~"4.."}[5m]) > 10
        for: 1m
        labels:
          severity: warning
        annotations:
          summary: "High rate of 4xx errors detected"

      - alert: SuspiciousActivity
        expr: rate(http_requests_total[1m]) > 1000
        for: 30s
        labels:
          severity: critical
        annotations:
          summary: "Unusually high request rate - possible attack"
```

---

## 📈 Capacity Planning

### 1. Resource Monitoring

#### Capacity Metrics Dashboard
- CPU usage trends
- Memory consumption patterns
- Disk usage growth
- Network I/O patterns
- Request volume trends

### 2. Scaling Guidelines

#### Horizontal Scaling
```yaml
# docker-compose.scale.yml
services:
  fastapi-backend:
    deploy:
      replicas: 3
      
  otel-collector:
    deploy:
      replicas: 2
```

#### Vertical Scaling
```yaml
# Increase resources for high-load components
services:
  elasticsearch:
    environment:
      - "ES_JAVA_OPTS=-Xms4g -Xmx4g"
    deploy:
      resources:
        limits:
          memory: 8G
          cpus: '2.0'
```

### 3. Load Testing

#### Performance Testing Script
```bash
#!/bin/bash
# load_test.sh

# Install prerequisites
pip install locust

# Run load test
locust -f tests/locustfile.py \
  --host=http://localhost:8000 \
  --users=100 \
  --spawn-rate=10 \
  --run-time=10m \
  --html=reports/load_test_$(date +%Y%m%d_%H%M%S).html
```

This operations manual provides comprehensive guidance for running the observability stack in production. Regular review and updates of these procedures ensure reliable operation and optimal performance.