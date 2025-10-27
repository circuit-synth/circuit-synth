# Test 13: Power Rail Connections (GND, VCC)

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
cd /Users/shanemattner/Desktop/circuit-synth/tests/bidirectional/13_power_rails

# Step 1: Generate KiCad project from Python (3 resistors with GND/VCC)
uv run power_rails.py
open power_rails/power_rails.kicad_pro
# Verify in KiCad schematic:
#   - All three resistors (R1, R2, R3) present
#   - GND hierarchical labels visible and connected to all components
#   - VCC hierarchical labels visible and connected to all components
#   - Net names show GND and VCC rails properly

# Step 2: Verify netlist shows power connections
# Check netlist file contains:
#   - GND net with multiple component pins
#   - VCC net with multiple component pins
#   - All expected connections present
```

## Expected Result

- ✅ Circuit created with GND and VCC power rails
- ✅ Multiple components sharing power rail connections
- ✅ KiCad project generated with hierarchical labels for power
- ✅ All components exist in schematic with correct connections
- ✅ Six hierarchical labels total: GND×3 and VCC×3 (one pair per component)
- ✅ NO physical wires between components
- ✅ Electrical connections established by matching label names
- ✅ Power rail connections properly represented in nets

**Note**: Uses `hierarchical_label` format for power rails - matching label names create power distribution without wires

## Why This Is Important

Power rail distribution is fundamental to every real circuit. Proper handling of shared power connections (many components connecting to the same GND/VCC) is essential for practical circuit design.
