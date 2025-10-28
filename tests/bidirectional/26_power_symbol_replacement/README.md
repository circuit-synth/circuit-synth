# Test 26: Power Symbol Replacement

## What This Tests

Validates that power symbols (GND, VCC, +3V3, +5V, -5V) are generated at correct positions and with correct rotations when connected to power nets.

This test suite ensures that:
1. Each power symbol type generates with correct KiCad library reference
2. Power symbols are positioned correctly relative to component pins
3. Positive supplies (VCC, +3V3, +5V) are oriented correctly (0° rotation)
4. Ground and negative supplies (GND, -5V) are oriented correctly (180° rotation for downward-pointing symbols)
5. Multiple power symbols in a single schematic all generate correctly

## When This Situation Happens

- Multi-voltage designs with multiple power rails (e.g., 3.3V, 5V, and GND)
- Circuits using standard KiCad power symbols instead of hierarchical labels
- Power distribution networks requiring proper symbol representation
- Any design following KiCad best practices (power symbols, not labels)

## What Should Work

Each test file validates a specific power symbol type:

1. **test_power_symbol_vcc.py** - VCC symbol (positive supply)
   - Creates single resistor connected to VCC net
   - Expects VCC power symbol at position (30.48, 31.75, 0°)
   - Validates power symbol library reference is `power:VCC`

2. **test_power_symbol_3v3.py** - +3V3 symbol (3.3V supply)
   - Creates single resistor connected to +3V3 net
   - Expects +3V3 power symbol at position (30.48, 31.75, 0°)
   - Validates power symbol library reference is `power:+3V3`

3. **test_power_symbol_5v.py** - +5V symbol (5V supply)
   - Creates single resistor connected to +5V net
   - Expects +5V power symbol at position (30.48, 31.75, 0°)
   - Validates power symbol library reference is `power:+5V`

4. **test_power_symbol_gnd.py** - GND symbol (ground/return)
   - Creates single resistor connected to GND net
   - Expects GND power symbol at position (30.48, 39.37, 0°)
   - Validates power symbol library reference is `power:GND`
   - Note: GND connects to bottom pin (pin 2) of resistor

5. **test_power_symbol_neg5v.py** - -5V symbol (negative supply)
   - Creates single resistor connected to -5V net
   - Expects -5V power symbol at position (30.48, 39.37, 180°)
   - Validates power symbol library reference is `power:-5V`
   - Note: -5V connects to bottom pin (pin 2) of resistor, rotated 180° for downward orientation

6. **test_power_symbol_all.py** - All power symbols combined
   - Creates five resistors, each connected to a different power net
   - Validates all five power symbols in a single schematic
   - Comprehensive test ensuring no conflicts between multiple power symbols

7. **test_multiple_power_nets.py** - Interactive verification
   - Generates circuit with all five power net types
   - Produces KiCad project for manual verification
   - Shows how multiple power nets work in practice

## Manual Test Instructions

### Run Individual Power Symbol Tests

```bash
cd /Users/shanemattner/Desktop/circuit-synth2/tests/bidirectional/26_power_symbol_replacement

# Test VCC symbol
uv run test_power_symbol_vcc.py

# Test +3V3 symbol
uv run test_power_symbol_3v3.py

# Test +5V symbol
uv run test_power_symbol_5v.py

# Test GND symbol
uv run test_power_symbol_gnd.py

# Test -5V symbol
uv run test_power_symbol_neg5v.py

# Test all symbols combined
uv run test_power_symbol_all.py
```

### Run All Tests

```bash
# Run pytest to execute all tests
pytest test_power_symbol_vcc.py test_power_symbol_3v3.py test_power_symbol_5v.py \
       test_power_symbol_gnd.py test_power_symbol_neg5v.py test_power_symbol_all.py -v
```

### Generate and Inspect in KiCad

```bash
# Generate a multi-power circuit for visual inspection
uv run test_multiple_power_nets.py

# Open in KiCad to verify power symbols visually
open multiple_power_nets/multiple_power_nets.kicad_pro
```

## Expected Result

### Individual Tests Pass When:

- ✅ Power symbol library reference is correct (`power:VCC`, `power:+3V3`, etc.)
- ✅ Power symbol position matches expected coordinates
- ✅ Power symbol rotation matches expected value
- ✅ Positive supplies (VCC, +3V3, +5V) have 0° rotation
- ✅ Ground and negative supplies (GND, -5V) have appropriate rotation for orientation
- ✅ Power symbol connects to correct component pin

### Combined Test Passes When:

- ✅ All five power symbols generate in single schematic
- ✅ No conflicts or errors with multiple power net types
- ✅ Each power symbol has correct position and rotation
- ✅ No unexpected hierarchical labels alongside power symbols

### Visual Verification in KiCad:

- ✅ VCC shows as upward-pointing arrow (⬆ VCC)
- ✅ +3V3 shows as upward-pointing arrow (⬆ +3V3)
- ✅ +5V shows as upward-pointing arrow (⬆ +5V)
- ✅ GND shows as ground symbol (⏚ GND)
- ✅ -5V shows as downward-pointing arrow (⬇ -5V)
- ✅ All symbols are properly connected to component pins

## Why This Is Critical

**Power symbols are fundamental to circuit design:**

1. **Global Connection Semantics** - Power symbols connect globally across entire schematic. Unlike hierarchical labels, GND anywhere connects to GND everywhere. This is essential for proper electrical representation.

2. **KiCad Best Practice** - Professional KiCad designs use power symbols, not hierarchical labels for power nets. They provide visual clarity and correct electrical semantics.

3. **Multi-Sheet Designs** - Power symbols maintain global connections across multiple hierarchical sheets. Hierarchical labels (the alternative) are sheet-local and don't connect across hierarchy boundaries.

4. **Standard Visualization** - Power symbols provide clear visual indication of supply type:
   - Upward arrow for positive supplies (VCC, +3V3, +5V)
   - Downward symbols for return paths (GND, -5V)
   - Immediate recognition of power distribution

5. **Integration with Real Projects** - Any circuit with multiple voltage supplies (3.3V, 5V, GND) needs proper power symbol handling. This includes:
   - Mixed-voltage microcontroller designs
   - Analog/digital power separation
   - Multi-rail power distribution
   - Proper electrical net validation

6. **Round-Trip Fidelity** - When users export from Python and import back to Python, power symbols should be preserved. This test validates that power symbols are generated correctly in the first place.

## Edge Cases Covered

- Multiple power net types in single circuit
- Both positive (upward) and negative/ground (downward) supplies
- Correct rotation based on net name semantics
- Position consistency for power symbols connected to different pin locations
- Library reference accuracy for KiCad integration

## Related Tests

- **Test 11** - Symbol rotation (related positioning behavior)
- **Test 04** - Round-trip cycle (tests preservation of symbols)
- **Test 15** - Net operations (tests net creation and connection)

## Related Issues

- **#346** - Power symbol rotation algorithm
- **#362** - Fix power symbol rotation (fixed)
- **#363** - Correct import path for Net class in PCB generator
