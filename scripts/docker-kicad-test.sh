#!/bin/bash

# Circuit-Synth + KiCad Docker Integration Test Script
set -e

echo "🔧 Building Circuit-Synth + KiCad Docker image..."
docker-compose -f docker/docker-compose.kicad.yml build circuit-synth-kicad

echo "🧪 Testing KiCad CLI functionality..."
docker-compose -f docker/docker-compose.kicad.yml run --rm circuit-synth-kicad bash -c "
    echo '=== KiCad CLI Version Check ==='
    kicad-cli version
    
    echo '=== KiCad Library Verification ==='
    ls -la /usr/share/kicad/symbols/ | head -10
    ls -la /usr/share/kicad/footprints/ | head -10
    
    echo '=== Circuit-Synth Import Test ==='
    python -c 'import circuit_synth; print(\"✅ Circuit-Synth imported successfully\")'
    
    echo '=== Integration Test ==='
    python -c '
import subprocess
import os

# Test KiCad CLI from Python
try:
    result = subprocess.run([\"kicad-cli\", \"version\"], capture_output=True, text=True, check=True)
    print(f\"✅ KiCad CLI accessible from Python: {result.stdout.strip()}\")
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

echo "🎯 Testing example project generation..."
docker-compose -f docker/docker-compose.kicad.yml run --rm circuit-synth-kicad bash -c "
    echo '=== Running Circuit-Synth Example ==='
    python examples/example_kicad_project.py
    
    echo '=== Verifying Generated Files ==='
    if [ -d 'output' ]; then
        find output -name '*.kicad_*' -o -name '*.net' | head -10
        echo '✅ KiCad files generated successfully'
    else
        echo '❌ No output directory found'
    fi
"

echo "🚀 All tests completed!"
echo ""
echo "Usage examples:"
echo "  # Interactive development shell:"
echo "  docker-compose -f docker/docker-compose.kicad.yml run --rm circuit-synth-kicad-dev"
echo ""
echo "  # Run KiCad CLI directly:"
echo "  docker-compose -f docker/docker-compose.kicad.yml run --rm kicad-cli sch export pdf --help"
echo ""
echo "  # Run example script:"
echo "  docker-compose -f docker/docker-compose.kicad.yml run --rm circuit-synth-kicad python examples/example_kicad_project.py"