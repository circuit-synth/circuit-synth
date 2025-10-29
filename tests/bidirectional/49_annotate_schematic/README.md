# Test 49: Schematic Annotation (Real-World Workflow)

## What This Tests

**Core Question**: When you create a circuit with unannotated references (R?, R?, C?), generate to KiCad, run KiCad's annotation tool to assign numbers (R1, R2, C1), and sync back to Python, does circuit-synth recognize these as the same components (via UUID matching) and preserve their positions and connections?

This validates **UUID-based component matching through annotation** - a critical real-world workflow where reference designators change from placeholders (?) to numbered references.

## When This Situation Happens

**Real-World Workflow:**
1. Designer creates circuit in Python with unannotated references (R?, R?, C?)
2. Generates initial KiCad schematic - components appear with ? references
3. Opens KiCad and arranges components on schematic (layout work)
4. Runs KiCad annotation tool: Tools > Annotate Schematic > Annotate
   - R? → R1, R? → R2, C? → C1 (sequential numbering)
5. Saves schematic in KiCad
6. Returns to Python, wants to sync annotated references back
7. **Critical**: Does circuit-synth recognize R1 is the same as R?, or treat it as Remove+Add?

**Why This Matters:**
- Annotation is a **standard KiCad workflow** for assigning reference numbers
- If sync treats annotation as Remove+Add, all layout work is lost
- UUID matching should recognize same component despite reference change
- Nets must update to use new references (R1 instead of R?)

## What Should Work

### Initial Generation (Unannotated)
1. ✅ Generate KiCad with R?, R?, C? (unannotated references)
2. ✅ Components appear in schematic with ? placeholders
3. ✅ Position assignment works (components don't overlap)
4. ✅ Nets connect to R?, R?, C? pins

### After KiCad Annotation
5. ✅ Run KiCad annotation tool: R? → R1, R? → R2, C? → C1
6. ✅ Save schematic with annotated references
7. ✅ Schematic file now has R1, R2, C1 instead of R?, R?, C?

### Python Synchronization
8. ✅ Sync back to Python circuit
9. ✅ **UUID matching recognizes same components** (not Remove+Add)
10. ✅ Component positions preserved (layout work not lost)
11. ✅ Python circuit now has R1, R2, C1 references
12. ✅ Nets updated to show R1, R2, C1 connections

### Adding New Component After Annotation
13. ✅ Add new R? component in Python
14. ✅ Regenerate KiCad
15. ✅ New component gets next number: R3 (after annotation)
16. ✅ Existing R1, R2, C1 unchanged

## Manual Test Instructions

```bash
cd /Users/shanemattner/Desktop/circuit-synth2/tests/bidirectional/49_annotate_schematic

# Step 1: Generate initial KiCad with unannotated references
uv run unannotated_circuit.py
# Verify: unannotated_circuit/unannotated_circuit.kicad_sch created
# Check schematic file contains: (property "Reference" "R?")

# Step 2: Open schematic in KiCad and arrange components
open unannotated_circuit/unannotated_circuit.kicad_pro
# - Notice components show R?, R?, C? in schematic
# - Arrange components in a specific layout (spend time positioning)
# - Note the positions (e.g., R? at (100, 50), R? at (120, 50), C? at (140, 50))
# - Save schematic but don't close yet

# Step 3: Run KiCad annotation tool
# In KiCad:
#   - Tools > Annotate Schematic... > Click "Annotate"
#   - Annotation assigns: R? → R1, R? → R2, C? → C1
#   - Save schematic (Cmd+S)
#   - Close KiCad

# Step 4: Verify annotation in schematic file
grep 'property "Reference"' unannotated_circuit/unannotated_circuit.kicad_sch
# Should show: R1, R2, C1 (no more R?, C?)

# Step 5: Sync back to Python (simulated by regenerating)
# In a real workflow, this would be:
#   circuit_obj = load_from_kicad("unannotated_circuit/unannotated_circuit.kicad_sch")
# For testing, we'll modify Python code and regenerate:

# Edit unannotated_circuit.py:
#   Change ref="R?" to ref="R1" (first resistor)
#   Change ref="R?" to ref="R2" (second resistor)
#   Change ref="C?" to ref="C1" (capacitor)

# Step 6: Regenerate KiCad from annotated Python
uv run unannotated_circuit.py

# Step 7: Open regenerated schematic and verify
open unannotated_circuit/unannotated_circuit.kicad_pro
# Verify:
#   - Components now show R1, R2, C1 (annotated references)
#   - Positions preserved at (100, 50), (120, 50), (140, 50)
#   - UUIDs unchanged (same components, just renamed)
#   - Nets now show R1, R2, C1 connections (not R?, R?, C?)

# Step 8: Add new unannotated component and re-annotate
# Edit unannotated_circuit.py: Add another R? resistor
# Regenerate, open in KiCad, run annotation tool again
# Verify: New component gets R3 (sequential after R1, R2)
```

## Expected Result

### Initial Generation
- ✅ KiCad schematic has components with R?, R?, C? references
- ✅ Components placed at default positions
- ✅ Nets show connections to R?, R?, C? pins
- ✅ Warning in KiCad: "Components need annotation"

### After Annotation in KiCad
- ✅ Schematic file updated: R? → R1, R? → R2, C? → C1
- ✅ Component positions unchanged (manual layout preserved)
- ✅ UUIDs unchanged (same components, just renamed)
- ✅ Nets now reference R1, R2, C1 instead of R?, R?, C?

### After Python Sync
- ✅ Python circuit references updated to R1, R2, C1
- ✅ **Positions preserved** (UUID matching worked!)
- ✅ No "Remove R? + Add R1" behavior (would lose position)
- ✅ Nets in Python show R1, R2, C1 connections
- ✅ Component count unchanged (3 components before/after)

### After Adding New Component
- ✅ New R? component added in Python
- ✅ Regenerated schematic has 4 components: R1, R2, R3 (new), C1
- ✅ After annotation, new component becomes R3 (sequential)
- ✅ Existing R1, R2, C1 unchanged and positions preserved

## Why This Is Critical

**Standard KiCad Workflow:**
- **Annotation is THE standard way** to assign reference numbers in KiCad
- Most designers use ? placeholders during initial design
- KiCad's annotation tool assigns sequential numbers automatically
- This is not an edge case - it's a fundamental KiCad workflow

**If UUID Matching Fails:**
- ❌ Sync treats R1 as "new component" and R? as "removed"
- ❌ Component position is lost (Remove+Add instead of Rename)
- ❌ All manual layout work discarded
- ❌ User must re-position components after every annotation
- ❌ Bidirectional sync becomes unusable for real projects

**If UUID Matching Works (Issue #369 Fix):**
- ✅ Sync recognizes R1 as renamed R? (same component)
- ✅ Component position preserved through annotation
- ✅ Manual layout work is NOT lost
- ✅ Nets automatically update to new references
- ✅ Bidirectional sync supports real KiCad workflows
- ✅ Designer can iterate: Python → KiCad → Annotate → Python

## Validation Levels

**Level 1: Text Search (Basic)**
- Schematic file contains R1, R2, C1 (not R?, R?, C?)
- No duplicate components (no Remove+Add)

**Level 2: Semantic Validation (kicad-sch-api)**
- `component.reference` shows R1, R2, C1
- `component.uuid` unchanged before/after annotation
- `component.position` preserved through reference change

**Level 3: Netlist Validation**
- Generated netlist uses R1, R2, C1 (not R?, R?, C?)
- Net connections reflect annotated references
- No "net to unconnected pin" warnings

## Success Criteria

This test PASSES when:
1. ✅ Unannotated circuit (R?, R?, C?) generates to KiCad successfully
2. ✅ Components can be manually positioned in KiCad
3. ✅ KiCad annotation tool successfully assigns R1, R2, C1
4. ✅ Python sync recognizes annotated components via UUID
5. ✅ **Component positions preserved through annotation** (not Remove+Add)
6. ✅ Python circuit references update to R1, R2, C1
7. ✅ Nets update to use new references (R1, R2, C1)
8. ✅ Adding new R? component results in R3 after annotation
9. ✅ No duplicate components created
10. ✅ No position loss through rename workflow

## Related Issues

- **Issue #369**: UUID-based component matching for reference changes
- This test validates UUID matching works for annotation workflow
- Critical for real-world KiCad usage patterns
