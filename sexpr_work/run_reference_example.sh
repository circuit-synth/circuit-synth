#!/bin/bash


echo "🧹 Cleaning circuit_synth cache..."
rm -rf ~/.cache/circuit_synth

echo "🗑️  Removing existing reference_generated directory..."
rm -rf reference_generated

echo "🚀 Running reference circuit generation..."
uv run python reference_circuit-synth/main.py

open reference_generated/reference_generated.kicad_pro
echo "✅ Done!"