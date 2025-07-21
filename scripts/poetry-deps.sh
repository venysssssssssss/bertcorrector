#!/bin/bash

# Poetry Dependency Management Script
# Manages dependencies across all microservices

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Service directories
SERVICES=(
    "."
    "services/api-gateway"
    "services/spacy-enhancer"
)

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

check_poetry() {
    if ! command -v poetry &> /dev/null; then
        log_error "Poetry is not installed. Please install Poetry first:"
        echo "curl -sSL https://install.python-poetry.org | python3 -"
        exit 1
    fi
    log_success "Poetry is installed: $(poetry --version)"
}

install_dependencies() {
    local service_path=$1
    local service_name=${service_path##*/}
    
    if [ "$service_path" = "." ]; then
        service_name="root"
    fi
    
    log_info "Installing dependencies for $service_name..."
    
    cd "$service_path"
    
    if [ -f "pyproject.toml" ]; then
        poetry install --no-root
        log_success "Dependencies installed for $service_name"
    else
        log_warning "No pyproject.toml found in $service_path"
    fi
    
    cd - > /dev/null
}

update_dependencies() {
    local service_path=$1
    local service_name=${service_path##*/}
    
    if [ "$service_path" = "." ]; then
        service_name="root"
    fi
    
    log_info "Updating dependencies for $service_name..."
    
    cd "$service_path"
    
    if [ -f "pyproject.toml" ]; then
        poetry update
        log_success "Dependencies updated for $service_name"
    else
        log_warning "No pyproject.toml found in $service_path"
    fi
    
    cd - > /dev/null
}

add_dependency() {
    local service_path=$1
    local package=$2
    local service_name=${service_path##*/}
    
    if [ "$service_path" = "." ]; then
        service_name="root"
    fi
    
    log_info "Adding $package to $service_name..."
    
    cd "$service_path"
    
    if [ -f "pyproject.toml" ]; then
        poetry add "$package"
        log_success "$package added to $service_name"
    else
        log_warning "No pyproject.toml found in $service_path"
    fi
    
    cd - > /dev/null
}

remove_dependency() {
    local service_path=$1
    local package=$2
    local service_name=${service_path##*/}
    
    if [ "$service_path" = "." ]; then
        service_name="root"
    fi
    
    log_info "Removing $package from $service_name..."
    
    cd "$service_path"
    
    if [ -f "pyproject.toml" ]; then
        poetry remove "$package"
        log_success "$package removed from $service_name"
    else
        log_warning "No pyproject.toml found in $service_path"
    fi
    
    cd - > /dev/null
}

show_dependencies() {
    local service_path=$1
    local service_name=${service_path##*/}
    
    if [ "$service_path" = "." ]; then
        service_name="root"
    fi
    
    echo ""
    log_info "Dependencies for $service_name:"
    echo "================================="
    
    cd "$service_path"
    
    if [ -f "pyproject.toml" ]; then
        poetry show
    else
        log_warning "No pyproject.toml found in $service_path"
    fi
    
    cd - > /dev/null
}

export_requirements() {
    local service_path=$1
    local service_name=${service_path##*/}
    
    if [ "$service_path" = "." ]; then
        service_name="root"
    fi
    
    log_info "Exporting requirements.txt for $service_name..."
    
    cd "$service_path"
    
    if [ -f "pyproject.toml" ]; then
        poetry export -f requirements.txt --output requirements.txt --without-hashes
        log_success "requirements.txt exported for $service_name"
    else
        log_warning "No pyproject.toml found in $service_path"
    fi
    
    cd - > /dev/null
}

install_all() {
    log_info "Installing dependencies for all services..."
    for service in "${SERVICES[@]}"; do
        install_dependencies "$service"
    done
    log_success "All dependencies installed!"
}

update_all() {
    log_info "Updating dependencies for all services..."
    for service in "${SERVICES[@]}"; do
        update_dependencies "$service"
    done
    log_success "All dependencies updated!"
}

show_all() {
    log_info "Showing dependencies for all services..."
    for service in "${SERVICES[@]}"; do
        show_dependencies "$service"
    done
}

export_all() {
    log_info "Exporting requirements.txt for all services..."
    for service in "${SERVICES[@]}"; do
        export_requirements "$service"
    done
    log_success "All requirements.txt files exported!"
}

usage() {
    echo "Poetry Dependency Management Script"
    echo ""
    echo "Usage: $0 <command> [options]"
    echo ""
    echo "Commands:"
    echo "  install                 Install dependencies for all services"
    echo "  update                  Update dependencies for all services"
    echo "  show                    Show dependencies for all services"
    echo "  export                  Export requirements.txt for all services"
    echo "  add <service> <package> Add package to specific service"
    echo "  remove <service> <package> Remove package from specific service"
    echo ""
    echo "Services:"
    echo "  root                    Root project"
    echo "  api-gateway             API Gateway service"
    echo "  spacy-enhancer          SpaCy Enhancer service"
    echo ""
    echo "Examples:"
    echo "  $0 install"
    echo "  $0 update"
    echo "  $0 add api-gateway fastapi"
    echo "  $0 remove spacy-enhancer requests"
    echo "  $0 show"
    echo "  $0 export"
}

main() {
    check_poetry
    
    case "${1:-}" in
        install)
            install_all
            ;;
        update)
            update_all
            ;;
        show)
            show_all
            ;;
        export)
            export_all
            ;;
        add)
            if [ $# -ne 3 ]; then
                log_error "Usage: $0 add <service> <package>"
                exit 1
            fi
            
            case "$2" in
                root)
                    add_dependency "." "$3"
                    ;;
                api-gateway)
                    add_dependency "services/api-gateway" "$3"
                    ;;
                spacy-enhancer)
                    add_dependency "services/spacy-enhancer" "$3"
                    ;;
                *)
                    log_error "Unknown service: $2"
                    usage
                    exit 1
                    ;;
            esac
            ;;
        remove)
            if [ $# -ne 3 ]; then
                log_error "Usage: $0 remove <service> <package>"
                exit 1
            fi
            
            case "$2" in
                root)
                    remove_dependency "." "$3"
                    ;;
                api-gateway)
                    remove_dependency "services/api-gateway" "$3"
                    ;;
                spacy-enhancer)
                    remove_dependency "services/spacy-enhancer" "$3"
                    ;;
                *)
                    log_error "Unknown service: $2"
                    usage
                    exit 1
                    ;;
            esac
            ;;
        help|--help|-h)
            usage
            ;;
        *)
            log_error "Unknown command: ${1:-}"
            usage
            exit 1
            ;;
    esac
}

main "$@"
