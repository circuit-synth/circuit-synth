# Manual Setup Guide for Bidirectional Tests

This guide walks you through creating all the required KiCad fixtures for the bidirectional test suite.

## Overview

The test suite requires manually-created KiCad projects as reference fixtures. This is because:
1. We need known-good KiCad projects to test import functionality
2. We need to validate that generated KiCad matches reference implementations
3. Manual creation ensures real-world KiCad format compatibility

## Prerequisites

- ✅ KiCad 8+ installed
- ✅ Standard KiCad symbol libraries available
- ✅ Standard KiCad footprint libraries available
- ✅ ~1-2 hours for complete setup

## Fixture Checklist

### Priority 0 (Required for Core Tests)

- [ ] `fixtures/blank/blank.kicad_pro` - Empty project
- [ ] `fixtures/single_resistor/single_resistor.kicad_pro` - One resistor
- [ ] `fixtures/resistor_divider/resistor_divider.kicad_pro` - R1-R2 divider

### Priority 1 (Required for Full Test Coverage)

- [ ] `fixtures/resistor_divider/positioned_resistor.kicad_pro` - For position tests
- [ ] `fixtures/three_types/three_types.kicad_pro` - R, C, LED mix
- [ ] `fixtures/series_chain/series_chain.kicad_pro` - R1-R2-R3 chain

### Priority 2 (Advanced Tests)

- [ ] `fixtures/hierarchical_simple/hierarchical_simple.kicad_pro` - 2-level hierarchy
- [ ] `fixtures/hierarchical_complex/hierarchical_complex.kicad_pro` - 3-level hierarchy

---

## Step-by-Step Instructions

### Fixture 1: Blank Project (5 min)

**Purpose**: Foundation test for empty circuits

**Steps**:
1. Open KiCad
2. File → New Project → Save as `fixtures/blank/blank.kicad_pro`
3. Open schematic editor (blank.kicad_sch)
4. **Don't add anything** - leave completely empty
5. Save and close
6. Verify files created:
   - `blank.kicad_pro`
   - `blank.kicad_sch`

**Validation**:
```bash
ls -la fixtures/blank/
# Should show: blank.kicad_pro, blank.kicad_sch
```

---

### Fixture 2: Single Resistor (10 min)

**Purpose**: Basic single-component operations

**Schematic Layout**:
```
GND
 |
R1 (10k)
 |
GND
```

**Steps**:
1. File → New Project → `fixtures/single_resistor/single_resistor.kicad_pro`
2. Open schematic editor
3. **Add Resistor**:
   - Press `A` (Add Symbol)
   - Search: "Device:R"
   - Place at (50, 50)
   - Press `E` (Edit) → Properties:
     - Reference: R1
     - Value: 10k
     - Footprint: Resistor_SMD:R_0603_1608Metric
4. **Add GND symbols**:
   - Press `P` (Add Power)
   - Select: "power:GND"
   - Place one below R1 pin 1
   - Place one below R1 pin 2
5. **Wire connections**:
   - Press `W` (Wire)
   - Connect R1 pin 1 to GND
   - Connect R1 pin 2 to GND
6. Save schematic

**Validation**:
```bash
# Open in KiCad and verify:
# - R1 exists with value 10k
# - Footprint is R_0603
# - Both pins connected to GND
```

---

### Fixture 3: Resistor Divider (15 min)

**Purpose**: Classic multi-component circuit for most tests

**Schematic Layout**:
```
VIN
 |
R1 (10k)
 |
VOUT (labeled net)
 |
R2 (10k)
 |
GND
```

**Steps**:
1. File → New Project → `fixtures/resistor_divider/resistor_divider.kicad_pro`
2. Open schematic editor
3. **Add R1**:
   - Symbol: Device:R
   - Place at (50, 50)
   - Reference: R1
   - Value: 10k
   - Footprint: Resistor_SMD:R_0603_1608Metric
4. **Add R2**:
   - Symbol: Device:R
   - Place at (50, 100)
   - Reference: R2
   - Value: 10k
   - Footprint: Resistor_SMD:R_0603_1608Metric
5. **Add Power Symbols**:
   - VIN (power:+3V3 or similar) above R1
   - GND below R2
6. **Add Label for VOUT**:
   - Press `L` (Label)
   - Type: "VOUT"
   - Place between R1 and R2
7. **Wire connections**:
   - VIN → R1 pin 1
   - R1 pin 2 → VOUT → R2 pin 1
   - R2 pin 2 → GND
8. **Arrange neatly** (for position tests)
9. Save schematic

**Validation**:
```bash
# Verify in KiCad:
# - R1, R2 both 10k, R_0603 footprint
# - Three nets: VIN, VOUT, GND
# - VIN → R1 → VOUT → R2 → GND topology
```

---

### Fixture 4: Positioned Resistor (For Position Preservation Tests) (10 min)

**Purpose**: Test that component positions are preserved

**Steps**:
1. Copy `single_resistor.kicad_pro` → `positioned_resistor.kicad_pro`
2. Open `positioned_resistor.kicad_sch`
3. Move R1 to specific position: **(100, 100)** exactly
   - Select R1
   - Press `M` (Move)
   - Type coordinates in properties
4. Save

**Critical**: Position must be exactly (100, 100) for tests to pass

---

### Fixture 5: Three Component Types (15 min)

**Purpose**: Test different component types

**Schematic Layout**:
```
VCC
 |
R1 (10k) → LED (D1) → C1 (100nF)
 |          |           |
GND        GND         GND
```

**Steps**:
1. New Project → `fixtures/three_types/three_types.kicad_pro`
2. Add components:
   - R1: Device:R, 10k, R_0603
   - D1: Device:LED, value "RED", LED_SMD:LED_0603
   - C1: Device:C, 100nF, Capacitor_SMD:C_0603
3. Connect all to VCC and GND
4. Save

---

### Fixture 6: Series Chain (15 min)

**Purpose**: Test multi-hop net connections

**Schematic Layout**:
```
VIN → R1 → MID1 → R2 → MID2 → R3 → GND
```

**Steps**:
1. New Project → `fixtures/series_chain/series_chain.kicad_pro`
2. Add R1, R2, R3 (all 10k, R_0603)
3. Add labels: VIN, MID1, MID2, GND
4. Wire in series: VIN → R1 → MID1 → R2 → MID2 → R3 → GND
5. Save

---

### Fixture 7: Hierarchical Simple (30 min) - ADVANCED

**Purpose**: 2-level hierarchy testing

**Structure**:
```
main.kicad_sch
  └── subcircuit.kicad_sch (hierarchical sheet)
```

**Steps**:
1. New Project → `fixtures/hierarchical_simple/hierarchical_simple.kicad_pro`
2. In main schematic:
   - Add → Hierarchical Sheet
   - Name: "Subcircuit"
   - File: "subcircuit.kicad_sch"
   - Add hierarchical pins: VIN (input), VOUT (output), GND (input)
3. Create `subcircuit.kicad_sch`:
   - Add hierarchical labels matching pins
   - Add R1, R2 voltage divider inside
   - Connect VIN → R1 → VOUT → R2 → GND
4. Back in main schematic:
   - Connect VCC to sheet VIN pin
   - Connect GND to sheet GND pin
   - Label sheet VOUT pin
5. Save both schematics

**This is complex** - refer to KiCad hierarchical design documentation

---

## Validation Checklist

For each fixture, verify:

### File Structure
```bash
cd fixtures/<fixture_name>/
ls
# Should see:
# - <name>.kicad_pro
# - <name>.kicad_sch
# - (optional) <name>.kicad_pcb
```

### KiCad Opens Without Errors
1. Open project in KiCad
2. Open schematic - no error dialogs
3. Check ERC (Electrical Rules Check) - should pass or have expected warnings

### Netlist Export Works
```bash
cd fixtures/<fixture_name>/
kicad-cli sch export netlist --format kicad <name>.kicad_sch
# Should create <name>.net without errors
```

### Python Fixture Matches
Each KiCad fixture should have corresponding Python file with equivalent circuit

---

## Time Estimates

- P0 fixtures (blank, single resistor, resistor divider): **30 minutes**
- P1 fixtures (positioned, three types, series chain): **40 minutes**
- P2 fixtures (hierarchical): **1 hour**

**Total**: ~2 hours for complete setup

---

## Common Issues

### Issue: Symbol Not Found
**Solution**: Update KiCad symbol libraries (Preferences → Manage Symbol Libraries)

### Issue: Footprint Not Found
**Solution**: Update KiCad footprint libraries (Preferences → Manage Footprint Libraries)

### Issue: Can't Create Hierarchical Sheet
**Solution**: Make sure you're in schematic editor, use Add → Hierarchical Sheet

### Issue: Netlist Export Fails
**Solution**: Check all components have footprints assigned

---

## After Setup

Once all fixtures are created:

1. **Commit to git**:
   ```bash
   git add tests/bidirectional_new/fixtures/
   git commit -m "feat: Add KiCad fixtures for bidirectional tests"
   ```

2. **Run validation**:
   ```bash
   pytest tests/bidirectional_new/01_blank_projects/ -v
   # Should pass with fixtures in place
   ```

3. **Mark as complete** in this document

---

## Need Help?

- KiCad Documentation: https://docs.kicad.org/
- Hierarchical Sheets Guide: https://docs.kicad.org/8.0/en/eeschema/eeschema.html#hierarchical-schematics
- Circuit-Synth Issues: https://github.com/circuit-synth/circuit-synth/issues

---

**Last Updated**: 2025-10-25
