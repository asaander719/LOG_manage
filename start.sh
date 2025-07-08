#!/bin/bash

# API HTTP Request Logging Management System
# Startup script for comprehensive observability stack

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check prerequisites
check_prerequisites() {
    print_header "Checking Prerequisites"
    
    # Check Docker
    if command -v docker &> /dev/null; then
        print_success "Docker is installed"
    else
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Check Docker Compose
    if command -v docker-compose &> /dev/null || docker compose version &> /dev/null; then
        print_success "Docker Compose is available"
    else
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    # Check if ports are available
    print_info "Checking port availability..."
    
    ports=(80 3000 4317 4318 5601 8000 8428 9090 9200 16686)
    occupied_ports=()
    
    for port in "${ports[@]}"; do
        if ss -tuln | grep ":$port " &> /dev/null; then
            occupied_ports+=($port)
        fi
    done
    
    if [ ${#occupied_ports[@]} -gt 0 ]; then
        print_warning "The following ports are already in use: ${occupied_ports[*]}"
        print_warning "Please stop services using these ports or modify docker-compose.yml"
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    else
        print_success "All required ports are available"
    fi
}

# Build and start services
start_services() {
    print_header "Starting Observability Stack"
    
    print_info "Pulling and building Docker images..."
    docker-compose pull
    docker-compose build
    
    print_info "Starting services..."
    docker-compose up -d
    
    print_success "All services started successfully!"
}

# Wait for services to be healthy
wait_for_services() {
    print_header "Waiting for Services to be Ready"
    
    services=(
        "elasticsearch:9200/_cluster/health"
        "prometheus:9090/-/ready"
        "jaeger:16686/"
        "fastapi-backend:8000/health"
    )
    
    for service in "${services[@]}"; do
        IFS=':' read -r name endpoint <<< "$service"
        print_info "Waiting for $name to be ready..."
        
        max_attempts=60
        attempt=0
        
        while [ $attempt -lt $max_attempts ]; do
            if curl -s "http://localhost:$endpoint" &> /dev/null; then
                print_success "$name is ready!"
                break
            fi
            
            sleep 2
            ((attempt++))
            
            if [ $attempt -eq $max_attempts ]; then
                print_warning "$name is taking longer than expected to start"
            fi
        done
    done
}

# Display service URLs
show_urls() {
    print_header "Service URLs"
    
    echo -e "${GREEN}🌐 Frontend Demo:${NC}         http://localhost"
    echo -e "${GREEN}📊 Grafana Dashboard:${NC}    http://localhost:3000 (admin/admin)"
    echo -e "${GREEN}🔍 Jaeger Tracing:${NC}       http://localhost:16686"
    echo -e "${GREEN}📈 Prometheus Metrics:${NC}   http://localhost:9090"
    echo -e "${GREEN}📋 Kibana Logs:${NC}          http://localhost:5601"
    echo -e "${GREEN}🔧 FastAPI Backend:${NC}      http://localhost:8000"
    echo -e "${GREEN}🏪 VictoriaMetrics:${NC}      http://localhost:8428"
    echo ""
    echo -e "${YELLOW}💡 Tip: Start by opening the Frontend Demo to test the system!${NC}"
}

# Show system status
show_status() {
    print_header "System Status"
    
    echo "Container Status:"
    docker-compose ps
    
    echo ""
    echo "Resource Usage:"
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"
}

# Stop services
stop_services() {
    print_header "Stopping Services"
    
    print_info "Stopping all containers..."
    docker-compose down
    
    print_success "All services stopped!"
}

# Clean up everything
cleanup() {
    print_header "Cleaning Up"
    
    print_warning "This will remove all containers, volumes, and data!"
    read -p "Are you sure? (y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_info "Removing containers and volumes..."
        docker-compose down -v --remove-orphans
        
        print_info "Removing images..."
        docker-compose down --rmi all
        
        print_success "Cleanup completed!"
    else
        print_info "Cleanup cancelled"
    fi
}

# Show logs
show_logs() {
    if [ -z "$1" ]; then
        print_info "Showing logs for all services (press Ctrl+C to stop)..."
        docker-compose logs -f
    else
        print_info "Showing logs for $1 (press Ctrl+C to stop)..."
        docker-compose logs -f "$1"
    fi
}

# Test the system
test_system() {
    print_header "Testing the System"
    
    print_info "Testing FastAPI backend..."
    if curl -s http://localhost:8000/health | grep -q "healthy"; then
        print_success "Backend is responding"
    else
        print_error "Backend is not responding"
        return 1
    fi
    
    print_info "Testing frontend..."
    if curl -s http://localhost/health | grep -q "healthy"; then
        print_success "Frontend is responding"
    else
        print_error "Frontend is not responding"
        return 1
    fi
    
    print_info "Making test API calls..."
    curl -s http://localhost:8000/api/users > /dev/null
    curl -s http://localhost:8000/api/users/1 > /dev/null
    
    print_success "Test API calls completed"
    print_info "Check Jaeger at http://localhost:16686 for traces"
    print_info "Check Grafana at http://localhost:3000 for metrics"
}

# Main script
case "$1" in
    "start")
        check_prerequisites
        start_services
        wait_for_services
        show_urls
        ;;
    "stop")
        stop_services
        ;;
    "status")
        show_status
        ;;
    "logs")
        show_logs "$2"
        ;;
    "test")
        test_system
        ;;
    "cleanup")
        cleanup
        ;;
    "restart")
        stop_services
        sleep 2
        start_services
        wait_for_services
        show_urls
        ;;
    *)
        print_header "API HTTP Request Logging Management System"
        echo ""
        echo "Usage: $0 {start|stop|restart|status|logs|test|cleanup}"
        echo ""
        echo "Commands:"
        echo "  start    - Start all observability services"
        echo "  stop     - Stop all services"
        echo "  restart  - Restart all services"
        echo "  status   - Show service status and resource usage"
        echo "  logs     - Show logs (optional: specify service name)"
        echo "  test     - Run system tests"
        echo "  cleanup  - Remove all containers, volumes, and images"
        echo ""
        echo "Examples:"
        echo "  $0 start"
        echo "  $0 logs fastapi-backend"
        echo "  $0 status"
        exit 1
        ;;
esac