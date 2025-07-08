import json
import logging
import time
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

# OpenTelemetry imports
from opentelemetry import trace, metrics, baggage
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.propagate import inject, extract
from opentelemetry.trace.status import Status, StatusCode

# Prometheus metrics
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
import prometheus_client

# Custom logging formatter with trace_id
class TraceFormatter(logging.Formatter):
    def format(self, record):
        trace_id = None
        span_id = None
        
        # Get current span context
        span = trace.get_current_span()
        if span:
            span_context = span.get_span_context()
            if span_context.is_valid:
                trace_id = format(span_context.trace_id, '032x')
                span_id = format(span_context.span_id, '016x')
        
        # Add trace info to log record
        record.trace_id = trace_id or "00000000000000000000000000000000"
        record.span_id = span_id or "0000000000000000"
        
        return super().format(record)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] [trace_id=%(trace_id)s span_id=%(span_id)s] %(name)s: %(message)s'
)

# Set custom formatter for all loggers
for handler in logging.root.handlers:
    handler.setFormatter(TraceFormatter(
        '%(asctime)s [%(levelname)s] [trace_id=%(trace_id)s span_id=%(span_id)s] %(name)s: %(message)s'
    ))

logger = logging.getLogger(__name__)

# Initialize OpenTelemetry
def init_telemetry():
    # Resource information
    resource = Resource.create({
        "service.name": "fastapi-backend",
        "service.version": "1.0.0",
        "service.instance.id": "backend-1",
        "deployment.environment": "development"
    })
    
    # Trace provider
    trace_provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(trace_provider)
    
    # OTLP exporter for traces
    otlp_exporter = OTLPSpanExporter(
        endpoint="http://otel-collector:4317",
        insecure=True
    )
    
    span_processor = BatchSpanProcessor(otlp_exporter)
    trace_provider.add_span_processor(span_processor)
    
    # Metrics provider
    metric_reader = PeriodicExportingMetricReader(
        OTLPMetricExporter(
            endpoint="http://otel-collector:4317",
            insecure=True
        ),
        export_interval_millis=10000
    )
    
    metrics_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
    metrics.set_meter_provider(metrics_provider)
    
    # Initialize instrumentations
    LoggingInstrumentor().instrument(set_logging_format=True)
    RequestsInstrumentor().instrument()

# Initialize telemetry
init_telemetry()

# Get tracer and meter
tracer = trace.get_tracer(__name__)
meter = metrics.get_meter(__name__)

# Prometheus metrics
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code']
)

REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

ACTIVE_REQUESTS = Gauge(
    'http_requests_active',
    'Number of active HTTP requests'
)

ERROR_COUNT = Counter(
    'http_errors_total',
    'Total HTTP errors',
    ['method', 'endpoint', 'error_type']
)

# OpenTelemetry metrics
otel_request_counter = meter.create_counter(
    name="api_requests_total",
    description="Total number of API requests",
    unit="1"
)

otel_request_duration = meter.create_histogram(
    name="api_request_duration",
    description="API request duration",
    unit="ms"
)

# Application lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("FastAPI application starting up...")
    yield
    logger.info("FastAPI application shutting down...")

# Create FastAPI app
app = FastAPI(
    title="Observability Demo API",
    version="1.0.0",
    description="FastAPI backend with comprehensive observability",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Instrument FastAPI
FastAPIInstrumentor.instrument_app(app)

# Middleware for metrics and logging
@app.middleware("http")
async def observability_middleware(request: Request, call_next):
    start_time = time.time()
    
    # Extract trace context from headers
    carrier = dict(request.headers)
    ctx = extract(carrier)
    
    with tracer.start_as_current_span(
        f"{request.method} {request.url.path}",
        context=ctx
    ) as span:
        # Increment active requests
        ACTIVE_REQUESTS.inc()
        
        # Add span attributes
        span.set_attribute("http.method", request.method)
        span.set_attribute("http.url", str(request.url))
        span.set_attribute("http.scheme", request.url.scheme)
        span.set_attribute("http.host", request.url.hostname)
        span.set_attribute("http.target", request.url.path)
        span.set_attribute("user_agent.original", request.headers.get("user-agent", ""))
        
        # Log request
        logger.info(
            f"Request started: {request.method} {request.url.path}",
            extra={
                "method": request.method,
                "path": request.url.path,
                "user_agent": request.headers.get("user-agent", ""),
                "client_ip": request.client.host if request.client else None
            }
        )
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Add response attributes to span
            span.set_attribute("http.status_code", response.status_code)
            span.set_attribute("http.response.duration_ms", duration * 1000)
            
            # Record metrics
            REQUEST_COUNT.labels(
                method=request.method,
                endpoint=request.url.path,
                status_code=response.status_code
            ).inc()
            
            REQUEST_DURATION.labels(
                method=request.method,
                endpoint=request.url.path
            ).observe(duration)
            
            # OpenTelemetry metrics
            otel_request_counter.add(1, {
                "method": request.method,
                "endpoint": request.url.path,
                "status_code": str(response.status_code)
            })
            
            otel_request_duration.record(duration * 1000, {
                "method": request.method,
                "endpoint": request.url.path
            })
            
            # Log response
            logger.info(
                f"Request completed: {request.method} {request.url.path} - {response.status_code} ({duration:.3f}s)",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration_ms": duration * 1000
                }
            )
            
            # Set span status
            if response.status_code >= 400:
                span.set_status(Status(StatusCode.ERROR, f"HTTP {response.status_code}"))
            else:
                span.set_status(Status(StatusCode.OK))
                
            return response
            
        except Exception as e:
            # Record error metrics
            ERROR_COUNT.labels(
                method=request.method,
                endpoint=request.url.path,
                error_type=type(e).__name__
            ).inc()
            
            # Set span error status
            span.set_status(Status(StatusCode.ERROR, str(e)))
            span.record_exception(e)
            
            # Log error
            logger.error(
                f"Request failed: {request.method} {request.url.path} - {str(e)}",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "error": str(e),
                    "error_type": type(e).__name__
                },
                exc_info=True
            )
            
            raise
        finally:
            # Decrement active requests
            ACTIVE_REQUESTS.dec()

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": time.time()}

# Metrics endpoint for Prometheus
@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

# API endpoints
@app.get("/")
async def root():
    with tracer.start_as_current_span("root_handler") as span:
        span.set_attribute("custom.handler", "root")
        logger.info("Root endpoint accessed")
        return {"message": "FastAPI Backend with Observability", "version": "1.0.0"}

@app.get("/api/users")
async def get_users():
    with tracer.start_as_current_span("get_users") as span:
        span.set_attribute("operation", "list_users")
        
        # Simulate some work
        await simulate_work(0.1, 0.3)
        
        users = [
            {"id": 1, "name": "Alice", "email": "alice@example.com"},
            {"id": 2, "name": "Bob", "email": "bob@example.com"},
            {"id": 3, "name": "Charlie", "email": "charlie@example.com"}
        ]
        
        span.set_attribute("users.count", len(users))
        logger.info(f"Retrieved {len(users)} users")
        
        return {"users": users, "count": len(users)}

@app.get("/api/users/{user_id}")
async def get_user(user_id: int):
    with tracer.start_as_current_span("get_user") as span:
        span.set_attribute("user.id", user_id)
        span.set_attribute("operation", "get_user")
        
        # Simulate database lookup
        await simulate_work(0.05, 0.15)
        
        if user_id > 10:
            logger.warning(f"User not found: {user_id}")
            span.set_attribute("error", "user_not_found")
            raise HTTPException(status_code=404, detail="User not found")
        
        user = {
            "id": user_id,
            "name": f"User {user_id}",
            "email": f"user{user_id}@example.com"
        }
        
        logger.info(f"Retrieved user {user_id}")
        return user

@app.post("/api/users")
async def create_user(user_data: Dict[str, Any]):
    with tracer.start_as_current_span("create_user") as span:
        span.set_attribute("operation", "create_user")
        span.set_attribute("user.name", user_data.get("name", ""))
        
        # Simulate user creation
        await simulate_work(0.2, 0.5)
        
        new_user = {
            "id": 100,
            "name": user_data.get("name"),
            "email": user_data.get("email"),
            "created_at": time.time()
        }
        
        logger.info(f"Created user: {new_user['name']}")
        return new_user

@app.get("/api/slow")
async def slow_endpoint():
    with tracer.start_as_current_span("slow_operation") as span:
        span.set_attribute("operation", "slow_processing")
        
        # Simulate slow operation
        await simulate_work(2.0, 3.0)
        
        logger.info("Slow operation completed")
        return {"message": "This was a slow operation", "duration": "2-3 seconds"}

@app.get("/api/error")
async def error_endpoint():
    with tracer.start_as_current_span("error_operation") as span:
        span.set_attribute("operation", "intentional_error")
        
        logger.error("Intentional error triggered")
        raise HTTPException(status_code=500, detail="Intentional server error for testing")

# Helper function to simulate work
async def simulate_work(min_duration: float, max_duration: float):
    import asyncio
    import random
    duration = random.uniform(min_duration, max_duration)
    await asyncio.sleep(duration)

if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )