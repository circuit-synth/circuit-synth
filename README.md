# circuit-synth

**Python-based circuit design with KiCad integration and AI acceleration.**

Generate professional KiCad projects from Python code with hierarchical design, version control, and automated documentation.

## 🚀 First Time User? Start Here!

**Complete working example in 3 minutes:**

```bash
# 1. Install circuit-synth
pip install circuit-synth

# 2. Create a new project with working example
uv run cs-new-project my_first_board

# 3. Generate KiCad files from the example
cd my_first_board/circuit-synth
uv run python example_project/circuit-synth/main.py

# 4. Open in KiCad (generated in ESP32_C6_Dev_Board/)
open ESP32_C6_Dev_Board/ESP32_C6_Dev_Board.kicad_pro
```

**That's it!** You now have a complete ESP32-C6 development board schematic and PCB.

**What you just created:**
- ✅ ESP32-C6 microcontroller with proper power connections
- ✅ USB-C connector with CC resistors
- ✅ 3.3V voltage regulator
- ✅ LED with current-limiting resistor
- ✅ Complete KiCad project ready to edit/manufacture

**Next steps:**
- Modify `example_project/circuit-synth/main.py` to customize your circuit
- Re-run `uv run python example_project/circuit-synth/main.py` to regenerate KiCad files
- Open KiCad to view/edit your schematic and PCB layout

## Installation

```bash
# Install with uv (recommended)
uv add circuit-synth

# Or with pip
pip install circuit-synth
```

## Configuration

### Logging Control

By default, circuit-synth runs with minimal logging output (WARNING level). To enable detailed logs for debugging:

```bash
# Enable verbose logging via environment variable
export CIRCUIT_SYNTH_LOG_LEVEL=INFO

# Or set it in your Python script
import os
os.environ['CIRCUIT_SYNTH_LOG_LEVEL'] = 'INFO'
```

Available log levels:
- `ERROR`: Only show errors
- `WARNING`: Show warnings and errors (default)
- `INFO`: Show informational messages, progress updates
- `DEBUG`: Show detailed debugging information

## Quick Start

```bash
# Create new project with example circuit
uv run cs-new-project

# This generates a complete ESP32-C6 development board
cd circuit-synth && uv run python example_project/circuit-synth/main.py
```

## Example: Power Supply Circuit

```python
from circuit_synth import *

@circuit(name="Power_Supply")
def power_supply(vbus_in, vcc_3v3_out, gnd):
    """5V to 3.3V power regulation subcircuit"""
    
    # Components with KiCad integration
    regulator = Component(
        symbol="Regulator_Linear:AMS1117-3.3", 
        ref="U",
        footprint="Package_TO_SOT_SMD:SOT-223-3_TabPin2"
    )
    
    # Input/output capacitors
    cap_in = Component(symbol="Device:C", ref="C", value="10uF",
                      footprint="Capacitor_SMD:C_0805_2012Metric")
    cap_out = Component(symbol="Device:C", ref="C", value="22uF",
                       footprint="Capacitor_SMD:C_0805_2012Metric")
    
    # Explicit connections
    regulator["VI"] += vbus_in    # Input pin
    regulator["VO"] += vcc_3v3_out # Output pin
    regulator["GND"] += gnd
    
    cap_in[1] += vbus_in
    cap_in[2] += gnd
    cap_out[1] += vcc_3v3_out
    cap_out[2] += gnd

@circuit(name="Main_Circuit")
def main_circuit():
    """Complete circuit with hierarchical design"""
    
    # Create shared nets
    vbus = Net('VBUS')
    vcc_3v3 = Net('VCC_3V3')
    gnd = Net('GND')
    
    # Use the power supply subcircuit
    power_circuit = power_supply(vbus, vcc_3v3, gnd)

# Generate KiCad project
if __name__ == "__main__":
    circuit = main_circuit()
    circuit.generate_kicad_project("my_board")
```

## Core Features

- **Professional KiCad Output**: Generate .kicad_pro, .kicad_sch, .kicad_pcb files with modern kicad-sch-api integration
- **Hierarchical Design**: Modular subcircuits like software modules  
- **Atomic KiCad Operations**: Add/remove individual components from existing schematics with rollback safety
- **Modern KiCad Integration**: Uses PyPI kicad-sch-api (v0.1.1+) for professional schematic generation
- **Component Intelligence**: JLCPCB & DigiKey integration, symbol/footprint verification
- **Fast JLCPCB Search**: Direct search with 80% speed improvement, 90% less tokens
- **AI Integration**: Claude Code agents for automated design assistance
- **Circuit Debugging**: AI-powered PCB troubleshooting with systematic fault-finding
- **FMEA Analysis**: Comprehensive reliability analysis with physics-based failure models
- **Test Generation**: Automated test plans for validation
- **Version Control**: Git-friendly text-based circuit definitions

## KiCad-sch-api Integration

Circuit-synth integrates with the modern **kicad-sch-api** PyPI package - a valuable standalone tool that was extracted from circuit-synth for broader community use.

### Benefits of kicad-sch-api
- **Professional KiCad Files**: Generates industry-standard .kicad_sch files with proper formatting
- **Symbol Library Integration**: Full access to KiCad's extensive symbol libraries  
- **Hierarchical Support**: Clean handling of complex multi-sheet designs
- **Version Compatibility**: Works with modern KiCad versions (v7.0+)

### Hybrid Architecture
Circuit-synth uses a hybrid approach combining the best of both worlds:
- **Legacy System**: Handles component positioning and hierarchical structure
- **Modern API**: Professional schematic file writing via kicad-sch-api
- **Intelligent Selection**: Automatically chooses the right approach per schematic type

```python
# The modern API integration is automatic - just use circuit-synth as normal!
@circuit(name="MyCircuit")
def my_design():
    # Your circuit design here
    pass

# Behind the scenes: circuit-synth + kicad-sch-api = professional results
```

### Standalone kicad-sch-api Usage
The kicad-sch-api package is also valuable as a standalone tool for Python KiCad integration:

```bash
pip install kicad-sch-api
```

Visit the [kicad-sch-api repository](https://github.com/circuit-synth/kicad-sch-api) for standalone usage examples.

## AI-Powered Design

### Claude Code Commands

```bash
# Component search
/find-symbol STM32                    # Search KiCad symbols
/find-footprint LQFP64                # Find footprints
/find-parts "STM32F407" --source jlcpcb   # Check JLCPCB availability
/find-stm32 "3 SPIs, USB"             # STM32-specific search

# Circuit generation
/generate-validated-circuit "ESP32 IoT sensor" mcu

# Fast JLCPCB CLI (no agents, 80% faster)
jlc-fast search STM32G4               # Direct search
jlc-fast cheapest "10uF 0805"         # Find cheapest option
```

### 🤖 AI Assistance

When using Claude Code, you can ask for help with:

- **Component Selection**: "Find me a 3.3V regulator available on JLCPCB"
- **Circuit Design**: "Design a USB-C power supply with protection"
- **KiCad Integration**: "What footprint should I use for LQFP-48?"
- **Troubleshooting**: "My board isn't powering on - help debug"
- **SPICE Simulation**: "Simulate this amplifier circuit"
- **Test Planning**: "Generate test procedures for my power supply"

The AI agents will automatically select the right tools and expertise for your request.

## 🚀 Commands

### Project Creation
```bash
cs-new-project              # Complete project setup with ESP32-C6 example
```

### Circuit Generation
```bash
cd circuit-synth && uv run python example_project/circuit-synth/main.py    # Generate KiCad files from Python code
```

### Available Commands

```bash
# Component Search
/find-symbol STM32              # Search KiCad symbols
/find-footprint LQFP64          # Find footprints
/find-parts "STM32F407" --source jlcpcb   # Check availability
/find-stm32 "3 SPIs, USB"       # STM32-specific search

# Circuit Generation
/generate-validated-circuit "ESP32 IoT sensor" mcu
/validate-existing-circuit      # Validate circuit code

# Fast JLCPCB CLI
jlc-fast search STM32G4         # Direct search
jlc-fast cheapest "10uF 0805"   # Find cheapest option

# FMEA Analysis
/analyze-fmea my_circuit.py     # Run reliability analysis
```

## ⚡ Atomic KiCad Operations

Circuit-synth provides atomic operations for surgical modifications to existing KiCad schematics, enabling incremental updates without regenerating entire projects:

### Production API

```python
from circuit_synth.kicad.atomic_integration import AtomicKiCadIntegration, migrate_circuit_to_atomic

# Initialize atomic integration for a KiCad project
atomic = AtomicKiCadIntegration("/path/to/project")

# Add components using atomic operations
atomic.add_component_atomic("main", {
    'symbol': 'Device:R',
    'ref': 'R1',
    'value': '10k',
    'footprint': 'Resistor_SMD:R_0603_1608Metric',
    'position': (100, 80)
})

# Remove components
atomic.remove_component_atomic("main", "R1")

# Fix hierarchical main schematics with sheet references
subcircuits = [
    {"name": "USB_Port", "filename": "USB_Port.kicad_sch", "position": (35, 35), "size": (43, 25)},
    {"name": "Power_Supply", "filename": "Power_Supply.kicad_sch", "position": (95, 35), "size": (44, 20)}
]
atomic.fix_hierarchical_main_schematic(subcircuits)

# Migrate JSON netlist to KiCad using atomic operations
migrate_circuit_to_atomic("circuit.json", "output_project/")
```

### Key Benefits

- **True Atomic Operations**: Add/remove individual components with rollback safety
- **Hierarchical Sheet Management**: Fixes blank main schematics automatically
- **Production Integration**: Seamless integration with existing circuit-synth pipeline  
- **S-Expression Safety**: Proper parsing with backup/restore on failure
- **JSON Pipeline Integration**: Full compatibility with circuit-synth JSON format

### Use Cases

- **Incremental Updates**: Add components to existing designs without full regeneration
- **Debug and Fix**: Resolve blank schematic issues (like ESP32-C6 project)
- **External Integration**: Third-party tools can manipulate circuit-synth schematics
- **Advanced Workflows**: Power users building custom automation

## FMEA and Quality Assurance

Circuit-synth includes comprehensive failure analysis capabilities to ensure your designs are reliable:

### Automated FMEA Analysis

```python
from circuit_synth.quality_assurance import EnhancedFMEAAnalyzer
from circuit_synth.quality_assurance import ComprehensiveFMEAReportGenerator

# Analyze your circuit for failures
analyzer = EnhancedFMEAAnalyzer()
circuit_context = {
    'environment': 'industrial',    # Set operating environment
    'safety_critical': True,        # Affects severity ratings
    'production_volume': 'high'     # Influences detection ratings
}

# Generate comprehensive PDF report (50+ pages)
generator = ComprehensiveFMEAReportGenerator("My Project")
report_path = generator.generate_comprehensive_report(
    analysis_results,
    output_path="FMEA_Report.pdf"
)
```

### What Gets Analyzed

- **300+ Failure Modes**: Component failures, solder joints, environmental stress
- **Physics-Based Models**: Arrhenius, Coffin-Manson, Black's equation
- **IPC Class 3 Compliance**: High-reliability assembly standards
- **Risk Assessment**: RPN (Risk Priority Number) calculations
- **Mitigation Strategies**: Specific recommendations for each failure mode

### Command Line FMEA

```bash
# Quick FMEA analysis
uv run python -m circuit_synth.tools.quality_assurance.fmea_cli my_circuit.py

# Specify output file
uv run python -m circuit_synth.tools.quality_assurance.fmea_cli my_circuit.py -o FMEA_Report.pdf

# Analyze with custom threshold
uv run python -m circuit_synth.tools.quality_assurance.fmea_cli my_circuit.py --threshold 150
```

See [FMEA Guide](docs/FMEA_GUIDE.md) for detailed documentation.

## Library Sourcing System

Hybrid component discovery across multiple sources with automatic fallback:

### Setup
```bash
cs-library-setup                    # Show configuration status
cs-setup-snapeda-api YOUR_KEY       # Optional: SnapEDA API access  
cs-setup-digikey-api KEY CLIENT_ID  # Optional: DigiKey API access
```

### Usage
Enhanced `/find-symbol` and `/find-footprint` commands automatically search:
1. **Local KiCad** (user installation)
2. **DigiKey GitHub** (150 curated libraries, auto-converted)
3. **SnapEDA API** (millions of components)
4. **DigiKey API** (supplier validation)

Results show source tags: `[Local]`, `[DigiKey GitHub]`, `[SnapEDA]`, `[DigiKey API]`

## Fast JLCPCB Component Search

The optimized search API provides direct JLCPCB component lookup without agent overhead:

### Python API

```python
from circuit_synth.manufacturing.jlcpcb import fast_jlc_search, find_cheapest_jlc

# Fast search with filtering
results = fast_jlc_search("STM32G4", min_stock=100, max_results=5)
for r in results:
    print(f"{r.part_number}: {r.description} (${r.price}, stock: {r.stock})")

# Find cheapest option
cheapest = find_cheapest_jlc("0.1uF 0603", min_stock=1000)
print(f"Cheapest: {cheapest.part_number} at ${cheapest.price}")
```

### CLI Usage

```bash
# Search components
jlc-fast search "USB-C connector" --min-stock 500

# Find cheapest with stock
jlc-fast cheapest "10k resistor" --min-stock 10000

# Performance benchmark
jlc-fast benchmark
```

### Performance Improvements

- **80% faster**: ~0.5s vs ~30s with agent-based search
- **90% less tokens**: 0 LLM tokens vs ~500 per search
- **Intelligent caching**: Avoid repeated API calls
- **Batch operations**: Search multiple components efficiently

## Project Structure

```
my_circuit_project/
├── example_project/
│   ├── circuit-synth/
│   │   ├── main.py              # ESP32-C6 dev board (hierarchical)
│   │   ├── power_supply.py      # 5V→3.3V regulation
│   │   ├── usb.py               # USB-C with CC resistors
│   │   ├── esp32c6.py           # ESP32-C6 microcontroller
│   │   └── led_blinker.py       # Status LED control
│   └── ESP32_C6_Dev_Board/      # Generated KiCad files
│       ├── ESP32_C6_Dev_Board.kicad_pro
│       ├── ESP32_C6_Dev_Board.kicad_sch
│       ├── ESP32_C6_Dev_Board.kicad_pcb
│       └── ESP32_C6_Dev_Board.net
├── README.md                # Project guide
├── CLAUDE.md                # AI assistant instructions
└── pyproject.toml           # Project dependencies
```


## Why Circuit-Synth?

| Traditional EE Workflow | With Circuit-Synth |
|-------------------------|-------------------|
| Manual component placement | `python example_project/circuit-synth/main.py` → Complete project |
| Hunt through symbol libraries | Verified components with JLCPCB & DigiKey availability |
| Visual net verification | Explicit Python connections |
| GUI-based editing | Version-controlled Python files |
| Copy-paste patterns | Reusable circuit functions |
| Manual FMEA documentation | Automated 50+ page reliability analysis |

## Resources

- [Documentation](https://docs.circuit-synth.com)
- [Examples](https://github.com/circuit-synth/examples)
- [Contributing](CONTRIBUTING.md)

## Development Setup

```bash
# Clone and install
git clone https://github.com/circuit-synth/circuit-synth.git
cd circuit-synth
uv sync

# Run tests
uv run pytest

# Optional: Register Claude Code agents
uv run register-agents
```


For 6x performance improvement:

```bash

# Build modules

# Test integration
```

## Testing

```bash
# Run comprehensive tests
./tools/testing/run_full_regression_tests.py

# Python tests only
uv run pytest --cov=circuit_synth

# Pre-release regression test
./tools/testing/run_full_regression_tests.py

# Code quality
black src/ && isort src/ && flake8 src/ && mypy src/
```

## KiCad Requirements

KiCad 8.0+ required:

```bash
# macOS
brew install kicad

# Linux
sudo apt install kicad

# Windows
# Download from kicad.org
```

## Troubleshooting

Install the AI-powered KiCad plugin for direct Claude Code integration:

```bash
# Install KiCad plugins
uv run cs-setup-kicad-plugins
```

**Usage:**
- **PCB Editor**: Tools → External Plugins → "Circuit-Synth AI"  
- **Schematic Editor**: Tools → Generate BOM → "Circuit-Synth AI"

## 🛠️ Advanced Configuration

### Environment Variables

```bash
# Optional performance settings
export CIRCUIT_SYNTH_PARALLEL_PROCESSING=true

# KiCad path override (if needed)
export KICAD_SYMBOL_DIR="/custom/path/to/symbols"
export KICAD_FOOTPRINT_DIR="/custom/path/to/footprints"
```

### Component Database Configuration

```bash
# JLCPCB API configuration (optional)
export JLCPCB_API_KEY="your_api_key"
export JLCPCB_CACHE_DURATION=3600  # Cache for 1 hour

# DigiKey API configuration (optional, for component search)
export DIGIKEY_CLIENT_ID="your_client_id"
export DIGIKEY_CLIENT_SECRET="your_client_secret"
# Or run: python -m circuit_synth.manufacturing.digikey.config_manager
```

## 🔍 Component Sourcing

circuit-synth provides integrated access to multiple component distributors for real-time availability, pricing, and specifications.

### Unified Multi-Source Search (Recommended)
Search across all suppliers with one interface:
```python
from circuit_synth.manufacturing import find_parts

# Search all suppliers
results = find_parts("0.1uF 0603 X7R", sources="all")

# Search specific supplier
jlc_results = find_parts("STM32F407", sources="jlcpcb")
dk_results = find_parts("LM358", sources="digikey")

# Compare across suppliers
comparison = find_parts("3.3V regulator", sources="all", compare=True)
print(comparison)  # Shows price/availability comparison table

# Filter by requirements
high_stock = find_parts("10k resistor", min_stock=10000, max_price=0.10)
```

### JLCPCB Integration
Best for PCB assembly and production:
```python
from circuit_synth.manufacturing.jlcpcb import search_jlc_components_web

# Find components available for assembly
results = search_jlc_components_web("STM32F407", max_results=10)
```

### DigiKey Integration  
Best for prototyping and wide selection:
```python
from circuit_synth.manufacturing.digikey import search_digikey_components

# Search DigiKey's 8M+ component catalog
results = search_digikey_components("0.1uF 0603 X7R", max_results=10)

# Get detailed pricing and alternatives
from circuit_synth.manufacturing.digikey import DigiKeyComponentSearch
searcher = DigiKeyComponentSearch()
component = searcher.get_component_details("399-1096-1-ND")
alternatives = searcher.find_alternatives(component, max_results=5)
```

### DigiKey Setup
```bash
# Interactive configuration
python -m circuit_synth.manufacturing.digikey.config_manager

# Test connection
python -m circuit_synth.manufacturing.digikey.test_connection
```

See [docs/DIGIKEY_SETUP.md](docs/DIGIKEY_SETUP.md) for detailed setup instructions.

### Multi-Source Strategy
- **Prototyping**: Use DigiKey for fast delivery and no minimums
- **Small Batch**: Compare JLCPCB vs DigiKey for best value
- **Production**: Optimize with JLCPCB for integrated assembly
- **Risk Mitigation**: Maintain alternatives from multiple sources

## 🐛 Troubleshooting

### Common Issues

**KiCad Symbol/Footprint Not Found:**
```bash
# Verify KiCad installation
kicad-cli version

# Search for components (with Claude Code)
/find-symbol STM32
/find-footprint LQFP64
```

**Build Issues:**
```bash
# Clean rebuild
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup and guidelines.

## 🏗️ Architecture Overview

### Technical Stack
- **Frontend**: Python 3.9+ with type hints
- **KiCad Integration**: Direct file format support (.kicad_pro, .kicad_sch, .kicad_pcb)
- **AI Integration**: Claude Code agents with specialized circuit design expertise

### File Structure
```
circuit-synth/
├── src/circuit_synth/           # Python package
│   ├── core/                    # Core circuit representation
│   ├── kicad/                   # KiCad file I/O
│   ├── component_info/          # Component databases
│   ├── manufacturing/           # JLCPCB, DigiKey, etc.
│   └── simulation/              # SPICE integration
├── example_project/             # Complete usage example
├── tests/                       # Test suites
└── tools/                       # Development and build tools (organized by category)
```

## 🤝 Contributing

### Development Workflow
1. **Fork repository** and create feature branch
2. **Follow coding standards** (black, isort, mypy)
3. **Add tests** for new functionality
4. **Update documentation** as needed
5. **Submit pull request** with clear description

### Coding Standards
- **Python**: Type hints, dataclasses, SOLID principles
- **Documentation**: Clear docstrings and inline comments
- **Testing**: Comprehensive test coverage for new features

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

---

**Professional PCB Design with Python**