#!/bin/bash
set -e

echo "Building Rust modules for circuit-synth..."

# Build rust_netlist_processor
echo "Building rust_netlist_processor..."
cd rust_modules/rust_netlist_processor
maturin develop --release
cd ../..

# Build rust_force_directed_placement
echo "Building rust_force_directed_placement..."
cd rust_modules/rust_force_directed_placement
maturin develop --release
cd ../..

echo "All Rust modules built successfully!"
echo ""
echo "If you encounter import errors, make sure you have:"
echo "  1. Rust installed (https://rustup.rs/)"
echo "  2. maturin installed: pip install maturin"
echo "  3. All dependencies available"