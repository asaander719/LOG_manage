import { WebTracerProvider } from '@opentelemetry/sdk-trace-web'
import { Resource } from '@opentelemetry/resources'
import { SemanticResourceAttributes } from '@opentelemetry/semantic-conventions'
import { BatchSpanProcessor, ConsoleSpanExporter } from '@opentelemetry/sdk-trace-web'
import { OTLPTraceExporter } from '@opentelemetry/exporter-trace-otlp-http'
import { registerInstrumentations } from '@opentelemetry/instrumentation'
import { getWebAutoInstrumentations } from '@opentelemetry/auto-instrumentations-web'
import { FetchInstrumentation } from '@opentelemetry/instrumentation-fetch'
import { XMLHttpRequestInstrumentation } from '@opentelemetry/instrumentation-xml-http-request'
import { UserInteractionInstrumentation } from '@opentelemetry/instrumentation-user-interaction'
import { DocumentLoadInstrumentation } from '@opentelemetry/instrumentation-document-load'
import { trace, context, propagation } from '@opentelemetry/api'
import { W3CTraceContextPropagator } from '@opentelemetry/core'
import { CompositePropagator, W3CBaggagePropagator } from '@opentelemetry/core'

// Custom logger for structured logging with trace correlation
class TraceLogger {
  constructor() {
    this.logs = []
  }

  log(level, message, attributes = {}) {
    const span = trace.getActiveSpan()
    const spanContext = span?.spanContext()
    
    const logEntry = {
      timestamp: new Date().toISOString(),
      level,
      message,
      trace_id: spanContext?.traceId || '00000000000000000000000000000000',
      span_id: spanContext?.spanId || '0000000000000000',
      attributes: {
        ...attributes,
        'service.name': 'frontend-vue',
        'service.version': '1.0.0',
        'deployment.environment': 'development'
      }
    }

    // Store log locally
    this.logs.push(logEntry)

    // Send to collector if configured
    this.sendLog(logEntry)

    // Also log to console
    console.log(`[${level}] [trace_id=${logEntry.trace_id}] ${message}`, attributes)
  }

  info(message, attributes) {
    this.log('INFO', message, attributes)
  }

  warn(message, attributes) {
    this.log('WARN', message, attributes)
  }

  error(message, attributes) {
    this.log('ERROR', message, attributes)
  }

  debug(message, attributes) {
    this.log('DEBUG', message, attributes)
  }

  async sendLog(logEntry) {
    try {
      // Send structured log to OpenTelemetry Collector
      await fetch('http://localhost:4318/v1/logs', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          resourceLogs: [{
            resource: {
              attributes: [
                { key: 'service.name', value: { stringValue: 'frontend-vue' } },
                { key: 'service.version', value: { stringValue: '1.0.0' } }
              ]
            },
            scopeLogs: [{
              scope: { name: 'frontend-logger' },
              logRecords: [{
                timeUnixNano: Date.now() * 1000000,
                severityText: logEntry.level,
                body: { stringValue: logEntry.message },
                attributes: Object.entries(logEntry.attributes).map(([key, value]) => ({
                  key,
                  value: { stringValue: String(value) }
                })),
                traceId: logEntry.trace_id,
                spanId: logEntry.span_id
              }]
            }]
          }]
        })
      })
    } catch (error) {
      console.warn('Failed to send log to collector:', error)
    }
  }

  getLogs() {
    return this.logs
  }
}

// Global logger instance
export const logger = new TraceLogger()

// HTTP interceptor to add trace headers and logging
class HTTPInterceptor {
  constructor() {
    this.originalFetch = window.fetch
    this.setupFetchInterceptor()
  }

  setupFetchInterceptor() {
    window.fetch = async (input, init = {}) => {
      const url = typeof input === 'string' ? input : input.url
      const method = init.method || 'GET'
      
      // Create span for HTTP request
      const tracer = trace.getTracer('frontend-http')
      
      return tracer.startActiveSpan(`HTTP ${method}`, async (span) => {
        const startTime = Date.now()
        
        try {
          // Set span attributes
          span.setAttributes({
            'http.method': method,
            'http.url': url,
            'http.scheme': new URL(url, window.location.origin).protocol.replace(':', ''),
            'http.target': new URL(url, window.location.origin).pathname,
            'user_agent.original': navigator.userAgent
          })

          // Inject trace context into headers
          const headers = new Headers(init.headers || {})
          const carrier = {}
          
          propagation.inject(context.active(), carrier)
          
          // Add trace headers
          Object.entries(carrier).forEach(([key, value]) => {
            headers.set(key, value)
          })

          // Add custom correlation headers
          const spanContext = span.spanContext()
          headers.set('X-Trace-Id', spanContext.traceId)
          headers.set('X-Span-Id', spanContext.spanId)

          // Log request start
          logger.info(`HTTP request started: ${method} ${url}`, {
            'http.method': method,
            'http.url': url,
            'request.headers': Object.fromEntries(headers.entries())
          })

          // Make the actual request
          const response = await this.originalFetch(input, {
            ...init,
            headers
          })

          const duration = Date.now() - startTime

          // Set response attributes
          span.setAttributes({
            'http.status_code': response.status,
            'http.response.duration_ms': duration
          })

          // Log response
          logger.info(`HTTP request completed: ${method} ${url} - ${response.status} (${duration}ms)`, {
            'http.method': method,
            'http.url': url,
            'http.status_code': response.status,
            'http.response.duration_ms': duration
          })

          // Set span status based on response
          if (response.status >= 400) {
            span.recordException(new Error(`HTTP ${response.status}: ${response.statusText}`))
            span.setStatus({
              code: trace.SpanStatusCode.ERROR,
              message: `HTTP ${response.status}`
            })
          } else {
            span.setStatus({ code: trace.SpanStatusCode.OK })
          }

          return response

        } catch (error) {
          const duration = Date.now() - startTime
          
          // Record error
          span.recordException(error)
          span.setStatus({
            code: trace.SpanStatusCode.ERROR,
            message: error.message
          })

          // Log error
          logger.error(`HTTP request failed: ${method} ${url} - ${error.message}`, {
            'http.method': method,
            'http.url': url,
            'error.message': error.message,
            'error.type': error.constructor.name,
            'http.response.duration_ms': duration
          })

          throw error
        } finally {
          span.end()
        }
      })
    }
  }
}

export function initTelemetry() {
  // Resource configuration
  const resource = new Resource({
    [SemanticResourceAttributes.SERVICE_NAME]: 'frontend-vue',
    [SemanticResourceAttributes.SERVICE_VERSION]: '1.0.0',
    [SemanticResourceAttributes.SERVICE_INSTANCE_ID]: 'frontend-1',
    [SemanticResourceAttributes.DEPLOYMENT_ENVIRONMENT]: 'development'
  })

  // Tracer provider
  const provider = new WebTracerProvider({
    resource: resource
  })

  // Configure trace exporters
  const collectorExporter = new OTLPTraceExporter({
    url: 'http://localhost:4318/v1/traces',
    headers: {
      'Content-Type': 'application/json'
    }
  })

  const consoleExporter = new ConsoleSpanExporter()

  // Add span processors
  provider.addSpanProcessor(new BatchSpanProcessor(collectorExporter, {
    maxQueueSize: 100,
    scheduledDelayMillis: 500,
    exportTimeoutMillis: 30000,
    maxExportBatchSize: 10
  }))

  // Add console exporter for debugging (optional)
  if (process.env.NODE_ENV === 'development') {
    provider.addSpanProcessor(new BatchSpanProcessor(consoleExporter))
  }

  // Register the provider
  provider.register({
    propagator: new CompositePropagator({
      propagators: [
        new W3CTraceContextPropagator(),
        new W3CBaggagePropagator()
      ]
    })
  })

  // Register instrumentations
  registerInstrumentations({
    instrumentations: [
      // Auto-instrumentations for common web APIs
      getWebAutoInstrumentations({
        '@opentelemetry/instrumentation-fetch': {
          propagateTraceHeaderCorsUrls: /.*/,
          clearTimingResources: true,
          applyCustomAttributesOnSpan: (span, request, response) => {
            span.setAttributes({
              'custom.request_size': request.headers.get('content-length') || 0,
              'custom.response_size': response.headers.get('content-length') || 0
            })
          }
        },
        '@opentelemetry/instrumentation-xml-http-request': {
          propagateTraceHeaderCorsUrls: /.*/
        },
        '@opentelemetry/instrumentation-user-interaction': {
          eventNames: ['click', 'submit', 'keypress', 'load']
        },
        '@opentelemetry/instrumentation-document-load': {}
      }),

      // Additional custom instrumentations
      new FetchInstrumentation({
        propagateTraceHeaderCorsUrls: /.*/,
        clearTimingResources: true
      }),

      new XMLHttpRequestInstrumentation({
        propagateTraceHeaderCorsUrls: /.*/
      }),

      new UserInteractionInstrumentation({
        eventNames: ['click', 'submit', 'keypress']
      }),

      new DocumentLoadInstrumentation()
    ]
  })

  // Initialize HTTP interceptor for additional logging
  new HTTPInterceptor()

  // Store references globally for access
  window.otel = {
    trace,
    provider,
    logger
  }

  // Log initialization
  logger.info('OpenTelemetry initialized for frontend', {
    'service.name': 'frontend-vue',
    'service.version': '1.0.0'
  })

  // Track page loads
  const tracer = trace.getTracer('frontend-page')
  tracer.startActiveSpan('page_load', (span) => {
    span.setAttributes({
      'page.url': window.location.href,
      'page.title': document.title,
      'user_agent.original': navigator.userAgent
    })
    
    logger.info('Page loaded', {
      'page.url': window.location.href,
      'page.title': document.title
    })
    
    span.end()
  })

  return { provider, logger }
}