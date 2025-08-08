# KiCad Schematic Editor (Rust)

A Rust library for programmatically creating and manipulating KiCad schematic files.

## Features

- ✅ Create KiCad schematics programmatically
- ✅ Add/remove/update components
- ✅ Support for hierarchical labels
- ✅ Handle extended symbols (inheritance)
- ✅ Multi-unit component support
- ✅ Preserve KiCad metadata and UUIDs
- ✅ Python bindings available

## Installation

### Rust
```toml
[dependencies]
kicad-schematic-editor = "0.1.0"
```

### Python
```bash
pip install kicad-schematic-editor
```

## Usage

### Rust Example
```rust
use kicad_schematic_editor::{SchematicEditor, SimpleComponent};

fn main() -> Result<(), Box<dyn std::error::Error>> {
    // Load a schematic
    let mut editor = SchematicEditor::load_from_file("my_schematic.kicad_sch")?;
    
    // Add a component
    let resistor = SimpleComponent {
        reference: "R1".to_string(),
        lib_id: "Device:R".to_string(),
        value: "10k".to_string(),
        position: (100.0, 50.0),
        footprint: Some("Resistor_SMD:R_0603_1608Metric".to_string()),
    };
    editor.add_component(&resistor)?;
    
    // Save the result
    editor.save_to_file("output.kicad_sch")?;
    Ok(())
}
```

### Python Example
```python
import kicad_schematic_editor as kicad

# Create a new schematic
schematic = kicad.create_minimal_schematic()

# Add a resistor
schematic = kicad.add_component_to_schematic(
    schematic,
    reference="R1",
    lib_id="Device:R",
    value="10k",
    x=100.0,
    y=50.0,
    rotation=0.0,
    footprint="Resistor_SMD:R_0603_1608Metric"
)

# Add a hierarchical label
schematic = kicad.add_hierarchical_label_to_schematic(
    schematic,
    name="VCC",
    shape="input",
    x=100.0,
    y=30.0,
    rotation=90.0
)

# Save to file
with open("output.kicad_sch", "w") as f:
    f.write(schematic)
```

## API Reference

### Core Functions

#### `create_minimal_schematic() -> str`
Creates a minimal valid KiCad schematic.

#### `add_component_to_schematic(schematic, reference, lib_id, value, x, y, rotation, footprint) -> str`
Adds a component to the schematic.

#### `remove_component_from_schematic(schematic, reference) -> str`
Removes a component by reference.

#### `add_hierarchical_label_to_schematic(schematic, name, shape, x, y, rotation) -> str`
Adds a hierarchical label.

#### `update_component_by_uuid(schematic, uuid, updates) -> str`
Updates a component by UUID (planned).

## Contributing

Contributions are welcome! Please see CONTRIBUTING.md for details.

## License

MIT OR Apache-2.0

## Acknowledgments

Originally developed as part of the [circuit-synth](https://github.com/circuit-synth/circuit-synth) project.