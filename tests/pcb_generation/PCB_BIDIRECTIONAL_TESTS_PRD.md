# PCB Bidirectional Test Suite - Product Requirements Document

## Executive Summary

This PRD defines a focused bidirectional test suite for PCB-level **component placement operations** in circuit-synth, mirroring the successful pattern established for schematic testing in `tests/bidirectional/`. The PCB test suite will validate Python ↔ KiCad PCB synchronization for component placement, footprint management, and basic board setup.

**Scope**: Component placement, vias, footprint assignment, board outline, manufacturing output
**Out of Scope**: Complex trace routing, autorouting, trace preservation (future)
**Status**: Planning Phase
**Target**: Component placement + via management + manufacturing workflow validation
**Foundation**: Mirrors `tests/bidirectional/` schematic test architecture
**Timeline**: Focused implementation (18 comprehensive tests covering placement + vias + manufacturing)

---

## 1. Background & Motivation

### 1.1 Current State

**Schematic Testing (Complete)**: The `tests/bidirectional/` directory contains 33+ comprehensive tests validating:
- ✅ Component CRUD operations (add, delete, modify)
- ✅ Net creation and modification
- ✅ Position preservation (THE KILLER FEATURE)
- ✅ Power symbol handling
- ✅ Hierarchical sheets
- ✅ Round-trip synchronization
- ✅ UUID-based component matching

**PCB Testing (Minimal)**: Currently only basic PCB generation exists:
- ✅ Blank PCB generation (`tests/integration/test_blank_pcb_generation.py`)
- ✅ PCB Generator API (`src/circuit_synth/kicad/pcb_gen/pcb_generator.py`)
- ⚠️ **NO bidirectional tests** (Python ↔ KiCad PCB sync)
- ⚠️ **NO placement preservation tests**
- ⚠️ **NO component add/delete/modify tests**

**Explicit Non-Goals (Current Scope)**:
- ❌ Manual trace routing preservation (future feature)
- ❌ Autorouting algorithms
- ❌ Complex impedance-controlled routing
- ❌ Length-matched differential pairs (routing level)

Circuit-synth focuses on **intelligent component placement** and lets users route in KiCad.

### 1.2 Why PCB Bidirectional Tests Are Critical

**The PCB Problem**: Component placement is the first critical step in PCB design. Engineers:
1. Generate initial PCB from schematic
2. **Manually place components** (critical for signal integrity, thermal, mechanical)
3. **Route traces in KiCad** (manual routing, not automated by circuit-synth)
4. Need to **modify circuit** (add decoupling caps, change footprints)
5. **MUST preserve** manual component placement when regenerating
6. **Accept re-routing** after component changes (routing is manual anyway)

**Circuit-Synth's Focus**: Intelligent component placement, not routing
- ✅ Generate PCB with components in smart initial positions
- ✅ Preserve manual placement adjustments when circuit changes
- ✅ Handle component add/delete/modify operations
- ✅ Let users route traces in KiCad (the right tool for manual routing)
- ❌ NOT trying to preserve manual routing (future feature, low priority)

**Without Bidirectional PCB Tests**:
- ❌ No confidence that manual placement survives Python changes
- ❌ Risk of destroying hours of component placement work
- ❌ No validation of footprint changes
- ❌ Users won't trust tool for iterative PCB development

**With Focused PCB Tests**:
- ✅ Validates placement preservation (like schematic test 09)
- ✅ Proves component operations work bidirectionally
- ✅ Enables iterative PCB development workflow
- ✅ Users route in KiCad, regenerate when circuit changes
- ✅ Clear scope: placement, not routing

---

## 2. Goals & Success Criteria

### 2.1 Primary Goals

1. **Mirror schematic test architecture**: Follow proven patterns from `tests/bidirectional/`
2. **Validate placement preservation**: THE killer feature for PCB (like schematic test 09)
3. **Test component operations**: Add, delete, modify components on PCB
4. **Verify footprint management**: Footprint changes, assignment, library sync
5. **Validate board setup**: Board outline, mounting holes, basic mechanical
6. **Test manufacturing workflow**: Gerber generation, pick-and-place, BOM

**Explicit Non-Goals (Current Scope)**:
- ❌ Routing preservation (users route in KiCad, accept re-routing)
- ❌ Trace/via operations (future feature)
- ❌ Complex layer management (focus on 2-layer for now)
- ❌ Autorouting algorithms (not circuit-synth's focus)

### 2.2 Success Criteria

**Test Suite Completeness**:
- ✅ **18 comprehensive PCB tests** (no duplication, all critical operations covered)
- ✅ Every test has comprehensive README.md
- ✅ All tests use kicad-pcb-api for validation (Level 2)
- ✅ **Position preservation validated** for all component operations
- ✅ **Via placement validated** for all via types (through-hole, blind, buried)
- ✅ **Component layer assignment validated** (F.Cu vs B.Cu)
- ✅ Footprint changes validated
- ✅ Component add/delete/modify operations proven
- ✅ Manufacturing output validated

**Test Quality**:
- ✅ Independent execution (each test self-contained)
- ✅ Fixture-based (reproducible starting states)
- ✅ Clear step-by-step workflows with printed output
- ✅ Structural validation (kicad-pcb-api)
- ✅ Cleanup in finally blocks
- ✅ `--keep-output` flag support

**Real-World Workflows**:
- ✅ Iterative development (add components without losing placement)
- ✅ Footprint changes (swap SOIC → QFN, preserve other placements)
- ✅ Component operations (add decoupling caps, remove test points)
- ✅ **Via placement** (power/ground connections, layer transitions)
- ✅ Multi-layer board support (via blind/buried vias)
- ✅ Board outline and mechanical features
- ✅ Manufacturing output (Gerbers, pick-and-place, BOM)

**Accepted Limitations (Not Failures)**:
- ⚠️ Manual trace routing not automated (users route in KiCad)
- ⚠️ No trace preservation tests (future feature)
- ⚠️ Simple orthogonal traces only (complex routing in KiCad)

---

## 3. Architecture & Design

### 3.1 Test Directory Structure

Mirror `tests/bidirectional/` pattern:

```
tests/bidirectional_pcb/
├── README.md                           # Overview, philosophy, usage
├── PCB_BIDIRECTIONAL_TESTS_PRD.md     # This document
├── TEST_AUTOMATION_PLAN.md            # Implementation roadmap
├── conftest.py                        # pytest fixtures
│
├── 01_blank_pcb/
│   ├── README.md                      # What, why, how, expected
│   ├── blank_pcb.py                   # Python fixture
│   └── test_01_blank_pcb.py           # Automated test
│
├── 02_generate_pcb_from_schematic/
│   ├── README.md
│   ├── single_resistor.py
│   └── test_02_generate_pcb.py
│
├── 03_placement_preservation/         # THE KILLER FEATURE for PCB
│   ├── README.md                      # Detailed explanation
│   ├── two_resistors.py
│   └── test_03_placement_preservation.py
│
├── 04_add_component_to_pcb/
├── 05_delete_component_from_pcb/
├── 06_modify_footprint/
├── 07_component_rotation/
├── 08_trace_routing_preservation/
├── 09_add_trace/
├── 10_delete_trace/
├── 11_zone_creation/
├── 12_layer_management/
├── 13_design_rules_sync/
├── 14_via_placement/
├── 15_differential_pair_routing/
├── 16_power_plane/
├── 17_ground_plane/
├── 18_copper_pour/
├── 19_keepout_zones/
├── 20_board_outline/
├── 21_mounting_holes/
├── 22_text_on_silkscreen/
├── 23_fiducial_markers/
├── 24_component_groups/
└── 25_gerber_generation/
```

### 3.2 Test Pattern (Following Schematic Tests)

Every PCB test follows this pattern:

```python
#!/usr/bin/env python3
"""
Automated test for XX_feature_name PCB bidirectional test.

Tests [SPECIFIC PCB CAPABILITY] when [SCENARIO].

This validates that you can:
1. [Step 1]
2. [Step 2]
3. [Step 3 - what should be preserved]

This is critical because [REAL-WORLD IMPACT].

Workflow:
1. Generate initial PCB from Python
2. Validate initial state (Level 2: kicad-pcb-api)
3. Make change (Python OR KiCad PCB)
4. Regenerate
5. Validate:
   - Change reflected in PCB
   - Manual placements preserved
   - Routing preserved (if applicable)
   - Design rules intact

Validation uses:
- kicad-pcb-api for PCB structure validation
- Position comparison for placement preservation
- Net connectivity for routing validation
- Design rule extraction for DRC verification
"""

import shutil
import subprocess
from pathlib import Path
import pytest


def test_XX_feature_name(request):
    """Test [feature] in [direction] → syncs correctly.

    THE KILLER FEATURE FOR PCB:
    Validates that [manual work] is preserved when [change happens].

    Workflow:
    1. Setup paths
    2. Generate initial PCB
    3. Validate initial state
    4. Manually modify PCB (move component/add trace)
    5. Make Python change
    6. Regenerate PCB
    7. Validate manual work preserved

    Why critical:
    - Without this, [hours of work] lost every regeneration
    - Tool becomes unusable for real PCB design
    - This is THE feature that makes PCB workflow viable

    Level 2 PCB Validation:
    - kicad-pcb-api for structural validation
    - Position comparison for placement
    - Net connectivity for routing
    """

    # Setup paths
    test_dir = Path(__file__).parent
    python_file = test_dir / "fixture.py"
    output_dir = test_dir / "output"
    pcb_file = output_dir / "output.kicad_pcb"

    # Check for --keep-output flag
    cleanup = not request.config.getoption("--keep-output", default=False)

    # Clean existing output
    if output_dir.exists():
        shutil.rmtree(output_dir)

    # Read original fixture
    with open(python_file, "r") as f:
        original_code = f.read()

    try:
        # =====================================================================
        # STEP 1: Generate initial PCB
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 1: Generate initial PCB from Python")
        print("="*70)

        result = subprocess.run(
            ["uv", "run", "fixture.py"],
            cwd=test_dir,
            capture_output=True,
            text=True,
            timeout=30
        )

        assert result.returncode == 0, (
            f"Step 1 failed: Initial generation\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )

        assert pcb_file.exists(), "PCB file not created"

        # =====================================================================
        # STEP 2: Validate initial state using kicad-pcb-api
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 2: Validate initial PCB structure")
        print("="*70)

        from kicad_pcb_api import PCBBoard
        pcb = PCBBoard.load(str(pcb_file))

        # Validate components exist
        assert len(pcb.footprints) == 2, f"Expected 2 footprints, found {len(pcb.footprints)}"

        # Find components
        r1 = next((fp for fp in pcb.footprints if fp.reference == "R1"), None)
        r2 = next((fp for fp in pcb.footprints if fp.reference == "R2"), None)

        assert r1 is not None, "R1 not found"
        assert r2 is not None, "R2 not found"

        # Store initial positions
        r1_initial_pos = r1.position
        r2_initial_pos = r2.position

        print(f"✅ Step 2: Initial PCB validated")
        print(f"   - R1 at: {r1_initial_pos}")
        print(f"   - R2 at: {r2_initial_pos}")

        # =====================================================================
        # STEP 3: Manually move R1 (simulating manual layout)
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 3: Manually move R1 to (50, 30)")
        print("="*70)

        r1.position = (50.0, 30.0)
        pcb.save(str(pcb_file))

        # Verify move
        pcb_moved = PCBBoard.load(str(pcb_file))
        r1_moved = next(fp for fp in pcb_moved.footprints if fp.reference == "R1")

        assert r1_moved.position == (50.0, 30.0), "R1 move failed"

        print(f"✅ Step 3: R1 manually moved to (50, 30)")

        # =====================================================================
        # STEP 4: Add R3 in Python
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 4: Add R3 to Python code")
        print("="*70)

        # Modify Python code to add R3
        modified_code = original_code.replace(
            "# ADD R3 HERE",
            '''
    r3 = Component(
        symbol="Device:R",
        ref="R3",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )'''
        )

        with open(python_file, "w") as f:
            f.write(modified_code)

        print(f"✅ Step 4: R3 added to Python")

        # =====================================================================
        # STEP 5: Regenerate PCB
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 5: Regenerate PCB with R3")
        print("="*70)

        result = subprocess.run(
            ["uv", "run", "fixture.py"],
            cwd=test_dir,
            capture_output=True,
            text=True,
            timeout=30
        )

        assert result.returncode == 0, (
            f"Step 5 failed: Regeneration\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )

        # =====================================================================
        # STEP 6: Validate R1 position preserved (THE KILLER FEATURE)
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 6: Validate placement preservation")
        print("="*70)

        pcb_final = PCBBoard.load(str(pcb_file))

        assert len(pcb_final.footprints) == 3, f"Expected 3 footprints"

        r1_final = next(fp for fp in pcb_final.footprints if fp.reference == "R1")
        r2_final = next(fp for fp in pcb_final.footprints if fp.reference == "R2")
        r3_final = next(fp for fp in pcb_final.footprints if fp.reference == "R3")

        # CRITICAL VALIDATION: R1 manual position preserved
        assert r1_final.position == (50.0, 30.0), (
            f"❌ POSITION NOT PRESERVED! R1 should stay at (50, 30)\n"
            f"   But R1 moved back to {r1_final.position}\n"
            f"   This means manual PCB layout work is lost!\n"
            f"   THE KILLER FEATURE IS BROKEN!"
        )

        # R2 position should be preserved (unchanged)
        assert r2_final.position == r2_initial_pos, (
            f"R2 position should be preserved"
        )

        # R3 should be auto-placed
        assert r3_final is not None, "R3 should exist"

        print(f"✅ Step 6: Placement preservation VERIFIED!")
        print(f"   - R1 preserved at: {r1_final.position} ✓")
        print(f"   - R2 preserved at: {r2_final.position} ✓")
        print(f"   - R3 auto-placed at: {r3_final.position} ✓")
        print(f"\n🎉 THE KILLER FEATURE WORKS FOR PCB!")
        print(f"   Manual PCB layout work is NOT lost!")

    finally:
        # Restore original fixture
        with open(python_file, "w") as f:
            f.write(original_code)

        # Cleanup
        if cleanup and output_dir.exists():
            shutil.rmtree(output_dir)
```

### 3.3 Validation Strategy

**Level 1: Text Matching (NOT USED)**
- Avoid text matching - too brittle for PCB files

**Level 2: kicad-pcb-api Validation (PRIMARY)**
- Structural validation using kicad-pcb-api
- Component positions, rotations, layers
- Trace coordinates, widths, layers
- Zone definitions, copper pours
- Design rules, clearances
- Board outline

**Level 3: PCB Export Validation (SECONDARY)**
- Gerber file generation
- Drill file validation
- BOM/assembly data
- DRC report comparison
- IPC-2581/ODB++ exports

**Level 4: Manufacturing Data (ADVANCED)**
- Pick-and-place files
- Assembly drawings
- Test point reports
- Panel layouts

---

## 4. Test Categories & Priority

### 4.1 Phase 1: Core Placement Operations (Tests 01-07)

**Status**: CRITICAL - Must have for basic PCB workflow

**01: Blank PCB Generation**
- **What**: Generate empty PCB with board outline
- **Why**: Foundation test - proves basic PCB creation works
- **Validation**: PCB file exists, has valid structure
- **Scope**: No components, just board outline

**02: Placement Preservation** ⭐ **THE KILLER FEATURE**
- **What**: Manual component placement survives Python changes
- **Why**: Without this, tool is unusable for real PCB design
- **Validation**: Moved component stays at manual position after regeneration
- **Critical**: This is to PCB what test 09 is to schematics
- **Scope**: Only placement, NOT routing (routing expected to be redone)
- **Note**: Schematic → PCB generation is KiCad's job, we test regeneration preservation

**03: Add Component to PCB**
- **What**: Add component in Python, appears on existing PCB with smart auto-placement
- **Why**: Iterative PCB development workflow (e.g., add decoupling caps)
- **Validation**: New component exists, old placements preserved, no collisions, intelligent placement
- **Scope**: Placement + collision avoidance + auto-placement algorithm
- **Auto-Placement Validation**:
  - New component not placed at (0, 0) or invalid position
  - No overlap with existing components (collision detection works)
  - Reasonable proximity to related components (smart placement)
  - Within board boundaries

**04: Delete Component from PCB**
- **What**: Remove component from Python, disappears from PCB
- **Why**: Component removal workflow (e.g., remove test points)
- **Validation**: Component removed, others preserved
- **Scope**: Placement only, connected traces become unconnected (expected)

**05: Modify All Component Fields** ⭐ **CANONICAL UPDATE TEST**
- **What**: Update ALL component properties: footprint, value, description, MPN, DNP, tolerance, custom fields
- **Why**: Tests canonical update - all fields sync correctly from Python to PCB
- **Validation**: Every field updated correctly, position preserved, no field leakage
- **Scope**: Complete component metadata synchronization
- **Critical**: Ensures Python is authoritative source for ALL component data
- **Fields Tested**:
  - Reference (R1, C1, etc.)
  - Value (10k, 100nF, etc.)
  - Footprint (library:name) - **position MUST be preserved when footprint changes**
  - Description (component description text)
  - Manufacturer Part Number (MPN)
  - Do Not Place (DNP flag)
  - Tolerance (±5%, ±10%, etc.)
  - Custom properties (test_point, voltage_rating, etc.)
- **Position Preservation Validation**:
  - When footprint changes (e.g., 0805 → 0603), component stays at same XY position
  - Critical workflow: optimize footprint sizes without losing placement work
  - Validates that field updates don't trigger position reset

**06: Component Rotation**
- **What**: Rotate component 90°/180°/270° in Python
- **Why**: Orientation affects placement density and assembly
- **Validation**: Component at correct angle, position preserved
- **Scope**: Rotation + placement

**07: Round-Trip Regeneration**
- **What**: Full cycle: Python → PCB → move component → modify Python → regenerate
- **Why**: Validates complete regeneration with preservation workflow
- **Validation**: Manual placement changes preserved through cycle
- **Scope**: Regeneration workflow, not testing routing preservation

### 4.2 Phase 2: Board & Footprint Management (Tests 08-11)

**Status**: HIGH PRIORITY - Professional PCB workflow support

**08: Component Layer Assignment** ⭐ **CRITICAL MISSING TEST**
- **What**: Place components on top layer (F.Cu) vs bottom layer (B.Cu)
- **Why**: Essential for double-sided boards, affects assembly cost and design density
- **Validation**: Component on correct layer, position preserved when changing layers
- **Scope**: Layer assignment, double-sided placement
- **Critical**: Fundamental placement operation for professional PCB design
- **Use Cases**:
  - SMD components on both sides for dense layouts
  - Through-hole components (always both layers)
  - Cost optimization (single-side vs double-side assembly)

**09: Board Outline Definition**
- **What**: Define custom board shape in Python
- **Why**: Form factor requirements (rectangular, rounded corners, custom)
- **Validation**: Edge.Cuts layer geometry matches Python
- **Scope**: Board mechanical outline, not placement constraints

**10: Mounting Holes**
- **What**: Add mechanical mounting holes in Python
- **Why**: PCB assembly to enclosure
- **Validation**: Holes at correct positions, sizes, plating
- **Scope**: Mechanical features, not electrical

**11: Footprint Library Sync**
- **What**: Change footprint library (e.g., update to newer library version)
- **Why**: Library updates, custom footprint libraries
- **Validation**: Components use correct library footprints
- **Scope**: Footprint assignment, placement preserved
- **Note**: Different from Test 05 - this tests library switching, Test 05 tests field modification

### 4.3 Phase 3: Via Management (Tests 12-14)

**Status**: HIGH PRIORITY - Essential for multi-layer boards

**12: Through-Hole Vias**
- **What**: Add through-hole vias in Python (connects all layers)
- **Why**: Most common via type, essential for layer transitions
- **Validation**: Via position, drill size, pad size, connects all layers
- **Scope**: Via placement and properties, not routing (yet)
- **Use Case**: Power/ground connections, signal layer transitions

**13: Blind Vias**
- **What**: Add blind vias in Python (outer layer to inner layer)
- **Why**: Advanced PCB designs, space-constrained layouts
- **Validation**: Via position, start/end layers, drill size
- **Scope**: Via placement, layer span validation
- **Use Case**: High-density interconnect (HDI) boards

**14: Buried Vias**
- **What**: Add buried vias in Python (inner layer to inner layer)
- **Why**: Advanced multi-layer boards (4+ layers)
- **Validation**: Via position, start/end layers (not touching outer layers)
- **Scope**: Via placement, layer-to-layer connections
- **Use Case**: Complex 6-8 layer boards with internal routing

### 4.4 Phase 4: Board Features (Tests 15-16)

**Status**: MEDIUM PRIORITY - Professional board features

**15: Silkscreen Features**
- **What**: Add text annotations, graphics, and logos to silkscreen in Python
- **Why**: Assembly instructions, branding, part numbers, polarity marks, version info
- **Validation**: Text content, graphic elements, correct layers (F.Silkscreen/B.Silkscreen)
- **Scope**: Silkscreen annotation and artwork (text + graphics combined)
- **Features Tested**:
  - Text annotations (part numbers, assembly notes)
  - Graphic elements (logos, polarity marks)
  - Layer assignment (top/bottom silkscreen)
  - Position and orientation

**16: Fiducial Markers**
- **What**: Add fiducials for pick-and-place in Python
- **Why**: Assembly automation registration points
- **Validation**: Fiducial positions, sizes, copper clearance
- **Scope**: Assembly features, treated as special components

### 4.5 Phase 5: Manufacturing Output (Tests 17-18)

**Status**: MEDIUM PRIORITY - Production integration

**17: Gerber & Drill Export**
- **What**: Export Gerbers, drill files from Python
- **Why**: Manufacturing handoff - verify output is valid
- **Validation**: Files generated, valid format, all layers present
- **Scope**: Export validation, not DRC

**18: Pick-and-Place Export**
- **What**: Export pick-and-place (PnP) file from Python with complete BOM data
- **Why**: Assembly automation requires component positions + BOM (MPN, value, DNP)
- **Validation**: All components listed, positions accurate, rotation correct, BOM fields present
- **Scope**: Complete assembly data export (positions + BOM combined)
- **Note**: PnP files include all BOM data (reference, value, footprint, MPN, DNP) plus XY positions - no separate BOM test needed

### 4.6 Future Enhancements (Not Current Scope)

**Status**: FUTURE - Not in initial test suite

These features may be added in future iterations:

**Routing Features** (Future):
- **Trace drawing in Python** - Simple point-to-point traces
- **Trace preservation** when adding components
- **Orthogonal routing** - 90° angle traces
- Differential pair routing support
- Autorouting integration

**Advanced Via Features** (Future):
- **Micro-vias** (laser-drilled, HDI)
- **Via-in-pad** configurations
- **Stacked vias** (multiple blind vias)
- Via stitching for planes

**Advanced Layer Management** (Future):
- Power/ground plane zones
- Copper pours with thermal relief
- Complex layer stackup rules
- Impedance control layers

**Advanced Manufacturing** (Future):
- Panel layout generation
- IPC-2581/ODB++ export
- 3D model assignment
- Assembly drawing generation
- Test point reports

**Current Focus**: Component placement, vias, basic board features, manufacturing output

---

## 5. Validation Levels

### 5.1 Level 2: kicad-pcb-api (PRIMARY)

All PCB tests use kicad-pcb-api for structural validation, **focused on placement**:

```python
from kicad_pcb_api import PCBBoard

# Load PCB
pcb = PCBBoard.load(str(pcb_file))

# Validate components (CORE TEST)
assert len(pcb.footprints) == expected_count
r1 = next(fp for fp in pcb.footprints if fp.reference == "R1")
assert r1.position == expected_position  # THE KILLER FEATURE
assert r1.rotation == expected_rotation
assert r1.layer == "F.Cu"

# Validate footprint assignment
assert r1.footprint == "Resistor_SMD:R_0603_1608Metric"

# Validate component properties
assert r1.properties.get("DNP") == expected_dnp
assert r1.properties.get("MPN") == expected_mpn

# Validate board outline
outline_segments = pcb.board_outline
assert len(outline_segments) > 0

# Validate mechanical features
mounting_holes = [fp for fp in pcb.footprints if fp.is_mounting_hole]
assert len(mounting_holes) == expected_hole_count

# NOTE: We do NOT validate traces/vias/zones in placement tests
# Users route manually in KiCad after component placement
```

### 5.2 Level 3: Gerber Validation (SECONDARY)

For manufacturing tests:

```python
import subprocess

# Generate Gerbers
result = subprocess.run([
    "kicad-cli", "pcb", "export", "gerbers",
    str(pcb_file),
    "--output", str(gerber_dir)
], capture_output=True, text=True)

assert result.returncode == 0

# Validate Gerber files exist
expected_gerbers = [
    "project-F_Cu.gbr",
    "project-B_Cu.gbr",
    "project-F_Mask.gbr",
    "project-B_Mask.gbr",
    "project-Edge_Cuts.gbr",
    "project.drl",  # Drill file
]

for gerber in expected_gerbers:
    gerber_file = gerber_dir / gerber
    assert gerber_file.exists()
    assert gerber_file.stat().st_size > 0

# Parse Gerber content (basic validation)
with open(gerber_dir / "project-F_Cu.gbr") as f:
    content = f.read()
    assert "G04 #@! TF.FileFunction,Copper,L1,Top*" in content
```

### 5.3 Position Preservation Validation (CRITICAL)

**THE KILLER FEATURE** - validated in every placement test:

```python
# BEFORE: Store original positions
positions_before = {
    fp.reference: (fp.position, fp.rotation)
    for fp in pcb.footprints
}

# MODIFY: Make changes in Python (add R3, change footprint, etc.)

# REGENERATE: Run Python script again

# AFTER: Load regenerated PCB
pcb_after = PCBBoard.load(str(pcb_file))

# VALIDATE: Manual positions preserved (THE KILLER FEATURE)
for ref, (pos_before, rot_before) in positions_before.items():
    fp_after = next(fp for fp in pcb_after.footprints if fp.reference == ref)

    # Position should be EXACTLY preserved
    assert fp_after.position == pos_before, (
        f"{ref} position not preserved!\n"
        f"Before: {pos_before}\n"
        f"After: {fp_after.position}\n"
        f"Manual PLACEMENT work LOST!"
    )

    # Rotation should be preserved
    assert fp_after.rotation == rot_before, (
        f"{ref} rotation not preserved!"
    )

# NOTE: We do NOT check traces/vias
# Users route in KiCad after placement, accept re-routing when components change
```

---

## 6. Real-World Workflows

### 6.1 Iterative PCB Development (Realistic Workflow)

**Workflow:**
1. Generate initial PCB from Python (components with auto-placement)
2. Open in KiCad, **manually place components** for optimal layout
3. **Route traces in KiCad** (manual routing - circuit-synth doesn't route)
4. Realize need to add decoupling caps in Python
5. Add caps in Python, regenerate PCB → **component positions preserved** ✅
6. **Re-route new connections in KiCad** (expected - new components need routing)
7. Change R1 footprint from 0805 to 0603 in Python
8. Regenerate PCB → **placements preserved**, R1 has new footprint ✅
9. **Adjust routing in KiCad** for smaller footprint (expected)
10. Continue iterating (placement preserved, routing adjusted as needed)

**Reality**: Users accept re-routing when components change. Placement preservation is critical, routing preservation is nice-to-have (future).

**Tests That Validate This:**
- Test 03: Placement Preservation (THE CRITICAL ONE)
- Test 04: Add Component to PCB
- Test 06: Modify Footprint
- Test 08: Round-Trip Placement

### 6.2 Footprint Optimization (Realistic Workflow)

**Workflow:**
1. Design with 0805 passives initially
2. Place components and route PCB in KiCad
3. Realize 0603 saves board space
4. Change footprints in Python (0805 → 0603)
5. Regenerate PCB → **positions preserved** ✅, routing lost (expected)
6. **Re-route in KiCad** (smaller footprints, may need rework anyway)

**Reality**: Footprint changes often require routing adjustments anyway. Key is preserving positions so users don't have to re-place everything.

**Tests That Validate This:**
- Test 06: Modify Footprint (position preserved, new footprint correct)
- Test 03: Placement Preservation

### 6.3 Decoupling Cap Workflow (Common Pattern)

**Workflow:**
1. Generate initial PCB with main components (MCU, regulators)
2. Place components in KiCad for optimal layout
3. Route power and signal traces in KiCad
4. Realize need more decoupling caps near MCU power pins
5. Add 4 decoupling caps in Python (0.1uF, 1uF, etc.)
6. Regenerate → **existing placements preserved**, new caps auto-placed near MCU ✅
7. **Adjust cap positions** in KiCad (fine-tune near power pins)
8. **Route cap connections** in KiCad (short, wide traces to minimize inductance)
9. Continue development

**Reality**: Adding components is common (decoupling, test points, debug headers). Placement preservation is key.

**Tests That Validate This:**
- Test 04: Add Component to PCB
- Test 03: Placement Preservation
- Test 12: Component Properties (DNP for test points)

### 6.4 Design Iteration Workflow

**Workflow:**
1. Generate PCB with initial components
2. Place and route in KiCad
3. Design review reveals need for test points
4. Add test point components in Python
5. Regenerate → **existing placements preserved**, test points auto-placed ✅
6. **Move test points** to accessible locations in KiCad
7. **Route test point connections** in KiCad (minimal routing needed)
8. Assembly review suggests moving connector
9. **Move connector** in KiCad (manual adjustment)
10. **Re-route affected traces** in KiCad (expected)
11. Regenerate for new schematic change → **connector position preserved** ✅

**Reality**: Design iteration involves placement adjustments and re-routing. Tool preserves manual placement work, users accept re-routing.

**Tests That Validate This:**
- Test 03: Placement Preservation (manual moves preserved)
- Test 04: Add Component to PCB (test points, debug headers)
- Test 08: Round-Trip Placement (full cycle)

### 6.5 Manufacturing Handoff (Realistic)

**Workflow:**
1. Finalize PCB design (placement and routing complete in KiCad)
2. Add fiducials and mounting holes in Python
3. Regenerate → **component placements preserved**, fiducials added ✅
4. Add assembly notes on silkscreen in Python
5. Regenerate → **all positions preserved**, silkscreen text added ✅
6. Export Gerbers, drill files, pick-and-place from Python
7. Verify pick-and-place file has correct positions
8. Verify BOM matches actual components
9. Submit to manufacturer

**Reality**: Manufacturing data generated from finalized PCB. Placement must be correct.

**Tests That Validate This:**
- Test 14: Fiducial Markers
- Test 10: Mounting Holes
- Test 13: Text on Silkscreen
- Test 15: Gerber & Manufacturing Export
- Test 12: Component Properties (DNP, MPN for BOM)

---

## 7. Implementation Plan

### 7.1 Phase 1: Foundation (Weeks 1-2)

**Milestone**: Core placement operations validated

**Tests to Implement:**
- Test 01: Blank PCB Generation
- ⭐ **Test 02: Placement Preservation** (THE KILLER FEATURE - highest priority)
- Test 03: Add Component to PCB (with collision avoidance)
- Test 04: Delete Component from PCB

**Deliverables:**
- Test directory structure created (`tests/pcb_generation/`)
- First 4 tests implemented with comprehensive README.md
- conftest.py with shared fixtures
- README.md overview document
- All tests passing or XFAIL with issues documented

**Success Criteria:**
- ✅ **Test 02 proves placement preservation works** (critical milestone)
- ✅ Test 03 proves collision avoidance when adding components
- ✅ All tests follow established patterns
- ✅ kicad-pcb-api validation working
- ✅ Position comparison logic reliable

**Note**: Removed "Generate PCB from Schematic" test - KiCad already does this, we test regeneration

### 7.2 Phase 2: Component Operations (Weeks 3-4)

**Milestone**: Component manipulation complete

**Tests to Implement:**
- ⭐ **Test 05: Modify All Component Fields** (CANONICAL UPDATE TEST)
- Test 06: Component Rotation
- Test 07: Round-Trip Regeneration

**Deliverables:**
- 3 more tests implemented (7 tests total)
- Canonical update validated (all component fields sync correctly)
- Component rotation verified
- Round-trip regeneration workflow proven
- All tests with comprehensive README.md

**Success Criteria:**
- ✅ **Test 05 proves ALL component fields update correctly** (critical for data integrity)
- ✅ Test 06 validates rotation + placement
- ✅ Test 07 proves full regeneration with preservation workflow
- ✅ 7 core placement tests passing

### 7.3 Phase 3: Board & Mechanical (Weeks 5-6)

**Milestone**: Board setup and mechanical features

**Tests to Implement:**
- Test 09: Board Outline Definition
- Test 10: Mounting Holes
- Test 11: Footprint Library Sync
- Test 12: Component Properties (DNP, MPN)

**Deliverables:**
- 4 board/mechanical tests implemented (12 tests total)
- Board outline validation working
- Mounting hole placement verified
- Component property sync proven
- Comprehensive test suite documentation

**Success Criteria:**
- ✅ Custom board shapes work
- ✅ Mounting holes positioned correctly
- ✅ Footprint library changes sync
- ✅ Component metadata preserved

### 7.4 Phase 4: Via Management (Weeks 7-8)

**Milestone**: Multi-layer board support via vias

**Tests to Implement:**
- Test 13: Through-Hole Vias
- Test 14: Blind Vias
- Test 15: Buried Vias

**Deliverables:**
- 3 via tests implemented (14 tests completed so far)
- Through-hole via placement validated
- Blind via layer transitions verified
- Buried via internal connections proven
- Multi-layer board capability demonstrated

**Success Criteria:**
- ✅ Through-hole vias connect all layers
- ✅ Blind vias start/end on correct layers
- ✅ Buried vias stay internal (not on outer layers)
- ✅ Via positions preserved when components added
- ✅ **Multi-layer board workflow validated**

### 7.5 Phase 5: Board Features (Weeks 7-8)

**Milestone**: Professional board finishing

**Tests to Implement:**
- Test 15: Silkscreen Features (text + graphics combined)
- Test 16: Fiducial Markers

**Deliverables:**
- 2 board feature tests (16 tests completed so far)
- Silkscreen text placement validated
- Silkscreen graphics (logos, polarity marks) validated
- Fiducial positioning verified

**Success Criteria:**
- ✅ Silkscreen text + graphics positioned correctly on correct layers
- ✅ Fiducials placed for assembly automation
- ✅ All board features preserved during regeneration

### 7.6 Phase 6: Manufacturing Output (Weeks 9-10)

**Milestone**: Production-ready manufacturing data

**Tests to Implement:**
- Test 17: Gerber & Drill Export
- Test 18: Pick-and-Place Export (includes BOM data)

**Deliverables:**
- 2 manufacturing tests (**18 tests total - COMPLETE**)
- Gerber/drill file generation validated
- Pick-and-place data accuracy verified (includes BOM: MPN, value, DNP)
- **Complete PCB workflow production-ready**

**Success Criteria:**
- ✅ Gerber files for all layers generated correctly
- ✅ Drill files include all vias and holes
- ✅ Pick-and-place file has accurate positions/rotations + complete BOM data
- ✅ All manufacturing data validated for production use
- ✅ **Full manufacturing data package validated**

### 7.7 Future Phases (TBD - Not Current Scope)

**Milestone**: Advanced features when needed

**Potential Future Tests:**
- **Basic trace drawing** (simple Python-defined point-to-point traces)
- **Orthogonal routing** (90° angle auto-routing from via to pad)
- Trace preservation when adding components
- Copper pour/zone tests
- Advanced DRC rule synchronization
- Panel layout generation
- 3D model assignment
- Via-in-pad configurations
- Micro-via support

**Scope Decision**: These are not priority for initial test suite. Add as features are implemented in circuit-synth.

**Timeline**: No estimate - driven by feature development, not test development

---

## 8. Technical Requirements

### 8.1 Dependencies

**Required:**
- `kicad-pcb-api`: Primary validation library
- `pytest`: Test framework
- `circuit-synth`: Core library

**Optional:**
- `gerbonara`: Gerber file parsing (Phase 4)
- `pcbdl`: PCB design validation (future)

### 8.2 Test Infrastructure

**Fixtures (conftest.py):**
```python
import pytest
from pathlib import Path

@pytest.fixture
def test_output_dir(tmp_path):
    """Provide temporary directory for test output"""
    return tmp_path / "test_output"

@pytest.fixture
def cleanup_flag(request):
    """Check if --keep-output flag is set"""
    return not request.config.getoption("--keep-output", default=False)

def pytest_addoption(parser):
    """Add --keep-output flag"""
    parser.addoption(
        "--keep-output",
        action="store_true",
        default=False,
        help="Keep test output files for inspection"
    )
```

**Helper Functions:**
```python
def load_pcb(pcb_file):
    """Load PCB with error handling"""
    from kicad_pcb_api import PCBBoard
    return PCBBoard.load(str(pcb_file))

def compare_positions(pos1, pos2, tolerance=0.01):
    """Compare positions with tolerance"""
    return (abs(pos1[0] - pos2[0]) < tolerance and
            abs(pos1[1] - pos2[1]) < tolerance)

def validate_footprint_count(pcb, expected_count):
    """Validate footprint count with clear error"""
    actual = len(pcb.footprints)
    assert actual == expected_count, (
        f"Expected {expected_count} footprints, found {actual}\n"
        f"Footprints: {[fp.reference for fp in pcb.footprints]}"
    )
```

### 8.3 CI/CD Integration

**pytest.ini:**
```ini
[pytest]
testpaths = tests/bidirectional_pcb
python_files = test_*.py
python_functions = test_*
markers =
    pcb: PCB-level bidirectional tests
    placement: Placement preservation tests
    routing: Routing preservation tests
    manufacturing: Manufacturing output tests
addopts = -v --tb=short
```

**GitHub Actions:**
```yaml
- name: Run PCB Bidirectional Tests
  run: |
    cd tests/bidirectional_pcb
    pytest -v --tb=short
    pytest -v --tb=short -m placement  # Critical tests
```

---

## 9. Risk Analysis

### 9.1 Technical Risks

**Risk**: kicad-pcb-api incomplete or buggy
**Mitigation**: Contribute fixes upstream, implement workarounds
**Likelihood**: Medium
**Impact**: High

**Risk**: PCB file format changes in KiCad updates
**Mitigation**: Version pinning, format parsing abstraction
**Likelihood**: Low
**Impact**: Medium

**Risk**: Position preservation complex to implement
**Mitigation**: Learn from schematic test 09 success
**Likelihood**: Low
**Impact**: Critical

**Risk**: Routing preservation extremely difficult
**Mitigation**: Start with simple cases, iterate
**Likelihood**: High
**Impact**: High

### 9.2 Project Risks

**Risk**: Test suite too large to maintain
**Mitigation**: Follow proven schematic pattern
**Likelihood**: Low
**Impact**: Medium

**Risk**: Tests take too long to run
**Mitigation**: Parallel execution, skip flags
**Likelihood**: Medium
**Impact**: Low

**Risk**: Users don't trust PCB generation without tests
**Mitigation**: Comprehensive test suite addresses this
**Likelihood**: High (current state)
**Impact**: Critical

---

## 10. Success Metrics

### 10.1 Quantitative Metrics

- ✅ **18 comprehensive PCB tests** implemented and passing (no duplication)
  - 11 placement/component tests (01-11) - includes layer assignment, canonical update
  - 3 via tests (12-14) - through-hole, blind, buried
  - 2 board feature tests (15-16) - silkscreen (combined), fiducials
  - 2 manufacturing tests (17-18) - Gerbers, PnP/BOM (combined)
- ✅ **>85% test coverage** for PCB generation code
- ✅ **<5 minutes** full test suite execution time
- ✅ **100% README.md coverage** (every test documented)
- ✅ **0 text-matching tests** (all use kicad-pcb-api)
- ✅ **Test 02 (placement preservation) passing** - THE critical milestone
- ✅ **Test 05 (canonical update) passing** - ALL fields sync correctly
- ✅ **Via tests passing** - Essential for multi-layer boards

### 10.2 Qualitative Metrics

- ✅ Engineers trust PCB generation for real projects
- ✅ **Manual placement work provably preserved** (THE key metric)
- ✅ Component operations (add/delete/modify) validated
- ✅ Footprint changes preserve positions
- ✅ **Via placement works for multi-layer boards** (through-hole, blind, buried)
- ✅ Board features (silkscreen, fiducials) properly positioned
- ✅ Manufacturing output validated and accurate
- ✅ **Iterative PCB workflow is practical**
- ⚠️ Basic trace drawing capability (future: simple Python-defined traces)
- ⚠️ Users do complex routing in KiCad (documented expectation)

### 10.3 User Validation

**Before PCB Tests:**
- ❌ "I don't trust circuit-synth for PCB - might lose my placement work"
- ❌ "How do I know my component positions are preserved?"
- ❌ "What if component properties don't sync correctly?"
- ❌ "What about multi-layer boards with vias?"
- ❌ "What if I need to add components later?"
- ❌ "Can't use this for real boards"

**After PCB Tests:**
- ✅ "Test 02 proves placement preservation works"
- ✅ "Test 03 shows collision avoidance + smart auto-placement when adding components"
- ✅ "Test 05 proves ALL component fields sync correctly (canonical update)"
- ✅ "Test 08 shows component layer assignment works (F.Cu vs B.Cu)"
- ✅ "Tests 12-14 show vias work for multi-layer boards"
- ✅ "Tests 17-18 show manufacturing data is accurate"
- ✅ "I can use this for production boards"
- ✅ "Clear expectations: circuit-synth for placement/vias, KiCad for complex routing"

---

## 11. Appendices

### 11.1 Comparison: Schematic vs PCB Tests

| Aspect | Schematic Tests | PCB Tests |
|--------|----------------|-----------|
| **File Format** | .kicad_sch | .kicad_pcb |
| **Validation API** | kicad-sch-api | kicad-pcb-api |
| **Killer Feature** | Position preservation (Test 09) | Placement preservation (Test 02) |
| **Primary Focus** | Netlist/connectivity | Component placement |
| **Test Count** | 33+ tests | 18 tests (no duplication, all critical ops) |
| **Scope** | Components, nets, hierarchy | Placement, footprints, board setup |
| **Out of Scope** | N/A | Routing (users do in KiCad) |
| **Validation Levels** | Level 2 (kicad-sch-api), Level 3 (netlist) | Level 2 (kicad-pcb-api), Level 3 (Gerber) |

### 11.2 Glossary

- **PCB**: Printed Circuit Board
- **Footprint**: Physical component package on PCB
- **Trace**: Copper connection between components
- **Via**: Hole connecting traces on different layers
- **Zone**: Copper fill area (planes, pours)
- **DRC**: Design Rule Check
- **Gerber**: Manufacturing file format
- **Pick-and-place**: Assembly machine instruction file
- **Fiducial**: Reference marker for assembly automation
- **Differential Pair**: Matched-length signal pairs

### 11.3 References

- Schematic Bidirectional Tests: `tests/bidirectional/`
- PCB Generator: `src/circuit_synth/kicad/pcb_gen/pcb_generator.py`
- kicad-pcb-api: https://github.com/electronics-synth/kicad-pcb-api
- KiCad File Format: https://dev-docs.kicad.org/en/file-formats/

---

## 12. Document History

| Date | Version | Author | Changes |
|------|---------|--------|---------|
| 2025-10-28 | 1.0 | Claude Code | Initial PRD creation (20 tests) |
| 2025-10-28 | 1.1 | Claude Code | Reduced to 18 tests: Added Test 08 (layer assignment), removed Test 12 (duplicate), combined Tests 16+18→15 (silkscreen), combined Tests 20+21→18 (PnP/BOM), enhanced Tests 03 & 05 |

---

**End of PRD**
