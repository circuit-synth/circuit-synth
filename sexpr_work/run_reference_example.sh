#!/bin/bash


echo "🧹 Cleaning circuit_synth cache..."
rm -rf ~/.cache/circuit_synth

echo "🗑️  Removing existing test_multiunit directory..."
rm -rf test_multiunit

echo "🚀 Running multi-unit test circuit generation..."
uv run python test_multiunit.py

echo "📄 Generating PDFs with KiCad CLI for visual verification..."

# Generate PDF of main schematic
if [ -f "test_multiunit/test_multiunit.kicad_sch" ]; then
    kicad-cli sch export pdf \
        --output test_multiunit/test_multiunit_main.pdf \
        test_multiunit/test_multiunit.kicad_sch
    echo "✅ Generated: test_multiunit/test_multiunit_main.pdf"
else
    echo "❌ Main schematic file not found!"
fi

echo "📊 Generated files:"
ls -la test_multiunit/*.pdf 2>/dev/null || echo "No PDFs found"

open test_multiunit/test_multiunit.kicad_pro
echo "✅ Done!"