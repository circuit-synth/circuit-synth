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
- **🔧 STM32 MCU Selection**: `/find-stm32-mcu` - AI-powered STM32 selection with complete pin assignments
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

## 🔧 STM32 Integration

Circuit-synth provides the most advanced STM32 development experience available, combining official pin mapping data with intelligent MCU selection and manufacturing integration.

### AI-Powered MCU Selection

Simply describe your project requirements and get complete STM32 recommendations:

```bash
/find-stm32-mcu IoT project with WiFi, 2 UARTs, SPI, I2C, low power
```

**Instant Response:**
```
🎯 STM32G431CBT6 - Recommended for IoT Project
💡 ARM Cortex-M4 @ 170MHz, 128KB Flash, 32KB RAM
📦 LQFP-48 Package | 💰 $2.50@100pcs | ✅ 83K units in stock

📋 Complete Pin Assignment:
- USART1_TX: PA9 (AF7) | USART1_RX: PA10 (AF7)  
- USART2_TX: PA2 (AF7) | USART2_RX: PA3 (AF7)
- SPI1_SCK: PA5 (AF5) | SPI1_MISO: PA6 (AF5) | SPI1_MOSI: PA7 (AF5)
- I2C1_SCL: PB8 (AF4) | I2C1_SDA: PB9 (AF4)

🔌 Ready Circuit-Synth Code:
mcu = Component(
    symbol="MCU_ST_STM32G4:STM32G431CBTx",
    ref="U1",
    footprint="Package_QFP:LQFP-48_7x7mm_P0.5mm"
)
# Complete pin connections included...
```

### Programmatic Pin Mapping

For advanced use cases, access the pin mapping system directly:

```python
from circuit_synth.stm32_pinout import STM32PinMapper

# Initialize for STM32G4 family
mapper = STM32PinMapper("g4-31_41", modm_devices_path="external_repos/modm-devices")

# Find optimal pins for USART
usart_options = mapper.find_pins_for_peripheral("usart1", "tx")
for option in usart_options[:3]:
    print(f"{option.pin.name}: {option.reasoning} (confidence: {option.confidence:.2f})")

# Get complete pin assignment for multiple peripherals
requirements = {
    "usart1_tx": "tx",
    "usart1_rx": "rx", 
    "spi1_sck": "sck",
    "i2c1_sda": "sda"
}
assignments = mapper.suggest_pin_assignment(requirements)
```

### Key Advantages

- **Official Data**: Uses modm-devices repository for accurate pin mappings across all STM32 families
- **Conflict Resolution**: Intelligent assignment prevents pin conflicts in complex designs
- **Manufacturing Ready**: Integrated JLCPCB availability and pricing verification
- **AI-Powered**: Natural language project descriptions → complete MCU solutions
- **Production Quality**: Confidence scoring and alternative options for robust designs

### Supported STM32 Families

Complete pin mapping support for all major STM32 families:
- **STM32F Series**: F0, F1, F2, F3, F4, F7 (general purpose, high performance)
- **STM32G Series**: G0, G4 (mainstream, high performance with DSP)  
- **STM32H Series**: H5, H7 (high performance, dual core)
- **STM32L Series**: L0, L1, L4, L5 (ultra-low power)
- **STM32U Series**: U0, U5 (ultra-low power, AI-enabled)
- **STM32W Series**: WB, WL (wireless, LoRa)

## Key Features

- **🐍 Pure Python**: Standard Python syntax - no DSL to learn
- **🔄 Bidirectional KiCad Integration**: Import existing projects, export clean KiCad files
- **📋 Professional Netlists**: Generate industry-standard KiCad .net files
- **🏗️ Hierarchical Design**: Multi-sheet projects with proper organization
- **📝 Smart Annotations**: Automatic docstring extraction + manual text/tables
- **⚡ Rust-Accelerated**: Fast symbol lookup and placement algorithms
- **🏭 Manufacturing Integration**: Real-time component availability and pricing from JLCPCB
- **🔍 Smart Component Finder**: AI-powered component recommendations with instant circuit-synth code generation
- **🔧 STM32 Pin Mapping**: Complete STM32 pin assignment with modm-devices integration and conflict resolution

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

**CI Setup:**
```bash
# For continuous integration testing
./tools/ci-setup/setup-ci-symbols.sh
```

## Contributing

We welcome contributions! See [CLAUDE.md](CLAUDE.md) for development setup and coding standards.

For AI-powered circuit design features, see [docs/integration/CLAUDE_INTEGRATION.md](docs/integration/CLAUDE_INTEGRATION.md).

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
