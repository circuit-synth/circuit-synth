# circuit-synth

[![Documentation](https://readthedocs.org/projects/circuit-synth/badge/?version=latest)](https://circuit-synth.readthedocs.io/en/latest/?badge=latest)
[![PyPI version](https://badge.fury.io/py/circuit-synth.svg)](https://badge.fury.io/py/circuit-synth)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Pythonic circuit design for professional KiCad projects**

Generate complete KiCad projects using simple Python code. No DSL to learn - just Python classes and functions that any engineer can read and modify.

## 🤖 Optimized for Claude Code

This repository is fully optimized for AI-assisted development with Claude Code:

- **🔍 Component Search**: `/find-symbol`, `/find-footprint` - Instantly find KiCad symbols and footprints
- **🎯 Smart Component Finding**: `/find-jlc-component`, `/quick-component` - Find manufacturable parts with ready code
- **🤖 Component Wizard**: `/component-wizard` - Interactive component selection with trade-off analysis
- **🏗️ Circuit Design Agent**: Specialized `circuit-synth` agent for expert guidance on component selection and circuit topology
- **⚡ Development Commands**: `/dev-run-tests`, `/dev-update-and-commit` - Streamlined development workflow
- **📋 Pre-configured Permissions**: Skip repetitive approval prompts with curated tool allowlists

**Perfect for AI-assisted circuit design - just ask Claude to help you build circuits!**

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
from circuit_synth.jlc_integration import get_component_availability_web

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
    
    # Voltage regulator - check availability with JLCPCB
    jlc_vreg = get_component_availability_web("AMS1117-3.3")
    print(f"AMS1117-3.3 stock: {jlc_vreg['stock']} units available")
    
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
- **🏭 Manufacturing Integration**: Real-time component availability and pricing from JLCPCB
- **🔍 Smart Component Finder**: AI-powered component recommendations with instant circuit-synth code generation

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
