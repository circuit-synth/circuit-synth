#!/bin/bash

# Circuit Synth Docker Runner with KiCad Libraries Support
# This script provides flexible KiCad library mounting options

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
IMAGE_NAME="circuit-synth-simple"
SCRIPT_TO_RUN="examples/example_kicad_project.py"
USE_OFFICIAL_LIBS=false
CUSTOM_SYMBOLS_DIR=""
CUSTOM_FOOTPRINTS_DIR=""
CUSTOM_3D_DIR=""
DEV_MODE=false

# Usage function
show_usage() {
    echo "Usage: $0 [OPTIONS] [SCRIPT]"
    echo ""
    echo "Options:"
    echo "  --official-libs     Use official KiCad libraries from submodules"
    echo "  --symbols DIR       Custom symbols directory to mount"
    echo "  --footprints DIR    Custom footprints directory to mount"
    echo "  --3d DIR           Custom 3D models directory to mount"
    echo "  --dev              Run in development mode (interactive shell)"
    echo "  --image NAME       Docker image to use (default: circuit-synth-simple)"
    echo "  --help             Show this help message"
    echo ""
    echo "Examples:"
    echo "  # Use official KiCad libraries"
    echo "  $0 --official-libs"
    echo ""
    echo "  # Use custom libraries"
    echo "  $0 --symbols /path/to/symbols --footprints /path/to/footprints"
    echo ""
    echo "  # Development mode with official libraries"
    echo "  $0 --official-libs --dev"
    echo ""
    echo "  # Run specific script"
    echo "  $0 --official-libs examples/my_circuit.py"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --official-libs)
            USE_OFFICIAL_LIBS=true
            shift
            ;;
        --symbols)
            CUSTOM_SYMBOLS_DIR="$2"
            shift 2
            ;;
        --footprints)
            CUSTOM_FOOTPRINTS_DIR="$2"
            shift 2
            ;;
        --3d)
            CUSTOM_3D_DIR="$2"
            shift 2
            ;;
        --dev)
            DEV_MODE=true
            shift
            ;;
        --image)
            IMAGE_NAME="$2"
            shift 2
            ;;
        --help)
            show_usage
            exit 0
            ;;
        *.py)
            SCRIPT_TO_RUN="$1"
            shift
            ;;
        *)
            print_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Build Docker run command
DOCKER_CMD="docker run --rm"

# Add volume mounts
DOCKER_CMD="$DOCKER_CMD -v $(pwd)/src:/app/src"
DOCKER_CMD="$DOCKER_CMD -v $(pwd)/examples:/app/examples"
DOCKER_CMD="$DOCKER_CMD -v $(pwd)/output:/app/output"

# Handle library mounting
if [ "$USE_OFFICIAL_LIBS" = true ]; then
    print_status "Using official KiCad libraries from submodules"
    
    # Check if submodules exist
    if [ ! -d "../kicad-symbols" ]; then
        print_error "Official KiCad symbols submodule not found at ../kicad-symbols"
        print_error "Run: git submodule update --init --recursive"
        exit 1
    fi
    
    DOCKER_CMD="$DOCKER_CMD -v $(realpath ../kicad-symbols):/app/kicad-libs/symbols:ro"
    DOCKER_CMD="$DOCKER_CMD -e KICAD_SYMBOL_DIR=/app/kicad-libs/symbols"
    
    if [ -d "../kicad-footprints" ]; then
        DOCKER_CMD="$DOCKER_CMD -v $(realpath ../kicad-footprints):/app/kicad-libs/footprints:ro"
        DOCKER_CMD="$DOCKER_CMD -e KICAD_FOOTPRINT_DIR=/app/kicad-libs/footprints"
    else
        print_warning "KiCad footprints submodule not found - footprints will not be available"
    fi
    
    if [ -d "../kicad-packages3d" ]; then
        DOCKER_CMD="$DOCKER_CMD -v $(realpath ../kicad-packages3d):/app/kicad-libs/packages3d:ro"
    else
        print_warning "KiCad 3D packages submodule not found - 3D models will not be available"
    fi
fi

# Handle custom libraries
if [ ! -z "$CUSTOM_SYMBOLS_DIR" ]; then
    if [ -d "$CUSTOM_SYMBOLS_DIR" ]; then
        print_status "Using custom symbols from: $CUSTOM_SYMBOLS_DIR"
        DOCKER_CMD="$DOCKER_CMD -v $(realpath $CUSTOM_SYMBOLS_DIR):/app/kicad-libs/custom/symbols:ro"
        DOCKER_CMD="$DOCKER_CMD -e KICAD_SYMBOL_DIR=/app/kicad-libs/custom/symbols"
    else
        print_error "Custom symbols directory not found: $CUSTOM_SYMBOLS_DIR"
        exit 1
    fi
fi

if [ ! -z "$CUSTOM_FOOTPRINTS_DIR" ]; then
    if [ -d "$CUSTOM_FOOTPRINTS_DIR" ]; then
        print_status "Using custom footprints from: $CUSTOM_FOOTPRINTS_DIR"
        DOCKER_CMD="$DOCKER_CMD -v $(realpath $CUSTOM_FOOTPRINTS_DIR):/app/kicad-libs/custom/footprints:ro"
        DOCKER_CMD="$DOCKER_CMD -e KICAD_FOOTPRINT_DIR=/app/kicad-libs/custom/footprints"
    else
        print_error "Custom footprints directory not found: $CUSTOM_FOOTPRINTS_DIR"
        exit 1
    fi
fi

if [ ! -z "$CUSTOM_3D_DIR" ]; then
    if [ -d "$CUSTOM_3D_DIR" ]; then
        print_status "Using custom 3D models from: $CUSTOM_3D_DIR"
        DOCKER_CMD="$DOCKER_CMD -v $(realpath $CUSTOM_3D_DIR):/app/kicad-libs/custom/packages3d:ro"
        DOCKER_CMD="$DOCKER_CMD -e KICAD_3DMODEL_DIR=/app/kicad-libs/custom/packages3d"
    else
        print_error "Custom 3D models directory not found: $CUSTOM_3D_DIR"
        exit 1
    fi
fi

# Set working directory
DOCKER_CMD="$DOCKER_CMD -w /app"

# Add command to run
if [ "$DEV_MODE" = true ]; then
    print_status "Starting development mode..."
    DOCKER_CMD="$DOCKER_CMD -it $IMAGE_NAME /bin/bash"
else
    print_status "Running script: $SCRIPT_TO_RUN"
    DOCKER_CMD="$DOCKER_CMD $IMAGE_NAME python $SCRIPT_TO_RUN"
fi

# Execute the command
print_status "Executing: $DOCKER_CMD"
eval $DOCKER_CMD

if [ $? -eq 0 ]; then
    print_success "Execution completed successfully!"
else
    print_error "Execution failed!"
    exit 1
fi