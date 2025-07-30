# Rust Integration for PyPI Release

This document outlines three approaches for integrating Rust logic into the official PyPI release of Circuit-Synth.

## Current Rust Modules

The project includes 9 high-performance Rust modules:
- `rust_core_circuit_engine` - Core circuit logic with performance optimizations
- `rust_force_directed_placement` - Advanced component placement algorithms  
- `rust_io_processor` - High-speed file I/O operations
- `rust_kicad_schematic_writer` - Optimized KiCad schematic generation
- `rust_netlist_processor` - Fast netlist processing and generation
- `rust_pin_calculator` - Pin coordinate calculations
- `rust_reference_manager` - Component reference management
- `rust_symbol_cache` - Symbol caching and indexing
- `rust_symbol_search` - Fuzzy symbol search capabilities

## Integration Approaches

### 1. Pre-built Wheels (Recommended) ⭐

**Best for: Production releases with maximum performance**

Build platform-specific wheels containing compiled Rust extensions:

```bash
# Install build tools
pip install maturin cibuildwheel

# Build for current platform
maturin build --release --features python

# Build for multiple platforms using cibuildwheel
cibuildwheel --platform linux
cibuildwheel --platform windows  
cibuildwheel --platform macos
```

**Advantages:**
- ✅ Users get optimized Rust performance immediately
- ✅ No compilation required during installation
- ✅ Works on systems without Rust toolchain
- ✅ Fastest runtime performance

**Disadvantages:**
- ❌ Larger wheel sizes (~50-100MB vs ~5MB)
- ❌ Must build for each platform (Linux, Windows, macOS)
- ❌ Complex CI/CD setup required

### 2. Optional Rust Dependencies

**Best for: Backward compatibility with performance upgrades**

Make Rust modules optional extras that fall back to Python implementations:

```toml
# pyproject.toml
[project.optional-dependencies]
rust = [
    "maturin>=1.0.0",
    # Rust modules as optional dependencies
]
performance = [
    "circuit-synth[rust]",
    # Other performance dependencies
]
```

Installation options:
```bash
# Basic Python-only installation
pip install circuit-synth

# With Rust performance boost
pip install circuit-synth[rust]

# Full performance suite
pip install circuit-synth[performance]
```

**Advantages:**
- ✅ Maintains compatibility for users without Rust
- ✅ Optional performance improvements
- ✅ Smaller base package size
- ✅ Gradual migration path

**Disadvantages:**
- ❌ Requires Rust toolchain for performance features
- ❌ Complex fallback logic needed
- ❌ Installation complexity for end users

### 3. Hybrid Release Strategy

**Best for: Supporting both user types**

Publish two versions:
- `circuit-synth` - Python-only version (current)
- `circuit-synth-rust` - Full Rust integration

```bash
# Python-only installation
pip install circuit-synth

# Rust-accelerated installation  
pip install circuit-synth-rust
```

**Advantages:**
- ✅ Clear separation of concerns
- ✅ Users choose their preferred version
- ✅ No fallback complexity
- ✅ Maintains existing user base

**Disadvantages:**
- ❌ Maintain two separate packages
- ❌ Documentation complexity
- ❌ Potential confusion between versions

## Recommended Implementation: Pre-built Wheels

Based on your mature Rust codebase and professional target audience, **pre-built wheels** are recommended:

### Step 1: Configure Maturin Integration

```toml
# pyproject.toml additions
[build-system]
requires = ["maturin>=1.0,<2.0", "setuptools>=61.0", "wheel"]
build-backend = "maturin"

[tool.maturin]
python-source = "src"
module-name = "circuit_synth._rust"
features = ["pyo3/extension-module"]

# Build multiple Rust modules
[[tool.maturin.modules]]
name = "circuit_synth._rust.core_engine"
path = "rust_modules/rust_core_circuit_engine"

[[tool.maturin.modules]]  
name = "circuit_synth._rust.placement"
path = "rust_modules/rust_force_directed_placement"

# ... additional modules
```

### Step 2: Set Up CI/CD for Multi-Platform Builds

```yaml
# .github/workflows/build-wheels.yml
name: Build Wheels

on:
  release:
    types: [published]

jobs:
  build_wheels:
    name: Build wheels on ${{ matrix.os }}
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]

    steps:
    - uses: actions/checkout@v4
    
    - name: Build wheels
      uses: PyO3/maturin-action@v1
      with:
        command: build
        args: --release --out dist --find-interpreter
        
    - name: Upload wheels
      uses: actions/upload-artifact@v3
      with:
        name: wheels
        path: dist
```

### Step 3: Update Package Configuration

```toml
# Add Rust-specific classifiers
classifiers = [
    # ... existing classifiers
    "Programming Language :: Rust",
    "Topic :: Software Development :: Libraries :: Python Modules",
]

# Add Rust build dependencies
[project.optional-dependencies]
build = [
    "maturin>=1.0.0",
    "setuptools-rust>=1.5.0",
]
```

### Step 4: Python Integration Layer

```python
# src/circuit_synth/rust_integration.py
"""Rust integration layer with fallbacks."""

try:
    from circuit_synth._rust import (
        core_engine,
        placement,
        netlist_processor,
        # ... other modules
    )
    RUST_AVAILABLE = True
except ImportError:
    RUST_AVAILABLE = False
    # Import Python fallbacks
    from circuit_synth.python_implementations import (
        core_engine,
        placement, 
        netlist_processor,
    )

def get_engine():
    """Get the best available circuit engine."""
    if RUST_AVAILABLE:
        return core_engine.RustCircuitEngine()
    else:
        return core_engine.PythonCircuitEngine()
```

## Performance Impact

Based on your existing benchmarks, Rust integration should provide:
- **10-50x faster** component processing
- **5-20x faster** netlist generation  
- **3-10x faster** symbol searching
- **Reduced memory usage** for large circuits

## Migration Path

1. **Phase 1**: Add Rust as optional dependency (`circuit-synth[rust]`)
2. **Phase 2**: Build pre-compiled wheels for major platforms
3. **Phase 3**: Make Rust the default with Python fallbacks
4. **Phase 4**: Rust-only release (optional, for maximum performance)

## Testing Strategy

```bash
# Test Python-only installation
pip install dist/circuit_synth-0.1.0-py3-none-any.whl
python -c "import circuit_synth; print('Python OK')"

# Test Rust-enabled installation  
pip install dist/circuit_synth-0.1.0-cp311-cp311-linux_x86_64.whl
python -c "import circuit_synth; print('Rust available:', circuit_synth.RUST_AVAILABLE)"

# Performance comparison
python scripts/benchmark_rust_integration.py
```

This approach provides maximum performance while maintaining compatibility and professional deployment standards.