# Test 11: Power Rail Connections (GND, VCC)

## What This Tests

Validates power rail distribution, the most fundamental and common circuit pattern - multiple components connected to GND and VCC.

## When This Situation Happens

- Every real circuit needs power distribution
- Multiple components need to connect to common GND rail
- Multiple components need to connect to common VCC rail
- Developer creates circuit with shared power connections in Python
- Generates KiCad and expects power rails to be properly represented

## What Should Work

- Circuit with multiple components sharing GND connections
- Circuit with multiple components sharing VCC connections
- KiCad project correctly represents power rail connections
- All power connections are present and properly labeled

## Manual Test Instructions

```bash
cd /Users/shanemattner/Desktop/circuit-synth/tests/bidirectional/11_power_rails

# Step 1: Create Python circuit with power rails
# Create power_rails.py with multiple components sharing GND and VCC
# Example circuit should have:
#   - 3 resistors (R1, R2, R3)
#   - All connected to common GND rail
#   - All connected to common VCC rail

# Step 2: Generate KiCad project from Python
uv run power_rails.py

# Step 3: Open generated KiCad project
open power_rails/power_rails.kicad_pro

# Step 4: Verify power rail connections in schematic
#   - All three resistors (R1, R2, R3) present
#   - GND power symbol visible and connected to all components
#   - VCC power symbol visible and connected to all components
#   - Net names show GND and VCC rails properly

# Step 5: Verify netlist shows power connections
# Check that netlist file contains:
#   - GND net with multiple component pins
#   - VCC net with multiple component pins
#   - All expected connections present
```

## Expected Result

- ✅ Circuit created with GND and VCC power rails
- ✅ Multiple components sharing power rail connections
- ✅ KiCad project generated with power symbols
- ✅ All components exist in schematic with correct connections
- ✅ Power rail connections properly represented in nets
- ✅ GND and VCC nets visible in schematic

## Why This Is Important

Power rail distribution is fundamental to every real circuit. Proper handling of shared power connections (many components connecting to the same GND/VCC) is essential for practical circuit design.
