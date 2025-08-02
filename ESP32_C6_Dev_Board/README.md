# ESP32_C6_Dev_Board

A circuit-synth project converted from an existing KiCad design.

## 🚀 Quick Start

```bash
# Run the converted circuit
uv run python circuit-synth/main.py

# Test circuit-synth is working
uv run python -c "from circuit_synth import *; print('✅ Circuit-synth ready!')"
```

## 📁 Project Structure

```
ESP32_C6_Dev_Board/
├── circuit-synth/        # Circuit-synth Python files
│   └── main.py           # Main circuit (converted from KiCad)
├── *.kicad_pro          # Original KiCad project file
├── *.kicad_sch          # Original KiCad schematic  
├── *.kicad_pcb          # Original KiCad PCB (if present)
├── .claude/             # AI agents for Claude Code
│   ├── agents/          # Specialized circuit design agents
│   └── commands/        # Slash commands
├── README.md           # This file
└── CLAUDE.md           # Project-specific Claude guidance
```

## 🔄 Next Steps

1. **Review the generated code** in `circuit-synth/main.py`
2. **Update component symbols and footprints** as needed
3. **Verify net connections** match your original design
4. **Test the circuit generation** with `uv run python circuit-synth/main.py`
5. **Use Claude Code agents** for AI-assisted improvements

## 🤖 AI-Powered Design

This project includes specialized AI agents:
- **circuit-synth**: Circuit code generation and KiCad integration
- **simulation-expert**: SPICE simulation and validation  
- **jlc-parts-finder**: JLCPCB component sourcing
- **orchestrator**: Master coordinator for complex projects

Use natural language to improve your design:
```
👤 "Optimize this power supply for better efficiency"
👤 "Add protection circuits to prevent overcurrent"  
👤 "Find alternative components available on JLCPCB"
```

## 📖 Documentation

- Circuit-Synth: https://circuit-synth.readthedocs.io
- KiCad: https://docs.kicad.org

**Happy circuit designing!** 🎛️
