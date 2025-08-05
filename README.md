# circuit-synth

**Python-based circuit design with KiCad integration and AI acceleration.**

Generate professional KiCad projects from Python code with hierarchical design, version control, and automated documentation.

## 🚀 Getting Started

```bash
# Install uv (if not already installed)  
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create new project
uv init my_circuit_project
cd my_circuit_project

# Add circuit-synth
uv add circuit-synth

# Setup complete project template
uv run cs-new-pcb

# Generate complete KiCad project  
uv run python circuit-synth/main.py
```

This creates an ESP32-C6 development board with USB-C, power regulation, programming interface, and status LED.

## 💡 Quick Example

```python
from circuit_synth import *

@circuit(name="Power_Supply")
def usb_to_3v3():
    """USB-C to 3.3V regulation"""
    
    # Define nets
    vbus_in = Net('VBUS_IN')
    vcc_3v3_out = Net('VCC_3V3_OUT') 
    gnd = Net('GND')
    
    # Components with KiCad integration
    regulator = Component(
        symbol="Regulator_Linear:AMS1117-3.3", 
        ref="U",
        footprint="Package_TO_SOT_SMD:SOT-223-3_TabPin2"
    )
    
    cap_in = Component(symbol="Device:C", ref="C", value="10uF")
    cap_out = Component(symbol="Device:C", ref="C", value="22uF")
    
    # Explicit connections
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

## 🔧 Core Features

- **Professional KiCad Output**: Generate .kicad_pro, .kicad_sch, .kicad_pcb files
- **Hierarchical Design**: Modular subcircuits like software modules  
- **Component Intelligence**: JLCPCB integration, symbol/footprint verification
- **AI Integration**: Claude Code agents for automated design assistance
- **Version Control Friendly**: Git-trackable Python files vs binary KiCad files

## 🤖 AI-Powered Design

Work with Claude Code to describe circuits and get production-ready results:

```bash
# AI agent commands (with Claude Code)
/find-symbol STM32                    # Search KiCad symbols
/find-footprint LQFP64                # Find footprints  
/generate-validated-circuit "ESP32 IoT sensor" mcu
```

## 📋 Project Structure

```
my_circuit_project/
├── circuit-synth/
│   ├── main.py              # Main circuit definition
│   ├── power_supply.py      # Modular subcircuits
│   ├── usb.py
│   └── esp32c6.py
├── MyProject/               # Generated KiCad files
│   ├── MyProject.kicad_pro
│   ├── MyProject.kicad_sch
│   └── MyProject.kicad_pcb
├── memory-bank/             # Auto-documentation
└── .claude/                 # AI agent config
```

## ⚡ Performance (Optional)

Circuit-synth includes optional Rust acceleration modules. The package works perfectly without them using Python fallbacks.

**To enable Rust acceleration:**

```bash
# For developers who want maximum performance
pip install maturin
./scripts/build_rust_modules.sh
```

## 🚀 Commands

```bash
# Project creation
cs-new-project              # Complete project setup
cs-new-pcb "Board Name"     # PCB-focused project

# Development  
cd circuit-synth && uv run python main.py    # Generate KiCad files
```

## 🏭 Why Circuit-Synth?

| Traditional EE Workflow | With Circuit-Synth |
|-------------------------|-------------------|
| Manual component placement | `python main.py` → Complete project |
| Hunt through symbol libraries | Verified components with JLCPCB availability |
| Visual net verification | Explicit Python connections |
| Binary KiCad files | Git-friendly Python source |
| Documentation drift | Automated engineering docs |

## 📚 Learn More

- **Website**: [circuit-synth.com](https://www.circuit-synth.com)
- **Documentation**: [docs.circuit-synth.com](https://circuit-synth.readthedocs.io/en/latest/)
- **Examples**: [github.com/circuit-synth/examples](https://github.com/circuit-synth/examples)

## 🤝 Contributing

See [Contributors.md](Contributors.md) for development setup and guidelines.

---

⚡ **Professional PCB Design, Programmatically** ⚡
