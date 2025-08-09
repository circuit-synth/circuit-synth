#!/bin/bash

# Clean cache and regenerate ESP32 development board

echo "🧹 Cleaning circuit_synth cache..."
rm -rf ~/.cache/circuit_synth

echo "🗑️  Removing existing ESP32_C6_Dev_Board directory..."
rm -rf ESP32_C6_Dev_Board

echo "🚀 Running ESP32 development board generation..."
uv run python example_project/circuit-synth/main.py

open ESP32_C6_Dev_Board/ESP32_C6_Dev_Board.kicad_pro
echo "✅ Done!"