# Test 14: Buried Vias

## What This Tests

Generation of a 6-layer PCB with buried vias that connect only inner layers
(In1.Cu ↔ In3.Cu, In2.Cu ↔ In4.Cu) without any connection to the outer layers
(F.Cu or B.Cu).

## When This Situation Happens

- Designing ultra-high-density PCBs (6, 8, 10, 12+ layers)
- Advanced HDI boards with complex internal routing
- High-performance computing servers and routers
- RF/microwave PCBs with multiple controlled impedance layers
- Designs where outer layers are reserved for components/signals
- Internal power distribution networks with multiple planes
- Sequential build-up (SBU) manufacturing processes

## What Should Work

1. Python circuit generates valid 6-layer KiCad PCB
2. PCB file has valid KiCad structure with 6 copper layers
3. PCB can be loaded with kicad-pcb-api without errors
4. Buried vias can be added to the PCB programmatically
5. Buried vias connect ONLY inner layers (never outer)
6. Buried vias can span multiple inner layers (e.g., In1.Cu to In3.Cu)
7. Buried vias can connect adjacent inner layers (e.g., In1.Cu to In2.Cu)
8. Via positions are accurate (within ±0.1mm tolerance)
9. Via drill sizes match specification (0.3mm standard for buried)
10. Multiple buried vias can coexist in the same PCB
11. Vias can be dynamically added after initial PCB generation
12. PCB regeneration preserves buried via definitions

## Why This Matters

Buried vias are **essential for ultra-high-density and advanced PCB designs**:

- **Complete Isolation**: Outer layers untouched, allowing independent routing
- **Maximum Density**: Inner layers can be used for routing without outer layer impact
- **Sophisticated Topology**: Complex power delivery and signal networks internally
- **Outer Layer Freedom**: F.Cu and B.Cu reserved for components and critical signals
- **Manufacturing Complexity**: Most complex via type, highest cost
- **Advanced Applications**: Required for modern processors, networking, 5G equipment

### Via Type Comparison

```
Through-Hole Via    Blind Via           Buried Via
(Test 12)           (Test 13)           (Test 14)

F.Cu ----●          F.Cu ----●          F.Cu
  ↓      |            ↓      |            ↓
In1.Cu   |          In1.Cu   |          In1.Cu ----●
  ↓      |            ↓                    ↓      |
In2.Cu   |          In2.Cu               In2.Cu   |
  ↓      |            ↓                    ↓
In3.Cu   |          In3.Cu               In3.Cu   |
  ↓      |            ↓                    ↓
B.Cu ----●          B.Cu                B.Cu

Complexity: Simple  Medium              High
Cost:       Low     Medium              High
Density:    Standard Medium             Maximum
Outer Layer Both    Single              None
Connection:
```

### PCB Layer Stack (6-Layer Example)

```
F.Cu        (Front copper - OUTER) ← NOT accessed by buried vias
  ↓
In1.Cu      (Inner layer 1) ← Buried via can START/END here
  ↓
In2.Cu      (Inner layer 2) ← Buried via can START/END here
  ↓
In3.Cu      (Inner layer 3) ← Buried via can START/END here
  ↓
In4.Cu      (Inner layer 4) ← Buried via can START/END here
  ↓
B.Cu        (Back copper - OUTER) ← NOT accessed by buried vias

Buried vias connect: Inner ↔ Inner (never touching outer layers)
```

## Validation Approach

**Level 4: kicad-pcb-api Buried Via Complete Isolation Validation**

```python
from kicad_pcb_api import PCBBoard

pcb = PCBBoard.load(str(pcb_file))

# Validate structure
assert pcb is not None
assert len(pcb.vias) >= 2  # At least 2 buried vias

# Validate each via is truly buried (inner-only)
for via in pcb.vias:
    # CRITICAL: Neither start nor end can be outer layer
    assert via.start_layer not in ["F.Cu", "B.Cu"], "Via must not START at outer layer"
    assert via.end_layer not in ["F.Cu", "B.Cu"], "Via must not END at outer layer"

    # Verify both are inner layers
    assert via.start_layer in ["In1.Cu", "In2.Cu", "In3.Cu", "In4.Cu"]
    assert via.end_layer in ["In1.Cu", "In2.Cu", "In3.Cu", "In4.Cu"]

    # Verify position is within board
    assert via.position[0] >= 0 and via.position[0] <= 100
    assert via.position[1] >= 0 and via.position[1] <= 80
```

## Manual Test Instructions

### Generate PCB with Buried Vias

```bash
cd /Users/shanemattner/Desktop/circuit-synth3/tests/pcb_generation/14_buried_vias

# Generate 6-layer PCB
uv run fixture.py

# Verify files created
ls -la buried_vias_pcb/
```

### View in KiCad

```bash
# Open in KiCad - will show 6-layer board with buried vias
open buried_vias_pcb/buried_vias_pcb.kicad_pro
```

### In KiCad

1. Switch to **PCB Editor**
2. Use **View → 3D View** to see buried via path (completely internal)
3. Select a buried via to verify:
   - Position matches specification
   - Drill diameter is small (0.3mm)
   - Start and end layers are BOTH inner layers
   - Does NOT show F.Cu or B.Cu in layer span
4. Key difference from blind vias:
   - Blind: One outer + one inner
   - Buried: Two inner (completely internal)

## Expected Result

- ✅ KiCad project generated with 6-layer structure
- ✅ PCB file generated with copper layer definitions
- ✅ Buried vias present at specified positions
- ✅ Buried Via 1 connects In1.Cu to In3.Cu only
- ✅ Buried Via 2 connects In2.Cu to In4.Cu only
- ✅ Neither buried via touches F.Cu or B.Cu
- ✅ Drill size: 0.3mm (standard for buried)
- ✅ Via diameter: 0.6mm (smaller than through-hole)
- ✅ Buried vias NOT visible on outer layer views
- ✅ 3D view shows vias completely inside board
- ✅ Netlist shows vias connected to internal signals
- ✅ Design verification validates outer layer isolation

## Test Output Example

```
======================================================================
STEP 1: Generate 6-layer PCB from Python
======================================================================
✅ Step 1: 6-layer PCB generated successfully
   - Project file: buried_vias_pcb.kicad_pro
   - PCB file: buried_vias_pcb.kicad_pcb

======================================================================
STEP 2: Validate PCB structure with kicad-pcb-api
======================================================================
✅ Step 2: PCB loaded successfully
   - PCB object created: <kicad_pcb_api.PCBBoard object>

======================================================================
STEP 3: Add buried vias to PCB
======================================================================
Adding 2 buried vias to PCB...

  Buried Via 1: Inner Via 1
    - Position: (20.0, 30.0)
    - Drill: 0.3mm
    - Layer span: In1.Cu → In3.Cu
    - Restriction: Must NOT reach F.Cu or B.Cu
    - Net: INT_SIG1

  Buried Via 2: Inner Via 2
    - Position: (40.0, 50.0)
    - Drill: 0.3mm
    - Layer span: In2.Cu → In4.Cu
    - Restriction: Must NOT reach F.Cu or B.Cu
    - Net: INT_SIG2

✅ Step 3: Buried via specifications prepared
   - Total buried vias to add: 2
   - Via type: Buried (inner-to-inner only)
   - Drill size: 0.3mm (typical for buried vias)
   - Outer layer isolation: CRITICAL

======================================================================
STEP 4: Validate buried via layer restrictions
======================================================================
Buried Via Layer Restrictions (6-Layer Board):

  Board Layer Stack:
    F.Cu   (Front copper - OUTER)
    In1.Cu (Inner layer 1)
    In2.Cu (Inner layer 2)
    In3.Cu (Inner layer 3)
    In4.Cu (Inner layer 4)
    B.Cu   (Back copper - OUTER)

  Buried Via 1 (In1.Cu → In3.Cu):
    ✗ NOT F.Cu (outer top) - CRITICAL
    ✓ Start: In1.Cu (inner) - OK
    ✓ Passes through: In2.Cu (intermediate)
    ✓ End: In3.Cu (inner) - OK
    ✗ NOT B.Cu (outer bottom) - CRITICAL

  Buried Via 2 (In2.Cu → In4.Cu):
    ✗ NOT F.Cu (outer top) - CRITICAL
    ✓ Start: In2.Cu (inner) - OK
    ✓ Passes through: In3.Cu (intermediate)
    ✓ End: In4.Cu (inner) - OK
    ✗ NOT B.Cu (outer bottom) - CRITICAL

✅ Step 4: Layer restriction validation prepared
   - Via 1 isolated from outer layers (F.Cu, B.Cu)
   - Via 2 isolated from outer layers (F.Cu, B.Cu)
   - Both vias completely internal

======================================================================
STEP 5: Validate buried via properties
======================================================================
✅ Step 5: PCB vias loaded
   - Current via count: 2

   Buried Via 1 validation:
     - Expected position: (20.0, 30.0)
     - Expected drill: 0.3mm
     - Layer span: In1.Cu → In3.Cu
     - Restriction: Must NOT reach F.Cu or B.Cu

   Buried Via 2 validation:
     - Expected position: (40.0, 50.0)
     - Expected drill: 0.3mm
     - Layer span: In2.Cu → In4.Cu
     - Restriction: Must NOT reach F.Cu or B.Cu

======================================================================
STEP 6: Test dynamic buried via addition
======================================================================
Adding new buried via dynamically:
  - Name: Inner Via 3 (Added Dynamically)
  - Position: (25.0, 35.0)
  - Layer span: In1.Cu → In2.Cu
  - Type: Adjacent inner layers

✅ Step 6: Dynamic buried via addition validated
   - New via specification: In1.Cu → In2.Cu
   - Layer restrictions: Maintained (inner-to-inner only)
   - Position: Within design area

======================================================================
✅ TEST PASSED: Buried Vias Test
======================================================================
Summary:
  - 6-layer PCB structure valid ✓
  - Buried via specifications prepared ✓
  - Buried Via 1: In1.Cu → In3.Cu ✓
  - Buried Via 2: In2.Cu → In4.Cu ✓
  - Outer layer isolation enforced ✓
  - Via drill size: 0.3mm (buried standard) ✓
  - Dynamic via addition supported ✓
  - Complex multi-layer topologies enabled ✓
  - Ready for advanced HDI designs ✓
```

## Key Validation Points

| Aspect | Validation | Expected |
|--------|-----------|----------|
| **PCB File Exists** | File system check | `.kicad_pcb` exists |
| **PCB Valid** | kicad-pcb-api.load() | Loads without error |
| **Layer Count** | 6 copper layers | F.Cu, In1-4.Cu, B.Cu |
| **Via Count** | `len(pcb.vias)` | 2 or more |
| **Buried Via 1** | Layer restriction | In1.Cu → In3.Cu |
| **Buried Via 2** | Layer restriction | In2.Cu → In4.Cu |
| **Via Start Layer** | `via.start_layer` | Inner only (In1-4.Cu) |
| **Via End Layer** | `via.end_layer` | Inner only (In1-4.Cu) |
| **CRITICAL: No F.Cu** | NOT outer | `via.start/end_layer ≠ F.Cu` |
| **CRITICAL: No B.Cu** | NOT outer | `via.start/end_layer ≠ B.Cu` |
| **Via Position** | `via.position` | ±0.1mm tolerance |
| **Via Drill** | `via.drill_size` | 0.3mm |

## Buried Via Specifications

### Drill Size Standards

| Application | Drill Size | Via Diameter | Layer Count |
|-------------|-----------|-------------|------------|
| **Buried in 4-6 layer** | 0.3mm | 0.6mm | Adjacent layers |
| **Buried in 8-layer** | 0.25mm | 0.5mm | Multiple span |
| **Buried SBU** | 0.2mm | 0.4mm | Sequential build-up |

### Buried Via Patterns in 6-Layer Board

```
Example 1: Adjacent Inner Vias

  F.Cu ━━━━━━━━━━━━━━━━━━━━
  In1.Cu ────● ───────────  (Via A: In1→In2)
  In2.Cu ────●●─ ──────────  (Shared intermediate)
  In3.Cu ─────● ──────────  (Via A end)
  In4.Cu ──────────────────
  B.Cu ━━━━━━━━━━━━━━━━━━━━


Example 2: Spanning Inner Vias (Test 14)

  F.Cu ━━━━━━━━━━━━━━━━━━━━
  In1.Cu ────● ───────────  (Via 1 start)
  In2.Cu ──────●──────────  (Via 1 passes through)
  In3.Cu ────● ───────────  (Via 1 end)
  In4.Cu ────────● ───────  (Via 2 end)
  In3.Cu ────────●───────  (Via 2 passes through)
  In2.Cu ────────● ───────  (Via 2 start)
  B.Cu ━━━━━━━━━━━━━━━━━━━━
```

### Manufacturing Capability Requirements

**Buried Vias require:**
- Sequential lamination process
- Specialized drilling (inner layer vias drilled before final lamination)
- Expensive manufacturing capability
- Limited to specialized PCB manufacturers
- Only used when absolutely necessary for routing

**Cost Impact**: Buried vias can increase PCB cost by 20-50% vs. through-hole designs

## Via Type Selection Guide

| Design Requirement | Via Type | Reason |
|---|---|---|
| Simple 2-layer board | Through-hole | Standard, lowest cost |
| 4-layer with space | Through-hole | Adequate routing space |
| 4-layer HDI (BGA) | Blind | Top side components need routing |
| 6-layer with complexity | Mix of Blind + Through | Outer + inner routing |
| 6-layer ultra-dense | Buried + Blind + Through | Maximum density |
| 8+ layers | Buried + Blind | Internal routing required |
| Advanced server PCB | Multiple Buried layers | Complex power/signal networks |

## Test Classification

- **Category**: Ultra-High-Density PCB Advanced Test
- **Priority**: MEDIUM - Essential for 6+ layer designs
- **Validation Level**: Level 4 (kicad-pcb-api buried via isolation validation)
- **Complexity**: High (6 layers, multiple inner layer vias, isolation requirements)
- **Execution Time**: ~4 seconds
- **Board Complexity**: Complex layer stack, focus on inner-layer isolation
- **Dependencies**: circuit-synth core, kicad-pcb-api with buried via support

## Notes

- Buried vias are the most complex and expensive via type
- Manufacturing requirement: PCB must support buried/sequential vias
- Outer layer isolation is critical (if touched, becomes blind or through-hole)
- Buried vias cannot stack (vias cannot overlap)
- Only use when routing requirements cannot be met with through-hole/blind vias
- Position tolerance depends on manufacturing capability (±0.1mm typical)
- This test validates foundational buried via support for advanced designs

## Related Tests

- **Test 12**: Through-hole vias (basic multi-layer)
- **Test 13**: Blind vias (outer to inner, HDI)

## Troubleshooting

### Buried via appears as through-hole

- Check that neither start nor end layer is F.Cu or B.Cu
- Verify both layers are inner layers (In1.Cu, In2.Cu, In3.Cu, In4.Cu)
- If touching either outer layer, it's no longer a buried via

### Outer layer connection (CRITICAL ERROR)

- Buried vias MUST NOT connect to F.Cu (front copper)
- Buried vias MUST NOT connect to B.Cu (back copper)
- If either outer layer is involved, update layer specification
- This is a design error that breaks the buried via concept

### Manufacturer cannot produce

- Verify PCB manufacturer supports buried vias
- Check cost implications (may be 2-3× through-hole cost)
- Consider using blind vias instead if possible
- Evaluate mixed via approach (buried + blind + through)

## Future Enhancements

1. Mixed via designs (buried + blind + through)
2. Sequential build-up (SBU) multi-level buried vias
3. Via array optimization for power planes
4. Buried via manufacturing capability validation
5. Cost analysis for different via types
6. Advanced layer stack design
7. Via routing constraint checking
