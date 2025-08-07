#!/bin/bash
# Demo script showing CLI debugging commands

echo "🔧 Demonstrating Circuit Debugging CLI"
echo "======================================"
echo ""

# Start a debugging session
echo "Starting debug session..."
uv run python -m circuit_synth.tools.debug_cli start "STM32F4_Board" --version "1.2" --symptoms "I2C not working" "No ACK from sensor"

echo ""
echo "Adding measurements..."
uv run python -m circuit_synth.tools.debug_cli measure "SDA_High" "3.3" --unit "V" --notes "Measured with pullup"
uv run python -m circuit_synth.tools.debug_cli measure "SCL_High" "3.3" --unit "V"

echo ""
echo "Analyzing symptoms..."
uv run python -m circuit_synth.tools.debug_cli analyze

echo ""
echo "Getting suggestions..."
uv run python -m circuit_synth.tools.debug_cli suggest

echo ""
echo "Showing I2C troubleshooting tree..."
uv run python -m circuit_synth.tools.debug_cli tree i2c