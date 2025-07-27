#!/bin/bash

# Circuit Synth Docker Build Script
# This script builds and optionally runs the circuit-synth Docker container

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Default values
IMAGE_NAME="circuit-synth"
TAG="latest"
BUILD_ONLY=false
RUN_TESTS=false
DEV_MODE=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --build-only)
            BUILD_ONLY=true
            shift
            ;;
        --run-tests)
            RUN_TESTS=true
            shift
            ;;
        --dev)
            DEV_MODE=true
            shift
            ;;
        --tag)
            TAG="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --build-only    Only build the image, don't run"
            echo "  --run-tests     Run tests after building"
            echo "  --dev           Run in development mode with interactive shell"
            echo "  --tag TAG       Specify image tag (default: latest)"
            echo "  --help          Show this help message"
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    print_error "Docker is not running. Please start Docker and try again."
    exit 1
fi

# Create necessary directories
print_status "Creating output and cache directories..."
mkdir -p output cache test_output

# Build the Docker image
print_status "Building Docker image: $IMAGE_NAME:$TAG"
docker build -t "$IMAGE_NAME:$TAG" .

if [ $? -eq 0 ]; then
    print_success "Docker image built successfully!"
else
    print_error "Failed to build Docker image"
    exit 1
fi

# If build-only mode, exit here
if [ "$BUILD_ONLY" = true ]; then
    print_success "Build completed. Use 'docker run' to run the container."
    exit 0
fi

# Run the container based on mode
if [ "$RUN_TESTS" = true ]; then
    print_status "Running tests..."
    docker run --rm \
        -v "$(pwd)/src:/app/src" \
        -v "$(pwd)/tests:/app/tests" \
        -v "$(pwd)/test_output:/app/test_output" \
        -e PYTHONPATH=/app/src \
        -e RUST_LOG=info \
        "$IMAGE_NAME:$TAG" \
        python -m pytest tests/ -v

elif [ "$DEV_MODE" = true ]; then
    print_status "Starting development container with interactive shell..."
    print_warning "Press Ctrl+C to exit the container"
    docker run --rm -it \
        -v "$(pwd)/src:/app/src" \
        -v "$(pwd)/examples:/app/examples" \
        -v "$(pwd)/tests:/app/tests" \
        -v "$(pwd)/output:/app/output" \
        -v "$(pwd)/cache:/app/cache" \
        -e PYTHONPATH=/app/src \
        -e RUST_LOG=debug \
        "$IMAGE_NAME:$TAG" \
        /bin/bash

else
    print_status "Running circuit-synth container..."
    docker run --rm \
        -v "$(pwd)/src:/app/src" \
        -v "$(pwd)/examples:/app/examples" \
        -v "$(pwd)/output:/app/output" \
        -v "$(pwd)/cache:/app/cache" \
        -e PYTHONPATH=/app/src \
        -e RUST_LOG=info \
        "$IMAGE_NAME:$TAG"
fi

print_success "Done!" 