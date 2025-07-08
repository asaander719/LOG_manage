import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import { initTelemetry } from './telemetry'

// Initialize OpenTelemetry
initTelemetry()

// Create Vue app
const app = createApp(App)

// Use router
app.use(router)

// Global error handler
app.config.errorHandler = (error, instance, info) => {
  console.error('Vue error:', error)
  console.error('Error info:', info)
  
  // Report error to telemetry
  if (window.otel && window.otel.trace) {
    const span = window.otel.trace.getActiveSpan()
    if (span) {
      span.recordException(error)
      span.setStatus({ code: window.otel.trace.SpanStatusCode.ERROR, message: error.message })
    }
  }
}

// Mount the app
app.mount('#app')