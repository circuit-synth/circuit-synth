# Test 62: Wire Routing Preservation (Priority 2 - Nice-to-have Aesthetic)

## What This Tests

**Core Question**: When you manually route wires with specific paths (multiple segments, corners) in KiCad and then regenerate from Python, are the wire routing paths preserved, or do they get reset to default straight-line connections?

This validates whether **custom wire routing is preserved** during bidirectional synchronization, which is important for aesthetically pleasing schematics and complex routing scenarios.

## Priority Level

**Priority 2: Nice-to-have Aesthetic Feature**

Wire routing preservation is desirable for maintaining clean, professional-looking schematics, but it's not critical for electrical functionality. The circuit will work correctly regardless of wire routing.

## When This Situation Happens

- Developer generates KiCad circuit with two resistors connected by a net
- Manually routes the wire with multiple segments (e.g., L-shaped path with corner)
- Later modifies component value in Python (e.g., change R1 from 10k to 22k)
- Regenerates KiCad from Python
- **Question**: Does the custom wire routing stay, or does it reset to straight line?

## What Should Work (Ideal Behavior)

1. Generate KiCad with R1-R2 connected by net → auto-routed with straight line
2. Manually route wire in KiCad with L-shaped path (3 segments with corners)
3. Modify R1 value in Python → regenerate
4. **Wire routing preserved** (still L-shaped, not reset to straight line)
5. Add R3 to same net → existing routing preserved, new wire segment added

## Current Behavior (Likely)

Based on typical schematic tools and complexity:
- Wire routing is **likely NOT preserved** during regeneration
- Wires reset to default straight-line connections
- This is acceptable for Priority 2 feature (aesthetic, not functional)

## Manual Test Instructions

```bash
cd /Users/shanemattner/Desktop/circuit-synth2/tests/bidirectional/62_wire_routing_preservation

# Step 1: Generate initial KiCad project with R1-R2 connected
uv run routed_circuit.py
open routed_circuit/routed_circuit.kicad_pro
# Note: Wire between R1 and R2 is straight line (default)

# Step 2: Manually route wire in KiCad with L-shaped path
# In KiCad schematic editor:
#   - Delete existing wire segment
#   - Draw new wire from R1 pin 2
#   - Add corner/bend (e.g., go down 10mm, then right to R2)
#   - Connect to R2 pin 1
#   - Result: L-shaped wire path with 2-3 segments
# Save schematic (Cmd+S), close KiCad

# Step 3: Verify custom routing in .kicad_sch file
# Check for multiple (wire (pts (xy ...) (xy ...))) entries with corners

# Step 4: Modify component value in Python
# Edit routed_circuit.py: change R1 value from "10k" to "22k"

# Step 5: Regenerate KiCad from modified Python
uv run routed_circuit.py

# Step 6: Check wire routing preservation
open routed_circuit/routed_circuit.kicad_pro
# Verify:
#   - R1 value updated to 22k ✓
#   - Wire routing: preserved (L-shaped) OR reset (straight line)?
#   - Document actual behavior
```

## Expected Result

**Scenario A: Routing Preserved (Ideal)**
- ✅ R1 value updated to 22k
- ✅ L-shaped wire routing preserved (not reset to straight line)
- ✅ Custom schematic aesthetic maintained

**Scenario B: Routing Reset (Acceptable for Priority 2)**
- ✅ R1 value updated to 22k
- ⚠️ Wire routing reset to straight line (custom routing lost)
- ⚠️ User must re-route wires after each regeneration
- 📝 Document as current limitation
- 📝 Test marked as XFAIL if not preserved

## Validation Levels

**Level 1: File Generation**
- Schematic file exists and is valid
- Wire segments present in .kicad_sch

**Level 2: Wire Segment Analysis**
- Parse .kicad_sch to extract wire segments
- Count number of wire segments for the net
- Compare segment positions before/after regeneration
- Document preservation vs. reset behavior

**Visual Validation**
- Manual inspection in KiCad schematic editor
- Verify wire path appearance (corners, bends)

## Why This Test Matters

**For Professional Schematics:**
- Complex circuits need organized wire routing
- Manual routing improves readability
- Aesthetic appearance matters for documentation

**For Iterative Development:**
- If routing is preserved: users can maintain clean layouts
- If routing is reset: users lose aesthetic work (but circuit still works)

**Acceptable Trade-off:**
- Priority 2 feature - not critical for functionality
- Electrical connectivity is more important than routing aesthetics
- Can be implemented later as enhancement

## KiCad Wire Format

Wire segments in .kicad_sch format:
```lisp
(wire
  (pts
    (xy 100.0 50.0) (xy 100.0 75.0)  ; Vertical segment (down)
  )
  (stroke (width 0) (type default))
  (uuid "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
)
(wire
  (pts
    (xy 100.0 75.0) (xy 150.0 75.0)  ; Horizontal segment (right)
  )
  (stroke (width 0) (type default))
  (uuid "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
)
```

Multiple wire blocks = multi-segment routing with corners/bends.

## Test Outcome Options

1. **PASS**: Wire routing preserved through regeneration
2. **XFAIL**: Wire routing reset (document as known limitation)
3. **SKIP**: Test documents behavior without enforcing requirement
