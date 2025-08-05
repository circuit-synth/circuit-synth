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
def usb_to_3v3():
    """USB-C to 3.3V regulation"""
    
    # Define nets
    vbus_in = Net('VBUS_IN')
    vcc_3v3_out = Net('VCC_3V3_OUT') 
    gnd = Net('GND')
    
    # Components with KiCad integration
    regulator = Component(
        symbol="Regulator_Linear:AMS1117-3.3", 
        ref="U",
        footprint="Package_TO_SOT_SMD:SOT-223-3_TabPin2"
    )
    
    cap_in = Component(symbol="Device:C", ref="C", value="10uF")
    cap_out = Component(symbol="Device:C", ref="C", value="22uF")
    
    # Explicit connections
    regulator["VI"] += vbus_in
    regulator["VO"] += vcc_3v3_out
    regulator["GND"] += gnd
    
    cap_in[1] += vbus_in
    cap_in[2] += gnd
    cap_out[1] += vcc_3v3_out
    cap_out[2] += gnd

# Generate KiCad project
circuit = usb_to_3v3()
circuit.generate_kicad_project("power_supply")
```

## 🔧 Core Features

- **Professional KiCad Output**: Generate .kicad_pro, .kicad_sch, .kicad_pcb files
- **Hierarchical Design**: Modular subcircuits like software modules  
- **Component Intelligence**: JLCPCB integration, symbol/footprint verification
- **AI Integration**: Claude Code agents for automated design assistance
- **Version Control Friendly**: Git-trackable Python files vs binary KiCad files

## 🤖 AI-Powered Design

Work with Claude Code to describe circuits and get production-ready results:

```bash
# AI agent commands (with Claude Code)
/find-symbol STM32                    # Search KiCad symbols
/find-footprint LQFP64                # Find footprints  
/generate-validated-circuit "ESP32 IoT sensor" mcu
```

## 📋 Project Structure

```
my_circuit_project/
├── circuit-synth/
│   ├── main.py              # Main circuit definition
│   ├── power_supply.py      # Modular subcircuits
│   ├── usb.py
│   └── esp32c6.py
├── MyProject/               # Generated KiCad files
│   ├── MyProject.kicad_pro
│   ├── MyProject.kicad_sch
│   └── MyProject.kicad_pcb
├── memory-bank/             # Auto-documentation
└── .claude/                 # AI agent config
```

## ⚡ Performance (Optional)

Circuit-synth includes optional Rust acceleration modules. The package works perfectly without them using Python fallbacks.

**To enable Rust acceleration:**

```bash
# For developers who want maximum performance
pip install maturin
./scripts/build_rust_modules.sh
```

## 🚀 Commands

```bash
# Project creation
cs-new-project              # Complete project setup
cs-new-pcb "Board Name"     # PCB-focused project

# Development  
cd circuit-synth && uv run python main.py    # Generate KiCad files
```

## 🏭 Why Circuit-Synth?

| Traditional EE Workflow | With Circuit-Synth |
|-------------------------|-------------------|
| Manual component placement | `python main.py` → Complete project |
| Hunt through symbol libraries | Verified components with JLCPCB availability |
| Visual net verification | Explicit Python connections |
| Binary KiCad files | Git-friendly Python source |
| Documentation drift | Automated engineering docs |

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

```bash
# Run full test suite
./scripts/run_all_tests.sh

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
```

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
│   ├── manufacturing/           # JLCPCB, etc.
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