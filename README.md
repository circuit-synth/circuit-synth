# circuit-synth

**Python-based circuit design with KiCad integration and AI acceleration.**

Generate professional KiCad projects from Python code with hierarchical design, version control, and automated documentation.

## Installation

```bash
# Install with uv (recommended)
uv add circuit-synth

# Or with pip
pip install circuit-synth
```

## Quick Start

```bash
# Create new project with example circuit
uv run cs-new-project

# This generates a complete ESP32-C6 development board
cd circuit-synth && uv run python main.py
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

- **KiCad Integration**: Generate .kicad_pro, .kicad_sch, .kicad_pcb files
- **Hierarchical Design**: Modular subcircuits with clean Python syntax
- **Component Intelligence**: JLCPCB availability and footprint verification
- **AI Assistance**: Claude Code agents for design automation
- **FMEA Analysis**: Comprehensive reliability analysis with physics-based failure models
- **Test Generation**: Automated test plans for validation
- **Version Control**: Git-friendly text-based circuit definitions

## AI-Powered Design

### Claude Code Commands

```bash
# Component search
/find-symbol STM32              # Search KiCad symbol libraries
/find-footprint LQFP64          # Find footprint libraries
/find-stm32 "3 SPIs, USB"       # STM32 with specific peripherals

# Circuit generation
/generate-validated-circuit "ESP32 IoT sensor" mcu
/validate-existing-circuit      # Validate current circuit code

# JLCPCB integration
/jlc-search "voltage regulator 3.3V"

# FMEA analysis
/analyze-fmea my_circuit.py     # Run FMEA analysis on circuit
```

### Specialized AI Agents

When working with Claude Code, these agents provide domain expertise:

- **circuit-architect**: Overall circuit design and system architecture
- **circuit-synth**: Python code generation for circuits  
- **simulation-expert**: SPICE simulation and validation
- **component-guru**: Component selection and JLCPCB sourcing
- **jlc-parts-finder**: Real-time JLCPCB availability checking
- **stm32-mcu-finder**: STM32 peripheral search and selection
- **test-plan-creator**: Automated test plan generation
- **fmea-analyzer**: Reliability analysis and failure prediction

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
uv run python -m circuit_synth.tools.quality_assurance.fmea_cli analyze my_circuit.py

# Generate comprehensive report
uv run python -m circuit_synth.tools.quality_assurance.fmea_cli analyze my_circuit.py --comprehensive
```

See [FMEA Guide](docs/FMEA_GUIDE.md) for detailed documentation.

## Project Structure

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


## Why Circuit-Synth?

| Traditional Workflow | Circuit-Synth |
|---------------------|---------------|
| Manual component placement | Python code generates complete projects |
| Search through symbol libraries | Verified components with JLCPCB availability |
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

### Rust Acceleration (Optional)

For 6x performance improvement:

```bash
# Install Rust
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Build modules
./scripts/build_rust_modules.sh

# Test integration
./scripts/test_rust_modules.sh
```

## Testing

```bash
# Run all tests
./scripts/run_all_tests.sh

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

**Symbol/Footprint Not Found:**
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
cargo clean
./scripts/build_rust_modules.sh
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup and guidelines.

Quick start:
1. Fork and clone the repository
2. Run `uv sync` to install dependencies
3. Make changes with tests
4. Submit a pull request

---

**Professional PCB Design with Python**