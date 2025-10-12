# Circuit-Synth Project

Professional PCB design with Python and AI assistance.

## 🚀 Quick Start

```bash
# Generate KiCad project from Python code
uv run python main.py

# Open in KiCad
open output/circuit.kicad_pro
```

## 📁 Project Structure

```
my_project/
├── main.py            # Your circuit design
├── output/            # Generated KiCad files
├── memory-bank/       # Automatic documentation
├── .claude/           # AI assistant configuration
├── CLAUDE.md          # Development guide
└── README.md          # This file
```

## 🏗️ Basic Circuit Example

```python
from circuit_synth import Component, Net, circuit

@circuit(name="MyCircuit")
def my_circuit():
    """Simple LED circuit"""

    # Create components
    led = Component(
        symbol="Device:LED",
        ref="D",
        value="RED",
        footprint="LED_SMD:LED_0603_1608Metric"
    )

    resistor = Component(
        symbol="Device:R",
        ref="R",
        value="330",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )

    # Create nets
    vcc = Net('VCC_3V3')
    gnd = Net('GND')

    # Connect components
    resistor[1] += vcc
    resistor[2] += led[1]
    led[2] += gnd

# Generate KiCad project
if __name__ == "__main__":
    circuit = my_circuit()
    circuit.generate_kicad_project(
        project_name="output",
        generate_pcb=True
    )
    print("✅ KiCad project generated!")
```

## 🔧 Development Workflow

1. **Edit** your circuit in `main.py`
2. **Run** `uv run python main.py` to generate KiCad files
3. **Open** in KiCad to view and edit
4. **Iterate** - make changes and regenerate as needed

## 📦 Common Components

### Microcontrollers:
- **ESP32-C6**: `RF_Module:ESP32-C6-MINI-1`
- **STM32F4**: `MCU_ST_STM32F4:STM32F411CEUx`

### Power:
- **3.3V Regulator**: `Regulator_Linear:AMS1117-3.3`

### Passives:
- **Resistor**: `Device:R`
- **Capacitor**: `Device:C`
- **LED**: `Device:LED`

### Connectors:
- **USB-C**: `Connector:USB_C_Receptacle_USB2.0_16P`
- **Headers**: `Connector_Generic:Conn_01x10_Pin`

## 🤖 AI Assistance

Ask Claude Code for help with:
- Finding KiCad symbols and footprints
- Component selection and JLCPCB availability
- Circuit design guidance
- Troubleshooting

## 📚 Resources

- **Circuit-Synth Docs**: https://circuit-synth.readthedocs.io
- **KiCad Docs**: https://docs.kicad.org

## 🚀 Next Steps

1. Modify `main.py` with your circuit design
2. Run `uv run python main.py` to generate KiCad files
3. Open the generated KiCad project
4. Edit PCB layout and export manufacturing files

Built with [circuit-synth](https://github.com/circuit-synth/circuit-synth) 🚀
