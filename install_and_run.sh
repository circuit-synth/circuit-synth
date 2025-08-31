#!/bin/bash

echo "🚀 Installing dependencies and running voltage divider demo"
echo "=========================================================="

# Install dependencies using uv
echo "📦 Installing plotly..."
uv pip install plotly

echo "📦 Installing numpy..."
uv pip install numpy

echo ""
echo "🎯 Running voltage divider demo..."
echo "=================================="

# Run the demo
uv run python voltage_divider_demo.py