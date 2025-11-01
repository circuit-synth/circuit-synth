# Circuit-Synth Testing Structure

**Date:** 2025-11-01
**Purpose:** Define clear boundaries and organization for all test categories

---

## Test Folder Organization

```
tests/
├── bidirectional/              # ONLY synchronization tests (Python ↔ KiCad)
│   ├── component_crud_root/    # Component CRUD on root sheet
│   ├── component_crud_hier/    # Component CRUD on hierarchical sheets
│   ├── net_crud_root/          # Net CRUD on root sheet
│   ├── net_crud_hier/          # Net CRUD on hierarchical sheets
│   ├── sheet_crud/             # Hierarchical sheet CRUD
│   ├── label_crud/             # Hierarchical label/pin CRUD
│   ├── power_crud/             # Power symbol CRUD
│   ├── cross_hierarchy/        # Cross-sheet operations
│   └── bulk_operations/        # Bulk CRUD operations
│
├── generation/                 # One-way Python → KiCad generation
│   ├── basic_circuits/         # Simple generation tests
│   │   ├── 01_blank_circuit/
│   │   ├── 02_single_component/
│   │   └── 03_simple_net/
│   ├── power_distribution/     # Power rail generation
│   │   ├── 01_single_power/
│   │   ├── 02_multi_voltage/
│   │   └── 03_power_in_hierarchy/
│   ├── hierarchical/           # Hierarchy generation (not sync)
│   │   ├── 01_single_level/
│   │   ├── 02_multi_level/
│   │   └── 03_parallel_sheets/
│   ├── advanced_features/      # Advanced generation features
│   │   ├── 01_differential_pairs/
│   │   ├── 02_bus_connections/
│   │   ├── 03_multi_unit_components/
│   │   └── 04_unicode_names/
│   └── edge_cases/             # Edge case generation
│       ├── 01_empty_circuit/
│       ├── 02_isolated_component/
│       └── 03_missing_footprint/
│
├── NOTE: kicad-sch-api object tests belong in kicad-sch-api repo, NOT here!
│   See: https://github.com/shanemmattner/kicad-sch-api/tests/
│
├── conversion/                 # Round-trip & import/export
│   ├── import/                 # KiCad → Python conversion
│   │   ├── 01_blank_import/
│   │   ├── 02_component_import/
│   │   ├── 03_net_import/
│   │   └── 04_hierarchy_import/
│   ├── export/                 # Python → KiCad conversion
│   │   ├── 01_basic_export/
│   │   ├── 02_complex_export/
│   │   └── 03_hierarchy_export/
│   └── roundtrip/              # Full cycle fidelity
│       ├── 01_simple_roundtrip/
│       ├── 02_complex_roundtrip/
│       └── 03_hierarchy_roundtrip/
│
├── integration/                # External tool integration
│   ├── kicad_tools/            # KiCad CLI tool integration
│   │   ├── test_drc.py
│   │   ├── test_erc.py
│   │   ├── test_netlist_export.py
│   │   ├── test_bom_export.py
│   │   └── test_annotation.py
│   ├── pcb_sync/               # PCB synchronization
│   │   ├── test_footprint_sync.py
│   │   └── test_netlist_to_pcb.py
│   └── external_edits/         # External editor handling
│       ├── test_git_merge.py
│       └── test_concurrent_edit.py
│
├── performance/                # Performance & stress tests
│   ├── test_large_circuit.py       # 100+ components
│   ├── test_deep_hierarchy.py      # 5+ levels
│   ├── test_bulk_operations.py     # 1000+ components
│   └── test_sync_performance.py    # Sync speed benchmarks
│
├── validation/                 # Design rule & constraint validation
│   ├── test_reference_collision.py
│   ├── test_net_isolation.py
│   └── test_constraint_checking.py
│
└── fixtures/                   # Shared test fixtures
    ├── comprehensive_root.py       # Full-featured root circuit
    ├── comprehensive_hierarchical.py  # Full-featured hierarchy
    ├── helpers.py                  # Verification helpers
    └── conftest.py                 # pytest fixtures
```

---

## Test Category Definitions

### 1. `tests/bidirectional/` - Synchronization Tests (THE CORE)

**Purpose:** Test that Python code modifications correctly synchronize to KiCad schematics while preserving all other elements.

**Pattern:**
1. Generate initial state
2. Modify Python code
3. Regenerate (sync detects change)
4. Verify ONLY intended change occurred, all else preserved

**Key Characteristics:**
- ✅ Multi-step tests (Step 1: initial, Step 2: modify, Step 3: verify)
- ✅ Uses `kicad-sch-api` to verify exact schematic contents
- ✅ Checks synchronization logs (`➕ Add: R2`, `🔄 Update: R1`, `❌ Delete: R3`)
- ✅ Verifies preservation (positions, rotations, other components unchanged)

**Examples:**
- `sync_component_root_create` - Add R2 to circuit with R1, C1, verify R1/C1 preserved
- `sync_net_hier_delete` - Delete NET2 from child sheet, verify parent unchanged
- `sync_hierpin_rename` - Rename DATA_IN→SPI_MOSI, verify old label removed

**NOT in this folder:**
- ❌ One-time generation tests (no modification/sync)
- ❌ Import/export tests (conversion, not sync)
- ❌ Tool integration tests (DRC, ERC, BOM)

---

### 2. `tests/generation/` - One-Way Generation Tests

**Purpose:** Test that circuit-synth can generate valid KiCad projects for various circuit patterns.

**Pattern:**
1. Run Python circuit script
2. Verify KiCad files generated
3. Validate output structure

**Key Characteristics:**
- ✅ Single-step tests (generate once, validate)
- ✅ No modification or synchronization
- ✅ Tests feature coverage (differential pairs, buses, multi-voltage)
- ✅ Edge case handling (empty circuits, missing footprints)

**Examples:**
- `01_blank_circuit` - Generate empty project
- `02_multi_voltage` - Generate circuit with VCC, 3V3, 5V, 12V rails
- `03_differential_pairs` - Generate USB differential pair routing

**NOT in this folder:**
- ❌ Synchronization tests (multi-step modify+regenerate)
- ❌ Round-trip conversion tests

---

### 3. kicad-sch-api Object Tests - BELONGS IN kicad-sch-api REPO

**NOTE:** Tests for kicad-sch-api primitives (Component, Wire, Label, etc.) should be in the kicad-sch-api repository, NOT in circuit-synth.

**kicad-sch-api Current Test Coverage:**
- ✅ Component creation and properties
- ✅ Wire creation (basic)
- ✅ Geometry and positioning
- ✅ Grid snapping
- ✅ Pin positioning
- ✅ CLI integration (ERC, netlist, BOM)
- ✅ Hierarchical instances

**kicad-sch-api Missing Test Coverage** (from their README.md):
- ⚠️ Wire connections (pending)
- ⚠️ Labels (local, global, hierarchical) (pending)
- ⚠️ Text elements and text boxes (pending)
- ⚠️ Hierarchical sheets (pending)
- ⚠️ Power symbols (pending)
- ⚠️ Multi-unit components (pending)
- ⚠️ NoConnect markers (pending)
- ⚠️ Junctions (pending)
- ⚠️ Bus connections (pending)
- ⚠️ Bus entries (pending)

**Action:** ✅ GitHub issue created: https://github.com/circuit-synth/kicad-sch-api/issues/79

---

### 4. `tests/conversion/` - Import/Export Round-Trip

**Purpose:** Test that conversion between Python and KiCad preserves data (fidelity tests).

**Pattern:**
1. Python → KiCad (export)
2. KiCad → Python (import)
3. Python → KiCad (re-export)
4. Verify properties preserved through full cycle

**Key Characteristics:**
- ✅ Tests conversion fidelity (data preservation)
- ✅ Round-trip validation
- ✅ AST validation for Python code
- ✅ kicad-sch-api validation for KiCad schematics

**Examples:**
- `01_simple_roundtrip` - R1 component survives full cycle
- `02_complex_roundtrip` - Multi-component circuit with nets
- `03_hierarchy_roundtrip` - Hierarchical circuit survives cycle

**NOT in this folder:**
- ❌ Synchronization tests (multi-step modifications)
- ❌ Generation-only tests

---

### 5. `tests/integration/` - External Tool Integration

**Purpose:** Test integration with external tools (KiCad CLI, PCB sync, etc.).

**Pattern:**
1. Generate circuit
2. Run external tool (kicad-cli drc, erc, etc.)
3. Verify tool output

**Examples:**
- `test_drc.py` - Run DRC validation via kicad-cli
- `test_erc.py` - Run ERC validation via kicad-cli
- `test_bom_export.py` - Export BOM to CSV
- `test_netlist_export.py` - Export netlist

**NOT in this folder:**
- ❌ Synchronization tests
- ❌ Generation tests
- ❌ Conversion tests

---

### 6. `tests/performance/` - Performance & Stress Tests

**Purpose:** Validate performance with large/complex circuits.

**Pattern:**
1. Generate large circuit (100+ components, 5+ hierarchy levels, etc.)
2. Measure execution time
3. Verify all components present
4. Check performance thresholds

**Examples:**
- `test_large_circuit.py` - 100+ components
- `test_deep_hierarchy.py` - 5+ hierarchy levels
- `test_bulk_operations.py` - 1000+ component operations

---

### 7. `tests/validation/` - Design Rule Validation

**Purpose:** Test circuit-synth's own validation rules (reference collisions, net isolation, etc.).

**Pattern:**
1. Create circuit with potential rule violation
2. Run validation
3. Verify expected warnings/errors

**Examples:**
- `test_reference_collision.py` - Detect duplicate references
- `test_net_isolation.py` - Ensure isolated nets don't merge

---

## Test Verification Patterns

### Synchronization Test Pattern (bidirectional/)
```python
def test_sync_operation():
    # Step 1: Generate initial state
    run_circuit()
    verify_initial_state_exact()  # Uses kicad-sch-api

    # Step 2: Modify Python code
    modify_python_file()

    # Step 3: Regenerate (sync)
    run_circuit()
    verify_sync_log()  # Check "Add:", "Update:", "Delete:"

    # Step 4: Verify preservation
    verify_only_intended_change()  # All else unchanged
    verify_positions_preserved()
    verify_other_sheets_unchanged()
```

### Generation Test Pattern (generation/)
```python
def test_generation_feature():
    # Step 1: Generate
    run_circuit()

    # Step 2: Validate output
    verify_files_exist()
    verify_schematic_structure()
    verify_feature_generated()
```

### kicad-sch-api Test Pattern (kicad_sch_api/)
```python
def test_api_object():
    # Step 1: Create object
    obj = ApiClass(...)

    # Step 2: Verify properties
    verify_properties()

    # Step 3: Serialize
    sexpr = obj.to_sexpr()

    # Step 4: Validate S-expression
    verify_sexpr_format()
```

### Conversion Test Pattern (conversion/)
```python
def test_roundtrip():
    # Python → KiCad
    run_circuit()
    verify_kicad_output()

    # KiCad → Python
    run_import()
    verify_python_code()

    # Python → KiCad (again)
    run_circuit()
    verify_preserved()
```

---

## Migration Plan for Existing Tests

### Tests to Move to `generation/`:
- `01_blank_circuit`
- `18_multiple_power_domains`
- `21_multi_unit_components`
- `30_component_missing_footprint`
- `31_isolated_component`
- `33_bus_connections`
- `43_differential_pairs`
- `47_power_symbol_in_subcircuit`
- `48_multi_voltage_subcircuit`
- `52_unicode_component_names`
- `57_global_label_multi_sheet`
- `58_hierarchical_pin_to_global_label`
- `66_duplicate_net_names_isolation`
- `67_connected_multi_level_hierarchy`

### Tests to Move to `integration/`:
- `49_annotate_schematic` → `integration/kicad_tools/test_annotation.py`
- `54_drc_validation` → `integration/kicad_tools/test_drc.py`
- `55_erc_validation` → `integration/kicad_tools/test_erc.py`
- `56_bom_export` → `integration/kicad_tools/test_bom_export.py`

### Tests to Move to `performance/`:
- `61_large_circuit_performance` → `performance/test_large_circuit.py`

### Tests to Move to `conversion/`:
- `02_kicad_to_python` → `conversion/import/01_blank_import/`
- `03_python_to_kicad` → `conversion/export/01_basic_export/`
- `04_roundtrip` → `conversion/roundtrip/01_simple_roundtrip/`
- `05_add_resistor_kicad_to_python` → `conversion/import/02_component_import/`
- `45_import_power_symbols_from_kicad` → `conversion/import/03_power_import/`

### Tests to Keep in `bidirectional/` (True Sync Tests):
All tests that follow the multi-step pattern:
1. Generate initial
2. Modify Python
3. Regenerate
4. Verify sync + preservation

Examples: 06, 07, 08, 13, 19, 22, 23, 34, 35, 36, 37, 39, 40, 41, 42, 59, 60, 64, 65

---

## kicad-sch-api GitHub Issue

Since kicad-sch-api object tests belong in the kicad-sch-api repository, we've filed a GitHub issue requesting comprehensive unit test coverage:

**✅ Issue Created:** https://github.com/circuit-synth/kicad-sch-api/issues/79

---

### Title: Add comprehensive unit tests for all schematic object types

**Description:**

The kicad-sch-api library needs comprehensive unit test coverage for all schematic object types to ensure API correctness, prevent regressions, and document usage patterns.

**Current Test Coverage** (from tests/README.md):
- ✅ Component creation and properties
- ✅ Wire creation (basic)
- ✅ Geometry and positioning
- ✅ Grid snapping
- ✅ Pin positioning
- ✅ CLI integration (ERC, netlist, BOM)
- ✅ Hierarchical instances

**Missing Test Coverage** (marked as "Pending Implementation"):
- ⚠️ Wire connections (pending)
- ⚠️ Labels (local, global, hierarchical) (pending)
- ⚠️ Text elements and text boxes (pending)
- ⚠️ Hierarchical sheets (pending)
- ⚠️ Power symbols (pending)
- ⚠️ Multi-unit components (pending)
- ⚠️ NoConnect markers (pending)
- ⚠️ Junctions (pending)
- ⚠️ Bus connections (pending)
- ⚠️ Bus entries (pending)

**Proposed Test Structure:**

```
tests/unit/
├── wrappers/
│   ├── test_component.py          ✅ EXISTS
│   ├── test_wire.py                ✅ EXISTS
│   ├── test_label.py               ❌ MISSING
│   ├── test_global_label.py        ❌ MISSING
│   ├── test_hierarchical_label.py  ❌ MISSING
│   ├── test_power_symbol.py        ❌ MISSING
│   ├── test_no_connect.py          ❌ MISSING
│   ├── test_junction.py            ❌ MISSING
│   ├── test_text.py                ❌ MISSING
│   ├── test_text_box.py            ❌ MISSING
│   ├── test_bus.py                 ❌ MISSING
│   ├── test_bus_entry.py           ❌ MISSING
│   ├── test_sheet.py               ❌ MISSING
│   └── test_sheet_pin.py           ❌ MISSING
```

**Test Pattern (Example):**

Each object type should have tests for:
1. **Creation** - Object instantiation with valid parameters
2. **Properties** - Getting/setting properties
3. **Validation** - Required field enforcement
4. **Serialization** - S-expression output format
5. **Deserialization** - Loading from S-expression
6. **Modification** - Updating properties after creation

Example for `test_label.py`:
```python
def test_label_creation():
    """Test creating a local label."""
    label = Label(
        text="DATA",
        position=Position(100.0, 100.0)
    )
    assert label.text == "DATA"
    assert label.position.x == 100.0

def test_label_serialization():
    """Test label serializes to valid S-expression."""
    label = Label(text="DATA", position=Position(100.0, 100.0))
    sexpr = label.to_sexpr()
    assert '(label "DATA"' in sexpr
    assert '(at 100 100)' in sexpr

def test_label_deserialization():
    """Test label can be loaded from S-expression."""
    sexpr = '(label "DATA" (at 100 100 0))'
    label = Label.from_sexpr(sexpr)
    assert label.text == "DATA"

def test_label_validation():
    """Test label validates required fields."""
    with pytest.raises(ValueError):
        Label(text="")  # Empty text should fail
```

**Benefits:**
1. ✅ Prevents API regressions
2. ✅ Documents correct usage patterns
3. ✅ Enables confident refactoring
4. ✅ Validates S-expression format correctness
5. ✅ Catches edge cases and validation issues

**Priority:**
- **HIGH**: Labels, Power symbols, Hierarchical sheets (commonly used)
- **MEDIUM**: NoConnect, Junction, Text (frequently needed)
- **LOW**: Bus, BusEntry, TextBox (less common)

**Related:**
- Tests should follow existing pattern in `tests/unit/wrappers/test_component.py` and `test_wire.py`
- Each test file should be focused on a single object type
- Use pytest fixtures for common test data

---

---

## Summary

| Folder | Purpose | Pattern | Uses kicad-sch-api? |
|--------|---------|---------|---------------------|
| `bidirectional/` | Sync tests | Multi-step modify+verify | ✅ Yes (verification) |
| `generation/` | One-way generation | Single generate+validate | ✅ Yes (validation) |
| `kicad_sch_api/` | API object tests | Direct object creation | ✅ Yes (primary focus) |
| `conversion/` | Import/export fidelity | Round-trip cycle | ✅ Yes (validation) |
| `integration/` | External tools | Generate+run tool | ⚠️ Sometimes |
| `performance/` | Stress tests | Large circuits | ✅ Yes (validation) |
| `validation/` | Design rules | Rule checking | ✅ Yes (validation) |

---

**Next Steps:**

1. Create `tests/kicad_sch_api/` folder structure
2. Implement example tests for Component, Wire, Label
3. Move existing tests to appropriate folders
4. Implement Phase 1 of bidirectional test plan

Ready to proceed?
