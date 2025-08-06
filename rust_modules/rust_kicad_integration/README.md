# Rust KiCad Schematic Writer

[![CI](https://github.com/circuit-synth/circuit-synth/actions/workflows/ci.yml/badge.svg)](https://github.com/circuit-synth/circuit-synth/actions)
[![Documentation](https://docs.rs/rust_kicad_schematic_writer/badge.svg)](https://docs.rs/rust_kicad_schematic_writer)
[![Crates.io](https://img.shields.io/crates/v/rust_kicad_schematic_writer.svg)](https://crates.io/crates/rust_kicad_schematic_writer)

High-performance Rust library for generating and editing KiCad schematic files with optional Python bindings.

## Features

- 🚀 **High Performance** - Written in Rust for maximum speed and safety
- 📝 **Simple API** - Easy-to-use functions for creating schematics quickly
- 🔧 **Component Management** - Full support for component placement and configuration
- ⚡ **Net Connections** - Define electrical connections between components
- 📊 **Hierarchical Design** - Support for complex multi-level circuit designs
- 🎯 **Clean S-expressions** - Proper KiCad-compatible output without dotted pairs
- 🐍 **Python Bindings** - Optional PyO3 integration for Python users
- 📏 **Multiple Paper Sizes** - A4, A3, A2, A1, A0, Letter, Legal
- ✅ **Well Tested** - Comprehensive unit and integration tests
- 📈 **Benchmarked** - Performance benchmarks for critical paths

## Installation

### As a Rust Library

Add to your `Cargo.toml`:

```toml
[dependencies]
rust_kicad_schematic_writer = "0.1"
```

### With Python Bindings

```bash
# Build from source with Python support
cd rust_modules/rust_kicad_integration
maturin build --release -F python
pip install target/wheels/*.whl
```

## Quick Start

### Rust Usage

```rust
use rust_kicad_schematic_writer::schematic_api::*;

// Create minimal A4 schematic
let schematic = create_minimal_schematic();

// Create schematic with specific paper size
let schematic = create_empty_schematic("A3");

// Save to file
std::fs::write("my_schematic.kicad_sch", schematic)?;
```

### Python Usage

```python
import rust_kicad_schematic_writer as kicad

# Create minimal A4 schematic
schematic = kicad.create_minimal_schematic()

# Save to file
with open("my_schematic.kicad_sch", "w") as f:
    f.write(schematic)
```

### Advanced Circuit Generation

```rust
use rust_kicad_schematic_writer::{
    CircuitData, Component, Net, PinConnection, Pin, Position,
    RustSchematicWriter, SchematicConfig,
};

// Create circuit with components and nets
let circuit = CircuitData {
    name: "voltage_divider".to_string(),
    components: vec![
        Component {
            reference: "R1".to_string(),
            lib_id: "Device:R".to_string(),
            value: "10k".to_string(),
            position: Position { x: 100.0, y: 50.0 },
            rotation: 90.0,
            pins: vec![/* ... */],
        },
    ],
    nets: vec![
        Net {
            name: "VCC".to_string(),
            connected_pins: vec![/* ... */],
        },
    ],
    subcircuits: vec![],
};

// Generate schematic
let config = SchematicConfig::default();
let writer = RustSchematicWriter::new(circuit, config);
writer.write_to_file("output.kicad_sch")?;
```

## Project Structure

```
rust_kicad_integration/
├── src/                    # Source code
│   ├── lib.rs             # Main library interface
│   ├── schematic_api.rs   # Simple API functions
│   ├── types.rs           # Core data structures
│   ├── s_expression.rs    # S-expression generation
│   ├── hierarchical_labels.rs # Hierarchical label support
│   └── python_bindings.rs # Optional Python interface
├── examples/              # Example programs
│   ├── basic_schematic.rs
│   ├── circuit_with_components.rs
│   └── hierarchical_design.rs
├── tests/                 # Integration tests
│   └── integration_test.rs
├── benches/              # Performance benchmarks
│   └── schematic_generation.rs
└── .github/workflows/    # CI/CD pipeline
    └── ci.yml
```

## Examples

Run the examples:

```bash
# Create output directory
mkdir -p examples/output

# Run basic schematic example
cargo run --example basic_schematic

# Run circuit with components
cargo run --example circuit_with_components

# Run hierarchical design
cargo run --example hierarchical_design
```

## Development

### Running Tests

```bash
# Run all tests
cargo test

# Run without Python features
cargo test --no-default-features

# Run with Python features
cargo test --features python

# Run benchmarks
cargo bench
```

### Building Documentation

```bash
# Build and open documentation
cargo doc --open
```

### Code Quality

```bash
# Format code
cargo fmt

# Run linter
cargo clippy -- -D warnings
```

## Best Practices

This crate follows Rust best practices:

- ✅ **Comprehensive Documentation** - All public APIs are documented
- ✅ **Error Handling** - Custom error types with `thiserror`
- ✅ **Testing** - Unit tests, integration tests, and benchmarks
- ✅ **CI/CD** - Automated testing on multiple platforms
- ✅ **Examples** - Clear examples for common use cases
- ✅ **Modular Design** - Clean separation of concerns
- ✅ **Optional Features** - Python bindings are optional

## Contributing

This module is part of the circuit-synth project. When contributing:

1. **Write tests first** - Follow TDD practices
2. **Document your code** - Add rustdoc comments for public APIs
3. **Maintain compatibility** - Test generated files in KiCad
4. **Keep it simple** - Simple API should remain simple
5. **Run CI locally** - `cargo test && cargo clippy && cargo fmt`

## License

MIT OR Apache-2.0

## Links

- [Documentation](https://docs.rs/rust_kicad_schematic_writer)
- [Crates.io](https://crates.io/crates/rust_kicad_schematic_writer)
- [GitHub Repository](https://github.com/circuit-synth/circuit-synth)