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

Automatic engineering documentation that tracks decisions across sessions:

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