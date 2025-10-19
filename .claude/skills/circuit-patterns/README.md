# Circuit Patterns Skill

## Overview

The circuit-patterns skill provides access to a curated library of pre-made circuit patterns for common electronic design building blocks. Each pattern is a proven, manufacturable circuit design with complete component selection, design calculations, and PCB layout guidelines.

## Purpose

**Problem**: Users repeatedly ask "how do I design a buck converter?" or "what's a good battery charging circuit?"

**Solution**: Pre-made, proven circuit patterns that can be directly used or customized. Progressive disclosure means patterns only load when requested, avoiding context bloat.

## Available Patterns

| Pattern | Description | Key Components |
|---------|-------------|----------------|
| `buck_converter` | Step-down switching regulator | TPS54331, inductor, caps |
| `boost_converter` | Step-up switching regulator | TPS61070, Schottky diode |
| `lipo_charger` | Li-ion battery charging | MCP73831, USB-C |
| `resistor_divider` | Voltage scaling for ADC | Resistors (parametric) |
| `thermistor` | Temperature sensing | NTC thermistor, resistor |
| `opamp_follower` | Unity-gain buffer | MCP6001 op-amp |
| `rs485` | Industrial communication | MAX485, termination |

## Skill Benefits

### 1. Progressive Disclosure
- Only loads requested pattern
- Saves 10,000+ tokens vs including all patterns
- Can scale to 50+ patterns without bloating context

### 2. Proven Designs
- Based on manufacturer reference designs
- Component values properly calculated
- PCB layout guidelines included
- Common pitfalls documented

### 3. Manufacturing Ready
- Components verified available on JLCPCB
- Standard KiCad symbols/footprints
- DFM considerations included
- Assembly-friendly designs

### 4. Educational Value
- Extensive design notes and theory
- Step-by-step calculations
- Alternatives and trade-offs explained
- Testing and validation procedures

## Usage

### Automatic Invocation

Claude will automatically invoke this skill when users:
- Mention circuit pattern names: "buck converter", "battery charger"
- Ask for pre-made circuits: "do you have a circuit for..."
- Request design references: "how to design a..."
- Want to list patterns: "what patterns are available?"

### Manual Invocation

You can explicitly request a pattern:
```
"Show me the buck converter pattern"
"Load the RS-485 circuit"
"What parameters does the boost converter support?"
```

### Example Queries

**Get a pattern:**
```
User: "I need a buck converter from 12V to 5V"
Skill: Loads buck_converter.py, shows usage with parameters
```

**List patterns:**
```
User: "What circuit patterns are available?"
Skill: Lists all patterns with brief descriptions
```

**Customize pattern:**
```
User: "How do I change the boost converter to output 12V instead of 5V?"
Skill: Shows feedback resistor calculation and custom example
```

**Combine patterns:**
```
User: "Create a battery monitor with RS-485"
Skill: Shows how to import and combine lipo_charger, thermistor, and rs485
```

## Pattern Structure

Each pattern includes:

```python
@circuit(name="PatternName")
def pattern_function(vin, vout, gnd, **parameters):
    """Complete circuit implementation"""
    # Component selection
    # Net connections
    # Configuration

"""
Design notes:
- Theory of operation
- Component selection guide
- PCB layout guidelines
- Thermal considerations
- Design calculations
- Common issues & solutions
"""
```

## Integration Examples

### Simple Usage
```python
from buck_converter import buck_converter

@circuit(name="Power_Supply")
def my_power_supply():
    vin = Net('VIN_12V')
    vout = Net('VOUT_5V')
    gnd = Net('GND')

    buck_converter(vin, vout, gnd, output_voltage="5V", max_current="3A")
```

### Combined Patterns
```python
from lipo_charger import lipo_charger
from buck_converter import buck_converter
from thermistor import thermistor_sensor

@circuit(name="Battery_System")
def battery_system():
    # Use multiple patterns together
    lipo_charger(usb_5v, gnd, battery, gnd, led)
    buck_converter(battery, system_3v3, gnd, "3.3V", "2A")
    thermistor_sensor(system_3v3, adc_temp, gnd, "NTC_10k")
```

## Complete Examples

Reference implementations showing pattern combinations:
- `battery_monitor_example.py` - 5 patterns integrated
- `power_systems_example.py` - Power conversion scenarios

## Pattern Categories

### Power Management
- Voltage regulation (buck, boost, LDO)
- Battery charging
- Power distribution

### Sensing & Measurement
- Voltage sensing (resistor divider)
- Temperature sensing (thermistor)
- Signal conditioning (op-amp buffer)

### Communication
- Industrial interfaces (RS-485)
- Serial protocols
- Isolation and protection

## Technical Details

### Component Selection
- All components have verified KiCad symbols
- Footprints specified for manufacturability
- Alternatives provided where applicable
- JLCPCB availability noted

### Design Documentation
- Theory of operation explained
- Design equations provided
- Component selection rationale
- PCB layout best practices
- Thermal management guidelines
- Common failure modes

### Parameters
Most patterns support customization:
- Output voltages
- Current ratings
- Component values
- Feature enable/disable

## Skill Performance

- **Load Time**: <1 second per pattern
- **Token Usage**: 1,500-3,000 tokens per pattern
- **Context Savings**: ~10,000 tokens vs loading all patterns
- **Accuracy**: Based on manufacturer reference designs

## Best Practices

### When to Use
✅ Starting a new design
✅ Need proven reference
✅ Want manufacturing-ready circuit
✅ Learning circuit design

### When to Customize
✅ Different voltage/current requirements
✅ Alternative components needed
✅ Specific constraints (size, cost, etc.)

### When to Create New Pattern
✅ Common use case not covered
✅ Repeatedly building same circuit
✅ Want to share design with team

## Related Skills

**component-search**
- Find JLCPCB availability for pattern components
- Get pricing and stock information
- Find alternatives if primary part unavailable

**kicad-integration**
- Locate KiCad symbols for pattern components
- Find appropriate footprints
- Validate symbol/footprint compatibility

## Roadmap

Future pattern additions based on user demand:
- Linear voltage regulators (LDO)
- Crystal oscillator circuits
- USB interface circuits
- CAN bus transceivers
- Motor driver circuits
- LED constant-current drivers
- Audio amplifiers
- Sensor interfaces (I2C, SPI)

## Contributing Patterns

Want to add a pattern to the library?

**Requirements:**
1. Complete circuit-synth implementation
2. Verified KiCad symbols/footprints
3. Component availability (prefer JLCPCB basic parts)
4. Comprehensive design notes
5. PCB layout guidelines
6. Usage example

**Pattern Template:**
See existing patterns for structure and documentation style.

## Troubleshooting

**Pattern not loading:**
- Verify pattern file exists in `example_project/circuit-synth/`
- Check file permissions
- Ensure file is valid Python

**Symbol/footprint not found:**
- Use kicad-integration skill to verify
- Check KiCad library installation
- Consider alternative components

**Parameters not working:**
- Check pattern documentation for supported parameters
- Verify parameter format (e.g., "3.3V" not 3.3)
- Review example usage

## Support

For questions or issues:
- Check pattern design notes
- Review example circuits
- Consult component datasheets
- Ask for clarification in chat

## License

Circuit patterns are provided under MIT license as part of circuit-synth.
Reference designs based on public manufacturer application notes.
