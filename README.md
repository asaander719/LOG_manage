# API HTTP Request Logging Management System

A comprehensive observability solution for API monitoring using OpenTelemetry, Prometheus, ELK Stack, and Grafana. This system provides end-to-end tracing, metrics collection, and log correlation for Vue.js frontend and FastAPI backend applications.

## 🎯 Objectives

- **Capture Metrics, Traces, and Logs** for all API requests (Frontend Vue → Backend FastAPI)
- **Correlate data across services** using distributed tracing with trace_id propagation
- **Provide unified visualization** in Grafana dashboards
- **Enable real-time monitoring** and debugging capabilities

## 🏗️ Architecture

### Data Flow
```
Vue.js Frontend → OpenTelemetry Collector → Storage Backends → Grafana
     ↓                      ↓                       ↓
FastAPI Backend    →    Traces: Jaeger      →   Unified
                       Metrics: Prometheus    Dashboards
                       Logs: Elasticsearch
```

### Components

| Component | Purpose | Port |
|-----------|---------|------|
| **Vue.js Frontend** | Web application with OTel instrumentation | 80 |
| **FastAPI Backend** | API server with observability | 8000 |
| **OpenTelemetry Collector** | Central telemetry data hub | 4317/4318 |
| **Jaeger** | Distributed tracing storage | 16686 |
| **Prometheus** | Metrics collection and storage | 9090 |
| **VictoriaMetrics** | Long-term metrics storage | 8428 |
| **Elasticsearch** | Log storage and search | 9200 |
| **Kibana** | Log visualization | 5601 |
| **Grafana** | Unified observability dashboards | 3000 |

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- Node.js 18+ (for local frontend development)
- Python 3.11+ (for local backend development)

### 1. Deploy the Complete Stack

```bash
# Clone the repository
git clone <repository-url>
cd LOG_manage

# Start all services
docker-compose up -d

# Check service health
docker-compose ps
```

### 2. Access the Interfaces

| Service | URL | Description |
|---------|-----|-------------|
| **Frontend Demo** | http://localhost | Interactive API testing interface |
| **Grafana** | http://localhost:3000 | Unified dashboards (admin/admin) |
| **Jaeger** | http://localhost:16686 | Distributed tracing |
| **Prometheus** | http://localhost:9090 | Metrics and alerts |
| **Kibana** | http://localhost:5601 | Log exploration |
| **FastAPI Backend** | http://localhost:8000 | API documentation |

### 3. Test the System

1. **Open the Frontend**: Navigate to http://localhost
2. **Trigger API Calls**: Use the buttons to test different endpoints
3. **View Traces**: Check Jaeger at http://localhost:16686
4. **Monitor Metrics**: Open Grafana dashboard at http://localhost:3000
5. **Explore Logs**: Use Kibana at http://localhost:5601

## 📊 Features

### ✅ Frontend Instrumentation (Vue.js)
- **Automatic HTTP Request Tracing**: All fetch/XHR requests are traced
- **Trace Context Propagation**: W3C traceparent headers are automatically injected
- **User Interaction Tracking**: Button clicks, form submissions, page loads
- **Error Tracking**: Frontend errors are captured and correlated with traces
- **Structured Logging**: Logs include trace_id for correlation

### ✅ Backend Instrumentation (FastAPI)
- **Comprehensive Span Creation**: Each API endpoint creates detailed spans
- **Prometheus Metrics**: Request rate, duration, error rate, active requests
- **Trace-Correlated Logs**: All logs include trace_id and span_id
- **Custom Attributes**: Business logic attributes added to spans
- **Error Handling**: Exceptions are properly recorded in traces

### ✅ OpenTelemetry Collector
- **Multi-Protocol Support**: OTLP gRPC/HTTP, Prometheus scraping
- **Data Processing**: Batching, filtering, attribute manipulation
- **Multiple Exporters**: Routes data to Jaeger, Prometheus, Elasticsearch
- **Performance Optimized**: Memory limits, batching, sampling

### ✅ Grafana Dashboards
- **Unified View**: Metrics, traces, and logs in one dashboard
- **Real-time Updates**: Auto-refresh every 5 seconds
- **Interactive Exploration**: Click trace IDs to jump to Jaeger
- **Alerting Ready**: Threshold-based alerts for SLIs

## 🔧 Configuration

### Environment Variables

#### Backend (FastAPI)
```bash
OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317
OTEL_SERVICE_NAME=fastapi-backend
OTEL_RESOURCE_ATTRIBUTES=service.name=fastapi-backend,service.version=1.0.0
```

#### Frontend (Vue.js)
OpenTelemetry is configured in `frontend/src/telemetry.js`:
```javascript
// Collector endpoint
url: 'http://localhost:4318/v1/traces'

// Service identification
SERVICE_NAME: 'frontend-vue'
SERVICE_VERSION: '1.0.0'
```

### Customization

#### Add Custom Metrics
```python
# In FastAPI backend
from prometheus_client import Counter

custom_counter = Counter('custom_operations_total', 'Custom operations')
custom_counter.inc()
```

#### Add Custom Spans
```python
# In FastAPI backend
with tracer.start_as_current_span("custom_operation") as span:
    span.set_attribute("custom.attribute", "value")
    # Your business logic here
```

#### Frontend Custom Tracing
```javascript
// In Vue.js component
import { trace } from '@opentelemetry/api'

const tracer = trace.getTracer('frontend-custom')
tracer.startActiveSpan('user_action', (span) => {
  span.setAttributes({ 'user.id': userId })
  // Your custom logic
  span.end()
})
```

## 📈 Monitoring & Alerting

### Key Metrics to Monitor

1. **Request Rate**: `rate(http_requests_total[5m])`
2. **Error Rate**: `rate(http_errors_total[5m])`
3. **Response Time**: `histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))`
4. **Active Requests**: `http_requests_active`

### Sample Alerts

```yaml
# prometheus/alert_rules.yml
groups:
  - name: api_alerts
    rules:
      - alert: HighErrorRate
        expr: rate(http_errors_total[5m]) > 0.1
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "High error rate detected"

      - alert: HighLatency
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 1
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High API latency detected"
```

## 🔍 Troubleshooting

### Common Issues

#### 1. No Traces in Jaeger
```bash
# Check collector logs
docker-compose logs otel-collector

# Verify backend is sending traces
docker-compose logs fastapi-backend | grep trace

# Check frontend telemetry
# Open browser dev tools → Console → Look for OTel logs
```

#### 2. Missing Metrics in Prometheus
```bash
# Check if Prometheus can scrape targets
curl http://localhost:9090/api/v1/targets

# Verify FastAPI metrics endpoint
curl http://localhost:8000/metrics
```

#### 3. No Logs in Elasticsearch
```bash
# Check Elasticsearch health
curl http://localhost:9200/_cluster/health

# Verify log indices
curl http://localhost:9200/_cat/indices
```

### Health Checks

```bash
# Check all service health
docker-compose ps

# Individual service health
curl http://localhost:8000/health  # FastAPI
curl http://localhost/health       # Frontend
curl http://localhost:9200/_cluster/health  # Elasticsearch
```

## 🔒 Security Considerations

### Implemented Security Measures

1. **Header Sanitization**: Authorization and Cookie headers are removed from traces
2. **CORS Configuration**: Properly configured for cross-origin requests
3. **Data Masking**: Sensitive data is masked in logs and traces
4. **Network Isolation**: Services communicate within Docker network

### Additional Security Steps

```yaml
# For production deployment
version: '3.8'
services:
  otel-collector:
    environment:
      - OTEL_EXPORTER_OTLP_HEADERS=authorization=Bearer ${API_TOKEN}
  
  grafana:
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}
      - GF_USERS_ALLOW_SIGN_UP=false
```

## 📚 Development Guide

### Local Development Setup

#### Backend Development
```bash
cd backend
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend Development
```bash
cd frontend
npm install
npm run dev
```

### Adding New Endpoints

1. **Create FastAPI Endpoint**:
```python
@app.get("/api/new-endpoint")
async def new_endpoint():
    with tracer.start_as_current_span("new_endpoint") as span:
        span.set_attribute("operation", "new_operation")
        # Your logic here
        return {"result": "data"}
```

2. **Add Frontend Integration**:
```javascript
async testNewEndpoint() {
  await this.makeApiCall('GET', '/api/new-endpoint')
}
```

### Testing

#### Load Testing
```bash
# Install wrk or apache bench
# Generate load on API
wrk -t12 -c400 -d30s http://localhost:8000/api/users

# Monitor in Grafana during load test
```

#### Trace Validation
```bash
# Query traces by service
curl "http://localhost:16686/api/traces?service=fastapi-backend&limit=10"

# Search logs by trace_id
curl "http://localhost:9200/otel-logs/_search?q=trace_id:YOUR_TRACE_ID"
```

## 🎛️ Advanced Configuration

### Custom Sampling
```yaml
# otel/otel-collector-config.yml
processors:
  probabilistic_sampler:
    sampling_percentage: 10  # Sample 10% of traces
```

### Log Correlation
```python
# Custom log formatter with trace correlation
class TraceFormatter(logging.Formatter):
    def format(self, record):
        span = trace.get_current_span()
        if span:
            record.trace_id = format(span.get_span_context().trace_id, '032x')
        return super().format(record)
```

## 📖 References

- [OpenTelemetry Documentation](https://opentelemetry.io/docs/)
- [FastAPI Observability Guide](https://fastapi.tiangolo.com/)
- [Vue.js Performance Monitoring](https://vuejs.org/)
- [Prometheus Best Practices](https://prometheus.io/docs/practices/)
- [Grafana Dashboard Design](https://grafana.com/docs/)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/new-feature`
3. Commit changes: `git commit -am 'Add new feature'`
4. Push to branch: `git push origin feature/new-feature`
5. Submit a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

**Built with ❤️ for comprehensive API observability**