# Test 45: Import Power Symbols from KiCad (BIDIRECTIONAL CRITICAL)

## What This Tests

**Core Question**: When you import a KiCad schematic (.kicad_sch) that contains power symbols (VCC, GND), does circuit-synth correctly recognize and preserve them during import, Python modification, and regeneration?

This tests **BIDIRECTIONAL power symbol handling** - the CRITICAL missing piece in current test coverage.

## Why This Is Priority 0

**Current coverage gap:**
- Tests 16-18: Python → KiCad power symbol export ✅
- **Test 45: KiCad → Python power symbol import** ❌ (THIS TEST)

**Real workflow:**
1. User opens existing KiCad design with power symbols
2. Imports to circuit-synth for programmatic modification
3. Adds new components that use existing power rails
4. Regenerates to KiCad
5. Expects: Power symbols preserved, new connections to power work correctly

**Without this test:**
- Unknown if power symbols survive import
- Unknown if imported power nets can be reused
- No validation of round-trip power handling
- Real-world KiCad designs may fail to import correctly

## When This Situation Happens

- Developer has existing KiCad project with power rails (VCC, GND, +3V3, etc.)
- Wants to use circuit-synth to add components programmatically
- Imports .kicad_sch file to Python
- Expects to connect new components to existing power rails
- Regenerates expecting power structure preserved

## What Should Work

### Phase 1: Import KiCad with Power Symbols
1. Start with hand-crafted .kicad_sch containing:
   - R1 resistor (10k)
   - VCC power symbol connected to R1 pin 1
   - GND power symbol connected to R1 pin 2
   - Wires connecting power symbols to resistor pins
2. Import to circuit-synth using `import_kicad_project()`
3. Validate:
   - Power symbols recognized (VCC, GND nets exist)
   - R1 component imported
   - R1 connections to power preserved
   - Net structure includes power nets

### Phase 2: Modify in Python (Add Component Using Power)
4. In Python, add new resistor R2
5. Connect R2 to existing VCC and GND nets
6. Validate circuit object shows both resistors connected to power

### Phase 3: Regenerate to KiCad
7. Regenerate circuit to KiCad
8. Validate:
   - Original power symbols preserved
   - Original R1 position preserved
   - New R2 component appears
   - R2 connected to VCC and GND (hierarchical labels or power symbols)
   - Netlist shows all power connections

### Phase 4: Electrical Validation (Level 3)
9. Export netlist using kicad-cli
10. Validate:
    - VCC net includes R1[1] and R2[1]
    - GND net includes R1[2] and R2[2]
    - No unconnected pins
    - Power net semantics correct (global connection)

## Manual Test Instructions

```bash
cd /Users/shanemattner/Desktop/circuit-synth2/tests/bidirectional/45_import_power_symbols_from_kicad

# Step 1: Inspect hand-crafted KiCad file
open circuit_with_power.kicad_sch
# In KiCad:
#   - R1 visible with VCC on pin 1, GND on pin 2
#   - Power symbols visible (⏚ GND, +V VCC)
#   - Wires connecting power to component

# Step 2: Run test (automated)
pytest test_45_import_power_symbols.py -v

# Step 3: Inspect regenerated KiCad (if --keep-output)
open output/circuit_with_power_modified.kicad_pro
# In KiCad:
#   - Original R1 preserved at same position
#   - New R2 added
#   - Both R1 and R2 connected to VCC/GND
#   - Power symbols or hierarchical labels present
```

## Expected Result

### Import Phase (KiCad → Python)
- ✅ circuit-synth imports .kicad_sch successfully
- ✅ Power symbols recognized as nets (VCC, GND)
- ✅ R1 component imported with correct connections
- ✅ Net structure: VCC net includes R1[1], GND net includes R1[2]
- ✅ Component positions preserved from KiCad

### Modification Phase (Python)
- ✅ Can reference existing VCC and GND nets
- ✅ Can add new component (R2) using existing power nets
- ✅ Circuit object shows correct topology

### Regeneration Phase (Python → KiCad)
- ✅ Original R1 position preserved
- ✅ Original power symbols preserved (or regenerated correctly)
- ✅ New R2 appears with power connections
- ✅ Netlist validates: VCC connects R1[1] + R2[1], GND connects R1[2] + R2[2]
- ✅ No electrical rule errors

## Why This Is Important

**Bidirectional power workflow:**
1. Most real circuits have power rails
2. Users want to import existing designs
3. Need to add components to existing power structure
4. Must preserve power topology during round-trip

**If this doesn't work:**
- Cannot import real KiCad designs with power
- Power structure lost during import
- Must manually recreate power connections after import
- Bidirectional workflow breaks for most real circuits
- Test coverage has critical gap

## Success Criteria

This test PASSES when:

### Level 1 - Import succeeds
- ✅ `import_kicad_project()` completes without error
- ✅ Returns Circuit object

### Level 2 - Semantic validation (import)
- ✅ Circuit contains R1 component
- ✅ Circuit has VCC net with R1[1] connection
- ✅ Circuit has GND net with R1[2] connection
- ✅ Component position matches original KiCad position

### Level 3 - Python modification
- ✅ Can reference existing nets by name
- ✅ Can add new component to existing nets
- ✅ Circuit topology correct after modification

### Level 4 - Regeneration validation
- ✅ Regeneration succeeds without error
- ✅ Original component position preserved
- ✅ New component appears
- ✅ Netlist shows correct power connections

### Level 5 - Electrical validation
- ✅ kicad-cli netlist export succeeds
- ✅ VCC net contains expected pins
- ✅ GND net contains expected pins
- ✅ No ERC errors

## Critical Implementation Notes

### Power Symbol Handling in circuit-synth

**KiCad power symbols are special:**
- Symbol library: `power:VCC`, `power:GND`, etc.
- Create global net connections
- Don't appear in component list (no footprint, no BOM)
- Represented internally as nets with special semantics

**circuit-synth approach:**
- Power symbols may become Net objects
- OR hierarchical labels with power net names
- Must recognize both representations
- Must preserve global connection semantics

### Importer Capabilities Check

**This test may reveal limitations:**
- Does importer recognize power symbols?
- Are power symbols converted to Net objects?
- Are positions preserved for power symbols?
- Can regenerated circuit reconnect to power?

**Expected scenarios:**
1. **Best case**: Power symbols imported as Net objects, full round-trip works
2. **Good case**: Power symbols imported as nets, regeneration uses hierarchical labels
3. **Acceptable case**: Power symbols lost during import, but nets preserved (XFAIL with note)
4. **Failure case**: Power nets not recognized, connections lost (BUG)

### Test Strategy

**Fixture:** Hand-crafted .kicad_sch (NOT generated by circuit-synth)
- Ensures we test real KiCad power symbol format
- Validates importer handles authentic KiCad files
- Not circular test (no circuit-synth generation involved initially)

**Validation levels:**
1. Import succeeds
2. Nets recognized (VCC, GND)
3. Component connections to power preserved
4. Can modify in Python using existing power nets
5. Regeneration preserves power structure
6. Netlist electrical validation passes

### XFAIL Scenarios

**This test may need XFAIL markers if:**
- Power symbol import not yet implemented (GitHub issue needed)
- Power symbols recognized but regeneration differs (hierarchical labels vs symbols)
- Position preservation not working for power symbols

**XFAIL should include:**
- Clear explanation of limitation
- Link to GitHub issue tracking fix
- Expected vs actual behavior
- Workaround if available

## Related Tests

- **Test 16**: Add power symbol (Python → KiCad only)
- **Test 17**: Add ground symbol (Python → KiCad only)
- **Test 18**: Multiple power domains (Python → KiCad only)
- **Test 26**: Power symbol replacement (tests different power symbols)
- **Test 45**: THIS TEST (KiCad → Python bidirectional)

## Implementation Checklist

- [x] Create hand-crafted .kicad_sch with power symbols
- [x] Validate .kicad_sch opens correctly in KiCad
- [x] Implement test phases:
  - [x] Import phase
  - [x] Validation phase (nets exist)
  - [x] Modification phase (add component)
  - [x] Regeneration phase
  - [x] Netlist validation phase
- [x] Add comprehensive assertions at each level
- [x] Add detailed logging of test progress
- [x] Handle --keep-output flag for debugging
- [x] Add XFAIL markers if needed
- [x] Document limitations found
- [x] Create GitHub issue if bugs found

## Notes

**This test is FOUNDATIONAL for bidirectional workflows.**

Without power symbol import support:
- Cannot import real KiCad designs
- Bidirectional editing limited to simple circuits
- Power rail handling incomplete

**This test reveals the current state of power import support and documents any gaps.**
