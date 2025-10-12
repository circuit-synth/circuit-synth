# circuit-synth Project

A professional circuit design project using circuit-synth with hierarchical architecture.

## 🚀 Quick Start

```bash
# Generate KiCad project from Python code
uv run python circuit-synth/main.py

# Open in KiCad
open kicad-project/ESP32_C6_Dev_Board.kicad_pro
```

That's it! You now have a complete ESP32-C6 development board with schematic and PCB.

## 📁 Project Structure

```
my_kicad_project/
├── circuit-synth/        # Circuit-synth Python files
│   ├── main.py           # Main circuit (nets and subcircuits)
│   ├── usb_subcircuit.py # USB-C circuit
│   ├── power_supply_subcircuit.py # Power regulation
│   ├── debug_header_subcircuit.py # Programming interface
│   ├── led_blinker_subcircuit.py  # Status LED
│   └── esp32_subcircuit.py        # ESP32-C6 MCU
├── kicad-project/        # Generated KiCad files
│   ├── ESP32_C6_Dev_Board.kicad_pro  # KiCad project
│   ├── ESP32_C6_Dev_Board.kicad_sch  # Main schematic
│   ├── ESP32_C6_Dev_Board.kicad_pcb  # PCB layout
│   └── [subcircuit sheets]           # Hierarchical sheets
├── README.md            # This file
└── CLAUDE.md            # AI assistant guide
```

## 🏗️ Circuit-Synth Basics

### Hierarchical Design

Circuit-synth uses **hierarchical subcircuits** - each subcircuit is a self-contained module:

```python
from circuit_synth import *

@circuit(name="Power_Supply")
def power_supply_subcircuit(vbus_in, vcc_3v3_out, gnd):
    """5V to 3.3V power regulation"""

    # Create components
    regulator = Component(
        symbol="Regulator_Linear:AMS1117-3.3",
        ref="U",
        footprint="Package_TO_SOT_SMD:SOT-223-3_TabPin2"
    )

    cap_in = Component(
        symbol="Device:C",
        ref="C",
        value="10uF",
        footprint="Capacitor_SMD:C_0805_2012Metric"
    )

    # Connect components
    regulator["VI"] += vbus_in
    regulator["VO"] += vcc_3v3_out
    regulator["GND"] += gnd

    cap_in[1] += vbus_in
    cap_in[2] += gnd

@circuit(name="Main_Circuit")
def main_circuit():
    """Main circuit - only nets and subcircuit connections"""

    # Define shared nets
    vbus = Net('VBUS')
    vcc_3v3 = Net('VCC_3V3')
    gnd = Net('GND')

    # Connect subcircuits
    power = power_supply_subcircuit(vbus, vcc_3v3, gnd)

# Generate KiCad project
if __name__ == "__main__":
    circuit = main_circuit()
    circuit.generate_kicad_project(
        project_name="my_design",
        placement_algorithm="hierarchical",
        generate_pcb=True
    )
```

### Component Creation

```python
# Create components with KiCad symbol and footprint
mcu = Component(
    symbol="RF_Module:ESP32-C6-MINI-1",  # KiCad symbol library:name
    ref="U",                              # Reference prefix (U, R, C, etc.)
    footprint="RF_Module:ESP32-C6-MINI-1" # KiCad footprint library:name
)

# Passive components with values
resistor = Component(
    symbol="Device:R",
    ref="R",
    value="330",
    footprint="Resistor_SMD:R_0805_2012Metric"
)
```

### Net Connections

```python
# Create nets
vcc = Net("VCC_3V3")
gnd = Net("GND")

# Connect to named pins
mcu["VDD"] += vcc
mcu["VSS"] += gnd

# Connect to numbered pins
resistor[1] += vcc
resistor[2] += gnd
```

### Generate KiCad Output

```python
# Generate complete KiCad project with PCB
circuit = my_circuit()
circuit.generate_kicad_project(
    project_name="my_design",
    placement_algorithm="hierarchical",  # Professional hierarchical layout
    generate_pcb=True                    # Include PCB file
)
```

## 🛠️ Development Workflow

1. **Design**: Create or modify circuits in Python files
2. **Generate**: Run `uv run python circuit-synth/main.py`
3. **Verify**: Open KiCad project and check schematic
4. **Iterate**: Make changes and regenerate

## 🔍 Finding Components

If you need to find KiCad symbols or footprints, you can:

**Using Claude Code (recommended):**
```
Ask: "Find me a KiCad symbol for STM32F411"
Ask: "What footprint should I use for LQFP-48?"
```

**Manual search:**
```bash
# Search for symbols
find /usr/share/kicad/symbols -name "*.kicad_sym" | xargs grep -l "STM32"

# Search for footprints
find /usr/share/kicad/footprints -name "*.kicad_mod" | grep -i lqfp
```

## 📦 Working Component Library

These components are proven to work well:

### Microcontrollers:
- **ESP32-C6**: `RF_Module:ESP32-C6-MINI-1`
- **STM32F4**: `MCU_ST_STM32F4:STM32F411CEUx` / `Package_QFP:LQFP-48_7x7mm_P0.5mm`

### Power Components:
- **Linear Reg**: `Regulator_Linear:AMS1117-3.3` / `Package_TO_SOT_SMD:SOT-223-3_TabPin2`

### Passives:
- **Resistor**: `Device:R` / `Resistor_SMD:R_0603_1608Metric`
- **Capacitor**: `Device:C` / `Capacitor_SMD:C_0603_1608Metric`
- **LED**: `Device:LED` / `LED_SMD:LED_0603_1608Metric`

### Connectors:
- **USB-C**: `Connector:USB_C_Receptacle_USB2.0_16P`
- **Headers**: `Connector_Generic:Conn_01x10_Pin`

## 📚 Resources

- **Circuit-Synth Docs**: https://circuit-synth.readthedocs.io
- **KiCad Docs**: https://docs.kicad.org
- **Ask Claude Code**: Get help with component selection, circuit design, and troubleshooting

## 🚀 Next Steps

1. Explore the example circuits in `circuit-synth/`
2. Modify `main.py` to customize your design
3. Run `uv run python circuit-synth/main.py` to regenerate
4. Open KiCad to view and edit your schematic and PCB

**Happy circuit designing!** 🎛️
