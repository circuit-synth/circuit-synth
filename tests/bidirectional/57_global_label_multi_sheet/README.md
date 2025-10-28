# Test 57: Global Label Multi-Sheet (Peer Sheets, Non-Hierarchical)

## What This Tests

**Core Question**: When you have multiple peer subcircuits (NOT parent-child hierarchy) that need to share signals like SPI_CLK, can you use global labels to connect them across sheets without hierarchical pins?

This tests **global labels for flat multi-sheet designs** - using KiCad's global label mechanism to connect peer sheets at the same hierarchy level without parent-child relationships.

## Priority 0 Test - Critical Multi-Sheet Connectivity

This is a **Priority 0 test** because:
1. **Global labels** are KiCad's native mechanism for cross-sheet connectivity in flat designs
2. **Different from hierarchical labels** which require parent-child sheet relationships
3. **Essential for modular designs** where peer subsystems need shared signals (SPI bus, I2C bus, power nets)
4. **Tests circuit-synth's current limitation** - uses hierarchical labels by design (see test 24)

## Global Labels vs Hierarchical Labels

### Hierarchical Labels (circuit-synth default)
- **Purpose**: Connect parent sheet to child sheets
- **Requires**: Hierarchical sheet structure with parent-child relationships
- **Use case**: Organized hierarchical designs with clear subsystem boundaries
- **KiCad visual**: Flag/arrow shape pointing into hierarchical sheet symbol
- **Scope**: Sheet-local, requires matching hierarchical pin on sheet symbol

### Global Labels (KiCad native, test target)
- **Purpose**: Connect any sheets at any hierarchy level
- **Requires**: NO hierarchical relationship needed
- **Use case**: Flat multi-sheet designs, peer subsystems sharing signals
- **KiCad visual**: Circle/globe shape
- **Scope**: Project-wide, any matching global label name connects electrically

## When This Situation Happens

**Real-world scenario**: SPI bus connecting multiple peripheral subsystems

```
Main Sheet (MCU):
  - MCU with SPI master
  - Global labels: SPI_CLK, SPI_MOSI, SPI_MISO

Display Sheet (peer):
  - Display controller with SPI slave
  - Global labels: SPI_CLK, SPI_MOSI, SPI_MISO

Sensor Sheet (peer):
  - Sensor with SPI slave
  - Global labels: SPI_CLK, SPI_MOSI, SPI_MISO

Result: All three sheets electrically connected via matching global label names
```

This is a **flat multi-sheet design** where sheets are peers, not parent-child.

## What Should Work

1. Create 2 peer subcircuits (both at same level) needing shared SPI_CLK signal
2. Use global label "SPI_CLK" in both subcircuits (NOT hierarchical labels/pins)
3. Generate to KiCad, validate:
   - Global labels exist in both sheets (search for `global_label` in .kicad_sch files)
   - Netlist shows components on different sheets connected via SPI_CLK
   - NO hierarchical pins created (flat design, not parent-child hierarchy)
4. Add third peer sheet using same SPI_CLK global label
5. Regenerate, validate all three sheets connected via global labels

## Manual Test Instructions

```bash
cd /Users/shanemattner/Desktop/circuit-synth2/tests/bidirectional/57_global_label_multi_sheet

# Step 1: Generate initial KiCad with 2 peer sheets using global labels
uv run spi_bus.py
open spi_bus/spi_bus.kicad_pro

# Verify in KiCad:
#   - Multiple .kicad_sch files (one per subcircuit)
#   - Each sheet has "SPI_CLK" global label (circle/globe visual)
#   - NO hierarchical sheet symbols (peer sheets, not parent-child)
#   - Open each sheet individually (not hierarchical navigation)

# Step 2: Check netlist connectivity
kicad-cli sch export netlist spi_bus/spi_bus.kicad_sch -o spi_bus/spi_bus.net
grep "SPI_CLK" spi_bus/spi_bus.net
# Should see components from multiple sheets connected to SPI_CLK net

# Step 3: Validate global label syntax in schematic files
grep "global_label" spi_bus/*.kicad_sch
# Should find global_label entries (NOT hierarchical_label)

# Step 4: Uncomment third sheet in spi_bus.py
# Edit spi_bus.py, uncomment the sensor_sheet section

# Step 5: Regenerate with third sheet
uv run spi_bus.py
open spi_bus/spi_bus.kicad_pro

# Verify:
#   - Third sheet file exists
#   - Third sheet has SPI_CLK global label
#   - Netlist shows all three sheets connected via SPI_CLK
```

## Expected Result

**If circuit-synth supports global labels:**
- ✅ Multiple peer subcircuits generate as separate .kicad_sch files
- ✅ Global labels "SPI_CLK" appear in each sheet (circle/globe visual)
- ✅ Netlist shows cross-sheet connectivity via SPI_CLK net
- ✅ NO hierarchical pins/sheet symbols (flat peer design)
- ✅ Adding third sheet maintains connectivity
- ✅ `grep "global_label"` finds entries in schematic files

**If circuit-synth uses hierarchical labels (current behavior per test 24):**
- ⚠️ circuit-synth creates hierarchical_label objects instead of global_label
- ⚠️ May require parent-child sheet structure (not peer sheets)
- ⚠️ May need hierarchical pins on sheet symbols
- ⚠️ This test will XFAIL with clear message about limitation

## Why This Is Important

**Flat multi-sheet design workflow (no hierarchy):**
1. Organize complex circuit into functional peer subsystems (Display, Sensor, Power)
2. Each subsystem is a separate sheet (easier to work on independently)
3. Shared signals (SPI bus, I2C bus, power rails) use global labels
4. NO parent-child hierarchy needed (simpler mental model)
5. Add/remove subsystem sheets without reorganizing hierarchy

**Contrast with hierarchical design:**
- Hierarchical: Parent sheet contains hierarchical sheet symbols, hierarchical pins pass signals
- Flat with global labels: Peer sheets, global labels match by name, no parent required

If global labels don't work:
- Users must use hierarchical design (adds complexity)
- Can't have simple peer sheets sharing signals
- Modular subsystem approach becomes harder

## Success Criteria

This test PASSES when:
- Multiple peer subcircuits generate as separate .kicad_sch files
- Global labels (NOT hierarchical_label) appear in schematic files
- Search for `(global_label "SPI_CLK"` succeeds in .kicad_sch files
- Netlist shows components from different sheets connected via SPI_CLK
- NO hierarchical sheet symbols or pins required
- Adding third peer sheet maintains connectivity
- All global labels with matching names are electrically connected

This test XFAILS (expected failure) when:
- circuit-synth creates hierarchical_label instead of global_label
- Requires parent-child hierarchy instead of peer sheets
- Test will document this as known limitation

## Validation Level

**Level 2 + Level 3 Validation:**
- **Level 2 (Text search)**: Search .kicad_sch files for `global_label` entries (NOT `hierarchical_label`)
- **Level 3 (Netlist comparison)**: Validate cross-sheet connectivity via netlist
  - Components on different sheets connected to same net name
  - SPI_CLK net includes components from all peer sheets

## Related Tests

- **Test 24** - Add global label (found circuit-synth uses hierarchical_label)
- **Test 22** - Add subcircuit sheet (hierarchical parent-child)
- **Test 11** - Add hierarchical labels (sheet-local scope)

## Design Notes

### KiCad Global Label Syntax

```scheme
(global_label "SPI_CLK" (shape input) (at 100 100 0)
  (effects (font (size 1.27 1.27)) (justify left))
  (uuid "...")
  (property "Intersheetrefs" "" (id 0) (at 0 0 0))
)
```

### Expected Schematic Structure

**spi_bus.kicad_sch (root sheet):**
```
(kicad_sch (version 20230121)
  ...
  (symbol (lib_id "MCU") (at 100 100) (reference "U1") ...)
  (global_label "SPI_CLK" (shape output) (at 120 100 0) ...)
  ...
)
```

**display_sheet.kicad_sch (peer sheet 1):**
```
(kicad_sch (version 20230121)
  ...
  (symbol (lib_id "Display") (at 100 100) (reference "U2") ...)
  (global_label "SPI_CLK" (shape input) (at 90 100 0) ...)
  ...
)
```

**sensor_sheet.kicad_sch (peer sheet 2):**
```
(kicad_sch (version 20230121)
  ...
  (symbol (lib_id "Sensor") (at 100 100) (reference "U3") ...)
  (global_label "SPI_CLK" (shape input) (at 90 100 0) ...)
  ...
)
```

### Netlist Expected Output

```
(net (code "1") (name "SPI_CLK")
  (node (ref "U1") (pin "CLK"))
  (node (ref "U2") (pin "CLK"))
  (node (ref "U3") (pin "CLK"))
)
```

All three components connected to same net, even though on different sheets.

## Test Implementation Strategy

1. **Create spi_bus.py**: Multiple peer subcircuits with global label connections
2. **Initial generation**: 2 peer sheets with SPI_CLK global labels
3. **Validate Level 2**: Text search for `global_label` in .kicad_sch files
4. **Validate Level 3**: Netlist shows cross-sheet connectivity
5. **Add third sheet**: Uncomment sensor sheet in Python
6. **Regenerate and validate**: Third sheet adds to SPI_CLK net
7. **XFAIL handling**: If circuit-synth uses hierarchical_label, mark test as XFAIL with explanation

## Current circuit-synth Behavior (from Test 24)

**Known from test 24_add_global_label:**
- circuit-synth creates `hierarchical_label` objects for net connections
- Does NOT create `global_label` objects in KiCad schematic files
- Test 24 comment: "circuit-synth creates hierarchical_label objects (not global_label objects)"

**Implication for test 57:**
- This test will likely XFAIL initially
- Tests the DESIRED behavior (global labels for peer sheets)
- Documents gap between current implementation and multi-sheet peer connectivity
- Provides target for future enhancement

## Enhancement Path (if XFAIL)

If this test fails because circuit-synth doesn't support global labels:

1. **Document limitation**: Test XFAILS with clear message
2. **Feature request**: Create GitHub issue for global label support
3. **Workaround**: Use hierarchical design instead of flat peer design
4. **Future enhancement**: Add `label_type="global"` parameter to Net() API

```python
# Desired future API:
global_net = Net("SPI_CLK", label_type="global")  # Forces global labels
hierarchical_net = Net("LOCAL_SIG", label_type="hierarchical")  # Hierarchical labels
```

## Test Categories

- **Category**: Multi-sheet connectivity, flat design, global labels
- **Priority**: 0 (critical for modular multi-sheet designs)
- **Complexity**: Medium (2 sheets → 3 sheets expansion)
- **Validation**: Level 2 (text search) + Level 3 (netlist)
- **Expected**: XFAIL initially (circuit-synth uses hierarchical labels)
