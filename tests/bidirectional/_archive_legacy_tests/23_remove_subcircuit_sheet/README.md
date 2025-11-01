# Test 23: Remove Subcircuit Sheet

## What This Tests

Validates that removing a hierarchical child sheet from Python code correctly removes it from the regenerated KiCad project.

## When This Situation Happens

- Developer has a hierarchical circuit with root sheet and child sheet(s)
- Decides a child sheet module is no longer needed
- Removes the subcircuit from Python code
- Regenerates KiCad project to reflect the deletion

## What Should Work

- Initial hierarchical circuit created with root sheet (R1) and child sheet (R2)
- Subcircuit removed from Python code
- Regenerated KiCad project only has root sheet
- Child sheet file removed from output directory
- Root sheet component positions preserved

## Manual Test Instructions

```bash
cd /Users/shanemattner/Desktop/circuit-synth2/tests/bidirectional/23_remove_subcircuit_sheet

# Step 1: Generate initial KiCad project with hierarchical structure
uv run hierarchical_circuit.py
open hierarchical_circuit/hierarchical_circuit.kicad_pro
# Verify: Root sheet has R1, Child sheet exists with R2

# Step 2: Edit hierarchical_circuit.py to remove the subcircuit
# Comment out or delete the add_subcircuit() call

# Step 3: Regenerate KiCad project (without child sheet)
uv run hierarchical_circuit.py

# Step 4: Open regenerated KiCad project
open hierarchical_circuit/hierarchical_circuit.kicad_pro

# Step 5: Verify child sheet is removed
#   - Root sheet still has R1 (position preserved)
#   - Child sheet no longer exists (no .kicad_sch file)
#   - Only root schematic file present
```

## Expected Result

- ✅ Initial KiCad project has hierarchical structure with root and child sheets
  - Root sheet contains R1 (10k resistor)
  - Child sheet contains R2 (4.7k resistor)
- ✅ After removing subcircuit from Python and regenerating:
  - Root sheet is regenerated with only R1
  - Root sheet component (R1) preserved with original position
  - Child sheet is no longer created/updated
- ✅ KiCad project structure validated with kicad-sch-api
- ✅ Level 2 validation: semantic validation using schematic parser
