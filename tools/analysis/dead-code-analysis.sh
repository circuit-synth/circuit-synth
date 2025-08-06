#!/bin/bash
"""
Dead Code Analysis Command Wrapper

This script implements the /dead-code-analysis Claude command.
"""

set -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/dead-code-analysis.py"

# Default target script
TARGET_SCRIPT="${1:-main.py}"

echo "🔍 Dead Code Analysis Starting..."
echo "📂 Target script: $TARGET_SCRIPT"
echo ""

# Check if Python script exists
if [[ ! -f "$PYTHON_SCRIPT" ]]; then
    echo "❌ Python script not found: $PYTHON_SCRIPT"
    exit 1
fi

# Check if target script exists
if [[ ! -f "$TARGET_SCRIPT" ]]; then
    echo "❌ Target script not found: $TARGET_SCRIPT"
    echo "💡 Make sure you're in the correct directory or specify the full path"
    exit 1
fi

# Run the Python analysis script
echo "🚀 Running dead code analysis..."
python3 "$PYTHON_SCRIPT" "$TARGET_SCRIPT"

echo ""
echo "✅ Dead code analysis complete!"
echo "📋 Review the generated Dead_Code_Analysis_Report.md for detailed results"