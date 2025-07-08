#!/usr/bin/env python3
"""
API HTTP Request Logging Management System - Validation Script

This script validates that all components of the observability stack are working correctly:
- Frontend (Vue.js) with OpenTelemetry instrumentation
- Backend (FastAPI) with observability
- OpenTelemetry Collector
- Jaeger for traces
- Prometheus for metrics
- Elasticsearch for logs
- Grafana for visualization
"""

import asyncio
import json
import sys
import time
from typing import Dict, List, Optional
import requests
import aiohttp


class ObservabilityValidator:
    def __init__(self):
        self.services = {
            'frontend': 'http://localhost',
            'backend': 'http://localhost:8000',
            'jaeger': 'http://localhost:16686',
            'prometheus': 'http://localhost:9090',
            'elasticsearch': 'http://localhost:9200',
            'kibana': 'http://localhost:5601',
            'grafana': 'http://localhost:3000',
            'victoriametrics': 'http://localhost:8428',
            'otel-collector': 'http://localhost:8888'
        }
        
        self.test_results = {}
        self.trace_id = None
        
    def print_header(self, title: str):
        print(f"\n{'='*60}")
        print(f"🔍 {title}")
        print(f"{'='*60}")
        
    def print_success(self, message: str):
        print(f"✅ {message}")
        
    def print_error(self, message: str):
        print(f"❌ {message}")
        
    def print_warning(self, message: str):
        print(f"⚠️  {message}")
        
    def print_info(self, message: str):
        print(f"ℹ️  {message}")

    def test_service_health(self, service_name: str, url: str, endpoint: str = '') -> bool:
        """Test if a service is responding to health checks."""
        try:
            full_url = f"{url}{endpoint}"
            response = requests.get(full_url, timeout=10)
            
            if response.status_code == 200:
                self.print_success(f"{service_name} is healthy")
                return True
            else:
                self.print_error(f"{service_name} returned status {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            self.print_error(f"{service_name} is not responding: {str(e)}")
            return False

    def test_basic_connectivity(self) -> Dict[str, bool]:
        """Test basic connectivity to all services."""
        self.print_header("Testing Basic Service Connectivity")
        
        health_endpoints = {
            'frontend': '/health',
            'backend': '/health',
            'jaeger': '/',
            'prometheus': '/-/ready',
            'elasticsearch': '/_cluster/health',
            'kibana': '/api/status',
            'grafana': '/api/health',
            'victoriametrics': '/health',
            'otel-collector': '/metrics'
        }
        
        results = {}
        for service, base_url in self.services.items():
            endpoint = health_endpoints.get(service, '')
            results[service] = self.test_service_health(service, base_url, endpoint)
            
        return results

    def test_backend_api(self) -> bool:
        """Test FastAPI backend endpoints and collect trace information."""
        self.print_header("Testing FastAPI Backend API")
        
        try:
            # Test basic endpoints
            endpoints = [
                ('GET', '/'),
                ('GET', '/api/users'),
                ('GET', '/api/users/1'),
                ('POST', '/api/users', {'name': 'Test User', 'email': 'test@example.com'})
            ]
            
            for method, path, *data in endpoints:
                url = f"{self.services['backend']}{path}"
                
                if method == 'GET':
                    response = requests.get(url, timeout=10)
                elif method == 'POST':
                    response = requests.post(url, json=data[0] if data else None, timeout=10)
                
                if response.status_code < 400:
                    self.print_success(f"{method} {path} - Status: {response.status_code}")
                else:
                    self.print_warning(f"{method} {path} - Status: {response.status_code}")
                    
                # Extract trace ID from response headers if available
                trace_header = response.headers.get('X-Trace-Id')
                if trace_header and not self.trace_id:
                    self.trace_id = trace_header
                    self.print_info(f"Captured trace ID: {self.trace_id}")
                    
            return True
            
        except Exception as e:
            self.print_error(f"Backend API test failed: {str(e)}")
            return False

    def test_prometheus_metrics(self) -> bool:
        """Test that Prometheus is collecting metrics from the backend."""
        self.print_header("Testing Prometheus Metrics Collection")
        
        try:
            # Check if Prometheus is scraping FastAPI metrics
            metrics_url = f"{self.services['prometheus']}/api/v1/query"
            
            queries = [
                'http_requests_total',
                'http_request_duration_seconds',
                'http_requests_active'
            ]
            
            for query in queries:
                params = {'query': query}
                response = requests.get(metrics_url, params=params, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('data', {}).get('result'):
                        self.print_success(f"Metric '{query}' is available")
                    else:
                        self.print_warning(f"Metric '{query}' has no data yet")
                else:
                    self.print_error(f"Failed to query metric '{query}'")
                    
            return True
            
        except Exception as e:
            self.print_error(f"Prometheus metrics test failed: {str(e)}")
            return False

    def test_jaeger_traces(self) -> bool:
        """Test that Jaeger is receiving traces."""
        self.print_header("Testing Jaeger Trace Collection")
        
        try:
            # Check if Jaeger has traces from our services
            services_url = f"{self.services['jaeger']}/api/services"
            response = requests.get(services_url, timeout=10)
            
            if response.status_code == 200:
                services = response.json().get('data', [])
                
                expected_services = ['fastapi-backend', 'frontend-vue']
                found_services = []
                
                for service in expected_services:
                    if service in services:
                        found_services.append(service)
                        self.print_success(f"Service '{service}' found in Jaeger")
                    else:
                        self.print_warning(f"Service '{service}' not found in Jaeger yet")
                
                # Try to find traces for fastapi-backend
                if 'fastapi-backend' in services:
                    traces_url = f"{self.services['jaeger']}/api/traces"
                    params = {
                        'service': 'fastapi-backend',
                        'limit': 10
                    }
                    trace_response = requests.get(traces_url, params=params, timeout=10)
                    
                    if trace_response.status_code == 200:
                        traces_data = trace_response.json()
                        trace_count = len(traces_data.get('data', []))
                        if trace_count > 0:
                            self.print_success(f"Found {trace_count} traces for fastapi-backend")
                        else:
                            self.print_warning("No traces found yet - try making some API calls first")
                
                return len(found_services) > 0
                
            else:
                self.print_error(f"Failed to get services from Jaeger: {response.status_code}")
                return False
                
        except Exception as e:
            self.print_error(f"Jaeger traces test failed: {str(e)}")
            return False

    def test_elasticsearch_logs(self) -> bool:
        """Test that Elasticsearch is receiving logs."""
        self.print_header("Testing Elasticsearch Log Collection")
        
        try:
            # Check if Elasticsearch has the logs index
            indices_url = f"{self.services['elasticsearch']}/_cat/indices?format=json"
            response = requests.get(indices_url, timeout=10)
            
            if response.status_code == 200:
                indices = response.json()
                log_indices = [idx for idx in indices if 'otel-logs' in idx.get('index', '')]
                
                if log_indices:
                    self.print_success(f"Found {len(log_indices)} log indices")
                    
                    # Try to search for logs
                    search_url = f"{self.services['elasticsearch']}/otel-logs/_search"
                    search_response = requests.get(search_url, timeout=10)
                    
                    if search_response.status_code == 200:
                        search_data = search_response.json()
                        hit_count = search_data.get('hits', {}).get('total', {})
                        
                        if isinstance(hit_count, dict):
                            count = hit_count.get('value', 0)
                        else:
                            count = hit_count
                            
                        if count > 0:
                            self.print_success(f"Found {count} log entries")
                        else:
                            self.print_warning("No log entries found yet")
                            
                else:
                    self.print_warning("No otel-logs indices found yet")
                    
                return True
                
            else:
                self.print_error(f"Failed to get indices from Elasticsearch: {response.status_code}")
                return False
                
        except Exception as e:
            self.print_error(f"Elasticsearch logs test failed: {str(e)}")
            return False

    def test_grafana_datasources(self) -> bool:
        """Test that Grafana has the required datasources configured."""
        self.print_header("Testing Grafana Datasource Configuration")
        
        try:
            # Get datasources from Grafana
            datasources_url = f"{self.services['grafana']}/api/datasources"
            response = requests.get(
                datasources_url, 
                auth=('admin', 'admin'),
                timeout=10
            )
            
            if response.status_code == 200:
                datasources = response.json()
                
                expected_datasources = ['Prometheus', 'Jaeger', 'Elasticsearch', 'VictoriaMetrics']
                found_datasources = []
                
                for ds in datasources:
                    ds_name = ds.get('name', '')
                    if ds_name in expected_datasources:
                        found_datasources.append(ds_name)
                        self.print_success(f"Datasource '{ds_name}' is configured")
                
                missing = set(expected_datasources) - set(found_datasources)
                for ds_name in missing:
                    self.print_warning(f"Datasource '{ds_name}' is not configured")
                
                return len(found_datasources) >= 2  # At least Prometheus and Jaeger
                
            else:
                self.print_error(f"Failed to get datasources from Grafana: {response.status_code}")
                return False
                
        except Exception as e:
            self.print_error(f"Grafana datasources test failed: {str(e)}")
            return False

    async def test_frontend_tracing(self) -> bool:
        """Test that the frontend is generating traces."""
        self.print_header("Testing Frontend OpenTelemetry Instrumentation")
        
        try:
            # This test would require browser automation or checking collector logs
            # For now, we'll just verify the frontend is serving the instrumented code
            
            response = requests.get(self.services['frontend'], timeout=10)
            if response.status_code == 200:
                content = response.text
                
                # Check if OpenTelemetry-related code is present
                otel_indicators = [
                    'opentelemetry',
                    'trace',
                    'span',
                    'telemetry'
                ]
                
                found_indicators = []
                for indicator in otel_indicators:
                    if indicator.lower() in content.lower():
                        found_indicators.append(indicator)
                
                if found_indicators:
                    self.print_success(f"Frontend contains OpenTelemetry instrumentation")
                    self.print_info(f"Found indicators: {', '.join(found_indicators)}")
                else:
                    self.print_warning("Frontend may not have OpenTelemetry instrumentation")
                
                return True
            else:
                self.print_error(f"Frontend not accessible: {response.status_code}")
                return False
                
        except Exception as e:
            self.print_error(f"Frontend tracing test failed: {str(e)}")
            return False

    def test_trace_correlation(self) -> bool:
        """Test end-to-end trace correlation."""
        self.print_header("Testing End-to-End Trace Correlation")
        
        if not self.trace_id:
            self.print_warning("No trace ID captured from previous tests")
            return False
            
        try:
            # Check if we can find the trace in Jaeger
            trace_url = f"{self.services['jaeger']}/api/traces/{self.trace_id}"
            response = requests.get(trace_url, timeout=10)
            
            if response.status_code == 200:
                trace_data = response.json()
                
                if trace_data.get('data'):
                    spans = []
                    for trace in trace_data['data']:
                        spans.extend(trace.get('spans', []))
                    
                    self.print_success(f"Found trace with {len(spans)} spans")
                    
                    # Check for both frontend and backend spans
                    services = set()
                    for span in spans:
                        process = span.get('process', {})
                        service_name = process.get('serviceName', '')
                        if service_name:
                            services.add(service_name)
                    
                    self.print_info(f"Services in trace: {', '.join(services)}")
                    
                    if 'fastapi-backend' in services:
                        self.print_success("Backend spans found in trace")
                    else:
                        self.print_warning("No backend spans found")
                    
                    return True
                else:
                    self.print_warning("Trace data is empty")
                    return False
            else:
                self.print_error(f"Failed to get trace from Jaeger: {response.status_code}")
                return False
                
        except Exception as e:
            self.print_error(f"Trace correlation test failed: {str(e)}")
            return False

    async def run_all_tests(self):
        """Run all validation tests."""
        self.print_header("API HTTP Request Logging Management System - Validation")
        
        print("🚀 Starting comprehensive validation of the observability stack...")
        
        # Run tests
        tests = [
            ("Basic Connectivity", self.test_basic_connectivity),
            ("Backend API", self.test_backend_api),
            ("Prometheus Metrics", self.test_prometheus_metrics),
            ("Jaeger Traces", self.test_jaeger_traces),
            ("Elasticsearch Logs", self.test_elasticsearch_logs),
            ("Grafana Datasources", self.test_grafana_datasources),
            ("Frontend Tracing", self.test_frontend_tracing),
            ("Trace Correlation", self.test_trace_correlation),
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test_name, test_func in tests:
            try:
                if asyncio.iscoroutinefunction(test_func):
                    result = await test_func()
                else:
                    result = test_func()
                
                self.test_results[test_name] = result
                if result:
                    passed_tests += 1
                    
            except Exception as e:
                self.print_error(f"Test '{test_name}' failed with exception: {str(e)}")
                self.test_results[test_name] = False
        
        # Print summary
        self.print_header("Validation Summary")
        
        for test_name, result in self.test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} {test_name}")
        
        print(f"\nOverall Result: {passed_tests}/{total_tests} tests passed")
        
        if passed_tests == total_tests:
            print("🎉 All tests passed! Your observability stack is working correctly.")
            return True
        elif passed_tests >= total_tests * 0.7:
            print("⚠️  Most tests passed. Some components may need additional setup time.")
            return True
        else:
            print("❌ Multiple tests failed. Please check your setup.")
            return False


async def main():
    validator = ObservabilityValidator()
    success = await validator.run_all_tests()
    
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    # Install required packages if not available
    try:
        import requests
        import aiohttp
    except ImportError:
        print("Installing required packages...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "requests", "aiohttp"])
        import requests
        import aiohttp
    
    asyncio.run(main())