# circuit-synth

Pythonic circuit design for production-ready KiCad projects

## Overview

Circuit Synth is an open-source Python library that provides a high-level, programmatic interface for designing electronic circuits and generating KiCad projects. It allows you to define circuits using Python code, automatically handle component placement, and generate production-ready KiCad schematics and PCB layouts.

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
from circuit_synth import Circuit, Component, Net, circuit

# Define a simple LED circuit
@circuit
def led_circuit():
    # Create components
    led = Component("LED", "D1")
    resistor = Component("R", "R1", value="330")
    power = Component("VCC", "U1")
    ground = Component("GND", "U2")
    
    # Create nets to connect components
    vcc_net = Net("VCC")
    led_net = Net("LED_NET")
    gnd_net = Net("GND")
    
    # Connect components
    power.connect("OUT", vcc_net)
    resistor.connect("1", vcc_net)
    resistor.connect("2", led_net)
    led.connect("A", led_net)
    led.connect("K", gnd_net)
    ground.connect("IN", gnd_net)
    
    # Create and return circuit
    circuit = Circuit("LED Circuit")
    circuit.add_components(led, resistor, power, ground)
    circuit.add_nets(vcc_net, led_net, gnd_net)
    
    return circuit

# Generate KiCad files
from circuit_synth import create_unified_kicad_integration

kicad = create_unified_kicad_integration()
circuit = led_circuit()
kicad.generate_schematic(circuit, "output/led_circuit")
```

## Documentation

Full documentation is available at [https://circuitsynth.readthedocs.io](https://circuitsynth.readthedocs.io)

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- Documentation: [https://circuitsynth.readthedocs.io](https://circuitsynth.readthedocs.io)
- Issues: [GitHub Issues](https://github.com/circuitsynth/circuit-synth/issues)
- Discussions: [GitHub Discussions](https://github.com/circuitsynth/circuit-synth/discussions)
