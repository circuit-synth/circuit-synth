# circuit-synth

[![Documentation](https://readthedocs.org/projects/circuit-synth/badge/?version=latest)](https://circuit-synth.readthedocs.io/en/latest/?badge=latest)
[![PyPI version](https://badge.fury.io/py/circuit-synth.svg)](https://badge.fury.io/py/circuit-synth)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Pythonic circuit design for professional KiCad projects

## Overview

Circuit Synth is an open-source Python library that fits seamlessly into normal EE workflows without getting too fancy. Unlike domain-specific languages that require learning new syntax, circuit-synth uses simple, transparent Python code that any engineer can understand and modify.

**Core Principles:**
- **Simple Python Code**: No special DSL to learn - just Python classes and functions
- **Transparent to Users**: Generated KiCad files are clean and human-readable
- **Bidirectional Updates**: KiCad can remain the source of truth - import existing projects and export changes back
- **Normal EE Workflow**: Integrates with existing KiCad-based development processes

**Current Status**: Circuit-synth is ready for professional use with the following capabilities:
- **Full KiCad Integration**: Generate complete KiCad projects with schematics and PCB layouts
- **Schematic Annotations**: Automatic docstring extraction and manual text annotations with tables
- **Netlist Generation**: Export industry-standard KiCad netlist files (.net) for seamless PCB workflow
- **Hierarchical Design Support**: Multi-sheet projects with proper organization and connectivity
- **Professional Component Management**: Complete footprint, symbol, and library integration
- Places components functionally (not yet optimized for intelligent board layout)
- Places schematic parts (without intelligent placement algorithms)
- Generates working KiCad projects suitable for professional development

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

**Compilation Process:**
```bash
# Navigate to the Rust module directory  
cd rust_modules/rust_kicad_integration

# Build and install the Rust extension (development mode)
maturin develop --release

# Or for production installation
maturin build --release
pip install target/wheels/*.whl
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

## Quick Start

Try circuit-synth immediately without installation:

```bash
# Clone the repository
git clone https://github.com/circuit-synth/circuit-synth.git
cd circuit-synth

# Run the example (automatically installs dependencies with uv)
uv run python examples/example_kicad_project.py
```

This will generate a complete KiCad project in the `example_kicad_project/` directory, including:
- Hierarchical schematic files (.kicad_sch)
- PCB layout file (.kicad_pcb) 
- KiCad netlist file (.net)
- JSON netlist file (.json)

## KiCad Netlist Generation

Circuit-synth provides industry-standard KiCad netlist generation for seamless PCB layout workflows:

### Basic Netlist Export
```python
from circuit_synth import *

@circuit
def my_circuit():
    # Define your circuit...
    pass

if __name__ == '__main__':
    circuit = my_circuit()
    
    # Generate KiCad netlist (.net file)
    circuit.generate_kicad_netlist("my_circuit.net")
    
    # Generate JSON netlist for analysis
    circuit.generate_json_netlist("my_circuit.json")
```

### Features
- **Industry Standard Format**: Generates KiCad-compatible .net files
- **Hierarchical Design Support**: Multi-sheet projects with proper organization  
- **Complete Component Data**: Includes footprints, values, datasheets, and library references
- **Perfect KiCad Import**: Zero warnings, zero errors when importing into KiCad
- **Scalable**: Works with simple 3-component circuits to complex 20+ component systems

### Verification
All generated netlists are validated through KiCad import:
```
Reading netlist file 'my_circuit.net'. 
Using reference designators to match symbols and footprints.
Processing symbol 'U1:RF_Module:ESP32-S2-MINI-1'.
...
Total warnings: 0, errors: 0.
```

### Integration with PCB Workflow
1. **Design in Python**: Define circuits using circuit-synth syntax
2. **Generate Netlist**: Export to KiCad-compatible .net format
3. **Import to KiCad**: Load netlist directly into KiCad PCB editor
4. **Layout PCB**: Use KiCad's routing and placement tools
5. **Manufacturing**: Generate Gerber files and assembly drawings

## Installation

### Using PyPI (Recommended)

```bash
# Install from PyPI
pip install circuit-synth

# Or using uv (faster)
uv pip install circuit-synth
```

### Development Installation

For development work:

```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Clone and install
git clone https://github.com/circuit-synth/circuit-synth.git
cd circuit-synth
pip install -e ".[dev]"
```

### Development Setup

For development work:

```bash
# Clone the repository
git clone https://github.com/circuit-synth/circuit-synth.git
cd circuit-synth

# Install with development dependencies using uv
uv sync

# Or with pip
pip install -e ".[dev]"
```

### Using Docker

Circuit-synth can be run in Docker containers with full KiCad library support:

```bash
# Build the Docker image
./docker/build-docker.sh

# Run any circuit-synth command in Docker
./scripts/circuit-synth-docker python examples/example_kicad_project.py

# Run with interactive shell
./scripts/circuit-synth-docker --interactive bash

# Run without KiCad libraries (faster startup)
./scripts/circuit-synth-docker --no-libs python -c "import circuit_synth; print('Ready!')"
```

**Docker Features:**
- Pre-configured environment with all dependencies
- Official KiCad symbol and footprint libraries included
- Automatic file persistence to local `output/` directory
- Security through non-root user execution
- Two Dockerfile options: simplified Python-only (main) and full Rust build (`docker/Dockerfile.rust-build`)

**Docker Commands:**
```bash
# Universal command runner
./scripts/circuit-synth-docker <any-python-command>

# KiCad library-specific runner
./scripts/run-with-kicad.sh --official-libs

# Docker Compose services (from docker/ directory)
cd docker && docker-compose up circuit-synth        # Basic service
cd docker && docker-compose up circuit-synth-dev    # Development mode
cd docker && docker-compose up circuit-synth-test   # Test runner
```

**Docker Build Options:**
```bash
# Quick Python-only build (recommended)
./docker/build-docker.sh

# Full build with Rust modules (advanced users)
docker build -f docker/Dockerfile.rust-build -t circuit-synth-rust .

# Windows users
./docker/build-docker.bat
```

#### Docker Attribution

The Docker implementation is a collaborative effort:
- **Original implementation**: Kumuda Subramanyam Govardhanam (@KumudaSG) - comprehensive Rust module compilation support
- **Enhancements**: KiCad library integration, simplified Python-only build, universal command runners, and build automation

## Documentation

Full documentation is available at [https://circuit-synth.readthedocs.io](https://circuit-synth.readthedocs.io)

## Contributing

We welcome contributions! Here's how to get started:

### Development Setup

**Prerequisites:**
- Python 3.9 or higher
- [uv](https://docs.astral.sh/uv/) (recommended package manager)
- Git

**Getting Started:**

1. **Fork and clone the repository:**
   ```bash
   git clone https://github.com/yourusername/circuit-synth.git
   cd circuit-synth
   ```

2. **Install dependencies (recommended with uv):**
   ```bash
   # Install the project in development mode
   uv pip install -e ".[dev]"
   
   # Install dependencies
   uv sync
   ```

3. **Alternative installation with pip:**
   ```bash
   # Create and activate virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   
   # Install in development mode
   pip install -e ".[dev]"
   ```

**Development Guidelines:**
- Follow existing code style and patterns
- Write tests for new functionality
- Update documentation as needed
- Test your changes with `uv run python examples/example_kicad_project.py`
- Use the Docker environment for testing: `./scripts/circuit-synth-docker python examples/example_kicad_project.py`

## Manual Testing Checklist

**Run these manual tests on every major change to ensure system integrity:**

### 1. Core Example Script Testing

**Local Environment:**
```bash
# Run the primary example script locally
uv run python examples/example_kicad_project.py

# Verify generated files exist
ls -la example_kicad_project/
```

**Docker Environment:**
```bash
# Test the same script in Docker environment
./scripts/circuit-synth-docker python examples/example_kicad_project.py

# Verify files are generated in Docker context
./scripts/circuit-synth-docker ls -la example_kicad_project/
```

**Verification Steps:**
- ✅ Script completes without errors
- ✅ Generates complete KiCad project directory
- ✅ Creates `.kicad_sch`, `.kicad_pcb`, `.kicad_pro`, and `.net` files
- ✅ Annotation system debug output appears (docstring extraction)

### 2. KiCad Project Inspection

**Open Generated Project in KiCad:**
```bash
# Open the generated project
kicad example_kicad_project/example_kicad_project.kicad_pro
```

**Schematic Verification:**
- ✅ All components are placed and visible
- ✅ Net connections are correct (no unconnected pins)
- ✅ Hierarchical structure is properly organized
- ✅ Annotations appear as text boxes with docstring content
- ✅ Component references are sequential and logical (R1, R2, C1, C2, etc.)
- ✅ Net names are clean and descriptive (5V, 3V3, GND, USB_DM, etc.)

**PCB Layout Verification:**
- ✅ All components are placed on PCB (not overlapping)
- ✅ All nets have proper connectivity (ratsnest shows connections)
- ✅ Footprints are correct and match schematic symbols
- ✅ Bounding boxes are drawn around components (if `draw_bounding_boxes=True`)

### 3. Docker Command Testing

**Basic Docker Commands:**
```bash
# Test help command
./scripts/circuit-synth-docker --help

# Test version information
./scripts/circuit-synth-docker python -c "import circuit_synth; print(circuit_synth.__version__)"

# Test package installation status
./scripts/circuit-synth-docker pip list | grep circuit-synth
```

**File System Operations:**
```bash
# Test file creation and access
./scripts/circuit-synth-docker touch test_file.txt
./scripts/circuit-synth-docker ls -la test_file.txt
./scripts/circuit-synth-docker rm test_file.txt
```

### 4. Regression Test Suite

**Automated Test Execution:**
```bash
# Run unit tests
uv run pytest tests/unit/test_core_circuit.py -v

# Run functional tests
cd tests/functional_tests/test_01_resistor_divider && uv run python test_netlist_comparison.py
cd tests/functional_tests/test_02_import_resistor_divider && uv run python test_kicad_import.py  
cd tests/functional_tests/test_03_round_trip_python_kicad_python && uv run python test_round_trip.py
cd tests/functional_tests/test_04_nested_kicad_sch_import && uv run python test_complex_hierarchical_structure.py

# Run integration tests
uv run pytest tests/kicad_netlist_exporter/test_sheet_hierarchy.py -v
uv run pytest tests/kicad_netlist_exporter/test_netlist_exporter_basics.py -v
```

**Success Criteria:**
- ✅ All unit tests pass (18/18)
- ✅ All functional tests complete successfully
- ✅ Integration tests pass without errors
- ✅ No regression in existing functionality

### 5. System Integration Verification

**Web Dashboard (if available):**
```bash
# Test dashboard startup
uv run circuit-synth-web
# Verify: Dashboard starts without critical errors
```

**LLM Analysis Pipeline:**
```bash
# Test analysis system availability
uv run python -m circuit_synth.intelligence.scripts.llm_circuit_analysis --help
# Verify: Help output appears, no import errors
```

### 6. Advanced Validation

**Hierarchical Structure Testing:**
- ✅ Test complex hierarchical projects (3+ levels deep)
- ✅ Verify proper nested import chains in generated Python
- ✅ Confirm parameter passing through hierarchy levels
- ✅ Check that KiCad→Python→KiCad round-trip preserves structure

**Bidirectional Sync Testing:**
- ✅ Import existing KiCad project to Python
- ✅ Modify Python code and regenerate KiCad
- ✅ Verify changes appear correctly in KiCad
- ✅ Test that manual KiCad changes can be preserved

**Component and Net Validation:**
- ✅ Test various component types (resistors, capacitors, ICs, connectors)
- ✅ Verify footprint assignments are correct
- ✅ Check net naming conventions and cleanup
- ✅ Test pin mapping for complex components (ESP32, connectors)

### 7. Performance and Resource Testing

**Resource Usage:**
```bash
# Monitor memory usage during generation
time uv run python examples/example_kicad_project.py

# Check generated file sizes are reasonable
du -h example_kicad_project/
```

**Docker Performance:**
```bash
# Test Docker startup time
time ./scripts/circuit-synth-docker echo "Docker ready"

# Compare Docker vs local execution time  
time ./scripts/circuit-synth-docker python examples/example_kicad_project.py
```

### 8. Error Handling and Edge Cases

**Error Condition Testing:**
- ✅ Test with invalid component references
- ✅ Test with missing footprints or symbols
- ✅ Test with circular hierarchical dependencies
- ✅ Verify graceful error messages and recovery

**Edge Case Validation:**
- ✅ Test empty circuits
- ✅ Test very large circuits (100+ components)
- ✅ Test circuits with no nets
- ✅ Test circuits with only power nets

## Manual Testing Frequency

**Before Each Commit:**
- Run core example script (local + Docker)
- Execute unit tests
- Verify no regressions in key functionality

**Before Each Release:**
- Complete full manual testing checklist
- Perform KiCad project inspection
- Run entire regression test suite
- Test Docker commands and environment
- Validate hierarchical and bidirectional features

**After Major Refactoring:**
- Execute complete testing checklist
- Additional focus on changed subsystems
- Performance regression testing
- Cross-platform validation (if applicable)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- Documentation: [https://circuit-synth.readthedocs.io](https://circuit-synth.readthedocs.io)
- Issues: [GitHub Issues](https://github.com/circuit-synth/circuit-synth/issues)
- Discussions: [GitHub Discussions](https://github.com/circuit-synth/circuit-synth/discussions)
