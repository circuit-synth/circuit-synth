#!/bin/bash
# Download KiCad symbol libraries from GitLab

set -e

echo "📦 Downloading KiCad symbol libraries from GitLab..."

# Create symbols directory
SYMBOLS_DIR="/usr/share/kicad/symbols"
sudo mkdir -p "$SYMBOLS_DIR"

# Download KiCad symbols repository
cd /tmp
git clone --depth=1 https://gitlab.com/kicad/libraries/kicad-symbols.git
cd kicad-symbols

# Copy all .kicad_sym files to the symbols directory
echo "📂 Installing symbol libraries..."
sudo find . -name "*.kicad_sym" -exec cp {} "$SYMBOLS_DIR/" \;

echo "✅ KiCad symbol libraries installed to $SYMBOLS_DIR"
echo "📊 Installed $(sudo find "$SYMBOLS_DIR" -name "*.kicad_sym" | wc -l) symbol libraries"

# List some examples
echo "📋 Example libraries installed:"
sudo ls "$SYMBOLS_DIR" | head -10