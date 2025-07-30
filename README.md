# circuit-synth

[![Documentation](https://readthedocs.org/projects/circuit-synth/badge/?version=latest)](https://circuit-synth.readthedocs.io/en/latest/?badge=latest)
[![PyPI version](https://badge.fury.io/py/circuit-synth.svg)](https://badge.fury.io/py/circuit-synth)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Pythonic circuit design with AI-powered component intelligence**

Generate complete KiCad projects using familiar Python syntax. Integrated AI agents help with component selection, availability checking, and design optimization - while you maintain full control over the circuit implementation.

### 🔍 **Component Intelligence**

**Ask for components naturally:**

```
👤 "find a stm32 mcu that has 3 spi's and is available on jlcpcb"

🤖 **STM32G431CBT6** - Found matching component
   📊 Stock: 83,737 units | Price: $2.50@100pcs | LCSC: C529092
   ✅ 3 SPIs: SPI1, SPI2, SPI3 
   📦 LQFP-48 package | 128KB Flash, 32KB RAM

   📋 Circuit-Synth Code:
   stm32g431 = Component(
       symbol="MCU_ST_STM32G4:STM32G431CBTx",
       ref="U",
       footprint="Package_QFP:LQFP-48_7x7mm_P0.5mm"
   )
```

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
- **🔍 Smart Component Finder**: AI-powered component recommendations with circuit-synth code generation
- **⚙️ SPICE Simulation**: Professional-grade circuit simulation with PySpice/ngspice backend

## 🚀 Claude Code Integration

### **AI-Assisted Circuit Design**

Circuit-synth works with Claude Code to streamline component selection and circuit generation:

#### **1. Natural Language Queries**
```
👤 "Design a motor controller with STM32, 3 half-bridges, current sensing, and CAN bus"
```

Claude will search components, check availability, and generate circuit-synth code.

#### **2. AI Commands**

- `/find-symbol STM32G4` → Locates KiCad symbols
- `/find-footprint LQFP` → Find footprints

#### **3. Component Search Example**

```
👤 "STM32 with 3 SPIs available on JLCPCB"

🤖 **STM32G431CBT6** - Found matching component
   📊 Stock: 83,737 units | Price: $2.50@100pcs 
   ✅ 3 SPIs: SPI1, SPI2, SPI3
   📦 LQFP-48 | 128KB Flash, 32KB RAM

   mcu = Component(
       symbol="MCU_ST_STM32G4:STM32G431CBTx",
       ref="U",
       footprint="Package_QFP:LQFP-48_7x7mm_P0.5mm"
   )
```

### **Workflow**

1. Describe requirements in natural language
2. Claude searches components and checks availability  
3. Generate circuit-synth code with verified components
4. Export to KiCad for PCB layout

### **Benefits**

- **🔍 Component Search**: AI finds suitable components
- **✅ Availability Check**: Real-time JLCPCB stock verification
- **🔧 Code Generation**: Ready-to-use circuit-synth code
- **🧠 Engineering Context**: AI explains component choices

## ⚙️ SPICE Simulation Integration

**Professional-grade circuit simulation with PySpice backend**

Circuit-synth now includes complete SPICE simulation capabilities for design validation and optimization:

```python
from circuit_synth import circuit, Component, Net

@circuit
def voltage_divider():
    """Simple resistor divider for simulation"""
    r1 = Component("Device:R", ref="R", value="4.7k")
    r2 = Component("Device:R", ref="R", value="10k") 
    
    vin = Net('VIN')    # 5V supply (auto-detected)
    vout = Net('VOUT')  # Output node
    gnd = Net('GND')    # Ground
    
    r1[1] += vin
    r1[2] += vout
    r2[1] += vout
    r2[2] += gnd

# Run simulation
circuit = voltage_divider()
sim = circuit.simulator()

# DC analysis
result = sim.operating_point()
print(f"Output voltage: {result.get_voltage('VOUT'):.3f}V")  # 3.391V

# AC frequency response
ac_result = sim.ac_analysis(1, 100000)  # 1Hz to 100kHz

# Transient analysis
transient = sim.transient_analysis(1e-6, 1e-3)  # 1μs steps, 1ms duration
```

### **Simulation Features**

- **🔬 Professional Analysis**: DC, AC, and Transient simulation with ngspice engine
- **📊 Accurate Results**: Sub-millivolt precision matching theoretical calculations
- **🔄 Seamless Integration**: Native `.simulator()` method on all circuits
- **🖥️ Cross-Platform**: Automatic ngspice detection on macOS, Linux, Windows
- **📈 Visualization Support**: Built-in plotting with matplotlib integration
- **⚡ High Performance**: Rust-accelerated circuit conversion and analysis

### **Setup**

```bash
# Install with simulation support
pip install circuit-synth[simulation]

# Or with uv
uv add circuit-synth --extra simulation
```

See [`docs/SIMULATION_SETUP.md`](docs/SIMULATION_SETUP.md) for complete setup instructions.

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
