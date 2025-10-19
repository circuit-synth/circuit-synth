---
name: circuit-patterns
description: Pre-made circuit patterns library for common circuit building blocks
allowed-tools: ["Read", "Bash", "Write"]
---

# Circuit Patterns Skill

## When to Use This Skill

Invoke this skill when the user:
- Mentions circuit patterns: "buck converter", "battery charger", "voltage divider"
- Asks for pre-made circuits: "do you have a circuit for X", "example circuit"
- Needs design references: "how to design a boost converter", "thermistor circuit"
- Requests circuit templates: "template for RS-485", "op-amp buffer circuit"
- Wants to see available patterns: "what circuits are available", "list patterns"

## Available Circuit Patterns

### Power Management
1. **buck_converter** - Step-down switching regulator (12V→5V/3.3V)
   - Keywords: buck, step-down, switching regulator, DC-DC
   - Example: 12V to 5V @ 3A with TPS54331

2. **boost_converter** - Step-up switching regulator (3.7V→5V)
   - Keywords: boost, step-up, battery to USB
   - Example: Li-ion battery to 5V USB power

3. **lipo_charger** - Li-ion/LiPo battery charging circuit
   - Keywords: battery charger, LiPo, Li-ion, USB charging
   - Example: USB-C to single-cell LiPo with MCP73831

### Sensing & Measurement
4. **resistor_divider** - Parametric voltage divider for ADC scaling
   - Keywords: voltage divider, ADC, voltage sensing, scaling
   - Example: 12V battery monitoring with 3.3V ADC

5. **thermistor** - NTC thermistor temperature sensing
   - Keywords: temperature sensor, thermistor, NTC
   - Example: Battery temperature monitoring

6. **opamp_follower** - Unity-gain voltage buffer
   - Keywords: op-amp, buffer, impedance matching, voltage follower
   - Example: High-impedance sensor buffering

### Communication
7. **rs485** - Industrial differential serial interface
   - Keywords: RS-485, RS485, Modbus, industrial communication
   - Example: Multi-drop industrial network with MAX485

## Capabilities

### Pattern Retrieval
- Load complete circuit pattern code
- Show design notes and calculations
- Provide component selection rationale
- Include PCB layout guidelines

### Design Assistance
- Explain pattern parameters and customization
- Suggest combinations of patterns
- Show usage examples
- Recommend alternatives

### Code Integration
- Patterns are importable Python modules
- Use with `from pattern_name import function_name`
- All patterns follow circuit-synth `@circuit` decorator
- Composable - combine multiple patterns in one design

## Usage Examples

### Example 1: Get Buck Converter Pattern
**User:** "show me the buck converter circuit"

**Process:**
1. Read buck_converter.py pattern file
2. Extract main circuit function and design notes
3. Show component selection and parameters
4. Provide usage example

**Output:**
```python
# Buck Converter Pattern
@circuit(name="Buck_Converter_3A")
def buck_converter(vin, vout, gnd, output_voltage="3.3V", max_current="3A"):
    """
    Synchronous buck converter for efficient step-down regulation

    Example specs:
    - Input: 7V-36V
    - Output: 3.3V @ 3A
    - Efficiency: ~90%
    - IC: TPS54331 (SOIC-8)
    """
    # [Complete circuit code...]

# Usage:
vin_12v = Net('VIN_12V')
vout_5v = Net('VOUT_5V')
gnd = Net('GND')

buck_converter(vin_12v, vout_5v, gnd, output_voltage="5V", max_current="3A")
```

### Example 2: List Available Patterns
**User:** "what circuit patterns are available?"

**Process:**
1. List all pattern files in circuit-synth directory
2. Categorize by function (power, sensing, communication)
3. Provide brief description of each

**Output:**
```
Available Circuit Patterns:

POWER MANAGEMENT:
• buck_converter - 12V→5V step-down switching regulator
• boost_converter - 3.7V→5V step-up for battery applications
• lipo_charger - USB-C Li-ion/LiPo charging circuit

SENSING & MEASUREMENT:
• resistor_divider - Voltage scaling for ADC inputs
• thermistor - NTC temperature sensing
• opamp_follower - High-impedance buffer for sensors

COMMUNICATION:
• rs485 - Industrial differential serial (Modbus, BACnet)

Use: "show me [pattern_name]" to see implementation details
```

### Example 3: Combine Multiple Patterns
**User:** "create a battery monitor with temperature and RS-485"

**Process:**
1. Load relevant patterns (lipo_charger, thermistor, rs485)
2. Show how to import and combine
3. Provide complete integration example
4. Reference battery_monitor_example.py

**Output:**
```python
from lipo_charger import lipo_charger
from thermistor import thermistor_sensor
from rs485 import rs485_transceiver

@circuit(name="Battery_Monitor")
def battery_monitor():
    # Power nets
    usb_5v = Net('USB_5V')
    battery = Net('VBAT')
    system_3v3 = Net('VCC_3V3')
    gnd = Net('GND')

    # Battery charging
    lipo_charger(usb_5v, gnd, battery, gnd, charge_led)

    # Temperature monitoring
    thermistor_sensor(system_3v3, adc_temp, gnd, "NTC_10k")

    # Communication
    rs485_transceiver(system_3v3, gnd, tx, rx, de, rs485_a, rs485_b)

See: battery_monitor_example.py for complete implementation
```

### Example 4: Pattern Customization
**User:** "how do I change the boost converter output voltage?"

**Process:**
1. Read boost_converter.py
2. Extract parameter documentation
3. Show feedback resistor calculation
4. Provide custom example

**Output:**
```python
# Boost Converter Output Voltage Customization

# The output voltage is set by the feedback resistor divider:
# Vout = Vref × (1 + R1/R2)

# For TPS61070 (Vref = 0.5V):
# 5V output:  R1/R2 = 9  → R1=91kΩ, R2=10kΩ
# 12V output: R1/R2 = 23 → R1=237kΩ, R2=10kΩ

# Custom 9V output:
# R1/R2 = (9/0.5) - 1 = 17
# R1 = 174kΩ, R2 = 10kΩ

boost_converter(battery, vout_9v, gnd, output_voltage="9V", max_current="1A")

# The pattern will automatically calculate resistor values
# based on the output_voltage parameter.
```

## Pattern File Locations

Patterns are located in:
```
circuit-synth/
├── example_project/circuit-synth/     # Development source
│   ├── buck_converter.py
│   ├── boost_converter.py
│   ├── lipo_charger.py
│   ├── resistor_divider.py
│   ├── thermistor.py
│   ├── opamp_follower.py
│   └── rs485.py
```

## Pattern Structure

Each pattern follows this structure:

```python
#!/usr/bin/env python3
"""
Pattern Name - Brief Description
Detailed explanation of circuit function and applications
"""

from circuit_synth import *

@circuit(name="Pattern_Name")
def pattern_function(inputs, outputs, parameters):
    """
    Docstring with:
    - Function description
    - Key features
    - Common applications
    - Parameter explanations
    - Example specifications
    """

    # Component definitions with symbols and footprints
    # Net connections
    # Configuration

    # Return is optional (circuit auto-captured)

# Optional: Additional variants or helper functions

# Design notes as module docstring at end:
"""
DESIGN NOTES:

1. Theory of Operation
2. Component Selection Guide
3. PCB Layout Guidelines
4. Thermal Considerations
5. Design Calculations
6. Common Issues & Solutions
7. Testing & Validation
"""
```

## Pattern Features

### Complete Component Selection
- All components have verified KiCad symbols
- Footprints specified (0603, 0805, SOT-23, SOIC-8, etc.)
- Manufacturer examples provided
- Alternative parts suggested

### Design Documentation
- Theory of operation explained
- Component selection rationale
- Design calculations provided
- PCB layout guidelines included
- Thermal management considerations
- Common pitfalls documented

### Manufacturing Ready
- Components available on JLCPCB (where applicable)
- Standard footprints used
- DFM considerations included
- Assembly-friendly design

## Integration Strategy

### Step 1: Identify Pattern Need
User describes requirement → Match to available pattern

### Step 2: Load Pattern Code
Use Read tool to load pattern file:
```bash
Read(file_path="example_project/circuit-synth/buck_converter.py")
```

### Step 3: Extract Relevant Information
- Main circuit function
- Parameter options
- Component details
- Design notes

### Step 4: Provide to User
- Show pattern code
- Explain customization options
- Suggest usage examples
- Reference combination examples

## Common Pattern Combinations

### Power Supply + Monitoring
```python
# Battery-powered system with monitoring
lipo_charger()      # Charge from USB
buck_converter()    # Step down to 3.3V
resistor_divider()  # Monitor battery voltage
thermistor()        # Monitor temperature
```

### Multi-Rail Power System
```python
# Multiple voltage rails from single input
buck_converter(12V, 5V, ...)    # First rail
buck_converter(5V, 3.3V, ...)   # Second rail
boost_converter(5V, 12V, ...)   # Boost for legacy devices
```

### Sensor Interface
```python
# Professional sensor conditioning
thermistor()         # Temperature measurement
opamp_follower()     # Buffer high-Z sensor
resistor_divider()   # Scale to ADC range
```

### Industrial Communication
```python
# Robust industrial interface
rs485()              # Differential communication
opamp_follower()     # Signal conditioning
```

## Usage Examples Reference

Complete examples available:
- **battery_monitor_example.py** - Integration of 5 patterns
- **power_systems_example.py** - Power conversion scenarios

Load examples:
```bash
Read(file_path="example_project/circuit-synth/battery_monitor_example.py")
```

## Pattern Parameters

### Buck Converter
- `output_voltage`: "3.3V", "5V", "12V", etc.
- `max_current`: "1A", "3A", "5A", etc.

### Boost Converter
- `output_voltage`: "5V", "12V", etc.
- `max_current`: "500mA", "1A", "2A", etc.

### Resistor Divider
- `ratio`: "2:1", "10:1", "4:1", etc.

### Thermistor
- `thermistor_type`: "NTC_10k", "NTC_100k", etc.

### RS-485
- Termination and biasing (see pattern for options)

### LiPo Charger
- Charge current set by resistor (500mA default)

## Best Practices

### Pattern Selection
✅ Match pattern to exact requirement
✅ Consider combining patterns for complex designs
✅ Review design notes before implementation
❌ Don't modify patterns directly - create variants

### Customization
✅ Use provided parameters
✅ Follow design equations for custom values
✅ Reference datasheet for advanced changes
❌ Don't skip PCB layout guidelines

### Integration
✅ Import patterns as modules
✅ Share nets between patterns
✅ Follow example circuits
❌ Don't duplicate pattern code - import instead

## Error Handling

**Pattern Not Found:**
```
Pattern "xyz" not found.
Available patterns: buck_converter, boost_converter, lipo_charger,
resistor_divider, thermistor, opamp_follower, rs485
```

**Invalid Parameters:**
```
Invalid output_voltage "15V" for buck_converter.
Supported range: 1.2V-28V
Example values: "3.3V", "5V", "12V"
```

## Performance

- **Pattern Load**: <1 second (Read file)
- **Code Size**: 200-300 lines per pattern
- **Token Usage**: ~1500-3000 tokens per pattern
- **Context Efficiency**: Progressive disclosure saves 10,000+ tokens

## Advantages Over Generic Code Generation

### Proven Designs
- Based on manufacturer reference designs
- Component values calculated properly
- PCB layout considerations included

### Manufacturing Ready
- Components verified available
- Footprints matched to parts
- DFM guidelines included

### Educational Value
- Extensive design notes
- Calculation examples
- Best practices documented

### Consistency
- Standard KiCad symbols/footprints
- Uniform naming conventions
- Compatible interfaces

## Future Patterns (Roadmap)

Potential additions based on user demand:
- Linear regulators (LDO)
- Crystal oscillators
- USB interfaces
- CAN bus
- SPI flash memory
- SD card interface
- Motor drivers
- LED drivers
- Audio amplifiers

## Related Skills

- **kicad-integration**: Find symbols/footprints for pattern components
- **component-search**: Source pattern components from JLCPCB

## Example Workflow

**Complete design workflow:**
1. User: "I need a battery-powered device with temperature monitoring"
2. circuit-patterns skill: Shows lipo_charger + thermistor + buck_converter
3. User: "show me the battery charger circuit"
4. circuit-patterns skill: Loads and displays lipo_charger.py
5. User: "what components do I need?"
6. component-search skill: Searches JLCPCB for each component
7. User: "find KiCad symbols"
8. kicad-integration skill: Locates all required symbols
9. User creates complete circuit with verified, sourced components

This multi-skill workflow ensures:
- Proven circuit designs
- Available components
- Valid KiCad symbols
- Manufacturing-ready output
