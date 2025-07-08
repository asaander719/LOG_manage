<template>
  <div id="app">
    <header class="app-header">
      <h1>🔍 API Observability Demo</h1>
      <p>Frontend Vue.js → Backend FastAPI with OpenTelemetry Tracing</p>
    </header>

    <main class="main-content">
      <!-- API Test Section -->
      <section class="api-section">
        <h2>API Testing</h2>
        
        <div class="button-group">
          <button @click="testGetUsers" :disabled="loading.users" class="btn btn-primary">
            {{ loading.users ? 'Loading...' : 'Get Users' }}
          </button>
          
          <button @click="testGetUser" :disabled="loading.user" class="btn btn-primary">
            {{ loading.user ? 'Loading...' : 'Get User by ID' }}
          </button>
          
          <button @click="testCreateUser" :disabled="loading.create" class="btn btn-success">
            {{ loading.create ? 'Creating...' : 'Create User' }}
          </button>
          
          <button @click="testSlowOperation" :disabled="loading.slow" class="btn btn-warning">
            {{ loading.slow ? 'Processing...' : 'Slow Operation (2-3s)' }}
          </button>
          
          <button @click="testErrorEndpoint" :disabled="loading.error" class="btn btn-danger">
            {{ loading.error ? 'Loading...' : 'Test Error (500)' }}
          </button>
        </div>

        <!-- Results Display -->
        <div v-if="lastResult" class="result-section">
          <h3>Last API Result:</h3>
          <div class="result-box">
            <div class="result-meta">
              <span class="trace-id">Trace ID: {{ lastTraceId }}</span>
              <span class="duration">Duration: {{ lastDuration }}ms</span>
              <span class="status" :class="lastStatus >= 400 ? 'error' : 'success'">
                Status: {{ lastStatus }}
              </span>
            </div>
            <pre>{{ JSON.stringify(lastResult, null, 2) }}</pre>
          </div>
        </div>

        <!-- Error Display -->
        <div v-if="lastError" class="error-section">
          <h3>Last Error:</h3>
          <div class="error-box">
            <div class="error-meta">
              <span class="trace-id">Trace ID: {{ lastTraceId }}</span>
              <span class="error-type">{{ lastError.type }}</span>
            </div>
            <pre>{{ lastError.message }}</pre>
          </div>
        </div>
      </section>

      <!-- Telemetry Info -->
      <section class="telemetry-section">
        <h2>📊 Telemetry Information</h2>
        
        <div class="telemetry-grid">
          <div class="telemetry-card">
            <h3>Current Session</h3>
            <p><strong>Trace ID:</strong> {{ currentTraceId }}</p>
            <p><strong>Requests Made:</strong> {{ requestCount }}</p>
            <p><strong>Errors:</strong> {{ errorCount }}</p>
          </div>
          
          <div class="telemetry-card">
            <h3>Monitoring Links</h3>
            <ul class="monitoring-links">
              <li><a href="http://localhost:16686" target="_blank">🔗 Jaeger Traces</a></li>
              <li><a href="http://localhost:9090" target="_blank">📈 Prometheus Metrics</a></li>
              <li><a href="http://localhost:5601" target="_blank">📋 Kibana Logs</a></li>
              <li><a href="http://localhost:3000" target="_blank">📊 Grafana Dashboards</a></li>
            </ul>
          </div>
          
          <div class="telemetry-card">
            <h3>Recent Logs</h3>
            <div class="logs-container">
              <div v-for="log in recentLogs" :key="log.timestamp" class="log-entry">
                <span class="log-timestamp">{{ formatTime(log.timestamp) }}</span>
                <span class="log-level" :class="log.level.toLowerCase()">{{ log.level }}</span>
                <span class="log-message">{{ log.message }}</span>
              </div>
            </div>
          </div>
        </div>
      </section>
    </main>
  </div>
</template>

<script>
import { logger } from './telemetry'
import { trace } from '@opentelemetry/api'

export default {
  name: 'App',
  data() {
    return {
      loading: {
        users: false,
        user: false,
        create: false,
        slow: false,
        error: false
      },
      lastResult: null,
      lastError: null,
      lastTraceId: '',
      lastDuration: 0,
      lastStatus: 0,
      requestCount: 0,
      errorCount: 0,
      recentLogs: []
    }
  },
  computed: {
    currentTraceId() {
      const span = trace.getActiveSpan()
      if (span) {
        const spanContext = span.spanContext()
        return spanContext.traceId || 'No active trace'
      }
      return 'No active trace'
    }
  },
  mounted() {
    // Start monitoring logs
    this.startLogMonitoring()
    
    // Initial log
    logger.info('App component mounted', {
      'component': 'App',
      'action': 'mounted'
    })
  },
  methods: {
    async makeApiCall(method, endpoint, data = null) {
      const tracer = trace.getTracer('frontend-api')
      
      return tracer.startActiveSpan(`API ${method} ${endpoint}`, async (span) => {
        const startTime = Date.now()
        this.requestCount++
        
        try {
          span.setAttributes({
            'api.method': method,
            'api.endpoint': endpoint,
            'api.request_count': this.requestCount
          })

          const url = `http://localhost:8000${endpoint}`
          const options = {
            method,
            headers: {
              'Content-Type': 'application/json',
            }
          }

          if (data) {
            options.body = JSON.stringify(data)
          }

          logger.info(`Making API call: ${method} ${endpoint}`, {
            'api.method': method,
            'api.endpoint': endpoint,
            'api.url': url
          })

          const response = await fetch(url, options)
          const responseData = await response.json()
          
          this.lastDuration = Date.now() - startTime
          this.lastStatus = response.status
          this.lastTraceId = span.spanContext().traceId

          if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${responseData.detail || 'Unknown error'}`)
          }

          this.lastResult = responseData
          this.lastError = null

          logger.info(`API call successful: ${method} ${endpoint}`, {
            'api.method': method,
            'api.endpoint': endpoint,
            'api.status_code': response.status,
            'api.duration_ms': this.lastDuration
          })

          return responseData

        } catch (error) {
          this.lastDuration = Date.now() - startTime
          this.lastError = {
            message: error.message,
            type: error.constructor.name
          }
          this.lastResult = null
          this.errorCount++
          
          span.recordException(error)
          span.setStatus({
            code: trace.SpanStatusCode.ERROR,
            message: error.message
          })

          logger.error(`API call failed: ${method} ${endpoint}`, {
            'api.method': method,
            'api.endpoint': endpoint,
            'error.message': error.message,
            'error.type': error.constructor.name,
            'api.duration_ms': this.lastDuration
          })

          throw error
        } finally {
          span.end()
        }
      })
    },

    async testGetUsers() {
      this.loading.users = true
      try {
        await this.makeApiCall('GET', '/api/users')
      } finally {
        this.loading.users = false
      }
    },

    async testGetUser() {
      this.loading.user = true
      try {
        const userId = Math.floor(Math.random() * 12) + 1 // Random ID 1-12 (some will 404)
        await this.makeApiCall('GET', `/api/users/${userId}`)
      } finally {
        this.loading.user = false
      }
    },

    async testCreateUser() {
      this.loading.create = true
      try {
        const userData = {
          name: `User ${Date.now()}`,
          email: `user${Date.now()}@example.com`
        }
        await this.makeApiCall('POST', '/api/users', userData)
      } finally {
        this.loading.create = false
      }
    },

    async testSlowOperation() {
      this.loading.slow = true
      try {
        await this.makeApiCall('GET', '/api/slow')
      } finally {
        this.loading.slow = false
      }
    },

    async testErrorEndpoint() {
      this.loading.error = true
      try {
        await this.makeApiCall('GET', '/api/error')
      } catch (error) {
        // Expected error, don't rethrow
      } finally {
        this.loading.error = false
      }
    },

    startLogMonitoring() {
      // Monitor logs from the logger
      setInterval(() => {
        if (window.otel && window.otel.logger) {
          const logs = window.otel.logger.getLogs()
          this.recentLogs = logs.slice(-10).reverse() // Show last 10 logs, newest first
        }
      }, 1000)
    },

    formatTime(timestamp) {
      return new Date(timestamp).toLocaleTimeString()
    }
  }
}
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  min-height: 100vh;
}

#app {
  min-height: 100vh;
  color: #333;
}

.app-header {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  padding: 2rem;
  text-align: center;
  box-shadow: 0 2px 20px rgba(0, 0, 0, 0.1);
}

.app-header h1 {
  font-size: 2.5rem;
  margin-bottom: 0.5rem;
  background: linear-gradient(45deg, #667eea, #764ba2);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.app-header p {
  font-size: 1.1rem;
  color: #666;
}

.main-content {
  padding: 2rem;
  max-width: 1200px;
  margin: 0 auto;
}

.api-section, .telemetry-section {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-radius: 15px;
  padding: 2rem;
  margin-bottom: 2rem;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
}

.api-section h2, .telemetry-section h2 {
  margin-bottom: 1.5rem;
  color: #333;
}

.button-group {
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
  margin-bottom: 2rem;
}

.btn {
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 8px;
  font-size: 1rem;
  cursor: pointer;
  transition: all 0.3s ease;
  font-weight: 500;
}

.btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

.btn-primary {
  background: #667eea;
  color: white;
}

.btn-success {
  background: #28a745;
  color: white;
}

.btn-warning {
  background: #ffc107;
  color: #212529;
}

.btn-danger {
  background: #dc3545;
  color: white;
}

.result-section, .error-section {
  margin-top: 2rem;
}

.result-box, .error-box {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 1rem;
  border-left: 4px solid #667eea;
}

.error-box {
  border-left-color: #dc3545;
  background: #fff5f5;
}

.result-meta, .error-meta {
  display: flex;
  gap: 1rem;
  margin-bottom: 1rem;
  font-size: 0.9rem;
}

.trace-id {
  background: #e9ecef;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-family: monospace;
}

.duration, .status {
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-weight: 500;
}

.status.success {
  background: #d4edda;
  color: #155724;
}

.status.error {
  background: #f8d7da;
  color: #721c24;
}

.error-type {
  background: #f8d7da;
  color: #721c24;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-weight: 500;
}

.telemetry-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 1.5rem;
}

.telemetry-card {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 1.5rem;
  border: 1px solid #e9ecef;
}

.telemetry-card h3 {
  margin-bottom: 1rem;
  color: #495057;
}

.monitoring-links {
  list-style: none;
}

.monitoring-links li {
  margin-bottom: 0.5rem;
}

.monitoring-links a {
  color: #667eea;
  text-decoration: none;
  font-weight: 500;
}

.monitoring-links a:hover {
  text-decoration: underline;
}

.logs-container {
  max-height: 200px;
  overflow-y: auto;
  background: #ffffff;
  border-radius: 4px;
  padding: 0.5rem;
}

.log-entry {
  display: flex;
  gap: 0.5rem;
  padding: 0.25rem 0;
  border-bottom: 1px solid #f1f3f4;
  font-size: 0.85rem;
}

.log-timestamp {
  color: #6c757d;
  font-family: monospace;
  min-width: 80px;
}

.log-level {
  font-weight: 500;
  min-width: 50px;
  text-align: center;
  border-radius: 3px;
  padding: 0 0.25rem;
}

.log-level.info {
  background: #d1ecf1;
  color: #0c5460;
}

.log-level.warn {
  background: #fff3cd;
  color: #856404;
}

.log-level.error {
  background: #f8d7da;
  color: #721c24;
}

.log-message {
  flex: 1;
  color: #495057;
}

pre {
  background: #ffffff;
  padding: 1rem;
  border-radius: 4px;
  border: 1px solid #e9ecef;
  font-size: 0.9rem;
  overflow-x: auto;
  white-space: pre-wrap;
  word-wrap: break-word;
}

@media (max-width: 768px) {
  .button-group {
    flex-direction: column;
  }
  
  .result-meta, .error-meta {
    flex-direction: column;
    gap: 0.5rem;
  }
  
  .telemetry-grid {
    grid-template-columns: 1fr;
  }
}
</style>