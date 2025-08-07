# circuit-synth

**Python-based circuit design with KiCad integration and AI acceleration.**

Generate professional KiCad projects from Python code with hierarchical design, version control, and automated documentation.

## 🚀 Getting Started

```bash
# Install uv (if not already installed)  
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create new project
uv init my_circuit_project
cd my_circuit_project

# Add circuit-synth
uv add circuit-synth

# Setup complete project template
uv run cs-new-project

# Generate complete KiCad project  
uv run python circuit-synth/main.py
```

This creates an ESP32-C6 development board with USB-C, power regulation, programming interface, and status LED.

## 💡 Quick Example

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

## 🔧 Core Features

- **Professional KiCad Output**: Generate .kicad_pro, .kicad_sch, .kicad_pcb files
- **Hierarchical Design**: Modular subcircuits like software modules  
- **Component Intelligence**: JLCPCB & DigiKey integration, symbol/footprint verification
- **AI Integration**: Claude Code agents for automated design assistance
- **FMEA Analysis**: Comprehensive reliability analysis with physics-based failure models
- **Test Plan Generation**: Automated test procedures for validation and manufacturing
- **Version Control Friendly**: Git-trackable Python files with meaningful diffs

## 🤖 AI-Powered Design

Work with Claude Code to describe circuits and get production-ready results:

```bash
# AI agent commands (with Claude Code)
/find-symbol STM32                    # Search KiCad symbols
/find-footprint LQFP64                # Find footprints  
/generate-validated-circuit "ESP32 IoT sensor" mcu
```

### 🤖 Claude Code Agents

Circuit-synth includes specialized AI agents for different aspects of circuit design. Each agent has deep expertise in their domain:

#### **circuit-architect** - Master Circuit Design Coordinator
- **Use for**: Complex multi-component designs, system-level architecture
- **Expertise**: Circuit topology planning, component selection, design trade-offs
- **Example**: *"Design a complete IoT sensor node with power management, wireless connectivity, and sensor interfaces"*

#### **circuit-synth** - Circuit Code Generation Specialist  
- **Use for**: Converting natural language to working Python circuit code
- **Expertise**: circuit-synth syntax, KiCad integration, hierarchical design patterns
- **Example**: *"Generate Python code for a USB-C PD trigger circuit with 20V output"*

#### **simulation-expert** - SPICE Simulation and Circuit Validation
- **Use for**: Circuit analysis, performance optimization, validation
- **Expertise**: SPICE simulation setup, component modeling, performance analysis
- **Example**: *"Simulate this amplifier circuit and optimize for 40dB gain with <100mW power"*

#### **component-search** - Multi-Source Component Search
- **Use for**: Component selection across all suppliers, price comparison, availability checking
- **Expertise**: JLCPCB, DigiKey, and future suppliers (Mouser, LCSC, etc.)
- **Example**: *"Find 0.1uF 0603 capacitors across all suppliers with pricing comparison"*

#### **jlc-parts-finder** - JLCPCB Component Intelligence
- **Use for**: Real-time component availability, pricing, and alternatives
- **Expertise**: JLCPCB catalog search, stock levels, KiCad symbol verification
- **Example**: *"Find STM32 with 3 SPIs available on JLCPCB under $5"*

#### **digikey-parts-finder** - DigiKey Component Search
- **Use for**: Comprehensive component search with extensive catalog access
- **Expertise**: DigiKey's 8M+ components, price breaks, alternatives, datasheets
- **Example**: *"Find 0.1uF 0603 X7R capacitors with pricing at DigiKey"*

#### **general-purpose** - Research and Analysis
- **Use for**: Open-ended research, codebase analysis, complex searches
- **Expertise**: Technical research, documentation analysis, multi-step problem solving
- **Example**: *"Research best practices for EMI reduction in switching power supplies"*

#### **test-plan-creator** - Test Plan Generation and Validation
- **Use for**: Creating comprehensive test procedures for circuit validation
- **Expertise**: Functional, performance, safety, and manufacturing test plans
- **Example**: *"Generate test plan for ESP32 dev board with power measurements"*

#### **fmea-analyzer** - Failure Mode and Effects Analysis
- **Use for**: Reliability analysis, risk assessment, failure prediction
- **Expertise**: Component failure modes, physics of failure, IPC Class 3 compliance
- **Example**: *"Analyze my circuit for potential failure modes and generate FMEA report"*

### Using Agents Effectively

```bash
# Start with circuit-architect for complex projects
"Design an ESP32-based environmental monitoring station"

# Use circuit-synth for code generation
"Generate circuit-synth code for the power supply section"

# Validate with simulation-expert
"Simulate this buck converter and verify 3.3V output ripple"

# Optimize with component-guru
"Replace expensive components with JLCPCB alternatives"
```

**Pro Tip**: Let the **circuit-architect** coordinate complex projects - it will automatically delegate to other specialists as needed!

### **Agent Categories:**
- **Circuit Design**: circuit-architect, circuit-synth, simulation-expert, test-plan-creator
- **Development**: circuit_generation_agent, contributor, first_setup_agent  
- **Manufacturing**: component-guru, jlc-parts-finder, stm32-mcu-finder

### **Command Categories:**
- **Circuit Design**: analyze-design, find-footprint, find-symbol, validate-existing-circuit
- **Development**: dev-run-tests, dev-update-and-commit, dev-review-branch
- **Manufacturing**: find-mcu, find_stm32
- **Test Planning**: create-test-plan, generate-manufacturing-tests
- **Setup**: setup-kicad-plugins, setup_circuit_synth

## 🚀 Commands

### Project Creation
```bash
cs-new-project              # Complete project setup with ESP32-C6 example
```

### Circuit Generation
```bash
cd circuit-synth && uv run python main.py    # Generate KiCad files from Python code
```

### Claude Code Slash Commands
Available when working with Claude Code in a circuit-synth project:

```bash
# Component Search
/find-symbol STM32              # Search KiCad symbol libraries
/find-footprint LQFP64          # Search KiCad footprint libraries
/find-component "op-amp"        # Search for components with specifications

# Circuit Generation
/generate-validated-circuit "ESP32 IoT sensor" mcu    # AI circuit generation
/validate-existing-circuit                            # Validate current code

# Component Intelligence  
/find-parts "0.1uF 0603 X7R capacitor"               # Search all suppliers
/find-parts "STM32F407" --source jlcpcb              # JLCPCB only
/find-parts "LM358" --compare                        # Compare across suppliers
/find-stm32 "3 SPIs, USB, available JLCPCB"          # STM32-specific search

# Development (for contributors)
/dev-run-tests                  # Run comprehensive test suite
/dev-update-and-commit "msg"    # Update docs and commit changes
```

## 🔍 FMEA and Quality Assurance

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
uv run python -m circuit_synth.tools.quality_assurance.fmea_cli analyze my_circuit.py

# Generate comprehensive report
uv run python -m circuit_synth.tools.quality_assurance.fmea_cli analyze my_circuit.py --comprehensive
```

See [FMEA Guide](docs/FMEA_GUIDE.md) for detailed documentation.

## 📋 Project Structure

```
my_circuit_project/
├── circuit-synth/
│   ├── main.py              # ESP32-C6 dev board (hierarchical)
│   ├── power_supply.py      # 5V→3.3V regulation
│   ├── usb.py               # USB-C with CC resistors
│   ├── esp32c6.py           # ESP32-C6 microcontroller
│   ├── debug_header.py      # Programming interface
│   ├── led_blinker.py       # Status LED control
│   └── ESP32_C6_Dev_Board.json  # Generated netlist
├── ESP32_C6_Dev_Board/      # Generated KiCad files
│   ├── ESP32_C6_Dev_Board.kicad_pro
│   ├── ESP32_C6_Dev_Board.kicad_sch
│   ├── ESP32_C6_Dev_Board.kicad_pcb
│   └── ESP32_C6_Dev_Board.net
├── README.md                # Project guide
├── CLAUDE.md                # AI assistant instructions
└── pyproject.toml           # Project dependencies
```


## 🏭 Why Circuit-Synth?

| Traditional EE Workflow | With Circuit-Synth |
|-------------------------|-------------------|
| Manual component placement | `python main.py` → Complete project |
| Hunt through symbol libraries | Verified components with JLCPCB & DigiKey availability |
| Visual net verification | Explicit Python connections |
| GUI-based KiCad editing | Text-based Python circuit definitions |
| Copy-paste circuit patterns | Reusable circuit functions |
| Manual FMEA documentation | Automated 50+ page reliability analysis |

## 📚 Learn More

- **Website**: [circuit-synth.com](https://www.circuit-synth.com)
- **Documentation**: [docs.circuit-synth.com](https://docs.circuit-synth.com)
- **Examples**: [github.com/circuit-synth/examples](https://github.com/circuit-synth/examples)

## 🔧 Development Installation

For contributing to circuit-synth or advanced usage:

```bash
# Clone repository
git clone https://github.com/circuit-synth/circuit-synth.git
cd circuit-synth

# Development installation with uv (recommended)
uv sync

# Alternative: pip installation
pip install -e ".[dev]"

# Register AI agents for enhanced development
uv run register-agents

# Run tests to verify installation
uv run pytest
```

## ⚙️ Rust Module Development

Circuit-synth uses Rust backend for performance-critical operations. The Python package works without Rust modules using fallbacks.

### Building Rust Modules

```bash
# Install Rust toolchain (if not installed)
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Build all Rust modules
./scripts/build_rust_modules.sh

# Build specific module manually
cd rust_modules/rust_netlist_processor
cargo build --release
maturin develop
```

### Testing Rust Integration

```bash
# Test all Rust modules
./scripts/test_rust_modules.sh

# Run comprehensive test suite
./scripts/run_all_tests.sh

# Test with verbose output
./scripts/run_all_tests.sh --verbose
```

## 🧪 Testing & Quality Assurance

### Pre-Release Testing (CRITICAL for PyPI)

```bash
# Comprehensive regression test before any release
./tools/testing/run_full_regression_tests.py

# This performs COMPLETE environment reconstruction:
# - Clears ALL caches (Python, Rust, system)
# - Reinstalls Python environment from scratch
# - Rebuilds all Rust modules with Python bindings
# - Runs comprehensive functionality tests
# - Validates example project generation
# - Takes ~2 minutes, gives 100% confidence
```

### Development Testing

```bash
# Run full test suite
./scripts/run_all_tests.sh

# Quick regression test (skip reinstall)
./tools/testing/run_full_regression_tests.py --skip-install --quick

# Python tests only
uv run pytest --cov=circuit_synth

# Rust tests only  
./scripts/test_rust_modules.sh

# Code formatting and linting
black src/
isort src/
flake8 src/
mypy src/

# Run specific test file
uv run pytest tests/unit/test_core_circuit.py -v
```

## 🔍 KiCad Integration Details

### Prerequisites

**KiCad 8.0+ Required:**
```bash
# macOS
brew install kicad

# Ubuntu/Debian  
sudo apt install kicad

# Windows: Download from kicad.org
```

### KiCad Plugin (Optional)

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
export CIRCUIT_SYNTH_USE_RUST=true
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

# Search for symbols/footprints
/find-symbol STM32
/find-footprint LQFP64

# Check library paths
find /usr/share/kicad/symbols -name "*.kicad_sym" | head -5
```

**Rust Module Build Failures:**
```bash
# Install required tools
pip install maturin
cargo --version  # Verify Rust installation

# Clean build
cargo clean
./scripts/build_rust_modules.sh
```

**AI Agent Issues:**
```bash
# Re-register agents
uv run register-agents

# Verify Claude Code integration
claude --version  # Ensure Claude Code is installed
```

## 🏗️ Architecture Overview

### Technical Stack
- **Frontend**: Python 3.9+ with type hints
- **Backend**: Rust modules for performance-critical operations
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
├── rust_modules/                # Rust acceleration
├── examples/                    # Usage examples
├── tests/                       # Test suites
└── scripts/                     # Build and development scripts
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
- **Rust**: Standard formatting with `cargo fmt`
- **Documentation**: Clear docstrings and inline comments
- **Testing**: Comprehensive test coverage for new features

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

---

⚡ **Professional PCB Design, Programmatically** ⚡