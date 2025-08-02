# KiCad to Python Example Projects

This directory contains progressive example projects to test and validate the KiCad-to-Python conversion logic.

## Test Structure Philosophy

Each example follows this pattern:
```
example_name/
├── kicad_source/           # Original KiCad project files
│   ├── project.kicad_pro
│   ├── project.kicad_sch
│   └── project.kicad_pcb   
├── expected_python/        # Expected Python output
│   ├── main.py
│   └── circuit_modules/    # For hierarchical designs
├── test_conversion.py      # Test runner
└── README.md              # Example-specific documentation
```

## Examples (Progressive Complexity)

### 1. Basic Examples
- **simple_resistor_divider** - Two resistors, basic voltage divider
- **led_blinker** - LED + resistor + microcontroller pin connection
- **power_supply_basic** - Linear regulator with input/output capacitors

### 2. Intermediate Examples  
- **usb_interface** - USB connector with data lines and power
- **sensor_interface** - I2C sensor with pull-up resistors
- **multi_rail_power** - Multiple voltage regulators with different outputs

### 3. Advanced Examples
- **hierarchical_design** - Multi-sheet project with subcircuits
- **mixed_signal** - Analog and digital sections with proper isolation
- **complex_mcu_board** - Full microcontroller board with peripherals

## Testing Strategy

1. **Incremental Development**: Start with simple circuits, add complexity gradually
2. **Manual Validation**: Each example includes hand-crafted expected Python output
3. **Automated Testing**: Test runners validate the conversion produces expected results
4. **Round-Trip Testing**: Verify Python → KiCad → Python preserves structure

## Usage

Run individual example tests:
```bash
cd tests/kicad_to_python_examples/simple_resistor_divider
python test_conversion.py
```

Run all example tests:
```bash
pytest tests/kicad_to_python_examples/ -v
```