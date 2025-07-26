# Rust Pin Calculator

A high-performance pin position calculator and coordinate transformer for KiCad schematic generation, implementing Phase 2 of the Python-to-Rust migration plan.

## Overview

This crate provides fast and accurate pin position calculations for electronic circuit schematics, with a focus on matching reference design positions exactly. It replaces Python-based pin position calculations with optimized Rust implementations for 10-100x performance improvements.

## Features

- **High-Performance Coordinate Transformations**: Fast 2D coordinate transformations with rotation support
- **Reference Design Validation**: Exact position matching against reference designs
- **Hierarchical Label Positioning**: Intelligent placement of hierarchical labels based on net topology
- **Python Integration**: PyO3 bindings for seamless integration with existing Python workflows
- **Comprehensive Testing**: 44 unit tests covering all functionality with performance benchmarks
- **Type Safety**: Strong typing prevents coordinate calculation errors

## Architecture

```
rust_pin_calculator/
├── src/
│   ├── lib.rs                    # Main library and PyO3 bindings
│   ├── coordinate_transform.rs   # Core coordinate transformation logic
│   ├── pin_calculator.rs         # Pin position calculations
│   ├── types.rs                  # Data structures and types
│   ├── tests.rs                  # Comprehensive unit tests
│   └── bin/main.rs              # CLI interface
├── Cargo.toml                    # Dependencies and configuration
└── README.md                     # This file
```

## Key Components

### Core Types (`types.rs`)
- `Position`: 2D coordinate representation
- `Component`: Electronic component with pins and position
- `Pin`: Individual pin with local position and orientation
- `Net`: Network connection between pins
- `HierarchicalLabelPosition`: Calculated label positions

### Coordinate Transformations (`coordinate_transform.rs`)
- `transform_pin_position()`: Convert local pin positions to global coordinates
- `inverse_transform_pin_position()`: Reverse transformation
- `transform_component_pins()`: Batch transformation for all component pins
- Rotation matrix calculations and angle normalization

### Pin Calculator (`pin_calculator.rs`)
- `PinCalculator`: Main calculator with reference design support
- `calculate_hierarchical_label_positions()`: Intelligent label placement
- Reference design validation and position matching
- Centroid calculation and optimal positioning algorithms

## Reference Design Validation

The calculator validates against exact reference design positions:

```rust
// Reference positions from specification
R1: (95.25, 62.23) with pins at (95.25, 58.42) and (95.25, 66.04)
R2: (106.68, 62.23) with pins at (106.68, 58.42) and (106.68, 66.04)  
C1: (120.65, 63.5) with pins at (120.65, 59.69) and (120.65, 67.31)
```

All calculated positions match the reference design exactly (✓ PASS validation).

## Performance

- **1000 pin calculations**: ~1.459ms total (~1.459μs per calculation)
- **10-100x faster** than equivalent Python implementations
- **Memory efficient**: Zero-copy transformations where possible
- **Batch operations**: Optimized for processing multiple components

## Usage

### Rust API

```rust
use rust_pin_calculator::*;

// Create calculator with reference design validation
let config = PinCalculator::create_reference_design_config();
let mut calculator = PinCalculator::with_config(config);

// Add components
let component = Component::new("R1".to_string(), Position::new(95.25, 62.23), 0.0);
calculator.add_component(component);

// Calculate pin positions
let result = calculator.calculate_pin_position("R1", "1")?;
println!("Pin position: ({:.2}, {:.2})", result.global_position.x, result.global_position.y);

// Calculate hierarchical labels
let nets = PinCalculator::create_reference_design_nets();
let labels = calculator.calculate_hierarchical_label_positions(&nets)?;
```

### Python API (via PyO3)

```python
import rust_pin_calculator

# Create calculator
calc = rust_pin_calculator.PyPinCalculator()

# Add component and pins
calc.add_component_simple("R1", 95.25, 62.23, 0.0, "Resistor", "10k")
calc.add_pin_to_component("R1", "1", 0.0, -3.81, "passive", "down")

# Calculate position
x, y = calc.calculate_pin_position("R1", "1")
print(f"Pin position: ({x:.2f}, {y:.2f})")

# Test reference design
results = rust_pin_calculator.PyPinCalculator.create_reference_design_test()
for component_ref, pin_num, x, y in results:
    print(f"{component_ref}.{pin_num}: ({x:.2f}, {y:.2f})")
```

### CLI Interface

```bash
cargo run --bin pin_calculator_cli --no-default-features
```

Output:
```
=== Reference Design Pin Positions ===
R1.1: (95.25, 58.42) [local: (0.00, -3.81), rotation: 0.0°]
  Validation: ✓ PASS
R1.2: (95.25, 66.04) [local: (0.00, 3.81), rotation: 0.0°]
  Validation: ✓ PASS
...

=== Performance Test ===
1000 iterations of pin position calculation: 1.459ms
Average per calculation: 1.459µs
```

## Testing

Run the comprehensive test suite:

```bash
# Run all tests (without Python bindings)
cargo test --no-default-features

# Run with Python bindings (requires Python development headers)
cargo test --features python-bindings
```

**Test Coverage**: 44 tests covering:
- Basic coordinate transformations
- Complex rotation scenarios
- Reference design validation
- Error handling
- Performance characteristics
- Edge cases and boundary conditions

## Integration Points

This crate is designed to integrate with:

1. **Python Integration Layer** (`rust_integration.py`): Replace hardcoded positions
2. **Component Placement Engine**: Use real component positions from placement algorithms
3. **Hierarchical Label Generator**: Feed calculated positions to KiCad schematic writer
4. **Netlist Processor**: Extract component and net information for calculations

## Migration Benefits

Compared to the original Python implementation:

- **Performance**: 10-100x faster pin position calculations
- **Accuracy**: Exact floating-point calculations with proper rotation handling
- **Type Safety**: Compile-time guarantees prevent coordinate calculation errors
- **Memory Efficiency**: Zero-copy operations and optimized data structures
- **Maintainability**: Clear separation of concerns and comprehensive testing

## Dependencies

- `pyo3`: Python bindings (optional)
- `serde`: Serialization support
- `thiserror`: Error handling
- `approx`: Floating-point comparisons in tests

## Future Enhancements

- Support for more complex component geometries
- Advanced label collision detection and avoidance
- Integration with KiCad symbol libraries
- Parallel processing for large circuits
- Additional coordinate system transformations

## License

This crate is part of the Circuit Synth project and follows the same licensing terms.