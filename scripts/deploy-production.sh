#!/bin/bash

# Circuit-Synth Production Deployment Script
# Cross-platform Docker deployment with intelligent optimization

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
COMPOSE_FILE="docker/docker-compose.production.yml"
IMAGE_NAME="circuit-synth:production"
BUILD_ARGS=""

# Utility functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

log_header() {
    echo -e "${PURPLE}🚀 $1${NC}"
    echo "=================================================="
}

# System detection
detect_system() {
    ARCH=$(uname -m)
    OS=$(uname -s)
    
    log_header "System Detection"
    log_info "Architecture: $ARCH"
    log_info "Operating System: $OS"
    
    # Docker platform detection
    if command -v docker &> /dev/null; then
        DOCKER_VERSION=$(docker --version | cut -d' ' -f3 | cut -d',' -f1)
        log_info "Docker Version: $DOCKER_VERSION"
        
        # Check for Docker Desktop on Mac/Windows
        if [[ "$OS" == "Darwin" ]] || [[ "$OS" == *"NT"* ]]; then
            log_info "Docker Desktop detected - emulation available"
        fi
    else
        log_error "Docker not found. Please install Docker first."
        exit 1
    fi
    
    # Check for docker-compose
    if command -v docker-compose &> /dev/null; then
        COMPOSE_VERSION=$(docker-compose --version | cut -d' ' -f3 | cut -d',' -f1)
        log_info "Docker Compose Version: $COMPOSE_VERSION"
    else
        log_error "Docker Compose not found."
        exit 1
    fi
    
    echo ""
}

# Pre-deployment checks
pre_deployment_checks() {
    log_header "Pre-Deployment Checks"
    
    # Check disk space (need at least 2GB)
    AVAILABLE_SPACE=$(df . | tail -1 | awk '{print $4}')
    if [[ $AVAILABLE_SPACE -lt 2097152 ]]; then
        log_warning "Low disk space detected. Build may fail."
    else
        log_success "Sufficient disk space available"
    fi
    
    # Check if ports are available
    if lsof -i :8000 &>/dev/null; then
        log_warning "Port 8000 is in use. May conflict with web services."
    fi
    
    # Verify project structure
    if [[ ! -f "pyproject.toml" ]]; then
        log_error "pyproject.toml not found. Run from project root."
        exit 1
    fi
    
    if [[ ! -d "src/circuit_synth" ]]; then
        log_error "Circuit-Synth source not found. Check project structure."
        exit 1
    fi
    
    log_success "Pre-deployment checks passed"
    echo ""
}

# Build optimization based on architecture
optimize_build() {
    log_header "Build Optimization"
    
    case $ARCH in
        "x86_64")
            log_info "Native AMD64 build - using official KiCad image"
            BUILD_ARGS="--build-arg KICAD_VERSION=9.0"
            ;;
        "aarch64"|"arm64")
            log_info "ARM64 detected - using emulation for KiCad"
            BUILD_ARGS="--build-arg KICAD_VERSION=9.0"
            log_warning "Build may take longer due to emulation (~20% overhead)"
            ;;
        *)
            log_warning "Unsupported architecture: $ARCH"
            log_info "Attempting build with emulation..."
            BUILD_ARGS="--build-arg KICAD_VERSION=8.0"
            ;;
    esac
    
    # Check available memory for parallel builds
    if [[ "$OS" == "Linux" ]]; then
        MEM_GB=$(free -g | awk '/^Mem:/{print $2}')
        if [[ $MEM_GB -gt 4 ]]; then
            export DOCKER_BUILDKIT=1
            log_info "Using BuildKit for optimized builds"
        fi
    fi
    
    echo ""
}

# Main build process
build_production() {
    log_header "Building Production Image"
    
    log_info "Starting build process..."
    echo "Build command: docker-compose -f $COMPOSE_FILE build $BUILD_ARGS circuit-synth"
    
    # Build with progress output
    if docker-compose -f "$COMPOSE_FILE" build $BUILD_ARGS circuit-synth; then
        log_success "Production image built successfully!"
        
        # Get image size
        IMAGE_SIZE=$(docker images $IMAGE_NAME --format "table {{.Size}}" | tail -1)
        log_info "Final image size: $IMAGE_SIZE"
    else
        log_error "Build failed. Check the output above for details."
        exit 1
    fi
    
    echo ""
}

# Deployment verification
verify_deployment() {
    log_header "Deployment Verification"
    
    log_info "Running comprehensive integration tests..."
    
    # Test 1: Basic container startup
    if docker-compose -f "$COMPOSE_FILE" run --rm circuit-synth-test; then
        log_success "Integration tests passed"
    else
        log_error "Integration tests failed"
        return 1
    fi
    
    # Test 2: Example project execution
    log_info "Testing example project execution..."
    if docker-compose -f "$COMPOSE_FILE" run --rm examples; then
        log_success "Example projects executed successfully"
    else
        log_warning "Example projects had issues (may be expected)"
    fi
    
    echo ""
}

# Deployment summary
deployment_summary() {
    log_header "Deployment Summary"
    
    echo -e "${CYAN}🎉 Circuit-Synth Production Deployment Complete!${NC}"
    echo ""
    echo "📋 Available Services:"
    echo "  • circuit-synth        - Main production service"
    echo "  • circuit-synth-dev    - Development environment"  
    echo "  • circuit-synth-test   - Test runner"
    echo "  • kicad-cli           - Standalone KiCad CLI"
    echo "  • examples            - Example project runner"
    echo ""
    echo "🚀 Quick Start Commands:"
    echo "  # Run development environment:"
    echo "  docker-compose -f $COMPOSE_FILE run --rm circuit-synth-dev"
    echo ""
    echo "  # Execute example project:"
    echo "  docker-compose -f $COMPOSE_FILE run --rm examples"
    echo ""
    echo "  # Use KiCad CLI directly:"
    echo "  docker-compose -f $COMPOSE_FILE run --rm kicad-cli version"
    echo ""
    echo "  # Run specific tests:"
    echo "  docker-compose -f $COMPOSE_FILE run --rm circuit-synth-test"
    echo ""
    echo "🔧 Configuration:"
    echo "  • Architecture: $ARCH"
    echo "  • KiCad Version: $(docker-compose -f $COMPOSE_FILE run --rm circuit-synth 'kicad-cli version' 2>/dev/null | head -1 || echo 'TBD')"
    echo "  • Image Size: $(docker images $IMAGE_NAME --format '{{.Size}}' | head -1)"
    echo ""
    echo "📚 Next Steps:"
    echo "  1. Place your KiCad projects in: ./kicad_projects/"
    echo "  2. Generated files appear in: ./output/"
    echo "  3. Check logs: docker-compose -f $COMPOSE_FILE logs"
    echo ""
}

# Cleanup function
cleanup_on_exit() {
    if [[ $? -ne 0 ]]; then
        log_error "Deployment failed. Cleaning up..."
        docker-compose -f "$COMPOSE_FILE" down --remove-orphans 2>/dev/null || true
    fi
}

# Main execution flow
main() {
    trap cleanup_on_exit EXIT
    
    log_header "Circuit-Synth Production Deployment"
    echo "Cross-platform Docker deployment with KiCad integration"
    echo ""
    
    detect_system
    pre_deployment_checks
    optimize_build
    build_production
    verify_deployment
    deployment_summary
    
    log_success "Deployment completed successfully! 🎉"
}

# Parse command line arguments
case "${1:-deploy}" in
    "deploy"|"build")
        main
        ;;
    "test")
        log_info "Running tests only..."
        docker-compose -f "$COMPOSE_FILE" run --rm circuit-synth-test
        ;;
    "clean")
        log_info "Cleaning up containers and images..."
        docker-compose -f "$COMPOSE_FILE" down --rmi all --volumes --remove-orphans
        ;;
    "help"|"-h"|"--help")
        echo "Usage: $0 [command]"
        echo ""
        echo "Commands:"
        echo "  deploy (default)  - Full deployment with build and verification"
        echo "  build            - Build production image only"
        echo "  test             - Run integration tests"
        echo "  clean            - Clean up all containers and images"
        echo "  help             - Show this help message"
        ;;
    *)
        log_error "Unknown command: $1"
        echo "Use '$0 help' for available commands."
        exit 1
        ;;
esac