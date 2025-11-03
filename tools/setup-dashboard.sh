#!/bin/bash
# Setup script for Claude API Dashboard on Raspberry Pi
#
# This installs dashboard dependencies system-wide since this Pi
# is dedicated to running the TAC coordinator.

set -e

echo "📦 Installing dashboard dependencies..."
echo ""

# Check if we're on the dedicated Pi
if [ ! -f "adws/coordinator.py" ]; then
    echo "❌ Error: Must run from circuit-synth repository root"
    exit 1
fi

# Install dashboard dependencies
pip3 install --break-system-packages \
    dash>=2.14.0 \
    plotly>=5.18.0 \
    pandas>=2.1.0

echo ""
echo "✅ Dashboard dependencies installed!"
echo ""
echo "To start the dashboard:"
echo "  python3 dashboard/api_dashboard.py"
echo ""
echo "Then open: http://localhost:8050"
