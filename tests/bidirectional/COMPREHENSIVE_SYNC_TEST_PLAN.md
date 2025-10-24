# Comprehensive Bidirectional Sync Test Plan

**Branch:** `test/comprehensive-bidirectional-sync-scenarios`
**Goal:** Exhaustively test all Python ↔ KiCad sync scenarios with focus on **idempotency**
**Key Principle:** Re-syncing without changes should be a no-op

---

## 🎯 Core Testing Philosophy

**Idempotency:** The most important property
```
State A → sync → State B → sync → State B (no change!)
```

If nothing changed between syncs, the second sync should detect this and **not modify files**.

**Incremental Testing:** Test one change at a time
- Start with blank project
- Add one component
- Add one connection
- Verify at each step

**Bidirectional Coverage:** Test both directions equally
- Python → KiCad (generation)
- KiCad → Python (import/update)

---

## 📋 Test Scenarios

### Phase 1: Blank Projects & Basic Generation

#### Test 1.1: Blank Python → Blank KiCad
- [ ] Create empty Python circuit (no components, no nets)
- [ ] Generate KiCad project
- [ ] Verify KiCad schematic created (blank but valid)
- [ ] Verify JSON netlist created (empty components/nets)

**Expected:**
```python
@circuit(name="blank")
def blank_circuit():
    pass  # No components or nets

circuit = blank_circuit()
circuit.generate_kicad_project("blank")
# Creates: blank/blank.kicad_sch (valid but empty)
#          blank/blank.json ({"components": {}, "nets": {}})
```

#### Test 1.2: Blank KiCad → Blank Python
- [ ] Create blank KiCad schematic manually
- [ ] Import to Python using kicad-to-python
- [ ] Verify Python code generated (blank circuit function)

**Expected:**
```python
# Generated from blank KiCad schematic
@circuit(name="blank")
def blank():
    pass  # No components detected
```

#### Test 1.3: Regenerate Blank Python → No Change
- [ ] Generate blank KiCad project from Python
- [ ] Record file checksums (or timestamps)
- [ ] Regenerate KiCad project (force_regenerate=True)
- [ ] Verify KiCad files unchanged (or minimal timestamp changes only)

**Critical:** This tests idempotency for blank projects

---

### Phase 2: Single Component Addition

#### Test 2.1: Add Resistor to KiCad
- [ ] Start with blank KiCad project
- [ ] Manually add one resistor (R1, 10k) in KiCad
- [ ] Save schematic
- [ ] Export to JSON (KiCad → JSON)
- [ ] Verify JSON has R1 with value 10k

#### Test 2.2: Import Resistor to Python
- [ ] Take KiCad project with R1
- [ ] Run kicad-to-python sync
- [ ] Verify Python code has:
  ```python
  r1 = Component(symbol="Device:R", ref="R1", value="10k", footprint="...")
  ```

#### Test 2.3: Re-import Without Changes → No Change
- [ ] Import KiCad to Python (creates Python code)
- [ ] Re-run kicad-to-python sync immediately
- [ ] Verify Python code **unchanged** (file checksum identical)

**Critical:** Idempotency test for KiCad → Python

#### Test 2.4: Run Python Project → KiCad Untouched
- [ ] Import KiCad to Python (creates Python with R1)
- [ ] Run Python circuit generation (Python → KiCad)
- [ ] Verify KiCad files **unchanged** if force_regenerate=False

**Expected behavior:** If Python code matches KiCad state, regeneration should detect this and skip rewriting files.

---

### Phase 3: Incremental Component Addition (Both Directions)

#### Test 3.1: Add Second Resistor in Python
- [ ] Start with Python project (has R1 from import)
- [ ] Add R2 in Python code:
  ```python
  r2 = Component(symbol="Device:R", ref="R2", value="20k", footprint="...")
  ```
- [ ] Generate KiCad project
- [ ] Verify KiCad schematic now has both R1 and R2
- [ ] Verify R1 **position preserved** (if it was manually placed)

#### Test 3.2: Re-generate Python → KiCad = No Change
- [ ] Generate KiCad from Python (R1 + R2)
- [ ] Record file checksums
- [ ] Re-generate KiCad from Python
- [ ] Verify KiCad files unchanged (or only timestamps)

**Critical:** Idempotency for Python → KiCad with multiple components

---

### Phase 4: Connection/Net Changes

#### Test 4.1: Connect Resistors in KiCad
- [ ] Start with KiCad having R1 and R2 (unconnected)
- [ ] Draw wire connecting R1 pin 2 to R2 pin 1 in KiCad
- [ ] Label net as "VOUT"
- [ ] Export to JSON
- [ ] Verify JSON has net "VOUT" with connections to R1[2] and R2[1]

#### Test 4.2: Import Connections to Python
- [ ] Take KiCad with R1-R2 connection
- [ ] Run kicad-to-python sync
- [ ] Verify Python code updated with:
  ```python
  vout = Net("VOUT")
  r1[2] += vout
  r2[1] += vout
  ```

#### Test 4.3: Re-import Connections → No Change
- [ ] Import KiCad connections to Python
- [ ] Re-run kicad-to-python sync
- [ ] Verify Python code **unchanged**

**Critical:** Connection idempotency

---

### Phase 5: Hierarchical Changes (Moving Components Between Circuits)

#### Test 5.1: Move Component to Different Circuit (Python)
- [ ] Start with Python project:
  ```python
  @circuit(name="power")
  def power_circuit():
      r1 = Component(...)  # In power circuit

  @circuit(name="signal")
  def signal_circuit():
      pass  # Empty
  ```
- [ ] Move R1 from power_circuit to signal_circuit in Python
- [ ] Generate KiCad
- [ ] Verify KiCad reflects new hierarchy (R1 in signal sheet)

#### Test 5.2: Move Component in KiCad Hierarchy
- [ ] Create KiCad with hierarchical sheets (power.kicad_sch, signal.kicad_sch)
- [ ] Move component from power sheet to signal sheet
- [ ] Import to Python
- [ ] Verify Python code has component in correct circuit function

---

### Phase 6: Preservation Tests (Critical!)

#### Test 6.1: Python Comments Not Deleted
- [ ] Create Python circuit with comments:
  ```python
  @circuit(name="voltage_divider")
  def voltage_divider():
      # This is the input voltage
      vin = Net("VIN")

      # Divider resistors (10k/10k = 50% voltage division)
      r1 = Component(...)  # Top resistor
      r2 = Component(...)  # Bottom resistor
  ```
- [ ] Generate KiCad
- [ ] Modify component value in KiCad (R1: 10k → 12k)
- [ ] Run kicad-to-python sync
- [ ] Verify Python code updated BUT **comments preserved**:
  ```python
  # This is the input voltage
  vin = Net("VIN")

  # Divider resistors (10k/10k = 50% voltage division)
  r1 = Component(..., value="12k")  # Top resistor  ← VALUE UPDATED
  r2 = Component(...)  # Bottom resistor            ← COMMENT PRESERVED
  ```

**Critical:** Comments are developer intent - must survive sync!

#### Test 6.2: KiCad Non-Component Objects Untouched
- [ ] Create KiCad schematic with:
  - Components (R1, R2)
  - Text annotations ("DO NOT POPULATE" on R2)
  - Graphical shapes (border around power section)
  - Title block information
- [ ] Update Python to change R1 value
- [ ] Generate KiCad from Python
- [ ] Verify KiCad:
  - R1 value updated ✓
  - R2 value unchanged ✓
  - Text annotation "DO NOT POPULATE" **preserved** ✓
  - Graphical shapes **preserved** ✓
  - Title block **preserved** ✓

**Critical:** Manual work in KiCad must not be destroyed by Python regeneration!

#### Test 6.3: Component Positions Preserved
- [ ] Generate KiCad from Python (auto-placement)
- [ ] Manually arrange components nicely in KiCad
- [ ] Record R1 position (x=50, y=50)
- [ ] Update R1 value in Python (10k → 12k)
- [ ] Regenerate KiCad with force_regenerate=False
- [ ] Verify R1 position **unchanged** (still x=50, y=50)
- [ ] Verify R1 value **updated** (now 12k)

**Critical:** Position is manual work - preserve during value updates!

#### Test 6.4: Wire Routing Preserved
- [ ] Generate KiCad from Python
- [ ] Manually route wires nicely (orthogonal, clean paths)
- [ ] Update component value in Python
- [ ] Regenerate KiCad
- [ ] Verify wire routing **unchanged** (same path, same vertices)

---

### Phase 7: Value Change Scenarios (Both Directions)

#### Test 7.1: Change Value in Python → KiCad Updated
- [ ] Python: R1 value = "10k"
- [ ] Generate KiCad
- [ ] Python: R1 value = "12k"
- [ ] Regenerate KiCad
- [ ] Verify KiCad schematic shows R1 = 12k

#### Test 7.2: Change Value in KiCad → Python Updated
- [ ] KiCad: R1 value = "10k"
- [ ] Import to Python
- [ ] KiCad: R1 value = "12k"
- [ ] Re-import to Python
- [ ] Verify Python code shows value="12k"

#### Test 7.3: Change Value Back and Forth
- [ ] Start: R1 = "10k" (both sides)
- [ ] Python: R1 = "12k" → generate KiCad
- [ ] KiCad: R1 = "15k" → import Python
- [ ] Python: R1 = "10k" → generate KiCad
- [ ] Verify: KiCad shows R1 = "10k"
- [ ] Re-import to Python → no change (already "10k")

**Tests that changes propagate correctly in both directions**

---

### Phase 8: Idempotency Stress Tests

#### Test 8.1: Sync 10 Times → No Drift
- [ ] Create circuit with 5 components, 3 nets
- [ ] For i in range(10):
  - Generate KiCad from Python
  - Import Python from KiCad
- [ ] Verify: After 10 round-trips, circuit unchanged

**Critical:** No data loss or drift over multiple syncs

#### Test 8.2: Blank → Component → Blank
- [ ] Start with blank circuit
- [ ] Add R1 in Python → generate KiCad
- [ ] Remove R1 in Python → regenerate KiCad
- [ ] Verify KiCad blank again (R1 removed)

#### Test 8.3: Complex State Preserved
- [ ] Create circuit with:
  - 20 components
  - 15 nets
  - 40 connections
  - Python comments on every component
  - Manual KiCad positions
  - KiCad text annotations
- [ ] Change one resistor value in Python
- [ ] Regenerate KiCad
- [ ] Verify:
  - Changed component updated ✓
  - All other 19 components unchanged ✓
  - All positions preserved ✓
  - All comments preserved ✓
  - All annotations preserved ✓

---

### Phase 9: Edge Cases & Error Handling

#### Test 9.1: Duplicate Component References
- [ ] KiCad has R1, R2
- [ ] Python already has R1 (different value)
- [ ] Import KiCad to Python
- [ ] Expected: Detect conflict, warn user, offer merge strategy

#### Test 9.2: Missing Footprint
- [ ] Python: Component without footprint
- [ ] Generate KiCad
- [ ] Expected: Warning, use default footprint or ask user

#### Test 9.3: Unknown Symbol
- [ ] KiCad: Custom symbol "MyCustomIC:SpecialChip"
- [ ] Import to Python
- [ ] Expected: Import symbol string as-is, warn if symbol not in library

#### Test 9.4: Circular References (Subcircuits)
- [ ] Python: Circuit A calls Circuit B, Circuit B calls Circuit A
- [ ] Generate KiCad
- [ ] Expected: Detect cycle, error with clear message

---

### Phase 10: Performance & Scaling

#### Test 10.1: Large Circuit (1000 components)
- [ ] Create Python circuit with 1000 resistors
- [ ] Generate KiCad
- [ ] Measure time: should be < 10 seconds
- [ ] Change one resistor value
- [ ] Regenerate KiCad
- [ ] Measure time: should be < 2 seconds (incremental update)

#### Test 10.2: Deep Hierarchy (10 levels)
- [ ] Create 10-level hierarchical circuit
- [ ] Generate KiCad
- [ ] Import back to Python
- [ ] Verify hierarchy preserved

---

### Phase 11: Footprint Changes

#### Test 11.1: Change Footprint in Python → KiCad Updated
- [ ] Python: R1 footprint = "Resistor_SMD:R_0603_1608Metric"
- [ ] Generate KiCad
- [ ] Python: R1 footprint = "Resistor_SMD:R_0805_2012Metric"
- [ ] Regenerate KiCad
- [ ] Verify KiCad schematic shows new footprint

#### Test 11.2: Change Footprint in KiCad → Python Updated
- [ ] KiCad: R1 footprint = "R_0603"
- [ ] Import to Python
- [ ] KiCad: R1 footprint = "R_0805"
- [ ] Re-import to Python
- [ ] Verify Python code shows new footprint

#### Test 11.3: Footprint-Only Change (Value Unchanged)
- [ ] Start: R1 value="10k", footprint="R_0603"
- [ ] Python: Change only footprint to "R_0805", keep value="10k"
- [ ] Generate KiCad
- [ ] Verify: Footprint changed, value unchanged
- [ ] Re-import to Python
- [ ] Verify: Python unchanged (already has correct state)

---

### Phase 12: Component Deletion

#### Test 12.1: Delete Component in Python → Removed from KiCad
- [ ] Python has R1, R2, R3
- [ ] Generate KiCad (all 3 present)
- [ ] Delete R2 from Python code
- [ ] Regenerate KiCad
- [ ] Verify: R1 and R3 present, R2 **removed** from schematic

#### Test 12.2: Delete Component in KiCad → Removed from Python
- [ ] KiCad has R1, R2, R3
- [ ] Import to Python (all 3 present)
- [ ] Delete R2 from KiCad schematic
- [ ] Re-import to Python
- [ ] Verify: Python code has only R1 and R3, R2 removed

#### Test 12.3: Delete All Components → Empty Circuit
- [ ] Start with circuit having 5 components
- [ ] Delete all components in Python
- [ ] Regenerate KiCad
- [ ] Verify: KiCad schematic blank (valid but no components)

#### Test 12.4: Delete Component Preserves Connections
- [ ] Python: R1--C1--R2 (series connection)
- [ ] Delete C1 in Python
- [ ] Regenerate KiCad
- [ ] Verify: R1 and R2 still present, C1 removed
- [ ] Net between R1-C1 should be gone or merged

---

### Phase 13: Net/Connection Deletion

#### Test 13.1: Delete Net in Python → Removed from KiCad
- [ ] Python has nets: VIN, VOUT, GND
- [ ] Generate KiCad
- [ ] Delete VOUT net in Python (disconnect components)
- [ ] Regenerate KiCad
- [ ] Verify: KiCad has no VOUT net

#### Test 13.2: Disconnect Wire in KiCad → Python Updated
- [ ] KiCad: R1[2] connected to VOUT
- [ ] Import to Python (has connection)
- [ ] Delete wire in KiCad (disconnect R1[2])
- [ ] Re-import to Python
- [ ] Verify: Python code no longer has r1[2] += vout

#### Test 13.3: Rename Net
- [ ] Python: Net named "VOUT"
- [ ] Generate KiCad
- [ ] Rename net to "OUTPUT" in Python
- [ ] Regenerate KiCad
- [ ] Verify: KiCad net labeled "OUTPUT"

---

### Phase 14: Metadata & Custom Properties

#### Test 14.1: Custom Component Properties Preserved
- [ ] Python: Add custom property to R1:
  ```python
  r1 = Component(..., custom_data={"tolerance": "1%", "power": "0.1W"})
  ```
- [ ] Generate KiCad
- [ ] Import back to Python
- [ ] Verify: custom_data preserved

#### Test 14.2: KiCad DNP (Do Not Populate) → Python
- [ ] KiCad: Mark R1 as DNP (Do Not Populate)
- [ ] Import to Python
- [ ] Verify: Python code reflects DNP status
  ```python
  r1 = Component(..., dnp=True)
  ```

#### Test 14.3: Reference Designator Change
- [ ] Python: Component ref="R1"
- [ ] Generate KiCad
- [ ] Change ref to "R10" in Python
- [ ] Regenerate KiCad
- [ ] Verify: KiCad shows R10, R1 reference removed

---

### Phase 15: Whitespace & Formatting Preservation

#### Test 15.1: Python Indentation Preserved
- [ ] Python code uses 4-space indentation
- [ ] Import KiCad changes
- [ ] Verify: Indentation still 4 spaces (not changed to tabs or 2 spaces)

#### Test 15.2: Blank Lines Preserved
- [ ] Python code has blank lines between component groups:
  ```python
  # Power components
  r1 = Component(...)

  # Signal components
  r2 = Component(...)
  ```
- [ ] Import KiCad changes
- [ ] Verify: Blank lines preserved

#### Test 15.3: Import Order Preserved
- [ ] Python code has imports in specific order:
  ```python
  from circuit_synth import Component
  from circuit_synth import Net
  from circuit_synth import circuit
  ```
- [ ] Import KiCad changes
- [ ] Verify: Import order unchanged

---

### Phase 16: Multi-File Projects

#### Test 16.1: Multi-File Python Project
- [ ] Python project structure:
  ```
  main.py
  subcircuits/power.py
  subcircuits/signal.py
  ```
- [ ] Generate KiCad
- [ ] Modify component in signal.py
- [ ] Regenerate KiCad
- [ ] Verify: Only signal.py circuit updated in KiCad

#### Test 16.2: Multi-Sheet KiCad Project
- [ ] KiCad with multiple sheets:
  ```
  main.kicad_sch
  power.kicad_sch
  signal.kicad_sch
  ```
- [ ] Import to Python
- [ ] Verify: Creates separate .py files for each sheet
- [ ] Modify power.kicad_sch
- [ ] Re-import
- [ ] Verify: Only power.py updated

---

### Phase 17: Version Control Friendliness

#### Test 17.1: Minimal Git Diff for Value Change
- [ ] Initial circuit, commit to git
- [ ] Change R1 value from 10k to 12k
- [ ] Regenerate KiCad
- [ ] Check git diff
- [ ] Verify: Only R1 value line changed (no spurious changes)

#### Test 17.2: Deterministic Output (Same Input → Same Output)
- [ ] Generate KiCad from Python circuit
- [ ] Record file contents
- [ ] Delete KiCad files
- [ ] Regenerate KiCad from same Python
- [ ] Verify: Files byte-identical (deterministic generation)

**Critical:** Non-deterministic generation causes spurious diffs

#### Test 17.3: Sorted Output for Stability
- [ ] Python with components in random order: [R3, R1, R2]
- [ ] Generate KiCad
- [ ] Python with components reordered: [R1, R2, R3]
- [ ] Regenerate KiCad
- [ ] Verify: KiCad file unchanged (components sorted internally)

---

### Phase 18: Concurrent Editing Scenarios

#### Test 18.1: Python and KiCad Modified Simultaneously
- [ ] Start with synced state (Python = KiCad)
- [ ] Modify R1 value in Python (10k → 12k)
- [ ] Modify R2 value in KiCad (20k → 22k)
- [ ] User tries to sync
- [ ] Expected: Detect conflict, show diff, ask user to resolve

#### Test 18.2: Same Component Modified in Both
- [ ] Start synced: R1 value = "10k"
- [ ] Python: R1 value = "12k"
- [ ] KiCad: R1 value = "15k"
- [ ] User tries to sync
- [ ] Expected: Conflict detected, user chooses which to keep

---

### Phase 19: Symbol Library Changes

#### Test 19.1: Symbol Changes (Library Update)
- [ ] Python uses Device:R (old symbol)
- [ ] Symbol library updated (Device:R_Small now preferred)
- [ ] Generate KiCad
- [ ] Expected: Warning about symbol change, offer migration

#### Test 19.2: Custom Symbol Library
- [ ] Python uses custom symbol: MyLib:CustomIC
- [ ] Generate KiCad
- [ ] KiCad doesn't have MyLib
- [ ] Expected: Clear error message with path to add library

---

### Phase 20: Error Recovery & Robustness

#### Test 20.1: Malformed KiCad File
- [ ] Create valid KiCad file
- [ ] Import to Python (works)
- [ ] Corrupt KiCad file (invalid s-expression)
- [ ] Try to re-import
- [ ] Expected: Clear error, point to line number, don't crash

#### Test 20.2: Partial File Write Failure
- [ ] Generate KiCad from Python
- [ ] Simulate disk full during write
- [ ] Expected: Atomic write fails cleanly, original file unchanged

#### Test 20.3: Python Syntax Error After Import
- [ ] Import KiCad to Python (generates valid Python)
- [ ] User manually edits, introduces syntax error
- [ ] Try to regenerate KiCad
- [ ] Expected: Detect syntax error, show clear message, don't crash

---

### Phase 21: Annotation & Labels

#### Test 21.1: Net Label Position Preserved
- [ ] KiCad: Place "VCC" label at specific position
- [ ] Import to Python
- [ ] Modify component value in Python
- [ ] Regenerate KiCad
- [ ] Verify: "VCC" label still at same position

#### Test 21.2: Component Annotation (Reference) Preserved
- [ ] Auto-annotate components in KiCad (R1, R2, R3...)
- [ ] Import to Python
- [ ] Add new component in Python
- [ ] Regenerate KiCad
- [ ] Verify: Existing references unchanged, new component gets next number

#### Test 21.3: Global Labels vs Local Labels
- [ ] KiCad: Mix of local and global labels
- [ ] Import to Python
- [ ] Verify: Label scope preserved (global vs local)

---

### Phase 22: Power/Ground Symbols

#### Test 22.1: Power Symbol Handling
- [ ] Python: Use power symbols (VCC, GND)
- [ ] Generate KiCad
- [ ] Verify: Power symbols rendered correctly (not as regular components)

#### Test 22.2: Ground Symbol Variants
- [ ] KiCad: Mix of GNDREF, GNDA, GNDD
- [ ] Import to Python
- [ ] Verify: Ground variants preserved (not all mapped to GND)

---

### Phase 23: Schematic Graphics

#### Test 23.1: Graphical Lines/Shapes Preserved
- [ ] KiCad: Draw rectangle around power section
- [ ] Import to Python (no representation in code)
- [ ] Modify component in Python
- [ ] Regenerate KiCad
- [ ] Verify: Rectangle still present in KiCad

#### Test 23.2: Text Box Annotations Preserved
- [ ] KiCad: Add text box "High voltage section - use caution"
- [ ] Import to Python
- [ ] Regenerate KiCad
- [ ] Verify: Text box preserved

---

## 🎯 Extended Testing Scenarios Summary

**Total Planned Tests:** ~80+

### By Category:
- Blank Projects: 3 tests
- Single Component: 4 tests
- Incremental Addition: 3 tests
- Connections: 3 tests
- Hierarchical: 2 tests
- Preservation: 4 tests
- Value Changes: 3 tests
- Idempotency Stress: 3 tests
- Edge Cases: 4 tests
- Performance: 2 tests
- **Footprint Changes: 3 tests** ← NEW
- **Component Deletion: 4 tests** ← NEW
- **Net Deletion: 3 tests** ← NEW
- **Metadata: 3 tests** ← NEW
- **Formatting: 3 tests** ← NEW
- **Multi-File: 2 tests** ← NEW
- **Version Control: 3 tests** ← NEW
- **Concurrent Editing: 2 tests** ← NEW
- **Symbol Library: 2 tests** ← NEW
- **Error Recovery: 3 tests** ← NEW
- **Annotations: 3 tests** ← NEW
- **Power Symbols: 2 tests** ← NEW
- **Graphics: 2 tests** ← NEW

---

## 🧪 Test Implementation Strategy

### Test Structure

```python
class TestBidirectionalSync:
    """Comprehensive bidirectional sync tests"""

    def test_1_1_blank_python_to_kicad(self):
        """Test 1.1: Blank Python → Blank KiCad"""
        # Implementation
        pass

    def test_1_2_blank_kicad_to_python(self):
        """Test 1.2: Blank KiCad → Blank Python"""
        pass

    # ... etc
```

### Helper Functions

```python
def assert_files_unchanged(files_before, files_after):
    """Verify files unchanged (by checksum or timestamp)"""
    for file in files_before:
        assert checksum(file) == checksum(files_after[file])

def assert_python_has_component(python_file, ref, value):
    """Parse Python AST and verify component exists with value"""
    tree = ast.parse(python_file.read_text())
    # ... check for Component(ref="R1", value="10k")

def assert_kicad_has_component(kicad_sch, ref, value):
    """Parse KiCad schematic and verify component"""
    parser = KiCadSchematicParser(kicad_sch)
    components = parser.get_components()
    assert ref in components
    assert components[ref]["value"] == value
```

### Fixture Strategy

```python
@pytest.fixture
def blank_python_circuit(tmp_path):
    """Blank Python circuit for testing"""
    circuit_file = tmp_path / "blank.py"
    circuit_file.write_text("""
from circuit_synth import circuit

@circuit(name="blank")
def blank_circuit():
    pass
""")
    return circuit_file

@pytest.fixture
def simple_kicad_project(tmp_path):
    """Simple KiCad project with one resistor"""
    # Create .kicad_pro, .kicad_sch with R1
    # Return project directory
    pass
```

---

## 📊 Success Criteria

**Passing all tests means:**
- ✅ Blank projects work in both directions
- ✅ Incremental changes sync correctly
- ✅ Re-syncing is idempotent (no unnecessary changes)
- ✅ Comments preserved in Python
- ✅ Manual work preserved in KiCad (positions, annotations, graphics)
- ✅ No data loss over multiple round-trips
- ✅ Large circuits perform adequately
- ✅ Edge cases handled gracefully

---

## 🚀 Implementation Plan

### Week 1: Foundation (Tests 1.1 - 2.4)
- [ ] Implement blank project tests
- [ ] Implement single component tests
- [ ] Implement basic idempotency tests

### Week 2: Bidirectional (Tests 3.1 - 4.3)
- [ ] Implement incremental addition tests
- [ ] Implement connection/net tests
- [ ] Verify both directions work

### Week 3: Preservation (Tests 6.1 - 6.4)
- [ ] Implement comment preservation tests
- [ ] Implement KiCad manual work preservation
- [ ] Critical for user trust!

### Week 4: Edge Cases & Performance (Tests 9.1 - 10.2)
- [ ] Implement error handling tests
- [ ] Implement large circuit tests
- [ ] Optimize based on results

---

## 📝 Test Tracking

Use checkboxes above to track progress. Update this file as tests are implemented.

**Current Status:**
- Total Tests Planned: ~40
- Tests Implemented: 0
- Tests Passing: 0

---

## 🔗 Related Documents

- `ROUND_TRIP_TESTING_SUMMARY.md` - Basic round-trip validation
- `BIDIRECTIONAL_SYNC_TESTS.md` - Original test plan (15 tests)
- `PRD_JSON_TO_PYTHON_CANONICAL_UPDATE.md` - Phase 1-4 implementation plan

---

## 💡 Key Insights

### 1. Idempotency is King
If you sync twice without changes, nothing should happen. This is how users gain confidence in the tool.

### 2. Preserve Manual Work
Users spend time in KiCad positioning components and routing. Destroying this work kills trust.

### 3. Comments are Code
Python comments represent developer intent. Losing them makes code unmaintainable.

### 4. Test One Thing at a Time
Start with blank, add one component, add one connection. Incremental testing catches subtle bugs.

### 5. Both Directions Equally Important
Python → KiCad and KiCad → Python must both work flawlessly. Test symmetrically.

---

**Last Updated:** 2025-10-23
**Branch:** `test/comprehensive-bidirectional-sync-scenarios`
