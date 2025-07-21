#!/bin/bash

# LanguageTool Corrector v2 - Deploy Script
# Automated deployment with Poetry dependency management, health checks and monitoring

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="bertcorrector"
COMPOSE_FILE="docker-compose.yml"
HEALTH_TIMEOUT=300
PROMETHEUS_URL="http://localhost:9090"
GRAFANA_URL="http://localhost:3000"
API_URL="http://localhost:8000"

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_dependencies() {
    log_info "Checking dependencies..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed"
        exit 1
    fi
    
    # Check if Docker daemon is running
    if ! docker info &> /dev/null; then
        log_error "Docker daemon is not running"
        exit 1
    fi
    
    log_success "All dependencies are available"
}

cleanup_existing() {
    log_info "Cleaning up existing deployment..."
    
    # Stop and remove containers
    docker-compose -f ${COMPOSE_FILE} down --remove-orphans || true
    
    # Remove dangling images
    docker image prune -f || true
    
    log_success "Cleanup completed"
}

build_services() {
    log_info "Building services..."
    
    # Build all services
    docker-compose -f ${COMPOSE_FILE} build --parallel
    
    if [ $? -eq 0 ]; then
        log_success "All services built successfully"
    else
        log_error "Failed to build services"
        exit 1
    fi
}

deploy_services() {
    log_info "Deploying services..."
    
    # Start services in background
    docker-compose -f ${COMPOSE_FILE} up -d
    
    if [ $? -eq 0 ]; then
        log_success "Services deployed successfully"
    else
        log_error "Failed to deploy services"
        exit 1
    fi
}

wait_for_service() {
    local service_name=$1
    local health_url=$2
    local timeout=${3:-60}
    
    log_info "Waiting for ${service_name} to be healthy..."
    
    local counter=0
    while [ $counter -lt $timeout ]; do
        if curl -s -f "${health_url}" > /dev/null 2>&1; then
            log_success "${service_name} is healthy"
            return 0
        fi
        
        echo -n "."
        sleep 2
        counter=$((counter + 2))
    done
    
    log_error "${service_name} failed to become healthy within ${timeout}s"
    return 1
}

check_health() {
    log_info "Performing health checks..."
    
    # Wait for core services
    wait_for_service "API Gateway" "${API_URL}/health" 120
    wait_for_service "Prometheus" "${PROMETHEUS_URL}/-/healthy" 60
    wait_for_service "Grafana" "${GRAFANA_URL}/api/health" 60
    
    # Check all containers are running
    local failed_containers=$(docker-compose -f ${COMPOSE_FILE} ps --filter "status=exited" --format "table {{.Service}}")
    
    if [ -n "$failed_containers" ] && [ "$failed_containers" != "SERVICE" ]; then
        log_error "Some containers failed to start:"
        echo "$failed_containers"
        return 1
    fi
    
    log_success "All health checks passed"
}

run_tests() {
    log_info "Running integration tests..."
    
    # Test API Gateway
    local response=$(curl -s -w "%{http_code}" -o /dev/null -X POST "${API_URL}/correct" \
        -H "Content-Type: application/json" \
        -d '{"text": "eu gosta de teste"}')
    
    if [ "$response" = "200" ]; then
        log_success "API Gateway test passed"
    else
        log_warning "API Gateway test failed (HTTP $response)"
    fi
    
    # Test legacy endpoint
    local legacy_response=$(curl -s -w "%{http_code}" -o /dev/null -X POST "${API_URL}/corrigir" \
        -H "Content-Type: application/json" \
        -d '{"text": "nos fomos ao cinema"}')
    
    if [ "$legacy_response" = "200" ]; then
        log_success "Legacy endpoint test passed"
    else
        log_warning "Legacy endpoint test failed (HTTP $legacy_response)"
    fi
}

show_status() {
    log_info "Service status:"
    docker-compose -f ${COMPOSE_FILE} ps
    
    echo ""
    log_info "Service URLs:"
    echo "  🚀 API Gateway:     ${API_URL}"
    echo "  📊 Grafana:         ${GRAFANA_URL} (admin/admin123)"
    echo "  📈 Prometheus:      ${PROMETHEUS_URL}"
    echo "  📚 API Docs:        ${API_URL}/docs"
    echo "  🔍 Health Check:    ${API_URL}/health"
    
    echo ""
    log_info "Example usage:"
    echo "  curl -X POST '${API_URL}/correct' \\"
    echo "    -H 'Content-Type: application/json' \\"
    echo "    -d '{\"text\": \"eu gosta de programar\"}'"
}

show_logs() {
    log_info "Recent logs from all services:"
    docker-compose -f ${COMPOSE_FILE} logs --tail=10
}

# Main deployment function
main() {
    echo ""
    echo "🚀 LanguageTool Corrector v2 - Deployment"
    echo "=========================================="
    echo ""
    
    # Parse command line arguments
    case "${1:-deploy}" in
        "deploy")
            check_dependencies
            cleanup_existing
            build_services
            deploy_services
            sleep 10  # Give services time to start
            check_health
            run_tests
            show_status
            ;;
        "build")
            check_dependencies
            build_services
            ;;
        "start")
            deploy_services
            check_health
            show_status
            ;;
        "stop")
            log_info "Stopping all services..."
            docker-compose -f ${COMPOSE_FILE} down
            log_success "All services stopped"
            ;;
        "restart")
            log_info "Restarting services..."
            docker-compose -f ${COMPOSE_FILE} restart
            check_health
            show_status
            ;;
        "status")
            show_status
            ;;
        "logs")
            show_logs
            ;;
        "clean")
            cleanup_existing
            log_info "Removing unused Docker resources..."
            docker system prune -f
            log_success "Cleanup completed"
            ;;
        "test")
            run_tests
            ;;
        "help"|"-h"|"--help")
            echo "Usage: $0 [command]"
            echo ""
            echo "Commands:"
            echo "  deploy    - Full deployment (build, start, test)"
            echo "  build     - Build all services"
            echo "  start     - Start services"
            echo "  stop      - Stop all services"
            echo "  restart   - Restart services"
            echo "  status    - Show service status"
            echo "  logs      - Show recent logs"
            echo "  clean     - Clean up resources"
            echo "  test      - Run integration tests"
            echo "  help      - Show this help"
            ;;
        *)
            log_error "Unknown command: $1"
            echo "Use '$0 help' for usage information"
            exit 1
            ;;
    esac
}

# Handle script interruption
trap 'log_warning "Deployment interrupted"; exit 1' INT TERM

# Run main function
main "$@"
