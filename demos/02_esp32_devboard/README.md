# ESP32-C6 Development Board Demo

This demonstrates circuit-synth's hierarchical design capabilities with a complete, manufacturable ESP32-C6 development board.

## What This Demonstrates

1. **Hierarchical Circuit Organization**
   - Main circuit orchestrates 4 subcircuits
   - Each subcircuit handles a specific function
   - Clean interfaces between modules

2. **Professional Schematic Output**
   - Multi-sheet hierarchical design
   - Proper net naming and organization
   - Manufacturing-ready documentation

3. **Real Component Integration**
   - ESP32-C6-MINI-1 module (JLCPCB available)
   - USB-C connector with proper CC resistors
   - AMS1117-3.3 regulator (industry standard)
   - ESD protection and filtering

## Circuit Architecture

```
Main Circuit (ESP32_C6_Dev_Board.kicad_sch)
├── USB Port (USB_Port.kicad_sch)
│   ├── USB-C receptacle
│   ├── CC pull-down resistors (5.1k)
│   └── ESD protection
├── Power Supply (Power_Supply.kicad_sch) 
│   ├── AMS1117-3.3 regulator
│   ├── Input/output filtering
│   └── Power LED indicator
├── ESP32-C6 MCU (ESP32_C6_MCU.kicad_sch)
│   ├── ESP32-C6-MINI-1 module
│   ├── Reset circuitry
│   ├── Boot mode selection
│   └── USB D+/D- connections
└── Debug Header (Debug_Header.kicad_sch)
    ├── SWD programming interface
    ├── UART debug pins
    └── GPIO breakout
```

## Files Generated

- `ESP32_C6_Dev_Board.kicad_pro` - KiCad project
- `ESP32_C6_Dev_Board.kicad_sch` - Top-level schematic  
- `USB_Port.kicad_sch` - USB-C interface
- `Power_Supply.kicad_sch` - Power regulation
- `ESP32_C6_MCU.kicad_sch` - Microcontroller
- `Debug_Header.kicad_sch` - Programming interface
- `ESP32_C6_Dev_Board.kicad_pcb` - PCB layout
- `ESP32_C6_Dev_Board.net` - Netlist

## To Run

```bash
cd demos/02_esp32_devboard/
python main.py
```

Open the generated `ESP32_C6_Dev_Board.kicad_pro` in KiCad to explore the hierarchical schematic sheets.