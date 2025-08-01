# circuit-synth

[![Documentation](https://readthedocs.org/projects/circuit-synth/badge/?version=latest)](https://circuit-synth.readthedocs.io/en/latest/?badge=latest)
[![PyPI version](https://badge.fury.io/py/circuit-synth.svg)](https://badge.fury.io/py/circuit-synth)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Agent-first hierarchical circuit design library with AI-powered component intelligence**

Circuit-synth is designed to be used **with and by AI agents** for intelligent circuit design. Generate complete KiCad projects with professional hierarchical architecture using familiar Python syntax. Each subcircuit follows software engineering principles - single responsibility, clear interfaces, and modular design. Specialized AI agents provide component selection, availability checking, SPICE simulation, and design optimization.

## 🤖 Agent-First Design Philosophy

**Natural Language → Working Circuit Code**

Circuit-synth excels when used with AI agents that can:
- **Understand Requirements**: "Design a motor controller with STM32 and 3 half-bridges"
- **Search Components**: Find suitable parts with real JLCPCB availability 
- **Generate Code**: Create production-ready hierarchical circuit-synth code
- **Validate Designs**: Run SPICE simulation and optimization
- **Export Projects**: Professional KiCad projects ready for manufacturing

**Built-in AI Agents:**
- 🎯 **circuit-synth**: Component selection and code generation specialist
- 🔬 **simulation-expert**: SPICE simulation and circuit validation expert

## 🚀 Getting Started from Scratch

### Option 1: Using uv (Recommended - Modern Python)

```bash
# 1. Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Create new KiCad project
uv init my_kicad_project
cd my_kicad_project

# 3. Add circuit-synth
uv add circuit-synth

# 4. Setup circuit-synth in current project
uv run cs-new-project
```

### Option 2: Using pip (Traditional Python)

```bash
# 1. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 2. Install circuit-synth
pip install circuit-synth

# 3. Setup new project
cs-new-project
```

**Result:** Complete KiCad project setup with circuit-synth Python files, AI agents, and KiCad plugins ready!

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
# Create and run a new project  
uv init my_kicad_project && cd my_kicad_project
uv add circuit-synth && uv run cs-new-project
uv run python circuit-synth/main.py
```

Generates a complete hierarchical KiCad project with modular subcircuits, professional schematics, PCB layout, and netlists.

## 🏗️ Hierarchical Circuit Design

**Professional modular architecture following software engineering principles**

Circuit-synth now generates circuits as **hierarchical subcircuits** - each subcircuit is like a software function with single responsibility, clear interfaces, and modular design.

### STM32 + IMU + USB-C Hierarchical Demo

```python
from circuit_synth import circuit, Component, Net
from circuit_synth.core.decorators import enable_comments

@enable_comments
@circuit(name="Power_Supply")
def power_supply_subcircuit():
    """
    USB-C Power Supply Subcircuit
    
    Converts 5V USB VBUS to regulated 3.3V system power.
    Single responsibility: Power regulation only.
    
    Interface:
    - VBUS_IN: 5V input from USB-C
    - VCC_3V3_OUT: Regulated 3.3V output  
    - GND: System ground
    """
    # Define subcircuit interface nets
    vbus_in = Net('VBUS_IN')
    vcc_3v3_out = Net('VCC_3V3_OUT')
    gnd = Net('GND')
    
    # USB-C connector and regulation circuit
    usb_connector = Component(
        symbol="Connector:USB_C_Receptacle_USB2.0_16P",
        ref="J", footprint="Connector_USB:USB_C_Receptacle_Palconn_UTC16-G"
    )
    
    regulator = Component(
        symbol="Regulator_Linear:AMS1117-3.3",
        ref="U", footprint="Package_TO_SOT_SMD:SOT-223-3_TabPin2"
    )
    # ... complete power regulation circuit

@enable_comments  
@circuit(name="MCU_Core")
def mcu_core_subcircuit():
    """
    STM32G431CBU6 Microcontroller Core Subcircuit
    
    Single responsibility: MCU with essential support circuits.
    Clean interfaces for I2C, SWD, and GPIO connections.
    """
    # STM32 with oscillator, reset, and decoupling
    # ... complete MCU support circuit

@enable_comments
@circuit(name="STM32_IMU_USBC_Hierarchical")  
def main_circuit():
    """
    Main circuit instantiating all hierarchical subcircuits.
    
    Professional modular design with 6 subcircuits:
    • Power Supply (USB-C → 3.3V regulation)
    • MCU Core (STM32G431CBU6 + support)
    • IMU Sensor (LSM6DSL I2C interface)
    • Programming Interface (SWD connector)
    • Status LEDs (Power + user indicators)
    • Test Points (Debug access points)
    """
    # Create and connect all subcircuits
    power_supply = power_supply_subcircuit()
    mcu_core = mcu_core_subcircuit()
    imu_sensor = imu_sensor_subcircuit()
    programming_interface = programming_interface_subcircuit()
    status_leds = status_leds_subcircuit()
    test_points = test_points_subcircuit()

# Generate hierarchical KiCad project
circuit = main_circuit()
circuit.generate_kicad_project(
    project_name="STM32_IMU_USBC_Hierarchical",
    placement_algorithm="hierarchical",
    generate_pcb=True
)
```

### Hierarchical Design Benefits

- **🔧 Single Responsibility**: Each subcircuit has one clear purpose
- **🔗 Clear Interfaces**: Well-defined connections between modules  
- **🔄 Maintainability**: Modify subcircuits independently
- **📦 Reusability**: Subcircuits work across multiple projects
- **📈 Scalability**: Easy to add new functionality as subcircuits
- **👥 Team Development**: Multiple developers can work on different subcircuits
- **🏭 Professional Output**: Industry-standard hierarchical KiCad projects

### Professional Workflow

**Requirements** → **Hierarchical Subcircuits** → **SPICE Validation** → **KiCad Hierarchical Project**

1. **Analyze Requirements**: Identify functional blocks and interfaces
2. **Design Subcircuits**: Each subcircuit = one responsibility (like software functions)
3. **Validate with SPICE**: Simulate critical subcircuits (power, analog, etc.)
4. **Generate KiCad Project**: Complete hierarchical project with separate sheets per subcircuit

### Generated KiCad Files

```
my_kicad_project/
├── circuit-synth/                          # Circuit-synth Python files  
│   ├── main.py                             # Hierarchical circuit definition
│   ├── simple_led.py                       # Simple examples
│   └── voltage_divider.py                  # More examples
├── .claude/                                # AI agents and commands
├── STM32_LED_Blinker/                      # Generated KiCad project
│   ├── STM32_LED_Blinker.kicad_pro         # Main project
│   ├── STM32_LED_Blinker.kicad_sch         # Top-level schematic  
│   ├── STM32_LED_Blinker.kicad_pcb         # PCB layout
│   ├── Power_Supply.kicad_sch              # Power subcircuit sheet
│   └── LED_Blinker.kicad_sch               # LED subcircuit sheet
├── README.md                               # Project documentation
└── CLAUDE.md                               # Claude Code guidance
```

Each subcircuit appears as a **separate hierarchical sheet** in KiCad - perfect for complex designs and team collaboration.

## Example Circuit (Legacy Flat Design)

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

- **🏗️ Hierarchical Circuit Design**: Professional modular architecture with subcircuits following software engineering principles (single responsibility, clear interfaces, maintainability)
- **🐍 Pure Python**: Standard Python syntax - no DSL to learn
- **🔄 Bidirectional KiCad Integration**: Import existing projects, export hierarchical KiCad projects with separate sheets per subcircuit
- **📋 Professional Netlists**: Generate industry-standard KiCad .net files with hierarchical structure
- **🏗️ Hierarchical Design**: Multi-sheet projects with proper organization following software engineering principles
- **📝 Smart Annotations**: Automatic docstring extraction + manual text/tables for comprehensive documentation
- **⚡ Rust-Accelerated**: Fast symbol lookup and hierarchical placement algorithms
- **🏭 Manufacturing Integration**: Real-time component availability and pricing from JLCPCB with JLCPCB-compatible component selection
- **🔍 Smart Component Finder**: AI-powered component recommendations with circuit-synth code generation
- **🎨 KiCad Plugin Integration**: Native AI-powered plugins for both PCB and schematic editors
- **🤖 5 Specialized AI Agents**: circuit-architect, power-expert, signal-integrity, component-guru, simulation-expert
- **⚙️ SPICE Simulation**: Professional-grade circuit simulation with PySpice/ngspice backend for subcircuit validation

> **🏗️ New Professional Standard**: All circuits are now generated as hierarchical subcircuits following software engineering principles. This replaces monolithic circuit design with modular, maintainable architecture that scales to complex designs.

## 🚀 Claude Code Integration

### **AI-Assisted Circuit Design**

Circuit-synth works with Claude Code to streamline component selection and circuit generation:

#### **1. Natural Language Queries**
```
👤 "Design a motor controller with STM32, 3 half-bridges, current sensing, and CAN bus"
```

Claude will search components, check availability, and generate hierarchical circuit-synth code with proper subcircuit organization.

#### **2. AI Commands & Agents**

- `/find-symbol STM32G4` → Locates KiCad symbols
- `/find-footprint LQFP` → Find footprints
- **🆕 `simulation-expert` agent** → SPICE simulation and circuit validation specialist

**Setup AI agents:**
```bash
uv run register-agents  # Register all 5 specialized circuit design agents
```

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
3. Generate hierarchical circuit-synth code with verified components and proper subcircuit organization
4. Export to hierarchical KiCad project for professional PCB layout

### **Benefits**

- **🔍 Component Search**: AI finds suitable components
- **✅ Availability Check**: Real-time JLCPCB stock verification
- **🔧 Hierarchical Code Generation**: Ready-to-use modular circuit-synth code
- **🏗️ Professional Architecture**: AI organizes circuits into proper subcircuits
- **🧠 Engineering Context**: AI explains component choices and hierarchical design decisions
- **🔬 Simulation Expert**: Dedicated AI agent for SPICE simulation and circuit validation

## ⚙️ SPICE Simulation Integration

**Professional-grade circuit simulation with PySpice backend**

Circuit-synth includes complete SPICE simulation capabilities for hierarchical design validation and optimization. Validate individual subcircuits or complete systems:

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
- **🏗️ Hierarchical Validation**: Simulate individual subcircuits or complete hierarchical designs
- **📊 Accurate Results**: Sub-millivolt precision matching theoretical calculations
- **🔄 Seamless Integration**: Native `.simulator()` method on all circuits and subcircuits
- **🖥️ Cross-Platform**: Automatic ngspice detection on macOS, Linux, Windows
- **📈 Visualization Support**: Built-in plotting with matplotlib integration
- **⚡ High Performance**: Rust-accelerated circuit conversion and analysis

### **Setup**

```bash
# Install circuit-synth (simulation included by default)
pip install circuit-synth

# Or with uv
uv add circuit-synth
```

See [`docs/SIMULATION_SETUP.md`](docs/SIMULATION_SETUP.md) for ngspice installation instructions.

## 🎨 KiCad Plugin Integration

Circuit-synth includes **native KiCad plugins** that bring AI-powered circuit analysis directly into KiCad's interface:

### **📋 PCB Editor Plugin**
- **Access**: Tools → External Plugins → "Circuit-Synth AI"
- **Features**: 
  - Complete PCB analysis (components, tracks, board size)
  - Associated schematic analysis integration
  - AI-powered design recommendations
  - Real-time board statistics

### **📐 Schematic Editor Plugin** 
- **Access**: Tools → Generate Bill of Materials → "Circuit-Synth AI"
- **Method**: Breakthrough "BOM backdoor" approach
- **Features**:
  - Component type analysis and breakdown
  - Net connectivity mapping
  - Design complexity assessment
  - AI-powered optimization suggestions

### **Installation**
```bash
# Install plugins to KiCad
cd kicad_plugins/
uv run python install_plugin.py

# Or manual installation - see kicad_plugins/INSTALL.md
```

### **Example Plugin Output**
```
🚀 Circuit-Synth AI - Schematic Analysis Results

📋 Project Information:
• Design: my_circuit
• Components Found: 17

📐 Component Analysis:
• Device: 10 components
• RF_Module: 1 components
• Regulator_Linear: 1 components

🤖 AI Insights:
• Design complexity: Low
• Component diversity: 7 different types

💡 Recommendations:
• Consider component placement optimization
• Review power supply decoupling
• Check signal integrity for high-speed signals
```

**📚 Full Documentation**: See [kicad_plugins/README.md](kicad_plugins/README.md) for complete installation and usage instructions.

## Installation

### Prerequisites

**KiCad Installation Required:**
Circuit-synth requires KiCad 8.0+ to be installed locally for full functionality.

```bash
# macOS
brew install kicad
# or download from: https://www.kicad.org/download/macos/

# Ubuntu/Debian  
sudo apt install kicad

# Fedora
sudo dnf install kicad

# Windows
# Download from: https://www.kicad.org/download/windows/
```

### Circuit-Synth Installation

**PyPI (Recommended):**
```bash
pip install circuit-synth
# or: uv pip install circuit-synth

# Verify installation
python -c "import circuit_synth; circuit_synth.validate_kicad_installation()"
```

**Development:**
```bash
git clone https://github.com/circuit-synth/circuit-synth.git
cd circuit-synth
uv sync  # or: pip install -e ".[dev]"

# Register AI agents for circuit design assistance
uv run register-agents
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
uv run python stm32_imu_usbc_demo_hierarchical.py  # Test hierarchical design
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- Documentation: [https://circuit-synth.readthedocs.io](https://circuit-synth.readthedocs.io)
- Issues: [GitHub Issues](https://github.com/circuit-synth/circuit-synth/issues)
- Discussions: [GitHub Discussions](https://github.com/circuit-synth/circuit-synth/discussions)
