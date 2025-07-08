# 📁 Project Structure - API Observability Stack

This document provides a complete overview of the project structure, explaining the purpose of each component and file in the API HTTP Request Logging Management System.

## 🌳 Complete Directory Tree

```
LOG_manage/
├── 📄 README.md                           # Main project documentation
├── 📄 DEPLOYMENT_GUIDE.md                 # Step-by-step deployment guide
├── 📄 PROJECT_STRUCTURE.md               # This file - project organization
├── 🐳 docker-compose.yml                 # Main infrastructure definition
├── 🚀 start.sh                          # Automated deployment script
├── 🔍 validate-setup.py                  # System validation script
│
├── 📁 docs/                              # Comprehensive documentation
│   ├── 📄 COMPONENTS_OVERVIEW.md         # Technical architecture details
│   ├── 📄 CUSTOMIZATION_GUIDE.md         # How to adapt for your project
│   └── 📄 OPERATIONS_MANUAL.md           # Production operations guide
│
├── 📁 frontend/                          # Vue.js frontend application
│   ├── 📁 src/
│   │   ├── 🎨 App.vue                    # Main Vue.js component
│   │   ├── ⚡ main.js                     # Application entry point
│   │   ├── 🔧 telemetry.js               # OpenTelemetry Web SDK setup
│   │   └── 📁 router/
│   │       └── 🗺️ index.js                # Vue Router configuration
│   ├── 🐳 Dockerfile                     # Multi-stage build (Node.js + Nginx)
│   ├── ⚙️ nginx.conf                     # Production web server config
│   ├── 📦 package.json                   # Dependencies and build scripts
│   ├── ⚡ vite.config.js                 # Build tool configuration
│   └── 🌐 index.html                     # HTML template
│
├── 📁 backend/                           # FastAPI backend application
│   ├── 🐍 app.py                        # Main FastAPI app with instrumentation
│   ├── 📦 requirements.txt               # Python dependencies
│   └── 🐳 Dockerfile                     # Python runtime container
│
├── 📁 otel/                              # OpenTelemetry Collector
│   └── ⚙️ otel-collector-config.yml      # Collector configuration
│
├── 📁 prometheus/                        # Metrics collection and storage
│   └── ⚙️ prometheus.yml                 # Prometheus configuration
│
└── 📁 grafana/                           # Unified dashboards and visualization
    ├── 📁 provisioning/
    │   ├── 📁 datasources/
    │   │   └── ⚙️ datasources.yml         # Auto-configured data sources
    │   └── 📁 dashboards/
    │       └── ⚙️ dashboards.yml          # Dashboard provisioning
    └── 📁 dashboards/
        └── 📊 api-observability-dashboard.json  # Pre-built dashboard
```

---

## 📋 File Descriptions by Category

### 🎯 Core Infrastructure

#### `docker-compose.yml`
**Purpose**: Defines the complete observability infrastructure  
**Contains**:
- 9 services: Frontend, Backend, OTel Collector, Jaeger, Prometheus, VictoriaMetrics, Elasticsearch, Kibana, Grafana
- Network configuration for service communication
- Volume definitions for data persistence
- Environment variables and service dependencies

**Key Services Defined**:
```yaml
services:
  frontend          # Vue.js app (Port: 80)
  fastapi-backend   # API server (Port: 8000)
  otel-collector    # Telemetry hub (Ports: 4317/4318)
  jaeger           # Trace storage (Port: 16686)
  prometheus       # Metrics collection (Port: 9090)
  victoriametrics  # Long-term metrics (Port: 8428)
  elasticsearch    # Log storage (Port: 9200)
  kibana          # Log visualization (Port: 5601)
  grafana         # Unified dashboards (Port: 3000)
```

#### `start.sh`
**Purpose**: Automated deployment and management script  
**Functions**:
- Pre-deployment checks (ports, resources)
- Service startup and health monitoring
- Status reporting and troubleshooting
- System testing and validation

**Usage Examples**:
```bash
./start.sh start    # Deploy the complete stack
./start.sh status   # Check service health
./start.sh logs     # View service logs
./start.sh test     # Run system tests
./start.sh cleanup  # Remove everything
```

#### `validate-setup.py`
**Purpose**: Comprehensive system validation  
**Tests**:
- Service connectivity and health
- Data flow between components
- Trace correlation end-to-end
- Dashboard functionality
- Performance metrics

**Validation Areas**:
- ✅ Basic service connectivity
- ✅ API endpoint functionality
- ✅ Metrics collection in Prometheus
- ✅ Trace generation in Jaeger
- ✅ Log ingestion in Elasticsearch
- ✅ Grafana datasource configuration
- ✅ Frontend instrumentation
- ✅ End-to-end trace correlation

---

### 🎨 Frontend Application (`frontend/`)

#### `src/App.vue`
**Purpose**: Main Vue.js application component  
**Features**:
- Interactive API testing interface
- Real-time observability data display
- Trace ID correlation demonstration
- Error handling and logging
- Beautiful responsive UI

**Key Sections**:
```vue
<template>
  <!-- API Testing Buttons -->
  <!-- Results Display with Trace IDs -->
  <!-- Telemetry Information Panel -->
  <!-- Monitoring Links -->
</template>
```

#### `src/main.js`
**Purpose**: Application entry point  
**Responsibilities**:
- Vue.js app initialization
- OpenTelemetry setup
- Router configuration
- Global error handling

#### `src/telemetry.js`
**Purpose**: OpenTelemetry Web SDK configuration  
**Features**:
- Automatic HTTP request instrumentation
- W3C trace context propagation
- Custom span creation
- Structured logging with trace correlation
- Performance optimization

**Key Classes**:
```javascript
TraceLogger        // Custom logger with trace correlation
HTTPInterceptor    // Automatic request tracing
initTelemetry()    // Main setup function
```

#### `Dockerfile`
**Purpose**: Multi-stage container build  
**Stages**:
1. **Build stage**: Node.js environment for building Vue.js app
2. **Production stage**: Nginx server for serving static files

#### `nginx.conf`
**Purpose**: Production web server configuration  
**Features**:
- CORS headers for OpenTelemetry
- Gzip compression
- Security headers
- API proxy configuration
- Health check endpoints

#### Configuration Files
- `package.json`: Dependencies and build scripts
- `vite.config.js`: Build tool configuration
- `index.html`: HTML template

---

### 🚀 Backend Application (`backend/`)

#### `app.py`
**Purpose**: FastAPI application with comprehensive instrumentation  
**Features**:
- OpenTelemetry automatic and manual instrumentation
- Prometheus metrics (request rate, latency, errors)
- Trace-correlated logging
- Custom span creation
- Security (header masking)

**Key Components**:
```python
TraceFormatter      # Custom log formatter with trace IDs
init_telemetry()    # OpenTelemetry setup
observability_middleware  # Request/response instrumentation
Custom metrics      # Prometheus counters and histograms
API endpoints       # Instrumented business logic
```

**API Endpoints**:
- `GET /` - Root endpoint
- `GET /health` - Health check
- `GET /metrics` - Prometheus metrics
- `GET /api/users` - List users (demo)
- `GET /api/users/{id}` - Get user by ID
- `POST /api/users` - Create user
- `GET /api/slow` - Slow operation simulation
- `GET /api/error` - Error simulation

#### `requirements.txt`
**Purpose**: Python dependency specifications  
**Key Dependencies**:
- FastAPI and Uvicorn (web framework)
- OpenTelemetry Python SDK packages
- Prometheus client
- Type checking and validation libraries

#### `Dockerfile`
**Purpose**: Python runtime container  
**Features**:
- Python 3.11 base image
- System dependencies
- Application code and dependencies
- Health check configuration
- Environment variable setup

---

### 🔄 OpenTelemetry Collector (`otel/`)

#### `otel-collector-config.yml`
**Purpose**: Central telemetry data processing hub  
**Configuration Sections**:

```yaml
receivers:         # Data input sources
  otlp:           # From applications
  prometheus:     # Metrics scraping
  httpcheck:      # Health monitoring

processors:        # Data transformation
  batch:          # Performance optimization
  memory_limiter: # Resource management
  resource:       # Attribute addition
  attributes:     # Data filtering/masking
  filter:         # Content filtering

exporters:         # Data output destinations
  jaeger:         # Traces to Jaeger
  prometheus:     # Metrics exposure
  prometheusremotewrite:  # To VictoriaMetrics
  elasticsearch:  # Logs to Elasticsearch
  logging:        # Debug output

service:           # Pipeline definitions
  pipelines:      # traces, metrics, logs
  extensions:     # health_check, pprof, zpages
```

**Key Features**:
- Multi-protocol data ingestion
- Intelligent data routing
- Performance optimization
- Security filtering
- Debugging capabilities

---

### 📊 Monitoring Configuration

#### `prometheus/prometheus.yml`
**Purpose**: Metrics collection configuration  
**Scrape Targets**:
- OpenTelemetry Collector metrics
- FastAPI application metrics
- Infrastructure service metrics
- Self-monitoring

**Features**:
- Recording rules for performance
- Remote write to VictoriaMetrics
- Service discovery configuration
- Alert rule integration

#### `grafana/provisioning/datasources/datasources.yml`
**Purpose**: Automated Grafana data source configuration  
**Configured Sources**:
- Prometheus (default) - Metrics and alerting
- VictoriaMetrics - Long-term metrics storage
- Jaeger - Distributed tracing
- Elasticsearch - Log search and analysis

**Features**:
- Automatic data source provisioning
- Cross-datasource correlation
- Trace-to-logs linking
- Metrics-to-traces linking

#### `grafana/dashboards/api-observability-dashboard.json`
**Purpose**: Pre-built unified observability dashboard  
**Panels**:
- API request rate over time
- Response time percentiles
- Error rate monitoring
- Active request gauges
- Distributed trace explorer
- Correlated log table

**Features**:
- Real-time data updates
- Interactive trace exploration
- Template variables for filtering
- Alert integration
- Mobile-responsive design

---

### 📚 Documentation (`docs/`)

#### `COMPONENTS_OVERVIEW.md`
**Purpose**: Detailed technical architecture documentation  
**Content**:
- Component descriptions and purposes
- Data flow diagrams
- Health check endpoints
- Resource requirements
- Service dependencies
- Port mappings

#### `CUSTOMIZATION_GUIDE.md`
**Purpose**: How to adapt the stack for your own projects  
**Content**:
- Framework migration guides (React, Angular, Spring Boot, etc.)
- Service configuration templates
- Environment-specific configurations
- Security customization
- Performance tuning
- Migration strategies

#### `OPERATIONS_MANUAL.md`
**Purpose**: Production operations and maintenance  
**Content**:
- Deployment procedures for different environments
- Monitoring and alerting setup
- Troubleshooting guides
- Backup and recovery procedures
- Performance optimization
- Security operations
- Capacity planning

---

### 📖 Documentation Files

#### `README.md`
**Purpose**: Main project documentation and getting started guide  
**Content**:
- Project overview and objectives
- Quick start instructions
- Architecture explanation
- Feature descriptions
- Configuration guidance
- Development setup
- Contributing guidelines

#### `DEPLOYMENT_GUIDE.md`
**Purpose**: Step-by-step deployment instructions  
**Content**:
- Deployment scenarios (demo, custom, production)
- Cloud platform deployment
- Framework integration guides
- Post-deployment validation
- Troubleshooting common issues
- Next steps and resources

#### `PROJECT_STRUCTURE.md` (This File)
**Purpose**: Complete project organization explanation  
**Content**:
- Directory structure overview
- File descriptions and purposes
- Component relationships
- Usage examples
- Quick reference guide

---

## 🔗 Component Relationships

### Data Flow Architecture
```
Frontend Apps → OpenTelemetry Collector → Storage Backends → Grafana
     ↓                    ↓                      ↓
Vue.js/React          Jaeger           Unified Dashboards
   Angular     →    Prometheus      →       + Alerts
FastAPI/Express   VictoriaMetrics        + Correlation
Spring Boot      Elasticsearch          + Analysis
```

### Service Dependencies
```
Infrastructure Services:
├── Elasticsearch (required by Kibana, Collector)
├── Prometheus (required by Grafana)
├── Jaeger (required by Collector)
└── VictoriaMetrics (independent)

Application Services:
├── OpenTelemetry Collector (depends on storage)
├── Backend Applications (depend on Collector)
└── Frontend Applications (depend on Backend)

Visualization Services:
├── Kibana (depends on Elasticsearch)
└── Grafana (depends on all data sources)
```

---

## 🚀 Getting Started Reference

### Quick Commands
```bash
# Deploy everything
./start.sh start

# Check system health
./start.sh status

# View logs
./start.sh logs [service-name]

# Validate system
python3 validate-setup.py

# Clean up
./start.sh cleanup
```

### Key URLs
- **Frontend Demo**: http://localhost
- **Grafana**: http://localhost:3000 (admin/admin)
- **Jaeger**: http://localhost:16686
- **Prometheus**: http://localhost:9090
- **Kibana**: http://localhost:5601

### Configuration Files to Customize
1. **Service Names**: `otel/otel-collector-config.yml`
2. **Application Code**: `backend/app.py`, `frontend/src/`
3. **Dashboards**: `grafana/dashboards/`
4. **Metrics**: `prometheus/prometheus.yml`
5. **Environment**: `docker-compose.yml`

---

## 📝 File Size and Complexity Overview

| Category | Files | Lines of Code | Complexity |
|----------|-------|---------------|------------|
| **Infrastructure** | 3 | ~200 | ⭐⭐⭐ |
| **Frontend** | 7 | ~800 | ⭐⭐⭐⭐ |
| **Backend** | 3 | ~400 | ⭐⭐⭐ |
| **Configuration** | 4 | ~300 | ⭐⭐ |
| **Documentation** | 5 | ~2000 | ⭐ |
| **Scripts** | 2 | ~600 | ⭐⭐ |

**Total**: 24 files, ~4,300 lines of code and documentation

---

This project structure provides a complete, production-ready observability solution that can be easily understood, customized, and deployed for any API-based application.