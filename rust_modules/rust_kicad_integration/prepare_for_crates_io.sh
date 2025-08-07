#!/bin/bash
# Script to prepare the Rust KiCad module for extraction to its own repository

echo "Preparing Rust KiCad module for extraction to standalone repository..."

# Create a directory for the new repository
EXPORT_DIR="kicad-rust-export"
rm -rf $EXPORT_DIR
mkdir -p $EXPORT_DIR

echo "📁 Created export directory: $EXPORT_DIR"

# Copy source files
cp -r src/ $EXPORT_DIR/src/
cp Cargo_crates_io.toml $EXPORT_DIR/Cargo.toml
cp README_crates_io.md $EXPORT_DIR/README.md

echo "📄 Copied source files"

# Create examples directory
mkdir -p $EXPORT_DIR/examples

# Create a simple Rust example
cat > $EXPORT_DIR/examples/voltage_divider.rs << 'EOF'
//! Example: Create a simple voltage divider circuit

use kicad::{Schematic, Component, Net};

fn main() -> Result<(), Box<dyn std::error::Error>> {
    // Create a new schematic
    let mut schematic = Schematic::new("VoltageDivider");
    
    // Add resistors
    schematic.add_component(Component {
        reference: "R1".to_string(),
        symbol: "Device:R".to_string(),
        value: Some("10k".to_string()),
        position: (50.0, 50.0),
        footprint: Some("Resistor_SMD:R_0603_1608Metric".to_string()),
    })?;
    
    schematic.add_component(Component {
        reference: "R2".to_string(),
        symbol: "Device:R".to_string(),
        value: Some("10k".to_string()),
        position: (50.0, 100.0),
        footprint: Some("Resistor_SMD:R_0603_1608Metric".to_string()),
    })?;
    
    // Create nets
    let vin = Net::new("VIN");
    let vout = Net::new("VOUT");
    let gnd = Net::new("GND");
    
    // Connect components
    schematic.connect("R1", 1, &vin)?;
    schematic.connect("R1", 2, &vout)?;
    schematic.connect("R2", 1, &vout)?;
    schematic.connect("R2", 2, &gnd)?;
    
    // Save to file
    schematic.save("voltage_divider.kicad_sch")?;
    
    println!("✅ Created voltage_divider.kicad_sch");
    Ok(())
}
EOF

echo "📝 Created example files"

# Create LICENSE files
cat > $EXPORT_DIR/LICENSE-MIT << 'EOF'
MIT License

Copyright (c) 2024 Circuit-Synth Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
EOF

cat > $EXPORT_DIR/LICENSE-APACHE << 'EOF'
Apache License
Version 2.0, January 2004
http://www.apache.org/licenses/

Copyright 2024 Circuit-Synth Contributors

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
EOF

echo "📜 Created LICENSE files"

# Create .gitignore
cat > $EXPORT_DIR/.gitignore << 'EOF'
# Rust
target/
Cargo.lock
**/*.rs.bk
*.pdb

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Test outputs
*.kicad_sch
*.kicad_pcb
*.log
EOF

echo "🔧 Created .gitignore"

# Create GitHub Actions workflow
mkdir -p $EXPORT_DIR/.github/workflows

cat > $EXPORT_DIR/.github/workflows/ci.yml << 'EOF'
name: CI

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

env:
  CARGO_TERM_COLOR: always

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - uses: dtolnay/rust-toolchain@stable
    - uses: Swatinem/rust-cache@v2
    - name: Run tests
      run: cargo test --all-features
    - name: Check formatting
      run: cargo fmt -- --check
    - name: Run clippy
      run: cargo clippy --all-features -- -D warnings

  python:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.8', '3.9', '3.10', '3.11', '3.12']
    steps:
    - uses: actions/checkout@v3
    - uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    - uses: dtolnay/rust-toolchain@stable
    - name: Install maturin
      run: pip install maturin
    - name: Build Python package
      run: maturin build --features python
    - name: Install package
      run: pip install target/wheels/*.whl
    - name: Test import
      run: python -c "import kicad; print(kicad.__version__)"
EOF

cat > $EXPORT_DIR/.github/workflows/release.yml << 'EOF'
name: Release

on:
  push:
    tags:
      - 'v*'

jobs:
  publish-crates-io:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - uses: dtolnay/rust-toolchain@stable
    - name: Publish to crates.io
      run: cargo publish
      env:
        CARGO_REGISTRY_TOKEN: ${{ secrets.CARGO_REGISTRY_TOKEN }}

  publish-pypi:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    - name: Install maturin
      run: pip install maturin
    - name: Build wheels
      run: maturin build --release --features python
    - name: Publish to PyPI
      run: maturin publish --features python
      env:
        MATURIN_PYPI_TOKEN: ${{ secrets.PYPI_API_TOKEN }}
EOF

echo "🚀 Created GitHub Actions workflows"

# Create CONTRIBUTING.md
cat > $EXPORT_DIR/CONTRIBUTING.md << 'EOF'
# Contributing to kicad-rust

We welcome contributions! Here's how to get started:

## Development Setup

1. Clone the repository:
```bash
git clone https://github.com/circuit-synth/kicad-rust.git
cd kicad-rust
```

2. Build the project:
```bash
cargo build --all-features
```

3. Run tests:
```bash
cargo test --all-features
```

## Python Development

To work on Python bindings:

```bash
pip install maturin
maturin develop --features python
```

## Making Changes

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to your fork (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## Code Style

- Run `cargo fmt` before committing
- Run `cargo clippy` and fix any warnings
- Add documentation for public APIs
- Include examples for new features

## Reporting Issues

Please use GitHub Issues to report bugs or request features.
EOF

echo "📖 Created CONTRIBUTING.md"

echo ""
echo "✅ Export preparation complete!"
echo ""
echo "Next steps:"
echo "1. Review the exported files in: $EXPORT_DIR/"
echo "2. Create repository: https://github.com/circuit-synth/kicad-rust"
echo "3. Push the code:"
echo "   cd $EXPORT_DIR"
echo "   git init"
echo "   git add ."
echo "   git commit -m 'Initial commit'"
echo "   git remote add origin git@github.com:circuit-synth/kicad-rust.git"
echo "   git push -u origin main"
echo "4. Set up repository secrets:"
echo "   - CARGO_REGISTRY_TOKEN (from crates.io)"
echo "   - PYPI_API_TOKEN (from PyPI)"
echo "5. Publish to crates.io:"
echo "   cargo publish --dry-run  # Test first"
echo "   cargo publish"
echo ""
echo "📦 The crate will be available at: https://crates.io/crates/kicad"