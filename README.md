# circuit-synth

[![Documentation](https://readthedocs.org/projects/circuit-synth/badge/?version=latest)](https://circuit-synth.readthedocs.io/en/latest/?badge=latest)
[![PyPI version](https://badge.fury.io/py/circuit-synth.svg)](https://badge.fury.io/py/circuit-synth)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Pythonic circuit design for professional KiCad projects**

Generate complete KiCad projects using simple Python code. No DSL to learn - just Python classes and functions that any engineer can read and modify.

## 🤖 AI-Powered Circuit Design with Claude Code

Circuit-synth is **the first circuit design tool built for AI collaboration**. Natural language requests become complete, manufacturable circuits with ready-to-use code.

### ⚡ **Instant Component Intelligence**

**Ask for components naturally, get professional results:**

```
👤 "find a stm32 mcu that has 3 spi's and is available on jlcpcb"

🤖 **STM32G431CBT6** - Perfect match found!
   📊 Stock: 83,737 units | Price: $2.50@100pcs | LCSC: C529092
   ✅ 3 SPIs: SPI1, SPI2, SPI3 
   📦 LQFP-48 package | 128KB Flash, 32KB RAM

   📋 Ready Circuit-Synth Code:
   stm32g431 = Component(
       symbol="MCU_ST_STM32G4:STM32G431CBTx",
       ref="U",
       footprint="Package_QFP:LQFP-48_7x7mm_P0.5mm"
   )
```

**No catalog browsing. No datasheets. No guesswork. Just instant, accurate results.**

### 🎯 **Professional AI Commands**

- **`/find-mcu`** - Intelligent MCU search with specifications and peripheral matching
- **`/find-symbol`** - Instantly find KiCad symbols across all libraries  
- **`/find-footprint`** - Locate correct footprints with package verification
- **`/check-manufacturing`** - Real-time JLCPCB availability and pricing
- **`/analyze-power`** - Power tree analysis and regulation recommendations
- **`/optimize-routing`** - Signal integrity and PCB layout guidance

### 🏗️ **Specialized Design Agents**

- **`circuit-architect`** - Master circuit coordinator for complex multi-domain systems
- **`power-expert`** - Power supply design and regulation specialist  
- **`signal-integrity`** - High-speed PCB design and EMI expert
- **`component-guru`** - Manufacturing optimization and sourcing specialist

### 🔥 **Complete Workflow Example**

```
👤 "I need a USB-C power delivery circuit with 3.3V and 5V outputs"

🤖 Let me design a complete USB-C PD solution for you...

   [Searches for USB-C controllers with PD support]
   [Finds optimal regulators with JLCPCB availability] 
   [Generates complete circuit with protection]
   [Provides manufacturing-ready component list]
   [Outputs ready-to-compile circuit-synth code]

📋 Complete implementation ready in 30 seconds!
```

**This is the future of circuit design - AI that understands electrical engineering.**

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
from circuit_synth.manufacturing.jlcpcb import get_component_availability_web

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
from circuit_synth.component_info.microcontrollers.stm32 import STM32PinMapper

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

## 🚀 Claude Code Workflow Guide

### **The New Standard for Circuit Design**

Circuit-synth + Claude Code creates the most productive circuit design workflow ever built. Here's how to leverage this powerful combination:

#### **1. Start with Natural Language**
```
👤 "Design a motor controller with STM32, 3 half-bridges, current sensing, and CAN bus"
```

Instead of spending hours researching components, just describe what you need. Claude will:
- Search the modm-devices database for optimal MCUs
- Check JLCPCB availability and pricing in real-time  
- Generate complete circuit-synth code with proper connections
- Provide manufacturing-ready component recommendations

#### **2. Use Professional AI Commands**

**Component Intelligence:**
- `/find-mcu 5 uarts` → Finds MCUs with specific peripheral counts
- `/find-symbol STM32G4` → Locates exact KiCad symbols
- `/check-manufacturing LM358` → Real-time availability and pricing

**Design Expertise:**
- `/analyze-power` → Complete power tree analysis
- `/optimize-routing` → Signal integrity recommendations  
- `/suggest-improvements` → Design optimization suggestions

#### **3. Leverage Specialized Agents**

**For complex designs, delegate to experts:**
```
👤 "I need a power supply that converts 24V to 3.3V and 5V rails"

🤖 I'll use the power-expert agent to design this for you...
   [Agent analyzes requirements, selects topology, finds components]
   [Generates complete power tree with protection circuits]
   [Outputs manufacturing-ready design]
```

#### **4. Real-World Example: STM32 Selection**

**Traditional workflow:** 2-3 hours of research, datasheets, availability checking
**Claude Code workflow:** 30 seconds

```
👤 "/find-mcu STM32 with 3 SPIs available on JLCPCB"

🤖 **STM32G431CBT6** - Perfect match!
   📊 Stock: 83,737 units | Price: $2.50@100pcs 
   ✅ 3 SPIs: SPI1, SPI2, SPI3
   📦 LQFP-48 | 128KB Flash, 32KB RAM

   Ready code:
   mcu = Component(
       symbol="MCU_ST_STM32G4:STM32G431CBTx",
       ref="U",
       footprint="Package_QFP:LQFP-48_7x7mm_P0.5mm"
   )
```

#### **5. End-to-End Circuit Generation**

**The complete workflow in action:**
1. **Describe** your requirements in natural language
2. **Claude searches** components across multiple databases  
3. **AI agents** provide domain expertise (power, signal integrity, etc.)
4. **Generate** complete circuit-synth code with verified components
5. **Export** to KiCad for PCB layout and manufacturing

**Result:** Professional circuit designs in minutes, not days.

### **Why This Changes Everything**

- **🎯 No Research Required**: AI finds optimal components instantly
- **✅ Manufacturing Ready**: Real-time availability and pricing verification
- **🔧 Professional Quality**: Expert domain knowledge built-in
- **⚡ Incredible Speed**: Complete designs in 30 seconds to 5 minutes
- **🧠 Learning Accelerator**: AI explains decisions and trade-offs

**This isn't just faster circuit design - it's fundamentally better circuit design.**

### **🚀 Getting Started with Claude Code**

**1. Install circuit-synth:**
```bash
pip install circuit-synth[claude]  # Includes Claude Code integration
```

**2. Set up AI agents (optional but recommended):**
```bash
python -c "from circuit_synth import setup_claude_integration; setup_claude_integration()"
```

**3. Start designing with AI:**
```bash
# In Claude Code, just ask natural questions:
"find me an stm32 with 3 spis and can bus"
"design a 3.3v regulator circuit with thermal protection"
"help me choose between buck and ldo for this application"
```

**4. Use professional commands:**
```bash
/find-mcu         # Intelligent MCU search
/check-manufacturing  # Component availability  
/analyze-power    # Power tree analysis
# ... and 9 more specialized commands
```

**The AI handles the complexity. You focus on the design.**

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
