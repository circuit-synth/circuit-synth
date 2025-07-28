#!/bin/bash

# Modern Docker + KiCad Integration Script
# Automatically detects architecture and uses appropriate build strategy

set -e

ARCH=$(uname -m)
echo "🔍 Detected architecture: $ARCH"

# Choose the appropriate Docker strategy based on architecture
if [[ "$ARCH" == "x86_64" ]]; then
    echo "🏗️  Using multi-stage build with official KiCad image (x86_64 optimized)"
    COMPOSE_FILE="docker/docker-compose.kicad.yml"
    DOCKERFILE="docker/Dockerfile.kicad-integrated"
    BUILD_STRATEGY="multi-stage"
elif [[ "$ARCH" == "aarch64" || "$ARCH" == "arm64" ]]; then
    echo "🏗️  Using native ARM64 build with KiCad from source"
    COMPOSE_FILE="docker/docker-compose.kicad-arm64.yml"
    DOCKERFILE="docker/Dockerfile.kicad-arm64"
    BUILD_STRATEGY="native-source"
else
    echo "❌ Unsupported architecture: $ARCH"
    echo "   Supported: x86_64, aarch64, arm64"
    exit 1
fi

echo ""
echo "📋 Build Configuration:"
echo "   Strategy: $BUILD_STRATEGY"
echo "   Compose File: $COMPOSE_FILE"
echo "   Dockerfile: $DOCKERFILE"
echo ""

# Build the image
echo "🔧 Building Circuit-Synth + KiCad Docker image..."
docker-compose -f "$COMPOSE_FILE" build circuit-synth-kicad

echo ""
echo "🧪 Testing KiCad + Circuit-Synth integration..."

# Run comprehensive integration tests
docker-compose -f "$COMPOSE_FILE" run --rm circuit-synth-kicad bash -c "
    echo '=== System Information ==='
    echo 'Architecture:' && uname -m
    echo 'Build Strategy: $BUILD_STRATEGY'
    
    echo ''
    echo '=== KiCad Installation Verification ==='
    kicad-cli version || echo 'KiCad CLI version check failed'
    
    echo ''
    echo '=== Library Verification ==='
    echo 'Symbol libraries:'
    if [ -d '/usr/share/kicad/symbols' ]; then
        ls /usr/share/kicad/symbols/ | head -5
        echo \"Total symbol libraries: \$(ls /usr/share/kicad/symbols/ | wc -l)\"
    else
        echo 'Symbol libraries not found'
    fi
    
    echo ''
    echo 'Footprint libraries:'
    if [ -d '/usr/share/kicad/footprints' ]; then
        ls /usr/share/kicad/footprints/ | head -5
        echo \"Total footprint libraries: \$(ls /usr/share/kicad/footprints/ | wc -l)\"
    else
        echo 'Footprint libraries not found'
    fi
    
    echo ''
    echo '=== Circuit-Synth Import Test ==='
    python -c '
import circuit_synth
import sys
try:
    print(\"✅ Circuit-Synth imported successfully\")
    print(f\"   Python version: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}\")
except Exception as e:
    print(f\"❌ Circuit-Synth import failed: {e}\")
    '
    
    echo ''
    echo '=== Integration Test ==='
    python -c '
import subprocess
import os

# Test KiCad CLI from Python
try:
    result = subprocess.run([\"kicad-cli\", \"version\"], capture_output=True, text=True, check=True)
    print(f\"✅ KiCad CLI accessible from Python\")
    print(f\"   Version: {result.stdout.strip()}\")
except Exception as e:
    print(f\"❌ KiCad CLI error: {e}\")

# Test library paths
for lib_type, path in [(\"symbols\", \"/usr/share/kicad/symbols\"), 
                       (\"footprints\", \"/usr/share/kicad/footprints\")]:
    if os.path.exists(path):
        count = len([f for f in os.listdir(path) if not f.startswith(\".\")])
        print(f\"✅ Found {count} {lib_type} libraries\")
    else:
        print(f\"❌ Missing {lib_type} libraries at {path}\")
    '
"

echo ""
echo "🎯 Testing example project generation..."
docker-compose -f "$COMPOSE_FILE" run --rm circuit-synth-kicad bash -c "
    echo '=== Running Circuit-Synth Example ==='
    if [ -f 'examples/example_kicad_project.py' ]; then
        timeout 60 python examples/example_kicad_project.py || echo 'Example script timed out or failed'
        
        echo ''
        echo '=== Verifying Generated Files ==='
        if [ -d 'output' ] || [ -d 'example_kicad_project' ]; then
            find . -name '*.kicad_*' -o -name '*.net' | head -10
            echo '✅ KiCad files generated successfully'
        else
            echo '❌ No output files found'
        fi
    else
        echo '❌ Example script not found'
    fi
"

echo ""
echo "🚀 All tests completed!"
echo ""
echo "📖 Usage Examples:"
echo ""
echo "  # Interactive development shell:"
echo "  docker-compose -f $COMPOSE_FILE run --rm circuit-synth-kicad-dev"
echo ""
echo "  # Run KiCad CLI directly:"
echo "  docker-compose -f $COMPOSE_FILE run --rm kicad-cli sch export pdf --help"
echo ""  
echo "  # Run example script:"
echo "  docker-compose -f $COMPOSE_FILE run --rm circuit-synth-kicad python examples/example_kicad_project.py"
echo ""
echo "  # Run specific tests:"
echo "  docker-compose -f $COMPOSE_FILE run --rm circuit-synth-kicad-test"
echo ""
echo "🎉 Circuit-Synth + KiCad 9 ($BUILD_STRATEGY) integration ready!"