# Orthogonal Routing - Implementation Guide

**Branch:** `feature/orthogonal-routing`
**Date:** 2025-10-19

## Codebase Exploration Summary

### Key Files Identified

#### 1. Entry Point: Circuit API
**File:** `src/circuit_synth/core/circuit.py`
**Method:** `Circuit.generate_kicad_project()` (lines 615-757)

```python
def generate_kicad_project(
    self,
    project_name: str,
    generate_pcb: bool = True,
    placement_algorithm: str = "connection_centric",
    # ... existing params
)
```

**Action Required:**
- Add `routing_style` parameter
- Add `via_size` parameter
- Pass these to PCB generation

#### 2. PCB Generation
**File:** `src/circuit_synth/kicad/pcb_gen/pcb_generator.py`
**Method:** `PCBGenerator.generate_pcb()` (lines 150-433)

```python
def generate_pcb(
    self,
    # ... existing params
    auto_route: bool = False,
    routing_passes: int = 4,
    routing_effort: float = 1.0,
    generate_ratsnest: bool = True,
)
```

**Action Required:**
- Add `routing_style` and `via_size` parameters
- Pass to DSN exporter
- Update KiCad project file with design rules

#### 3. Freerouting DSN Export
**File:** `src/circuit_synth/pcb/routing/dsn_exporter.py`
**Class:** `DSNExporter`

**Key Methods:**
- `__init__()` (line 83): Initialize with PCB board
- `_extract_layers()` (lines 173-192): Define layer routing directions
- `_generate_dsn()` (lines 442-548): Generate complete DSN file
- `_add_padstack_definitions()` (lines 550-611): Define via types

**Current Layer Definition (lines 176-179):**
```python
self.layers = [
    DSNLayer("front", "signal", "horizontal"),
    DSNLayer("back", "signal", "vertical"),
]
```

**Current Design Rules (lines 485-490):**
```python
lines.append("    (rule")
lines.append(f"      (width {self.DEFAULT_TRACK_WIDTH})")
lines.append(f"      (clearance {self.DEFAULT_CLEARANCE})")
lines.append("      (clearance 0.1 (type smd_to_turn_gap))")
lines.append("      (clearance 0.2 (type default_smd))")
lines.append("    )")
```

**Current Via Definition (lines 476-482):**
```python
lines.append("    (via")
lines.append(
    f'      "Via[0-{len(self.layers)-1}]_'
    f'{self.DEFAULT_VIA_SIZE}:{self.DEFAULT_VIA_DRILL}_um"'
)
lines.append("    )")
```

**Action Required:**
- Accept routing_style and via_size in `__init__()`
- Modify `_extract_layers()` to set all layers to "orthogonal" when routing_style="orthogonal"
- Update via size constants when via_size specified
- Add blind/buried via support to DSN

#### 4. KiCad Project File Template
**File:** `src/circuit_synth/kicad/sch_gen/kicad_blank_project/kicad_blank_project.kicad_pro`

**Relevant Section (lines 34-60):**
```json
"net_settings": {
  "classes": [
    {
      "name": "Default",
      "track_width": 0.2,
      "via_diameter": 0.6,
      "via_drill": 0.3,
      "clearance": 0.2
    }
  ]
}
```

**Action Required:**
- Update via_diameter and via_drill when via_size specified
- Add design rules for orthogonal routing (if KiCad supports it in .kicad_pro)

## Implementation Plan

### Step 1: Update Circuit API
**File:** `src/circuit_synth/core/circuit.py`

```python
def generate_kicad_project(
    self,
    project_name: str,
    generate_pcb: bool = True,
    force_regenerate: bool = False,
    placement_algorithm: str = "connection_centric",
    draw_bounding_boxes: bool = False,
    generate_ratsnest: bool = True,
    update_source_refs: Optional[bool] = None,
    routing_style: Optional[str] = None,  # NEW: "orthogonal" or None
    via_size: Optional[str] = None,        # NEW: "drill/annular" e.g. "0.6/0.3"
) -> None:
```

- Parse `via_size` if provided (split on "/")
- Pass `routing_style` and `via_size` to SchematicGenerator
- Set default via_size="0.6/0.3" when routing_style="orthogonal"

### Step 2: Update PCB Generator
**File:** `src/circuit_synth/kicad/pcb_gen/pcb_generator.py`

```python
def generate_pcb(
    self,
    # ... existing params
    routing_style: Optional[str] = None,
    via_size: Optional[str] = None,
) -> bool:
```

- Store routing config
- Pass to DSN exporter when creating exporter instance
- Update project file with via sizes

### Step 3: Update DSN Exporter
**File:** `src/circuit_synth/pcb/routing/dsn_exporter.py`

```python
class DSNExporter:
    def __init__(
        self,
        pcb_board: PCBBoard,
        routing_style: Optional[str] = None,
        via_size: Optional[str] = None
    ):
        self.board = pcb_board
        self.routing_style = routing_style

        # Parse via size
        if via_size:
            drill, annular = via_size.split("/")
            self.DEFAULT_VIA_DRILL = float(drill)
            # Calculate via size from drill + annular
            annular_ring = float(annular)
            self.DEFAULT_VIA_SIZE = self.DEFAULT_VIA_DRILL + 2 * annular_ring
        elif routing_style == "orthogonal":
            # Default for orthogonal routing
            self.DEFAULT_VIA_DRILL = 0.6
            self.DEFAULT_VIA_SIZE = 1.2  # 0.6 + 2*0.3
```

**Modify `_extract_layers()` method:**
```python
def _extract_layers(self) -> None:
    """Extract layer information from the PCB."""
    if self.routing_style == "orthogonal":
        # All layers orthogonal for orthogonal routing + blind/buried vias
        direction = "orthogonal"  # Tell Freerouting to only use 90° angles
    else:
        direction = None  # Default behavior (horizontal/vertical alternating)

    self.layers = [
        DSNLayer("front", "signal", direction or "horizontal"),
        DSNLayer("back", "signal", direction or "vertical"),
    ]

    # Handle inner layers...
```

**Modify DSN generation to include blind/buried via support:**
- Add via type definitions for blind and buried vias when routing_style="orthogonal"
- Update structure section with blind/buried via rules

### Step 4: Update Project File Template (Optional)
**File:** Update the generation code that uses the template

```python
# When generating project file, update via sizes
if via_size or routing_style == "orthogonal":
    # Parse via size
    drill, annular = (via_size or "0.6/0.3").split("/")
    via_diameter = float(drill) + 2 * float(annular)
    via_drill = float(drill)

    # Update net_settings in project JSON
    project_data["net_settings"]["classes"][0]["via_diameter"] = via_diameter
    project_data["net_settings"]["classes"][0]["via_drill"] = via_drill
```

## DSN Format for Orthogonal Routing

### Layer Definition with Orthogonal Direction
```lisp
(structure
  (layer front (type signal) (direction orthogonal))
  (layer back (type signal) (direction orthogonal))
  (layer inner1 (type signal) (direction orthogonal))
  (layer inner2 (type signal) (direction orthogonal))
  ...
)
```

### Blind/Buried Via Support
```lisp
(structure
  ; Standard through via
  (via "Via[0-3]_1200:600_um")

  ; Blind via (e.g., layer 0 to layer 1)
  (via "Via[0-1]_1200:600_um" (type blind))

  ; Buried via (e.g., layer 1 to layer 2)
  (via "Via[1-2]_1200:600_um" (type buried))

  (rule
    (width 0.25)
    (clearance 0.2)
  )
)
```

## Testing Strategy

### Test Case 1: Simple Circuit with Orthogonal Routing
```python
from circuit_synth import Circuit, Component

@circuit
def test_orthogonal(circuit: Circuit):
    '''Simple test circuit for orthogonal routing'''
    # Create a simple circuit
    r1 = Component("Device:R", ref="R1", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
    r2 = Component("Device:R", ref="R2", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
    # ... add a few more components

if __name__ == "__main__":
    test_circuit = test_orthogonal()

    # Generate with orthogonal routing
    test_circuit.generate_kicad_project(
        "test_orthogonal",
        routing_style="orthogonal",
        via_size="0.6/0.3"
    )
```

### Verification Steps
1. Check generated DSN file has `(direction orthogonal)` for all layers
2. Check via sizes in DSN match `0.6/0.3` (1.2mm diameter, 0.6mm drill)
3. Check .kicad_pro file has correct via sizes
4. Open in KiCad and verify blind/buried vias are enabled
5. Run Freerouting and verify routes are orthogonal (90° only)

## Files to Modify (Summary)

1. `src/circuit_synth/core/circuit.py` - Add params to `generate_kicad_project()`
2. `src/circuit_synth/kicad/sch_gen/main_generator.py` - Pass params through
3. `src/circuit_synth/kicad/pcb_gen/pcb_generator.py` - Accept and use params
4. `src/circuit_synth/pcb/routing/dsn_exporter.py` - Implement orthogonal logic
5. Project file generation code - Update via sizes

## Next Steps

1. Implement changes in order (Circuit API → PCB Generator → DSN Exporter)
2. Test with simple circuit
3. Verify DSN output manually
4. Test Freerouting with generated DSN
5. Document usage in README
