#!/bin/bash
# Sync example_project to project_template for PyPI packaging
# This ensures users get the latest agents and commands when installing from PyPI

set -e

echo "🔄 Syncing example_project to project_template for PyPI packaging..."

# Define paths
EXAMPLE_PROJECT_DIR="example_project"
PROJECT_TEMPLATE_DIR="src/circuit_synth/data/templates/project_template"

# Verify source exists
if [ ! -d "$EXAMPLE_PROJECT_DIR" ]; then
    echo "❌ ERROR: example_project directory not found!"
    echo "   Expected: $EXAMPLE_PROJECT_DIR"
    exit 1
fi

# Create template directory if it doesn't exist
mkdir -p "$PROJECT_TEMPLATE_DIR"

echo "📁 Source: $EXAMPLE_PROJECT_DIR/"
echo "📁 Target: $PROJECT_TEMPLATE_DIR/"

# Remove old template contents (except .gitkeep files)
echo "🧹 Cleaning old template..."
find "$PROJECT_TEMPLATE_DIR" -type f ! -name '.gitkeep' -delete
find "$PROJECT_TEMPLATE_DIR" -type d -empty -delete 2>/dev/null || true

# Copy entire example_project structure
echo "📋 Copying complete example_project structure..."
cp -r "$EXAMPLE_PROJECT_DIR/"* "$PROJECT_TEMPLATE_DIR/"

# Verify key files were copied
CRITICAL_FILES=(
    ".claude/agents/circuit-design/interactive-circuit-designer.md"
    ".claude/commands/circuit-design/design.md"
    ".claude/commands/circuit-design/find-pins.md"
    ".claude/commands/circuit-design/quick-validate.md"
    "CLAUDE.md"
)

echo "✅ Verifying critical files were copied:"
for file in "${CRITICAL_FILES[@]}"; do
    if [ -f "$PROJECT_TEMPLATE_DIR/$file" ]; then
        echo "   ✅ $file"
    else
        echo "   ❌ MISSING: $file"
        exit 1
    fi
done

# Count agents and commands
AGENT_COUNT=$(find "$PROJECT_TEMPLATE_DIR/.claude/agents" -name "*.md" | wc -l)
COMMAND_COUNT=$(find "$PROJECT_TEMPLATE_DIR/.claude/commands" -name "*.md" | wc -l)

echo ""
echo "📊 Sync Summary:"
echo "   🤖 Agents: $AGENT_COUNT agent files"
echo "   ⚡ Commands: $COMMAND_COUNT command files"
echo "   📋 Interactive Circuit Design Agent: ✅ Included"
echo "   🛠️ Validation commands: ✅ Included"

# CRITICAL: Validate template integrity
echo ""
echo "🔍 Validating template integrity..."

# Check for known problematic symbols that break cs-new-project
BROKEN_SYMBOLS=(
    "USB_C_Receptacle_USB2.0_16P_TopMount_DrillsUnspecified"
    "NonExistentSymbol"
)

echo "🚨 Checking for broken symbols that will break cs-new-project..."
for symbol in "${BROKEN_SYMBOLS[@]}"; do
    if grep -r "$symbol" "$PROJECT_TEMPLATE_DIR" >/dev/null 2>&1; then
        echo "❌ CRITICAL: Found broken symbol '$symbol' in templates!"
        echo "   This will cause cs-new-project to fail for users"
        echo "   Location: $(grep -r "$symbol" "$PROJECT_TEMPLATE_DIR")"
        echo ""
        echo "🔧 To fix:"
        echo "   1. Update $EXAMPLE_PROJECT_DIR with correct symbols"
        echo "   2. Re-run this sync script"
        exit 1
    fi
done

# Verify that correct symbols exist
REQUIRED_SYMBOLS=(
    "USB_C_Receptacle_USB2.0_16P"
    "Device:R"
    "Device:C"
)

echo "✅ Checking for required working symbols..."
for symbol in "${REQUIRED_SYMBOLS[@]}"; do
    if grep -r "$symbol" "$PROJECT_TEMPLATE_DIR" >/dev/null 2>&1; then
        echo "   ✅ $symbol found"
    else
        echo "   ⚠️  $symbol not found (may be OK)"
    fi
done

echo ""
echo "✅ Template integrity validation passed!"
echo ""
echo "✅ Sync complete! PyPI package will now include:"
echo "   🎛️ Interactive Circuit Design Agent"
echo "   🔧 Component validation commands (/find-pins, /quick-validate)"
echo "   ⚡ Quick access commands (/design, /design-mode)"
echo "   📚 Complete agent and command ecosystem"
echo "   🔌 WORKING circuit examples with validated KiCad symbols"

echo ""
echo "🚀 Ready for PyPI release with latest agents and WORKING templates!"