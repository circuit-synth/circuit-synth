#!/bin/bash
# Cross-platform script to set up KiCad symbols for CI testing
# Compatible with Linux, macOS, and Windows (via Git Bash/WSL)

set -e

echo "🔧 Setting up KiCad symbols for CI testing..."

# Detect platform and set appropriate temp directory
if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]] || [[ -n "$WINDIR" ]]; then
    # Windows (Git Bash, MSYS2, or Cygwin)
    CI_SYMBOLS_DIR="${TEMP:-$TMP}/kicad-symbols-ci"
    if [[ -z "$CI_SYMBOLS_DIR" ]]; then
        CI_SYMBOLS_DIR="/tmp/kicad-symbols-ci"
    fi
elif [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    CI_SYMBOLS_DIR="/tmp/kicad-symbols-ci"
else
    # Linux and others
    CI_SYMBOLS_DIR="/tmp/kicad-symbols-ci"
fi

echo "📁 Using symbols directory: $CI_SYMBOLS_DIR"
mkdir -p "$CI_SYMBOLS_DIR"

# Download symbols to the CI directory
echo "📋 Downloading symbols to $CI_SYMBOLS_DIR..."

# Detect available download tool (curl preferred, fallback to wget)
if command -v curl >/dev/null 2>&1; then
    DOWNLOAD_CMD="curl -sSLf -o"
    echo "📥 Using curl for downloads..."
elif command -v wget >/dev/null 2>&1; then
    DOWNLOAD_CMD="wget -q -O"
    echo "📥 Using wget for downloads..."
else
    echo "❌ Error: Neither curl nor wget is available!"
    echo "   Please install curl or wget to download KiCad symbols."
    exit 1
fi

# Download function with error handling
download_symbol() {
    local filename="$1"
    local url="$2"
    local output_path="$CI_SYMBOLS_DIR/$filename"
    
    echo "⬇️  Downloading $filename..."
    if $DOWNLOAD_CMD "$output_path" "$url"; then
        # Verify file was downloaded and isn't empty
        if [[ -f "$output_path" ]] && [[ -s "$output_path" ]]; then
            echo "✅ Successfully downloaded $filename ($(stat -f%z "$output_path" 2>/dev/null || stat -c%s "$output_path" 2>/dev/null || echo "unknown") bytes)"
        else
            echo "❌ Downloaded $filename appears to be empty or invalid"
            return 1
        fi
    else
        echo "❌ Failed to download $filename from $url"
        return 1
    fi
}

# Download required symbol libraries
download_symbol "Device.kicad_sym" \
  "https://gitlab.com/kicad/libraries/kicad-symbols/-/raw/master/Device.kicad_sym"

download_symbol "power.kicad_sym" \
  "https://gitlab.com/kicad/libraries/kicad-symbols/-/raw/master/power.kicad_sym"

download_symbol "Regulator_Linear.kicad_sym" \
  "https://gitlab.com/kicad/libraries/kicad-symbols/-/raw/master/Regulator_Linear.kicad_sym"

echo "✅ Downloaded $(find "$CI_SYMBOLS_DIR" -name "*.kicad_sym" | wc -l) symbol libraries"

# Set environment variable for the session
echo "🔗 Setting KICAD_SYMBOL_DIR=$CI_SYMBOLS_DIR"
export KICAD_SYMBOL_DIR="$CI_SYMBOLS_DIR"

# Cross-platform Python detection
PYTHON_CMD=""
if command -v python3 >/dev/null 2>&1; then
    PYTHON_CMD="python3"
elif command -v python >/dev/null 2>&1; then
    # Check if it's Python 3
    PYTHON_VERSION=$(python -c "import sys; print(sys.version_info[0])" 2>/dev/null || echo "2")
    if [[ "$PYTHON_VERSION" == "3" ]]; then
        PYTHON_CMD="python"
    fi
fi

if [[ -z "$PYTHON_CMD" ]]; then
    echo "⚠️  Python 3 not found - skipping symbol validation test"
    echo "   (This is OK for CI environments that will set up Python separately)"
else
    # Verify symbols are accessible
    echo "🧪 Testing symbol access with $PYTHON_CMD..."
    $PYTHON_CMD -c "
import os
import sys
os.environ['KICAD_SYMBOL_DIR'] = '$CI_SYMBOLS_DIR'
try:
    from circuit_synth.kicad.kicad_symbol_cache import SymbolLibCache
    data = SymbolLibCache.get_symbol_data('Device:R')
    print(f'✅ Successfully loaded Device:R symbol with {len(data[\"pins\"])} pins')
except ImportError as e:
    print(f'⚠️  circuit_synth not installed - symbols downloaded but validation skipped')
    print(f'   This is normal for CI setup phase. Error: {e}')
except Exception as e:
    print(f'❌ Failed to load symbol: {e}')
    sys.exit(1)
"
fi

# Print setup completion message
echo ""
echo "✅ KiCad symbols setup complete for CI"
echo "📁 Symbols location: $CI_SYMBOLS_DIR"
echo "🔧 Set KICAD_SYMBOL_DIR environment variable to use these symbols"
echo ""

# For CI usage instructions
if [[ -n "$CI" ]] || [[ -n "$GITHUB_ACTIONS" ]] || [[ -n "$GITLAB_CI" ]]; then
    echo "🤖 CI Environment Detected"
    echo "Add this to your CI configuration:"
    echo "   export KICAD_SYMBOL_DIR=\"$CI_SYMBOLS_DIR\""
    echo ""
fi