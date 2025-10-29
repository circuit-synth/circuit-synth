# Test 59: Modify Hierarchical Pin Name

## What This Tests

**Core Question**: When you have a hierarchical circuit with established pin connections and you rename a hierarchical pin in Python code, do both the hierarchical label (in subcircuit) and hierarchical pin (on sheet symbol) update correctly while preserving electrical connectivity?

This tests **hierarchical pin renaming** - the ability to refactor interface names during iterative design while maintaining netlist correctness.

## Priority 1 Test - Important for Interface Refinement

This is a **Priority 1** test because renaming hierarchical pins is a common refactoring operation during design evolution. As designs mature, interface names become more specific (e.g., "DATA_IN" → "SPI_MOSI"), and this refactoring must work without breaking electrical connectivity.

## When This Situation Happens

Real-world scenario (design refinement workflow):
1. Designer creates SPI subcircuit with generic pin name "DATA_IN"
2. Initial design generation with DATA_IN hierarchical pin/label
3. During review, team decides to use specific SPI naming: "SPI_MOSI"
4. Designer renames DATA_IN → SPI_MOSI in Python code
5. Regeneration should update both hierarchical label and sheet pin
6. Netlist should reflect new name
7. **Issue #380 Check**: Old "DATA_IN" label should be removed

## What Should Work

### Initial State
1. Generate hierarchical circuit with DATA_IN pin connecting parent to subcircuit
2. Validate:
   - Subcircuit .kicad_sch has hierarchical_label "DATA_IN"
   - Parent .kicad_sch has sheet symbol with pin "DATA_IN"
   - Component R1 in subcircuit connected to DATA_IN
   - Netlist shows DATA_IN net with R1 connection

### After Renaming
3. Rename DATA_IN → SPI_MOSI in Python code
4. Regenerate KiCad
5. Validate:
   - Subcircuit hierarchical_label updated to "SPI_MOSI"
   - Parent sheet pin updated to "SPI_MOSI"
   - **CRITICAL (Issue #380)**: Old "DATA_IN" label removed from subcircuit
   - Component R1 still connected (connectivity preserved)
   - Netlist shows SPI_MOSI net (not DATA_IN)
   - Net contains R1 connection (electrical continuity maintained)

## How Hierarchical Pin Renaming Should Work

### KiCad Structure Before Renaming

**Subcircuit (SPI_Driver.kicad_sch):**
```lisp
(hierarchical_label "DATA_IN"
  (shape input)
  (at 100.0 50.0 0)
  (uuid "abc123...")
)
(wire
  (pts (xy 100.0 50.0) (xy 110.0 50.0))
  (uuid "wire1...")
)
(symbol (lib_id "Device:R") (ref "R1") (unit 1)
  (pin "1" (uuid "pin1..."))
)
```

**Parent Sheet (spi_subcircuit.kicad_sch):**
```lisp
(sheet
  (at 35.56 34.29)
  (property "Sheetname" "SPI_Driver")
  (property "Sheetfile" "SPI_Driver.kicad_sch")
  (pin "DATA_IN" input (at 77.31 36.83 0))
)
```

### Expected Structure After Renaming

**Subcircuit (SPI_Driver.kicad_sch):**
```lisp
(hierarchical_label "SPI_MOSI"
  (shape input)
  (at 100.0 50.0 0)
  (uuid "abc123...")  # UUID preserved
)
# Old "DATA_IN" hierarchical_label REMOVED
(wire
  (pts (xy 100.0 50.0) (xy 110.0 50.0))
  (uuid "wire1...")
)
(symbol (lib_id "Device:R") (ref "R1") (unit 1)
  (pin "1" (uuid "pin1..."))
)
```

**Parent Sheet (spi_subcircuit.kicad_sch):**
```lisp
(sheet
  (at 35.56 34.29)
  (property "Sheetname" "SPI_Driver")
  (property "Sheetfile" "SPI_Driver.kicad_sch")
  (pin "SPI_MOSI" input (at 77.31 36.83 0))  # Updated name
)
```

### Key Requirements

1. **Label Name Update**: hierarchical_label text updated from DATA_IN → SPI_MOSI
2. **Pin Name Update**: Sheet symbol pin updated from DATA_IN → SPI_MOSI
3. **Old Label Removal (Issue #380)**: No "DATA_IN" hierarchical_label should remain
4. **Connectivity Preservation**: Wire connections to component pins maintained
5. **Netlist Accuracy**: Netlist uses new name "SPI_MOSI" (not "DATA_IN")
6. **UUID Preservation**: Hierarchical label UUID should remain same (indicates update, not replace)

## Manual Test Instructions

```bash
cd /Users/shanemattner/Desktop/circuit-synth2/tests/bidirectional/59_modify_hierarchical_pin_name

# Step 1: Generate initial circuit with DATA_IN pin
uv run spi_subcircuit.py
open spi_subcircuit/spi_subcircuit.kicad_pro

# Step 2: Verify initial hierarchical structure
# In KiCad:
#   - Open parent sheet (spi_subcircuit.kicad_sch)
#   - See sheet symbol for SPI_Driver with "DATA_IN" pin
#   - Open SPI_Driver sheet
#   - See hierarchical label "DATA_IN" connected to resistor R1

# Step 3: Verify initial netlist
# Tools → Generate Netlist → Export
# Check that R1 appears in "DATA_IN" net

# Step 4: Modify Python to rename DATA_IN → SPI_MOSI
# Edit spi_subcircuit.py:
#   Old: connections={"DATA_IN": data_in}
#   New: connections={"SPI_MOSI": data_in}

# Step 5: Regenerate and verify renaming
uv run spi_subcircuit.py
open spi_subcircuit/spi_subcircuit.kicad_pro

# Step 6: Verify hierarchical pin renamed
# In KiCad:
#   - Parent sheet: "DATA_IN" → "SPI_MOSI" pin on sheet symbol
#   - SPI_Driver sheet: "DATA_IN" → "SPI_MOSI" hierarchical label
#   - **CRITICAL**: Search for "DATA_IN" - should NOT exist (Issue #380)

# Step 7: Verify netlist updated
# Tools → Generate Netlist → Export
# Check:
#   - "SPI_MOSI" net exists with R1 connection
#   - "DATA_IN" net does NOT exist (old name removed)
```

## Expected Result

**Initial Generation:**
- ✅ Parent circuit has DATA_IN net
- ✅ SPI_Driver sheet symbol has "DATA_IN" pin
- ✅ SPI_Driver.kicad_sch has hierarchical_label "DATA_IN"
- ✅ R1 resistor connected to DATA_IN hierarchical label
- ✅ Netlist shows R1 in DATA_IN net

**After Renaming DATA_IN → SPI_MOSI:**
- ✅ Parent sheet symbol pin updated to "SPI_MOSI"
- ✅ Subcircuit hierarchical_label updated to "SPI_MOSI"
- ✅ **Issue #380**: Old "DATA_IN" hierarchical_label removed (no orphans)
- ✅ R1 still connected (wire/connectivity preserved)
- ✅ Netlist shows "SPI_MOSI" net (not DATA_IN)
- ✅ Netlist shows R1 in SPI_MOSI net

## Known Issue (Issue #380)

**Potential Failure Mode:**
The synchronizer may NOT remove old hierarchical labels when pin names change. This could cause:
- Old "DATA_IN" hierarchical label to remain in subcircuit
- Two hierarchical labels with different names in same subcircuit
- Netlist confusion with both DATA_IN and SPI_MOSI nets
- ERC errors about unconnected hierarchical labels

**Expected Behavior (Test Likely XFAIL):**
If old hierarchical label is NOT removed, this test will fail with:
```
AssertionError: Old hierarchical label 'DATA_IN' still present after renaming.
Found labels: ['DATA_IN', 'SPI_MOSI']
Expected: ['SPI_MOSI'] only
```

**If this test fails due to Issue #380:** Mark test as XFAIL and document the specific orphaned label behavior.

## Why This Is Important

**Interface Refinement is Essential During Design:**

1. **Naming Evolution**: Early designs use generic names, later refined to specific protocols
2. **Team Communication**: Standardized naming (SPI_MOSI vs DATA_IN) improves clarity
3. **Code Reuse**: Renaming subcircuit interfaces for different contexts
4. **Protocol Specificity**: Generic pins become protocol-specific (DATA → I2C_SDA)
5. **Documentation**: Interface names match datasheet terminology

**Real-world impact:**
- SPI interfaces: DATA_IN/DATA_OUT → SPI_MOSI/SPI_MISO
- I2C interfaces: SCL/SDA standardization
- USB interfaces: D+/D- vs DP/DM naming
- Power domains: VCC → VDD_3V3 for clarity

If hierarchical pin renaming doesn't work correctly:
- Designers stuck with initial naming choices
- Manual KiCad editing required for refactoring
- Risk of connectivity loss during manual renaming
- Inability to standardize interfaces across projects

## Success Criteria

This test PASSES when:
- Hierarchical label in subcircuit renamed from DATA_IN → SPI_MOSI
- Hierarchical pin on sheet symbol renamed from DATA_IN → SPI_MOSI
- **Old DATA_IN hierarchical label completely removed (Issue #380 requirement)**
- Component connections preserved (R1 still connected)
- Netlist shows new name "SPI_MOSI" with correct connectivity
- No "DATA_IN" net remains in netlist
- No orphaned or duplicate hierarchical labels

## Validation Level

**Level 2 (kicad-sch-api Semantic Validation):**
- Parse subcircuit .kicad_sch to find hierarchical labels
- Verify "SPI_MOSI" present, "DATA_IN" absent
- Parse parent .kicad_sch to verify sheet pin name updated
- Check component connections maintained

**Level 3 (Netlist Validation):**
- Export netlist via kicad-cli
- Parse netlist to verify "SPI_MOSI" net exists
- Verify "DATA_IN" net does NOT exist
- Confirm R1 appears in SPI_MOSI net

## Related Tests

- **Test 44**: Subcircuit hierarchical ports (basic port creation)
- **Test 13**: Rename component (UUID-based matching for component reference changes)
- **Test 58**: Mixed hierarchical + global labels (label type coexistence)
- **Test 40**: Net operations in subcircuit (modifying nets in child sheets)

## Notes

- This test focuses on RENAMING existing pins (not adding/removing)
- Tests hierarchical PIN renaming (not component reference renaming)
- Critical validation: Issue #380 (orphaned label removal)
- Validates netlist-level correctness (Level 3)
- Real-world scenario: design evolution and interface standardization
- Should use UUID-based matching (similar to Test 13 component renaming)
- May expose Issue #380 if old labels aren't properly cleaned up
