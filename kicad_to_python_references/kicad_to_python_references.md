
# KiCad-to-Python Reference Test Cases

## Essential KiCad-to-Python References (10 Total)

### Hierarchy Complexity Testing
- 01_reference: resistor divider on top level schematic
- 02_reference: resistor divider on first child hierarchy
- 03_reference: resistor divider on top level and first child hierarchy
- 04_reference: resistor divider on first child hierarchy and second child hierarchy
- 05_reference: 3 nested levels of resistor dividers
- 06_reference: 3 nested levels of resistor dividers in 2 separate branches

### Component & Circuit Complexity Testing
- 07_reference: Mixed components (resistor, capacitor, LED) single level
- 08_reference: Microcontroller circuit (ESP32 + power + USB)
- 09_reference: Power nets across hierarchy (VCC_3V3, GND distribution)
- 10_reference: Real ESP32 dev board (your current working example)

## Test Coverage

This set provides comprehensive testing of:
- **Hierarchy complexity** (01-06): Simple to complex nesting patterns
- **Component variety** (07-08): Beyond just resistors  
- **Net complexity** (09): Power distribution testing
- **Real-world validation** (10): Complete working circuit

These 10 references will thoroughly test the conversion logic without overwhelming the testing process.
