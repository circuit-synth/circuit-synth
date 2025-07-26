# circuit-synth

Pythonic circuit design for professional KiCad projects

## Overview

Circuit Synth is an open-source Python library that provides a high-level, programmatic interface for designing electronic circuits and generating KiCad projects. It allows you to define circuits using Python code, automatically handle component placement, and generate professional-quality KiCad schematics and PCB layouts.

**Current Status**: Circuit-synth is ready for professional use with the following capabilities:
- Places components functionally (not yet optimized for intelligent board layout)
- Places schematic parts (without intelligent placement algorithms)
- Generates working KiCad projects suitable for professional development

## Features

- **Pythonic Circuit Design**: Define circuits using intuitive Python classes and decorators
- **KiCad Integration**: Generate KiCad schematics and PCB layouts automatically
- **Component Management**: Built-in component library with easy extensibility
- **Smart Placement**: Automatic component placement algorithms
- **Type Safety**: Full type hints support for better IDE integration
- **Extensible Architecture**: Clean interfaces for custom implementations

## Installation

```bash
pip install circuit-synth
```

## Quick Start

```python
from circuit_synth import *
import os

# Define components
LED_0603 = Component(
    symbol="Device:LED", ref="D", value="LED",
    footprint="LED_SMD:LED_0603_1608Metric"
)

R_330 = Component(
    symbol="Device:R", ref="R", value="330",
    footprint="Resistor_SMD:R_0603_1608Metric"
)

# Define a simple LED circuit
@circuit
def led_circuit():
    # Create power nets
    _3v3 = Net('3V3')
    GND = Net('GND')
    led_net = Net('LED_NET')
    
    # Create components
    led = LED_0603()
    led.ref = "D1"
    
    resistor = R_330()
    resistor.ref = "R1"
    
    # Connect components using pin access
    resistor[1] += _3v3      # Resistor to power
    resistor[2] += led_net   # Resistor to LED
    led[1] += led_net        # LED anode
    led[2] += GND            # LED cathode

# Generate KiCad files
if __name__ == '__main__':
    c = led_circuit()
    
    # Create output directory
    output_dir = "kicad_output"
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate KiCad project
    gen = create_unified_kicad_integration(output_dir, "led_circuit")
    gen.generate_project(
        circuit=c,
        generate_pcb=True,
        force_regenerate=True
    )
```

## Documentation

Full documentation is available at [https://circuit-synth.readthedocs.io](https://circuit-synth.readthedocs.io)

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- Documentation: [https://circuit-synth.readthedocs.io](https://circuit-synth.readthedocs.io)
- Issues: [GitHub Issues](https://github.com/circuit-synth/circuit-synth/issues)
- Discussions: [GitHub Discussions](https://github.com/circuit-synth/circuit-synth/discussions)
