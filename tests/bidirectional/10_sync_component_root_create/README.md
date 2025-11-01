# Test 10: Add Component to Root Sheet (Sync Preservation Test)

## What This Tests

Validates that adding a new component (R2) to an existing circuit preserves ALL other schematic elements:
- Existing components (R1, C1) remain unchanged
- Component positions preserved
- Component values preserved
- Component footprints preserved
- Power symbols (VCC, GND) preserved
- Net labels (DATA) preserved

This is a **comprehensive preservation test** using kicad-sch-api to verify exact schematic state.

## When This Situation Happens

- Developer has an existing circuit with components (R1, C1)
- Needs to add a new component (R2) to the circuit
- Modifies Python code to include R2
- Regenerates KiCad project
- **Expects**: Only R2 added, everything else exactly the same

## What Should Work

✅ Initial circuit with R1, C1 generates successfully
✅ Python code modified to add R2 component
✅ Regenerated KiCad project contains R1, R2, C1
✅ R1 completely unchanged (value, footprint, position, rotation)
✅ C1 completely unchanged (value, footprint, position, rotation)
✅ Power symbols (VCC, GND) preserved
✅ Net labels (DATA) preserved

## Manual Test Instructions

```bash
cd tests/bidirectional/10_sync_component_root_create

# Step 1: Generate initial KiCad project (R1, C1 only)
uv run comprehensive_root.py
open comprehensive_root/comprehensive_root.kicad_pro
# Verify: R1 (10k) and C1 (100nF) present, no R2

# Step 2: Edit comprehensive_root.py
# Uncomment lines 26-32 to enable R2:
#   r2 = Component(
#       symbol="Device:R",
#       ref="R2",
#       value="4.7k",
#       footprint="Resistor_SMD:R_0603_1608Metric"
#   )

# Step 3: Regenerate KiCad project
uv run comprehensive_root.py

# Step 4: Open regenerated project in KiCad
open comprehensive_root/comprehensive_root.kicad_pro

# Step 5: Verify preservation
#   ✅ R1 still at same position with value=10k
#   ✅ C1 still at same position with value=100nF
#   ✅ R2 added with value=4.7k
#   ✅ VCC and GND power symbols present
#   ✅ DATA net label present
```

## Automated Test

```bash
# Run automated preservation test
pytest test_add_component.py -v

# Keep output for manual inspection
pytest test_add_component.py -v --keep-output
```

## Expected Result

### Step 1: Initial State
- Components: R1 (10k), C1 (100nF)
- Power: VCC, GND
- Nets: DATA (connecting R1-C1)

### Step 2: After Adding R2
- Components: R1 (10k), **R2 (4.7k)**, C1 (100nF)
- R1 position: **PRESERVED** (not moved)
- R1 value: **PRESERVED** (still 10k)
- C1 position: **PRESERVED** (not moved)
- C1 value: **PRESERVED** (still 100nF)
- Power: VCC, GND **PRESERVED**
- Nets: DATA **PRESERVED**
- R2 placed in available space (no overlap)

## What This Tests (Technical)

This test validates the **bidirectional synchronization preservation logic**:

1. **Python → KiCad generation**: Creates initial schematic
2. **Python modification**: Adds R2 to circuit definition
3. **Sync operation**: `generate_kicad_project()` detects existing schematic
4. **Diff calculation**: Determines R2 is new, R1/C1 exist
5. **Preservation**: Keeps R1, C1 positions/properties intact
6. **Addition**: Adds R2 without disrupting existing components

Uses **kicad-sch-api** to programmatically verify:
- Exact component counts
- Component property values
- Component positions (coordinates)
- Power symbol preservation
- Net label preservation

## Related Tests

- Test 11: Update component value (preserve position)
- Test 12: Rename component reference (preserve properties)
- Test 13: Delete component (preserve others)
