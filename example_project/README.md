# ESP32-S3 Development Board Example

A complete ESP32-S3 development board demonstrating circuit-synth capabilities. This example shows how to create a functional development board with USB-C connectivity, power regulation, and status indicators.

## Structure

- `circuit-synth/` - Python circuit-synth code
  - `main.py` - Complete ESP32-S3 development board design
- `kicad_project/` - Generated KiCad files
- `README.md` - This file
- `CLAUDE.md` - Claude-specific instructions
- `.claude/` - Claude configuration

## Usage

```bash
cd circuit-synth
python main.py
```

## Features

- **ESP32-S3 Microcontroller**: WiFi + Bluetooth with dual-core processor
- **USB-C Connector**: Modern power and programming interface
- **3.3V Power Regulation**: AMS1117-3.3 linear regulator from 5V USB
- **Status LEDs**: Power indicator (red) and user-controllable (blue)
- **Reset Circuit**: Push button with proper pull-up resistor
- **Decoupling**: Multiple capacitors for clean power delivery
- **Test Points**: Debug access for 5V, 3.3V, and GND
- **Professional Layout**: Proper component selection and connections

## Components Used

- ESP32-S3-MINI-1 module
- USB-C receptacle connector
- AMS1117-3.3 voltage regulator
- Filtering capacitors (10µF, 22µF, 100nF)
- Status LEDs with current limiting resistors
- Reset button and pull-up resistor
- Test points for debugging

## Generated Files

After running `main.py`, you'll get:

- `ESP32_S3_Dev_Board.kicad_pro` - KiCad project file
- `ESP32_S3_Dev_Board.kicad_sch` - Schematic layout
- `ESP32_S3_Dev_Board.kicad_pcb` - PCB layout (empty, ready for routing)
- `ESP32_S3_Dev_Board.net` - Text netlist
- `ESP32_S3_Dev_Board.json` - JSON netlist

## Design Notes

This development board is designed for:
- Rapid prototyping with ESP32-S3
- WiFi and Bluetooth projects
- Learning circuit-synth fundamentals
- Understanding professional PCB design practices

The design includes proper power filtering, ESD protection considerations, and follows industry best practices for development board layout.