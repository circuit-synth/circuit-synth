# Circuit-Synth Agent Architecture: Example-Driven Code Generation

## Core Philosophy: Examples-First Training

Instead of hardcoded component libraries, agents learn from extensive examples of:
1. **Circuit Patterns** - Real circuit-synth code examples
2. **Context Knowledge** - Electronics design principles and best practices
3. **KiCad Integration** - Symbol/footprint selection and pin mapping

## Agent Architecture

### 1. Specialized Domain Agents

Each agent has deep expertise in one circuit domain:

```
circuit-power-agent:
  - Examples: LDO regulators, switching supplies, power distribution
  - Context: Voltage regulation, current capacity, thermal design
  - KiCad: Power management ICs, inductors, capacitors

circuit-interface-agent:
  - Examples: USB-C, UART, SPI, I2C interfaces
  - Context: Signal integrity, protection, termination
  - KiCad: Connectors, protection diodes, series resistors

circuit-mcu-agent:
  - Examples: ESP32, STM32, Arduino integration
  - Context: MCU pinouts, peripheral assignment, clocking
  - KiCad: MCU symbols, crystal oscillators, decoupling

circuit-analog-agent:
  - Examples: Op-amp circuits, ADC/DAC, sensor interfaces
  - Context: Signal conditioning, filtering, calibration
  - KiCad: Analog ICs, precision passives, sensors

circuit-protection-agent:
  - Examples: ESD protection, overcurrent, overvoltage
  - Context: Protection strategies, failure modes
  - KiCad: Protection diodes, fuses, TVS devices
```

### 2. Example Database Structure

```
examples/
├── power/
│   ├── 01_basic_ldo_3v3.py           # Simple LDO with caps
│   ├── 02_dual_rail_supply.py        # +5V/-5V supply
│   ├── 03_switching_buck_5v.py       # Efficient switching reg
│   └── context/
│       ├── ldo_design_principles.md
│       ├── capacitor_selection.md
│       └── thermal_management.md
├── interfaces/
│   ├── 01_basic_usb_c.py             # USB-C power only
│   ├── 02_usb_c_data.py              # USB-C with data lines
│   ├── 03_uart_interface.py          # UART with protection
│   └── context/
│       ├── usb_c_design_guide.md
│       ├── esd_protection.md
│       └── signal_integrity.md
├── microcontrollers/
│   ├── 01_esp32_minimal.py           # Basic ESP32 setup
│   ├── 02_esp32_with_peripherals.py  # ESP32 + SPI/I2C
│   ├── 03_stm32_basic.py             # STM32 minimal
│   └── context/
│       ├── esp32_pinout_guide.md
│       ├── peripheral_assignment.md
│       └── crystal_oscillator.md
```

### 3. Example Format Standard

Each example follows strict format for agent training:

```python
#!/usr/bin/env python3
"""
CIRCUIT: Basic 3.3V LDO Regulator
PURPOSE: Convert 5V input to stable 3.3V output with 1A capacity
COMPONENTS: NCP1117 LDO + input/output capacitors
COMPLEXITY: Beginner
"""

from circuit_synth import Circuit, Component, Net, circuit

@circuit
def ldo_regulator_3v3():
    """
    3.3V LDO regulator with proper decoupling.
    
    Design Notes:
    - NCP1117 can handle 1A output current
    - 10µF input cap reduces input ripple
    - 22µF output cap improves transient response
    - SOT-223 package provides good thermal dissipation
    """
    # Create nets
    vin_5v = Net('VIN_5V')
    vout_3v3 = Net('VOUT_3V3') 
    gnd = Net('GND')
    
    # Main regulator - NCP1117 in SOT-223 package
    regulator = Component(
        symbol="Regulator_Linear:NCP1117-3.3_SOT223",
        ref="U1",
        footprint="Package_TO_SOT_SMD:SOT-223-3_TabPin2"
    )
    
    # Input decoupling capacitor - 10µF ceramic
    cap_input = Component(
        symbol="Device:C",
        ref="C1", 
        value="10uF",
        footprint="Capacitor_SMD:C_0805_2012Metric"
    )
    
    # Output decoupling capacitor - 22µF ceramic  
    cap_output = Component(
        symbol="Device:C",
        ref="C2",
        value="22uF", 
        footprint="Capacitor_SMD:C_0805_2012Metric"
    )
    
    # Regulator connections (pin numbers from datasheet)
    regulator[1] += gnd        # Pin 1: GND
    regulator[2] += vout_3v3   # Pin 2: VOUT (3.3V)
    regulator[3] += vin_5v     # Pin 3: VIN (5V)
    
    # Input capacitor connections
    cap_input[1] += vin_5v     # Positive terminal to 5V
    cap_input[2] += gnd        # Negative terminal to GND
    
    # Output capacitor connections  
    cap_output[1] += vout_3v3  # Positive terminal to 3.3V
    cap_output[2] += gnd       # Negative terminal to GND

if __name__ == '__main__':
    circuit = ldo_regulator_3v3()
    circuit.generate_kicad_project("basic_ldo_3v3")
```

### 4. Context Knowledge Files

Each example category includes context files with design principles:

```markdown
# LDO Design Principles

## Component Selection
- **Input Capacitor**: 10µF ceramic, placed close to VIN pin
  - Reduces input voltage ripple
  - Improves regulator stability
  - Use X7R dielectric for stability

- **Output Capacitor**: 22µF ceramic, placed close to VOUT pin  
  - Improves transient response
  - Reduces output voltage ripple
  - Larger value = better load regulation

## Thermal Considerations
- SOT-223 package: ~2°C/W thermal resistance
- Calculate power dissipation: P = (VIN - VOUT) × IOUT
- Add thermal vias under package if P > 1W

## Layout Guidelines
- Keep input/output caps close to regulator pins
- Use wide traces for power connections
- Add ground plane for thermal dissipation
- Separate analog and digital grounds if needed
```

### 5. Agent Training Process

Agents are trained on:

1. **Code Patterns**: Learn component selection, pin connections, net management
2. **Context Knowledge**: Understand why certain design choices are made  
3. **KiCad Integration**: Know which symbols/footprints work together
4. **Progressive Complexity**: From basic → intermediate → advanced examples

### 6. Code Generation Workflow

```
User Request: "I need USB-C power input with 3.3V regulation"
↓
Orchestrator Agent:
  - Identifies: power conversion + interface requirements
  - Delegates to: circuit-interface-agent + circuit-power-agent
↓  
circuit-interface-agent:
  - Reviews examples/interfaces/01_basic_usb_c.py
  - Applies context/usb_c_design_guide.md principles
  - Generates Component() calls for USB-C connector
  - Adds ESD protection based on examples
↓
circuit-power-agent:  
  - Reviews examples/power/01_basic_ldo_3v3.py
  - Applies context/ldo_design_principles.md
  - Generates Component() calls for LDO + capacitors
  - Connects power nets properly
↓
Orchestrator Agent:
  - Combines both agent outputs
  - Ensures net connections between subsystems
  - Produces final Python circuit-synth code
```

### 7. Implementation Strategy

1. **Create Example Database**: Start with 20-30 core examples across domains
2. **Context Knowledge Base**: Write design principle docs for each domain  
3. **Agent Implementation**: Create specialized agents trained on examples
4. **Integration Testing**: Verify generated code produces working KiCad projects
5. **Continuous Learning**: Add new examples based on user requests

This approach ensures:
- **Transparency**: All generated code is inspectable Python
- **Accuracy**: Examples are tested and verified to work
- **Extensibility**: Easy to add new circuit types by adding examples
- **Learning**: Agents improve as example database grows