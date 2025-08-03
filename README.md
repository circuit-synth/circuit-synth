# circuit-synth

**Python-based circuit design with KiCad integration and AI acceleration.**

Generate professional KiCad projects from Python code with hierarchical design, version control, and automated documentation.

## 🚀 Getting Started

```bash
# Install circuit-synth
uv tool install circuit-synth

# Create new PCB project
uv run cs-new-pcb "ESP32 Sensor Board"
cd esp32-sensor-board/circuit-synth && uv run python main.py

# Or add to existing KiCad project
uv run cs-init-pcb existing_kicad_project_dir
```

## 📋 Project Structure

```
esp32-sensor-board/
├── circuit-synth/main.py       # Python circuit definition
├── kicad/                      # Generated KiCad files
├── memory-bank/                # AI documentation system
│   ├── decisions.md            # Design rationale
│   ├── fabrication.md          # PCB notes
│   └── testing.md              # Validation results
└── .claude/                    # AI assistant config
```

## 💡 Example

```python
from circuit_synth import *

@circuit(name="Power_Supply")
def usb_to_3v3():
    """USB-C to 3.3V regulation"""
    
    # Define nets
    vbus_in = Net('VBUS_IN')
    vcc_3v3_out = Net('VCC_3V3_OUT') 
    gnd = Net('GND')
    
    # Components
    regulator = Component(
        symbol="Regulator_Linear:AMS1117-3.3", 
        ref="U",
        footprint="Package_TO_SOT_SMD:SOT-223-3_TabPin2"
    )
    
    cap_in = Component(symbol="Device:C", ref="C", value="10uF")
    cap_out = Component(symbol="Device:C", ref="C", value="22uF")
    
    # Connections
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

## 🔧 Features

- **KiCad Integration**: Generate professional .kicad_pro, .kicad_sch, .kicad_pcb files
- **Hierarchical Design**: Modular subcircuits like software modules  
- **Component Intelligence**: JLCPCB integration, symbol/footprint verification
- **AI Acceleration**: Claude Code integration for automated design
- **Version Control**: Git-friendly Python files vs binary KiCad

## 🧠 Memory-Bank System - AI Documentation

<<<<<<< HEAD
### **🏗️ Hierarchical Design**
- **Modular Subcircuits**: Each function in its own file (like software modules)
- **Clear Interfaces**: Explicit net definitions - no hidden dependencies
- **Reusable Circuits**: USB ports, power supplies, debug interfaces work across projects
- **Version Control**: Git-friendly Python files vs binary KiCad files

### **🤖 Optional AI Acceleration with Built-in Quality Assurance**
**Work with Claude Code to describe circuits and get production-ready, validated results:**

```
👤 "Design ESP32 IoT sensor with LoRaWAN, solar charging, and environmental sensors"

🤖 Claude (using circuit-synth):
   ✅ Searches components with JLCPCB availability
   ✅ Generates hierarchical Python circuits
   ✅ Validates syntax, imports, and runtime execution
   ✅ Auto-fixes common issues and provides quality reports
   ✅ Creates complete KiCad project with proper sheets
   ✅ Includes simulation validation and alternatives
```

**AI agents with built-in validation double-check everything and eliminate manual work - but it's completely optional.**

### **🔍 Component Intelligence**
- **Smart Search**: Find components by function, package, availability
- **JLCPCB Integration**: Real-time stock levels and pricing
- **Symbol/Footprint Verification**: No more "symbol not found" errors
- **Manufacturing Ready**: Components verified for automated assembly

### **✅ Built-in Circuit Validation**
- **Automatic Quality Assurance**: Validates syntax, imports, and runtime execution
- **Intelligent Auto-Fixing**: Automatically corrects common circuit code issues
- **Context-Aware Generation**: Provides design patterns and best practices
- **Professional Quality Reports**: Clear validation status and improvement suggestions

### **✅ Circuit Validation & Quality Assurance**
```python
from circuit_synth.validation import validate_and_improve_circuit, get_circuit_design_context

# Automatic validation and fixing
code, is_valid, status = validate_and_improve_circuit(circuit_code)
print(f"Validation: {status}")  # ✅ Circuit code validated successfully

# Context-aware generation assistance
context = get_circuit_design_context("esp32")  # Power, USB, analog contexts available
# Use context for better AI-generated circuits
```

**Claude Code Integration:**
```bash
# Generate validated circuits directly
/generate-validated-circuit "ESP32 with USB-C power" mcu

# Validate existing code
/validate-existing-circuit
```

### **⚙️ Automated SPICE Simulation**
```python
# One-click simulation setup
circuit = my_circuit()
sim = circuit.simulator()
result = sim.operating_point()
print(f"Output voltage: {result.get_voltage('VOUT'):.3f}V")
```

## 🧠 Memory-Bank Documentation System

Every PCB project includes an **automatic documentation system** that tracks your engineering decisions:
=======
Automatic engineering documentation that tracks decisions across sessions:
>>>>>>> 5e00046 (Remove non-existent commands and clean up configuration)

```bash
# AI agent automatically documents design decisions
git commit -m "Add voltage regulator"  # → Updates decisions.md, timeline.md
```

**Files automatically maintained:**
- `decisions.md` - Component choices and rationale
- `fabrication.md` - PCB notes and assembly
- `testing.md` - Validation results
- `timeline.md` - Development progress

## 🚀 Commands

<<<<<<< HEAD
## 🏭 Professional Workflow Benefits

| Traditional EE Workflow | With Circuit-Synth |
|-------------------------|-------------------|
| Manual component placement | `python main.py` → Complete project |
| Hunt through symbol libraries | Verified components with availability |
| Visual net verification | Explicit Python connections |
| Manual syntax/import checking | Automatic validation and fixing |
| Difficult design versioning | Git-friendly Python files |
| Manual SPICE netlist creation | One-line simulation setup |
| Copy-paste circuit blocks | Reusable subcircuit modules |
| Lost design knowledge | Automatic memory-bank documentation |
| Context switching overhead | `cs-switch-board` instant project switching |

## 🎨 Advanced Features

### **KiCad Plugin Integration**
Optional AI-powered plugins for KiCad integration:
=======
>>>>>>> 5e00046 (Remove non-existent commands and clean up configuration)
```bash
# PCB Projects
cs-new-pcb "My Sensor Board"           # Create new PCB project
cs-init-pcb /path/to/project           # Add to existing KiCad project

# Memory-Bank (AI agent uses extensively)
cs-memory-bank-init "My Project"      # Initialize if needed

# Development
cd circuit-synth && uv run python main.py  # Generate KiCad files
/find-symbol STM32                         # Search symbols (Claude Code)
/jlc-search "voltage regulator"            # Find JLCPCB parts (Claude Code)
```

### 🧠 Critical: AI Agent Memory-Bank Usage

**The AI agent MUST use memory-bank extensively for:**
1. **Planning**: Document requirements and constraints
2. **Implementation**: Record component choices and rationale
3. **Testing**: Track validation results
4. **Context**: Maintain persistent knowledge across sessions

## 🤝 Contributing

```bash
# Setup
git clone https://github.com/circuit-synth/circuit-synth.git
cd circuit-synth && uv sync

# Register AI agents (Claude Code)
uv run register-agents

# Test PCB workflow
cs-new-pcb "Test Board"
cd test-board/circuit-synth && uv run python main.py
```

**Resources:**
- [Contributors/README.md](Contributors/README.md) - Setup guide
- [CLAUDE.md](CLAUDE.md) - Development commands

## 📖 Support

- [Documentation](https://circuit-synth.readthedocs.io)
- [GitHub Issues](https://github.com/circuit-synth/circuit-synth/issues)