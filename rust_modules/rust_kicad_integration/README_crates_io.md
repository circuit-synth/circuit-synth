# kicad-rust

[![Crates.io](https://img.shields.io/crates/v/kicad.svg)](https://crates.io/crates/kicad)
[![Documentation](https://docs.rs/kicad/badge.svg)](https://docs.rs/kicad)
[![License](https://img.shields.io/crates/l/kicad.svg)](https://github.com/circuit-synth/kicad-rust#license)
[![CI](https://github.com/circuit-synth/kicad-rust/workflows/CI/badge.svg)](https://github.com/circuit-synth/kicad-rust/actions)

A Rust library for programmatically creating and manipulating KiCad schematic and PCB files.

## Features

- 🚀 **High Performance** - Native Rust implementation for fast file manipulation
- 📝 **Schematic Generation** - Create KiCad schematics programmatically
- 🔧 **Component Management** - Add, remove, and update components
- 🏗️ **Symbol Inheritance** - Full support for extended symbols
- 📦 **Multi-Unit Components** - Handle complex parts like op-amps and MCUs
- 🐍 **Python Bindings** - Use from Python with zero overhead
- 🎯 **Type Safe** - Leverage Rust's type system for correctness

## Installation

### Rust

Add to your `Cargo.toml`:

```toml
[dependencies]
kicad = "0.1"
```

### Python

```bash
pip install kicad
```

## Quick Start

### Rust

```rust
use kicad::{Schematic, Component, Net};

fn main() -> Result<(), Box<dyn std::error::Error>> {
    // Create a new schematic
    let mut schematic = Schematic::new("MyCircuit");
    
    // Add components
    schematic.add_component(Component {
        reference: "R1".to_string(),
        symbol: "Device:R".to_string(),
        value: Some("10k".to_string()),
        position: (50.0, 50.0),
        footprint: Some("Resistor_SMD:R_0603_1608Metric".to_string()),
    })?;
    
    schematic.add_component(Component {
        reference: "C1".to_string(),
        symbol: "Device:C".to_string(),
        value: Some("100nF".to_string()),
        position: (100.0, 50.0),
        footprint: Some("Capacitor_SMD:C_0603_1608Metric".to_string()),
    })?;
    
    // Create nets
    let vcc = Net::new("VCC");
    let gnd = Net::new("GND");
    
    // Connect components
    schematic.connect("R1", 1, &vcc)?;
    schematic.connect("R1", 2, &gnd)?;
    schematic.connect("C1", 1, &vcc)?;
    schematic.connect("C1", 2, &gnd)?;
    
    // Save to file
    schematic.save("my_circuit.kicad_sch")?;
    
    Ok(())
}
```

### Python

```python
import kicad

# Create a new schematic
schematic = kicad.Schematic("MyCircuit")

# Add components
schematic.add_component(
    reference="R1",
    symbol="Device:R",
    value="10k",
    position=(50.0, 50.0),
    footprint="Resistor_SMD:R_0603_1608Metric"
)

schematic.add_component(
    reference="C1",
    symbol="Device:C",
    value="100nF",
    position=(100.0, 50.0),
    footprint="Capacitor_SMD:C_0603_1608Metric"
)

# Create and connect nets
vcc = kicad.Net("VCC")
gnd = kicad.Net("GND")

schematic.connect("R1", 1, vcc)
schematic.connect("R1", 2, gnd)
schematic.connect("C1", 1, vcc)
schematic.connect("C1", 2, gnd)

# Save to file
schematic.save("my_circuit.kicad_sch")
```

## Advanced Features

### Extended Symbols

Handle KiCad's symbol inheritance automatically:

```rust
// AMS1117-3.3 extends AP1117-15
schematic.add_component(Component {
    reference: "U1".to_string(),
    symbol: "Regulator_Linear:AMS1117-3.3".to_string(),
    // Inheritance is handled automatically
    ..Default::default()
})?;
```

### Multi-Unit Components

Work with complex multi-unit parts:

```rust
// Dual op-amp with multiple units
schematic.add_component(Component {
    reference: "U2".to_string(),
    symbol: "Amplifier_Operational:LM358".to_string(),
    unit: Some(1),  // First op-amp
    ..Default::default()
})?;

schematic.add_component(Component {
    reference: "U2".to_string(),
    symbol: "Amplifier_Operational:LM358".to_string(),
    unit: Some(2),  // Second op-amp
    ..Default::default()
})?;
```

### Hierarchical Labels

Add hierarchical labels for complex designs:

```rust
schematic.add_hierarchical_label(
    "POWER_IN",
    HierarchicalShape::Input,
    (25.0, 50.0)
)?;

schematic.add_hierarchical_label(
    "DATA_OUT",
    HierarchicalShape::Output,
    (200.0, 100.0)
)?;
```

## Documentation

Full API documentation is available at [docs.rs/kicad](https://docs.rs/kicad).

## Examples

Check out the [examples](https://github.com/circuit-synth/kicad-rust/tree/main/examples) directory for more complete examples:

- `voltage_divider.rs` - Simple resistor divider
- `power_supply.rs` - Linear regulator with decoupling
- `mcu_board.rs` - Microcontroller with peripherals
- `hierarchical.rs` - Multi-sheet hierarchical design

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](https://github.com/circuit-synth/kicad-rust/blob/main/CONTRIBUTING.md) for details.

## License

This project is dual-licensed under either:

- MIT license ([LICENSE-MIT](LICENSE-MIT) or http://opensource.org/licenses/MIT)
- Apache License, Version 2.0 ([LICENSE-APACHE](LICENSE-APACHE) or http://www.apache.org/licenses/LICENSE-2.0)

at your option.

## Acknowledgments

Originally developed as part of the [circuit-synth](https://github.com/circuit-synth/circuit-synth) project for AI-assisted circuit design.