# Hierarchical Schematic Support - Product & Engineering Requirements Document

**Issue**: #269
**Branch**: `feat/hierarchical-schematic-support`
**Created**: 2025-10-25
**Status**: Planning

---

## 1. Executive Summary

Enable bidirectional synchronization of **hierarchical KiCad schematics** (with sheet symbols) to multi-file Python projects. Currently, only flat (single-file) schematics work. This feature is essential for production use with complex designs.

---

## 2. Problem Statement

### Current Behavior
When a KiCad project contains hierarchical sheets:
- Parser warnings: `Could not parse sheet block: name=None, file=None`
- Only root schematic components are synced
- Sub-schematics (`.kicad_sch` files) are completely ignored
- No Python files are created for sheets

### Impact
- Users cannot sync complex, real-world designs
- Forces flat schematic organization (hundreds of components in one file)
- No modularity or reusability of subcircuits
- Blocks production adoption of bidirectional sync

---

## 3. Goals & Non-Goals

### Goals
✅ Parse sheet symbols from KiCad schematics
✅ Generate separate Python file for each sheet
✅ Support nested sheets (sheets within sheets)
✅ Bidirectional sync: KiCad ↔ Python for hierarchical designs
✅ Preserve hierarchical labels and connections
✅ Handle sheet name sanitization (Python identifiers)

### Non-Goals
❌ GUI for managing hierarchical structure
❌ Automatic circuit decomposition/hierarchy suggestions
❌ Migration of existing flat designs to hierarchical

---

## 4. KiCad Hierarchical Structure Analysis

### 4.1 File Structure

**Flat Schematic** (current support):
```
MyProject/
├── MyProject.kicad_pro
├── MyProject.kicad_sch      # Root schematic only
└── MyProject.json           # Generated netlist
```

**Hierarchical Schematic** (target):
```
MyProject/
├── MyProject.kicad_pro
├── MyProject.kicad_sch      # Root schematic with sheet symbols
├── power_supply.kicad_sch   # Sub-schematic 1
├── signal_proc.kicad_sch    # Sub-schematic 2
└── MyProject.json           # Generated netlist (all levels)
```

### 4.2 KiCad Sheet Block Format

From `BidirectionalTest.kicad_sch`:
```lisp
(sheet
  (at 91.44 118.11)              ; Position on parent schematic
  (size 21.59 20.32)             ; Size of sheet box
  (exclude_from_sim no)
  (in_bom yes)
  (on_board yes)
  (dnp no)
  (fields_autoplaced yes)
  (stroke ...)
  (fill ...)
  (uuid "f0651755-9815-4d54-ba93-6b3bccba6c7f")

  ; KEY PROPERTIES
  (property "Sheetname" "sheet1_name"    ; Display name
    (at 91.44 117.3984 0)
    (effects ...)
  )
  (property "Sheetfile" "shane1.kicad_sch"  ; File reference
    (at 91.44 139.0146 0)
    (effects ...)
  )

  ; Hierarchical pins (connections to parent)
  (pin "VCC" input (at 91.44 120.65 180) ...)
  (pin "GND" input (at 91.44 125.73 180) ...)
  (pin "OUT" output (at 113.03 120.65 0) ...)
)
```

### 4.3 Current Parser Behavior

**Location**: `src/circuit_synth/tools/utilities/kicad_parser.py`

The parser attempts to extract sheets but fails:
```python
# Current code (simplified)
def _parse_sheet_block(self, sheet_block):
    # Extracts 'name' and 'file' but returns None
    logger.warning(f"Could not parse sheet block: name=None, file=None")
```

**Root Cause**: Sheet properties are nested inside `(property ...)` blocks, not at top level.

---

## 5. Desired Python Structure

### 5.1 Single-Level Hierarchy

**KiCad Structure**:
```
MainProject/
├── main.kicad_sch              (has R1, R2, sheet symbol "PowerSupply")
└── power_supply.kicad_sch      (has C1, LDO1)
```

**Generated Python**:
```
MainProject/
├── main.py
└── power_supply.py
```

**main.py**:
```python
from circuit_synth import *
from power_supply import power_supply_circuit

@circuit(name="MainProject")
def main():
    # Root-level components
    r1 = Component(symbol="Device:R", ref="R1", value="10k")
    r2 = Component(symbol="Device:R", ref="R2", value="10k")

    # Subcircuit instantiation
    psu = power_supply_circuit()
```

**power_supply.py**:
```python
from circuit_synth import *

@circuit(name="PowerSupply")
def power_supply_circuit():
    # Sheet components
    c1 = Component(symbol="Device:C", ref="C1", value="10uF")
    ldo1 = Component(symbol="Regulator_Linear:AMS1117-3.3", ref="U1")
```

### 5.2 Multi-Level Hierarchy (Nested Sheets)

**KiCad Structure**:
```
MainProject/
├── main.kicad_sch                    (sheet: "PowerSupply")
├── power_supply.kicad_sch            (sheet: "LDO_Stage")
└── ldo_stage.kicad_sch               (components)
```

**Generated Python**:
```
MainProject/
├── main.py
├── power_supply.py
└── ldo_stage.py
```

**main.py**:
```python
from power_supply import power_supply_circuit

@circuit(name="MainProject")
def main():
    psu = power_supply_circuit()
```

**power_supply.py**:
```python
from ldo_stage import ldo_stage_circuit

@circuit(name="PowerSupply")
def power_supply_circuit():
    ldo = ldo_stage_circuit()
```

**ldo_stage.py**:
```python
@circuit(name="LDO_Stage")
def ldo_stage_circuit():
    c1 = Component(...)
```

---

## 6. Technical Questions

### Q1: File Naming Strategy
When converting `Sheetname` → Python filename:

**Option A**: Use `Sheetfile` basename (e.g., `power_supply.kicad_sch` → `power_supply.py`)
- ✅ Already unique (enforced by filesystem)
- ✅ Easy to find corresponding files
- ❌ User might have non-descriptive names

**Option B**: Use `Sheetname` property (e.g., `"Power Supply Stage"` → `power_supply_stage.py`)
- ✅ More descriptive
- ❌ Need to sanitize for Python identifiers
- ❌ Potential name collisions

**Question**: Which approach should we use? Or hybrid (sanitized Sheetname with fallback to Sheetfile)?

### Q2: Function Naming Convention
For the circuit function inside each Python file:

**Option A**: `{sheetname}_circuit()` (e.g., `power_supply_circuit()`)
**Option B**: `main()` in every file (import aliasing handles conflicts)
**Option C**: `circuit()` (rely on module namespace)

**Question**: What naming convention is clearest for users?

### Q3: Hierarchical Labels/Pins
KiCad sheets have pins for hierarchical connections:
```lisp
(pin "VCC" input (at 91.44 120.65 180))
(pin "GND" input (at 91.44 125.73 180))
(pin "OUT" output (at 113.03 120.65 0))
```

**Question**: How should these map to Python?
- Function parameters? `def power_supply_circuit(vcc, gnd):`
- Net objects passed in? `psu = power_supply_circuit(vcc_net, gnd_net)`
- Implicit via net names? (current flat approach)

### Q4: Circular Dependencies
What if there are circular sheet references?
- Sheet A includes Sheet B
- Sheet B includes Sheet A

**Question**: Should we:
- Detect and error?
- Allow but warn?
- Handle with late binding?

### Q5: Multiple Instances
KiCad allows multiple instances of the same sheet:
```
(sheet (property "Sheetfile" "filter_stage.kicad_sch") (uuid "aaa..."))
(sheet (property "Sheetfile" "filter_stage.kicad_sch") (uuid "bbb..."))
```

**Question**: How should Python represent this?
```python
filter1 = filter_stage_circuit()
filter2 = filter_stage_circuit()
```
Or track instances differently?

### Q6: Sheet UUID Handling
Each sheet instance has a unique UUID.

**Question**: Should we preserve these in Python comments or metadata for round-trip fidelity?

### Q7: JSON Netlist Structure
The generated JSON netlist contains all hierarchy levels flattened.

**Question**: Do we need to modify JSON generation to preserve hierarchy, or is flat netlist sufficient?

---

## 7. Proposed Architecture

### 7.1 Data Structures

```python
@dataclass
class SheetInstance:
    """Represents a sheet symbol in a schematic."""
    uuid: str
    sheetname: str           # Display name
    sheetfile: str           # File reference (e.g., "power_supply.kicad_sch")
    position: tuple[float, float]
    size: tuple[float, float]
    pins: List[SheetPin]
    parent_schematic: str    # Path to parent .kicad_sch

@dataclass
class SheetPin:
    """Hierarchical label connection."""
    name: str                # e.g., "VCC"
    direction: str           # input, output, bidirectional
    position: tuple[float, float]

@dataclass
class HierarchicalCircuit:
    """Represents entire circuit hierarchy."""
    root: Circuit            # Root schematic
    sheets: Dict[str, Circuit]  # Keyed by sheetfile
    hierarchy: Dict[str, List[SheetInstance]]  # Parent → children
```

### 7.2 Component Flow

```
┌─────────────────────────────────────────────────────────────┐
│ KiCad → Python (Import Direction)                           │
└─────────────────────────────────────────────────────────────┘

1. Parse root .kicad_sch
   ├── Extract components (existing)
   └── NEW: Extract sheet blocks
       ├── Parse Sheetname property
       ├── Parse Sheetfile property
       └── Parse hierarchical pins

2. For each sheet:
   ├── Parse {sheetfile}.kicad_sch recursively
   ├── Extract components
   └── Extract nested sheets (if any)

3. Build hierarchy tree
   ├── Detect circular references
   └── Establish parent-child relationships

4. Generate Python files
   ├── Root: main.py
   │   ├── Import statements for all sheets
   │   ├── Root components
   │   └── Sheet instantiations
   └── For each sheet: {sheetname}.py
       ├── Import statements for nested sheets
       ├── Circuit decorator
       ├── Sheet components
       └── Nested sheet instantiations

┌─────────────────────────────────────────────────────────────┐
│ Python → KiCad (Export Direction)                           │
└─────────────────────────────────────────────────────────────┘

1. Detect circuit function calls
   ├── Analyze imports: `from power_supply import power_supply_circuit`
   ├── Identify instantiations: `psu = power_supply_circuit()`

2. For each subcircuit call:
   ├── Create sheet symbol in parent .kicad_sch
   │   ├── Generate UUID
   │   ├── Set Sheetname from function/module name
   │   ├── Set Sheetfile to {module_name}.kicad_sch
   │   └── Infer hierarchical pins from net connections
   └── Generate/update sub-schematic file
       └── Recursively process nested circuits

3. Update positions
   ├── Auto-place sheet symbols
   └── Preserve positions if they exist
```

---

## 8. Testing Strategy

### 8.1 Unit Tests

**Fixture Structure**:
```
tests/bidirectional/fixtures/
├── simple_hierarchy/
│   ├── main.kicad_sch           # Root with 1 sheet
│   ├── power_supply.kicad_sch   # Sub-schematic
│   └── main.json
├── nested_hierarchy/
│   ├── main.kicad_sch           # Root with sheet to level2
│   ├── level2.kicad_sch         # Has sheet to level3
│   ├── level3.kicad_sch         # Leaf
│   └── main.json
└── multi_instance/
    ├── main.kicad_sch           # Root with 2x same sheet
    ├── filter_stage.kicad_sch   # Reused sheet
    └── main.json
```

**Test Cases**:
1. `test_parse_single_sheet_block()` - Extract sheet properties
2. `test_parse_nested_sheets()` - Recursive parsing
3. `test_detect_circular_dependency()` - Error on circular refs
4. `test_generate_sheet_python_file()` - Single sheet → Python
5. `test_generate_hierarchical_imports()` - Import statements
6. `test_multiple_sheet_instances()` - Reused sheets
7. `test_sheet_pin_extraction()` - Hierarchical labels
8. `test_python_to_kicad_sheet_creation()` - Reverse sync
9. `test_hierarchical_idempotency()` - Multiple syncs identical

### 8.2 Integration Tests

1. **Full KiCad → Python → KiCad round-trip**
2. **Nested 3-level hierarchy sync**
3. **Sheet addition detection** (user adds new sheet in KiCad)
4. **Sheet removal detection** (user deletes sheet in KiCad)

### 8.3 Manual Test Plan

See Section 10 for detailed manual test procedures.

---

## 9. Implementation Phases

### Phase 1: Sheet Block Parsing ✓
- [ ] Update `KiCadParser._parse_sheet_block()` to extract properties correctly
- [ ] Add `SheetInstance` and `SheetPin` dataclasses
- [ ] Write unit tests for sheet extraction
- [ ] Test with `bidirectional_test/BidirectionalTest/` fixture

### Phase 2: Recursive Schematic Parsing
- [ ] Implement recursive `.kicad_sch` file parsing
- [ ] Build hierarchical tree structure
- [ ] Detect circular dependencies
- [ ] Add integration test with 2-level hierarchy

### Phase 3: Multi-File Python Generation
- [ ] Generate separate `.py` file for each sheet
- [ ] Create import statements in parent files
- [ ] Handle function naming and sanitization
- [ ] Test with simple_hierarchy fixture

### Phase 4: Hierarchical Labels (Optional - Complex)
- [ ] Parse sheet pin definitions
- [ ] Map to function parameters or net passing
- [ ] Update code generation templates

### Phase 5: Reverse Sync (Python → KiCad)
- [ ] Detect subcircuit function calls in Python
- [ ] Generate sheet symbols in parent `.kicad_sch`
- [ ] Create/update sub-schematic files
- [ ] Test round-trip fidelity

### Phase 6: Polish & Edge Cases
- [ ] Handle multiple instances of same sheet
- [ ] Sheet name sanitization edge cases
- [ ] Position preservation
- [ ] UUID tracking for existing sheets

---

## 10. Manual Test Procedures

### Test 1: Simple Hierarchy (KiCad → Python)

**Setup**:
1. Create `SimpleProject/main.kicad_sch` with R1, R2
2. Add sheet symbol "PowerSupply" → `psu.kicad_sch`
3. In `psu.kicad_sch`, add C1, LDO1

**Execute**:
```bash
uv run kicad-to-python SimpleProject/ main.py
```

**Expected**:
```
SimpleProject/
├── main.py
└── psu.py
```

**main.py**:
```python
from psu import psu_circuit

@circuit(name="SimpleProject")
def main():
    r1 = Component(...)
    r2 = Component(...)
    psu = psu_circuit()
```

**psu.py**:
```python
@circuit(name="PowerSupply")
def psu_circuit():
    c1 = Component(...)
    ldo1 = Component(...)
```

### Test 2: Nested Hierarchy (3 Levels)

**Setup**:
- `main.kicad_sch` → sheet "System" → `system.kicad_sch`
- `system.kicad_sch` → sheet "PSU" → `psu.kicad_sch`
- `psu.kicad_sch` → components only

**Expected**: 3 Python files with correct import chain

### Test 3: Multiple Instances

**Setup**:
- `main.kicad_sch` with 2 sheet symbols both referencing `filter.kicad_sch`

**Expected**:
```python
filter1 = filter_circuit()  # Instance 1
filter2 = filter_circuit()  # Instance 2
```

### Test 4: Round-Trip Fidelity

**Setup**:
1. Start with hierarchical KiCad project (2 levels)
2. Sync to Python
3. Modify Python (add component to sheet)
4. Regenerate KiCad
5. Sync back to Python

**Expected**: Changes preserved, no data loss

---

## 11. Success Criteria

- [ ] Sheet blocks parsed correctly from `.kicad_sch` files
- [ ] Separate Python file created for each sheet
- [ ] Nested sheets (3+ levels) supported
- [ ] Import statements generated correctly
- [ ] Round-trip preserves all data
- [ ] Circular dependencies detected and reported
- [ ] Multiple instances of same sheet handled
- [ ] All unit tests passing (target: 10+ new tests)
- [ ] Integration tests passing
- [ ] Manual test procedures completed

---

## 12. Design Decisions ✓

**Answered 2025-10-25:**

### 1. File Naming: Use Sheetfile basename
- `Sheetfile: "psu.kicad_sch"` → `psu.py`
- Simple, matches KiCad filesystem
- No sanitization needed (already valid filename)

### 2. Function Naming: Circuit function per file
- Each file contains a circuit function
- Minimal code: circuit definition + comments only
- Example: `psu.py` contains circuit function for power supply

### 3. Hierarchical Pins: Function Parameters
- **Signals crossing circuits**: Pass as function parameters
  - Example: I2C, 3V3, GND, any inter-circuit signal
- **Internal signals**: Created inside function
  - Only used within that circuit, not passed in
- Maps directly to KiCad sheet pins (input/output)

### 4. Multiple Instances: Independent calls
- Calling `filter_circuit()` twice creates two independent instances
- `filter1 = filter_circuit()` and `filter2 = filter_circuit()` are different
- Each gets unique component references

### 5. Implementation Strategy: Test-Driven
- Focus on **blocking issue**: Adding sheet in KiCad should create Python file
- Incremental approach: Fix issues as found
- Write unit test for each issue discovered
- No need to solve everything upfront

### Open Questions (defer until needed):
- Circular dependency handling (error when encountered)
- UUID tracking (add if round-trip needs it)
- JSON structure (keep flat for now)

---

## 13. Implementation Plan (Test-Driven)

### Sprint 1: Basic Sheet Detection
**Goal**: When I add a sheet in KiCad, running sync should create a Python file

**Tasks**:
1. Write failing test: `test_parse_sheet_block_extracts_properties()`
2. Fix parser to extract `Sheetname` and `Sheetfile` from properties
3. Write failing test: `test_sync_creates_python_file_for_sheet()`
4. Implement: Generate `{sheetfile_basename}.py` when sheet detected
5. Verify: Manual test with `bidirectional_test/`

### Sprint 2: Sheet Components
**Goal**: Components in sheet schematic appear in sheet Python file

**Tasks**:
1. Write failing test: `test_parse_sheet_schematic_components()`
2. Implement: Recursively parse `{sheetfile}.kicad_sch`
3. Write failing test: `test_sheet_python_contains_components()`
4. Implement: Generate component code in sheet Python file

### Sprint 3: Import & Instantiation
**Goal**: Main Python file imports and calls sheet circuit

**Tasks**:
1. Write failing test: `test_main_imports_sheet_module()`
2. Implement: Generate `from psu import psu_circuit` in main.py
3. Write failing test: `test_main_instantiates_sheet()`
4. Implement: Generate `psu = psu_circuit()` in main.py

### Sprint 4: Hierarchical Pins (deferred until needed)
### Sprint 5: Reverse Sync (deferred until needed)

---

**Next Steps**: Start Sprint 1, Task 1 - Write first failing test.
