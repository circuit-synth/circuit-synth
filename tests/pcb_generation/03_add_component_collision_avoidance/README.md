# Test 03: Add Component to PCB with Collision Avoidance

## What This Tests

Adding new components to an existing PCB with smart auto-placement and collision avoidance.

## When This Situation Happens

- Adding decoupling capacitors near power inputs
- Adding test points for debugging
- Adding debug headers (JTAG, UART, etc.)
- Adding pull-up/pull-down resistors
- Fixing schematic issues by adding components
- Optimizing power distribution (adding bulk caps)

## What Should Work

1. Generate initial PCB with R1, R2
2. Store R1, R2 positions
3. Add R3 in Python code
4. Regenerate PCB
5. **R1, R2 positions PRESERVED** (placement preservation)
6. **R3 auto-placed WITHOUT collisions**
7. **R3 NOT at origin (0, 0)** - intelligent placement
8. All components properly spaced (minimum 5mm separation)
9. All components within board bounds

## Why This Matters

**Adding components is a common PCB development workflow:**

Real-world scenario:
1. Generate PCB with main components (MCU, power, regulators)
2. Place components optimally (2-4 hours of work)
3. Route traces (4-8 hours)
4. Power analysis shows need for more decoupling caps
5. **Add 4 decoupling caps in Python**
6. **Regenerate PCB**
7. **Placement preserved** ✓ (from Test 02)
8. **New caps auto-placed nearby** ✓ (what this test validates)
9. **Adjust cap positions, re-route** as needed

Without smart auto-placement + collision avoidance:
- ❌ New components placed randomly
- ❌ Overlap with existing components
- ❌ Placed at origin (0, 0) - unusable
- ❌ Manual placement recovery required (hours of work)
- ❌ Tool becomes unreliable

With this test passing:
- ✅ New components added reliably
- ✅ Existing placements preserved
- ✅ Auto-placement is intelligent (not origin, proper spacing)
- ✅ Iterative development is practical
- ✅ Users can add components anytime

## Validation Approach

**Level 2: kicad-pcb-api Structural Validation**

```python
from kicad_pcb_api import PCBBoard

# Load regenerated PCB
pcb = PCBBoard.load(str(pcb_file))
assert len(pcb.footprints) == 3  # R1, R2, R3

# Find components
r1_final = next(fp for fp in pcb.footprints if fp.reference == "R1")
r2_final = next(fp for fp in pcb.footprints if fp.reference == "R2")
r3_final = next(fp for fp in pcb.footprints if fp.reference == "R3")

# Validation 1: Placement preserved
assert r1_final.position == r1_initial_pos
assert r2_final.position == r2_initial_pos

# Validation 2: R3 auto-placed (not at origin)
assert r3_final.position != (0.0, 0.0)

# Validation 3: Collision avoidance
def distance(p1, p2):
    return ((p2[0]-p1[0])**2 + (p2[1]-p1[1])**2)**0.5

assert distance(r1_final.position, r2_final.position) >= 5.0
assert distance(r1_final.position, r3_final.position) >= 5.0
assert distance(r2_final.position, r3_final.position) >= 5.0

# Validation 4: Within board bounds
max_x = max(fp.position[0] for fp in pcb.footprints)
max_y = max(fp.position[1] for fp in pcb.footprints)
assert max_x < 500.0 and max_y < 500.0
```

## Manual Test Instructions

```bash
cd /Users/shanemattner/Desktop/circuit-synth3/tests/pcb_generation/03_add_component_collision_avoidance

# Step 1: Generate initial PCB
uv run fixture.py

# Step 2: Verify initial state
open add_component_test/add_component_test.kicad_pro
# Note positions of R1 and R2

# Step 3: Modify fixture.py - uncomment R3 section

# Step 4: Regenerate
uv run fixture.py

# Step 5: Verify R3 was added and placed
open add_component_test/add_component_test.kicad_pro

# Check: R1 and R2 still in original positions ✓
# Check: R3 exists and not at (0, 0) ✓
# Check: R3 properly spaced from R1, R2 ✓
```

## Expected Result

- ✅ Initial PCB generated with R1, R2
- ✅ R1, R2 positions noted
- ✅ R3 added in Python code
- ✅ PCB regenerated successfully
- ✅ **R1 and R2 PRESERVED at original positions** ✓✓
- ✅ **R3 auto-placed** ✓
- ✅ **R3 NOT at origin (0, 0)** ✓
- ✅ **Minimum 5mm spacing between all components** ✓✓
- ✅ **All components within board bounds** ✓
- ✅ No overlaps or collisions

## Test Output Example

```
======================================================================
STEP 1: Generate initial PCB with R1, R2
======================================================================
✅ Step 1: Initial PCB generated

======================================================================
STEP 2: Validate initial PCB structure
======================================================================
✅ Step 2: Initial PCB validated
   - R1 position: (25.4, 15.2)
   - R2 position: (35.6, 25.4)

======================================================================
STEP 3: Add R3 to Python code
======================================================================
✅ Step 3: R3 added to Python code

======================================================================
STEP 4: Regenerate PCB with R3
======================================================================
✅ Step 4: PCB regenerated with R3

======================================================================
STEP 5: Validate preservation and auto-placement
======================================================================
✅ Validation 1: Placement PRESERVED
   - R1 at (25.4, 15.2) ✓
   - R2 at (35.6, 25.4) ✓
✅ Validation 2: R3 intelligent auto-placement
   - R3 NOT at origin ✓
   - R3 auto-placed at (50.8, 35.6) ✓
✅ Validation 3: Collision avoidance
   - R1 ↔ R2: distance OK ✓
   - R1 ↔ R3: distance OK ✓
   - R2 ↔ R3: distance OK ✓
✅ Validation 4: Component bounds
   - Max X: 50.8mm ✓
   - Max Y: 35.6mm ✓

======================================================================
✅ TEST PASSED: Add Component with Collision Avoidance
======================================================================

Summary:
  ✅ Placement preserved:
     - R1 stayed at (25.4, 15.2)
     - R2 stayed at (35.6, 25.4)
  ✅ Component addition works:
     - R3 added and auto-placed
  ✅ Smart auto-placement:
     - R3 NOT at origin (intelligent)
     - R3 at (50.8, 35.6)
  ✅ Collision avoidance:
     - All components properly spaced
     - Minimum 5mm separation maintained

🏆 Adding components to PCB works reliably!
   Iterative development with component additions is viable!
```

## Key Validation Points

| Aspect | Validation | Expected |
|--------|-----------|----------|
| **Initial PCB** | Generate with R1, R2 | 2 components |
| **Store Positions** | R1_initial, R2_initial | Positions recorded |
| **Add Component** | Add R3 in Python | Python code modified |
| **Regenerate** | Run fixture.py | 3 components in PCB |
| **R1 Preserved** | `r1.position == r1_initial` | EXACT MATCH ✓ |
| **R2 Preserved** | `r2.position == r2_initial` | EXACT MATCH ✓ |
| **R3 Exists** | `r3 is not None` | True ✓ |
| **R3 Smart Place** | `r3.position != (0, 0)` | True ✓ |
| **R1-R2 Distance** | distance ≥ 5mm | Maintained ✓ |
| **R1-R3 Distance** | distance ≥ 5mm | Maintained ✓ |
| **R2-R3 Distance** | distance ≥ 5mm | Maintained ✓ |
| **Board Bounds** | max(x,y) < 500mm | Within bounds ✓ |

## Test Classification

- **Category**: Component Addition Test
- **Priority**: HIGH - Common workflow pattern
- **Validation Level**: Level 2 (kicad-pcb-api structural validation)
- **Complexity**: Medium (involves Python modification + validation)
- **Execution Time**: ~5 seconds

## Comparison to Test 02

| Aspect | Test 02 (Placement Preservation) | Test 03 (Add Component) |
|--------|----------------------------------|------------------------|
| **Purpose** | Preserve manual work | Add new components |
| **Change** | Add component to circuit | Add component to circuit |
| **Manual Step** | Manually move R1 | No manual step |
| **Key Validation** | R1 stays at (50, 30) | R1, R2 preserved + R3 auto-placed |
| **Auto-placement** | Validates placement preserved | Validates smart placement |
| **Collision** | Collision avoidance bonus | **Primary focus: collision avoidance** |

## Real-World Workflow Examples

### Example 1: Adding Decoupling Caps

```
1. Generate PCB with MCU, power regulators, etc.
2. Place components optimally (2-4 hours)
3. Route power and ground (1-2 hours)
4. Power analysis shows need for more decoupling
5. Add 4x 0.1µF caps near VDD pins
6. Regenerate PCB
7. ✓ MCU stays in place (placement preserved)
8. ✓ Existing component positions unchanged
9. ✓ Caps auto-placed near power pins (smart)
10. ✓ No collisions between caps
11. Move caps to optimal positions near VDD
12. Route cap connections
13. Done!
```

### Example 2: Adding Test Points

```
1. PCB design mostly complete
2. Review team suggests test points for debugging
3. Add 3 test point components in Python
4. Regenerate PCB
5. ✓ Existing placements preserved
6. ✓ Test points auto-placed at sensible locations
7. ✓ No overlap with existing components
8. Fine-tune test point positions for access
9. Route test point connections
10. Continue testing
```

## Notes

- Smart auto-placement should place new components near related components
- Example: decoupling caps should be placed near power pins (future enhancement)
- Current test validates minimum collision avoidance (5mm spacing)
- Advanced placement algorithms can optimize further (proximity, routing density)
- Users can always manually adjust auto-placement after regeneration

## Related Tests

- **Test 01**: Blank PCB (foundation)
- **Test 02**: Placement Preservation (preservation mechanism)
- **Test 03**: Add Component (this test - addition with placement)
- **Test 04**: Delete Component (complement to addition)
- **Test 05**: Modify Fields (with placement preservation)
- **Test 06**: Component Rotation (with placement preservation)
