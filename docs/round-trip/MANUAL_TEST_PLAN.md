# Round-Trip Preservation - Manual Test Plan

**Purpose:** Systematically exercise and validate all round-trip preservation features through hands-on testing.

**Date:** 2025-10-12
**Status:** 🔄 Ready for Testing

---

## Prerequisites

- [ ] All automated tests passing (11/11)
- [ ] KiCad installed and accessible
- [ ] circuit-synth development environment set up
- [ ] Clean working directory

## Test Environment Setup

```bash
# Navigate to test directory
cd ~/Desktop/circuit-synth/docs/round-trip

# Tests will create projects in test-projects/ subdirectory
# You can also copy examples/test1_basic_divider.py to modify it
```

---

## Test 1: Basic Voltage Divider Generation

**Objective:** Generate a simple voltage divider circuit and verify it opens correctly in KiCad.

### Steps

1. Use the provided `examples/test1_basic_divider.py` or create your own:
```python
from circuit_synth import Component, Net, circuit

@circuit(name="voltage_divider")
def voltage_divider():
    r1 = Component("Device:R", ref="R1", value="10k",
                   footprint="Resistor_SMD:R_0603_1608Metric")
    r2 = Component("Device:R", ref="R2", value="10k",
                   footprint="Resistor_SMD:R_0603_1608Metric")

    vin = Net("VIN")
    vout = Net("VOUT")
    gnd = Net("GND")

    r1[1] += vin
    r1[2] += vout
    r2[1] += vout
    r2[2] += gnd

    return r1, r2

c = voltage_divider()
c.generate_kicad_project("voltage_divider", force_regenerate=True, generate_pcb=False)
```

2. Run the script:
```bash
uv run python examples/test1_basic_divider.py
```

3. Open `test-projects/voltage_divider/voltage_divider.kicad_sch` in KiCad

### Expected Results

- [ ] Schematic opens without errors
- [ ] R1 and R2 components present
- [ ] Components have correct values (10k)
- [ ] Components have correct footprints (R_0603_1608Metric)
- [ ] Hierarchical labels present: VIN, VOUT, GND

### Notes

**Status:** ⬜ Not Started / ⏳ In Progress / ✅ Passed / ❌ Failed

---

## Test 2: Replace Hierarchical Labels with Wires

**Objective:** Manually wire the circuit in KiCad and verify wires are preserved.

### Steps

1. In KiCad schematic editor:
   - Delete all hierarchical labels (VIN, VOUT, GND)
   - Use the "Wire" tool (W) to connect:
     - R1 pin 1 → add wire going left, add label "VIN"
     - R1 pin 2 → R2 pin 1 (direct wire connection)
     - R2 pin 1 → add wire going right, add label "VOUT"
     - R2 pin 2 → add wire going down, add label "GND"
   - Save the schematic (Ctrl+S)

2. Record wire positions (for verification later):
   - Note approximate coordinates of each wire segment
   - Take a screenshot for reference

### Expected Results

- [ ] All wires drawn successfully
- [ ] Net labels added successfully
- [ ] Schematic saves without errors
- [ ] ERC shows proper connectivity

### Notes

**Status:** ⬜ Not Started / ⏳ In Progress / ✅ Passed / ❌ Failed

---

## Test 3: Re-run Python Without Changes

**Objective:** Verify that re-running the same Python code preserves manual wiring.

### Steps

1. Run the same Python script again (WITHOUT modifying the code):
```bash
uv run python examples/test1_basic_divider.py
```

2. Open the schematic in KiCad again

3. Compare with your screenshot from Test 2

### Expected Results

- [ ] All manual wires are still present
- [ ] Wire positions unchanged
- [ ] Net labels are still present
- [ ] R1 and R2 values unchanged (10k)
- [ ] No hierarchical labels reappeared

### Critical Verification

**CRITICAL:** If wires disappeared, this is a MAJOR BUG. Wire preservation is the core feature.

### Notes

**Status:** ⬜ Not Started / ⏳ In Progress / ✅ Passed / ❌ Failed

---

## Test 4: Add Component Manually in KiCad

**Objective:** Verify that manually added components are preserved.

### Steps

1. In KiCad schematic editor:
   - Press "A" to add a component
   - Search for "Device:C"
   - Add a capacitor C1 with value "100n"
   - Position it near VOUT net
   - Add wire from VOUT to C1 pin 1
   - Add wire from C1 pin 2 to GND
   - Save the schematic

2. Record C1 details:
   - Position: (x, y) = _______
   - Connections: VOUT, GND
   - Screenshot for reference

### Expected Results

- [ ] C1 added successfully
- [ ] C1 connected to VOUT and GND
- [ ] Schematic saves without errors

### Notes

**Status:** ⬜ Not Started / ⏳ In Progress / ✅ Passed / ❌ Failed

---

## Test 5: Update R1 Value in Python

**Objective:** Verify that Python changes propagate while preserving manual additions.

### Steps

1. Modify `examples/test1_basic_divider.py` - change R1 value to 22k:
```python
r1 = Component("Device:R", ref="R1", value="22k",  # Changed from 10k
               footprint="Resistor_SMD:R_0603_1608Metric")
```

2. Run with `force_regenerate=False`:
```bash
uv run python examples/test1_basic_divider.py
```

3. Open schematic in KiCad

### Expected Results

- [ ] R1 value updated to 22k ✅
- [ ] R2 value unchanged (10k)
- [ ] Manual C1 still present ✅
- [ ] All manual wires still present ✅
- [ ] Net labels still present ✅
- [ ] C1 position unchanged ✅

### Critical Verification

**CRITICAL:** Both Python changes (R1 value) AND manual additions (C1, wires) should coexist.

### Notes

**Status:** ⬜ Not Started / ⏳ In Progress / ✅ Passed / ❌ Failed

---

## Test 6: Move Components in KiCad

**Objective:** Verify that component repositioning is preserved.

### Steps

1. In KiCad schematic editor:
   - Select R1 and move it to a new position
   - Select R2 and move it to a new position
   - Adjust wires as needed to maintain connections
   - Save the schematic

2. Record new positions:
   - R1: (x, y) = _______
   - R2: (x, y) = _______
   - Screenshot for reference

### Expected Results

- [ ] Components move successfully
- [ ] Wires adjust automatically
- [ ] Schematic saves without errors

### Notes

**Status:** ⬜ Not Started / ⏳ In Progress / ✅ Passed / ❌ Failed

---

## Test 7: Update R2 Value and Verify Positions Preserved

**Objective:** Verify component positions preserved during value updates.

### Steps

1. Modify `test1_basic_divider.py` - change R2 value to 47k:
```python
r2 = Component("Device:R", ref="R2", value="47k",  # Changed from 10k
               footprint="Resistor_SMD:R_0603_1608Metric")
```

2. Run the script:
```bash
uv run python test1_basic_divider.py
```

3. Open schematic and compare with Test 6 screenshot

### Expected Results

- [ ] R1 value still 22k (from Test 5)
- [ ] R2 value updated to 47k ✅
- [ ] R1 position preserved from Test 6 ✅
- [ ] R2 position preserved from Test 6 ✅
- [ ] Manual C1 still present ✅
- [ ] All wires still intact ✅

### Notes

**Status:** ⬜ Not Started / ⏳ In Progress / ✅ Passed / ❌ Failed

---

## Test 8: Add Power Symbols in KiCad

**Objective:** Verify that power symbols are preserved.

### Steps

1. In KiCad schematic editor:
   - Press "P" to add power port
   - Search for "power:VCC"
   - Place VCC symbol near VIN net
   - Connect it to VIN with a wire
   - Add another power port: "power:GND"
   - Place GND symbol near GND net
   - Connect it to GND with a wire
   - Save the schematic

2. Record power symbols:
   - VCC (#PWR01): (x, y) = _______
   - GND (#PWR02): (x, y) = _______

### Expected Results

- [ ] VCC power symbol added
- [ ] GND power symbol added
- [ ] Both connected to appropriate nets
- [ ] Schematic saves without errors

### Notes

**Status:** ⬜ Not Started / ⏳ In Progress / ✅ Passed / ❌ Failed

---

## Test 9: Change Footprints in Python

**Objective:** Verify footprint updates propagate while preserving layout.

### Steps

1. Modify `test1_basic_divider.py` - change both resistors to 0805:
```python
r1 = Component("Device:R", ref="R1", value="22k",
               footprint="Resistor_SMD:R_0805_2012Metric")  # Changed from 0603
r2 = Component("Device:R", ref="R2", value="47k",
               footprint="Resistor_SMD:R_0805_2012Metric")  # Changed from 0603
```

2. Run the script:
```bash
uv run python test1_basic_divider.py
```

3. Open schematic in KiCad

### Expected Results

- [ ] R1 footprint updated to R_0805_2012Metric ✅
- [ ] R2 footprint updated to R_0805_2012Metric ✅
- [ ] Component positions unchanged ✅
- [ ] Component values unchanged (22k, 47k)
- [ ] Manual C1 still present ✅
- [ ] Power symbols still present ✅
- [ ] All wires intact ✅

### Notes

**Status:** ⬜ Not Started / ⏳ In Progress / ✅ Passed / ❌ Failed

---

## Test 10: Rotate Components in KiCad

**Objective:** Verify component rotation is preserved.

### Steps

1. In KiCad schematic editor:
   - Select R1 and press "R" to rotate 90 degrees
   - Select C1 and press "R" to rotate 90 degrees
   - Adjust wires as needed
   - Save the schematic

2. Record rotations:
   - R1 angle: _______°
   - C1 angle: _______°
   - Screenshot for reference

### Expected Results

- [ ] Components rotate successfully
- [ ] Wires adjust to maintain connections
- [ ] Schematic saves without errors

### Notes

**Status:** ⬜ Not Started / ⏳ In Progress / ✅ Passed / ❌ Failed

---

## Test 11: Update Values and Verify Rotation Preserved

**Objective:** Verify rotation preserved during value updates.

### Steps

1. Modify `test1_basic_divider.py` - change R1 value to 100k:
```python
r1 = Component("Device:R", ref="R1", value="100k",  # Changed from 22k
               footprint="Resistor_SMD:R_0805_2012Metric")
```

2. Run the script:
```bash
uv run python test1_basic_divider.py
```

3. Open schematic and compare with Test 10 screenshot

### Expected Results

- [ ] R1 value updated to 100k ✅
- [ ] R1 rotation preserved ✅
- [ ] C1 rotation preserved ✅
- [ ] All other elements unchanged
- [ ] Wires intact ✅
- [ ] Power symbols intact ✅

### Notes

**Status:** ⬜ Not Started / ⏳ In Progress / ✅ Passed / ❌ Failed

---

## Test 12: Add Third Resistor in Python

**Objective:** Verify new components can be added via Python without breaking manual edits.

### Steps

1. Modify `test1_basic_divider.py` - add R3:
```python
@circuit(name="voltage_divider")
def voltage_divider():
    r1 = Component("Device:R", ref="R1", value="100k",
                   footprint="Resistor_SMD:R_0805_2012Metric")
    r2 = Component("Device:R", ref="R2", value="47k",
                   footprint="Resistor_SMD:R_0805_2012Metric")
    r3 = Component("Device:R", ref="R3", value="1k",  # NEW
                   footprint="Resistor_SMD:R_0805_2012Metric")

    vin = Net("VIN")
    vout = Net("VOUT")
    gnd = Net("GND")

    r1[1] += vin
    r1[2] += vout
    r2[1] += vout
    r2[2] += gnd
    r3[1] += vout  # NEW - parallel with R2
    r3[2] += gnd   # NEW

    return r1, r2, r3
```

2. Run the script:
```bash
uv run python test1_basic_divider.py
```

3. Open schematic in KiCad

### Expected Results

- [ ] R3 appears in schematic ✅
- [ ] R3 has correct value (1k)
- [ ] R1 and R2 unchanged
- [ ] Manual C1 still present ✅
- [ ] All rotations preserved ✅
- [ ] All wires intact ✅
- [ ] Power symbols intact ✅

### Notes

**Status:** ⬜ Not Started / ⏳ In Progress / ✅ Passed / ❌ Failed

---

## Test 13: Complex Wiring in KiCad

**Objective:** Test preservation of complex wiring patterns.

### Steps

1. In KiCad schematic editor:
   - Wire R3 to VOUT net (if not auto-connected)
   - Add multiple wire segments with junctions
   - Add additional net labels on various wire segments
   - Create a bus of wires for visual clarity
   - Add wire annotations/notes
   - Save the schematic

2. Document complex wiring:
   - Number of junctions: _______
   - Number of net labels: _______
   - Screenshot for reference

### Expected Results

- [ ] Complex wiring added successfully
- [ ] Junctions created automatically where needed
- [ ] Multiple net labels on same net work correctly
- [ ] Schematic saves without errors

### Notes

**Status:** ⬜ Not Started / ⏳ In Progress / ✅ Passed / ❌ Failed

---

## Test 14: Final Comprehensive Update

**Objective:** Verify all manual edits preserved after comprehensive Python changes.

### Steps

1. Modify `test1_basic_divider.py` - make multiple changes:
```python
@circuit(name="voltage_divider")
def voltage_divider():
    r1 = Component("Device:R", ref="R1", value="220k",  # Changed value
                   footprint="Resistor_SMD:R_1206_3216Metric")  # Changed footprint
    r2 = Component("Device:R", ref="R2", value="100k",  # Changed value
                   footprint="Resistor_SMD:R_0805_2012Metric")
    r3 = Component("Device:R", ref="R3", value="2.2k",  # Changed value
                   footprint="Resistor_SMD:R_0805_2012Metric")

    vin = Net("VIN")
    vout = Net("VOUT")
    gnd = Net("GND")

    r1[1] += vin
    r1[2] += vout
    r2[1] += vout
    r2[2] += gnd
    r3[1] += vout
    r3[2] += gnd

    return r1, r2, r3
```

2. Run the script:
```bash
uv run python test1_basic_divider.py
```

3. Open schematic and thoroughly verify all elements

### Expected Results

- [ ] R1 value updated to 220k ✅
- [ ] R1 footprint updated to R_1206_3216Metric ✅
- [ ] R2 value updated to 100k ✅
- [ ] R3 value updated to 2.2k ✅
- [ ] All component positions preserved ✅
- [ ] All component rotations preserved ✅
- [ ] Manual C1 still present ✅
- [ ] Power symbols (#PWR01, #PWR02) still present ✅
- [ ] All manual wires intact ✅
- [ ] All junctions intact ✅
- [ ] All net labels intact ✅
- [ ] Complex wiring from Test 13 intact ✅

### Critical Verification

**CRITICAL:** This is the ultimate test. ALL manual edits should be preserved while ALL Python changes propagate correctly.

### Notes

**Status:** ⬜ Not Started / ⏳ In Progress / ✅ Passed / ❌ Failed

---

## Test 15: Remove Component in Python

**Objective:** Verify component removal works correctly.

### Steps

1. Modify `test1_basic_divider.py` - remove R3:
```python
@circuit(name="voltage_divider")
def voltage_divider():
    r1 = Component("Device:R", ref="R1", value="220k",
                   footprint="Resistor_SMD:R_1206_3216Metric")
    r2 = Component("Device:R", ref="R2", value="100k",
                   footprint="Resistor_SMD:R_0805_2012Metric")
    # R3 removed

    vin = Net("VIN")
    vout = Net("VOUT")
    gnd = Net("GND")

    r1[1] += vin
    r1[2] += vout
    r2[1] += vout
    r2[2] += gnd

    return r1, r2
```

2. Run the script:
```bash
uv run python test1_basic_divider.py
```

3. Open schematic in KiCad

### Expected Results

- [ ] R3 removed (or preserved if `preserve_user_components=True`)
- [ ] R1 and R2 still present
- [ ] Manual C1 still present ✅
- [ ] Power symbols still present ✅
- [ ] Wires adjusted or intact ✅

### Note on Component Removal

**Note:** By default, `preserve_user_components=True` may keep R3. This is expected behavior to prevent accidental deletion of manually added components.

### Notes

**Status:** ⬜ Not Started / ⏳ In Progress / ✅ Passed / ❌ Failed

---

## Test 16: Junction Preservation

**Objective:** Explicitly test junction preservation.

### Steps

1. In KiCad schematic editor:
   - Create a T-junction by connecting three wires at a single point
   - Create an X-junction by connecting four wires at a single point
   - Verify junctions appear as dots
   - Save the schematic

2. Document junctions:
   - T-junction location: (x, y) = _______
   - X-junction location: (x, y) = _______
   - Screenshot for reference

3. Run Python script again:
```bash
uv run python test1_basic_divider.py
```

4. Open schematic and verify junctions

### Expected Results

- [ ] T-junction preserved ✅
- [ ] X-junction preserved ✅
- [ ] Junction positions unchanged
- [ ] Junction properties unchanged

### Notes

**Status:** ⬜ Not Started / ⏳ In Progress / ✅ Passed / ❌ Failed

---

## Test 17: Import Manual Component to Python

**Objective:** Document workflow for importing manually added components back to Python.

**Note:** This is currently a manual workflow, not automated.

### Steps

1. Open the KiCad schematic

2. Note down manual component C1:
   - Reference: C1
   - Value: 100n
   - Footprint: _______
   - Connections: VOUT (pin 1), GND (pin 2)

3. Create `test2_with_manual_cap.py` to explicitly include C1:
```python
from circuit_synth import Component, Net, circuit

@circuit(name="voltage_divider")
def voltage_divider():
    r1 = Component("Device:R", ref="R1", value="220k",
                   footprint="Resistor_SMD:R_1206_3216Metric")
    r2 = Component("Device:R", ref="R2", value="100k",
                   footprint="Resistor_SMD:R_0805_2012Metric")
    c1 = Component("Device:C", ref="C1", value="100n",  # Imported from KiCad
                   footprint="Capacitor_SMD:C_0603_1608Metric")

    vin = Net("VIN")
    vout = Net("VOUT")
    gnd = Net("GND")

    r1[1] += vin
    r1[2] += vout
    r2[1] += vout
    r2[2] += gnd
    c1[1] += vout  # Imported from KiCad
    c1[2] += gnd   # Imported from KiCad

    return r1, r2, c1

c = voltage_divider()
c.generate_kicad_project("voltage_divider", force_regenerate=False, generate_pcb=False)
```

4. Run the new script:
```bash
uv run python test2_with_manual_cap.py
```

### Expected Results

- [ ] C1 now explicitly in Python code
- [ ] C1 position in KiCad unchanged (synchronizer matches by ref)
- [ ] All other manual edits preserved

### Notes

**Status:** ⬜ Not Started / ⏳ In Progress / ✅ Passed / ❌ Failed

**Future Enhancement:** Automatic Python code generation from KiCad schematic (reverse synchronization).

---

## Test 18: Stress Test - Multiple Rapid Updates

**Objective:** Test stability under rapid successive updates.

### Steps

1. Perform 5 rapid iterations:
   - Update R1 value: 100k → 150k → 200k → 250k → 300k
   - Run Python script after each change
   - Briefly open KiCad schematic to verify

2. After all 5 iterations, thoroughly verify:
   - All manual edits still present
   - Latest R1 value (300k) applied
   - No corruption or data loss

### Expected Results

- [ ] All 5 updates processed successfully
- [ ] Final R1 value is 300k
- [ ] Manual C1 still present ✅
- [ ] Power symbols still present ✅
- [ ] Wires intact ✅
- [ ] Junctions intact ✅
- [ ] Rotations preserved ✅
- [ ] Positions preserved ✅

### Notes

**Status:** ⬜ Not Started / ⏳ In Progress / ✅ Passed / ❌ Failed

---

## Test 19: Replace Hierarchical Labels with Direct Power Symbol Connections

**Objective:** Verify that power symbols directly connected to components (instead of hierarchical labels) are preserved.

**Scenario:** This tests a very common KiCad workflow where users delete hierarchical labels and connect power symbols directly to component pins for cleaner schematics.

### Steps

1. Generate a fresh voltage divider circuit:
```bash
uv run python test1_basic_divider.py
```

2. In KiCad schematic editor:
   - Delete the VIN hierarchical label
   - Delete the GND hierarchical label
   - Press "P" to add power port
   - Search for "power:+3V3" (or "power:VCC")
   - Place power symbol directly above R1
   - Use wire tool to connect power symbol to R1 pin 1
   - Add another power port: "power:GND"
   - Place GND symbol directly below R2
   - Use wire tool to connect GND symbol to R2 pin 2
   - Keep the VOUT hierarchical label (for testing mixed approach)
   - Save the schematic

3. Document the power symbol connections:
   - VCC symbol (#PWR0X): Connected to R1 pin 1
   - GND symbol (#PWR0Y): Connected to R2 pin 2
   - VIN hierarchical label: DELETED
   - GND hierarchical label: DELETED
   - VOUT hierarchical label: KEPT
   - Screenshot for reference

4. Re-run Python script without changes:
```bash
uv run python test1_basic_divider.py
```

5. Open schematic in KiCad and verify

### Expected Results

- [ ] Power symbol on R1 pin 1 preserved ✅
- [ ] Power symbol on R2 pin 2 preserved ✅
- [ ] Wire connections to power symbols intact ✅
- [ ] VOUT hierarchical label still present ✅
- [ ] VIN hierarchical label did NOT reappear ✅
- [ ] GND hierarchical label did NOT reappear ✅
- [ ] R1 and R2 values unchanged
- [ ] All manual wiring preserved

### Critical Verification

**CRITICAL:** This tests that circuit-synth respects the user's choice to use power symbols instead of hierarchical labels. The synchronizer should NOT re-create deleted hierarchical labels.

### Advanced: Update Component Value

6. Modify `test1_basic_divider.py` - change R1 value to 33k:
```python
r1 = Component("Device:R", ref="R1", value="33k",  # Changed
               footprint="Resistor_SMD:R_0603_1608Metric")
```

7. Run the script:
```bash
uv run python test1_basic_divider.py
```

8. Open schematic and verify:

- [ ] R1 value updated to 33k ✅
- [ ] Power symbol on R1 still connected ✅
- [ ] GND power symbol on R2 still connected ✅
- [ ] Wire connections maintained ✅
- [ ] No hierarchical labels reappeared ✅

### Use Case

This test validates the common professional workflow where:
1. Engineer generates schematic from Python (with hierarchical labels)
2. Engineer replaces hierarchical labels with direct power connections for cleaner schematics
3. Engineer continues to update component values in Python
4. All manual wiring and power symbol choices are preserved

### Notes

**Status:** ⬜ Not Started / ⏳ In Progress / ✅ Passed / ❌ Failed

**Design Note:** Power symbols are semantically different from hierarchical labels:
- Hierarchical labels: Used for hierarchical design, connecting to parent sheets
- Power symbols: Global power connections, cleaner for flat schematics

Circuit-synth should respect the user's choice and not force one over the other.

---

## Test Results Summary

| Test # | Test Name | Status | Notes |
|--------|-----------|--------|-------|
| 1 | Basic Generation | ⬜ | |
| 2 | Manual Wiring | ⬜ | |
| 3 | Re-run Without Changes | ⬜ | CRITICAL |
| 4 | Add Manual Component | ⬜ | |
| 5 | Update Value | ⬜ | CRITICAL |
| 6 | Move Components | ⬜ | |
| 7 | Update Value + Position | ⬜ | CRITICAL |
| 8 | Add Power Symbols | ⬜ | |
| 9 | Change Footprints | ⬜ | |
| 10 | Rotate Components | ⬜ | |
| 11 | Update + Rotation | ⬜ | |
| 12 | Add Component Python | ⬜ | |
| 13 | Complex Wiring | ⬜ | |
| 14 | Comprehensive Update | ⬜ | CRITICAL |
| 15 | Remove Component | ⬜ | |
| 16 | Junction Preservation | ⬜ | |
| 17 | Import to Python | ⬜ | |
| 18 | Stress Test | ⬜ | |
| 19 | Power Symbols vs Labels | ⬜ | CRITICAL |

### Pass Criteria

- All CRITICAL tests must pass
- At least 90% of total tests must pass
- No data corruption or file corruption
- No loss of manual edits

### Overall Status

**Overall:** ⬜ Not Started / ⏳ In Progress / ✅ All Passed / ❌ Failed

---

## Bug Reporting Template

If any test fails, document the bug using this template:

```markdown
### Bug Report

**Test Number:**
**Test Name:**
**Date:**
**Severity:** 🔴 Critical / 🟡 Major / 🟢 Minor

**Description:**
[Describe what went wrong]

**Steps to Reproduce:**
1.
2.
3.

**Expected Behavior:**
[What should have happened]

**Actual Behavior:**
[What actually happened]

**Screenshots:**
[Attach before/after screenshots]

**Files:**
[Attach .kicad_sch files or Python scripts]

**Additional Context:**
[Any other relevant information]
```

---

## Completion Checklist

- [ ] All tests executed
- [ ] All critical tests passed
- [ ] Results documented
- [ ] Screenshots archived
- [ ] Test files backed up
- [ ] Bugs reported (if any)
- [ ] Final summary written

---

## Notes and Observations

*Use this section to document any interesting findings, edge cases, or suggestions for improvement.*

---

*Manual Test Plan Generated: 2025-10-12*
*Version: 1.1 (19 tests)*
*For circuit-synth Round-Trip Preservation Feature*
