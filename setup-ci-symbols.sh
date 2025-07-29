#!/bin/bash
# Backup script to set up KiCad symbols for CI with explicit environment setup

set -e

echo "🔧 Setting up KiCad symbols for CI testing..."

# Create a dedicated directory for CI symbols
CI_SYMBOLS_DIR="/tmp/kicad-symbols-ci"
mkdir -p "$CI_SYMBOLS_DIR"

# Download symbols to the CI directory
echo "📋 Downloading symbols to $CI_SYMBOLS_DIR..."

wget -O "$CI_SYMBOLS_DIR/Device.kicad_sym" \
  "https://gitlab.com/kicad/libraries/kicad-symbols/-/raw/master/Device.kicad_sym"

wget -O "$CI_SYMBOLS_DIR/power.kicad_sym" \
  "https://gitlab.com/kicad/libraries/kicad-symbols/-/raw/master/power.kicad_sym"

wget -O "$CI_SYMBOLS_DIR/Regulator_Linear.kicad_sym" \
  "https://gitlab.com/kicad/libraries/kicad-symbols/-/raw/master/Regulator_Linear.kicad_sym"

echo "✅ Downloaded $(find "$CI_SYMBOLS_DIR" -name "*.kicad_sym" | wc -l) symbol libraries"

# Set environment variable for the session
echo "🔗 Setting KICAD_SYMBOL_DIR=$CI_SYMBOLS_DIR"
export KICAD_SYMBOL_DIR="$CI_SYMBOLS_DIR"

# Verify symbols are accessible
echo "🧪 Testing symbol access..."
python3 -c "
import os
os.environ['KICAD_SYMBOL_DIR'] = '$CI_SYMBOLS_DIR'
from circuit_synth.kicad.kicad_symbol_cache import SymbolLibCache
try:
    data = SymbolLibCache.get_symbol_data('Device:R')
    print(f'✅ Successfully loaded Device:R symbol with {len(data[\"pins\"])} pins')
except Exception as e:
    print(f'❌ Failed to load symbol: {e}')
    raise
"

echo "✅ KiCad symbols setup complete for CI"