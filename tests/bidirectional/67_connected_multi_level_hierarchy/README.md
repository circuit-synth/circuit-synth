# Test 67: Connected Multi-Level Hierarchy (ULTIMATE TEST)

## What This Tests

**Core Question**: Can you build a 3-level hierarchy incrementally AND have electrical connections (nets) flow through all levels connecting components across sheets?

This is the **ultimate hierarchical test** - combines progressive subcircuit addition with cross-sheet electrical connectivity.

## When This Situation Happens

Real hierarchical designs need both:
1. **Incremental development** - Start simple (1 level), add complexity (2→3 levels)
2. **Cross-sheet connections** - Components in different subcircuits need electrical connections

**Example: Signal processing chain**
- Main board has microcontroller (R1 simulates MCU output)
- Level1 subcircuit has amplifier (R2 simulates amp)
- Level2 subcircuit has filter (R3 simulates filter)
- Signal flows: MCU → Amplifier → Filter (all connected electrically)

This requires:
- 3-level hierarchy: main → level1 → level2
- Net passing through all levels
- Single net connects all three components

## What Should Work

### Step 1: Single-level circuit (main with R1)
```python
@circuit(name="main")
def main():
    r1 = Component("Device:R", ref="R1", value="10k")
```
Generate → Verify: 1 sheet, R1 unconnected

### Step 2: Add level1, connect R1—R2 (2 levels)
```python
@circuit(name="level1")
def level1(signal_net):  # Accept net from main
    r2 = Component("Device:R", ref="R2", value="4.7k")
    r2[1] += signal_net  # Connect to passed net

@circuit(name="main")
def main():
    r1 = Component("Device:R", ref="R1", value="10k")
    signal = Net("SIGNAL")
    r1[1] += signal
    level1(signal_net=signal)  # Pass net to level1
```
Regenerate → Verify:
- 2 sheets: main + level1
- Hierarchical pin "SIGNAL" on main's sheet symbol
- Hierarchical label "SIGNAL" on level1 sheet
- Netlist: R1[1]—R2[1] connected

### Step 3: Add level2, connect R1—R2—R3 (3 levels)
```python
@circuit(name="level2")
def level2(signal_net):  # Accept net from level1
    r3 = Component("Device:R", ref="R3", value="20k")
    r3[1] += signal_net

@circuit(name="level1")
def level1(signal_net):
    r2 = Component("Device:R", ref="R2", value="4.7k")
    r2[1] += signal_net
    level2(signal_net=signal_net)  # Pass same net to level2

@circuit(name="main")
def main():
    r1 = Component("Device:R", ref="R1", value="10k")
    signal = Net("SIGNAL")
    r1[1] += signal
    level1(signal_net=signal)
```
Regenerate → Verify:
- 3 sheets: main + level1 + level2
- Hierarchical pins on main and level1 sheet symbols
- Hierarchical labels on level1 and level2 sheets
- Netlist: R1[1]—R2[1]—R3[1] all on same net

## Manual Test Instructions

```bash
cd tests/bidirectional/67_connected_multi_level_hierarchy

# STEP 1: Generate main with R1 (unconnected)
uv run connected_hierarchy.py
open connected_hierarchy/connected_hierarchy.kicad_pro
# Verify: Main sheet with R1, no connections

# STEP 2: Add level1 with Net("SIGNAL") connecting R1—R2
# Edit connected_hierarchy.py:
#   - Uncomment level1 circuit definition
#   - Uncomment Net("SIGNAL") creation in main
#   - Uncomment r1[1] += signal
#   - Uncomment level1(signal_net=signal)
uv run connected_hierarchy.py
open connected_hierarchy/connected_hierarchy.kicad_pro
# Verify:
#   - Main sheet: R1 + hierarchical sheet symbol with pin "SIGNAL"
#   - Level1 sheet: R2 + hierarchical label "SIGNAL"
#   - Export netlist: R1 and R2 on same net

# STEP 3: Add level2 with R1—R2—R3 connected
# Edit connected_hierarchy.py:
#   - Uncomment level2 circuit definition
#   - Uncomment level2(signal_net=signal_net) in level1
uv run connected_hierarchy.py
open connected_hierarchy/connected_hierarchy.kicad_pro
# Verify:
#   - Main: R1 + sheet symbol with pin "SIGNAL"
#   - Level1: R2 + hierarchical label "SIGNAL" + sheet symbol with pin "SIGNAL"
#   - Level2: R3 + hierarchical label "SIGNAL"
#   - Export netlist: R1, R2, R3 all on same net "SIGNAL"

# STEP 4: Validate multi-level connectivity
kicad-cli sch export netlist connected_hierarchy/connected_hierarchy.kicad_sch \
  --output connected.net
# Check netlist:
# (net (name "SIGNAL")
#   (node (ref "R1") (pin "1"))
#   (node (ref "R2") (pin "1"))
#   (node (ref "R3") (pin "1")))
```

## Expected Result

**Step 1 (1 level, unconnected):**
- ✅ 1 schematic: `connected_hierarchy.kicad_sch`
- ✅ R1 visible, no nets

**Step 2 (2 levels, R1—R2 connected):**
- ✅ 2 schematics: main + level1.kicad_sch
- ✅ Hierarchical pin "SIGNAL" on main's sheet symbol
- ✅ Hierarchical label "SIGNAL" on level1 sheet
- ✅ Netlist: R1[1] and R2[1] on same net

**Step 3 (3 levels, R1—R2—R3 connected):**
- ✅ 3 schematics: main + level1 + level2.kicad_sch
- ✅ Hierarchical pins at each level
- ✅ Hierarchical labels on level1 and level2
- ✅ Netlist: R1[1], R2[1], R3[1] all on same net "SIGNAL"
- ✅ Signal flows through all 3 hierarchy levels

## Why This Is The Ultimate Test

**This test validates the COMPLETE hierarchical feature set:**

1. **Progressive development** (test 22) - Build hierarchy incrementally
2. **Cross-sheet connectivity** (test 24) - Pass nets between circuits
3. **Multi-level net passing** (NEW) - Net flows through nested hierarchy
4. **Hierarchical infrastructure** - Pins, labels, sheet symbols auto-generated
5. **Electrical correctness** - Netlist proves multi-level connectivity

**If this passes:**
- ✅ Hierarchical circuit design is FULLY functional
- ✅ Can build complex nested circuits incrementally
- ✅ Electrical connections work across any depth
- ✅ Tool is production-ready for real hierarchical designs

**If this fails:**
- ❌ Hierarchical feature is incomplete
- ❌ Cannot build real-world complex circuits
- ❌ Must fix before claiming hierarchical support

## Success Criteria

This test PASSES when:
- Step 1: Single-level generation works
- Step 2: Adding level1 with net passing creates 2-level connected circuit
- Step 3: Adding level2 creates 3-level circuit with net spanning all levels
- Hierarchical pins generated at each parent level
- Hierarchical labels generated at each child level
- Netlist proves R1, R2, R3 all on same net
- Component positions preserved through all steps
- No electrical rule errors

## Current Status

⚠️ **XFAIL - Blocked by Multiple Dependencies**

This test is blocked by:
1. **Issue #406** - Subcircuit sheet generation broken
2. **Test 22** - Progressive subcircuit addition must pass first
3. **Test 24** - Cross-sheet connection must pass first

**Dependency chain:**
```
Issue #406 fixed
    ↓
Test 22 passes (progressive hierarchy)
    ↓
Test 24 passes (cross-sheet connection)
    ↓
Test 67 can be executed (combines both)
```

This test documents the expected complete workflow but cannot execute until dependencies are resolved.

## Validation Level

**Level 3 (Netlist Comparison)**: Multi-level electrical connectivity
- File existence checking
- kicad-sch-api for structure verification
- Text search for hierarchical_pin and hierarchical_label
- **CRITICAL**: Netlist comparison to prove R1—R2—R3 all connected
- Position preservation across all steps

## Related Tests

- **Test 22** - Progressive subcircuit addition (MUST PASS FIRST)
- **Test 24** - Cross-sheet connection (MUST PASS FIRST)
- **Test 66** - Net isolation safety (ensures nets don't accidentally merge)
- **Issue #406** - Subcircuit generation (BLOCKING)

## Design Notes

**Net passing through hierarchy:**

```python
# Main creates net and passes to level1
signal = Net("SIGNAL")
level1(signal_net=signal)

# Level1 receives net and passes to level2
def level1(signal_net):
    level2(signal_net=signal_net)  # Same net instance

# Level2 receives same net instance
def level2(signal_net):
    r3[1] += signal_net  # All three resistors on SAME Net instance
```

**KiCad structure generated:**

Main sheet:
```
R1 --o SIGNAL
      |
   +--+--------+
   | SIGNAL   |  <- Hierarchical pin
   | level1   |
   +----------+
```

Level1 sheet:
```
SIGNAL o-- R2
      |
   +--+--------+
   | SIGNAL   |  <- Hierarchical pin (passes to level2)
   | level2   |
   +----------+
```

Level2 sheet:
```
SIGNAL o-- R3
```

**Netlist (proves connectivity):**
```
(net (code "1") (name "SIGNAL")
  (node (ref "R1") (pin "1"))   <- Main sheet
  (node (ref "R2") (pin "1"))   <- Level1 sheet
  (node (ref "R3") (pin "1")))  <- Level2 sheet
```

All three components on ONE net spanning THREE hierarchy levels!
