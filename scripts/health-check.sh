#!/bin/bash

# Health Check Script for LanguageTool Corrector
# Monitors all services and reports their status

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Service endpoints
API_GATEWAY="http://localhost:8000/health"
PROMETHEUS="http://localhost:9090/-/healthy"
GRAFANA="http://localhost:3000/api/health"
LANGUAGETOOL="http://localhost:8010/v2/check?text=test"
SPACY="http://localhost:8020/health"

# Functions
check_service() {
    local name=$1
    local url=$2
    local timeout=${3:-10}
    
    if curl -s --max-time $timeout -f "$url" > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} $name is healthy"
        return 0
    else
        echo -e "${RED}✗${NC} $name is unhealthy"
        return 1
    fi
}

check_docker_containers() {
    echo -e "${BLUE}Docker Containers Status:${NC}"
    echo "=========================="
    
    local containers=(
        "api-gateway"
        "languagetool-server"
        "spacy-enhancer"
        "prometheus"
        "grafana"
        "redis-cache"
        "nginx-proxy"
    )
    
    local all_healthy=true
    
    for container in "${containers[@]}"; do
        if docker ps --format "table {{.Names}}" | grep -q "^$container$"; then
            local status=$(docker inspect --format='{{.State.Health.Status}}' "$container" 2>/dev/null || echo "no-healthcheck")
            case $status in
                "healthy")
                    echo -e "${GREEN}✓${NC} $container (healthy)"
                    ;;
                "unhealthy")
                    echo -e "${RED}✗${NC} $container (unhealthy)"
                    all_healthy=false
                    ;;
                "starting")
                    echo -e "${YELLOW}⏳${NC} $container (starting)"
                    ;;
                "no-healthcheck")
                    # Check if running
                    if docker ps -q -f name="^$container$" | grep -q .; then
                        echo -e "${GREEN}✓${NC} $container (running)"
                    else
                        echo -e "${RED}✗${NC} $container (not running)"
                        all_healthy=false
                    fi
                    ;;
                *)
                    echo -e "${RED}✗${NC} $container (unknown status: $status)"
                    all_healthy=false
                    ;;
            esac
        else
            echo -e "${RED}✗${NC} $container (not found)"
            all_healthy=false
        fi
    done
    
    echo ""
    return $all_healthy
}

check_services() {
    echo -e "${BLUE}Service Health Checks:${NC}"
    echo "====================="
    
    local all_healthy=true
    
    check_service "API Gateway" "$API_GATEWAY" || all_healthy=false
    check_service "Prometheus" "$PROMETHEUS" || all_healthy=false
    check_service "Grafana" "$GRAFANA" || all_healthy=false
    check_service "LanguageTool" "$LANGUAGETOOL" 15 || all_healthy=false
    check_service "SpaCy" "$SPACY" || all_healthy=false
    
    echo ""
    return $all_healthy
}

check_system_resources() {
    echo -e "${BLUE}System Resources:${NC}"
    echo "================="
    
    # CPU usage
    local cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | sed 's/%us,//')
    echo "CPU Usage: ${cpu_usage}"
    
    # Memory usage
    local mem_info=$(free -h | grep '^Mem:')
    local mem_used=$(echo $mem_info | awk '{print $3}')
    local mem_total=$(echo $mem_info | awk '{print $2}')
    echo "Memory Usage: $mem_used / $mem_total"
    
    # Disk usage
    local disk_usage=$(df -h / | tail -1 | awk '{print $5}')
    echo "Disk Usage: $disk_usage"
    
    # Docker stats
    echo ""
    echo "Container Resource Usage:"
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}" | head -10
    
    echo ""
}

test_api_functionality() {
    echo -e "${BLUE}API Functionality Tests:${NC}"
    echo "======================="
    
    # Test correction endpoint
    echo -n "Testing correction endpoint... "
    local response=$(curl -s -w "%{http_code}" -o /tmp/correction_test.json \
        -X POST "http://localhost:8000/correct" \
        -H "Content-Type: application/json" \
        -d '{"text": "eu gosta de programar"}' 2>/dev/null)
    
    if [ "$response" = "200" ]; then
        echo -e "${GREEN}✓${NC}"
        # Show correction result
        if command -v jq &> /dev/null; then
            local original=$(jq -r '.original_text' /tmp/correction_test.json 2>/dev/null)
            local corrected=$(jq -r '.corrected_text' /tmp/correction_test.json 2>/dev/null)
            echo "  Original: $original"
            echo "  Corrected: $corrected"
        fi
    else
        echo -e "${RED}✗ (HTTP $response)${NC}"
    fi
    
    # Test health endpoint
    echo -n "Testing health endpoint... "
    local health_response=$(curl -s -w "%{http_code}" -o /dev/null "http://localhost:8000/health" 2>/dev/null)
    if [ "$health_response" = "200" ]; then
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${RED}✗ (HTTP $health_response)${NC}"
    fi
    
    # Test metrics endpoint
    echo -n "Testing metrics endpoint... "
    local metrics_response=$(curl -s -w "%{http_code}" -o /dev/null "http://localhost:8000/metrics" 2>/dev/null)
    if [ "$metrics_response" = "200" ]; then
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${RED}✗ (HTTP $metrics_response)${NC}"
    fi
    
    echo ""
}

show_logs() {
    echo -e "${BLUE}Recent Error Logs:${NC}"
    echo "=================="
    
    # Show recent errors from all containers
    docker-compose logs --tail=5 --since="5m" | grep -i error || echo "No recent errors found"
    
    echo ""
}

main() {
    echo ""
    echo "🔍 LanguageTool Corrector - Health Check"
    echo "========================================"
    echo ""
    
    local overall_health=true
    
    # Check Docker containers
    check_docker_containers || overall_health=false
    
    # Check service endpoints
    check_services || overall_health=false
    
    # Check system resources
    check_system_resources
    
    # Test API functionality
    test_api_functionality
    
    # Show recent logs if there are issues
    if [ "$overall_health" = false ]; then
        show_logs
    fi
    
    echo ""
    if [ "$overall_health" = true ]; then
        echo -e "${GREEN}🎉 All systems healthy!${NC}"
        exit 0
    else
        echo -e "${RED}⚠️  Some issues detected${NC}"
        echo ""
        echo "Troubleshooting steps:"
        echo "1. Check logs: docker-compose logs [service-name]"
        echo "2. Restart services: ./scripts/deploy.sh restart"
        echo "3. Full redeploy: ./scripts/deploy.sh deploy"
        exit 1
    fi
}

# Clean up temporary files on exit
trap 'rm -f /tmp/correction_test.json' EXIT

main "$@"
