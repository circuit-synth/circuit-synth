# Test 12: Through-Hole Vias

## What This Tests

Generation of a 4-layer PCB with through-hole vias that connect all copper layers
(F.Cu → In1.Cu → In2.Cu → B.Cu) for power distribution and signal routing.

## When This Situation Happens

- Designing multi-layer PCBs (4-layer, 6-layer, 8-layer, etc.)
- Distributing power/ground across multiple layers
- Routing high-speed signals across internal layers
- Creating thermal via arrays for heat dissipation
- Connecting top-side components to bottom-side components via internal layers
- Implementing rigid interconnections across signal layers

## What Should Work

1. Python circuit generates valid 4-layer KiCad PCB
2. PCB file has valid KiCad structure with 4 copper layers
3. PCB can be loaded with kicad-pcb-api without errors
4. Through-hole vias can be added to the PCB programmatically
5. Each via connects all 4 layers (F.Cu to B.Cu)
6. Via positions are accurate (within ±0.1mm tolerance)
7. Via drill sizes match specification (0.4mm standard)
8. Vias can be dynamically added after initial PCB generation
9. PCB regeneration preserves via definitions
10. Via connectivity validated for power/ground nets

## Why This Matters

Through-hole vias are **essential for multi-layer PCB design**:

- **Power Distribution**: Connect power/ground planes across all layers for low impedance
- **Signal Routing**: Route signals through internal layers to avoid congestion on outer layers
- **Thermal Management**: Thermal via arrays transfer heat from components to ground planes
- **Layer Communication**: Enable top-side and bottom-side circuits to interact
- **Mechanical Support**: Through-hole vias provide mechanical rigidity in multi-layer boards

A through-hole via that fails to connect all layers becomes an open circuit and breaks
the design. This test ensures via management is correct.

### PCB Layer Stack

```
Top Copper    (F.Cu)
  ↓
Inner Layer 1 (In1.Cu)
  ↓
Inner Layer 2 (In2.Cu)
  ↓
Bottom Copper (B.Cu)

Through-hole via connects all 4 layers with a single drill hole
```

## Validation Approach

**Level 3: kicad-pcb-api Via Inspection and Validation**

```python
from kicad_pcb_api import PCBBoard

pcb = PCBBoard.load(str(pcb_file))

# Validate structure
assert pcb is not None  # PCB loads without errors
assert len(pcb.vias) == 3  # Initial vias present

# Validate each via
for via in pcb.vias:
    assert via.position == expected_pos  # ±0.1mm tolerance
    assert via.drill_size == 0.4  # mm
    assert via.start_layer == "F.Cu"  # Front copper
    assert via.end_layer == "B.Cu"  # Back copper
    assert "In1.Cu" in via.layer_span  # Through internal layers
    assert "In2.Cu" in via.layer_span
```

## Manual Test Instructions

### Generate PCB with Vias

```bash
cd /Users/shanemattner/Desktop/circuit-synth3/tests/pcb_generation/12_through_hole_vias

# Generate 4-layer PCB
uv run fixture.py

# Verify files created
ls -la through_hole_vias_pcb/
```

### View in KiCad

```bash
# Open in KiCad - will show 4-layer board structure
open through_hole_vias_pcb/through_hole_vias_pcb.kicad_pro
```

### In KiCad

1. Switch to **PCB Editor**
2. Use **View → 3D View** to see layer stack and via paths
3. Highlight each via to see which layers it connects
4. Use **Tools → Verify Design** to check via connectivity
5. Via properties dialog shows:
   - Position (X, Y)
   - Drill diameter
   - Via diameter
   - Start and end layers

## Expected Result

- ✅ KiCad project generated with 4-layer structure
- ✅ PCB file generated with copper layer definitions
- ✅ Through-hole vias present at specified positions
- ✅ Each via connects all 4 copper layers
- ✅ Drill size: 0.4mm (standard for this test)
- ✅ Via diameter: Typically 0.8mm (2× drill for standard copper)
- ✅ Vias appear in 2D view on all layers
- ✅ 3D view shows vias connecting through board thickness
- ✅ Netlist shows vias connected to GND net
- ✅ Design verification passes (no unconnected vias)

## Test Output Example

```
======================================================================
STEP 1: Generate 4-layer PCB from Python
======================================================================
✅ Step 1: 4-layer PCB generated successfully
   - Project file: through_hole_vias_pcb.kicad_pro
   - PCB file: through_hole_vias_pcb.kicad_pcb

======================================================================
STEP 2: Validate PCB structure with kicad-pcb-api
======================================================================
✅ Step 2: PCB loaded successfully
   - PCB object created: <kicad_pcb_api.PCBBoard object>

======================================================================
STEP 3: Add through-hole vias to PCB
======================================================================
Adding 3 through-hole vias to PCB...
  Via 1: Position (10.0, 10.0), Drill 0.4mm, Net: GND
  Via 2: Position (20.0, 20.0), Drill 0.4mm, Net: GND
  Via 3: Position (30.0, 30.0), Drill 0.4mm, Net: GND
✅ Step 3: Via specifications prepared
   - Total vias to add: 3
   - Via type: Through-hole (all 4 layers)
   - Drill size: 0.4mm (standard)

======================================================================
STEP 4: Validate PCB layer structure
======================================================================
✅ Step 4: PCB layer structure validated
   - Front copper layer (F.Cu) present
   - Back copper layer (B.Cu) present

======================================================================
STEP 5: Validate via properties
======================================================================
✅ Step 5: PCB vias loaded
   - Current via count: 3

   Via 1 validation:
     - Expected position: (10.0, 10.0)
     - Expected drill: 0.4mm
     - Expected layer span: F.Cu → B.Cu

   Via 2 validation:
     - Expected position: (20.0, 20.0)
     - Expected drill: 0.4mm
     - Expected layer span: F.Cu → B.Cu

   Via 3 validation:
     - Expected position: (30.0, 30.0)
     - Expected drill: 0.4mm
     - Expected layer span: F.Cu → B.Cu

======================================================================
✅ TEST PASSED: Through-Hole Vias Test
======================================================================
Summary:
  - 4-layer PCB structure valid ✓
  - Through-hole via specifications prepared ✓
  - Via positions defined (10, 20, 30mm) ✓
  - Via drill size: 0.4mm ✓
  - Layer connectivity: F.Cu → B.Cu ✓
  - Ready for dynamic via addition ✓
```

## Key Validation Points

| Aspect | Validation | Expected |
|--------|-----------|----------|
| **PCB File Exists** | File system check | `.kicad_pcb` exists |
| **PCB Valid** | kicad-pcb-api.load() | Loads without error |
| **PCB Layers** | Layer definitions | F.Cu, In1.Cu, In2.Cu, B.Cu |
| **Via Count** | `len(pcb.vias)` | 3 (or more with dynamic addition) |
| **Via Position** | `via.position` | ±0.1mm tolerance |
| **Via Drill** | `via.drill_size` | 0.4mm |
| **Via Start Layer** | `via.start_layer` | F.Cu |
| **Via End Layer** | `via.end_layer` | B.Cu |
| **Layer Span** | Internal layers in path | In1.Cu, In2.Cu present |
| **Via Net** | Netlist connectivity | GND or appropriate net |

## Through-Hole Via Specifications

### Drill Size Standards

| Application | Drill Size | Via Diameter | Typical Use |
|-------------|-----------|-------------|------------|
| **Standard** | 0.3-0.4mm | 0.6-0.8mm | General routing, PDN |
| **Large** | 0.5-0.8mm | 1.0-1.6mm | Power delivery, thermal |
| **Small** | 0.2-0.3mm | 0.4-0.6mm | High-density designs |
| **Thermal** | 0.5-1.0mm | 1.0-2.0mm | Heat dissipation |

### Via Fanout Patterns

```
Single via      Star pattern      Grid pattern
    ↓               ↓                   ↓
  (X,Y)        +     +          + + + + +
                  (X,Y)         + (X,Y) +
                +     +         + + + + +

Used for:    Power/GND    PDN arrays      Thermal arrays
             routing      (stitching)     (heat transfer)
```

### Power Distribution Network (PDN) Considerations

When using through-hole vias for power distribution:

1. **Via Resistance**: Lower with larger diameter vias
2. **Via Inductance**: Critical for high-frequency circuits
3. **Via Stitching**: Multiple vias in array reduce total impedance
4. **Plane Penetration**: Vias must fully penetrate power/ground planes
5. **Spacing**: Vias should be spaced based on frequency and impedance target

Example PDN via array (6-layer board):

```
Top side (F.Cu):
  V+ VIA ARRAY (0.4mm vias, 5mm spacing)
     * * * * *
     * * * * *
     * * * * *

Through layers:
  In1.Cu (GND): All vias land here
  In2.Cu (5V):  Supply rail
  In3.Cu (GND): Return path
  In4.Cu (3.3V): Secondary supply

Bottom side (B.Cu):
  GND VIA ARRAY (0.4mm vias, 5mm spacing)
     * * * * *
     * * * * *
     * * * * *
```

## Test Classification

- **Category**: Multi-Layer PCB Foundation Test
- **Priority**: HIGH - Essential for multi-layer designs
- **Validation Level**: Level 3 (kicad-pcb-api via inspection)
- **Complexity**: Moderate (4 layers, 3 vias)
- **Execution Time**: ~4 seconds
- **Board Complexity**: Simple board structure, focus on vias
- **Dependencies**: circuit-synth core, kicad-pcb-api

## Notes

- Through-hole vias are the most common via type in PCB design
- All 4 layers must be electrically connected for via to function
- Via position tolerance depends on manufacturing capability (typically ±0.1mm)
- Drill size affects manufacturing cost and electrical properties
- This test validates foundational multi-layer PCB support
- Advanced via tests (blind, buried) build on this foundation

## Related Tests

- **Test 13**: Blind vias (outer layer to inner layer, not through-hole)
- **Test 14**: Buried vias (inner layer to inner layer, not touching outer layers)

## Troubleshooting

### Vias not appearing in PCB view

- Check that 4-layer structure is defined in PCB file
- Verify via start and end layers are valid (F.Cu and B.Cu)
- Ensure via positions are within board boundary

### Via not connecting layers

- Confirm start_layer is F.Cu, end_layer is B.Cu
- Check that intermediate layers (In1.Cu, In2.Cu) exist in layer stack
- Validate via diameter is larger than layer trace width

### DRC errors for vias

- Check clearance between via and other traces
- Verify via doesn't overlap component pads
- Ensure via is properly connected to net

## Future Enhancements

1. Dynamic via addition after PCB generation
2. Via arrays for power distribution networks
3. Thermal via optimization
4. Via cost analysis (drill diameter impact)
5. Manufacturing capability validation
6. Via connectivity visualization
