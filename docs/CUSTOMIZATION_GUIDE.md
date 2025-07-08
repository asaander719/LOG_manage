# Customization Guide - Adapting the Observability Stack

This guide helps you customize the API HTTP Request Logging Management System for your own projects and requirements.

## 🎯 Quick Customization Checklist

### ✅ Essential Customizations (Must Change)
- [ ] Service names and versions
- [ ] Application endpoints and business logic
- [ ] Port mappings (if conflicts exist)
- [ ] Environment-specific configurations
- [ ] Security credentials and secrets

### 🔧 Optional Customizations (Recommended)
- [ ] Custom metrics and spans
- [ ] Dashboard layouts and visualizations
- [ ] Alert rules and thresholds
- [ ] Retention policies
- [ ] Resource limits and scaling

## 📂 Customization Areas by Component

### 1. 🎨 Frontend Application Customization

#### **Location**: `frontend/`

#### **Essential Changes**

##### Service Configuration (`frontend/src/telemetry.js`)
```javascript
// CHANGE THESE VALUES
const resource = new Resource({
  [SemanticResourceAttributes.SERVICE_NAME]: 'YOUR-FRONTEND-SERVICE-NAME',
  [SemanticResourceAttributes.SERVICE_VERSION]: 'YOUR-VERSION',
  [SemanticResourceAttributes.SERVICE_INSTANCE_ID]: 'YOUR-INSTANCE-ID',
  [SemanticResourceAttributes.DEPLOYMENT_ENVIRONMENT]: 'YOUR-ENVIRONMENT' // dev/staging/prod
})

// CHANGE COLLECTOR ENDPOINT
const collectorExporter = new OTLPTraceExporter({
  url: 'http://YOUR-COLLECTOR-HOST:4318/v1/traces',  // Update if different host
  headers: {
    'Content-Type': 'application/json'
  }
})
```

##### Application Content (`frontend/src/App.vue`)
```vue
<!-- CUSTOMIZE YOUR UI -->
<template>
  <div id="app">
    <header class="app-header">
      <h1>🔍 YOUR APPLICATION NAME</h1>
      <p>YOUR APPLICATION DESCRIPTION</p>
    </header>
    
    <!-- Replace with your actual frontend components -->
    <YourMainComponent />
  </div>
</template>
```

##### API Endpoints (`frontend/src/App.vue`)
```javascript
// REPLACE WITH YOUR API ENDPOINTS
async testGetUsers() {
  await this.makeApiCall('GET', '/api/your-endpoint')
}

// ADD YOUR CUSTOM API CALLS
async yourCustomApiCall() {
  await this.makeApiCall('POST', '/api/your-custom-endpoint', {
    // your data structure
  })
}
```

#### **Framework Migration Options**

##### For React Applications
```bash
# Replace Vue.js with React
npm install react react-dom @opentelemetry/api @opentelemetry/sdk-trace-web
# Use the same OpenTelemetry configuration patterns
```

##### For Angular Applications
```bash
# Replace Vue.js with Angular
ng new your-app
npm install @opentelemetry/api @opentelemetry/sdk-trace-web
# Adapt telemetry.js to Angular service pattern
```

---

### 2. 🚀 Backend Application Customization

#### **Location**: `backend/`

#### **Essential Changes**

##### Service Configuration (`backend/app.py`)
```python
# CHANGE SERVICE IDENTIFICATION
resource = Resource.create({
    "service.name": "YOUR-BACKEND-SERVICE-NAME",
    "service.version": "YOUR-VERSION",
    "service.instance.id": "YOUR-INSTANCE-ID",
    "deployment.environment": "YOUR-ENVIRONMENT"
})
```

##### Application Details
```python
# CUSTOMIZE APPLICATION METADATA
app = FastAPI(
    title="YOUR API TITLE",
    version="YOUR-VERSION",
    description="YOUR API DESCRIPTION",
    lifespan=lifespan
)
```

##### Business Logic Endpoints
```python
# REPLACE WITH YOUR ACTUAL ENDPOINTS
@app.get("/api/your-resource")
async def get_your_resource():
    with tracer.start_as_current_span("get_your_resource") as span:
        span.set_attribute("operation", "your_operation")
        
        # YOUR BUSINESS LOGIC HERE
        result = await your_business_logic()
        
        span.set_attribute("result.count", len(result))
        logger.info(f"Retrieved {len(result)} items")
        
        return result

# ADD YOUR CUSTOM METRICS
YOUR_CUSTOM_COUNTER = Counter(
    'your_custom_operations_total',
    'Description of your custom metric',
    ['your_label1', 'your_label2']
)
```

#### **Framework Migration Options**

##### For Express.js (Node.js)
```javascript
// Replace FastAPI with Express.js
const express = require('express');
const { NodeSDK } = require('@opentelemetry/sdk-node');
// Use OpenTelemetry Node.js SDK
```

##### For Spring Boot (Java)
```java
// Replace FastAPI with Spring Boot
// Use OpenTelemetry Java agent or manual instrumentation
@RestController
public class YourController {
    // Your endpoints here
}
```

##### For ASP.NET Core (C#)
```csharp
// Replace FastAPI with ASP.NET Core
// Use OpenTelemetry .NET SDK
[ApiController]
public class YourController : ControllerBase
{
    // Your endpoints here
}
```

---

### 3. 🔄 OpenTelemetry Collector Customization

#### **Location**: `otel/otel-collector-config.yml`

#### **Essential Changes**

##### Service Discovery
```yaml
receivers:
  prometheus:
    config:
      scrape_configs:
        - job_name: 'YOUR-SERVICE-NAME'
          static_configs:
            - targets: ['YOUR-SERVICE-HOST:YOUR-PORT']
          metrics_path: '/metrics'
          scrape_interval: 15s
```

##### Custom Attributes
```yaml
processors:
  resource:
    attributes:
      - key: environment
        value: "YOUR-ENVIRONMENT"  # development/staging/production
        action: upsert
      - key: cluster
        value: "YOUR-CLUSTER-NAME"
        action: upsert
      - key: region
        value: "YOUR-REGION"
        action: upsert
```

##### Security and Filtering
```yaml
processors:
  attributes:
    actions:
      # ADD YOUR SENSITIVE HEADERS TO REMOVE
      - key: http.request.header.YOUR_CUSTOM_AUTH_HEADER
        action: delete
      - key: http.request.header.YOUR_API_KEY_HEADER
        action: delete
```

#### **Scaling Configurations**

##### High-Volume Environments
```yaml
processors:
  batch:
    timeout: 200ms
    send_batch_size: 2048
    send_batch_max_size: 4096
  
  memory_limiter:
    check_interval: 1s
    limit_mib: 1024  # Increase for high volume
```

---

### 4. 📊 Monitoring Configuration Customization

#### **Location**: `prometheus/prometheus.yml`

##### Custom Scrape Targets
```yaml
scrape_configs:
  # ADD YOUR SERVICES
  - job_name: 'your-service-name'
    static_configs:
      - targets: ['your-service:your-port']
    metrics_path: '/metrics'
    scrape_interval: 15s
    
  # KUBERNETES DISCOVERY (if applicable)
  - job_name: 'kubernetes-pods'
    kubernetes_sd_configs:
      - role: pod
    relabel_configs:
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
        action: keep
        regex: true
```

---

### 5. 📈 Grafana Dashboard Customization

#### **Location**: `grafana/dashboards/`

#### **Custom Metrics Dashboard**
```json
{
  "targets": [
    {
      "expr": "rate(your_custom_metric_total[5m])",
      "legendFormat": "Your Custom Metric - {{label_name}}"
    }
  ]
}
```

#### **Custom Variables**
```json
{
  "templating": {
    "list": [
      {
        "name": "your_service",
        "query": "label_values(your_metric, service_name)",
        "type": "query"
      }
    ]
  }
}
```

---

## 🏗️ Environment-Specific Configurations

### Development Environment
```yaml
# docker-compose.dev.yml
version: '3.8'
services:
  fastapi-backend:
    environment:
      - OTEL_RESOURCE_ATTRIBUTES=service.name=your-app-dev,deployment.environment=development
      - LOG_LEVEL=DEBUG
    volumes:
      - ./backend:/app  # Live reload for development
```

### Staging Environment
```yaml
# docker-compose.staging.yml
version: '3.8'
services:
  fastapi-backend:
    environment:
      - OTEL_RESOURCE_ATTRIBUTES=service.name=your-app-staging,deployment.environment=staging
      - LOG_LEVEL=INFO
```

### Production Environment
```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  fastapi-backend:
    environment:
      - OTEL_RESOURCE_ATTRIBUTES=service.name=your-app-prod,deployment.environment=production
      - LOG_LEVEL=WARNING
    deploy:
      replicas: 3
      resources:
        limits:
          memory: 512M
        reservations:
          memory: 256M
```

---

## 🔐 Security Customization

### 1. Credentials Management
```bash
# Create .env file for sensitive data
cat > .env << EOF
GRAFANA_ADMIN_PASSWORD=your-secure-password
ELASTICSEARCH_PASSWORD=your-es-password
OTEL_EXPORTER_OTLP_HEADERS=authorization=Bearer your-api-token
EOF
```

### 2. Network Security
```yaml
# docker-compose.yml
networks:
  observability:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16  # Custom subnet
```

### 3. TLS/SSL Configuration
```yaml
# For production with SSL
services:
  grafana:
    environment:
      - GF_SERVER_PROTOCOL=https
      - GF_SERVER_CERT_FILE=/etc/ssl/certs/grafana.crt
      - GF_SERVER_CERT_KEY=/etc/ssl/private/grafana.key
```

---

## 📏 Scaling and Performance Customization

### 1. Resource Limits
```yaml
# docker-compose.yml
services:
  elasticsearch:
    environment:
      - "ES_JAVA_OPTS=-Xms2g -Xmx2g"  # Adjust based on your needs
    deploy:
      resources:
        limits:
          memory: 4G
        reservations:
          memory: 2G
```

### 2. Retention Policies
```yaml
# elasticsearch configuration
services:
  elasticsearch:
    environment:
      - "indices.lifecycle.rollover.max_size=1gb"
      - "indices.lifecycle.delete.min_age=30d"
```

### 3. Sampling Configuration
```yaml
# otel-collector-config.yml
processors:
  probabilistic_sampler:
    sampling_percentage: 1.0  # Adjust for your volume (1.0 = 100%, 0.1 = 10%)
```

---

## 🔄 Migration Strategies

### From Existing Monitoring Solutions

#### **From Datadog**
1. Replace Datadog agent with OpenTelemetry Collector
2. Convert Datadog dashboards to Grafana
3. Migrate APM instrumentation to OpenTelemetry

#### **From New Relic**
1. Replace New Relic agent with OpenTelemetry SDK
2. Convert New Relic queries to PromQL
3. Recreate dashboards in Grafana

#### **From AWS CloudWatch**
1. Add OpenTelemetry exporters for CloudWatch
2. Dual-write during migration period
3. Gradually migrate dashboards and alerts

---

## 📋 Customization Templates

### 1. Custom Service Template
```python
# templates/custom_service.py
from opentelemetry import trace, metrics
from prometheus_client import Counter, Histogram

# Your service configuration
SERVICE_NAME = "your-service-name"
tracer = trace.get_tracer(SERVICE_NAME)
meter = metrics.get_meter(SERVICE_NAME)

# Your custom metrics
your_counter = Counter('your_operations_total', 'Your operations', ['operation_type'])
your_histogram = Histogram('your_duration_seconds', 'Your operation duration')

# Your instrumented function
def your_function():
    with tracer.start_as_current_span("your_operation") as span:
        span.set_attribute("custom.attribute", "value")
        your_counter.labels(operation_type="your_type").inc()
        
        with your_histogram.time():
            # Your business logic
            pass
```

### 2. Custom Frontend Component Template
```vue
<!-- templates/CustomComponent.vue -->
<template>
  <div class="custom-component">
    <h2>Your Custom Component</h2>
    <button @click="performAction">Your Action</button>
  </div>
</template>

<script>
import { trace } from '@opentelemetry/api'
import { logger } from '../telemetry'

export default {
  name: 'CustomComponent',
  methods: {
    async performAction() {
      const tracer = trace.getTracer('frontend-custom')
      
      tracer.startActiveSpan('your_custom_action', async (span) => {
        try {
          span.setAttributes({
            'user.action': 'your_action',
            'component': 'CustomComponent'
          })
          
          logger.info('Custom action started')
          
          // Your business logic here
          
          logger.info('Custom action completed')
        } finally {
          span.end()
        }
      })
    }
  }
}
</script>
```

---

## 🛠️ Testing Your Customizations

### 1. Validation Script Customization
```python
# Modify validate-setup.py
class CustomValidator(ObservabilityValidator):
    def __init__(self):
        super().__init__()
        # Add your custom service endpoints
        self.services.update({
            'your-service': 'http://localhost:your-port'
        })
    
    def test_your_custom_endpoint(self):
        # Add your custom validation logic
        pass
```

### 2. Load Testing Your Setup
```bash
# Install load testing tools
pip install locust

# Create load test
cat > locustfile.py << 'EOF'
from locust import HttpUser, task

class YourAppUser(HttpUser):
    @task
    def test_your_endpoint(self):
        self.client.get("/api/your-endpoint")
EOF

# Run load test
locust --host=http://localhost:8000
```

---

## 📚 Best Practices for Customization

### 1. **Naming Conventions**
- Use consistent service names across all components
- Include environment in service names (e.g., `your-app-prod`)
- Use semantic versioning for service versions

### 2. **Resource Management**
- Set appropriate resource limits for each service
- Monitor resource usage during load testing
- Adjust retention policies based on storage capacity

### 3. **Security**
- Never commit secrets to version control
- Use environment variables for all sensitive data
- Regularly rotate credentials and tokens

### 4. **Monitoring**
- Set up alerts for critical metrics
- Test your dashboards with real data
- Document your custom metrics and their meanings

### 5. **Maintenance**
- Keep OpenTelemetry SDK versions updated
- Regularly review and clean up unused metrics
- Monitor collector performance and adjust as needed

---

## 🔍 Troubleshooting Customizations

### Common Issues and Solutions

#### **Service Discovery Problems**
```bash
# Check if your service is reachable
curl http://your-service:your-port/metrics

# Verify in Prometheus targets
curl http://localhost:9090/api/v1/targets
```

#### **Missing Traces**
```bash
# Check collector logs
docker-compose logs otel-collector

# Verify your service is sending traces
# Add debug logging to your application
```

#### **Dashboard Issues**
```bash
# Test Grafana datasource connectivity
curl -u admin:admin http://localhost:3000/api/datasources/proxy/1/api/v1/query?query=up
```

This customization guide provides comprehensive instructions for adapting the observability stack to your specific needs. Use it as a reference when implementing observability for your own applications.