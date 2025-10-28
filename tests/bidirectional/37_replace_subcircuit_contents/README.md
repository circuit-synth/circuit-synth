# Test 37: Replace Subcircuit Contents

## What This Tests

**Core Question**: When you have a hierarchical circuit with a subcircuit containing specific components, can you replace the entire subcircuit implementation with a different design while preserving the hierarchical structure and port connections?

This tests **subcircuit redesign** - completely replacing what's inside a child sheet while keeping the sheet itself and its interface to the parent circuit.

## When This Situation Happens

- Developer creates a subcircuit with initial implementation (e.g., simple amplifier with R1, C1)
- Later decides to redesign that subcircuit internally (different components, different topology)
- Wants to replace the internal components while keeping:
  - The subcircuit name and identity
  - The sheet file in KiCad project
  - Port connections to parent circuit (if any)
- Regenerates KiCad expecting the old components removed and new ones added

## What Should Work

1. Generate initial KiCad with hierarchical structure:
   - Root circuit with main components
   - Subcircuit named "Amplifier" containing: R1 (10k), C1 (1µF)
2. Verify subcircuit contains initial components
3. Edit Python to redesign Amplifier subcircuit:
   - Remove: R1, C1
   - Add: R2 (4.7k), R3 (2.2k), C2 (10µF)
4. Regenerate KiCad project
5. Validate:
   - Amplifier subcircuit still exists as separate sheet file
   - New components (R2, R3, C2) exist in subcircuit
   - Old components (R1, C1) removed from subcircuit
   - Root circuit structure preserved
   - Hierarchical sheet structure maintained

## Manual Test Instructions

```bash
cd /Users/shanemattner/Desktop/circuit-synth2/tests/bidirectional/37_replace_subcircuit_contents

# Step 1: Generate initial KiCad project with subcircuit
uv run subcircuit_redesign.py
open subcircuit_redesign/subcircuit_redesign.kicad_pro

# Verify in KiCad:
#   - Root sheet exists with main circuit
#   - Amplifier subcircuit exists as separate sheet
#   - Amplifier sheet contains: R1 (10k), C1 (1µF)

# Step 2: Edit subcircuit_redesign.py
# Replace the Amplifier subcircuit creation section:
#   OLD: amplifier with R1, C1
#   NEW: amplifier with R2, R3, C2

# Step 3: Regenerate KiCad project
uv run subcircuit_redesign.py

# Step 4: Open regenerated KiCad project
open subcircuit_redesign/subcircuit_redesign.kicad_pro

# Step 5: Verify subcircuit redesign
#   - Amplifier sheet still exists (same file)
#   - Amplifier now contains: R2 (4.7k), R3 (2.2k), C2 (10µF)
#   - R1 and C1 no longer exist
#   - Root circuit structure unchanged
#   - No orphaned references or broken connections
```

## Expected Result

- ✅ Initial generation: Root circuit + Amplifier subcircuit with R1, C1
- ✅ Amplifier subcircuit file exists in KiCad project
- ✅ After redesign: New components R2, R3, C2 appear in Amplifier sheet
- ✅ Old components R1, C1 are removed from Amplifier sheet
- ✅ Amplifier sheet file preserved (not recreated unnecessarily)
- ✅ Root circuit components unchanged
- ✅ Hierarchical structure maintained
- ✅ No duplicate or orphaned components
- ✅ No broken port connections to parent

## Why This Is Important

**Iterative design workflow:**
1. Create circuit with initial subcircuit design
2. Later realize different topology needed for that subsystem
3. Can iterate on subcircuit implementation without reorganizing overall hierarchy
4. Changes are localized to subcircuit, don't affect parent circuit

If this doesn't work, users must either:
- Manually edit KiCad schematic (defeats purpose of code-based design)
- Delete subcircuit and recreate with new name (loses hierarchy and connections)
- Manually manage synchronization between Python and KiCad

## Success Criteria

This test PASSES when:
- Root circuit is generated with initial subcircuit (R1, C1)
- Amplifier subcircuit file exists as separate sheet
- After redesign and regeneration:
  - New components (R2, R3, C2) present in Amplifier sheet
  - Old components (R1, C1) removed from Amplifier sheet
  - Amplifier sheet file preserved
  - Root circuit unchanged
  - No ERC errors in KiCad project
  - JSON netlist shows correct hierarchical structure with updated components

## Validation Level

**Level 2 (kicad-sch-api)**: Validates schematic structure using kicad-sch-api library
- Checks subcircuit sheet file exists
- Verifies new components present in correct sheet
- Confirms old components removed
- Validates JSON netlist hierarchical structure
- Confirms root circuit unmodified

## Notes

- Tests complete subcircuit replacement (not partial updates)
- Assumes subcircuit has no external ports (simplified)
- Cross-sheet power connections future test (FUTURE_TESTS.md Category B)
- Tests Python → KiCad workflow (not KiCad → Python redesign)
- Demonstrates iterative subcircuit development capability
