# circuit-synth

[![Documentation](https://readthedocs.org/projects/circuit-synth/badge/?version=latest)](https://circuit-synth.readthedocs.io/en/latest/?badge=latest)
[![PyPI version](https://badge.fury.io/py/circuit-synth.svg)](https://badge.fury.io/py/circuit-synth)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Pythonic circuit design with AI-powered component intelligence**

Generate complete KiCad projects using familiar Python syntax. Integrated AI agents help with component selection, availability checking, and design optimization - while you maintain full control over the circuit implementation.

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

### 🎯 **AI Commands**

- **`/find-symbol`** - Find KiCad symbols across all libraries  
- **`/find-footprint`** - Locate correct footprints with package verification

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


## Key Features

- **🐍 Pure Python**: Standard Python syntax - no DSL to learn
- **🔄 Bidirectional KiCad Integration**: Import existing projects, export clean KiCad files
- **📋 Professional Netlists**: Generate industry-standard KiCad .net files
- **🏗️ Hierarchical Design**: Multi-sheet projects with proper organization
- **📝 Smart Annotations**: Automatic docstring extraction + manual text/tables
- **⚡ Rust-Accelerated**: Fast symbol lookup and placement algorithms
- **🏭 Manufacturing Integration**: Real-time component availability and pricing from JLCPCB
- **🔍 Smart Component Finder**: AI-powered component recommendations with instant circuit-synth code generation

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

#### **2. Use AI Commands**

- `/find-symbol STM32G4` → Locates exact KiCad symbols
- `/find-footprint LQFP` → Find correct footprints

#### **3. Real-World Example: STM32 Selection**

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

#### **4. End-to-End Circuit Generation**

**The complete workflow in action:**
1. **Describe** your requirements in natural language
2. **Claude searches** components and finds optimal matches  
3. **Generate** complete circuit-synth code with verified components
4. **Export** to KiCad for PCB layout and manufacturing

**Result:** Professional circuit designs in minutes, not days.

### **Why This Changes Everything**

- **🎯 No Research Required**: AI finds optimal components instantly
- **✅ Manufacturing Ready**: Real-time availability and pricing verification
- **🔧 Professional Quality**: Expert domain knowledge built-in
- **⚡ Incredible Speed**: Complete designs in 30 seconds to 5 minutes
- **🧠 Learning Accelerator**: AI explains decisions and trade-offs

**This isn't just faster circuit design - it's fundamentally better circuit design.**

### **🧠 Python + AI Working Together**

Circuit-synth combines the best of both approaches:

- **✅ Pure Python**: Standard classes and functions you can read, modify, and extend
- **✅ AI Assistance**: Intelligent component search, availability checking, and optimization suggestions
- **✅ Your Control**: AI provides recommendations, you make the final decisions
- **✅ No Lock-in**: Generated Python code works with or without AI features

**The result**: Faster development with professional component choices, while maintaining full engineering control.

### **🚀 Getting Started with Claude Code**

**1. Install circuit-synth:**
```bash
pip install circuit-synth
```

**2. Start designing with AI:**
```bash
# In Claude Code, just ask natural questions:
"find me an stm32 with 3 spis and can bus"
"design a 3.3v regulator circuit with thermal protection"
"help me choose between buck and ldo for this application"
```

**3. Use AI commands:**
```bash
/find-symbol      # Find KiCad symbols
/find-footprint   # Find component footprints
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
