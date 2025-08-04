#!/bin/bash

# Circuit-Synth Rust Module Rebuild Script
# Incremental rebuild of all Rust modules with latest code (use --clean for full rebuild)

set -e  # Exit on any error

echo "🦀 Circuit-Synth Rust Module Rebuild Script"
echo "============================================"
echo ""

# Parse command line arguments
CLEAN_BUILD=false
if [[ "$1" == "--clean" ]]; then
    CLEAN_BUILD=true
    echo "🧹 Clean build mode enabled"
fi

# Get the base directory dynamically
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(dirname "$SCRIPT_DIR")"
RUST_MODULES_DIR="$BASE_DIR/rust_modules"

# Function to incrementally rebuild a Rust module
rebuild_rust_module() {
    local module_name=$1
    local module_path="$RUST_MODULES_DIR/$module_name"
    
    if [ ! -d "$module_path" ]; then
        echo "❌ Module $module_name not found at $module_path"
        return 1
    fi
    
    echo "🔨 Rebuilding $module_name..."
    cd "$module_path"
    
    # Only clean if requested
    if [ "$CLEAN_BUILD" = true ]; then
        echo "  🧹 Cleaning previous builds..."
        cargo clean
        
        # Remove any existing Python wheels and build artifacts
        rm -rf target/
        rm -rf build/
        rm -rf dist/
        rm -rf *.egg-info/
    fi
    
    # Update Rust dependencies
    echo "  📦 Updating dependencies..."
    cargo update
    
    # Build with maturin (for Python bindings)
    if [ -f "pyproject.toml" ] || [ -f "Cargo.toml" ]; then
        echo "  🐍 Building Python bindings with maturin..."
        
        # Set VIRTUAL_ENV to use the main project's virtual environment
        if [ -d "$BASE_DIR/.venv" ]; then
            echo "  🎯 Installing in main project virtual environment..."
            VIRTUAL_ENV="$BASE_DIR/.venv" maturin develop --release
        else
            echo "  ⚠️  Main project .venv not found, using default installation..."
            maturin develop --release
        fi
        
        echo "  ✅ $module_name rebuilt successfully"
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

if [ "$CLEAN_BUILD" = true ]; then
    echo "🚀 Starting comprehensive clean Rust rebuild..."
else
    echo "🚀 Starting incremental Rust rebuild..."
fi
echo "Modules to rebuild: ${RUST_MODULES[@]}"
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

if ! command -v maturin &> /dev/null; then
    echo "📦 Installing maturin with uv..."
    uv pip install maturin
fi

echo "✅ Rust toolchain ready"
echo ""

# Rebuild each module
for module in "${RUST_MODULES[@]}"; do
    if rebuild_rust_module "$module"; then
        SUCCESSFUL_BUILDS+=("$module")
    else
        FAILED_BUILDS+=("$module")
        echo "❌ Failed to rebuild $module"
    fi
done

# Summary
echo "🎯 Rebuild Summary"
echo "=================="
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
echo ""
echo "💡 Usage:"
echo "  ./rebuild_all_rust.sh          # Incremental build (default, faster)"
echo "  ./rebuild_all_rust.sh --clean  # Clean build (slower but thorough)"

cd "$BASE_DIR"