# PCB Bidirectional Test Suite - Product Requirements Document

## Executive Summary

This PRD defines a comprehensive bidirectional test suite for PCB-level operations in circuit-synth, mirroring the successful pattern established for schematic testing in `tests/bidirectional/`. The PCB test suite will validate Python ↔ KiCad PCB synchronization across component placement, routing, layers, design rules, and manufacturing constraints.

**Status**: Planning Phase
**Target**: Full PCB-level bidirectional synchronization validation
**Foundation**: Mirrors `tests/bidirectional/` schematic test architecture
**Timeline**: Phased implementation starting with core placement tests

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
- ⚠️ **NO routing/trace tests**
- ⚠️ **NO layer management tests**

### 1.2 Why PCB Bidirectional Tests Are Critical

**The PCB Problem**: PCB layout is where 80% of design time is spent. Engineers:
1. Generate initial PCB from schematic
2. **Manually place components** (critical for signal integrity, thermal, mechanical)
3. **Route traces** (controlled impedance, differential pairs, power planes)
4. Need to **modify circuit** (add decoupling caps, change footprints)
5. **MUST preserve** manual layout work when regenerating

**Without Bidirectional PCB Tests**:
- ❌ No confidence that manual placement survives Python changes
- ❌ No validation that routing is preserved
- ❌ No verification of layer stack synchronization
- ❌ Risk of destroying hours of PCB layout work
- ❌ Users won't trust tool for real PCB design

**With Comprehensive PCB Tests**:
- ✅ Validates placement preservation (like schematic test 09)
- ✅ Proves routing can survive component additions
- ✅ Verifies design rules transfer between Python and KiCad
- ✅ Enables iterative PCB development workflow
- ✅ Production-ready PCB generation confidence

---

## 2. Goals & Success Criteria

### 2.1 Primary Goals

1. **Mirror schematic test architecture**: Follow proven patterns from `tests/bidirectional/`
2. **Validate placement preservation**: THE killer feature for PCB (like schematic test 09)
3. **Prove routing preservation**: Traces survive component additions/changes
4. **Test component operations**: Add, delete, modify components on PCB
5. **Validate layer management**: Layer stack, zones, copper pours
6. **Verify design rules**: DRC rules, clearances, track widths
7. **Test manufacturing workflow**: Gerber generation, drill files, assembly data

### 2.2 Success Criteria

**Test Suite Completeness**:
- ✅ 25+ PCB-specific bidirectional tests
- ✅ Every test has comprehensive README.md
- ✅ All tests use kicad-pcb-api for validation (Level 2)
- ✅ Position preservation validated for all component operations
- ✅ Routing preservation validated where applicable
- ✅ Design rule synchronization verified

**Test Quality**:
- ✅ Independent execution (each test self-contained)
- ✅ Fixture-based (reproducible starting states)
- ✅ Clear step-by-step workflows with printed output
- ✅ Multi-level validation (structural + electrical)
- ✅ Cleanup in finally blocks
- ✅ `--keep-output` flag support

**Real-World Workflows**:
- ✅ Iterative development (add components without losing layout)
- ✅ Footprint changes (swap SOIC → QFN, preserve routing)
- ✅ Layer management (add/remove layers, update stack)
- ✅ Design rule updates (sync DRC rules from Python)
- ✅ Manufacturing output (Gerbers, drill files, BOM)

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

### 4.1 Phase 1: Core PCB Operations (Tests 01-11)

**Status**: CRITICAL - Must have for basic PCB workflow

**01: Blank PCB Generation**
- **What**: Generate empty PCB with board outline
- **Why**: Foundation test - proves basic PCB creation works
- **Validation**: PCB file exists, has valid structure

**02: Generate PCB from Schematic**
- **What**: Python → KiCad PCB with components
- **Why**: Basic Python → PCB workflow
- **Validation**: Components exist on PCB with footprints

**03: Placement Preservation** ⭐ **THE KILLER FEATURE**
- **What**: Manual component placement survives Python changes
- **Why**: Without this, tool is unusable for real PCB design
- **Validation**: Moved component stays at manual position after regeneration
- **Critical**: This is to PCB what test 09 is to schematics

**04: Add Component to PCB**
- **What**: Add component in Python, appears on existing PCB
- **Why**: Iterative PCB development workflow
- **Validation**: New component exists, old components unchanged

**05: Delete Component from PCB**
- **What**: Remove component from Python, disappears from PCB
- **Why**: Component removal workflow
- **Validation**: Component removed, others preserved

**06: Modify Footprint**
- **What**: Change component footprint (e.g., 0603 → 0805)
- **Why**: Footprint changes during design iteration
- **Validation**: New footprint on PCB, position preserved

**07: Component Rotation**
- **What**: Rotate component 90°/180°/270°
- **Why**: Orientation affects routing and assembly
- **Validation**: Component at correct angle, position preserved

**08: Trace Routing Preservation** ⭐
- **What**: Manual traces survive component additions
- **Why**: Routing takes hours - must be preserved
- **Validation**: Existing traces unchanged after regeneration

**09: Add Trace**
- **What**: Add connection in Python, trace appears on PCB
- **Why**: Programmatic routing capability
- **Validation**: New trace exists with correct coordinates

**10: Delete Trace**
- **What**: Remove connection, trace disappears
- **Why**: Connection removal workflow
- **Validation**: Trace removed, others preserved

**11: Round-Trip PCB**
- **What**: Full cycle: Python → PCB → modify → regenerate
- **Why**: Validates complete bidirectional sync
- **Validation**: All changes preserved through cycle

### 4.2 Phase 2: Layer & Stack Management (Tests 12-18)

**Status**: HIGH PRIORITY - Professional PCB design requirement

**12: Layer Management**
- **What**: Add/remove layers in Python, sync to PCB
- **Why**: Multi-layer boards common in professional design
- **Validation**: Layer stack matches Python definition

**13: Design Rules Sync**
- **What**: Update DRC rules in Python, sync to PCB
- **Why**: Design rules critical for manufacturability
- **Validation**: Clearances, track widths match Python

**14: Via Placement**
- **What**: Add vias in Python, appear on PCB
- **Why**: Layer transitions essential for routing
- **Validation**: Vias at correct positions, sizes, drill

**15: Differential Pair Routing**
- **What**: Define differential pair, enforce spacing
- **Why**: High-speed signals (USB, HDMI, PCIe)
- **Validation**: Pair spacing, matching enforced

**16: Power Plane**
- **What**: Create power plane on internal layer
- **Why**: Low-impedance power distribution
- **Validation**: Plane on correct layer, net assigned

**17: Ground Plane**
- **What**: Create ground plane (copper pour)
- **Why**: Return path, EMI reduction
- **Validation**: Ground plane covers area, clearances

**18: Copper Pour**
- **What**: Create arbitrary copper zone
- **Why**: Thermal relief, shielding
- **Validation**: Zone boundaries, fill settings

### 4.3 Phase 3: Advanced Features (Tests 19-25)

**Status**: MEDIUM PRIORITY - Professional polish

**19: Keepout Zones**
- **What**: Define no-copper/no-component areas
- **Why**: Mechanical clearances, mounting
- **Validation**: Zone boundaries, restrictions

**20: Board Outline**
- **What**: Define custom board shape
- **Why**: Form factor requirements
- **Validation**: Edge.Cuts layer geometry

**21: Mounting Holes**
- **What**: Add mechanical mounting holes
- **Why**: PCB assembly to enclosure
- **Validation**: Holes at correct positions, sizes

**22: Text on Silkscreen**
- **What**: Add text annotations to silkscreen
- **Why**: Assembly instructions, part numbers
- **Validation**: Text content, position, layer

**23: Fiducial Markers**
- **What**: Add fiducials for pick-and-place
- **Why**: Assembly automation registration
- **Validation**: Fiducial positions, sizes

**24: Component Groups**
- **What**: Group related components for placement
- **Why**: Hierarchical placement optimization
- **Validation**: Groups maintained, relative positions

**25: Gerber Generation**
- **What**: Export Gerbers, drill files from Python
- **Why**: Manufacturing output
- **Validation**: Files generated, valid format

### 4.4 Phase 4: Manufacturing Workflow (Tests 26-35)

**Status**: LOWER PRIORITY - Production integration

**26: Pick-and-Place Export**
**27: Assembly Drawing Generation**
**28: BOM with PCB Positions**
**29: Test Point Report**
**30: Panel Layout**
**31: DRC Report Comparison**
**32: Footprint Library Sync**
**33: 3D Model Assignment**
**34: IPC-2581 Export**
**35: ODB++ Export**

---

## 5. Validation Levels

### 5.1 Level 2: kicad-pcb-api (PRIMARY)

All PCB tests use kicad-pcb-api for structural validation:

```python
from kicad_pcb_api import PCBBoard

# Load PCB
pcb = PCBBoard.load(str(pcb_file))

# Validate components
assert len(pcb.footprints) == expected_count
r1 = next(fp for fp in pcb.footprints if fp.reference == "R1")
assert r1.position == expected_position
assert r1.rotation == expected_rotation
assert r1.layer == "F.Cu"

# Validate traces
tracks = [t for t in pcb.tracks if t.net.name == "NET1"]
assert len(tracks) == expected_count
assert tracks[0].start == expected_start
assert tracks[0].end == expected_end
assert tracks[0].width == expected_width

# Validate zones
zones = [z for z in pcb.zones if z.net.name == "GND"]
assert len(zones) > 0
assert zones[0].layer == "B.Cu"

# Validate layers
layers = pcb.layers
assert "F.Cu" in layers
assert "B.Cu" in layers
assert "GND" in layers  # Internal plane

# Validate design rules
rules = pcb.design_rules
assert rules.track_width_min == expected_min
assert rules.clearance_min == expected_clearance
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

### 5.3 Position Preservation Validation

Critical for all placement tests:

```python
# BEFORE: Store original positions
positions_before = {
    fp.reference: (fp.position, fp.rotation)
    for fp in pcb.footprints
}

# MODIFY: Make changes in Python

# REGENERATE: Run Python script again

# AFTER: Load regenerated PCB
pcb_after = PCBBoard.load(str(pcb_file))

# VALIDATE: Manual positions preserved
for ref, (pos_before, rot_before) in positions_before.items():
    fp_after = next(fp for fp in pcb_after.footprints if fp.reference == ref)

    # Position should be EXACTLY preserved
    assert fp_after.position == pos_before, (
        f"{ref} position not preserved!\n"
        f"Before: {pos_before}\n"
        f"After: {fp_after.position}\n"
        f"Manual layout work LOST!"
    )

    # Rotation should be preserved
    assert fp_after.rotation == rot_before, (
        f"{ref} rotation not preserved!"
    )
```

---

## 6. Real-World Workflows

### 6.1 Iterative PCB Development

**Workflow:**
1. Generate initial PCB from Python (components only)
2. Open in KiCad, manually place components for optimal layout
3. Add power connections in Python
4. Regenerate PCB → **component positions preserved**
5. Route traces in KiCad
6. Add decoupling caps in Python
7. Regenerate PCB → **positions AND traces preserved**
8. Continue iterating

**Tests That Validate This:**
- Test 03: Placement Preservation
- Test 04: Add Component to PCB
- Test 08: Trace Routing Preservation
- Test 11: Round-Trip PCB

### 6.2 Footprint Optimization

**Workflow:**
1. Design with 0805 passives initially
2. Layout and route PCB
3. Realize 0603 saves board space
4. Change footprints in Python (0805 → 0603)
5. Regenerate PCB → **positions preserved, routing preserved**
6. Minor routing adjustments in KiCad

**Tests That Validate This:**
- Test 06: Modify Footprint
- Test 03: Placement Preservation
- Test 08: Trace Routing Preservation

### 6.3 Multi-Voltage Design

**Workflow:**
1. Define power planes in Python (VCC, 3V3, 5V, GND)
2. Generate PCB with plane layers
3. Place components for optimal thermal distribution
4. Verify plane connectivity with DRC
5. Add more components to each rail in Python
6. Regenerate → **planes preserved, new components added**

**Tests That Validate This:**
- Test 16: Power Plane
- Test 17: Ground Plane
- Test 04: Add Component to PCB
- Test 12: Layer Management

### 6.4 High-Speed Design

**Workflow:**
1. Define differential pairs in Python (USB D+/D-)
2. Generate PCB with length matching rules
3. Route differential pairs in KiCad
4. Verify impedance with calculator
5. Add termination resistors in Python
6. Regenerate → **routing preserved, terminators added**

**Tests That Validate This:**
- Test 15: Differential Pair Routing
- Test 04: Add Component to PCB
- Test 08: Trace Routing Preservation

### 6.5 Manufacturing Handoff

**Workflow:**
1. Finalize PCB design
2. Add fiducials and mounting holes in Python
3. Generate assembly notes on silkscreen
4. Export Gerbers, drill files, BOM
5. Verify pick-and-place file accuracy
6. Submit to manufacturer

**Tests That Validate This:**
- Test 23: Fiducial Markers
- Test 21: Mounting Holes
- Test 22: Text on Silkscreen
- Test 25: Gerber Generation
- Test 26: Pick-and-Place Export

---

## 7. Implementation Plan

### 7.1 Phase 1: Foundation (Weeks 1-2)

**Milestone**: Core PCB operations validated

**Tests to Implement:**
- ✅ Test 01: Blank PCB Generation
- ✅ Test 02: Generate PCB from Schematic
- ⭐ Test 03: Placement Preservation (THE KILLER FEATURE)
- ✅ Test 04: Add Component to PCB
- ✅ Test 05: Delete Component from PCB

**Deliverables:**
- Test directory structure created
- First 5 tests implemented with README.md
- conftest.py with shared fixtures
- README.md overview document
- All tests passing or XFAIL with issues documented

**Success Criteria:**
- Test 03 proves placement preservation works
- All tests follow established pattern
- kicad-pcb-api validation working

### 7.2 Phase 2: Component Operations (Weeks 3-4)

**Milestone**: Component-level operations complete

**Tests to Implement:**
- Test 06: Modify Footprint
- Test 07: Component Rotation
- Test 08: Trace Routing Preservation ⭐
- Test 09: Add Trace
- Test 10: Delete Trace
- Test 11: Round-Trip PCB

**Deliverables:**
- 6 more tests implemented
- Routing preservation validated
- Round-trip workflow proven
- All tests with comprehensive README.md

**Success Criteria:**
- Test 08 proves routing survives changes
- Test 11 proves full bidirectional sync
- 11 tests total passing

### 7.3 Phase 3: Layers & Design Rules (Weeks 5-6)

**Milestone**: Professional PCB features

**Tests to Implement:**
- Test 12: Layer Management
- Test 13: Design Rules Sync
- Test 14: Via Placement
- Test 15: Differential Pair Routing
- Test 16: Power Plane
- Test 17: Ground Plane
- Test 18: Copper Pour

**Deliverables:**
- 7 advanced tests implemented
- Multi-layer PCB support validated
- Design rule synchronization proven
- 18 tests total

**Success Criteria:**
- Multi-layer boards work correctly
- Design rules sync between Python and KiCad
- Power/ground planes validated

### 7.4 Phase 4: Advanced Features (Weeks 7-8)

**Milestone**: Production-ready PCB workflow

**Tests to Implement:**
- Test 19: Keepout Zones
- Test 20: Board Outline
- Test 21: Mounting Holes
- Test 22: Text on Silkscreen
- Test 23: Fiducial Markers
- Test 24: Component Groups
- Test 25: Gerber Generation

**Deliverables:**
- 7 polish tests implemented
- Manufacturing output validated
- 25 tests total
- Full test suite documentation

**Success Criteria:**
- Gerber generation working
- Assembly data accurate
- Complete PCB workflow validated

### 7.5 Phase 5: Manufacturing Integration (Weeks 9-10)

**Milestone**: Production manufacturing support

**Tests to Implement:**
- Test 26-35: Manufacturing workflow tests
- Pick-and-place, BOM, test points, etc.

**Deliverables:**
- 10 manufacturing tests
- 35 tests total
- Production-ready test suite

**Success Criteria:**
- Manufacturing data export validated
- Full workflow from design to fabrication
- Test suite at production quality

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

- ✅ **25+ PCB tests** implemented and passing
- ✅ **>85% test coverage** for PCB generation code
- ✅ **<5 minutes** full test suite execution time
- ✅ **100% README.md coverage** (every test documented)
- ✅ **0 text-matching tests** (all use kicad-pcb-api)

### 10.2 Qualitative Metrics

- ✅ Engineers trust PCB generation for real projects
- ✅ Manual layout work provably preserved
- ✅ Routing survives component additions
- ✅ Design rules sync correctly
- ✅ Manufacturing output validated
- ✅ Iterative PCB workflow is practical

### 10.3 User Validation

**Before PCB Tests:**
- ❌ "I don't trust circuit-synth for PCB - might lose my layout"
- ❌ "How do I know routing is preserved?"
- ❌ "What about design rules?"
- ❌ "Can't use this for real boards"

**After PCB Tests:**
- ✅ "Test 03 proves placement preservation works"
- ✅ "Test 08 shows routing is preserved"
- ✅ "Test 13 validates design rules sync"
- ✅ "I can use this for production boards"

---

## 11. Appendices

### 11.1 Comparison: Schematic vs PCB Tests

| Aspect | Schematic Tests | PCB Tests |
|--------|----------------|-----------|
| **File Format** | .kicad_sch | .kicad_pcb |
| **Validation API** | kicad-sch-api | kicad-pcb-api |
| **Killer Feature** | Position preservation (Test 09) | Placement preservation (Test 03) |
| **Critical Feature** | Netlist validation (Test 10, 11) | Routing preservation (Test 08) |
| **Test Count** | 33+ tests | 25+ tests (planned) |
| **Hierarchy** | Hierarchical sheets | Layer stackup |
| **Connection** | Nets via labels | Traces/zones |
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
| 2025-10-28 | 1.0 | Claude Code | Initial PRD creation |

---

**End of PRD**
