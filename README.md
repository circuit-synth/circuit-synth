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

# 5. Optional: Setup KiCad plugins for AI integration
uv run cs-setup-kicad-plugins
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

# 4. Optional: Setup KiCad plugins
cs-setup-kicad-plugins
```

**Result:** Complete KiCad project setup with circuit-synth Python files and AI agents ready! (KiCad plugins available separately)

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

## 🏗️ Hierarchical Circuit Design

**Professional modular architecture following software engineering principles**

Circuit-synth now generates circuits as **hierarchical subcircuits** - each subcircuit is like a software function with single responsibility, clear interfaces, and modular design.

### ESP32-C6 Development Board - Modular Design

**Each subcircuit in its own file with clear interfaces - no global nets!**

#### `usb_subcircuit.py` - USB-C Port
```python
from circuit_synth import *

@circuit(name="USB_Port")
def usb_port_subcircuit():
    """USB-C port with CC resistors and ESD protection"""
    
    # Clear interface - all nets defined here
    vbus_out = Net('VBUS_OUT')
    gnd = Net('GND')
    usb_dp = Net('USB_DP')
    usb_dm = Net('USB_DM')
    
    # USB-C connector with proper CC resistors
    usb_conn = Component(
        symbol="Connector:USB_C_Receptacle_USB2.0_16P",
        ref="J",
        footprint="Connector_USB:USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal"
    )
    
    # CC pull-down resistors (5.1k for device mode)
    cc1_resistor = Component(symbol="Device:R", ref="R", value="5.1k",
                            footprint="Resistor_SMD:R_0603_1608Metric")
    
    # ESD protection for data lines
    esd_dp = Component(symbol="Diode:ESD5Zxx", ref="D",
                      footprint="Diode_SMD:D_SOD-523")
    
    # Connections - single responsibility
    usb_conn["VBUS"] += vbus_out
    usb_conn["CC1"] += cc1_resistor[1]
    cc1_resistor[2] += gnd
    # ... complete USB-C implementation
```

#### `power_supply_subcircuit.py` - Clean Power Regulation
```python
from circuit_synth import *

@circuit(name="Power_Supply")
def power_supply_subcircuit():
    """5V to 3.3V power regulation - single responsibility"""
    
    # Interface nets - no globals
    vbus_in = Net('VBUS_IN')
    vcc_3v3_out = Net('VCC_3V3_OUT') 
    gnd = Net('GND')
    
    # Simple, focused power regulation
    regulator = Component(
        symbol="Regulator_Linear:AMS1117-3.3", 
        ref="U",
        footprint="Package_TO_SOT_SMD:SOT-223-3_TabPin2"
    )
    
    # Input/output filtering
    cap_in = Component(symbol="Device:C", ref="C", value="10uF", 
                      footprint="Capacitor_SMD:C_0805_2012Metric")
    cap_out = Component(symbol="Device:C", ref="C", value="22uF",
                       footprint="Capacitor_SMD:C_0805_2012Metric")
    
    # Clean connections - one purpose
    regulator["VI"] += vbus_in
    regulator["VO"] += vcc_3v3_out
    regulator["GND"] += gnd
    # ... complete regulation circuit
```

#### `main.py` - Orchestrates All Subcircuits
```python
from circuit_synth import *

# Import modular subcircuits
from usb_subcircuit import usb_port_subcircuit
from power_supply_subcircuit import power_supply_subcircuit
from debug_header_subcircuit import debug_header_subcircuit
from led_blinker_subcircuit import led_blinker_subcircuit

@circuit(name="ESP32_C6_Dev_Board_Main")
def main_circuit():
    """Main circuit orchestrating all modular subcircuits"""
    
    # Create all subcircuits (each manages its own nets)
    usb_port = usb_port_subcircuit()
    power_supply = power_supply_subcircuit()
    debug_header = debug_header_subcircuit()
    led_blinker = led_blinker_subcircuit()
    
    # Add ESP32-C6 with explicit connections
    esp32_c6 = Component(
        symbol="RF_Module:ESP32-C6-MINI-1",
        ref="U", 
        footprint="RF_Module:ESP32-C6-MINI-1"
    )
    
    # Explicit net management - know where every connection comes from
    vcc_3v3 = Net('VCC_3V3')
    gnd = Net('GND')
    
    # Clear, explicit connections
    esp32_c6["3V3"] += vcc_3v3
    esp32_c6["GND"] += gnd
    esp32_c6["IO18"] += Net('USB_DP')
    esp32_c6["IO8"] += Net('LED_CONTROL')

# Generate complete project
if __name__ == "__main__":
    circuit = main_circuit()
    circuit.generate_kicad_project(
        project_name="ESP32_C6_Dev_Board",
        placement_algorithm="hierarchical",
        generate_pcb=True
    )
```

### Hierarchical Design Benefits

- **🔧 Single Responsibility**: Each subcircuit has one clear purpose (USB port, power supply, debug interface)
- **🔗 Explicit Interfaces**: No global nets - all connections are explicit and traceable  
- **🔄 Maintainability**: Modify subcircuits independently without affecting others
- **📦 Reusability**: Subcircuits work across multiple ESP32/MCU projects
- **📁 File-per-Function**: Each subcircuit lives in its own file - like software modules
- **👥 Team Development**: Multiple developers can work on different subcircuits simultaneously
- **🏭 Professional Output**: Industry-standard hierarchical KiCad projects ready for manufacturing

### Modular Design Philosophy

**Requirements** → **Modular Subcircuits** → **Explicit Interfaces** → **KiCad Hierarchical Project**

1. **Single Responsibility**: Each subcircuit file handles one function (USB, power, debug, LED)
2. **No Global Nets**: Every net is explicitly defined - no hidden dependencies
3. **Clear Interfaces**: Know exactly where every connection comes from and goes to
4. **Decoupled Design**: Modify any subcircuit without affecting others
5. **Software Best Practices**: Treat circuits like software modules with clean APIs

### Generated KiCad Files

```
my_esp32_project/
├── circuit-synth/                          # Modular circuit-synth files  
│   ├── main.py                             # Main orchestration - connects all subcircuits
│   ├── usb_subcircuit.py                   # USB-C port with CC resistors & ESD
│   ├── power_supply_subcircuit.py          # 5V to 3.3V regulation (single purpose)
│   ├── debug_header_subcircuit.py          # Programming interface (isolated)
│   ├── led_blinker_subcircuit.py          # Status LED control (decoupled)
│   ├── simple_led.py                       # Tutorial examples
│   └── voltage_divider.py                  # Learning examples
├── .claude/                                # AI agents and commands
├── ESP32_C6_Dev_Board/                     # Generated KiCad project
│   ├── ESP32_C6_Dev_Board.kicad_pro        # Main project
│   ├── ESP32_C6_Dev_Board.kicad_sch        # Top-level schematic  
│   ├── ESP32_C6_Dev_Board.kicad_pcb        # PCB layout
│   ├── ESP32_C6_Dev_Board.net              # Netlist for ratsnest display
│   ├── ESP32_C6_Dev_Board.json             # JSON netlist for analysis
│   ├── USB_Port.kicad_sch                  # USB subcircuit sheet
│   ├── Power_Supply.kicad_sch              # Power subcircuit sheet  
│   ├── Debug_Header.kicad_sch              # Debug subcircuit sheet
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
# Automatic installation (recommended)
uv run cs-setup-kicad-plugins

# Manual installation instructions
uv run cs-setup-kicad-plugins --manual

# System-wide installation (requires admin privileges)
uv run cs-setup-kicad-plugins --system
```

**Note**: KiCad plugins are **optional** and installed separately from project creation. Use `cs-new-project` to create minimal projects, then add KiCad integration only when needed.

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
