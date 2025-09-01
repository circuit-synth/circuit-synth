# SPICE Export for Circuit-Synth

## Overview

The ESP32-C6 example now includes automatic SPICE netlist generation for circuit simulation alongside KiCad output for PCB manufacturing.

## Usage

Run the main example:
```bash
cd circuit-synth
PYTHONPATH=src python example_project/circuit-synth/main.py
```

## Generated Files

The example generates both manufacturing and simulation outputs:

### Manufacturing (KiCad)
- `ESP32_C6_Dev_Board.kicad_pro` - KiCad project
- `ESP32_C6_Dev_Board.kicad_sch` - Hierarchical schematic
- `ESP32_C6_Dev_Board.kicad_pcb` - PCB layout
- `ESP32_C6_Dev_Board.net` - KiCad netlist

### Simulation (SPICE)
- `ESP32_C6_Dev_Board.cir` - SPICE netlist with behavioral models

## SPICE Models Included

The generated SPICE netlist includes professional behavioral models:

- **AMS1117-3.3**: Voltage regulator with dropout and thermal modeling
- **ESP32-C6**: Power consumption model (200mA active, 10µA sleep)
- **ESD Protection**: Diode models with breakdown characteristics
- **USB Connector**: Simplified model with CC resistors

## Example SPICE Netlist Structure

```spice
* ESP32_C6_Dev_Board_Main
.title ESP32_C6_Dev_Board_Main

* Components
XU1 VBUS 0 VCC_3V3 AMS1117_3V3
CC1 VBUS VCC_3V3 10uF
RR1 VCC_3V3 0 16.5  ; ESP32 load

* Behavioral Models
.SUBCKT AMS1117_3V3 VI GND VO
E1 VO GND VALUE={IF(V(VI,GND) > 4.0, 3.3, V(VI,GND)-1.2)}
.ENDS AMS1117_3V3

* Analysis
.DC VIN 3 6 0.1
.TRAN 0 10m 0 10u
.END
```

## Using the SPICE Netlist

The generated `.cir` file can be used with any SPICE simulator:

### ngspice
```bash
ngspice ESP32_C6_Dev_Board.cir
```

### LTspice
Import the `.cir` file directly into LTspice

### Circuit-Simulation Integration
```python
from circuit_sim.circuit_synth_integration import simulate_from_spice

with open("ESP32_C6_Dev_Board.cir", "r") as f:
    spice_netlist = f.read()
    
results = simulate_from_spice(spice_netlist, analysis_type="dc")
```

## Benefits

1. **Single Source of Truth**: Define circuit once in Python
2. **Dual Output**: Manufacturing (KiCad) + Simulation (SPICE)
3. **Professional Models**: Realistic component behavior
4. **Automated Workflow**: No manual translation needed

## Implementation

The SPICE export is added to `main.py`:

```python
# Generate SPICE netlist for circuit simulation
print("⚡ Generating SPICE netlist for simulation...")
try:
    spice_netlist = circuit.to_spice(include_analysis=True)
    with open("ESP32_C6_Dev_Board.cir", "w") as f:
        f.write(spice_netlist)
    print("✅ SPICE netlist saved as ESP32_C6_Dev_Board.cir")
except Exception as e:
    print(f"⚠️  SPICE export not available: {e}")
```

This provides a clean, professional workflow from Python circuit definition to both PCB manufacturing and circuit simulation.