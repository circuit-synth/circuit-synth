# Test 10: Mounting Holes

## What This Tests

Mounting hole definition and placement - the ability to define mechanical mounting holes in Python, verify their positions, and modify them while preserving other board features.

## When This Situation Happens

- Designing PCBs that mount to an enclosure
- Creating boards that fit standard mounting patterns (100x80mm, 50x50mm)
- Adapting designs for different enclosures (requires moving mounting holes)
- Optimizing mechanical assembly (adding reinforcement points)
- Designing test fixtures that require precise mounting points
- Creating modular boards with standard mounting interfaces

## What Should Work

1. Mounting holes can be defined with position and drill diameter
2. PCB generation creates holes at specified positions
3. Hole dimensions match specification (e.g., 2.5mm for M2)
4. Mounting holes can be found and analyzed via kicad-pcb-api
5. Hole positions can be validated (typically via-like structures)
6. Mounting holes can be added or moved in Python code
7. PCB regeneration applies hole changes
8. Positions remain accurate through design iterations

## Why This Matters

**Mechanical assembly is mandatory for real products:**
- **Enclosure fit**: Board must mount to case with zero tolerance
- **Stress relief**: Proper mounting prevents mechanical failure
- **Thermal management**: Mounting points affect heat dissipation
- **Manufacturing**: Hole placement affects drilling costs
- **Testing**: Mounting points define test fixture design
- **Reliability**: Poor mounting causes field failures

Without proper hole placement, boards can't be assembled into products.

## Standard Mounting Patterns

### 100x80mm Board (Common)
```
(3,77)  ○─────────────────────────○ (97,77)

   │  COMPONENT AREA                │
   │                                │
   │                                │
   │                                │
   │  STANDARD 94mm HORIZONTAL      │
   │  STANDARD 74mm VERTICAL        │

(3,3)   ○─────────────────────────○ (97,3)
```

### 50x50mm Board (Compact)
```
(3,47)  ○─────────────────○ (47,47)

   │  SMALL BOARD       │
   │                    │
   │  44x44mm USABLE    │
   │                    │

(3,3)   ○─────────────────○ (47,3)
```

## Validation Approach

**Level 2: kicad-pcb-api Structural Validation**

```python
from kicad_pcb_api import PCBBoard

# Initial PCB with 4 mounting holes
pcb = PCBBoard.load(str(pcb_file))

# Validate holes present (via structures in PCB)
expected_holes = [
    (3.0, 3.0),      # Bottom-left
    (97.0, 3.0),     # Bottom-right
    (3.0, 77.0),     # Top-left
    (97.0, 77.0),    # Top-right
]

# Extract holes from PCB file
import re
final_holes = []
pattern = r'\(pad\s+""\s+thru_hole\s+circle.*?\)'
for match in re.finditer(pattern, content, re.DOTALL):
    pos_match = re.search(r'\(at\s+([\d.-]+)\s+([\d.-]+)\)', match.group(0))
    if pos_match:
        x, y = map(float, pos_match.groups())
        final_holes.append((x, y))

# Verify all expected holes present (tolerance 0.5mm)
for expected_pos in expected_holes:
    assert any(
        abs(actual[0] - expected_pos[0]) < 0.5 and
        abs(actual[1] - expected_pos[1]) < 0.5
        for actual in final_holes
    ), f"Hole at {expected_pos} not found!"
```

## Manual Test Instructions

```bash
cd /Users/shanemattner/Desktop/circuit-synth3/tests/pcb_generation/10_mounting_holes

# Generate PCB with 4 mounting holes
uv run fixture.py

# Check files created
ls -la mounted_pcb/

# Open in KiCad - should show mounting holes
open mounted_pcb/mounted_pcb.kicad_pro

# In KiCad PCB editor:
# - Use "Measure" tool to verify hole positions
# - Holes should be at corners: (3,3), (97,3), (3,77), (97,77)
# - Drill size should be 2.5mm (M2 standard)
# - Use "Design Rules Check" to verify no clearance issues
```

## Expected Result

- ✅ KiCad project generated (.kicad_pro)
- ✅ PCB file generated (.kicad_pcb)
- ✅ PCB opens successfully in KiCad
- ✅ 4 mounting holes visible at corners:
  - (3mm, 3mm) - bottom-left
  - (97mm, 3mm) - bottom-right
  - (3mm, 77mm) - top-left
  - (97mm, 77mm) - top-right
- ✅ Hole drill diameter: 2.5mm (M2 standard)
- ✅ Holes can be found and analyzed
- ✅ After modification: 5 holes with center hole at (50mm, 40mm)
- ✅ Positions preserved through design iterations

## Test Output Example

```
======================================================================
STEP 1: Generate PCB with 4 mounting holes
======================================================================
✅ Step 1: PCB with 4 mounting holes generated

======================================================================
STEP 2: Validate mounting hole positions
======================================================================
✅ Step 2: Mounting holes validated
   - Found 4 holes in PCB file
     Hole at (3.0, 3.0)
     Hole at (97.0, 3.0)
     Hole at (3.0, 77.0)
     Hole at (97.0, 77.0)

======================================================================
STEP 3: Validate hole dimensions
======================================================================
✅ Step 3: Hole dimensions validated
   - Expected drill diameter: 2.5mm
   - Found hole size: 2.5mm

======================================================================
STEP 4: Add 5th mounting hole at center (50mm, 40mm)
======================================================================
✅ Step 4: 5th mounting hole added at center

======================================================================
STEP 5: Regenerate PCB with 5 mounting holes
======================================================================
✅ Step 5: PCB regenerated with 5 mounting holes

======================================================================
STEP 6: Validate 5 holes with correct positions
======================================================================
✅ Step 6: Hole validation complete
   - Expected: 5 mounting holes
   - Found: 5 holes
   ✓ Hole at (3.0, 3.0) confirmed
   ✓ Hole at (97.0, 3.0) confirmed
   ✓ Hole at (3.0, 77.0) confirmed
   ✓ Hole at (97.0, 77.0) confirmed
   ✓ Hole at (50.0, 40.0) confirmed
   - All 5 holes present at correct positions ✓

======================================================================
✅ TEST PASSED: Mounting Holes
======================================================================
```

## Key Validation Points

| Aspect | Validation | Expected |
|--------|-----------|----------|
| **Hole Count** | Count of mounting holes | 4 initial, 5 after modification |
| **Hole Positions** | Coordinates match specification | Within 0.5mm tolerance |
| **Drill Diameter** | Hole size | 2.5mm (M2 standard) |
| **Hole Structure** | Via/thru-hole detection | Via count increases with modifications |
| **PCB Regeneration** | Holes apply correctly | All 5 holes present after regen |
| **Clearance** | No interference with components | Components away from holes |
| **Manufacturability** | Standard hole sizes supported | 2.5mm M2 holes typical |

## Test Classification

- **Category**: Board Management Test
- **Priority**: CRITICAL - Mechanical assembly is mandatory
- **Validation Level**: Level 2 (kicad-pcb-api structural validation)
- **Complexity**: Medium (hole positioning, verification)
- **Execution Time**: ~5 seconds

## Mounting Hardware Standards

### M2 (2.5mm hole)
- Screw: M2x4 or M2x6
- Cost: Very low
- Common in: Consumer electronics, enclosures

### M3 (3.2mm hole)
- Screw: M3x6 or M3x8
- Cost: Low
- Common in: Industrial, automotive

### M4 (4.5mm hole)
- Screw: M4x8 or M4x10
- Cost: Low
- Common in: Heavy duty, vibration-prone

## Design Best Practices

1. **Use standard patterns** - 100x80mm is widely supported
2. **Plan for thermal** - Mounting points affect heat flow
3. **Add extra holes** - Allows flexibility for enclosure changes
4. **Position away from high-speed signals** - Reduce EMI
5. **Verify clearances** - No components within 3mm of holes
6. **Consider stress relief** - Larger pad sizes near mounting
7. **Document pattern** - Make pattern reusable for next design

## Manufacturing Implications

### Hole Placement Cost Factors

| Factor | Impact | Notes |
|--------|--------|-------|
| **Standard pattern** | Baseline cost | 4 corner holes, typical spacing |
| **Extra holes** | +3-5% cost | Drilling is fast, fixed tool cost dominates |
| **Precision tolerance** | No impact | Standard ±0.2mm tolerance included |
| **Hole size** | No impact | All standard sizes (M2-M4) same cost |
| **Panel layout** | +10-20% cost | Complex patterns reduce panelization density |

### Typical Drill Specifications

- **Tool**: Standard twist drill
- **Tolerance**: ±0.2mm (manufacturer standard)
- **Speeds**: 2000-4000 RPM depending on material
- **Cost**: Fixed setup cost, negligible per-hole cost
- **Availability**: All standard sizes immediately available

## Notes

- Mounting holes are typically non-plated thru-holes (NPTHs)
- Standard 100x80mm spacing is widely supported by enclosure manufacturers
- M2 holes (2.5mm) are most common in consumer products
- Mounting points should avoid high-speed signal traces
- Clearance zone around mounting holes prevents electrical issues
- Position precision is critical - use exact measurements from enclosure
