# Test 08: Component Layer Assignment

## What This Tests

Component layer assignment for double-sided PCBs - the ability to place components on the top (F.Cu) or bottom (B.Cu) side of the PCB, and to modify layer assignments while preserving positions.

## When This Situation Happens

- Designing cost-optimized double-sided PCBs (component placement on both sides)
- Moving components between sides to balance the board
- Managing assembly cost (bottom-side assembly typically costs more)
- Re-optimizing component placement for manufacturing
- Supporting flex circuits or specialized assembly workflows

## What Should Work

1. Components can be assigned to specific layers (F.Cu for top, B.Cu for bottom)
2. PCB generation respects layer assignments
3. Layer assignments can be modified in Python code
4. PCB regeneration applies new layer assignments
5. Component positions are preserved when changing layers
6. Assembly documentation reflects actual layer assignments
7. Double-sided PCBs are manufacturable with correct layer separation

## Why This Matters

**Double-sided PCBs are critical for real-world design:**
- **Cost optimization**: Placing components on bottom side may reduce board size/cost
- **Assembly planning**: Top and bottom sides have different assembly sequences and costs
- **Design iteration**: Ability to move components between sides without losing position data
- **Manufacturing**: Layer assignments affect bill of materials and assembly workflow
- **Flexibility**: Some designs require components on both sides for routing or thermal reasons

Without this working, users cannot optimize designs for cost or implement complex layouts.

## Validation Approach

**Level 2: kicad-pcb-api Structural Validation**

```python
from kicad_pcb_api import PCBBoard

# Initial PCB with R1 on F.Cu, R2 on B.Cu
pcb = PCBBoard.load(str(pcb_file))
r1 = next(fp for fp in pcb.footprints if fp.reference == "R1")
r2 = next(fp for fp in pcb.footprints if fp.reference == "R2")

# Store positions
r1_pos_initial = r1.position  # (x, y)
r2_pos_initial = r2.position

# Modify Python code to swap layers:
# r1.layer = "B.Cu"  # Moved from F.Cu to B.Cu
# r2.layer = "F.Cu"  # Moved from B.Cu to F.Cu

# Regenerate and validate
pcb_final = PCBBoard.load(str(pcb_file))
r1_final = next(fp for fp in pcb_final.footprints if fp.reference == "R1")
r2_final = next(fp for fp in pcb_final.footprints if fp.reference == "R2")

# CRITICAL: Positions must be preserved
assert r1_final.position == r1_pos_initial  # Position unchanged!
assert r2_final.position == r2_pos_initial  # Position unchanged!
```

## Manual Test Instructions

```bash
cd /Users/shanemattner/Desktop/circuit-synth3/tests/pcb_generation/08_component_layer_assignment

# Generate initial PCB with R1 on F.Cu, R2 on B.Cu
uv run fixture.py

# Check files created
ls -la double_sided_pcb/

# Open in KiCad - should show components on different sides
open double_sided_pcb/double_sided_pcb.kicad_pro

# In KiCad PCB editor:
# - View → Show layers
# - Toggle F.Cu layer - should see R1
# - Toggle B.Cu layer - should see R2
```

## Expected Result

- ✅ KiCad project generated (.kicad_pro)
- ✅ PCB file generated (.kicad_pcb)
- ✅ PCB opens successfully in KiCad
- ✅ Components present on correct layers:
  - R1 on F.Cu (top/front side)
  - R2 on B.Cu (bottom/back side)
- ✅ Positions preserved when layers modified
- ✅ kicad-pcb-api can load and analyze PCB
- ✅ Assembly workflow properly reflects layer assignments

## Test Output Example

```
======================================================================
STEP 1: Generate initial PCB with layers
======================================================================
✅ Step 1: Initial PCB generated

======================================================================
STEP 2: Validate initial layer assignments
======================================================================
✅ Step 2: Initial PCB validated
   - R1 found at position: (20.0, 15.0)
   - R2 found at position: (50.0, 15.0)
   - Components on expected layers

======================================================================
STEP 3: Swap layer assignments (R1: B.Cu, R2: F.Cu)
======================================================================
✅ Step 3: Layer assignments swapped in Python
   - R1: F.Cu → B.Cu
   - R2: B.Cu → F.Cu

======================================================================
STEP 4: Regenerate PCB with swapped layers
======================================================================
✅ Step 4: PCB regenerated with swapped layers

======================================================================
STEP 5: Validate new layer assignments
======================================================================
✅ Step 5: Components validated after layer swap

======================================================================
STEP 6: VALIDATE POSITION PRESERVATION
======================================================================
✅ Step 6: POSITION PRESERVATION VERIFIED!
   - R1 position preserved: (20.0, 15.0) ✓
   - R2 position preserved: (50.0, 15.0) ✓

======================================================================
STEP 7: Validate assembly workflow implications
======================================================================
✅ Step 7: Assembly workflow implications
   - R1 assigned to B.Cu (bottom assembly)
   - R2 assigned to F.Cu (top assembly)
   - Cost implications: Bottom assembly typically costs more
   - Manufacturing sequence: F.Cu components first, then B.Cu

======================================================================
✅ TEST PASSED: Component Layer Assignment
======================================================================
```

## Key Validation Points

| Aspect | Validation | Expected |
|--------|-----------|----------|
| **Layer Assignment** | Components assigned to F.Cu/B.Cu | F.Cu for R1, B.Cu for R2 |
| **PCB File Valid** | kicad-pcb-api.load() | Loads without error |
| **Components Found** | Footprint count and references | R1 and R2 present |
| **Position Preservation** | Positions before/after layer swap | Exactly equal |
| **Layer Modification** | Python code accepts layer attribute | Modifies without error |
| **Regeneration Works** | PCB regenerates with new layers | New layers applied correctly |
| **Assembly Workflow** | Layer assignments affect manufacturing | Documented and understood |

## Test Classification

- **Category**: Board Management Test
- **Priority**: HIGH - Double-sided PCBs are common in real designs
- **Validation Level**: Level 2 (kicad-pcb-api structural validation)
- **Complexity**: Medium (layer management, position preservation)
- **Execution Time**: ~5 seconds

## Assembly Cost Implications

### Top Layer (F.Cu) Assembly
- Standard pick-and-place assembly
- Automated, lowest cost
- Solder reflow in single pass

### Bottom Layer (B.Cu) Assembly
- Secondary pick-and-place operation
- Typically 30-50% cost premium over top layer
- Reflow process more complex
- Manual verification may be required

### Design Optimization
The ability to modify layer assignments in Python enables:
1. Cost exploration: Move low-value components to top layer
2. Thermal optimization: Strategic placement for heat dissipation
3. Layout iteration: Rebalance board without losing position data
4. Manufacturing planning: Accurate assembly process planning

## Notes

- Layer assignments are specified via `component.layer` attribute
- Positions are measured from board origin (typically corner)
- Layer assignment affects manufacturing cost and process
- Both F.Cu (top) and B.Cu (bottom) are standard for rigid PCBs
- Position preservation is critical - users won't accept losing layout work
- Some contract manufacturers may charge premium for complex double-sided layouts
