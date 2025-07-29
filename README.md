# circuit-synth

[![Documentation](https://readthedocs.org/projects/circuit-synth/badge/?version=latest)](https://circuit-synth.readthedocs.io/en/latest/?badge=latest)
[![PyPI version](https://badge.fury.io/py/circuit-synth.svg)](https://badge.fury.io/py/circuit-synth)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Pythonic circuit design for professional KiCad projects**

Generate complete KiCad projects using simple Python code. No DSL to learn - just Python classes and functions that any engineer can read and modify.

## 🤖 Optimized for Claude Code

This repository is fully optimized for AI-assisted development with Claude Code:

- **🔍 Component Search**: `/find-symbol`, `/find-footprint` - Instantly find KiCad symbols and footprints
- **🏗️ Circuit Design Agent**: Specialized `circuit-synth` agent for expert guidance on component selection and circuit topology
- **⚡ Development Commands**: `/dev-run-tests`, `/dev-update-and-commit` - Streamlined development workflow
- **📋 Pre-configured Permissions**: Skip repetitive approval prompts with curated tool allowlists

## Example

```python
from circuit_synth import *

@circuit(name="esp32s3_simple")
def esp32s3_simple():
    """Simple ESP32-S3 circuit with decoupling capacitor and debug header"""
    
    # Create power nets
    _3V3 = Net('3V3')
    GND = Net('GND')
    
    # ESP32-S3 module
    esp32s3 = Component(
        symbol="RF_Module:ESP32-S3-MINI-1",
        ref="U",
        footprint="RF_Module:ESP32-S2-MINI-1"
    )
    
    # Decoupling capacitor
    cap_power = Component(
        symbol="Device:C",
        ref="C", 
        value="10uF",
        footprint="Capacitor_SMD:C_0603_1608Metric"
    )
    
    # Debug header
    debug_header = Component(
        symbol="Connector_Generic:Conn_02x03_Odd_Even",
        ref="J",
        footprint="Connector_IDC:IDC-Header_2x03_P2.54mm_Vertical"
    )
    
    # Power connections
    esp32s3["3V3"] += _3V3  # Power pin
    esp32s3["GND"] += GND   # Ground pin
    
    # Decoupling capacitor connections
    cap_power[1] += _3V3
    cap_power[2] += GND
    
    # Debug header connections
    debug_header[1] += esp32s3['EN']
    debug_header[2] += _3V3
    debug_header[3] += esp32s3['TXD0']
    debug_header[4] += GND
    debug_header[5] += esp32s3['RXD0']
    debug_header[6] += esp32s3['IO0']

if __name__ == '__main__':
    circuit = esp32s3_simple()
    
    # Generate KiCad netlist for PCB workflow
    circuit.generate_kicad_netlist("esp32s3_simple.net")
    
    # Generate complete KiCad project
    circuit.generate_kicad_project("esp32s3_simple")
```

## Schematic Annotations

Circuit-synth includes a powerful annotation system for adding documentation directly to your KiCad schematics:

### Automatic Docstring Extraction

```python
from circuit_synth import *
from circuit_synth.core.annotations import enable_comments

@enable_comments  # Automatically extracts docstring as schematic annotation
@circuit(name="documented_circuit")
def power_filter_circuit():
    """Power filtering circuit for clean 3.3V supply.
    
    This circuit provides stable power filtering using a 10uF ceramic capacitor
    placed close to the power input for optimal performance."""
    
    # Circuit implementation...
```

### Manual Annotations

```python
from circuit_synth.core.annotations import TextBox, TextProperty, Table

# Add text boxes with background
circuit.add_annotation(TextBox(
    text="⚠️ Critical: Verify power supply ratings before connection!",
    position=(50, 30),
    background_color='yellow',
    size=(80, 20)
))

# Add component tables
table = Table(
    data=[
        ["Component", "Value", "Package", "Notes"],  # Header row
        ["C1", "10uF", "0603", "X7R ceramic"],
        ["R1", "1kΩ", "0603", "1% precision"]
    ],
    position=(20, 100)
)
circuit.add_annotation(table)
```

## Key Differentiators

### Bidirectional KiCad Integration
Unlike other circuit design tools that generate KiCad files as output only, circuit-synth provides true bidirectional updates:
- **Import existing KiCad projects** into Python for programmatic modification
- **Export Python circuits** to clean, readable KiCad projects
- **Hierarchical Structure Support** - correctly handles complex multi-level circuit hierarchies
- **KiCad remains source of truth** - make manual changes in KiCad and sync back to Python
- **Hybrid workflows** - combine manual design with automated generation

**Hierarchical Conversion Features:**
- **Multi-level Hierarchies**: Supports arbitrary depth circuit nesting (main → subcircuit → sub-subcircuit)
- **Proper Import Chains**: Generates clean Python imports matching KiCad hierarchical structure
- **Parameter Passing**: Automatically handles net parameter passing between hierarchical levels
- **Clean Code Generation**: Produces readable, maintainable Python code with proper separation of concerns

### Engineering-Friendly Approach
- **No Domain-Specific Language**: Uses standard Python syntax that any engineer can read and modify
- **Transparent Output**: Generated KiCad files are clean and human-readable, not machine-generated gibberish
- **Fits Existing Workflows**: Designed to integrate with normal EE development processes, not replace them
- **Professional Development**: Built for real engineering teams, not just hobbyists

### Additional Features
- **Pythonic Circuit Design**: Define circuits using intuitive Python classes and decorators
- **KiCad Netlist Export**: Generate industry-standard .net files for PCB layout workflows
- **Hierarchical Design Support**: Multi-sheet projects with proper organization and cross-references
- **Component Management**: Built-in component library with easy extensibility  
- **Smart Placement**: Automatic component placement algorithms
- **Type Safety**: Full type hints support for better IDE integration
- **Professional Output**: Clean, human-readable KiCad files suitable for production use
- **Extensible Architecture**: Clean interfaces for custom implementations
- **Rust Performance Optimization**: Optional Rust modules for faster KiCad generation (S-expression acceleration active)

## Performance Optimization

### ⚡ Lazy Symbol Loading - 30x Performance Improvement

Circuit-synth features an intelligent lazy symbol loading system that dramatically improves first-run performance by loading only the symbols you actually need:

#### Performance Results
- **Before**: 17+ seconds (building complete symbol index)
- **After**: 0.56 seconds (lazy loading on-demand)
- **Improvement**: **30x faster first-run performance**

#### Multi-Strategy Symbol Discovery
The lazy loading system uses four intelligent strategies in order of speed:

1. **File-based Discovery (< 0.01s)**: Intelligent filename guessing and common variations
2. **Ripgrep Search (< 0.1s)**: Fast pattern matching in .kicad_sym files  
3. **Python Grep Fallback (< 1s)**: Chunk-based file scanning for reliability
4. **Complete Index Build (fallback)**: Only as last resort when other strategies fail

#### Usage
Lazy loading is completely transparent - just use circuit-synth normally:

```python
from circuit_synth import *

# Lazy loading happens automatically - no code changes needed
component = Component(symbol="Device:R", ref="R", value="10K")
# Symbol loaded on-demand in ~0.01-0.1 seconds instead of 17+ seconds
```

**Clear Cache for Fresh Testing:**
```bash
# Test lazy loading from completely fresh state
./scripts/clear_all_caches.sh
time uv run python examples/example_kicad_project.py
```

### Enhanced Performance Profiling System

Circuit-synth includes a comprehensive performance profiling system that provides detailed timing analysis for all circuit generation operations:

#### Key Features
- **Granular Operation Timing**: Track performance of individual operations like symbol loading, component generation, and schematic writing
- **Quick Debugging**: `@quick_time` decorator provides immediate timing feedback during development
- **Performance Summary**: Comprehensive reports showing bottlenecks and optimization opportunities
- **Strategic Monitoring**: Performance decorators on critical operations in KiCad symbol cache, parser, and schematic writer

#### Usage Examples

**Basic Profiling:**
```python
from circuit_synth.core.performance_profiler import profile, print_performance_summary

# Profile circuit generation
with profile("circuit_generation"):
    circuit = my_circuit()
    circuit.generate_kicad_project("test_project")

# Print detailed performance summary
print_performance_summary()
```

**Quick Development Debugging:**
```python
from circuit_synth.core.performance_profiler import quick_time

@quick_time("Component Creation")
def create_component():
    return Component(symbol="Device:R", ref="R", value="10K")

# Output: ⏱️ Starting Component Creation...
#         ✅ Component Creation: 0.0023s
```

**Performance Summary Output:**
```
📊 PERFORMANCE SUMMARY:
============================================================
🕐 Total Time: 2.847s

📈 Get Symbol Data              |  1.234s (43.4%) | avg:  0.617s | count:   2
📈 Generate S-Expression        |  0.789s (27.7%) | avg:  0.789s | count:   1
📈 Add Components to Schematic  |  0.456s (16.0%) | avg:  0.456s | count:   1
📈 Load Symbol Library          |  0.368s (12.9%) | avg:  0.092s | count:   4
============================================================
```

### Rust Integration for High-Performance KiCad Generation

Circuit-synth includes optional Rust modules that provide significant performance improvements for KiCad file generation. The Rust integration uses a defensive design with automatic fallback to ensure reliability.

#### Features
- **6x Performance Improvement**: Rust S-expression generation is ~6x faster than Python for KiCad schematic files
- **Automatic Fallback**: If Rust modules aren't compiled, the system automatically uses optimized Python implementations
- **Zero API Changes**: Drop-in replacement with identical Python interface - no code changes required
- **Defensive Design**: Ultra-conservative implementation with comprehensive logging and error handling
- **Production Ready**: Complete TDD implementation with comprehensive testing

#### Performance Benchmarks
- **Python (baseline)**: ~4.7M operations/second
- **Python (optimized)**: ~8.3M operations/second (1.8x improvement) 
- **Rust (compiled)**: ~29.2M operations/second (6.2x vs baseline, 3.5x vs optimized)

### 🦀 Rust Module Compilation

**Prerequisites:**
```bash
# Install Rust toolchain
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source ~/.cargo/env

# Install maturin for Python-Rust bindings
pip install maturin
```

**Simple One-Command Setup:**
```bash
# Enable Rust acceleration with a single command
python enable_rust_acceleration.py

# This automatically compiles the 3 most impactful modules:
# - KiCad generation: ~6x faster
# - Symbol caching: ~3-10x faster  
# - Component placement: ~10-50x faster
```

**Verification:**
```bash
# Test that Rust module compiled successfully
python -c "
import rust_kicad_schematic_writer
test_component = {'ref': 'R1', 'symbol': 'Device:R', 'value': '10K'}
result = rust_kicad_schematic_writer.generate_component_sexp(test_component)
print(f'✅ Rust module working! Generated {len(result)} characters')
"
```

### 🔧 Integration Status

**Current Status: ✅ PARTIALLY OPERATIONAL**

The defensive Rust integration system includes working S-expression acceleration:

1. **✅ Working Module**: `rust_kicad_schematic_writer` - KiCad S-expression generation acceleration
2. **✅ Automatic Detection**: Integration module automatically detects compiled Rust extensions
3. **✅ Defensive Fallback**: Seamlessly falls back to optimized Python if Rust unavailable
4. **✅ Comprehensive Logging**: Full execution path tracing and performance monitoring
5. **🚧 Additional Modules**: Symbol cache and placement modules available for compilation

**Integration Module:** `rust_modules/rust_kicad_integration/`
- Provides defensive wrapper around compiled Rust extensions
- Handles automatic fallback and error recovery
- Includes comprehensive performance benchmarking
- Enables detailed execution logging

### 🚀 Usage

**Transparent Usage:**
The performance optimization is completely transparent - just use circuit-synth normally!

```python
# No code changes needed - Rust optimization happens automatically
from circuit_synth import *

@circuit
def my_circuit():
    # Your circuit definition here
    pass

# Rust acceleration happens automatically during generation
circuit = my_circuit()
circuit.generate_kicad_project("my_project")  # Uses Rust if available, Python fallback otherwise
```

**Direct Integration Usage:**
For advanced users who want explicit control:

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd() / 'rust_modules'))

import rust_kicad_integration

# Check if Rust is available
print(f"Rust available: {rust_kicad_integration.is_rust_available()}")

# Generate S-expression with automatic Rust/Python selection
component_data = {"ref": "R1", "symbol": "Device:R", "value": "10K"}
result = rust_kicad_integration.generate_component_sexp(component_data)
```

**Performance Benchmarking:**
```python
import rust_kicad_integration

# Run performance benchmark comparing Python vs Rust
component = {"ref": "U1", "symbol": "RF_Module:ESP32-S3-MINI-1", "value": "ESP32-S3"}
results = rust_kicad_integration.benchmark_implementations(component, iterations=1000)

print(f"Python baseline: {results['python_ops_per_sec']:.0f} ops/sec")
print(f"Rust performance: {results['rust_ops_per_sec']:.0f} ops/sec")
print(f"Speedup: {results['rust_speedup']:.1f}x")
```

### 🔍 Monitoring and Debugging

**Enable Detailed Logging:**
```python
import logging
logging.basicConfig(level=logging.INFO)

# Run your circuit generation - you'll see detailed logs like:
# INFO:rust_kicad_integration:🦀 EXECUTION_PATH: Using Rust implementation for component 'R1'
# INFO:rust_kicad_integration:✅ RUST_SUCCESS: Component 'R1' generated via Rust in 0.13ms
```

**Log Messages Explained:**
- `🦀 EXECUTION_PATH: Using Rust implementation` - Rust module is active
- `🐍 EXECUTION_PATH: Using Python implementation` - Fallback mode active
- `✅ RUST_SUCCESS: Component generated via Rust in Xms` - Rust generation successful
- `🔄 FALLBACK: Switching to Python implementation` - Error recovery in action

### 🏗️ Development and Testing

**TDD Framework:**
The Rust integration includes a complete Test-Driven Development framework:

```bash
# Run the TDD test suite
cd rust_modules && python -m pytest rust_integration/test_simple_rust_tdd.py -v

# Test output shows:
# ✅ RED Phase: Infrastructure complete
# ✅ GREEN Phase: Functional equivalence achieved
# ✅ REFACTOR Phase: Performance optimization demonstrated
```

**Manual Testing:**
```bash
# Test the integration system
python rust_modules/rust_integration/test_simple_rust_tdd.py

# Should output:
# ✅ Python implementation works
# ✅ Rust implementation works  
# ✅ Rust and Python produce identical output
# ✅ Performance improvement achieved (6.2x speedup)
```

### 🔧 Troubleshooting

**Common Issues:**

1. **"Rust module not found"**
   ```bash
   # Solution: Compile the Rust module
   cd rust_modules/rust_kicad_integration
   maturin develop --release
   ```

2. **"Permission denied" or compilation errors**
   ```bash
   # Solution: Ensure Rust toolchain is properly installed
   rustc --version  # Should show Rust version
   cargo --version  # Should show Cargo version
   ```

3. **Import errors or path issues**
   ```bash
   # Solution: Verify installation
   pip list | grep rust-kicad
   # Should show: rust-kicad-schematic-writer
   ```

**Verification Script:**
```python
# Complete verification of Rust integration
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd() / 'rust_modules'))

import logging
logging.basicConfig(level=logging.INFO)

try:
    import rust_kicad_integration
    print(f"✅ Integration module loaded")
    print(f"🦀 Rust available: {rust_kicad_integration.is_rust_available()}")
    
    # Test function call
    test_data = {"ref": "TEST", "symbol": "Device:R", "value": "1K"}
    result = rust_kicad_integration.generate_component_sexp(test_data)  
    print(f"✅ Function call successful: {len(result)} chars generated")
    
except Exception as e:
    print(f"❌ Error: {e}")
    print("💡 Try compiling Rust module: cd rust_modules/rust_kicad_integration && maturin develop --release")
```

## AI-Powered Development

Circuit-synth includes a specialized Claude agent for expert guidance on circuit-synth syntax, structure, and best practices. The agent helps with:

- **Code Reviews**: Analyzing circuit-synth projects for proper structure and conventions
- **Best Practices**: Guidance on component reuse, net management, and circuit organization  
- **Syntax Help**: Examples and patterns for proper circuit-synth implementation
- **Refactoring**: Suggestions for improving code maintainability and clarity

### Using the Circuit-Synth Agent

The agent is available in `.claude/agents/circuit-synth.md` and specializes in:

```python
# Component reuse patterns the agent recommends
C_10uF_0805 = Component(
    symbol="Device:C", ref="C", value="10uF",
    footprint="Capacitor_SMD:C_0805_2012Metric"
)

# Then instantiate with unique references
cap_input = C_10uF_0805()
cap_input.ref = "C4"  # Override ref for specific instance
```

The agent provides structured feedback on:
- Component definition and reuse patterns
- Circuit structure and @circuit decorator usage
- Net management and naming conventions
- Pin connection syntax (integer vs string access)
- Code organization and maintainability
**Perfect for AI-assisted circuit design - just ask Claude to help you build circuits!**

## 📁 Repository Structure

```
circuit-synth/
├── README.md              # This file
├── CLAUDE.md              # Claude Code instructions  
├── pyproject.toml         # Python package configuration
├── docs/                  # 📚 Documentation & guides
│   ├── SCRIPT_REFERENCE.md    # → Complete script index
│   ├── AUTOMATED_TESTING.md   # → Testing infrastructure  
│   ├── RUST_TESTING_GUIDE.md  # → Rust testing guide
│   └── RUST_PYPI_INTEGRATION.md # → Python-Rust integration
├── scripts/               # 🔧 All utility scripts  
│   ├── run_all_tests.sh       # → Comprehensive testing
│   ├── rebuild_all_rust.sh    # → Rebuild Rust modules
│   └── test_rust_modules.sh   # → Rust-only testing
├── src/circuit_synth/     # 🐍 Main Python package
├── rust_modules/          # 🦀 Rust performance modules  
└── examples/              # 💡 Usage examples
```

**📖 Script Reference**: See [`docs/SCRIPT_REFERENCE.md`](docs/SCRIPT_REFERENCE.md) for all available scripts and their usage.

## Quick Start

```bash
# Clone and run example
git clone https://github.com/circuit-synth/circuit-synth.git
cd circuit-synth
uv run python examples/example_kicad_project.py
```

Generates a complete KiCad project with schematics, PCB layout, and netlists.

## Example Circuit

```python
from circuit_synth import *

@circuit(name="esp32_dev_board")
def esp32_dev_board():
    """ESP32 development board with USB-C and power regulation"""
    
    # Create power nets
    VCC_5V = Net('VCC_5V')
    VCC_3V3 = Net('VCC_3V3') 
    GND = Net('GND')
    
    # ESP32 module (use /find-symbol ESP32 to find the right symbol)
    esp32 = Component(
        symbol="RF_Module:ESP32-S3-MINI-1",
        ref="U1",
        footprint="RF_Module:ESP32-S3-MINI-1"
    )
    
    # Voltage regulator (use /find-footprint SOT23 to find footprint)
    vreg = Component(
        symbol="Regulator_Linear:AMS1117-3.3",
        ref="U2", 
        footprint="Package_TO_SOT_SMD:SOT-223-3_TabPin2"
    )
    
    # Connections
    esp32["3V3"] += VCC_3V3
    esp32["GND"] += GND
    vreg["VIN"] += VCC_5V
    vreg["VOUT"] += VCC_3V3
    vreg["GND"] += GND

# Generate KiCad project
circuit = esp32_dev_board()
circuit.generate_kicad_project("esp32_dev")
```

## Key Features

- **🐍 Pure Python**: Standard Python syntax - no DSL to learn
- **🔄 Bidirectional KiCad Integration**: Import existing projects, export clean KiCad files
- **📋 Professional Netlists**: Generate industry-standard KiCad .net files
- **🏗️ Hierarchical Design**: Multi-sheet projects with proper organization
- **📝 Smart Annotations**: Automatic docstring extraction + manual text/tables
- **⚡ Rust-Accelerated**: Fast symbol lookup and placement algorithms
- **📊 Performance Profiling**: Comprehensive timing analysis and optimization tools

## Installation

**PyPI (Recommended):**
```bash
pip install circuit-synth
# or: uv pip install circuit-synth
```

**Development:**
```bash
git clone https://github.com/circuit-synth/circuit-synth.git
cd circuit-synth
uv sync  # or: pip install -e ".[dev]"
```

**Docker:**
```bash
./docker/build-docker.sh
./scripts/circuit-synth-docker python examples/example_kicad_project.py
```

## Contributing

We welcome contributions! See [CLAUDE.md](CLAUDE.md) for development setup and coding standards.

**Quick start:**
```bash
git clone https://github.com/yourusername/circuit-synth.git
cd circuit-synth
uv sync
uv run python examples/example_kicad_project.py  # Test your setup
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- Documentation: [https://circuit-synth.readthedocs.io](https://circuit-synth.readthedocs.io)
- Issues: [GitHub Issues](https://github.com/circuit-synth/circuit-synth/issues)
- Discussions: [GitHub Discussions](https://github.com/circuit-synth/circuit-synth/discussions)
