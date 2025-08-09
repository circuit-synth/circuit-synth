#!/bin/bash


echo "🧹 Cleaning circuit_synth cache..."
rm -rf ~/.cache/circuit_synth

echo "🗑️  Removing existing reference_generated directory..."
rm -rf reference_generated

echo "🚀 Running reference circuit generation..."
uv run python reference_circuit-synth/main.py

echo "📄 Generating PDFs with KiCad CLI for visual verification..."

# Generate PDF of main schematic
if [ -f "reference_generated/reference_generated.kicad_sch" ]; then
    kicad-cli sch export pdf \
        --output reference_generated/reference_generated_main.pdf \
        reference_generated/reference_generated.kicad_sch
    echo "✅ Generated: reference_generated/reference_generated_main.pdf"
else
    echo "❌ Main schematic file not found!"
fi

# Generate PDF of child schematic  
if [ -f "reference_generated/child1.kicad_sch" ]; then
    kicad-cli sch export pdf \
        --output reference_generated/child1.pdf \
        reference_generated/child1.kicad_sch
    echo "✅ Generated: reference_generated/child1.pdf"
else
    echo "❌ Child schematic file not found!"
fi

echo "📊 Generated files:"
ls -la reference_generated/*.pdf 2>/dev/null || echo "No PDFs found"

open reference_generated/reference_generated.kicad_pro
echo "✅ Done!"