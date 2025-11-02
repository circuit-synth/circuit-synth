# Test 22: Add Subcircuit Sheet (Hierarchical Child Sheet)

## What This Tests

**Core Question**: When you have a hierarchical circuit with a root sheet and add a subcircuit (child sheet) in Python code, does KiCad generation create both sheets with proper hierarchy and component placement?

This tests **hierarchical sheet creation** - adding a new child sheet (subcircuit) that appears as a separate schematic file in KiCad.

## When This Situation Happens

- Developer generates circuit with components on root sheet (R1)
- Later decides to organize components hierarchically
- Adds a Subcircuit (child circuit) in Python code with its own components (R2)
- Regenerates KiCad expecting both sheets to exist as separate files

## What Should Work

1. Generate initial KiCad with root circuit containing R1 (root sheet only)
2. Manually verify only one schematic file exists in KiCad project
3. Edit Python to add Subcircuit with R2 component
4. Regenerate KiCad project
5. Validate both sheets exist:
   - Root sheet contains R1
   - Child sheet exists as separate file
   - Child sheet contains R2
6. Validate positions preserved in both sheets

## Manual Test Instructions

```bash
cd /Users/shanemattner/Desktop/circuit-synth2/tests/bidirectional/22_add_subcircuit_sheet

# Step 1: Generate initial KiCad project (root sheet only, R1)
uv run hierarchical_circuit.py
open hierarchical_circuit/hierarchical_circuit.kicad_pro
# Verify: Only one .kicad_sch file in project
# Verify: R1 visible on root sheet

# Step 2: Edit hierarchical_circuit.py to add child sheet
# Uncomment the subcircuit section or add:
#   child = Circuit("ChildSheet")
#   r2 = Component(symbol="Device:R", ref="R2", value="4.7k",
#                  footprint="Resistor_SMD:R_0603_1608Metric")
#   child.add_component(r2)
#   circuit_obj.add_subcircuit(child)

# Step 3: Regenerate KiCad project with subcircuit
uv run hierarchical_circuit.py

# Step 4: Open regenerated KiCad project
open hierarchical_circuit/hierarchical_circuit.kicad_pro
# Verify:
#   - Root sheet has R1
#   - Child sheet file exists (e.g., ChildSheet.kicad_sch)
#   - Child sheet contains R2
#   - Positions preserved in both sheets
#   - Hierarchy properly established (KiCad shows hierarchy tree)
```

## Expected Result

- ✅ Initial generation: Only root sheet with R1
- ✅ Child sheet file created after regeneration
- ✅ Root sheet contains R1 at preserved position
- ✅ Child sheet contains R2 at auto-placed position
- ✅ KiCad recognizes hierarchical structure (File > Reload Schematic shows proper tree)
- ✅ Both sheets are separate .kicad_sch files
- ✅ No cross-sheet connections yet (simplified - cross-sheet nets in FUTURE_TESTS.md)
- ✅ No duplicate components on either sheet

## Why This Is Important

**Hierarchical design workflow:**
1. Start with flat circuit (single sheet)
2. As complexity grows, organize into subsystems (child sheets)
3. Each sheet can be worked on independently
4. Organization is maintainable without losing existing work

If this doesn't work, users can't build complex systems incrementally - they must choose hierarchical structure upfront or manually reorganize in KiCad (defeating the purpose of code-based design).

## Success Criteria

This test PASSES when:
- Root sheet is generated with R1
- After adding subcircuit and regenerating, child sheet file exists
- Child sheet contains R2 with proper position
- Root sheet R1 position preserved across regeneration
- KiCad project recognizes both sheets as hierarchy
- No error messages during generation
- No ERC errors in KiCad project
- Each sheet is a separate .kicad_sch file

## Validation Level

**Level 2 (kicad-sch-api)**: Validates schematic structure and sheet hierarchy using kicad-sch-api library
- Checks that schematic files exist
- Verifies component presence on correct sheets
- Confirms hierarchy relationship
- Does NOT yet validate cross-sheet connections (future test)

## Notes

- This is a SIMPLIFIED test of hierarchical capability
- Complex operations like cross-sheet power nets in FUTURE_TESTS.md Category B
- Uses Circuit.add_subcircuit() API for hierarchical organization
- Each subcircuit becomes a separate .kicad_sch file in KiCad
