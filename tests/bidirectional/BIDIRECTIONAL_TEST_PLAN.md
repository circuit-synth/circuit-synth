# Bidirectional Synchronization Test Plan

**Date:** 2025-11-01
**Status:** Active Planning
**Purpose:** Complete guide for bidirectional sync test coverage and implementation

---

## Table of Contents

1. [Core Principles](#core-principles)
2. [Current State Analysis](#current-state-analysis)
3. [Test Matrix: CRUD Coverage](#test-matrix-crud-coverage)
4. [Verification Patterns](#verification-patterns)
5. [Test Fixtures](#test-fixtures)
6. [Implementation Phases](#implementation-phases)
7. [Migration Plan](#migration-plan)

---

## Core Principles

### 1. Preservation is Key

**Every CRUD operation must preserve all other schematic elements.**

When we:
- **Add** a component → All existing components, labels, power symbols, wires preserved
- **Update** a component → All other components unchanged, positions/rotations preserved
- **Delete** a component → Only that component removed, everything else preserved

**Verification Method:** Use `kicad-sch-api` to enumerate ALL schematic objects and verify exactly the expected set exists (no more, no less).

### 2. Parallel Coverage: Root and Hierarchical

**Every CRUD operation tested at BOTH hierarchy levels.**

| Operation | Root Sheet | Child Sheet | Notes |
|-----------|------------|-------------|-------|
| Add Component | ✅ Test | ✅ Test | Same verification pattern |
| Update Component | ✅ Test | ✅ Test | Same verification pattern |
| Delete Component | ✅ Test | ✅ Test | Same verification pattern |
| Add Net | ✅ Test | ✅ Test | Same verification pattern |
| Update Net | ✅ Test | ✅ Test | Same verification pattern |
| Delete Net | ✅ Test | ✅ Test | Same verification pattern |

### 3. Hierarchical-Specific Operations

Additional tests for cross-hierarchy operations:
- Update component connections between hierarchies (hierarchical pins)
- Pass nets from parent → child
- Rename hierarchical pins (affects both parent and child)
- Change hierarchical pin direction

### 4. Comprehensive Schematic Element Coverage

**Initial test state should include ALL kicad-sch-api object types:**

Objects to include in test fixtures:
- ✅ `Component` (various types: R, C, L, IC)
- ✅ `Wire` (connecting components)
- ✅ `Label` (local labels)
- ⚠️ `GlobalLabel` (if supported)
- ✅ `HierarchicalLabel` (in subcircuits)
- ✅ `Power` (power symbols: VCC, GND, 3V3)
- ⚠️ `NoConnect` (NC markers)
- ⚠️ `Junction` (wire junctions)
- ⚠️ `Text` (annotations)
- ⚠️ `Bus` (bus connections)
- ⚠️ `BusEntry` (bus tap points)
- ✅ `HierarchicalSheet` (sheet symbols in parent)
- ✅ `SheetPin` (pins on sheet symbols)

**Verification Pattern:**
```python
from kicad_sch_api import Schematic

sch = Schematic.load("circuit.kicad_sch")

# Verify EXACTLY the expected components
expected_refs = {"R1", "R2", "C1", "U1"}
actual_refs = {c.reference for c in sch.components}
assert actual_refs == expected_refs, f"Expected {expected_refs}, got {actual_refs}"

# Verify EXACTLY the expected labels
expected_labels = {"DATA", "CLK"}
actual_labels = {l.text for l in sch.labels}
assert actual_labels == expected_labels, f"Expected {expected_labels}, got {actual_labels}"

# Verify EXACTLY the expected power symbols
expected_power = {"VCC", "GND"}
actual_power = {p.value for p in sch.power_symbols}
assert actual_power == expected_power, f"Expected {expected_power}, got {actual_power}"

# Continue for all element types...
```

---

## Current State Analysis

### Existing Test Classification

**Total Tests:** 68 tests (numbered 01-68, test 27 removed)

#### ✅ True Synchronization Tests (Keep in `bidirectional/`)

**Component CRUD (Root):**
- 06_add_component
- 07_delete_component
- 08_modify_value
- 13_rename_component
- 19_swap_component_type
- 50_component_footprint_change
- 09_position_preservation
- 20_component_orientation
- 63_component_rotation_preservation

**Component CRUD (Hierarchical):**
- 39_modify_component_in_subcircuit
- 41_copy_component_cross_sheet
- 42_move_component_between_sheets

**Net CRUD (Root):**
- 10_generate_with_net
- 11_add_net_to_components
- 12_change_pin_connection
- 14_merge_nets
- 15_split_net

**Net CRUD (Hierarchical):**
- 40_net_operations_in_subcircuit

**Sheet CRUD:**
- 22_add_subcircuit_sheet
- 23_remove_subcircuit_sheet
- 37_replace_subcircuit_contents
- 38_empty_subcircuit

**Hierarchical Pin/Label CRUD:**
- 44_subcircuit_hierarchical_ports
- 59_modify_hierarchical_pin_name
- 60_remove_hierarchical_pin

**Power Symbol CRUD:**
- 16_add_power_symbol
- 17_add_ground_symbol
- 26_power_symbol_replacement

**Other Elements:**
- 24_add_global_label
- 25_add_local_label

**Bulk Operations:**
- 34_bulk_component_add
- 35_bulk_component_remove
- 36_copy_paste_component

**Workflows:**
- 64_complex_multi_step_workflow
- 65_conflict_resolution

**Edge Cases:**
- 29_component_custom_properties

#### ❌ Non-Sync Tests (Move to Other Folders)

**Move to `tests/conversion/`:**
- 02_kicad_to_python
- 03_python_to_kicad
- 04_roundtrip
- 05_add_resistor_kicad_to_python
- 45_import_power_symbols_from_kicad

**Move to `tests/generation/`:**
- 01_blank_circuit
- 18_multiple_power_domains
- 21_multi_unit_components
- 30_component_missing_footprint
- 31_isolated_component
- 33_bus_connections
- 43_differential_pairs
- 47_power_symbol_in_subcircuit
- 48_multi_voltage_subcircuit
- 52_unicode_component_names
- 57_global_label_multi_sheet
- 58_hierarchical_pin_to_global_label
- 66_duplicate_net_names_isolation
- 67_connected_multi_level_hierarchy

**Move to `tests/integration/`:**
- 49_annotate_schematic
- 54_drc_validation
- 55_erc_validation
- 56_bom_export

**Move to `tests/performance/`:**
- 61_large_circuit_performance

**Blocked/Skipped:**
- 28_add_no_connect (Issue #408)
- 32_text_annotations (Issue #411)
- 51_sync_after_external_edit (SKIP - documents behavior)
- 62_wire_routing_preservation (XFAIL - aesthetic)
- 68_dynamic_sheet_sizing (XFAIL - Issue #413)

### Coverage Gaps (Need New Tests)

**Component CRUD (Hierarchical):**
- ⚠️ Add component to existing subcircuit
- ⚠️ Delete component from subcircuit

**Net CRUD (Root):**
- ⚠️ Remove component from net
- ⚠️ Delete entire net

**Net CRUD (Hierarchical):**
- ⚠️ Create net in child
- ⚠️ Add component to net in child
- ⚠️ Remove component from net in child
- ⚠️ Rename net in child
- ⚠️ Merge nets in child
- ⚠️ Split net in child
- ⚠️ Delete net in child
- ⚠️ Change pin connection in child

**Hierarchical Pin/Label:**
- ⚠️ Add new hierarchical pin to existing interface
- ⚠️ Change hierarchical pin direction

**Power Symbol:**
- ⚠️ Delete power symbol (root)
- ⚠️ Delete power symbol (hierarchical)

**Labels:**
- ⚠️ Modify label
- ⚠️ Delete label

---

## Test Matrix: CRUD Coverage

### Component CRUD

#### Root Sheet Component CRUD

| Test # | Name | Operation | Initial State | Modification | Final State | Preservation Check |
|--------|------|-----------|---------------|--------------|-------------|-------------------|
| 10 | `sync_component_root_create` | Create | R1, C1, U1, VCC, GND, Labels | Add R2 | R1, R2, C1, U1, VCC, GND, Labels | All others preserved |
| 11 | `sync_component_root_update_value` | Update | R1(10k), C1, U1 | R1→47k | R1(47k), C1, U1 | C1, U1 unchanged |
| 12 | `sync_component_root_update_ref` | Update | R1, C1, U1 | R1→R10 | R10, C1, U1 | C1, U1 unchanged |
| 13 | `sync_component_root_update_footprint` | Update | R1(0603), C1, U1 | R1→0805 | R1(0805), C1, U1 | C1, U1 unchanged |
| 14 | `sync_component_root_update_type` | Update | R1, C1, U1 | R1→C2 | C1, C2, U1 | C1, U1 unchanged, positions preserved |
| 15 | `sync_component_root_delete` | Delete | R1, R2, C1, U1 | Delete R2 | R1, C1, U1 | R1, C1, U1 unchanged |
| 16 | `sync_component_root_position_preserve` | Update | R1@(100,100) | R1 value change | R1@(100,100) | Position unchanged |
| 17 | `sync_component_root_rotation_preserve` | Update | R1@90° | R1 value change | R1@90° | Rotation unchanged |

#### Hierarchical Sheet Component CRUD

| Test # | Name | Operation | Initial State | Modification | Final State | Preservation Check |
|--------|------|-----------|---------------|--------------|-------------|-------------------|
| 50 | `sync_component_hier_create` | Create | Child: R1, C1; Parent: R_main | Child: Add R2 | Child: R1, R2, C1; Parent: R_main | Parent unchanged, child R1,C1 preserved |
| 51 | `sync_component_hier_update_value` | Update | Child: R1(10k), C1 | Child: R1→47k | Child: R1(47k), C1 | Parent unchanged, C1 unchanged |
| 52 | `sync_component_hier_update_ref` | Update | Child: R1, C1 | Child: R1→R10 | Child: R10, C1 | Parent unchanged, C1 unchanged |
| 53 | `sync_component_hier_update_footprint` | Update | Child: R1(0603), C1 | Child: R1→0805 | Child: R1(0805), C1 | Parent unchanged, C1 unchanged |
| 54 | `sync_component_hier_update_type` | Update | Child: R1, C1 | Child: R1→C2 | Child: C1, C2 | Parent unchanged, C1 unchanged |
| 55 | `sync_component_hier_delete` | Delete | Child: R1, R2, C1 | Child: Delete R2 | Child: R1, C1 | Parent unchanged, R1,C1 unchanged |
| 56 | `sync_component_hier_position_preserve` | Update | Child: R1@(100,100) | Child: R1 value change | Child: R1@(100,100) | Position unchanged |
| 57 | `sync_component_hier_rotation_preserve` | Update | Child: R1@90° | Child: R1 value change | Child: R1@90° | Rotation unchanged |

---

### Net CRUD

#### Root Sheet Net CRUD

| Test # | Name | Operation | Initial State | Modification | Final State | Preservation Check |
|--------|------|-----------|---------------|--------------|-------------|-------------------|
| 30 | `sync_net_root_create` | Create | NET1(R1-R2) | Add NET2(R3-R4) | NET1, NET2 | NET1 unchanged |
| 31 | `sync_net_root_add_component` | Update | NET1(R1-R2) | Add R3 to NET1 | NET1(R1-R2-R3) | R1-R2 connection preserved |
| 32 | `sync_net_root_remove_component` | Update | NET1(R1-R2-R3) | Remove R3 from NET1 | NET1(R1-R2) | R1-R2 connection preserved |
| 33 | `sync_net_root_rename` | Update | NET1(R1-R2) | NET1→DATA | DATA(R1-R2) | Connection preserved |
| 34 | `sync_net_root_merge` | Update | NET1(R1-R2), NET2(R3-R4) | Merge NET2→NET1 | NET1(R1-R2-R3-R4) | All connections preserved |
| 35 | `sync_net_root_split` | Update | NET1(R1-R2-R3-R4) | Split R3-R4→NET2 | NET1(R1-R2), NET2(R3-R4) | Connections preserved |
| 36 | `sync_net_root_delete` | Delete | NET1(R1-R2), NET2(R3-R4) | Delete NET2 | NET1(R1-R2) | NET1 unchanged, R3-R4 unconnected |
| 37 | `sync_net_root_change_pin` | Update | NET1(R1.1-R2.1) | R2.1→R2.2 | NET1(R1.1-R2.2) | R1 connection preserved |

#### Hierarchical Sheet Net CRUD

| Test # | Name | Operation | Initial State | Modification | Final State | Preservation Check |
|--------|------|-----------|---------------|--------------|-------------|-------------------|
| 60 | `sync_net_hier_create` | Create | Child: NET1(R1-R2) | Child: Add NET2(R3-R4) | Child: NET1, NET2 | Parent unchanged, NET1 unchanged |
| 61 | `sync_net_hier_add_component` | Update | Child: NET1(R1-R2) | Child: Add R3 to NET1 | Child: NET1(R1-R2-R3) | Parent unchanged |
| 62 | `sync_net_hier_remove_component` | Update | Child: NET1(R1-R2-R3) | Child: Remove R3 | Child: NET1(R1-R2) | Parent unchanged |
| 63 | `sync_net_hier_rename` | Update | Child: NET1(R1-R2) | Child: NET1→DATA | Child: DATA(R1-R2) | Parent unchanged |
| 64 | `sync_net_hier_merge` | Update | Child: NET1(R1-R2), NET2(R3-R4) | Child: Merge NET2→NET1 | Child: NET1(R1-R2-R3-R4) | Parent unchanged |
| 65 | `sync_net_hier_split` | Update | Child: NET1(R1-R2-R3-R4) | Child: Split R3-R4→NET2 | Child: NET1(R1-R2), NET2(R3-R4) | Parent unchanged |
| 66 | `sync_net_hier_delete` | Delete | Child: NET1(R1-R2), NET2(R3-R4) | Child: Delete NET2 | Child: NET1(R1-R2) | Parent unchanged, NET1 unchanged |
| 67 | `sync_net_hier_change_pin` | Update | Child: NET1(R1.1-R2.1) | Child: R2.1→R2.2 | Child: NET1(R1.1-R2.2) | Parent unchanged |

---

### Hierarchical Sheet CRUD

| Test # | Name | Operation | Initial State | Modification | Final State | Preservation Check |
|--------|------|-----------|---------------|--------------|-------------|-------------------|
| 40 | `sync_sheet_create_level1` | Create | Main only | Add level1() | Main + level1 sheets | Main unchanged |
| 41 | `sync_sheet_create_level2` | Create | Main + level1 | level1: Add level2() | Main + level1 + level2 | Main, level1 unchanged |
| 42 | `sync_sheet_create_parallel` | Create | Main + child1 | Add child2() | Main + child1 + child2 | Main, child1 unchanged |
| 43 | `sync_sheet_delete_leaf` | Delete | Main + level1 + level2 | Remove level2() | Main + level1 | Main, level1 unchanged |
| 44 | `sync_sheet_delete_branch` | Delete | Main + child1 + child2 | Remove child1() | Main + child2 | Main, child2 unchanged |
| 45 | `sync_sheet_replace_contents` | Update | Child: R1, C1 | Child: R2, R3 | Child: R2, R3 | Parent unchanged |
| 46 | `sync_sheet_rename` | Update | child_circuit → spi_driver | Rename function | New sheet name | Parent sheet symbol updates |

---

### Hierarchical Pin/Label CRUD

| Test # | Name | Operation | Initial State | Modification | Final State | Preservation Check |
|--------|------|-----------|---------------|--------------|-------------|-------------------|
| 70 | `sync_hierpin_create` | Create | Child: no pins; Parent: no pins | Pass net to child | Child: HierLabel; Parent: SheetPin | Both created |
| 71 | `sync_hierpin_rename` | Update | DATA_IN pin | Rename DATA_IN→SPI_MOSI | SPI_MOSI pin | Connection preserved, old label removed |
| 72 | `sync_hierpin_delete` | Delete | DATA_IN, CLK pins | Remove DATA_IN | CLK pin only | CLK unchanged, DATA_IN removed from both |
| 73 | `sync_hierpin_change_direction` | Update | DATA_IN (input) | DATA_IN→bidirectional | DATA_IN (bidirectional) | Connection preserved |
| 74 | `sync_hierpin_add_to_existing` | Create | Child: DATA pin | Add CLK pin | Child: DATA, CLK pins | DATA unchanged |

---

### Power Symbol CRUD

| Test # | Name | Operation | Initial State | Modification | Final State | Preservation Check |
|--------|------|-----------|---------------|--------------|-------------|-------------------|
| 20 | `sync_power_root_create` | Create | R1, C1 | Add VCC symbol | R1, C1, VCC | R1, C1 unchanged |
| 21 | `sync_power_root_delete` | Delete | R1, VCC, GND | Remove VCC | R1, GND | R1, GND unchanged |
| 22 | `sync_power_root_replace` | Update | VCC symbol | VCC→3V3 | 3V3 symbol | R1, C1 unchanged |
| 23 | `sync_power_hier_create` | Create | Child: R1, C1 | Child: Add VCC | Child: R1, C1, VCC | Parent unchanged |
| 24 | `sync_power_hier_delete` | Delete | Child: R1, VCC, GND | Child: Remove VCC | Child: R1, GND | Parent unchanged |

---

### Other Schematic Elements CRUD

| Test # | Name | Operation | Initial State | Modification | Final State | Preservation Check |
|--------|------|-----------|---------------|--------------|-------------|-------------------|
| 80 | `sync_label_root_create` | Create | R1, C1 | Add "DATA" label | R1, C1, "DATA" label | R1, C1 unchanged |
| 81 | `sync_label_root_delete` | Delete | R1, "DATA", "CLK" labels | Remove "DATA" | R1, "CLK" label | R1, CLK unchanged |
| 82 | `sync_label_root_rename` | Update | "DATA" label | DATA→SPI_MOSI | "SPI_MOSI" label | R1, C1 unchanged |

---

### Bulk Operations

| Test # | Name | Operation | Initial State | Modification | Final State | Preservation Check |
|--------|------|-----------|---------------|--------------|-------------|-------------------|
| 90 | `sync_bulk_component_add` | Create | R1-R10 | Add R11-R20 (loop) | R1-R20 | R1-R10 unchanged |
| 91 | `sync_bulk_component_delete` | Delete | R1-R20 | Delete R11-R20 (loop) | R1-R10 | R1-R10 unchanged |
| 92 | `sync_bulk_net_create` | Create | 10 resistor pairs | Connect all pairs | 10 nets | All resistors preserved |

---

### Cross-Hierarchy Operations

| Test # | Name | Operation | Description | Preservation Check |
|--------|------|-----------|-------------|--------------------|
| 95 | `sync_cross_hier_pass_net` | Create | Parent net passed to child | Child gets hierarchical label/pin, parent sheet pin created |
| 96 | `sync_cross_hier_disconnect_net` | Delete | Stop passing net to child | Hierarchical label/pin removed, child components preserved |
| 97 | `sync_cross_hier_multi_level_net` | Create | Net passed main→level1→level2 | Hierarchical labels at each level |
| 98 | `sync_cross_hier_component_move` | Update | Move component from child1 to child2 | Both sheets preserve other components |
| 99 | `sync_cross_hier_component_copy` | Create | Copy component from child1 to child2 | child1 unchanged, child2 gets copy |

---

## Verification Patterns

### Standard Test Structure

Every synchronization test follows this pattern:

```python
def test_XX_operation_name(request):
    """Test [operation] while preserving all other schematic elements.

    Initial State:
    - Root: R1, R2, C1, VCC, GND, DATA label
    - Child: (if applicable)

    Operation:
    - [Describe modification]

    Expected Result:
    - [Describe expected state]

    Preservation:
    - All elements except [modified element] unchanged
    - Positions, rotations, properties preserved
    - Other sheets unaffected (if hierarchical)
    """

    # Setup
    test_dir = Path(__file__).parent
    python_file = test_dir / "circuit.py"
    output_dir = test_dir / "circuit"
    schematic_file = output_dir / "circuit.kicad_sch"

    # Read original
    with open(python_file, "r") as f:
        original_code = f.read()

    try:
        # ================================================================
        # STEP 1: Generate initial state with ALL element types
        # ================================================================
        print("\n" + "="*70)
        print("STEP 1: Generate initial comprehensive circuit")
        print("="*70)

        result = subprocess.run(
            ["uv", "run", "circuit.py"],
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

        # COMPREHENSIVE VERIFICATION using kicad-sch-api
        from kicad_sch_api import Schematic
        sch = Schematic.load(str(schematic_file))

        # Verify EXACTLY expected components
        expected_components = {"R1", "R2", "C1"}
        actual_components = {c.reference for c in sch.components}
        assert actual_components == expected_components, \
            f"Components mismatch: expected {expected_components}, got {actual_components}"

        # Verify EXACTLY expected power symbols
        expected_power = {"VCC", "GND"}
        actual_power = {p.value for p in sch.power_symbols}
        assert actual_power == expected_power, \
            f"Power symbols mismatch: expected {expected_power}, got {actual_power}"

        # Verify EXACTLY expected labels
        expected_labels = {"DATA"}
        actual_labels = {l.text for l in sch.labels}
        assert actual_labels == expected_labels, \
            f"Labels mismatch: expected {expected_labels}, got {actual_labels}"

        # Store initial state for comparison
        r1_initial = next(c for c in sch.components if c.reference == "R1")
        r1_initial_pos = r1_initial.position
        r1_initial_value = r1_initial.value

        r2_initial = next(c for c in sch.components if c.reference == "R2")
        c1_initial = next(c for c in sch.components if c.reference == "C1")

        print(f"✅ Initial state verified:")
        print(f"   Components: {actual_components}")
        print(f"   Power: {actual_power}")
        print(f"   Labels: {actual_labels}")
        print(f"   R1 position: {r1_initial_pos}")

        # ================================================================
        # STEP 2: Modify Python code (perform CRUD operation)
        # ================================================================
        print("\n" + "="*70)
        print("STEP 2: Modify circuit (CRUD operation)")
        print("="*70)

        modified_code = original_code.replace(
            'r1 = Component(..., value="10k", ...)',
            'r1 = Component(..., value="47k", ...)'
        )

        with open(python_file, "w") as f:
            f.write(modified_code)

        print(f"✅ Modified: R1 value 10k → 47k")

        # ================================================================
        # STEP 3: Regenerate (sync should detect change)
        # ================================================================
        print("\n" + "="*70)
        print("STEP 3: Regenerate circuit (trigger synchronization)")
        print("="*70)

        result = subprocess.run(
            ["uv", "run", "circuit.py"],
            cwd=test_dir,
            capture_output=True,
            text=True,
            timeout=30
        )

        assert result.returncode == 0, (
            f"Step 3 failed: Regeneration\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )

        # Verify sync log shows update
        assert "🔄 Update: R1" in result.stdout or "Update: R1" in result.stdout, \
            f"Sync log should show R1 update. Output:\n{result.stdout}"

        print(f"✅ Synchronization detected R1 update")

        # ================================================================
        # STEP 4: COMPREHENSIVE VERIFICATION - Only R1 value changed
        # ================================================================
        print("\n" + "="*70)
        print("STEP 4: Verify ONLY R1 value changed, all else preserved")
        print("="*70)

        sch_updated = Schematic.load(str(schematic_file))

        # Verify component set unchanged (same references)
        actual_components_updated = {c.reference for c in sch_updated.components}
        assert actual_components_updated == expected_components, \
            f"Component set changed! Expected {expected_components}, got {actual_components_updated}"

        # Verify power symbols unchanged
        actual_power_updated = {p.value for p in sch_updated.power_symbols}
        assert actual_power_updated == expected_power, \
            f"Power symbols changed! Expected {expected_power}, got {actual_power_updated}"

        # Verify labels unchanged
        actual_labels_updated = {l.text for l in sch_updated.labels}
        assert actual_labels_updated == expected_labels, \
            f"Labels changed! Expected {expected_labels}, got {actual_labels_updated}"

        # Verify R1 value updated
        r1_updated = next(c for c in sch_updated.components if c.reference == "R1")
        assert r1_updated.value == "47k", \
            f"R1 value not updated: expected '47k', got '{r1_updated.value}'"

        # Verify R1 position preserved
        assert r1_updated.position == r1_initial_pos, \
            f"R1 position changed! Expected {r1_initial_pos}, got {r1_updated.position}"

        # Verify R2 completely unchanged
        r2_updated = next(c for c in sch_updated.components if c.reference == "R2")
        assert r2_updated.value == r2_initial.value, \
            f"R2 value changed! Expected {r2_initial.value}, got {r2_updated.value}"
        assert r2_updated.position == r2_initial.position, \
            f"R2 position changed! Expected {r2_initial.position}, got {r2_updated.position}"
        assert r2_updated.footprint == r2_initial.footprint, \
            f"R2 footprint changed! Expected {r2_initial.footprint}, got {r2_updated.footprint}"

        # Verify C1 completely unchanged
        c1_updated = next(c for c in sch_updated.components if c.reference == "C1")
        assert c1_updated.value == c1_initial.value, \
            f"C1 value changed! Expected {c1_initial.value}, got {c1_updated.value}"
        assert c1_updated.position == c1_initial.position, \
            f"C1 position changed! Expected {c1_initial.position}, got {c1_updated.position}"

        print(f"✅ Verification passed:")
        print(f"   ✓ R1 value updated: 10k → 47k")
        print(f"   ✓ R1 position preserved: {r1_updated.position}")
        print(f"   ✓ R2 completely unchanged")
        print(f"   ✓ C1 completely unchanged")
        print(f"   ✓ Power symbols unchanged: {actual_power_updated}")
        print(f"   ✓ Labels unchanged: {actual_labels_updated}")
        print(f"\n🎉 PRESERVATION TEST PASSED!")

    finally:
        # Restore original
        with open(python_file, "w") as f:
            f.write(original_code)

        # Cleanup
        cleanup = not request.config.getoption("--keep-output", default=False)
        if cleanup and output_dir.exists():
            shutil.rmtree(output_dir)
```

---

## Test Fixtures

### Comprehensive Root Fixture

```python
# tests/bidirectional/fixtures/comprehensive_root.py

from circuit_synth import circuit, Component, Net, Power

@circuit(name="comprehensive_root")
def comprehensive_root():
    """Comprehensive root circuit with ALL element types.

    Used for testing that CRUD operations preserve all other elements.

    Contains:
    - 3 components (R1, C1, U1)
    - 2 power symbols (VCC, GND)
    - 2 nets with labels (DATA, CLK)
    - Connections between components
    """
    # Components
    r1 = Component(
        symbol="Device:R",
        ref="R1",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )
    c1 = Component(
        symbol="Device:C",
        ref="C1",
        value="100nF",
        footprint="Capacitor_SMD:C_0603_1608Metric"
    )
    u1 = Component(
        symbol="74xx:74LS00",
        ref="U1",
        footprint="Package_DIP:DIP-14_W7.62mm"
    )

    # Power symbols
    vcc = Power("VCC")
    gnd = Power("GND")

    # Nets with labels
    data = Net("DATA")
    clk = Net("CLK")

    # Connections
    data.connect(r1, 1)
    data.connect(c1, 1)
    clk.connect(u1, 1)

    # Power connections
    vcc.connect(r1, 2)
    gnd.connect(c1, 2)
```

### Comprehensive Hierarchical Fixture

```python
# tests/bidirectional/fixtures/comprehensive_hierarchical.py

from circuit_synth import circuit, Component, Net, Power

@circuit(name="child_comprehensive")
def child_comprehensive():
    """Comprehensive child circuit with all element types."""
    r1 = Component(symbol="Device:R", ref="R1", value="10k", footprint="R_0603")
    c1 = Component(symbol="Device:C", ref="C1", value="100nF", footprint="C_0603")
    vcc = Power("VCC")
    gnd = Power("GND")

    data = Net("DATA")
    data.connect(r1, 1)
    data.connect(c1, 1)
    vcc.connect(r1, 2)
    gnd.connect(c1, 2)

@circuit(name="parent_comprehensive")
def parent_comprehensive():
    """Parent circuit with child subcircuit and own elements."""
    r_main = Component(symbol="Device:R", ref="R_main", value="1k", footprint="R_0603")
    vcc_main = Power("VCC")

    data_parent = Net("DATA_PARENT")
    data_parent.connect(r_main, 1)
    vcc_main.connect(r_main, 2)

    # Child with passed net (creates hierarchical connection)
    child_comprehensive(connections={"DATA": data_parent})
```

---

## Implementation Phases

### Phase 1: Root Sheet CRUD (Complete Coverage)
**Priority: HIGHEST**

Implement all root sheet CRUD tests:
- Component CRUD (tests 10-17)
- Net CRUD (tests 30-37)
- Power CRUD (tests 20-22)
- Label CRUD (tests 80-82)

**Deliverable:** Complete CRUD coverage for root sheet with comprehensive preservation verification.

**Estimated Tests:** 20 tests

### Phase 2: Hierarchical Sheet CRUD (Parallel Coverage)
**Priority: HIGH**

Implement all hierarchical sheet CRUD tests:
- Component CRUD (tests 50-57) - Mirror of root sheet tests
- Net CRUD (tests 60-67) - Mirror of root sheet tests
- Sheet CRUD (tests 40-46)
- Power CRUD (tests 23-24)

**Deliverable:** Same CRUD operations work correctly in hierarchical contexts.

**Estimated Tests:** 25 tests

### Phase 3: Cross-Hierarchy Operations
**Priority: MEDIUM**

Implement cross-hierarchy tests:
- Hierarchical pin CRUD (tests 70-74)
- Cross-hierarchy operations (tests 95-99)

**Deliverable:** Multi-level hierarchy operations work correctly.

**Estimated Tests:** 10 tests

### Phase 4: Other Elements & Bulk Operations
**Priority: LOW**

- Other elements (NoConnect, Text, Bus)
- Bulk operations (tests 90-92)
- Complex workflows

**Deliverable:** Complete coverage of all schematic elements.

**Estimated Tests:** 10 tests

---

## Migration Plan

### Step 1: Create New Folder Structure

```bash
mkdir -p tests/conversion/{import,export,roundtrip}
mkdir -p tests/generation/{basic,power,hierarchical,advanced,edge_cases}
mkdir -p tests/integration/kicad_tools
mkdir -p tests/performance
mkdir -p tests/kicad_sch_api/{primitives,hierarchical,properties,validation}
mkdir -p tests/bidirectional/fixtures
```

### Step 2: Move Non-Sync Tests

**To `tests/conversion/`:**
```bash
mv tests/bidirectional/02_kicad_to_python tests/conversion/import/01_blank_import
mv tests/bidirectional/04_roundtrip tests/conversion/roundtrip/01_simple_roundtrip
# ... etc
```

**To `tests/generation/`:**
```bash
mv tests/bidirectional/01_blank_circuit tests/generation/basic/01_blank
mv tests/bidirectional/18_multiple_power_domains tests/generation/power/01_multi_voltage
# ... etc
```

**To `tests/integration/`:**
```bash
mv tests/bidirectional/49_annotate_schematic tests/integration/kicad_tools/
mv tests/bidirectional/54_drc_validation tests/integration/kicad_tools/
# ... etc
```

**To `tests/performance/`:**
```bash
mv tests/bidirectional/61_large_circuit_performance tests/performance/test_large_circuit.py
```

### Step 3: Renumber Remaining Tests

After moving non-sync tests, renumber the remaining sync tests according to the test matrix (10-99).

### Step 4: Implement New Tests

Follow the implementation phases to add missing CRUD coverage.

---

## Summary

### Test Count Summary

**Existing Sync Tests (to keep):** ~40 tests
**New Tests Needed (gaps):** ~25 tests
**Total Sync Tests (target):** ~65 tests

**Non-Sync Tests (to move):** ~28 tests
- Conversion: 5 tests
- Generation: 14 tests
- Integration: 4 tests
- Performance: 1 test
- Blocked/Skipped: 4 tests

### Coverage Quality

**After Implementation:**
- ✅ Component CRUD (root): 8 tests - COMPLETE
- ✅ Component CRUD (hierarchical): 8 tests - COMPLETE
- ✅ Net CRUD (root): 8 tests - COMPLETE
- ✅ Net CRUD (hierarchical): 8 tests - COMPLETE
- ✅ Sheet CRUD: 7 tests - COMPLETE
- ✅ Hierarchical Pin CRUD: 5 tests - COMPLETE
- ✅ Power CRUD: 5 tests - COMPLETE
- ✅ Cross-hierarchy: 5 tests - COMPLETE
- ✅ Bulk operations: 3 tests - COMPLETE

**Total: ~65 systematic synchronization tests with comprehensive preservation verification**

---

**Ready to implement?** Next steps:
1. Create fixtures (`comprehensive_root.py`, `comprehensive_hierarchical.py`)
2. Create helper utilities (verification functions)
3. Implement Phase 1 (Root Component CRUD - tests 10-17)
4. Validate pattern works, iterate on helpers
5. Expand to other CRUD categories
