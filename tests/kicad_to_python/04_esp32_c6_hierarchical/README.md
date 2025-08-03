# ESP32-C6 Hierarchical Circuit Test Suite

## Overview

This test suite provides comprehensive validation of the circuit-synth hierarchical circuit generation workflow using a complex, real-world ESP32-C6 development board design.

## Test Circuit Complexity

### Hierarchical Structure (3 levels)
```
main (0 components - orchestrator only)
├── USB_Port (6 components)
│   ├── J1: USB-C connector (16-pin)
│   ├── R1, R2: 5.1kΩ pull-down resistors
│   ├── D1, D2: ESD protection diodes
│   └── C1: Decoupling capacitor
├── Power_Supply (3 components)
│   ├── U1: AMS1117-3.3 voltage regulator
│   ├── C2: 10µF input capacitor
│   └── C3: 22µF output capacitor
└── ESP32_C6_MCU (4 components)
    ├── U2: ESP32-C6-MINI-1 module
    ├── C4: 100nF decoupling capacitor
    ├── R4, R5: 22Ω USB differential pair resistors
    ├── Debug_Header (1 component)
    │   └── J2: 2x3 programming header
    └── LED_Blinker (2 components)
        ├── D3: Status LED
        └── R3: 330Ω current limiting resistor
```

### Circuit Statistics
- **Total Components**: 16
- **Total Nets**: 15 
- **Hierarchy Levels**: 3
- **Circuit Files**: 6
- **Component Types**: Microcontroller module, connectors, regulators, passives, protection devices

### Key Nets
- **Power**: `VBUS` (5V USB), `VCC_3V3` (regulated 3.3V), `GND`
- **USB**: `USB_DP`, `USB_DM` (differential pair to/from connector)
- **Debug**: `DEBUG_EN`, `DEBUG_IO0`, `DEBUG_RX`, `DEBUG_TX`
- **Control**: `LED_CONTROL` (GPIO for status indication)
- **Internal**: `USB_DP_MCU`, `USB_DM_MCU` (post-termination to MCU)

## Test Coverage

### Core Functionality Tests
1. **Hierarchical Project Detection** - Validates proper identification of 6-circuit hierarchy
2. **Component Distribution** - Verifies correct component assignment across hierarchy levels
3. **Code Structure Generation** - Tests creation of all 6 Python files with proper structure
4. **Import Statement Generation** - Validates lowercase function name imports (critical bug fix)
5. **Parameter Passing** - Tests child circuit instantiation with proper net parameters

### Integration Tests
6. **Round-Trip Execution** - Full KiCad → Python → KiCad workflow validation
7. **Net Connectivity Preservation** - Ensures electrical connectivity through conversion
8. **Component Reference Preservation** - Validates unique component reference assignment
9. **Full Hierarchical Round-Trip** - Tests KiCad → Python → KiCad → Python consistency

### Advanced Validation
10. **Hierarchical Structure Validation** - Confirms 3-level parent-child relationships
11. **Comparative Output Validation** - Compares against known-good reference outputs

## Critical Bug Validations

### Import Statement Bug (Fixed)
**Issue**: System was generating `from USB_Port import USB_Port` when function was `usb_port`
**Test**: `test_import_statement_generation` validates lowercase function imports
**Validation**: Ensures no `ImportError: cannot import name 'USB_Port' from 'USB_Port'`

### Parameter Instantiation Bug (Fixed)  
**Issue**: Child circuits called as `debug_header()` instead of `debug_header(gnd, vcc_3v3, ...)`
**Test**: `test_hierarchical_parameter_passing` validates parameterized instantiation
**Validation**: Ensures no `TypeError: debug_header() missing 6 required positional arguments`

## Test Data Structure

```
04_esp32_c6_hierarchical/
├── README.md                                    # This documentation
├── test_04_esp32_c6_hierarchical_workflow.py    # Comprehensive test suite
├── ESP32_C6_Dev_Board_reference/               # Original KiCad project
│   ├── ESP32_C6_Dev_Board.kicad_pro
│   ├── ESP32_C6_Dev_Board.kicad_sch            # Main schematic
│   ├── USB_Port.kicad_sch                      # USB interface
│   ├── Power_Supply.kicad_sch                  # Voltage regulation
│   ├── ESP32_C6_MCU.kicad_sch                  # MCU + children
│   ├── Debug_Header.kicad_sch                  # Programming interface
│   └── LED_Blinker.kicad_sch                   # Status indication
├── ESP32_C6_Dev_Board_python_reference/        # Generated Python reference
│   ├── main.py                                 # Top-level orchestrator
│   ├── USB_Port.py                             # USB interface implementation
│   ├── Power_Supply.py                         # Power regulation implementation
│   ├── ESP32_C6_MCU.py                         # MCU + child circuit calls
│   ├── Debug_Header.py                         # Programming header implementation
│   └── LED_Blinker.py                          # LED control implementation
└── ESP32_C6_Dev_Board_generated_reference/     # Generated KiCad reference
    ├── ESP32_C6_Dev_Board_generated.kicad_pro  # Project file
    ├── ESP32_C6_Dev_Board_generated.kicad_sch  # Main schematic
    ├── ESP32_C6_Dev_Board_generated.kicad_pcb  # PCB layout
    ├── ESP32_C6_Dev_Board_generated.net        # Netlist
    └── [6 hierarchical .kicad_sch files]       # All subcircuit schematics
```

## Running the Tests

### Individual Test Execution
```bash
# Run specific test
pytest tests/kicad_to_python/04_esp32_c6_hierarchical/test_04_esp32_c6_hierarchical_workflow.py::TestESP32C6HierarchicalWorkflow::test_hierarchical_project_detection -v

# Run all hierarchical tests
pytest tests/kicad_to_python/04_esp32_c6_hierarchical/ -v
```

### Full Test Suite
```bash
# Run with comprehensive output
pytest tests/kicad_to_python/04_esp32_c6_hierarchical/ -v --tb=short

# Run with performance timing
pytest tests/kicad_to_python/04_esp32_c6_hierarchical/ -v --durations=10
```

## Expected Results

All tests should pass, validating:
- ✅ Correct hierarchical structure identification
- ✅ Proper component distribution across hierarchy
- ✅ Valid Python code generation and execution  
- ✅ Successful round-trip KiCad ↔ Python conversion
- ✅ Preserved electrical connectivity and component references
- ✅ Resolution of critical import and parameter bugs

## Performance Benchmarks

This complex circuit provides performance baselines:
- **Parsing Time**: ~1-2 seconds for 6 hierarchical files
- **Python Generation**: ~2-3 seconds for complete codebase  
- **KiCad Generation**: ~3-5 seconds for full project with PCB
- **Round-Trip Time**: ~10-15 seconds total workflow

## Debugging

If tests fail:
1. Check temporary output directories for generated files
2. Review Python execution stdout/stderr for runtime errors
3. Validate KiCad project files can be opened manually
4. Compare generated content against reference implementations

## Historical Context

This test suite was created to validate the successful resolution of critical hierarchical generation bugs that were blocking production use of circuit-synth for complex, real-world circuit designs. It represents the most comprehensive validation of the hierarchical workflow capability.