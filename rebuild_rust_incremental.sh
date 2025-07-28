#!/bin/bash

# Circuit-Synth Rust Module Incremental Rebuild Script
# Rebuilds Rust modules WITHOUT cleaning first (faster incremental builds)

set -e  # Exit on any error

echo "🦀 Circuit-Synth Rust Module Incremental Rebuild Script"
echo "======================================================="
echo ""

# Get the base directory
BASE_DIR="/Users/shanemattner/Desktop/Circuit_Synth2/submodules/circuit-synth"
RUST_MODULES_DIR="$BASE_DIR/rust_modules"

# Function to incrementally rebuild a Rust module
rebuild_rust_module_incremental() {
    local module_name=$1
    local module_path="$RUST_MODULES_DIR/$module_name"
    
    if [ ! -d "$module_path" ]; then
        echo "❌ Module $module_name not found at $module_path"
        return 1
    fi
    
    echo "🔨 Incrementally rebuilding $module_name..."
    cd "$module_path"
    
    # Update Rust dependencies (but don't clean)
    echo "  📦 Updating dependencies..."
    cargo update
    
    # Build with maturin (for Python bindings) - incremental
    if [ -f "pyproject.toml" ] || [ -f "Cargo.toml" ]; then
        echo "  🐍 Incremental build with maturin..."
        
        # Use existing virtual environment or create if needed
        if [ ! -d ".venv" ]; then
            echo "  📁 Creating virtual environment..."
            python3 -m venv .venv
        fi
        
        source .venv/bin/activate
        
        # Install/upgrade maturin if needed
        if ! pip show maturin &> /dev/null; then
            echo "  📥 Installing maturin..."
            pip install maturin
        fi
        
        # Incremental build and install the module
        maturin develop --release
        
        echo "  ✅ $module_name incrementally rebuilt successfully"
    else
        echo "  ⚠️  No pyproject.toml found for $module_name, skipping Python binding build"
    fi
    
    echo ""
}

# List of all Rust modules to rebuild
RUST_MODULES=(
    "rust_symbol_cache"
    "rust_core_circuit_engine" 
    "rust_force_directed_placement"
    "rust_kicad_integration"
    "rust_io_processor"
    "rust_netlist_processor"
    "rust_reference_manager"
    "rust_pin_calculator"
    "rust_symbol_search"
)

echo "🚀 Starting incremental Rust rebuild..."
echo "Modules to rebuild: ${RUST_MODULES[@]}"
echo "⚡ Note: This will NOT clean previous builds for faster compilation"
echo ""

# Track successful and failed builds
SUCCESSFUL_BUILDS=()
FAILED_BUILDS=()

# Ensure we have Rust and required tools
echo "🔧 Checking Rust toolchain..."
if ! command -v cargo &> /dev/null; then
    echo "❌ Cargo not found. Please install Rust: https://rustup.rs/"
    exit 1
fi

echo "✅ Rust toolchain ready"
echo ""

# Rebuild each module incrementally
for module in "${RUST_MODULES[@]}"; do
    if rebuild_rust_module_incremental "$module"; then
        SUCCESSFUL_BUILDS+=("$module")
    else
        FAILED_BUILDS+=("$module")
        echo "❌ Failed to incrementally rebuild $module"
    fi
done

# Summary
echo "🎯 Incremental Rebuild Summary"
echo "=============================="
echo "✅ Successfully rebuilt: ${#SUCCESSFUL_BUILDS[@]} modules"
for module in "${SUCCESSFUL_BUILDS[@]}"; do
    echo "  ✓ $module"
done

if [ ${#FAILED_BUILDS[@]} -gt 0 ]; then
    echo ""
    echo "❌ Failed to rebuild: ${#FAILED_BUILDS[@]} modules"
    for module in "${FAILED_BUILDS[@]}"; do
        echo "  ✗ $module"
    done
fi

echo ""
echo "🔧 Next Steps:"
echo "1. Test the rebuilt modules with: uv run python examples/example_kicad_project.py"
echo "2. Check performance improvements"
echo "3. Verify graphics rendering works correctly"

cd "$BASE_DIR"