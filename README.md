# circuit-synth

[![Documentation](https://readthedocs.org/projects/circuit-synth/badge/?version=latest)](https://circuit-synth.readthedocs.io/en/latest/?badge=latest)
[![PyPI version](https://badge.fury.io/py/circuit-synth.svg)](https://badge.fury.io/py/circuit-synth)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Enhance your traditional EE workflow with Python-based circuit design, software engineering practices, and optional AI acceleration.**

Circuit-synth eliminates tedious component placement, symbol hunting, and manual netlist verification while adding hierarchical design, version control, and automated simulation. Use it for specific pain points or go full-automation with Claude Code integration—it fits transparently into any workflow.

## 🚀 Getting Started

### Quick Setup (uv - Recommended)

#### New Projects
```bash
# 1. Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Create new project
uv init my_circuit_project
cd my_circuit_project

# 3. Add circuit-synth
uv add circuit-synth

# 4. Setup project template
uv run cs-new-project

# 5. Run the ESP32-C6 example
uv run python circuit-synth/main.py
```

#### Existing KiCad Projects
```bash
# Convert existing KiCad project to circuit-synth
uv add circuit-synth
uv run cs-init-existing-project /path/to/my_board.kicad_pro

# Or from directory containing KiCad files
uv run cs-init-existing-project /path/to/project_directory/

# Test the converted circuit
uv run python circuit-synth/main.py
```

**Result:** Complete project template with modular ESP32-C6 example, hierarchical subcircuits, and AI agents ready!

### 📋 **Generated Project Structure**

The `cs-new-project` command creates a complete working template:

```
my_circuit_project/
├── circuit-synth/              # Modular Python circuits
│   ├── main.py                 # ESP32-C6 dev board (hierarchical)
│   ├── usb_subcircuit.py       # USB-C with CC resistors
│   ├── power_supply_subcircuit.py  # 5V→3.3V regulation  
│   ├── debug_header_subcircuit.py  # Programming interface
│   ├── led_blinker_subcircuit.py   # Status LED control
│   ├── simple_led.py           # Basic LED example
│   └── voltage_divider.py      # Tutorial circuit
├── .claude/                    # AI agents & commands (optional)
├── README.md                   # Project guide
└── CLAUDE.md                   # AI assistant instructions
```

## 💡 Quick Example

**Before**: Hunt through KiCad libraries, manually place components, visual net verification  
**After**: Define circuits in Python with clear interfaces

```python
from circuit_synth import *

@circuit(name="Power_Supply")
def usb_to_3v3():
    """USB-C to 3.3V regulation with overcurrent protection"""
    
    # Interface nets - explicit and traceable
    vbus_in = Net('VBUS_IN')
    vcc_3v3_out = Net('VCC_3V3_OUT') 
    gnd = Net('GND')
    
    # Components with verified symbols/footprints
    regulator = Component(
        symbol="Regulator_Linear:AMS1117-3.3", 
        ref="U",
        footprint="Package_TO_SOT_SMD:SOT-223-3_TabPin2"
    )
    
    # Input and output bulk capacitors for stability
    cap_in = Component(
        symbol="Device:C", 
        ref="C", 
        value="10uF",
        rating="15V",
        footprint="Capacitor_SMD:C_0805_2012Metric"
    )
    cap_out = Component(
        symbol="Device:C", 
        ref="C", 
        value="22uF",
        rating="10V",
        footprint="Capacitor_SMD:C_0805_2012Metric"
    )
    
    # Clear, safe connections
    regulator["VI"] += vbus_in
    regulator["VO"] += vcc_3v3_out
    regulator["GND"] += gnd
    
    # Capacitor connections
    cap_in[1] += vbus_in
    cap_in[2] += gnd
    cap_out[1] += vcc_3v3_out
    cap_out[2] += gnd

# Generate complete KiCad project
circuit = usb_to_3v3()
circuit.generate_kicad_project("power_supply")
```

**→ See complete ESP32-C6 development board with hierarchical subcircuits in `example_project/`**

## 🔧 Key Features

### **🔄 Bidirectional KiCad Integration**
- **Export**: Generate professional KiCad projects with hierarchical sheets
- **Import**: Read existing KiCad projects back into Python
- **Netlists**: Industry-standard .net files with proper connectivity

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

## 🎨 Advanced Features

### **KiCad Plugin Integration**
Optional AI-powered plugins for KiCad integration:
```bash
# Install KiCad plugins (optional)
uv run cs-setup-kicad-plugins
```
- **PCB Editor**: Tools → External Plugins → "Circuit-Synth AI"  
- **Schematic Editor**: Tools → Generate BOM → "Circuit-Synth AI"

### **Manufacturing Integration**
- **JLCPCB**: Real-time component availability and pricing
- **Professional Output**: Industry-standard files ready for manufacturing
- **Assembly Optimization**: Component selection for automated assembly

### **Documentation as Code**
```python
@circuit(name="Amplifier")
def audio_amp():
    """
    Common-emitter amplifier stage.
    
    Gain: ~100dB, Input impedance: 1kΩ
    Power supply: 3.3V, Current: 2.5mA
    """
    # Implementation with automatic documentation
```

## 📚 Installation & Setup

### Prerequisites
**KiCad 8.0+ Required:**
```bash
# macOS
brew install kicad

# Ubuntu/Debian  
sudo apt install kicad

# Windows: Download from kicad.org
```

### Development Installation
```bash
git clone https://github.com/circuit-synth/circuit-synth.git
cd circuit-synth
uv sync

# Explore the generated project template
ls example_project/
uv run python example_project/circuit-synth/main.py
```

## 🔄 Converting Existing Projects

The `cs-init-existing-project` command adds circuit-synth functionality to your existing KiCad projects:

### What it does:
- **Organizes KiCad files** into a clean subdirectory structure
- **Generates Python code** from your existing schematic
- **Adds AI agents** for Claude Code integration
- **Creates documentation** and development setup
- **Preserves your original design** - no data loss

### Usage Examples:
```bash
# Direct KiCad project file
uv run cs-init-existing-project ~/projects/my_board.kicad_pro

# Directory containing KiCad files (auto-detects .kicad_pro)
uv run cs-init-existing-project ~/projects/esp32_project/

# Skip automatic conversion (create template only)
uv run cs-init-existing-project --skip-conversion ~/projects/my_board.kicad_pro
```

### Resulting Structure:
```
my_existing_project/
├── my_board/                    # Organized KiCad files
│   ├── my_board.kicad_pro      # Original project file
│   ├── my_board.kicad_sch      # Original schematic
│   └── my_board.kicad_pcb      # Original PCB (if present)
├── circuit-synth/              # Generated Python code
│   └── main.py                 # Converted circuit
├── .claude/                    # AI agents & commands
├── README.md                   # Project documentation
└── CLAUDE.md                   # AI assistant instructions
```

## 🤝 Contributing - Designed for Maximum Developer Productivity

**Circuit-synth is the most contributor-friendly EE design tool ever built!** We've designed every aspect to make development as smooth as possible.

### 🤖 Recommended Development Experience (Claude Code + GitHub MCP)

**Use [Claude Code](https://claude.ai/code) for the best development experience:**

```bash
# 1. Setup Claude Code (if not installed)
# Visit: https://claude.ai/code

# 2. Setup GitHub MCP Server (ultimate workflow)
# Follow: https://github.com/anthropics/mcp-servers/tree/main/src/github

# 3. Register our specialized agents
uv run register-agents
```

**Why Claude Code + GitHub MCP?**
- **Specialized Agents**: Deep circuit-synth knowledge built-in
- **Automated Development**: `/dev-review-branch`, `/find-symbol`, `/jlc-search` commands
- **GitHub Integration**: Create issues, review PRs, check CI status seamlessly
- **Architecture Guidance**: Understand our Python+Rust hybrid approach instantly
- **Test-Driven Development**: Built-in TDD workflow assistance

### 🚀 5-Minute Contributor Setup

```bash
# Clone and setup
git clone https://github.com/circuit-synth/circuit-synth.git
cd circuit-synth
uv sync

# Register AI agents (if using Claude Code)
uv run register-agents
# Now you have access to the 'contributor' agent for development help!

# Verify everything works
uv run python example_project/circuit-synth/main.py
./scripts/run_all_tests.sh --python-only
```

### 📚 Contributor Resources

**Start here for a great contribution experience:**

- **[Contributors/README.md](Contributors/README.md)** - Welcoming 5-minute setup guide
- **[Contributors/Getting-Started.md](Contributors/Getting-Started.md)** - Your first contribution walkthrough
- **[Contributors/detailed/](Contributors/detailed/)** - In-depth technical documentation
- **[CLAUDE.md](CLAUDE.md)** - Development commands and AI assistance

### 🎯 High-Impact Contribution Opportunities

**Rust Integration (Perfect for Major Impact):**
- **[Issue #36](https://github.com/circuit-synth/circuit-synth/issues/36)**: Netlist processor (HIGH PRIORITY)
- **[Issue #37](https://github.com/circuit-synth/circuit-synth/issues/37)**: KiCad integration compilation (HIGH PRIORITY)
- **[Issue #40](https://github.com/circuit-synth/circuit-synth/issues/40)**: Component processing (97% performance impact!)

**Easy Entry Points:**
- Examples and tutorials for other EEs
- Component library expansion  
- Test coverage improvements
- Documentation enhancements

### 🤖 Alternative AI Tools Welcome

While we optimize for Claude Code, other AI tools work great too:
- **ChatGPT/GPT-4**: Read our `Contributors/` docs for context
- **Cursor/GitHub Copilot**: Excellent code completion with our patterns
- **Any LLM**: Extensive documentation designed for AI agent consumption

### 💡 Our Development Philosophy

- **Infrastructure for AI/LLM development** - Make this library easy for agents to use
- **Test-driven everything** - Every feature has comprehensive tests
- **Simple Python + Fast Rust** - Best of both worlds
- **EE workflow integration** - Enhance existing processes, don't replace them

**Traditional Python Installation:**
For pip-based workflows, see [installation docs](https://circuit-synth.readthedocs.io/en/latest/installation.html).

## 📖 Support

- **Documentation**: [circuit-synth.readthedocs.io](https://circuit-synth.readthedocs.io)
- **Issues**: [GitHub Issues](https://github.com/circuit-synth/circuit-synth/issues)
- **Discussions**: [GitHub Discussions](https://github.com/circuit-synth/circuit-synth/discussions)

---

**Transform your circuit design workflow with software engineering best practices and optional AI acceleration.** 🎛️